// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt



frappe.ui.form.on('Maintenance Contract Item', {	
	item_name: function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
        if(row.item_name && !row.description && !row.item_code){
            row.description = row.item_name
            frm.refresh_field("items")
        }
    },
	jo: function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		frappe.call({
			method: "cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.create_job_order",
			args: {
				source: frm.doc.name,
				row_name: row.name
			},
			callback: function(r) {
				if (r.message) {
					var doc = frappe.model.sync(r.message);
					frappe.set_route("Form", doc[0].doctype, doc[0].name);
				}
			}
		})
	}
})
const LARGE_CONTRACT_THRESHOLD = 50; 

frappe.ui.form.on("Maintenance Contract", {
	onload(frm) {
		frappe.realtime.on('maintenance_contract_submitted', (data) => {
			if (data.name !== frm.doc.name) return;

			if (data.status === 'success') {
				frappe.show_alert({ message: __('Maintenance Contract submitted'), indicator: 'green' });
			} else {
				frappe.show_alert({ message: __('Submission failed — check the Error Log'), indicator: 'red' });
			}
			frm.reload_doc();
		});
	},

	html(frm) {
        if (!frm.doc.name) return;

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Quotation",
                filters: {
                    maintenance_contract: frm.doc.name,
					docstatus: 1,
					workflow_state: "Approved by Customer",
					quotation_type: ["in",["Customer Quotation - MC","Customer Quotation - MC - Revised"]]
                },
                fields: ["name", "transaction_date", "workflow_state as status"],
                order_by: "transaction_date desc"
            },
            callback: function(q_res) {

                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Sales Invoice",
                        filters: {
                            maintenance_contract: frm.doc.name,
							docstatus: 1
                        },
                        fields: ["name", "posting_date", "status"],
                        order_by: "posting_date desc"
                    },
                    callback: function(si_res) {

                        // 🔹 Quotations Table
                        let html = `<h5>Quotations</h5>`;
                        if (q_res.message.length) {
                            html += `
                                <table class="table table-bordered table-sm">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Date</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;

                            q_res.message.forEach(q => {
                                html += `
                                    <tr>
                                        <td width="35%">
                                            <a href="/app/quotation/${q.name}" target="_blank">
                                                ${q.name}
                                            </a>
                                        </td>
                                        <td width="35%">${q.transaction_date ? frappe.datetime.str_to_user(q.transaction_date) : ""}</td>
                                        <td width="30%">${q.status}</td>
                                    </tr>
                                `;
                            });

                            html += `</tbody></table>`;
                        } else {
                            html += `<p>No Quotations found</p>`;
                        }

                        // 🔹 Sales Invoices Table
                        html += `<h5>Sales Invoices</h5>`;
                        if (si_res.message.length) {
                            html += `
                                <table class="table table-bordered table-sm">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Date</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;

                            si_res.message.forEach(si => {
                                html += `
                                    <tr>
                                        <td width="35%">
                                            <a href="/app/sales-invoice/${si.name}" target="_blank">
                                                ${si.name}
                                            </a>
                                        </td>
                                        <td width="35%">${si.posting_date ? frappe.datetime.str_to_user(si.posting_date) : ""}</td>
                                        <td width="30%">${si.status}</td>
                                    </tr>
                                `;
                            });

                            html += `</tbody></table>`;
                        } else {
                            html += `<p>No Sales Invoices found</p>`;
                        }

                        frm.fields_dict.html.$wrapper.html(html);
                    }
                });

            }
        });
	},

	create_schedule: function(frm) {
		frm.clear_table("schedule");
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.create_schedule",
				args: {
					from_date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					interval: frm.doc.interval
				},
				callback: function(r) {
					$.each(r.message, function(index, schedule) {
						frappe.model.add_child(frm.doc, "Maintenance Schedule", "schedule");
						var row = frm.doc.schedule[frm.doc.schedule.length - 1];
						row.date = schedule;
						frm.refresh_field("schedule");
					});
					frappe.msgprint(__("Maintenance Schedule created successfully."));
				}
			})
	},

	refresh: function(frm) {
		frm.trigger("html");
		$('[data-fieldname="create_schedule"] button').css({'color':'white', 'background':'linear-gradient(135deg, #015ca3 0%,#00adef 100%)'});

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Service Call"), function() {
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.create_service_call_form",
					args: {
						source: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				})
			}, __("Create") );

			frm.add_custom_button(__('Internal Quotation'), function(){
                frappe.call({
                    method: "cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.create_qtn",
                    args: {
                        "source":frm.doc.name
                    },
                    callback: function(r) {
                        if(r.message) {
                            var doc = frappe.model.sync(r.message);
                            frappe.set_route("Form", doc[0].doctype, doc[0].name);
                        }
                    }
                });
			}, ('Create'))
		}
				const item_count = (frm.doc.items || []).length;
		const is_large = item_count > LARGE_CONTRACT_THRESHOLD;

		if (frm.doc.docstatus === 0 && is_large && frm.doc.queue_status !== 'Queued') {
			// Override the primary "Submit" action for large contracts
			frm.page.set_primary_action(__('Queue for Submission'), () => {
				frappe.confirm(
					__('This contract has {0} items and may take a while to process. It will be submitted in the background — continue?', [item_count]),
					() => {
						frm.save().then(() => {
							frappe.call({
								method: 'cyrix.cyrix_tsl.doctype.maintenance_contract.maintenance_contract.queue_submit',
								args: { name: frm.doc.name },
								freeze: true,
								freeze_message: __('Queuing submission...'),
								callback: () => {
									frappe.show_alert({ message: __('Submission queued — you can leave this page'), indicator: 'blue' });
									frm.reload_doc();
								},
							});
						});
					}
				);
			});
		}

		if (frm.doc.queue_status === 'Queued') {
			frm.dashboard.set_headline_alert(
				__('Submission is processing in the background. This page will update automatically when it finishes.')
			);
		} else if (frm.doc.queue_status === 'Failed') {
			frm.dashboard.set_headline_alert(
				__('Background submission failed. Check the Error Log, then try again.'),
				'red'
			);
		}
	},

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
            },
            "CMC": {
                "Kuwait": "CMC-K.YY.-",
                "Riyadh": "CMC-R.YY.-",
            },
        }
        if (frm.doc.type && frm.doc.branch) {
            const series = naming_series[frm.doc.type][frm.doc.branch];
            if (series) {
                frm.set_value("naming_series", series);
            }
        }
    },
    setup: function (frm) {
        frm.trigger("setup_query");
		$('[data-fieldname="create_schedule"] button').css({'color':'white', 'background':'linear-gradient(135deg, #015ca3 0%,#00adef 100%)'});

    },
    setup_query: function (frm) {
		frm.fields_dict['items'].grid.get_field('item_code').get_query = function (frm, cdt, cdn) {
			var child = locals[cdt][cdn];
			var d = {};
			if (child.model) {
				d['model'] = child.model;
			}
			if (child.manufacturer) {
				d['mfg'] = child.manufacturer;
			}
			if (child.item_group) {
				d['item_group'] = child.item_group;
			}
			return {
				filters: d
			}
		}
        frm.set_query("address", function () {
			return {
				filters: [
					["Dynamic Link", "parenttype", "=", "Address"],
					["Dynamic Link", "link_name", "=", frm.doc.customer],
					["Dynamic Link", "link_doctype", "=", "Customer"]

				]
			}
		});
		frm.trigger("set_branch");

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
	},
    address: function (frm) {
        // to set address_display
		if (frm.doc.address) {
			frappe.call({
				method: 'frappe.contacts.doctype.address.address.get_address_display',
				args: {
					"address_dict": frm.doc.address
				},
				callback: function (r) {
					frm.set_df_property("customer_address", "options", "<b>Customer Address</b> <br>" + r.message + "<br>");
					frm.refresh_fields();
				}
			});
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
