// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Cancellation', {
	refresh: function(frm) {
		frm.set_query('job_order_data', 'cancellation_table', function(doc, cdt, cdn) {
			return {
				filters:[
					['company', '=', doc.company],
					['branch', '=', doc.branch],
					['sales_rep', '=', doc.sales_person],
					['status', '!=', "C-Cancelled"],
					['invoice_no', 'is', 'set']
				]
			};
		});

		frm.set_query('invoice_no', 'cancellation_list', function(doc, cdt, cdn) {
			return {
				filters:[
					['company', '=', doc.company],
					['branch', '=', doc.branch],
					['sales_rep', '=', doc.sales_person],
					['is_return', '!=', "1"],
				]
			};
		});
	}
});



frappe.ui.form.on('Cancellation Table', {
	job_order_data(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.job_order_data) {
		  	frappe.call({
				method: "cyrix.cyrix_tsl.doctype.invoice_cancellation.invoice_cancellation.invoice_cancellation",
				args: {
					"job_order_data": child.job_order_data
				},
				callback: function(r) {
					if(r.message) {
					
						$.each(r.message,function(i,d){
							let child = frm.add_child('cancellation_table');
								child.sales_invoice = d.name;
							
						})
						frm.refresh_field('cancellation_table');		
						
					}
				}				
			})
		}	
	},
	invoice_no(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.invoice_no) {
		  	frappe.call({
				method: "cyrix.cyrix_tsl.doctype.invoice_cancellation.invoice_cancellation.invoice_cancellation_si",
				args: {
					"sales_invoice": child.invoice_no
				},
				callback: function(r) {
						console.log(r)
					if(r.message) {
						console.log(r)
						// $.each(r.message,function(i,d){
						// 	let child = frm.add_child('cancellation_table');
						// 		child.sales_invoice = d.name;
							
						// })
						// frm.refresh_field('cancellation_table');		
						
					}
				}				
			})
		}	
	},
})