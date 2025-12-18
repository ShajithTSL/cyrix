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



import frappe

def is_english(text):
    if not text:
        return True
    try:
        text.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def styled_text_per_word(text):
    if not text:
        return ""

    words = text.split(" ")
    styled_words = []

    for word in words:
        if is_english(word):
            font_family = "Roboto"
            font_size = "9px"
        else:
            font_family = "'Scheherazade New'"
            font_size = "12px"  # adjust if needed

        styled_words.append(
            f'<span style="font-family:{font_family}; font-size:{font_size};">'
            f'{word}'
            f'</span>'
        )

    return " ".join(styled_words) + "<br>"


def show_address(address_name):
    if not address_name:
        return ""

    try:
        address = frappe.get_doc("Address", address_name)
    except frappe.DoesNotExistError:
        return ""

    html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Scheherazade+New&family=Roboto&display=swap" rel="stylesheet">

                {styled_text_per_word(address.address_line1)}
                {styled_text_per_word(address.address_line2)}
                {styled_text_per_word(address.city)}
                {styled_text_per_word(address.state)}
                {styled_text_per_word(address.pincode)}
                {styled_text_per_word(address.country)}
                <br>
                {styled_text_per_word("Phone: " + address.phone if address.phone else "")}
                {styled_text_per_word("Email: " + address.email_id if address.email_id else "")}

    """

    return html
