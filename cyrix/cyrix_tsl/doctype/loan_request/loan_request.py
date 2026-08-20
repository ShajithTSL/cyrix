# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, date_diff, flt, get_last_day, getdate,today
from frappe.utils import cint, flt, rounded
from frappe.utils import formatdate
from datetime import datetime, timedelta
import calendar

class LoanRequest(Document):
	def make_payment_entry(self):
		pe = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Pay",
			"party_type": "Employee",
			"party": self.employee,
			"company": self.company,
			"posting_date": self.disbursement_date,
			"mode_of_payment": "Bank Draft",
			
			"paid_from": self.disbursement_account,   
			"paid_to": self.loan_account,
			
			"paid_amount": self.disbursed_amount,
			"received_amount": self.disbursed_amount,
			"reference_no": self.name,
			"reference_date": self.disbursement_date,
			"reference_remarks": _("Disbursement against loan: ") + self.name,
		})
		pe.insert(ignore_permissions=True)
		pe.submit()

		frappe.db.set_value("Loan Request", self.name, "disbursement_reference", pe.name, update_modified = False)

		frappe.msgprint("Payment Entry created for Disbursement - <b>"+pe.name+"</b>")
		return pe.name

	def cancel_payment_entry(self):
		if frappe.db.exists("Payment Entry",self.disbursement_reference):
			pe = frappe.get_doc("Payment Entry",self.disbursement_reference)
			pe.cancel()
			pe.delete(ignore_permissions=1, force=1, delete_permanently=1)

	
	def validate_disbursal_amount(self):
		if self.disbursed_amount and self.disbursed_amount > self.loan_amount:
			frappe.throw(_("Disbursed Amount cannot be greater than {0}").format(self.loan_amount))


	def get_repayment_details(self):
		if self.repayment_amount:
			if self.is_term_loan:

				if self.repayment_method == "Repay Fixed Amount per Period":
					self.repayment_periods = self.loan_amount / self.repayment_amount

				self.calculate_payable_amount()
			else:
				self.total_payable_amount = self.loan_amount
			
	def calculate_payable_amount(self):
		balance_amount = self.loan_amount
		self.total_payable_amount = 0
		self.total_payable_interest = 0

		while balance_amount > 0:
			interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (12 * 100))
			balance_amount = rounded(balance_amount + interest_amount - self.repayment_amount)

			self.total_payable_interest += interest_amount

		self.total_payable_amount = self.loan_amount + self.total_payable_interest

	def validate(self):
		self.get_repayment_details()
		self.make_repayment_schedule()

		if not self.is_term_loan or (self.is_term_loan and not self.is_new()):
			self.calculate_totals()

	def after_insert(self):
		if self.is_term_loan:
			self.calculate_totals(on_insert=True)

	def on_submit(self):
		if not self.disbursement_date or not self.disbursed_amount:
			frappe.throw(_("Disbursement Date and Amount is mandatory"))

		self.make_payment_entry()
		self.validate_disbursal_amount()

	def on_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry"]
		self.cancel_payment_entry()

	def calculate_totals(self, on_insert=False):
		self.total_payment = 0
		self.total_amount_paid = 0
		self.total_payment = self.loan_amount

		if on_insert:
			self.db_set("repayment_amount", self.repayment_amount)
			self.db_set("total_payment", self.total_payment)
	
	def add_repayment_schedule_row(
		self, payment_date, principal_amount, interest_amount, total_payment, balance_loan_amount, days
	):
		self.append(
			"repayment_schedule",
			{
				"number_of_days": days,
				"payment_date": payment_date,
				"principal_amount": principal_amount,
				"interest_amount": interest_amount,
				"total_payment": total_payment,
				"balance_loan_amount": balance_loan_amount,
			},
		)

	def make_repayment_schedule(self):
		# if not self.repayment_start_date:
		# 	frappe.throw(_("Repayment Start Date is mandatory for term loans"))

		schedule_type_details = frappe.db.get_value(
			"Loan Product", self.loan_product, ["repayment_schedule_type", "repayment_date_on"], as_dict=1
		)

		self.repayment_schedule = []
		payment_date = self.repayment_start_date
		balance_amount = self.loan_amount
		broken_period_interest_days = date_diff(add_months(payment_date, -1), self.posting_date)
		carry_forward_interest = self.adjusted_interest

		while balance_amount > 0:
			interest_amount, principal_amount, balance_amount, total_payment, days = self.get_amounts(
				payment_date,
				balance_amount,
				schedule_type_details.repayment_schedule_type,
				schedule_type_details.repayment_date_on,
				broken_period_interest_days,
				carry_forward_interest,
			)

			if schedule_type_details.repayment_schedule_type == "Pro-rated calendar months":
				next_payment_date = get_last_day(payment_date)
				if schedule_type_details.repayment_date_on == "Start of the next month":
					next_payment_date = add_days(next_payment_date, 1)

				payment_date = next_payment_date

			self.add_repayment_schedule_row(
				payment_date, principal_amount, interest_amount, total_payment, balance_amount, days
			)

			if (
				self.repayment_method == "Repay Over Number of Periods"
				and len(self.get("repayment_schedule")) >= self.repayment_periods
			):
				self.get("repayment_schedule")[-1].principal_amount += balance_amount
				self.get("repayment_schedule")[-1].balance_loan_amount = 0
				self.get("repayment_schedule")[-1].total_payment = (
					self.get("repayment_schedule")[-1].interest_amount
					+ self.get("repayment_schedule")[-1].principal_amount
				)
				balance_amount = 0

			if (
				schedule_type_details.repayment_schedule_type
				in ["Monthly as per repayment start date", "Monthly as per cycle date"]
				or schedule_type_details.repayment_date_on == "End of the current month"
			):
				next_payment_date = add_single_month(payment_date)
				payment_date = next_payment_date

			bmi_days = 0
			carry_forward_interest = 0
	def get_amounts(
		self,
		payment_date,
		balance_amount,
		schedule_type,
		repayment_date_on,
		additional_days,
		carry_forward_interest=0,
	):
		if schedule_type == "Monthly as per repayment start date":
			days = 1
			months = 12
		else:
			expected_payment_date = get_last_day(payment_date)
			if repayment_date_on == "Start of the next month":
				expected_payment_date = add_days(expected_payment_date, 1)

			if schedule_type == "Monthly as per cycle date":
				days = date_diff(payment_date, add_months(payment_date, -1))
				if additional_days < 0:
					days = date_diff(self.repayment_start_date, self.posting_date)
					additional_days = 0

				months = 365
				if additional_days:
					days += additional_days
					additional_days = 0
			elif expected_payment_date == payment_date:
				# using 30 days for calculating interest for all full months
				days = 30
				months = 365
			else:
				days = date_diff(get_last_day(payment_date), payment_date)
				months = 365

		interest_amount = flt(balance_amount * flt(self.rate_of_interest) * days / (months * 100))
		principal_amount = self.repayment_amount - flt(interest_amount)
		balance_amount = flt(balance_amount + interest_amount - self.repayment_amount)
		if balance_amount < 0:
			principal_amount += balance_amount
			balance_amount = 0.0

		if carry_forward_interest:
			interest_amount += carry_forward_interest

		total_payment = principal_amount + interest_amount

		return interest_amount, principal_amount, balance_amount, total_payment, days


@frappe.whitelist()
def add_single_month(date):
	if getdate(date) == get_last_day(date):
		return get_last_day(add_months(date, 1))
	else:
		return add_months(date, 1)

def update_total_amount_paid(docname):
	doc = frappe.get_doc("Loan Request",docname)
	total_amount_paid = 0
	for data in doc.repayment_schedule:
		if data.paid_amount:
			total_amount_paid += data.paid_amount
	frappe.db.set_value("Loan Request", doc.name, "total_amount_paid", total_amount_paid)
	frappe.db.set_value("Loan Request", doc.name, "balance_amount", doc.total_payment - total_amount_paid)
	if total_amount_paid > 0 and total_amount_paid == doc.total_payment:
		frappe.db.set_value("Loan Request", doc.name, "status", "Loan Settled")		
		frappe.db.set_value("Loan Request", doc.name, "closure_date", today())

@frappe.whitelist()
def create_loan_repayment(name):
	loan = frappe.get_doc("Loan Request", name)

	repayment = frappe.new_doc("Loan Request Repayment")
	repayment.against_loan = name
	repayment.employee = loan.employee
	repayment.posting_date = frappe.utils.nowdate()
	repayment.amount_paid = (loan.total_payment or 0) - (loan.total_amount_paid or 0)

	# Load unpaid schedule rows
	schedule_rows = frappe.get_all(
		"Loan Request Repayment Schedule",
		filters={
			"parent": name,
			"is_accrued": 0
		},
		fields=["name", "payment_date", "total_payment", "paid_amount"],
		order_by="payment_date asc"
	)
	repayment_rows = []

	for row in schedule_rows:
		pending = (row.total_payment or 0) - (row.paid_amount or 0)
		if pending > 0:
			repayment_rows.append({
				"payment_date": row.payment_date,
				"reference": row.name,
				"accrual_type": "Repayment",
				"paid_principal_amount": pending,
				"total_payment": pending,
			})
	# Sort by payment_date (descending)
	repayment_rows.sort(key=lambda x: x["payment_date"], reverse=True)

	# Now append in sorted order
	for r in repayment_rows:
		repayment.append("repayment_details", r)
	repayment.flags.ignore_permissions = True

	return repayment

@frappe.whitelist()
def shift_payment_dates_for_pause(self, from_date, to_date, loan_pause_details):
	loan = frappe.get_doc("Loan Request", self)
	from frappe.utils import (
		getdate, add_days, add_months,
		get_first_day, get_last_day
	)

	# Expand to month boundaries
	from_date = getdate(add_days(get_first_day(from_date), -1))
	to_date = getdate(get_last_day(to_date))
	pause_days = (to_date - from_date).days

	if pause_days <= 0:
		frappe.throw("To Date must be after From Date")

	updated_count = 0
	used_months = set()       # 👈 Track which months already assigned

	for schedule in loan.repayment_schedule:
		if getdate(schedule.payment_date) > from_date and not schedule.is_accrued:

			# 1️⃣ Shift by pause days
			new_date = add_days(schedule.payment_date, pause_days)

			# 2️⃣ Move to 1st of month
			new_date = get_first_day(new_date)

			# 3️⃣ Avoid duplicate months (important!)
			while new_date.strftime("%Y-%m") in used_months:
				new_date = get_first_day(add_months(new_date, 1))

			# 4️⃣ Assign & mark month as used
			used_months.add(new_date.strftime("%Y-%m"))
			schedule.payment_date = new_date
			updated_count += 1

	if not updated_count:
		frappe.msgprint("No repayment dates were shifted (either no eligible entries or all had demand generated).")

	# Handle pause details
	if isinstance(loan_pause_details, str):
		loan_pause_details = frappe.parse_json(loan_pause_details)

	loan.append("loan_pause_details", loan_pause_details)

	loan.save(ignore_permissions=True)
	frappe.db.commit()

	return f"{updated_count} repayment date(s) successfully shifted!"

@frappe.whitelist()
def preview_shifted_repayment_schedule(loan_name, from_date, to_date):
	from frappe.utils import (
		getdate, add_days, add_months,
		get_first_day, get_last_day
	)

	loan = frappe.get_doc("Loan Request", loan_name)

	# Expand to full month boundaries
	from_date = getdate(add_days(get_first_day(from_date), -1))
	to_date = getdate(get_last_day(to_date))
	# pause_days = (to_date - from_date).days

	pause_months = (
		(to_date.year - from_date.year) * 12 +
		(to_date.month - from_date.month)
	)

	preview = []

	# Step 1: collect only eligible rows
	rows = [
		r for r in loan.repayment_schedule
		if getdate(r.payment_date) > from_date
	]

	# Step 2: sort to ensure strict order
	rows.sort(key=lambda x: x.payment_date)

	# Step 3: compute how many installments to shift
	pause_months = (
		(to_date.year - from_date.year) * 12 +
		(to_date.month - from_date.month)
	)

	last_date = None

	for i, row in enumerate(rows):
		old_date = getdate(row.payment_date)

		if row.is_accrued:
			preview.append({
				"old_date": old_date.strftime("%d-%m-%Y"),
				"new_date": "Locked (Demand Generated)"
			})
			continue

		# 🔥 KEY FIX: shift based on POSITION, not raw date math
		if last_date:
			new_date = add_months(last_date, 1)
		else:
			new_date = get_first_day(add_months(old_date, pause_months))

		new_date = get_first_day(new_date)
		last_date = new_date

		preview.append({
			"old_date": old_date.strftime("%d-%m-%Y"),
			"new_date": new_date.strftime("%d-%m-%Y")
		})
	return preview
	
@frappe.whitelist()
def get_criteria(employee, cur_name):
    filters = {'employee': employee, 'date': frappe.utils.nowdate()}
    from cyrix.cyrix_tsl.report.gratuity.gratuity import execute

    # Get gratuity details
    result = execute(filters)
    records = result[1]

    experience = records[0][3] if records else "N/A"
    termination_amount = records[0][8] if records else 0
    resignation_amount = records[0][10] if records else 0

    # Fetch pending loans
    pending_loans = frappe.get_list(
        "Loan Request",
        filters={
            "employee": employee,
            "docstatus": 1,
            "balance_amount": (">", 0)
        },
        fields=["name", "loan_product", "balance_amount", "total_payment", "total_amount_paid"],
        order_by="creation asc",
    )

    # Build pending loans table
    loans_html = ""
    if pending_loans:
        loans_html = """
        <h2 style='border-bottom:2px solid #0066AD; padding-bottom:5px; color:#0066AD;'>Pending Loans</h2>
        <table style='width:100%; border-collapse: collapse; font-family: Arial, sans-serif;'>
            <thead style='background-color:#0066AD;color:white;'>
                <tr>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;'>Loan Type</th>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;'>Reference</th>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>Total Amount</th>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>Balance Amount</th>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>Repaid %</th>
                    <th style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>Closing Date</th>
                </tr>
            </thead>
            <tbody>
        """

        for loan in pending_loans:
            schedule = frappe.get_all(
                "Loan Request Repayment Schedule",
                filters={"parent": loan["name"], "is_accrued": 0},
                fields=["payment_date"],
                order_by="payment_date desc",
                limit_page_length=1
            )

            last_payment_date = formatdate(schedule[0]["payment_date"], "dd-MMM-yyyy") if schedule else "N/A"

            link = f'<a href="/app/loan-request/{loan["name"]}" target="_blank">{loan["name"]}</a>'
            repay_percentage = round((loan['total_amount_paid'] / loan['total_payment']) * 100, 2) if loan['total_amount_paid'] else 0

            # Row coloring
            if repay_percentage < 50:
                row_style = "background-color:#fff3cd;font-weight:bold;" if loan['name'] != cur_name else "background-color:#B6FFA3;font-weight:bold;"
                warning_note = "<span style='color:red; font-weight:bold;font-size:10px'> ⚠️ Review before next loan</span>" if loan['name'] != cur_name else ""
            else:
                row_style = ""
                warning_note = ""

            loans_html += f"""
                <tr style='{row_style}'>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;'>{loan['loan_product']}{warning_note}</td>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;'>{link}</td>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>{loan['total_payment']}</td>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>{loan['balance_amount']}</td>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>{repay_percentage}%</td>
                    <td style='padding: 10px; border-bottom:1px solid #ddd;text-align:right'>{last_payment_date}</td>
                </tr>
            """
        loans_html += "</tbody></table>"

    # Gratuity info table
    html = f"""
    <div style='padding: 20px; font-family: Arial, sans-serif; font-size:14px;'>
        <h2 style='border-bottom:2px solid #0066AD; padding-bottom:5px; color:#0066AD;'>Employee Gratuity & Loans</h2>

        <table style='width:100%; border-collapse: collapse; margin-bottom: 20px;'>
            <tr>
                <th style='text-align:left; padding: 10px;'>Work Experience</th>
                <td style='padding: 10px;'>{experience}</td>
            </tr>
            <tr>
                <th style='text-align:left; padding: 10px;'>On Resignation</th>
                <td style='padding: 10px;'>{resignation_amount}</td>
            </tr>
            <tr>
                <th style='text-align:left; padding: 10px;'>On Termination</th>
                <td style='padding: 10px;'>{termination_amount}</td>
            </tr>
        </table>

        {loans_html}
    </div>
    """
    return html

@frappe.whitelist()
def get_pending_loans_html(employee):
	from frappe.utils import formatdate

	# Fetch pending loans
	pending_loans = frappe.get_list(
		"Loan Request",
		filters={
			"employee": employee,
			"docstatus": 1,
			"balance_amount": (">", 0),
		},
		fields=["name", "loan_product", "balance_amount"],
		order_by="creation asc",
	)

	# Build pending loans table
	if pending_loans:
		loans_html = """
			<table style='width:100%; border-collapse: collapse;'>
			<tr>
				<th style='text-align:left; padding: 8px; border-bottom:1px solid #ddd;'>Loan Product</th>
				<th style='text-align:left; padding: 8px; border-bottom:1px solid #ddd;'>Reference</th>
				<th style='text-align:left; padding: 8px; border-bottom:1px solid #ddd;'>Balance Amount</th>
				<th style='text-align:left; padding: 8px; border-bottom:1px solid #ddd;'>Closing Date</th>
			</tr>
		"""

		for loan in pending_loans:
			# Fetch last Loan Request Repayment Schedule date
			schedule = frappe.get_all(
				"Loan Request Repayment Schedule",
				filters={"parent": loan["name"], "is_accrued": 0},
				fields=["payment_date"],
				order_by="payment_date desc",
				limit_page_length=1
			)

			last_payment_date = (
				formatdate(schedule[0]["payment_date"], "dd-MMM-yyyy")
				if schedule else "N/A"
			)

			link = f"""<a href="/app/loan-request/{loan['name']}" target="_blank">
						{loan['name']}
					</a>"""

			loans_html += f"""
				<tr>
					<td style='padding: 8px; border-bottom:1px solid #ddd;'>{loan['loan_product']}</td>
					<td style='padding: 8px; border-bottom:1px solid #ddd;'>{link}</td>
					<td style='padding: 8px; border-bottom:1px solid #ddd;'>{loan['balance_amount']}</td>
					<td style='padding: 8px; border-bottom:1px solid #ddd;'>{last_payment_date}</td>
				</tr>
			"""

		loans_html += "</table>"

	else:
		loans_html = "No Pending Loans"

	return loans_html

@frappe.whitelist()
def get_pending_loans_with_dates(employee):
	from frappe.utils import formatdate

	loans = frappe.get_list(
		"Loan Request",
		filters={
			"employee": employee,
			"docstatus": 1,
			"balance_amount": (">", 0)
		},
		fields=["name", "loan_product", "balance_amount"],
		order_by="creation asc",
	)

	results = []

	for loan in loans:
		schedule = frappe.get_all(
			"Loan Request Repayment Schedule",
			filters={"parent": loan["name"], "is_accrued": 0},
			fields=["payment_date"],
			order_by="payment_date desc",
			limit_page_length=1
		)

		last_payment_date = schedule[0].payment_date if schedule else None

		js_date = (
			formatdate(schedule[0]["payment_date"], "dd-MMM-yyyy")
			if schedule else "N/A"
		)
		results.append({
			"name": loan.name,
			"loan_product": loan.loan_product,
			"balance_amount": loan.balance_amount,
			"last_payment_date": last_payment_date,
			"js_date": js_date,
		})

	return results



@frappe.whitelist()
def check_pending_loans(employee, current_name=None):
	filters = {
		"employee": employee,
		"docstatus": 1,
		"balance_amount": (">",0)
	}
	if current_name:
		filters["name"] = ["!=", current_name]

	pending = frappe.get_list(
		"Loan Request",
		filters=filters,
		fields=["name"],
		order_by="creation asc",
	)

	return {
		"has_pending": True if pending else False
	}

@frappe.whitelist()
def preview_repayment_change(
	loan_name,
	new_amount,
	effective_date
):

	loan = frappe.get_doc("Loan Request", loan_name)

	remaining_rows = []

	balance = loan.balance_amount

	start_date = getdate(effective_date)

	while balance > 0:

		amount = min(flt(new_amount), balance)

		remaining_rows.append({
			"payment_date": start_date.strftime("%d-%m-%Y"),
			"amount": amount,
			"status": "New"
		})

		balance -= amount
		start_date = add_single_month(start_date)

	return remaining_rows


@frappe.whitelist()
def change_repayment_amount(
	loan_name,
	new_amount,
	effective_date
):

	loan = frappe.get_doc("Loan Request", loan_name)

	new_amount = flt(new_amount)

	old_amount = loan.repayment_amount

	future_rows = []
	accrued_rows = []

	for row in loan.repayment_schedule:
		if row.is_accrued:
			accrued_rows.append(row)
		else:
			future_rows.append(row)

	if not future_rows:
		frappe.throw("No future schedules available.")

	first_future_date = getdate(effective_date)

	remaining_balance = loan.balance_amount

	loan.repayment_amount = new_amount

	rebuilt_rows = []

	payment_date = first_future_date

	while remaining_balance > 0:

		interest_amount = flt(
			remaining_balance *
			flt(loan.rate_of_interest) /
			(12 * 100)
		)

		principal_amount = new_amount - interest_amount

		if principal_amount <= 0:
			frappe.throw(
				"Repayment amount too small to cover interest."
			)

		if principal_amount > remaining_balance:
			principal_amount = remaining_balance

		total_payment = principal_amount + interest_amount

		remaining_balance -= principal_amount

		rebuilt_rows.append({
			"payment_date": payment_date,
			"principal_amount": principal_amount,
			"interest_amount": interest_amount,
			"total_payment": total_payment,
			"balance_loan_amount": remaining_balance
		})

		payment_date = add_single_month(payment_date)

	existing_rows = []

	for row in accrued_rows:

		existing_rows.append({
			"doctype": "Loan Request Repayment Schedule",
			"payment_date": row.payment_date,
			"principal_amount": row.principal_amount,
			"interest_amount": row.interest_amount,
			"total_payment": row.total_payment,
			"balance_loan_amount": row.balance_loan_amount,
			"is_accrued": row.is_accrued,
			"paid_amount": row.paid_amount
		})

	loan.set("repayment_schedule", [])

	for row in existing_rows:
		loan.append("repayment_schedule", row)

	for row in rebuilt_rows:
		loan.append("repayment_schedule", row)

	loan.save(ignore_permissions=True)

	frappe.db.commit()

	return "Repayment schedule updated successfully."