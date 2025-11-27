// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Budgetary Quotation", {
	refresh(frm) {
        frm.trigger("create_quotation")
        frm.trigger("create_rfq")
	},
    create_quotation: function(frm){
        frm.add_custom_button(__('Quotation'), function(){	
            frm.call('create_quotation').then(r=>{
                if(r.message){
                    var doc = frappe.model.sync(r.message);
                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                }
            })
        },__("Create"))
    },
    create_rfq: function(frm){
        frm.add_custom_button(__('Request for Quotation'), function(){	
            frm.call('create_rfq').then(r=>{
                if(r.message){
                    var doc = frappe.model.sync(r.message);
                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                }
            })
        },__("Create"))
    }
});
