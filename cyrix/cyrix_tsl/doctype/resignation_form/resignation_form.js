// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resignation Form", {
	refresh(frm) {
		if (frm.doc.docstatus == 1){
			if (frappe.user.has_role("HR Manager")){
				frm.add_custom_button(__('F & F Statement'), function() {
				    frappe.db.get_value('Full and Final Settlement',{'employee': frm.doc.employee },'name').then(r => {
                        if(r.message && Object.entries(r.message).length === 0){
                            frappe.route_options = { 'employee':frm.doc.employee,'employee_name': frm.doc.employee_name,'company': frm.doc.company}
                            frappe.set_route('Form','Full and Final Settlement','new-full-and-final-settlement-1')
                        }
                        else{
                            frappe.set_route('Form','Full and Final Settlement',r.message.name)
                        }
                    })
                });
			}		
		}
	},
	validate(frm){
	    if(frm.doc.employee_name){
	        frm.set_value('session_user',frappe.session.user)
      	} 
	},
	hods_relieving_date: function(frm){
		if (frm.doc.hods_relieving_date && frm.doc.employee){
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.resignation_form.resignation_form.calculate_relieving_date",
				args: {
					posting_date : frm.doc.hods_relieving_date,
					employee: frm.doc.employee
				},
				callback(r){
					if(r.message){
						frm.set_value("actual_relieving_date",r.message)
					}
				}
			})
		}
	}		
})