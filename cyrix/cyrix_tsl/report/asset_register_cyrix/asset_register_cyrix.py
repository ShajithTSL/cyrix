# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Max, Sum
from frappe.utils import add_days, flt, formatdate, getdate

from collections import defaultdict


def execute(filters=None):
	filters.day_before_from_date = add_days(filters.from_date, -1)
	columns, data = get_columns(filters), get_data(filters)
	return columns, data


def get_data(filters):
	if filters.get("group_by") == "Asset Category":
		return get_group_by_asset_category_data(filters)
	elif filters.get("group_by") == "Asset":
		return get_group_by_asset_data(filters)


def get_group_by_asset_category_data(filters):
	data = []

	asset_categories = get_asset_categories_for_grouped_by_category(filters)
	assets = get_assets_for_grouped_by_category(filters)
	asset_value_adjustment_map = get_asset_value_adjustment_map_by_category(filters)

	for asset_category in asset_categories:
		row = frappe._dict()
		row.update(asset_category)

		adjustments = asset_value_adjustment_map.get(asset_category.get("asset_category"), {})
		row.adjustment_before_from_date = flt(adjustments.get("adjustment_before_from_date", 0))
		row.adjustment_till_to_date = flt(adjustments.get("adjustment_till_to_date", 0))
		row.adjustment_during_period = row.adjustment_till_to_date - row.adjustment_before_from_date

		row.value_as_on_from_date += row.adjustment_before_from_date
		row.value_as_on_to_date = (
			flt(row.value_as_on_from_date)
			+ flt(row.value_of_new_purchase)
			- flt(row.value_of_sold_asset)
			- flt(row.value_of_scrapped_asset)
			- flt(row.value_of_capitalized_asset)
			+ flt(row.adjustment_during_period)
		)

		row.update(
			next(
				asset
				for asset in assets
				if asset["asset_category"] == asset_category.get("asset_category", "")
			)
		)

		row.accumulated_depreciation_as_on_to_date = (
			flt(row.accumulated_depreciation_as_on_from_date)
			+ flt(row.depreciation_amount_during_the_period)
			- flt(row.depreciation_eliminated_during_the_period)
			- flt(row.depreciation_eliminated_via_reversal)
		)

		row.net_asset_value_as_on_from_date = flt(row.value_as_on_from_date) - flt(
			row.accumulated_depreciation_as_on_from_date
		)

		row.net_asset_value_as_on_to_date = flt(row.value_as_on_to_date) - flt(
			row.accumulated_depreciation_as_on_to_date
		)

		data.append(row)

	return data


def get_asset_categories_for_grouped_by_category(filters):
	asset = frappe.qb.DocType("Asset")
	asset_depreciation_schedule = frappe.qb.DocType("Asset Depreciation Schedule")
	asset_capitalization_asset_item = frappe.qb.DocType("Asset Capitalization Asset Item")
	asset_capitalization = frappe.qb.DocType("Asset Capitalization")

	disposal_in_period = (
		(IfNull(asset.disposal_date, 0) != 0)
		& (asset.disposal_date >= filters.from_date)
		& (asset.disposal_date <= filters.to_date)
	)

	value_as_on_from_date = IfNull(
		Sum(
			frappe.qb.terms.Case()
			.when(
				(asset.purchase_date < filters.from_date)
				& ((IfNull(asset.disposal_date, 0) == 0) | (asset.disposal_date >= filters.from_date)),
				asset.gross_purchase_amount,
			)
			.else_(0)
		),
		0,
	).as_("value_as_on_from_date")

	value_of_new_purchase = IfNull(
		Sum(
			frappe.qb.terms.Case()
			.when(asset.purchase_date >= filters.from_date, asset.gross_purchase_amount)
			.else_(0)
		),
		0,
	).as_("value_of_new_purchase")

	value_of_sold_asset = IfNull(
		Sum(
			frappe.qb.terms.Case()
			.when(disposal_in_period & (asset.status == "Sold"), asset.gross_purchase_amount)
			.else_(0)
		),
		0,
	).as_("value_of_sold_asset")

	value_of_scrapped_asset = IfNull(
		Sum(
			frappe.qb.terms.Case()
			.when(disposal_in_period & (asset.status == "Scrapped"), asset.gross_purchase_amount)
			.else_(0)
		),
		0,
	).as_("value_of_scrapped_asset")

	value_of_capitalized_asset = IfNull(
		Sum(
			frappe.qb.terms.Case()
			.when(disposal_in_period & (asset.status == "Capitalized"), asset.gross_purchase_amount)
			.else_(0)
		),
		0,
	).as_("value_of_capitalized_asset")

	capitalized_before_from_date = (
		frappe.qb.from_(asset_capitalization_asset_item)
		.join(asset_capitalization)
		.on(asset_capitalization_asset_item.parent == asset_capitalization.name)
		.select(asset_capitalization_asset_item.asset)
		.where(asset_capitalization.posting_date < filters.from_date)
		.where(asset_capitalization.docstatus == 1)
	)

	query = (
		frappe.qb.from_(asset)
		.select(
			asset.asset_category,
			value_as_on_from_date,
			value_of_new_purchase,
			value_of_sold_asset,
			value_of_scrapped_asset,
			value_of_capitalized_asset,
		)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(asset.name.notin(capitalized_before_from_date))
		.groupby(asset.asset_category)
	)

	if filters.get("asset_category"):
		query = query.where(asset.asset_category == filters.get("asset_category"))

	if filters.get("finance_book"):
		assets_with_finance_book = (
			frappe.qb.from_(asset_depreciation_schedule)
			.select(asset_depreciation_schedule.asset)
			.where(asset_depreciation_schedule.finance_book == filters.get("finance_book"))
		)
		query = query.where(asset.name.isin(assets_with_finance_book))

	return query.run(as_dict=True)


def get_accumulated_depreciation_account_map(filters):
	"""Return {asset_category: accumulated_depreciation_account} plus the company default.

	The accumulated depreciation account is what the Trial Balance reports, so the
	report's depreciation balances are derived from this account's GL postings.
	"""
	asset_category_account = frappe.qb.DocType("Asset Category Account")

	rows = (
		frappe.qb.from_(asset_category_account)
		.select(
			asset_category_account.parent.as_("asset_category"),
			asset_category_account.accumulated_depreciation_account,
		)
		.where(asset_category_account.company_name == filters.company)
	).run(as_dict=True)

	company_default = frappe.db.get_value(
		"Company", filters.company, "accumulated_depreciation_account"
	)

	category_account_map = {}
	for r in rows:
		category_account_map[r.asset_category] = r.accumulated_depreciation_account or company_default

	return category_account_map, company_default


def get_accumulated_depreciation_balances_by_account(filters, accounts):
	"""Sum the accumulated depreciation account movements from the GL, grouped by account.

	Balance convention (accumulated depreciation is a contra-asset / credit account):
	        balance = SUM(credit) - SUM(debit)

	This is exactly how the Trial Balance derives the account's closing balance, so the
	figures produced here tie out to the Trial Balance.
	"""
	if not accounts:
		return {}

	gl_entry = frappe.qb.DocType("GL Entry")

	query = (
		frappe.qb.from_(gl_entry)
		.select(
			gl_entry.account,
			# Opening balance: everything posted strictly before the From Date.
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(gl_entry.posting_date < filters.from_date, gl_entry.credit - gl_entry.debit)
					.else_(0)
				),
				0,
			).as_("accumulated_depreciation_as_on_from_date"),
			# Depreciation charged during the period = credits inside the period.
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date >= filters.from_date)
						& (gl_entry.posting_date <= filters.to_date),
						gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("depreciation_amount_during_the_period"),
			# Depreciation removed during the period (disposals / reversals) = debits inside the period.
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date >= filters.from_date)
						& (gl_entry.posting_date <= filters.to_date),
						gl_entry.debit,
					)
					.else_(0)
				),
				0,
			).as_("depreciation_eliminated_during_the_period"),
		)
		.where(gl_entry.is_cancelled == 0)
		.where(gl_entry.company == filters.company)
		.where(gl_entry.account.isin(list(accounts)))
		.groupby(gl_entry.account)
	)

	if filters.get("finance_book"):
		query = query.where(IfNull(gl_entry.finance_book, "") == filters.get("finance_book"))

	balances = {}
	for row in query.run(as_dict=True):
		balances[row.account] = row

	return balances


def get_categories_in_scope(filters):
	asset = frappe.qb.DocType("Asset")
	asset_depreciation_schedule = frappe.qb.DocType("Asset Depreciation Schedule")

	query = (
		frappe.qb.from_(asset)
		.select(asset.asset_category)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.groupby(asset.asset_category)
	)

	if filters.get("asset_category"):
		query = query.where(asset.asset_category == filters.get("asset_category"))

	if filters.get("finance_book"):
		assets_with_finance_book = (
			frappe.qb.from_(asset_depreciation_schedule)
			.select(asset_depreciation_schedule.asset)
			.where(asset_depreciation_schedule.finance_book == filters.get("finance_book"))
		)
		query = query.where(asset.name.isin(assets_with_finance_book))

	return [r.asset_category for r in query.run(as_dict=True)]


def get_assets_for_grouped_by_category(filters):
	"""Accumulated depreciation per asset category, sourced from the accumulated
	depreciation GL account so the totals match the Trial Balance."""
	categories = get_categories_in_scope(filters)
	category_account_map, company_default = get_accumulated_depreciation_account_map(filters)

	resolved_account = {}
	accounts = set()
	for category in categories:
		account = category_account_map.get(category) or company_default
		resolved_account[category] = account
		if account:
			accounts.add(account)

	account_balances = get_accumulated_depreciation_balances_by_account(filters, accounts)

	results = []
	for category in categories:
		account = resolved_account.get(category)
		balance = account_balances.get(account) if account else None

		results.append(
			{
				"asset_category": category,
				"accumulated_depreciation_as_on_from_date": flt(
					balance.accumulated_depreciation_as_on_from_date
				)
				if balance
				else 0.0,
				"depreciation_amount_during_the_period": flt(
					balance.depreciation_amount_during_the_period
				)
				if balance
				else 0.0,
				"depreciation_eliminated_during_the_period": flt(
					balance.depreciation_eliminated_during_the_period
				)
				if balance
				else 0.0,
				# Folded into "eliminated during the period"; kept for column compatibility.
				"depreciation_eliminated_via_reversal": 0.0,
			}
		)

	return results


def get_asset_value_adjustment_map_by_category(filters):
	asset = frappe.qb.DocType("Asset")
	gl_entry = frappe.qb.DocType("GL Entry")
	asset_category_account = frappe.qb.DocType("Asset Category Account")

	asset_value_adjustments = (
		frappe.qb.from_(gl_entry)
		.join(asset)
		.on(gl_entry.against_voucher == asset.name)
		.join(asset_category_account)
		.on(
			(asset_category_account.parent == asset.asset_category)
			& (asset_category_account.company_name == filters.company)
		)
		.select(
			asset.asset_category.as_("asset_category"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date < filters.from_date)
						& (asset.disposal_date.isnull() | (asset.disposal_date >= filters.from_date)),
						gl_entry.debit - gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("value_adjustment_before_from_date"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date <= filters.to_date)
						& (asset.disposal_date.isnull() | (asset.disposal_date >= filters.to_date)),
						gl_entry.debit - gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("value_adjustment_till_to_date"),
		)
		.where(gl_entry.is_cancelled == 0)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(gl_entry.account == asset_category_account.fixed_asset_account)
		.where(gl_entry.is_opening == "No")
		.groupby(asset.asset_category)
	).run(as_dict=True)

	category_value_adjustment_map = {}

	for r in asset_value_adjustments:
		category_value_adjustment_map[r["asset_category"]] = {
			"adjustment_before_from_date": flt(r.get("value_adjustment_before_from_date", 0)),
			"adjustment_till_to_date": flt(r.get("value_adjustment_till_to_date", 0)),
		}

	return category_value_adjustment_map


def get_group_by_asset_data(filters):
	data = []

	asset_details = get_asset_details_for_grouped_by_category(filters)
	assets = get_assets_for_grouped_by_asset(filters)
	asset_value_adjustment_map = get_asset_value_adjustment_map(filters)

	for asset_detail in asset_details:
		row = frappe._dict()
		row.update(asset_detail)

		row.update(next(asset for asset in assets if asset["asset"] == asset_detail.get("name", "")))
		adjustments = asset_value_adjustment_map.get(
			asset_detail.get("name", ""),
			{
				"adjustment_before_from_date": 0.0,
				"adjustment_till_to_date": 0.0,
			},
		)
		row.adjustment_before_from_date = adjustments["adjustment_before_from_date"]
		row.adjustment_till_to_date = adjustments["adjustment_till_to_date"]
		row.adjustment_during_period = flt(row.adjustment_till_to_date) - flt(row.adjustment_before_from_date)

		row.value_as_on_from_date += row.adjustment_before_from_date

		row.value_as_on_to_date = (
			flt(row.value_as_on_from_date)
			+ flt(row.value_of_new_purchase)
			- flt(row.value_of_sold_asset)
			- flt(row.value_of_scrapped_asset)
			- flt(row.value_of_capitalized_asset)
			+ flt(row.adjustment_during_period)
		)

		row.accumulated_depreciation_as_on_to_date = (
			flt(row.accumulated_depreciation_as_on_from_date)
			+ flt(row.depreciation_amount_during_the_period)
			- flt(row.depreciation_eliminated_during_the_period)
			- flt(row.depreciation_eliminated_via_reversal)
		)

		row.net_asset_value_as_on_from_date = flt(row.value_as_on_from_date) - flt(
			row.accumulated_depreciation_as_on_from_date
		)

		row.net_asset_value_as_on_to_date = flt(row.value_as_on_to_date) - flt(
			row.accumulated_depreciation_as_on_to_date
		)

		data.append(row)

	# --- Unallocated reconciliation lines (one per account/category) ---
	# Some accumulated-depreciation GL entries can't be tied to any asset (opening/migration
	# entries or manual journal entries with no asset in against_voucher, e.g. an auditor
	# adjustment). The category view includes them because it sums the whole account, but the
	# per-asset view can't attribute them. Surface each account's remainder as its own labelled
	# line so both the grand total AND each category reconcile to the GL account / Trial Balance.
	data.extend(get_unallocated_accumulated_depreciation(filters, data))

	return data


def get_unallocated_accumulated_depreciation(filters, data):
	"""Return one reconciliation row per accumulated-depreciation account holding the amount
	that is in the GL account but not attributable to any asset. Each row carries its
	asset_category so the by-asset view reconciles per category as well as in total."""
	category_account_map, company_default = get_accumulated_depreciation_account_map(filters)

	accounts = {account for account in category_account_map.values() if account}
	if company_default:
		accounts.add(company_default)

	account_balances = get_accumulated_depreciation_balances_by_account(filters, accounts)

	# account -> list of categories that post to it
	account_categories = defaultdict(list)
	for category, account in category_account_map.items():
		if account:
			account_categories[account].append(category)

	# Resolve each in-scope asset to its accumulated-depreciation account via its category.
	name_to_category = dict(
		frappe.get_all(
			"Asset",
			filters={"company": filters.company, "docstatus": 1},
			fields=["name", "asset_category"],
			as_list=True,
		)
	)

	assets_from_by_account = defaultdict(float)
	assets_to_by_account = defaultdict(float)
	for r in data:
		category = name_to_category.get(r.get("asset"))
		account = category_account_map.get(category) or company_default
		assets_from_by_account[account] += flt(r.accumulated_depreciation_as_on_from_date)
		assets_to_by_account[account] += flt(r.accumulated_depreciation_as_on_to_date)

	rows = []
	for account, balance in account_balances.items():
		bal_from = flt(balance.accumulated_depreciation_as_on_from_date)
		bal_to = (
			bal_from
			+ flt(balance.depreciation_amount_during_the_period)
			- flt(balance.depreciation_eliminated_during_the_period)
		)

		unallocated_from = flt(bal_from - assets_from_by_account.get(account, 0.0))
		unallocated_to = flt(bal_to - assets_to_by_account.get(account, 0.0))

		if abs(unallocated_from) < 0.01 and abs(unallocated_to) < 0.01:
			continue

		categories = account_categories.get(account, [])
		label = ", ".join(categories) if categories else account

		rows.append(
			frappe._dict(
				{
					"asset": None,
					"asset_category": categories[0] if len(categories) == 1 else None,
					"asset_name": _("Unallocated - {0} (GL entries not linked to an asset)").format(label),
					"value_as_on_from_date": 0.0,
					"value_of_new_purchase": 0.0,
					"value_of_sold_asset": 0.0,
					"value_of_scrapped_asset": 0.0,
					"value_of_capitalized_asset": 0.0,
					"value_as_on_to_date": 0.0,
					"accumulated_depreciation_as_on_from_date": unallocated_from,
					"depreciation_amount_during_the_period": flt(unallocated_to - unallocated_from),
					"depreciation_eliminated_during_the_period": 0.0,
					"depreciation_eliminated_via_reversal": 0.0,
					"accumulated_depreciation_as_on_to_date": unallocated_to,
					"net_asset_value_as_on_from_date": -unallocated_from,
					"net_asset_value_as_on_to_date": -unallocated_to,
				}
			)
		)

	return rows


def get_asset_details_for_grouped_by_category(filters):
	asset = frappe.qb.DocType("Asset")
	asset_depreciation_schedule = frappe.qb.DocType("Asset Depreciation Schedule")
	asset_capitalization_asset_item = frappe.qb.DocType("Asset Capitalization Asset Item")
	asset_capitalization = frappe.qb.DocType("Asset Capitalization")

	disposal_in_period = (
		(IfNull(asset.disposal_date, 0) != 0)
		& (asset.disposal_date >= filters.from_date)
		& (asset.disposal_date <= filters.to_date)
	)

	capitalized_before_from_date = (
		frappe.qb.from_(asset_capitalization_asset_item)
		.join(asset_capitalization)
		.on(asset_capitalization_asset_item.parent == asset_capitalization.name)
		.select(asset_capitalization_asset_item.asset)
		.where(asset_capitalization.posting_date < filters.from_date)
		.where(asset_capitalization.docstatus == 1)
	)

	query = (
		frappe.qb.from_(asset)
		.select(
			asset.name,
			asset.asset_name,
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(asset.purchase_date < filters.from_date)
						& (
							(IfNull(asset.disposal_date, 0) == 0) | (asset.disposal_date >= filters.from_date)
						),
						asset.gross_purchase_amount,
					)
					.else_(0)
				),
				0,
			).as_("value_as_on_from_date"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(asset.purchase_date >= filters.from_date, asset.gross_purchase_amount)
					.else_(0)
				),
				0,
			).as_("value_of_new_purchase"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(disposal_in_period & (asset.status == "Sold"), asset.gross_purchase_amount)
					.else_(0)
				),
				0,
			).as_("value_of_sold_asset"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(disposal_in_period & (asset.status == "Scrapped"), asset.gross_purchase_amount)
					.else_(0)
				),
				0,
			).as_("value_of_scrapped_asset"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						disposal_in_period & (asset.status == "Capitalized"),
						asset.gross_purchase_amount,
					)
					.else_(0)
				),
				0,
			).as_("value_of_capitalized_asset"),
		)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(asset.name.notin(capitalized_before_from_date))
		.groupby(asset.name)
	)

	if filters.get("asset"):
		query = query.where(asset.name == filters.get("asset"))

	if filters.get("finance_book"):
		assets_with_finance_book = (
			frappe.qb.from_(asset_depreciation_schedule)
			.select(asset_depreciation_schedule.asset)
			.where(asset_depreciation_schedule.finance_book == filters.get("finance_book"))
		)
		query = query.where(asset.name.isin(assets_with_finance_book))

	return query.run(as_dict=True)


def get_asset_names_in_scope(filters):
	asset = frappe.qb.DocType("Asset")
	asset_depreciation_schedule = frappe.qb.DocType("Asset Depreciation Schedule")
	asset_capitalization_asset_item = frappe.qb.DocType("Asset Capitalization Asset Item")
	asset_capitalization = frappe.qb.DocType("Asset Capitalization")

	capitalized_before_from_date = (
		frappe.qb.from_(asset_capitalization_asset_item)
		.join(asset_capitalization)
		.on(asset_capitalization_asset_item.parent == asset_capitalization.name)
		.select(asset_capitalization_asset_item.asset)
		.where(asset_capitalization.posting_date < filters.from_date)
		.where(asset_capitalization.docstatus == 1)
	)

	query = (
		frappe.qb.from_(asset)
		.select(asset.name)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(asset.name.notin(capitalized_before_from_date))
	)

	if filters.get("asset"):
		query = query.where(asset.name == filters.get("asset"))

	if filters.get("finance_book"):
		assets_with_finance_book = (
			frappe.qb.from_(asset_depreciation_schedule)
			.select(asset_depreciation_schedule.asset)
			.where(asset_depreciation_schedule.finance_book == filters.get("finance_book"))
		)
		query = query.where(asset.name.isin(assets_with_finance_book))

	return [r.name for r in query.run(as_dict=True)]


def get_assets_for_grouped_by_asset(filters):
	"""Accumulated depreciation per asset from POSTED GL entries on the accumulated
	depreciation account (linked to the asset via against_voucher), so the figures tie to
	the Trial Balance exactly like the Asset Category grouping does.

	Only posted depreciation is counted (scheduled-but-unbooked depreciation is excluded),
	because the Trial Balance only reflects posted entries.

	Split assets are then corrected: an asset split posts no GL, so the pre-split
	depreciation stays in the GL against the original asset. We move each split-off asset's
	carried opening (Asset.opening_accumulated_depreciation) from the original asset to the
	split asset. This reallocation nets to zero, so every total still ties to the TB.
	"""
	asset = frappe.qb.DocType("Asset")
	gl_entry = frappe.qb.DocType("GL Entry")
	asset_category_account = frappe.qb.DocType("Asset Category Account")
	company = frappe.qb.DocType("Company")
	asset_depreciation_schedule = frappe.qb.DocType("Asset Depreciation Schedule")

	assets_with_finance_book = None
	if filters.get("finance_book"):
		assets_with_finance_book = (
			frappe.qb.from_(asset_depreciation_schedule)
			.select(asset_depreciation_schedule.asset)
			.where(asset_depreciation_schedule.finance_book == filters.get("finance_book"))
		)

	accumulated_depreciation_account = IfNull(
		asset_category_account.accumulated_depreciation_account,
		company.accumulated_depreciation_account,
	)

	query = (
		frappe.qb.from_(gl_entry)
		.join(asset)
		.on(gl_entry.against_voucher == asset.name)
		.join(asset_category_account)
		.on(
			(asset_category_account.parent == asset.asset_category)
			& (asset_category_account.company_name == filters.company)
		)
		.join(company)
		.on(company.name == filters.company)
		.select(
			asset.name.as_("asset"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(gl_entry.posting_date < filters.from_date, gl_entry.credit - gl_entry.debit)
					.else_(0)
				),
				0,
			).as_("accumulated_depreciation_as_on_from_date"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date >= filters.from_date)
						& (gl_entry.posting_date <= filters.to_date),
						gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("depreciation_amount_during_the_period"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date >= filters.from_date)
						& (gl_entry.posting_date <= filters.to_date),
						gl_entry.debit,
					)
					.else_(0)
				),
				0,
			).as_("depreciation_eliminated_during_the_period"),
		)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(gl_entry.is_cancelled == 0)
		.where(gl_entry.account == accumulated_depreciation_account)
		.groupby(asset.name)
	)

	if filters.get("asset"):
		query = query.where(asset.name == filters.get("asset"))

	if assets_with_finance_book is not None:
		query = query.where(
			IfNull(gl_entry.finance_book, "") == filters.get("finance_book")
		).where(asset.name.isin(assets_with_finance_book))

	combined = {}
	gl_linked_assets = set()
	for row in query.run(as_dict=True):
		gl_linked_assets.add(row.asset)
		combined[row.asset] = {
			"asset": row.asset,
			"accumulated_depreciation_as_on_from_date": flt(row.accumulated_depreciation_as_on_from_date),
			"depreciation_amount_during_the_period": flt(row.depreciation_amount_during_the_period),
			"depreciation_eliminated_during_the_period": flt(row.depreciation_eliminated_during_the_period),
			"depreciation_eliminated_via_reversal": 0.0,
		}

	# Ensure every in-scope asset has a row so downstream `next(...)` never raises.
	for asset_name in get_asset_names_in_scope(filters):
		combined.setdefault(
			asset_name,
			{
				"asset": asset_name,
				"accumulated_depreciation_as_on_from_date": 0.0,
				"depreciation_amount_during_the_period": 0.0,
				"depreciation_eliminated_during_the_period": 0.0,
				"depreciation_eliminated_via_reversal": 0.0,
			},
		)

	# --- Add opening accumulated depreciation ONLY for assets with no GL-linked depreciation ---
	# Migrated/existing assets that were fully (or partly) depreciated before go-live can have
	# their opening depreciation posted to the accumulated-depreciation account WITHOUT being
	# tagged to the asset (against_voucher). Those assets show 0 in the GL-by-asset query above,
	# so we add their master opening back — that is the piece the Trial Balance / category view
	# has but this view was missing.
	#
	# Assets that DO have GL-linked depreciation are already fully represented by the GL; their
	# master opening was used only to seed the schedule and is NOT separately posted, so adding
	# it would double-count and overshoot the Trial Balance.
	opening_query = (
		frappe.qb.from_(asset)
		.select(asset.name.as_("asset"), asset.opening_accumulated_depreciation)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(IfNull(asset.opening_accumulated_depreciation, 0) != 0)
	)

	if filters.get("asset"):
		opening_query = opening_query.where(asset.name == filters.get("asset"))

	for row in opening_query.run(as_dict=True):
		amount = flt(row.opening_accumulated_depreciation)
		if not amount or row.asset not in combined:
			continue
		if row.asset in gl_linked_assets:
			# Already counted via the GL; adding the opening would double-count.
			continue
		combined[row.asset]["accumulated_depreciation_as_on_from_date"] += amount

	return list(combined.values())


def get_asset_value_adjustment_map(filters):
	asset = frappe.qb.DocType("Asset")
	gl_entry = frappe.qb.DocType("GL Entry")
	asset_category_account = frappe.qb.DocType("Asset Category Account")

	asset_with_value_adjustments = (
		frappe.qb.from_(gl_entry)
		.join(asset)
		.on(gl_entry.against_voucher == asset.name)
		.join(asset_category_account)
		.on(
			(asset_category_account.parent == asset.asset_category)
			& (asset_category_account.company_name == filters.company)
		)
		.select(
			asset.name.as_("asset"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date < filters.from_date)
						& (asset.disposal_date.isnull() | (asset.disposal_date >= filters.from_date)),
						gl_entry.debit - gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("value_adjustment_before_from_date"),
			IfNull(
				Sum(
					frappe.qb.terms.Case()
					.when(
						(gl_entry.posting_date <= filters.to_date)
						& (asset.disposal_date.isnull() | (asset.disposal_date >= filters.to_date)),
						gl_entry.debit - gl_entry.credit,
					)
					.else_(0)
				),
				0,
			).as_("value_adjustment_till_to_date"),
		)
		.where(gl_entry.is_cancelled == 0)
		.where(asset.docstatus == 1)
		.where(asset.company == filters.company)
		.where(asset.purchase_date <= filters.to_date)
		.where(gl_entry.account == asset_category_account.fixed_asset_account)
		.where(gl_entry.is_opening == "No")
		.groupby(asset.name)
	).run(as_dict=True)

	asset_value_adjustment_map = {}

	for r in asset_with_value_adjustments:
		asset_value_adjustment_map[r["asset"]] = {
			"adjustment_before_from_date": flt(r.get("value_adjustment_before_from_date", 0)),
			"adjustment_till_to_date": flt(r.get("value_adjustment_till_to_date", 0)),
		}

	return asset_value_adjustment_map


def get_columns(filters):
	columns = []

	if filters.get("group_by") == "Asset Category":
		columns.append(
			{
				"label": _("Asset Category"),
				"fieldname": "asset_category",
				"fieldtype": "Link",
				"options": "Asset Category",
				"width": 120,
			}
		)
	elif filters.get("group_by") == "Asset":
		columns.append(
			{
				"label": _("Asset"),
				"fieldname": "asset",
				"fieldtype": "Link",
				"options": "Asset",
				"width": 120,
			}
		)
		columns.append(
			{
				"label": _("Asset Name"),
				"fieldname": "asset_name",
				"fieldtype": "Data",
				"width": 140,
			}
		)

	columns += [
		{
			"label": _("Value as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "value_as_on_from_date",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Value of New Purchase"),
			"fieldname": "value_of_new_purchase",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Value of Sold Asset"),
			"fieldname": "value_of_sold_asset",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Value of Scrapped Asset"),
			"fieldname": "value_of_scrapped_asset",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Value of New Capitalized Asset"),
			"fieldname": "value_of_capitalized_asset",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Value as on") + " " + formatdate(filters.to_date),
			"fieldname": "value_as_on_to_date",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Accumulated Depreciation as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "accumulated_depreciation_as_on_from_date",
			"fieldtype": "Currency",
			"width": 270,
		},
		{
			"label": _("Depreciation Amount during the period"),
			"fieldname": "depreciation_amount_during_the_period",
			"fieldtype": "Currency",
			"width": 240,
		},
		{
			"label": _("Depreciation Eliminated due to disposal of assets"),
			"fieldname": "depreciation_eliminated_during_the_period",
			"fieldtype": "Currency",
			"width": 300,
		},
		{
			"label": _("Accumulated Depreciation as on") + " " + formatdate(filters.to_date),
			"fieldname": "accumulated_depreciation_as_on_to_date",
			"fieldtype": "Currency",
			"width": 270,
		},
		{
			"label": _("Depreciation eliminated via reversal"),
			"fieldname": "depreciation_eliminated_via_reversal",
			"fieldtype": "Currency",
			"width": 270,
		},
		{
			"label": _("Net Asset value as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "net_asset_value_as_on_from_date",
			"fieldtype": "Currency",
			"width": 200,
		},
		{
			"label": _("Net Asset value as on") + " " + formatdate(filters.to_date),
			"fieldname": "net_asset_value_as_on_to_date",
			"fieldtype": "Currency",
			"width": 200,
		},
	]

	return columns