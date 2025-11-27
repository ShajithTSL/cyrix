// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Cancellation', {
	refresh: function(frm) {
		frm.set_query('work_order_data', 'cancellation_table', function(doc, cdt, cdn) {
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
					['sales_person', '=', doc.sales_person],
					['is_return', '!=', "1"],
				]
			};
		});
	}
});
