# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WOApproval(Document):
	pass

def weekly_sales(self):
    company = self.company
    from_date = self.from_date
    to_date = self.to_date
    brnch = self.branch
    sales_person = getattr(self, "sales_person", None)
    department = getattr(self, "department", None)

    # -------------------------
    # HELPER: Initialize weeks
    # -------------------------
    def init_weeks():
        return {"Week 1": 0, "Week 2": 0, "Week 3": 0, "Week 4": 0, "Week 5": 0}

    # -------------------------
    # MAIN DATA STRUCTURE
    # -------------------------
    data = {}

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

    # -------------------------
    # HELPER: Add Data
    # -------------------------
    def add_data(rows, count_key=None, amount_key=None):
        for row in rows:
            person = row.get("sales_person") or "Unassigned"
            dept = (row.get("department") or "").lower()
            week = row.get("week_name")
            ensure_sales_person(person)

            if "repair" in dept:
                if count_key:
                    data[person]["PO Count Repair"][week] += row.get(count_key, 0)
                if amount_key:
                    data[person]["PO Repair Amount"][week] += row.get(amount_key, 0)
            elif "supply" in dept:
                if count_key:
                    data[person]["PO Count Supply"][week] += row.get(count_key, 0)
                if amount_key:
                    data[person]["PO Supply Amount"][week] += row.get(amount_key, 0)

    # -------------------------
    # PO (Quotation)
    # -------------------------
    po_condition = ""
    po_values = [company, from_date, to_date]

    if brnch:
        po_condition += " AND q.branch = %s "
        po_values.append(brnch)

    if sales_person:
        po_condition += " AND q.sales_person = %s "
        po_values.append(sales_person)

    # if department:
    #     po_condition += " AND q.department = %s "
    #     po_values.append(department)

    po_data = frappe.db.sql(f"""
    SELECT
        main.sales_person,
        main.week_name,
       
        COUNT(main.name) AS total_count,
        SUM(
            CASE
            
            WHEN YEAR(main.creation) >= 2026 THEN
                IFNULL(main.grand_total, 0)

              
            END
        ) AS total_amount
    FROM (
        SELECT
            q.name,
            q.sales_person,
            q.creation,
            q.grand_total,
           
           
            CASE
                WHEN DAY(q.approval_date) BETWEEN 1 AND 7 THEN 'Week 1'
                WHEN DAY(q.approval_date) BETWEEN 8 AND 14 THEN 'Week 2'
                WHEN DAY(q.approval_date) BETWEEN 15 AND 21 THEN 'Week 3'
                WHEN DAY(q.approval_date) BETWEEN 22 AND 28 THEN 'Week 4'
                ELSE 'Week 5'
            END AS week_name
        FROM `tabQuotation` q
        LEFT JOIN `tabQuotation Item` qi ON qi.parent = q.name
        WHERE q.company = %s
        AND q.approval_date BETWEEN %s AND %s
        AND q.docstatus = 1
        AND IFNULL(q.sales_person,'') NOT IN (
            'Michael Veniston',
            'Dhinesh',
            'MOHAMED MOSAAD ALY DIAB',
            'MUHAMMAD UMAR'
        )
        {po_condition}
            ) main
            GROUP BY main.sales_person, main.week_name
        """, po_values, as_dict=True)
    add_data(po_data, "total_count", "total_amount")

    # -------------------------
    # SI (Sales Invoice)
    # -------------------------
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
            si.cost_center,
            si.sales_person,
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
        AND si.cost_center IS NOT NULL
        AND IFNULL(si.sales_person,'') NOT IN ('Michael Veniston','Dhinesh','MOHAMED MOSAAD ALY DIAB','MUHAMMAD UMAR')
        {si_condition}
        GROUP BY si.cost_center, si.sales_person, week_name
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

    # -------------------------
    # COLLECTION
    # -------------------------
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
            si.cost_center,
            si.sales_person,
            CASE
                WHEN DAY(pe.posting_date) BETWEEN 1 AND 7 THEN 'Week 1'
                WHEN DAY(pe.posting_date) BETWEEN 8 AND 14 THEN 'Week 2'
                WHEN DAY(pe.posting_date) BETWEEN 15 AND 21 THEN 'Week 3'
                WHEN DAY(pe.posting_date) BETWEEN 22 AND 28 THEN 'Week 4'
                ELSE 'Week 5'
            END AS week_name,
            SUM(per.allocated_amount) AS total_amount
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        INNER JOIN `tabSales Invoice` si ON si.name = per.reference_name
        WHERE pe.company = %s
        AND pe.posting_date BETWEEN %s AND %s
        AND pe.docstatus = 1
        AND IFNULL(si.sales_person,'') NOT IN ('Michael Veniston','Dhinesh','MOHAMED MOSAAD ALY DIAB','MUHAMMAD UMAR')
        {col_condition}
        GROUP BY si.cost_center, si.sales_person, week_name
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

    # -------------------------
    # HTML OUTPUT
    # -------------------------
    html = ""

    for person, metrics in data.items():
        html += f"""
        <table border="1" style="width:100%; border-collapse:collapse; margin-bottom:30px;">
            <tr style="background-color:#F0F8FF;">
                <th style='text-align:center' colspan="7">{person}</th>
            </tr>
            <tr style="background-color:#F0F8FF;">
                <th>Metrics</th>
                <th>Week 1</th>
                <th>Week 2</th>
                <th>Week 3</th>
                <th>Week 4</th>
                <th>Week 5</th>
            </tr>
        """

        # -------------------------
        # PO SUBTOTAL TRACKING
        # -------------------------
        po_repair = metrics["PO Repair Amount"]
        po_supply = metrics["PO Supply Amount"]

        inv_repair = metrics["Invoice Repair"]
        inv_supply = metrics["Invoice Supply"]

        col_repair = metrics["Collection Repair"]
        col_supply = metrics["Collection Supply"]

        for label, weeks in metrics.items():

            html += f"""
            <tr>
                <td><b>{label}</b></td>
                <td>{weeks['Week 1']:,.0f}</td>
                <td>{weeks['Week 2']:,.0f}</td>
                <td>{weeks['Week 3']:,.0f}</td>
                <td>{weeks['Week 4']:,.0f}</td>
                <td>{weeks['Week 5']:,.0f}</td>
            </tr>
            """

            # -------------------------
            # PO SUBTOTAL
            # -------------------------
            if label == "PO Supply Amount":
                html += f"""
                <tr style="background:#e6e6e6;font-weight:bold;">
                    <td>PO Subtotal</td>
                    <td>{po_repair['Week 1'] + po_supply['Week 1']:,.0f}</td>
                    <td>{po_repair['Week 2'] + po_supply['Week 2']:,.0f}</td>
                    <td>{po_repair['Week 3'] + po_supply['Week 3']:,.0f}</td>
                    <td>{po_repair['Week 4'] + po_supply['Week 4']:,.0f}</td>
                    <td>{po_repair['Week 5'] + po_supply['Week 5']:,.0f}</td>
                </tr>
                """

            # -------------------------
            # INVOICE SUBTOTAL
            # -------------------------
            if label == "Invoice Supply":
                html += f"""
                <tr style="background:#e6e6e6;font-weight:bold;">
                    <td>Invoice Subtotal</td>
                    <td>{inv_repair['Week 1'] + inv_supply['Week 1']:,.0f}</td>
                    <td>{inv_repair['Week 2'] + inv_supply['Week 2']:,.0f}</td>
                    <td>{inv_repair['Week 3'] + inv_supply['Week 3']:,.0f}</td>
                    <td>{inv_repair['Week 4'] + inv_supply['Week 4']:,.0f}</td>
                    <td>{inv_repair['Week 5'] + inv_supply['Week 5']:,.0f}</td>
                </tr>
                """

            # -------------------------
            # COLLECTION SUBTOTAL
            # -------------------------
            if label == "Collection Supply":
                html += f"""
                <tr style="background:#e6e6e6;font-weight:bold;">
                    <td>Collection Subtotal</td>
                    <td>{col_repair['Week 1'] + col_supply['Week 1']:,.0f}</td>
                    <td>{col_repair['Week 2'] + col_supply['Week 2']:,.0f}</td>
                    <td>{col_repair['Week 3'] + col_supply['Week 3']:,.0f}</td>
                    <td>{col_repair['Week 4'] + col_supply['Week 4']:,.0f}</td>
                    <td>{col_repair['Week 5'] + col_supply['Week 5']:,.0f}</td>
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
        AND IFNULL(q.sales_person,'') NOT IN ('Michael Veniston','Dhinesh','MOHAMED MOSAAD ALY DIAB','MUHAMMAD UMAR')
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
        html += "<td><b>WO</b></td>"
        for d in sorted_dates:
            html += f"<td>{wo_info['wo']}</td>"
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