// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Budgetary Quotation", {
    create_delivery_note: function(frm){
        frm.add_custom_button(__("Delivery Note"), function(){
            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.budgetary_quotation.budgetary_quotation.create_delivery_note",
                args: {
                    "budgetary_quotation": frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        const dn_data = r.message[0];
                        const items_data = r.message[1];

                        if (!Array.isArray(items_data)) {
                            frappe.msgprint("Item data is not in expected format.");
                            return;
                        }

                        frappe.model.with_doctype("Delivery Note", function () {
                            const doc = frappe.model.get_new_doc("Delivery Note");

                            // Store custom item data temporarily
                            doc.__custom_items_to_override = items_data;

                            // Assign DN fields (like customer, company, etc.)
                            Object.assign(doc, dn_data);

                            doc.items = [];

                            // Add items (without setting rate yet)
                            items_data.forEach(item => {
                                let child = frappe.model.add_child(doc, "Delivery Note Item", "items");
                                child.item_code = item.item_code;
                                child.item_name = item.item_name || "";
                                child.qty = item.qty;
                                child.uom = item.uom || "Nos";
                                child.warehouse = item.warehouse;
                                child.budgetary_quotation = item.budgetary_quotation;
                            });

                            // Route to unsaved DN
                            frappe.set_route("Form", doc.doctype, doc.name);
                        });
                    }
                }
            });
        },__('Create'));
    },
    show_tender_popup(frm) {
        let d = new frappe.ui.Dialog({
            title: "Enter Tender Details",
            fields: [
                {
                    label: "Tender Number",
                    fieldname: "tender_number",
                    fieldtype: "Data",
                    reqd: true
                },
                {
                    label: "Tender Converted Date",
                    fieldname: "tender_converted_date",
                    fieldtype: "Date",
                    reqd: true
                }
            ],
            primary_action_label: "Submit",
            primary_action(values) {

                // Set values into the document
                frm.set_value("tender_number", values.tender_number);
                frm.set_value("tender_converted_date", values.tender_converted_date);
                
				frappe.show_alert({ message: __("Make sure to save the document"), indicator: "red" });
                // frappe.msgprint("Tender details updated.");
                d.hide();
            }
        });

        d.show();
    },
	refresh(frm) {
        if(frm.doc.tender_number && frm.doc.tender_converted_date){
            frm.set_intro("<b style = font-size:15px> Tender Converted </b>")
        }
        if (!frm.doc.tender_number || !frm.doc.tender_converted_date){
            frm.add_custom_button("Convert Tender", function(){
                    frm.trigger("show_tender_popup")
            })
            
            frm.change_custom_button_type(__("Convert Tender"), null, "primary");
        }
        frm.trigger("create_quotation")
        frm.trigger("create_rfq")
        if(frm.doc.docstatus == 1){
            frm.trigger("create_delivery_note")
        }
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
