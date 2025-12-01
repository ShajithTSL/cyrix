// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Order Data", {
	refresh(frm) {
        if(frm.doc.attach_image && frm.doc.docstatus == 1){
			cur_frm.set_df_property("image", "options","<img src="+frm.doc.attach_image+">");
			cur_frm.refresh_fields();
		}
        frm.trigger("create_evaluation_report")
		frm.trigger("create_internal_quotation")
		frm.trigger("route_to_jo_creation")
		frm.trigger("create_delivery_note")
		frm.trigger("create_return_note")
	},
    create_evaluation_report(frm){
        if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Evaluation Report"), function(){
				if(frm.doc.technician.length == 0){
					frappe.msgprint("Select <b>Technician</b> to create Evaluation Report")
					return
				}
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_evaluation_report",
					args: {
						"doc_no": frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							console.log(r.message)
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
		}
    },
	create_internal_quotation(frm){
        if(frm.doc.docstatus == 1 && !frm.doc.parent_jo) {
			frm.add_custom_button(__("Internal Quotation"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_internal_quotation",
					args: {
						"job_order_data": frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
		}
	},
	route_to_jo_creation(frm){
		if(frm.doc.docstatus ==1 && frm.doc.unit_type == "Service and Board Level Unit"){
			frm.add_custom_button(__("Board Level JO"), function(){
				frappe.route_options = {
					job_order_data: frm.doc.name,
				};																
				frappe.set_route('Form', 'Create Job Order', 'Create Job Order');
			},__('Create'));
		}
	},	
	create_delivery_note:function(frm){
		if(frm.doc.docstatus == 1 && !frm.doc.parent_jo){
			frm.add_custom_button(__("Delivery Note"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_delivery_note",
					args: {
						"job_order_data": frm.doc.name
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
									child.job_order_data = item.job_order_data;
								});

								// Route to unsaved DN
								frappe.set_route("Form", doc.doctype, doc.name);
							});
						}
					}
				});
			},__('Create'));
		}
	},
	create_return_note: function(frm){
		if(frm.doc.docstatus == 1 && ["RNR-Return Not Repaired","RNRC-Return Not Repaired Client",
									"RNF-Return No Fault","RNA-Return Not Approved",
									"RNP-Return No Parts" ,"C-Comparison"].includes(frm.doc.status)){
			frm.add_custom_button(__("Return Note"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_return_note",
					args: {
						"job_order_data": frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
		}
	}
});
