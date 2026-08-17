# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

from frappe import _
from frappe.utils import today, escape_html

class PlannedLeaves(Document):
	def on_cancel(self):
		leave_app = frappe.db.get_value("Leave Application", {"reference": self.reference})
		if leave_app:
			doc = frappe.get_doc("Leave Application", leave_app)
			if doc.docstatus == 1:
				doc.cancel()

	def on_submit(self):
		if self.lop_start_date:
			lop = frappe.new_doc("Leave Application")
			lop.employee = self.employee
			lop.from_date = self.lop_start_date
			lop.to_date = self.lop_end_date
			lop.description = self.description
			lop.leave_type = "Leave Without Pay"
			lop.posting_date = self.posting_date
			lop.status = "Approved"
			lop.follow_via_email = 0
			lop.leave_approver = self.leave_approver


			lop.save(ignore_permissions=1)
			lop.submit()

		l_ap = frappe.new_doc("Leave Application")
		l_ap.employee = self.employee
		l_ap.from_date = self.leave_start_date
		l_ap.to_date = self.leave_end_date
		l_ap.description = self.description
		l_ap.leave_type = self.leave_type
		l_ap.posting_date = self.posting_date
		l_ap.status = "Approved"
		l_ap.follow_via_email = 0
		l_ap.leave_approver = self.leave_approver

		l_ap.save(ignore_permissions =1)
		l_ap.submit()


@frappe.whitelist()
def create_planned_leaves():

	current_date = today()

	planned_leaves = frappe.db.sql(
		"""
		select name
		from `tabPlanned Leaves`
		where docstatus = 0
			and from_date = %s
		""",
		(current_date,),
		as_dict=1,
	)

	if not planned_leaves:
		return

	failures = []

	for row in planned_leaves:
		try:
			pl = frappe.get_doc("Planned Leaves", row.name)
			pl.submit()
			frappe.db.commit()

		except Exception:
			frappe.db.rollback()

			error_message = frappe.get_traceback()

			try:
				doc = frappe.get_doc("Planned Leaves", row.name)
				doc.add_comment(
					"Comment",
					text=f"Auto-submit failed on {current_date}:<br><pre>{escape_html(error_message)}</pre>",
				)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(
					title=f"Could not add failure comment on Planned Leaves {row.name}",
					message=frappe.get_traceback(),
				)

			# Also keep a record in the Error Log for later debugging.
			frappe.log_error(
				title=f"Planned Leaves auto-submit failed: {row.name}",
				message=error_message,
			)

			failures.append({"name": row.name, "error": error_message})

			continue

	if failures:
		notify_planned_leaves_failures(failures, current_date)


def notify_planned_leaves_failures(failures, current_date):
	rows_html = "".join(
		f"""
		<tr>
			<td style="padding:4px 8px;border:1px solid #ddd;">
				<a href="/app/planned-leaves/{f['name']}">{f['name']}</a>
			</td>
			<td style="padding:4px 8px;border:1px solid #ddd;">
				<pre style="white-space:pre-wrap;margin:0;">{escape_html(f['error'])}</pre>
			</td>
		</tr>
		"""
		for f in failures
	)

	message = f"""
		<p>The scheduled job <b>submit_planned_leaves</b> ran on {current_date}
		and the following Planned Leaves record(s) could not be auto-submitted:</p>
		<table style="border-collapse:collapse;width:100%;">
			<tr>
				<th style="padding:4px 8px;border:1px solid #ddd;text-align:left;">Planned Leaves</th>
				<th style="padding:4px 8px;border:1px solid #ddd;text-align:left;">Error</th>
			</tr>
			{rows_html}
		</table>
		<p>The error has also been added as a comment on each document, and logged
		to the Error Log for reference.</p>
	"""

	frappe.sendmail(
		recipients=["shajith@tsl-me.com","yousuf@tsl-me.com"],
		subject=f"[Action needed] Planned Leaves auto-submit failed for {len(failures)} record(s) — {current_date}",
		message=message,
	)

def schedule_create_planned_leaves():
	job = frappe.db.exists('Scheduled Job Type', 'planned_leaves.create_planned_leaves')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'tsl.tsl.doctype.planned_leaves.planned_leaves.create_planned_leaves',
			"frequency" : 'Daily',
		})
		sjt.save(ignore_permissions=True)


def tod():
	current_time = datetime.today()
	print(current_time)