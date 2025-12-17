// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Create Job Order", {
	branch: function(frm){
		if(!frm.doc.branch){
			frm.set_value("repair_warehouse", null);
			return
		}
		frappe.db.get_value('Warehouse', {'is_repair_warehouse':1,'company':frappe.defaults.get_default("company"),"name":["like","%"+frm.doc.branch+"%"]}, 'name', (values) => {
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
					["company", "=", frappe.defaults.get_default("company")],
					["is_repair_warehouse", "=", 1]
				]
			}
		});
		const branchMap = frappe.boot.company_branches;

		if (branchMap[frappe.defaults.get_default("company")]) {
			const branches = branchMap[frappe.defaults.get_default("company")];

			// If only one branch exists, auto-set it
			if (branches.length === 1) {
				frm.set_value("branch", branches[0]);
				frm.set_df_property("branch", "read_only", 1);
			}
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frappe.defaults.get_default("company")]]
					]
				};
			});
		}	
		
		const territoryMap = frappe.boot.company_territories;

		if (territoryMap[frappe.defaults.get_default("company")]) {
			frm.set_query("customer", function () {
				return {
					filters: [
						["territory", "in", territoryMap[frappe.defaults.get_default("company")]]
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
					frm.set_df_property("customer_address", "options", "Customer  Address <br>" + r.message + "<br>");
					frm.refresh_fields();
				}
			});
		}
	},

	update_or_create_jo :function(frm){
		if(frm.doc.job_order_data){
			if(frm.doc.is_returned_unit){
				 // If job_order_data exists Update the existing Job Order
				frm.add_custom_button(__("Update Job Order"), function () {
					frappe.call({
						method:"cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.update_job_order_data",
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
				frm.remove_custom_button(__("Create Job Order")); // Remove the "Create Job Order" button to avoid duplication/conflict
				frm.remove_custom_button(__("Create Board Level JO")); // Remove the "Create Board Level JO" button to avoid duplication/conflict
			}
			else{
				 // If job_order_data exists Update the existing Job Order
				frm.add_custom_button(__("Create Board Level JO"), function () {
					frappe.call({
						method:"cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.create_job_order_data",
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
				frm.remove_custom_button(__("Create Job Order")); // Remove the "Create Job Order" button to avoid duplication/conflict
				frm.remove_custom_button(__("Update Job Order")); // Remove the "Update Job Order" button since it's not applicable yet
			}
        }
        else{
            // If job_order_data does not exist Create a New Job Order
            frm.add_custom_button(__("Create Job Order"), function () {
                frappe.call({
                    method:"cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.create_job_order_data",
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
			frm.remove_custom_button(__("Update Job Order")); // Remove the "Update Job Order" button since it's not applicable yet
        }
	},


	refresh(frm) {
		frm.disable_save();

		frappe.run_serially([
			() => frm.set_value("company", frappe.defaults.get_default("company")),

			() => frm.trigger("branch"),

			() => frm.trigger("update_or_create_jo"),

			() => {
				if (frappe.route_options.job_order_data) {
					frm.set_value("job_order_data", frappe.route_options.job_order_data);
					frappe.route_options = null;
				}
			},
			
			() => {
				frm.add_custom_button(__('<i class="fa fa-trash"></i>'), function () {
					frappe.model.delete_doc("Create Job Order", "Create Job Order", function () {
						window.location.reload();
					});
				})
			}
		]);
	},

    job_order_data: function (frm) {
        frm.trigger("refresh")
		if (frm.doc.job_order_data) { // if the job_order_data is present, fetch the details
			frappe.call({
				method: 'cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.get_jo_details',
				args: {
					"jo": frm.doc.job_order_data,
				},
				callback(r) {
					if (r.message) {
						for (var i = 0; i < r.message.length; i++) {
							if(frm.doc.is_returned_unit){								
								var childTable = cur_frm.add_child("received_equipment");
								childTable.item_code = r.message[i]['item_code'],
								childTable.item_name = r.message[i]["item_name"],
								childTable.manufacturer = r.message[i]["mfg"]
								childTable.model = r.message[i]["model_no"],
								childTable.type = r.message[i]["type"],
								childTable.qty = r.message[i]["qty"]
							}
                            frm.doc.sales_person = r.message[i]["sales_person"],
                            frm.doc.customer = r.message[i]["customer"],
							frm.doc.address = r.message[i]["address"],
							frm.doc.incharge = r.message[i]["incharge"],
							frm.doc.incharge_name = r.message[i]["incharge_name"],
							frm.doc.incharge_email = r.message[i]["incharge_email"],
							frm.doc.incharge_phone_no = r.message[i]["incharge_phone_no"],
							frm.doc.branch = r.message[i]["branch"]
							frm.doc.company = r.message[i]["company"]
							frm.doc.repair_warehouse = r.message[i]["repair_warehouse"]
							cur_frm.refresh_fields();
							frappe.run_serially([
								() => frm.trigger("address")
							])
						}
					}
				}
			});

		}
	},

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
						frm.set_value("sales_person",r.message[1])
					}
				}
			}
		});
	},
});