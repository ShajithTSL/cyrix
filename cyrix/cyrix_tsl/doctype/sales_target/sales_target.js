// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Target", {
	refresh(frm) {
        frm.add_custom_button(__('Generate Monthly Targets'), () => {
			if (!frm.doc.from_date) {
				frappe.msgprint(__('Please set From Date first'));
				return;
			}

			frm.call('get_month_ranges')
				.then(() => {
					frm.refresh_field('target_table');
					frappe.msgprint(__('Monthly targets generated successfully'));
				});
		});
	},
});
