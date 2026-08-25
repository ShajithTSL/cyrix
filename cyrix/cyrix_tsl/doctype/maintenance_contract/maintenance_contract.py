import frappe
from frappe import _
from frappe.model.document import Document
from cyrix.custom_py import utils
from datetime import datetime

from cyrix.custom_py.bulk_import_utils import bulk_get_or_create, bulk_activate_serials

BULK_LOOKUP_CHUNK_SIZE = 500  # keep IN-clauses to a sane size

ITEM_MODEL_TITLE_FIELD = "model"          # confirmed from child table's fetch_from
ITEM_MFG_TITLE_FIELD = "mfg"     # TODO: confirm against your Item Mfg doctype


class MaintenanceContract(Document):
    def before_submit(self):
        self.status = "Submitted"
        now = datetime.now()
        self.append("status_duration_details",{
            "status":self.status,
            "date":now,
        })
    
        if self.status != self.status_duration_details[-1].status:
            ldate = self.status_duration_details[-1].date
            now = datetime.now()
            time_date = str(ldate).split(".")[0]
            format_data = "%Y-%m-%d %H:%M:%S"
            date = datetime.strptime(time_date, format_data)
            duration = now - date
            duration_in_s = duration.total_seconds()
            minutes = divmod(duration_in_s, 60)[0]/60
            data = str(minutes).split(".")[0]+"hrs "+str(minutes).split(".")[1][:2]+"min"
            self.status_duration_details[-1].duration = data
            self.append("status_duration_details",{
                "status":self.status,
                "date":now,
            })

        items = self.get('items') or []
        if not items:
            return

        # rows needing any creation at all — normally empty/tiny once the
        # bulk import tool has pre-resolved item_code for everything
        pending = [i for i in items if not i.get('item_code')]

        if pending:
            model_map, mfg_map = self._resolve_models_and_mfgs(pending)
            item_lookup = self._get_existing_item_lookup(pending, model_map, mfg_map)
            for i in pending:
                self.check_for_item(i, item_lookup, model_map, mfg_map)

        self._activate_serials(items)

    def on_update_after_submit(self):
        if self.status != self.status_duration_details[-1].status:
            ldate = self.status_duration_details[-1].date
            now = datetime.now()
            time_date = str(ldate).split(".")[0]
            format_data = "%Y-%m-%d %H:%M:%S"
            date = datetime.strptime(time_date, format_data)
            duration = now - date
            duration_in_s = duration.total_seconds()
            minutes = divmod(duration_in_s, 60)[0]/60
            data = str(minutes).split(".")[0]+"hrs "+str(minutes).split(".")[1][:2]+"min"
            frappe.db.set_value("Status Duration Details",self.status_duration_details[-1].name,"duration",data)
            self.append("status_duration_details",{
                "status":self.status,
                "date":now,
            })
            doc = frappe.get_doc("Maintenance Contract",self.name)
            doc.append("status_duration_details",{
                "status":self.status,
                "date":now,
            })
            doc.save(ignore_permissions=True)


    # ------------------------------------------------------------------
    # Bulk lookups (replace the old per-row frappe.db.get_value / exists)
    # ------------------------------------------------------------------

    def _resolve_models_and_mfgs(self, pending):
        """
        model/manufacturer on the child table are Link fields (to Item
        Model / Item Mfg), so their values must exist as real records
        before an Item can be saved referencing them. Resolve/create both
        in bulk rather than trusting the raw child-table values are
        already valid link targets.

        Only rows with BOTH model and manufacturer set count as a valid
        combination to resolve — a row with just one of the two doesn't
        identify anything and is left for check_for_item to skip/fall
        through, not half-resolved here.
        """
        complete = [i for i in pending if i.get('model') and i.get('manufacturer')]

        model_map, _created_models = bulk_get_or_create(
            "Item Model", ITEM_MODEL_TITLE_FIELD, [i.get('model') for i in complete]
        )
        mfg_map, _created_mfgs = bulk_get_or_create(
            "Item Mfg", ITEM_MFG_TITLE_FIELD, [i.get('manufacturer') for i in complete]
        )
        return model_map, mfg_map

    def _get_existing_item_lookup(self, pending, model_map, mfg_map):
        """
        One query instead of one per row. Returns {(model, mfg): item_row},
        keyed by the *resolved* Item Model / Item Mfg doc names.

        Only rows with both model and manufacturer set contribute to the
        filter — see _resolve_models_and_mfgs.

        Note: the filter below fetches every Item whose model OR mfg is in
        the requested sets (an AND-of-INs, which can over-fetch compared to
        the exact pairs requested). That's fine — matching happens by exact
        (model, mfg) tuple afterwards, so over-fetched rows are simply
        unused, never mis-assigned.
        """
        complete = [i for i in pending if i.get('model') and i.get('manufacturer')]

        resolved_models = list({model_map.get(i.get('model')) for i in complete})
        resolved_mfgs = list({mfg_map.get(i.get('manufacturer')) for i in complete})

        if not resolved_models and not resolved_mfgs:
            return {}

        existing = frappe.get_all(
            "Item",
            filters=[["model", "in", resolved_models], ["mfg", "in", resolved_mfgs]],
            fields=["name", "model", "mfg", "item_name"],
        )
        return {(d.model, d.mfg): d for d in existing}

    # ------------------------------------------------------------------
    # Serial Number activation — bulk UPDATE for existing serials,
    # normal Document API only for genuinely new ones.
    # ------------------------------------------------------------------

    def _activate_serials(self, items):
        rows_with_serial = [i for i in items if i.get('serial_number')]
        if not rows_with_serial:
            return

        serials = [i.get('serial_number') for i in rows_with_serial]
        existing = set()
        for start in range(0, len(serials), BULK_LOOKUP_CHUNK_SIZE):
            chunk = serials[start:start + BULK_LOOKUP_CHUNK_SIZE]
            existing.update(
                frappe.get_all("Serial Number", filters={"name": ["in", chunk]}, pluck="name")
            )

        to_activate = {}  # serial_no -> item_code, for existing serials
        for i in rows_with_serial:
            serial_number = i.get('serial_number')
            if serial_number in existing:
                to_activate[serial_number] = i.get('item_code')
            else:
                sn_doc = frappe.new_doc("Serial Number")
                sn_doc.serial_no = serial_number
                sn_doc.item_code = i.get('item_code')
                sn_doc.company = self.company
                sn_doc.status = "Active"
                sn_doc.insert(ignore_permissions=True)
                existing.add(serial_number)

        # one/few UPDATE statements instead of hundreds of .save() calls —
        # see bulk_import_utils.bulk_activate_serials for the tradeoffs
        bulk_activate_serials(to_activate)

    # ------------------------------------------------------------------
    # Fallback per-row creation — only reached for rows without a
    # pre-resolved item_code (i.e. bypassed the bulk import tool).
    # ------------------------------------------------------------------

    def check_for_item(self, i, item_lookup, model_map, mfg_map):
        # Only a genuine (model, manufacturer) *pair* identifies an Item
        # combination worth resolving/creating. A row with just one of the
        # two doesn't — skip this check for it and fall through instead
        # of creating a half-populated Item.
        if i.get("model") and i.get("manufacturer"):
            model_name = model_map.get(i.get('model'))
            mfg_name = mfg_map.get(i.get('manufacturer'))
            key = (model_name, mfg_name)
            match = item_lookup.get(key)

            if match:
                i.item_code = match.name
                i.item_name = match.item_name
            else:
                new_doc = self._make_item(i, model_name, mfg_name)
                i.item_code = new_doc.name
                # register so other rows in the same contract reuse it
                # instead of creating a duplicate Item
                item_lookup[key] = frappe._dict(
                    name=new_doc.name,
                    model=new_doc.model,
                    mfg=new_doc.mfg,
                    item_name=new_doc.item_name,
                )

        elif i.get("item_name"):
            # no model+manufacturer combination — fall back to creating a
            # plain Item from item_name alone (model/mfg left unset)
            new_doc = self._make_item(i, None, None)
            i.item_code = new_doc.name

        # else: neither a (model, manufacturer) combination nor an
        # item_name — nothing to resolve or create for this row, skip it
        # and move on to the remaining rows/combinations.

    def _make_item(self, i, model_name, mfg_name):
        new_doc = frappe.new_doc('Item')
        new_doc.naming_series = '.######'
        new_doc.item_name = i.get('item_name') or ""
        new_doc.item_group = i.get('item_group') or "Equipments"
        new_doc.description = i.get('item_name') or ""
        new_doc.model = model_name
        new_doc.stock_uom = i.get('uom') or "Nos"
        new_doc.is_stock_item = 1
        new_doc.mfg = mfg_name
        new_doc.insert(ignore_permissions=True)
        return new_doc


# ----------------------------------------------------------------------
# Background submission (used for large contracts to keep the HTTP
# request fast; the actual submit — including before_submit above — runs
# on an RQ worker with a 1500s timeout instead of the web request's).
# ----------------------------------------------------------------------

@frappe.whitelist()
def queue_submit(name):
    doc = frappe.get_doc("Maintenance Contract", name)
    doc.check_permission("submit")

    if doc.docstatus != 0:
        frappe.throw(_("Only draft documents can be queued for submission"))

    frappe.db.set_value(
        "Maintenance Contract", name, "queue_status", "Queued", update_modified=False
    )

    frappe.enqueue(
        "cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.background_submit",
        queue="long",
        timeout=3000,
        name=name,
        enqueue_after_commit=True,
    )
    return {"queued": True}


def background_submit(name):
    doc = frappe.get_doc("Maintenance Contract", name)
    try:
        doc.submit()
        frappe.db.set_value(
            "Maintenance Contract", name, "queue_status", "Submitted", update_modified=False
        )
        frappe.publish_realtime(
            event="maintenance_contract_submitted",
            message={"name": name, "status": "success"},
            user=doc.owner,
        )
    except Exception:
        frappe.db.rollback()
        frappe.db.set_value(
            "Maintenance Contract", name, "queue_status", "Failed", update_modified=False
        )
        frappe.log_error(title=f"Maintenance Contract {name} background submit failed")
        frappe.publish_realtime(
            event="maintenance_contract_submitted",
            message={"name": name, "status": "failed", "error": frappe.get_traceback()},
            user=doc.owner,
        )



# Interval is mentioned in days. Need to calculate the no of schedules based on the start and end date and interval and return the list of schedule dates
@frappe.whitelist()
def create_schedule(from_date, to_date, interval):
    schedule_dates = []
    current_date = from_date

    while current_date <= to_date:
        schedule_dates.append(current_date)
        current_date = frappe.utils.add_days(current_date, int(interval))

    return schedule_dates


# @frappe.whitelist()
# def create_service_call_form(source):
# 	doc = frappe.get_doc("Maintenance Contract", source)
# 	new_doc = frappe.new_doc("Service Call Form")
# 	new_doc.document_type = "Maintenance Contract"
# 	new_doc.related_doc = doc.name
# 	new_doc.customer = doc.customer
# 	new_doc.company = doc.company
# 	new_doc.sales_person = doc.sales_person
# 	new_doc.branch = doc.branch

# 	return new_doc

from frappe.model.mapper import get_mapped_doc
@frappe.whitelist()
def create_service_call_form(source, target_doc=None):
    doc = get_mapped_doc(
        "Maintenance Contract",
        source,
        {
            "Maintenance Contract": {
                "doctype": "Service Call Form",
                "field_map": {
                    "doctype": "document_type",
                    "name": "related_doc",
                    "description": "reason"
                },
            },
            "Maintenance Contract Item": {
                "doctype": "Service Call Item"
            },
        },
        target_doc,
    )
    doc.naming_series = ""
    doc.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or ""

    return doc

# route to Create Job Order single doctype page with reference to Maintenance Contract and pre-fill the item details in Job Order Item child table based on the items added in Maintenance Contract
@frappe.whitelist()
def create_job_order(source, row_name):
    doc = frappe.get_doc("Maintenance Contract", source)
    # if doc.items:
    job_order = frappe.new_doc("Create Job Order")
    job_order.maintenance_contract = doc.name
    job_order.customer = doc.customer
    job_order.incharge = doc.incharge
    job_order.incharge_name = doc.incharge_name
    job_order.incharge_email = doc.incharge_email
    job_order.incharge_phone_no = doc.incharge_phone_no
    job_order.company = doc.company
    job_order.sales_person = doc.sales_person
    job_order.branch = doc.branch
    for item in doc.items:
        if row_name and item.name != row_name:
            continue
        serial_no = item.serial_number if item.serial_number else ""
        has_serial_no = 1 if item.serial_number else 0
        job_order.append("received_equipment", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "model": item.model,
            "manufacturer": item.manufacturer,
            "serial_no": serial_no,
            "has_serial_no": has_serial_no,
            "uom": frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
            "qty": item.qty
        })
    return job_order


@frappe.whitelist()
def create_callibration(source):
    doc = frappe.get_doc("Maintenance Contract", source)
    # if doc.items:
    job_order = frappe.new_doc("Create Job Order")
    job_order.maintenance_contract = doc.name
    job_order.customer = doc.customer
    job_order.incharge = doc.incharge
    job_order.incharge_name = doc.incharge_name
    job_order.incharge_email = doc.incharge_email
    job_order.incharge_phone_no = doc.incharge_phone_no
    job_order.company = doc.company
    job_order.sales_person = doc.sales_person
    job_order.branch = doc.branch
    job_order.unit_type = "Calibration"
    for item in doc.items:
        serial_no = item.serial_number if item.serial_number else ""
        has_serial_no = 1 if item.serial_number else 0
        job_order.append("received_equipment", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "model": item.model,
            "manufacturer": item.manufacturer,
            "serial_no": serial_no,
            "has_serial_no": has_serial_no,
            "uom": frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
            "qty": item.qty
        })
    return job_order


@frappe.whitelist()
def create_qtn(source):
    doc = frappe.get_doc("Maintenance Contract",source)
    new_doc = frappe.new_doc("Quotation")	
    new_doc.company = doc.company
    new_doc.party_name = doc.customer
    new_doc.customer_address = frappe.db.get_value("Customer",doc.customer,"customer_primary_address")
    new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
    new_doc.quotation_type = "Internal Quotation - MC"
    new_doc.sales_person = doc.sales_person
    new_doc.maintenance_contract = doc.name
    new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
    new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
    new_doc.branch = doc.branch
    for item in doc.items:
        new_doc.append("items",{
            "item_code":item.item_code,
            "item_name":item.item_name,
            "model":frappe.db.get_value("Item", item.item_code, "model"),
            "mfg":frappe.db.get_value("Item", item.item_code, "mfg"),
            "description":item.description,
            "serial_number":item.serial_number,
            "qty":item.qty,
            "uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
            "stock_uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
            "conversion_factor":1,
            "maintenance_contract":doc.name
        })

    return new_doc




def update_quote():
    maintenance_contract = frappe.db.get_list("Maintenance Contract",{"docstatus":1},"name")
    for mc in maintenance_contract:
        self = frappe.get_doc("Maintenance Contract",mc.name)
        rebuild_maintenance_contract_status_history(self)

from datetime import datetime, time
import frappe



def normalize_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    return datetime.combine(value, time.min)



def rebuild_maintenance_contract_status_history(self):

    events = []

    mc_status_map = {
        "Customer Quotation - MC": {
            "Quoted to Customer": "Quoted",
            "Approved by Customer": "Approved",
            "Rejected by Customer": "Not Approved"
        },
        "Customer Quotation - MC - Revised": {
            "Quoted to Customer": "Quoted",
            "Approved by Customer": "Approved",
            "Rejected by Customer": "Not Approved"
        },
        "Internal Quotation - MC": {
            "Approved by Management": "Internal Quotation",
            "Waiting For Approval": "Pending Internal Approval"
        }
    }

    # ----------------------------------------
    # Quotations
    # ----------------------------------------

    quotation_items = frappe.get_all(
        "Quotation Item",
        filters={
            "maintenance_contract": self.name
        },
        fields=["parent"]
    )

    quotation_names = {
        row.parent for row in quotation_items
    }

    quotation_docs = frappe.get_all(
        "Quotation",
        filters={
            "maintenance_contract": self.name
        },
        fields=["name"]
    )

    quotation_names.update(
        row.name for row in quotation_docs
    )

    for quotation_name in quotation_names:

        quotation = frappe.get_doc(
            "Quotation",
            quotation_name
        )

        status = mc_status_map.get(
            quotation.quotation_type,
            {}
        ).get(
            quotation.workflow_state
        )

        if not status:
            continue

        events.append({
            "status": status,
            "date": normalize_datetime(
                quotation.creation
            ),
            "source": quotation.name
        })

    # ----------------------------------------
    # Sales Invoices
    # ----------------------------------------

    invoice_items = frappe.get_all(
        "Sales Invoice Item",
        filters={
            "maintenance_contract": self.name
        },
        fields=["parent"]
    )

    invoice_names = {
        row.parent for row in invoice_items
    }

    invoice_docs = frappe.get_all(
        "Sales Invoice",
        filters={
            "maintenance_contract": self.name
        },
        fields=["name"]
    )

    invoice_names.update(
        row.name for row in invoice_docs
    )

    for invoice_name in invoice_names:

        invoice = frappe.get_doc(
            "Sales Invoice",
            invoice_name
        )

        if invoice.docstatus != 1:
            continue

        invoice_datetime = frappe.utils.get_datetime(
            f"{invoice.posting_date} {invoice.posting_time}"
        )


        events.append({
            "status": "Invoiced",
            "date": invoice_datetime,
            "source": invoice.name
        })

    # ----------------------------------------
    # Sort
    # ----------------------------------------

    events = [
        event for event in events
        if event["date"]
    ]

    events.sort(
        key=lambda x: x["date"]
    )
    # ----------------------------------------
    # Remove consecutive duplicate statuses
    # ----------------------------------------

    cleaned_events = []

    for event in events:

        if (
            cleaned_events
            and cleaned_events[-1]["status"] == event["status"]
        ):
            continue

        cleaned_events.append(event)

    print(cleaned_events)

    # ----------------------------------------
    # Rebuild child table
    # ----------------------------------------

    self.set("status_duration_details", [])

    for event in cleaned_events:
        self.append(
            "status_duration_details",
            {
                "status": event["status"],
                "date": event["date"]
            }
        )


    # ----------------------------------------
    # Calculate durations
    # ----------------------------------------

    for i in range(len(self.status_duration_details) - 1):

        current = self.status_duration_details[i]
        next_row = self.status_duration_details[i + 1]

        duration = next_row.date - current.date

        total_minutes = int(duration.total_seconds() / 60)

        hours = total_minutes // 60
        minutes = total_minutes % 60

        current.duration = f"{hours}hrs {minutes}min"


    # ----------------------------------------
    # Update Maintenance Contract status
    # ----------------------------------------

    if cleaned_events:
        self.status = cleaned_events[-1]["status"]

    self.save()
