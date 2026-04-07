import frappe
from datetime import datetime
@frappe.whitelist()
def get_technicians(doc_name):
	technician_names = set()
	try:
		doc = frappe.get_doc("Quotation", doc_name)

		for item in doc.items:
			if item.job_order_data:
				job_order = frappe.get_doc("Job Order Data", item.job_order_data)
				for tech_row in job_order.technician:
					if tech_row.technician:
						# Get the actual technician name from linked Technician ID
						tech_name = frappe.db.get_value("Technician ID", tech_row.technician, "technician")
						if tech_name:
							technician_names.add(tech_name)

		return ", ".join(sorted(technician_names)) if technician_names else "-"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Technicians Error")
		return "-"

def is_english(text):
	if not text:
		return True
	try:
		text.encode("ascii")
		return True
	except UnicodeEncodeError:
		return False


def styled_text_per_word(text):
	if not text:
		return ""

	words = text.split(" ")
	styled_words = []

	for word in words:
		if is_english(word):
			font_family = "Roboto"
			font_size = "9px"
		else:
			font_family = "'Scheherazade New'"
			font_size = "12px"  # adjust if needed

		styled_words.append(
			f'<span style="font-family:{font_family}; font-size:{font_size};">'
			f'{word}'
			f'</span>'
		)

	return " ".join(styled_words) + "<br>"


def show_address(address_name):
	if not address_name:
		return ""

	try:
		address = frappe.get_doc("Address", address_name)
	except frappe.DoesNotExistError:
		return ""

	html = f"""
	<link href="https://fonts.googleapis.com/css2?family=Scheherazade+New&family=Roboto&display=swap" rel="stylesheet">

				{styled_text_per_word(address.address_line1)}
				{styled_text_per_word(address.address_line2)}
				{styled_text_per_word(address.city)}
				{styled_text_per_word(address.state)}
				{styled_text_per_word(address.pincode)}
				{styled_text_per_word(address.country)}
				<br>
				{styled_text_per_word("Phone: " + address.phone if address.phone else "")}
				{styled_text_per_word("Email: " + address.email_id if address.email_id else "")}

	"""

	return html

@frappe.whitelist()
def get_mt(name):
	company = frappe.get_value("Quotation", name, "company")

	query = """
		SELECT
			ths.job_order_data,
			ths.total_price,
			IFNULL(SUM(ipd.amount), 0) AS m_cost
		FROM
			`tabQuotation` AS q
		LEFT JOIN 
			`tabTechnician Hours Spent` AS ths ON q.name = ths.parent
		LEFT JOIN 
			`tabItem Price Details` AS ipd ON ths.job_order_data = ipd.job_order_data
			AND q.name = ipd.parent
		WHERE
			q.name = %s
		GROUP BY
			ths.job_order_data
		ORDER BY
			ths.job_order_data
	"""
	result = frappe.db.sql(query, (name,), as_dict=True)

	# Initialize the total material cost
	total_m_cost = 0

	# Process each job_order_data and calculate material cost
	for row in result:
		# Add material cost for each job_order_data to the total
		total_m_cost += row.get("m_cost", 0)


	# Return the total material cost
	return total_m_cost


@frappe.whitelist()
def get_labour(name):
	company = frappe.get_value("Quotation", name, "company")

	query = """
		SELECT
			ths.job_order_data,
			ths.total_price,
			IFNULL(SUM(ipd.amount), 0) AS m_cost,
			qi.net_amount AS mar
		FROM
			`tabQuotation` AS q
		LEFT JOIN
			`tabTechnician Hours Spent` AS ths ON q.name = ths.parent
		LEFT JOIN
			`tabItem Price Details` AS ipd ON ths.job_order_data = ipd.job_order_data
			AND q.name = ipd.parent
		LEFT JOIN
			`tabQuotation Item` AS qi ON q.name = qi.parent
			AND ths.job_order_data = qi.job_order_data
		WHERE
			q.name = %s
		GROUP BY
			ths.job_order_data, qi.net_amount
		ORDER BY
			ths.job_order_data
	"""

	result = frappe.db.sql(query, (name,), as_dict=True)

	t_hrs = 0
	for row in result:
		if row.get("total_price"):
			t_hrs += row.get("total_price", 0)

	return t_hrs


@frappe.whitelist()
def get_material_cost(name):
	ship_cost  = 0
	s_cost = frappe.get_value("Quotation",name,"shipping_cost")
	if s_cost:
		ship_cost = round(s_cost)


	split_cost = 0
	d = frappe.get_doc("Quotation",name)
	if d.items:
		split_cost = ship_cost / len(d.items)
		split_cost = round(split_cost)

	
	company = frappe.get_value("Quotation",name,"company")

	qu = frappe.db.sql(""" select `tabTechnician Hours Spent`.job_order_data,`tabTechnician Hours Spent`.total_price from `tabQuotation` left join 
	`tabTechnician Hours Spent` on `tabQuotation`.name = `tabTechnician Hours Spent`.parent where `tabQuotation`.name = '%s' ORDER BY 
	`tabTechnician Hours Spent`.job_order_data """ %(name) ,as_dict=1)

	qi = frappe.db.sql(""" select `tabQuotation Item`.job_order_data from `tabQuotation` left join 
	`tabQuotation Item` on `tabQuotation`.name = `tabQuotation Item`.parent where `tabQuotation`.name = '%s' """ %(name) ,as_dict=1)

	data = ""
	data += '<thead>'
	data+= '<tr>'
	data+= '<th class="text-center" ><b style = "color:#4a5568" >JO</b></th>'
	data+= '<th class="text-center" colspan="3"><b style = "color:#4a5568">Labor Cost</b></th>'
	data+= '<th class="text-center" colspan="3" ><b style = "color:#4a5568">Inventory</b></th>'
	data+= '<th class="text-center" colspan="3" ><b style = "color:#4a5568">Supplier Cost</b></th>'
	data+= '<th class="text-center" colspan="3"><b style = "color:#4a5568">Total Cost</b></th>'
	data+='</tr>'
	data+= '</thead>'

	dat= []

	total_lab = 0
	total_inv = 0
	total_mat = 0
	sum_grand_total = 0
			
	for i in qu:
	

		dat.append(i.job_order_data)
		
		
		mc = frappe.db.sql(""" select sum(`tabItem Price Details`.amount) as mcost from `tabQuotation` left join 
		`tabItem Price Details` on `tabQuotation`.name = `tabItem Price Details`.parent 
		where `tabItem Price Details`.item_source = 'Supplier' and `tabItem Price Details`.job_order_data = '%s' and `tabItem Price Details`.parent = '%s' """ %(i.job_order_data,name) ,as_dict=1)
		
		inv = frappe.db.sql(""" select sum(`tabItem Price Details`.amount) as cost from `tabQuotation` left join 
		`tabItem Price Details` on `tabQuotation`.name = `tabItem Price Details`.parent 
		where `tabItem Price Details`.item_source = 'TSL Inventory' and `tabItem Price Details`.job_order_data = '%s' and `tabItem Price Details`.parent = '%s' """ %(i.job_order_data,name) ,as_dict=1)
		

		up = frappe.db.sql(""" select `tabQuotation Item`.rate as up,`tabQuotation Item`.net_amount as mar from `tabQuotation` left join 
		`tabQuotation Item` on `tabQuotation`.name =  `tabQuotation Item`.parent
		where  `tabQuotation Item`.job_order_data= '%s' and  `tabQuotation Item`.parent = '%s' """ %(i.job_order_data,name) ,as_dict=1)
		
		import re

		input_string = str(i.job_order_data)

		match = re.search(r'\d+$', input_string)
		if match:
			numeric_part = match.group()
		else:
			numeric_part = None

		total_price = i.get("total_price") or 0
		data+= '<tr>'
		data+= '<td class="text-center">%s</td>' %(numeric_part)
		data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>' %(f"{total_price:,.0f}")
		inv[0]['cost'] = (inv[0]['cost'] or 0)
		data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>' %(f"{inv[0]['cost']:,.0f}")
		mc[0]['mcost'] = (mc[0]['mcost'] or 0)
		frappe.log_error("MCOST", mc)
		data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>' %(f"{mc[0]['mcost']:,.0f}")
		data+= '<td class="text-center" colspan="3"><b style = "color:black">%s</b></td>' %(f"{inv[0]['cost'] + mc[0]['mcost'] + total_price:,.0f}") 
		data+= '</tr>'

		total_lab =  total_lab + round(total_price)
		total_inv =  total_inv + inv[0]['cost']
		total_mat = total_mat + mc[0]['mcost']
		sum_grand_total = sum_grand_total + (inv[0]['cost'] + mc[0]['mcost'] + total_price)
	
	for k in qi:
		if not k.job_order_data in dat:
			if k.job_order_data:
				up_1 = frappe.db.sql(""" select `tabQuotation Item`.rate as up,`tabQuotation Item`.net_amount as mar from `tabQuotation` left join 
				`tabQuotation Item` on `tabQuotation`.name =  `tabQuotation Item`.parent
				where  `tabQuotation Item`.job_order_data= '%s' and  `tabQuotation Item`.parent = '%s' """ %(k.job_order_data,name) ,as_dict=1)

				import re
				numeric_part = ""
				if k.job_order_data:
					input_string = k.job_order_data
					numeric_part = re.search(r'\d+$', input_string).group()

				data+= '<tr>'
				data+= '<td class="text-center" >%s</td>' %(numeric_part)
				data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>'%("0.00")
				data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>'%("0.00")
				data+= '<td class="text-center" colspan="3"><b style = "color:red">%s</b></td>'%("0.00")
				
				# if company == "TSL COMPANY - Kuwait":
				# 	data+= '<td class="text-center" colspan="2"><b style = "color:black">%s</b></td>' %(f"{round(up_1[0]['up'])-round(up_1[0]['mav']):,.2f}")
				# else:
				data+= '<td class="text-center" colspan="2"><b style = "color:black">%s</b></td>' %(f"{up_1[0]['mar']:,.2f}")
				data+= '</tr>'

	data+= '<tr>'
	data+= '<td class="text-center" ><b style = "color:#4a5568" >Total</b></td>'
	data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>'  %(f"{total_lab:,.0f}")
	data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold">%s</td>'  %(f"{total_inv:,.0f}")
	data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>' %(f"{total_mat:,.0f}")
	data+= '<td class="text-center" colspan="3" style = "color:black;font-weight:bold" >%s</td>' %(f"{round(sum_grand_total):,.0f}")


	if ship_cost:
		data+= '<tr>'
		data+= '<td class="text-center" ><b style = "color:#4a5568" ></b></td>'
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>'  %("")
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold">%s</td>'  %("")
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>' %("Shipping Cost")
		data+= '<td class="text-center" colspan="3" style = "color:red;font-weight:bold" >%s</td>' %(f"{round(ship_cost):,.0f}")
		data+='</tr>'

		data+= '<tr>'
		data+= '<td class="text-center" ><b style = "color:#4a5568" ></b></td>'
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>'  %("")
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold">%s</td>'  %("")
		data+= '<td class="text-center" colspan="3" style = "color:#4a5568;font-weight:bold" >%s</td>' %("Grand Total")
		data+= '<td class="text-center" colspan="3" style = "color:black;font-weight:bold" >%s</td>' %(f"{round(sum_grand_total + ship_cost):,.0f}")
		data+='</tr>'

	data+='</tr>'

	return data

@frappe.whitelist()
def get_invoice_details(name):
	ic = frappe.get_doc("Invoice Cancellation",name)
	data = ''
	if ic:
		for i in ic.cancellation_list:
			if i.invoice_no and not i.job_order_data:
				customer = frappe.get_value("Sales Invoice",i.invoice_no,"customer")
				company = frappe.get_value("Sales Invoice",i.invoice_no,"company")
				vat_applicable = frappe.db.get_value("Company",company,"vat_applicable")
				data = ""
				ogdate = datetime.strptime(str(ic.date),"%Y-%m-%d")
				formatted_date = ogdate.strftime("%d-%m-%Y")
				data+= '<table border = 1 width = 100% style = "border-collapse:collapse;font-size:9px"><tr>'
				data+= '<td colspan = 2 style = "border-right:hidden;text-align:left;font-weight:bold;"><b>Customer :</b></td>'
				if vat_applicable:
					data+= '<td colspan = 5 style = "border-right:hidden;text-align:left;">%s</td>' %(customer)
				else:
					data+= '<td colspan = 3 style = "border-right:hidden;text-align:left;">%s</td>' %(customer)
				data+= '<td colspan = 1 style = "border-right:hidden;text-align:right;font-weight:bold;"><b>Date :</b></td>'
				data+= '<td colspan = 2 style = "text-align:left;">%s</td>' %(formatted_date)
				data+= '</tr>'
	
	data+= '<tr>'
	data+= '<td style = "width:5%;text-align:center;font-weight:bold;padding:1px !important"><b>Sr</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Invoice No</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Invoice Date</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>JO / SO</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Model</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Mfg</b></td>'
	data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Amount</b></td>'
	if vat_applicable:
		data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>VAT</b></td>'
		data+= '<td style = "text-align:center;font-weight:bold;padding:1px !important"><b>Amount with VAT</b></td>'
	data+='</tr>'
	count = 0
	
	invoice_nos = []

	if ic.cancellation_list:
		for i in ic.cancellation_list:
			if i.invoice_no and i.invoice_no not in invoice_nos:
				invoice_nos.append(i.invoice_no)

	for i in invoice_nos:
		if i:
			sales_details = frappe.db.sql(""" select 
			`tabSales Invoice Item`.tax_amount,
			`tabSales Invoice`.posting_date as date,
			`tabSales Invoice Item`.total_amount,
			`tabSales Invoice`.name as name,
			`tabSales Invoice`.company,
			`tabSales Invoice Item`.job_order_data as jod,
			`tabSales Invoice Item`.supply_order_data as sod,
			IFNULL(`tabSales Invoice Item`.manufacturer, '-') AS mfg,
			`tabSales Invoice Item`.base_net_amount as amt,
			IFNULL(`tabItem Model`.model, '-') AS md  
			from `tabSales Invoice` 
			left join `tabSales Invoice Item` on `tabSales Invoice`.name = `tabSales Invoice Item`.parent
			left join `tabItem Model` on `tabSales Invoice Item`.model = `tabItem Model`.name
			where  `tabSales Invoice`.name = '%s' """ %(i),as_dict=1)
			for s in sales_details:
				count = count + 1
				data+= '<tr>'
				data+= '<td style = "text-align:center;">%s</td>' %(count)
				data+= '<td style = "text-align:center;">%s</td>' %(s.name or "")
				nv_date = datetime.strptime(str(s.date),"%Y-%m-%d")
				i_date = nv_date.strftime("%d-%m-%Y")
				data+= '<td style = "text-align:center;">%s</td>' %(i_date or "")
				data+= '<td style="text-align:center;">%s</td>'   %(s.jod or s.sod or '-')
				data+= '<td style = "text-align:center;">%s</td>' %(s.md)
				data+= '<td style = "text-align:center;">%s</td>' %(s.mfg)
				data+= '<td style = "text-align:center;">%s</td>'  % (f"{s.amt or 0:,.2f}")
				if vat_applicable:
					data+= '<td style = "text-align:center;">%s</td>'  % (f"{s.tax_amount or 0:,.2f}")
					data+= '<td style = "text-align:center;">%s</td>'  % (f"{s.total_amount or 0:,.2f}")
				data+='</tr>'

	return data


@frappe.whitelist()
def get_pi1(doc):
	# posting_date,name,party_name,amount_in,total_allocated_amount,currency_paid,cost_center,references,remarks,company
	data = ""
	data+= '<tr><td colspan = 6><center><b style = "color:blue !important;font-size:15px">%s</b></center></td></tr>' %(doc.company)
	data+= '<tr><td colspan = 2><center><b style = "color:red !important">PAYMENT TRANSFER APPROVAL FORM</b></center></td></tr>'
	data+= '<tr><td>Date</td><td>%s</td></tr>' %(doc.get_formatted("posting_date"))
	data+='<tr><td>REF NO</td><td>%s</td></tr>' %(doc.name)
	data+='<tr>  <td>Supplier Name</td><td>%s</td></tr>' %(doc.party_name)
	data+='<tr> <td>Amount</td><td>%s</td></tr>' %("{:,.2f}".format(doc.total_allocated_amount))
	data+='<tr><td>Currency</td><td>%s</td></tr>' %(doc.paid_from_account_currency)
	data+='<tr><td>Department</td><td>%s</td></tr>' %(doc.cost_center)
	data+='<tr><td >Remarks</td><td>%s</td></tr>' %(doc.remarks or "")

	for i in doc.references:

		if i.reference_doctype == "Purchase Invoice" or i.reference_doctype == "Purchase Order":

			cr = ""
			pat = ""
			conv_amt = 0

			cur = frappe.get_value("Company",{"name":doc.company},"default_currency")

			if i.reference_doctype == "Purchase Invoice":
				pat = frappe.get_value("Purchase Invoice",{"name":i.reference_name},"supplier_invoice_attach")
				cr = frappe.get_value("Purchase Invoice",{"name":i.reference_name},"currency")
				conv_amt = frappe.get_value("Purchase Invoice",{"name":i.reference_name},"grand_total")

			if i.reference_doctype == "Purchase Order":
				pat = frappe.get_value("Purchase Order",{"name":i.reference_name},"supplier_invoice_attach")
				cr = frappe.get_value("Purchase Order",{"name":i.reference_name},"currency")
				conv_amt = frappe.get_value("Purchase Order",{"name":i.reference_name},"grand_total")

			pi = frappe.db.sql("""
				select DISTINCT 
				`tabPurchase Invoice`.name as p,
				`tabPurchase Invoice Item`.job_order_data as jo,
				`tabPurchase Invoice Item`.supply_order_data as so
				from `tabPurchase Invoice` 
				left join `tabPurchase Invoice Item`
				on `tabPurchase Invoice`.name = `tabPurchase Invoice Item`.parent
				where `tabPurchase Invoice`.name = %s
			""",(i.reference_name),as_dict=1)

			po = frappe.db.sql("""
				select DISTINCT 
				`tabPurchase Order`.name as p,
				`tabPurchase Order Item`.job_order_data as jo,
				`tabPurchase Order Item`.supply_order_data as so
				from `tabPurchase Order`
				left join `tabPurchase Order Item`
				on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
				where `tabPurchase Order`.name = %s
			""",(i.reference_name),as_dict=1)

			if i.reference_doctype == "Purchase Invoice":
				data+='<tr><td>Attached Document</td><td><b>%s - (Outstanding - %s %s)</b>/<a href="%s" target="_blank"><u><b style="color:red !important"><br>Supplier Invoice Link</b></u></a></td></tr>'%(i.reference_name,f"{round(conv_amt,2):,.2f}",cr,pat)

			if i.reference_doctype == "Purchase Order":
				data+='<tr><td>Attached Document</td><td><b>%s - (Outstanding - %s %s)</b>/<a href="%s" target="_blank"><u><b style="color:red !important"><br>Supplier Invoice Link</b></u></a></td></tr>'%(i.reference_name,f"{round(conv_amt,2):,.2f}",cr,pat)

			wo_so_links = []

			for j in pi:
				if j["jo"]:
					wo_so_links.append(j["jo"])
				if j["so"]:
					wo_so_links.append(j["so"])

			for j in po:
				if j["jo"]:
					wo_so_links.append(j["jo"])
				if j["so"]:
					wo_so_links.append(j["so"])

			# -------- FORMAT WOD/SOD/SCV ----------
			
			formatted = {}
			for val in wo_so_links:
				if val:
					parts = val.split("-")
					if len(parts) >= 3:
						prefix = parts[0]
						number = parts[-1]

						if prefix not in formatted:
							formatted[prefix] = []

						formatted[prefix].append(number)

			final_links = []
			for k,v in formatted.items():
				final_links.append(f",".join(v))

			if final_links:
				frappe.log_error("final_links",final_links)
				data += "<tr><td></td><td>%s</td></tr>" % ", ".join(final_links)

		if i.reference_doctype == "Journal Entry":
			je_attach = frappe.get_value("Journal Entry",{"name":i.reference_name},"attach")
			data+='<tr><td>Attached With Supporting Document</td><td><b>%s</b>/ <a href="%s"><u><b style="color:red !important">Journal Entry Attachment</b></u></a></td></tr>'%(i.reference_name,je_attach)

	return data


import frappe
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from frappe.utils import getdate, flt

@frappe.whitelist()
def get_sales_ksa(company, branch):
	"""
	Main function to generate sales report for KSA branches
	"""
	try:
		now = datetime.now()
		formatted_date = now.strftime("%d-%m-%Y")

		months = get_last_twelve_months(now)
		salespersons = get_salespersons_by_branch(company, branch)

		if not salespersons:
			return "<div style='color:red; padding:20px;'>No active salespersons found for this branch.</div>"

		html = []
		
		# ===== Header with Logo and Flag =====
		html.append(build_header(branch, formatted_date))
		
		# Get all data in bulk for better performance
		all_sales_data = get_bulk_sales_data(salespersons, months)
		
		# Calculate cumulative totals
		cum_totals = calculate_cumulative_totals(all_sales_data)
		
		# ===== Add Cumulative Table after Header =====
		html.append(render_cumulative_section(
			cum_totals['quoted_wo'], cum_totals['approved_wo'], 
			cum_totals['percent_wo'], cum_totals['avg_days_wo'],
			cum_totals['quoted_so'], cum_totals['approved_so'], 
			cum_totals['percent_so'], cum_totals['avg_days_so']
		))
		
		# Generate individual salesperson tables using pre-fetched data
		for user_id in salespersons:
			try:
				salesperson_name = frappe.db.get_value("Sales Person", {"custom_user": user_id}, "name")
				if salesperson_name:
					salesperson_html = build_salesperson_table_optimized(
						salesperson_name, user_id, months, all_sales_data
					)
					html.append(salesperson_html)
			except Exception as e:
				frappe.log_error(f"Error processing salesperson {user_id}: {str(e)}", "Sales Report Error")
				continue
		
		return "\n".join(html)
		
	except Exception as e:
		frappe.log_error(f"Error in get_sales_ksa: {str(e)}", "Sales Report Error")
		return f"<div style='color:red; padding:20px;'>Error generating report: {str(e)}</div>"

def get_bulk_sales_data(salespersons, months):
	"""
	Fetch all sales data in bulk with optimized queries
	"""
	all_data = {}
	
	# Prepare date ranges
	date_ranges = []
	for m in months:
		date_ranges.append({
			'from_date': m["first_day"].date(),
			'to_date': m["last_day"].date(),
			'month_name': m['month_name'],
			'month_num': m['month_number']
		})
	
	# Fetch data for each salesperson
	for user_id in salespersons:
		if not user_id:
			continue
			
		all_data[user_id] = {}
		
		# Get WOD data
		wod_data = get_bulk_wod_data(user_id, date_ranges)
		
		# Get SOD data
		sod_data = get_bulk_sod_data(user_id, date_ranges)
		
		# Organize by month
		for i, dr in enumerate(date_ranges):
			month_key = f"{dr['month_name']}_{dr['month_num']}"
			
			wod_month = wod_data[i] if i < len(wod_data) else {}
			sod_month = sod_data[i] if i < len(sod_data) else {}
			
			all_data[user_id][month_key] = {
				'quoted_wo': flt(wod_month.get('quoted', 0)),
				'approved_wo': flt(wod_month.get('approved', 0)),
				'wo_days': int(wod_month.get('days', 0)),
				'wo_count': int(wod_month.get('count', 0)),
				'quoted_so': flt(sod_month.get('quoted', 0)),
				'approved_so': flt(sod_month.get('approved', 0)),
				'so_days': int(sod_month.get('days', 0)),
				'so_count': int(sod_month.get('count', 0)),
			}
	
	return all_data

def get_bulk_wod_data(sales_person, date_ranges):
	"""
	Get WOD data for all months in a single optimized query
	"""
	if not date_ranges or not sales_person:
		return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in range(len(date_ranges))]
	
	try:
		conditions = []
		params = []
		
		for i, dr in enumerate(date_ranges):
			conditions.append(f"""
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.workflow_state = 'Approved By Customer' 
						THEN COALESCE(qi.net_amount, 0) + COALESCE(qi.tax_amount, 0) 
					ELSE 0 END) as approved_{i},
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.quotation_type = 'Customer Quotation - Repair' 
						THEN COALESCE(qi.net_amount, 0) + COALESCE(qi.tax_amount, 0) 
					ELSE 0 END) as quoted_{i},
				COUNT(DISTINCT CASE WHEN q.transaction_date BETWEEN %s AND %s 
									AND q.workflow_state = 'Approved By Customer' 
									THEN qi.job_order_data END) as count_{i},
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.workflow_state = 'Approved By Customer' 
						AND q.approval_date IS NOT NULL 
						AND q.transaction_date IS NOT NULL
						THEN DATEDIFF(q.approval_date, q.transaction_date) 
					ELSE 0 END) as days_{i}
			""")
			
			# Add parameters for this month (2 params per condition × 4 conditions = 8 params)
			params.extend([dr['from_date'], dr['to_date']] * 4)
		
		query = f"""
			SELECT 
				{','.join(conditions)}
			FROM `tabQuotation` q
			LEFT JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Repair', 'Revised Quotation - Repair')
		"""
		
		# Add sales_person parameter
		params.append(sales_person)
		
		result = frappe.db.sql(query, tuple(params), as_dict=True)
		
		if not result or not result[0]:
			return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in date_ranges]
		
		# Process results
		monthly_data = []
		row = result[0]
		
		for i in range(len(date_ranges)):
			approved = flt(row.get(f'approved_{i}', 0))
			quoted = flt(row.get(f'quoted_{i}', 0))
			count = int(row.get(f'count_{i}', 0) or 0)
			days = int(row.get(f'days_{i}', 0) or 0)
			
			avg_days = round(days / count) if count > 0 else 0
			
			monthly_data.append({
				'quoted': quoted,
				'approved': approved,
				'days': avg_days,
				'count': count
			})
		
		return monthly_data
		
	except Exception as e:
		frappe.log_error(f"Error in get_bulk_wod_data for {sales_person}: {str(e)}", "WOD Data Error")
		return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in date_ranges]

def get_bulk_sod_data(sales_person, date_ranges):
	"""
	Get SOD data for all months in a single optimized query
	"""
	if not date_ranges or not sales_person:
		return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in range(len(date_ranges))]
	
	try:
		conditions = []
		params = []
		
		for i, dr in enumerate(date_ranges):
			conditions.append(f"""
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.workflow_state = 'Approved By Customer' 
						THEN COALESCE(qi.net_amount, 0) + COALESCE(qi.tax_amount, 0) 
					ELSE 0 END) as approved_{i},
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.quotation_type = 'Customer Quotation - Supply' 
						THEN COALESCE(qi.net_amount, 0) + COALESCE(qi.tax_amount, 0) 
					ELSE 0 END) as quoted_{i},
				COUNT(DISTINCT CASE WHEN q.transaction_date BETWEEN %s AND %s 
									AND q.workflow_state = 'Approved By Customer' 
									THEN qi.supply_order_data END) as count_{i},
				SUM(CASE WHEN q.transaction_date BETWEEN %s AND %s 
						AND q.workflow_state = 'Approved By Customer' 
						AND q.approval_date IS NOT NULL 
						AND q.transaction_date IS NOT NULL
						THEN DATEDIFF(q.approval_date, q.transaction_date) 
					ELSE 0 END) as days_{i}
			""")
			
			# Add parameters for this month
			params.extend([dr['from_date'], dr['to_date']] * 4)
		
		query = f"""
			SELECT 
				{','.join(conditions)}
			FROM `tabQuotation` q
			LEFT JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Supply', 'Revised Quotation - Supply')
		"""
		
		# Add sales_person parameter
		params.append(sales_person)
		
		result = frappe.db.sql(query, tuple(params), as_dict=True)
		
		if not result or not result[0]:
			return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in date_ranges]
		
		# Process results
		monthly_data = []
		row = result[0]
		
		for i in range(len(date_ranges)):
			approved = flt(row.get(f'approved_{i}', 0))
			quoted = flt(row.get(f'quoted_{i}', 0))
			count = int(row.get(f'count_{i}', 0) or 0)
			days = int(row.get(f'days_{i}', 0) or 0)
			
			avg_days = round(days / count) if count > 0 else 0
			
			monthly_data.append({
				'quoted': quoted,
				'approved': approved,
				'days': avg_days,
				'count': count
			})
		
		return monthly_data
		
	except Exception as e:
		frappe.log_error(f"Error in get_bulk_sod_data for {sales_person}: {str(e)}", "SOD Data Error")
		return [{'quoted': 0, 'approved': 0, 'days': 0, 'count': 0} for _ in date_ranges]

def calculate_cumulative_totals(all_data):
	"""
	Calculate cumulative totals from bulk data
	"""
	cum_quoted_wo = cum_approved_wo = cum_quoted_so = cum_approved_so = 0
	cum_wo_days = cum_so_days = 0
	cum_wo_count = cum_so_count = 0
	
	for user_id, months_data in all_data.items():
		for month_key, data in months_data.items():
			cum_quoted_wo += data.get('quoted_wo', 0)
			cum_approved_wo += data.get('approved_wo', 0)
			cum_quoted_so += data.get('quoted_so', 0)
			cum_approved_so += data.get('approved_so', 0)
			cum_wo_days += data.get('wo_days', 0) * data.get('wo_count', 0)
			cum_so_days += data.get('so_days', 0) * data.get('so_count', 0)
			cum_wo_count += data.get('wo_count', 0)
			cum_so_count += data.get('so_count', 0)
	
	cum_wo_percent = round((cum_approved_wo / cum_quoted_wo) * 100) if cum_quoted_wo else 0
	cum_so_percent = round((cum_approved_so / cum_quoted_so) * 100) if cum_quoted_so else 0
	avg_wo_days = round(cum_wo_days / cum_wo_count) if cum_wo_count > 0 else 0
	avg_so_days = round(cum_so_days / cum_so_count) if cum_so_count > 0 else 0
	
	return {
		'quoted_wo': cum_quoted_wo,
		'approved_wo': cum_approved_wo,
		'percent_wo': cum_wo_percent,
		'avg_days_wo': avg_wo_days,
		'quoted_so': cum_quoted_so,
		'approved_so': cum_approved_so,
		'percent_so': cum_so_percent,
		'avg_days_so': avg_so_days
	}

def build_salesperson_table_optimized(salesperson_name, sales_user, months, all_data):
	"""
	Generate optimized salesperson table using pre-fetched data
	"""
	try:
		rows = []
		total_q1 = total_q2 = total_q3 = total_q4 = wo_days_total = so_days_total = 0
		wo_count_total = so_count_total = 0

		# Table header
		rows.append(f"""
		<tr style="background-color:#0e86d4; border-color:#000000;">
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Sales</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Quoted Month</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Quoted</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Approved</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">% of Approved</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Approval Days</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Quoted</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Approved</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">% Approved</td>
			<td style="font-weight:bold; text-align:center; color:white; font-size:10px; width:10%;">Approval Days</td>
		</tr>
		""")

		# Monthly data rows
		for m in months:
			month_key = f"{m['month_name']}_{m['month_number']}"
			data = all_data.get(sales_user, {}).get(month_key, {})
			
			quoted = flt(data.get('quoted_wo', 0))
			approved = flt(data.get('approved_wo', 0))
			quoted2 = flt(data.get('quoted_so', 0))
			approved2 = flt(data.get('approved_so', 0))
			wod_days = int(data.get('wo_days', 0))
			sod_days = int(data.get('so_days', 0))
			wo_count = int(data.get('wo_count', 0))
			so_count = int(data.get('so_count', 0))

			# Update totals
			total_q1 += quoted
			total_q2 += approved
			total_q3 += quoted2
			total_q4 += approved2
			wo_days_total += wod_days * wo_count if wo_count > 0 else 0
			so_days_total += sod_days * so_count if so_count > 0 else 0
			wo_count_total += wo_count
			so_count_total += so_count

			# Calculate percentages
			percent = round((approved / quoted) * 100) if quoted else 0
			percent2 = round((approved2 / quoted2) * 100) if quoted2 else 0

			# Get colors
			color1 = get_color(percent)
			color2 = get_color(percent2)

			# Format numbers with thousand separators
			quoted_str = f"{round(quoted):,}" if quoted else "0"
			approved_str = f"{round(approved):,}" if approved else "0"
			quoted2_str = f"{round(quoted2):,}" if quoted2 else "0"
			approved2_str = f"{round(approved2):,}" if approved2 else "0"

			rows.append(f"""
			<tr>
				<td style="text-align:center; border-bottom:hidden;">{salesperson_name if m['month_number'] == 6 else ''}</td>
				<td>{m['month_name']}</td>
				<td>{quoted_str}</td>
				<td>{approved_str}</td>
				<td style="background-color:{color1};"><b>{percent}%</b></td>
				<td><b>{wod_days}</b></td>
				<td>{quoted2_str}</td>
				<td>{approved2_str}</td>
				<td style="background-color:{color2};"><b>{percent2}%</b></td>
				<td><b>{sod_days}</b></td>
			</tr>
			""")

		# Calculate totals row
		pct_total = round((total_q2 / total_q1) * 100) if total_q1 else 0
		pct_total2 = round((total_q4 / total_q3) * 100) if total_q3 else 0

		color = get_color(pct_total)
		color2 = get_color(pct_total2)

		avg_wo_days = round(wo_days_total / wo_count_total) if wo_count_total > 0 else 0
		avg_so_days = round(so_days_total / so_count_total) if so_count_total > 0 else 0

		# Format total numbers
		total_q1_str = f"{round(total_q1):,}" if total_q1 else "0"
		total_q2_str = f"{round(total_q2):,}" if total_q2 else "0"
		total_q3_str = f"{round(total_q3):,}" if total_q3 else "0"
		total_q4_str = f"{round(total_q4):,}" if total_q4 else "0"

		rows.append(f"""
		<tr style="font-weight:bold;">
			<td></td>
			<td>Total</td>
			<td style="background-color:#D3D3D3;">{total_q1_str}</td>
			<td style="background-color:#D3D3D3;">{total_q2_str}</td>
			<td style="background-color:{color};">{pct_total}%</td>
			<td style="background-color:#D3D3D3;"><b>{avg_wo_days}</b></td>
			<td style="background-color:#D3D3D3;">{total_q3_str}</td>
			<td style="background-color:#D3D3D3;">{total_q4_str}</td>
			<td style="background-color:{color2};">{pct_total2}%</td>
			<td style="background-color:#D3D3D3;"><b>{avg_so_days}</b></td>
		</tr>
		<tr><td colspan="10" style="text-align:center;">-</td></tr>
		""")

		return "<table border='1' style='text-align:center; border-color:#000000; width:100%; border-collapse:collapse; margin-bottom:10px;'>" + "\n".join(rows) + "</table>"
		
	except Exception as e:
		frappe.log_error(f"Error building table for {salesperson_name}: {str(e)}", "Table Build Error")
		return f"<div style='color:red;'>Error loading data for {salesperson_name}</div>"

# ==================== Helper Functions ====================

def get_last_twelve_months(now):
	"""Get last 12 months with first and last days"""
	months = []
	for i in range(11, -1, -1):
		dt = now - relativedelta(months=i)
		first_day = dt.replace(day=1)
		last_day = dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])
		months.append({
			"month_name": dt.strftime("%B"),
			"month_number": dt.month,
			"year": dt.year,
			"first_day": first_day,
			"last_day": last_day,
		})
	return months

def get_salespersons_by_branch(company, branch):
	"""Get active salespersons for a branch"""
	try:
		# result = frappe.db.sql("""
		#     SELECT DISTINCT sp.user
		#     FROM `tabSales Person` sp
		#     INNER JOIN `tabEmployee` e ON e.user_id = sp.user
		#     WHERE sp.company = %s 
		#       AND e.status = 'Active' 
		#       AND e.branch = %s
		#       AND sp.user IS NOT NULL
		#       AND sp.user != ''
		# """, (company, branch), as_dict=True)
		
		# return [r.user for r in result if r.get('user')]
		return ["Yazeed","Jubil"]
	except Exception as e:
		frappe.log_error(f"Error fetching salespersons: {str(e)}", "Salespersons Error")
		return []

def build_header(branch, date_str):
	"""Build report header with logo and branch info"""
	branch_labels = {
		"Riyadh - TSL- KSA": "Riyadh",
		"Jeddah - TSL-SA": "Jeddah"
	}
	branch_label = branch_labels.get(branch, "Dammam")
	
	logo_path = ""
	flag_path = ""
	
	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td style="width:30%; border-color:#000000;"><img src="{logo_path}" width="220"></td>
			<td style="width:40%; border-color:#000000; color:#055c9d; font-size:16px; font-weight:bold; text-align:center;">
				TSL Company<br>WO & SO Approval Percentage by Amount
			</td>
			<td style="width:30%; border-color:#000000;">
				<center><img src="{flag_path}" width="120" height="90"></center>
			</td>
		</tr>
	</table>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td align="left" style="width:30%; border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Branch - {branch_label}
			</td>
			<td align="center" style="width:40%; border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Currency - SAR
			</td>
			<td align="right" style="width:30%; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Generation Date: {date_str}
			</td>
		</tr>
	</table>
	"""

def render_cumulative_section(q_wo, a_wo, p_wo, d_wo, q_so, a_so, p_so, d_so):
	"""Render cumulative summary section"""
	color_wo = get_color(p_wo)
	color_so = get_color(p_so)
	
	# Format numbers
	q_wo_str = f"{q_wo:,.0f}" if q_wo else "0"
	a_wo_str = f"{a_wo:,.0f}" if a_wo else "0"
	q_so_str = f"{q_so:,.0f}" if q_so else "0"
	a_so_str = f"{a_so:,.0f}" if a_so else "0"
	
	return f"""
	<br>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td colspan="10" align="center" style="background-color:#0e86d4; color:white; font-size:14px; font-weight:bold; padding:8px;">
				CUMULATIVE SUMMARY
			</td>
		</tr>
		<tr style="background-color:#145da0; color:white; font-weight:bold;">
			<td colspan="3" style="text-align:center; padding:8px; font-size:12px; border-right:1px solid white;color:white;">WORK ORDER</td>
			<td colspan="3" style="text-align:center; padding:8px; font-size:12px;color:white;">SUPPLY ORDER</td>
		</tr>
		<tr style="background-color:#f0f0f0; font-weight:bold;">
			<td style="padding:8px; text-align:center; font-size:11px;">Quoted (SAR)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Approved (SAR)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">% Approved</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Quoted (SAR)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Approved (SAR)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">% Approved</td>
		</tr>
		<tr style="font-size:14px;">
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{q_wo_str}</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{a_wo_str}</td>
			<td style="padding:10px; text-align:center; background-color:{color_wo}; font-weight:bold;">{p_wo}%</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{q_so_str}</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{a_so_str}</td>
			<td style="padding:10px; text-align:center; background-color:{color_so}; font-weight:bold;">{p_so}%</td>
		</tr>
	</table>
	<br>
	"""

def get_color(percentage):
	"""Return color based on percentage"""
	if percentage < 60:
		return "#FF7074"  # Red
	elif percentage < 80:
		return "#FFFF8F"  # Yellow
	else:
		return "#98FB98"  # Green

# Remove old unused functions to avoid confusion
# def calculate_salesperson_totals - Removed
# def build_salesperson_table - Removed  
# def get_monthly_amounts_exact_logic - Removed
# def render_header2 - Removed (unused)
# def render_table_header2 - Removed (unused)