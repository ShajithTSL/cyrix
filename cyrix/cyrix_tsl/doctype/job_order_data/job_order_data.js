// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Order Data", {
	
	receive_unit: function(frm){
		let d = new frappe.ui.Dialog({
			title: 'Receive Unit',
			fields: [
				{
					label: 'Serial Number',
					fieldname: 'serial_number',
					default:frm.doc.material_list[0].serial_no,
					description:"<b style = 'color:red'>Note: If needed, mention the Serial Number and Click Proceed</b>",
					fieldtype: 'Data'
				},
				{
					label: 'Attach',
					fieldname: 'attach_image',
					fieldtype: 'Attach Image'
				}
			],
			primary_action_label: '',
			primary_action(values) {
				d.hide();
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_received_unit",
					args: {
						job_order_data: frm.doc.name,
						serial_number: values.serial_number ||  null,
						attach_image: values.attach_image || null
					},
					callback: function(res) {
						window.location.reload();
					}
				});
			}
		});
		d.show();
	},

	custom_status: function(frm) {
		frm.set_value("status", frm.doc.custom_status);
	},
	
	refresh(frm) {
		frm.dashboard.links_area.body.find('.btn-new').each(function(i, el) {
			$(el).hide();
		});
		if(frm.doc.docstatus == 1 ){
			frm.add_custom_button(__("Technical Report"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_technical_report",
					args: {
						name: frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
			frm.add_custom_button(__("Request for Quotation"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_rfq_from_jo",
					args: {
						name: frm.doc.name
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

	// frm.set_df_property('item_price_details', 'hidden', 1);


	 frappe.db.get_value(
            'Replacement Unit',
            { name: frm.doc.name },
            ['name']
        ).then((r) => {

            let replacement_unit_exists = 0;

            if (r.message && r.message.name) {
                replacement_unit_exists = 1;
            }

            // Hide child table
            if (replacement_unit_exists == 1) {
                frm.set_df_property('item_price_details', 'hidden', 0);
            } else {
                frm.set_df_property('item_price_details', 'hidden', 1);
            }

            frm.refresh_field('items');
        });


	if (frm.doc.status == "Replace" || frm.doc.status == "RNR-Return Not Repaired" || frm.doc.status == "RNP-Return No Parts") {
		
		// create Supply Order Data button
		frm.add_custom_button(__("Supply Order Data"), function(){
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_supply_order_data",
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

	frm.add_custom_button(__('Replacement Unit'), function () {

        frappe.confirm(
            __('Do you want to release stock for this Replacement?'),

            // YES → Replacement + Stock
            function () {
                create_replacement(1);
            },

            // NO → Only Replacement
            function () {
                create_replacement(0);
            }
        );

        function create_replacement(release_stock) {
            frappe.call({
                method: "cyrix.custom_py.utils.create_replacement_item",
                freeze: true,
                freeze_message: __("Creating Replacement..."),
                args: {
                    customer: frm.doc.customer,
                    wod: frm.doc.name,
                    items: frm.doc.material_list,
                    release_stock: release_stock
                },
                callback: function (r) {
                    if (!r.exc) {
                        frappe.msgprint(__('Replacement Created Successfully'));
                        frm.reload_doc();
                    }
                }
            });
        }

    },__('Create'));
	// Request for Quotation option
	

}
        if(frm.doc.attach_image && frm.doc.docstatus == 1){
			cur_frm.set_df_property("image", "options","<img src="+frm.doc.attach_image+">");
			cur_frm.refresh_fields();
		}
        frm.trigger("create_evaluation_report")
		frm.trigger("create_internal_quotation")
		frm.trigger("route_to_jo_creation")
		frm.trigger("create_delivery_note")
		frm.trigger("create_return_note")

		frappe.call({
			method:"cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.fetch_payment_details",
			args:{
				name: frm.doc.name
			},
			callback(r){
				if(r.message){
					const html = frappe.render_template("job_order_data", {
						doc: frm.doc,
						payment_details: r.message
					});
					frm.fields_dict.detail_html.$wrapper.html(html);
				}
			}
		})
		
		frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "DocShare",
                filters: {
                    share_doctype: frm.doctype,
                    share_name: frm.doc.name
                },
                fields: ["user"]
            },
            callback: function (r) {
                let description;

                if (r.message && r.message.length) {
                    const users = r.message.map(d => d.user).join(", ");
                    description = `
                        <span>Shared with: <b>${users}</b></span>
                        &nbsp;•&nbsp;
                        <a href="#" class="open-share">Manage</a>
                    `;
                } else {
                    description = `
                        <a href="#" class="open-share text-muted">
                            Not shared with any users — Click to share
                        </a>
                    `;
                }

                frm.set_df_property(
                    "multiple_technicians",
                    "description",
                    description
                );

                // Attach click handler AFTER description is rendered
                setTimeout(() => {
                    frm.fields_dict.multiple_technicians.$wrapper
                        .find(".open-share")
                        .off("click")
                        .on("click", function (e) {
                            e.preventDefault();
							if (!frm.shared) {
								frm.shared = new frappe.ui.form.Share({ frm: frm, parent: frm.sidebar });
							}
							
							// Show the standard share dialog
							frm.shared.show();
                        });
                }, 0);
            }
        });


	},
    create_evaluation_report(frm){
        if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Evaluation Report"), function(){
				if(!frm.doc.technician && !frm.doc.multiple_technicians.length > 0){
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

			frm.add_custom_button(__("Internal Quotation"), function() {
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.get_eval_list", // 👈 create this whitelisted method
					args: {
						job_order_data: frm.doc.name
					},
					callback: function(r) {

						let jo_list = r.message || [];

						if (!jo_list.length) {
							frappe.msgprint("No Job Orders found.");
							return;
						}

						// // ✅ Check if ANY evaluation exists for parent/children
						// frappe.db.get_list("Evaluation Report", {
						// 	filters: {
						// 		job_order_data: ["in", jo_list],
						// 		docstatus: 1
						// 	},
						// 	limit: 1
						// }).then(records => {

						// 	// ✅ If EXISTS → normal flow
						// 	if (records.length > 0) {
						// 		create_internal_quotation(0);
						// 	}

						// 	// ⚠️ If NOT EXISTS → confirm
						// 	else {
						// 		frappe.confirm(
						// 			"Evaluation not Completed for any related Job Order. Do you want to proceed with pre evaluation?",

						// 			function() { // YES
						// 				create_internal_quotation(1);
						// 			},

						// 			function() { // NO
						// 				frappe.msgprint("Please create Evaluation Report to proceed.");
						// 			}
						// 		);
						// 	}
						// });


						// Check Evaluation Report
					frappe.db.get_list("Evaluation Report", {
						filters: {
							job_order_data: ["in", jo_list],
							docstatus: 1
						},
						limit: 1
					}).then(eval_records => {

						if (eval_records.length > 0) {
							// Evaluation completed
							create_internal_quotation(0,0);
						} else {

							// Check Replacement Unit
							frappe.db.get_list("Replacement Unit", {
								filters: {
									parent_jo: frm.doc.name
								},
								limit: 1
							}).then(rep_records => {

								if (rep_records.length > 0) {

									frappe.confirm(
										"Replacement Unit has been created for this Job Order. Do you want to proceed with creating the quotation?",

										function () { // YES
											create_internal_quotation(0,1);
										},

										function () { // NO
											frappe.msgprint("Quotation creation cancelled.");
										}
									);

								} else {

									frappe.confirm(
										"Evaluation not completed for any related Job Order. Do you want to proceed with pre-evaluation?",

										function () { // YES
											create_internal_quotation(1,0);
										},

										function () { // NO
											frappe.msgprint("Please create an Evaluation Report to proceed.");
										}
									);

								}
							});

						}
					});
					}
				});

				function create_internal_quotation(pre_eval,rp) {
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
								method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_internal_quotation",
								args: {
									job_order_data: frm.doc.name,
									pre_evaluation: pre_eval,
									customer: values.customer,
									replacement:rp
								},
								callback: function(res) {
									if (res.message) {
										var doc = frappe.model.sync(res.message);
										frappe.set_route("Form", doc[0].doctype, doc[0].name);
									}
								}
							});
						}
					});
					d.show();
				}

			}, __('Create'));
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
				show_customer_dialog_dn(frm);
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


frappe.ui.form.on('Material List', {
    update_sku(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
		update_sku_dialog(frm, child);
	},
	update_serial(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		update_serial_dialog(frm, child);
	}
});

function show_customer_dialog_dn(frm) {
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
				method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.create_delivery_note",
				args: {
					"job_order_data": frm.doc.name,
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
								child.job_order_data = item.job_order_data;
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
}

function update_serial_dialog(frm, row) {
	let dialog = new frappe.ui.Dialog({
		title: "Change Serial Number",
		fields: [
			{
				label: "Serial Number",
				fieldname: "serial_no",
				fieldtype: "Data",
				default: row.serial_no || "",
				reqd: 1
			}
		],
		primary_action_label: "Proceed",
		primary_action(values) {

			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.change_serial_number",
				args: {
					job_order_data: frm.doc.name,
					row_name: row.name,
					new_serial_no: values.serial_no
				},
				freeze: true,
				callback: function(r) {
					if (!r.exc) {
						frm.reload_doc();
						dialog.hide();
					}
				}
			});

		}
	});

	dialog.show();
}

function update_sku_dialog(frm, row) {
    let dialog = new frappe.ui.Dialog({
        title: "Change Item Details",
        fields: [
            {
                label: "Item Name",
                fieldname: "item_name",
                fieldtype: "Data",
                default: row.item_name || "",
                reqd: 1
            },
            {
                label: "Item Model",
                fieldname: "model",
                fieldtype: "Link",
                options: "Item Model",
                default: row.model_no || "",
                reqd: 1
            },
            {
                label: "Manufacturer",
                fieldname: "mfg",
                fieldtype: "Link",
                options: "Item Mfg",
                default: row.mfg || "",
                reqd: 1
            },
            {
                label: "Description",
                fieldname: "description",
                fieldtype: "Small Text",
                default: row.item_name || ""
            },
            {
                label: "Action",
                fieldname: "action",
                fieldtype: "Select",
                options: [
                    { label: "Create New Item", value: "create" },
                    { label: "Update Existing Item (If Not Used)", value: "update" }
                ],
                default: "create",
                reqd: 1
            }
        ],
        primary_action_label: "Proceed",
        primary_action(values) {

            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.job_order_data.job_order_data.change_or_create_item",
                args: {
                    job_order_data: frm.doc.name,
                    row_name: row.name,
                    values: values
                },
                freeze: true,
                callback: function(r) {
                    if (!r.exc) {
                        frm.reload_doc();
                        dialog.hide();
                    }
                }
            });

        }
    });

    dialog.show();
}

