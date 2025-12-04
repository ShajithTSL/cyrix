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
		frm.disable_save()
		frm.fields_dict['items'].grid.get_field('sku').get_query = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                filters: {
                    'model': row.model // Filter by model
                }
            };
        };
        frm.trigger("create_bq") // create BQ
	},

	setup: function (frm) {
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
		frm.set_query("department", function () {
			return {
                filters: {
                    'company': frm.doc.company  // Filter department by company
                }
			}
		});
	}
});
