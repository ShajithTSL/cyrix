frappe.listview_settings['Return Note'] = {
	get_indicator: function (doc) {
		if (doc.status === "Return") {
			return [__("Return"), "darkgrey", "status,=,Return"];
		}
    },
};
