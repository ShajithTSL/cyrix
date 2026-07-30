import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt

from erpnext import get_default_cost_center
from erpnext.accounts.doctype.bank_transaction.bank_transaction import get_total_allocated_amount
from erpnext.accounts.party import get_party_account
from erpnext.accounts.report.bank_reconciliation_statement.bank_reconciliation_statement import (
	get_amounts_not_reflected_in_system,
	get_entries,
)
from erpnext.accounts.utils import get_account_currency, get_balance_on
from erpnext.setup.utils import get_exchange_rate


@frappe.whitelist()
def create_journal_entry_bts(
	bank_transaction_name,
	reference_number=None,
	reference_date=None,
	posting_date=None,
	entry_type=None,
	second_account=None,
	mode_of_payment=None,
	party_type=None,
	party=None,
	allow_edit=None,
	cost_center=None,
	branch=None,
	pay_to_recd_from=None,
	user_remark=None,
	attach_file=None,
):
	# Create a new journal entry based on the bank transaction
	bank_transaction = frappe.db.get_values(
		"Bank Transaction",
		bank_transaction_name,
		fieldname=["name", "deposit", "withdrawal", "bank_account", "currency","unallocated_amount"],
		as_dict=True,
	)[0]
	
	if bank_transaction.deposit > 0:
		deposit = bank_transaction.unallocated_amount
		withdrawal = 0
	if bank_transaction.withdrawal > 0:
		deposit = 0
		withdrawal = bank_transaction.unallocated_amount

	company_account = frappe.get_value("Bank Account", bank_transaction.bank_account, "account")
	account_type = frappe.db.get_value("Account", second_account, "account_type")
	if account_type in ["Receivable", "Payable"]:
		if not (party_type and party):
			frappe.throw(
				_("Party Type and Party is required for Receivable / Payable account {0}").format(
					second_account
				)
			)

	company = frappe.get_value("Account", company_account, "company")
	company_default_currency = frappe.get_cached_value("Company", company, "default_currency")
	company_account_currency = frappe.get_cached_value("Account", company_account, "account_currency")
	second_account_currency = frappe.get_cached_value("Account", second_account, "account_currency")
	
	# determine if multi-currency Journal or not
	is_multi_currency = (
		True
		if company_default_currency != company_account_currency
		or company_default_currency != second_account_currency
		or company_default_currency != bank_transaction.currency
		else False
	)

	accounts = []
	second_account_dict = {
		"account": second_account,
		"account_currency": second_account_currency,
		"credit_in_account_currency": deposit,
		"debit_in_account_currency": withdrawal,
		"party_type": party_type,
		"party": party,
		# "cost_center": get_default_cost_center(company),
		"cost_center": cost_center,
		"branch": branch,
		"user_remark": user_remark,
	}

	company_account_dict = {
		"account": company_account,
		"account_currency": company_account_currency,
		"bank_account": bank_transaction.bank_account,
		"credit_in_account_currency": withdrawal,
		"debit_in_account_currency": deposit,
		"cost_center": get_default_cost_center(company),
		"cost_center": cost_center,
		"branch": branch,
		"user_remark": user_remark,
	}

	# convert transaction amount to company currency
	if is_multi_currency:
		exc_rate = get_exchange_rate(bank_transaction.currency, company_default_currency, posting_date)
		withdrawal_in_company_currency = flt(exc_rate * abs(withdrawal))
		deposit_in_company_currency = flt(exc_rate * abs(deposit))
	else:
		withdrawal_in_company_currency = withdrawal
		deposit_in_company_currency = deposit

	# if second account is of foreign currency, convert and set debit and credit fields.
	if second_account_currency != company_default_currency:
		exc_rate = get_exchange_rate(second_account_currency, company_default_currency, posting_date)
		second_account_dict.update(
			{
				"exchange_rate": exc_rate,
				"credit": deposit_in_company_currency,
				"debit": withdrawal_in_company_currency,
				"credit_in_account_currency": flt(deposit_in_company_currency / exc_rate) or 0,
				"debit_in_account_currency": flt(withdrawal_in_company_currency / exc_rate) or 0,
			}
		)
	else:
		second_account_dict.update(
			{
				"exchange_rate": 1,
				"credit": deposit_in_company_currency,
				"debit": withdrawal_in_company_currency,
				"credit_in_account_currency": deposit_in_company_currency,
				"debit_in_account_currency": withdrawal_in_company_currency,
			}
		)

	# if company account is of foreign currency, convert and set debit and credit fields.
	if company_account_currency != company_default_currency:
		exc_rate = get_exchange_rate(company_account_currency, company_default_currency, posting_date)
		company_account_dict.update(
			{
				"exchange_rate": exc_rate,
				"credit": withdrawal_in_company_currency,
				"debit": deposit_in_company_currency,
			}
		)
	else:
		company_account_dict.update(
			{
				"exchange_rate": 1,
				"credit": withdrawal_in_company_currency,
				"debit": deposit_in_company_currency,
				"credit_in_account_currency": withdrawal_in_company_currency,
				"debit_in_account_currency": deposit_in_company_currency,
			}
		)

	accounts.append(second_account_dict)
	accounts.append(company_account_dict)

	journal_entry_dict = {
		"voucher_type": entry_type,
		"company": company,
		"posting_date": posting_date,
		"cheque_date": reference_date,
		"cheque_no": reference_number,
		"mode_of_payment": mode_of_payment,
		"pay_to_recd_from": pay_to_recd_from,
		"reconcile": 1,
		"bank_transaction_name":bank_transaction_name
	}
	if is_multi_currency:
		journal_entry_dict.update({"multi_currency": True})

	journal_entry = frappe.new_doc("Journal Entry")
	journal_entry.update(journal_entry_dict)
	journal_entry.set("accounts", accounts)

	if allow_edit:
		return journal_entry
	journal_entry.set("reconcile", 0)
	journal_entry.set("bank_transaction_name", '')
	journal_entry.insert()
	journal_entry.submit()
	frappe.db.set_value("Journal Entry",journal_entry.name,"pay_to_recd_from",pay_to_recd_from)
	if attach_file:
		link_file_to_journal_entry(journal_entry.name, attach_file)
		
	if bank_transaction.deposit > 0.0:
		paid_amount = bank_transaction.deposit
	else:
		paid_amount = bank_transaction.withdrawal

	vouchers = json.dumps(
		[
			{
				"payment_doctype": "Journal Entry",
				"payment_name": journal_entry.name,
				"amount": paid_amount,
			}
		]
	)

	return reconcile_vouchers(bank_transaction_name, vouchers)


def link_file_to_journal_entry(je_name, file_url):
	# Find the File doc created by the dialog upload
	file_doc = frappe.get_doc("File", {
		"file_url": file_url
	})

	# Link it to Journal Entry
	file_doc.attached_to_doctype = "Journal Entry"
	file_doc.attached_to_name = je_name
	file_doc.save(ignore_permissions=True)

@frappe.whitelist()
def reconcile_vouchers(bank_transaction_name, vouchers):
	# updated clear date of all the vouchers based on the bank transaction
	vouchers = json.loads(vouchers)
	transaction = frappe.get_doc("Bank Transaction", bank_transaction_name)
	transaction.add_payment_entries(vouchers)
	transaction.validate_duplicate_references()
	transaction.allocate_payment_entries()
	transaction.update_allocated_amount()
	transaction.set_status()
	transaction.save()

	return transaction
	
def link_file_to_payment_entry(pe_name, file_url):
	# Find the File doc created by the dialog upload
	file_doc = frappe.get_doc("File", {
		"file_url": file_url
	})

	# Link it to Payment Entry
	file_doc.attached_to_doctype = "Payment Entry"
	file_doc.attached_to_name = pe_name
	file_doc.save(ignore_permissions=True)


@frappe.whitelist()
def create_payment_entry_bts(
	bank_transaction_name,
	reference_number=None,
	reference_date=None,
	party_type=None,
	party=None,
	posting_date=None,
	mode_of_payment=None,
	project=None,
	cost_center=None,
	branch=None,
	allow_edit=None,
	attach_file=None,
):
	# Create a new payment entry based on the bank transaction
	bank_transaction = frappe.db.get_values(
		"Bank Transaction",
		bank_transaction_name,
		fieldname=["name", "unallocated_amount", "deposit", "bank_account", "currency"],
		as_dict=True,
	)[0]

	payment_type = "Receive" if bank_transaction.deposit > 0.0 else "Pay"

	bank_account = frappe.get_cached_value("Bank Account", bank_transaction.bank_account, "account")
	company = frappe.get_cached_value("Account", bank_account, "company")
	party_account = get_party_account(party_type, party, company)

	bank_currency = bank_transaction.currency
	party_currency = frappe.get_cached_value("Account", party_account, "account_currency")

	exc_rate = get_exchange_rate(bank_currency, party_currency, posting_date)

	amt_in_bank_acc_currency = bank_transaction.unallocated_amount
	amount_in_party_currency = bank_transaction.unallocated_amount * exc_rate

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = company
	pe.reference_no = reference_number
	pe.reference_date = reference_date
	pe.party_type = party_type
	pe.party = party
	pe.posting_date = posting_date
	pe.paid_from = party_account if payment_type == "Receive" else bank_account
	pe.paid_to = party_account if payment_type == "Pay" else bank_account
	pe.paid_from_account_currency = party_currency if payment_type == "Receive" else bank_currency
	pe.paid_to_account_currency = party_currency if payment_type == "Pay" else bank_currency
	pe.paid_amount = amount_in_party_currency if payment_type == "Receive" else amt_in_bank_acc_currency
	pe.received_amount = amount_in_party_currency if payment_type == "Pay" else amt_in_bank_acc_currency
	pe.mode_of_payment = mode_of_payment
	pe.project = project
	pe.cost_center = cost_center
	pe.branch = branch

	pe.validate()

	if allow_edit:
		return pe

	pe.insert()
	pe.submit()

	if attach_file:
		link_file_to_payment_entry(pe.name, attach_file)

	vouchers = json.dumps(
		[
			{
				"payment_doctype": "Payment Entry",
				"payment_name": pe.name,
				"amount": amt_in_bank_acc_currency,
			}
		]
	)
	return reconcile_vouchers(bank_transaction_name, vouchers)

def update_deposit_values_as_positive():
	docs = frappe.get_all(
		"Bank Transaction",
		filters={"withdrawal": ("<", 0)},
		fields=["name", "withdrawal"],
	)

	for d in docs:
		# Ensure withdrawal values are positive
		if d.withdrawal < 0:
			withdrawal = abs(d.withdrawal)
			print(d.name)
		else:
			withdrawal = d.withdrawal
		frappe.db.set_value("Bank Transaction", d.name, "withdrawal", withdrawal)



@frappe.whitelist()
def get_bank_transactions(bank_account, from_date=None, to_date=None, type=None):
	# returns bank transactions for a bank account
	filters = []
	
	if type:
		filters.append([type, ">", 0])
		
	filters.append(["bank_account", "=", bank_account])
	filters.append(["docstatus", "=", 1])
	filters.append(["unallocated_amount", ">", 0.0])
	if to_date:
		filters.append(["date", "<=", to_date])
	if from_date:
		filters.append(["date", ">=", from_date])
	transactions = frappe.get_all(
		"Bank Transaction",
		fields=[
			"date",
			"deposit",
			"withdrawal",
			"currency",
			"description",
			"name",
			"bank_account",
			"company",
			"unallocated_amount",
			"reference_number",
			"party_type",
			"party",
			"remarks"
		],
		filters=filters,
		order_by="date",
	)
	return transactions