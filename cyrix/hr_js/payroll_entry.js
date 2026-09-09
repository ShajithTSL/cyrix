frappe.ui.form.on('Payroll Entry', {
    refresh: function(frm) {
        frm.add_custom_button('Download Report', () => {
            if (frm.doc.salary_slips_submitted == 1){
                var status = "Submitted"
            }
            else{
                var status = "Draft"
            }
            let d = new frappe.ui.Dialog({
                title: 'Download Report',
                fields: [
                    {
                        label: 'Document Status',
                        fieldname: 'docstatus',
                        fieldtype: 'Select',
                        options: "Draft\nSubmitted\nCancelled",
                        default: status,
                        reqd: 1
                    },
                    {
                        label: 'Download As',
                        fieldname: 'file_type',
                        fieldtype: 'Select',
                        options: ['PDF', 'Excel'],
                        onchange: function() {
                            toggle_download_button();
                        }
                    }
                ],
                primary_action_label: 'Download',
                primary_action(values) {


                    d.hide();

                    if (values.file_type == "PDF") {
                        frappe.call({
                            method: "cyrix.hr_py.salary_register.download_custom_payroll_pdf",
                            args: {
                                docname: frm.doc.name,
                            },
                            callback: function(r) {
                                if (r.message) {
                                    window.open(r.message);
                                } else {
                                    frappe.msgprint("Failed to generate PDF");
                                }
                            }
                        });
                    } else {
                        var path = "cyrix.hr_py.salary_register.salary_register_excel";
                        var args = 'name=%(name)s&doc_status=%(doc_status)s';

                        window.location.href = repl(frappe.request.url + '?cmd=%(cmd)s&%(args)s', {
                            cmd: path,
                            args: args,
                            name: frm.doc.name,
                            doc_status: values.docstatus
                        });
                    }
                }
            });

            // 🔁 Helper function to enable/disable Download button
            function toggle_download_button() {
                const values = d.get_values();
                const any_selected = values.file_type;

                // Enable or disable the primary action (Download)
                d.get_primary_btn().prop('disabled', !any_selected);
            }


            // Disable the Download button initially
            d.get_primary_btn().prop('disabled', true);

            d.show();
        });
    }

});
