# Copyright (c) 2026, TSL
# Iqama expiry email notifications to HR (Gregorian dates).
#
#  1. Last day of every month -> list of employees expiring in 0-50 days.
#  2. Every day               -> reminder for employees expiring in exactly 20, 10 or 3 days
#                                (i.e. still not renewed / not updated in the system).

import frappe
from frappe.utils import (
    add_days,
    date_diff,
    escape_html,
    formatdate,
    get_last_day,
    get_url,
    get_url_to_form,
    getdate,
    nowdate,
)

EXPIRY_FIELD = "civil_id_expiry_date"
MONTHLY_WINDOW_DAYS = 50
REMINDER_DAYS = (20, 10, 3)
HR_ROLE = "HR Manager"
DATE_FORMAT = "dd-MM-yyyy"
TOOL_URL = "/app/iqama-renewal-tool"

MISSING_CHECK_COMPANY = "Company Al-Halloul Faniye Medical"
NATIONALITY_FIELD = "nationality"
# Any of these values (case-insensitive) counts as Saudi and is skipped.
SAUDI_VALUES = ("SAUDI")
# Day for the "missing expiry date" email. Monday=0 ... Sunday=6
MISSING_REMINDER_WEEKDAY = 6
CIVIL_ID_FIELD = "civil_id_no"

def schedule_iqama_reminder():
    passport_expiry = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.iqama_expiry_reminder.send_iqama_notifications'})
    if not passport_expiry:
        sjt = frappe.new_doc("Scheduled Job Type")  
        sjt.update({
            "method" : 'cyrix.hr_py.iqama_expiry_reminder.send_iqama_notifications',
            "cron_format" : '0 8 * * *'
        })
        sjt.save(ignore_permissions=True)


# --------------------------------------------------------------------------
# Scheduler entry point (runs every day, see hooks)
# --------------------------------------------------------------------------
def send_iqama_notifications():
    today = getdate(nowdate())
    if today == getdate(get_last_day(today)):
        send_monthly_expiry_list()
    send_expiry_reminders()
    send_missing_expiry_reminder()


# --------------------------------------------------------------------------
# 1. Monthly list (0-50 days)
# --------------------------------------------------------------------------
def send_monthly_expiry_list():
    today = getdate(nowdate())
    rows = get_expiring_employees([today, add_days(today, MONTHLY_WINDOW_DAYS)])
    if not rows:
        return

    subject = f"Iqama Expiry List: {len(rows)} employee(s) expiring by {formatdate(add_days(today, MONTHLY_WINDOW_DAYS), DATE_FORMAT)}"
    intro = (
        f"The following employees have an Iqama expiring within the next "
        f"<b>{MONTHLY_WINDOW_DAYS} days</b> (as of {formatdate(today, DATE_FORMAT)})."
    )
    send_mail(subject, intro, rows)


# --------------------------------------------------------------------------
# 2. Daily reminders (20 / 10 / 3 days before expiry)
# --------------------------------------------------------------------------
def send_expiry_reminders():
    today = getdate(nowdate())
    target_dates = [add_days(today, d) for d in REMINDER_DAYS]
    rows = get_expiring_employees(target_dates, exact=True)
    if not rows:
        return

    subject = f"Reminder: Iqama not yet renewed for {len(rows)} employee(s)"
    intro = (
        "The Iqama of the following employees has <b>not been renewed</b> in the system yet "
        f"and will expire in {', '.join(map(str, REMINDER_DAYS))} days. "
        "Please renew and update the expiry date."
    )
    send_mail(subject, intro, rows)

# --------------------------------------------------------------------------
# 3. Weekly reminder: non-Saudi employees with no Iqama expiry date
# --------------------------------------------------------------------------
def send_missing_expiry_reminder():
    # Expiry date missing, whether or not the Iqama number is filled in.
    filters = [["status", "=", "Active"], [EXPIRY_FIELD, "is", "not set"], [NATIONALITY_FIELD, "!=", "SAUDI"]]
    if MISSING_CHECK_COMPANY:
        filters.append(["company", "=", MISSING_CHECK_COMPANY])

    rows = frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name", "employee_name", "department", "designation", NATIONALITY_FIELD, CIVIL_ID_FIELD],
        order_by="name asc",
    )

    # Employees missing both the Iqama number and the expiry date are listed first.
    rows.sort(key=lambda r: (bool((r.get(CIVIL_ID_FIELD) or "").strip()), r.name))
    both = sum(1 for r in rows if not (r.get(CIVIL_ID_FIELD) or "").strip())

    subject = f"Action Required: Iqama details missing for {len(rows)} employee(s)"
    intro = (
        "The following non-Saudi employees do <b>not have an Iqama expiry date</b> in the ERP"
        f"{f' ({both} of them also have no Iqama number)' if both else ''}. "
        "Please update the missing Iqama details on their Employee record so they are included "
        "in the expiry list and renewal reminders."
    )
    if rows:
        send_mail(subject, intro, rows, missing=True)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def get_expiring_employees(dates, exact=False):
    """exact=False -> dates is [from, to]; exact=True -> dates is a list of exact dates."""
    condition = ["in", dates] if exact else ["between", dates]
    rows = frappe.get_all(
        "Employee",
        filters={"status": "Active","company":"Company Al-Halloul Faniye Medical", EXPIRY_FIELD: condition},
        fields=["name", "employee_name", "civil_id_no", "designation", EXPIRY_FIELD],
        order_by=f"{EXPIRY_FIELD} asc",
    )
    today = getdate(nowdate())
    for r in rows:
        r["days_left"] = date_diff(r[EXPIRY_FIELD], today)
    return rows

def send_mail(subject, intro, rows, missing=False):
    frappe.sendmail(
        recipients="admin@tsl-me.com",
        cc="admin-sa1@tsl-me.com",
        subject=subject,
        sender= "no-reply@cyrix-tsl.com",
        bcc=None,
        message=build_message(intro, rows),
        expose_recipients="header",
    )
    
def build_message(intro, rows, missing=False):
    cell = 'style="border:1px solid #d1d8dd;padding:6px 10px;"'
    head = 'style="border:1px solid #d1d8dd;padding:6px 10px;background:#f4f5f6;text-align:left;"'

    def days_style(days):
        if days is None:  # note: 0 (expires today) is valid, so don't use "if days:"
            return cell
        color = "#e03636" if days <= 15 else "#e8742e" if days <= 30 else "#b8860b"
        return f'style="border:1px solid #d1d8dd;padding:6px 10px;color:{color};font-weight:600;"'

    missing_cell = '<td style="border:1px solid #d1d8dd;padding:6px 10px;color:#e03636;font-weight:600;">Missing</td>'

    def extra_cells(r):
        if missing:
            nat = escape_html(r.get(NATIONALITY_FIELD) or "Not set")
            civil_id = (r.get(CIVIL_ID_FIELD) or "").strip()
            id_cell = f"<td {cell}>{escape_html(civil_id)}</td>" if civil_id else missing_cell
            return f"<td {cell}>{nat}</td>{id_cell}{missing_cell}"
        expiry = r.get(EXPIRY_FIELD)
        if not expiry:
            return f"{missing_cell}<td {cell}>-</td>"
        days_left = r.get("days_left")
        return (
            f"<td {cell}>{formatdate(expiry, DATE_FORMAT)}</td>"
            f"<td {days_style(days_left)}>{'' if days_left is None else days_left}</td>"
        )

    extra_heads = (
        f"<th {head}>Nationality</th><th {head}>Iqama No</th><th {head}>Iqama Expiry</th>"
        if missing
        else f"<th {head}>Iqama Expiry</th><th {head}>Days Left</th>"
    )

    body = "".join(
        f"""<tr>
            <td {cell}><a href="{get_url_to_form('Employee', r.name)}">{escape_html(r.name)}</a></td>
            <td {cell}>{escape_html(r.employee_name or '')}</td>
            <td {cell}>{escape_html(r.department or '')}</td>
            <td {cell}>{escape_html(r.designation or '')}</td>
            {extra_cells(r)}
        </tr>"""
        for r in rows
    )
    footer = "" if missing else f'<p><a href="{get_url(TOOL_URL)}">Open Iqama Renewal Tool</a></p>'

    return f"""
        <p>Dear HR Team,</p>
        <p>{intro}</p>
        <table style="border-collapse:collapse;font-size:13px;">
            <tr>
                <th {head}>Employee</th>
                <th {head}>Employee Name</th>
                <th {head}>Department</th>
                <th {head}>Designation</th>
                {extra_heads}
            </tr>
            {body}
        </table>
        {footer}
    """



