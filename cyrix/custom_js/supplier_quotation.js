// frappe.ui.form.on('Supplier Quotation', {
//     before_workflow_action: async function(frm) {

//         if (frm.selected_workflow_action !== "Approve") {
//             return;
//         }

//         let approved_jo_found = false;

//         for (let row of frm.doc.items || []) {

//             if (!row.job_order_data) continue;

//             let r = await frappe.db.get_value(
//                 "Job Order Data",
//                 row.job_order_data,
//                 "is_approved"
//             );

//             if (r.message && r.message.is_approved) {
//                 approved_jo_found = true;
//                 break;
//             }
//         }

//         if (!approved_jo_found) {
//             return;
//         }

//         return new Promise((resolve) => {
//             frappe.dom.unfreeze();

//             frappe.confirm(
//                 __(
//                     "One or more linked Job Orders are already <b>A-Approved</b>.<br><br>" +
//                     "<b>Yes</b> → Change approved Job Orders back to Parts Priced.<br>" +
//                     "<b>No</b> → Continue approval without changing Job Order status."
//                 ),

//                 // YES
//                 async () => {

//                     await frappe.call({
//                         method: "app.custom_py.supplier_quotation.revert_approved_job_orders",
//                         args: {
//                             supplier_quotation: frm.doc.name
//                         },
//                         callback(r){
//                             frappe.call({
//                                 method: 'frappe.client.insert',
//                                 args: {
//                                     doc: {
//                                         doctype: 'Document Log',

//                                         document_type: frm.doc.doctype,
//                                         document_reference: frm.doc.name,

//                                         data: "Status Override Done by the User"
//                                     }
//                                 }
//                             });

//                         }
//                     });

//                     resolve();
//                 },

//                 // NO
//                 () => {
//                     resolve();
//                 }
//             );
//         });
//     },
frappe.ui.form.on('Supplier Quotation', {
    before_workflow_action: async function(frm) {

        if (frm.selected_workflow_action !== "Approve") {
            return;
        }

        let approved_items = [];

        for (let row of frm.doc.items || []) {

            // check Job Order Data
            if (row.job_order_data) {
                let r = await frappe.db.get_value(
                    "Job Order Data",
                    row.job_order_data,
                    "is_approved"
                );

                let s = await frappe.db.get_value(
                    "Job Order Data",
                    row.job_order_data,
                    "status"
                );

                if (r.message?.is_approved) {
                    approved_items.push({
                        type: "Job Order Data",
                        name: row.job_order_data,
                        status: s.message.status
                    });
                }
            }

            // check Supply Order Data
            if (row.supply_order_data) {
                let r = await frappe.db.get_value(
                    "Supply Order Data",
                    row.supply_order_data,
                    "is_approved"
                );

                let s = await frappe.db.get_value(
                    "Supply Order Data",
                    row.supply_order_data,
                    "status"
                );

                if (r.message?.is_approved) {
                    approved_items.push({
                        type: "Supply Order Data",
                        name: row.supply_order_data,
                        status: s.message.status
                    });
                }
            }

            // optional early exit if you only need one
            if (approved_items.length) break;
        }

        if (!approved_items.length) {
            return;
        }

        return new Promise((resolve) => {

            frappe.dom.unfreeze();

            let list_html = approved_items.map(d =>
                `<li><b>${d.type}</b> → ${d.name} → <b style = 'color:green'>${d.status}</b> </li>`
            ).join("");

            frappe.confirm(
                __(
                    `The following linked documents are already <b>Approved</b>:<br><br>
                    <ul>${list_html}</ul><br>
                    <b>Yes</b> → Revert to Parts Priced<br>
                    <b>No</b> → Continue approval without changes`
                ),

                // YES
                async () => {

                    await frappe.call({
                        method: "cyrix.custom_py.supplier_quotation.revert_approved_orders",
                        args: {
                            supplier_quotation: frm.doc.name
                        },
                        callback() {
                            frappe.call({
                                method: 'frappe.client.insert',
                                args: {
                                    doc: {
                                        doctype: 'Document Log',
                                        document_type: frm.doc.doctype,
                                        document_reference: frm.doc.name,
                                        data: "Status Override Done by User"
                                    }
                                }
                            });
                        }
                    });

                    resolve();
                },

                // NO
                () => {
                    resolve();
                }
            );
        });
    },
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