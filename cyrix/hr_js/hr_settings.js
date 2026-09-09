frappe.ui.form.on("Annual Leave Policy",{ 
	total_days:function(frm,cdt,cdn){
		var item = locals[cdt][cdn];
		if(item.total_days){
			item.monthly_allocation = item.total_days / 12;
			cur_frm.refresh_fields();
	    }
	},
})