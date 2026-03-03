frappe.ui.form.on('Sales Invoice', {
    company: function(frm) {
        frm.trigger("hide_section");
    },
    refresh: function(frm) {
        frm.trigger("hide_section");
    },
    onload: function(frm) {
        frappe.run_serially([
            () => {
                frm.trigger("hide_section")
            },
            () => {
                if (frm.doc.__custom_items_to_override) {
                    frm.custom_items_to_override = frm.doc.__custom_items_to_override;
                    delete frm.doc.__custom_items_to_override;
                }
            },
        ])
    },
    hide_section: function(frm) {
        frappe.db.get_value("Company", {"name": frm.doc.company}, "custom_zatca_invoice_enabled").then(r => {
            if (r && r.message) {
                if (r.message.custom_zatca_invoice_enabled === 0){
                    frm.set_df_property('custom_section_break_gqwpx', 'hidden', true);
                }
                else{
                    frm.set_df_property('custom_section_break_gqwpx', 'hidden', false);
                }
            }
        })
    },
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            if(frm.doc.is_return == 1){
                const series = {
                    "Kuwait": "INV-RE-K.YY.-",
                    "Dammam": "INV-RE-D.YY.-",
                    "Riyadh": "INV-RE-R.YY.-",
                    "Jeddah": "INV-RE-J.YY.-",
                    "Dubai": "INV-RE-DU.YY.-"
                };
                const return_series = series[frm.doc.branch];
                if (return_series) {
                    frm.set_value('naming_series', return_series);
                }
            }
            else{               
                const naming_series = {
                    "Kuwait": "INV-K.YY.-",
                    "Dammam": "INV-D.YY.-",
                    "Riyadh": "INV-R.YY.-",
                    "Jeddah": "INV-J.YY.-",
                    "Dubai": "INV-DU.YY.-"
                };
                const series = naming_series[frm.doc.branch];
                if (series) {
                    frm.set_value('naming_series', series);
                }
            }
        }
    },
    before_save: function (frm) {
        if (frm.custom_items_to_override && Array.isArray(frm.custom_items_to_override)) {
            frm.doc.items.forEach(row => {
                const custom_item = frm.custom_items_to_override.find(ci => ci.item_code === row.item_code);
                if (custom_item) {
                    row.rate = custom_item.rate;
                    row.price_list_rate = custom_item.rate;
                    row.amount = custom_item.rate * row.qty;
                }
            });
            // Clear after applying
            frm.custom_items_to_override = null;
        }
    }
})