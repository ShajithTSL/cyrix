// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Request", {
    onload: function(frm) {
        // Set the query for the child table field
        frm.fields_dict['invoice_list'].grid.get_field('quotation').get_query = function(doc, cdt, cdn) {
            // Custom filter logic
            return {
                filters: {
                    'quotation_type': ['in', ['Customer Quotation - Repair','Customer Quotation - R - Revised']],
					'workflow_state': ['in', ['Approved By Customer']],
                    
                }
            };
        };


		frm.fields_dict['sod_quotation'].grid.get_field('quotation').get_query = function(doc, cdt, cdn) {
            // Custom filter logic
            return {
                filters: {
                    'quotation_type': ['in', ['Customer Quotation - Supply','Customer Quotation - S - Revised']],
                    'workflow_state': ['in', ['Approved By Customer']],
                }
            };
        };
    },
});

frappe.ui.form.on('Invoice Creation', {	
	quotation(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (child.quotation) {		    
		    frm.call({
				method: 'cyrix.cyrix_tsl.doctype.invoice_request.invoice_request.get_quotation_details',
				args: {
					quotation:child.quotation,
                    type:"Job Order"
				}
			}).then(r => {
				if (r.message) {
					$.each(r.message, function(i,d) {
						child.job_order_data = d.job_order_data;
					});
					frm.refresh_field('invoice_list');		
				}
			});
		}	
	},
})

frappe.ui.form.on('SOD IV Creation', {
	quotation(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
        if (child.quotation) {		    
		    frm.call({
				method: 'cyrix.cyrix_tsl.doctype.invoice_request.invoice_request.get_quotation_details',
				args: {
					quotation:child.quotation,
                    type:"Supply Order"
				}
			}).then(r => {
				if (r.message) {
					$.each(r.message, function(i,d) {
						child.supply_order_data = d.supply_order_data;
					});
					frm.refresh_field('sod_quotation');		
				}
            })
        }	
	},
})