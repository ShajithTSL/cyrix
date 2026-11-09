const SOA_METHOD_PATH = "cyrix.custom_py.soa";


// Approximate printable width of an A4 page (210mm / 297mm minus the 15mm
// side margins Frappe's PDF uses), in CSS px, plus the editor's own
// padding + border. Only used to make the edit box roughly match the
// chosen orientation - it is never part of the saved HTML.
const SOA_PREVIEW_WIDTH = { Portrait: '714px', Landscape: '1043px' };

frappe.ui.form.on('Customer', {
	refresh(frm) {
		frm.add_custom_button('New', () => open_soa_editor(frm),"SOA");
	}
});

function open_soa_editor(frm) {
	let d = new frappe.ui.Dialog({
		title: 'Statement of Account',
		size: 'extra-large',
		fields: [
			{ fieldname: 'company', fieldtype: 'Link', options: 'Company', label: 'Company',
			  reqd: 1, default: frappe.defaults.get_default('company') },
			{ fieldname: 'orientation', fieldtype: 'Select', label: 'Page Orientation', reqd: 1,
			  options: ['Portrait', 'Landscape'], default: 'Portrait',
			  description: 'Orientation of the saved PDF. Can be changed any time before saving.' },
			{ fieldname: 'col1', fieldtype: 'Column Break' },
			{ fieldname: 'from_date', fieldtype: 'Date', label: 'From Date', reqd: 1 , default: "2020-01-01"},
			{ fieldname: 'show_ageing', fieldtype: 'Check', label: 'Show Ageing Summary', default: 0,
			  description: 'Ageing by due date, shown under the statement. Applies when you click '+ '<b style="color: #007bff;">Load Statement</b>' +'.' },
			{ fieldname: 'col2', fieldtype: 'Column Break' },
			{ fieldname: 'to_date', fieldtype: 'Date', label: 'To Date', reqd: 1,
			  default: frappe.datetime.get_today() },
			{ fieldname: 'col3', fieldtype: 'Column Break' },
			{ fieldname: 'statement_type', fieldtype: 'Select', label: 'Statement Type', reqd: 1,
			  options: ['Without Credit Note', 'With Credit Note', 'All Transactions', 'Only Outstanding Transactions'],
			  default: 'All Transactions',
			  description: 'Without/With Credit Note = only outstanding invoices. All Transactions = full ledger with running balance. Only Outstanding Transactions = every still-open item (invoices, credit notes, unallocated payments), no running balance.' },
			{ fieldname: 'sb_options', fieldtype: 'Section Break' },
			{ fieldname: 'col4', fieldtype: 'Column Break' },
			{ fieldname: 'sb1', fieldtype: 'Section Break' },
			{ fieldname: 'load_btn_html', fieldtype: 'HTML' },
			{ fieldname: 'editor_html', fieldtype: 'HTML' },
		],
		primary_action_label: 'Save as PDF',
		primary_action() {
			let values = d.get_values(true);
			let html = d.$wrapper.find('.soa-editable').html();

			if (!html || d.$wrapper.find('.soa-editable').hasClass('soa-empty')) {
				frappe.msgprint(__('Load the statement first, then edit it before saving.'));
				return;
			}

			frappe.call({
				method: `${SOA_METHOD_PATH}.save_edited_soa_pdf`,
				args: {
					customer: frm.doc.name,
					html: html,
					from_date: values.from_date,
					to_date: values.to_date,
					orientation: values.orientation,
				},
				freeze: true,
				freeze_message: __('Generating PDF...'),
				callback(r) {
					if (r.message && r.message.file_url) {
						frappe.show_alert({
							message: __('Saved to this Customer\'s attachments.'),
							indicator: 'green'
						});
						window.open(r.message.file_url, '_blank');
						d.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});

	d.fields_dict.load_btn_html.$wrapper.html(
		`<button class="btn btn-default btn-sm" id="soa-load-btn">Load Statement</button>
		 <span class="text-muted small" style="margin-left: 8px;">
		 	Loads the statement below so you can edit anything before saving it as a PDF.
		 </span>`
	);

	d.fields_dict.editor_html.$wrapper.html(
		`<div class="soa-editable soa-empty" contenteditable="false"
			 style="border:1px solid #d1d8dd; border-radius: 4px; padding:16px;
			        margin: 12px auto 0 auto; min-height:350px; max-height:60vh;
			        overflow:auto; background:#fff;">
			 <p class="text-muted">Set the dates and company above, then click
			 "Load Statement".</p>
		 </div>`
	);

	// Make the edit box roughly as wide as the page that will be produced.
	// Listens on the underlying <select> so it fires for every user change.
	function apply_orientation_preview() {
		let orientation = d.get_value('orientation') || 'Portrait';
		d.$wrapper.find('.soa-editable').css('max-width', SOA_PREVIEW_WIDTH[orientation]);
	}
	d.fields_dict.orientation.$input.on('change', apply_orientation_preview);
	apply_orientation_preview();

	d.$wrapper.find('#soa-load-btn').on('click', () => {
		let values = d.get_values();
		if (!values) return; // required fields not filled in yet

		frappe.call({
			method: `${SOA_METHOD_PATH}.get_soa_html_for_edit`,
			args: {
				customer: frm.doc.name,
				company: values.company,
				from_date: values.from_date,
				to_date: values.to_date,
				statement_type: values.statement_type,
				show_ageing: values.show_ageing ? 1 : 0,
			},
			freeze: true,
			freeze_message: __('Loading statement...'),
			callback(r) {
				let $editable = d.$wrapper.find('.soa-editable');
				$editable.removeClass('soa-empty').attr('contenteditable', 'true');
				$editable.html(r.message);
			}
		});
	});

	d.show();
}