// Saturday Off Schedule — ERPNext v16 desk page (/app/saturday-off-schedul)
// Set this to the dotted path of saturday_off_schedul.py in your app:
//   <app>.<module_folder>.page.saturday_off_schedul.saturday_off_schedul
const SR_API = "cyrix.cyrix_tsl.page.saturday_off_schedul.saturday_off_schedul";

frappe.pages["saturday-off-schedul"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Saturday Off Schedule"),
		single_column: true,
	});
	wrapper.saturday_roster = new SaturdayRoster(page);
};

frappe.pages["saturday-off-schedul"].on_page_show = function (wrapper) {
	wrapper.saturday_roster?.refresh();
};

// Styles are injected from here so they always match this script, even if the browser
// still has an older copy of the page CSS cached.
const SR_CSS = `/* Saturday Off Schedule page — scoped to .sr-root */
.sr-root {
	--sr-navy: #0e2b5c; --sr-navy2: #173f7e; --sr-blue: #2e6db4; --sr-row: #e4eef8; --sr-line: #b9c7dd;
	--sr-y-bg: #f1f2f4; --sr-y: #6b7280; --sr-n-bg: #dcefd9; --sr-n: #1e6b27;
	--sr-vac-bg: #fff2c2; --sr-vac: #7a5800; --sr-ot-bg: #ece6f8; --sr-ot: #4b2c91;
	--sr-wfh-bg: #ffe7cc; --sr-wfh: #8a4b00; --sr-ph-bg: #d4eef6; --sr-ph: #0b5d78;
	--sr-sh-bg: #fce1ec; --sr-sh: #a3164f; --sr-none-bg: var(--fg-color); --sr-none: var(--text-muted);
	/* white space on the left and right, centred on wide screens */
	max-width: 1440px;
	margin: 0 auto;
	padding: .5rem clamp(12px, 3vw, 40px) 2rem;
	box-sizing: border-box;
}
[data-theme="dark"] .sr-root {
	--sr-navy: #0b2147; --sr-navy2: #16376b; --sr-blue: #2a5e9c; --sr-row: #1d2838; --sr-line: #33415a;
	--sr-y-bg: #232b37; --sr-y: #aab2bf; --sr-n-bg: #183a22; --sr-n: #8fdb98;
	--sr-vac-bg: #3d3210; --sr-vac: #ffd866; --sr-ot-bg: #2c2445; --sr-ot: #c9b6ff;
	--sr-wfh-bg: #3d2a14; --sr-wfh: #ffc27a; --sr-ph-bg: #123643; --sr-ph: #8fddf5;
	--sr-sh-bg: #43182b; --sr-sh: #ff9cc4;
}

/* tabs + toolbar */
.sr-tabs { display: flex; gap: 1.25rem; border-bottom: 1px solid var(--border-color); margin-bottom: 1rem; overflow-x: auto; }
.sr-tab { background: none; border: 0; border-bottom: 2px solid transparent; padding: .6rem 0; color: var(--text-muted); font-weight: 500; white-space: nowrap; }
.sr-tab.active { color: var(--text-color); border-bottom-color: var(--text-color); }
.sr-count { background: var(--control-bg); border-radius: 999px; padding: 0 .45rem; font-size: .75rem; }
.sr-toolbar { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin-bottom: .9rem; }
.sr-toolbar select.form-control { width: auto; min-width: 9rem; }
.sr-grow { flex: 1; }
.sr-notice { background: var(--bg-blue, #e8f1fd); color: var(--text-on-blue, #1d5fbf); border-radius: var(--border-radius); padding: .5rem .8rem; margin-bottom: .9rem; }
.sr-empty { border: 1px dashed var(--border-color); border-radius: var(--border-radius-md); padding: 2rem; text-align: center; background: var(--fg-color); }
.sr-empty p { color: var(--text-muted); }
.sr-scroll { overflow-x: auto; }

/* the HR sheet */
.sr-sheet { background: var(--fg-color); border: 1px solid var(--sr-line); font-family: Calibri, Carlito, "Segoe UI", sans-serif; font-size: 14px; }
.sr-band { background: var(--sr-navy); color: #fff; text-align: center; }
.sr-band .c { font-size: 1.6rem; font-weight: 700; padding: .35rem; }
.sr-band .t { font-size: 1.2rem; font-weight: 700; padding: .3rem; background: var(--sr-navy2); }
.sr-band .dpt { font-style: italic; padding: .2rem; opacity: .9; }
.sr-table { width: 100%; border-collapse: collapse; }
.sr-table th, .sr-table td { border: 1px solid var(--sr-line); padding: 0; }
.sr-table thead th { background: var(--sr-blue); color: #fff; text-align: center; padding: .35rem .5rem; line-height: 1.25; }
.sr-table thead th.nm { min-width: 13rem; }
.sr-table thead th.past::after { content: " (past)"; font-weight: 400; font-size: .8em; opacity: .85; }
.sr-sr { text-align: center; padding: .3rem .5rem !important; width: 4.5rem; }
.sr-name { padding: .3rem .5rem !important; white-space: nowrap; }
.sr-table tbody tr:nth-child(even) .sr-sr, .sr-table tbody tr:nth-child(even) .sr-name { background: var(--sr-row); }
.sr-table tr.sr-me .sr-name { font-weight: 700; }
.sr-cell { min-width: 7.5rem; position: relative; text-align: center; }
.sr-cell select, .sr-cell span:not(.sr-sw) { display: block; width: 100%; border: 0; background: transparent; color: inherit; padding: .3rem .25rem; font: inherit; font-weight: 700; text-align: center; text-align-last: center; appearance: none; -webkit-appearance: none; cursor: pointer; }
.sr-cell span:not(.sr-sw) { cursor: default; }
.sr-cell select option { background: var(--fg-color); color: var(--text-color); font-weight: 400; }
.sr-sw { position: absolute; top: 1px; right: 3px; font-size: .72rem; font-weight: 700; }
.sr-st-Y { background: var(--sr-y-bg); color: var(--sr-y); } .sr-st-Y select, .sr-st-Y span { font-weight: 400 !important; }
.sr-st-N { background: var(--sr-n-bg); color: var(--sr-n); }
.sr-st-VAC { background: var(--sr-vac-bg); color: var(--sr-vac); }
.sr-st-OT { background: var(--sr-ot-bg); color: var(--sr-ot); }
.sr-st-WFH { background: var(--sr-wfh-bg); color: var(--sr-wfh); }
.sr-st-PH { background: var(--sr-ph-bg); color: var(--sr-ph); }
.sr-st-SH { background: var(--sr-sh-bg); color: var(--sr-sh); }
.sr-st-none { background: var(--sr-none-bg); color: var(--sr-none); }
.sr-table tfoot td { background: var(--sr-row); text-align: center; font-weight: 700; padding: .3rem .5rem; }
.sr-table tfoot td.lab { text-align: right; }
.sr-legend-wrap { padding: 1.25rem .75rem 0; }
.sr-legend { border-collapse: collapse; min-width: min(22rem, 100%); }
.sr-legend th { background: var(--sr-navy); color: #fff; text-align: center; padding: .3rem .5rem; border: 1px solid var(--sr-line); }
.sr-legend td { border: 1px solid var(--sr-line); padding: .25rem .5rem; }
.sr-legend td.k { text-align: center; font-weight: 700; width: 5.5rem; }
.sr-foot { margin-top: 1rem; text-align: center; font-style: italic; color: var(--text-muted); font-size: .85rem; padding: .35rem; border-top: 1px solid var(--sr-line); background: var(--sr-row); }

/* chips, swaps list, history */
.sr-chip { display: inline-block; border-radius: 4px; padding: 0 .4rem; font-weight: 700; font-family: Calibri, Carlito, sans-serif; }
.sr-preview td { padding: .2rem 1rem .2rem 0; }
.sr-list { background: var(--fg-color); border: 1px solid var(--border-color); border-radius: var(--border-radius-md); overflow: hidden; }
.sr-list-head, .sr-item { display: grid; grid-template-columns: minmax(12rem, 2fr) minmax(8rem, 1fr) minmax(9rem, 1fr) auto; gap: .75rem; align-items: center; padding: .65rem 1rem; }
.sr-list-head { background: var(--subtle-fg, var(--control-bg)); color: var(--text-muted); font-size: .78rem; }
.sr-item { border-top: 1px solid var(--border-color); }
.sr-item small { display: block; color: var(--text-muted); }
.sr-acts { display: flex; gap: .35rem; flex-wrap: wrap; justify-content: flex-end; }
.sr-item details { grid-column: 1 / -1; color: var(--text-muted); }
.sr-item details p { color: var(--text-color); margin: .3rem 0 0; }
.sr-item details ul { margin: .3rem 0 0; padding-left: 1rem; font-size: .8rem; }
.sr-card { padding: 1rem; }
.sr-hist-table { margin: 0; }

@media (max-width: 640px) {
	.sr-list-head { display: none; }
	.sr-item { grid-template-columns: 1fr; gap: .35rem; }
	.sr-acts { justify-content: flex-start; }
}

@media print {
	.navbar, .page-head, .sr-tabs, .sr-toolbar, .sr-notice, .layout-side-section, .page-actions { display: none !important; }
	.sr-table thead th.past::after { content: ""; }
	.sr-sw { display: none; }
	.sr-sheet, .sr-sheet * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}

/* filter-related additions */
.sr-notice.sr-warn { background: var(--bg-orange, #fff1e7); color: var(--text-on-orange, #c2410c); }
.sr-notice .btn { margin-left: .5rem; }
@media print {
	.page-form, .standard-filter-section { display: none !important; }
}

/* keep the sheet away from the edges and give it a soft card look */
.sr-root .sr-sheet { border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, .06); }
.sr-root .sr-name { padding-left: .75rem !important; }

@media print {
	.sr-root { max-width: none; padding: 0; }
	.sr-root .sr-sheet { box-shadow: none; border-radius: 0; }
}

/* bulk change bar */
.sr-bulk { display: flex; flex-wrap: wrap; align-items: center; gap: .6rem 1.5rem; padding: .55rem .9rem; margin-bottom: .75rem;
	border: 1px solid var(--sr-blue); border-radius: 8px; background: var(--fg-color);
	box-shadow: 0 2px 6px rgba(0, 0, 0, .06); position: sticky; top: calc(var(--navbar-height, 48px) + 4px); z-index: 5; }
.sr-bulk-left { display: flex; align-items: center; gap: .5rem; }
.sr-bulk-count { font-weight: 600; color: var(--text-color); white-space: nowrap; }
.sr-bulk-count b { display: inline-grid; place-items: center; min-width: 1.6rem; height: 1.6rem; padding: 0 .4rem; margin-right: .35rem;
	border-radius: 999px; background: var(--sr-blue); color: #fff; font-size: .8rem; }
.sr-link { background: none; border: 0; padding: 0; color: var(--text-muted); font-size: .85rem; text-decoration: underline; cursor: pointer; }
.sr-bulk-group { display: flex; align-items: center; gap: .5rem; }
.sr-bulk-label { color: var(--text-muted); font-size: .8rem; white-space: nowrap; }
.sr-seg { display: inline-flex; border: 1px solid var(--border-color); border-radius: 6px; overflow: hidden; }
.sr-seg button { border: 0; border-right: 1px solid var(--border-color); background: var(--fg-color); color: var(--text-color);
	padding: .28rem .65rem; font-size: .82rem; font-weight: 500; line-height: 1.4; cursor: pointer; white-space: nowrap; }
.sr-seg button:last-child { border-right: 0; }
.sr-seg button:hover { background: var(--control-bg); }
.sr-seg button.sr-on { background: var(--sr-blue); color: #fff; }
.sr-seg button.sr-yes { background: var(--sr-y-bg); color: var(--sr-y); }
.sr-seg button.sr-no { background: var(--sr-n-bg); color: var(--sr-n); font-weight: 700; }
.sr-seg button.sr-yes:hover, .sr-seg button.sr-no:hover { filter: brightness(.95); }
.sr-mini-select { width: auto !important; height: auto; padding: .28rem 1.6rem .28rem .6rem; font-size: .82rem; border: 1px solid var(--border-color);
	border-radius: 6px; background-color: var(--fg-color); color: var(--text-color); cursor: pointer; }
.sr-hint { color: var(--text-muted); font-size: .82rem; margin: -.35rem 0 .6rem; }

/* checkbox column */
.sr-table th.sr-chk, .sr-table td.sr-chk { width: 2.5rem; min-width: 2.5rem; text-align: center; vertical-align: middle; padding: 0 !important; }
.sr-table td.sr-chk { background: var(--fg-color); }
.sr-table .sr-chk input { display: block; margin: 0 auto; width: 15px; height: 15px; cursor: pointer; accent-color: var(--sr-blue); }
.sr-table tr.sr-selected .sr-sr, .sr-table tr.sr-selected .sr-name, .sr-table tr.sr-selected td.sr-chk { background: #dbe8f8 !important; }
[data-theme="dark"] .sr-table tr.sr-selected .sr-sr, [data-theme="dark"] .sr-table tr.sr-selected .sr-name, [data-theme="dark"] .sr-table tr.sr-selected td.sr-chk { background: #1f3354 !important; }


/* Excel import dialog */
.sr-import-steps { display: grid; gap: .8rem; margin-bottom: .5rem; }
.sr-step { display: flex; gap: .75rem; align-items: flex-start; }
.sr-step > span { flex: none; display: grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #2e6db4; color: #fff; font-weight: 600; font-size: .8rem; }
.sr-step p { margin: .15rem 0 .4rem; color: var(--text-muted); }
.sr-imp-ok { background: #e5f5e8; color: #1e6b27; border-radius: 6px; padding: .6rem .8rem; }
.sr-imp-err { background: #fdecec; color: #b42318; border-radius: 6px; padding: .6rem .8rem; margin-bottom: .5rem; }
.sr-imp-ok p { margin: .2rem 0 0; }
.sr-imp-err ul { margin: .35rem 0 0; padding-left: 1.1rem; max-height: 12rem; overflow: auto; }
[data-theme="dark"] .sr-imp-ok { background: #15301c; color: #86db97; }
[data-theme="dark"] .sr-imp-err { background: #3a1717; color: #ff9a9a; }

.sr-moves { margin: .5rem 0 0; min-width: 14rem; }
.sr-moves th, .sr-moves td { padding: .15rem .6rem .15rem 0; }
.sr-moves th { font-weight: 500; opacity: .8; }
.sr-imp-big { background: #fff1e7; color: #9a3412; }
.sr-imp-warn { margin-top: .5rem !important; font-weight: 600; }
[data-theme="dark"] .sr-imp-big { background: #3a2414; color: #ffb27a; }

/* cells changed by the last import */
.sr-cell.sr-flash { box-shadow: inset 0 0 0 2px #f0ae33; animation: sr-pulse 1.2s ease-in-out 3; }
@keyframes sr-pulse { 50% { box-shadow: inset 0 0 0 3px #f0ae33; } }
@media (prefers-reduced-motion: reduce) { .sr-cell.sr-flash { animation: none; } }

@media (max-width: 768px) { .sr-bulk { position: static; } }
@media print { .sr-bulk, .sr-hint, .sr-chk { display: none !important; } }
`;
(function sr_inject_css() {
	let el = document.getElementById("sr-page-style");
	if (!el) {
		el = document.createElement("style");
		el.id = "sr-page-style";
		document.head.appendChild(el);
	}
	el.textContent = SR_CSS;
})();

const SR_CODES = [
	{ c: "Y", label: "Yes", key: "YES", desc: "Employee is working this Saturday" },
	{ c: "N", label: "No", key: "NO", desc: "Employee is off this Saturday" },
	{ c: "VAC", label: "Vacation", key: "Vacation", desc: "Employee on approved annual leave" },
	{ c: "OT", label: "OT", key: "OT", desc: "Overtime scheduled" },
	{ c: "WFH", label: "WFH", key: "WFH", desc: "Working from home" },
	{ c: "PH", label: "PH", key: "PH", desc: "Public holiday – all staff off" },
	{ c: "SH", label: "Yes*", key: "YES*", desc: "Off / working on shift arrangement" },
];
const SR_WORKING = new Set(["Y", "OT", "WFH", "SH"]);
const SR_OPEN = ["Awaiting Partner", "Awaiting Approval"];
const SR_PILL = { "Awaiting Partner": "orange", "Awaiting Approval": "blue", Approved: "green", Rejected: "red", Cancelled: "gray" };

class SaturdayRoster {
	constructor(page) {
		this.page = page;
		this.view = "schedule";
		this.ym = frappe.datetime.get_today().slice(0, 7);
		this.swap_filter = "open";
		this.hist_period = "all";
		this.selected = new Set(); // employees ticked for bulk change
		this.bulk_dates = null; // Saturdays ticked in the bulk bar (null = all upcoming)
		this.$root = $('<div class="sr-root"></div>').appendTo(page.main);
		this.setup_filters();
		this.setup_page_actions();
		this.bind_events();
		this.refresh();
	}

	// ---------------------------------------------------------- helpers
	// frappe.call returns a jQuery promise (no .finally), so wrap it in a native Promise
	call(fn, args = {}) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: `${SR_API}.${fn}`,
				args,
				callback: (r) => resolve(r.message),
				error: (err) => reject(err),
			});
		});
	}
	e(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}
	code(c) {
		return SR_CODES.find((x) => x.c === c);
	}
	chip(c) {
		const i = this.code(c);
		return `<span class="sr-chip sr-st-${c || "none"}">${i ? this.e(i.label) : "—"}</span>`;
	}
	head_date(d) {
		return moment(d).format("DD-MMM-YYYY").toUpperCase();
	}
	month_label(ym) {
		return moment(ym + "-01").format("MMMM YYYY");
	}
	shift_month(ym, n) {
		return moment(ym + "-01").add(n, "months").format("YYYY-MM");
	}
	is_past(d) {
		return d < frappe.datetime.get_today();
	}
	status_of(emp, d) {
		return this.d?.month?.status?.[emp]?.[d] || "";
	}
	filters() {
		const v = (f) => (f ? f.get_value() || "" : "");
		return { company: v(this.f_company), branch: v(this.f_branch), employee: v(this.f_employee) };
	}
	scope_label() {
		const f = this.filters();
		return [f.company || __("All companies"), f.branch].filter(Boolean).join(" / ");
	}

	// ---------------------------------------------------------- filters
	setup_filters() {
		// One handler for all three filters. Link fields can fire "change" more than once
		// (typing, selecting, blur), so changes are debounced and only reload when a value really changed.
		const changed = (which) => {
			if (!this.ready) return;
			clearTimeout(this._ft);
			this._ft = setTimeout(() => {
				const f = this.filters();
				// Employee must belong to the selected Company / Branch
				if ((which === "company" || which === "branch") && f.employee) {
					this._last_key = null;
					Promise.resolve(this.f_employee.set_value("")).then(() => changed("employee"));
					return;
				}
				const key = JSON.stringify(f);
				if (key === this._last_key) return;
				this._last_key = key;
				this.refresh();
			}, 250);
		};
		const make = (df) => {
			const field = this.page.add_field({ ...df, onchange: () => changed(df.fieldname) });
			// Also catch selections from the dropdown and cleared inputs
			field.$input?.on("change awesomplete-selectcomplete", () => changed(df.fieldname));
			return field;
		};
		this.f_company = make({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		});
		this.f_branch = make({ fieldname: "branch", label: __("Branch"), fieldtype: "Link", options: "Branch" });
		this.f_employee = make({
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: () => {
				const q = { status: "Active" , saudization: 0};
				const company = this.f_company.get_value();
				const branch = this.f_branch.get_value();
				if (company) q.company = company;
				if (branch) q.branch = branch;
				return { filters: q };
			},
		});
		this.f_employee.get_query = this.f_employee.df.get_query;
		this._last_key = JSON.stringify(this.filters());
		this.ready = true;
	}

	setup_page_actions() {
		this.page.set_primary_action(__("Print"), () => this.print_sheet(), "printer");
		this.page.add_inner_button(__("Excel"), () => this.export_xlsx(), __("Export"));
		this.page.add_inner_button(__("CSV (no colours)"), () => this.export_csv(), __("Export"));
		this.page.add_inner_button(__("Import from Excel"), () => this.import_dialog());
		this.page.add_menu_item(__("Edit Sheet Heading"), () => this.heading_dialog());
		this.page.add_menu_item(__("Settings"), () => this.settings_dialog());
	}

	refresh() {
		// If a filter changes while loading, load again with the new filters afterwards
		if (this._loading) {
			this._reload = true;
			return this._loading;
		}
		this._loading = this.call("get_data", { ym: this.ym, ...this.filters() })
			.then((d) => {
				this.d = d;
				const ids = new Set((d.rows || []).map((r) => r.id));
				this.selected.forEach((id) => !ids.has(id) && this.selected.delete(id));
				this._last_key = JSON.stringify(this.filters());
				if (d.api_version !== 3 && !this._warned) {
					this._warned = true;
					frappe.msgprint({
						title: __("Old server code"),
						indicator: "red",
						message: __("The server is still running an old saturday_off_schedul.py, so filters are ignored. Replace the .py file and restart bench."),
					});
				}
				this.render();
				if (this.view === "history") this.load_history();
			})
			.finally(() => {
				this._loading = null;
				if (this._reload) {
					this._reload = false;
					this.refresh();
				}
			});
		return this._loading;
	}

	render() {
		const d = this.d;
		const open = d.swaps.filter((s) => SR_OPEN.includes(s.status)).length;
		if (!d.month) this.page.set_indicator(__("Not Created"), "orange");
		else if (d.locked) this.page.set_indicator(__("Archived"), "gray");
		else if (d.missing) this.page.set_indicator(__("Incomplete"), "orange");
		else this.page.set_indicator(__("Published"), "green");

		const tab = (v, label, extra = "") =>
			`<button class="sr-tab ${this.view === v ? "active" : ""}" data-view="${v}">${label}${extra}</button>`;
		let html = `<div class="sr-tabs">
			${tab("schedule", __("Schedule"))}
			${tab("swaps", __("Swap Requests"), open ? ` <span class="sr-count">${open}</span>` : "")}
			${tab("history", __("History"))}
		</div><div class="sr-body">`;
		if (this.view === "schedule") html += this.schedule_html();
		else if (this.view === "swaps") html += this.swaps_html();
		else html += `<div class="sr-history"><div class="text-muted">${__("Loading…")}</div></div>`;
		const scroll = this.$root.find(".sr-scroll").scrollLeft() || 0;
		this.$root.html(html + "</div>");
		this.$root.find(".sr-scroll").scrollLeft(scroll);
	}

	// ---------------------------------------------------------- schedule
	schedule_html() {
		const d = this.d, hr = d.ctx.is_hr;
		const h = d.heading || {
			title: d.settings?.company_title || this.filters().company || "",
			subtitle: d.settings?.subtitle || d.settings?.department_label || "",
			footer: d.settings?.footer || "",
		};
		const months = new Set(d.months);
		[0, 1, 2].forEach((n) => months.add(this.shift_month(frappe.datetime.get_today().slice(0, 7), n)));
		months.add(this.ym);
		const editable = hr && d.month && !d.locked;
		const upcoming = d.saturdays.filter((x) => !this.is_past(x));
		const f = this.filters();

		let html = `<div class="sr-toolbar">
			<button class="btn btn-default btn-sm" data-act="prev" aria-label="${__("Previous month")}">‹</button>
			<select class="form-control input-sm sr-month" aria-label="${__("Month")}">
				${[...months].sort().reverse().map((m) => `<option value="${m}" ${m === this.ym ? "selected" : ""}>${this.month_label(m)}${d.months.includes(m) ? "" : " (" + __("not created") + ")"}</option>`).join("")}
			</select>
			<button class="btn btn-default btn-sm" data-act="next" aria-label="${__("Next month")}">›</button>
			<span class="sr-grow"></span>
			${hr ? `<button class="btn btn-default btn-sm" data-act="heading">${frappe.utils.icon("edit", "xs")} ${__("Edit Heading")}</button>` : ""}
			${editable && upcoming.length ? `<select class="form-control input-sm sr-phdate" aria-label="${__("Public holiday")}">${upcoming.map((x) => `<option value="${x}">${this.head_date(x)}</option>`).join("")}</select>
				<button class="btn btn-default btn-sm" data-act="ph">${__("Mark Public Holiday")}</button>` : ""}
			${d.month && upcoming.length ? `<button class="btn btn-default btn-sm" data-act="new-swap">${__("New Swap Request")}</button>` : ""}
		</div>`;

		if (d.month && d.locked) html += `<div class="sr-notice">${__("Every Saturday in this month has passed, so it’s kept in the log as read only.")}</div>`;
		else if (d.month && d.saturdays.some((x) => this.is_past(x))) html += `<div class="sr-notice">${__("Saturdays that have passed are locked and kept as the record.")}</div>`;
		if (d.missing && !f.employee)
			html += `<div class="sr-notice sr-warn">${__("{0} employees in {1} have no Saturdays set for {2}.", [d.missing, this.e(this.scope_label()), this.month_label(this.ym)])}
				${hr ? ` <button class="btn btn-xs btn-default" data-act="create">${__("Add them, continuing their pattern")}</button>` : ""}</div>`;

		if (!d.month) {
			if (d.locked) return html + `<div class="sr-empty"><h4>${__("No schedule was saved for {0}", [this.month_label(this.ym)])}</h4></div>`;
			return html + `<div class="sr-empty"><h4>${__("{0} isn’t created yet", [this.month_label(this.ym)])}</h4>
				<p>${__("Creating it adds the active employees of {0} and continues each person’s alternating Yes/No pattern from the previous month.", [this.e(this.scope_label())])}</p>
				${hr ? `<button class="btn btn-primary btn-sm" data-act="create">${__("Create {0} Schedule", [this.month_label(this.ym)])}</button>` : `<p>${__("Ask HR to create it.")}</p>`}</div>`;
		}
		if (!d.rows.length)
			return html + `<div class="sr-empty"><h4>${__("No employees match these filters")}</h4><p>${__("Change Company, Branch or Employee above.")}</p></div>`;

		const swapped = new Map();
		d.swaps.filter((x) => x.ym === this.ym && x.status === "Approved").forEach((x) =>
			[x.date, x.ret].filter(Boolean).forEach((day) => {
				swapped.set(x.emp + "|" + day, x.partnerName);
				swapped.set(x.partner + "|" + day, x.empName);
			})
		);
		const work = d.saturdays.map(() => 0), off = d.saturdays.map(() => 0);
		const me = d.ctx.employee;
		const bulk = editable && upcoming.length > 0;
		if (bulk) html += this.bulk_bar_html(upcoming);
		const sub = [h.subtitle, f.branch].filter(Boolean).join(" — ");

		html += `<div class="sr-sheet">
			<div class="sr-band"><div class="c">${this.e(h.title)}</div>
			<div class="t">${__("Saturday Off Schedule")} — ${this.e(this.month_label(this.ym).toUpperCase())}</div>
			${sub ? `<div class="dpt">${this.e(sub)}</div>` : ""}</div>
			<div class="sr-scroll"><table class="sr-table"><thead><tr>${bulk ? `<th class="sr-chk"><input type="checkbox" class="sr-chk-all" aria-label="${__("Select all")}" ${d.rows.length && d.rows.every((r) => this.selected.has(r.id)) ? "checked" : ""}></th>` : ""}<th>SR #</th><th class="nm">${__("Employee Name")}</th>
			${d.saturdays.map((x) => `<th class="${this.is_past(x) ? "past" : ""}">${this.head_date(x)}<br>(Sat)</th>`).join("")}</tr></thead><tbody>`;

		d.rows.forEach((r) => {
			const sel = this.selected.has(r.id);
			html += `<tr class="${r.id === me ? "sr-me" : ""} ${sel ? "sr-selected" : ""}">${bulk ? `<td class="sr-chk"><input type="checkbox" class="sr-chk-row" data-emp="${this.e(r.id)}" aria-label="${__("Select")} ${this.e(r.name)}" ${sel ? "checked" : ""}></td>` : ""}<td class="sr-sr">${this.e(r.sr)}</td><td class="sr-name">${this.e(r.name)}</td>`;
			d.saturdays.forEach((day, i) => {
				const c = this.status_of(r.id, day);
				if (c) SR_WORKING.has(c) ? work[i]++ : off[i]++;
				const sw = swapped.get(r.id + "|" + day);
				const mark = sw ? `<span class="sr-sw" title="${this.e(__("Swapped with {0}", [sw]))}">⇄</span>` : "";
				if (editable && !this.is_past(day)) {
					const fl = this.flash?.has(r.id + "|" + day) ? " sr-flash" : "";
					html += `<td class="sr-cell sr-st-${c || "none"}${fl}">${mark}<select data-emp="${this.e(r.id)}" data-date="${day}" aria-label="${this.e(r.name)} ${this.head_date(day)}">
						<option value="">—</option>${SR_CODES.map((x) => `<option value="${x.c}" ${x.c === c ? "selected" : ""}>${x.label}</option>`).join("")}</select></td>`;
				} else {
					html += `<td class="sr-cell sr-st-${c || "none"}">${mark}<span>${c ? this.e(this.code(c).label) : "—"}</span></td>`;
				}
			});
			html += "</tr>";
		});
		html += `</tbody><tfoot>
			<tr>${bulk ? '<td class="sr-chk"></td>' : ""}<td colspan="2" class="lab">${__("Working")}</td>${work.map((n) => `<td>${n}</td>`).join("")}</tr>
			<tr>${bulk ? '<td class="sr-chk"></td>' : ""}<td colspan="2" class="lab">${__("Off")}</td>${off.map((n) => `<td>${n}</td>`).join("")}</tr>
		</tfoot></table></div>
		<div class="sr-legend-wrap"><table class="sr-legend"><thead><tr><th colspan="2">${__("Legend / Key")}</th></tr></thead><tbody>
			${SR_CODES.map((x) => `<tr><td class="k sr-st-${x.c}">${x.key}</td><td>${__(x.desc)}</td></tr>`).join("")}
			<tr><td class="k">⇄</td><td>${__("Changed by an approved swap")}</td></tr>
		</tbody></table></div>
		${h.footer ? `<div class="sr-foot">${this.e(h.footer)}</div>` : ""}</div>`;
		return html;
	}

	// ---------------------------------------------------------- bulk change
	reset_bulk() {
		this.selected.clear();
		this.bulk_dates = null;
		this._last_index = null;
	}

	bulk_dates_list(upcoming) {
		if (!this.bulk_dates) this.bulk_dates = new Set(upcoming);
		return upcoming.filter((x) => this.bulk_dates.has(x));
	}

	bulk_bar_html(upcoming) {
		const n = this.selected.size;
		if (!n) return `<div class="sr-hint">${__("Tip: tick employees in the first column to change many cells at once. Hold Shift to tick a range.")}</div>`;
		const dates = this.bulk_dates_list(upcoming);
		const other = SR_CODES.filter((x) => !["Y", "N"].includes(x.c));
		return `<div class="sr-bulk">
			<div class="sr-bulk-left">
				<span class="sr-bulk-count"><b>${n}</b>${__("selected")}</span>
				<button class="sr-link" data-act="bulk-clear">${__("Clear")}</button>
			</div>
			<div class="sr-bulk-group">
				<span class="sr-bulk-label">${__("Saturdays")}</span>
				<div class="sr-seg">${upcoming.map((x) => `<button class="${dates.includes(x) ? "sr-on" : ""}" data-bulk-date="${x}" aria-pressed="${dates.includes(x)}">${moment(x).format("DD MMM")}</button>`).join("")}</div>
			</div>
			<div class="sr-bulk-group">
				<span class="sr-bulk-label">${__("Set to")}</span>
				<div class="sr-seg">
					<button class="sr-yes" data-bulk="Y">${__("Yes")}</button>
					<button class="sr-no" data-bulk="N">${__("No")}</button>
					<button data-bulk="FLIP" title="${__("Yes becomes No and No becomes Yes. Other statuses stay.")}">${__("Flip")} ⇄</button>
				</div>
				<select class="sr-mini-select sr-bulk-other" aria-label="${__("Set another status")}">
					<option value="">${__("More…")}</option>
					${other.map((x) => `<option value="${x.c}">${x.label}</option>`).join("")}
					<option value="CLEAR">${__("Clear (—)")}</option>
				</select>
			</div>
		</div>`;
	}

	apply_bulk(code) {
		const upcoming = this.d.saturdays.filter((x) => !this.is_past(x));
		const dates = this.bulk_dates_list(upcoming);
		const employees = [...this.selected];
		if (!employees.length) return;
		if (!dates.length) return frappe.msgprint(__("Tick at least one Saturday in the bar."));
		const label = code === "FLIP" ? __("flip Yes ⇄ No") : __("set to “{0}”", [code ? this.code(code).label : "—"]);
		const run = () =>
			this.call("bulk_set_cells", { ym: this.ym, employees, dates, code }).then((n) => {
				frappe.show_alert({ message: __("{0} cells changed.", [n]), indicator: "green" });
				this.refresh();
			});
		if (employees.length * dates.length > 10)
			frappe.confirm(__("{0} employees × {1} Saturdays: {2}?", [employees.length, dates.length, label]), run);
		else run();
	}

	// ---------------------------------------------------------- swaps
	swaps_html() {
		const d = this.d, ctx = d.ctx;
		const list = d.swaps.filter((s) =>
			this.swap_filter === "all" ? true : this.swap_filter === "open" ? SR_OPEN.includes(s.status) : s.status === this.swap_filter
		);
		const filters = [["open", __("Open")], ["Approved", __("Approved")], ["Rejected", __("Rejected")], ["Cancelled", __("Cancelled")], ["all", __("All")]];
		let html = `<div class="sr-toolbar">
			<button class="btn btn-primary btn-sm" data-act="new-swap">${__("New Swap Request")}</button>
			<span class="sr-grow"></span>
			<select class="form-control input-sm sr-swap-filter" aria-label="${__("Filter")}">${filters.map(([v, l]) => `<option value="${v}" ${v === this.swap_filter ? "selected" : ""}>${l}</option>`).join("")}</select>
		</div>`;
		if (!list.length) return html + `<div class="sr-empty"><p>${d.swaps.length ? __("No requests match this filter.") : __("No swap requests for {0}.", [this.e(this.scope_label())])}</p></div>`;

		html += `<div class="sr-list"><div class="sr-list-head"><span>${__("Employees")}</span><span>${__("Saturday")}</span><span>${__("Status")}</span><span></span></div>`;
		list.forEach((s) => {
			const acts = [];
			const btn = (cls, act, label) => `<button class="btn ${cls} btn-xs" data-swap="${s.id}" data-ym="${s.ym}" data-do="${act}">${label}</button>`;
			const mine = ctx.user === s.createdBy || ctx.employee === s.emp;
			if (s.status === "Awaiting Partner" && (ctx.employee === s.partner || ctx.is_hr))
				acts.push(btn("btn-primary", "accept", __("Accept")), btn("btn-default", "decline", __("Decline")));
			if (s.status === "Awaiting Approval" && ctx.is_hr)
				acts.push(btn("btn-primary", "approve", __("Approve")), btn("btn-danger", "reject", __("Reject")));
			if (SR_OPEN.includes(s.status) && (mine || ctx.is_hr)) acts.push(btn("btn-default", "cancel", __("Withdraw")));
			if (s.status === "Approved" && ctx.is_hr && [s.date, s.ret].filter(Boolean).every((x) => !this.is_past(x)))
				acts.push(btn("btn-default", "cancel", __("Cancel Swap")));

			const hist = (s.history || []).map((h) => `<li>${this.e(__(h.action))} · ${frappe.datetime.str_to_user(h.at)} · ${this.e(frappe.user.full_name(h.by))}</li>`).join("");
			html += `<div class="sr-item">
				<div><b>${this.e(s.empName)}</b> ⇄ <b>${this.e(s.partnerName)}</b>
					<small>${this.e(s.empName.split(" ")[0])}: ${this.chip(s.empStatus)} → ${this.chip(s.partnerStatus)}</small></div>
				<div>${this.head_date(s.date)}${s.ret ? `<small>${__("Return")}: ${this.head_date(s.ret)}</small>` : ""}</div>
				<div><span class="indicator-pill ${SR_PILL[s.status]}">${__(s.status)}</span></div>
				<div class="sr-acts">${acts.join("")}</div>
				<details><summary>${__("Reason and history")}</summary><p>${this.e(s.reason)}</p>${s.remarks ? `<p>${__("Remarks")}: ${this.e(s.remarks)}</p>` : ""}<ul>${hist}</ul></details>
			</div>`;
		});
		return html + "</div>";
	}

	swap_dialog() {
		const d = this.d, ctx = d.ctx;
		if (!d.month) return frappe.msgprint(__("Create the schedule for {0} first.", [this.month_label(this.ym)]));
		const upcoming = d.saturdays.filter((x) => !this.is_past(x));
		if (!upcoming.length) return frappe.msgprint(__("All Saturdays in {0} have passed. Pick a later month on the Schedule tab.", [this.month_label(this.ym)]));
		if (!ctx.is_hr && !ctx.employee) return frappe.msgprint(__("Your user isn’t linked to an Employee record. Ask HR to set it."));

		const people = (d.people || d.rows)
			.filter((p) => d.month.status[p.id])
			.map((p) => ({ value: p.id, label: (p.sr ? p.sr + " – " : "") + p.name }));
		const sats = upcoming.map((x) => ({ value: x, label: this.head_date(x) }));
		const dlg = new frappe.ui.Dialog({
			title: __("New Swap Request — {0}", [this.month_label(this.ym)]),
			fields: [
				{ fieldname: "date", fieldtype: "Select", label: __("Saturday to Swap"), options: sats, reqd: 1 },
				{ fieldname: "return_date", fieldtype: "Select", label: __("Return Saturday (optional)"), options: [{ value: "", label: __("No return swap") }, ...sats],
					description: __("Swap back on this Saturday so both keep the same number of days off.") },
				{ fieldtype: "Column Break" },
				{ fieldname: "employee", fieldtype: "Select", label: __("Employee"), options: people, reqd: 1, read_only: ctx.is_hr ? 0 : 1 },
				{ fieldname: "partner", fieldtype: "Select", label: __("Swap With"), options: [{ value: "", label: "" }, ...people], reqd: 1,
					description: __("Showing employees of {0}.", [this.e(this.scope_label())]) },
				{ fieldtype: "Section Break" },
				{ fieldname: "preview", fieldtype: "HTML" },
				{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
			],
			primary_action_label: __("Send Request"),
			primary_action: (v) => {
				this.call("create_swap", { ym: this.ym, date: v.date, return_date: v.return_date || null, employee: v.employee, partner: v.partner, reason: v.reason })
					.then(() => {
						dlg.hide();
						frappe.show_alert({ message: __("Swap request sent."), indicator: "green" });
						this.view = "swaps";
						this.swap_filter = "open";
						this.refresh();
					});
			},
		});
		const preview = () => {
			const v = dlg.get_values(true);
			if (!v.date || !v.employee || !v.partner || v.employee === v.partner) return dlg.fields_dict.preview.$wrapper.html("");
			const nm = (id) => (d.people || d.rows).find((r) => r.id === id)?.name || id;
			const line = (day) => {
				const a = this.status_of(v.employee, day), b = this.status_of(v.partner, day);
				return `<tr><td><b>${this.head_date(day)}</b></td><td>${this.e(nm(v.employee))}: ${this.chip(a)} → ${this.chip(b)}</td><td>${this.e(nm(v.partner))}: ${this.chip(b)} → ${this.chip(a)}</td></tr>`;
			};
			dlg.fields_dict.preview.$wrapper.html(`<table class="sr-preview">${line(v.date)}${v.return_date ? line(v.return_date) : ""}</table>`);
		};
		["date", "return_date", "employee", "partner"].forEach((fn) => (dlg.fields_dict[fn].df.onchange = preview));
		dlg.show();
		const preset = ctx.is_hr ? this.filters().employee || ctx.employee : ctx.employee;
		if (preset) dlg.set_value("employee", preset);
	}

	swap_action(ym, id, act) {
		const done = (msg) => () => { frappe.show_alert({ message: msg, indicator: "green" }); this.refresh(); };
		if (act === "accept") return this.call("respond_swap", { ym, swap_id: id, accept: 1 }).then(done(__("Accepted. Waiting for HR approval.")));
		if (act === "decline") return frappe.confirm(__("Decline this swap request?"), () => this.call("respond_swap", { ym, swap_id: id, accept: 0 }).then(done(__("Declined."))));
		if (act === "approve") return frappe.confirm(__("Approve this swap? The schedule will be updated."), () => this.call("decide_swap", { ym, swap_id: id, approve: 1 }).then(done(__("Approved. The schedule has been updated."))));
		if (act === "reject")
			return frappe.prompt({ fieldname: "remarks", fieldtype: "Small Text", label: __("Reason for rejecting") },
				(v) => this.call("decide_swap", { ym, swap_id: id, approve: 0, remarks: v.remarks }).then(done(__("Rejected."))), __("Reject Swap"), __("Reject"));
		if (act === "cancel") return frappe.confirm(__("Cancel this swap?"), () => this.call("cancel_swap", { ym, swap_id: id }).then(done(__("Cancelled."))));
	}

	// ---------------------------------------------------------- history
	load_history() {
		this.call("get_history", { period: this.hist_period, ...this.filters() }).then((h) => {
			const opts = [["all", __("All time")], ["3m", __("Last 3 months")], ...h.years.map((y) => [y, __("Year {0}", [y])]), ...h.months.map((m) => [m, this.month_label(m)])];
			let html = `<div class="sr-toolbar"><select class="form-control input-sm sr-hist" aria-label="${__("Period")}">${opts.map(([v, l]) => `<option value="${v}" ${v === this.hist_period ? "selected" : ""}>${l}</option>`).join("")}</select>
				<span class="sr-grow"></span><button class="btn btn-default btn-sm" data-act="hist-csv">${__("Export CSV")}</button></div>`;
			if (!h.rows.length) {
				html += `<div class="sr-empty"><h4>${__("The log is empty for this period")}</h4><p>${__("As each Saturday passes, who worked and who was off is kept here.")}</p></div>`;
			} else {
				html += `<div class="frappe-card sr-card"><h5>${this.e(this.scope_label())} — ${__("{0} Saturdays that have passed in this period", [h.saturdays])}</h5><div class="sr-scroll"><table class="table table-bordered sr-hist-table">
					<thead><tr><th>SR #</th><th>${__("Employee")}</th>${SR_CODES.map((x) => `<th class="text-center">${x.label}</th>`).join("")}<th class="text-center">${__("Swaps")}</th></tr></thead><tbody>
					${h.rows.map((r) => `<tr><td>${this.e(r.sr)}</td><td>${this.e(r.name)}</td>${SR_CODES.map((x) => `<td class="text-center">${r[x.c] ? `<span class="sr-chip sr-st-${x.c}">${r[x.c]}</span>` : ""}</td>`).join("")}<td class="text-center">${r.swaps || ""}</td></tr>`).join("")}
					</tbody></table></div></div>`;
			}
			this.history = h;
			this.$root.find(".sr-history").html(html);
		});
	}

	// ---------------------------------------------------------- dialogs
	heading_dialog() {
		if (!this.d?.ctx.is_hr) return frappe.msgprint(__("Only HR can edit the heading."));
		const company = this.filters().company;
		const h = this.d.heading || { title: "", subtitle: "", footer: "" };
		const dlg = new frappe.ui.Dialog({
			title: company ? __("Sheet Heading for {0}", [company]) : __("Sheet Heading for All Companies"),
			fields: [
				{ fieldtype: "HTML", options: `<p class="text-muted">${__("Leave Title empty to use the company name.")}</p>` },
				{ fieldname: "title", fieldtype: "Data", label: __("Title"), default: h.custom ? h.title : "", placeholder: h.title },
				{ fieldname: "subtitle", fieldtype: "Data", label: __("Subtitle"), default: h.subtitle },
				{ fieldname: "footer", fieldtype: "Data", label: __("Footer"), default: h.footer },
			],
			primary_action_label: __("Save"),
			primary_action: (v) =>
				this.call("save_heading", { company, ...v }).then(() => {
					dlg.hide();
					frappe.show_alert({ message: __("Heading saved."), indicator: "green" });
					this.refresh();
				}),
		});
		dlg.show();
	}

	settings_dialog() {
		if (!this.d?.ctx.is_hr) return frappe.msgprint(__("Only HR can change settings."));
		const s = this.d.settings;
		const dlg = new frappe.ui.Dialog({
			title: __("Saturday Schedule Settings"),
			fields: [
				{ fieldname: "subtitle", fieldtype: "Data", label: __("Default Subtitle"), default: s.subtitle },
				{ fieldname: "footer", fieldtype: "Data", label: __("Default Footer"), default: s.footer },
				{ fieldname: "cutoff_hours", fieldtype: "Int", label: __("Employees must request swaps at least (hours before the Saturday)"), default: s.cutoff_hours },
			],
			primary_action_label: __("Save"),
			primary_action: (v) => this.call("save_settings", v).then(() => { dlg.hide(); this.refresh(); }),
		});
		dlg.show();
	}

	import_dialog() {
		if (!this.d?.ctx.is_hr) return frappe.msgprint(__("Only HR can import schedules."));
		const f = this.filters();
		const scope = this.e(this.scope_label());
		let checked = null; // result of the last successful check
		let imported = false;

		const dlg = new frappe.ui.Dialog({
			title: __("Import Saturday Schedule from Excel"),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "steps",
					options: `<div class="sr-import-steps">
						<div class="sr-step"><span>1</span><div><b>${__("Download the template")}</b>
							<p>${__("For {0}, {1}. It already has the current schedule, a dropdown in every cell and the same colours.", [this.month_label(this.ym), scope])}</p>
							<button class="btn btn-default btn-sm" data-template>${frappe.utils.icon("download", "xs")} ${__("Download Template")}</button></div></div>
						<div class="sr-step"><span>2</span><div><b>${__("Fill it in and save")}</b>
							<p>${__("Pick Yes, No, Vacation, OT, WFH, PH, Yes* or Clear from each cell’s dropdown. Empty cells stay as they are. Past Saturdays are ignored.")}</p>
							<p>${__("Avoid Find & Replace. If you use it, select only the Saturday cells and tick “Match entire cell contents”.")}</p></div></div>
						<div class="sr-step"><span>3</span><div><b>${__("Upload, check, then import")}</b>
							<p>${__("Nothing is saved until you click Import.")}</p></div></div>
					</div>`,
				},
				{
					fieldtype: "Attach",
					fieldname: "file",
					label: __("Excel File (.xlsx)"),
					reqd: 1,
					options: { restrictions: { allowed_file_types: [".xlsx"] } },
					onchange: () => {
						checked = null;
						dlg.fields_dict.result.$wrapper.html("");
						dlg.set_primary_action(__("Check File"), check);
					},
				},
				{ fieldtype: "HTML", fieldname: "result" },
			],
		});

		const show = (r) => {
			const errs = r.error_count
				? `<div class="sr-imp-err"><b>${__("{0} problems found. Fix them in the file and upload it again.", [r.error_count])}</b>
					<ul>${r.errors.map((x) => `<li>${this.e(x)}</li>`).join("")}${r.error_count > r.errors.length ? `<li>…</li>` : ""}</ul></div>`
				: "";
			const other = r.ym !== this.ym ? `<p class="text-muted">${__("This file is for {0}.", [this.month_label(r.ym)])}</p>` : "";
			const moves = (r.transitions || []).map(([m, n]) => `<tr><td>${this.e(m)}</td><td class="text-right"><b>${n}</b></td></tr>`).join("");
			const big = r.cells && r.changes / r.cells > 0.4;
			const ok = !r.error_count
				? `<div class="sr-imp-ok ${big ? "sr-imp-big" : ""}"><b>${r.changes ? __("Ready to import {0} changes for {1} employees.", [r.changes, r.employees]) : __("No changes found in this file.")}</b>
					<p>${__("{0} rows read · {1} cells already the same", [r.rows, r.unchanged])}${r.skipped_past ? " · " + __("{0} cells on past Saturdays ignored", [r.skipped_past]) : ""}</p>
					${moves ? `<table class="sr-moves"><thead><tr><th>${__("Change")}</th><th class="text-right">${__("Cells")}</th></tr></thead><tbody>${moves}</tbody></table>` : ""}
					${big ? `<p class="sr-imp-warn">${__("This changes {0}% of the cells. If you used Find & Replace in Excel, check that only the cells you meant were changed before importing.", [Math.round((r.changes / r.cells) * 100)])}</p>` : ""}</div>`
				: "";
			dlg.fields_dict.result.$wrapper.html(other + errs + ok);
		};

		const check = () => {
			const file_url = dlg.get_value("file");
			if (!file_url) return frappe.msgprint(__("Upload the Excel file first."));
			this.call("import_xlsx", { file_url, company: f.company, dry_run: 1 }).then((r) => {
				show(r);
				if (!r.error_count && r.changes) {
					checked = { file_url, ym: r.ym };
					dlg.set_primary_action(__("Import {0} Changes", [r.changes]), run);
				}
			});
		};

		const run = () => {
			if (!checked) return check();
			this.call("import_xlsx", { file_url: checked.file_url, company: f.company, dry_run: 0 }).then((r) => {
				imported = true;
				dlg.hide();
				this.ym = r.ym;
				this.view = "schedule";
				this.reset_bulk();
				this.flash = new Set(r.changed_cells);
				this.refresh().then(() => {
					frappe.show_alert({ message: __("Imported {0} changes. Updated cells are highlighted.", [r.changes]), indicator: "green" }, 6);
					clearTimeout(this._flash_t);
					this._flash_t = setTimeout(() => {
						this.flash = null;
						this.$root.find(".sr-flash").removeClass("sr-flash");
					}, 8000);
				});
			});
		};

		dlg.set_primary_action(__("Check File"), check);
		dlg.$wrapper.on("click", "[data-template]", () => {
			const params = new URLSearchParams({ ym: this.ym, ...f });
			window.open(`/api/method/${SR_API}.download_template?${params.toString()}`, "_blank");
		});
		dlg.onhide = () => {
			const file_url = dlg.get_value("file");
			if (file_url && !imported) this.call("discard_upload", { file_url }).catch(() => {});
		};
		dlg.show();
	}

	// Print only the sheet, in a hidden frame, so desk buttons and floating icons never appear
	print_sheet() {
		if (this.view !== "schedule") {
			this.view = "schedule";
			this.render();
		}
		const $sheet = this.$root.find(".sr-sheet");
		if (!$sheet.length) return frappe.msgprint(__("There is no schedule to print for this month."));

		const $copy = $sheet.clone();
		$copy.find(".sr-chk, .sr-sw").remove();
		$copy.find(".sr-cell select").each(function () {
			const text = $(this).find("option:selected").text() || "—";
			$(this).replaceWith($("<span>").text(text));
		});
		const title = `${this.d.heading?.title || ""} - ${this.month_label(this.ym)}`;
		const html = `<!doctype html><html><head><meta charset="utf-8"><title>${frappe.utils.escape_html(title)}</title>
			<style>
				:root { --fg-color:#fff; --text-color:#1f272e; --text-muted:#6b7280; --border-color:#d1d8dd; --control-bg:#f4f5f6; }
				@page { size: A4 portrait; margin: 8mm; }
				html, body { margin: 0; background: #fff; }
				* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
				${SR_CSS}
				.sr-root { max-width: none; margin: 0; padding: 0; }
				.sr-sheet { box-shadow: none !important; border-radius: 0 !important; font-size: 11px; }
				.sr-table thead th.past::after { content: ""; }
				.sr-cell { min-width: 0; }
				.sr-table thead { display: table-header-group; }
				.sr-table tr { page-break-inside: avoid; }
				.sr-legend-wrap { page-break-inside: avoid; }
			</style></head>
			<body><div class="sr-root">${$copy.prop("outerHTML")}</div></body></html>`;

		const frame = document.createElement("iframe");
		frame.setAttribute("aria-hidden", "true");
		Object.assign(frame.style, { position: "fixed", right: "0", bottom: "0", width: "0", height: "0", border: "0" });
		document.body.appendChild(frame);
		const doc = frame.contentWindow.document;
		doc.open();
		doc.write(html);
		doc.close();
		setTimeout(() => {
			frame.contentWindow.focus();
			frame.contentWindow.print();
			setTimeout(() => frame.remove(), 2000);
		}, 400);
	}

	export_xlsx() {
		if (!this.d?.month) return frappe.msgprint(__("There is no schedule for this month yet."));
		const params = new URLSearchParams({ ym: this.ym, ...this.filters() });
		window.open(`/api/method/${SR_API}.export_xlsx?${params.toString()}`, "_blank");
	}

	export_csv() {
		const tag = (this.filters().company || "all").replace(/[^\w-]+/g, "-");
		if (this.view === "history" && this.history) {
			const rows = [["SR #", "Employee", ...SR_CODES.map((x) => x.label), "Swaps"]];
			this.history.rows.forEach((r) => rows.push([r.sr, r.name, ...SR_CODES.map((x) => r[x.c] || 0), r.swaps || 0]));
			return frappe.tools.downloadify(rows, null, `saturday-history-${tag}-${this.hist_period}`);
		}
		if (!this.d?.month) return frappe.msgprint(__("Nothing to export for this month."));
		const rows = [[this.d.heading?.title || ""], ["SR #", "Employee Name", ...this.d.saturdays.map((x) => this.head_date(x))]];
		this.d.rows.forEach((r) => rows.push([r.sr, r.name, ...this.d.saturdays.map((x) => this.code(this.status_of(r.id, x))?.label || "")]));
		frappe.tools.downloadify(rows, null, `saturday-off-${tag}-${this.ym}`);
	}

	// ---------------------------------------------------------- events
	bind_events() {
		const $r = this.$root;
		$r.on("click", ".sr-tab", (e) => {
			this.view = $(e.currentTarget).data("view");
			this.render();
			if (this.view === "history") this.load_history();
		});
		$r.on("change", ".sr-month", (e) => { this.ym = e.target.value; this.reset_bulk(); this.refresh(); });
		$r.on("change", ".sr-swap-filter", (e) => { this.swap_filter = e.target.value; this.render(); });
		$r.on("change", ".sr-hist", (e) => { this.hist_period = e.target.value; this.load_history(); });
		$r.on("change", ".sr-cell select", (e) => {
			const el = e.target;
			this.call("set_cell", { ym: this.ym, employee: el.dataset.emp, date: el.dataset.date, code: el.value })
				.then(() => this.refresh(), () => this.refresh());
		});
		// bulk selection: row ticks (Shift+click selects a range), select all, Saturdays, actions
		$r.on("click", ".sr-chk-row", (e) => {
			const boxes = $r.find(".sr-chk-row").toArray();
			const i = boxes.indexOf(e.currentTarget);
			const on = e.currentTarget.checked;
			const range = e.shiftKey && this._last_index != null ? [Math.min(i, this._last_index), Math.max(i, this._last_index)] : [i, i];
			for (let k = range[0]; k <= range[1]; k++) {
				const id = boxes[k].dataset.emp;
				on ? this.selected.add(id) : this.selected.delete(id);
			}
			this._last_index = i;
			this.render();
		});
		$r.on("change", ".sr-chk-all", (e) => {
			(this.d.rows || []).forEach((r) => (e.target.checked ? this.selected.add(r.id) : this.selected.delete(r.id)));
			this.render();
		});
		$r.on("click", "[data-bulk-date]", (e) => {
			const day = e.currentTarget.dataset.bulkDate;
			this.bulk_dates.has(day) ? this.bulk_dates.delete(day) : this.bulk_dates.add(day);
			this.render();
		});
		$r.on("click", "[data-bulk]", (e) => this.apply_bulk(e.currentTarget.dataset.bulk));
		$r.on("change", ".sr-bulk-other", (e) => {
			const v = e.target.value;
			e.target.value = "";
			if (v) this.apply_bulk(v === "CLEAR" ? "" : v);
		});
		$r.on("click", "[data-swap]", (e) => {
			const b = e.currentTarget.dataset;
			this.swap_action(b.ym, b.swap, b.do);
		});
		$r.on("click", "[data-act]", (e) => {
			const act = e.currentTarget.dataset.act;
			const f = this.filters();
			if (act === "prev") { this.ym = this.shift_month(this.ym, -1); this.reset_bulk(); this.refresh(); }
			else if (act === "next") { this.ym = this.shift_month(this.ym, 1); this.reset_bulk(); this.refresh(); }
			else if (act === "heading") this.heading_dialog();
			else if (act === "bulk-clear") { this.selected.clear(); this._last_index = null; this.render(); }
			else if (act === "create")
				this.call("create_month", { ym: this.ym, company: f.company, branch: f.branch }).then((n) => {
					frappe.show_alert({ message: __("{0} employees added to {1}.", [n, this.month_label(this.ym)]), indicator: "green" });
					this.refresh();
				});
			else if (act === "ph") {
				const day = $r.find(".sr-phdate").val();
				frappe.confirm(__("Mark {0} as a public holiday for everyone in {1}?", [this.head_date(day), this.e(this.scope_label())]), () =>
					this.call("mark_public_holiday", { ym: this.ym, date: day, company: f.company, branch: f.branch }).then(() => this.refresh()));
			}
			else if (act === "new-swap") this.swap_dialog();
			else if (act === "hist-csv") this.export_csv();
		});
	}
}