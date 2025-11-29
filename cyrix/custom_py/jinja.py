import frappe

@frappe.whitelist()
def get_technicians(doc_name):
    technician_names = set()
    try:
        doc = frappe.get_doc("Quotation", doc_name)

        for item in doc.items:
            if item.job_order_data:
                job_order = frappe.get_doc("Job Order Data", item.job_order_data)
                for tech_row in job_order.technician:
                    if tech_row.technician:
                        # Get the actual technician name from linked Technician ID
                        tech_name = frappe.db.get_value("Technician ID", tech_row.technician, "technician")
                        if tech_name:
                            technician_names.add(tech_name)

        return ", ".join(sorted(technician_names)) if technician_names else "-"
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Technicians Error")
        return "-"
