"""Visit Plan: one plan (a day or trip) for a salesperson, with many visit lines.

- Fills each line's party name from the lead / deal / customer.
- Keeps the counters and the plan status up to date from the lines.
- A line with a "Next Follow-up" date creates a follow-up once: a CRM Task for leads and
  deals, a ToDo for customers, assigned to the person the plan is for.
- Finished lines (Visited / Not Visited / Rescheduled / Cancelled) and Completed / Cancelled plans
  are locked: only a Sales Manager or System Manager can change or remove them.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, formatdate, get_fullname

FINISHED = {"Visited", "Not Visited", "Rescheduled", "Cancelled"}
CLOSED = {"Completed", "Cancelled"}
MANAGERS = {"System Manager", "Sales Manager"}
LOCKED_FIELDS = ("visit_time", "party_type", "party", "visit_type", "location", "purpose", "status", "outcome",
                 "next_followup_date")


def is_manager():
	return bool(MANAGERS & set(frappe.get_roles()))


def _norm(field, v):
	if v is None or v == "":
		return ""
	if field == "visit_time":
		return str(v).zfill(8)[:5] if ":" in str(v) else str(v)
	return str(v)
TITLE_FIELD = {"CRM Lead": "lead_name", "CRM Deal": "organization", "Customer": "customer_name"}


class VisitPlan(Document):
	def validate(self):
		self.check_locked()
		for row in self.items:
			row.status = row.status or "Planned"
			f = TITLE_FIELD.get(row.party_type)
			name = None
			if row.party and f and frappe.db.exists("DocType", row.party_type):
				name = frappe.db.get_value(row.party_type, row.party, f)
			row.party_name = name or row.party
		live = [r for r in self.items if r.status != "Cancelled"]
		self.total_visits = len(live)
		self.completed_visits = len([r for r in self.items if r.status == "Visited"])
		if self.status not in ("Cancelled", "Draft", "Completed") and self.items:
			if all(r.status in FINISHED for r in self.items):
				self.status = "Completed"
			elif any(r.status in FINISHED for r in self.items):
				self.status = "In Progress"
		self.title = f"{get_fullname(self.sales_user) or self.sales_user} · {formatdate(self.plan_date)}"

	def check_locked(self):
		if self.is_new() or is_manager():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		if before.status in CLOSED:
			sig = lambda doc: [(r.name, tuple(_norm(f, r.get(f)) for f in LOCKED_FIELDS)) for r in doc.items]
			if sig(self) != sig(before):
				frappe.throw(_("This plan is {0}. Ask a manager to reopen it.").format(_(before.status)))
		old = {r.name: r for r in before.items}
		now = {r.name: r for r in self.items}
		for name, o in old.items():
			if o.status not in FINISHED:
				continue
			r = now.get(name)
			if not r:
				frappe.throw(_("Row {0}: a finished visit can't be removed.").format(o.idx))
			changed = [f for f in LOCKED_FIELDS if _norm(f, o.get(f)) != _norm(f, r.get(f))]
			if changed:
				frappe.throw(_("Row {0}: this visit is {1} and locked. Ask a manager to change it.").format(o.idx, _(o.status)))

	def on_update(self):
		for row in self.items:
			if row.next_followup_date and row.party and not cint(row.followup_created):
				create_followup(self, row)
				frappe.db.set_value("Visit Plan Item", row.name, "followup_created", 1, update_modified=False)
				row.followup_created = 1


def create_followup(plan, row):
	title = _("Follow up after visit") + (f": {row.purpose}" if row.purpose else f" ({row.visit_type})" if row.visit_type else "")
	is_crm = row.party_type in ("CRM Lead", "CRM Deal")
	if is_crm and frappe.db.exists("DocType", "CRM Task") and not frappe.get_meta("CRM Task").istable:
		meta = frappe.get_meta("CRM Task")
		data = {"title": title, "status": "Todo", "priority": "Medium", "due_date": row.next_followup_date,
		        "assigned_to": plan.sales_user, "reference_doctype": row.party_type, "reference_docname": row.party,
		        "description": f"<p>{frappe.utils.escape_html(row.outcome or '')}</p>", "custom_followup_type": "Call"}
		doc = frappe.get_doc({"doctype": "CRM Task", **{k: v for k, v in data.items() if meta.has_field(k)}})
	else:
		doc = frappe.get_doc({"doctype": "ToDo", "description": title, "date": row.next_followup_date,
		                      "allocated_to": plan.sales_user, "reference_type": row.party_type,
		                      "reference_name": row.party})
	doc.flags.ignore_permissions = True  # the plan owner already has access to the visited record
	doc.insert()