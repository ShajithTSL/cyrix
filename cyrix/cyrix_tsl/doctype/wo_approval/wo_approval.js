// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("WO Approval", {
	download:function(frm){

		if (frm.doc.type == "Sales Weekly Summary"){
			var print_format = "Sales Weekly Summary";
			var f_name = "Sales Weekly Summary"
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("WO Approval")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}



		if (frm.doc.type == "Sales Daily Summary"){
			var print_format = "Sales Daily Summary";
			var f_name = "Sales Daily Summary"
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("WO Approval")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}


		
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

		if (frm.doc.type == "AMC"){

			var print_format ="AMC";
			var f_name = "AMC"
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

		if (frm.doc.type == "Target Master"){
			var print_format = "Target Master";
			var f_name = "Target Master"
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



		if (frm.doc.type == "Statement of Customer"){
			var print_format ="Statement of Customer";
			var f_name = "Statement of Customer"
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
