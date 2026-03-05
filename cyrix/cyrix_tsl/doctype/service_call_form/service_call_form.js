// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Call Form', {

    company: function(frm) {
        frm.trigger("set_query");
    },

    set_query: function(frm) {
        frm.set_query("department", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
				]
			}
		});
        frm.set_query("related_doc", function () {
            return {
                filters: [
                    ["company", "=", frm.doc.company],
                ]
            }
        });
        
    },

	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('Internal Quotation'), function(){
                frappe.call({
                    method: "cyrix.cyrix_tsl.doctype.service_call_form.service_call_form.create_qtn",
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
        frm.trigger("set_query");
	},

    related_doc: function(frm) {
        if (frm.doc.related_doc) {
            let data = frm.doc.related_doc;
            let doc_type = frm.doc.document_type;

            const fields_to_fetch = {
                customer: "customer",
                branch: "branch",
                department: "department",
                sales_person: "sales_person",
                company: "company",
            };

            for (let source_field in fields_to_fetch) {
                let target_field = fields_to_fetch[source_field];
                frappe.db.get_value(doc_type, { name: data }, source_field, function(r) {
                    if (r && r[source_field]) {
                        frm.set_value(target_field, r[source_field]);
                    } else {
                        frm.set_value(target_field, "");
                    }
                });
            }
        }
    },	
});

frappe.ui.form.on('Service Call Schedule', {
	date: function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		if(row.date){
            var days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
            var now = new Date(row.date);
            var day = days[ now.getDay() ];
            row.day = day;
            frm.refresh_field("service_call_schedule")
        }
	}
})