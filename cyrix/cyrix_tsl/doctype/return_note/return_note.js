// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Return Note', {
	refresh: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value("conversion_rate","1")
			frm.set_value("plc_conversion_rate","1")
		}
	},
	validate:function(frm){
		frm.set_value("grand_total","1")
		frm.set_value("base_grand_total","1")
		frm.set_value("base_total","1")
		frm.set_value("base_net_total","1")
	}
});
