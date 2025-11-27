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
    },
};