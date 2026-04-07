// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("WO Approval", {
	download:function(frm){
		if (frm.doc.type == "WO Approval"){

			var print_format ="WO Approval";
			var f_name = "WO Approval"
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("WO Approval")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}



		if (frm.doc.type == "Sales Summary"){

			var print_format ="Sales Summary";
			var f_name = "Sales Summary"
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("WO Approval")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}


		if (frm.doc.type == "Weekly Lab Report"){
			var print_format ="Weekly Lab Report";
			var f_name = "Weekly Lab Report"
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("WO Approval")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}
			
		
		},
});
