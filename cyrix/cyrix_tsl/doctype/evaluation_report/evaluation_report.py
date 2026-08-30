# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe.utils import add_to_date
from cyrix.custom_py.boot import get_bootinfo as info
from cyrix.custom_py.utils import sendmail
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime
import datetime

NO_REPLY_EMAIL = "no-reply@cyrix-tsl.com"
base_url = frappe.utils.get_url()
warehouse_list = {
	"Kuwait": "Kuwait - CT-K",
	"Riyadh":"Riyadh - BM",
	"Jeddah":"Jeddah - BM",
	"Dubai": "Dubai - CT-UAE",
}

def validate_status(self):
	before = self.get_doc_before_save()
	if before:
		if before.docstatus:
			if before.status != self.status:
				return True
			else:
				return False
		else:
			return True

# ---------------------------------------------------------------------------
# Stock helpers
# ---------------------------------------------------------------------------
def _get_bin_values(item_code: str, warehouse: str) -> dict:
	"""Return actual_qty, awaiting_qty and custom_reserve_qty from Bin."""
	values = frappe.db.get_value(
		"Bin",
		{"item_code": item_code, "warehouse": warehouse},
		["actual_qty", "awaiting_qty", "custom_reserve_qty"],
		as_dict=True,
	)
	if not values:
		return {"actual_qty": 0.0, "awaiting_qty": 0.0, "custom_reserve_qty": 0.0}
	return {
		"actual_qty":         float(values.actual_qty or 0),
		"awaiting_qty":       float(values.awaiting_qty or 0),
		"custom_reserve_qty": float(values.custom_reserve_qty or 0),
	}


def _recompute_bin_reserved(item_code: str, warehouse: str) -> None:
	"""
	Recompute custom_reserve_qty on the Bin by summing ALL active
	Evaluation Stock Reservations for this item/warehouse.

	Called after every reservation create, update, cancel, or release
	so the Bin always reflects the true total.
	"""
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(reserved_qty), 0) - COALESCE(SUM(released_qty), 0)
		FROM   `tabEvaluation Stock Reservation`
		WHERE  item_code  = %(item_code)s
		AND  warehouse  = %(warehouse)s
		AND  status     = 'Active'
		""",
		{"item_code": item_code, "warehouse": warehouse},
	)
	total_reserved = float(result[0][0] if result else 0)

	bin_name = frappe.db.get_value(
		"Bin", {"item_code": item_code, "warehouse": warehouse}, "name"
	)
	if bin_name:
		frappe.db.set_value(
			"Bin", bin_name, "custom_reserve_qty", total_reserved
		)


# ---------------------------------------------------------------------------
# Reservation record helpers
# ---------------------------------------------------------------------------

def _get_existing_reservations(doc_name: str) -> dict:
	rows = frappe.get_all(
		"Evaluation Stock Reservation",
		filters={
			"evaluation_report": doc_name,
			"status": ["in", ["Active", "Released"]],
		},
		fields=[
			"name", "item_code", "warehouse", "qty", "reserved_qty",
			"released_qty", "status", "child_row_name", "released_date",
		],
	)
	out = {}
	for r in rows:
		if r.get("child_row_name"):
			r["status"] = (r["status"] or "").strip()
			out[r["child_row_name"]] = r
	return out

def _cancel_reservation(res_name: str, item_code: str, warehouse: str, reason: str = "") -> None:
	frappe.db.set_value(
		"Evaluation Stock Reservation",
		res_name,
		{
			"status":        "Cancelled",
			"released_date": now_datetime(),
			"notes":         reason or "Row removed from Evaluation Report.",
		},
	)
	_recompute_bin_reserved(item_code, warehouse)


def _update_reservation(
	res_name: str,
	item_code: str,
	warehouse: str,
	qty: float,
	reserved_qty: float,
	status: str,
	notes: str = None,
) -> None:
	"""Update an existing reservation in place (works for Active AND Released)."""
	values = {
		"qty":          qty,
		"reserved_qty": reserved_qty,
		"status":       status,
	}
	if status == "Active":
		# Reactivated — clear released_date so it doesn't look closed
		values["released_date"] = None
	elif status == "Released":
		values["released_date"] = now_datetime()
	if notes:
		values["notes"] = notes

	frappe.db.set_value("Evaluation Stock Reservation", res_name, values)
	_recompute_bin_reserved(item_code, warehouse)


def _create_reservation(
	evaluation_report: str,
	item_code: str,
	warehouse: str,
	qty: float,
	reserved_qty: float,
	child_row_name: str,
	technician: str = None,
) -> None:
		# Guard: never allow two Active reservations for the same child row
	stale = frappe.get_all(
		"Evaluation Stock Reservation",
		filters={
			"evaluation_report": evaluation_report,
			"child_row_name": child_row_name,
			"status": "Active",
		},
		fields=["name", "item_code", "warehouse"],
	)
	for s in stale:
		_cancel_reservation(s["name"], s["item_code"], s["warehouse"],
			reason="Superseded by new reservation for the same row.")

	res = frappe.new_doc("Evaluation Stock Reservation")
	res.evaluation_report = evaluation_report
	res.item_code         = item_code
	res.warehouse         = warehouse
	res.qty               = qty
	res.reserved_qty      = reserved_qty
	res.status            = "Active"
	res.technician        = technician
	res.reservation_date  = now_datetime()
	res.child_row_name    = child_row_name
	res.insert(ignore_permissions=True)
	_recompute_bin_reserved(item_code, warehouse)

def _availability_label(required: float, reserved: float, from_scrap: bool = False) -> str:
	if from_scrap:
		return "Yes"
	if reserved <= 0:
		return "No"
	if reserved >= required:
		return "Yes"
	return "Partial"

def _resolve_status(reserved_qty: float, released_qty: float) -> str:
	"""
	Active   → there is still something held that hasn't been issued
	Released → everything reserved has been issued
	"""
	if released_qty > 0 and flt(reserved_qty) <= flt(released_qty):
		return "Released"
	return "Active"


# ---------------------------------------------------------------------------
# Core diff logic
# ---------------------------------------------------------------------------

def _sync_reservations(doc) -> None:
	from datetime import datetime

	if datetime.strptime(str(doc.date), "%Y-%m-%d").date() < datetime.strptime("2026-07-07", "%Y-%m-%d").date():
		return
	
	if doc.status in ("Completed", "Cancelled"):
		_cancel_all_active(doc.name)
		return

	warehouse = warehouse_list.get(doc.branch)
	if not warehouse:
		frappe.throw(
			_("No warehouse mapped for branch <b>{0}</b>. "
			  "Please update warehouse_list in evaluation_report.py.").format(doc.branch)
		)

	existing          = _get_existing_reservations(doc.name)
	current_row_names = set()
	no_stock_items    = []
	partial_items     = []
	over_release_note = []

	for row in doc.items:
		# Ignore items sourced from scrap
		if getattr(row, "from_scrap", 0):
			continue

		if not (row.part and row.qty):
			continue

		required = flt(row.qty)
		current_row_names.add(row.name)
		existing_res = existing.get(row.name)
		released     = flt(existing_res["released_qty"]) if existing_res else 0.0

		# ── Read Bin values ───────────────────────────────────────────────
		bin_vals      = _get_bin_values(row.part, warehouse)
		actual_qty = bin_vals["actual_qty"]
		awaiting_qty  = bin_vals["awaiting_qty"]
		available_qty = actual_qty - awaiting_qty


		# The Bin's custom_reserve_qty holds SUM(reserved − released) for
		# Active reservations. Add back THIS row's own NET contribution so
		# it doesn't count against itself during the recalculation.
		own_net = flt(frappe.db.sql(
			"""
			SELECT COALESCE(SUM(reserved_qty), 0) - COALESCE(SUM(released_qty), 0)
			FROM   `tabEvaluation Stock Reservation`
			WHERE  evaluation_report = %(doc)s
			AND    child_row_name    = %(row)s
			AND    item_code         = %(item)s
			AND    warehouse         = %(wh)s
			AND    status            = 'Active'
			""",
			{"doc": doc.name, "row": row.name, "item": row.part, "wh": warehouse},
		)[0][0] or 0)

		total_eval_reserved = bin_vals["custom_reserve_qty"]
		free_qty = available_qty - total_eval_reserved + own_net

		# ── How much can we hold in total? ────────────────────────────────
		# Released qty is already physically issued — it is permanently
		# secured and never competes for free stock again. Only the
		# remaining need is checked against free stock.
		remaining_need = max(required - released, 0)
		additional     = min(remaining_need, max(free_qty, 0))
		can_reserve    = released + additional
		shortage       = max(required - can_reserve, 0)

		# ── Guard: qty reduced below already-issued qty ───────────────────
		if released > 0 and required < released:
			over_release_note.append(
				"Row {0}: {1} — qty reduced to {2} but {3} already issued. "
				"Reservation kept at {3}. Use a Material Receipt to return parts.".format(
					row.idx, row.part, required, released
				)
			)
			# Never hold less than what has physically left the warehouse
			can_reserve = released
			shortage    = 0

		# ── No stock available for the remaining need ─────────────────────
		if available_qty <= 0 and remaining_need > 0 and additional <= 0:
			if existing_res and released == 0:
				# Nothing issued yet — safe to cancel entirely
				_cancel_reservation(
					existing_res["name"],
					item_code=row.part,
					warehouse=warehouse,
					reason="Item has no stock. Cancelled; needs to be purchased.",
				)
				_write_row_fields(row, reserved=0, shortage=required, label="No")
			elif existing_res:
				# Parts already issued — keep the reservation document,
				# clamp reserved to the released level
				_update_reservation(
					existing_res["name"],
					item_code=row.part,
					warehouse=warehouse,
					qty=required,
					reserved_qty=released,
					status="Released",
					notes="Qty increased but no stock for the balance. Balance to be purchased.",
				)
				_write_row_fields(
					row,
					reserved=released,
					shortage=max(required - released, 0),
					label=_availability_label(required, released),
				)
			else:
				_write_row_fields(row, reserved=0, shortage=required, label="No")

			no_stock_items.append(
				"Row {0}: {1} — no stock in {2}".format(row.idx, row.part, warehouse)
			)
			continue

		new_status = _resolve_status(can_reserve, released)

		# ── Diff against existing reservation ─────────────────────────────
		if existing_res:
			same_item = existing_res["item_code"] == row.part
			same_wh   = existing_res["warehouse"] == warehouse

			if not (same_item and same_wh):
				# Item or warehouse changed
				if released > 0:
					frappe.throw(
						_("Row {0}: cannot change item/warehouse — {1} qty already "
						  "issued against this row. Return the parts via Material "
						  "Receipt first.").format(row.idx, released)
					)
				_cancel_reservation(
					existing_res["name"],
					item_code=existing_res["item_code"],
					warehouse=existing_res["warehouse"],
					reason="Item or warehouse changed on Evaluation Report.",
				)
				_create_reservation(
					evaluation_report=doc.name,
					item_code=row.part,
					warehouse=warehouse,
					qty=required,
					reserved_qty=can_reserve,
					child_row_name=row.name,
					technician=doc.technician,
				)
			else:
				changed = (
					flt(existing_res["qty"]) != required
					or flt(existing_res["reserved_qty"]) != can_reserve
					or existing_res["status"] != new_status
				)
				if changed:
					# Same document updated in place — this is the path that
					# handles qty changes on Released reservations too
					_update_reservation(
						existing_res["name"],
						item_code=row.part,
						warehouse=warehouse,
						qty=required,
						reserved_qty=can_reserve,
						status=new_status,
					)
				# else: nothing changed — leave untouched
		else:
			_create_reservation(
				evaluation_report=doc.name,
				item_code=row.part,
				warehouse=warehouse,
				qty=required,
				reserved_qty=can_reserve,
				child_row_name=row.name,
				technician=doc.technician,
			)

		# ── Write display fields ──────────────────────────────────────────
		label = _availability_label(required, can_reserve)
		_write_row_fields(row, reserved=can_reserve, shortage=shortage, label=label)

		if label == "Partial":
			partial_items.append(
				"Row {0}: {1} — reserved {2} of {3}. "
				"Shortage: {4} (to be purchased).".format(
					row.idx, row.part, can_reserve, required, shortage
				)
			)

	# ── Cancel reservations for deleted rows ──────────────────────────────
	removed = set(existing.keys()) - current_row_names
	for row_name in removed:
		res = existing[row_name]
		if flt(res["released_qty"]) > 0:
			# Parts already issued against this row — do NOT cancel.
			# Clamp reservation to released level and close it.
			_update_reservation(
				res["name"],
				item_code=res["item_code"],
				warehouse=res["warehouse"],
				qty=res["qty"],
				reserved_qty=flt(res["released_qty"]),
				status="Released",
				notes="Row deleted from Evaluation Report after partial/full issue.",
			)
		else:
			_cancel_reservation(
				res["name"],
				item_code=res["item_code"],
				warehouse=res["warehouse"],
				reason="Row deleted from Evaluation Report.",
			)

	# ── Consolidated warnings ─────────────────────────────────────────────
	messages = []
	if over_release_note:
		messages.append("<b>Qty below issued qty:</b><br>" + "<br>".join(over_release_note))
	if no_stock_items:
		messages.append("<b>No stock — Purchase Required:</b><br>" + "<br>".join(no_stock_items))
	if partial_items:
		messages.append("<b>Partial stock — balance to be purchased:</b><br>" + "<br>".join(partial_items))
	if messages:
		frappe.msgprint(
			msg="<br><br>".join(messages),
			title="Stock Reservation Summary",
			indicator="orange",
			alert=False,
		)



def _write_row_fields(row, reserved: float, shortage: float, label: str) -> None:
	if row.name:
		frappe.db.set_value(
			row.doctype,
			row.name,
			{
				"reserved_qty":       reserved,
				"shortage_qty":       shortage,
				"parts_availability": label,
			},
		)
	row.reserved_qty       = reserved
	row.shortage_qty       = shortage
	row.parts_availability = label


def _cancel_all_active(doc_name: str) -> None:
	reservations = frappe.get_all(
		"Evaluation Stock Reservation",
		filters={"evaluation_report": doc_name, "status": "Active"},
		fields=["name", "item_code", "warehouse", "qty", "released_qty"],
	)
	for r in reservations:
		if flt(r["released_qty"]) > 0:
			_update_reservation(
				r["name"],
				item_code=r["item_code"],
				warehouse=r["warehouse"],
				qty=r["qty"],
				reserved_qty=flt(r["released_qty"]),
				status="Released",
				notes="Evaluation Report cancelled/completed after partial issue.",
			)
		else:
			_cancel_reservation(
				r["name"],
				item_code=r["item_code"],
				warehouse=r["warehouse"],
				reason="Evaluation Report cancelled/completed.",
			)

class EvaluationReport(Document):
	@frappe.whitelist()
	def update_availability_status(self):
		for i in self.items:
			if i.part:
				if frappe.db.exists("Bin",{'item_code':i.part,'warehouse':self.warehouse}):
					bin = frappe.db.get_value("Bin",{'item_code':i.part,'warehouse':self.warehouse},'actual_qty')
					price = frappe.db.get_value("Bin", {"item_code": i.part,'warehouse':self.warehouse}, "valuation_rate") or frappe.db.get_value("Item Price", {"item_code": i.part, "buying": 1}, "price_list_rate") or 0
					if float(bin) >= float(i.qty):
						status = "Yes"
						i.parts_availability = status
						i.price_ea = price
						total = price * i.qty
						i.total = total

						frappe.db.sql('''update `tabPart Sheet Item` set parts_availability = '{0}', price_ea = {1}, total = {2} where name ='{3}' '''.format(status,price,total,i.name))
					else:
						i.parts_availability = "No"
						frappe.db.sql('''update `tabPart Sheet Item` set parts_availability = '{0}'  where name ='{1}' '''.format("No",i.name))


		self.check_stock_availability() # to update the stock availability
		self.update_job_order_status() # to update the Job Order Data status

	def validate(self):			
		self.update_part_sheet_number()

	def update_part_sheet_number(self):
		for i in self.items:
			if not i.part_sheet_no:
				i.part_sheet_no = 1

	def update_part_no(self):
		if self.if_parts_required:
			self.part_no = 0
			for i in self.get("items"):
				if not i.part_sheet_no:
					i.part_sheet_no = int(self.part_no)+1
					frappe.db.sql('''update `tabPart Sheet Item` set part_sheet_no = %s where name = %s''',((int(self.part_no)+1),i.name))
				self.part_no = i.part_sheet_no
				frappe.db.sql('''update `tabEvaluation Report` set part_no = %s where name = %s''',((int(i.part_sheet_no)),self.name))
		
			if self.items and int(self.items[-1].part_sheet_no) > int(1) and self.status in ["Spare Parts","Comparison","Extra Parts","Internal Extra Parts"] and self.ner_field != "NER-Need Evaluation Return":
				self.status = "Internal Extra Parts"
				frappe.db.sql('''update `tabEvaluation Report` set status = %s where name = %s ''',("Internal Extra Parts",self.name))
				if self.document_active_status == "Yes":
					wd = frappe.get_doc("Job Order Data",self.job_order_data)
					wd.status = "IP-Internal Extra Parts"
					wd.save(ignore_permissions = 1)
			
	def after_insert(self):		
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		doc.status = "UE-Under Evaluation"
		doc.save(ignore_permissions = True)
		check_for_shared_docs_on_evaluation(self)	
	
	def on_update(self):		
		check_for_shared_docs_on_evaluation(self)
		
	def validate_evaluation_time(self):
		if (not self.evaluation_time or not self.estimated_repair_time) and self.status not in ["Return Not Repaired"]:
			frappe.throw("Note: Evaluation Time and Estimated Repair Time is not given.")
		self.check_stock_availability() # to update the stock availability

	def before_submit(self):
		self.validate_evaluation_time()
		
	def on_submit(self):
		_sync_reservations(self)
		self.update_job_order_status() # to update the Job Order Data status
		self.send_mail_on_status_update(action = "on_submit")

	def on_update_after_submit(self):
		_sync_reservations(self)
		self.check_stock_availability() # to update the stock availability
		self.update_job_order_status() # to update the Job Order Data status
		self.update_part_no()
		check_for_shared_docs_on_evaluation(self)
		self.send_mail_on_status_update(action = "on_update_after_submit")

	def on_cancel(self):
		_cancel_all_active(self.name)

	def check_stock_availability(self):
		# based on the stock availability check in child table rows, overall availability is defined
		if self.if_parts_required:
			check =0
			for i in self.get("items"):
				if i.parts_availability == "No" and not i.from_scrap:
					check=1
			if check:
				self.parts_availability = "No"
				frappe.db.set_value("Evaluation Report",self.name,'parts_availability',"No",update_modified = False)
			else:
				self.parts_availability = "Yes"
				frappe.db.set_value("Evaluation Report",self.name,'parts_availability',"Yes",update_modified = False)

	def update_jo_status_after_purchase_receipt(self):
		# based on the stock availability check in child table rows, update the Job Order status
		if self.if_parts_required:
			check =0
			for i in self.get("items"):
				if i.parts_availability == "No" and not i.from_scrap:
					check=1
			doc = frappe.get_doc("Job Order Data",self.job_order_data)
			if check == 0:
				doc.status = "TR-Technician Repair"
			else:
				doc.status = "WP-Waiting Parts"
			doc.save(ignore_permissions=True)

	def update_job_order_status(self):
		# based on the stock availability Job Order Data status will be defined
		doc = frappe.get_doc("Job Order Data",self.job_order_data)

		self.update_working_status() # if the document status is changed as Working, Need to change the JO status as Working
		self.update_board_evaluation_status() # if the document status is changed as Board Evaluation, Need to change the JO status as Board Evaluation
		# 1. this case mostly works on initial submission
		if doc.status in ["NE-Need Evaluation","NER-Need Evaluation Return","UE-Under Evaluation"]:
			if self.status == "Spare Parts":

				# if parts avaliability field is yes
				if self.parts_availability == "Yes":
					doc.status = "AP-Available Parts"
				else:
					doc.status = "SP-Searching Parts"
				doc.save(ignore_permissions=True)

	def update_working_status(self):
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		if self.status == "Working" and validate_status(self):
			if doc.status != "W-Working" and not self.check_quotation_exists(self.job_order_data):
				doc.status = "W-Working"
			doc.save(ignore_permissions=True)

		if self.status == "Installed and Completed/Repaired" and validate_status(self):
			doc.status = "RS-Repaired and Shipped"
			doc.save(ignore_permissions=True)

		if self.status == "Return Not Repaired" and validate_status(self):
			doc.status = "RNR-Return Not Repaired"
			doc.save(ignore_permissions=True)	

		if self.status == "RNP-Return No Parts" and validate_status(self):
			doc.status = "RNP-Return No Parts"
			doc.save(ignore_permissions=True)

		if self.status == "Return No Fault" and validate_status(self):
			doc.status = "RNF-Return No Fault"
			doc.save(ignore_permissions=True)
		
		if self.status == "Comparison" and validate_status(self):
			doc.status = "C-Comparison"
			doc.save(ignore_permissions=True)

		if self.status == "Extra Parts" and self.parts_availability != "Yes" and validate_status(self):
			doc.status = "EP-Extra Parts"
			doc.save(ignore_permissions = True)	

	def update_board_evaluation_status(self):
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		if self.status == "Board Evaluation" and validate_status(self):
			doc.status = "Board Evaluation"
			doc.save(ignore_permissions=True)

	def check_quotation_exists(self,jo):
		# check whether the Customer Quotation is exists for the given Job Order Data, workflow_state should beApproved by Customer and the job_order_data is set in Quotation Item table.
		quotation_exists = False
		quotations = frappe.get_all("Quotation Item", filters={"job_order_data": jo, "docstatus": 1}, pluck="parent")
		if quotations:
			for q in quotations:
				quotation_doc = frappe.get_doc("Quotation", q)
				if quotation_doc.workflow_state == "Approved by Customer":
					quotation_exists = True
					break
		return quotation_exists

	def send_mail_on_status_update(self, action):
		if self.status not in ["Internal Extra Parts", "Spare Parts", "Extra Parts"]:
			return

		# to check for the previous status
		before = self.get_doc_before_save()

		if not before:
			return

		if before.status == self.status and action != "on_submit":
			return

		message = f""" Dear Purchase Team,<br><br>
						Evaluation Report - <b>{self.name}</b> has been created<br>
						Job Order Data - <b>{self.get("job_order_data")}</b><br>
						Status - <b>{self.get("status")}</b><br><br>
						Please take action to release the parts.<br><br>
						<a href="{base_url}/app/evaluation-report/{self.name}" target="_blank">Click Here</a>
					"""

		sendmail(self, 
			message, 
			subject = f"Evaluation Report - {self.name}", 
			sender = NO_REPLY_EMAIL, 
			recipients = info().get("purchase_to").get(self.company), 
			attachments = None, 
			cc = None 
		)

def check_for_shared_docs_on_evaluation(self):
	jo_doc = frappe.get_doc("Job Order Data", self.job_order_data)

	technicians = []

	# Main JO technician
	tech_user = frappe.db.get_value(
		"Technician ID", jo_doc.technician, "user_email"
	)
	if tech_user:
		technicians.append(tech_user)

	# Parent JO technicians
	if jo_doc.parent_jo:
		parent_doc = frappe.get_doc("Job Order Data", jo_doc.parent_jo)

		parent_tech_user = frappe.db.get_value(
			"Technician ID", parent_doc.technician, "user_email"
		)
		if parent_tech_user and parent_tech_user not in technicians:
			technicians.append(parent_tech_user)

		for row in parent_doc.multiple_technicians:
			if row.email and row.email not in technicians:
				technicians.append(row.email)

	# Current JO additional technicians
	for row in jo_doc.multiple_technicians:
		if row.email and row.email not in technicians:
			technicians.append(row.email)

	# Existing shares
	existing_shares = frappe.get_all(
		"DocShare",
		filters={
			"share_doctype": self.doctype,
			"share_name": self.name,
		},
		fields=["name", "user"],
	)

	existing_users = {share.user for share in existing_shares}

	# Add missing shares
	for user in technicians:
		if user not in existing_users:
			doc = frappe.new_doc("DocShare")
			doc.user = user
			doc.share_doctype = self.doctype
			doc.share_name = self.name
			doc.read = 1
			doc.write = 1
			doc.save(ignore_permissions=True)

	# Remove obsolete shares
	for share in existing_shares:
		if share.user not in technicians:
			frappe.delete_doc(
				"DocShare",
				share.name,
				ignore_permissions=True,
				force=True,
			)


@frappe.whitelist()
def get_valuation_rate(item, warehouse, qty):
	price = 0
	sts = "No"
	if frappe.db.exists("Bin",{'item_code':item,'warehouse':warehouse}):
		bin = frappe.db.get_value("Bin",{'item_code':item,'warehouse':warehouse},'actual_qty')
		if float(bin) >= float(qty):
			sts = "Yes"		
	price = frappe.db.get_value("Bin", {"item_code": item,'warehouse':warehouse}, "valuation_rate") or frappe.db.get_value("Item Price", {"item_code": item, "buying": 1}, "price_list_rate") or 0

	return {"price": price, "status": sts}

# Item creation
@frappe.whitelist()
def sku_creation(doc):
	sku_list = []
	data_dict = frappe._dict(json.loads(doc))

	for pm in data_dict.get("items", []):
		model = pm.get("model")
		part_no = pm.get("part")
		category = pm.get("category")
		sub_cat = pm.get("sub_category")
		package = pm.get("part_description")
		des = pm.get("part_name")
		if not part_no:
			# Check if an item already exists with same model, category, sub_category
			existing_item = frappe.get_all("Item", filters={
				"model": model,
				"category": category,
				"sub_category": sub_cat
			}, fields=["name"])

			if not existing_item:
				item_doc = frappe.new_doc("Item")
				item_doc.naming_series = 'P.######'
				item_doc.model = model

				# Fetch model number
				mod = frappe.db.get_value("Item Model", model, "model")
				item_doc.model_num = mod if mod else ""

				item_doc.category = category

				# Fetch sub-category name
				scn = frappe.db.get_value("Sub Category", sub_cat, "sub_category")
				item_doc.sub_category = sub_cat
				item_doc.sub_category_name = scn if scn else ""

				item_doc.package = package
				item_doc.description = des
				item_doc.item_name = des
				item_doc.item_group = "Components"

				try:
					item_doc.save(ignore_permissions=True)
					if not des:
						frappe.db.set_value("Item",item_doc.name,"description",item_doc.name,update_modified = False)
						frappe.db.set_value("Item",item_doc.name,"item_name",item_doc.name,update_modified = False)

					frappe.db.set_value("Part Sheet Item",pm.get("name"),'part',item_doc.name)
					sku_list.append(item_doc.name)
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), "SKU Creation Error")
			else:
				frappe.msgprint(f"Item with model: {model}, category: {category}, sub-category: {sub_cat} already exists as <a href='/app/item/{existing_item[0].name}'>{existing_item[0].name}</a>.")
				frappe.db.set_value("Part Sheet Item",pm.get("name"),'part',existing_item[0].name)
	if sku_list:
		links = [f"<a href='/app/item/{sku}'>{sku}</a>" for sku in sku_list]
		frappe.msgprint("SKU Created: " + ', '.join(links))
	else:
		frappe.msgprint("No new SKUs were created based on the provided data.")


@frappe.whitelist()
def create_rfq(name):
	doc = frappe.get_doc("Evaluation Report",name)
	rfq = frappe.new_doc("Request for Quotation")
	rfq.company = doc.company
	rfq.branch = frappe.db.get_value("Job Order Data",doc.job_order_data,"branch")
	rfq.job_order_data = doc.job_order_data
	rfq.evaluation_report = doc.name
	rfq.cost_center = frappe.db.get_value("Job Order Data",doc.job_order_data,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1})
	rfq.schedule_date = add_to_date(rfq.transaction_date,days = 2)
	rfq.items=[]
	rfq.status = "Draft"
	warehouse = warehouse_based_on_branch_and_company(rfq.company,rfq.branch)
	for i in doc.get("items"):
		if i.parts_availability == "No" and i.from_scrap == 0:
			rfq.append("items",{
				"item_code":i.part,
				"item_name":i.part_name,
				"description":i.part_name,
				'model':i.model,
				"category":i.category,
				"sub_category":i.sub_category,
				"mfg":i.manufacturer,
				'serial_no':i.serial_no,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"stock_qty":1,
				"qty":i.qty,
				"schedule_date":add_to_date(rfq.transaction_date,days = 2),
				"warehouse":warehouse,
				"branch":rfq.branch,
				"parent_jo":doc.parent_jo,
				"job_order_data":doc.job_order_data,
				"cost_center":frappe.db.get_value("Job Order Data",doc.job_order_data,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1})
			})

	return rfq

@frappe.whitelist()
def warehouse_based_on_branch_and_company(company,branch):
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["actual_warehouse"])
	return warehouse
	
@frappe.whitelist()
def create_item(model,part_no,category,sub_category,package,description):
	part = frappe.db.exists("Item",{'model':model,'category':category,'sub_category':sub_category})
	if part:
		return part
	else:
		if not part_no:
			# if frappe.session.user == "purchase@tsl-me.com" or frappe.session.user == "purchase-sa1@tsl-me.com":
			item_doc = frappe.new_doc("Item")
			item_doc.naming_series = "P.######"
			item_doc.model = model
			item_doc.category = category
			item_doc.sub_category = sub_category
			item_doc.package = package
			item_doc.item_name = description
			item_doc.item_group = "Components"
			item_doc.save(ignore_permissions = True)
			if not description:
				frappe.db.set_value("Item",item_doc.name,"item_name",item_doc.name,update_modified = False)
			return item_doc.name
		else:
			frappe.msgprint("SKU already there in this row")

@frappe.whitelist()
def release_parts(name):
	try:
		doc = frappe.get_doc('Evaluation Report', name)
		if doc.parts_released:
			frappe.throw("Parts have already been released for this Evaluation Report.")
		if not doc.items:
			frappe.throw("No items found in Evaluation Report to release.")

		warehouse = warehouse_based_on_branch_and_company(doc.company, doc.branch)

		new_doc = frappe.new_doc("Stock Entry")
		new_doc.stock_entry_type = "Material Issue"
		new_doc.company = doc.company
		new_doc.from_warehouse = warehouse

		for i in doc.items:
			if i.released != 1 and i.from_scrap == 0:
				new_doc.append("items", {
					's_warehouse': warehouse,
					'item_code': i.part,
					'qty': i.qty,
					'uom': frappe.db.get_value("Item", i.part, 'stock_uom'),
					'conversion_factor': 1,
					'rate': i.price_ea,
					'job_order_data': doc.job_order_data
				})
				i.released = 1
		new_doc.job_order_data = doc.job_order_data
		new_doc.save(ignore_permissions=True)
		new_doc.submit()

		# Mark parts as released in the Evaluation Report
		# doc.parts_released = 1
		doc.save(ignore_permissions=True)

		frappe.msgprint(f"Parts Released and Material Issue is Created - <b>{new_doc.name}</b>")
		return True

	except Exception as e:
		# Catch all other exceptions
		frappe.msgprint(f"An unexpected error occurred: {str(e)}")
		return False


from frappe.utils import flt


@frappe.whitelist()
def get_release_items(docname):

	doc = frappe.get_doc("Evaluation Report", docname)

	output = []

	for row in doc.items:
		if row.from_scrap == 1:
			continue

		# REQUIRED QTY
		required_qty = flt(row.qty)
		reserved_qty = flt(row.reserved_qty)

		# ALREADY RELEASED (from Stock Entry)
		released_qty = frappe.db.sql("""
			SELECT IFNULL(SUM(sed.qty),0)
			FROM `tabStock Entry Detail` sed
			JOIN `tabStock Entry` se ON se.name = sed.parent
			WHERE se.docstatus < 2
			AND sed.item_code=%s
			AND sed.job_order_data=%s
			AND se.awaiting_parts = 1
			AND sed.evaluation_row = %s
		""", (row.part, doc.job_order_data, row.name))[0][0] or 0

		# STOCK IN WAREHOUSE
		stock_qty = frappe.db.get_value(
			"Bin",
			{"item_code": row.part, "warehouse": warehouse_list.get(doc.branch)},
			["actual_qty", "awaiting_qty"],
			as_dict=True
		)
		
		available_qty = 0
		if stock_qty:
			available_qty = (stock_qty.actual_qty or 0) - (stock_qty.awaiting_qty or 0)

		released = released_qty
		balance_to_release = max(flt(reserved_qty) - released, 0)

		output.append({
			"row_name":           row.name,
			"item_code":          row.part,
			"model":              frappe.db.get_value("Item Model", row.model, "model") or row.model,
			"required_qty":       required_qty,
			"releasable_qty":     reserved_qty,        # reservation ceiling
			"released_qty":       released,            # net released (issued − returned)
			"balance_to_release": balance_to_release,  # releasable − released, capped at 0
			"stock_qty":          available_qty,       # actual − awaiting in bin
		})

	return output

@frappe.whitelist()
def remove_reserved_qty(item,branch,qty,name):

	rq = 0
	q = frappe.db.sql("""
	SELECT 
		IFNULL(SUM(psi.qty), 0) AS qty
	FROM `tabPart Sheet Item` psi
	LEFT JOIN `tabEvaluation Report` er
		ON er.name = psi.parent
	WHERE psi.part = %s
	AND IFNULL(psi.reserve, 0) = 1
	AND psi.parent != %s
	""", (item,name), as_dict=1)

	rq = q[0].get("qty", 0)

	
	bin_exists = frappe.db.exists("Bin", {'item_code': item, 'warehouse':warehouse_list[branch]})
	if bin_exists:
		doc = frappe.get_doc("Bin", bin_exists)
		doc.custom_reserve_qty = float(rq)
		doc.save(ignore_permissions=True)





@frappe.whitelist()
def get_available_qty(item_code: str, branch: str, required_qty: float, current_doc: str = "") -> dict:
	warehouse = warehouse_list.get(branch)
	if not warehouse:
		return {"error": "No warehouse mapped for branch: {0}".format(branch)}

	required   = float(required_qty)
	bin_vals   = _get_bin_values(item_code, warehouse)
	actual_qty = bin_vals["actual_qty"]
	awaiting_qty  = bin_vals["awaiting_qty"]
	available_qty = actual_qty - awaiting_qty

	# If editing an existing doc, add back its own reservation so it
	# doesn't count against itself during the real-time check.
	own_reserved = 0.0
	if current_doc and current_doc not in ("", "__new__"):
		own_result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(reserved_qty), 0) - COALESCE(SUM(released_qty), 0)
			FROM   `tabEvaluation Stock Reservation`
			WHERE  evaluation_report = %(doc)s
			AND    item_code         = %(item_code)s
			AND    warehouse         = %(warehouse)s
			AND    status            = 'Active'
			""",
			{"doc": current_doc, "item_code": item_code, "warehouse": warehouse},
		)
		own_reserved = flt(own_result[0][0] if own_result else 0)

	total_eval_reserved = bin_vals["custom_reserve_qty"]
	free_qty    = max(available_qty - total_eval_reserved + own_reserved, 0)

	can_reserve = min(required, free_qty)
	shortage    = required - can_reserve

	return {
		"actual_qty":              actual_qty,
		"custom_reserve_qty": total_eval_reserved,
		"own_reserved":            own_reserved,
		"free_qty":                free_qty,
		"can_reserve":             can_reserve,
		"shortage":                shortage,
		"warehouse":               warehouse,
		"label":                   _availability_label(required, can_reserve),
	}


# ---------------------------------------------------------------------------
# Whitelisted API – Lab team releases parts
# ---------------------------------------------------------------------------

@frappe.whitelist()
def release_reservations(evaluation_report: str) -> str:
	reservations = frappe.get_all(
		"Evaluation Stock Reservation",
		filters={"evaluation_report": evaluation_report, "status": "Active"},
		fields=["name", "item_code", "warehouse"],
	)
	for r in reservations:
		frappe.db.set_value(
			"Evaluation Stock Reservation",
			r["name"],
			{
				"status":        "Released",
				"released_date": now_datetime(),
				"notes":         "Parts issued to technician.",
			},
		)
		_recompute_bin_reserved(r["item_code"], r["warehouse"])

	frappe.db.commit()
	return _("Reservations released successfully.")

def cleanup_reservations(item_code=None, warehouse=None):
	"""One-time cleanup: cancel orphan/duplicate Active reservations, rebuild Bin."""
	filters = {"status": "Active"}
	if item_code:
		filters["item_code"] = item_code

	rows = frappe.get_all(
		"Evaluation Stock Reservation",
		filters=filters,
		fields=["name", "evaluation_report", "child_row_name",
		        "item_code", "warehouse", "reserved_qty", "released_qty", "creation"],
		order_by="creation desc",
	)

	seen = set()
	touched_bins = set()

	for r in rows:
		cancel_reason = None

		# Orphan checks
		if not r.child_row_name:
			cancel_reason = "Cleanup: no child_row_name (pre-migration record)."
		elif not frappe.db.exists("Part Sheet Item", r.child_row_name):
			cancel_reason = "Cleanup: child row no longer exists."
		elif not frappe.db.exists("Evaluation Report", r.evaluation_report):
			cancel_reason = "Cleanup: parent Evaluation Report no longer exists."
		# Duplicate check — keep the newest per (report, row), cancel the rest
		elif (r.evaluation_report, r.child_row_name) in seen:
			cancel_reason = "Cleanup: duplicate reservation for the same row."
		else:
			seen.add((r.evaluation_report, r.child_row_name))

		if cancel_reason:
			if flt(r.released_qty) > 0:
				# parts already issued — close it, don't erase history
				frappe.db.set_value("Evaluation Stock Reservation", r.name, {
					"status": "Released",
					"reserved_qty": flt(r.released_qty),
					"notes": cancel_reason,
				})
			else:
				frappe.db.set_value("Evaluation Stock Reservation", r.name, {
					"status": "Cancelled",
					"released_date": now_datetime(),
					"notes": cancel_reason,
				})
			print("Fixed:", r.name, "-", cancel_reason)

		touched_bins.add((r.item_code, r.warehouse))

	for ic, wh in touched_bins:
		_recompute_bin_reserved(ic, wh)

	frappe.db.commit()
	print("Done.")




@frappe.whitelist()
def unreserve_qty(evaluation_report: str, child_row_name: str, qty: float) -> dict:
	"""
	Manually pull back part of a reservation (e.g. to prioritize an
	approved Evaluation Report over an unapproved one).

	Only the un-issued portion (reserved_qty − released_qty) can be
	unreserved. The freed qty goes back to the Bin's free stock so
	another report can reserve it on its next save.
	"""
	qty = flt(qty)
	if qty <= 0:
		frappe.throw(_("Qty to unreserve must be greater than zero."))

	res = frappe.db.get_value(
		"Evaluation Stock Reservation",
		{
			"evaluation_report": evaluation_report,
			"child_row_name": child_row_name,
			"status": "Active",
		},
		["name", "item_code", "warehouse", "qty", "reserved_qty", "released_qty"],
		as_dict=True,
	)
	if not res:
		frappe.throw(_("No active reservation found for this row."))

	unissued = flt(res.reserved_qty) - flt(res.released_qty)
	if qty > unissued:
		frappe.throw(
			_("Cannot unreserve {0}. Only {1} is un-issued "
			  "(reserved {2} − released {3}).").format(
				qty, unissued, res.reserved_qty, res.released_qty
			)
		)

	new_reserved = flt(res.reserved_qty) - qty
	new_status   = _resolve_status(new_reserved, flt(res.released_qty))

	frappe.db.set_value(
		"Evaluation Stock Reservation",
		res.name,
		{
			"reserved_qty": new_reserved,
			"status":       new_status,
			"notes": _("Manually unreserved {0} by {1} on {2}.").format(
				qty, frappe.session.user, now_datetime()
			),
		},
	)
	_recompute_bin_reserved(res.item_code, res.warehouse)

	# Update the child row's display fields so the report shows the truth
	row_required = flt(frappe.db.get_value("Part Sheet Item", child_row_name, "qty"))
	frappe.db.set_value(
		"Part Sheet Item",
		child_row_name,
		{
			"reserved_qty":       new_reserved,
			"shortage_qty":       max(row_required - new_reserved, 0),
			"parts_availability": _availability_label(row_required, new_reserved),
		},
		update_modified=False,
	)

	return {
		"reserved_qty": new_reserved,
		"freed_qty":    qty,
		"status":       new_status,
		"message": _('Unreserved {0}. Freed stock is now available.').format(qty),
	}


@frappe.whitelist()
def reserve_qty(evaluation_report: str, child_row_name: str, qty: float = None) -> dict:
	"""
	Manually reserve (top-up) stock for one row without re-syncing the
	whole document. Reserves min(requested, remaining need, free stock).

	If qty is not given, reserves as much of the remaining need as
	free stock allows.
	"""
	doc = frappe.get_doc("Evaluation Report", evaluation_report)

	warehouse = warehouse_list.get(doc.branch)
	if not warehouse:
		frappe.throw(_("No warehouse mapped for branch <b>{0}</b>.").format(doc.branch))

	row = None
	for r in doc.items:
		if r.name == child_row_name:
			row = r
			break
	if not row:
		frappe.throw(_("Row not found on this Evaluation Report."))

	required = flt(row.qty)

	# Existing reservation (Active or Released — a fully released one
	# gets reactivated by the top-up)
	res = frappe.db.get_value(
		"Evaluation Stock Reservation",
		{
			"evaluation_report": evaluation_report,
			"child_row_name": child_row_name,
			"status": ["in", ["Active", "Released"]],
		},
		["name", "item_code", "warehouse", "qty", "reserved_qty", "released_qty", "status"],
		as_dict=True,
	)

	current_reserved = flt(res.reserved_qty) if res else 0.0
	released         = flt(res.released_qty) if res else 0.0

	remaining_need = max(required - current_reserved, 0)
	if remaining_need <= 0:
		frappe.throw(
			_("Nothing to reserve — already reserved {0} of {1}.").format(
				current_reserved, required
			)
		)

	# ── Free stock, same formula as _sync_reservations ────────────────────
	bin_vals      = _get_bin_values(row.part, warehouse)
	available_qty = bin_vals["actual_qty"] - bin_vals["awaiting_qty"]

	own_net = flt(frappe.db.sql(
		"""
		SELECT COALESCE(SUM(reserved_qty), 0) - COALESCE(SUM(released_qty), 0)
		FROM   `tabEvaluation Stock Reservation`
		WHERE  evaluation_report = %(doc)s
		AND    child_row_name    = %(row)s
		AND    item_code         = %(item)s
		AND    warehouse         = %(wh)s
		AND    status            = 'Active'
		""",
		{"doc": evaluation_report, "row": child_row_name,
		 "item": row.part, "wh": warehouse},
	)[0][0] or 0)

	free_qty = max(available_qty - bin_vals["custom_reserve_qty"] + own_net - own_net, 0)
	# own_net cancels out here on purpose: the Bin already excludes this
	# row's net hold, and a TOP-UP must only consume stock nobody holds.
	# Written explicitly for clarity:
	free_qty = max(available_qty - bin_vals["custom_reserve_qty"], 0)

	if free_qty <= 0:
		frappe.throw(_("No free stock available in {0}.").format(warehouse))

	requested = flt(qty) if qty else remaining_need
	if requested > remaining_need:
		frappe.throw(
			_("Cannot reserve {0} — remaining need is only {1} "
			  "(required {2} − already reserved {3}).").format(
				requested, remaining_need, required, current_reserved
			)
		)

	to_reserve   = min(requested, free_qty)
	new_reserved = current_reserved + to_reserve
	new_status   = _resolve_status(new_reserved, released)

	if res:
		_update_reservation(
			res.name,
			item_code=row.part,
			warehouse=warehouse,
			qty=required,
			reserved_qty=new_reserved,
			status=new_status,
			notes=_("Manually reserved {0} by {1} on {2}.").format(
				to_reserve, frappe.session.user, now_datetime()
			),
		)
	else:
		_create_reservation(
			evaluation_report=evaluation_report,
			item_code=row.part,
			warehouse=warehouse,
			qty=required,
			reserved_qty=to_reserve,
			child_row_name=child_row_name,
			technician=doc.technician,
		)

	# Update child row display fields
	frappe.db.set_value(
		"Part Sheet Item",
		child_row_name,
		{
			"reserved_qty":       new_reserved,
			"shortage_qty":       max(required - new_reserved, 0),
			"parts_availability": _availability_label(required, new_reserved),
		},
		update_modified=False,
	)

	msg = _("Reserved {0}.").format(to_reserve)
	if to_reserve < requested:
		msg += _(" (Only {0} free in stock — requested {1}.)").format(free_qty, requested)

	return {
		"reserved_now": to_reserve,
		"total_reserved": new_reserved,
		"shortage": max(required - new_reserved, 0),
		"status": new_status,
		"message": msg,
	}


import json
import frappe
from frappe import _


# All branches are always displayed, regardless of the company passed in.
# (warehouse_name, branch_label, company_label)
ALL_WAREHOUSES = [
	("Kuwait - CT-K", "KUWAIT"),
	("Dubai - CT-UAE",  "DUBAI"),
	("Riyadh - BM", "RIYADH"),
	("Jeddah - BM", "JEDDAH"),
]

# ---------- color palettes ----------
THEMES = {
	"light": {
		"wrap_bg":       "transparent",
		"title":         "#0380AE",
		"table_border":  "#e3e8ef",
		"th_border_b":   "#0380AE",
		"sub_bg":        "#E5F4FB",
		"sub_fg":        "#0574A0",
		"sub_border":    "#d3e9f5",
		"td_fg":         "#3b4a5f",
		"td_border":     "#eef1f6",
		"row_even":      "#ffffff",
		"row_odd":       "#fafbfd",
		"legend":        "#9aa5b1",
		"pill_zero":     ("#f6f8fa", "#9aa5b1"),
		"pill_stock":    ("#eef9f1", "#2e8b57"),
		"pill_reserved": ("#fdf6e3", "#b08a2e"),
		"detail_bg":     "#fffdf4",
		"detail_border": "#f0e6c8",
		"detail_head":   "#8a6d1a",
		"link":          "#0574A0",
	},
	"dark": {
		"wrap_bg":       "#1b212b",
		"title":         "#5BC4EE",
		"table_border":  "#3a4354",
		"th_border_b":   "#0380AE",
		"sub_bg":        "#14384c",
		"sub_fg":        "#8fd0ef",
		"sub_border":    "#1e4a63",
		"td_fg":         "#d7dee8",
		"td_border":     "#2b3342",
		"row_even":      "#232a36",
		"row_odd":       "#1d232d",
		"legend":        "#7b8698",
		"pill_zero":     ("#2a3140", "#7b8698"),
		"pill_stock":    ("#1f3d2c", "#6fd39a"),
		"pill_reserved": ("#3d3420", "#e3c06a"),
		"detail_bg":     "#2b2718",
		"detail_border": "#4a4128",
		"detail_head":   "#e3c06a",
		"link":          "#8fd0ef",
	},
}


def _styles(t):
	"""Build the inline-style strings for the given theme palette."""
	table = (
		"width:100%;border-collapse:separate;border-spacing:0;"
		"font-family:Arial,Helvetica,sans-serif;font-size:12px;"
		"border:1px solid {table_border};border-radius:8px;overflow:hidden;"
	).format(**t)
	# Header keeps the blue gradient in both themes - it reads well on dark too.
	th = (
		"padding:9px 10px;font-size:11px;font-weight:600;letter-spacing:.4px;"
		"background:#0791C4;"  # solid fallback for renderers without gradient support
		"background:linear-gradient(90deg,#0C9CDA 0%,#0380AE 100%);"
		"color:#ffffff;text-align:center;"
		"border-bottom:1px solid {th_border_b};border-right:1px solid rgba(255,255,255,.25);"
		"white-space:nowrap;"
	).format(**t)
	th_sub = (
		"padding:6px 8px;font-size:10px;font-weight:600;letter-spacing:.3px;"
		"background:{sub_bg};color:{sub_fg};text-align:center;"
		"border-bottom:1px solid {sub_border};border-right:1px solid {sub_border};"
		"white-space:nowrap;"
	).format(**t)
	td = (
		"padding:8px 10px;text-align:center;color:{td_fg};"
		"border-bottom:1px solid {td_border};border-right:1px solid {td_border};"
	).format(**t)
	return table, th, th_sub, td, td + "text-align:left;font-weight:600;"


def _qty(value, theme, reserved=False, clickable_target=None, count=0):
	"""
	Colored pill: green for stock, amber for reserved, muted for zero.
	When clickable_target is given (reserved qty with active reservations),
	the pill toggles the breakdown row with that DOM id.
	"""
	value = frappe.utils.flt(value)
	if value <= 0:
		bg, fg = theme["pill_zero"]
	elif reserved:
		bg, fg = theme["pill_reserved"]
	else:
		bg, fg = theme["pill_stock"]

	base = (
		"display:inline-block;min-width:36px;padding:2px 9px;"
		"border-radius:12px;font-weight:600;background:%s;color:%s;" % (bg, fg)
	)

	if clickable_target:
		# Look up the breakdown row RELATIVE to the clicked pill (scoped to its
		# own table). A global getElementById would find the stale copy inside
		# a previously-closed-but-not-destroyed Frappe dialog and toggle the
		# invisible one instead.
		onclick = (
			"var e=this.closest('table').querySelector('tr[data-esr=%s]');"
			"if(!e)return;"
			"var open=e.style.display!=='none';"
			"e.style.display=open?'none':'table-row';"
			"this.querySelector('.esr-caret').innerHTML=open?'\\u25BE':'\\u25B4';"
			% clickable_target
		)
		return (
			'<span onclick="%s" title="%s" '
			'style="%scursor:pointer;border:1px dashed %s;">'
			'%s <span class="esr-caret" style="font-size:9px;">&#9662;</span>'
			'</span>'
			% (onclick, _("Click to view active reservations ({0})").format(count),
			   base, fg, frappe.utils.flt(value, 2))
		)

	return '<span style="%s">%s</span>' % (base, frappe.utils.flt(value, 2))


def _get_active_reservations(skus, wh_names):
	"""
	Active Evaluation Stock Reservations for all items/warehouses in one query,
	grouped by (item_code, warehouse).
	"""
	if not skus:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT name, evaluation_report, child_row_name, item_code, warehouse,
		       technician, qty AS required_qty, reserved_qty, released_qty,
		       (reserved_qty - released_qty) AS net_qty,
		       (qty - reserved_qty) AS remaining_qty,
		       modified
		FROM `tabEvaluation Stock Reservation`
		WHERE status = 'Active'
		  AND item_code IN %(skus)s
		  AND warehouse IN %(whs)s
		ORDER BY modified DESC
		""",
		{"skus": tuple(skus), "whs": tuple(wh_names)},
		as_dict=True,
	)
	grouped = {}
	for r in rows:
		grouped.setdefault((r.item_code, r.warehouse), []).append(r)
	return grouped


def _breakdown_row(dom_id, sku, branch_label, reservations, total_cols, t):
	"""
	Hidden full-width row listing the Active reservations behind one
	reserved-qty pill. Toggled by clicking the pill.
	"""
	esc = frappe.utils.escape_html
	cell = (
		"padding:5px 8px;font-size:11px;text-align:center;color:%s;"
		"border-bottom:1px solid %s;" % (t["td_fg"], t["detail_border"])
	)
	head = (
		"padding:5px 8px;font-size:10px;font-weight:600;letter-spacing:.3px;"
		"text-align:center;color:%s;border-bottom:1px solid %s;"
		% (t["detail_head"], t["detail_border"])
	)

	inner = [
		'<div style="padding:8px 10px;">',
		'<div style="font-size:11px;font-weight:600;color:%s;margin-bottom:6px;">'
		'%s &mdash; %s : %s</div>'
		% (t["detail_head"], _("ACTIVE RESERVATIONS"), esc(sku), esc(branch_label)),
		'<table style="width:100%;border-collapse:collapse;">',
		"<tr>"
		'<th style="%s;text-align:left;">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s;text-align:left;">%s</th>'
		'<th style="%s">%s</th>'
		'<th style="%s">%s</th>'
		"</tr>"
		% (head, _("Evaluation Report"), head, _("Required"), head, _("Reserved"),
		   head, _("Released"), head, _("Net"), head, _("Remaining"),
		   head, _("Technician"), head, _("Last Updated"), head, _("Actions")),
	]

	btn = (
		"display:inline-block;padding:2px 8px;margin:0 2px;border-radius:6px;"
		"font-size:10px;font-weight:600;cursor:pointer;border:1px solid %s;"
		"background:transparent;color:%s;"
	)

	total_net = 0.0
	for r in reservations:
		total_net += frappe.utils.flt(r.net_qty)
		net = frappe.utils.flt(r.net_qty)
		required = frappe.utils.flt(r.required_qty)
		remaining = max(frappe.utils.flt(r.remaining_qty), 0)
		attrs = (
			'data-report="%s" data-row="%s" data-item="%s" data-warehouse="%s" '
			'data-net="%s" data-required="%s" data-remaining="%s"'
			% (esc(r.evaluation_report), esc(r.child_row_name or ""),
			   esc(r.item_code), esc(r.warehouse), net, required, remaining)
		)
		actions = ""
		if remaining > 0:
			actions += (
				'<button type="button" class="esr-reserve" %s style="%s" title="%s">+ %s</button>'
				% (attrs, btn % (t["pill_stock"][1], t["pill_stock"][1]),
				   _("Reserve more (remaining need: {0})").format(remaining), _("Reserve"))
			)
		if net > 0:
			actions += (
				'<button type="button" class="esr-release" %s style="%s" title="%s">&minus; %s</button>'
				% (attrs, btn % (t["pill_reserved"][1], t["pill_reserved"][1]),
				   _("Release / unreserve"), _("Unreserve"))
			)
		remaining_style = "font-weight:600;"
		if remaining > 0:
			remaining_style += "color:%s;" % t["pill_reserved"][1]  # still short - highlight
		inner.append(
			"<tr>"
			'<td style="%s;text-align:left;">'
			'<a href="/app/evaluation-report/%s" target="_blank" '
			'style="color:%s;font-weight:600;">%s</a></td>'
			'<td style="%s">%s</td>'
			'<td style="%s">%s</td>'
			'<td style="%s">%s</td>'
			'<td style="%s"><b>%s</b></td>'
			'<td style="%s"><span style="%s">%s</span></td>'
			'<td style="%s;text-align:left;">%s</td>'
			'<td style="%s">%s</td>'
			'<td style="%s;white-space:nowrap;">%s</td>'
			"</tr>"
			% (
				cell, esc(r.evaluation_report), t["link"], esc(r.evaluation_report),
				cell, frappe.utils.flt(required, 2),
				cell, frappe.utils.flt(r.reserved_qty, 2),
				cell, frappe.utils.flt(r.released_qty, 2),
				cell, frappe.utils.flt(r.net_qty, 2),
				cell, remaining_style, frappe.utils.flt(remaining, 2),
				cell, esc(r.technician or ""),
				cell, frappe.utils.format_datetime(r.modified, "dd-MM-yyyy HH:mm"),
				cell, actions or "&mdash;",
			)
		)

	inner.append(
		'<tr><td style="%s;text-align:left;font-weight:600;">%s</td>'
		'<td style="%s"></td><td style="%s"></td><td style="%s"></td>'
		'<td style="%s"><b>%s</b></td>'
		'<td style="%s"></td><td style="%s"></td><td style="%s"></td>'
		'<td style="%s"></td></tr>'
		% (cell, _("Total Net Reserved"), cell, cell, cell,
		   cell, frappe.utils.flt(total_net, 2), cell, cell, cell, cell)
	)
	inner.append("</table></div>")

	return (
		'<tr data-esr="%s" style="display:none;background:%s;">'
		'<td colspan="%s" style="border-bottom:1px solid %s;padding:0;">%s</td>'
		"</tr>"
		% (dom_id, t["detail_bg"], total_cols, t["detail_border"], "".join(inner))
	)


@frappe.whitelist()  # Stock against the Parts requested in initial Evaluation
def get_reserved_stock_detail(item_details, company=None, theme="light"):
	item_details = json.loads(item_details or "[]")
	if not item_details:
		return ""

	t = THEMES.get(theme) or THEMES["light"]
	TABLE, TH, TH_SUB, TD, TD_LEFT = _styles(t)

	wh_names = tuple(w[0] for w in ALL_WAREHOUSES)
	total_cols = 2 + len(ALL_WAREHOUSES) * 2  # SKU + Part No + (Avail, Reserved) per branch

	skus = [i.get("sku") for i in item_details if i.get("sku")]
	reservations = _get_active_reservations(skus, wh_names)

	# Unique per render, so ids never collide with a previous popup's leftover DOM
	render_id = frappe.generate_hash(length=8)

	html = [
		'<div style="font-family:Arial,Helvetica,sans-serif;background:%s;'
		'padding:%s;border-radius:10px;">'
		% (t["wrap_bg"], "12px" if theme == "dark" else "0"),
		'<h4 style="text-align:center;margin:4px 0 12px;letter-spacing:1.5px;'
		'color:%s;font-weight:600;">STOCK DETAILS</h4>' % t["title"],
		'<table style="%s">' % TABLE,
	]

	# ---- header: branch (with company) on top, Available / Reserved beneath ----
	html.append("<tr>")
	html.append('<th rowspan="2" style="%s">SKU</th>' % TH)
	html.append('<th rowspan="2" style="%s">PART NUMBER</th>' % TH)
	for _wh, branch in ALL_WAREHOUSES:
		html.append(
			'<th colspan="2" style="%s">%s<br>'
			% (TH, branch)
		)
	html.append("</tr>")

	html.append("<tr>")
	for _wh in ALL_WAREHOUSES:
		html.append('<th style="%s">AVAILABLE</th>' % TH_SUB)
		html.append('<th style="%s">RESERVED</th>' % TH_SUB)
	html.append("</tr>")

	# ---- rows ----
	for idx, item in enumerate(item_details):
		sku = item.get("sku")
		part_number = frappe.db.get_value("Item Model", item.get("model"), "model") or ""

		# One query per item covering every branch
		bins = {}
		for row in frappe.db.sql(
			"""
			SELECT warehouse,
			       (actual_qty - awaiting_qty) AS available_qty,
			       custom_reserve_qty AS reserved_qty
			FROM `tabBin`
			WHERE item_code = %s AND warehouse IN %s
			""",
			(sku, wh_names),
			as_dict=True,
		):
			bins[row.warehouse] = row

		row_bg = t["row_even"] if idx % 2 == 0 else t["row_odd"]
		html.append('<tr style="background:%s;">' % row_bg)
		html.append('<td style="%s">%s</td>' % (TD_LEFT, frappe.utils.escape_html(sku or "")))
		html.append('<td style="%s">%s</td>' % (TD_LEFT, frappe.utils.escape_html(str(part_number))))

		breakdown_rows = []  # hidden rows appended right after this item's row

		for wh_idx, (wh_name, branch) in enumerate(ALL_WAREHOUSES):
			row = bins.get(wh_name)
			available = frappe.utils.flt(row.available_qty) if row else 0
			reserved = frappe.utils.flt(row.reserved_qty) if row else 0

			html.append('<td style="%s">%s</td>' % (TD, _qty(available, t)))

			res_list = reservations.get((sku, wh_name)) or []
			if reserved > 0 and res_list:
				dom_id = "esr-%s-%s-%s" % (render_id, idx, wh_idx)
				html.append(
					'<td style="%s">%s</td>'
					% (TD, _qty(reserved, t, reserved=True,
					            clickable_target=dom_id, count=len(res_list)))
				)
				breakdown_rows.append(
					_breakdown_row(dom_id, sku, branch, res_list, total_cols, t)
				)
			else:
				html.append('<td style="%s">%s</td>' % (TD, _qty(reserved, t, reserved=True)))

		html.append("</tr>")
		html.extend(breakdown_rows)

	html.append("</table>")

	# ---- small legend ----
	html.append(
		'<div style="margin-top:8px;font-size:11px;color:%s;">'
		"Available = Actual Qty &minus; Awaiting Qty<br>"
		"Reserved = Qty committed against Evaluation Report "
		"&nbsp;&bull;&nbsp; Click a reserved value to see which "
		"Evaluation Reports are holding it"
		"</div>" % t["legend"]
	)
	html.append("</div>")

	return "".join(html)



def _reserve_row(doc, warehouse: str, row, qty: float) -> dict:
	"""Core top-up logic for one row. Returns a result dict, raises nothing
	fatal — problems are returned as 'error' so bulk processing continues."""
	required = flt(row.qty)

	res = frappe.db.get_value(
		"Evaluation Stock Reservation",
		{
			"evaluation_report": doc.name,
			"child_row_name": row.name,
			"status": ["in", ["Active", "Released"]],
		},
		["name", "item_code", "warehouse", "qty", "reserved_qty", "released_qty", "status"],
		as_dict=True,
	)

	current_reserved = flt(res.reserved_qty) if res else 0.0
	released         = flt(res.released_qty) if res else 0.0
	remaining_need   = max(required - current_reserved, 0)

	if remaining_need <= 0:
		return {"row_name": row.name, "item_code": row.part, "reserved_now": 0,
				"error": _("Already fully reserved ({0} of {1}).").format(current_reserved, required)}

	requested = flt(qty)
	if requested > remaining_need:
		requested = remaining_need  # clamp silently in bulk mode

	# Free stock for a TOP-UP: only stock nobody holds
	bin_vals      = _get_bin_values(row.part, warehouse)
	available_qty = bin_vals["actual_qty"] - bin_vals["awaiting_qty"]
	free_qty      = max(available_qty - bin_vals["custom_reserve_qty"], 0)

	if free_qty <= 0:
		return {"row_name": row.name, "item_code": row.part, "reserved_now": 0,
				"error": _("No free stock in {0}.").format(warehouse)}

	to_reserve   = min(requested, free_qty)
	new_reserved = current_reserved + to_reserve
	new_status   = _resolve_status(new_reserved, released)

	if res:
		_update_reservation(
			res.name, item_code=row.part, warehouse=warehouse,
			qty=required, reserved_qty=new_reserved, status=new_status,
			notes=_("Manually reserved {0} by {1} on {2}.").format(
				to_reserve, frappe.session.user, now_datetime()),
		)
	else:
		_create_reservation(
			evaluation_report=doc.name, item_code=row.part, warehouse=warehouse,
			qty=required, reserved_qty=to_reserve,
			child_row_name=row.name, technician=doc.technician,
		)

	frappe.db.set_value(
		"Part Sheet Item", row.name,
		{
			"reserved_qty":       new_reserved,
			"shortage_qty":       max(required - new_reserved, 0),
			"parts_availability": _availability_label(required, new_reserved),
		},
		update_modified=False,
	)

	return {"row_name": row.name, "item_code": row.part,
			"reserved_now": to_reserve, "total_reserved": new_reserved,
			"shortage": max(required - new_reserved, 0)}


def _unreserve_row(doc, row, qty: float) -> dict:
	"""Core pull-back logic for one row."""
	res = frappe.db.get_value(
		"Evaluation Stock Reservation",
		{
			"evaluation_report": doc.name,
			"child_row_name": row.name,
			"status": "Active",
		},
		["name", "item_code", "warehouse", "qty", "reserved_qty", "released_qty"],
		as_dict=True,
	)
	if not res:
		return {"row_name": row.name, "item_code": row.part, "unreserved_now": 0,
				"error": _("No active reservation.")}

	unissued  = flt(res.reserved_qty) - flt(res.released_qty)
	requested = min(flt(qty), unissued)  # clamp to un-issued in bulk mode

	if requested <= 0:
		return {"row_name": row.name, "item_code": row.part, "unreserved_now": 0,
				"error": _("Nothing un-issued to unreserve (reserved {0}, released {1}).").format(
					res.reserved_qty, res.released_qty)}

	new_reserved = flt(res.reserved_qty) - requested
	new_status   = _resolve_status(new_reserved, flt(res.released_qty))

	frappe.db.set_value(
		"Evaluation Stock Reservation", res.name,
		{
			"reserved_qty": new_reserved,
			"status":       new_status,
			"notes": _("Manually unreserved {0} by {1} on {2}.").format(
				requested, frappe.session.user, now_datetime()),
		},
	)
	_recompute_bin_reserved(res.item_code, res.warehouse)

	required = flt(row.qty)
	frappe.db.set_value(
		"Part Sheet Item", row.name,
		{
			"reserved_qty":       new_reserved,
			"shortage_qty":       max(required - new_reserved, 0),
			"parts_availability": _availability_label(required, new_reserved),
		},
		update_modified=False,
	)

	return {"row_name": row.name, "item_code": row.part,
			"unreserved_now": requested, "total_reserved": new_reserved}


@frappe.whitelist()
def get_reservation_rows(docname):
	"""Feed for the reserve/unreserve dialogs — one entry per part row."""
	doc = frappe.get_doc("Evaluation Report", docname)
	warehouse = warehouse_list.get(doc.branch)

	output = []
	for row in doc.items:
		if not row.part or row.from_scrap == 1:
			continue

		res = frappe.db.get_value(
			"Evaluation Stock Reservation",
			{
				"evaluation_report": doc.name,
				"child_row_name": row.name,
				"status": ["in", ["Active", "Released"]],
			},
			["reserved_qty", "released_qty", "status"],
			as_dict=True,
		) or frappe._dict(reserved_qty=0, released_qty=0, status="")

		bin_vals      = _get_bin_values(row.part, warehouse)
		available_qty = bin_vals["actual_qty"] - bin_vals["awaiting_qty"]
		free_qty      = max(available_qty - bin_vals["custom_reserve_qty"], 0)

		reserved  = flt(res.reserved_qty)
		released  = flt(res.released_qty)
		required  = flt(row.qty)

		output.append({
			"row_name":       row.name,
			"idx":            row.idx,
			"item_code":      row.part,
			"model":          frappe.db.get_value("Item Model", row.model, "model") or row.model or "",
			"required_qty":   required,
			"reserved_qty":   reserved,
			"released_qty":   released,
			"unissued_qty":   max(reserved - released, 0),          # max unreservable
			"remaining_need": max(required - reserved, 0),           # max reservable (need side)
			"free_qty":       free_qty,                              # stock side
			"status":         (res.status or "").strip(),
		})
	return output


@frappe.whitelist()
def bulk_reserve_qty(evaluation_report: str, items):
	items = frappe.parse_json(items)
	doc   = frappe.get_doc("Evaluation Report", evaluation_report)

	warehouse = warehouse_list.get(doc.branch)
	if not warehouse:
		frappe.throw(_("No warehouse mapped for branch <b>{0}</b>.").format(doc.branch))

	row_map = {r.name: r for r in doc.items}
	results, errors = [], []

	for item in items:
		if flt(item.get("qty")) <= 0:
			continue
		row = row_map.get(item.get("row_name"))
		if not row:
			continue
		# Sequential processing: each _reserve_row recomputes the Bin,
		# so the next row sees the reduced free stock.
		r = _reserve_row(doc, warehouse, row, flt(item["qty"]))
		if r.get("error"):
			errors.append("Row {0} ({1}): {2}".format(row.idx, row.part, r["error"]))
		elif r.get("reserved_now"):
			results.append("Row {0} ({1}): reserved {2}".format(row.idx, row.part, r["reserved_now"]))

	return {"results": results, "errors": errors}


@frappe.whitelist()
def bulk_unreserve_qty(evaluation_report: str, items):
	items = frappe.parse_json(items)
	doc   = frappe.get_doc("Evaluation Report", evaluation_report)

	row_map = {r.name: r for r in doc.items}
	results, errors = [], []

	for item in items:
		if flt(item.get("qty")) <= 0:
			continue
		row = row_map.get(item.get("row_name"))
		if not row:
			continue
		r = _unreserve_row(doc, row, flt(item["qty"]))
		if r.get("error"):
			errors.append("Row {0} ({1}): {2}".format(row.idx, row.part, r["error"]))
		elif r.get("unreserved_now"):
			results.append("Row {0} ({1}): unreserved {2}".format(row.idx, row.part, r["unreserved_now"]))

	return {"results": results, "errors": errors}
def update_reservation_status():
	"""
	Recompute the status of all Active reservations based on their reserved
	and released quantities. This is a safety net in case something went
	wrong and a reservation got stuck in the wrong state.
	"""
	reservations = frappe.get_all(
		"Evaluation Stock Reservation",
		filters={"status": "Active"},
		fields=["name", "qty", "reserved_qty", "released_qty"],
	)

	for res in reservations:
		new_status = _resolve_status(flt(res.reserved_qty), flt(res.released_qty))
		if new_status != "Active":
			frappe.db.set_value("Evaluation Stock Reservation", res.name, "status", new_status)


def schedule_update_reservation_status():
	"""Schedule the status update to run every hour."""
	job = frappe.db.exists('Scheduled Job Type', 'evaluation_report.update_reservation_status')
	if not job:
		sjt1 = frappe.new_doc("Scheduled Job Type")  
		sjt1.update({
			"method" : 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.update_reservation_status',
			"frequency" : 'Hourly'
		})
		sjt1.save(ignore_permissions=True)

@frappe.whitelist()
def create_stock_entry(evaluation, items):

	doc = frappe.get_doc("Evaluation Report", evaluation)
	items = frappe.parse_json(items)

	# Branch Mapping

	branch_map = {
		"Kuwait": ("Kuwait - CT-K", "Kuwait - Repair - CT-K"),
		"Riyadh": ("Riyadh - BM", "Riyadh - Repair - BM"),
		"Jeddah": ("Jeddah - BM", "Jeddah - Repair - BM"),
		"Dubai": ("Dubai - CT-UAE", "Dubai - Repair - CT-UAE"),
	}

	war, cc = branch_map.get(doc.branch, ("", ""))

	if not war:
		frappe.throw("Warehouse not configured for this branch")

	new_doc = frappe.new_doc("Stock Entry")
	new_doc.company = doc.company
	new_doc.stock_entry_type = "Material Issue"
	new_doc.from_warehouse = war

	for item in items:
		if item.get("qty", 0) <= 0:
			continue

		new_doc.append("items", {
			"s_warehouse": war,
			"item_code": item["item_code"],
			"qty": item["qty"],
			"serial_no": item.get("serial_no", ""),
			"uom": item.get("uom"),
			"stock_uom": item.get("uom"),
			"cost_center": cc,
			"job_order_data": doc.job_order_data,
			"conversion_factor": 1,
			"evaluation_row":item.get("row_name")
			# "allow_zero_valuation_rate": 1
		})


	new_doc.awaiting_parts = 1
	new_doc.save(ignore_permissions=True)
	# new_doc.submit()

	frappe.msgprint("Parts Released and Material Issue is Created")
	return new_doc.name


def migrate_old_releases():
	# find old entries without row reference
	old_rows = frappe.db.sql("""
		SELECT 
			sed.parent,
			sed.name, 
			sed.item_code,
			sed.qty, 
			sed.job_order_data
		FROM `tabStock Entry Detail` sed
		JOIN `tabStock Entry` se ON se.name = sed.parent
		WHERE se.docstatus = 1
			# AND se.awaiting_parts = 1
			AND se.stock_entry_type = 'Material Issue'
			AND IFNULL(sed.job_order_data,'') != ''
			AND IFNULL(sed.evaluation_row,'') = ''
			ORDER BY se.posting_date, se.creation
	""", as_dict=True)

	for sed in old_rows:
		print(sed)

		remaining_qty = flt(sed.qty)
		eval_list = frappe.db.get_all("Evaluation Report",{'job_order_data':sed.job_order_data},'name')
		for eval in eval_list:
			# get evaluation rows FIFO
			eval_rows = frappe.db.sql("""
				SELECT parent,name, part, qty
				FROM `tabPart Sheet Item`
				WHERE parent=%s
				AND parenttype = 'Evaluation Report'
				AND part=%s
				ORDER BY idx
			""", (eval.name, sed.item_code), as_dict=True)
			if eval_rows:
				print(eval_rows)

			for row in eval_rows:

				if remaining_qty <= 0:
					break

				# already allocated qty for this row
				allocated = frappe.db.sql("""
					SELECT IFNULL(SUM(qty),0)
					FROM `tabStock Entry Detail`
					WHERE evaluation_row=%s
				""", row.name)[0][0] or 0

				balance = flt(row.qty) - flt(allocated)

				if balance <= 0:
					continue

				allocate = min(balance, remaining_qty)
				print(allocate)

				# update stock entry row
				frappe.db.set_value(
					"Stock Entry Detail",
					sed.name,
					"evaluation_row",
					row.name
				)

				remaining_qty -= allocate
			frappe.db.commit()
		print("Migration completed")


@frappe.whitelist()
def create_technical_report(name):
	doc = frappe.get_doc("Job Order Data", name)
	new_doc = frappe.new_doc("Technical Report")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.customer_address = frappe.db.get_value("Customer", doc.customer, "customer_primary_address")
	new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
	new_doc.sales_person = doc.sales_person
	new_doc.document_type = doc.doctype
	new_doc.document_reference = doc.name
	new_doc.branch = doc.branch
	for item in doc.material_list:
		new_doc.manufacturer = item.mfg
		new_doc.model = item.model_no
		new_doc.serial_number = item.serial_no
		new_doc.description = item.item_name
	new_doc.append("technician",{
		"technician": doc.technician,
	})

	return new_doc

@frappe.whitelist()
def create_returned_parts(source_name, target_doc=None):
	target_doc = frappe.new_doc("Returned Parts")
	def set_missing_values(source, target):
		target.evaluation_report = source.name
		target.run_method("set_missing_values")

	doc = get_mapped_doc(
		"Evaluation Report",
		source_name,
		{
			"Evaluation Report": {
				"doctype": "Returned Parts"
			},
			"Part Sheet Item": {
				"doctype": "Returned Parts Item",
				"field_map": {
					"name": "reference",  # Mapping source child row name to reference field in target
				},
				"condition": lambda doc: (doc.qty - doc.returned_qty) > 0
			}
		},
		target_doc,
		set_missing_values
	)

	# Adjust quantity to be `remaining` (qty - returned_qty)
	for item in doc.returned_parts:
		source_item = frappe.get_doc("Part Sheet Item", item.reference)
		item.qty = source_item.qty - source_item.returned_qty

	branch_series_map = {
		"Dammam": "RP-D.YY.-",
		"Jeddah": "RP-J.YY.-",
		"Riyadh": "RP-R.YY.-",
		"Kuwait": "RP-K.YY.-",
		"Dubai": "RP-DU.YY.-"
	}
	target_doc.naming_series = branch_series_map.get(doc.branch, "")
	target_doc.warehouse = warehouse_list.get(doc.branch)
	target_doc.date = datetime.datetime.now()
	target_doc.job_order_data = frappe.db.get_value("Evaluation Report",source_name,"job_order_data")
	target_doc.evaluation_report = source_name	
	return doc