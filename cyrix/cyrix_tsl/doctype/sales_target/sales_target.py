# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from datetime import date


class SalesTarget(Document):
	@frappe.whitelist()
	def get_month_ranges(self,year=None):
		"""
		Returns list of months with:
		- short name (Jan, Feb...)
		- start date
		- end date
		"""
	
		
		year = date.today().year

		months = []

		for month in range(1, 13):
			month_name = calendar.month_abbr[month]  # Jan, Feb, ...

			start_date = date(year, month, 1)

			# get last day of month
			last_day = calendar.monthrange(year, month)[1]
			end_date = date(year, month, last_day)

		

			self.append("target_table", {
				
					"month": month_name,
					"from_date": start_date,
					"to_date": end_date,
					
				})


		return months
