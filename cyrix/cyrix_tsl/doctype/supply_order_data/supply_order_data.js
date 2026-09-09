// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supply Order Data", {
	
	refresh(frm) {
		frm.dashboard.links_area.body.find('.btn-new').each(function(i, el) {
			$(el).hide();
		});
		
        if(frm.doc.docstatus == 1){
			if (frm.doc.status == "Supplier Quoted") {
				frm.add_custom_button(__("Supplier Quotation"), function () {

					frappe.call({
						method: "cyrix.custom_py.supplier_quotation.get_sq_details",
						args: {
							so: frm.doc.name
						},
						callback: function (r) {

							let quotations = r.message || [];
							console.log("Supplier Quotation Data", quotations);

							let d = new frappe.ui.Dialog({
								title: "Supplier Quotations Comparison",
								size: "extra-large",
								fields: [
									{
										fieldtype: "HTML",
										fieldname: "quotation_html"
									}
								],
								primary_action_label: "Close",
								primary_action() {
									d.hide();
								}
							});

							d.show();
							let is_mobile = window.innerWidth < 768;
							let wrapper = d.fields_dict.quotation_html.wrapper;

							// =====================================
							// GROUP BY SUPPLIER
							// =====================================

							let suppliers = {};
							let items = [];

							quotations.forEach(row => {

								// Supplier columns
								if (!suppliers[row.name]) {

									suppliers[row.name] = {
										supplier: row.supplier,
										currency: row.currency,
										grand_total: row.grand_total,
										shipping_cost: row.shipping_cost,
										terms: row.terms,
										items: {},
										taxes: []
									};
								}
								if (row.description) {
										suppliers[row.name].taxes.push({
											description: row.description,
											tax_amount: row.tax_amount
										});
									}
								if (
									row.description &&
									!suppliers[row.name].taxes.some(
										t => t.description === row.description &&
											t.tax_amount === row.tax_amount
									)
								) {
									suppliers[row.name].taxes.push({
										description: row.description,
										tax_amount: row.tax_amount
									});
								}
								// Store item against supplier
									suppliers[row.name].items[row.item_code] = {
									qty: row.qty,
									rate: row.rate,
									amount: row.amount,
									model: row.model_number,
									description: row.item_name
						};

								// Unique item list
								if (!items.includes(row.item_code)) {
									items.push(row.item_code);
								}
							});

							// =====================================
							// HTML
							// =====================================

							let html = "";

				if (!quotations.length) {
					html = `
						<div style="padding:30px;text-align:center;font-size:14px;">
							No Supplier Quotations Found
						</div>
					`;
				}
				else {

					// =====================================
					// MOBILE VIEW (CARD UI)
					// =====================================
					if (is_mobile) {

						html += `<div style="display:flex;flex-direction:column;gap:12px;">`;

						items.forEach(item_code => {

							html += `
								<div style="border:1px solid #ddd;border-radius:10px;padding:10px;">
									<div style="font-weight:700;margin-bottom:8px;">
										${item_code}
									</div>
							`;

							Object.keys(suppliers).forEach(name => {

								let s = suppliers[name];
								let item = s.items[item_code];

								html += `
					<div style="
						border-top:1px solid #f2f2f2;
						padding:10px;
						margin-top:8px;
						background:#fafafa;
						border-radius:8px;
					">

						<div style="
							font-weight:700;
							font-size:13px;
							color:#111827;
							margin-bottom:6px;
						">
							${s.supplier}
						</div>

						${
							item?.model
							? `
								<div style="
									font-size:12px;
									font-weight:600;
									color:#374151;
									margin-bottom:2px;
								">
									${item.model}
								</div>
							`
							: ""
						}

						${
							item?.description
							? `
								<div style="
									font-size:11px;
									color:#6b7280;
									margin-bottom:8px;
									line-height:1.3;
								">
									${item.description}
								</div>
							`
							: ""
						}

						<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
							<span style="color:#6b7280;">Rate</span>
							<span style="
								background:#e0f2fe;
								padding:2px 6px;
								border-radius:6px;
								font-weight:600;
								font-size:12px;
							">
								${item ? format_currency(item.rate || 0, s.currency) : "-"}
							</span>
						</div>

						<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
							<span style="color:#6b7280;">Qty</span>
							<span style="font-weight:500;">
								${item ? item.qty || 0 : "-"}
							</span>
						</div>

						<div style="
							display:flex;
							justify-content:space-between;
							margin-top:6px;
							padding-top:6px;
							border-top:1px dashed #ddd;
							font-weight:700;
						">
							<span>Total</span>
							<span style="color:#065f46;">
								${item ? format_currency(item.amount || 0, s.currency) : "-"}
							</span>
						</div>

					</div>
				`;
			});

			html += `</div>`;
		});

		// summary
		html += `<div style="margin-top:15px;border-top:1px solid #ddd;padding-top:10px;">`;

		Object.keys(suppliers).forEach(name => {
			let s = suppliers[name];

			html += `
				<div style="margin-bottom:10px;">
					<strong>${s.supplier}</strong><br>
					Shipping: ${format_currency(s.shipping_cost || 0, s.currency)}<br>
					Grand: <b>${format_currency(s.grand_total || 0, s.currency)}</b>
				</div>
			`;
		});

		html += `</div>`;
	}

	// =====================================
	// DESKTOP VIEW (TABLE UI - YOUR ORIGINAL)
	// =====================================
	else {

	html = `
	<div style="display:flex;gap:12px;overflow-x:auto;padding:10px;">

		<!-- ITEM COLUMN -->
		<div style="min-width:220px;position:sticky;left:0;background:#fff;z-index:5;border-right:1px solid #ddd;">
			<div style="font-weight:700;padding:10px;background:#f5f5f5;">
				Items
			</div>
	`;

	items.forEach(item_code => {
		html += `
			<div style="padding:10px;border-bottom:1px solid #eee;">
				${item_code}
			</div>
		`;
	});

	html += `
		</div>
	`;

	// =====================================
	// SUPPLIER CARDS
	// =====================================

	Object.keys(suppliers).forEach(name => {

		let s = suppliers[name];

		html += `
			<div style="
				min-width:260px;
				border:1px solid #ddd;
				border-radius:10px;
				background:#fff;
			">

				<div style="padding:10px;background:#e0f2fe;font-weight:700;">
					Supplier :${s.supplier}<br>
					<div style="margin-top:6px;">
						<a class="link"
							onclick="frappe.set_route('Form','Supplier Quotation','${name}')">
							${name}
						</a>
					</div>
				</div>
		`;

		items.forEach(item_code => {

			let item = s.items[item_code];

			html += `
			<div style="padding:10px;border-bottom:1px solid #f1f1f1;">

				<div style="font-weight:600;font-size:13px;">
					${item ? (item.model || item_code) : item_code}
				</div>

				<div style="font-size:11px;color:#666;margin-bottom:8px;white-space:normal;">
				
					${item ? (item.description || "") : ""}
				</div>

				<div style="display:flex;justify-content:space-between;">
					<span>Rate</span>
					<span>
						${item ? format_currency(item.rate || 0, s.currency) : "-"}
					</span>
				</div>

				<div style="display:flex;justify-content:space-between;">
					<span>Qty</span>
					<span>
						${item ? item.qty || 0 : "-"}
					</span>
				</div>

				<div style="display:flex;justify-content:space-between;font-weight:600;">
					<span>Total</span>
					<span>
						${item ? format_currency(item.amount || 0, s.currency) : "-"}
					</span>
				</div>
				<div style="font-size:11px;color:#666;margin-bottom:8px;white-space:normal;">
				
					${item ? (item.terms || "") : ""}
				</div>

			</div>
		`;
		});
		// Tax Table
		if (s.taxes && s.taxes.length) {

			html += `
				<div style="padding:10px;border-top:1px solid #ddd;">
					<div style="font-weight:600;margin-bottom:6px;">
						Taxes & Charges
					</div>
			`;

			s.taxes.forEach(tax => {
				html += `
					<div style="
						display:flex;
						justify-content:space-between;
						font-size:12px;
						margin-bottom:4px;
					">
						<span>${tax.description || ""}</span>
						<span>${format_currency(tax.tax_amount || 0, s.currency)}</span>
					</div>
				`;
			});

			html += `</div>`;
		}
		// summary
		html += `
			<div style="padding:10px;background:#f9fafb;">
			<div><b>Shipping:</b> ${format_currency(s.shipping_cost || 0, s.currency)}</div>
			<div><b>Grand:</b> ${format_currency(s.grand_total || 0, s.currency)}</div>

			<div style="
				margin-top:10px;
				padding-top:10px;
				border-top:1px solid #ddd;
				white-space:pre-line;
				font-size:11px;
			">
				<b>Terms & Conditions</b><br>
				${s.terms || ""}
			</div>
		</div>
		`;
	});

	html += `</div>`;
}
}

			$(wrapper).html(html);
		}
	});

});
}


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
											child.stock_uom = item.uom || "Nos";
											child.conversion_factor = 1;
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
											child.stock_uom = item.uom || "Nos";
											child.conversion_factor = 1;
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
						payment_details: r.message[0],
						sales_invoice_details: r.message[1]
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
