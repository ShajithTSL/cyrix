// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Stock Release", {
    refresh:function(frm){
        // to set the date automatically
        frm.set_value("from_date",frappe.datetime.month_start())
        frm.set_value("to_date",frappe.datetime.now_date())

        frm.disable_save()
        frm.set_query("account",function(){
            return {
                filters: [
                    ["is_group","=",0]
                ]
            };
        })
        frm.trigger("branch")
    },
    company:function(frm){
        frm.trigger("branch")
    },
    branch: function(frm){
        if (frm.doc.company) {
            frm.set_query("branch",function(){
                return {
                    filters: [
                        ["company","=",frm.doc.company]
                    ]
                };
            })
            frm.set_query("account",function(){
                return {
                    filters: [
                        ["company","=",frm.doc.company]
                    ]
                };
            })
            if (frm.doc.branch) {                
                var details = {
                    "Dubai":{
                        "warehouse":"Dubai - CT-UAE",
                        "cost_center":"Dubai - Repair - CT-UAE",
                        "account":"3010101 - Cost of Material for Service - CT-UAE"
                    },
                    "Kuwait":{
                        "warehouse":"Kuwait - CT-K",
                        "cost_center":"Kuwait - Repair - CT-K",
                        "account":"3010101 - Cost of Material for Service - CT-K"
                    },
                    "Jeddah":{
                        'warehouse':"Jeddah - BM",
                        "cost_center":"Jeddah - Repair - BM",
                        "account":"3010101 - Cost of Material for Service - BM"
                    },
                    "Riyadh":{
                        'warehouse':"Riyadh - BM",
                        "cost_center":"Riyadh - Repair - BM", 
                        "account":"3010101 - Cost of Material for Service - BM"
                    },
                }
                const warehouse = details[frm.doc.branch].warehouse;
                const cost_center = details[frm.doc.branch].cost_center;
                const account = details[frm.doc.branch].account;
                frm.set_value("warehouse", warehouse);
                frm.set_value("cost_center", cost_center);
                frm.set_value("account", account);
                frm.set_query("warehouse",function(){
                    return {
                        filters: [
                            ["name","=",warehouse]
                        ]
                    };
                })
                frm.set_query("cost_center",function(){
                    return {
                        filters: [
                            ["name","=",cost_center]
                        ]
                    };
                })
            }
        }
    },
    submit: function(frm){
        frappe.show_alert({
            message: __("Processing... Please wait"),
            indicator: "green"
        });
        frm.call("submit_bulk_entries")
        .then(r => {
            frm.trigger('fetch_draft_entries');
        })
        .catch(err => {
            frappe.run_serially([
                () => frappe.show_alert({
                    message: __(err.statusText),
                    indicator: "red"
                })
            ]);
            
        })
    },
    
    warehouse:function(frm){
        frm.trigger('fetch_draft_entries')
    },
    from_date:function(frm){
        frm.trigger('fetch_draft_entries')
    },
    to_date:function(frm){
        frm.trigger('fetch_draft_entries')
    },
    cost_center:function(frm){
        frm.trigger('fetch_draft_entries')
    },
	fetch_draft_entries(frm) {
        frappe.call({
            method:"cyrix.cyrix_tsl.doctype.bulk_stock_release.bulk_stock_release.fetch_draft_entries",
            args:{
                from_date: frm.doc.from_date || '',
                to_date: frm.doc.to_date || '',
                warehouse: frm.doc.warehouse || '',
                cost_center: frm.doc.cost_center || '',
                branch: frm.doc.branch || ''
            },
            callback(r){
                if(r){
                    frm.set_value('stock_details',r.message)
                }
            }
        })
	},
});