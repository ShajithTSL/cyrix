import frappe
from frappe.model.mapper import get_mapped_doc
import json
from erpnext.setup.utils import get_exchange_rate
naming_series = {
    "Internal Quotation - Repair": {
        "Kuwait": {"series": "IQR-K.YY.-", "status": "IQ-Internally Quoted"},
        "Dammam": {"series": "IQR-D.YY.-", "status": "IQ-Internally Quoted"},
        "Riyadh": {"series": "IQR-R.YY.-", "status": "IQ-Internally Quoted"},
        "Jeddah": {"series": "IQR-J.YY.-", "status": "IQ-Internally Quoted"},
        "Dubai": {"series": "IQR-DU.YY.-", "status": "IQ-Internally Quoted"}
    },
    "Internal Quotation - Supply": {
        "Kuwait": {"series": "IQS-K.YY.-", "status": "IQ-Internally Quoted"},
        "Dammam": {"series": "IQS-D.YY.-", "status": "IQ-Internally Quoted"},
        "Riyadh": {"series": "IQS-R.YY.-", "status": "IQ-Internally Quoted"},
        "Jeddah": {"series": "IQS-J.YY.-", "status": "IQ-Internally Quoted"},
        "Dubai": {"series": "IQS-DU.YY.-", "status": "IQ-Internally Quoted"}
    },
    "Customer Quotation - Repair": {
        "Kuwait": {"series": "CQR-K.YY.-", "status": "A-Approved"},
        "Dammam": {"series": "CQR-D.YY.-", "status": "A-Approved"},
        "Riyadh": {"series": "CQR-R.YY.-", "status": "A-Approved"},
        "Jeddah": {"series": "CQR-J.YY.-", "status": "A-Approved"},
        "Dubai": {"series": "CQR-DU.YY.-", "status": "A-Approved"}
    },
    "Customer Quotation - Supply": {
        "Kuwait": {"series": "CQS-K.YY.-", "status": "A-Approved"},
        "Dammam": {"series": "CQS-D.YY.-", "status": "A-Approved"},
        "Riyadh": {"series": "CQS-R.YY.-", "status": "A-Approved"},
        "Jeddah": {"series": "CQS-J.YY.-", "status": "A-Approved"},
        "Dubai": {"series": "CQS-DU.YY.-", "status": "A-Approved"}
    },
    "Customer Quotation - R - Revised": {
        "Kuwait": {"series": "CQR-K.YY.-", "status": "A-Approved"},
        "Dammam": {"series": "CQR-D.YY.-", "status": "A-Approved"},
        "Riyadh": {"series": "CQR-R.YY.-", "status": "A-Approved"},
        "Jeddah": {"series": "CQR-J.YY.-", "status": "A-Approved"},
        "Dubai": {"series": "CQR-DU.YY.-", "status": "A-Approved"}
    },
}

quotation_type = ["Customer Quotation - Repair","Customer Quotation - R - Revised",
                "Customer Quotation - Supply","Customer Quotation - S - Revised",
                "Customer Quotation - Site Visit","Customer Quotation - SV - Revised"]


def on_update_after_submit(doc,method):
    if not doc.type_of_approval and doc.quotation_type in quotation_type and doc.docstatus == 1:
        frappe.throw("Cannot submit: 'Type of Approval' field is required.")

    if doc.quotation_type in quotation_type:
        for i in doc.items:
            if i.job_order_data:
                frappe.db.set_value("Job Order Data",i.job_order_data,"quotation_approved_date",doc.approval_date)
            if i.supply_order_data:
                frappe.db.set_value("Supply Order Data",i.supply_order_data,"quotation_approved_date",doc.approval_date)
    update_quotation_reference(doc,method)


def update_job_order_status(self, method):        
    def update_status(self,item, status):
        if item.job_order_data:
            update = frappe.get_doc("Job Order Data", item.job_order_data)
            update.status = status
            update.po_no = self.get("purchase_order_no")
            update.save(ignore_permissions=True)

    if method == "on_submit":        
        # if not self.type_of_approval and self.quotation_type in quotation_type and self.docstatus == 1:
        #     frappe.throw("Cannot submit: 'Type of Approval' field is required.")
        for item in self.get("items"):
            if self.quotation_type:
                status = naming_series.get(self.quotation_type, {}).get(self.branch, {}).get("status")
                if status:
                    update_status(self,item, status)
        update_quotation_reference(self,method)

    if method == "validate":
        for item in self.get("items"):
            if self.quotation_type in ["Customer Quotation - Repair","Customer Quotation - R - Revised"]:
                if self.workflow_state == "Draft":
                    update_status(self,item, "Q-Quoted")
                if self.workflow_state == "Rejected":
                    update_status(self,item, "RNA-Return Not Approved")
                
            if self.quotation_type in ["Internal Quotation - Repair","Internal Quotation - Supply"]:
                if self.workflow_state == "Draft":
                    update_status(self,item, "Pending Internal Approval")

def update_supply_order_status(self, method):
    for i in self.get("items"):
        if i.supply_order_data:            
            doc = frappe.get_doc("Supply Order Data",i.supply_order_data)
            if self.quotation_type in ["Customer Quotation - Supply","Customer Quotation - S - Revised"]:
                if frappe.db.get_value(self.doctype, self.name, "workflow_state") == "Approved by Customer":
                    doc.status = "Quoted"
                    doc.save(ignore_permissions=True)
                if frappe.db.get_value(self.doctype, self.name, "workflow_state") == "Rejected":
                    doc.status =  "Not Approved"
                    doc.save(ignore_permissions=True)

            if self.quotation_type == "Internal Quotation - Supply":
                if frappe.db.get_value(self.doctype, self.name, "workflow_state") == "Approved by Management":
                    doc.status = "Internal Quotation"	
                doc.save(ignore_permissions=True)

def update_budgetary_quotation_status(self, method):
    for i in self.get("items"):
        if i.budgetary_quotation and self.quotation_type in ["Internal Quotation - BQ","Customer Quotation - BQ","Customer Quotation - BQ - Revised"]:
            doc = frappe.get_doc("Budgetary Quotation",i.budgetary_quotation)
            if frappe.db.get_value(self.doctype, self.name, "workflow_state") == "Approved by Management":
                doc.status = "IQ-Internally Quoted"
            if frappe.db.get_value(self.doctype, self.name, "workflow_state") == "Approved by Customer":
                doc.status = "A-Approved"
            doc.save(ignore_permissions=True)



def update_quotation_reference(self,method):
    if self.items:
        for i in self.items:
            if self.quotation_type in ["Customer Quotation - Repair","Customer Quotation - R - Revised"]:
                if i.job_order_data:
                    jo = frappe.get_doc("Job Order Data",i.job_order_data)
                    jo.quotation = self.name
                    if self.get("purchase_order_no"):
                        jo.po_no = self.get("purchase_order_no")
                    jo.save(ignore_permissions =1)

            if self.quotation_type in ["Customer Quotation - Supply","Customer Quotation - S - Revised"]:
                if i.supply_order_data:
                    so = frappe.get_doc("Supply Order Data",i.supply_order_data)
                    so.quotation = self.name
                    if self.get("purchase_order_no"):
                        so.po_no = self.get("purchase_order_no")
                    so.save(ignore_permissions =1)


@frappe.whitelist()
def get_quote(source,type = None):
    target_doc = frappe.new_doc("Quotation")
    doc = frappe.get_doc("Quotation",source)
    
    def postprocess(source, target_doc):
        target_doc.naming_series = naming_series.get("Customer Quotation - Repair", {}).get(target_doc.branch, {}).get("series")
        target_doc.quotation_type = type
        target_doc.internal_quotation = source.name
        
    doclist = get_mapped_doc("Quotation",source , {
        "Quotation": {
            "doctype": "Quotation",
        },
        "Quotation Item": {
            "doctype": "Quotation Item",            
        },
    }, target_doc, postprocess)
    return doclist

def fetch_previous_quotation_details(self, method):
    # Define mapping of internal quotation types to corresponding customer quotation types
    quotation_type_map = {
        "Internal Quotation - Repair": ["Customer Quotation - Repair", "Customer Quotation - R - Revised"],
        "Internal Quotation - Supply": ["Customer Quotation - Supply", "Customer Quotation - S - Revised"],
        "Internal Quotation - BQ": ["Customer Quotation - BQ","Customer Quotation - BQ - Revised"]
    }

    self.previously_quoted_item = []
    for i in self.get("items"):
        if i.item_code and self.quotation_type in quotation_type_map:
            # Get the customer quotation types for the current internal quotation type
            customer_quotation_types = quotation_type_map[self.quotation_type]

            # Create a dynamic number of %s placeholders for the IN clause
            placeholders = ', '.join(['%s'] * len(customer_quotation_types))

            # Execute the SQL query with the appropriate quotation types
            prev_quote = frappe.db.sql(f'''select 
                    qi.parent as quotation_no,
                    qi.job_order_data as job_order_data,
                    qi.rate as price,
                    qi.item_code as sku
                from `tabQuotation` as q 
                inner join `tabQuotation Item` as qi
                on qi.parent=q.name 
                where qi.item_code = %s 
                    and q.docstatus = 1 
                    and q.name != %s 
                    and q.company = %s
                    and q.quotation_type in ({placeholders})
            ''', (i.item_code, self.name, self.company, *customer_quotation_types), as_dict=1)

            if prev_quote:
                for j in prev_quote:
                    if j.job_order_data:
                        self.append("previously_quoted_item", {
                            "item_code": j.sku,
                            "quotation": j.quotation_no,
                            "job_order_data": j.job_order_data or "",
                            "price": j.price
                        })


def fetch_eval_list(eval_list,job_order_data):
    child_jo_list = frappe.get_all('Job Order Data', filters={'parent_jo': job_order_data,'docstatus':1})
    eval_list = [job_order_data] + [child['name'] for child in child_jo_list]
    return eval_list

def fetch_item_price_details(self, method=None):
    fetch_previous_quotation_details(self, method)
    fetch_price_from_eval_report(self, method)
    fetch_supplier_details(self, method)

def fetch_price_from_eval_report(self, method):
    if self.quotation_type != "Internal Quotation - Repair":
        return
    
    eval_list = []

    # Clear existing tables and totals
    self.item_price_details = []
    self.parts_price = []
    self.total_actual_cost = 0.0

    # Initialize totals with descriptive names
    tsl_inventory_total = 0.0
    supplier_total = 0.0
    scrap_total = 0.0

    for item in self.get("items"):
        child_eval_list = fetch_eval_list(eval_list, item.job_order_data)
        eval_list.extend(child_eval_list)

    for eval in  eval_list:
        eval_report_name = frappe.db.exists("Evaluation Report", {"job_order_data": eval})
        if not eval_report_name:
            continue

        eval_doc = frappe.get_doc("Evaluation Report", eval_report_name)
        if not eval_doc:
            continue

        for eval_item in eval_doc.get("items"):
            # Get full model name
            eval_item.model = frappe.get_value("Item Model", {"name": eval_item.model}, "model")

            item_source = "TSL Inventory" if eval_item.parts_availability == "Yes" else "Supplier"
            price = eval_item.price_ea
            amount = eval_item.total
            supplier_quotation = ""
            supplier = ""

            if eval_item.parts_availability == "No":
                # Get latest Supplier Quotation for item
                sq_data = frappe.db.sql("""
                    SELECT sq.supplier, sq.name AS sq, SUM(sq.shipping_cost) AS spc, sq.currency
                    FROM `tabSupplier Quotation` sq
                    INNER JOIN `tabSupplier Quotation Item` sqi ON sq.name = sqi.parent
                    WHERE sq.docstatus = 1 AND sqi.job_order_data = %s AND sqi.item_code = %s
                    ORDER BY sq.modified DESC LIMIT 1
                """, (eval_doc.job_order_data, eval_item.part), as_dict=True)

                if sq_data:
                    sq = sq_data[0]
                    supplier_quotation = sq.sq or ""
                    supplier = sq.supplier or ""

                    try:
                        exchange_rate = get_exchange_rate(sq.currency, self.currency)
                        if sq.spc:
                            self.total_actual_cost += sq.spc * exchange_rate
                    except Exception as e:
                        frappe.log_error(f"Exchange rate fetch failed: {e}", "Quotation Fetch Error")

            # Add to item_price_details
            self.append("item_price_details", {
                "item": eval_item.part,
                "item_source": item_source,
                "model": eval_item.model,
                "price": price,
                "amount": amount,
                "supplier_quotation": supplier_quotation,
                "supplier": supplier
            })

            # Accumulate totals
            if item_source == "TSL Inventory":
                tsl_inventory_total += amount
            elif item_source == "Supplier":
                supplier_total += amount
            elif item_source == "Scrap":
                scrap_total += amount

    # Append to parts_price table
    if self.item_price_details:
        total_material_cost = tsl_inventory_total + supplier_total + scrap_total
        self.append("parts_price", {
            "tsl_inventory": float(round(tsl_inventory_total, 2)),
            "supplier": float(round(supplier_total, 2)),
            "scrap": float(round(scrap_total, 2)),
            "total_material_cost": float(round(total_material_cost, 2))
        })


def fetch_supplier_details(self, method):
    self.parts_price = []
    self.supplier_details = []
    
    total_cost = 0
    for j in self.items:
        if j.supply_order_data:
            sup = frappe.db.sql(""" 
                select `tabSupplier Quotation`.supplier,
                    `tabSupplier Quotation`.name,
                    `tabSupplier Quotation Item`.base_amount,
                    `tabSupplier Quotation Item`.supply_order_data AS reference,
                    `tabSupplier Quotation`.shipping_cost 
                from `tabSupplier Quotation` 
                join `tabSupplier Quotation Item` 
                on `tabSupplier Quotation Item`.parent = `tabSupplier Quotation`.name 
                where `tabSupplier Quotation Item`.supply_order_data = %s 
                and `tabSupplier Quotation Item`.item_code = %s 
                and `tabSupplier Quotation`.docstatus = 1
            """, (j.supply_order_data, j.item_code), as_dict=1)

            if sup:  # Check if the query returned any data
                cur = frappe.get_value("Supplier", {"name": sup[0]["supplier"]}, ["default_currency"])
                exr = get_exchange_rate(cur, self.currency)
                cost = sup[0]["shipping_cost"] * exr
                total_cost += sup[0]["base_amount"]
                row = {
                    'reference_type': "Supply Order Data",
                    'supply_order_data': sup[0]["reference"],
                    'supplier_quotation': sup[0]["name"],
                    'supplier': sup[0]["supplier"],
                    'price': sup[0]["base_amount"],
                    'shipment': cost,
                    'item_code': j.item_code,
                }
                self.append("supplier_details", row)

        if j.budgetary_quotation:
            sup_budgetary = frappe.db.sql(""" 
                select `tabSupplier Quotation`.supplier,
                    `tabSupplier Quotation`.name,
                    `tabSupplier Quotation Item`.base_amount,
                    `tabSupplier Quotation Item`.budgetary_quotation AS reference,
                    `tabSupplier Quotation`.shipping_cost 
                from `tabSupplier Quotation` 
                join `tabSupplier Quotation Item` 
                on `tabSupplier Quotation Item`.parent = `tabSupplier Quotation`.name 
                where `tabSupplier Quotation Item`.budgetary_quotation = %s 
                and `tabSupplier Quotation Item`.item_code = %s 
                and `tabSupplier Quotation`.docstatus = 1
            """, (j.budgetary_quotation, j.item_code), as_dict=1)

            if sup_budgetary:
                cur = frappe.get_value("Supplier", {"name": sup_budgetary[0]["supplier"]}, ["default_currency"])
                exr = get_exchange_rate(cur, self.currency)
                cost = sup_budgetary[0]["shipping_cost"] * exr
                total_cost += sup_budgetary[0]["base_amount"]
                row = {
                    'reference_type': "Budgetary Quotation",
                    'supply_order_data': sup_budgetary[0]["reference"],
                    'supplier_quotation': sup_budgetary[0]["name"],
                    'supplier': sup_budgetary[0]["supplier"],
                    'price': sup_budgetary[0]["base_amount"],
                    'shipment': cost,
                    'item_code': j.item_code,
                }
                self.append("supplier_details", row)

    if self.supplier_details:
        self.append("parts_price", {
            "supplier": float(round(total_cost, 2)),
            "total_material_cost": float(round(total_cost, 2))
        })


@frappe.whitelist()
def get_job_order_data(job_order_data):
    job_order_data = json.loads(job_order_data)
    item_list=[]
    for k in list(job_order_data):
        er = 0
        er = frappe.db.sql('''select 
            sum(psi.total) as total_amount
            from `tabPart Sheet Item` psi
            join `tabEvaluation Report` er on psi.parent = er.name
            where er.job_order_data = %s
            group by er.job_order_data''',k,as_dict=1)
        doc = frappe.get_doc("Job Order Data",k)
        branch = doc.branch
        if len(er) and 'total_amount' in er[0]:
            er = er[0]['total_amount']
        else:
            er = 0
        for i in doc.get("material_list"):
            item_list.append(frappe._dict({
                "item_code" :i.item_code,
                "item_name" : i.item_name,
                "description":i.item_name,
                "job_order_data": k,
                "model_no": i.model_no,
                "uom": frappe.db.get_value("Item",{'name':i.item_code},'stock_uom'),
                "mfg": i.mfg,
                "qty": i.quantity,
                "rate":float(er)/float(i.quantity),
            }))
    return item_list,branch




@frappe.whitelist()
def get_supply_order_data(supply_order_data):
    supply_order_data = json.loads(supply_order_data)
    item_list=[]
    for k in list(supply_order_data):
        doc = frappe.get_doc("Supply Order Data",k)
        branch = doc.branch
        customer = doc.customer
        for i in doc.get("material_list"):
            item_list.append(frappe._dict({
                "item_code" :i.item_code,
                "item_name" : i.item_name,
                "description":i.item_name,
                "supply_order_data": k,
                "model_no": i.model_no,
                "uom": frappe.db.get_value("Item",{'name':i.item_code},'stock_uom'),
                "mfg": i.mfg,
                "qty": i.quantity,
                # "rate":float(er)/float(i.quantity),
            }))
    return item_list,branch,customer



@frappe.whitelist()
def create_sales_invoice(source):
    sales_invoice = frappe.new_doc("Sales Invoice")
    doc = frappe.get_doc("Quotation",source)
    # sales_invoice.custom_sales_person = doc.custom_sales_person
    # sales_invoice.sales_rep = doc.sales_rep
    doclist = get_mapped_doc("Quotation",source , {
        "Quotation": {
            "doctype": "Sales Invoice",
            "field_map": {
                "name": "quotation",
                "party_name":"customer",
                "branch":"branch",
            },
        },
        "Quotation Item": {
            "doctype": "Sales Invoice Item",			
        },

    }, sales_invoice)

    return doclist

def update_service_call_form(doc,method):
    if doc.service_call_form:
        if doc. quotation_type == "Internal Quotation - Site Visit":
            frappe.db.set_value("Service Call Form",doc.service_call_form,"status","Internally Quoted")
        if doc. quotation_type in ["Customer Quotation - Site Visit","Customer Quotation - SV - Revised"]:
            frappe.db.set_value("Service Call Form",doc.service_call_form,"status","Approved")



# def update_workflow():
#     transitions = frappe.db.get_all("Workflow Transition",['name','condition'])
#     for wo in transitions:
#         print(wo)
        
#     frappe.db.set_value("Workflow Transition",'4tr31a70gk', 'condition', 'doc.quotation_type in ["Internal Quotation - Repair","Internal Quotation - Supply","Internal Quotation - Site Visit","Internal Quotation - BQ"]')
#     frappe.db.set_value("Workflow Transition",'603tkifk9m', 'condition', 'doc.quotation_type not in ["Internal Quotation - Repair","Internal Quotation - Supply","Internal Quotation - Site Visit","Internal Quotation - BQ"]')
#     frappe.db.set_value("Workflow Transition",'80cu734dfl', 'condition', 'doc.quotation_type not in ["Internal Quotation - Repair","Internal Quotation - Supply","Internal Quotation - Site Visit","Internal Quotation - BQ"]')