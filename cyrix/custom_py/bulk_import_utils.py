"""
Shared helpers for bulk-resolving/creating simple master-data records
(Item Model, Item Mfg, and similar "lookup" doctypes) without one query
per row.

Used by both item_bulk_import.py (the Excel import tool) and, as a rare
fallback, maintenance_contract.py.
"""

import frappe


def bulk_get_or_create(doctype, title_field, values):
    """
    Given a list of raw string values (e.g. model names typed in a sheet),
    return ({value: docname}, created_count).

    One query to find what already exists, then one insert per genuinely
    missing value (this list is normally much shorter than your row count —
    e.g. 1200 items might only reference 40 distinct models).

    Assumes the doctype's identifying field is `title_field` and that
    autoname is based on that field (prompt/field-based naming), so the
    returned docname equals the value for newly created docs. If your
    "Item Model" / "Item Mfg" doctypes use a different naming rule (e.g. a
    separate naming series), swap `new_doc.name` in below instead of
    assuming `value_map[v] = new_doc.name` — the code already does that
    correctly either way since it reads back new_doc.name.
    """
    if not values:
        return {}, 0

    values = sorted({v for v in values if v})
    if not values:
        return {}, 0

    value_map = {}
    for start in range(0, len(values), 500):
        chunk = values[start:start + 500]
        existing = frappe.get_all(
            doctype, filters={title_field: ["in", chunk]}, fields=["name", title_field]
        )
        value_map.update({d[title_field]: d.name for d in existing})

    created = 0
    for v in values:
        if v in value_map:
            continue
        new_doc = frappe.new_doc(doctype)
        new_doc.set(title_field, v)
        new_doc.insert(ignore_permissions=True)
        value_map[v] = new_doc.name
        created += 1

    return value_map, created


def bulk_activate_serials(serial_to_item, chunk_size=200):
    """
    Flip a batch of existing Serial Number docs to Active and set their
    item_code, in one UPDATE per chunk instead of one .save() per serial.

    serial_to_item: {serial_no: item_code}

    This bypasses Serial Number's validate()/on_update hooks — only use it
    if that doctype has no side effects beyond the two fields being set
    (true for a stock Serial Number doctype with no custom hooks; check
    yours before relying on this for anything with, say, stock ledger
    side effects tied to on_update).
    """
    items = list(serial_to_item.items())
    if not items:
        return

    for start in range(0, len(items), chunk_size):
        chunk = items[start:start + chunk_size]
        names = [s for s, _ in chunk]

        case_parts = []
        params = {}
        for i, (serial_no, item_code) in enumerate(chunk):
            key = f"s{i}"
            case_parts.append(f"WHEN %({key}_name)s THEN %({key}_item)s")
            params[f"{key}_name"] = serial_no
            params[f"{key}_item"] = item_code

        placeholders = ", ".join(f"%(name{i})s" for i in range(len(names)))
        params.update({f"name{i}": n for i, n in enumerate(names)})

        frappe.db.sql(
            f"""
            UPDATE `tabSerial Number`
            SET status = 'Active',
                item_code = CASE name {' '.join(case_parts)} END
            WHERE name IN ({placeholders})
            """,
            params,
        )
