frappe.ui.form.on('Quotation', {
    transaction_date: function(frm) {
        if (frappe.boot.sysdefaults.quotation_valid_till) {
            frm.set_value(
                "valid_till",
                frappe.datetime.add_days(
                    frm.doc.transaction_date,
                    frappe.boot.sysdefaults.quotation_valid_till
                )
            );
        } else {
            frm.set_value("valid_till", frappe.datetime.add_months(frm.doc.transaction_date, 1));
        }
    },
    type_of_approval: function(frm) {
        if (frm.doc.type_of_approval){
            frm.set_df_property("approval_date", "reqd", 1);
        }
        else{
            frm.set_df_property("approval_date", "reqd", 0);
        }
    },

    before_workflow_action: async (frm) => {

        if(frm.doc.workflow_state == "Quoted to Customer"){
			let promise = new Promise((resolve, reject) => {
				if (frm.selected_workflow_action == "Approve") {
                    if (!frm.doc.type_of_approval){
                        frappe.utils.scroll_to(frm.fields_dict.type_of_approval.$wrapper);
                        frm.fields_dict.type_of_approval.set_focus();
                    }
				}
                if (frm.doc.warranty_duration == 0){
                    frm.fields_dict.warranty_duration.set_focus();
                }
				resolve();
			});
			await promise.catch(() => frappe.throw());
		}
    },



    filter_reference: function(frm) {
        let job_orders = [];

        if (frm.doc.items && frm.doc.items.length) {
            frm.doc.items.forEach(row => {
                if (row.job_order_data) {
                    job_orders.push(row.job_order_data);
                }
            });
        }

        frm.fields_dict['online_price_list'].grid.get_field('job_order_data').get_query = function(doc, cdt, cdn) {

            if (!job_orders.length) {
                return {
                    filters: {
                        name: ['=', '']
                    }
                };
            }

            return {
                filters: {
                    name: ['in', job_orders]
                }
            };
        };
    },

    validate: function(frm){
        frm.trigger("naming_series")
    },
    quotation_type: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            const naming_series = {
                "Internal Quotation - Repair": {
                    "Kuwait": { series: "IQR-K.YY.-", status: "IQ-Internally Quoted" },
                    "Dammam": { series: "IQR-D.YY.-", status: "IQ-Internally Quoted" },
                    "Riyadh": { series: "IQR-R.YY.-", status: "IQ-Internally Quoted" },
                    "Jeddah": { series: "IQR-J.YY.-", status: "IQ-Internally Quoted" },
                    "Dubai": { series: "IQR-DU.YY.-", status: "IQ-Internally Quoted" }
                },
                "Internal Quotation - Supply": {
                    "Kuwait": { series: "IQS-K.YY.-", status: "IQ-Internally Quoted" },
                    "Dammam": { series: "IQS-D.YY.-", status: "IQ-Internally Quoted" },
                    "Riyadh": { series: "IQS-R.YY.-", status: "IQ-Internally Quoted" },
                    "Jeddah": { series: "IQS-J.YY.-", status: "IQ-Internally Quoted" },
                    "Dubai": { series: "IQS-DU.YY.-", status: "IQ-Internally Quoted" }
                },
                "Internal Quotation - Site Visit": {
                    "Kuwait": { series: "IQSV-K.YY.-"},
                    "Dammam": { series: "IQSV-D.YY.-"},
                    "Riyadh": { series: "IQSV-R.YY.-"},
                    "Jeddah": { series: "IQSV-J.YY.-"},
                    "Dubai": { series: "IQSV-DU.YY.-"}
                },
                "Internal Quotation - BQ": {
                    "Kuwait": { series: "IBQ-K.YY.-"},
                    "Dammam": { series: "IBQ-D.YY.-"},
                    "Riyadh": { series: "IBQ-R.YY.-"},
                    "Jeddah": { series: "IBQ-J.YY.-"},
                    "Dubai": { series: "IBQ-DU.YY.-"}
                },
                "Internal Quotation - MC": {
                    "Kuwait": { series: "IQMC-K.YY.-"},
                    "Dammam": { series: "IQMC-D.YY.-"},
                    "Riyadh": { series: "IQMC-R.YY.-"},
                    "Jeddah": { series: "IQMC-J.YY.-"},
                    "Dubai": { series: "IQMC-DU.YY.-"}
                },
                "Customer Quotation - Repair": {
                    "Kuwait": { series: "CQR-K.YY.-", status: "A-Approved" },
                    "Dammam": { series: "CQR-D.YY.-", status: "A-Approved" },
                    "Riyadh": { series: "CQR-R.YY.-", status: "A-Approved" },
                    "Jeddah": { series: "CQR-J.YY.-", status: "A-Approved" },
                    "Dubai": { series: "CQR-DU.YY.-", status: "A-Approved" }
                },
                "Customer Quotation - Supply": {
                    "Kuwait": { series: "CQS-K.YY.-", status: "A-Approved" },
                    "Dammam": { series: "CQS-D.YY.-", status: "A-Approved" },
                    "Riyadh": { series: "CQS-R.YY.-", status: "A-Approved" },
                    "Jeddah": { series: "CQS-J.YY.-", status: "A-Approved" },
                    "Dubai": { series: "CQS-DU.YY.-", status: "A-Approved" }
                },
                "Customer Quotation - R - Revised": {
                    "Kuwait": { series: "CQR-K.YY.-", status: "A-Approved" },
                    "Dammam": { series: "CQR-D.YY.-", status: "A-Approved" },
                    "Riyadh": { series: "CQR-R.YY.-", status: "A-Approved" },
                    "Jeddah": { series: "CQR-J.YY.-", status: "A-Approved" },
                    "Dubai": { series: "CQR-DU.YY.-", status: "A-Approved" }
                },
                "Customer Quotation - S - Revised": {
                    "Kuwait": { series: "CQS-K.YY.-", status: "A-Approved" },
                    "Dammam": { series: "CQS-D.YY.-", status: "A-Approved" },
                    "Riyadh": { series: "CQS-R.YY.-", status: "A-Approved" },
                    "Jeddah": { series: "CQS-J.YY.-", status: "A-Approved" },
                    "Dubai": { series: "CQS-DU.YY.-", status: "A-Approved" }
                },
                "Customer Quotation - Site Visit": {
                    "Kuwait": { series: "CQSV-K.YY.-"},
                    "Dammam": { series: "CQSV-D.YY.-"},
                    "Riyadh": { series: "CQSV-R.YY.-"},
                    "Jeddah": { series: "CQSV-J.YY.-"},
                    "Dubai": { series: "CQSV-DU.YY.-"}
                },
                "Customer Quotation - SV - Revised": {
                    "Kuwait": { series: "CQSV-K.YY.-"},
                    "Dammam": { series: "CQSV-D.YY.-"},
                    "Riyadh": { series: "CQSV-R.YY.-"},
                    "Jeddah": { series: "CQSV-J.YY.-"},
                    "Dubai": { series: "CQSV-DU.YY.-"}
                },
                "Customer Quotation - BQ": {
                    "Kuwait": { series: "CBQ-K.YY.-"},
                    "Dammam": { series: "CBQ-D.YY.-"},
                    "Riyadh": { series: "CBQ-R.YY.-"},
                    "Jeddah": { series: "CBQ-J.YY.-"},
                    "Dubai": { series: "CBQ-DU.YY.-"}
                },
                "Customer Quotation - MC": {
                    "Kuwait": { series: "CQMC-K.YY.-"},
                    "Dammam": { series: "CQMC-D.YY.-"},
                    "Riyadh": { series: "CQMC-R.YY.-"},
                    "Jeddah": { series: "CQMC-J.YY.-"},
                    "Dubai": { series: "CQMC-DU.YY.-"}
                },
                "Customer Quotation - MC - Revised": {
                    "Kuwait": { series: "CQMC-K.YY.-"},
                    "Dammam": { series: "CQMC-D.YY.-"},
                    "Riyadh": { series: "CQMC-R.YY.-"},
                    "Jeddah": { series: "CQMC-J.YY.-"},
                    "Dubai": { series: "CQMC-DU.YY.-"}
                },
            };

            // Get the status (and optionally the series)
            const series = naming_series[frm.doc.quotation_type]?.[frm.doc.branch]?.series;
            if (series) {
                frm.set_value('naming_series', series);
            }
        }
    },
    onload:function(frm){
        frm.trigger("filter_reference")
        frm.remove_custom_button("Create")
        frm.remove_custom_button("Sales Invoice")
    },
    refresh:function(frm){
        frappe.run_serially([
            () => {
                if(frm.doc.workflow_state == "Approved by Management"){
                    if(frm.doc.quotation_type == "Internal Quotation - Repair"){
                        var quote_type = "Customer Quotation - Repair"
                    }
                    if(frm.doc.quotation_type == "Internal Quotation - Supply"){
                        var quote_type = "Customer Quotation - Supply"
                    }
                    if(frm.doc.quotation_type == "Internal Quotation - Site Visit"){
                        var quote_type = "Customer Quotation - Site Visit"
                    }
                    if(frm.doc.quotation_type == "Internal Quotation - BQ"){
                        var quote_type = "Customer Quotation - BQ"
                    }
                    if(frm.doc.quotation_type == "Internal Quotation - MC"){
                        var quote_type = "Customer Quotation - MC"
                    }
                    frm.add_custom_button("Customer Quotation", function(){
                        frappe.call({
                            method: "cyrix.custom_py.quotation.get_quote",
                            args: {
                                "source": frm.doc.name,
                                "type":quote_type
                            },
                            callback: function(r) {
                                if(r.message) {
                                    var doc = frappe.model.sync(r.message);
                                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                                }
                            }
                        });
                    },__("Create"))
                }
            },
       
            () => {
                 if(frm.doc.workflow_state == "Rejected by Customer"){
                    if (["Customer Quotation - R - Revised","Customer Quotation - Repair"].includes(frm.doc.quotation_type)){
                        var rev_type = "Customer Quotation - R - Revised"
                    }
                    if (["Customer Quotation - S - Revised","Customer Quotation - Supply"].includes(frm.doc.quotation_type)){
                        var rev_type = "Customer Quotation - S - Revised"
                    }
                    if (["Customer Quotation - Site Visit","Customer Quotation - SV - Revised"].includes(frm.doc.quotation_type)){
                        var rev_type = "Customer Quotation - SV - Revised"
                    }
                    if (["Customer Quotation - BQ","Customer Quotation - BQ - Revised"].includes(frm.doc.quotation_type)){
                        var rev_type = "Customer Quotation - BQ - Revised"
                    }
                    if (["Customer Quotation - MC","Customer Quotation - MC - Revised"].includes(frm.doc.quotation_type)){
                        var rev_type = "Customer Quotation - MC - Revised"
                    }
                    frm.add_custom_button("Revised Quotation", function(){
                        frappe.call({
                            method: "cyrix.custom_py.quotation.get_quote",
                            args: {
                                "source": frm.doc.name,
                                "type": rev_type
                            },
                            callback: function(r) {
                                if(r.message) {
                                    var doc = frappe.model.sync(r.message);
                                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                                }
                            }
                        });
                    },__("Create"))
                }
            },

            () => frm.trigger("filter_reference"),
            () => frm.trigger("fetch_job_order_data"),
            () => frm.trigger("fetch_supply_order_data"),
            () => frm.trigger("create_sales_invoice"),
            () => {
                if(frm.doc.docstatus == 1 && frm.doc.workflow_state == "Approved by Customer"){
				    frm.add_custom_button(__('Invoice Request'), function(){
                        let allowed_customers = [];

                        if (frm.doc.party_name) {
                            allowed_customers.push(frm.doc.party_name);
                        }

                        if (frm.doc.child_customer) {
                            allowed_customers.push(frm.doc.child_customer);
                        }

                        if (frm.doc.parent_customer) {
                            allowed_customers.push(frm.doc.parent_customer);
                        }

                        let d = new frappe.ui.Dialog({
                            title: 'Select Customer',
                            fields: [
                                {
                                    label: 'Customer',
                                    fieldname: 'customer',
                                    fieldtype: 'Link',
                                    options: 'Customer',
                                    reqd: 1,
                                    get_query: function() {
                                        return {
                                            filters: [
                                                ['Customer', 'name', 'in', allowed_customers]
                                            ]
                                        };
                                    }
                                }
                            ],
                            primary_action_label: 'Proceed',
                            primary_action(values) {
                                if (!values.customer) {
                                    frappe.msgprint('Please select a customer');
                                    return;
                                }

                                d.hide();
                                frappe.call({
                                    method: "cyrix.custom_py.quotation.create_invoice_request",
                                    args: {
                                        "source": frm.doc.name,
                                        "user": frappe.session.user,
                                        "customer": values.customer
                                    },
                                    callback: function(r) {
                                        if(r.message) {
                                            var doc = frappe.model.sync(r.message);
                                            frappe.db.get_value('Customer', {'name':frm.doc.customer}, ['customer_type'], (r) => {
                                                if(r.customer_type == "Company"){
                                                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                                                }
                                            });
                                        }
                                    }
                                });
                            }
                        });
                        d.show();
                    }, ('Create'))
			    }			
            }
        ]);
    },
    setup :function(frm){
        frm.trigger("filter_reference")
    },
    fetch_job_order_data: function(frm){    
        if(frm.doc.docstatus == 0){
            frm.add_custom_button(__("Job Order Data"), function () {
                let dialog;  // Declare in outer scope

                dialog = new frappe.ui.form.MultiSelectDialog({
                    doctype: "Job Order Data",
                    target: frm,
                    setters: {
                        status: "",
                        customer:frm.doc.party_name
                    },
                    add_filters_group: 1,
                    get_query() {
                        return {
                            filters: {
                                company: frm.doc.company,
                                // customer: frm.doc.party_name,
                                docstatus: 1,
                                parent_jo: ["is", "not set"],
                                quotation: ["is", "not set"]
                            }
                        };
                    },
                    action(selections) {
                        frappe.call({
                            method: "cyrix.custom_py.quotation.get_job_order_data",
                            args: {
                                "job_order_data": selections
                            },
                            callback: function(r) {
                                if(r.message) {
                                    console.log(r.message)
                                    frm.set_value("items",r.message[0])
                                    frm.set_value("quotation_type","Internal Quotation - Repair")
                                    frm.set_value("branch",r.message[1])
                                    frm.set_value("technician_hours_spent",r.message[3])
                                    frm.set_value("pre_evaluation",r.message[2])
                                    cur_frm.refresh_fields();
                                    cur_dialog.hide();
                                }
                            }
                        });
                    }
                });
            },__("Get Items From"));
        }    
    },
    fetch_supply_order_data: function(frm){    
        if(frm.doc.docstatus == 0){
            frm.add_custom_button(__("Supply Order Data"), function () {
                let dialog;  // Declare in outer scope

                dialog = new frappe.ui.form.MultiSelectDialog({
                    doctype: "Supply Order Data",
                    target: frm,
                    setters: {
                        status: "",
                        customer:frm.doc.party_name
                    },
                    add_filters_group: 1,
                    get_query() {
                        return {
                            filters: {
                                company: frm.doc.company,
                                // customer: frm.doc.party_name,
                                docstatus: 1,
                                quotation: ["is", "not set"]
                            }
                        };
                    },
                    action(selections) {
                        frappe.call({
                            method: "cyrix.custom_py.quotation.get_supply_order_data",
                            args: {
                                "supply_order_data": selections
                            },
                            callback: function(r) {
                                if(r.message) {
                                    frm.set_value("items",r.message[0])
                                    frm.set_value("quotation_type","Internal Quotation - Supply")
                                    frm.set_value("branch",r.message[1])
                                    frm.set_value("party_name",r.message[2])
                                    cur_frm.refresh_fields();
                                    cur_dialog.hide();
                                }
                            }
                        });
                    }
                });
            },__("Get Items From"));
        }    
    },
    create_sales_invoice: function(frm){
        if(frm.doc.docstatus == 1 && frm.doc.workflow_state == 'Approved by Customer'){
            frm.add_custom_button(__('Sales Invoice'), function(){
                let allowed_customers = [];

                if (frm.doc.party_name) {
                    allowed_customers.push(frm.doc.party_name);
                }

                if (frm.doc.child_customer) {
                    allowed_customers.push(frm.doc.child_customer);
                }

                if (frm.doc.parent_customer) {
                    allowed_customers.push(frm.doc.parent_customer);
                }

                let d = new frappe.ui.Dialog({
                    title: 'Select Customer',
                    fields: [
                        {
                            label: 'Customer',
                            fieldname: 'customer',
                            fieldtype: 'Link',
                            options: 'Customer',
                            reqd: 1,
                            get_query: function() {
                                return {
                                    filters: [
                                        ['Customer', 'name', 'in', allowed_customers]
                                    ]
                                };
                            }
                        }
                    ],
                    primary_action_label: 'Proceed',
                    primary_action(values) {
                        if (!values.customer) {
                            frappe.msgprint('Please select a customer');
                            return;
                        }

                        d.hide();
                        frappe.call({
                            method: "cyrix.custom_py.quotation.create_sales_invoice",
                            args: {
                                "source": frm.doc.name,
                                "customer": values.customer
                            },
                            callback: function(r) {
                                if(r.message) {
                                    var doc = frappe.model.sync(r.message);
                                    frappe.route_options = {
                                        currency: frm.doc.currency,
                                        conversion_rate: frm.doc.conversion_rate
                                    }
                                    frappe.set_route("Form", doc[0].doctype, doc[0].name);
                                }
                            }
                        });
                    }
                });
                d.show();
            }, ('Create'))
        }
    },
    warranty_duration(frm) {
        convert_warranty(frm);
    },

    warranty_type(frm) {
        convert_warranty(frm);
    }
});

function convert_warranty(frm) {
    if (!frm.doc.warranty_duration || !frm.doc.warranty_type){
        frm.set_value("warranty_months",0);
        return;
    }

    if (frm.doc.warranty_type === "Years") {
        frm.set_value("warranty_months", frm.doc.warranty_duration * 12);
    } else {
        frm.set_value("warranty_months", frm.doc.warranty_duration);
    }
}