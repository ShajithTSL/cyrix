// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Technical Report", {
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            const naming_series = {
                "Kuwait": "TR-K.YY.-",
                "Dammam": "TR-D.YY.-",
                "Riyadh": "TR-R.YY.-",
                "Jeddah": "TR-J.YY.-",
                "Dubai": "TR-DU.YY.-"
            };
            const series = naming_series[frm.doc.branch];
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
});
