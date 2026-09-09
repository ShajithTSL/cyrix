import json
import frappe
from frappe.utils import flt


def _recompute_invoiced_value(reference_type, reference_name):
    item_field = {
        "Job Order Data": "job_order_data",
        "Supply Order Data": "supply_order_data",
        "Budgetary Quotation": "budgetary_quotation",
    }[reference_type]

    amount_expr = "COALESCE(NULLIF(sii.total_amount, 0), sii.net_amount, 0)"

    result = frappe.db.sql(f"""
        SELECT SUM(
            CASE WHEN si.is_return = 1
                THEN -ABS({amount_expr})
                ELSE ABS({amount_expr})
            END
        ) AS total
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
        AND sii.{item_field} = %s
    """, (reference_name,), as_dict=True)

    return flt(result[0].total) if result and result[0].total else 0


def _recompute_maintenance_contract_invoiced_value(contract_name):
    amount_expr = "COALESCE(NULLIF(sii.total_amount, 0), sii.net_amount, 0)"

    result = frappe.db.sql(f"""
        SELECT SUM(
            CASE WHEN si.is_return = 1
                THEN -ABS({amount_expr})
                ELSE ABS({amount_expr})
            END
        ) AS total
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
        AND (
            sii.maintenance_contract = %(name)s
            OR (
                si.maintenance_contract = %(name)s
                AND (sii.maintenance_contract IS NULL OR sii.maintenance_contract = '')
            )
        )
    """, {"name": contract_name}, as_dict=True)

    return flt(result[0].total) if result and result[0].total else 0


def update_jo_so_status(doc, method):
    skip_jo_cancellation = doc.get("cancel_job_orders")

    touched_jo, touched_so, touched_bq = set(), set(), set()

    for item in doc.get("items"):
        if item.get("job_order_data"):
            jo_name = item.get("job_order_data")
            jo = frappe.get_doc("Job Order Data", jo_name)

            if doc.is_return:
                if not skip_jo_cancellation:
                    jo.status = "C-Cancelled"
                    jo.add_comment("Comment", text="Invoice Cancelled by " + frappe.session.user)
                # else: user chose "Don't Cancel Job Order" -> leave status as-is
            else:
                jo.status = "RSI-Repaired and Shipped Invoiced"

            jo.invoice_no = doc.name
            jo.invoice_date = doc.posting_date
            jo.save(ignore_permissions=True)
            touched_jo.add(jo_name)

        elif item.get("supply_order_data"):
            so_name = item.get("supply_order_data")
            so = frappe.get_doc("Supply Order Data", so_name)
            so.status = 'Invoiced'
            so.invoice_no = doc.name
            so.invoice_date = doc.posting_date
            so.save(ignore_permissions=True)
            touched_so.add(so_name)

        elif item.get("budgetary_quotation"):
            bq_name = item.get("budgetary_quotation")
            bq = frappe.get_doc("Budgetary Quotation", bq_name)
            bq.status = 'Invoiced'
            bq.invoice_no = doc.name
            bq.invoice_date = doc.posting_date
            bq.save(ignore_permissions=True)
            touched_bq.add(bq_name)

    for jo_name in touched_jo:
        frappe.db.set_value(
            "Job Order Data", jo_name, "invoiced_value",
            _recompute_invoiced_value("Job Order Data", jo_name),
        )
    for so_name in touched_so:
        frappe.db.set_value(
            "Supply Order Data", so_name, "invoiced_value",
            _recompute_invoiced_value("Supply Order Data", so_name),
        )
    for bq_name in touched_bq:
        frappe.db.set_value(
            "Budgetary Quotation", bq_name, "invoiced_value",
            _recompute_invoiced_value("Budgetary Quotation", bq_name),
        )


def update_service_call_form(doc, method):
    if doc.get("service_call_form"):
        frappe.db.set_value("Service Call Form", doc.get("service_call_form"), "sales_invoice", doc.name)
        frappe.db.set_value("Service Call Form", doc.get("service_call_form"), "status", "Invoiced")


def update_maintenance_contract_status(doc, method):
    contract_names = set()
    for item in doc.get("items") or []:
        contract_name = item.get("maintenance_contract") or doc.get("maintenance_contract")
        if contract_name:
            contract_names.add(contract_name)

    for contract_name in contract_names:
        mc = frappe.get_doc("Maintenance Contract", contract_name)
        mc.status = "Invoiced"
        mc.save(ignore_permissions=True)

        frappe.db.set_value(
            "Maintenance Contract", contract_name, "invoiced_value",
            _recompute_maintenance_contract_invoiced_value(contract_name),
        )


def update_invoice_percentage(doc, method):
    for item in doc.get("items"):
        if item.get("qi_reference"):
            qi_doc = frappe.get_doc("Quotation Item", item.get("qi_reference"))
            if qi_doc.qty:
                frappe.db.set_value("Quotation Item", item.get("qi_reference"), "invoiced_qty", qi_doc.invoiced_qty + item.qty)

            parent_qt = frappe.get_doc("Quotation", qi_doc.parent)
            total_qty = sum([d.qty for d in parent_qt.items])
            total_invoiced_qty = sum([d.invoiced_qty for d in parent_qt.items])
            percentage = (total_invoiced_qty / total_qty) * 100 if total_qty else 0
            frappe.db.set_value("Quotation", qi_doc.parent, "invoiced", percentage)


def update_invoice_percentage_on_cancel(doc, method):
    for item in doc.get("items"):
        if item.get("qi_reference"):
            qi_doc = frappe.get_doc("Quotation Item", item.get("qi_reference"))
            if qi_doc.qty:
                frappe.db.set_value("Quotation Item", item.get("qi_reference"), "invoiced_qty", qi_doc.invoiced_qty - item.qty)

            parent_qt = frappe.get_doc("Quotation", qi_doc.parent)
            total_qty = sum([d.qty for d in parent_qt.items])
            total_invoiced_qty = sum([d.invoiced_qty for d in parent_qt.items])
            percentage = (total_invoiced_qty / total_qty) * 100 if total_qty else 0
            frappe.db.set_value("Quotation", qi_doc.parent, "invoiced", percentage)


def update_branch():
    branches = frappe._dict(
        frappe.get_all(
            "Purchase Invoice",
            fields=["name", "branch"],
            as_list=True
        )
    )

    for row in frappe.get_all("Purchase Invoice Item", filters={"branch": ["in", ["", None]]}, fields=["name", "parent"]):
        if branches.get(row.parent):
            frappe.db.set_value("Purchase Invoice Item", row.name, "branch", branches[row.parent], update_modified=False)

    for row in frappe.get_all("Purchase Taxes and Charges", filters={"branch": ["in", ["", None]]}, fields=["name", "parent"]):
        if branches.get(row.parent):
            frappe.db.set_value("Purchase Taxes and Charges", row.name, "branch", branches[row.parent], update_modified=False)

    frappe.db.commit()


def update_vat_receivable():
    si_list = frappe.get_all("Sales Taxes and Charges", {'parenttype': "Sales Invoice", 'account_head': "1020801 - VAT Receivable 15% - BM", "docstatus": 1}, "parent")
    for s in si_list:
        doc = frappe.get_doc("Sales Invoice", s.parent)
        for s in doc.taxes:
            s.account_head = "2010504 - VAT Payable 15% - BM"
        print(s.parent)
        doc.flags.ignore_mandatory = True
        doc.save()


REFERENCE_FIELDS = (
    ("Job Order Data", ("job_order_data",)),
    ("Supply Order Data", ("supply_order_data",)),
    ("Budgetary Quotation", ("budgetary_quotation",)),
    ("Maintenance Contract", ("maintenance_contract", "parent_maintenance_contract")),
)


def _get_jo_so_info_for_invoice(sales_invoice_name):
    amount_expr = "COALESCE(NULLIF(sii.total_amount, 0), sii.net_amount, 0)"

    rows = frappe.db.sql(f"""
        SELECT
            sii.job_order_data AS job_order_data,
            sii.supply_order_data AS supply_order_data,
            sii.budgetary_quotation AS budgetary_quotation,
            sii.maintenance_contract AS maintenance_contract,
            si.maintenance_contract AS parent_maintenance_contract,
            {amount_expr} AS amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.name = %s
    """, (sales_invoice_name,), as_dict=True)

    item_totals = {}  # (reference_type, reference_name) -> summed amount for THIS invoice
    for row in rows:
        for reference_type, fieldnames in REFERENCE_FIELDS:
            reference_name = next(
                (row.get(fieldname) for fieldname in fieldnames if row.get(fieldname)),
                None,
            )
            if not reference_name:
                continue
            key = (reference_type, reference_name)
            item_totals[key] = item_totals.get(key, 0) + flt(row.amount)
            break  # an item belongs to at most one reference type

    info = []
    for (reference_type, reference_name), invoice_item_amount in item_totals.items():
        ref_values = frappe.db.get_value(
            reference_type,
            reference_name,
            ["invoiced_value", "advance_payment_amount"],
            as_dict=True,
        )
        if not ref_values:
            continue

        invoiced_value = flt(ref_values.invoiced_value)
        advance_payment_amount = flt(ref_values.advance_payment_amount)
        remaining = invoiced_value - advance_payment_amount

        info.append({
            "reference_type": reference_type,
            "reference_name": reference_name,
            "invoiced_value": invoiced_value,
            "advance_payment_amount": advance_payment_amount,
            "remaining_to_be_paid": remaining,
            "paid": 1 if remaining == 0 else 0,
            "invoice_item_amount": invoice_item_amount,
        })

    return info


def _split_amount_by_invoice_share(jo_so_info, total_amount):
    invoice_total = sum(flt(info["invoice_item_amount"]) for info in jo_so_info)
    if invoice_total <= 0:
        return [(jo_so_info[0], flt(total_amount))] if jo_so_info else []

    return [
        (info, flt(total_amount) * flt(info["invoice_item_amount"]) / invoice_total)
        for info in jo_so_info
    ]


def _apply_status(ref_doc, reference_type, updated_amount):
    if updated_amount <= 0:
        ref_doc.status = "Unpaid" if reference_type in ["Job Order Data", "Supply Order Data"] else "Invoiced"
    elif flt(ref_doc.invoiced_value) == updated_amount:
        ref_doc.status = "P-Paid" if reference_type == "Job Order Data" else "Paid"
    else:
        ref_doc.status = "Partially Paid"


# ---------------------------------------------------------------------
# A) Payment Entry - custom button + submit/cancel (unchanged - the
#    button flow already has a manual, per-reference allocate_amount,
#    so it never had the "full amount to every reference" bug)
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_jo_so_details(references):
    """Backs the custom 'Get JO/SO Details' button on Payment Entry."""
    references = json.loads(references)
    jo_so_info = []
    for i in references:
        if i.get("reference_name"):
            jo_so_info.extend(_get_jo_so_info_for_invoice(i["reference_name"]))
    return jo_so_info


def _apply_job_order_row(row, payment_entry_name, posting_date):
    if not (row.reference_name and flt(row.allocate_amount) > 0):
        return
    doc = frappe.get_doc(row.reference_type, row.reference_name)
    updated_amount = flt(doc.advance_payment_amount) + flt(row.allocate_amount)

    _apply_status(doc, row.reference_type, updated_amount)

    doc.payment_entry = payment_entry_name
    doc.advance_payment_amount = updated_amount
    doc.advance_paid_date = posting_date
    doc.save(ignore_permissions=True)


def _reverse_job_order_row(row):
    if not (row.reference_name and flt(row.allocate_amount) > 0):
        return
    doc = frappe.get_doc(row.reference_type, row.reference_name)
    updated_amount = flt(doc.advance_payment_amount) - flt(row.allocate_amount)

    _apply_status(doc, row.reference_type, updated_amount)

    doc.payment_entry = ''
    doc.advance_payment_amount = updated_amount
    if updated_amount == 0:
        doc.advance_paid_date = ''
    doc.save(ignore_permissions=True)


def _append_to_sync_log(sales_invoice_name, payment_entry_name, row_names):
    if not row_names:
        return

    existing_log = frappe.db.get_value("Sales Invoice", sales_invoice_name, "jo_so_sync_log")
    try:
        applied = json.loads(existing_log) if existing_log else []
    except ValueError:
        applied = []

    for row_name in row_names:
        applied.append({"payment_entry": payment_entry_name, "row_name": row_name})

    frappe.db.set_value(
        "Sales Invoice", sales_invoice_name, "jo_so_sync_log", json.dumps(applied),
        update_modified=False,
    )


def update_payment_reference(self, method):
    if self.payment_type == 'Receive':
        row_names = []
        for row in self.job_order_table:
            _apply_job_order_row(row, self.name, self.posting_date)
            if row.reference_name and flt(row.allocate_amount) > 0:
                row_names.append(row.name)

        if not row_names:
            return

        si_refs = [
            r.reference_name for r in self.references
            if r.reference_doctype == "Sales Invoice" and r.reference_name
        ]

        if len(si_refs) == 1:
            _append_to_sync_log(si_refs[0], self.name, row_names)
        elif len(si_refs) > 1:
            frappe.log_error(
                title="JO/SO sync: ambiguous invoice attribution",
                message=(
                    f"Payment Entry {self.name} has job_order_table rows and references "
                    f"multiple Sales Invoices ({si_refs}). These rows were NOT logged "
                    f"against any of those invoices, so cancelling one of them will not "
                    f"auto-reverse these rows - cancel this Payment Entry instead, or "
                    f"reverse manually."
                ),
            )


def update_payment_reference_cancel(self, method):
    if self.payment_type == 'Receive':
        for row in self.job_order_table:
            _reverse_job_order_row(row)


# ---------------------------------------------------------------------
# B) Sales Invoice submit/cancel - NOW splits proportionally across
#    distinct references instead of giving each one the full amount.
# ---------------------------------------------------------------------

def sync_jo_so_on_si_submit(self, method):
    """Hook: Sales Invoice on_submit"""
    if not self.advances:
        return

    jo_so_info = _get_jo_so_info_for_invoice(self.name)
    if not jo_so_info:
        return

    for adv in self.advances:
        if adv.reference_type != "Payment Entry" or not adv.reference_name:
            continue

        allocated_amount = flt(adv.allocated_amount)
        if allocated_amount <= 0:
            continue

        pe_doc = frappe.get_doc("Payment Entry", adv.reference_name)
        new_rows = []

        for info, share_amount in _split_amount_by_invoice_share(jo_so_info, allocated_amount):
            if share_amount <= 0:
                continue

            new_row = pe_doc.append("job_order_table", {})
            new_row.reference_type = info["reference_type"]
            new_row.reference_name = info["reference_name"]
            new_row.invoiced_value = info["invoiced_value"]
            new_row.advance_payment_amount = info["advance_payment_amount"]
            new_row.remaining_to_be_paid = info["remaining_to_be_paid"]
            new_row.allocate_amount = share_amount
            new_row.paid = info["paid"]

            _apply_job_order_row(new_row, pe_doc.name, self.posting_date)
            new_rows.append(new_row)

        pe_doc.flags.ignore_validate_update_after_submit = True
        pe_doc.save(ignore_permissions=True)

        _append_to_sync_log(self.name, pe_doc.name, [row.name for row in new_rows])


def sync_jo_so_on_si_cancel(self, method):
    """Hook: Sales Invoice on_cancel"""
    log = self.get("jo_so_sync_log")
    if not log:
        return

    try:
        applied = json.loads(log)
    except ValueError:
        applied = []
    if not applied:
        return

    by_pe = {}
    for entry in applied:
        by_pe.setdefault(entry["payment_entry"], []).append(entry["row_name"])

    for payment_entry_name, row_names in by_pe.items():
        pe_docstatus = frappe.db.get_value("Payment Entry", payment_entry_name, "docstatus")
        if pe_docstatus is None:
            continue
        if pe_docstatus != 1:
            continue

        pe_doc = frappe.get_doc("Payment Entry", payment_entry_name)
        row_names_set = set(row_names)

        rows_to_keep = []
        for row in pe_doc.job_order_table:
            if row.name in row_names_set:
                _reverse_job_order_row(row)
                continue
            rows_to_keep.append(row)

        pe_doc.set("job_order_table", rows_to_keep)
        pe_doc.flags.ignore_validate_update_after_submit = True
        pe_doc.save(ignore_permissions=True)

    frappe.db.set_value(
        "Sales Invoice", self.name, "jo_so_sync_log", "",
        update_modified=False,
    )