// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Full and Final Settlement", {
	before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to Finance") {
					frappe.call({
						method: 'cyrix.custom_py.email_notification.send_mail_on_fnf',
						args: {
							"name": frm.doc.name
						}
					})
				}
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
        
        if (["Under Finance"].includes(frm.doc.workflow_state) && frm.selected_workflow_action === "Reject") {
            const values = await new Promise((resolve, reject) => {
                frappe.prompt(
                    [
                        {
                            fieldname: "reason",
                            fieldtype: "Small Text",
                            label: "Rejection Reason",
                            reqd: 1
                        }
                    ],
                    resolve,
                    "Rejection Reason",
                    "Submit"
                );
                frappe.dom.unfreeze();
            });

            await frappe.call({
                method: "cyrix.custom_py.email_notification.send_fnf_rejection_mail",
                args: {
                    name: frm.doc.name,
                    rejection_reason: values.reason
                }
            });
        }
	},

    check_for_total_working_days : function(frm){
        if(frm.doc.company == "Cyrix TSL - Kuwait" && frm.doc.no_of_days_worked > frm.doc.total_working_days){
            frm.set_value("no_of_days_worked",frm.doc.total_working_days)
        }
    },
    
    type(frm){
        frm.trigger("gratuity_calculation")  
    },

    gratuity_calculation(frm){
        if(frm.doc.employee && frm.doc.docstatus == 0){
            frappe.call({
                method:"cyrix.cyrix_tsl.doctype.full_and_final_settlement.full_and_final_settlement.gratuity_amount",
                args:{
                    employee:frm.doc.employee,
					date:frm.doc.last_day_of_work || ''
                },
                callback(r){
                    if(r){
                        if(frm.doc.type == "Resignation"){
                            var resignation_amount = Math.round(r.message.resignation_amount* 100) / 100
                            var res_gratuity_amount = Math.round(frm.doc.gratuity_amount* 100) / 100
                            if(resignation_amount != res_gratuity_amount){
                                frm.set_value("gratuity_amount",r.message.resignation_amount)
                            }
                            frm.set_value("gratuity_days",r.message.resignation_days)
                        }
                        
                        if(frm.doc.type == "Termination"){
                            var termination_amount = Math.round(r.message.termination_amount* 100) / 100
                            var term_gratuity_amount = Math.round(frm.doc.gratuity_amount* 100) / 100
                            if(termination_amount != term_gratuity_amount){
                                frm.set_value("gratuity_amount",r.message.termination_amount)
                            }
                            frm.set_value("gratuity_days",r.message.termination_days)
                        }
                    }
                }
            })
        }
    },
    refresh(frm) {
        frm.add_custom_button(__("Print F & F"), function () {

            var f_name = frm.doc.name
            var print_format = "Full and Final Settlement";
            window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
                + "doctype=" + encodeURIComponent("Full and Final Settlement")
                + "&name=" + encodeURIComponent(f_name)
                + "&trigger_print=1"
                + "&format=" + print_format
                + "&no_letterhead=0"
            ))
        });
        frm.add_custom_button(__('Create Payment Entry'), function() {
            route_to_payment_entry(frm);
        });
    },
    net_pay(frm){
        var leave_pay = (frm.doc.leave_payment_amount)
        var gra_amount = (frm.doc.gratuity_amount)
        var leave_grat = ((parseFloat(leave_pay) + parseFloat(gra_amount)) + (parseFloat(frm.doc.additions)))
        frm.set_value('leave_gratuity_total', leave_grat)
        if (frm.doc.is_paid == 1) {
            var net_pay = leave_grat - (frm.doc.loan_other_deduction + frm.doc.air_ticket_deduction)
            frm.set_value('net_pay', net_pay)
        }
        else {
            var net_pay = leave_grat + frm.doc.total_salary - (frm.doc.loan_other_deduction + frm.doc.air_ticket_deduction)
            frm.set_value('net_pay', net_pay)
        }
    },
    validate(frm) {
        var date1 = new Date(frm.doc.date_of_joining);
        var date2 = new Date(frm.doc.pay_end_date);
        var diffTime = Math.abs(date2 - date1);
        var diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
        frm.set_value('employment_duration',diffDays +1)
        frm.set_value('total_worked',diffDays +1)
        frm.trigger("gratuity_calculation")
        frm.trigger("encashed_leaves")
        frm.trigger("net_pay")
        frm.trigger("check_for_total_working_days")
    },
    leaves_calculation(frm){
        var earned_basic = ((frm.doc.basic_salary / frm.doc.total_working_days) * (frm.doc.no_of_days_worked- frm.doc.absent_days))
        if (earned_basic) {
            frm.set_value('earned_basic', earned_basic.toFixed(2))
        }
        
        var earned_food_allowance = ((frm.doc.food_allowance/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (earned_food_allowance) {
            frm.set_value('earned_food_allowance', earned_food_allowance.toFixed(2))
        }
        
        var earned_mobile_allowance = ((frm.doc.mobile_allowance/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (earned_mobile_allowance) {
            frm.set_value('earned_mobile_allowance', earned_mobile_allowance.toFixed(2))
        }
        
        var earned_car_allowance = ((frm.doc.car_allowance/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (earned_car_allowance) {
            frm.set_value('earned_car_allowance', earned_car_allowance.toFixed(2))
        }
        
        var earned_hra = ((frm.doc.hra/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (earned_hra) {
            frm.set_value('earned_hra', earned_hra.toFixed(2))
        }
        
        var earned_other_allowance = ((frm.doc.other_allowances/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (earned_other_allowance) {
            frm.set_value('earned_other_allowance', earned_other_allowance.toFixed(2))
        }
        
        var gosi = ((frm.doc.gosi_deduction/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (gosi) {
            frm.set_value('gosi', gosi.toFixed(2))
        }
                
        var transportation = ((frm.doc.transportation_pay/frm.doc.total_working_days)*(frm.doc.no_of_days_worked - frm.doc.absent_days))
        if (transportation) {
            frm.set_value('transportation', transportation.toFixed(2))
        }
                
        var tott = (parseFloat(frm.doc.earned_basic)+parseFloat(frm.doc.earned_food_allowance)+
                    parseFloat(frm.doc.earned_mobile_allowance)+parseFloat(frm.doc.earned_car_allowance)+
                    parseFloat(frm.doc.earned_hra)+parseFloat(frm.doc.earned_other_allowance)+
                    parseFloat(frm.doc.amount)+parseFloat(frm.doc.transportation) - parseFloat(frm.doc.gosi))
        frm.set_value('total_salary',tott)
    },
    onload(frm){
		frappe.run_serially([
			()=>{                
                frappe.db.get_value(
                    "Employee",
                    frm.doc.employee,
                    "relieving_date",
                    (r) => {
                        frm.set_value("last_day_of_work", r.relieving_date)
                    }
                );
			},
			() => frm.trigger("gratuity_calculation"),
			() => frm.trigger("check_for_total_working_days")
		])
    },
    employee(frm) {
        if(frm.doc.employee && frm.doc.company){
            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.full_and_final_settlement.full_and_final_settlement.get_reg_form",
                args: {
                    'employee': frm.doc.employee
                },
                callback: function (d) {
                    if (d.message) {
                        frm.set_value('resignation_form', d.message[0])
                        frm.set_value('pay_start_date', d.message[1])
                        frm.set_value('pay_end_date', d.message[2])
                        frappe.run_serially([
                            () => frm.trigger("set_total_working_days"),
                            () => {
                                frappe.call({
                                    method:"cyrix.cyrix_tsl.doctype.full_and_final_settlement.full_and_final_settlement.get_number_of_leave_days",
                                    args:{
                                        company:frm.doc.company,
                                        employee: frm.doc.employee,
                                        leave_type: "Annual Leave",
                                        to_date:frm.doc.pay_end_date || '',
                                        from_date:frm.doc.pay_start_date ||''
                                    },
                                    callback(r){
                                        if(r.message>0){
                                            frm.set_value("no_of_days_worked",r.message)
                                        }
                                        else{
                                            frm.set_value("no_of_days_worked",0)
                                        }
                                    }
                                })
                            },
                            () => {
                                if (d.message[3] > 0) {
                                    frm.set_value("leave_balance", d.message[3]);
                                    frappe.call({
                                        method:"cyrix.cyrix_tsl.doctype.full_and_final_settlement.full_and_final_settlement.calculate_leave_payment_amount",
                                        args:{
                                            "company": frm.doc.company,
                                            "basic":frm.doc.ctc,
                                            "leave_balance":d.message[3]
                                        },
                                        callback(k){
                                            if(k.message){
                                                var return_value = Math.round(k.message* 100) / 100
                                                var leave_payment_amount = Math.round(frm.doc.leave_payment_amount* 100) / 100
                                                if (return_value != leave_payment_amount){
                                                    frm.set_value("leave_payment_amount",k.message)
                                                }
                                            }
                                        }
                                    })
                                
                                } else {
                                    frm.set_value("leave_balance", "0");
                                }
                            },
                        ])
                    }
                }
            })
        }
    },
    set_total_working_days(frm){
        frappe.call({
            method: "cyrix.cyrix_tsl.doctype.full_and_final_settlement.full_and_final_settlement.get_current_month_date",
            args: {
                'employee': frm.doc.employee,
            },
            callback: function (d) {
                if (d.message) {
                    if(frm.doc.company == "Cyrix TSL - Kuwait"){
                        frm.set_value('total_working_days', 26)
                    }
                    else{
                        frm.set_value('total_working_days', d.message)
                    }
                }
            }
        })
    },
    absent_days(frm){
        frm.trigger("leaves_calculation")
        frm.trigger("encashed_leaves")
        frm.trigger("net_pay")
    },
    amount(frm){
        frm.trigger("leaves_calculation")
        frm.trigger("encashed_leaves")
    },
    encashed_leaves(frm) {
        var cal = ((frm.doc.basic_salary / frm.doc.total_working_days) * frm.doc.encashed_leaves)
        frm.set_value('leave_pay', cal.toFixed(2))
        frm.trigger("leaves_calculation")
        frm.trigger("net_pay")
    },
    additions(frm){
        if (frm.doc.additions){
            frm.trigger("encashed_leaves")
        }
    },
    loan_other_deduction(frm){
        frm.trigger("encashed_leaves")
    },
    air_ticket_deduction(frm){
        frm.trigger("encashed_leaves")
    },
})

function route_to_payment_entry(frm) {
    frappe.model.with_doctype('Payment Entry', function () {
        var doc = frappe.model.get_new_doc('Payment Entry');
        doc.payment_type = "Pay";
        doc.party_type = "Employee";
        doc.fnf = frm.doc.name
        frappe.set_route('Form', doc.doctype, doc.name);
    });
}