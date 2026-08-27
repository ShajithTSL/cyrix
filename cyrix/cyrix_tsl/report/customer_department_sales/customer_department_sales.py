# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    cost_centers = get_cost_centers(filters)
    columns = get_columns(cost_centers)
    data = get_data(filters, cost_centers)

    return columns, data


def get_cost_centers(filters):

    conditions = """
        si.docstatus = 1
        AND si.cost_center IS NOT NULL
        AND si.cost_center != ''
    """

    values = {}

    if filters.get("company"):
        conditions += " AND si.company = %(company)s"
        values["company"] = filters["company"]

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"
        values["customer"] = filters["customer"]

    rows = frappe.db.sql(
        f"""
        SELECT DISTINCT
            si.cost_center
        FROM `tabSales Invoice` si
        WHERE {conditions}
        ORDER BY si.cost_center
        """,
        values,
        as_dict=True
    )

    # Keep the COMPLETE Cost Center name
    cost_centers = []

    for row in rows:
        if row.cost_center:
            cost_centers.append(row.cost_center.strip())

    return sorted(set(cost_centers))


def get_columns(cost_centers):

    columns = [
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 300
        }
    ]

    for cost_center in cost_centers:

        columns.append({
            "label": _(cost_center),
            "fieldname": frappe.scrub(cost_center),
            "fieldtype": "Currency",
            "width": 160
        })

    columns.append({
        "label": _("Total"),
        "fieldname": "total",
        "fieldtype": "Currency",
        "width": 150
    })

    return columns


def get_data(filters, cost_centers):

    conditions = """
        si.docstatus = 1
    """

    values = {}

    if filters.get("company"):
        conditions += " AND si.company = %(company)s"
        values["company"] = filters["company"]

    if filters.get("from_date"):
        conditions += " AND si.posting_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"
        values["customer"] = filters["customer"]

    if not cost_centers:
        return []

    cost_center_cases = []

    for index, cost_center in enumerate(cost_centers):

        fieldname = frappe.scrub(cost_center)

        # Unique parameter name
        parameter = f"cost_center_{index}"

        cost_center_cases.append(
            f"""
            SUM(
                CASE
                    WHEN si.cost_center = %({parameter})s
                    THEN si.grand_total
                    ELSE 0
                END
            ) AS `{fieldname}`
            """
        )

        values[parameter] = cost_center

    sql = f"""
        SELECT
            si.customer,
            si.customer_name,

            {", ".join(cost_center_cases)}

        FROM `tabSales Invoice` si

        WHERE {conditions}

        GROUP BY
            si.customer,
            si.customer_name

        ORDER BY
            si.customer_name
    """

    data = frappe.db.sql(
        sql,
        values,
        as_dict=True
    )

    # Calculate total
    for row in data:

        total = 0

        for cost_center in cost_centers:

            fieldname = frappe.scrub(cost_center)

            row[fieldname] = flt(row.get(fieldname))

            total += row[fieldname]

        row["total"] = total

    return data