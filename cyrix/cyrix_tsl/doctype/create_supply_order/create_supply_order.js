// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Create Supply Order", {
    branch: function(frm){
		if(!frm.doc.branch){
			frm.set_value("repair_warehouse", null);
			return
		}
		frappe.db.get_value('Warehouse', {'is_repair_warehouse':0,'company':frm.doc.company,"name":["like","%"+frm.doc.branch+"%"]}, 'name', (values) => {
			frm.set_value("repair_warehouse", values.name);
		});
	},
    setup: function (frm) {
        // child table set_query
		frm.fields_dict['received_equipment'].grid.get_field('item_code').get_query = function (frm, cdt, cdn) {
			var child = locals[cdt][cdn];
			var d = {};
			if (child.model) {
				d['model'] = child.model;
			}
			if (child.manufacturer) {
				d['mfg'] = child.manufacturer;
			}
			if (child.type) {
				d['type'] = child.type;
			}
			d['item_group'] = "Equipments";
			return {
				filters: d
			}
		}
        frm.set_query("address", function () {
			return {
				filters: [
					["Dynamic Link", "parenttype", "=", "Address"],
					["Dynamic Link", "link_name", "=", frm.doc.customer],
					["Dynamic Link", "link_doctype", "=", "Customer"]

				]
			}
		});
		frm.set_query("repair_warehouse", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
					["is_repair_warehouse", "=", 1]
				]
			}
		});
		const branchMap = frappe.boot.company_branches;

		if (branchMap[frm.doc.company]) {
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frm.doc.company]]
					]
				};
			});
		}		
	},
    address: function (frm) {
        // to set address_display
		if (frm.doc.address) {
			frappe.call({
				method: 'frappe.contacts.doctype.address.address.get_address_display',
				args: {
					"address_dict": frm.doc.address
				},
				callback: function (r) {
					frm.set_df_property("customer_address", "options", "Customer  Address <br><br>" + r.message + "<br>");
					frm.refresh_fields();
				}
			});
		}
	},
	refresh(frm) {
		frm.disable_save()
       	// If job_order_data does not exist Create a New Job Order
		frm.add_custom_button(__("Create Supply Order"), function () {
			frappe.call({
				method:"cyrix.cyrix_tsl.doctype.create_supply_order.create_supply_order.create_supply_order_data",
				args:{
					dict: cur_frm.doc
				},
				callback(r){
					if(r){
						// On success, reload the document to reflect changes
						cur_frm.reload_doc();
					}   
				}
			})
		})
	},
    // job_order_data: function (frm) {
    //     frm.trigger("refresh")
	// 	if (frm.doc.job_order_data) { // if the job_order_data is present, fetch the details
	// 		frappe.call({
	// 			method: 'cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.get_jo_details',
	// 			args: {
	// 				"jo": frm.doc.job_order_data,
	// 			},
	// 			callback(r) {
	// 				if (r.message) {
	// 					for (var i = 0; i < r.message.length; i++) {
	// 						var childTable = cur_frm.add_child("received_equipment");
	// 						childTable.item_code = r.message[i]['item_code'],
    //                         childTable.item_name = r.message[i]["item_name"],
    //                         childTable.manufacturer = r.message[i]["mfg"]
	// 						childTable.model = r.message[i]["model_no"],
	// 						childTable.type = r.message[i]["type"],
    //                         childTable.qty = r.message[i]["qty"],
    //                         frm.doc.sales_person = r.message[i]["sales_rep"],
    //                         frm.doc.customer = r.message[i]["customer"],
	// 						frm.doc.address = r.message[i]["address"],
	// 						frm.doc.incharge = r.message[i]["incharge"],
	// 						frm.doc.branch = r.message[i]["branch"]
	// 						frm.doc.company = r.message[i]["company"]
	// 						frm.doc.repair_warehouse = r.message[i]["repair_warehouse"]
	// 						cur_frm.refresh_fields();
	// 					}
	// 				}
	// 			}
	// 		});

	// 	}
	// },
	customer: function (frm) {
		if (!frm.doc.customer) {
			return
		}
		frappe.call({
			method: 'cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.get_contacts',
			args: {
				"customer": frm.doc.customer,
			},
			callback(r) {
				if (r.message) {
                    console.log(r.message)
					frm.set_query("incharge", function () {
						return {
							"filters": {
								"name": ["in", r.message[0]]
							}
						};
					});
					if (r.message[0]) {
						frm.set_value("incharge", r.message[0][0])
					}
					if (r.message[1]) {
						frm.set_query("sales_person", function () {
							return {
								"filters": {
									"name": ["in", r.message[1]]
								}
							};
						});
					}
				}
			}
		});
	},
});

