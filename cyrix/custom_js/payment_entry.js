frappe.ui.form.on("Payment Entry", {
    get_job_orders:function(frm){
        if(frm.doc.docstatus == 0){
            let remaining_paid = frm.doc.paid_amount || 0;
            frappe.call({
                method:"cyrix.custom_py.payment_entry.get_jo_so_details",
                args:{                
                    'references':frm.doc.references
                },
                callback: function(r) {
                    let jo_so_info = r.message || [];

                    frm.set_value("job_order_table",jo_so_info)
                    frm.doc.job_order_table.forEach((row) => {
                        let jo_so = jo_so_info.find(
                            (jo) => jo.reference_name === row.reference_name
                        );

                        // If job order data is found, calculate the remaining amount and allocate
                        if (jo_so) {
                            row.remaining_to_be_paid = jo_so.remaining_to_be_paid;

                            // Calculate the allocate_amount
                            let to_allocate = Math.min(row.remaining_to_be_paid, remaining_paid);
                            row.allocate_amount = to_allocate;
                            remaining_paid -= to_allocate;

                            // If all the remaining paid amount is allocated, break the loop
                            if (remaining_paid <= 0) {
                                return;
                            }
                        }
                    });

                    // Refresh the field to update the table
                    frm.refresh_field('job_order_table');
                }
            });
        }
    },
    refresh(frm){
        cur_frm.get_field("job_order_table").grid.cannot_add_rows = true;
        refresh_field("job_order_table");
    },
    validate_allocated_amount(frm){
        var total = 0
        $.each(frm.doc.job_order_table, function(i,j){
            total += j.allocate_amount
        })
        if(total > frm.doc.paid_amount){
            frappe.msgprint("Allocated Amount <b>"+total+"</b> cannot be greater than Paid Amount- <b>"+frm.doc.paid_amount+"</b>")
            frappe.validated = false
        }
    },
    validate: function(frm){
        frm.trigger("validate_allocated_amount")
    }
})


frappe.ui.form.on('Job Order table', {	
	allocate_amount:function(frm, cdt, cdn){
		var row = locals[cdt][cdn]
        frm.trigger("validate_allocated_amount")
	},
});