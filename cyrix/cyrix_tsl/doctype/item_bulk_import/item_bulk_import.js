// Item Bulk Import — client script
//
// Upload an Excel sheet + fill in the Maintenance Contract header fields,
// kick off the background import, watch progress live, and get routed
// straight to the resulting Maintenance Contract draft (item_code, model,
// manufacturer, serial_number already filled in on every row).

frappe.ui.form.on('Item Bulk Import', {
    set_department: function(frm) {
		if (frm.doc.company && frm.doc.branch) {
			frappe.db.get_value("Cost Center", {"company": frm.doc.company, "branch": frm.doc.branch, "is_repair": 1}, "name", function(value) {
				frm.set_value("department", value.name);
			});
		}
	},

	set_branch: function(frm) {
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
		else if (frm.doc.company) {
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

	company: function(frm){
		frm.trigger("set_department");
		frm.trigger("set_branch");
	},

    branch: function(frm){
        frm.trigger("type")
		frm.trigger("set_department");
    },
    type: function(frm){
        const naming_series = {
            "AMC": {
                "Kuwait": "AMC-K.YY.-",
                "Riyadh": "AMC-R.YY.-",
                "Jeddah": "AMC-J.YY.-",
                "Dubai": "AMC-DU.YY.-",
            },
            "CMC": {
                "Kuwait": "CMC-K.YY.-",
                "Riyadh": "CMC-R.YY.-",
                "Jeddah": "CMC-J.YY.-",
                "Dubai": "CMC-DU.YY.-",
            },
        }
        if (frm.doc.type && frm.doc.branch) {
            const series = naming_series[frm.doc.type][frm.doc.branch];
            if (series) {
                frm.set_value("custom_naming_series", series);
            }
        }
    },
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

    import_file: function(frm) {
        if ((frm.doc.status === 'Draft' || frm.doc.status === 'Failed') && (frm.doc.import_file)) {
			frm.add_custom_button(__('Start Import'), () => {
				if (!frm.doc.import_file) {
					frappe.msgprint(__('Attach the Excel template first'));
					return;
				}
				const required = ['custom_naming_series', 'type', 'customer', 'company', 'branch', 'sales_person', 'incharge'];
				const missing = required.filter((f) => !frm.doc[f]);
				if (missing.length) {
					frappe.msgprint(__('Fill in: {0}', [missing.join(', ')]));
					return;
				}
				
                frappe.call({
                    method: 'cyrix.cyrix_tsl.doctype.item_bulk_import.item_bulk_import.start_import',
                    args: { name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Queuing import...'),
                    callback: () => {
                        frappe.show_alert({ message: __('Import queued'), indicator: 'blue' });
                        window.location.reload();
                    },
                });
			}).addClass('btn-primary');
		}
        
        frm.trigger('download_file');
    },

    download_file: function(frm) {
        if (!frm.doc.import_file){
            frm.add_custom_button(__("Download Excel"), function () {
                window.open(
                    `/api/method/cyrix.cyrix_tsl.doctype.item_bulk_import.item_bulk_import.download_excel`
                );
            }).addClass('btn-primary');
        }
    },

	refresh(frm) {
		frm.trigger('import_file');
		frm.trigger('download_file');

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
