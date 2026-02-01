import frappe
from cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report import EvaluationReport as eval_report

def update_job_order_status(self, method):
    for item in self.get("items"):
        if item.job_order_data:
            ev = frappe.get_value("Evaluation Report",{"job_order_data":item.job_order_data},["name"])
            if ev:
                doc = frappe.get_doc("Evaluation Report",ev)
                eval_report.update_availability_status(doc)
                eval_report.update_jo_status_after_purchase_receipt(doc)
    
def update_supply_order_status(self, method):
    update_stock_received_percentage(self,method)

def update_stock_received_percentage(doc, method):
    for item in doc.items:
        if item.supply_order_data:
            supply_order_data = frappe.get_doc("Supply Order Data", item.supply_order_data)
            supply_order_data.received_quantity += item.received_qty
            # if supply_order_data.received_quantity == supply_order_data.quantity:
            #     supply_order_data.status = "Received"  # Fully received
            # elif supply_order_data.received_quantity > 0:
            #     supply_order_data.status = "Partially Received"  # Partially received
            supply_order_data.save()

        if item.budgetary_quotation:
            bq = frappe.get_doc("Budgetary Quotation", item.budgetary_quotation)
            bq.received_quantity += item.received_qty
            if bq.received_quantity == bq.quantity:
                bq.status = "Received"  # Fully received
            elif bq.received_quantity > 0:
                bq.status = "Partially Received"  # Partially received
            bq.save()

def update_received_percentage(doc, method):
    for item in doc.items:
        if item.supply_order_data:
            supply_order_data = frappe.get_doc("Supply Order Data", item.supply_order_data)
            supply_order_data.received_quantity -= item.received_qty
            # if supply_order_data.received_quantity == supply_order_data.quantity:
            #     supply_order_data.status = "Received"  # Fully received
            # elif supply_order_data.received_quantity > 0:
            #     supply_order_data.status = "Partially Received"  # Partially received
            supply_order_data.save()

        if item.budgetary_quotation:
            bq = frappe.get_doc("Budgetary Quotation", item.budgetary_quotation)
            bq.received_quantity -= item.received_qty
            if bq.received_quantity == bq.quantity:
                bq.status = "Received"  # Fully received
            elif bq.received_quantity > 0:
                bq.status = "Partially Received"  # Partially received
            bq.save()