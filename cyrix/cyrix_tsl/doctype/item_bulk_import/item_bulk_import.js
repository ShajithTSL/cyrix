// Item Bulk Import — client script
//
// Upload an Excel sheet + fill in the Maintenance Contract header fields,
// kick off the background import, watch progress live, and get routed
// straight to the resulting Maintenance Contract draft (item_code, model,
// manufacturer, serial_number already filled in on every row).

frappe.ui.form.on('Item Bulk Import', {
	onload(frm) {
		frappe.realtime.on('item_bulk_import_progress', (data) => {
			if (data.name !== frm.doc.name) return;
			frm.dashboard.set_headline_alert(
				__('Importing: {0}/{1} rows processed', [data.processed, data.total])
			);
		});

		frappe.realtime.on('item_bulk_import_done', (data) => {
			if (data.name !== frm.doc.name) return;

			if (data.status === 'Completed' && data.maintenance_contract) {
				frappe.show_alert({ message: __('Maintenance Contract created'), indicator: 'green' });
				frappe.set_route('Form', 'Maintenance Contract', data.maintenance_contract);
			} else {
				frappe.show_alert({ message: __('Import failed — check the error log'), indicator: 'red' });
				frm.reload_doc();
			}
		});
	},

	refresh(frm) {
		if (frm.doc.status === 'Draft' || frm.doc.status === 'Failed') {
			frm.add_custom_button(__('Start Import'), () => {
				if (!frm.doc.import_file) {
					frappe.msgprint(__('Attach the Excel template first'));
					return;
				}
				const required = ['naming_series', 'type', 'customer', 'company', 'branch', 'sales_person', 'incharge'];
				const missing = required.filter((f) => !frm.doc[f]);
				if (missing.length) {
					frappe.msgprint(__('Fill in: {0}', [missing.join(', ')]));
					return;
				}
				frm.save().then(() => {
					frappe.call({
						method: 'cyrix.cyrix_tsl.doctype.item_bulk_import.item_bulk_import.start_import',
						args: { name: frm.doc.name },
						freeze: true,
						freeze_message: __('Queuing import...'),
						callback: () => {
							frappe.show_alert({ message: __('Import queued'), indicator: 'blue' });
							frm.reload_doc();
						},
					});
				});
			}).addClass('btn-primary');
		}

		if (frm.doc.status === 'Processing' || frm.doc.status === 'Queued') {
			frm.dashboard.set_headline_alert(
				__('Import in progress: {0}/{1} rows processed', [frm.doc.processed_rows || 0, frm.doc.total_rows || '?'])
			);
		}

		if (frm.doc.status === 'Completed' && frm.doc.created_maintenance_contract) {
			frm.add_custom_button(__('Open Maintenance Contract'), () => {
				frappe.set_route('Form', 'Maintenance Contract', frm.doc.created_maintenance_contract);
			}).addClass('btn-primary');
		}
	},
});
