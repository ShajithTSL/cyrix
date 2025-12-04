frappe.ui.form.on('Delivery Note', {
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            const naming_series = {
                "Kuwait": "DN-K.YY.-",
                "Dammam": "DN-D.YY.-",
                "Riyadh": "DN-R.YY.-",
                "Jeddah": "DN-J.YY.-",
                "Dubai": "DN-DU.YY.-"
            };
            const series = naming_series[frm.doc.branch];
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
    onload: function (frm) {
        // Transfer custom data from temporary doc variable to form state
        if (frm.doc.__custom_items_to_override) {
            frm.custom_items_to_override = frm.doc.__custom_items_to_override;
            delete frm.doc.__custom_items_to_override;
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
            // frm.custom_items_to_override = null;
        }
    }
});
