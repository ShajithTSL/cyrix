// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Invoice Request", {
	company: function(frm){
		if (frm.doc.company){
			frm.set_query("branch", function () {
				return {
					"filters": {
						"company": ["in", frm.doc.company]
					}
				};
			});
		}
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
	before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to Finance") {
					frm.call({
						method: 'trigger_mail_on_invoice_request',
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
	refresh: function(frm) {
		$('[data-fieldname="attach"] button').css({'color':'white', 'background':'linear-gradient(135deg, #015ca3 0%,#00adef 100%)'});
	},
    onload: function(frm) {
		$('[data-fieldname="attach"] button').css({'color':'white', 'background':'linear-gradient(135deg, #015ca3 0%,#00adef 100%)'});
        // Set the query for the child table field
        frm.fields_dict['invoice_list'].grid.get_field('quotation').get_query = function(doc, cdt, cdn) {
            // Custom filter logic
            return {
                filters: {
                    'quotation_type': ['in', ['Customer Quotation - Repair','Customer Quotation - R - Revised']],
					'workflow_state': ['in', ['Approved by Customer']],
                    
                }
            };
        };


		frm.fields_dict['sod_quotation'].grid.get_field('quotation').get_query = function(doc, cdt, cdn) {
            // Custom filter logic
            return {
                filters: {
                    'quotation_type': ['in', ['Customer Quotation - Supply','Customer Quotation - S - Revised']],
                    'workflow_state': ['in', ['Approved by Customer']],
                }
            };
        };
    },
});

frappe.ui.form.on('Invoice Creation', {
	quotation(frm, cdt, cdn) {
        let child = locals[cdt][cdn];

        if (!child.quotation) {
            return;
        }

        // Validate the quotation, including pasted values
        frappe.db.get_value(
            'Quotation',
            child.quotation,
            ['quotation_type', 'workflow_state', 'invoiced']
        ).then(r => {

            let q = r.message;

            let valid_types = [
				'Customer Quotation - Repair','Customer Quotation - R - Revised'
            ];

            let valid =
                q &&
                valid_types.includes(q.quotation_type) &&
                q.workflow_state === 'Approved by Customer' &&
                flt(q.invoiced) < 100;
			
			console.log(q)
			console.log(valid_types)
			console.log(valid)
			console.log(valid_types.includes(q.quotation_type))
            // Invalid quotation
            if (!valid) {
                frappe.msgprint({
                    title: __('Invalid Quotation'),
                    message: __(
                        'Quotation {0} does not meet the required conditions.',
                        [child.quotation]
                    ),
                    indicator: 'red'
                });

                // Remove the pasted/invalid quotation
                frappe.model.set_value(cdt, cdn, 'quotation', '');

                return;
            }

		    frm.call({
				method: 'cyrix.cyrix_tsl.doctype.invoice_request.invoice_request.get_quotation_details',
				args: {
					quotation:child.quotation,
                    type:"Job Order"
				}
			}).then(r => {
				if (r.message) {
					$.each(r.message, function(i,d) {
						let child = frm.add_child('invoice_list');
						child.job_order_data = d.job_order_data;
					});
					frm.refresh_field('invoice_list');		
				}
			});
        });
    }
})

frappe.ui.form.on('SOD IV Creation', {
	quotation(frm, cdt, cdn) {
        let child = locals[cdt][cdn];

        if (!child.quotation) {
            return;
        }

        // First validate the pasted/entered quotation
        frappe.db.get_value(
            'Quotation',
            child.quotation,
            ['quotation_type', 'workflow_state', 'invoiced']
        ).then(r => {

            let q = r.message;

            // Check whether quotation satisfies the Link field filters
            let valid_types = ['Customer Quotation - Supply','Customer Quotation - S - Revised'];

            let valid =
                q &&
                valid_types.includes(q.quotation_type) &&
                q.workflow_state === 'Approved by Customer' &&
                flt(q.invoiced) < 100;

            if (!valid) {

                frappe.msgprint({
                    title: __('Invalid Quotation'),
                    message: __(
                        'Quotation {0} does not meet the required conditions.',
                        [child.quotation]
                    ),
                    indicator: 'red'
                });

                // Clear the invalid pasted quotation
                frappe.model.set_value(cdt, cdn, 'quotation', '');

                return;
            }

			frm.call({
				method: 'cyrix.cyrix_tsl.doctype.invoice_request.invoice_request.get_quotation_details',
				args: {
					quotation:child.quotation,
                    type:"Supply Order"
				}
			}).then(r => {
				if (r.message) {
					$.each(r.message, function(i,d) {
						let child = frm.add_child('sod_quotation');
						child.supply_order_data = d.supply_order_data;
					});
					frm.refresh_field('sod_quotation');		
				}
            })
        });
    }
})