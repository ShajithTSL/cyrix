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
            jo.invoiced_value = item.total_amount or item.net_amount
            jo.invoice_no=doc.name
            jo.invoice_date=doc.posting_date
            jo.save(ignore_permissions = True)

        elif item.get("supply_order_data"):
            so = frappe.get_doc("Supply Order Data",item.get("supply_order_data"))
            so.status = 'Invoiced'
            so.invoiced_value += item.total_amount or item.net_amount
            so.invoice_no=doc.name
            so.invoice_date=doc.posting_date
            so.save(ignore_permissions = True)

        elif item.get("budgetary_quotation"):
            bq = frappe.get_doc("Budgetary Quotation",item.get("budgetary_quotation"))
            bq.status = 'Invoiced'
            bq.invoiced_value = item.total_amount or item.net_amount
            bq.invoice_no=doc.name
            bq.invoice_date=doc.posting_date
            bq.save(ignore_permissions = True)

def update_service_call_form(doc,method):
    if doc.get("service_call_form"):
        frappe.db.set_value("Service Call Form",doc.get("service_call_form"),"sales_invoice",doc.name)
        frappe.db.set_value("Service Call Form",doc.get("service_call_form"),"status","Invoiced")



def update_jo_so_status_on_cancel(doc, method):
    for item in doc.get("items"):
        if item.get("job_order_data"):
            jo = frappe.get_doc("Job Order Data",item.get("job_order_data"))
            if jo.status != "RSI-Repaired and Shipped Invoiced":
                if doc.is_return:
                    jo.status = "C-Cancelled"  # for credit note need to set the status as cancelled
                else:
                    jo.status = "RSI-Repaired and Shipped Invoiced"
            jo.invoiced_value -= item.total_amount or item.net_amount
            jo.invoice_no = ''
            jo.invoice_date = ''
            jo.save(ignore_permissions = True)

        elif item.get("supply_order_data"):
            so = frappe.get_doc("Supply Order Data",item.get("supply_order_data"))
            so.status = 'Invoiced'
            so.invoiced_value -= item.total_amount or item.net_amount
            so.invoice_no = ''
            so.invoice_date = ''
            so.save(ignore_permissions = True)

        elif item.get("budgetary_quotation"):
            bq = frappe.get_doc("Budgetary Quotation",item.get("budgetary_quotation"))
            bq.status = 'Invoiced'
            bq.invoiced_value -= item.total_amount or item.net_amount
            bq.invoice_no = ''
            bq.invoice_date = ''
            bq.save(ignore_permissions = True)

def update_invoice_percentage(doc,method):
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

def update_invoice_percentage_on_cancel(doc,method):
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
    si_list = frappe.get_all("Sales Taxes and Charges",{'parenttype':"Sales Invoice",'account_head': "1020801 - VAT Receivable 15% - BM","docstatus":1},"parent")
    for s in si_list:
        doc = frappe.get_doc("Sales Invoice",s.parent)
        for s in doc.taxes:
            s.account_head = "2010504 - VAT Payable 15% - BM"
        print(s.parent)
        doc.flags.ignore_mandatory = True
        doc.save()