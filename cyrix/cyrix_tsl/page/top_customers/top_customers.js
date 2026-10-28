// Change this to your app/module path

const TC_METHOD = "cyrix.cyrix_tsl.page.top_customers.top_customers"; 
frappe.pages["top-customers"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Top Customers"),
		single_column: true,
	});
	wrapper.top_customers = new TopCustomers(page);
};
 
class TopCustomers {
	constructor(page) {
		this.page = page;
		this.add_styles();
		this.make_filters();
		this.$body = $(`<div class="tc-wrapper"></div>`).appendTo(page.main);
		this.$body.on("click", ".tc-amount-link", (e) => {
			e.preventDefault();
			this.show_breakdown($(e.currentTarget).attr("data-customer"));
		});
		this.refresh();
	}
 
	make_filters() {
		const today = frappe.datetime.now_date(true);
		const current_year = today.getFullYear();
		const current_q = Math.floor(today.getMonth() / 3) + 1;
		const years = [];
		for (let y = current_year; y >= current_year - 5; y--) years.push(String(y));
 
		this.company = this.page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			change: () => this.refresh(),
		});
		this.sales_person = this.page.add_field({
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			change: () => this.refresh(),
		});
		this.year = this.page.add_field({
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			options: years,
			default: String(current_year),
			change: () => this.refresh(),
		});
		this.quarter = this.page.add_field({
			fieldname: "quarter",
			label: __("Quarter"),
			fieldtype: "Select",
			options: ["Q1", "Q2", "Q3", "Q4"],
			default: "Q" + current_q,
			change: () => this.refresh(),
		});
		this.limit = this.page.add_field({
			fieldname: "limit",
			label: __("Top"),
			fieldtype: "Int",
			default: 5,
			change: () => this.refresh(),
		});
 
		this.page.set_primary_action(__("Download PDF"), () => this.download_pdf(), "printer");
		this.page.set_secondary_action(__("Refresh"), () => this.refresh(), "refresh");
	}
 
	get_args() {
		return {
			year: this.year.get_value(),
			quarter: (this.quarter.get_value() || "Q1").replace("Q", ""),
			company: this.company.get_value() || "",
			limit: this.limit.get_value() || 5,
			sales_person: this.sales_person.get_value() || "",
		};
	}
 
	refresh() {
		frappe.call({
			method: `${TC_METHOD}.get_top_customers`,
			args: this.get_args(),
			freeze: true,
			callback: (r) => {
				const data = r.message || {};
				this.render(data);
				if (data.warnings && data.warnings.length) {
					frappe.msgprint({
						title: __("JO / SO counts"),
						message: data.warnings.join("<br>"),
						indicator: "orange",
					});
				}
			},
		});
	}
 
	download_pdf() {
		const url = `/api/method/${TC_METHOD}.download_pdf?` + $.param(this.get_args());
		window.open(frappe.urllib.get_full_url(url));
	}
 
	render(data) {
		const rows = data.rows || [];
		const currency = data.currency;
		const limit = this.limit.get_value() || 5;
		const title = __("Top {0} Customers of {1}", [limit, this.quarter.get_value()]);
		const sp = data.sales_person ? ` · ${frappe.utils.escape_html(data.sales_person)}` : "";
 
		const body = rows.length
			? rows
					.map(
						(r) => `
				<tr>
					<td class="tc-name">
						<a href="/app/customer/${encodeURIComponent(r.customer)}">${frappe.utils.escape_html(r.customer_name)}</a>
					</td>
					<td class="tc-center">${r.jo_received}</td>
					<td class="tc-center">${r.so_received}</td>
					<td class="tc-center tc-amount">
						<a href="#" class="tc-amount-link" data-customer="${frappe.utils.escape_html(r.customer)}"
							title="${__("Show invoice split")}">${format_currency(r.total_invoice, currency, 0)}</a>
					</td>
				</tr>`
					)
					.join("")
			: `<tr><td colspan="4" class="tc-empty">${__(
					"No submitted Sales Invoices in this quarter. Pick another quarter or company."
			  )}</td></tr>`;
 
		this.$body.html(`
			<h2 class="tc-title">${title}
				<small>${frappe.datetime.str_to_user(data.from_date)} – ${frappe.datetime.str_to_user(data.to_date)}${sp}</small>
			</h2>
			<div class="tc-table-wrap">
				<table class="tc-table">
					<thead>
						<tr>
							<th>${__("Customer Name")}</th>
							<th>${__("JO Received")}</th>
							<th>${__("SO Received")}</th>
							<th>${__("Total Invoice")}</th>
						</tr>
					</thead>
					<tbody>${body}</tbody>
				</table>
			</div>
		`);
	}
 
	show_breakdown(customer) {
		frappe.call({
			method: `${TC_METHOD}.get_invoice_breakdown`,
			args: { customer, ...this.get_args() },
			freeze: true,
			callback: (r) => {
				const d = r.message;
				if (!d) return;
				const cur = d.currency;
				const esc = frappe.utils.escape_html;
 
				const months = d.months
					.map(
						(m) => `
					<div class="tc-month">
						<div class="tc-month-name">${__(m.month)}</div>
						<div class="tc-month-amt">${format_currency(m.amount, cur, 0)}</div>
						<div class="tc-month-count">${__("{0} invoices", [m.count])}</div>
					</div>`
					)
					.join("");
 
				const colors = {
					Paid: "green", Overdue: "red", Unpaid: "orange", "Partly Paid": "yellow",
					Return: "gray", "Credit Note Issued": "gray",
				};
				const rows = d.invoices.length
					? d.invoices
							.map(
								(inv) => `
					<tr>
						<td><a href="/app/sales-invoice/${encodeURIComponent(inv.name)}" target="_blank">${esc(inv.name)}</a></td>
						<td>${frappe.datetime.str_to_user(inv.posting_date)}</td>
						<td><span class="indicator-pill ${colors[inv.status] || "blue"}">${__(inv.status)}</span></td>
						<td class="text-right">${format_currency(inv.base_grand_total, cur, 0)}</td>
					</tr>`
							)
							.join("")
					: `<tr><td colspan="4" class="text-muted text-center">${__("No invoices")}</td></tr>`;
 
				const dialog = new frappe.ui.Dialog({
					title: __("Invoice split for {0}", [esc(d.customer_name)]),
					size: "large",
					fields: [{ fieldtype: "HTML", fieldname: "body" }],
				});
				dialog.fields_dict.body.$wrapper.html(`
					<div class="tc-split-sub">${frappe.datetime.str_to_user(d.from_date)} – ${frappe.datetime.str_to_user(d.to_date)}</div>
					<div class="tc-months">${months}</div>
					<div class="tc-table-wrap" style="border-width:1px">
						<table class="table table-bordered tc-split-table" style="margin:0">
							<thead><tr>
								<th>${__("Invoice")}</th><th>${__("Date")}</th>
								<th>${__("Status")}</th><th class="text-right">${__("Amount")}</th>
							</tr></thead>
							<tbody>${rows}</tbody>
							<tfoot><tr>
								<th colspan="3">${__("Total")}</th>
								<th class="text-right">${format_currency(d.total, cur, 0)}</th>
							</tr></tfoot>
						</table>
					</div>
				`);
				dialog.show();
			},
		});
	}
 
	add_styles() {
		frappe.dom.set_style(`
			.tc-wrapper { padding: 16px 0; }
			.tc-title { color: #0b4f9c; font-weight: 700; font-size: 28px; margin: 0 0 12px; }
			.tc-title small { font-size: 13px; font-weight: 400; color: var(--text-muted); margin-left: 8px; }
			.tc-table-wrap { overflow-x: auto; border: 2px solid #555; }
			.tc-table { width: 100%; border-collapse: collapse; background: #f7f8fa; }
			.tc-table thead th {
				background: #0b4f9c; color: #fff; font-weight: 700; font-size: 18px;
				text-align: center; padding: 22px 12px;
			}
			.tc-table tbody td { padding: 22px 12px; font-size: 16px; color: #333; }
			.tc-table tbody td.tc-name a { font-weight: 700; color: #333; }
			.tc-table tbody td.tc-name a:hover { color: #0b4f9c; }
			.tc-center { text-align: center; }
			.tc-amount { font-weight: 700; }
			.tc-empty { text-align: center; color: var(--text-muted); }
			.tc-amount-link { color: #0b4f9c; font-weight: 700; text-decoration: underline dotted; }
			.tc-amount-link:hover { color: #083a73; }
			.tc-split-sub { color: var(--text-muted); margin-bottom: 12px; }
			.tc-months { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
			.tc-month { border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 12px; }
			.tc-month-name { color: var(--text-muted); font-size: 12px; }
			.tc-month-amt { font-weight: 700; font-size: 16px; color: #0b4f9c; }
			.tc-month-count { color: var(--text-muted); font-size: 11px; }
			.tc-split-table thead th { background: #0b4f9c; color: #fff; }
			@media (max-width: 576px) { .tc-months { grid-template-columns: 1fr; } }
		`);
	}
}
 