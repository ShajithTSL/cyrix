// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Evaluation Report", {

	check_all_checked(frm) {
		const child_table = frm.doc.items || [];  // Get the child table records
		const allChecked = child_table.every(row => row.released === 1); // Check if all checkboxes are enabled

		if (!allChecked) {
			frm.trigger("release_parts")
		}
	},

	// Once all the materials were received, Release Parts button will be visible
	release_parts: function(frm){
		const child_table = frm.doc.items || [];
		const scrapCount = child_table.filter(row => row.from_scrap === 1).length;
		const totalItems = child_table.length;

		const allScrap = (scrapCount === totalItems);        // all items are scrap
		const hasNonScrap = scrapCount < totalItems;         // at least one non-scrap item exists
		const singleScrap = (totalItems === 1 && scrapCount === 1);  // one item & it is scrap

		if (frm.doc.parts_availability == "Yes" && frm.doc.docstatus == 1) {

			// Show button ONLY if there is at least one non-scrap item
			if (hasNonScrap && !singleScrap) {
				frm.add_custom_button(__("Release Parts"), function () {
					frappe.call({
						method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.release_parts",
						args:{
							'name':frm.doc.name,
						},
					});
				}, __('Create'));
			}
		}
	},

	// Item Creation
	create_sku: function(frm){
		if (frm.is_dirty()) {
			frappe.throw("Save the document first")
		}
		frappe.call({
			method:"cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.sku_creation",
			args:{
				doc:cur_frm.doc
			},
			callback(r){
				frm.refresh_fields()
				cur_frm.reload_doc();
			}
		})
	},
	// Request for Quotation option
	create_rfq: function(frm){
		if(frm.doc.docstatus == 1 && frm.doc.parts_availability == "No"){
			frm.add_custom_button(__("Request for Quotation"), function(){
				frappe.call({
					method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_rfq",
					args: {
						name: frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", doc[0].doctype, doc[0].name);
						}
					}
				});
			},__('Create'));
		}
	},
    if_parts_required:function(frm){
		if(frm.doc.if_parts_required){
            frm.set_value("status","Spare Parts")
		}
	},
	refresh: function(frm){
		frm.trigger("check_all_checked")
		frm.fields_dict['items'].grid.get_field('part').get_query = function(frm, cdt, cdn) {
			var child = locals[cdt][cdn];
			var d = {};
			d['item_group'] = "Components";
			if(child.model){
				d['model'] = child.model;
			}
			if(child.category){
				d['category'] = child.category;
			}
			if(child.sub_category){
				d['sub_category'] = child.sub_category;
			}
			return{
				filters: d
			}
		}
		set_field_options("status", ["Internal Extra Parts","Extra Parts","Working","Spare Parts","Comparison","Parts Missing","Return Not Repaired","Return No Fault","RNP-Return No Parts"])
		if(frm.doc.docstatus == 1){
			frm.set_df_property('estimated_repair_time', 'hidden', 1);
			frm.set_df_property('evaluation_time', 'hidden', 1);
			frm.set_df_property('extra_repair_time', 'hidden', 1);
		}
		frm.trigger("create_rfq")
		if(frm.doc.status == "Extra Parts"){
			frm.set_df_property('extra_repair_time', 'hidden', 0);
		}
	}
});

frappe.ui.form.on('Part Sheet Item', {	
	part: function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		if(row.part && row.qty){
			frappe.call({
				method :"cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.get_valuation_rate",
				args :{
					"item" :row.part,
					"qty":row.qty,
					"warehouse":frm.doc.warehouse
				},
				callback :function(r){
					console.log(r.message.status)
					frappe.model.set_value(cdt, cdn, "price_ea", r.message.price);
					frappe.model.set_value(cdt, cdn, "parts_availability", r.message.status);
					row.total = row.qty * r.message.price;
					let tot_qty = 0
					let tot_amount = 0
					for(let i in frm.doc.items){
						tot_qty += frm.doc.items[i].qty
						tot_amount += frm.doc.items[i].total
					}
					frm.set_value("total_qty", tot_qty)
					frm.set_value("total_amount", tot_amount)
					frm.refresh_fields();
				}
			})
		}
		frm.refresh();
	},
	qty:function(frm, cdt, cdn){
		var row = locals[cdt][cdn]
		if(row.qty && row.part){
			frm.script_manager.trigger('part',cdt,cdn)
	   	}
	},
});
