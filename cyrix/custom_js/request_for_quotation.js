frappe.ui.form.on('Request for Quotation', {
    fetch_last_purchase_rate(frm){    
        if(frm.doc.items.length > 0 && frm.doc.company && frm.doc.docstatus == 0){ 
            frappe.call({
                method:"cyrix.custom_py.request_for_quotation.fetch_last_purchase_rate",
                args:{
                    items:frm.doc.items,
                    company:frm.doc.company
                },
                callback(r){
                    if(r){
                        frm.set_value('last_purchase_rate',r.message)
                    }
                }
            })
        }   
    },
    onload: function(frm){
        frm.trigger("schedule_date")
        if(frm.doc.docstatus == 0){
            frm.fields_dict['items'].grid.wrapper.on('focus', 'input[data-fieldname="schedule_date"]', function() {
                let $input = $(this);
                setTimeout(function() {
                    let datepicker = $input.data('datepicker');
                    if (datepicker) {
                        datepicker.update({
                            minDate: new Date(frm.doc.transaction_date)
                        });
                    }
                }, 100);
            });
        }
        frm.trigger("fetch_last_purchase_rate")
    },
    refresh: function(frm){
        frm.trigger("schedule_date")
        frm.trigger("fetch_jo")
    },

    fetch_jo: function(frm){
        if(frm.doc.docstatus == 0){
            frm.add_custom_button(__("Job Order Data"), function () {
                let dialog;  // Declare in outer scope

                dialog = new frappe.ui.form.MultiSelectDialog({
                    doctype: "Job Order Data",
                    target: frm,
                    setters: {
                        customer:frm.doc.party_name,
                        status: ""
                    },
                    add_filters_group: 1,
                    get_query() {
                        return {
                            filters: {
                                company: frm.doc.company,
                                docstatus: 1
                            }
                        };
                    },
                    action(selections) {
                        frappe.call({
                            method: "cyrix.custom_py.purchase_order.get_job_order_data",
                            args: {
                                "job_order_data": selections
                            },
                            callback: function(r) {
                                if(r.message) {
                                    cur_frm.clear_table("items");
                                    $.each(r.message, function(i,v){
                                        if(v.part){
                                            var item_child = cur_frm.add_child("items");
                                            item_child.schedule_date = frm.doc.schedule_date,
                                            item_child.item_code = v.part,
                                            item_child.item_name = v.part_name,
                                            item_child.mfg = v.manufacturer,
                                            item_child.model = v.model,
                                            item_child.description = v.part_name,
                                            item_child.qty = v.qty,
                                            item_child.uom = "Nos",
                                            item_child.branch =  frm.doc.branch,
                                            item_child.job_order_data =  v.job_order_data,
                                            item_child.conversion_factor =1,
                                            item_child.department = frm.doc.department
                                            
                                            frm.refresh_field("items");
                                            frm.refresh();
                                        }
                                    })
                                }
                            }
                        });
                        
                        cur_dialog.hide();
                    }
                });
            },__("Get Items From"));
        }
    },
    schedule_date: function(frm){
        frm.fields_dict.schedule_date.datepicker.update({
            minDate: new Date(frm.doc.transaction_date)
        });
        if(frm.doc.schedule_date < frm.doc.transaction_date){
            frm.set_value("schedule_date",'')
        }
        if (!frm.doc.schedule_date) {
			frm.doc.items.forEach((item) => {
				item.schedule_date = '';
			});
		}
		refresh_field("items");
    },
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            const naming_series = {
                "Kuwait": "RFQ-K.YY.-",
                "Dammam": "RFQ-D.YY.-",
                "Riyadh": "RFQ-R.YY.-",
                "Jeddah": "RFQ-J.YY.-",
                "Dubai": "RFQ-DU.YY.-"
            };
            const series = naming_series[frm.doc.branch];
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
})

frappe.ui.form.on('Request for Quotation Item', {
    form_render: (frm, cdt, cdn) => {
        $('input[data-fieldname="schedule_date"]').click(function() {
            frm.cur_grid.grid_form.fields_dict.schedule_date.datepicker.update({
                minDate: new Date(frm.doc.transaction_date)
            });
        });
    },
    schedule_date: function(frm, cdt, cdn){
		var row = locals[cdt][cdn]
        if(row.schedule_date < frm.doc.transaction_date){
            row.schedule_date = ''
        }
	},
    item_code: function(frm, cdt, cdn){
		var row = locals[cdt][cdn]
        if(row.item_code){
            frm.trigger("fetch_last_purchase_rate")
        }
	},
});
