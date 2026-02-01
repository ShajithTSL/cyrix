// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supply Order Data", {
	refresh(frm) {
        if(frm.doc.docstatus == 1){
			frm.add_custom_button(__("Request for Quotation"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_rfq",
					args: {
						"supply_order_data": frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
			frm.add_custom_button(__("Quotation"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_internal_quotation",
					args: {
						"supply_order_data": frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
							
						}
					}
				});
			},__('Create'));
			frm.add_custom_button(__("Delivery Note"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_delivery_note",
					args: {
						"supply_order_data": frm.doc.name
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
									child.supply_order_data = item.supply_order_data;
								});

								// Route to unsaved DN
								frappe.set_route("Form", doc.doctype, doc.name);
							});
						}
					}
				});
			},__('Create'));


			frm.add_custom_button(__("Sales Invoice"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_sales_invoice",
					args: {
						"supply_order_data": frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							const dn_data = r.message[0];
							const items_data = r.message[1];

							if (!Array.isArray(items_data)) {
								frappe.msgprint("Item data is not in expected format.");
								return;
							}

							frappe.model.with_doctype("Sales Invoice", function () {
								const doc = frappe.model.get_new_doc("Sales Invoice");

								// Store custom item data temporarily
								doc.__custom_items_to_override = items_data;

								// Assign DN fields (like customer, company, etc.)
								Object.assign(doc, dn_data);

								doc.items = [];

								// Add items (without setting rate yet)
								items_data.forEach(item => {
									let child = frappe.model.add_child(doc, "Sales Invoice Item", "items");
									child.item_code = item.item_code;
									child.item_name = item.item_name || "";
									child.qty = item.qty;
									child.uom = item.uom || "Nos";
									child.warehouse = item.warehouse;
									child.supply_order_data = item.supply_order_data;
								});

								// Route to unsaved DN
								frappe.set_route("Form", doc.doctype, doc.name);
							});
						}
					}
				});
			},__('Create'));
		}

		frappe.call({
			method:"cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.fetch_payment_details",
			args:{
				name: frm.doc.name
			},
			callback(r){
				if(r.message){
					const html = frappe.render_template("supply_order_data", {
						doc: frm.doc,
						payment_details: r.message
					});
					// const html = frappe.render_template("status");
					frm.fields_dict.detail_html.$wrapper.html(html);
				}
			}
		})
	},
});
