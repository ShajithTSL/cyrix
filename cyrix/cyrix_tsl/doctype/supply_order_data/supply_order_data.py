# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.custom_py import utils
from frappe.utils import add_to_date
from datetime import datetime

from frappe.utils import flt
from cyrix.custom_py.sales_invoice import (
	_get_jo_so_info_for_invoice,
	_apply_status,
	_split_amount_by_invoice_share,
)


class SupplyOrderData(Document):	
	def supply_order_status(self, ordered_percentage, received_percentage, delivered_percentage):
		ordered = ordered_percentage or 0
		received = received_percentage or 0
		delivered = delivered_percentage or 0

		if delivered == 100:
			supply_status = "Delivered"

		elif ordered == 0 and received == 0:
			supply_status = "To Order"

		elif 0 < ordered < 100:
			supply_status = "Partially Ordered"
			
		elif 0 < delivered < 100:
			supply_status = "Partially Delivered"


		elif received >= 100 and delivered == 0:
			supply_status = "To Deliver"

		elif 0 < received < 100:
			supply_status = "Partially Received"

		else:
			supply_status = "To Receive and Deliver"

		self.supply_status = supply_status
		frappe.db.set_value("Supply Order Data",self.name,'supply_status',supply_status,update_modified=False)

	def update_qty(self):
		total_quantity = 0
		for i in self.get("material_list"):
			total_quantity += int(i.quantity)
		self.quantity = total_quantity
		frappe.db.set_value("Supply Order Data",self.name,'quantity',total_quantity,update_modified=False)
	
	def update_po_percentage(self):
		# need to calculate the ordered %
		if self.get("ordered_quantity") > 0:
			ordered_percentage = (self.get("ordered_quantity")/self.get("quantity"))*100
		else:
			ordered_percentage = 0
			
		self.ordered_percentage = ordered_percentage
		frappe.db.set_value("Supply Order Data",self.name,'ordered_percentage',float(round(ordered_percentage, 2)),update_modified=False)
		self.supply_order_status(ordered_percentage,self.get("received_percentage"), delivered_percentage = float(round(self.delivered_percentage, 2)))

	def update_dn_percentage(self):
		# need to calculate the delivered %
		delivered_qty = 0
		for i in self.get("material_list"):
			if i.delivered_quantity:
				delivered_qty += float(i.delivered_quantity)
		if self.get("quantity") > 0:
			delivered_percentage = (delivered_qty/self.get("quantity"))*100
		else:
			delivered_percentage = 0

		self.delivered_percentage = delivered_percentage
		frappe.db.set_value("Supply Order Data",self.name,'delivered_percentage',float(round(delivered_percentage, 2)),update_modified=False)
		self.supply_order_status(self.get("ordered_percentage"),self.get("received_percentage"), float(round(delivered_percentage, 2)))

	def update_pr_percentage(self):
		# need to calculate the procured % based on the received_quantity field in the parent table
		if self.get("quantity") > 0:
			received_percentage = (self.get("received_quantity")/self.get("quantity"))*100
		else:
			received_percentage = 0
			
		self.received_percentage = received_percentage
		frappe.db.set_value("Supply Order Data",self.name,'received_percentage',float(round(received_percentage, 2)),update_modified=False)
		self.supply_order_status(self.get("ordered_percentage"), received_percentage, delivered_percentage = float(round(self.delivered_percentage, 2)))

	def update_inv_percentage(self):
		# need to calculate the invoiced % based on the invoiced_quantity field in the parent table
		if self.invoice_no:
			frappe.db.set_value("Supply Order Data",self.name,'invoice_percentage',100,update_modified=False)
		else:
			frappe.db.set_value("Supply Order Data",self.name,'invoice_percentage',0,update_modified=False)

	def update_payment_percentage(self):
		# need to calculate the payment % based on the advance_payment_amount field in the parent table
		if self.invoiced_value and self.advance_payment_amount:
			payment_percentage = (self.advance_payment_amount/self.invoiced_value)*100
			frappe.db.set_value("Supply Order Data",self.name,'payment_percentage',float(round(payment_percentage, 2)),update_modified=False)
		else:
			self.payment_percentage = 0
			frappe.db.set_value("Supply Order Data",self.name,'payment_percentage',0,update_modified=False)


	def trigger_fn(self):
		self.update_qty()
		self.update_dn_percentage()
		self.update_pr_percentage()
		self.update_inv_percentage()
		self.update_payment_percentage()
		self.update_po_percentage()

	def before_submit(self):		
		now = datetime.now()
		self.append("status_duration_details",{
			"status":self.status,
			"date":now,
		})
		self.update_qty()

		
	def on_update_after_submit(self):
		if self.status != self.status_duration_details[-1].status:
			ldate = self.status_duration_details[-1].date
			now = datetime.now()
			time_date = str(ldate).split(".")[0]
			format_data = "%Y-%m-%d %H:%M:%S"
			date = datetime.strptime(time_date, format_data)
			duration = now - date
			duration_in_s = duration.total_seconds()
			minutes = divmod(duration_in_s, 60)[0]/60
			data = str(minutes).split(".")[0]+"hrs "+str(minutes).split(".")[1][:2]+"min"
			frappe.db.set_value("Status Duration Details",self.status_duration_details[-1].name,"duration",data)
			self.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc = frappe.get_doc("Supply Order Data",self.name)
			doc.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc.save(ignore_permissions=True)
		self.trigger_fn()
		if self.status in ["Approved"]:
			frappe.db.set_value("Supply Order Data", self.name, "is_approved", 1, update_modified=False)

@frappe.whitelist()
def create_rfq(supply_order_data):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	rfq = frappe.new_doc("Request for Quotation")
	rfq.company = doc.company
	rfq.branch = frappe.db.get_value("Supply Order Data",supply_order_data,"branch")
	rfq.supply_order_data = supply_order_data
	rfq.schedule_date = add_to_date(rfq.transaction_date,days = 2),
	rfq.cost_center = doc.department
	rfq.status = "Draft"
	rfq.items=[]
	warehouse = warehouse_based_on_branch_and_company(rfq.company,rfq.branch)
	for i in doc.get("material_list"):
		rfq.append("items",{
			"item_code":i.item_code,
			"item_name":i.description,
			"description":i.description,
			'model':i.model_no,
			"mfg":i.mfg,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"stock_qty":1,
			"qty":i.quantity,
			"schedule_date":add_to_date(rfq.transaction_date,days = 2),
			"warehouse":warehouse,
			"branch":rfq.branch,
			"supply_order_data":supply_order_data,
			"cost_center":frappe.db.get_value("Supply Order Data",supply_order_data,"department")
		})

	return rfq

@frappe.whitelist()
def warehouse_based_on_branch_and_company(company,branch):
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["actual_warehouse"])
	return warehouse

from cyrix.custom_py.quotation import fetch_item_price_details
@frappe.whitelist()
def create_internal_quotation(supply_order_data, customer):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc= frappe.new_doc("Quotation")
	new_doc.customer_reference_number = doc.customer_reference_number
	new_doc.sales_person = doc.sales_person
	if doc.branch:
		d = {
			"Internal Quotation - Supply":{
				"Kuwait":"IQS-K.YY.-",
				"Dammam":"IQS-D.YY.-",
				"Riyadh":"IQS-R.YY.-",
				"Jeddah":"IQS-J.YY.-",
				"Dubai":"IQS-DU.YY.-"
			},
			"Customer Quotation - Supply":{
				"Kuwait":"CQS-K.YY.-",
				"Dammam":"CQS-D.YY.-",
				"Riyadh":"CQS-R.YY.-",
				"Jeddah":"CQS-J.YY.-",
				"Dubai":"CQS-DU.YY.-"
			},
		}
	if new_doc.quotation_type:
		new_doc.naming_series = d[new_doc.quotation_type][doc.branch]
	new_doc.company = doc.company
	new_doc.party_name = customer
	new_doc.parent_customer = frappe.db.get_value("Customer",customer,"parent_customer")
	if doc.customer != customer:
		new_doc.child_customer = doc.customer
	new_doc.plant = doc.plant
	new_doc.branch = doc.branch
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")

	new_doc.quotation_type = "Internal Quotation - Supply"
	for i in doc.material_list:
		new_doc.append("items",{
			"item_code":i.item_code,
			"item_name":i.description,
			"description":i.description,
			"model":i.model_no,
			"model_number": frappe.db.get_value("Item Model",i.model_no,'model'),
			"mfg":i.mfg,
			"uom":'Nos',
			"qty":i.quantity,
			"supply_order_data":doc.name,
			"warehouse":doc.warehouse
		})
	fetch_item_price_details(new_doc,method="validate")
	return new_doc



@frappe.whitelist()
def create_delivery_note(supply_order_data, customer):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc = frappe.new_doc("Delivery Note")
	new_doc.customer_reference_number = doc.customer_reference_number
	new_doc.company = doc.company
	new_doc.customer = customer
	if doc.customer != customer:
		new_doc.child_customer = doc.customer
	new_doc.branch = doc.branch
	new_doc.cost_center = doc.department
	new_doc.set_warehouse = doc.warehouse
	new_doc.purchase_order_no = doc.po_no
	new_doc.supply_order_data = doc.name
	new_doc.sales_person = doc.sales_person
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	list_ = []
	for i in doc.get("material_list"):
		remaining_qty = float(i.quantity) - float(i.delivered_quantity)
		if remaining_qty > 0:
			new_doc.append("items",{
				"item_name":i.item_name or i.description,
				"item_code":i.item_code,
				"manufacturer":i.mfg,
				"model":i.model_no,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"serial_number":i.serial_no,
				"description":i.description,
				"qty":remaining_qty,
				"supply_order_data":supply_order_data,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center":doc.department or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
				"income_account":"",
				"branch":doc.branch
			})
			list_.append({
				"item_name":i.item_name or i.description,
				"item_code":i.item_code,
				"manufacturer":i.mfg,
				"model":i.model_no,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"serial_number":i.serial_no,
				"description":i.description,
				"qty":remaining_qty,
				"supply_order_data":supply_order_data,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center": doc.department or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
				"income_account":"",
				"branch":doc.branch
			})
	return new_doc,list_


@frappe.whitelist()
def create_sales_invoice(supply_order_data, customer):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc = frappe.new_doc("Sales Invoice")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.customer = customer

	new_doc.parent_customer = frappe.db.get_value("Customer",customer,"parent_customer")
	if doc.customer != customer:
		new_doc.child_customer = doc.customer

	new_doc.branch = doc.branch
	new_doc.supply_order_data = supply_order_data
	new_doc.sales_person = doc.sales_person
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.cost_center = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
	sales_invoice_list = []
	for i in doc.get("material_list"):
		qi_details = frappe.db.sql('''select 
			q.valid_till as valid_till,
			q.name,qi.qty as qty,
			qi.rate as rate,
			qi.amount as amount 
		from `tabQuotation Item` as qi 
			inner join `tabQuotation` as q on q.name = qi.parent 
		where qi.item_code = %s 
			and q.workflow_state = "Approved By Customer" 
			and qi.supply_order_data = %s 
			and q.docstatus = 1 
			order by q.modified desc limit 1''',(i.item_code,supply_order_data),as_dict=1)
		r = 0
		amt = 0
		qty = i.quantity
		if qi_details:
			r = qi_details[0]['rate']
			amt = qi_details[0]['amount']
			qty = qi_details[0]['qty']
			new_doc.due_date = qi_details[0]['valid_till']
		new_doc.append("items",{
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"rate":r,
			"amount":amt, 
			"serial_number":i.serial_no,
			"description":i.description,
			"qty":qty,
			"supply_order_data":supply_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
			"income_account":"",
			"branch":doc.branch
		})
		sales_invoice_list.append({
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"rate":r,
			"amount":amt, 
			"serial_number":i.serial_no,
			"description":i.description,
			"qty":qty,
			"supply_order_data":supply_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
			"income_account":"",
			"branch":doc.branch
		})

	return new_doc,sales_invoice_list


def list_desk():
	list = frappe.db.get_all("Desktop Icon","name")
	doc = frappe.get_doc("Desktop Icon","CYRIX")
	doc.delete()
	print(list)

def _fetch_journal_entry_payments(reference_type, reference_name):
	"""
	Journal Entries never reference a JO/SO/BQ directly - only the Sales
	Invoice, via a Journal Entry Account row. So: find every submitted
	invoice that touches this reference (the same lookup _recompute_invoiced_value
	uses), find submitted Journal Entries that knocked off an amount
	against any of those invoices, then split each one the same way
	sync_jo_so_on_je_submit did at the time it was applied - this
	reproduces exactly what was applied, without needing to parse
	jo_so_sync_log back out of Journal Entry.
	"""
	item_field = {
		"Job Order Data": "job_order_data",
		"Supply Order Data": "supply_order_data",
		"Budgetary Quotation": "budgetary_quotation",
	}.get(reference_type)

	if not item_field:
		return []

	invoice_names = frappe.db.sql_list(f"""
		SELECT DISTINCT si.name
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND sii.{item_field} = %s
	""", (reference_name,))

	if not invoice_names:
		return []

	je_rows = frappe.db.sql("""
		SELECT
			jea.parent AS journal_entry,
			jea.reference_name AS sales_invoice,
			COALESCE(jea.credit_in_account_currency, 0) AS credit,
			COALESCE(jea.debit_in_account_currency, 0) AS debit,
			jea.account_currency AS currency_code,
			c.symbol AS currency_symbol,
			je.posting_date
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
		LEFT JOIN `tabCurrency` c ON c.name = jea.account_currency
		WHERE je.docstatus = 1
		  AND jea.reference_type = 'Sales Invoice'
		  AND jea.reference_name IN %(invoices)s
	""", {"invoices": invoice_names}, as_dict=True)

	results = []
	for row in je_rows:
		knocked_off = flt(row.credit) or flt(row.debit)
		if knocked_off <= 0:
			continue

		jo_so_info = _get_jo_so_info_for_invoice(row.sales_invoice)
		if not jo_so_info:
			continue

		for info, share_amount in _split_amount_by_invoice_share(jo_so_info, knocked_off):
			if share_amount <= 0:
				continue
			if info["reference_type"] == reference_type and info["reference_name"] == reference_name:
				results.append(frappe._dict({
					"payment_entry": row.journal_entry,
					"amount": share_amount,
					"posting_date": row.posting_date,
					"currency": row.currency_code,
					"currency_symbol": row.currency_symbol,
					"voucher_type": "Journal Entry",
				}))

	return results

@frappe.whitelist()
def fetch_payment_details(name):
	payment = frappe.db.sql("""
		SELECT
			t.parent AS payment_entry,
			t.allocate_amount AS amount,
			p.posting_date,
			c.symbol AS currency,
			'Payment Entry' AS voucher_type
		FROM `tabJob Order table` t
		JOIN `tabPayment Entry` p
			ON p.name = t.parent
		JOIN `tabCurrency` c
			ON c.name = p.paid_to_account_currency
		WHERE
			t.parenttype = 'Payment Entry'
			AND t.reference_type = 'Supply Order Data'
			AND t.reference_name = %s
			AND p.docstatus = 1
	""", (name,), as_dict=True)

	journal_entries = _fetch_journal_entry_payments("Supply Order Data", name)
	for je in journal_entries:
		je["currency"] = je.pop("currency_symbol")

	payment = list(payment) + journal_entries
	payment.sort(key=lambda d: d.get("posting_date") or "")

	sales_invoice = frappe.db.sql("""
		SELECT
			DISTINCT(si.parent) AS sales_invoice,
			s.grand_total as amount,
			s.outstanding_amount AS outstanding_amount,
			s.posting_date AS invoice_date,
			s.status,
			c.symbol AS currency
		FROM `tabSales Invoice Item` si
		JOIN `tabSales Invoice` s
			ON s.name = si.parent
		JOIN `tabCurrency` c
			ON c.name = s.currency
		WHERE
			si.supply_order_data = %s
		AND s.docstatus = 1
		""", (name,), as_dict=True)

	return payment, sales_invoice