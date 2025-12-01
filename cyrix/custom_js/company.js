
frappe.ui.form.on('Company', {
    refresh: function (frm){
        const branchMap = frappe.boot.company_branches;

		if (branchMap[frm.doc.name]) {
            frm.set_query('branch', 'warehouse_list', function(doc, cdt, cdn) {
                return {
                    filters:[
                        ["name", "in", branchMap[frm.doc.name]]
                    ]
                };
            });
		}	
        frm.set_query('actual_warehouse', 'warehouse_list', function(doc, cdt, cdn) {
            var row = locals[cdt][cdn]
			return {
				filters:[
					['company', '=', doc.name],
					['is_repair_warehouse', '=', 0],
                    ['name','like',"%"+row.branch+"%"]
				]
			};
		});
        frm.set_query('repair_warehouse', 'warehouse_list', function(doc, cdt, cdn) {
            var row = locals[cdt][cdn]
			return {
				filters:[
					['company', '=', doc.name],
					['is_repair_warehouse', '=', 1],
                    ['name','like',"%"+row.branch+"%"]
				]
			};
		});
    }
})