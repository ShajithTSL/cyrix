// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

function set_late_days_description(frm) {
    const days = cint(frm.doc.late_days);
    let desc = "";

    if (days < 0) {
        const n = Math.abs(days);
        const msg = frm.doc.docstatus === 1
            ? __("Employee rejoined <b>{0}</b> day(s) early. These {0} day(s) are paid through an Additional Salary.", [n])
            : __("Employee rejoined <b>{0}</b> day(s) early. On submission, an Additional Salary will be created to pay these {0} day(s).", [n]);
        const link = frm.doc.early_join_additional_salary
            ? `<br>${__("Additional Salary")}: ${frappe.utils.get_form_link("Additional Salary", frm.doc.early_join_additional_salary, true)}`
            : "";
        desc = `<span style="color: var(--green-600)">${msg}${link}</span>`;
    } else if (days > 0) {
        desc = `<span style="color: var(--red-600)">${__("Employee rejoined <b>{0}</b> day(s) late.", [days])}</span>`;
    }

    frm.set_df_property("late_days", "description", desc);
}
frappe.ui.form.on("Leave Rejoining Form", {
    late_days(frm){
		frm.trigger("set_late_days_description")
	},
    before_submit(frm) {
        if (cint(frm.doc.late_days) >= 0) return;

        if (!frappe.user.has_role("HR Manager")) {
            frappe.throw(__("Only HR Manager can submit an early rejoining."));
        }

        return new Promise((resolve, reject) => {
            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.leave_rejoining_form.leave_rejoining_form.get_early_join_preview",
                args: { doc: frm.doc },
                freeze: true,
                freeze_message: __("Calculating early-join payment..."),
            }).then((r) => {
                const d = r.message;
                if (!d) return resolve();

                const cur = (v) => format_currency(v, d.currency);
                const esc = (v) => frappe.utils.escape_html(String(v ?? ""));
                const row = (label, value, strong) => `
                    <tr>
                        <td class="text-muted" style="width:45%">${label}</td>
                        <td>${strong ? `<b>${value}</b>` : value}</td>
                    </tr>`;

                const html = `
                    <p>${__("The employee rejoined <b>{0}</b> day(s) before the leave end date. "
                        + "The following Additional Salary will be created on submit:", [d.early_days])}</p>
                    <table class="table table-bordered" style="margin-bottom:0">
                        <tbody>
                            ${row(__("Employee"), `${esc(d.employee)} - ${esc(d.employee_name)}`)}
                            ${row(__("Company"), esc(d.company))}
                            ${row(__("Salary Component"), esc(d.salary_component))}
                            ${row(__("Payroll Date"), frappe.datetime.str_to_user(d.payroll_date))}
                            ${row(__("Early Joined Days"), d.early_days)}
                            ${row(__("Monthly Salary") + ` <small>(${esc(d.salary_basis)})</small>`, cur(d.monthly_base))}
                            ${row(__("Per-Day Salary (Monthly / {0})", [d.days_basis]), cur(d.per_day_salary))}
                            ${row(__("Additional Salary Amount"), cur(d.amount), true)}
                        </tbody>
                    </table>`;

                let approved = false;
                const dialog = new frappe.ui.Dialog({
                    title: __("Confirm Additional Salary – Early Rejoining"),
                    fields: [
                        { fieldtype: "HTML", fieldname: "summary_html" },
                        {
                            fieldtype: "Small Text",
                            fieldname: "custom_remarks",
                            label: __("Remarks"),
                            reqd: 1,
                            default: frm.doc.early_join_remarks || d.default_remarks,
                        },
                    ],
                    primary_action_label: __("Approve & Submit"),
                    primary_action(values) {
                        approved = true;
                        frm.doc.early_join_approved = 1;                    // sent with the submit request
                        frm.doc.early_join_remarks = values.custom_remarks; // mapped to Additional Salary
                        dialog.hide();
                        resolve();
                    },
                    secondary_action_label: __("Cancel"),
                    secondary_action() { dialog.hide(); },
                });

                dialog.fields_dict.summary_html.$wrapper.html(html);
                dialog.onhide = () => {
                    if (!approved) reject(__("Submission cancelled"));
                };
                dialog.show();
            }, reject);
        });
    },
	actual_rejoining_date(frm) {
		frappe.call({
			method: "cyrix.cyrix_tsl.doctype.leave_rejoining_form.leave_rejoining_form.get_number_of_leave_days",
			args: {
				employee: frm.doc.emp_no,
				leave_type: frm.doc.leave_type || null,
				from_date: frm.doc.rejoining_date,
				to_date: frappe.datetime.add_days(frm.doc.actual_rejoining_date, 0),
			},
			callback: function (r) {	
				frm.fields_dict.unpaid_start_date.datepicker.update({
					minDate: new Date(frm.doc.rejoining_date),
					maxDate: new Date(frappe.datetime.add_days(frm.doc.actual_rejoining_date, -1)),
				});					
				frm.fields_dict.unpaid_end_date.datepicker.update({
					minDate: new Date(frm.doc.rejoining_date),
					maxDate: new Date(frappe.datetime.add_days(frm.doc.actual_rejoining_date, -1)),
				});
				if (r) {
					var late_days = r.message - 1
					frm.set_value("late_days", late_days);
					if(late_days > frm.doc.eligible_days){
						frm.set_value("unpaid_start_date",null)
						frm.set_value("unpaid_end_date",frappe.datetime.add_days(frm.doc.actual_rejoining_date, -1))
					}	
				}
				else{
					frm.set_value("late_days", 0);
					frm.set_value("unpaid_start_date",null)
					frm.set_value("unpaid_end_date",null)
				}
			},
		});
		setTimeout(() => set_late_days_description(frm), 300);
	},
	emp_no(frm){
		if(frm.doc.emp_no){
			let today = new Date().toISOString().split('T')[0];
			frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
				async: false,
				args: {
					employee: frm.doc.emp_no,
					date: today,
				},
				callback: function (r) {
					let leave_details = r.message["leave_allocation"];
					let lwps = r.message["lwps"];
					if (frm.doc.docstatus == 0) {
						frm.get_field("leave_balance").$wrapper.html(renderLeaveDetailsTable(leave_details,frm))
					}
					let allowed_leave_types = Object.keys(leave_details);
					allowed_leave_types = allowed_leave_types.concat(lwps);
					frm.set_query("leave_type", function () {
						return {
							filters: [["leave_type_name", "in", allowed_leave_types]],
						};
					});
				},
			});
		}	
	},
	leave_type(frm){
		frm.trigger("emp_no")
		frm.trigger("actual_rejoining_date")
	},
	refresh(frm){	
		frappe.run_serially([
			() => frm.trigger("emp_no"),
			() => {
				frm.fields_dict.unpaid_start_date.datepicker.update({
					minDate: new Date(frm.doc.rejoining_date),
					maxDate: new Date(frm.doc.actual_rejoining_date),
				});	
			},
			() => {
				frm.fields_dict.unpaid_end_date.datepicker.update({
					minDate: new Date(frm.doc.rejoining_date),
					maxDate: new Date(frm.doc.actual_rejoining_date),
				}); 
			},
			() => setTimeout(() => set_late_days_description(frm), 300),
		]);
	}
})



function renderLeaveDetailsTable(data, frm) {
    if (jQuery.isEmptyObject(data)) {
        return `<p style="margin-top: 30px;">${__("No leaves have been allocated.")}</p>`;
    }

    let tableHTML = `
        <table class="table table-bordered small">
            <thead>
                <tr>
                    <th style="width: 16%">${__("Leave Type")}</th>
                    <th style="width: 16%" class="text-right">${__("Used Leaves")}</th>
                    <th style="width: 16%" class="text-right">${__("Available Leaves")}</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const [key, value] of Object.entries(data)) {
        let color = parseInt(value["remaining_leaves"]) > 0 ? "green" : "red";
        tableHTML += `
            <tr>
                <td>${key}</td>
                <td class="text-right">${value["leaves_taken"]}</td>
                <td class="text-right" style="color: ${color}">${value["remaining_leaves"]}</td>
            </tr>
        `
		if(key == frm.doc.leave_type && frm.doc.docstatus == 0){
			frm.set_value("eligible_days",parseInt((value["remaining_leaves"]),10))
		}
    }

    tableHTML += `
            </tbody>
        </table>
    `;
    return tableHTML;
}