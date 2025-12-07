frappe.listview_settings['Supply Order Data'] = {
	add_fields: ["status","name","priority_status"],
	get_indicator: function (doc) {
        if (doc.status === "Inquiry") {
            return [__("Inquiry"), "blue", "status,=,Inquiry"];
        }
        else if (doc.status === "Searching Items") {
            return [__("Searching Items"), "yellow", "status,=,Searching Items"];
        } else if (doc.status === "Not Found") {
            return [__("Not Found"), "red", "status,=,Not Found"];
        }
        else if (doc.status === "Internal Quotation") {
            return [__("Internal Quotation"), "orange", "status,=,Internal Quotation"];
        }
        else if (doc.status === "Quoted") {
            return [__("Quoted"), "green", "status,=,Quoted"];
        }
        else if (doc.status === "Unpaid") {
            return [__("Unpaid"), "red", "status,=,Unpaid"];
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
        else if (doc.status === "Ordered") {
            return [__("Ordered"), "cyan", "status,=,Ordered"];
        }
        else if (doc.status === "Shipped") {
            return [__("Shipped"), "pink", "status,=,Shipped"];
        }
        else if (doc.status === "Partially Received") {
            return [__("Partially Received"), "red", "status,=,Partially Received"];
        }
        else if (doc.status === "Received") {
            return [__("Received"), "yellow", "status,=,Received"];
        }
        else if (doc.status === "Paid") {
            return [__("Paid"), "green", "status,=,Paid"];
        }
        else if (doc.status === "Delivered") {
            return [__("Delivered"), "cyan", "status,=,Delivered"];
        }
        else if (doc.status === "Partially Delivered") {
            return [__("Partially Delivered"), "red", "status,=,Partially Delivered"];
        }
        else if (doc.status === "Invoiced") {
                return [__("Invoiced"), "cyan", "status,=,Invoiced"];
        }
        else if (doc.status === "Parts Priced") {
                return [__("Parts Priced"), "green", "status,=,Parts Priced"];
        }
        else if (doc.status === "Bid Submitted") {
                return [__("Bid Submitted"), "green", "status,=,Bid Submitted"];
        }
        else if (doc.status === "Awarded") {
                return [__("Awarded"), "green", "status,=,Awarded"];
        }
        else if (doc.status === "Lost") {
                return [__("Lost"), "green", "status,=,Lost"];
        }
        else if (doc.priority_status == "Not Urgent") {
                return [__("Not Urgent"), "gray", "priority_status=Not Urgent"];
        }
    },
};
