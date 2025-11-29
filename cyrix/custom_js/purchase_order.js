frappe.ui.form.on("Purchase Order", {
	onload: function(frm){
        frm.trigger("schedule_date")
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
		if(frm.doc.items.length>0 && frm.doc.items[0].warehouse && frm.doc.docstatus == 0){
			frm.set_value("set_warehouse",frm.doc.items[0].warehouse)
		}
    },
    refresh: function(frm){
        frm.trigger("schedule_date")
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
                "Kuwait": "PO-K.YY.-",
                "Dammam": "PO-D.YY.-",
                "Riyadh": "PO-R.YY.-",
                "Jeddah": "PO-J.YY.-",
                "Dubai": "PO-DU.YY.-"
            };
            const series = naming_series[frm.doc.branch];
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
	refresh(frm) {
        if(frm.doc.docstatus == 0){
			frm.add_custom_button(__("Job Order Data"), function () {
				let dialog;  // Declare in outer scope

				dialog = new frappe.ui.form.MultiSelectDialog({
					doctype: "Job Order Data",
					target: frm,
					setters: {
						status: "",
					},
					add_filters_group: 1,
					get_query() {
						return {
							filters: {
								docstatus: 1
							}
						};
					},
					action(selections) {
						if (selections.length === 0) {
							frappe.msgprint("Please select at least one Job Order.");
							return;
						}
						frappe.call({
							method: "cyrix.custom_py.purchase_order.make_po_from_job_order",
							args: {
								job_orders: selections
							},
							callback: function (r) {
								if (!r.exc && r.message) {
									let data = r.message;
									frm.set_value("supplier", data.supplier);
									frm.set_value("branch", data.branch);
									frm.set_value("cost_center", data.cost_center);
									frm.set_value("project", data.project);
									frm.set_value("schedule_date", data.schedule_date);
									frm.set_value("buying_price_list", data.buying_price_list);

									// Clear and set items
									frm.clear_table("items");
									(data.items || []).forEach(item => {
										let row = frm.add_child("items");
										Object.assign(row, item);
									});

									frm.refresh_field("items");
									frm.refresh();
									cur_dialog.hide();
								}
							}
						});
					}
				});
			},__("Get Items From"));
		}
	}
});


frappe.ui.form.on('Purchase Order Item', {
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
});