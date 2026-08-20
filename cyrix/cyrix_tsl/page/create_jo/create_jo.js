// Page: create-job-order-entry
//
// This replaces direct use of the "Create Job Order" Single DocType as an
// intake form. It renders the EXACT same form (same fields, sections,
// column breaks, child-table grids and link queries) but against a
// private, in-memory, never-saved instance of the doctype instead of the
// one shared Single record.
//
// Why: "Create Job Order" is issingle=1, so there is only ONE row in the
// database for it. Two problems followed from that:
//   1. Frappe auto-saves a Single DocType's form when it goes dirty and the
//      user navigates away. Any user without "write" on the DocType (i.e.
//      everyone except System Manager, per the current permissions table)
//      hit a PermissionError the moment a fetch_from field populated and
//      they clicked away.
//   2. Two people filling this form at the same time were silently editing
//      the same shared row.
// A local unsaved doc has neither problem: nothing is ever persisted to
// "Create Job Order" itself, so no write/create permission on it is
// needed, and each user's draft is fully private to their browser tab.
//
// The actual "save" your process cares about already happens via the
// whitelisted methods create_job_order_data / update_job_order_data in
// create_job_order.py (both use ignore_permissions=True to create the real
// "Job Order Data" document). None of that server-side code needs to
// change -- it already just reads a JSON blob of field values.

frappe.pages['create-jo'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Create Job Order',
		single_column: true
	});

	frappe.create_job_order_entry = new JobOrderEntry(page);
};

class JobOrderEntry {
	constructor(page) {
		this.page = page;
		this.render();
	}

	render() {
		// Loads (and caches) the DocType's field metadata. Requires only
		// READ permission on "Create Job Order" -- see README.
		frappe.model.with_doctype('Create Job Order', () => {
			this.build_form();
		});
	}

	build_form() {
		// A fresh local, unsaved instance of the doctype. This is a pure
		// client-side object living in `locals` -- it is never fetched
		// from or written to the real Single record.
		let doc = frappe.model.get_new_doc('Create Job Order');

		// Pass only (doctype, parent, in_form) to the constructor -- the
		// 4th positional arg means different things across Frappe versions
		// (doctype layout vs docname), so the doc is loaded explicitly via
		// refresh(doc.name) below instead of relying on it.
		this.frm = new frappe.ui.form.Form(
			'Create Job Order',
			this.page.body,
			true
		);

		// A lot of the existing "Create Job Order" client script reads and
		// writes `cur_frm` directly (button handlers, child table logic),
		// so point the global at this form for it to keep working as-is.
		cur_frm = this.frm;

		this.frm.doc = doc;
		this.frm.refresh(doc.name);

		// Belt-and-braces: this form must never attempt a real save.
		this.frm.disable_save();
	}

	reset() {
		// Used by the trash-icon button: discard the current in-memory
		// draft and start a clean one. (The original script called
		// frappe.model.delete_doc on the real Single here, which needed
		// delete permission and doesn't make sense for a Single record.)
		if (this.frm && this.frm.docname) {
			frappe.model.clear_doc(this.frm.doctype, this.frm.docname);
		}
		this.page.body.empty();
		this.build_form();
	}
}

// ---------------------------------------------------------------------
// Below this line is your existing "Create Job Order" client script,
// unchanged apart from the trash-button handler at the bottom of
// `refresh`. It is doctype-scoped (frappe.ui.form.on("Create Job Order",
// ...)), so it fires for this page's local form exactly like it fired for
// the old Single form view.
//
// NOTE: if this script is also still registered as the DocType's Client
// Script / doctype_js, keep only ONE copy loaded to avoid double-binding
// events. Either remove it from the DocType and keep it only here, or
// delete this copy and instead load the DocType's existing script file
// into this page (e.g. via frappe.require) -- your choice, just don't run
// both.
// ---------------------------------------------------------------------

frappe.ui.form.on("Create Job Order", {
	branch: function (frm) {
		if (!frm.doc.branch) {
			frm.set_value("repair_warehouse", null);
			return
		}
		frappe.db.get_value('Warehouse', { 'is_repair_warehouse': 1, 'company': frappe.defaults.get_default("company"), "name": ["like", "%" + frm.doc.branch + "%"] }, 'name', (values) => {
			frm.set_value("repair_warehouse", values.name);
		});
	},

	onload: function (frm) {
		frm.trigger("setup_query");
	},

	setup: function (frm) {
		frm.trigger("setup_query");
	},
	setup_query: function (frm) {
		// child table set_query
		frm.fields_dict['received_equipment'].grid.get_field('item_code').get_query = function (frm, cdt, cdn) {
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
		frm.set_query("repair_warehouse", function () {
			return {
				filters: [
					["company", "=", frappe.defaults.get_default("company")],
					["is_repair_warehouse", "=", 1]
				]
			}
		});
		const branchMap = frappe.boot.company_branches;

		if (branchMap[frappe.defaults.get_default("company")]) {
			const branches = branchMap[frappe.defaults.get_default("company")];

			// If only one branch exists, auto-set it
			if (branches.length === 1) {
				frm.set_value("branch", branches[0]);
				frm.set_df_property("branch", "read_only", 1);
			}
			else {
				frm.set_value("branch", frappe.defaults.get_default('branch'));
			}
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frappe.defaults.get_default("company")]]
					]
				};
			});
		}

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

	update_or_create_jo: function (frm) {
		if (frm.doc.job_order_data) {
			if (frm.doc.is_returned_unit) {
				// If job_order_data exists Update the existing Job Order
				frm.add_custom_button(__("Update Job Order"), function () {
					frappe.call({
						method: "cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.update_job_order_data",
						freeze: true,
						freeze_message: __("Please Wait, Job Order Updation is in Progress ..."),
						args: {
							dict: cur_frm.doc,
							doc_type: "Job Order Data",
							doc_name: cur_frm.doc.job_order_data
						},
						callback(r) {
							if (r) {
								// On success, reset the draft
								frappe.create_job_order_entry.reset();
							}
						}
					})
				})
				frm.remove_custom_button(__("Create Job Order")); // Remove the "Create Job Order" button to avoid duplication/conflict
				frm.remove_custom_button(__("Create Board Level JO")); // Remove the "Create Board Level JO" button to avoid duplication/conflict
			}
			else {
				// If job_order_data exists Update the existing Job Order
				frm.add_custom_button(__("Create Board Level JO"), function () {
					frappe.call({
						method: "cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.create_job_order_data",
						freeze: true,
						freeze_message: __("Please Wait, Job Order Creation is in Progress ..."),
						args: {
							dict: cur_frm.doc
						},
						callback(r) {
							if (r) {
								// On success, reset the draft
								frappe.create_job_order_entry.reset();
							}
						}
					})
				})
				frm.remove_custom_button(__("Create Job Order")); // Remove the "Create Job Order" button to avoid duplication/conflict
				frm.remove_custom_button(__("Update Job Order")); // Remove the "Update Job Order" button since it's not applicable yet
			}
		}
		else {
			// If job_order_data does not exist Create a New Job Order
			frm.add_custom_button(__("Create Job Order"), function () {
				let has_empty_complaint = false;

				(frm.doc.received_equipment || []).forEach(row => {

					let is_empty =
						!row.no_power &&
						!row.no_output &&
						!row.not_working &&
						!row.no_display &&
						!row.no_communication &&
						!row.supply_voltage &&
						!row.touchkeypad_not_working &&
						!row.no_backlight &&
						!row.error_code &&
						!row.short_circuit &&
						!row.overload_overcurrent &&
						!row.other;

					if (is_empty) {
						has_empty_complaint = true;
					}
				});

				let create_job_order = function () {

					frappe.call({
						method: "cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.create_job_order_data",
						freeze: true,
						freeze_message: __("Please Wait, Job Order Creation is in Progress ..."),
						args: {
							dict: cur_frm.doc
						},
						callback(r) {

							if (r.message) {
								// On success, reset the draft
								frappe.create_job_order_entry.reset();
							}
						}
					});
				};

				if (has_empty_complaint) {

					frappe.confirm(
						__("Some rows do not have complaints specified. Are you sure to continue?"),
						function () {
							create_job_order();
						}
					);

				} else {

					create_job_order();
				}
			});
			frm.remove_custom_button(__("Update Job Order")); // Remove the "Update Job Order" button since it's not applicable yet
		}
	},


	refresh(frm) {
		frm.disable_save();

		frappe.run_serially([
			() => frm.set_value("company", frappe.defaults.get_default("company")),

			() => frm.trigger("setup_query"),

			() => frm.trigger("branch"),

			() => frm.trigger("update_or_create_jo"),

			() => {
				if (frappe.route_options.job_order_data) {
					frm.set_value("job_order_data", frappe.route_options.job_order_data);
					frappe.route_options = null;
				}
			},

			() => {
				frm.add_custom_button(__('<i class="fa fa-trash"></i>'), function () {
					// Discard the in-memory draft and start a new one.
					// (No longer deletes the real Single record.)
					frappe.confirm(__("Discard this draft and start a new one?"), function () {
						frappe.create_job_order_entry.reset();
					});
				})
			}
		]);
	},

	job_order_data: function (frm) {
		frm.trigger("refresh")
		if (frm.doc.job_order_data) { // if the job_order_data is present, fetch the details
			frappe.call({
				method: 'cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.get_jo_details',
				args: {
					"jo": frm.doc.job_order_data,
				},
				callback(r) {
					if (r.message) {
						for (var i = 0; i < r.message.length; i++) {
							if (frm.doc.is_returned_unit) {
								var childTable = cur_frm.add_child("received_equipment");
								childTable.item_code = r.message[i]['item_code']
								childTable.item_name = r.message[i]["item_name"]
								childTable.description = r.message[i]["description"] || r.message[i]["item_name"]
								childTable.manufacturer = r.message[i]["mfg"]
								childTable.serial_no = r.message[i]["serial_no"]
								childTable.uom = r.message[i]["uom"]
								if (r.message[i]["serial_no"]) {
									childTable.has_serial_no = 1
								}
								else {
									childTable.has_serial_no = 0
								}

								childTable.model = r.message[i]["model_no"]
								childTable.type = r.message[i]["type"]
								childTable.qty = r.message[i]["qty"]
							}
							frm.doc.sales_person = r.message[i]["sales_person"],
								frm.doc.customer = r.message[i]["customer"],
								frm.doc.address = r.message[i]["address"],
								frm.doc.incharge = r.message[i]["incharge"],
								frm.doc.incharge_name = r.message[i]["incharge_name"],
								frm.doc.incharge_email = r.message[i]["incharge_email"],
								frm.doc.incharge_phone_no = r.message[i]["incharge_phone_no"],
								frm.doc.branch = r.message[i]["branch"]
							frm.doc.company = r.message[i]["company"]
							frm.doc.repair_warehouse = r.message[i]["repair_warehouse"]
							cur_frm.refresh_fields();
							frappe.run_serially([
								() => frm.trigger("address")
							])
						}
					}
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
						frm.set_value("sales_person", r.message[1][0])
					}
				}
			}
		});
	},
});

frappe.ui.form.on("Received Equipment", {
	item_name: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn]
		if (row.item_name) {
			row.description = row.item_name
			frm.refresh_field("received_equipment")
		}
	},
})