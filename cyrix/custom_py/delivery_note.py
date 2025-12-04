import frappe
from frappe import _
from frappe.exceptions import ValidationError

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
        if not i.supply_order_data:
            continue
        supply_order_doc = frappe.get_doc("Supply Order Data", i.supply_order_data)
        supply_order_doc.delivered_quantity = (supply_order_doc.delivered_quantity or 0) + i.qty
        found = False
        for row in supply_order_doc.material_list:
            if row.item_code == i.item_code:
                row.delivered_quantity = (row.delivered_quantity or 0) + i.qty
                found = True
                break

        if not found:
            frappe.throw(f"Item {i.item_code} not found in Supply Order Table for {i.supply_order_data}")
        if supply_order_doc.payment_entry and supply_order_doc.invoice_no:
            status = "Paid"
        elif not supply_order_doc.payment_entry and not supply_order_doc.invoice_no:
            if supply_order_doc.quantity == supply_order_doc.delivered_quantity:
                status = "Delivered"
            else:
                status = "Partially Delivered"
        elif supply_order_doc.invoice_no:
            status = "Invoiced"
        else:
            status = "Pending"

        supply_order_doc.status = status
        supply_order_doc.save(ignore_permissions=True)
        frappe.db.set_value("Supply Order Data", i.supply_order_data, "dn_no", supply_order_doc.name)
        frappe.db.set_value("Supply Order Data", i.supply_order_data, "dn_date", supply_order_doc.posting_date)

def update_so_qty_on_cancel(self, method):
    for i in self.get("items"):
        if not i.supply_order_data:
            continue
        supply_order_doc = frappe.get_doc("Supply Order Data", i.supply_order_data)
        supply_order_doc.delivered_quantity = (supply_order_doc.delivered_quantity or 0) - i.qty
        if supply_order_doc.delivered_quantity < 0:
            supply_order_doc.delivered_quantity = 0

        found = False
        for row in supply_order_doc.material_list:
            if row.item_code == i.item_code:
                row.delivered_quantity = (row.delivered_quantity or 0) - i.qty
                if row.delivered_quantity < 0:
                    row.delivered_quantity = 0
                found = True
                break

        if not found:
            frappe.throw(
                f"Item {i.item_code} not found in Supply Order Table for {i.supply_order_data}"
            )

        if supply_order_doc.payment_entry and supply_order_doc.invoice_no:
            status = "Paid"

        elif not supply_order_doc.payment_entry and not supply_order_doc.invoice_no:
            if supply_order_doc.delivered_quantity == supply_order_doc.quantity:
                status = "Delivered"
            elif supply_order_doc.delivered_quantity > 0:
                status = "Partially Delivered"
            else:
                status = "Received"

        elif supply_order_doc.invoice_no:
            status = "Invoiced"

        else:
            status = "Pending"

        supply_order_doc.status = status
        supply_order_doc.save(ignore_permissions=True)
