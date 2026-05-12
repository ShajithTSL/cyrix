// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Evaluation Report", {

	 
    send(frm){
         frappe.call({
		method: "cyrix.custom_py.mail_notification.purchase_msg_to_info",
		args: {
			"com": frm.doc.company,
			"branch":frm.doc.branch,
			"ev":frm.doc.name,
			"sender":frappe.session.user
		},
		
		callback: function(r) {
			if(r.message) {
		
				
			}
		}
				
		})
        
    },


	
	// Once all the materials were received, Release Parts button will be visible
	release_parts: function(frm){
		var s = 0 
		$.each(frm.doc.items, function(i,d) {
			if(d.parts_availability == "Yes"){
				s = s + 1
			}
		})
		
		if(s > 0){
			frm.add_custom_button(__("Release Parts"), function () {
				open_release_dialog(frm);
			}, __('Create'));
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
		frm.trigger("release_parts")
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
		set_field_options("status", ["Installed and Completed/Repaired","Board Evaluation","Internal Extra Parts","Extra Parts","Working","Spare Parts","Comparison","Parts Missing","Return Not Repaired","Return No Fault","RNP-Return No Parts"])
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
	create:function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_item",
			args:{
				model:child.model || '',
				part_no:child.part || '',
				category:child.category || '',
				sub_category:child.sub_category || '',
				description:child.part_name || '',
				package:child.part_description || '',
			},
			callback(r){
				if(r.message){
					child.part = r.message
					frm.refresh_field("items")
					frm.dirty();
					frm.save();
					frm.save();
				}
			}
		})
	},
});

// Dialog for releasing parts
async function open_release_dialog(frm) {

    // 🔹 Get calculated data from backend
    let r = await frappe.call({
        method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.get_release_items",
        args: {
            docname: frm.doc.name
        }
    });

	let items = r.message || [];

	var warehouse_list = {
		"Kuwait": "Kuwait - CT-K"
	}
    let d = new frappe.ui.Dialog({
		
        title: {warehouse: frm.doc.branch} ? `Release Items from ${warehouse_list[frm.doc.branch] || frm.doc.branch}` : "Release Items",
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "release_html"
            }
        ],
        primary_action_label: "Release",
        primary_action() {

    		d.get_primary_btn().prop("disabled", true);

            let selected = [];

            $(d.wrapper).find("#release_items_body tr").each(function () {

                let checked = $(this).find(".release-check").is(":checked");

                if (checked) {
                    selected.push({
                        item_code: $(this).data("item"),
						row_name: $(this).find(".row-name").text(),
                        qty: flt($(this).find(".issue-input").val())
                    });
                }
            });
			$(d.wrapper).find(".row-name").hide()

            if (!selected.length) {
                frappe.msgprint("Select items to release");
                return;
            }
            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_stock_entry",
                args: {
                    evaluation: frm.doc.name,
                    items: selected
                },
                callback() {
                    frappe.msgprint("Stock Entry Created");
                    d.hide();
                    frm.reload_doc();
                }
            });
        }
    });

    // ✅ SHOW FIRST
    d.show();
    const wrapper = d.fields_dict.release_html.wrapper;	
	$(wrapper).html(get_release_html());


    // ✅ Small delay ensures DOM ready (important in dialogs)
    setTimeout(() => {
        render_release_rows(items, wrapper);
    }, 500);
}

function get_release_html() {
	return `
	<style>

	.release-table{
	width:100%;
	border-collapse:collapse;
	font-size:13px;
	}

	.release-table th,
	.release-table td{
	padding:8px;
	border-bottom:1px solid #e5e7eb;
	text-align:center;
	}

	.release-table thead{
	background:#f3f4f6;
	}

	.issue-input{
	width:80px;
	text-align:center;
	}

	/* partially released */
	.row-partial {
		background-color: #fff7ed;
	}

	/* fully released */
	.row-complete {
		background-color: #ecfdf5;
		color: #065f46;
	}

	/* disable inputs visually */
	.row-complete input {
		pointer-events: none;
		opacity: 0.6;
	}

	.status-badge {
		padding: 3px 8px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 600;
	}

	.badge-partial {
		background: #fed7aa;
		color: #9a3412;
	}

	.badge-complete {
		background: #bbf7d0;
		color: #065f46;
	}

	/* 🔴 OVER RELEASED */
	.row-over {
		background-color: #fef2f2;
		color: #991b1b;
		font-weight: 600;
	}

	.row-over input {
		pointer-events: none;
		opacity: 0.5;
	}

	.badge-over {
		background: #fecaca;
		color: #7f1d1d;
	}
	/* 🟣 NO STOCK AVAILABLE */
	.row-no-stock {
		background-color: #f5f3ff;
		color: #bea7e0;
	}

	.badge-no-stock {
		background: #ddd6fe;
		color: #bfa7e1;
		font-weight: 600;
	}

	/* 🟡 PARTIAL BUT NO STOCK */
	.row-partial-nostock {
		background-color: #fffbeb;
		color: #92400e;
	}

	.badge-partial-nostock {
		background: #fde68a;
		color: #78350f;
		font-weight: 600;
	}
	.release-note {
		background: #fff0f0;
		border: 1px solid #fdbaba;
		color: #850707;
		padding: 10px 12px;
		border-radius: 6px;
		margin-bottom: 12px;
		font-size: 13px;
	}
	.warehouse-info {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		padding: 8px 12px;
		border-radius: 6px;
		margin-bottom: 12px;
		font-size: 13px;
		font-weight: 600;
	}
	.hidden-column {
		display: none;
	}




	</style>
	<div class="release-note">
		<strong>Note:</strong>
		Select the items to release. <br>
		&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Modify the Issue Quantity only if partial release is required.
	</div>

	<table class="release-table">
	<thead>
	<tr>
	<th><input type="checkbox" id="select_all"></th>
	<th>Item</th>
	<th>Required</th>
	<th>Released</th>
	<th>To be Released</th>
	<th>Stock</th>
	<th>Status</th>
	<th>Issue Qty</th>
	</tr>
	</thead>

	<tbody id="release_items_body"></tbody>
	</table>
	`;
}


function render_release_rows(items, wrapper) {
    let html = "";

    items.forEach(row => {

        let balance = row.required_qty - row.released_qty;
		// if stock_qty is less than balance, then max issue is stock_qty, else balance
		
        let max_issue = Math.min(balance, row.stock_qty);

		let status = get_status(row);

		let row_class = "";
		let status_badge = "";
		let disable_row = false;

		if (status === "over") {
			row_class = "row-over";
			disable_row = true;
			status_badge =
				`<span class="status-badge badge-over">
					OVER RELEASED
				</span>`;
		}

		else if (status === "no_stock") {
			row_class = "row-no-stock";
			disable_row = true;
			status_badge =
				`<span class="status-badge badge-no-stock">
					NO STOCK
				</span>`;
		}

		else if (status === "complete") {
			row_class = "row-complete";
			status_badge =
				`<span class="status-badge badge-complete">
					RELEASED
				</span>`;
		}

		else if (status === "partial") {
			row_class = "row-partial";
			status_badge =
				`<span class="status-badge badge-partial">
					PARTIALLY RELEASED
				</span>`;
		}

		else if (status === "partial_no_stock") {
			row_class = "row-partial-nostock";
			disable_row = true;
			status_badge =
				`<span class="status-badge badge-partial-nostock">
					PARTIAL — NO STOCK
				</span>`;
		}


		else {
			status_badge = "-";
		}

		html += `
		<tr class="${row_class}"
			data-item="${row.item_code}"
			data-status="${status}">

			// hide this column but keep the data attribute for reference
            <td class="row-name hidden-column">${row.row_name}</td>

            <td>
                <input type="checkbox"
                    class="release-check"
                    ${disable_row ? "disabled" : ""}>
            </td>

            <td>${row.item_code}</td>

            <td class="col-required">${row.required_qty}</td>

            <td class="col-released" title="Already issued via Stock Entry">
                ${row.released_qty}
            </td>

            <td>${Math.max(balance,0)}</td>

            <td class="col-available">${row.stock_qty}</td>

            <td>${status_badge}</td>

            <td>
                <input type="number"
                    class="issue-input"
                    value="${disable_row ? 0 : max_issue}"
                    min="0"
                    max="${disable_row ? 0 : max_issue}"
                    ${disable_row ? "disabled" : ""}>
            </td>

        </tr>`;
    });

    $(wrapper).find("#release_items_body").html(html);
}


function get_status(row) {

    // 🔴 over released
    if (row.released_qty > row.required_qty)
        return "over";

    // 🟡 partially released but no stock
    if (row.released_qty > 0 && row.available_qty <= 0)
        return "partial_no_stock";

    // 🟣 no stock and nothing released
    if (row.released_qty === 0 && row.stock_qty <= 0)
        return "no_stock";

    // 🟢 fully released
    if (row.released_qty >= row.required_qty)
        return "complete";

    // 🟠 partially released
    if (row.released_qty > 0)
        return "partial";

    return "normal";
}


$(document).on("change", "#select_all", function () {

    let table = $(this).closest("table");
    let checked = this.checked;

    table.find("tbody tr").each(function () {

        let status = $(this).data("status");

        // ❌ protected rows
        if (status === "over" || status === "no_stock") {
            return;
        }

        $(this).find(".release-check")
            .prop("disabled", false)
            .prop("checked", checked);

        $(this).find(".issue-input")
            .prop("disabled", !checked);
    });
});


$(document).on("change", ".release-check", function () {

    let row = $(this).closest("tr");

    row.find(".issue-input").prop(
        "disabled",
        !this.checked
    );
});

// Prevent over typing
$(document).on("input", ".issue-input", function () {

    let input = $(this);
    let row = input.closest("tr");

    let required = flt(row.find(".col-required").text());
    let released = flt(row.find(".col-released").text());
    let available = flt(row.find(".col-available").text());

    let balance = required - released;

    let allowed = Math.min(balance, available);

    let entered = flt(input.val());

    // 🚫 Stop over release
    if (entered > allowed) {
        frappe.show_alert({
            message: __("Cannot release more than allowed quantity"),
            indicator: "red"
        });

        input.val(allowed);
    }

    // no negative
    if (entered < 0) {
        input.val(0);
    }
});