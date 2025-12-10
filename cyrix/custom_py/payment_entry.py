import json
import frappe

@frappe.whitelist()
def get_jo_so_details(references):

    references = json.loads(references)
    jo_so_info = []

    for i in references:
        if i.get("reference_name"):
            jo_details = frappe.db.sql("""
                SELECT DISTINCT 
                    `tabSales Invoice Item`.job_order_data AS job_order_data,
                    `tabSales Invoice Item`.supply_order_data AS supply_order_data,
                    `tabSales Invoice Item`.budgetary_quotation AS budgetary_quotation
                FROM `tabSales Invoice`
                LEFT JOIN `tabSales Invoice Item` 
                    ON `tabSales Invoice`.name = `tabSales Invoice Item`.parent 
                WHERE `tabSales Invoice`.name = %s
            """, (i["reference_name"],), as_dict=1)
            for jo_entry in jo_details:
                job_order_name = jo_entry.get("job_order_data")
                if job_order_name:
                    job_order_doc = frappe.db.get_value(
                        "Job Order Data", job_order_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if job_order_doc:
                        remaining = (job_order_doc.invoiced_value or 0) - (job_order_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Job Order Data",
                            "reference_name": job_order_name,
                            "invoiced_value": job_order_doc.invoiced_value or 0,
                            "advance_payment_amount": job_order_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })

                supply_order_name = jo_entry.get("supply_order_data")
                if supply_order_name:
                    supply_order_doc = frappe.db.get_value(
                        "Supply Order Data", supply_order_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if supply_order_doc:
                        remaining = (supply_order_doc.invoiced_value or 0) - (supply_order_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Supply Order Data",
                            "reference_name": supply_order_name,
                            "invoiced_value": supply_order_doc.invoiced_value or 0,
                            "advance_payment_amount": supply_order_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })

                bq_name = jo_entry.get("budgetary_quotation")
                if bq_name:
                    bq_doc = frappe.db.get_value(
                        "Budgetary Quotation", bq_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if bq_doc:
                        remaining = (bq_doc.invoiced_value or 0) - (bq_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Budgetary Quotation",
                            "reference_name": bq_name,
                            "invoiced_value": bq_doc.invoiced_value or 0,
                            "advance_payment_amount": bq_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })
    return jo_so_info

def update_payment_reference(self, method):
    if self.payment_type == 'Receive':
        for row in self.job_order_table:
            if row.reference_name and row.allocate_amount > 0:
                # Fetch the Job Order Data document
                doc = frappe.get_doc(row.reference_type, row.reference_name)

                # Calculate the updated advance payment amount
                updated_amount = (doc.advance_payment_amount or 0) + row.allocate_amount

                # Determine status based on updated payment
                if doc.invoiced_value == updated_amount:
                    doc.status = "P-Paid" if row.reference_type == "Job Order Data" else "Paid"
                elif updated_amount == 0:
                    doc.status = "Unpaid"
                else:
                    doc.status = "Partially Paid"

                # Update fields
                doc.payment_entry = self.name
                doc.advance_payment_amount = updated_amount
                doc.advance_paid_date = self.posting_date

                # Save the updated document
                doc.save(ignore_permissions=True)


def update_payment_reference_cancel(self, method):
    if self.payment_type == 'Receive':
        for row in self.job_order_table:
            if row.reference_name and row.allocate_amount > 0:
                # Fetch the Job Order Data document
                doc = frappe.get_doc(row.reference_type, row.reference_name)

                # Calculate the updated advance payment amount
                updated_amount = (doc.advance_payment_amount or 0) - row.allocate_amount

                # Determine status based on updated payment
                if doc.invoiced_value == updated_amount:
                    doc.status = "P-Paid" if row.reference_type == "Job Order Data" else "Paid"
                elif updated_amount == 0:
                    doc.status = "Unpaid"
                else:
                    doc.status = "Partially Paid"

                # Update fields
                doc.payment_entry = ''
                doc.advance_payment_amount = updated_amount
                doc.advance_paid_date = ''

                # Save the updated document
                doc.save(ignore_permissions=True)