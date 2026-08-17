// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Request", {

    change_repayment_amount: function(frm) {
        if (frm.doc.docstatus !== 1) return;

        frm.add_custom_button(__('Update Repayment Amount'), function() {

            let dialog = new frappe.ui.Dialog({
                title: 'Change Repayment Amount',
                fields: [
                    {
                        fieldtype: 'Currency',
                        fieldname: 'new_amount',
                        label: 'New Repayment Amount',
                        reqd: 1
                    },
                    {
                        fieldtype: 'Date',
                        fieldname: 'effective_date',
                        label: 'Effective From',
                        reqd: 1,
                        default: frappe.datetime.now_date()
                    }
                ],

                primary_action_label: 'Preview',

                primary_action(values) {

                    frappe.call({
                        method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.preview_repayment_change",
                        args: {
                            loan_name: frm.doc.name,
                            new_amount: values.new_amount,
                            effective_date: values.effective_date
                        },
                        callback: function(r) {

                            if (!r.message) return;

                            let html = `
                            <table class="table table-bordered">
                                <tr>
                                    <th>Date</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                </tr>`;

                            r.message.forEach(row => {
                                html += `
                                <tr>
                                    <td>${row.payment_date}</td>
                                    <td>${row.amount}</td>
                                    <td>${row.status}</td>
                                </tr>`;
                            });

                            html += "</table>";

                            frappe.confirm(
                                html,
                                function() {

                                    frappe.call({
                                        method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.change_repayment_amount",
                                        args: {
                                            loan_name: frm.doc.name,
                                            new_amount: values.new_amount,
                                            effective_date: values.effective_date
                                        },
                                        callback: function(r) {
                                            frappe.msgprint(r.message);
                                            dialog.hide();
                                            frm.reload_doc();
                                        }
                                    });

                                }
                            );
                        }
                    });

                }
            });

            dialog.show();
        },__("Manage"));
    },

    before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to HR") {
					frappe.call({
						method: 'tsl.custom_py.email_notification.send_mail_on_loan_request',
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
				if (frm.selected_workflow_action == "Approve & Send to Finance") {
                    if(!frm.doc.repayment_start_date){
                        frappe.msgprint({
                            title: "Repayment Start Date Missing",
                            indicator: "red",
                            message: `
                                Please set the <b>Repayment Start Date</b> before approving the loan request.
                            `
                        });
                        frappe.validated = false
                        reject();
                        return;
                    }
					frappe.call({
						method: 'tsl.custom_py.email_notification.send_mail_on_loan_request',
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

        if (["Under Finance","Under HR"].includes(frm.doc.workflow_state) && frm.selected_workflow_action === "Reject") {
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
                method: "tsl.custom_py.email_notification.send_loan_rejection_mail",
                args: {
                    name: frm.doc.name,
                    rejection_reason: values.reason
                }
            });
        }
	},

    onload: function(frm) {
        frm.fields_dict["pending_loans"].$wrapper.html('');
    },
    show_criteria: function (frm){
        if (frappe.user.has_role("HR Manager") || frappe.user.has_role("Accounts Manager") || frappe.user.has_role("HR User") || frappe.user.has_role("Loan Approver") || frappe.user.has_role("System Manager") ) {
            frm.add_custom_button(__("Show Criteria"), function(){
            frappe.call({
                method: 'cyrix.cyrix_tsl.doctype.loan_request.loan_request.get_criteria',
                args: {
                    employee: frm.doc.employee,
                    cur_name : frm.doc.name || ''
                },
                callback: function(r) {
                    console.log(r)
                    if (r.message) {
                        let dialog = new frappe.ui.Dialog({
                        fields: [
                            {
                            fieldtype: 'HTML',
                            fieldname: 'table_html',
                            options: r.message
                            }
                        ],
                        size: 'extra-large'
                        });

                        dialog.show();
                    }
                }
            });
        });
        }
      
    },
    
    employee(frm){
        frm.trigger("set_pending_loans_snapshot");
    },

    check_pending_loan(frm) {
        // Fill HTML before saving
        frm.trigger("set_pending_loans_snapshot");
    },

    set_pending_loans_snapshot(frm) {
        if (!frm.doc.employee) {
            return;
        }
        frappe.call({
            method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.get_pending_loans_html",
            args: {
                employee: frm.doc.employee
            },
            callback: function(r) {
                if (!r.message) return;

                // Render on the form
                if (frm.fields_dict["pending_loans"])
                    frm.fields_dict["pending_loans"].$wrapper.html(r.message);
            }
        });
    },
    
    repayment_start_date: function(frm) {
        if (!frm.doc.employee || !frm.doc.repayment_start_date || frm.doc.allow_overlap) return;

        frm.set_value('stop',0)
        frappe.call({
            method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.get_pending_loans_with_dates",
            args: { employee: frm.doc.employee },
            callback: function(r) {
                if (!r.message || r.message.length === 0) return;

                let start_date = frm.doc.repayment_start_date;
                var check = 0
                r.message.forEach(loan => {
                    if (loan.last_payment_date && start_date <= loan.last_payment_date) {
                        check += 1
                        frappe.msgprint({
                            title: "Pending Loan Overlap",
                            indicator: "red",
                            message: `
                                The selected <b>Repayment Start Date</b> overlaps with an existing pending loan:<br><br>
                                <b>${loan.loan_product}</b> (${loan.name})<br>
                                Last Payment Date: <b>${loan.js_date}</b><br><br>
                                Please review the pending loans before proceeding.
                            `
                        });
                        frm.set_value('stop',1)
                    }
                });
            }
        });
    },

    validate : function(frm){
        // frm.trigger("repayment_start_date")
        if(frm.doc.stop == 1 && frm.doc.allow_overlap == 0){
            frappe.msgprint({
                title: "Pending Loan Overlap",
                indicator: "red",
                message: `
                    The selected <b>Repayment Start Date</b> overlaps with an existing pending loan<br><br>
                    Please review the pending loans before proceeding.
                `
            });
            frappe.validated = false
        }
    },

	create_loan_repayment: function(frm){
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__("Loan Repayment"), function(){
                frappe.call({
                    method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.create_loan_repayment",
                    args: {
                        "name": frm.doc.name
                    },
                    callback: function(r) {
                        if(r.message) {
                            var doc = frappe.model.sync(r.message);
                            frappe.set_route("Form", doc[0].doctype, doc[0].name);
                        }
                    }
                });
            },__('Create'));
        }
	},
	loan_amount : function(frm){
        frm.set_value('disbursed_amount',frm.doc.loan_amount)
        if(frm.doc.docstatus != 1){
            frm.set_value('balance_amount',frm.doc.loan_amount)
        }
    },
	repayment_method: function(frm) {
		frm.doc.repayment_amount = frm.doc.repayment_periods = "";
		frm.trigger("toggle_fields");
		frm.trigger("toggle_required");
	},
	toggle_fields: function(frm) {
		frm.toggle_enable("repayment_amount", frm.doc.repayment_method=="Repay Fixed Amount per Period")
		frm.toggle_enable("repayment_periods", frm.doc.repayment_method=="Repay Over Number of Periods")
	},
	toggle_required: function(frm){
		frm.toggle_reqd("repayment_amount", cint(frm.doc.repayment_method=='Repay Fixed Amount per Period'))
		frm.toggle_reqd("repayment_periods", cint(frm.doc.repayment_method=='Repay Over Number of Periods'))
	},

	refresh: function(frm) {
        frappe.run_serially([
			() => frm.trigger("show_criteria"),
			() => frm.trigger("loan_amount"),
			() => frm.trigger("company"),
			() => frm.trigger("create_loan_repayment"),
			() => frm.trigger("loan_pause"),
            () => frm.trigger("change_repayment_amount")
 		])
	},
	company : function (frm) {
		frm.set_query("employee", function () {
			return {
				"filters": {
					"company": frm.doc.company,
					"status": "Active"
				}
			};
		});
		frm.set_query("loan_product", function () {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		frm.set_query("branch", function () {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},
    

    loan_pause: function (frm) {
		if(frm.doc.docstatus == 1){
            frm.add_custom_button(__('Pause Repayment'), function() {
                let dialog = new frappe.ui.Dialog({
                    title: 'Pause Loan Accrual',
                    fields: [
                        {
                            fieldtype: 'Date',
                            fieldname: 'from_date',
                            label: 'From Date',
                            reqd: 1,
                        },
                        {
                            fieldtype: 'Date',
                            fieldname: 'to_date',
                            label: 'To Date',
                            reqd: 1
                        },
                        {
                            label: 'Date',
                            fieldname:'date',
                            fieldtype:'Date',
                            default: frappe.datetime.now_date(),
                            // hidden:1
                        },
                        {
                            label: 'Remarks',
                            fieldname:'remarks',
                            reqd:1,
                            fieldtype:'Small Text',
                        },
                    ],
                    primary_action_label: 'Pause',
                    primary_action: function() {
                        let data = dialog.get_values();
                        if (data) {
                            frappe.call({
                                method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.preview_shifted_repayment_schedule",
                                args: {
                                    loan_name: frm.doc.name,
                                    from_date: data.from_date,
                                    to_date: data.to_date,
                                },
                                callback: function(r) {
                                    if (r.message) {
                                        let preview_html = `<table class="table table-bordered">
                                            <tr><th>Old Date</th><th>New Date</th></tr>`;
                                        r.message.forEach(row => {
                                            if (row.new_date === "Locked (Paid Alreaday)") {
                                                preview_html += `<tr style="color:red;">
                                                    <td>${row.old_date}</td>
                                                    <td>${row.new_date}</td>
                                                </tr>`;
                                            } else {
                                                preview_html += `<tr>
                                                    <td>${row.old_date}</td>
                                                    <td>${row.new_date}</td>
                                                </tr>`;
                                            }
                                        });
                                        preview_html += `</table>`;

                                        frappe.confirm(
                                            `The following repayment dates will change:<br><br>${preview_html}<br>
                                            Do you want to continue?`,
                                            () => {
                                                let newRemark = {
                                                    pause_from: data.from_date,
                                                    pause_upto: data.to_date,
                                                    posting_date: data.date,
                                                    remarks: data.remarks,
                                                };

                                                frappe.call({
                                                    method: "cyrix.cyrix_tsl.doctype.loan_request.loan_request.shift_payment_dates_for_pause",
                                                    args: {
                                                        self: frm.doc.name,
                                                        from_date: data.from_date,
                                                        to_date: data.to_date,
                                                        loan_pause_details: newRemark
                                                    },
                                                    callback: function(r) {
                                                        if (!r.exc) {
                                                            frappe.msgprint(__('Repayment schedule updated successfully!'));
                                                            dialog.hide();
                                                            frm.reload_doc();
                                                        }
                                                    }
                                                });
                                            }
                                        );
                                    }
                                }
                            });
                        }
                    }

                });
                dialog.show();
            },__("Manage"));
        }
	},
});