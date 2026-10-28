
// Iqama Renewal Tool – Page script
// ⚠️ Change YOUR_APP / YOUR_MODULE to your custom app & module folder names.
const IQAMA_METHOD = "cyrix.cyrix_tsl.page.iqama_renewal_tool.iqama_renewal_tool";

frappe.pages["iqama-renewal-tool"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Iqama Renewal Tool"),
		single_column: true,
	});
	wrapper.iqama_tool = new IqamaRenewalTool(page);
};

class IqamaRenewalTool {
	constructor(page) {
		this.page = page;
		this.rows = [];
		this.selected = new Set();

		this.make_filters();
		this.make_body();

		this.page.set_primary_action(__("Update Expiry"), () => this.update(), "check");
		this.page.set_secondary_action(__("Refresh"), () => this.refresh());

		this.refresh();
	}

	make_filters() {
		const refresh = frappe.utils.debounce(() => this.refresh(), 300);

		this.days = this.page.add_field({
			fieldname: "days",
			label: __("Expiring Within (Days)"),
			fieldtype: "Int",
			default: 50,
			change: refresh,
		});
		this.period = this.page.add_field({
			fieldname: "period",
			label: __("Renewal Period"),
			fieldtype: "Select",
			options: [
				{ value: "", label: __("Select Renewal Period") },
				{ value: "3", label: __("3 Months") },
				{ value: "6", label: __("6 Months") },
				{ value: "9", label: __("9 Months") },
				{ value: "12", label: __("12 Months") },
			],
			change: refresh, // recompute preview of new dates
		});
	}

	make_body() {
		this.$body = $(`
			<div class="iqama-tool" style="padding: var(--padding-md, 15px);">
				<div class="iqama-summary text-muted small" style="margin-bottom: 10px;"></div>
				<div class="iqama-table table-responsive"></div>
			</div>`).appendTo(this.page.main);

		// checkbox events (delegated)
		this.$body.on("change", ".iqama-select-all", (e) => {
			const checked = $(e.target).prop("checked");
			this.selected = checked ? new Set(this.rows.map((r) => r.name)) : new Set();
			this.$body.find(".iqama-row-check").prop("checked", checked);
			this.update_summary();
		});
		this.$body.on("change", ".iqama-row-check", (e) => {
			const name = $(e.target).attr("data-name");
			$(e.target).prop("checked") ? this.selected.add(name) : this.selected.delete(name);
			this.$body
				.find(".iqama-select-all")
				.prop("checked", this.rows.length && this.selected.size === this.rows.length);
			this.update_summary();
		});
	}

	refresh() {
		frappe.call({
			method: `${IQAMA_METHOD}.get_employees`,
			args: {
				days: this.days.get_value() || 0,
				company: "Company Al-Halloul Faniye Medical",
				period: this.period.get_value(),
			},
			callback: (r) => {
				this.rows = r.message || [];
				// keep only selections still in the list
				const names = new Set(this.rows.map((d) => d.name));
				this.selected = new Set([...this.selected].filter((n) => names.has(n)));
				this.render();
			},
		});
	}

	render() {
		const esc = frappe.utils.escape_html;
		const has_period = !!this.period.get_value();

		if (!this.rows.length) {
			this.$body.find(".iqama-table").html(`
				<div class="text-muted text-center" style="padding: 40px 0;">
					${__("No employees with Iqama expiring in the selected range.")}
				</div>`);
			this.update_summary();
			return;
		}

		const badge = (days) => {
			const color = days <= 15 ? "red" : days <= 30 ? "orange" : "yellow";
			return `<span class="indicator-pill ${color}">${days} ${__("days")}</span>`;
		};

		const body = this.rows
			.map(
				(d) => `
				<tr>
					<td><input type="checkbox" class="iqama-row-check" data-name="${esc(d.name)}"
						${this.selected.has(d.name) ? "checked" : ""}></td>
					<td><a href="/app/employee/${encodeURIComponent(d.name)}">${esc(d.name)}</a></td>
					<td>${esc(d.employee_name || "")}</td>
					<td>${esc(d.designation || "")}</td>
					<td>${esc(d.civil_id_no || "")}</td>
					<td>${frappe.datetime.str_to_user(d.expiry_date)}</td>
					<td>${esc(d.expiry_hijri)}</td>
					<td>${badge(d.days_left)}</td>
					${
						has_period
							? `<td class="text-success">${frappe.datetime.str_to_user(d.new_expiry_date)}</td>
							   <td class="text-success">${esc(d.new_expiry_hijri)}</td>`
							: ""
					}
				</tr>`
			)
			.join("");

		this.$body.find(".iqama-table").html(`
			<table class="table table-bordered table-hover" style="background: var(--card-bg);">
				<thead>
					<tr>
						<th style="width: 30px;"><input type="checkbox" class="iqama-select-all"
							${this.selected.size === this.rows.length ? "checked" : ""}></th>
						<th>${__("Employee")}</th>
						<th>${__("Employee Name")}</th>
						<th>${__("Designation")}</th>
						<th>${__("Iqama Number")}</th>
						<th>${__("Iqama Expiry")}</th>
						<th>${__("Iqama Expiry (Hijri)")}</th>
						<th>${__("Days Left")}</th>
						${has_period ? `<th>${__("New Expiry")}</th><th>${__("New Expiry (Hijri)")}</th>` : ""}
					</tr>
				</thead>
				<tbody>${body}</tbody>
			</table>`);

		this.update_summary();
	}

	update_summary() {
		this.$body
			.find(".iqama-summary")
			.html(__("{0} employee(s) listed · {1} selected", [this.rows.length, this.selected.size]));
	}

	update() {
		const employees = [...this.selected];
		const period = this.period.get_value();

		if (!employees.length) {
			frappe.msgprint(__("Please select at least one employee."));
			return;
		}
		if (!period) {
			frappe.msgprint(__("Please select a Renewal Period."));
			return;
		}

		frappe.confirm(
			__("Renew Iqama for {0} employee(s) by {1} Hijri months?", [employees.length, period]),
			() => {
				frappe.call({
					method: `${IQAMA_METHOD}.update_expiry`,
					args: { employees, period },
					freeze: true,
					freeze_message: __("Updating Iqama expiry dates..."),
					callback: (r) => this.show_result(r.message || {}),
				});
			}
		);
	}

	show_result({ updated = [], failed = [] }) {
		const esc = frappe.utils.escape_html;
		let html = "";

		if (updated.length) {
			html += `<p class="text-success"><b>${__("{0} updated", [updated.length])}</b></p>
				<table class="table table-bordered small">
					<tr><th>${__("Employee")}</th><th>${__("Old")}</th><th>${__("New")}</th><th>${__("New (Hijri)")}</th></tr>
					${updated
						.map(
							(u) => `<tr>
								<td>${esc(u.employee)}: ${esc(u.employee_name || "")}</td>
								<td>${frappe.datetime.str_to_user(u.old_date)}</td>
								<td>${frappe.datetime.str_to_user(u.new_date)}</td>
								<td>${esc(u.new_hijri)}</td>
							</tr>`
						)
						.join("")}
				</table>`;
		}
		if (failed.length) {
			html += `<p class="text-danger"><b>${__("{0} failed", [failed.length])}</b></p>
				<ul>${failed.map((f) => `<li>${esc(f.employee)}: ${esc(f.error)}</li>`).join("")}</ul>`;
		}

		frappe.msgprint({ title: __("Iqama Renewal"), message: html, wide: true });
		this.selected = new Set();
		this.refresh();
	}
}