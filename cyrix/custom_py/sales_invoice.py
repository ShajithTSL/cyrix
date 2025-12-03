import frappe

def update_jo_so_status(doc, method):
    for item in doc.get("items"):
        if item.get("job_order_data"):
            jo = frappe.get_doc("Job Order Data",item.get("job_order_data"))
            if jo.status != "RSI-Repaired and Shipped Invoiced":
                if doc.is_return:
                    jo.status = "C-Cancelled"  # for credit note need to set the status as cancelled
                else:
                    jo.status = "RSI-Repaired and Shipped Invoiced"
            jo.invoiced_value = item.net_amount
            jo.invoice_no=doc.name
            jo.invoice_date=doc.posting_date
            jo.save(ignore_permissions = True)

        elif item.get("supply_order_data"):
            doc = frappe.get_doc("Supply Order Data",item.get("supply_order_data"))
            doc.status = 'Invoiced'
            doc.invoiced_value = item.net_amount
            doc.invoice_no=doc.name
            doc.invoice_date=doc.posting_date
            doc.save(ignore_permissions = True)

        elif item.get("budgetary_quotation"):
            doc = frappe.get_doc("Budgetary Quotation",item.get("budgetary_quotation"))
            doc.status = 'Invoiced'
            doc.save(ignore_permissions = True)

def update_service_call_form(doc,method):
    if doc.get("service_call_form"):
        frappe.db.set_value("Service Call Form",doc.get("service_call_form"),"sales_invoice",doc.name)
        frappe.db.set_value("Service Call Form",doc.get("service_call_form"),"status","Invoiced")