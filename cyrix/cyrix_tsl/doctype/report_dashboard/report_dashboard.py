# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReportDashboard(Document):
	pass

def weekly_sales(self):

    company = self.company
    from_date = self.from_date
    to_date = self.to_date
    brnch = self.branch
    sales_person = getattr(self, "sales_person", None)
    department = getattr(self, "cost_center", None)

    REPAIR_QT = ["Customer Quotation - Repair"]
    SUPPLY_QT = ["Customer Quotation - Supply"]

    def init_weeks():
        return {
            "Week 1": 0,
            "Week 2": 0,
            "Week 3": 0,
            "Week 4": 0,
            "Week 5": 0
        }

    data = {}

    # ---------------------------------
    # INITIALIZE SALES PERSON
    # ---------------------------------
    def ensure_sales_person(person):

        if person not in data:

            data[person] = {
                "PO Count Repair": init_weeks(),
                "PO Count Supply": init_weeks(),
                "PO Repair Amount": init_weeks(),
                "PO Supply Amount": init_weeks(),
                "Invoice Repair": init_weeks(),
                "Invoice Supply": init_weeks(),
                "Collection Repair": init_weeks(),
                "Collection Supply": init_weeks(),
            }

    # ---------------------------------
    # COMMON ADD FUNCTION
    # ---------------------------------
    def add_data(rows, count_key=None, amount_key=None):

        for row in rows:

            person = row.get("sales_person") or "Unassigned"
            week = row.get("week_name")
            qt = row.get("quotation_type") or ""

            ensure_sales_person(person)

            # -----------------------------
            # PO DATA
            # -----------------------------
            if count_key and amount_key:

                if qt in REPAIR_QT:

                    data[person]["PO Count Repair"][week] += row.get(count_key, 0)
                    data[person]["PO Repair Amount"][week] += row.get(amount_key, 0)

                elif qt in SUPPLY_QT:

                    data[person]["PO Count Supply"][week] += row.get(count_key, 0)
                    data[person]["PO Supply Amount"][week] += row.get(amount_key, 0)

    # ---------------------------------
    # PO DATA
    # ---------------------------------
    po_condition = ""
    po_values = [company, from_date, to_date]

    if brnch:
        po_condition += " AND q.branch = %s "
        po_values.append(brnch)

    if sales_person:
        po_condition += " AND q.sales_person = %s "
        po_values.append(sales_person)

    po_data = frappe.db.sql(f"""

        SELECT

            q.sales_person,
            q.quotation_type,

            CASE
                WHEN DAY(q.approval_date) BETWEEN 1 AND 7 THEN 'Week 1'
                WHEN DAY(q.approval_date) BETWEEN 8 AND 14 THEN 'Week 2'
                WHEN DAY(q.approval_date) BETWEEN 15 AND 21 THEN 'Week 3'
                WHEN DAY(q.approval_date) BETWEEN 22 AND 28 THEN 'Week 4'
                ELSE 'Week 5'
            END AS week_name,

            COUNT(DISTINCT q.name) AS total_count,
            SUM(q.grand_total) AS total_amount

        FROM `tabQuotation` q

        WHERE q.company = %s
            AND q.approval_date BETWEEN %s AND %s
            AND q.docstatus = 1
            AND IFNULL(q.sales_person,'') NOT IN ('Jubil')
            {po_condition}

        GROUP BY
            q.sales_person,
            q.quotation_type,
            week_name

    """, po_values, as_dict=True)

    add_data(po_data, "total_count", "total_amount")

    # ---------------------------------
    # SALES INVOICE
    # ---------------------------------
    si_condition = ""
    si_values = [company, from_date, to_date]

    if brnch:
        si_condition += " AND si.branch = %s "
        si_values.append(brnch)

    if sales_person:
        si_condition += " AND si.sales_person = %s "
        si_values.append(sales_person)

    if department:
        si_condition += " AND si.cost_center = %s "
        si_values.append(department)

    si_data = frappe.db.sql(f"""

        SELECT

            si.sales_person,
            si.cost_center AS department,

            CASE
                WHEN DAY(si.posting_date) BETWEEN 1 AND 7 THEN 'Week 1'
                WHEN DAY(si.posting_date) BETWEEN 8 AND 14 THEN 'Week 2'
                WHEN DAY(si.posting_date) BETWEEN 15 AND 21 THEN 'Week 3'
                WHEN DAY(si.posting_date) BETWEEN 22 AND 28 THEN 'Week 4'
                ELSE 'Week 5'
            END AS week_name,

            SUM(si.grand_total) AS total_amount

        FROM `tabSales Invoice` si

        WHERE si.company = %s
            AND si.posting_date BETWEEN %s AND %s
            AND si.docstatus = 1
            AND si.is_return = 0
            AND IFNULL(si.sales_person,'') NOT IN ('Jubil')
            {si_condition}

        GROUP BY
            si.sales_person,
            si.cost_center,
            week_name

    """, si_values, as_dict=True)

    for row in si_data:

        person = row.get("sales_person") or "Unassigned"
        dept = (row.get("department") or "").lower()
        week = row.get("week_name")

        ensure_sales_person(person)

        if "repair" in dept:
            data[person]["Invoice Repair"][week] += row.get("total_amount", 0)

        elif "supply" in dept:
            data[person]["Invoice Supply"][week] += row.get("total_amount", 0)

    # ---------------------------------
    # COLLECTION
    # ---------------------------------
    col_condition = ""
    col_values = [company, from_date, to_date]

    if brnch:
        col_condition += " AND si.branch = %s "
        col_values.append(brnch)

    if sales_person:
        col_condition += " AND si.sales_person = %s "
        col_values.append(sales_person)

    if department:
        col_condition += " AND si.cost_center = %s "
        col_values.append(department)

    col_data = frappe.db.sql(f"""

        SELECT

            si.sales_person,
            si.cost_center AS department,

            CASE
                WHEN DAY(pe.posting_date) BETWEEN 1 AND 7 THEN 'Week 1'
                WHEN DAY(pe.posting_date) BETWEEN 8 AND 14 THEN 'Week 2'
                WHEN DAY(pe.posting_date) BETWEEN 15 AND 21 THEN 'Week 3'
                WHEN DAY(pe.posting_date) BETWEEN 22 AND 28 THEN 'Week 4'
                ELSE 'Week 5'
            END AS week_name,

            SUM(per.allocated_amount) AS total_amount

        FROM `tabPayment Entry` pe

        INNER JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name

        INNER JOIN `tabSales Invoice` si
            ON si.name = per.reference_name

        WHERE pe.company = %s
            AND pe.posting_date BETWEEN %s AND %s
            AND pe.docstatus = 1
            AND IFNULL(si.sales_person,'') NOT IN ('Jubil')
            {col_condition}

        GROUP BY
            si.sales_person,
            si.cost_center,
            week_name

    """, col_values, as_dict=True)

    for row in col_data:

        person = row.get("sales_person") or "Unassigned"
        dept = (row.get("department") or "").lower()
        week = row.get("week_name")

        ensure_sales_person(person)

        if "repair" in dept:
            data[person]["Collection Repair"][week] += row.get("total_amount", 0)

        elif "supply" in dept:
            data[person]["Collection Supply"][week] += row.get("total_amount", 0)

    # ---------------------------------
    # HTML OUTPUT
    # ---------------------------------
    html = ""

    for person, metrics in data.items():

        html += f"""

        <table border="1"
            style="
                width:100%;
                border-collapse:collapse;
                margin-bottom:30px;
                font-size:12px;
            ">

            <tr style="background-color:#F0F8FF;">
                <th style="text-align:center;" colspan="7">
                    {person}
                </th>
            </tr>

            <tr style="background-color:#F0F8FF;">

                <th>Metrics</th>
                <th>Week 1</th>
                <th>Week 2</th>
                <th>Week 3</th>
                <th>Week 4</th>
                <th>Week 5</th>
                <th>Total</th>

            </tr>

        """

        po_repair = metrics["PO Repair Amount"]
        po_supply = metrics["PO Supply Amount"]

        inv_repair = metrics["Invoice Repair"]
        inv_supply = metrics["Invoice Supply"]

        col_repair = metrics["Collection Repair"]
        col_supply = metrics["Collection Supply"]

        for label, weeks in metrics.items():

            total = (
                weeks["Week 1"] +
                weeks["Week 2"] +
                weeks["Week 3"] +
                weeks["Week 4"] +
                weeks["Week 5"]
            )

            html += f"""

            <tr>

                <td>
                    <b>{label}</b>
                </td>

                <td>{weeks['Week 1']:,.0f}</td>
                <td>{weeks['Week 2']:,.0f}</td>
                <td>{weeks['Week 3']:,.0f}</td>
                <td>{weeks['Week 4']:,.0f}</td>
                <td>{weeks['Week 5']:,.0f}</td>

                <td style="font-weight:bold;">
                    {total:,.0f}
                </td>

            </tr>

            """

            # ---------------------------------
            # PO SUBTOTAL
            # ---------------------------------
            if label == "PO Supply Amount":

                po_total = (
                    sum(po_repair.values()) +
                    sum(po_supply.values())
                )

                html += f"""

                <tr style="background:#e6e6e6;font-weight:bold;">

                    <td>PO Subtotal</td>

                    <td>{po_repair['Week 1'] + po_supply['Week 1']:,.0f}</td>
                    <td>{po_repair['Week 2'] + po_supply['Week 2']:,.0f}</td>
                    <td>{po_repair['Week 3'] + po_supply['Week 3']:,.0f}</td>
                    <td>{po_repair['Week 4'] + po_supply['Week 4']:,.0f}</td>
                    <td>{po_repair['Week 5'] + po_supply['Week 5']:,.0f}</td>

                    <td>{po_total:,.0f}</td>

                </tr>

                """

            # ---------------------------------
            # INVOICE SUBTOTAL
            # ---------------------------------
            if label == "Invoice Supply":

                inv_total = (
                    sum(inv_repair.values()) +
                    sum(inv_supply.values())
                )

                html += f"""

                <tr style="background:#e6e6e6;font-weight:bold;">

                    <td>Invoice Subtotal</td>

                    <td>{inv_repair['Week 1'] + inv_supply['Week 1']:,.0f}</td>
                    <td>{inv_repair['Week 2'] + inv_supply['Week 2']:,.0f}</td>
                    <td>{inv_repair['Week 3'] + inv_supply['Week 3']:,.0f}</td>
                    <td>{inv_repair['Week 4'] + inv_supply['Week 4']:,.0f}</td>
                    <td>{inv_repair['Week 5'] + inv_supply['Week 5']:,.0f}</td>

                    <td>{inv_total:,.0f}</td>

                </tr>

                """

            # ---------------------------------
            # COLLECTION SUBTOTAL
            # ---------------------------------
            if label == "Collection Supply":

                col_total = (
                    sum(col_repair.values()) +
                    sum(col_supply.values())
                )

                html += f"""

                <tr style="background:#e6e6e6;font-weight:bold;">

                    <td>Collection Subtotal</td>

                    <td>{col_repair['Week 1'] + col_supply['Week 1']:,.0f}</td>
                    <td>{col_repair['Week 2'] + col_supply['Week 2']:,.0f}</td>
                    <td>{col_repair['Week 3'] + col_supply['Week 3']:,.0f}</td>
                    <td>{col_repair['Week 4'] + col_supply['Week 4']:,.0f}</td>
                    <td>{col_repair['Week 5'] + col_supply['Week 5']:,.0f}</td>

                    <td>{col_total:,.0f}</td>

                </tr>

                """

        html += "</table>"

    return html
    
def daily_sales(self):
    company = self.company
    from_date = self.from_date
    to_date = self.to_date
    brnch = self.branch
    sales_person = getattr(self, "sales_person", None)
    department = getattr(self, "department", None)

    # -------------------------
    # DATA STRUCTURES
    # -------------------------
    data = {}
    all_dates = set()

    def ensure_sales_person(person):
        if person not in data:
            data[person] = {
                "PO Count Repair": {},
                "PO Count Supply": {},
                "PO Repair Amount": {},
                "PO Supply Amount": {},
                "Invoice Repair": {},
                "Invoice Supply": {},
                "Collection Repair": {},
                "Collection Supply": {},
            }

    def init_date(person, date):
        for key in data[person]:
            if date not in data[person][key]:
                data[person][key][date] = 0

    # -------------------------
    # COMMON FILTERS
    # -------------------------
    def build_conditions(alias):
        condition = ""
        values = []

        if brnch:
            field = "branch" if alias == "q" else "branch"
            condition += f" AND {alias}.{field} = %s "
            values.append(brnch)

        if sales_person:
            condition += f" AND {alias}.sales_person = %s "
            values.append(sales_person)

        if department:
            condition += f" AND {alias}.department = %s "
            values.append(department)

        return condition, values

    # WO + NER DATA (FIXED)
    # -------------------------
    wo_data = frappe.db.sql("""
        SELECT
            COALESCE(sales_person, 'Unassigned') AS sales_person,
            COUNT(name) AS total_wo,
            SUM(
                CASE
                    WHEN status_cap_date IS NOT NULL
                        AND status_cap_date != ''
                    THEN 1 ELSE 0
                END
            ) AS ner_count
        FROM `tabJob Order Data`
        WHERE DATE(received_date) BETWEEN %s AND %s
        GROUP BY sales_person
    """, (from_date, to_date), as_dict=True)

    wo_map = {}
    for row in wo_data:
        wo_map[row["sales_person"]] = {
            "wo": row.get("total_wo", 0),
            "ner": row.get("ner_count", 0)
        }

    # -------------------------
    # SO DATA
    # -------------------------
    so_data = frappe.db.sql("""
        SELECT
            COALESCE(sales_person, 'Unassigned') AS sales_person,
            COUNT(name) AS total_so
        FROM `tabSupply Order Data`
        WHERE DATE(received_date) BETWEEN %s AND %s
        GROUP BY sales_person
    """, (from_date, to_date), as_dict=True)

    so_map = {}

    for row in so_data:
        so_map[row["sales_person"]] = {
            "so": row.get("total_so", 0)
        }
    # -------------------------
    # PO DATA
    # -------------------------
    po_condition, po_extra = build_conditions("q")

    po_data = frappe.db.sql(f"""
        SELECT
            q.sales_person,
            q.quotation_type,
            DATE(q.approval_date) as date,
            COUNT(q.name) AS total_count,
            SUM(
                CASE
                    WHEN YEAR(q.creation) >= 2026 THEN
                        IFNULL(qi.amount, 0)
                    ELSE COALESCE(IFNULL(q.grand_total, 0))
                END
            ) AS total_amount
        FROM `tabQuotation` q
        LEFT JOIN `tabQuotation Item` qi ON qi.parent = q.name
        WHERE q.company = %s
        AND q.approval_date BETWEEN %s AND %s
        AND q.docstatus = 1
        AND IFNULL(q.sales_person,'') NOT IN ('Jubil')
        {po_condition}
        GROUP BY q.sales_person, date
    """, [company, from_date, to_date] + po_extra, as_dict=True)

    for row in po_data:
        person = row.get("sales_person") or "Unassigned"
        dept = (row.get("quotation_type") or "").lower()
        date = str(row.get("date"))

        ensure_sales_person(person)
        init_date(person, date)
        all_dates.add(date)

        if "repair" in dept:
            data[person]["PO Count Repair"][date] += row.get("total_count", 0)
            data[person]["PO Repair Amount"][date] += row.get("total_amount", 0)
        elif "supply" in dept:
            data[person]["PO Count Supply"][date] += row.get("total_count", 0)
            data[person]["PO Supply Amount"][date] += row.get("total_amount", 0)

    # -------------------------
    # SALES INVOICE
    # -------------------------
    si_condition, si_extra = build_conditions("si")

    si_data = frappe.db.sql(f"""
        SELECT
            si.cost_center,
            si.sales_person,
            DATE(si.posting_date) as date,
            SUM(si.grand_total) AS total_amount
        FROM `tabSales Invoice` si
        WHERE si.company = %s
        AND si.posting_date BETWEEN %s AND %s
        AND si.docstatus = 1
        AND si.is_return = 0
        AND IFNULL(si.sales_person,'') NOT IN ('Michael Veniston','Dhinesh','MOHAMED MOSAAD ALY DIAB','MUHAMMAD UMAR')
        {si_condition}
        GROUP BY si.cost_center, si.sales_person, date
    """, [company, from_date, to_date] + si_extra, as_dict=True)

    for row in si_data:
        person = row.get("sales_person") or "Unassigned"
        dept = (row.get("cost_center") or "").lower()
        date = str(row.get("date"))

        ensure_sales_person(person)
        init_date(person, date)
        all_dates.add(date)

        if "repair" in dept:
            data[person]["Invoice Repair"][date] += row.get("total_amount", 0)
        elif "supply" in dept:
            data[person]["Invoice Supply"][date] += row.get("total_amount", 0)

    # -------------------------
    # COLLECTION
    # -------------------------
    col_condition, col_extra = build_conditions("si")

    col_data = frappe.db.sql(f"""
        SELECT
            si.cost_center,
            si.sales_person,
            DATE(pe.posting_date) as date,
            SUM(per.allocated_amount) AS total_amount
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        INNER JOIN `tabSales Invoice` si ON si.name = per.reference_name
        WHERE pe.company = %s
        AND pe.posting_date BETWEEN %s AND %s
        AND pe.docstatus = 1
        AND IFNULL(si.sales_person,'') NOT IN ('Michael Veniston','Dhinesh','MOHAMED MOSAAD ALY DIAB','MUHAMMAD UMAR')
        {col_condition}
        GROUP BY si.cost_center, si.sales_person, date
    """, [company, from_date, to_date] + col_extra, as_dict=True)

    for row in col_data:
        person = row.get("sales_person") or "Unassigned"
        dept = (row.get("department") or "").lower()
        date = str(row.get("date"))

        ensure_sales_person(person)
        init_date(person, date)
        all_dates.add(date)

        if "repair" in dept:
            data[person]["Collection Repair"][date] += row.get("total_amount", 0)
        elif "supply" in dept:
            data[person]["Collection Supply"][date] += row.get("total_amount", 0)

    # -------------------------
    # HTML OUTPUT
    # -------------------------
    html = ""
    sorted_dates = sorted(all_dates)

    for person, metrics in data.items():
        wo_info = wo_map.get(person, {"wo": 0, "ner": 0})
        so_info = so_map.get(person, {"so": 0, "ner": 0})

        po_repair = metrics["PO Repair Amount"]
        po_supply = metrics["PO Supply Amount"]

        inv_repair = metrics["Invoice Repair"]
        inv_supply = metrics["Invoice Supply"]

        col_repair = metrics["Collection Repair"]
        col_supply = metrics["Collection Supply"]

        html += f"""
        <table border="1" style="width:100%; border-collapse:collapse; margin-bottom:30px;">
            <tr style="background:#d9edf7;">
                <th colspan="{len(sorted_dates)+1}">{person}</th>
            </tr>
            <tr style="background:#f2f2f2;">
                <th>Metrics</th>
        """

        for d in sorted_dates:
            html += f"<th>{d}</th>"
        html += "</tr>"

        # ---------------- WO ROW ----------------
        html += "<tr style='background:#f9f9f9;'>"
        html += "<td><b>JO</b></td>"
        for d in sorted_dates:
            html += f"<td>{wo_info['wo']}</td>"
        html += "</tr>"
        # ---------------- SO ROW ----------------
        html += "<tr style='background:#f9f9f9;'>"
        html += "<td><b>SO</b></td>"

        for d in sorted_dates:
            html += f"<td>{so_info['so']}</td>"

        html += "</tr>"
        # ---------------- NER ROW ----------------
        html += "<tr style='background:#f9f9f9;'>"
        html += "<td><b>NER</b></td>"
        for d in sorted_dates:
            html += f"<td>{wo_info['ner']}</td>"
        html += "</tr>"

        # ---------------- PO SUBTOTAL ----------------
        html += "<tr style='background:#e6e6e6;font-weight:bold;'>"
        html += "<td>PO Subtotal</td>"
        for d in sorted_dates:
            html += f"<td>{po_repair.get(d,0) + po_supply.get(d,0):,.0f}</td>"
        html += "</tr>"

        # ---------------- INVOICE SUBTOTAL ----------------
        html += "<tr style='background:#e6e6e6;font-weight:bold;'>"
        html += "<td>Invoice Subtotal</td>"
        for d in sorted_dates:
            html += f"<td>{inv_repair.get(d,0) + inv_supply.get(d,0):,.0f}</td>"
        html += "</tr>"

        # ---------------- COLLECTION SUBTOTAL ----------------
        html += "<tr style='background:#e6e6e6;font-weight:bold;'>"
        html += "<td>Collection Subtotal</td>"
        for d in sorted_dates:
            html += f"<td>{col_repair.get(d,0) + col_supply.get(d,0):,.0f}</td>"
        html += "</tr>"

        html += "</table>"

    return html


import frappe
from datetime import datetime
import calendar
from frappe.utils import getdate

@frappe.whitelist()
def get_amc(company, branch):
	try:
		today = datetime.now().date()
		formatted_date = today.strftime("%d-%m-%Y")
		current_year = today.year

		months = list(calendar.month_name)[1:]
		current_month = today.month
		last_12_months = [
			(months[(current_month - i - 1) % 12],
			 (current_year if current_month - i > 0 else current_year - 1))
			for i in range(11, -1, -1)
		]

		sales_people = frappe.get_all(
		"Sales Person",
		filters={"name": ["!=", "Sales Team"],"custom_branch":branch}
		)

		# target_sales = {
		#     "Cyrix TSL - Kuwait": [
		#         "Yazeed", "Jubil"

		#     ]
		# }

		html = []

		# ===== Header with Logo and Flag =====
		html.append(render_header(company, formatted_date))

		# ===== Initialize cumulative totals =====
		total_quoted_wo = 0
		total_approved_wo = 0
		total_days_wo = 0
		wo_count_total = 0

		# First pass: Calculate cumulative totals
		for sp in sales_people:
			# if sp.name not in target_sales.get(company, []):
			#     continue

			# Get totals for this salesperson
			totals = calculate_salesperson_totals(sp, company, last_12_months)

			total_quoted_wo += totals.get('quoted_wo', 0)
			total_approved_wo += totals.get('approved_wo', 0)
			total_days_wo += totals.get('days_wo', 0)
			wo_count_total += totals.get('wo_count', 0)

		# Calculate cumulative percentages and averages
		total_per_wo = (total_approved_wo / total_quoted_wo * 100) if total_quoted_wo else 0
		avg_days_wo = round(total_days_wo / wo_count_total) if wo_count_total > 0 else 0

		# ===== Add Cumulative Table after Header =====
		html.append(render_cumulative_table(
			total_quoted_wo, total_approved_wo, total_per_wo, avg_days_wo
		))

		# ===== Main Table Header =====
		html.append(render_table_header(company))

		# Reset totals for display in main table
		total_quoted_wo = 0
		total_approved_wo = 0
		total_days_wo = 0

		# Second pass: Generate individual salesperson rows
		for sp in sales_people:
			# if sp.name not in target_sales.get(company, []):
			#     continue

			# Generate rows and collect data
			rows_result = generate_salesperson_rows(sp, company, last_12_months)
			if rows_result and len(rows_result) > 1:
				html.extend(rows_result[0])  # HTML rows

				# Get totals from the second return value
				if len(rows_result) > 1:
					totals = rows_result[1]
					total_quoted_wo += totals.get('quoted_wo', 0)
					total_approved_wo += totals.get('approved_wo', 0)
					total_days_wo += totals.get('days_wo', 0)

		# Calculate percentages for main table
		total_per_wo = (total_approved_wo / total_quoted_wo * 100) if total_quoted_wo else 0

		html.append("</table>")

		# ===== Second Section =====
		# html.append(render_header2(company, formatted_date))
		# html.append(render_table_header2(company))

		# # ===== Total Row =====
		# html.append(f"""
		# <tr style="font-weight:bold;background-color:#f2f2f2">
		#     <td style="background-color:#D3D3D3"><center>{total_quoted_wo:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{total_approved_wo:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{round(total_per_wo)}%</center></td>
		# </tr>
		# """)
		# html.append("</table>")

		return "".join(html)
	except Exception as e:
		frappe.log_error(f"Error in get_sales_kuwait: {str(e)}", "Sales Report Error")
		return f"<div style='color:red; padding:20px;'>Error generating report: {str(e)}</div>"

def calculate_salesperson_totals(sp, company, months):
	"""Calculate totals for a salesperson without generating HTML."""
	try:
		total_quoted = 0
		total_approved = 0
		total_days_wo = 0
		wo_count = 0

		for month_name, year in months:
			try:
				month_num = datetime.strptime(month_name, "%B").month
				first_day = datetime(year, month_num, 1).date()
				last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

				quoted, approved, quoted2, approved2, wod_hrs, sod_hrs = get_monthly_sales(
					sp.name, first_day, last_day, company
				)

				total_quoted += quoted or 0
				total_approved += approved or 0
				total_days_wo += wod_hrs or 0

				if wod_hrs > 0:
					wo_count += 1

			except Exception as e:
				frappe.log_error(f"Error in calculate_salesperson_totals for {sp.name}: {str(e)}", "Totals Calculation Error")
				continue

		return {
			'quoted_wo': total_quoted,
			'approved_wo': total_approved,
			'days_wo': total_days_wo,
			'wo_count': wo_count,
		}
	except Exception as e:
		frappe.log_error(f"Error in calculate_salesperson_totals for {sp.name}: {str(e)}", "Totals Calculation Error")
		return {}

def render_cumulative_table(q_wo, a_wo, p_wo, d_wo):
	"""Render the cumulative summary table."""

	# Determine color based on percentage
	color_wo = get_color(p_wo)

	return f"""
	<br>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse; margin-top:10px;">
		<tr>
			<td colspan="3" align="center" style="background-color:#0e86d4; color:white; font-size:14px; font-weight:bold; padding:8px;">
				CUMULATIVE SUMMARY
			</td>
		</tr>
		<tr style="background-color:#145da0; color:white; font-weight:bold;">
			<td colspan="3" style="text-align:center; padding:8px; font-size:12px;color:white;">MAINTENANCE CONTRACT</td>
		</tr>
		<tr style="background-color:#f0f0f0; font-weight:bold;">
			<td style="padding:8px; text-align:center; font-size:11px;">Quoted (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Approved (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">% Approved</td>
		</tr>
		<tr style="font-size:14px;">
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{q_wo:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{a_wo:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:{color_wo}; font-weight:bold;">{round(p_wo)}%</td>
		</tr>
	</table>
	<br>
	"""

def render_header(company, formatted_date):
	"""Generate the report header HTML."""
	logo_path = "/files/Cyrix Logo.png"
	country_label = "Kuwait" if "Kuwait" in company else "UAE"

	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td style="width:30%; border-color:#000000;"><img src="{logo_path}" width="200"></td>
			<td style="width:40%; border-color:#000000; font-size:16px; color:#055c9d; text-align:center; font-weight:bold;">
				<br>TSL Company<br>AMC Approval Percentage by Amount
			</td>
			<td style="width:30%; border-color:#000000;">
				<center><img src="/files/kuwait flag.jpg" width="140" height="80"></center>
			</td>
		</tr>
	</table>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td align="left" style="width:30%;border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Branch - {country_label}
			</td>
			<td align="center" style="width:40%;border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Currency - KWD
			</td>
			<td align="right" style="width:30%;border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Generation Date: {formatted_date}
			</td>
		</tr>
	</table>
	"""

def render_header2(company, formatted_date):
	"""Generate the report header HTML."""
	return f"""
	<br>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td colspan="7" align="center" style="border-color:#000000; background-color:#0e86d4; color:white; font-size:14px; font-weight:bold;">
				CUMULATIVE SUMMARY
			</td>
		</tr>
	</table>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
	"""

def render_table_header(company):
	"""Render the table column headers depending on company."""
	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse; margin-top:10px;">
		<tr>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="16%"></td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="16%"></td>
			<td colspan="4" style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;">MAINTENANCE CONTRACT</td>
		</tr>
		<tr>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="16%">Sales</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="16%">Quoted Month</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="17%">Quoted</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="17%">Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="17%">% of Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="17%">Approval Days</td>
		</tr>
	"""

def render_table_header2(company):
	"""Render the table column headers depending on company."""
	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td colspan="3" style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;">JOB ORDER</td>
			<td colspan="4" style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;">SUPPLY ORDER</td>
		</tr>
		<tr>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Quoted</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">% of Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Quoted</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">% of Approved</td>
		</tr>
	"""

def generate_salesperson_rows(sp, company, months):
	"""Generate monthly sales data for a single salesperson."""
	try:
		rows = []
		total_quoted = 0
		total_approved = 0
		total_days_wo = 0
		wo_count = 0

		for month_name, year in months:
			try:
				month_num = datetime.strptime(month_name, "%B").month
				first_day = datetime(year, month_num, 1).date()
				last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

				quoted, approved, quoted2, approved2, wod_hrs, sod_hrs = get_monthly_sales(
					sp.name, first_day, last_day, company
				)

				total_quoted += quoted or 0
				total_approved += approved or 0
				total_days_wo += wod_hrs or 0

				if wod_hrs > 0:
					wo_count += 1

				# Calculate percentage
				percent1 = round((approved / quoted) * 100) if quoted and quoted > 0 else 0

				# Set color based on percentage
				color4 = get_color(percent1)

				rows.append(f"""
				<tr>
					<td style="text-align:center; border-bottom:hidden; color:#145da0; font-weight:bold;">{sp.name if month_name == "June" else ''}</td>
					<td style="font-size:10px; text-align:center; font-weight:bold;">{month_name}</td>
					<td style="font-size:10px; text-align:center;">{quoted:,.0f}</td>
					<td style="font-size:10px; text-align:center;">{approved:,.0f}</td>
					<td style="font-size:10px; text-align:center; background-color:{color4}; font-weight:bold;">{percent1}%</td>
					<td style="font-size:10px; text-align:center;">{wod_hrs}</td>
				</tr>

				""")
			except Exception as e:
				frappe.log_error(f"Error processing month {month_name} for {sp.name}: {str(e)}", "Month Processing Error")
				continue

		# Calculate totals
		total_percent = round((total_approved / total_quoted) * 100) if total_quoted and total_quoted > 0 else 0

		# Get color for totals
		color1 = get_color(total_percent)

		# Calculate average days
		avg_days_wo = round(total_days_wo / wo_count) if wo_count > 0 else 0

		rows.append(f"""
		<tr>
			<td></td>
			<td><center><b>Total</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_quoted:,.0f}</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_approved:,.0f}</b></center></td>
			<td style="background-color:{color1};"><center><b>{total_percent}%</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{avg_days_wo}</b></center></td>
		</tr>
		<tr><td colspan="6"><center><b>-</b></center></td></tr>
		""")

		# Return both rows and totals
		totals = {
			'quoted_wo': total_quoted,
			'approved_wo': total_approved,
			'days_wo': avg_days_wo,
		}

		return [rows, totals]
	except Exception as e:
		frappe.log_error(f"Error in generate_salesperson_rows for {sp.name}: {str(e)}", "Salesperson Error")
		return [[], {}]

def get_color(percentage):
	"""Return color based on percentage."""
	if percentage < 60:
		return "#FF7074"
	elif percentage < 80:
		return "#FFFF8F"
	else:
		return "#98FB98"

def get_monthly_sales(sales_user, from_date, to_date, company):
	"""
	Calculates total quoted and approved amounts per distinct maintenance contract,
	with correct discount handling. Uses net_amount for 2026 onwards.

	Wherever a Quotation Item's maintenance_contract is referenced, it falls
	back to the parent Quotation's maintenance_contract whenever
	maintenance_contract is empty/blank:
		COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract)
	"""
	try:
		if not sales_user:
			return 0, 0, 0, 0, 0, 0

		# Get distinct Maintenance Contract list (falls back to header-level field when blank)
		wod_list = frappe.db.sql("""
			SELECT DISTINCT
				COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) AS jo
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi
				ON q.name = qi.parent
			WHERE q.sales_person = %s
				AND q.company = %s
				AND q.workflow_state IN (
					'Approved by Customer',
					'Quoted to Customer',
					'Rejected by Customer'
				)
				AND q.quotation_type IN (
					'Customer Quotation - MC',
					'Customer Quotation - MC - Revised'
				)
				AND q.transaction_date BETWEEN %s AND %s
				AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) IS NOT NULL
				AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		# Get Maintenance Contract count
		w_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract)) as ct
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - MC', 'Customer Quotation - MC - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) IS NOT NULL
			AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		wod_count = w_count[0]["ct"] if w_count else 0

		total_quoted = 0
		total_approved = 0
		ddf1 = 0
		approved_count = 0

		# Process each Maintenance Contract
		for wod in wod_list:
			jo = wod["jo"]

			# Get transaction year
			year_check = frappe.db.sql("""
				SELECT YEAR(q.transaction_date) as trans_year
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) = %s
				AND q.transaction_date BETWEEN %s AND %s
				LIMIT 1
			""", (sales_user, jo, from_date, to_date), as_dict=True)

			is_2026_or_later = year_check and year_check[0].get("trans_year", 0) >= 2026

			# Get Quoted Amount
			# if is_2026_or_later:
			quoted_rows = frappe.db.sql("""
				SELECT qi.net_amount as amount
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) = %s
				AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
				AND q.quotation_type IN ('Customer Quotation - MC','Customer Quotation - MC - Revised')
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user,jo, from_date, to_date), as_dict=True)
			if quoted_rows and quoted_rows[0].get("amount"):
				total_quoted += quoted_rows[0]["amount"] or 0




			# Check if approved
			rev_check = frappe.db.sql("""
				SELECT DISTINCT COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) AS jo
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND q.workflow_state IN ('Approved by Customer',"Quoted to Customer","Rejected by Customer")
				AND q.quotation_type IN ('Customer Quotation - MC','Customer Quotation - MC - Revised')
				AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) = %s
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user, jo, from_date, to_date), as_dict=True)

			if rev_check:
				# Get Approved Amount
				# if is_2026_or_later:
				approved_rows = frappe.db.sql("""
					SELECT SUM(qi.net_amount) as amount,
							q.transaction_date, q.approval_date
					FROM `tabQuotation` q
					INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
					WHERE q.sales_person = %s
					AND COALESCE(NULLIF(qi.maintenance_contract, ''), q.maintenance_contract) = %s
					AND q.workflow_state = 'Approved by Customer'
					AND q.quotation_type IN ('Customer Quotation - MC', 'Customer Quotation - MC - Revised')
					AND q.transaction_date BETWEEN %s AND %s
					GROUP BY q.name
				""", (sales_user, jo, from_date, to_date), as_dict=True)

				if approved_rows:
					for row in approved_rows:
						if row.get("approval_date") and row.get("transaction_date"):
							date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
							ddf1 += date_diff
							approved_count += 1
						total_approved += row.get("amount") or 0

		# SOD Section
		sod_list = frappe.db.sql("""
			SELECT DISTINCT qi.supply_order_data as sod
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.supply_order_data IS NOT NULL
			AND qi.supply_order_data != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		s_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT qi.supply_order_data) as sod
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.supply_order_data IS NOT NULL
			AND qi.supply_order_data != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		sod_count = s_count[0]["sod"] if s_count else 0

		total_quoted2 = 0
		total_approved2 = 0
		ddf2 = 0
		approved_count2 = 0

		# Process each SOD
		for s in sod_list:
			sod_no = s["sod"]

			# Get transaction year
			year_check = frappe.db.sql("""
				SELECT YEAR(q.transaction_date) as trans_year
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.supply_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
				LIMIT 1
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			is_2026_or_later = year_check and year_check[0].get("trans_year", 0) >= 2026

			# Get Quoted Amount
			# if is_2026_or_later:
			quoted_rows2 = frappe.db.sql("""
				SELECT q.name, SUM(qi.net_amount) as net_amount
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.supply_order_data = %s
				AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
				AND q.quotation_type IN ('Customer Quotation - Supply')
				AND q.transaction_date BETWEEN %s AND %s
				GROUP BY q.name
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			if quoted_rows2:
				for row in quoted_rows2:
					total_quoted2 += row.get("net_amount") or 0

			# Check if approved
			rev_check2 = frappe.db.sql("""
				SELECT DISTINCT qi.supply_order_data
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND q.workflow_state IN ('Approved by Customer')
				AND q.quotation_type IN ('Customer Quotation - Supply','Customer Quotation - S - Revised')
				AND qi.supply_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			if rev_check2:
				# Get Approved Amount
				# if is_2026_or_later:
				approved_rows2 = frappe.db.sql("""
					SELECT q.name, SUM(qi.net_amount) as net_amount,
							q.transaction_date, q.approval_date
					FROM `tabQuotation` q
					INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
					WHERE q.sales_person = %s
					AND qi.supply_order_data = %s
					AND q.workflow_state = 'Approved by Customer'
					AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
					AND q.transaction_date BETWEEN %s AND %s
					GROUP BY q.name
				""", (sales_user, sod_no, from_date, to_date), as_dict=True)

				if approved_rows2:
					for row in approved_rows2:
						if row.get("approval_date") and row.get("transaction_date"):
							date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
							ddf2 += date_diff
							approved_count2 += 1
						total_approved2 += row.get("net_amount") or 0

		# Calculate average days
		wod_hrs = round(ddf1 / approved_count) if approved_count > 0 else 0
		sod_hrs = round(ddf2 / approved_count2) if approved_count2 > 0 else 0

		return (
			round(total_quoted or 0),
			round(total_approved or 0),
			round(total_quoted2 or 0),
			round(total_approved2 or 0),
			wod_hrs,
			sod_hrs
		)
	except Exception as e:
		frappe.log_error(f"Error in get_monthly_sales for {sales_user}: {str(e)}", "Monthly Sales Error")
		return 0, 0, 0, 0, 0, 0