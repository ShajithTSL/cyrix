frappe.listview_settings['Maintenance Contract'] = {
	add_fields: ["status"],
	get_indicator: function (doc) {
        if (doc.status === "Internal Quotation") {
            return [__("Internal Quotation"), "orange", "status,=,Internal Quotation"];
        }
        else if (doc.status === "Quoted") {
            return [__("Quoted"), "green", "status,=,Quoted"];
        }
        else if (doc.status === "Partially Paid") {
            return [__("Partially Paid"), "yellow", "status,=,Partially Paid"];
        }
        else if (doc.status === "Approved") {
            return [__("Approved"), "green", "status,=,Approved"];
        }
        else if (doc.status === "Invoiced") {
                return [__("Invoiced"), "green", "status,=,Invoiced"];
        }
        else if (doc.status === "Not Approved") {
            return [__("Not Approved"), "red", "status,=,Not Approved"];
        }
        else if (doc.status === "Paid") {
            return [__("Paid"), "green", "status,=,Paid"];
        }
        else if (doc.status === "Invoiced") {
                return [__("Invoiced"), "cyan", "status,=,Invoiced"];
        }
        else if (doc.status === "Pending Internal Approval") {
                return [__("Pending Internal Approval"), "orange", "status,=,Pending Internal Approval"];
        }
        else if (doc.status === "Cancelled") {
                return [__("Cancelled"), "red", "status,=,Cancelled"];
        }
    },
};
