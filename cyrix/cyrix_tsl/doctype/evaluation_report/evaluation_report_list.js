frappe.listview_settings['Evaluation Report'] = {
	add_fields: ["status","name"],
	get_indicator: function (doc) {
        if (doc.status === "Installed and Completed/Repaired") {
            return [__("Installed and Completed"), "yellow", "status,=,Installed and Completed"];
        } 
        else if (doc.status === "Customer Testing") {
            return [__("Customer Testing"), "orange", "status,=,Customer Testing"];
        } 
        else if (doc.status === "Working") {
            return [__("Working"), "green", "status,=,Working"];
        }
        else if (doc.status === "Spare Parts") {
            return [__("Spare Parts"), "blue", "status,=,Spare Parts"];
        }
        else if (doc.status === "Extra Parts") {
            return [__("Extra Parts"), "cyan", "status,=,Extra Parts"];
        }
        else if (doc.status === "Comparison") {
            return [__("Comparison"), "yellow", "status,=,Comparison"];
        }
        else if (doc.status === "Internal Extra Parts") {
            return [__("Internal Extra Parts"), "pink", "status,=,Internal Extra Parts"];
        }
        else if (doc.status === "Return Not Repaired") {
            return [__("Return Not Repaired"), "red", "status,=,Return Not Repaired"];
        }
        else if (doc.status === "RNP-Return No Parts") {
            return [__("RNP-Return No Parts"), "red", "status,=,RNP-Return No Parts"];
        }
        else if (doc.status === "Return No Fault") {
            return [__("Return No Fault"), "green", "status,=,Return No Fault"];
        }
        else if (doc.status === "Supplier Quoted") {
            return [__("Supplier Quoted"), "green", "status,=,Supplier Quoted"];
        }
        else if(doc.docstatus === 0){
            return [__("ghgffh"), "green", "docstatus,=,0"];
        }
    },
};