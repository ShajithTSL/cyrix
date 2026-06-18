frappe.ui.form.on('Supplier Quotation', {
    fetch_price_list: function(frm){
        if (frm.doc.__islocal){
            frappe.call({
                method: "cyrix.custom_py.utils.fetch_price_list",
                args:{
                    company : frm.doc.company, 
                    document_type : "buying"
                },
                callback(r){
                    if (r.message){
                        frm.set_value("buying_price_list",r.message)
                    }
                }
            })
        }
    },
    set_cost_center: function(frm){
        $.each(frm.doc.items, function(i,j){
            j.cost_center = frm.doc.cost_center
        })
        frm.refresh_field("items")
    },
    set_branch: function(frm){
        $.each(frm.doc.items, function(i,j){
            j.branch = frm.doc.branch
        })
        frm.refresh_field("items")
    },
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
        frm.trigger("set_branch")
        frm.trigger("set_cost_center")
    },
    refresh : function(frm){
        if(frm.doc.docstatus == 0){
            frm.trigger("set_branch")
            frm.trigger("set_cost_center")
        }
        frm.trigger("fetch_price_list")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            const naming_series = {
                "Kuwait": "SQTN-K.YY.-",
                "Dammam": "SQTN-D.YY.-",
                "Riyadh": "SQTN-R.YY.-",
                "Jeddah": "SQTN-J.YY.-",
                "Dubai": "SQTN-DU.YY.-"
            };
            const series = naming_series[frm.doc.branch];
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
})