frappe.ui.form.on('Quotation', {
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
                    if(frm.doc.quotation_type == "Customer Quotation - Site Visit"){
                        var rev_type = "Customer Quotation - SV - Revised"
                    }
                    if(frm.doc.quotation_type == "Customer Quotation - BQ"){
                        var rev_type = "Customer Quotation - BQ - Revised"
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
                const quotation_formats = {
                    "Internal Quotation - Supply": {
                        label: "Internal Quotation",
                        format: "INT/KW/SO - V1"
                    },
                    "Customer Quotation - Supply": {
                        label: "Customer Quotation",
                        format: "CUS/KW/SO-V1"
                    },
                    "Internal Quotation - Repair": {
                        label: "Internal Quotation",
                        format: "INT/KW/JO - V1"
                    },
                    "Customer Quotation - Repair": {
                        label: "Customer Quotation",
                        format: "CUS/KW/JO - V1"
                    }
                };

                let config = quotation_formats[frm.doc.quotation_type];

                if (config) {
                    frm.add_custom_button(__(config.label), function () {

                        let f_name = frm.doc.name;

                        window.open(
                            frappe.urllib.get_full_url(
                                "/api/method/frappe.utils.print_format.download_pdf?"
                                + "doctype=" + encodeURIComponent(frm.doc.doctype)
                                + "&name=" + encodeURIComponent(f_name)
                                + "&trigger_print=1"
                                + "&format=" + encodeURIComponent(config.format)
                                + "&no_letterhead=0"
                            )
                        );

                    }, __('Print'));
                }
            },
            () => {
                if(frm.doc.docstatus == 1 && frm.doc.workflow_state == "Approved by Customer"){
				    frm.add_custom_button(__('Invoice Request'), function(){
                        frappe.call({
                            method: "cyrix.custom_py.quotation.create_invoice_request",
                            args: {
                                "source": frm.doc.name,
                                "user": frappe.session.user,
                            },
                            callback: function(r) {
                                if(r.message) {
                                    var doc = frappe.model.sync(r.message);
                                    frappe.db.get_value('Customer', {'name':frm.doc.customer}, ['customer_type'], (r) => {
                                        if(r.customer_type == "Company"){
                                            // if(!frm.doc.customer_address){
                                            //     frappe.throw("Please ensure the customer address is filled in; otherwise, the quotation will not be created. 😞 ")
                                            // }
                                            frappe.set_route("Form", doc[0].doctype, doc[0].name);
                                        }
                                    });
                                }
                            }
                        });
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
                    },
                    add_filters_group: 1,
                    get_query() {
                        return {
                            filters: {
                                company: frm.doc.company,
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
                        frappe.call({
                            method: "cyrix.custom_py.quotation.get_supply_order_data",
                            args: {
                                "supply_order_data": selections
                            },
                            callback: function(r) {
                                if(r.message) {
                                    console.log(r.message)
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
                frappe.call({
                    method: "cyrix.custom_py.quotation.create_sales_invoice",
                    args: {
                        "source": frm.doc.name,
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
            }, ('Create'))
        }
    }
})