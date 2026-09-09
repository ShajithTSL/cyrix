import json

import frappe
from frappe.utils import flt

from cyrix.custom_py.sales_invoice import (
	_get_jo_so_info_for_invoice,
	_apply_status,
	_split_amount_by_invoice_share,
)

def sync_jo_so_on_je_submit(self, method):
	"""Hook: Journal Entry on_submit"""
	applied = []

	for acc in self.accounts:
		if acc.reference_type != "Sales Invoice" or not acc.reference_name:
			continue

		knocked_off = flt(acc.credit_in_account_currency) or flt(acc.debit_in_account_currency)
		if knocked_off <= 0:
			continue

		jo_so_info = _get_jo_so_info_for_invoice(acc.reference_name)
		if not jo_so_info:
			continue

		# Split the knocked-off amount across this invoice's distinct
		# references in proportion to each one's own share of the
		# invoice - e.g. a 100-value invoice made up of JO 25 / SO 55 /
		# BQ 20 gets a 100 knock-off split 25/55/20, not 100/100/100.
		for info, share_amount in _split_amount_by_invoice_share(jo_so_info, knocked_off):
			if share_amount <= 0:
				continue

			ref_doc = frappe.get_doc(info["reference_type"], info["reference_name"])
			updated_amount = flt(ref_doc.advance_payment_amount) + share_amount

			_apply_status(ref_doc, info["reference_type"], updated_amount)

			ref_doc.advance_payment_amount = updated_amount
			ref_doc.advance_paid_date = self.posting_date
			ref_doc.save(ignore_permissions=True)

			applied.append({
				"reference_type": info["reference_type"],
				"reference_name": info["reference_name"],
				"amount": share_amount,
			})

	if applied:
		frappe.db.set_value(
			"Journal Entry", self.name, "jo_so_sync_log", json.dumps(applied),
			update_modified=False,
		)


def sync_jo_so_on_je_cancel(self, method):
	"""Hook: Journal Entry on_cancel - reverses sync_jo_so_on_je_submit()."""
	log = self.get("jo_so_sync_log")
	if not log:
		return

	try:
		applied = json.loads(log)
	except ValueError:
		applied = []
	if not applied:
		return

	for entry in applied:
		if not frappe.db.exists(entry["reference_type"], entry["reference_name"]):
			continue

		ref_doc = frappe.get_doc(entry["reference_type"], entry["reference_name"])
		updated_amount = flt(ref_doc.advance_payment_amount) - flt(entry["amount"])

		_apply_status(ref_doc, entry["reference_type"], updated_amount)

		ref_doc.advance_payment_amount = updated_amount
		if updated_amount == 0:
			ref_doc.advance_paid_date = ''
		ref_doc.save(ignore_permissions=True)

	frappe.db.set_value(
		"Journal Entry", self.name, "jo_so_sync_log", "",
		update_modified=False,
	)