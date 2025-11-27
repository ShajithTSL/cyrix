import frappe

def update_job_order_status(doc,method):
    if doc.get("job_order_data"):
        jo = frappe.get_doc("Job Order Data",doc.get("job_order_data"))
        if jo.status != "RSC-Repaired and Shipped Client":
            jo.status = "RSC-Repaired and Shipped Client"        
        jo.dn_no=doc.name
        jo.dn_date=doc.posting_date
        jo.warranty=doc.warranty
        jo.delivery=doc.posting_date
        jo.save(ignore_permissions = True)
        
def update_supply_order_status(doc, method):
    for i in doc.get("items"):
        if i.supply_order_data:
            supply_order_doc = frappe.get_doc("Supply Order Data", i.supply_order_data)
            dn_no = supply_order_doc.name
            dn_date = supply_order_doc.posting_date
            
            # Determine the status
            if supply_order_doc.payment_entry_reference and supply_order_doc.invoice_no:
                status = 'Paid'
            elif not supply_order_doc.payment_entry_reference and not supply_order_doc.invoice_no:
                status = 'Delivered'
            elif supply_order_doc.invoice_no:
                status = 'Invoiced'

            # Update status and fields
            supply_order_doc.status = status
            supply_order_doc.save(ignore_permissions=True)
            frappe.db.set_value("Supply Order Data", i.supply_order_data, "dn_no", dn_no)
            frappe.db.set_value("Supply Order Data", i.supply_order_data, "dn_date", dn_date)
