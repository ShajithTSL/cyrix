import frappe

# need to set the series of the item code based on the item group
def set_item_code_series(self, method):
    if not self.item_group:
        frappe.throw("Item Group is required to set the item code series.")

    item_group_series_map = {
        "Equipments": ".######",
        "Components": "P.######",
    }

    series_prefix = item_group_series_map.get(self.item_group)
    self.naming_series = series_prefix


def remove_item_price_list():
    frappe.db.sql("DELETE FROM `tabItem Price`")
    frappe.db.commit()

def remove_item_price_schedule():
    job = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.custom_py.item.remove_item_price_list'})
    if not job:
        sjt1 = frappe.new_doc("Scheduled Job Type")  
        sjt1.update({
            "method" : 'cyrix.custom_py.item.remove_item_price_list',
            "frequency" : 'Hourly'
        })
        sjt1.save(ignore_permissions=True)