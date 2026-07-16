"""
Item Bulk Import — parses an uploaded Excel sheet, pre-creates everything
a Maintenance Contract line needs in the correct dependency order:

    Item Model  ->  Item Mfg  ->  Item  ->  Serial Number

and then builds the Maintenance Contract itself as a Draft, with every
row already carrying item_code / model / manufacturer / serial_number /
qty. The user is routed straight to that draft to review and submit —
no intermediate result sheet to re-import.

Runs as a background job (frappe.enqueue) so 1200+ rows never sit inside
an HTTP request. Progress is written back to the document + pushed over
realtime so the form can show a live counter and redirect on completion.

Expected sheet columns (case-insensitive header row):
    item_name, model, manufacturer, item_group, uom, serial_number
    qty (optional, defaults to 1)

Note on where the time actually goes: the bulk lookups below turn "one
query per row" into a handful of queries regardless of row count — that
part is already as fast as it reasonably gets. What's left is the cost of
creating N new Item / Serial Number documents through the full ORM
(autoname + validate + hooks per doc), which no amount of indexing fixes,
because it isn't query time. If 1200-row imports are still too slow after
this, the next lever is switching Item/Serial Number creation from
frappe.new_doc().insert() to a true bulk SQL insert — see the comment
above _create_item for how to do that and what it gives up (hooks,
autoname, versioning) in exchange for speed. Not enabled by default here;
turn it on only if you've confirmed you don't need those doctypes'
validate()/hooks for correctness.
"""


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path

from cyrix.custom_py.bulk_import_utils import bulk_get_or_create

REQUIRED_COLUMNS = ["item_name", "model", "manufacturer", "item_group", "uom", "serial_number"]

ITEM_MODEL_TITLE_FIELD = "model"          # confirmed from child table's fetch_from
ITEM_MFG_TITLE_FIELD = "manufacturer"     # TODO: confirm against your Item Mfg doctype

PROGRESS_EVERY = 50


class ItemBulkImport(Document):
    pass


@frappe.whitelist()
def start_import(name):
    doc = frappe.get_doc("Item Bulk Import", name)
    doc.check_permission("write")

    if not doc.import_file:
        frappe.throw(_("Attach an Excel file first"))

    doc.db_set("status", "Queued", update_modified=False)

    frappe.enqueue(
        "cyrix.cyrix_tsl.doctype.item_bulk_import.item_bulk_import.process_import",
        queue="long",
        timeout=6000,
        name=name,
        enqueue_after_commit=True,
    )
    return {"queued": True}


def process_import(name):
    doc = frappe.get_doc("Item Bulk Import", name)
    doc.db_set("status", "Processing", update_modified=False)

    try:
        rows = _read_excel(doc.import_file)
        doc.db_set("total_rows", len(rows), update_modified=False)

        if not rows:
            frappe.throw(_("No data rows found in the sheet"))

        # -----------------------------------------------------------
        # Step 1 — Item Model / Item Mfg, resolved in bulk (small lists
        # even across 1000+ rows — normally a few dozen distinct values)
        #
        # Only rows with BOTH model and manufacturer filled in count as a
        # real combination — a row with just one of the two doesn't
        # identify anything, so it's excluded here and handled by the
        # item_name-only fallback (or skipped) in the row loop below.
        # -----------------------------------------------------------
        complete_rows = [r for r in rows if r.get("model") and r.get("manufacturer")]

        model_map, models_created = bulk_get_or_create(
            "Item Model", ITEM_MODEL_TITLE_FIELD, [r.get("model") for r in complete_rows]
        )
        mfg_map, mfgs_created = bulk_get_or_create(
            "Item Mfg", ITEM_MFG_TITLE_FIELD, [r.get("manufacturer") for r in complete_rows]
        )

        # -----------------------------------------------------------
        # Step 2 — Item, matched by (model, mfg) — bulk lookup first,
        # only insert what's genuinely missing
        # -----------------------------------------------------------
        resolved_models = list(set(model_map.values())) or [""]
        resolved_mfgs = list(set(mfg_map.values())) or [""]

        existing_items = frappe.get_all(
            "Item",
            filters=[["model", "in", resolved_models], ["mfg", "in", resolved_mfgs]],
            fields=["name", "model", "mfg"],
        )
        item_lookup = {(d.model, d.mfg): d.name for d in existing_items}

        # -----------------------------------------------------------
        # Step 3 — Serial Number existence, one chunked query
        # -----------------------------------------------------------
        serial_values = [r.get("serial_number") for r in rows if r.get("serial_number")]
        existing_serials = set()
        for start in range(0, len(serial_values), 500):
            chunk = serial_values[start:start + 500]
            existing_serials.update(
                frappe.get_all("Serial Number", filters={"name": ["in", chunk]}, pluck="name")
            )

        items_created = 0
        serials_created = 0
        errors = []

        skipped = 0

        for idx, row in enumerate(rows):
            try:
                if row.get("model") and row.get("manufacturer"):
                    model_name = model_map.get(row.get("model"))
                    mfg_name = mfg_map.get(row.get("manufacturer"))
                    key = (model_name, mfg_name)

                    item_code = item_lookup.get(key)
                    if not item_code:
                        item_code = _create_item(row, model_name, mfg_name)
                        item_lookup[key] = item_code
                        items_created += 1

                    row["_model_name"] = model_name
                    row["_mfg_name"] = mfg_name

                elif row.get("item_name"):
                    # no (model, manufacturer) combination — fall back to
                    # a plain Item from item_name alone
                    item_code = _create_item(row, None, None)
                    items_created += 1
                    row["_model_name"] = None
                    row["_mfg_name"] = None

                else:
                    # neither a full combination nor an item_name to fall
                    # back on — nothing to create for this row; skip it
                    # and keep going with the rest
                    skipped += 1
                    errors.append({
                        "row": idx + 2,
                        "error": "Skipped — no model+manufacturer combination and no item_name",
                    })
                    continue

                row["item_code"] = item_code

                serial_no = row.get("serial_number")
                if serial_no and serial_no not in existing_serials:
                    _create_serial(serial_no, item_code, doc.company)
                    existing_serials.add(serial_no)
                    serials_created += 1

            except Exception:
                errors.append({"row": idx + 2, "error": frappe.get_traceback()})

            if (idx + 1) % PROGRESS_EVERY == 0:
                doc.db_set("processed_rows", idx + 1, update_modified=False)
                frappe.publish_realtime(
                    "item_bulk_import_progress",
                    {"name": name, "processed": idx + 1, "total": len(rows)},
                    user=doc.owner,
                )
                frappe.db.commit()

        # -----------------------------------------------------------
        # Step 4 — build the Maintenance Contract itself, as a Draft.
        # Every row already has item_code/model/mfg/serial resolved, so
        # when the user submits it later, before_submit has nothing left
        # to create for these rows.
        # -----------------------------------------------------------
        mc_name = _create_maintenance_contract(doc, rows)
        doc.db_set("created_maintenance_contract", mc_name, update_modified=False)

        doc.db_set("processed_rows", len(rows), update_modified=False)
        doc.db_set("models_created", models_created, update_modified=False)
        doc.db_set("mfgs_created", mfgs_created, update_modified=False)
        doc.db_set("items_created", items_created, update_modified=False)
        doc.db_set("serials_created", serials_created, update_modified=False)
        doc.db_set("error_log", frappe.as_json(errors), update_modified=False)
        doc.db_set("status", "Completed", update_modified=False)

        if skipped:
            frappe.log_error(
                title=f"Item Bulk Import {name}: {skipped} row(s) skipped",
                message=f"{skipped} of {len(rows)} rows had no model+manufacturer "
                        f"combination and no item_name — see error_log for the row numbers.",
            )

        frappe.publish_realtime(
            "item_bulk_import_done",
            {"name": name, "status": "Completed", "maintenance_contract": mc_name},
            user=doc.owner,
        )

    except Exception:
        frappe.db.rollback()
        doc.db_set("status", "Failed", update_modified=False)
        doc.db_set("error_log", frappe.get_traceback(), update_modified=False)
        frappe.log_error(title=f"Item Bulk Import {name} failed")
        frappe.publish_realtime(
            "item_bulk_import_done", {"name": name, "status": "Failed"}, user=doc.owner
        )


# ---------------------------------------------------------------------
# Row-level creation (only called for genuinely missing records)
#
# To go faster than one-doc-at-a-time here, replace the body of
# _create_item / _create_serial with a true bulk insert once you've
# collected ALL the missing rows for this import (build a list of dicts,
# generate names via frappe.model.naming.make_autoname(...) for each,
# fill in owner/creation/modified/modified_by/docstatus, then call
# frappe.db.bulk_insert(doctype, fields, values)). That skips validate()/
# hooks entirely, so only do it if you've confirmed neither doctype has
# side effects you rely on beyond the fields being set.
# ---------------------------------------------------------------------

def _create_item(row, model_name, mfg_name):
    new_doc = frappe.new_doc("Item")
    new_doc.naming_series = ".######"
    new_doc.item_name = row.get("item_name") or ""
    new_doc.item_group = row.get("item_group") or "Equipments"
    new_doc.description = row.get("item_name") or ""
    new_doc.model = model_name
    new_doc.stock_uom = row.get("uom") or ""
    new_doc.is_stock_item = 1
    new_doc.mfg = mfg_name
    new_doc.insert(ignore_permissions=True)
    return new_doc.name


def _create_serial(serial_no, item_code, company):
    sn_doc = frappe.new_doc("Serial Number")
    sn_doc.serial_no = serial_no
    sn_doc.item_code = item_code
    sn_doc.company = company
    # Not tied to a contract yet — Maintenance Contract.before_submit flips
    # this to "Active" when a contract that references it is submitted.
    sn_doc.status = "Inactive"
    sn_doc.insert(ignore_permissions=True)


def _create_maintenance_contract(doc, rows):
    mc = frappe.new_doc("Maintenance Contract")
    mc.naming_series = doc.custom_naming_series
    mc.type = doc.type
    mc.customer = doc.customer
    mc.company = doc.company
    mc.branch = doc.branch
    mc.sales_person = doc.sales_person
    mc.department = doc.department
    mc.incharge = doc.incharge
    mc.date = doc.date or frappe.utils.today()

    for row in rows:
        # rows that had neither a (model, manufacturer) combination nor an
        # item_name were skipped earlier and never got an item_code —
        # nothing to add to the contract for those
        if not row.get("item_code"):
            continue

        mc.append("equipments", {
            "item_code": row.get("item_code"),
            "item_name": row.get("item_name"),
            "model": row.get("_model_name"),
            "manufacturer": row.get("_mfg_name"),
            "serial_number": row.get("serial_number"),
            "qty": row.get("qty") or 1,
            "item_group": row.get("item_group"),
            "description": row.get("item_name"),
        })
    mc.flags.ignore_mandatory = True  # left as Draft — user reviews, then submits
    mc.insert(ignore_permissions=True)
    return mc.name


# ---------------------------------------------------------------------
# Excel I/O
# ---------------------------------------------------------------------

def _read_excel(file_url):
    import openpyxl

    file_path = get_file_path(file_url)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    header_row = next(ws.iter_rows(min_row=1, max_row=1))
    headers = [str(c.value).strip().lower() if c.value else "" for c in header_row]

    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        frappe.throw(_("Missing columns in template: {0}").format(", ".join(missing)))

    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not any(r):
            continue
        row = dict(zip(headers, r))
        row = {k: (str(v).strip() if v is not None else "") for k, v in row.items()}
        if "qty" in row:
            row["qty"] = frappe.utils.cint(row["qty"]) or 1
        rows.append(row)
    return rows
