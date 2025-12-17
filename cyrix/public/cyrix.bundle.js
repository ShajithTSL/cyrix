
import './navbar.html';

frappe.ui.form.States = class FormStates {
	constructor(opts) {
		$.extend(this, opts);
		this.state_fieldname = frappe.workflow.get_state_fieldname(this.frm.doctype);

		// no workflow?
		if (!this.state_fieldname) return;

		this.update_fields = frappe.workflow.get_update_fields(this.frm.doctype);

		var me = this;
		$(this.frm.wrapper).bind("render_complete", function () {
			me.refresh();
		});
	}

	setup_help() {
		var me = this;
		this.frm.page.add_action_item(
			__("Help"),
			function () {
				frappe.workflow.setup(me.frm.doctype);
				var state = me.get_state();
				var d = new frappe.ui.Dialog({
					title: "Workflow: " + frappe.workflow.workflows[me.frm.doctype].name,
				});

				frappe.workflow.get_transitions(me.frm.doc).then((transitions) => {
					const next_actions =
						$.map(
							transitions,
							(d) => `${d.action.bold()} ${__("by Role")} ${d.allowed}`
						).join(", ") || __("None: End of Workflow").bold();

					const document_editable_by = frappe.workflow
						.get_document_state_roles(me.frm.doctype, state)
						.map((role) => role.bold())
						.join(", ");

					$(d.body)
						.html(
							`
					<p>${__("Current status")}: ${state.bold()}</p>
					<p>${__("Document is only editable by users with role")}: ${document_editable_by}</p>
					<p>${__("Next actions")}: ${next_actions}</p>
					<p>${__("{0}: Other permission rules may also apply", [__("Note").bold()])}</p>
				`
						)
						.css({ padding: "15px" });

					d.show();
				});
			},
			true
		);
	}

	refresh() {
		// hide if its not yet saved
		if (this.frm.doc.__islocal) {
			this.set_default_state();
			return;
		}

		// state text
		const state = this.get_state();

		if (state) {
			// show actions from that state
			this.show_actions(state);
		}
	}

	show_actions() {
		var added = false;
		var me = this;

		// if the loaded doc is dirty, don't show workflow buttons
		if (this.frm.doc.__unsaved === 1) {
			return;
		}

		function has_approval_access(transition) {
			let approval_access = false;
			const user = frappe.session.user;
			if (
				user === "Administrator" ||
				transition.allow_self_approval ||
				user !== me.frm.doc.owner
			) {
				approval_access = true;
			}
			return approval_access;
		}

		frappe.workflow.get_transitions(this.frm.doc).then((transitions) => {
			this.frm.page.clear_actions_menu();
			transitions.forEach((d) => {
				if (frappe.user_roles.includes(d.allowed) && has_approval_access(d)) {
					added = true;
					me.frm.page.add_action_item(__(d.action), function () {
						frappe.confirm(
							__("Are you sure you want to {0}?", [d.action]),
							() => me.handle_workflow_action(d)
						);
					});
				}
			});

			this.setup_btn(added);
		});
	}
	
	handle_workflow_action(transition) {
		var me = this;
		// set the workflow_action for use in form scripts
		frappe.dom.freeze();
		me.frm.selected_workflow_action = transition.action;
		me.frm.script_manager.trigger("before_workflow_action").then(() => {
			frappe.xcall("frappe.model.workflow.apply_workflow", {
				doc: me.frm.doc,
				action: transition.action,
			})
			.then((doc) => {
				frappe.model.sync(doc);
				me.frm.refresh();
				me.frm.selected_workflow_action = null;
				me.frm.script_manager.trigger("after_workflow_action");
			})
			.finally(() => {
				frappe.dom.unfreeze();
			});
		});
	}

	setup_btn(action_added) {
		if (action_added) {
			this.frm.page.btn_primary.addClass("hide");
			this.frm.page.btn_secondary.addClass("hide");
			this.frm.toolbar.current_status = "";
			this.setup_help();
		}
	}

	set_default_state() {
		var default_state = frappe.workflow.get_default_state(
			this.frm.doctype,
			this.frm.doc.docstatus
		);
		if (default_state) {
			this.frm.set_value(this.state_fieldname, default_state);
		}
	}

	get_state() {
		if (!this.frm.doc[this.state_fieldname]) {
			this.set_default_state();
		}
		return this.frm.doc[this.state_fieldname];
	}
};

frappe.views.ListView = class ListView extends frappe.views.ListView {
    refresh() {
		let fullwidth = JSON.parse(localStorage.container_fullwidth || "false");
		$(document.body).toggleClass("full-width", fullwidth);
        super.refresh();

        try {
            const default_company = frappe.defaults.get_user_default("Company");
            if (!default_company || frappe.ignore_company) return;

            // ✅ Only apply logic if doctype has company field
            if (!frappe.meta.has_field(this.doctype, "company")) {
                return;
            }

            const company_input = this.page?.fields_dict?.company;

            if (company_input) {
                company_input.df.read_only = 1;
                company_input.refresh();
                company_input.set_input(default_company);
            }

            const exists = this.filter_area.get().some(
                f => f[1] === "company" && f[3] === default_company
            );

            if (!exists) {
                this.filter_area.clear(true);
                this.filter_area.add([
                    [this.doctype, "company", "=", default_company]
                ]);

                this.on_filter_change();
                super.refresh();
            }

        } catch (e) {
            console.warn("Auto-company filter failed:", e);
        }
    }
};

frappe.views.ReportView = class ReportView extends frappe.views.ReportView {
    refresh() {
        super.refresh();

        try {
            const default_company = frappe.defaults.get_user_default("Company");
            if (!default_company || frappe.ignore_company) return;

            // ✅ Only apply logic if doctype has company field
            if (!frappe.meta.has_field(this.doctype, "company")) {
                return;
            }

            const company_input = this.page?.fields_dict?.company;

            if (company_input) {
                company_input.df.read_only = 1;
                company_input.refresh();
                company_input.set_input(default_company);
            }

            const exists = this.filter_area.get().some(
                f => f[1] === "company" && f[3] === default_company
            );

            if (!exists) {
                this.filter_area.clear(true);
                this.filter_area.add([
                    [this.doctype, "company", "=", default_company]
                ]);

                this.on_filter_change();
                super.refresh();
            }

        } catch (e) {
            console.warn("Auto-company filter failed:", e);
        }
    }
};

import './navbar.html';

function company_change() {
	// You can use Frappe methods here
	frappe.msgprint("Clicked!");
	
	// Example: call a Frappe API
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "User",
			fields: ["name", "email"],
			limit_page_length: 5
		},
		callback: function(r) {
			console.log(r.message);
		}
	});
}

import DataTable from "frappe-datatable";

// Expose DataTable globally to allow customizations.
window.DataTable = DataTable;

frappe.provide("frappe.widget.utils");
frappe.provide("frappe.views");
frappe.provide("frappe.query_reports");

frappe.standard_pages["query-report"] = function () {
	var wrapper = frappe.container.add_page("query-report");

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Query Report"),
		single_column: true,
	});

	frappe.query_report = new frappe.views.QueryReport({
		parent: wrapper,
	});

	$(wrapper).bind("show", function () {
		frappe.query_report.show();
	});
};

frappe.ui.form.ControlAttach = class ControlAttach extends frappe.ui.form.ControlAttach {
    clear_attachment() {
		let me = this;
		if (this.frm) {
			me.parse_validate_and_set_in_model(null);
			me.refresh();
			me.frm.attachments.remove_attachment_by_filename(me.value, async () => {
				await me.parse_validate_and_set_in_model(null);
				me.refresh();
				// me.frm.doc.docstatus == 1 ? me.frm.save("Update") : me.frm.save();
			});
		} else {
			this.dataurl = null;
			this.fileobj = null;
			this.set_input(null);
			this.parse_validate_and_set_in_model(null);
			this.refresh();
		}
	}
    async on_upload_complete(attachment) {
		if (this.frm) {
			await this.parse_validate_and_set_in_model(attachment.file_url);
			this.frm.attachments.update_attachment(attachment);
			// this.frm.doc.docstatus == 1 ? this.frm.save("Update") : this.frm.save();
		}
		this.set_value(attachment.file_url);
	}
}
frappe.ui.form.ControlAttachImage = class ControlAttachImage extends frappe.ui.form.ControlAttach{
	make_input() {
		super.make_input();

		let $file_link = this.$value.find(".attached-file-link");
		$file_link.popover({
			trigger: "hover",
			placement: "top",
			content: () => {
				return `<div>
					<img src="${this.get_value()}"
						width="150px"
						style="object-fit: contain;"
					/>
				</div>`;
			},
			html: true,
		});
	}
	set_upload_options() {
		super.set_upload_options();
		this.upload_options.restrictions.allowed_file_types = ["image/*"];
	}
};