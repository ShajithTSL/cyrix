// Copyright (c) 2025, cyrix and contributors
// For license information, please see license.txt
const APP_PATH = "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report";

function show_stock_details(frm) {
	const args = () => ({
		item_details: JSON.stringify(
			(frm.doc.items || []).map(r => ({ sku: r.part, model: r.model }))
		),
		theme: document.documentElement.getAttribute("data-theme-mode") === "dark"
			? "dark" : "light",
	});

	const load = (d) =>
		frappe.call({ method: APP_PATH + ".get_reserved_stock_detail", args: args() })
			.then(r => d.$body.html(r.message));

	const d = new frappe.ui.Dialog({ title: __("Stock Details"), size: "extra-large" });
	d.onhide = () => d.$wrapper.remove(); // no stale DOM copies

	// ---- Reserve more ----
	d.$body.on("click", ".esr-reserve", function (e) {
		e.stopPropagation();
		const $b = $(this);
		frappe.prompt(
			[{
				fieldname: "qty",
				fieldtype: "Float",
				label: __("Qty to reserve"),
				description: __("Leave empty to reserve the maximum possible"),
			}],
			(v) => {
				frappe.call({
					method: APP_PATH + ".reserve_qty",
					args: {
						evaluation_report: $b.data("report"),
						child_row_name: $b.data("row"),
						qty: v.qty || 0,
					},
					freeze: true,
				}).then(r => {
					frappe.show_alert({ message: r.message.message, indicator: "green" });
					load(d);          // refresh popup with fresh quantities
					frm.reload_doc(); // child row display fields changed server-side
				});
			},
			__("Reserve More"), __("Reserve")
		);
	});

	// ---- Unreserve / release ----
	d.$body.on("click", ".esr-release", function (e) {
		e.stopPropagation();
		const $b = $(this);
		const net = flt($b.data("net"));
		frappe.prompt(
			[{
				fieldname: "qty",
				fieldtype: "Float",
				label: __("Qty to release"),
				default: net,
				description: __("Currently held: {0}", [net]),
			}],
			(v) => {
				frappe.call({
					method: APP_PATH + ".unreserve_qty",
					args: {
						evaluation_report: $b.data("report"),
						child_row_name: $b.data("row"),
						qty: v.qty || 0,
					},
					freeze: true,
				}).then(r => {
					frappe.show_alert({ message: r.message.message, indicator: "orange" });
					load(d);
					frm.reload_doc();
				});
			},
			__("Unreserve"), __("Release")
		);
	});

	load(d).then(() => d.show());
}

function show_reserve_dialog(frm) {
	// Rows with a shortage (reserved < required)
	const rows = (frm.doc.items || []).filter(r =>
		r.part && flt(r.reserved_qty) < flt(r.qty)
	);
	if (!rows.length) {
		frappe.msgprint(__('All rows are fully reserved.'));
		return;
	}

	const d = new frappe.ui.Dialog({
		title: __('Reserve Stock'),
		fields: [
			{
				fieldname: 'row',
				fieldtype: 'Select',
				label: __('Row'),
				options: rows.map(r =>
					`${r.idx}: ${r.part} (reserved ${r.reserved_qty} of ${r.qty})`),
				reqd: 1,
			},
			{
				fieldname: 'qty',
				fieldtype: 'Float',
				label: __('Qty to Reserve'),
				description: __('Leave empty to reserve the full remaining need (as stock allows)'),
			},
		],
		primary_action_label: __('Reserve'),
		primary_action(values) {
			const idx = cint(values.row.split(':')[0]);
			const row = rows.find(r => r.idx === idx);
			frappe.call({
				method: 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.reserve_qty',
				args: {
					evaluation_report: frm.doc.name,
					child_row_name: row.name,
					qty: values.qty || 0,
				},
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({
							message: r.message.message,
							indicator: r.message.shortage > 0 ? 'orange' : 'green',
						});
						d.hide();
						frm.reload_doc();
					}
				},
			});
		},
	});
	d.show();
}

function show_unreserve_dialog(frm) {
	// Only rows with un-issued reserved qty
	const rows = (frm.doc.items || []).filter(r =>
		flt(r.reserved_qty) > 0
	);
	if (!rows.length) {
		frappe.msgprint(__('No reserved rows on this report.'));
		return;
	}

	const d = new frappe.ui.Dialog({
		title: __('Unreserve Stock'),
		fields: [
			{
				fieldname: 'row',
				fieldtype: 'Select',
				label: __('Row'),
				options: rows.map(r => `${r.idx}: ${r.part} (reserved ${r.reserved_qty})`),
				reqd: 1,
			},
			{
				fieldname: 'qty',
				fieldtype: 'Float',
				label: __('Qty to Unreserve'),
				reqd: 1,
			},
		],
		primary_action_label: __('Unreserve'),
		primary_action(values) {
			const idx = cint(values.row.split(':')[0]);
			const row = rows.find(r => r.idx === idx);
			frappe.call({
				method: 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.unreserve_qty',
				args: {
					evaluation_report: frm.doc.name,
					child_row_name: row.name,
					qty: values.qty,
				},
				callback(r) {
					if (!r.exc) {
						frappe.show_alert({
							message: __('Unreserved {0}. Freed stock is now available.', [values.qty]),
							indicator: 'green',
						});
						d.hide();
						frm.reload_doc();
					}
				},
			});
		},
	});
	d.show();
}

function show_reservation_dialog(frm, mode) {
	const is_reserve = mode === 'reserve';

	frappe.call({
		method: 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.get_reservation_rows',
		args: { docname: frm.doc.name },
		callback(r) {
			if (!r.message || !r.message.length) {
				frappe.msgprint(__('No part rows found.'));
				return;
			}
			render_reservation_dialog(frm, mode, r.message);
		},
	});

	function render_reservation_dialog(frm, mode, rows) {
		// max per row: reserve → min(remaining_need is the cap per row;
		// stock is shared, backend clamps); unreserve → unissued_qty
		rows.forEach(row => {
			row.max_qty = is_reserve ? row.remaining_need : row.unissued_qty;
		});

		const actionable = rows.filter(row => row.max_qty > 0);
		if (!actionable.length) {
			frappe.msgprint(is_reserve
				? __('All rows are fully reserved.')
				: __('No un-issued reserved qty to pull back.'));
			return;
		}

		const d = new frappe.ui.Dialog({
			title: is_reserve ? __('Reserve Stock') : __('Unreserve Stock'),
			size: 'extra-large',
			fields: [{ fieldname: 'items_html', fieldtype: 'HTML' }],
			primary_action_label: is_reserve ? __('Reserve') : __('Unreserve'),
			primary_action() {
				const items = [];
				d.$wrapper.find('.resv-qty-input').each(function () {
					const qty = flt($(this).val());
					if (qty > 0) {
						items.push({ row_name: $(this).data('row'), qty: qty });
					}
				});
				if (!items.length) {
					frappe.msgprint(__('Enter a qty for at least one row.'));
					return;
				}
				frappe.call({
					method: is_reserve
						? 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.bulk_reserve_qty'
						: 'cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.bulk_unreserve_qty',
					args: { evaluation_report: frm.doc.name, items: items },
					freeze: true,
					freeze_message: is_reserve ? __('Reserving...') : __('Unreserving...'),
					callback(res) {
						if (res.exc) return;
						const m = res.message || {};
						let html = '';
						if ((m.results || []).length)
							html += '<b>' + __('Done') + ':</b><br>' + m.results.join('<br>');
						if ((m.errors || []).length)
							html += (html ? '<br><br>' : '') + '<b>' + __('Skipped') + ':</b><br>' + m.errors.join('<br>');
						if (html) {
							frappe.msgprint({
								title: is_reserve ? __('Reserve Summary') : __('Unreserve Summary'),
								message: html,
								indicator: (m.errors || []).length ? 'orange' : 'green',
							});
						}
						d.hide();
						frm.reload_doc();
					},
				});
			},
		});

		// ── Table ──────────────────────────────────────────────────────
		const qty_col = is_reserve ? __('Qty to Reserve') : __('Qty to Unreserve');
		const max_col = is_reserve ? __('Remaining Need') : __('Un-issued');

		let table = `
			<div style="max-height: 420px; overflow-y: auto;">
			<table class="table table-bordered" style="margin: 0;">
				<thead>
					<tr>
						<th style="width:34px;">
							<input type="checkbox" class="resv-check-all" title="${__('Select all')}">
						</th>
						<th>#</th>
						<th>${__('Item')}</th>
						<th>${__('Model')}</th>
						<th class="text-right">${__('Required')}</th>
						<th class="text-right">${__('Reserved')}</th>
						<th class="text-right">${__('Released')}</th>
						<th class="text-right">${max_col}</th>
						${is_reserve ? `<th class="text-right">${__('Free Stock')}</th>` : ''}
						<th class="text-right" style="width:130px;">${qty_col}</th>
					</tr>
				</thead>
				<tbody>`;

		rows.forEach(row => {
			const disabled = row.max_qty <= 0;
			table += `
				<tr class="${disabled ? 'text-muted' : ''}">
					<td>
						<input type="checkbox" class="resv-check" data-row="${row.row_name}"
							${disabled ? 'disabled' : ''}>
					</td>
					<td>${row.idx}</td>
					<td>${frappe.utils.escape_html(row.item_code)}</td>
					<td>${frappe.utils.escape_html(row.model || '')}</td>
					<td class="text-right">${row.required_qty}</td>
					<td class="text-right">${row.reserved_qty}</td>
					<td class="text-right">${row.released_qty}</td>
					<td class="text-right">${row.max_qty}</td>
					${is_reserve ? `<td class="text-right">${row.free_qty}</td>` : ''}
					<td>
						<input type="number" class="form-control input-sm resv-qty-input text-right"
							data-row="${row.row_name}" data-max="${row.max_qty}"
							min="0" max="${row.max_qty}" step="any" value=""
							${disabled ? 'disabled' : ''}>
					</td>
				</tr>`;
		});

		table += `</tbody></table></div>
			<p class="text-muted small" style="margin-top:8px;">
				${is_reserve
					? __('Free stock is shared across rows — processed top to bottom; later rows get what remains.')
					: __('You can only unreserve qty that has not been physically issued.')}
			</p>`;

		d.fields_dict.items_html.$wrapper.html(table);

		// ── Behavior ───────────────────────────────────────────────────
		const $w = d.$wrapper;

		// Checkbox → fill with max qty; uncheck → clear
		$w.on('change', '.resv-check', function () {
			const row_name = $(this).data('row');
			const $input = $w.find(`.resv-qty-input[data-row="${row_name}"]`);
			$input.val(this.checked ? $input.data('max') : '');
		});

		// Select all
		$w.on('change', '.resv-check-all', function () {
			const checked = this.checked;
			$w.find('.resv-check:not(:disabled)').prop('checked', checked).trigger('change');
		});

		// Typing a qty checks the row; clamp to max
		$w.on('input', '.resv-qty-input', function () {
			const max = flt($(this).data('max'));
			let val = flt($(this).val());
			if (val > max) { $(this).val(max); val = max; }
			$w.find(`.resv-check[data-row="${$(this).data('row')}"]`).prop('checked', val > 0);
		});

		d.show();
	}
}

frappe.ui.form.on("Evaluation Report", {

	test_method:function(frm){

        colour_availability_cells(frm);
		if (frm.doc.docstatus === 1 && (frappe.user.has_role("Procurement") || frappe.user.has_role("Lab Coordinator") || frappe.session.user === "Administrator")) {
			
			frm.add_custom_button(__("Details"), () => { show_stock_details(frm) }, __('Stock'));
			frm.add_custom_button(__('Reserve Qty'), () => show_reservation_dialog(frm, 'reserve'), __('Stock'));
			frm.add_custom_button(__('Unreserve Qty'), () => show_reservation_dialog(frm, 'unreserve'), __('Stock'));
		}
	},
	
	after_save(frm) {
        colour_availability_cells(frm);
    },

	technician: function(frm){
		if(frm.doc.technician){
			frm.set_value("technician_id",frm.doc.technician)
		}
	},
	send(frm){
        frappe.call({
			method: "cyrix.custom_py.mail_notification.purchase_msg_to_info",
			args: {
				"com": frm.doc.company,
				"branch":frm.doc.branch,
				"ev":frm.doc.name,
				"sender":frappe.session.user
			}				
		})       
    },

	returned_parts: function(frm){
		// Returned Parts
		if(frm.doc.docstatus == 1 && frm.doc.if_parts_required == 1 && (frappe.user.has_role("Purchase Manager"))){
			// let all_checked = frm.doc.items.every(row => row.returned);
			// if (!all_checked) {
				frm.add_custom_button(__("Returned Parts"), function(){
					frappe.call({
						method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_returned_parts",
						args: {
							"source_name": frm.doc.name
						},
						callback: function(r) {
							if(r.message) {
								var doc = frappe.model.sync(r.message);
								frappe.set_route("Form", doc[0].doctype, doc[0].name);
							}
						}
					});
				},__('Create'));
			// }
		}
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
		frm.dashboard.links_area.body.find('.btn-new').each(function(i, el) {
			$(el).hide();
		});
		frm.add_custom_button(__("Technical Report"), function(){
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_technical_report",
				args: {
					name: frm.doc.job_order_data
				},
				callback: function(r) {
					if(r.message) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", doc[0].doctype, doc[0].name);
					}
				}
			});
		},__('Create'));

		frm.add_custom_button(__("Request for Purchaser"), function(){
			let email_list = [
				"purchase-uae@cyrix-tsl.com",
				"purchase@tsl-me.com",
				"lab-uae@tsl-me.com",
				"purchase-sa1@tsl-me.com"
			];

			let d = new frappe.ui.Dialog({
				title: "Send Email",
				fields: [
					{
						fieldtype: "Select",
						fieldname: "email",
						label: "Email",
						options: email_list.join("\n"),
						reqd: 1
					}
				],

				primary_action_label: "Send",

				primary_action(values) {

					frappe.call({
						method: "cyrix.custom_py.mail_notification.to_purchaser",
						args: {
						
						"com": frm.doc.company,
						"branch":frm.doc.branch,
						"ev":frm.doc.name,
						"sender":frappe.session.user,
						"recipients": values.email,
						},

						callback: function(r) {

							frappe.msgprint("Mail Sent");
							d.hide();
						}
					});
				}
			});

			d.show();
		},__('Create'));
							
						
			
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

		frm.trigger("returned_parts")
		frm.trigger("test_method")
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
	add_images: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let images = JSON.parse(row.attached_images || "[]");

		new frappe.ui.FileUploader({
			doctype: frm.doc.doctype,
			docname: frm.doc.name,
			allow_multiple: true,
			restrictions: {
				allowed_file_types: ["image/*"],
			},
			on_success: (file_doc) => {
				images.push({
					file_url: file_doc.file_url,
					file_name: file_doc.file_name,
				});
				frappe.model.set_value(cdt, cdn, "attached_images", JSON.stringify(images));
				render_image_previews(frm, cdt, cdn);
			},
		});
	},

	// Fires whenever the row's expanded form is (re)rendered
	form_render: function (frm, cdt, cdn) {
		render_image_previews(frm, cdt, cdn);
	},
});




async function open_release_dialog(frm) {

    let r = await frappe.call({
        method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.get_release_items",
        args: { docname: frm.doc.name }
    });

    let items = r.message || [];

    // Resolve display name for the warehouse from branch
    const warehouse_display = {
        "Riyadh":  "Riyadh - BM",
        "Jeddah":  "Jeddah - BM",
        "Kuwait":  "Kuwait - CT-K",
        "Dubai":   "Dubai - CT-UAE",
    };

    let title = warehouse_display[frm.doc.branch]
        ? `Release Items from ${warehouse_display[frm.doc.branch]}`
        : "Release Items";

    let d = new frappe.ui.Dialog({
        title,
        size: "extra-large",
        fields: [{ fieldtype: "HTML", fieldname: "release_html" }],
        primary_action_label: "Release",
        primary_action() {

            let selected = [];

            $(d.wrapper).find("#release_items_body tr").each(function () {
                if (!$(this).find(".release-check").is(":checked")) return;

                let qty = flt($(this).find(".issue-input").val());
                if (qty <= 0) return;

                selected.push({
                    item_code: $(this).data("item"),
                    row_name:  $(this).data("rowname"),
                    qty:       qty,
                });
            });

            if (!selected.length) {
                frappe.msgprint("Select at least one item to release.");
                return;
            }

            d.get_primary_btn().prop("disabled", true).text("Processing...");

            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.create_stock_entry",
                args: { evaluation: frm.doc.name, items: selected },
                callback() {
                    d.hide();
                    frm.reload_doc();
                },
                error() {
                    d.get_primary_btn().prop("disabled", false).text("Release");
                }
            });
        }
    });

    d.show();

    const wrapper = d.fields_dict.release_html.wrapper;
    $(wrapper).html(get_release_html());

    setTimeout(() => render_release_rows(items, wrapper), 300);
}


// ------------------------------------------------------------------
// Table HTML shell
// ------------------------------------------------------------------
function get_release_html() {
    return `
    <style>
    .release-table { width:100%; border-collapse:collapse; font-size:13px; }
    .release-table th, .release-table td { padding:8px; border-bottom:1px solid #e5e7eb; text-align:center; }
    .release-table thead { background:#f3f4f6; }
    .issue-input { width:70px; text-align:center; }

    .row-partial  { background:#fff7ed; }
    .row-complete { background:#ecfdf5; color:#065f46; }
    .row-complete input { pointer-events:none; opacity:0.6; }
    .row-over     { background:#fef2f2; color:#991b1b; font-weight:600; }
    .row-over input { pointer-events:none; opacity:0.5; }
    .row-no-stock { background:#f5f3ff; color:#bea7e0; }
    .row-partial-nostock { background:#fffbeb; color:#92400e; }

    .status-badge { padding:3px 8px; border-radius:6px; font-size:11px; font-weight:600; }
    .badge-partial          { background:#fed7aa; color:#9a3412; }
    .badge-complete         { background:#bbf7d0; color:#065f46; }
    .badge-over             { background:#fecaca; color:#7f1d1d; }
    .badge-no-stock         { background:#ddd6fe; color:#bfa7e1; }
    .badge-partial-nostock  { background:#fde68a; color:#78350f; }

    .release-note {
        background:#fff0f0; border:1px solid #fdbaba; color:#850707;
        padding:10px 12px; border-radius:6px; margin-bottom:12px; font-size:13px;
    }
    </style>

    <div class="release-note">
        <strong>Note:</strong> The <b>Releasable</b> qty is what was actually reserved (may be less than Required if stock was short).
        Modify <b>Issue Qty</b> only for partial release.
    </div>

    <table class="release-table">
    <thead>
        <tr>
            <th><input type="checkbox" id="select_all"></th>
            <th>Item Code</th>
            <th>Model</th>
            <th>Required</th>
            <th>Releasable<br><small style="font-weight:normal">(Reserved)</small></th>
            <th>Released</th>
            <th>Balance</th>
            <th>Stock</th>
            <th>Status</th>
            <th>Issue Qty</th>
        </tr>
    </thead>
    <tbody id="release_items_body"></tbody>
    </table>`;
}


// ------------------------------------------------------------------
// Render rows
// KEY: use row.releasable_qty (reserved ceiling) and
//      row.balance_to_release (backend pre-computed) for all limits.
//      max_issue = min(balance_to_release, stock_qty)
// ------------------------------------------------------------------
function render_release_rows(items, wrapper) {
    let html = "";
	console.log(items)

    items.forEach(row => {

        // balance_to_release and releasable_qty come from backend
        // balance_to_release = releasable_qty - net_released   (already capped at 0)
        let balance      = row.releasable_qty - row.released_qty;
        let max_issue    = Math.min(balance, row.stock_qty);

        let status       = get_status(row);
        let row_class    = "";
        let status_badge = "";
        let disabled     = false;

        if (status === "over") {
            row_class    = "row-over";
            disabled     = true;
            status_badge = `<span class="status-badge badge-over">OVER RELEASED</span>`;

        } else if (status === "no_stock") {
            row_class    = "row-no-stock";
            disabled     = true;
            status_badge = `<span class="status-badge badge-no-stock">NO STOCK</span>`;

        } else if (status === "partial_no_stock") {
            row_class    = "row-partial-nostock";
            disabled     = true;
            status_badge = `<span class="status-badge badge-partial-nostock">PARTIAL — NO STOCK</span>`;

        } else if (status === "complete") {
            row_class    = "row-complete";
            disabled     = true;
            status_badge = `<span class="status-badge badge-complete">RELEASED</span>`;

        } else if (status === "partial") {
            row_class    = "row-partial";
            status_badge = `<span class="status-badge badge-partial">PARTIALLY RELEASED</span>`;

        } else {
            status_badge = "—";
        }

        html += `
        <tr class="${row_class}"
            data-item="${row.item_code}"
            data-rowname="${row.row_name}"
            data-status="${status}"
            data-balance="${balance}"
            data-stock="${row.stock_qty}">

            <td><input type="checkbox" class="release-check" ${disabled ? "disabled" : ""}></td>
            <td>${row.item_code}</td>
            <td>${row.model || "—"}</td>
            <td>${row.required_qty}</td>
            <td><strong>${row.releasable_qty}</strong></td>
            <td>${row.released_qty}</td>
            <td>${Math.max(balance, 0)}</td>
            <td>${row.stock_qty}</td>
            <td>${status_badge}</td>
            <td>
                <input type="number"
                    class="issue-input"
                    value="${disabled ? 0 : max_issue}"
                    min="0"
                    max="${disabled ? 0 : max_issue}"
                    ${disabled ? "disabled" : ""}>
            </td>
        </tr>`;
    });

    $(wrapper).find("#release_items_body").html(html);
}


// ------------------------------------------------------------------
// Status logic — uses releasable_qty (reserved ceiling), not required_qty
// ------------------------------------------------------------------
function get_status(row) {
    // Over-released against the reservation ceiling
    if (row.released_qty > row.releasable_qty)
        return "over";

    // Fully released
    if (row.released_qty >= row.releasable_qty && row.releasable_qty > 0)
        return "complete";

    // Partially released but no stock left to give more
    if (row.released_qty > 0 && row.stock_qty <= 0)
        return "partial_no_stock";

    // Nothing released and no stock
    if (row.released_qty === 0 && row.stock_qty <= 0)
        return "no_stock";

    // Partially released, stock still available
    if (row.released_qty > 0)
        return "partial";

    return "normal";
}

$(document).on("change", "#select_all", function () {
    let checked = this.checked;
    $(this).closest("table").find("tbody tr").each(function () {
        let status = $(this).data("status");
        if (["over", "no_stock", "partial_no_stock", "complete"].includes(status)) return;
        $(this).find(".release-check").prop("checked", checked);
        $(this).find(".issue-input").prop("disabled", !checked);
    });
});

$(document).on("change", ".release-check", function () {
    $(this).closest("tr").find(".issue-input").prop("disabled", !this.checked);
});


// ------------------------------------------------------------------
// Prevent typing beyond allowed qty
// Ceiling = min(balance_to_release, stock_qty) — from data attributes
// ------------------------------------------------------------------
$(document).on("input", ".issue-input", function () {
    let input   = $(this);
    let tr      = input.closest("tr");
    let balance = flt(tr.data("balance"));
    let stock   = flt(tr.data("stock"));
    let allowed = Math.min(balance, stock);
    let entered = flt(input.val());

    if (entered > allowed) {
        frappe.show_alert({ message: __("Cannot release more than allowed quantity ({0})", [allowed]), indicator: "red" });
        input.val(allowed);
    }
    if (entered < 0) input.val(0);
});


function check_and_show_availability(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.part || !row.qty || !frm.doc.branch) return;

    frappe.call({
        method: "cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report.get_available_qty",
        args: {
            item_code:    row.part,
            branch:       frm.doc.branch,
            required_qty: row.qty,
            current_doc:  frm.doc.name || "",
        },
        callback(r) {
            if (!r.message) return;
            if (r.message.error) {
                frappe.show_alert({ message: r.message.error, indicator: "red" });
                return;
            }

            const { actual_qty, custom_reserve_qty, free_qty, can_reserve, shortage, warehouse, label } = r.message;

            frappe.model.set_value(cdt, cdn, "parts_availability", label);
            frappe.model.set_value(cdt, cdn, "reserved_qty",       can_reserve);
            frappe.model.set_value(cdt, cdn, "shortage_qty",       shortage);

            let msg, indicator;
            if (actual_qty <= 0) {
                msg       = __("🛒 {0} — No stock in {1}. Full qty ({2}) needs to be purchased.", [row.part, warehouse, row.qty]);
                indicator = "orange";
            } else if (label === "Yes") {
                msg       = __("✅ {0} — Full qty available in {1}. (Stock: {2} | Eval Reserved: {3} | Free: {4})", [row.part, warehouse, actual_qty, custom_reserve_qty, free_qty]);
                indicator = "green";
            } else if (label === "Partial") {
                msg       = __("⚠️ {0} — Partial. Reserving {1}, purchasing {2}. (Stock: {3} | Eval Reserved: {4} | Free: {5})", [row.part, can_reserve, shortage, actual_qty, custom_reserve_qty, free_qty]);
                indicator = "orange";
            } else {
                msg       = __("❌ {0} — No free stock in {1}. Full qty ({2}) needs to be purchased. (Stock: {3} | Eval Reserved: {4} | Free: {5})", [row.part, warehouse, row.qty, actual_qty, custom_reserve_qty, free_qty]);
                indicator = "red";
            }

            frappe.show_alert({ message: msg, indicator });
            colour_availability_cells(frm);
        },
    });
}


// ------------------------------------------------------------------
// Colour-code parts_availability column: green / orange / red
// ------------------------------------------------------------------
function colour_availability_cells(frm) {
    setTimeout(() => {
        frm.fields_dict["items"].grid.wrapper
            .find(".grid-row")
            .each(function () {
                const $cell = $(this).find("[data-fieldname='parts_availability']");
                const val   = $cell.text().trim();

                const color = val === "Yes"     ? "#2ecc71"
                            : val === "Partial" ? "#f39c12"
                            : val === "No"      ? "#e74c3c"
                            : "";

                $cell.css({ "color": color, "font-weight": "bold" });
            });
    }, 300);
}

const CHILD_TABLE_FIELDNAME = "items"; // <-- change to your parent's table fieldname

function render_image_previews(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let images = JSON.parse(row.attached_images || "[]");

	let html = images
		.map(
			(img) => `
			<div class="img-thumb" style="display:inline-block; margin:4px; position:relative;">
				<img src="${img.file_url}"
					style="width:80px; height:80px; object-fit:cover; border-radius:4px; border:1px solid var(--border-color);">
				<span class="remove-img" data-url="${img.file_url}"
					style="position:absolute; top:-6px; right:-6px; background:#e24c4c; color:#fff;
						   border-radius:50%; width:18px; height:18px; text-align:center;
						   line-height:18px; cursor:pointer; font-size:12px;">&times;</span>
			</div>`
		)
		.join("");

	let grid_row = frm.fields_dict[CHILD_TABLE_FIELDNAME].grid.grid_rows_by_docname[cdn];
	if (!grid_row || !grid_row.grid_form) return; // row form not open yet

	let $wrapper = grid_row.grid_form.fields_dict["images_preview"].$wrapper;
	$wrapper.html(html || `<span class="text-muted">No images attached</span>`);

	$wrapper.find(".remove-img").on("click", function () {
		let url = $(this).data("url");
		let updated = images.filter((i) => i.file_url !== url);
		frappe.model.set_value(cdt, cdn, "attached_images", JSON.stringify(updated));
		render_image_previews(frm, cdt, cdn);
	});
}

function update_missing_image_indicator(frm) {
	let grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid) return;

	let missing_rows = [];
	(frm.doc.items || []).forEach((row) => {
		let images = [];
		try {
			images = JSON.parse(row.attached_images || "[]");
		} catch (e) {
			images = [];
		}
		if (!images.length) {
			missing_rows.push(row.idx); // Frappe's own 1-based row number
		}
	});

	// --- 1. Banner at the top of the form ---
	frm.dashboard.clear_headline();
	if (missing_rows.length) {
		frm.dashboard.set_headline_alert(
			`<p style = "font-weight:bold;color:red">⚠️ Kindly attach the images inside the Part Sheet table</p>
			<div class="indicator-pill blue" style="padding:6px 10px;">
				${missing_rows.length} row(s) missing images: Row ${missing_rows.join(", ")}
			</div>`
		);
	}

	// --- 2. Highlight the affected rows in the grid itself ---
	inject_highlight_style_once();
	grid.grid_rows.forEach((grid_row) => {
		let is_missing = missing_rows.includes(grid_row.doc.idx);
		grid_row.row && grid_row.row.toggleClass("missing-image-row", is_missing);
	});
}

function inject_highlight_style_once() {
	if (document.getElementById("missing-image-row-style")) return;
	let style = document.createElement("style");
	style.id = "missing-image-row-style";
	style.innerHTML = `
		.missing-image-row {
			background-color: rgba(226, 76, 76, 0.16) !important;
			box-shadow: inset 3px 0 0 0 #e24c4c;
		}
		.missing-image-row:hover {
			background-color: rgba(226, 76, 76, 0.26) !important;
		}
	`;
	document.head.appendChild(style);
}