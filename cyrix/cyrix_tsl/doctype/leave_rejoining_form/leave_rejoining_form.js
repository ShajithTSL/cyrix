// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Rejoining Form", {
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
				if (r && r.message) {
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
					frm.get_field("leave_balance").$wrapper.html(renderLeaveDetailsTable(leave_details,frm))
					
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
		frm.trigger("emp_no")				
		frm.fields_dict.unpaid_start_date.datepicker.update({
			minDate: new Date(frm.doc.rejoining_date),
			maxDate: new Date(frm.doc.actual_rejoining_date),
		});					
		frm.fields_dict.unpaid_end_date.datepicker.update({
			minDate: new Date(frm.doc.rejoining_date),
			maxDate: new Date(frm.doc.actual_rejoining_date),
		});    
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