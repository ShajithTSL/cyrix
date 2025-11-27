import frappe
import json

@frappe.whitelist()
def fetch_last_purchase_rate(items,company):
    items = json.loads(items)
    results = []

    for item in items:
        item_code = item.get("item_code")
        if not item_code:
            continue

        last_invoice_item = frappe.db.sql("""
            SELECT 
                pii.rate, 
                pii.item_code,
                pii.item_name, 
                pi.posting_date, 
                pi.name as invoice_name,
                pi.currency,
                pi.supplier
            FROM `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
            WHERE pii.item_code = %s AND pi.docstatus = 1 AND pi.company = %s
            ORDER BY pi.posting_date DESC, pi.creation DESC
            LIMIT 1
        """,(item_code,company), as_dict=True)

        if last_invoice_item:
            results.append({
                "item_code": item_code,
                "item_name": last_invoice_item[0].item_name,
                "purchase_invoice":last_invoice_item[0].invoice_name,
                "rate": last_invoice_item[0].rate,
                "currency": last_invoice_item[0].currency,
                "supplier": last_invoice_item[0].supplier
            })

    return results
