// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Create Budgetary Quotation", {
    customer(frm){
		frm.call('get_contact').then(r=>{
			if(r.message){
				console.log(r.message[0])
				frm.set_value("customer_representative",r.message[0])
			}					
        })
	},

    create_bq(frm){        
        frm.add_custom_button("Create Budgetary Quotation", function(){
            frm.call('create_budget_quote').then(r=>{
                if(r){
                    cur_frm.reload_doc();
                }					
            })          
        })
    },

	refresh: function(frm) {
		frappe.run_serially([
			() => frm.disable_save(),

			() => frm.set_value("company", frappe.defaults.get_default("company")),

			() => {
				frm.fields_dict['items'].grid.get_field('sku').get_query = function(doc, cdt, cdn) {
					let row = locals[cdt][cdn];
					return {
						filters: {
							'model': row.model // Filter by model
						}
					};
				};
			},

			() => frm.trigger("create_bq") // create BQ
		]);
	},

	setup: function (frm) {
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
		
		frm.set_query("department", function () {
			return {
                filters: {
                    'company': frappe.defaults.get_default("company")  // Filter department by company
                }
			}
		});
	}
});
