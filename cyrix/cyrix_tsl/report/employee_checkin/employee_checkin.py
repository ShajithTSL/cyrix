# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta
from collections import defaultdict
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    # =========================
    # SORT (keeps clean grouping order)
    # =========================
    data.sort(key=lambda x: (int(x.get("employee") or 0), x.get("date")))

    grouped = defaultdict(list)

    # =========================
    # GROUP BY EMPLOYEE ONLY
    # =========================
    for row in data:
        grouped[row.get("employee")].append(row)

    final_data = []

    grand_late = 0
    grand_worked = 0
    grand_ot = 0

    # =========================
    # BUILD FINAL OUTPUT
    # =========================
    for emp, rows in grouped.items():

        emp_late = 0
        emp_worked = 0
        emp_ot = 0

        # employee rows (UNCHANGED)
        for r in rows:
            final_data.append(r)

            emp_late += r.get("late_seconds") or 0
            emp_worked += r.get("worked_seconds") or 0
            emp_ot += r.get("overtime_seconds") or 0

       # Show employee total only for date range
        if filters.get("from_date") != filters.get("to_date"):
            final_data.append({
                "employee": emp,
                "employee_name": "TOTAL",
                "company": "",
                "date": "",
                "day": "",
                "in_time": "",
                "out_time": "",
                "worked_hours": str(timedelta(seconds=emp_worked)) if emp_worked else "00:00:00",
                "in_location": "",
                "out_location": "",
                "permission_start_time": "",
                "permission_end_time": "",
                "late_by": str(timedelta(seconds=emp_late)) if emp_late else "00:00:00",
                "overtime": str(timedelta(seconds=emp_ot)) if emp_ot else "00:00:00",
            })

        grand_late += emp_late
        grand_worked += emp_worked
        grand_ot += emp_ot

    return columns, final_data


def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Data", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": "Day", "fieldname": "day", "fieldtype": "Data", "width": 100},
        {"label": "In Device ID", "fieldname": "in_device_id", "fieldtype": "Data", "width": 120},
        {"label": "Out Device ID", "fieldname": "out_device_id", "fieldtype": "Data", "width": 120},
        {"label": "In Time", "fieldname": "in_time", "fieldtype": "Time", "width": 120},
        {"label": "Out Time", "fieldname": "out_time", "fieldtype": "Time", "width": 120},
        {"label": "Worked Hours", "fieldname": "worked_hours", "fieldtype": "Time", "width": 130},
        {"label": "In Location", "fieldname": "in_location", "fieldtype": "Data", "width": 250},
        {"label": "Out Location", "fieldname": "out_location", "fieldtype": "Data", "width": 250},
        {"label": "Permission Start", "fieldname": "permission_start_time", "fieldtype": "Time", "width": 170},
        {"label": "Permission End", "fieldname": "permission_end_time", "fieldtype": "Time", "width": 170},
        {"label": "Late In By", "fieldname": "late_by", "fieldtype": "Time", "width": 120},
        {"label": "Overtime", "fieldname": "overtime", "fieldtype": "Time", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 220},
    ]


def get_data(filters):

    conditions = ""

    if filters.get("company"):
        conditions += " AND company = %(company)s "

    if filters.get("branch"):
        conditions += " AND branch = %(branch)s "

    if filters.get("employee"):
        conditions += " AND name = %(employee)s "

    query = f"""
    SELECT
        d.employee,
        emp.employee_name,
        emp.company,
        d.date,
        DAYNAME(d.date) AS day,
        (
    SELECT ec1.device_id
    FROM `tabEmployee Checkin` ec1
    WHERE ec1.employee = d.employee
      AND DATE(ec1.time)=d.date
      AND ec1.log_type='IN'
    ORDER BY ec1.time ASC, ec1.creation ASC
    LIMIT 1
) AS in_device_id,


(
    SELECT ec2.device_id
    FROM `tabEmployee Checkin` ec2
    WHERE ec2.employee = d.employee
      AND DATE(ec2.time)=d.date
      AND ec2.log_type='OUT'
    ORDER BY ec2.time DESC, ec2.creation DESC
    LIMIT 1
) AS out_device_id,


        (
    SELECT TIME(ec1.time)
    FROM `tabEmployee Checkin` ec1
    WHERE ec1.employee = d.employee
      AND DATE(ec1.time)=d.date
      AND ec1.log_type='IN'
    ORDER BY ec1.time ASC, ec1.creation ASC
    LIMIT 1
) AS in_time,


(
    SELECT TIME(ec2.time)
    FROM `tabEmployee Checkin` ec2
    WHERE ec2.employee = d.employee
      AND DATE(ec2.time)=d.date
      AND ec2.log_type='OUT'
    ORDER BY ec2.time DESC, ec2.creation DESC
    LIMIT 1
) AS out_time,

        /* =========================
           WORKED HOURS
        ========================== */
        CASE
            WHEN MIN(CASE WHEN ec.log_type='IN' THEN ec.time END) IS NOT NULL
             AND MAX(CASE WHEN ec.log_type='OUT' THEN ec.time END) IS NOT NULL
            THEN TIMESTAMPDIFF(
                    SECOND,
                    MIN(CASE WHEN ec.log_type='IN' THEN ec.time END),
                    MAX(CASE WHEN ec.log_type='OUT' THEN ec.time END)
                 )
            ELSE 0
        END AS worked_seconds,

        SEC_TO_TIME(
            CASE
                WHEN MIN(CASE WHEN ec.log_type='IN' THEN ec.time END) IS NOT NULL
                 AND MAX(CASE WHEN ec.log_type='OUT' THEN ec.time END) IS NOT NULL
                THEN TIMESTAMPDIFF(
                        SECOND,
                        MIN(CASE WHEN ec.log_type='IN' THEN ec.time END),
                        MAX(CASE WHEN ec.log_type='OUT' THEN ec.time END)
                     )
                ELSE 0
            END
        ) AS worked_hours,

        (
    SELECT ec1.gps_location
    FROM `tabEmployee Checkin` ec1
    WHERE ec1.employee=d.employee
      AND DATE(ec1.time)=d.date
      AND ec1.log_type='IN'
    ORDER BY ec1.time ASC, ec1.creation ASC
    LIMIT 1
) AS in_location,


(
    SELECT ec2.gps_location
    FROM `tabEmployee Checkin` ec2
    WHERE ec2.employee=d.employee
      AND DATE(ec2.time)=d.date
      AND ec2.log_type='OUT'
    ORDER BY ec2.time DESC, ec2.creation DESC
    LIMIT 1
) AS out_location,

        TIME(ar.from_time) AS permission_start_time,
        TIME(ar.to_time) AS permission_end_time,

        /* =========================
           LATE SECONDS
        ========================== */
        CASE 
            WHEN MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) IS NULL THEN 0

            WHEN MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) > '08:10:00'
                 AND (ar.from_time IS NULL OR TIME(ar.from_time) > '08:10:00')
            THEN TIME_TO_SEC(MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END))
                 - TIME_TO_SEC('08:10:00')

            ELSE 0
        END AS late_seconds,

        SEC_TO_TIME(
            CASE 
                WHEN MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) > '08:10:00'
                     AND (ar.from_time IS NULL OR TIME(ar.from_time) > '08:10:00')
                THEN TIME_TO_SEC(MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END))
                     - TIME_TO_SEC('08:10:00')
                ELSE 0
            END
        ) AS late_by,

        /* =========================
           OVERTIME (> 00.30 HOUR ONLY)
        ========================== */
        CASE
            WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NULL THEN 0

            WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) > '17:30:00'
            THEN TIME_TO_SEC(MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END))
                 - TIME_TO_SEC('17:00:00')

            ELSE 0
        END AS overtime_seconds,

        SEC_TO_TIME(
            CASE
                WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) > '17:30:00'
                THEN TIME_TO_SEC(MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END))
                     - TIME_TO_SEC('17:00:00')
                ELSE 0
            END
        ) AS overtime,

     CASE

    /* =========================
       HOLIDAY (FIXED FOR Cyrix TSL - UAE)
    ========================= */
    WHEN h.holiday_date IS NOT NULL
         AND (
            MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) IS NOT NULL
            OR
            MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NOT NULL
         )
         AND NOT (
            emp.company = 'Cyrix TSL - UAE'
            AND DAYNAME(d.date) = 'Friday'
         )
    THEN 'Present + Holiday'

    WHEN h.holiday_date IS NOT NULL
         AND NOT (
            emp.company = 'Cyrix TSL - UAE'
            AND DAYNAME(d.date) = 'Friday'
         )
    THEN 'Holiday'

    /* =========================
       WEEK OFF (Cyrix TSL - UAE = Sunday only)
    ========================= */
    WHEN (
        emp.company = 'Cyrix TSL - UAE' AND DAYNAME(d.date) = 'Sunday'
    )
    AND (
        MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) IS NOT NULL
        OR
        MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NOT NULL
    )
    THEN 'Present + Week Off'

    WHEN (
        emp.company = 'Cyrix TSL - UAE' AND DAYNAME(d.date) = 'Sunday'
    )
    THEN 'Week Off'

    /* =========================
       DEFAULT WEEK OFF (NON Cyrix TSL - UAE)
    ========================= */
    WHEN (
        emp.company != 'Cyrix TSL - UAE' AND DAYNAME(d.date) = 'Friday'
    )
    AND (
        MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) IS NOT NULL
        OR
        MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NOT NULL
    )
    THEN 'Present + Week Off'

    WHEN (
        emp.company != 'Cyrix TSL - UAE' AND DAYNAME(d.date) = 'Friday'
    )
    THEN 'Week Off'

    /* =========================
       LEAVE
    ========================= */
    WHEN lv.name IS NOT NULL THEN
        CASE
            WHEN lv.leave_type = 'Annual Leave' THEN 'Vacation'
            WHEN lv.leave_type = 'Sick Leave 100' THEN 'Sick'
            WHEN lv.leave_type = 'Leave Without Pay' THEN 'Leave WP'
            ELSE 'Leave'
        END

    /* =========================
       ABSENT
    ========================= */
    WHEN MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) IS NULL
     AND MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NULL
    THEN 'Absent'

    /* =========================
       MISS PUNCH
    ========================= */
    WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) IS NULL
    THEN 'Miss Punch'

    /* =========================
       LATE / EARLY LOGIC (UNCHANGED)
    ========================= */
    WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) < '16:50:00'
         AND MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) > '08:10:00'
         AND ar.from_time IS NOT NULL
    THEN 'Late In + Permission + Early Left'

    WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) < '16:50:00'
         AND ar.from_time IS NOT NULL
    THEN 'Permission + Early Left'

    WHEN MAX(CASE WHEN ec.log_type='OUT' THEN TIME(ec.time) END) < '16:50:00'
    THEN 'Early Left + Present'

    WHEN MIN(CASE WHEN ec.log_type='IN' THEN TIME(ec.time) END) > '08:10:00'
    THEN 'Late In + Present'

    ELSE 'Present'

END AS status
    FROM (

        SELECT e.name AS employee, d.date
        FROM (
            SELECT *
            FROM `tabEmployee`
            WHERE status = 'Active'
            AND name NOT IN ('143', '132', '197', '198','230')
            AND employment_type NOT IN ('Online Full - Time', 'Online Part - Time','')
            {conditions}
        ) e

        CROSS JOIN (
            SELECT DATE(%(from_date)s) + INTERVAL (a.a + (10*b.a)) DAY AS date
            FROM
                (SELECT 0 a UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a
            CROSS JOIN
                (SELECT 0 a UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b
        ) d

        WHERE d.date BETWEEN %(from_date)s AND %(to_date)s

    ) d

    LEFT JOIN `tabEmployee Checkin` ec
        ON ec.employee = d.employee
        AND DATE(ec.time) = d.date

    LEFT JOIN `tabEmployee` emp
        ON emp.name = d.employee

    LEFT JOIN `tabHoliday` h
        ON h.holiday_date = d.date

    LEFT JOIN `tabLeave Application` lv
        ON lv.employee = d.employee
        AND lv.status = 'Approved'
        AND d.date BETWEEN lv.from_date AND lv.to_date

    LEFT JOIN (
        SELECT 
            employee,
            DATE(from_time) AS date,
            MIN(from_time) AS from_time,
            MAX(to_time) AS to_time
        FROM `tabAttendance Requests`
        WHERE docstatus = 1
        GROUP BY employee, DATE(from_time)
    ) ar
    ON ar.employee = d.employee
    AND ar.date = d.date

    GROUP BY d.employee, d.date

    ORDER BY d.date ASC, d.employee ASC
    """

    return frappe.db.sql(query, filters, as_dict=True)


import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template

@frappe.whitelist()
def download_pdf(from_date, to_date, company=None, branch=None, employee=None):
    
    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "company": company,
        "branch": branch,
        "employee": employee
    }

    columns, data = execute(filters)

    html = render_template(
        "cyrix/cyrix_tsl/report/employee_checkin/employee_checkin.html",
        {
            "columns": columns,
            "data": data,
            "filters": filters,
        },
    )

    pdf = get_pdf(html)
    pdf = get_pdf(
    html,
    {
        "orientation": "Portrait",
        "page-size": "A4",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "5mm",
        "margin-right": "5mm",
    },
)
    frappe.local.response.filename = "Attendance Report.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"