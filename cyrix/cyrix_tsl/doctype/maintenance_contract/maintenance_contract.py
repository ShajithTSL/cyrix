import frappe
from frappe import _
from frappe.model.document import Document
from cyrix.custom_py import utils
from datetime import datetime
from frappe.utils import getdate, add_days, today
from html import escape as escape_html
import json

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


# Maintainance Schedule mail


# ============================================================
# GENERATE SCHEDULE DATA
# ============================================================

def generate_schedule_data(
    from_date,
    to_date,
    interval,
    existing_data=None
):
    """
    Generate schedule rows between From Date and To Date.

    Existing descriptions and email flags are preserved
    for matching schedule dates.
    """

    if not from_date or not to_date or not interval:
        return []

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    try:
        interval = int(interval)
    except Exception:
        return []

    if interval <= 0:
        return []

    existing_map = {}

    # --------------------------------------------------------
    # Preserve existing schedule information
    # --------------------------------------------------------

    if existing_data:

        try:

            for row in existing_data:

                if not isinstance(row, dict):
                    continue

                schedule_date = row.get("date")

                if not schedule_date:
                    continue

                try:
                    schedule_date = getdate(schedule_date)
                except Exception:
                    continue

                existing_map[str(schedule_date)] = {
                    "description": (
                        row.get("description") or ""
                    ),
                    "email_7_days_sent": bool(
                        row.get(
                            "email_7_days_sent",
                            False
                        )
                    ),
                    "email_2_days_sent": bool(
                        row.get(
                            "email_2_days_sent",
                            False
                        )
                    ),
                }

        except Exception:
            existing_map = {}

    # --------------------------------------------------------
    # Generate schedule
    # --------------------------------------------------------

    schedule = []

    current_date = from_date

    while current_date <= to_date:

        date_string = str(current_date)

        old_data = existing_map.get(
            date_string,
            {
                "description": "",
                "email_7_days_sent": False,
                "email_2_days_sent": False,
            }
        )

        schedule.append(
            {
                "date": date_string,
                "description": (
                    old_data.get("description") or ""
                ),
                "email_7_days_sent": bool(
                    old_data.get(
                        "email_7_days_sent",
                        False
                    )
                ),
                "email_2_days_sent": bool(
                    old_data.get(
                        "email_2_days_sent",
                        False
                    )
                ),
            }
        )

        current_date = add_days(
            current_date,
            interval
        )

    return schedule


# ============================================================
# BACKFILL ALL MAINTENANCE CONTRACT ITEMS
# ============================================================

def generate_all_maintenance_contract_schedule_data():

    items = frappe.get_all(
        "Maintenance Contract Item",
        fields=[
            "name",
            "parent",
            "from_date",
            "to_date",
            "interval",
            "schedule_data",
        ],
        order_by="modified asc",
    )

    updated = 0
    skipped = 0
    errors = []

    for item in items:

        try:

            if (
                not item.from_date
                or not item.to_date
                or not item.interval
            ):
                skipped += 1
                continue

            existing_data = []

            if item.schedule_data:

                try:

                    existing_data = json.loads(
                        item.schedule_data
                    )

                    if not isinstance(
                        existing_data,
                        list
                    ):
                        existing_data = []

                except Exception:

                    existing_data = []

            schedule = generate_schedule_data(
                item.from_date,
                item.to_date,
                item.interval,
                existing_data,
            )

            frappe.db.set_value(
                "Maintenance Contract Item",
                item.name,
                "schedule_data",
                frappe.as_json(schedule),
                update_modified=False,
            )

            updated += 1

        except Exception as e:

            errors.append(
                {
                    "item": item.name,
                    "error": str(e),
                }
            )

    frappe.db.commit()

    return {
        "items_checked": len(items),
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


# ============================================================
# FORMAT DATE
# ============================================================

def format_schedule_date(value):

    if not value:
        return ""

    try:

        return getdate(value).strftime(
            "%d-%b-%Y"
        )

    except Exception:

        return str(value)


# ============================================================
# GET ITEM DETAILS
# ============================================================

def get_item_details(item_code):

    if not item_code:

        return {
            "item_code": "",
            "item_name": "",
            "description": "",
        }

    try:

        item = frappe.db.get_value(
            "Item",
            item_code,
            [
                "item_code",
                "item_name",
                "description",
            ],
            as_dict=True,
        )

        if not item:

            return {
                "item_code": item_code,
                "item_name": "",
                "description": "",
            }

        return {
            "item_code": (
                item.item_code
                or item_code
            ),
            "item_name": (
                item.item_name
                or ""
            ),
            "description": (
                item.description
                or ""
            ),
        }

    except Exception:

        return {
            "item_code": item_code,
            "item_name": "",
            "description": "",
        }


# ============================================================
# GET CUSTOMER SUPPORT AND MANAGER FROM BRANCH
# ============================================================

def get_branch_email_recipients(branch):

    if not branch:
        return [], []

    branch_doc = frappe.get_doc(
        "Branch",
        branch
    )

    recipients = []
    cc = []

    # --------------------------------------------------------
    # Customer Support -> TO
    # --------------------------------------------------------

    customer_support = (
        getattr(
            branch_doc,
            "customer_support",
            None
        )
        or ""
    )

    if customer_support:

        if isinstance(customer_support, str):

            recipients = [
                email.strip()
                for email in customer_support.split(",")
                if email.strip()
            ]

    # --------------------------------------------------------
    # Manager -> CC
    # --------------------------------------------------------

    manager = (
        getattr(
            branch_doc,
            "manager",
            None
        )
        or ""
    )

    if manager:

        if isinstance(manager, str):

            cc = [
                email.strip()
                for email in manager.split(",")
                if email.strip()
            ]

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    recipients = list(
        dict.fromkeys(recipients)
    )

    cc = list(
        dict.fromkeys(cc)
    )

    # --------------------------------------------------------
    # Do not keep Manager in TO
    # --------------------------------------------------------

    cc = [
        email
        for email in cc
        if email not in recipients
    ]

    return recipients, cc


# ============================================================
# SEND MAINTENANCE SCHEDULE EMAIL
# ============================================================

def send_schedule_email(
    contract,
    item,
    schedule_row,
    reminder_type,
):
    """
    Create Communication and send email using
    Frappe Communication.make functionality.

    Recipients are taken from Company -> info.
    """

    schedule_date = schedule_row.get(
        "date"
    )

    schedule_description = (
        schedule_row.get(
            "description"
        )
        or ""
    )

    # --------------------------------------------------------
    # Get company recipients
    # --------------------------------------------------------

    recipients, cc = get_branch_email_recipients(
    contract.branch
)

    if not recipients:

        frappe.throw(
            "No Customer Support email found in "
            f"Branch: {contract.branch}"
        )

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    customer_name = (
        getattr(
            contract,
            "customer",
            None
        )
        or getattr(
            contract,
            "customer",
            None
        )
        or ""
    )

    # --------------------------------------------------------
    # Item details
    # --------------------------------------------------------

    item_code = (
        getattr(
            item,
            "item_code",
            None
        )
        or getattr(
            item,
            "item",
            None
        )
        or ""
    )

    item_name = (
        getattr(
            item,
            "item_name",
            None
        )
        or ""
    )

    item_description = (
        getattr(
            item,
            "description",
            None
        )
        or ""
    )

    # --------------------------------------------------------
    # Item master lookup
    # --------------------------------------------------------

    item_details = get_item_details(
        item_code
    )

    if not item_name:

        item_name = (
            item_details.get(
                "item_name"
            )
            or ""
        )

    if not item_description:

        item_description = (
            item_details.get(
                "description"
            )
            or ""
        )

    # --------------------------------------------------------
    # Child item fields
    # --------------------------------------------------------

    from_date = getattr(
        item,
        "from_date",
        None
    )

    to_date = getattr(
        item,
        "to_date",
        None
    )

    interval = getattr(
        item,
        "interval",
        None
    )

    # --------------------------------------------------------
    # HTML escape
    # --------------------------------------------------------

    contract_name_html = escape_html(
        str(
            contract.name
            or ""
        )
    )

    customer_html = escape_html(
        str(
            customer_name
            or ""
        )
    )

    item_code_html = escape_html(
        str(
            item_code
            or ""
        )
    )

    item_name_html = escape_html(
        str(
            item_name
            or ""
        )
    )

    item_description_html = escape_html(
        str(
            item_description
            or ""
        )
    )

    schedule_description_html = escape_html(
        str(
            schedule_description
            or ""
        )
    )

    from_date_html = escape_html(
        format_schedule_date(
            from_date
        )
    )

    to_date_html = escape_html(
        format_schedule_date(
            to_date
        )
    )

    schedule_date_html = escape_html(
        format_schedule_date(
            schedule_date
        )
    )

    interval_html = escape_html(
        str(
            interval
            or ""
        )
    )

    reminder_html = escape_html(
        str(
            reminder_type
            or ""
        )
    )

    # --------------------------------------------------------
    # Reminder colors
    # --------------------------------------------------------

    if reminder_type == "7 Days Before":

        reminder_color = "#2563eb"
        reminder_background = "#eff6ff"

    else:

        reminder_color = "#dc2626"
        reminder_background = "#fef2f2"

    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------

    subject = (
        "Maintenance Schedule Reminder - "
        f"{contract.name} - "
        f"{format_schedule_date(schedule_date)}"
    )

    # --------------------------------------------------------
    # HTML EMAIL
    # --------------------------------------------------------

    message = f"""
    <div style="
        margin:0;
        padding:30px 15px;
        background:#f5f7fa;
        font-family:Arial,Helvetica,sans-serif;
        color:#1f2937;
    ">

        <div style="
            max-width:850px;
            margin:0 auto;
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:10px;
            overflow:hidden;
        ">

            <!-- HEADER -->

            <div style="
                background:#1f2937;
                padding:24px 30px;
                color:#ffffff;
            ">

                <div style="
                    font-size:22px;
                    font-weight:600;
                    margin-bottom:6px;
                ">
                    Maintenance Schedule Reminder
                </div>

                <div style="
                    font-size:13px;
                    color:#d1d5db;
                ">
                    Scheduled maintenance notification
                </div>

            </div>


            <!-- REMINDER -->

            <div style="
                margin:24px 30px 10px 30px;
                padding:14px 18px;
                background:{reminder_background};
                border-left:4px solid {reminder_color};
                border-radius:5px;
                color:{reminder_color};
                font-size:15px;
                font-weight:600;
            ">

                {reminder_html}

                &nbsp;&nbsp;|&nbsp;&nbsp;

                Scheduled Date:
                {schedule_date_html}

            </div>


            <!-- CONTRACT DETAILS -->

            <div style="
                padding:10px 30px 20px 30px;
            ">

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        font-size:14px;
                    "
                >

                    <tr>

                        <td style="
                            width:180px;
                            padding:9px 0;
                            color:#6b7280;
                            font-weight:600;
                        ">
                            Maintenance Contract
                        </td>

                        <td style="
                            padding:9px 0;
                            color:#111827;
                            font-weight:600;
                        ">
                            {contract_name_html}
                        </td>

                    </tr>

                    <tr>

                        <td style="
                            padding:9px 0;
                            color:#6b7280;
                            font-weight:600;
                        ">
                            Customer
                        </td>

                        <td style="
                            padding:9px 0;
                            color:#111827;
                        ">
                            {customer_html}
                        </td>

                    </tr>

                </table>

            </div>


            <!-- ITEM DETAILS -->

            <div style="
                padding:0 30px 25px 30px;
            ">

                <div style="
                    font-size:16px;
                    font-weight:600;
                    color:#111827;
                    margin-bottom:12px;
                ">
                    Maintenance Item Details
                </div>

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        border:1px solid #d1d5db;
                        font-size:13px;
                    "
                >

                    <thead>

                        <tr style="
                            background:#f3f4f6;
                        ">

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                Item Code
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                Item Name
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                Description
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:center;
                            ">
                                Interval
                            </th>

                        </tr>

                    </thead>

                    <tbody>

                        <tr>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                                vertical-align:top;
                            ">
                                {item_code_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                                vertical-align:top;
                                font-weight:600;
                            ">
                                {item_name_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                                vertical-align:top;
                            ">
                                {item_description_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                                text-align:center;
                                vertical-align:top;
                            ">
                                {interval_html} days
                            </td>

                        </tr>

                    </tbody>

                </table>

            </div>


            <!-- SCHEDULE DETAILS -->

            <div style="
                padding:0 30px 25px 30px;
            ">

                <div style="
                    font-size:16px;
                    font-weight:600;
                    color:#111827;
                    margin-bottom:12px;
                ">
                    Schedule Details
                </div>

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        border:1px solid #d1d5db;
                        font-size:13px;
                    "
                >

                    <thead>

                        <tr style="
                            background:#f3f4f6;
                        ">

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                From Date
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                To Date
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                Schedule Date
                            </th>

                            <th style="
                                border:1px solid #d1d5db;
                                padding:11px 10px;
                                text-align:left;
                            ">
                                Description
                            </th>

                        </tr>

                    </thead>

                    <tbody>

                        <tr>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                            ">
                                {from_date_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                            ">
                                {to_date_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                                font-weight:600;
                            ">
                                {schedule_date_html}
                            </td>

                            <td style="
                                border:1px solid #d1d5db;
                                padding:12px 10px;
                            ">
                                {schedule_description_html}
                            </td>

                        </tr>

                    </tbody>

                </table>

            </div>


            <!-- NOTICE -->

            <div style="
                margin:0 30px 25px 30px;
                padding:16px 18px;
                background:#f9fafb;
                border:1px solid #e5e7eb;
                border-radius:6px;
                font-size:13px;
                color:#4b5563;
                line-height:1.6;
            ">

                This is an automated maintenance schedule reminder.
                Please review the above maintenance item and arrange
                the required service accordingly.

            </div>


            <!-- FOOTER -->

            <div style="
                padding:18px 30px;
                background:#f9fafb;
                border-top:1px solid #e5e7eb;
                font-size:11px;
                color:#9ca3af;
                text-align:center;
            ">

                This email was generated automatically by ERPNext.

            </div>

        </div>

    </div>
    """

    # --------------------------------------------------------
    # CREATE COMMUNICATION + SEND
    # --------------------------------------------------------

    from frappe.core.doctype.communication.email import make

    make(
        doctype="Maintenance Contract",
        name=contract.name,
        subject=subject,
        content=message,
        recipients=recipients,
        cc=cc,
        communication_type="Communication",
        send_email=1,
    )
    return recipients


# ============================================================
# MAIN EMAIL FUNCTION
# ============================================================

def send_maintenance_contract_schedule_email():

    today_date = getdate(today())
    today_string = today_date.strftime(
        "%Y-%m-%d"
    )

    contracts_checked = 0
    items_checked = 0
    schedule_rows_checked = 0

    seven_day_emails = 0
    two_day_emails = 0

    skipped_no_schedule = 0

    errors = []
    debug_matches = []

    # --------------------------------------------------------
    # Get Contracts
    # --------------------------------------------------------

    contracts = frappe.get_all(
        "Maintenance Contract",
        fields=[
            "name",
            "company",
            "customer",
            "customer",
        ],
        order_by="modified asc",
    )

    contracts_checked = len(
        contracts
    )

    # --------------------------------------------------------
    # Process Contracts
    # --------------------------------------------------------

    for contract_data in contracts:

        try:

            contract = frappe.get_doc(
                "Maintenance Contract",
                contract_data.name
            )

            # ------------------------------------------------
            # Child Items
            # ------------------------------------------------

            for item in contract.items:

                items_checked += 1

                # --------------------------------------------
                # No schedule
                # --------------------------------------------

                if not item.schedule_data:

                    skipped_no_schedule += 1
                    continue

                # --------------------------------------------
                # Parse JSON
                # --------------------------------------------

                try:

                    schedule = json.loads(
                        item.schedule_data
                    )

                except Exception as e:

                    errors.append(
                        {
                            "contract": contract.name,
                            "item": item.name,
                            "error": (
                                "Invalid schedule_data: "
                                + str(e)
                            ),
                        }
                    )

                    continue

                if not isinstance(
                    schedule,
                    list
                ):

                    skipped_no_schedule += 1
                    continue

                # --------------------------------------------
                # Schedule rows
                # --------------------------------------------

                for schedule_row in schedule:

                    if not isinstance(
                        schedule_row,
                        dict
                    ):
                        continue

                    schedule_date = (
                        schedule_row.get(
                            "date"
                        )
                    )

                    if not schedule_date:
                        continue

                    schedule_rows_checked += 1

                    # ----------------------------------------
                    # Date
                    # ----------------------------------------

                    try:

                        schedule_date_obj = getdate(
                            schedule_date
                        )

                    except Exception as e:

                        errors.append(
                            {
                                "contract": contract.name,
                                "item": item.name,
                                "schedule_date": str(
                                    schedule_date
                                ),
                                "error": (
                                    "Invalid schedule date: "
                                    + str(e)
                                ),
                            }
                        )

                        continue

                    schedule_string = (
                        schedule_date_obj.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    # ----------------------------------------
                    # Trigger dates
                    # ----------------------------------------

                    seven_day_date = add_days(
                        schedule_date_obj,
                        -7
                    )

                    two_day_date = add_days(
                        schedule_date_obj,
                        -2
                    )

                    seven_day_string = (
                        seven_day_date.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    two_day_string = (
                        two_day_date.strftime(
                            "%Y-%m-%d"
                        )
                    )

                    # ----------------------------------------
                    # Debug
                    # ----------------------------------------

                    if (
                        today_string
                        == seven_day_string
                        or
                        today_string
                        == two_day_string
                    ):

                        debug_matches.append(
                            {
                                "contract": contract.name,
                                "item": item.name,
                                "schedule_date": schedule_string,
                                "today": today_string,
                                "seven_day_trigger_date": (
                                    seven_day_string
                                ),
                                "two_day_trigger_date": (
                                    two_day_string
                                ),
                                "email_7_days_sent": bool(
                                    schedule_row.get(
                                        "email_7_days_sent",
                                        False
                                    )
                                ),
                                "email_2_days_sent": bool(
                                    schedule_row.get(
                                        "email_2_days_sent",
                                        False
                                    )
                                ),
                            }
                        )

                    # ========================================
                    # 7 DAYS BEFORE
                    # ========================================

                    if (
                        today_string
                        == seven_day_string
                        and not bool(
                            schedule_row.get(
                                "email_7_days_sent",
                                False
                            )
                        )
                    ):

                        try:

                            send_schedule_email(
                                contract=contract,
                                item=item,
                                schedule_row=schedule_row,
                                reminder_type="7 Days Before",
                            )

                            # Only mark as sent
                            # after successful send

                            schedule_row[
                                "email_7_days_sent"
                            ] = True

                            seven_day_emails += 1

                        except Exception as e:

                            errors.append(
                                {
                                    "contract": contract.name,
                                    "item": item.name,
                                    "schedule_date": schedule_string,
                                    "reminder": "7 Days Before",
                                    "error": str(e),
                                }
                            )

                    # ========================================
                    # 2 DAYS BEFORE
                    # ========================================

                    if (
                        today_string
                        == two_day_string
                        and not bool(
                            schedule_row.get(
                                "email_2_days_sent",
                                False
                            )
                        )
                    ):

                        try:

                            send_schedule_email(
                                contract=contract,
                                item=item,
                                schedule_row=schedule_row,
                                reminder_type="2 Days Before",
                            )

                            # Only mark as sent
                            # after successful send

                            schedule_row[
                                "email_2_days_sent"
                            ] = True

                            two_day_emails += 1

                        except Exception as e:

                            errors.append(
                                {
                                    "contract": contract.name,
                                    "item": item.name,
                                    "schedule_date": schedule_string,
                                    "reminder": "2 Days Before",
                                    "error": str(e),
                                }
                            )

                # --------------------------------------------
                # Save updated schedule
                # --------------------------------------------

                try:

                    frappe.db.set_value(
                        "Maintenance Contract Item",
                        item.name,
                        "schedule_data",
                        frappe.as_json(
                            schedule
                        ),
                        update_modified=False,
                    )

                except Exception as e:

                    errors.append(
                        {
                            "contract": contract.name,
                            "item": item.name,
                            "error": (
                                "Failed to save schedule_data: "
                                + str(e)
                            ),
                        }
                    )

        except Exception as e:

            errors.append(
                {
                    "contract": contract_data.name,
                    "error": str(e),
                }
            )

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    frappe.db.commit()

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {
        "today": today_string,
        "contracts_checked": contracts_checked,
        "items_checked": items_checked,
        "schedule_rows_checked": schedule_rows_checked,
        "seven_day_emails": seven_day_emails,
        "two_day_emails": two_day_emails,
        "skipped_no_schedule": skipped_no_schedule,
        "errors": errors,
        "debug_matches": debug_matches,
    }