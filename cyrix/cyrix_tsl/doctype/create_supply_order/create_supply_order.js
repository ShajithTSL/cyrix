// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Create Supply Order", {
    branch: function(frm){
		if(!frm.doc.branch){
			frm.set_value("repair_warehouse", null);
			return
		}
		frappe.db.get_value('Warehouse', {'is_repair_warehouse':0,'company':frappe.defaults.get_default("company"),"name":["like","%"+frm.doc.branch+"%"]}, 'name', (values) => {
			frm.set_value("repair_warehouse", values.name);
		});
	},
	branch_trigger: function(frm){
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
			if (child.item_group) {
				d['item_group'] = child.item_group;
			}
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
					["is_repair_warehouse", "=", 0]
				]
			}
		});
		
		frm.trigger("branch_trigger")

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
					frm.set_df_property("customer_address", "options", "Customer  Address <br><br>" + r.message + "<br>");
					frm.refresh_fields();
				}
			});
		}
	},

	refresh(frm) {
		frm.disable_save()
		frappe.run_serially([
			// () => $('[data-fieldname="document_type"] select').css({'color':'white', 'background':'#00adef', 'font-weight':'bold'}),
			() => frm.set_value("company", frappe.defaults.get_default("company")),

			() => frm.trigger("branch"),
			
			() => {
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
								frappe.run_serially([
									() => cur_frm.reload_doc(),
									() => frm.trigger("branch_trigger"),
								])
							}   
						}
					})
				})
			},

			() => {
				frm.add_custom_button(__('<i class="fa fa-trash"></i>'), function () {
					frappe.model.delete_doc("Create Supply Order", "Create Supply Order", function () {
						window.location.reload();
					});
				})
			}
		])
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
						frm.set_value("sales_person",r.message[1][0])
					}
				}
			}
		});
	},
});