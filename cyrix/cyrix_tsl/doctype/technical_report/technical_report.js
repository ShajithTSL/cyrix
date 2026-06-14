// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Technical Report", {

    customer: function (frm) {
		if (!frm.doc.customer) {
			return
		}
		frappe.call({
			method: 'cyrix.cyrix_tsl.doctype.create_job_order.create_job_order.get_contacts',
			args: {
				"customer": frm.doc.customer,
			},
			callback(r) {
				if (r.message) {
					frm.set_query("incharge", function () {
						return {
							"filters": {
								"name": ["in", r.message[0]]
							}
						};
					});
					if (r.message[1]) {
						frm.set_query("sales_person", function () {
							return {
								"filters": {
									"name": ["in", r.message[1]]
								}
							};
						});
						frm.set_value("sales_person",r.message[1][0])
					}
				}
			}
		});
        frm.trigger("scf_query");
	},

    scf_query: function(frm) {        
        frm.set_query("service_call_form", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
                    ["customer", "=", frm.doc.customer]
				]
			}
		});
    },

    refresh: function(frm) {        
        frm.trigger("set_query");
        frm.add_custom_button(__("Print"), function () {
    
            let f_name = frm.doc.name;

            window.open(
                frappe.urllib.get_full_url(
                    "/api/method/frappe.utils.print_format.download_pdf?"
                    + "doctype=" + encodeURIComponent(frm.doc.doctype)
                    + "&name=" + encodeURIComponent(f_name)
                    + "&trigger_print=1"
                    + "&format=" + encodeURIComponent("Service Report - V2")
                    + "&no_letterhead=0"
                )
            );

        });
    },

    company: function(frm) {
        frm.trigger("set_query");
        frm.trigger("scf_query");
    },

    set_query: function(frm) {
        frm.set_query("department", function () {
			return {
				filters: [
					["company", "=", frm.doc.company],
				]
			}
		});   
        const territoryMap = frappe.boot.company_territories;
        if (territoryMap[frappe.defaults.get_default("company")]) {
			frm.set_query("customer", function () {
				return {
					filters: [
						["territory", "in", territoryMap[frappe.defaults.get_default("company")]]
					]
				};
			});
		}
        else if (frm.doc.company){
            frm.set_query("customer", function () {
                return {
                    filters: [
                        ["territory", "in", territoryMap[frm.doc.company]]
                    ]
                };
            });
        }   

        const branchMap = frappe.boot.company_branches;

		if (branchMap[frappe.defaults.get_default("company")]) {
			const branches = branchMap[frappe.defaults.get_default("company")];

			// If only one branch exists, auto-set it
			if (branches.length === 1) {
				frm.set_value("branch", branches[0]);
				frm.set_df_property("branch", "read_only", 1);
			}
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frappe.defaults.get_default("company")]]
					]
				};
			});
		}	
        else if (frm.doc.company) {
            const branches = branchMap[frm.doc.company];

			// If only one branch exists, auto-set it
			if (branches.length === 1) {
				frm.set_value("branch", branches[0]);
				frm.set_df_property("branch", "read_only", 1);
			}
			frm.set_query("branch", function () {
				return {
					filters: [
						["name", "in", branchMap[frm.doc.company]]
					]
				};
			});
        }
    },
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
