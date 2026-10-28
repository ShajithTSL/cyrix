# Copyright (c) 2026, TSL
# Iqama Renewal Tool – backend for the "iqama-renewal-tool" Page.
#
# Requires the Umm al-Qura converter (official Saudi Hijri calendar):
#   bench pip install hijridate

import datetime
import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, getdate, nowdate

try:
    from hijridate import Gregorian, Hijri
except ImportError:  # older package name
    from hijri_converter import Gregorian, Hijri


EXPIRY_FIELD = "civil_id_expiry_date"
ALLOWED_PERIODS = (3, 6, 9, 12)
ALLOWED_ROLES = ("HR Manager", "HR User", "System Manager")
DEFAULT_DAYS = 50


# --------------------------------------------------------------------------
# Hijri helpers
# --------------------------------------------------------------------------
def to_hijri(gdate):
    gdate = getdate(gdate)
    return Gregorian(gdate.year, gdate.month, gdate.day).to_hijri()


def add_hijri_months(gdate, months):
    """Add `months` Hijri (Umm al-Qura) months to a Gregorian date.

    The Hijri day is kept; if the target Hijri month is shorter (29 days),
    the day is clamped to the last day of that month.
    Returns (gregorian datetime.date, hijri object).
    """
    h = to_hijri(gdate)
    total = (h.month - 1) + cint(months)
    year = h.year + total // 12
    month = total % 12 + 1
    last_day = Hijri(year, month, 1).month_length()
    new_h = Hijri(year, month, min(h.day, last_day))
    g = new_h.to_gregorian()
    return datetime.date(g.year, g.month, g.day), new_h


def fmt_hijri(h):
    return f"{h.day:02d}-{h.month:02d}-{h.year}"

# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
@frappe.whitelist()
def get_employees(days=DEFAULT_DAYS, company=None, period=None):
    frappe.only_for(ALLOWED_ROLES)

    days = max(cint(days), 0)
    period = cint(period)
    today = getdate(nowdate())

    filters = {
        "status": "Active",
        EXPIRY_FIELD: ["between", [today, add_days(today, days)]],
    }
    if company:
        filters["company"] = company

    rows = frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name", "employee_name", "department", "designation", "company", "civil_id_no", EXPIRY_FIELD],
        order_by=f"{EXPIRY_FIELD} asc",
    )

    for r in rows:
        expiry = getdate(r[EXPIRY_FIELD])
        r["expiry_date"] = expiry
        r["expiry_hijri"] = fmt_hijri(to_hijri(expiry))
        r["days_left"] = date_diff(expiry, today)
        r["civil_id_no"] = r.get("civil_id_no")
        if period in ALLOWED_PERIODS:
            new_g, new_h = add_hijri_months(expiry, period)
            r["new_expiry_date"] = new_g
            r["new_expiry_hijri"] = fmt_hijri(new_h)

    frappe.errprint(rows)
    return rows


@frappe.whitelist(methods=["POST"])
def update_expiry(employees, period):
    frappe.only_for(ALLOWED_ROLES)

    if isinstance(employees, str):
        employees = json.loads(employees)
    period = cint(period)

    if not employees:
        frappe.throw(_("Please select at least one employee."))
    if period not in ALLOWED_PERIODS:
        frappe.throw(_("Renewal period must be one of: {0} months.").format(", ".join(map(str, ALLOWED_PERIODS))))

    updated, failed = [], []

    for emp in employees:
        frappe.db.savepoint("iqama_renewal")
        try:
            doc = frappe.get_doc("Employee", emp)
            doc.check_permission("write")

            old = doc.get(EXPIRY_FIELD)
            if not old:
                raise frappe.ValidationError(_("No Iqama expiry date set."))

            new_g, new_h = add_hijri_months(old, period)
            doc.set(EXPIRY_FIELD, new_g)
            doc.save()  # creates a Version entry (audit trail)

            doc.add_comment(
                "Info",
                _("Iqama renewed for {0} months: {1} ({2} H) → {3} ({4} H)").format(
                    period,
                    frappe.format(old, "Date"),
                    fmt_hijri(to_hijri(old)),
                    frappe.format(new_g, "Date"),
                    fmt_hijri(new_h),
                ),
            )

            updated.append(
                {
                    "employee": doc.name,
                    "employee_name": doc.employee_name,
                    "old_date": old,
                    "new_date": new_g,
                    "new_hijri": fmt_hijri(new_h),
                }
            )
        except Exception as e:
            frappe.db.rollback(save_point="iqama_renewal")
            frappe.clear_messages()
            failed.append({"employee": emp, "error": str(e) or e.__class__.__name__})

    return {"updated": updated, "failed": failed}