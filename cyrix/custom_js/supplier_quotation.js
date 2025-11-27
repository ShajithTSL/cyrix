frappe.ui.form.on('Supplier Quotation', {
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
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