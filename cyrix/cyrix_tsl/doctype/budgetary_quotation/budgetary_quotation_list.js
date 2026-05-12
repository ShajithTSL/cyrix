frappe.listview_settings['Budgetary Quotation'] = {
	add_fields: ["status","name"],
	get_indicator: function (doc) {
        if (doc.status === "Inquiry") {
            return [__("Inquiry"), "blue", "status,=,Inquiry"];
        }
        else if (doc.status === "Parts Priced") {
            return [__("Parts Priced"), "green", "status,=,Parts Priced"];
        }
        else if (doc.status === "IQ-Internally Quoted") {
            return [__("IQ-Internally Quoted"), "cyan", "status,=,IQ-Internally Quoted"];
        }
        else if (doc.status === "A-Approved") {
            return [__("A-Approved"), "green", "status,=,A-Approved"];
        }
        else if (doc.status === "Q-Quoted") {
            return [__("Q-Quoted"), "green", "status,=,Q-Quoted"];
        }
        else if (doc.status === "Invoiced") {
            return[__("Invoiced"),"pink","status,=,Invoiced"];
        }
        else if (doc.status === "Ordered") {
            return [__("Ordered"), "green", "status,=,Ordered"];
        }
        else if (doc.status === "Partially Received") {
            return [__("Partially Received"), "red", "status,=,Partially Received"];
        }
        else if (doc.status === "Received") {
            return [__("Received"), "yellow", "status,=,Received"];
        }
        else if (doc.status === "Delivered") {
            return [__("Delivered"), "cyan", "status,=,Delivered"];
        }
        else if (doc.status === "Partially Delivered") {
            return [__("Partially Delivered"), "red", "status,=,Partially Delivered"];
        }        
        else if (doc.status === "Paid") {
            return [__("Paid"), "green", "status,=,Paid"];
        }
        else if (doc.status === "Unpaid") {
            return [__("Unpaid"), "red", "status,=,Unpaid"];
        }
        else if (doc.status === "Partially Paid") {
            return [__("Partially Paid"), "yellow", "status,=,Partially Paid"];
        }
    },
};