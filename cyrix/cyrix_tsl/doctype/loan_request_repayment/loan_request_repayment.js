// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Loan Request Repayment", {
	validate(frm) {
        if(frm.doc.__islocal){
            frm.set_value("payment_entry",'')
        }
        let remaining = frm.doc.amount_paid || 0;
        let total_principal = frm.doc.repayment_details.reduce(
            (sum, row) => sum + (row.paid_principal_amount || 0), 0
        );

        // Warn if repayment exceeds total principal
        if (remaining > total_principal) {
            frappe.msgprint({
                title: "Amount Exceeds Limit",
                message: `Repayment amount - <b>${remaining}</b> exceeds total principal - <b>${total_principal}</b>.`,
                indicator: "red"
            });
            frappe.validated = false
        }
	},
    amount_paid(frm) {
        let remaining = frm.doc.amount_paid || 0;

        if (!frm.doc.repayment_details) return;
        // Calculate total principal in child rows
        let total_principal = frm.doc.repayment_details.reduce(
            (sum, row) => sum + (row.paid_principal_amount || 0), 0
        );

        // Warn if repayment exceeds total principal
        if (remaining > total_principal) {
            frappe.msgprint({
                title: "Amount Exceeds Limit",
                message: `Repayment amount - <b>${remaining}</b> exceeds total principal - <b>${total_principal}</b>.`,
                indicator: "red"
            });
        }

        frm.doc.repayment_details.forEach(row => {
            // Reset total_payment before recalculating
            row.total_payment = 0;

            if (remaining <= 0) return;

            // How much this row can take
            let allowable = row.paid_principal_amount - (row.total_payment || 0);

            if (allowable <= 0) return;

            if (remaining >= allowable) {
                row.total_payment = allowable;
                remaining -= allowable;
            } else {
                row.total_payment = remaining;
                remaining = 0;
            }
        });

        frm.refresh_field("repayment_details");
    }
});
