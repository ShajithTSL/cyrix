// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Cancellation', {

	print_button: function(frm){
		frm.add_custom_button(__("Print"), function () {
			let f_name = frm.doc.name;
			window.open(
				frappe.urllib.get_full_url(
					"/api/method/frappe.utils.print_format.download_pdf?"
					+ "doctype=" + encodeURIComponent(frm.doc.doctype)
					+ "&name=" + encodeURIComponent(f_name)
					+ "&trigger_print=1"
					+ "&format=" + encodeURIComponent("Invoice Cancellation")
					+ "&no_letterhead=0"
				)
			);

		});
	},

	before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to Finance") {
					frm.call({
						method: 'trigger_mail_on_invoice_cancellation',
						args: {
							"name": frm.doc.name,
						},
					})
				}
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
	},

	company: function(frm){
		frm.trigger("setup_query")
	},

	onload: function(frm){
		frm.trigger("setup_query")
	},
	
	setup: function(frm){
		frm.trigger("setup_query")
	},
	
	branch: function(frm){
		if (frm.doc.branch){
			frm.set_query("sales_person", function () {
				return {
					"filters": {
						"custom_branch": ["in", [frm.doc.branch,""]]
					}
				};
			});
		}
	},

	setup_query: function(frm){
		const branchMap = frappe.boot.company_branches;

		if (branchMap[frm.doc.company]) {
			const branches = branchMap[frm.doc.company];

			// If only one branch exists, auto-set it
			if (branches.length === 1) {
				frm.set_value("branch", branches[0]);
				frm.set_df_property("branch", "read_only", 1);
			}
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frm.doc.company]]
					]
				};
			});
		}	
	},

	refresh: function(frm) {
		
		if (!frm.doc.__islocal && frm.doc.docstatus != 2){
			frm.trigger("print_button")
		}
		
		frm.set_query('invoice_no', 'cancellation_list', function(doc, cdt, cdn) {
			return {
				filters:[
					['company', '=', doc.company],
					['branch', '=', doc.branch],
					['sales_person', '=', doc.sales_person],
					['is_return', '!=', "1"],
				]
			};
		});

		frm.trigger("setup_query")
	}
});



frappe.ui.form.on('Cancellation List', {
	invoice_no(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.invoice_no) {
		  	frappe.call({
				method: "cyrix.cyrix_tsl.doctype.invoice_cancellation.invoice_cancellation.invoice_cancellation_si",
				args: {
					"sales_invoice": child.invoice_no
				},
				callback: function(r) {
					if(r.message) {
						$.each(r.message,function(i,d){
							console.log( d.job_order_data)
							if (d.job_order_data || d.supply_order_data) {
								let child = frm.add_child('cancellation_list');
								child.job_order_data = d.job_order_data;
								child.supply_order_data = d.supply_order_data;
							}
						})
						frm.refresh_field('cancellation_list');		
					}
				}				
			})
		}	
	},
})