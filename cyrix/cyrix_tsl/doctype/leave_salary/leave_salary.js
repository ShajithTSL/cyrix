// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Salary', {
	before_workflow_action: async (frm) => {
		if(frm.doc.workflow_state == "Draft"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Send to Finance") {
					frappe.call({
						method: 'tsl.custom_py.email_notification.send_mail_on_leave_salary',
						args: {
							"name": frm.doc.name
						}
					})
				}
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
	},
    onload: function(frm) {
		if (frm.doc.docstatus == 0 && frm.doc.employee){
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.leave_salary.leave_salary.check_balance_leaves",
				args:{
					employee: frm.doc.employee
				},
				callback(r){
					frm.set_value('encashable_days',r.message)
				}
			})
		}
	},
    encashment_days: function(frm){
        
		frappe.run_serially([
            () => {
                if(!frm.doc.encashment_days)
        			return
        		if(frm.doc.encashment_days && frm.doc.encashment_days > frm.doc.encashable_days){
        			frappe.msgprint("Encashment days cannot be greater than - <b>"+frm.doc.encashable_days+"</b>")
        			frm.set_value("encashment_days",0)
        		}
            },
            () => {
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
            () => frm.trigger("total_salary"),
            () => frm.trigger("total_salary"),
            () => frm.trigger("total_salary")
        ]);
	},
    total_gross_pay:function(frm){
        var total_gross_pay = frm.doc.basic + frm.doc.mobile_allowance +frm.doc.food + frm.doc.hra_salary + frm.doc.transport_allowance + frm.doc.other_allowance
        frm.set_value('total_gross_pay',total_gross_pay)
    },
	show_warning: function(frm){
		frappe.call({
			method:"cyrix.cyrix_tsl.doctype.leave_salary.leave_salary.check_for_active_loans",
			args:{
				name:frm.doc.employee
			},
			callback(r){
				if (r.message === "Exists") {
					frm.set_df_property("employee","description",'<span style="color: red; ">⚠️ This employee has an active loan.</span>');
					frm.set_value("loan_exists",1);
				}
			}
		})
	},
    validate(frm){
        frm.trigger("total_gross_pay") 
        frm.trigger("cals");
        frm.trigger("earned_total");
        frm.trigger("total_salary")
		frm.trigger("total_leave_salary")
    },
    cals(frm) {
        const now = new Date(frm.doc.from_date);
        const year = now.getFullYear();
        const month = now.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const nodw = frm.doc.no_of_days_worked || 0;
        const bas = frm.doc.basic || 0;
        const fa = frm.doc.food || 0;
        const ta = frm.doc.transport_allowance || 0;
        const hra = frm.doc.hra_salary || 0;
        let ebasic = 0;
        
        if (frm.doc.company === "Cyrix TSL - Kuwait") {
            ebasic = (frm.doc.total_gross_pay / 26) * nodw;
        } 
        else {
            const sub_t = bas + fa + ta + hra;
            if (sub_t > 0 && daysInMonth > 0) {
                ebasic = (sub_t / daysInMonth) * nodw;
            }
        }
        if (frm.doc.skip_earned_salary == 0){
            frm.set_value('salary_amount_pay', ebasic);
        }
        else{
            frm.set_value('salary_amount_pay', 0);
        }
    },
	earned_total(frm){
	    var sal = parseFloat(frm.doc.salary_amount_pay);
        frm.set_value('total_amount',sal.toFixed(2));
	},
	refresh(frm){
		frm.trigger("show_warning")
	    if(frm.doc.leave_application){
	        frappe.db.get_value("Leave Application Form", frm.doc.leave_application, "company", (r) => {
    			if(r.company){
    			    frm.set_value("company",r.company)
    			}
    		})
	    }
		
        frm.trigger("total_gross_pay") 
        if(!frm.doc.__islocal){
            frm.add_custom_button(__("Print"), function () {
    			var f_name = frm.doc.name;
    			var print_format = "Leave Salary";
    			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
    				+ "doctype=" + encodeURIComponent("Leave Salary")
    				+ "&name=" + encodeURIComponent(f_name)
    				+ "&trigger_print=1"
    				+ "&format=" + print_format
    				+ "&no_letterhead=0"
    			));
            });
        }
	    if(frm.doc.docstatus ==1 ){
            frm.add_custom_button(__('Create Payment Entry'), function() {
                route_to_payment_entry(frm);
            });
            frm.add_custom_button(__("Print"), function () {
    			var f_name = frm.doc.name;
    			var print_format = "Leave Salary";
    			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
    				+ "doctype=" + encodeURIComponent("Leave Salary")
    				+ "&name=" + encodeURIComponent(f_name)
    				+ "&trigger_print=1"
    				+ "&format=" + print_format
    				+ "&no_letterhead=0"
    			));
            }); 
	    }
	},
	employee(frm){
	    if(frm.doc.employee){
	        frappe.call({
    	        method:"cyrix.cyrix_tsl.doctype.leave_salary.leave_salary.get_leave_application",
    	        args:{
    	           'leave_application':frm.doc.leave_application
    	        },
    	        callback(d){
					frm.set_value('from_date',d.message[0]);
					frm.set_value('to_date',d.message[1]);
					frm.set_value('leave_start_date',d.message[2]);
					frm.set_value('leave_end_date',d.message[3]);
					frm.set_value('no_of_days_worked',d.message[4]);
					frm.set_value('no_of_days',d.message[5])
					frm.set_value('leave_balance',d.message[6])
					frm.set_value('special_holidays',d.message[7])
    	        }
            });
	    }
	},
	leaves_encashed(frm){
	    var no_of_days = parseFloat(frm.doc.leaves_availed) + parseFloat(frm.doc.leaves_encashed);
	    frm.set_value('no_of_days',no_of_days.toFixed(2));
	    frm.trigger('total_leave_salary');
	},
	ignore_loan: function(frm){
		frm.trigger("total_leave_salary")
	},
	total_leave_salary(frm){
		if (frm.doc.loan_exists == 1){
			if (frm.doc.ignore_loan == 1){
				if(frm.doc.company == "Cyrix TSL - Kuwait"){
					var nod = parseFloat(frm.doc.no_of_days) - parseFloat(frm.doc.deduction_days);
					var total = ((frm.doc.total_gross_pay/26)*nod);
				}
				else{
					var nod = parseFloat(frm.doc.no_of_days) - parseFloat(frm.doc.deduction_days) + parseFloat(frm.doc.special_holidays);
					var total = (frm.doc.total_gross_pay/30)*nod;
				}
				frm.set_value('total_salary',total.toFixed(2));
			}
			else{
				frm.set_value('total_salary',0)
			}
		}
		else{
			if(frm.doc.company == "Cyrix TSL - Kuwait"){
				var nod = parseFloat(frm.doc.no_of_days) - parseFloat(frm.doc.deduction_days);
				var total = ((frm.doc.total_gross_pay/26)*nod);
			}
			else{
				var nod = parseFloat(frm.doc.no_of_days) - parseFloat(frm.doc.deduction_days) + parseFloat(frm.doc.special_holidays);
				var total = (frm.doc.total_gross_pay/30)*nod;
			}
			frm.set_value('total_salary',total.toFixed(2));
		}
	    
	},
	air_fair(frm){
	    frm.trigger('total_leave_salary');
	},
	deduction(frm){
	    frm.trigger("total_salary")
	},  
	payment(frm){
	    frm.trigger("total_salary")
	},  
	total_salary(frm){
		var s1 = parseFloat(frm.doc.total_amount) || 0;
		var s2 = parseFloat(frm.doc.total_salary) || 0;
		var encash = parseFloat(frm.doc.encashment_amount) || 0;
		var s = s1 + s2 + encash;
		if(frm.doc.deduction){
			var s = s - frm.doc.deduction
		}
 	    if(frm.doc.payment){
	        var s = s + frm.doc.payment
	    }
		frm.set_value('total_released_amount',s.toFixed(2));
	}
});



function route_to_payment_entry(frm) {
    frappe.model.with_doctype('Payment Entry', function () {
        var doc = frappe.model.get_new_doc('Payment Entry');
        doc.payment_type = "Pay";
        doc.party_type = "Employee";
        doc.leave_salary = frm.doc.name
        frappe.set_route('Form', doc.doctype, doc.name);
    });
}
