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
			frm.add_custom_button(__("Internal Quotation"), function(){
				let allowed_customers = [];

				if (frm.doc.customer) {
					allowed_customers.push(frm.doc.customer);
				}

				if (frm.doc.parent_customer) {
					allowed_customers.push(frm.doc.parent_customer);
				}

				let d = new frappe.ui.Dialog({
					title: 'Select Customer',
					fields: [
						{
							label: 'Customer',
							fieldname: 'customer',
							fieldtype: 'Link',
							options: 'Customer',
							reqd: 1,
							get_query: function() {
								return {
									filters: [
										['Customer', 'name', 'in', allowed_customers]
									]
								};
							}
						}
					],
					primary_action_label: 'Proceed',
					primary_action(values) {
						if (!values.customer) {
							frappe.msgprint('Please select a customer');
							return;
						}

						d.hide();
						frappe.call({
							method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_internal_quotation",
							args: {
								"supply_order_data": frm.doc.name,
								"customer":values.customer
							},
							callback: function(r) {
								if(r.message) {
									var doc = frappe.model.sync(r.message);
									frappe.set_route("Form", doc[0].doctype, doc[0].name);
									
								}
							}
						});
					}
				});
				d.show();
			},__('Create'));
			frm.add_custom_button(__("Delivery Note"), function(){
				let allowed_customers = [];

				if (frm.doc.customer) {
					allowed_customers.push(frm.doc.customer);
				}

				if (frm.doc.parent_customer) {
					allowed_customers.push(frm.doc.parent_customer);
				}

				let d = new frappe.ui.Dialog({
					title: 'Select Customer',
					fields: [
						{
							label: 'Customer',
							fieldname: 'customer',
							fieldtype: 'Link',
							options: 'Customer',
							reqd: 1,
							get_query: function() {
								return {
									filters: [
										['Customer', 'name', 'in', allowed_customers]
									]
								};
							}
						}
					],
					primary_action_label: 'Proceed',
					primary_action(values) {
						if (!values.customer) {
							frappe.msgprint('Please select a customer');
							return;
						}

						d.hide();
						frappe.call({
							method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_delivery_note",
							args: {
								"supply_order_data": frm.doc.name,
								"customer":values.customer
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
					}
				});

				d.show();
			},__('Create'));


			frm.add_custom_button(__("Sales Invoice"), function(){
				let allowed_customers = [];

				if (frm.doc.customer) {
					allowed_customers.push(frm.doc.customer);
				}

				if (frm.doc.parent_customer) {
					allowed_customers.push(frm.doc.parent_customer);
				}

				let d = new frappe.ui.Dialog({
					title: 'Select Customer',
					fields: [
						{
							label: 'Customer',
							fieldname: 'customer',
							fieldtype: 'Link',
							options: 'Customer',
							reqd: 1,
							get_query: function() {
								return {
									filters: [
										['Customer', 'name', 'in', allowed_customers]
									]
								};
							}
						}
					],
					primary_action_label: 'Proceed',
					primary_action(values) {
						if (!values.customer) {
							frappe.msgprint('Please select a customer');
							return;
						}
						d.hide();
						frappe.call({
							method: "cyrix.cyrix_tsl.doctype.supply_order_data.supply_order_data.create_sales_invoice",
							args: {
								"supply_order_data": frm.doc.name,
								"customer": values.customer
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
					}
				});
				d.show();
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
					frm.fields_dict.detail_html.$wrapper.html(html);
					
					const status_html = frappe.render_template("status", {
						doc: frm.doc
					});
					frm.fields_dict.status_detail.$wrapper.html(status_html);
				}
			}
		})
	},
});
