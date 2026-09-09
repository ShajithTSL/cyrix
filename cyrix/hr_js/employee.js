frappe.ui.form.on('Employee', {
    validate:function(frm){
        frm.trigger("ctc") 
    },
    ctc:function(frm){
        if(!frm.doc.__islocal){
            var ctc = frm.doc.basic + frm.doc.mobile_allowance + frm.doc.car_allowance + 
                frm.doc.food_allowance + frm.doc.housing_allowance + frm.doc.transport_allowance + frm.doc.other_allowances
                - (frm.doc.gosi_deduction + frm.doc.loan)
            frm.set_value('ctc',ctc)
        }
    },
    basic:function(frm){
        frm.trigger("ctc")    
    },
    mobile_allowance:function(frm){
        frm.trigger("ctc")    
    },
    car_allowance:function(frm){
        frm.trigger("ctc")    
    },
    food_allowance:function(frm){
        frm.trigger("ctc")    
    },
    housing_allowance:function(frm){
        frm.trigger("ctc")    
    },
    transport_allowance:function(frm){
        frm.trigger("ctc")    
    },
    other_allowances:function(frm){
        frm.trigger("ctc")    
    },
    gosi_deduction:function(frm){
        frm.trigger("ctc")    
    },
    loan:function(frm){
        frm.trigger("ctc")    
    },
	date_of_joining(frm) {
        var join_date = new Date(frm.doc.date_of_joining);
        var difference = Date.now() - join_date.getTime();
        var diff_date = new Date(difference);
        var exp_years = Math.abs(diff_date.getUTCFullYear() - 1970);
        var tickets = Math.floor(exp_years / 2) * 1;
        frm.set_value("total_tickets", tickets);
        var tickets_available = tickets - frm.doc.used_tickets
	},
	refresh(frm){        
        frm.trigger("company")
	    if(frappe.user.has_role("HR Manager") || frappe.user.has_role("HR User") || frappe.user.has_role("Administrator")){
	        frm.add_custom_button(__("Leave Allocation"), function () {
                frappe.call({
                    method:"cyrix.hr_py.employee.create_leave_allocation",
                    args:{
                        'name':frm.doc.name
                    }
                })
            },__("Create"))
	    }
	    if (frm.doc.employee) {
	        frm.add_custom_button(__("Show Leaves"), function () {
                let today = new Date().toISOString().split('T')[0];
                frappe.call({
                    method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
                    async: false,
                    args: {
                        employee: frm.doc.employee,
                        date: today,
                    },
                    callback: function (r) {
                        let leave_details = r.message["leave_allocation"];
                        let lwps = r.message["lwps"];
                        let allowed_leave_types = Object.keys(leave_details);
                        allowed_leave_types = allowed_leave_types.concat(lwps);
                        let d = new frappe.ui.Dialog({
                            size: "small",
                            fields: [
                                {
                                    fieldname: 'custom_html',
                                    fieldtype: 'HTML'
                                },
                            ],
                        });
                        d.fields_dict.custom_html.wrapper.innerHTML = renderLeaveDetailsTable(leave_details);
                        d.show();
                    },
                });
	        })
        }
	},
    company(frm){
        if(frm.doc.__islocal){
            frappe.call({
                method:"cyrix.hr_py.employee.employee_series",
                callback(r){
                    if(r.message){
                        frm.set_value("employee_number",r.message)
                    }
                }
            })
        }
    },
    create_fnf(frm){
        frappe.db.get_value('Full and Final Settlement',{'employee': frm.doc.name },'name')
            .then(r => {
            if(r.message && Object.entries(r.message).length === 0){
                frappe.route_options = { 
                        'employee':frm.doc.employee,
                        'employee_name': frm.doc.employee_name,
                        'type': "Termination",
                }
                frappe.set_route('Form','Full and Final Settlement','new-full-and-final-settlement-1')
            }
            else{
                frappe.set_route('Form','Full and Final Settlement',r.message.name)
            }
        })
    }
})


// <th style="width: 16%" class="text-right">${__("Used Leaves")}</th>
// <td class="text-right">${value["leaves_taken"]}</td>

function renderLeaveDetailsTable(data) {
    if (jQuery.isEmptyObject(data)) {
        return `<p style="margin-top: 20px;text-align:center;font-size:14px">${__("No leaves have been allocated.")}</p>`;
    }

    let tableHTML = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th style="width: 16%">${__("Leave Type")}</th>
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
                <td class="text-right" style="color: ${color}">${value["remaining_leaves"]}</td>
            </tr>
        `;
    }

    tableHTML += `
            </tbody>
        </table>
    `;
    return tableHTML;
}
