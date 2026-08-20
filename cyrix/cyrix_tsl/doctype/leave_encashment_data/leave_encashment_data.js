// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Encashment Data', {
	print:function(frm){
		frm.add_custom_button(__('Print'), function () {
			var f_name = frm.doc.name
			var print_format = "Leave Encashment";
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent(frm.doc.doctype)
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		})
	},

    before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to HR") {
					frappe.call({
						method: 'cyrix.custom_py.email_notification.send_mail_on_leave_encashment',
						args: {
							"name": frm.doc.name,
                            "role": "HR"
						}
					})
				}
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
        if(frm.doc.workflow_state == "Under HR"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to Finance") {
					frappe.call({
						method: 'cyrix.custom_py.email_notification.send_mail_on_leave_encashment',
						args: {
							"name": frm.doc.name,
                            "role": "Finance"
						}
					})
				}
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
	},

	onload: function (frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];
		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
	},
	setup: function (frm) {
		frm.set_query("leave_type", function () {
			return {
				filters: {
					allow_encashment: 1,
				},
			};
		});
		frm.set_query("leave_period", function () {
			return {
				filters: {
					is_active: 1,
				},
			};
		});

		frm.set_query("payable_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && frm.doc.currency != company_currency) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					company: frm.doc.company,
					account_currency: ["in", currencies],
				},
			};
		});
	},
	refresh: function (frm) {
		frm.trigger("print")
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !frappe.user_roles.includes("Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		if (
			frm.doc.docstatus === 1 &&
			frm.doc.pay_via_payment_entry == 1 &&
			frm.doc.status !== "Paid"
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		}

		hrms.leave_utils.add_view_ledger_button(frm);
	},
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger("get_employee_currency"),
				() => frm.trigger("get_leave_details_for_encashment"),
			]);
		}
	},
	company: function (frm) {
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	},
	leave_type: function (frm) {
		frappe.run_serially([
			() => frm.trigger("get_leave_details_for_encashment"),
			() => {
				frappe.call({
					method:"cyrix.hr_py.leave_application.get_leave_balance_on",
					args:{
						employee:frm.doc.employee || '',
						leave_type:frm.doc.leave_type || '',
						date:frappe.datetime.now_date()
					},
					callback(k){
						console.log(k)
						if(k){
							frm.set_value("leave_balance",k.message)					
							frm.set_value("encashment_days",k.message)
							frm.set_value("actual_encashable_days",k.message)
							frm.trigger("calculate_encashable_amount")
						}
					}
				})
			},
		])
		
		
	},
	encashment_date: function (frm) {
		frm.trigger("get_leave_details_for_encashment");
	},
	get_leave_details_for_encashment: function (frm) {
		frm.set_value("actual_encashable_days", 0);
		frm.set_value("encashment_days", 0);

		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type) {
			return frappe.call({
				method: "get_leave_details_for_encashment",
				doc: frm.doc,
				callback: function (r) {
					frm.refresh_fields();
				},
			});
		}
	},

	get_employee_currency: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("currency", r.message);
					frm.refresh_fields();
				}
			},
		});
	},
	make_payment_entry: function (frm) {
		return frappe.call({
			method: "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},
	encashment_days : function(frm){
		frm.trigger("calculate_encashable_amount")
	},
	calculate_encashable_amount:function(frm){
		if(frm.doc.employee){
			frappe.call({
				method:"cyrix.cyrix_tsl.doctype.leave_encashment_data.leave_encashment_data.per_day_salary",
				args:{
					employee:frm.doc.employee,
				},
				callback(r){
					if(r){
						var encashable_amount  = frm.doc.encashment_days * r.message
						frm.set_value("encashment_amount",encashable_amount)
					}
				}
			})
		}
	},
	validate(frm){
		frm.trigger("calculate_encashable_amount")
	}
});
