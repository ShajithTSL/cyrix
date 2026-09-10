frappe.ui.form.on('Sales Invoice', {
    before_submit: function(frm){
        return check_dimension_mismatches(frm).then(() => {
            return check_job_order_cancellation(frm);
        });
    },
    company: function(frm) {
        frm.trigger("hide_section");
    },

    get_advance_payment_details_test: function(frm) {

        if (!frm.doc.name) {
            return;
        }

        frappe.call({
            method: "cyrix.custom_py.advance_popup.set_advances",
            args: {
                name: frm.doc.name,
            },

            callback: function(r) {

                let wrapper = frm.fields_dict.custom_advance_status.$wrapper;

                wrapper.empty();

                if (!r.message || !r.message.length) {
                    wrapper.html(`
                        <div style="
                            padding: 12px;
                            border: 1px solid #e5e7eb;
                            border-radius: 6px;
                            color: #6b7280;
                            background: #f8f9fa;
                        ">
                            ${__("No advance available")}
                        </div>
                    `);
                    return;
                }

                let currency = frm.doc.currency;

                let total_advance = 0;
                let total_allocated = 0;

                r.message.forEach(row => {
                    total_advance += flt(row.advance_amount);
                });

                let total_available = total_advance;

                let html = `
                    <div class="custom-advance-card" style="
                        padding: 1px;
                        border-radius: 8px;
                        background: #ffffff;
                        border: 1px solid #ffffff;
                        cursor: pointer;
                        transition: all 0.2s;
                    ">
                        <div style="
                            color: #16803c;
                            font-size: 12px;
                            margin-bottom: 5px;
                        ">
                            ${__("Available Advance")}
                        </div>

                        <div style="
                            font-size: 20px;
                            font-weight: bold;
                            color: #16803c;
                        ">
                            ${format_currency(total_available, currency)}
                        </div>

                        <div style="
                            font-size: 11px;
                            font-weight: 500;
                            color: #101411;
                            margin-top: 5px;
                        ">
                            ${__("Click to Get Advances")}
                        </div>
                    </div>
                `;

                wrapper.html(html);

                // Click HTML → scroll to Advances table
                wrapper.find(".custom-advance-card").on("click", function() {

                    frm.scroll_to_field("advances");

                    // Optional: highlight the table
                    let advance_wrapper = frm.fields_dict.advances.$wrapper;

                    advance_wrapper.css({
                        "transition": "background-color 0.3s",
                        "background-color": "white"
                    });

                    frm.trigger("get_advances")


                    setTimeout(() => {
                        advance_wrapper.css("background-color", "");
                    }, 1500);
                });
            }
        });
    },

    refresh: function(frm) {
        frm.trigger("hide_section");
        frm.trigger("get_advance_payment_details_test");
    },
    onload: function(frm) {
        frappe.run_serially([
            () => {
                frm.trigger("hide_section")
            },
            () => {
                frm.trigger("get_advance_payment_details_test");
            },
            () => {
                if (frm.doc.__custom_items_to_override) {
                    frm.custom_items_to_override = frm.doc.__custom_items_to_override;
                    delete frm.doc.__custom_items_to_override;
                }
            },
        ])
    },
    hide_section: function(frm) {
        frappe.db.get_value("Company", {"name": frm.doc.company}, "custom_zatca_invoice_enabled").then(r => {
            if (r && r.message) {
                if (r.message.custom_zatca_invoice_enabled === 0){
                    frm.set_df_property('custom_section_break_gqwpx', 'hidden', true);
                }
                else{
                    frm.set_df_property('custom_section_break_gqwpx', 'hidden', false);
                }
            }
        })
    },
  
    validate: function(frm){
        frm.trigger("naming_series")
    },
    branch: function(frm){
        frm.trigger("naming_series")
    },
    naming_series: function(frm){
        if(frm.doc.__islocal){
            if(frm.doc.is_return == 1){
                const series = {
                    "Kuwait": "INV-RE-K.YY.-",
                    "Dammam": "INV-RE-D.YY.-",
                    "Riyadh": "INV-RE-R.YY.-",
                    "Jeddah": "INV-RE-J.YY.-",
                    "Dubai": "INV-RE-DU.YY.-"
                };
                const return_series = series[frm.doc.branch];
                if (return_series) {
                    frm.set_value('naming_series', return_series);
                }
            }
            else{               
                const naming_series = {
                  
                    "Kuwait": "INV-K.YY.-",
                    "Dammam": "INV-D.YY.-",
                    "Riyadh": "INV-R.YY.-",
                    "Jeddah": "INV-J.YY.-",
                    "Dubai": "INV-DU.YY.-"
                };
                const series = naming_series[frm.doc.branch];
                if (series) {
                    frm.set_value('naming_series', series);
                }
            }
        }
    },
    before_save: function (frm) {
        if (frm.custom_items_to_override && Array.isArray(frm.custom_items_to_override)) {
            frm.doc.items.forEach(row => {
                const custom_item = frm.custom_items_to_override.find(ci => ci.item_code === row.item_code);
                if (custom_item) {
                    row.rate = custom_item.rate;
                    row.price_list_rate = custom_item.rate;
                    row.amount = custom_item.rate * row.qty;
                }
            });
            // Clear after applying
            frm.custom_items_to_override = null;
        }
    }
})

// -----------------------------------------------------------------------
// Existing cost center / branch mismatch check, extracted into its own
// function so before_submit can chain it with the new Job Order dialog.
// -----------------------------------------------------------------------
function check_dimension_mismatches(frm) {
    // ✅ CRITICAL: Return Promise
    let parent_cc = frm.doc.cost_center || "";
    let parent_branch = frm.doc.branch || "";

    let mismatches = [];

    // --- Items ---
    (frm.doc.items || []).forEach((row, idx) => {
        let cc_mismatch = (row.cost_center || "") !== parent_cc;
        let branch_mismatch = (row.branch || "") !== parent_branch;

        if (cc_mismatch || branch_mismatch) {
            mismatches.push({
                type: "Item",
                row: idx + 1,
                name: row.item_code,
                cost_center: row.cost_center,
                branch: row.branch,
                cc_mismatch,
                branch_mismatch
            });
        }
    });

    // --- Taxes ---
    (frm.doc.taxes || []).forEach((row, idx) => {
        let cc_mismatch = (row.cost_center || "") !== parent_cc;
        let branch_mismatch = (row.branch || "") !== parent_branch;

        if (cc_mismatch || branch_mismatch) {
            mismatches.push({
                type: "Tax",
                row: idx + 1,
                name: row.account_head,
                cost_center: row.cost_center,
                branch: row.branch,
                cc_mismatch,
                branch_mismatch
            });
        }
    });

    // ✅ No mismatch → allow workflow
    if (mismatches.length === 0) {
        return Promise.resolve();
    }

    let rows_html = mismatches.map(m => {
        const cc_badge = m.cc_mismatch
            ? `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:500;padding:2px 8px;border-radius:100px;background:#fff1f1;color:#c0392b;border:0.5px solid #f5c6c6;">✕ ${m.cost_center || '-'}</span>`
            : `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:500;padding:2px 8px;border-radius:100px;background:#f0faf4;color:#1a7f4b;border:0.5px solid #b7e4c7;">✓ ${m.cost_center || '-'}</span>`;

        const branch_badge = m.branch_mismatch
            ? `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:500;padding:2px 8px;border-radius:100px;background:#fff8ec;color:#b45309;border:0.5px solid #fcd9a0;">⚠ ${m.branch || '-'}</span>`
            : `<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:500;padding:2px 8px;border-radius:100px;background:#f0faf4;color:#1a7f4b;border:0.5px solid #b7e4c7;">✓ ${m.branch || '-'}</span>`;

        return `
            <tr style="transition:background 0.1s;" onmouseover="this.style.background='#f9f9f9'" onmouseout="this.style.background=''">
                <td style="padding:9px 12px; border-bottom:1px solid #f0f0f0;">
                    <span style="display:inline-block;font-size:11px;font-weight:500;padding:2px 8px;border-radius:100px;background:#f5f5f5;color:#555;border:0.5px solid #e0e0e0;">${m.type}</span>
                </td>
                <td style="padding:9px 12px; border-bottom:1px solid #f0f0f0; font-family:monospace; font-size:13px; color:#333;font-weight:bold">${m.row}</td>
                <td style="padding:9px 12px; border-bottom:1px solid #f0f0f0; font-size:13px; color:#666;font-weight:bold">${m.name || '-'}</td>
                <td style="padding:9px 12px; border-bottom:1px solid #f0f0f0; font-weight:bold">${cc_badge}</td>
                <td style="padding:9px 12px; border-bottom:1px solid #f0f0f0; font-weight:bold">${branch_badge}</td>
            </tr>
        `;
    }).join("");

    const mismatch_count = mismatches.length;

    let html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; color:#1a1a1a;">

        <!-- Header banner -->
        <div style="display:flex;align-items:center;gap:12px;padding:16px 20px;background:#fff8ec;border-bottom:1px solid #fde8b0;border-radius:8px 8px 0 0; margin:-15px -15px 0;">
            <div style="width:36px;height:36px;border-radius:8px;background:#fef3c7;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;">⚠️</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#92400e;">Dimension mismatch detected</div>
                <div style="font-size:12px;color:#b45309;margin-top:2px;">${mismatch_count} line${mismatch_count !== 1 ? 's' : ''} with mismatched cost center or branch</div>
            </div>
        </div>

        <!-- Parent dimensions -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:20px 0 18px;">
            <div style="background:#f9f9f9;border:1px solid #ebebeb;border-radius:8px;padding:10px 14px;">
                <div style="font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Parent cost center</div>
                <div style="font-size:14px;font-weight:bold;color:#1a1a1a;font-family:monospace;">${parent_cc || '-'}</div>
            </div>
            <div style="background:#f9f9f9;border:1px solid #ebebeb;border-radius:8px;padding:10px 14px;">
                <div style="font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Parent branch</div>
                <div style="font-size:14px;font-weight:bold;color:#1a1a1a;font-family:monospace;">${parent_branch || '-'}</div>
            </div>
        </div>

        <!-- Table label -->
        <div style="font-size:10px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Mismatched lines</div>

        <!-- Mismatch table -->
        <div style="border:1px solid #ebebeb;border-radius:8px;overflow:hidden;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                    <tr style="background:#f9f9f9;">
                        <th style="text-align:left;padding:8px 12px;font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.04em;border-bottom:1px solid #ebebeb;">Type</th>
                        <th style="text-align:left;padding:8px 12px;font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.04em;border-bottom:1px solid #ebebeb;">Row</th>
                        <th style="text-align:left;padding:8px 12px;font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.04em;border-bottom:1px solid #ebebeb;">Ref</th>
                        <th style="text-align:left;padding:8px 12px;font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.04em;border-bottom:1px solid #ebebeb;">Cost center</th>
                        <th style="text-align:left;padding:8px 12px;font-size:10px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.04em;border-bottom:1px solid #ebebeb;">Branch</th>
                    </tr>
                </thead>
                <tbody>${rows_html}</tbody>
            </table>
        </div>

        <!-- Footer note -->
        <div style="display:flex;align-items:center;gap:6px;margin-top:14px;font-size:12px;color:#999;">
            <span style="font-size:14px;">ℹ️</span>
            Proceeding will save with these mismatched dimensions
        </div>
    </div>
    `;
    
    frappe.dom.unfreeze();

    return new Promise((resolve, reject) => {
        let d = new frappe.ui.Dialog({
            title: 'Validation Warning',
            size: 'large',
            fields: [
                { fieldtype: 'HTML', fieldname: 'html_content' }
            ],

            primary_action_label: 'Proceed Anyway',
            primary_action() {
                d.hide();
                resolve(); // ✅ allow workflow
            },

            secondary_action_label: 'Cancel',
            secondary_action() {
                d.hide();
                reject(); // ❌ block workflow
            }
        });

        d.fields_dict.html_content.$wrapper.html(html);
        d.show();
    });
}
function check_job_order_cancellation(frm) {
    return new Promise((resolve) => {
        // Not a credit note -> nothing to ask, make sure the flag is reset
        if (!frm.doc.is_return) {
            frm.set_value("cancel_job_orders", 0);
            resolve();
            return;
        }

        const linked_items = (frm.doc.items || []).filter(row => row.job_order_data);

        // No linked Job Orders -> nothing to ask
        if (linked_items.length === 0) {
            frm.set_value("cancel_job_orders", 0);
            resolve();
            return;
        }

        const plural = linked_items.length !== 1;

        const item_rows_html = linked_items.map(row => `
            <tr>
                <td style="padding:6px 10px; border-bottom:1px solid #f0f0f0; font-size:13px; color:#1a1a1a !important;">${row.item_code || '-'}</td>
                <td style="padding:6px 10px; border-bottom:1px solid #f0f0f0; font-size:13px; font-family:monospace; color:#1a1a1a !important;">${row.job_order_data}</td>
            </tr>
        `).join("");

        // Same theme-proofing as check_dimension_mismatches(): pin the
        // wrapper's own background/color with !important so dark mode
        // can't paint the modal body dark behind dark text.
        const message_html = `
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif; color:#1a1a1a !important; background:#ffffff !important; font-size:13px; line-height:1.6; padding:16px; border-radius:8px;">
                <p style="color:#1a1a1a !important;">This Credit Note is linked to ${linked_items.length} Job Order${plural ? 's' : ''} through the item${plural ? 's' : ''} below.</p>
                <div style="border:1px solid #ebebeb;border-radius:8px;overflow:hidden;margin:10px 0 14px;">
                    <table style="width:100%;border-collapse:collapse;background:#ffffff !important;">
                        <thead>
                            <tr style="background:#f9f9f9 !important;">
                                <th style="text-align:left;padding:6px 10px;font-size:10px;font-weight:600;color:#999 !important;text-transform:uppercase;">Item</th>
                                <th style="text-align:left;padding:6px 10px;font-size:10px;font-weight:600;color:#999 !important;text-transform:uppercase;">Job Order</th>
                            </tr>
                        </thead>
                        <tbody>${item_rows_html}</tbody>
                    </table>
                </div>
                <p style="color:#1a1a1a !important;">Do you want to mark ${plural ? 'these Job Orders' : 'this Job Order'} status as <b>C-Cancelled</b>?</p>
            </div>
        `;

        let d = new frappe.ui.Dialog({
            title: "Job Order Status",
            fields: [
                { fieldtype: "HTML", fieldname: "jo_message" }
            ],
            primary_action_label: "Cancel Job Order",
            primary_action() {
                frm.set_value("cancel_job_orders", 0); // do NOT skip -> server will cancel
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Document Log',
                            document_type: frm.doc.doctype,
                            document_reference: frm.doc.name,
                            data: message_html
                        }
                    }
                });
                d.hide();
                resolve();
            },
            secondary_action_label: "Don't Cancel Job Order",
            secondary_action() {
                frm.set_value("cancel_job_orders", 1); // skip -> server leaves status untouched
                d.hide();
                resolve();
            }
        });

        d.fields_dict.jo_message.$wrapper.html(message_html);

        // Force an explicit choice: hide the (x) close icon so the two
        // buttons above are the only way out of the dialog.
        if (d.get_close_btn) {
            d.get_close_btn().hide();
        }

        d.show();
    });
}