# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, flt, formatdate, getdate

# ---------------------------------------------------------------------------
# CONFIG - matched against Account.account_name (exact, case-insensitive)
# ---------------------------------------------------------------------------
SECTION_PARENTS = {
	"trading_income": {"names": ["Direct Income"], "root_type": "Income"},
	"cost_of_sales": {"names": ["Direct Expenses"], "root_type": "Expense"},
	"other_income": {"names": ["Indirect Income"], "root_type": "Income"},
	"operating_expenses": {"names": ["Indirect Expenses", "Expenses"], "root_type": "Expense"},
}

GROUPED_SECTIONS = {"operating_expenses"}

PERIODICITY_MONTHS = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}
MAX_COLUMNS = 60


def execute(filters=None):
	filters = frappe._dict(filters or {})
	resolve_dates(filters)
	validate_filters(filters)

	column_periods, groups, single_branch = build_column_periods(filters)
	filters._single_branch = single_branch  # applied as plain filter
	columns = get_columns(filters, column_periods, groups)
	data, messages = get_data(filters, column_periods, groups)

	if filters.get("debug") and messages:
		frappe.msgprint("<br>".join(messages), title=_("P&L Debug"), indicator="blue")

	return columns, data


# ---------------------------------------------------------------------------
# Dates & filters
# ---------------------------------------------------------------------------
def resolve_dates(filters):
	if filters.get("filter_based_on") == "Date Range":
		filters.from_date = filters.get("period_start_date")
		filters.to_date = filters.get("period_end_date")
	else:
		from_fy = filters.get("from_fiscal_year")
		to_fy = filters.get("to_fiscal_year") or from_fy
		if from_fy:
			filters.from_date = frappe.db.get_value("Fiscal Year", from_fy, "year_start_date")
		if to_fy:
			filters.to_date = frappe.db.get_value("Fiscal Year", to_fy, "year_end_date")


def validate_filters(filters):
	if not filters.company:
		frappe.throw(_("Company is mandatory"))
	if not filters.from_date or not filters.to_date:
		frappe.throw(_("Please set a Fiscal Year range or a Date Range"))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("Start date cannot be after end date"))

	comp_years = parse_multiselect(filters.get("comparison_years"))
	branches = parse_multiselect(filters.get("branches"))
	consolidate = parse_multiselect(filters.get("consolidate_companies"))
	active_modes = sum([bool(comp_years), len(branches) > 1, bool(consolidate)])
	if active_modes > 1:
		frappe.throw(
			_("Please use one comparison at a time: Compare With Years, "
				"multiple Branches, or Consolidate With Companies.")
		)


def parse_multiselect(value):
	if not value:
		return []
	if isinstance(value, str):
		try:
			value = frappe.parse_json(value)
		except Exception:
			value = [value]
	if isinstance(value, str):
		value = [value]
	return [v for v in value if v]


def get_companies(filters):
	"""[(company, default_currency)] - primary company first, then any
	companies selected for consolidation."""
	companies = [filters.company]
	for c in parse_multiselect(filters.get("consolidate_companies")):
		if c and c not in companies:
			companies.append(c)
	return [
		(c, frappe.get_cached_value("Company", c, "default_currency"))
		for c in companies
	]


def get_report_currency(filters):
	"""Presentation currency if selected, else company currency."""
	company_currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	return filters.get("presentation_currency") or company_currency, company_currency


def get_exchange_rate_safe(from_currency, to_currency, date):
	if from_currency == to_currency:
		return 1.0
	try:
		from erpnext.setup.utils import get_exchange_rate
		rate = flt(get_exchange_rate(from_currency, to_currency, str(date)))
		return rate or 1.0
	except Exception:
		return 1.0


def get_extra_dimensions():
	"""Active Accounting Dimensions on GL Entry as {fieldname: label},
	excluding the ones this report already handles explicitly."""
	handled = {"cost_center", "project", "department", "branch"}
	dims = {}
	try:
		for d in frappe.get_all(
			"Accounting Dimension",
			filters={"disabled": 0},
			fields=["fieldname", "label"],
		):
			if d.fieldname and d.fieldname not in handled:
				dims[d.fieldname] = d.label or d.fieldname
	except Exception:
		pass
	return dims


def get_base_fiscal_year_start(filters):
	fy_start = frappe.db.get_value(
		"Fiscal Year",
		{
			"year_start_date": ["<=", filters.from_date],
			"year_end_date": [">=", filters.from_date],
		},
		"year_start_date",
	)
	return getdate(fy_start) if fy_start else getdate(filters.from_date)


# ---------------------------------------------------------------------------
# Comparison groups & column periods
# ---------------------------------------------------------------------------
def get_comparison_groups(filters):
	"""Returns (groups, single_branch).

	Each group: {suffix, label, offset_months, branch}
	  - Year comparison: base group + one group per comparison year (offset).
	  - Branch comparison (2+ branches): one group per branch (offset 0).
	  - Neither: a single base group.
	single_branch: branch name to apply as a plain filter (1 branch selected).
	"""
	branches = parse_multiselect(filters.get("branches"))
	comp_years = parse_multiselect(filters.get("comparison_years"))
	consolidate = parse_multiselect(filters.get("consolidate_companies"))

	# --- company consolidation mode: one column-group per company ---
	if consolidate:
		groups = []
		for i, (comp, _cur) in enumerate(get_companies(filters)):
			abbr = frappe.get_cached_value("Company", comp, "abbr") or comp
			groups.append({
				"suffix": f"c{i}",
				"label": abbr,
				"offset_months": 0,
				"branch": None,
				"company": comp,
			})
		return groups, None

	# --- branch comparison mode ---
	if len(branches) > 1:
		groups = []
		for i, br in enumerate(branches):
			groups.append({
				"suffix": f"b{i}",
				"label": br,
				"offset_months": 0,
				"branch": br,
			})
		return groups, None

	single_branch = branches[0] if branches else None

	# --- year comparison mode ---
	base_start = get_base_fiscal_year_start(filters)
	groups = [{
		"suffix": "y0",
		"label": str(base_start.year),
		"offset_months": 0,
		"branch": None,
	}]
	offsets = []
	for fy in comp_years:
		fy_start = frappe.db.get_value("Fiscal Year", fy, "year_start_date")
		if not fy_start:
			continue
		year_diff = base_start.year - getdate(fy_start).year
		if year_diff == 0:
			continue
		offsets.append((year_diff * 12, fy))
	offsets.sort(key=lambda x: x[0])  # most recent first
	for i, (offset, fy) in enumerate(offsets, start=1):
		groups.append({
			"suffix": f"y{i}",
			"label": fy,
			"offset_months": offset,
			"branch": None,
		})

	return groups, single_branch


def build_base_periods(filters):
	periodicity = filters.get("periodicity") or "Monthly"
	start = getdate(filters.from_date)
	end = getdate(filters.to_date)

	periods = []
	cursor = start
	while cursor <= end and len(periods) <= MAX_COLUMNS:
		if periodicity == "Weekly":
			p_end = min(add_days(cursor, 6), end)
		else:
			months = PERIODICITY_MONTHS.get(periodicity, 1)
			p_end = min(add_days(add_months(cursor, months), -1), end)
		periods.append({"from_date": cursor, "to_date": p_end})
		cursor = add_days(p_end, 1)

	return periods


def build_column_periods(filters):
	"""(column_periods, groups, single_branch)

	column_periods: interleaved per base period:
	  P1-group1, P1-group2, ..., P2-group1, P2-group2, ...
	Each: {key, label, from_date, to_date, group (suffix), branch}
	"""
	periodicity = filters.get("periodicity") or "Monthly"
	base_periods = build_base_periods(filters)
	groups, single_branch = get_comparison_groups(filters)
	branch_mode = any(g.get("branch") for g in groups)
	company_mode = any(g.get("company") for g in groups)

	column_periods = []
	for p_idx, p in enumerate(base_periods):
		for g in groups:
			if g["offset_months"]:
				c_start = add_months(p["from_date"], -g["offset_months"])
				c_end = add_months(p["to_date"], -g["offset_months"])
				if is_month_end(p["to_date"]):
					c_end = get_month_end(c_end)
			else:
				c_start, c_end = p["from_date"], p["to_date"]

			label = period_label(c_start, c_end, periodicity)
			if branch_mode or company_mode:
				label = f"{label}-{short_label(g['label'])}"

			column_periods.append({
				"key": f"p{p_idx}_{g['suffix']}",
				"label": label,
				"from_date": c_start,
				"to_date": c_end,
				"group": g["suffix"],
				"branch": g.get("branch"),
				"company": g.get("company"),
			})

	total_cols = len(column_periods)
	if len(base_periods) > 1:
		total_cols += len(groups)
	if company_mode:
		total_cols += 1  # Consolidated Total column
	if filters.get("show_growth") and not branch_mode and not company_mode:
		if len(groups) > 1:
			total_cols += len(base_periods) * (len(groups) - 1)
			if len(base_periods) > 1:
				total_cols += len(groups) - 1
		else:
			total_cols += max(len(base_periods) - 1, 0)

	if total_cols > MAX_COLUMNS:
		frappe.throw(
			_("This selection produces {0} columns (max {1}). "
				"Choose a shorter range, larger periodicity, or fewer comparison items.").format(
				total_cols, MAX_COLUMNS
			)
		)

	return column_periods, groups, single_branch


def short_label(text, length=14):
	text = (text or "").split(" - ")[0]  # drop company abbreviation suffix
	return text if len(text) <= length else text[: length - 1] + "…"


def is_month_end(d):
	return add_days(d, 1).day == 1


def get_month_end(d):
	first_next = add_months(getdate(f"{d.year}-{d.month:02d}-01"), 1)
	return add_days(first_next, -1)


def period_label(start, end, periodicity):
	if periodicity == "Weekly":
		return f"{formatdate(start, 'dd MMM')}-{formatdate(end, 'dd MMM yy')}"
	if periodicity == "Monthly":
		return formatdate(start, "MMM yy")
	if periodicity == "Quarterly":
		quarter = (start.month - 1) // 3 + 1
		return f"Q{quarter} {formatdate(start, 'yy')}" if start.year == end.year \
			else f"{formatdate(start, 'MMM yy')}-{formatdate(end, 'MMM yy')}"
	if periodicity == "Half-Yearly":
		return f"{formatdate(start, 'MMM yy')}-{formatdate(end, 'MMM yy')}"
	if start.year == end.year:
		return str(start.year)
	return f"{start.year}-{str(end.year)[-2:]}"


# ---------------------------------------------------------------------------
# Growth (year-comparison / sequential modes only)
# ---------------------------------------------------------------------------
def build_growth_defs(filters, column_periods, groups, show_totals):
	if not filters.get("show_growth"):
		return []
	defs = []
	if any(g.get("branch") for g in groups) or any(g.get("company") for g in groups):
		return []  # growth not applicable in branch/company comparison modes
	comp_labels = {cp["key"]: cp["label"] for cp in column_periods}
	base_period_keys = sorted(
		{cp["key"].split("_")[0] for cp in column_periods},
		key=lambda k: int(k[1:]),
	)

	if len(groups) > 1:
		for pk in base_period_keys:
			for g in groups[1:]:
				ref = f"{pk}_{g['suffix']}"
				defs.append((
					f"growth_{ref}",
					f"{pk}_y0",
					ref,
					_("% vs {0}").format(comp_labels.get(ref, g["label"])),
				))
		if show_totals:
			for g in groups[1:]:
				defs.append((
					f"growth_total_{g['suffix']}",
					"total_y0",
					f"total_{g['suffix']}",
					_("% vs Total {0}").format(g["label"]),
				))
	else:
		for prev, cur in zip(base_period_keys, base_period_keys[1:]):
			defs.append((f"growth_{cur}", f"{cur}_y0", f"{prev}_y0", _("% Δ")))
	return defs


def compute_growth(row_amounts, growth_defs):
	"""(current - comparison) / |comparison| * 100, rounded to whole number.
	Positive = current year is higher."""
	for gkey, base_key, ref_key, _label in growth_defs:
		base = row_amounts.get(base_key)
		ref = row_amounts.get(ref_key)
		if base is None or ref is None or not ref:
			row_amounts[gkey] = None
		else:
			row_amounts[gkey] = flt(round((flt(base) - flt(ref)) / abs(flt(ref)) * 100), 0)
	return row_amounts


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------
def get_columns(filters, column_periods, groups):
	currency, _company_currency = get_report_currency(filters)

	n_base_periods = len({cp["key"].split("_")[0] for cp in column_periods})
	show_totals = n_base_periods > 1
	growth_defs = build_growth_defs(filters, column_periods, groups, show_totals)
	growth_after = {}
	for gkey, base_key, ref_key, label in growth_defs:
		anchor = ref_key if len(groups) > 1 else base_key
		growth_after.setdefault(anchor, []).append((gkey, label))

	def growth_col(gkey, label):
		return {"fieldname": gkey, "label": label, "fieldtype": "Percent", "width": 100}

	columns = [
		{"fieldname": "account_label", "label": _("Account"), "fieldtype": "Data", "width": 360},
	]
	for cp in column_periods:
		columns.append({
			"fieldname": cp["key"],
			"label": cp["label"],
			"fieldtype": "Currency",
			"options": "currency",
			"width": 140,
		})
		for gkey, label in growth_after.get(cp["key"], []):
			columns.append(growth_col(gkey, label))

	if show_totals:
		for g in groups:
			tkey = f"total_{g['suffix']}"
			columns.append({
				"fieldname": tkey,
				"label": _("Total {0}").format(short_label(g["label"])),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			})
			for gkey, label in growth_after.get(tkey, []):
				columns.append(growth_col(gkey, label))

	if any(g.get("company") for g in groups):
		columns.append({
			"fieldname": "grand_total",
			"label": _("Consolidated Total"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 160,
		})

	columns.append({"fieldname": "currency", "label": _("Currency"), "fieldtype": "Link",
		"options": "Currency", "hidden": 1})
	return columns


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------
def get_data(filters, column_periods, groups):
	currency, company_currency = get_report_currency(filters)
	messages = []

	companies = get_companies(filters)

	# exchange rate per column per company (company currency -> report
	# currency, taken at each column period's end date)
	rates = {}
	for cp in column_periods:
		for comp, comp_currency in companies:
			rates[(cp["key"], comp)] = get_exchange_rate_safe(
				comp_currency, currency, cp["to_date"]
			)
	if len(companies) > 1:
		messages.append(
			_("Consolidating companies: {0}. Amounts presented in {1}.").format(
				", ".join(frappe.bold(c) for c, _cur in companies), frappe.bold(currency)
			)
		)
	elif currency != company_currency:
		messages.append(
			_("Amounts converted from {0} to {1} using exchange rates at each "
				"period's end date.").format(frappe.bold(company_currency), frappe.bold(currency))
		)

	col_keys = [cp["key"] for cp in column_periods]
	n_base_periods = len({k.split("_")[0] for k in col_keys})
	show_totals = n_base_periods > 1
	company_mode = any(cp.get("company") for cp in column_periods)
	total_keys = [f"total_{g['suffix']}" for g in groups] if show_totals else []
	if company_mode:
		total_keys = total_keys + ["grand_total"]
	all_keys = col_keys + total_keys
	growth_defs = build_growth_defs(filters, column_periods, groups, show_totals)
	growth_keys = [g[0] for g in growth_defs]

	keys_by_group = {g["suffix"]: [] for g in groups}
	for cp in column_periods:
		keys_by_group[cp["group"]].append(cp["key"])

	sections = classify_accounts(filters, messages)

	# member account names per company (Account.name is unique per company)
	accounts_by_company = {c: [] for c, _cur in companies}
	member_company = {}
	for sec in sections.values():
		for meta in sec.values():
			for m in meta["members"]:
				accounts_by_company[m["company"]].append(m["name"])
				member_company[m["name"]] = m["company"]
	all_accounts = [n for names in accounts_by_company.values() for n in names]

	balances = {}
	any_entries = False
	for cp in column_periods:
		merged = {}
		for comp, _cur in companies:
			if cp.get("company") and comp != cp["company"]:
				continue
			merged.update(
				get_gl_balances(
					filters, accounts_by_company[comp], cp["from_date"], cp["to_date"],
					branch=cp["branch"], company=comp,
				)
			)
		balances[cp["key"]] = merged
		if merged:
			any_entries = True

	if not any_entries:
		messages.append(_("No GL Entries found for any of the selected periods."))
	else:
		total_debit = sum(
			d for period in balances.values() for d, c in period.values()
		)
		total_credit = sum(
			c for period in balances.values() for d, c in period.values()
		)
		messages.append(
			_("Raw GL totals fetched — Debit: {0}, Credit: {1}").format(
				frappe.bold(flt(total_debit, 3)), frappe.bold(flt(total_credit, 3))
			)
		)

	# ---- Deep diagnostics (Debug mode): find where the chain breaks ----
	if filters.get("debug"):
		messages.append("<hr><b>--- Diagnostics (v10) ---</b>")

		r = frappe.db.sql(
			"""select count(*) cnt, ifnull(sum(debit),0) dr, ifnull(sum(credit),0) cr
			from `tabGL Entry` where company = %(c)s""",
			{"c": filters.company}, as_dict=True,
		)[0]
		messages.append(
			f"1. GL Entries for company '{filters.company}' (all time): "
			f"count={r.cnt}, debit={flt(r.dr,2)}, credit={flt(r.cr,2)}"
		)

		r = frappe.db.sql(
			"""select count(*) cnt, ifnull(sum(debit),0) dr, ifnull(sum(credit),0) cr,
				min(posting_date) mn, max(posting_date) mx
			from `tabGL Entry`
			where company = %(c)s and posting_date between %(f)s and %(t)s""",
			{"c": filters.company, "f": str(filters.from_date), "t": str(filters.to_date)},
			as_dict=True,
		)[0]
		messages.append(
			f"2. In range {filters.from_date} → {filters.to_date}: count={r.cnt}, "
			f"debit={flt(r.dr,2)}, credit={flt(r.cr,2)} "
			f"(entry dates found: {r.mn} → {r.mx})"
		)

		gl_accounts = frappe.db.sql(
			"""select distinct account from `tabGL Entry`
			where company = %(c)s and posting_date between %(f)s and %(t)s limit 8""",
			{"c": filters.company, "f": str(filters.from_date), "t": str(filters.to_date)},
			pluck="account",
		)
		messages.append(f"3. Sample GL accounts in range: {gl_accounts or 'NONE'}")

		sample_classified = all_accounts[:8]
		messages.append(f"4. Sample classified accounts: {sample_classified or 'NONE'}")

		overlap = set(gl_accounts or []) & set(all_accounts)
		messages.append(f"5. Overlap between (3) and (4): {list(overlap) or 'NONE ← problem is here'}")

	# Debug: show which accounting-dimension filters arrived and were applied
	extra_dims = get_extra_dimensions()
	if extra_dims:
		applied = []
		for dim, nice_name in extra_dims.items():
			values = parse_multiselect(filters.get(dim))
			if values:
				has_col = frappe.db.has_column("GL Entry", dim)
				applied.append(
					f"{nice_name} ({dim}) = {', '.join(values)}"
					+ ("" if has_col else " — <b>no such column on GL Entry!</b>")
				)
		if applied:
			messages.append(_("Dimension filters applied: {0}").format("; ".join(applied)))
		else:
			messages.append(
				_("Active dimensions available (none selected): {0}").format(
					", ".join(f"{v} ({k})" for k, v in extra_dims.items())
				)
			)

	def account_amounts(meta, is_income):
		amounts = {}
		for cp in column_periods:
			amt = 0.0
			for m in meta["members"]:
				if cp.get("company") and m["company"] != cp["company"]:
					continue
				debit, credit = balances[cp["key"]].get(m["name"], (0.0, 0.0))
				raw = flt(credit) - flt(debit) if is_income else flt(debit) - flt(credit)
				amt += raw * rates[(cp["key"], m["company"])]
			amounts[cp["key"]] = flt(amt, 3)
		if show_totals:
			for g in groups:
				tkey = f"total_{g['suffix']}"
				amounts[tkey] = flt(sum(amounts[k] for k in keys_by_group[g["suffix"]]), 3)
		if company_mode:
			amounts["grand_total"] = flt(sum(amounts[k] for k in col_keys), 3)
		return amounts

	def make_row(label, amounts=None, **flags):
		row = {"account_label": label, "currency": currency}
		if amounts is not None:
			if growth_defs:
				amounts = compute_growth(dict(amounts), growth_defs)
			for k in all_keys + growth_keys:
				v = amounts.get(k)
				if (
					v is not None
					and filters.get("remove_decimals")
					and not k.startswith("growth_")
				):
					v = flt(round(v), 0)
				row[k] = v
		row.update(flags)
		return row

	def zero_amounts():
		return {k: 0.0 for k in all_keys}

	def add_amounts(target, source):
		for k in target:
			target[k] = flt(target[k] + source.get(k, 0.0), 3)

	def subtract_amounts(target, source):
		for k in target:
			target[k] = flt(target[k] - source.get(k, 0.0), 3)

	def is_all_zero(amounts):
		return all(not amounts[k] for k in col_keys)

	def flat_rows(section_key, is_income):
		rows, total = [], zero_amounts()
		for mkey, meta in sorted(sections[section_key].items(), key=lambda kv: kv[1]["label"]):
			amounts = account_amounts(meta, is_income)
			if is_all_zero(amounts) and not filters.get("show_zero_values"):
				continue
			add_amounts(total, amounts)
			rows.append(make_row("        " + meta["label"], amounts,
				account=meta["members"][0]["name"], indent=1))
		return rows, total

	def grouped_rows(section_key, is_income):
		grouped = {}
		for mkey, meta in sections[section_key].items():
			amounts = account_amounts(meta, is_income)
			if is_all_zero(amounts) and not filters.get("show_zero_values"):
				continue
			grouped.setdefault(meta["parent_label"], []).append(
				(meta["label"], meta["members"][0]["name"], amounts)
			)

		rows, total = [], zero_amounts()
		for parent_label in sorted(grouped):
			sub_total = zero_amounts()
			rows.append(make_row("    " + parent_label, is_subheader=1))
			for label, name, amounts in sorted(grouped[parent_label], key=lambda x: x[0]):
				add_amounts(sub_total, amounts)
				rows.append(make_row("            " + label, amounts, account=name, indent=2))
			rows.append(make_row("    " + _("Total {0}").format(parent_label), sub_total,
				is_subtotal=1))
			add_amounts(total, sub_total)
		return rows, total

	def section_rows(section_key, is_income):
		if section_key in GROUPED_SECTIONS and filters.get("group_operating_expenses", 1):
			return grouped_rows(section_key, is_income)
		return flat_rows(section_key, is_income)

	ti_rows, ti_total = section_rows("trading_income", True)
	cos_rows, cos_total = section_rows("cost_of_sales", False)
	oi_rows, oi_total = section_rows("other_income", True)
	oe_rows, oe_total = section_rows("operating_expenses", False)

	gross_profit = zero_amounts()
	add_amounts(gross_profit, ti_total)
	subtract_amounts(gross_profit, cos_total)

	net_profit = dict(gross_profit)
	add_amounts(net_profit, oi_total)
	subtract_amounts(net_profit, oe_total)

	data = []
	data.append(make_row(_("Trading Income"), is_header=1))
	data.extend(ti_rows)
	data.append(make_row(_("Total Trading Income"), ti_total, is_total=1))
	data.append(make_row(""))

	data.append(make_row(_("Cost of Sales"), is_header=1))
	data.extend(cos_rows)
	data.append(make_row(_("Total Cost of Sales"), cos_total, is_total=1))
	data.append(make_row(""))

	data.append(make_row(_("Gross Profit"), gross_profit, is_total=1, bold_class="profit"))
	data.append(make_row(""))

	data.append(make_row(_("Other Income"), is_header=1))
	data.extend(oi_rows)
	data.append(make_row(_("Total Other Income"), oi_total, is_total=1))
	data.append(make_row(""))

	data.append(make_row(_("Operating Expenses"), is_header=1))
	data.extend(oe_rows)
	data.append(make_row(_("Total Operating Expenses"), oe_total, is_total=1))
	data.append(make_row(""))

	data.append(make_row(_("Net Profit"), net_profit, is_total=1, bold_class="profit"))

	return data, messages


# ---------------------------------------------------------------------------
# Account classification
# ---------------------------------------------------------------------------
def classify_accounts(filters, messages):
	"""{section_key: {merged_key: {label, parent_label, members}}}

	members = [{"name": Account.name, "company": company}]
	Accounts from different companies are merged into one row when their
	account_number (preferred) or account_name matches - this is what makes
	consolidation line up e.g. '4010104 - Revenue from Direct Sales' across
	TSL Kuwait and TSL UAE.
	"""
	sections = {k: {} for k in SECTION_PARENTS}

	for company, _cur in get_companies(filters):
		claimed = set()

		all_groups = frappe.get_all(
			"Account",
			filters={"company": company, "is_group": 1},
			fields=["name", "account_name", "root_type", "lft", "rgt"],
		)
		group_label_by_name = {g.name: g.account_name for g in all_groups}

		def find_parents(cfg):
			wanted = [n.strip().lower() for n in cfg["names"]]
			return [
				g for g in all_groups
				if g.root_type == cfg["root_type"]
				and (g.account_name or "").strip().lower() in wanted
			]

		for key in ["trading_income", "cost_of_sales", "other_income", "operating_expenses"]:
			cfg = SECTION_PARENTS[key]
			parents = find_parents(cfg)
			if not parents:
				messages.append(
					_("[{0}] No group account found for section: {1}").format(
						company, frappe.bold(key)
					)
				)
				continue

			messages.append(
				_("[{0}] Section {1} → group(s): {2}").format(
					company, frappe.bold(key),
					", ".join(frappe.bold(p.name) for p in parents),
				)
			)

			for p in parents:
				children = frappe.get_all(
					"Account",
					filters={
						"company": company,
						"is_group": 0,
						"root_type": cfg["root_type"],
						"lft": [">=", p.lft],
						"rgt": ["<=", p.rgt],
					},
					fields=["name", "account_name", "account_number", "parent_account"],
				)
				for a in children:
					if a.name in claimed:
						continue
					claimed.add(a.name)
					merged_key = (a.account_number or a.account_name or "").strip().lower()
					label = (f"{a.account_number} - " if a.account_number else "") \
						+ a.account_name
					parent_label = group_label_by_name.get(a.parent_account, _("Other"))
					entry = sections[key].setdefault(
						merged_key,
						{"label": label, "parent_label": parent_label, "members": []},
					)
					entry["members"].append({"name": a.name, "company": company})

	total_accounts = sum(len(s) for s in sections.values())
	messages.append(_("Total merged account rows: {0}").format(frappe.bold(total_accounts)))

	return sections


# ---------------------------------------------------------------------------
# GL balances
# ---------------------------------------------------------------------------
def ensure_gl_dimension(fieldname, nice_name):
	if not frappe.db.has_column("GL Entry", fieldname):
		frappe.throw(
			_(
				"GL Entry has no {0} field. Create an Accounting Dimension for "
				"<b>{0}</b> (Accounting → Accounting Dimensions → New → Reference "
				"Document Type: {0}), then post transactions with a {1}."
			).format(nice_name, nice_name.lower())
		)


def get_gl_balances(filters, account_list, from_date, to_date, branch=None, company=None):
	if not account_list:
		return {}

	conditions = []
	values = {
		"company": company or filters.company,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"accounts": account_list,
	}

	if filters.get("project"):
		conditions.append("gle.project = %(project)s")
		values["project"] = filters.project

	# branch: per-column (comparison mode) or single plain filter
	effective_branch = branch or filters.get("_single_branch")
	if effective_branch:
		ensure_gl_dimension("branch", "Branch")
		conditions.append("gle.branch = %(branch)s")
		values["branch"] = effective_branch

	cost_centers = parse_multiselect(filters.get("cost_center"))
	if cost_centers:
		cc_list = []
		for cc in cost_centers:
			lft, rgt = frappe.db.get_value("Cost Center", cc, ["lft", "rgt"])
			cc_list += frappe.get_all(
				"Cost Center",
				filters={"lft": [">=", lft], "rgt": ["<=", rgt]},
				pluck="name",
			)
		conditions.append("gle.cost_center in %(cost_centers)s")
		values["cost_centers"] = list(set(cc_list))

	departments = parse_multiselect(filters.get("department"))
	if departments:
		ensure_gl_dimension("department", "Department")
		conditions.append("gle.department in %(departments)s")
		values["departments"] = departments

	# any other active Accounting Dimensions selected in the filters
	for dim, nice_name in get_extra_dimensions().items():
		dim_values = parse_multiselect(filters.get(dim))
		if dim_values:
			ensure_gl_dimension(dim, nice_name)
			conditions.append(f"gle.`{dim}` in %(dim_{dim})s")
			values[f"dim_{dim}"] = dim_values

	extra = (" and " + " and ".join(conditions)) if conditions else ""

	rows = frappe.db.sql(
		f"""
		select gle.account, sum(gle.debit) as debit, sum(gle.credit) as credit
		from `tabGL Entry` gle
		where gle.company = %(company)s
			and ifnull(gle.is_cancelled, 0) = 0
			and ifnull(gle.voucher_type, '') != 'Period Closing Voucher'
			and ifnull(gle.is_opening, 'No') != 'Yes'
			and gle.posting_date >= %(from_date)s
			and gle.posting_date <= %(to_date)s
			and gle.account in %(accounts)s
			{extra}
		group by gle.account
		""",
		values,
		as_dict=True,
	)
	return {r.account: (flt(r.debit), flt(r.credit)) for r in rows}