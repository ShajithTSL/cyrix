import frappe


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Task",
            "fieldname": "task",
            "fieldtype": "Link",
            "options": "Task",
            "width": 150,
        },
        {
            "label": "Task Subject",
            "fieldname": "task_subject",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Completed By",
            "fieldname": "completed_by",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180,
        },
        {
            "label": "Estimated Hrs",
            "fieldname": "estimated_hrs",
            "fieldtype": "Float",
            "precision": 2,
            "width": 120,
        },
        {
            "label": "Captured Hrs",
            "fieldname": "captured_hrs",
            "fieldtype": "Float",
            "precision": 2,
            "width": 120,
        },
        {
            "label": "Difference Hrs",
            "fieldname": "difference_hrs",
            "fieldtype": "Float",
            "precision": 2,
            "width": 130,
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_data(filters):

    conditions = []
    values = {}

    # Date
    if filters.get("from_date"):
        conditions.append("ts.start_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("ts.start_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    # Employee filter
    if filters.get("employee"):
        conditions.append("ts.employee = %(employee)s")
        values["employee"] = filters["employee"]

    # Company filter
    if filters.get("company"):
        conditions.append("ts.company = %(company)s")
        values["company"] = filters["company"]

    # Time Sheet filter
    if filters.get("time_sheet"):
        conditions.append("ts.name = %(time_sheet)s")
        values["time_sheet"] = filters["time_sheet"]

    condition_sql = ""

    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    # ---------------------------------------------------------
    # Get captured hours from Timesheet
    # Group only by Task
    # ---------------------------------------------------------

    rows = frappe.db.sql(
        f"""
        SELECT
            tsd.task,
            SUM(tsd.hours) AS captured_hrs

        FROM `tabTimesheet` ts

        INNER JOIN `tabTimesheet Detail` tsd
            ON tsd.parent = ts.name

        WHERE
            ts.docstatus < 2
            AND tsd.task IS NOT NULL
            AND tsd.task != ''
            {condition_sql}

        GROUP BY
            tsd.task

        ORDER BY
            tsd.task
        """,
        values,
        as_dict=True,
    )

    data = []

    for row in rows:

        # -----------------------------------------------------
        # Get information directly from Task
        # -----------------------------------------------------

        task_data = frappe.db.get_value(
            "Task",
            row.task,
            [
                "subject",
                "completed_by",
                "expected_time",
                "status",
            ],
            as_dict=True,
        )

        if not task_data:
            continue

        captured_hrs = float(row.captured_hrs or 0)
        estimated_hrs = float(task_data.expected_time or 0)

        difference_hrs = estimated_hrs - captured_hrs

        data.append({
            "task": row.task,
            "task_subject": task_data.subject or "",
            "completed_by": task_data.completed_by or "",
            "estimated_hrs": estimated_hrs,
            "captured_hrs": captured_hrs,
            "difference_hrs": difference_hrs,
            "status": task_data.status or "",
        })

    return data