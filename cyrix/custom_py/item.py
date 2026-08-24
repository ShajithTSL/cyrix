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