frappe.ui.form.on('Supplier Quotation', {
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