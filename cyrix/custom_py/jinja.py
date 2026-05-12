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
def get_pi(doc):
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
import calendar
from frappe.utils import getdate

@frappe.whitelist()
def get_sales(company, branch):
	try:
		today = datetime.now().date()
		formatted_date = today.strftime("%d-%m-%Y")
		current_year = today.year

		months = list(calendar.month_name)[1:]
		current_month = today.month
		last_12_months = [
			(months[(current_month - i - 1) % 12],
			 (current_year if current_month - i > 0 else current_year - 1))
			for i in range(11, -1, -1)
		]

		sales_people = frappe.get_all(
		"Sales Person",
		filters={"name": ["!=", "Sales Team"],"custom_branch":branch}
		)

		# target_sales = {
		#     "Cyrix TSL - Kuwait": [
		#         "Yazeed", "Jubil"
				
		#     ]
		# }

		html = []

		# ===== Header with Logo and Flag =====
		html.append(render_header(company, formatted_date))
		
		# ===== Initialize cumulative totals =====
		total_quoted_wo = 0
		total_approved_wo = 0
		total_days_wo = 0
		total_quoted_so = 0
		total_approved_so = 0
		total_days_so = 0
		wo_count_total = 0
		so_count_total = 0

		# First pass: Calculate cumulative totals
		for sp in sales_people:
			# if sp.name not in target_sales.get(company, []):
			#     continue

			# Get totals for this salesperson
			totals = calculate_salesperson_totals(sp, company, last_12_months)
			
			total_quoted_wo += totals.get('quoted_wo', 0)
			total_approved_wo += totals.get('approved_wo', 0)
			total_days_wo += totals.get('days_wo', 0)
			total_quoted_so += totals.get('quoted_so', 0)
			total_approved_so += totals.get('approved_so', 0)
			total_days_so += totals.get('days_so', 0)
			wo_count_total += totals.get('wo_count', 0)
			so_count_total += totals.get('so_count', 0)

		# Calculate cumulative percentages and averages
		total_per_wo = (total_approved_wo / total_quoted_wo * 100) if total_quoted_wo else 0
		total_per_so = (total_approved_so / total_quoted_so * 100) if total_quoted_so else 0
		avg_days_wo = round(total_days_wo / wo_count_total) if wo_count_total > 0 else 0
		avg_days_so = round(total_days_so / so_count_total) if so_count_total > 0 else 0

		# ===== Add Cumulative Table after Header =====
		html.append(render_cumulative_table(
			total_quoted_wo, total_approved_wo, total_per_wo, avg_days_wo,
			total_quoted_so, total_approved_so, total_per_so, avg_days_so
		))

		# ===== Main Table Header =====
		html.append(render_table_header(company))

		# Reset totals for display in main table
		total_quoted_wo = 0
		total_approved_wo = 0
		total_days_wo = 0
		total_quoted_so = 0
		total_approved_so = 0
		total_days_so = 0

		# Second pass: Generate individual salesperson rows
		for sp in sales_people:
			# if sp.name not in target_sales.get(company, []):
			#     continue

			# Generate rows and collect data
			rows_result = generate_salesperson_rows(sp, company, last_12_months)
			if rows_result and len(rows_result) > 1:
				html.extend(rows_result[0])  # HTML rows
				
				# Get totals from the second return value
				if len(rows_result) > 1:
					totals = rows_result[1]
					total_quoted_wo += totals.get('quoted_wo', 0)
					total_approved_wo += totals.get('approved_wo', 0)
					total_days_wo += totals.get('days_wo', 0)
					total_quoted_so += totals.get('quoted_so', 0)
					total_approved_so += totals.get('approved_so', 0)
					total_days_so += totals.get('days_so', 0)

		# Calculate percentages for main table
		total_per_wo = (total_approved_wo / total_quoted_wo * 100) if total_quoted_wo else 0
		total_per_so = (total_approved_so / total_quoted_so * 100) if total_quoted_so else 0

		html.append("</table>")

		# ===== Second Section =====
		# html.append(render_header2(company, formatted_date))
		# html.append(render_table_header2(company))
		
		# # ===== Total Row =====
		# html.append(f"""
		# <tr style="font-weight:bold;background-color:#f2f2f2">
		#     <td style="background-color:#D3D3D3"><center>{total_quoted_wo:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{total_approved_wo:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{round(total_per_wo)}%</center></td>
		#     <td style="background-color:#D3D3D3"><center>{total_quoted_so:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{total_approved_so:,.0f}</center></td>
		#     <td style="background-color:#D3D3D3"><center>{round(total_per_so)}%</center></td>
		# </tr>
		# """)
		# html.append("</table>")

		return "".join(html)
	except Exception as e:
		frappe.log_error(f"Error in get_sales_kuwait: {str(e)}", "Sales Report Error")
		return f"<div style='color:red; padding:20px;'>Error generating report: {str(e)}</div>"

def calculate_salesperson_totals(sp, company, months):
	"""Calculate totals for a salesperson without generating HTML."""
	try:
		total_quoted = 0
		total_approved = 0
		total_quoted2 = 0
		total_approved2 = 0
		total_days_wo = 0
		total_days_so = 0
		wo_count = 0
		so_count = 0


		for month_name, year in months:
			try:
				month_num = datetime.strptime(month_name, "%B").month
				first_day = datetime(year, month_num, 1).date()
				last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

				quoted, approved, quoted2, approved2, wod_hrs, sod_hrs = get_monthly_sales(
					sp.name, first_day, last_day, company
				)

				total_quoted += quoted or 0
				total_approved += approved or 0
				total_quoted2 += quoted2 or 0
				total_approved2 += approved2 or 0
				total_days_wo += wod_hrs or 0
				total_days_so += sod_hrs or 0
				
				if wod_hrs > 0:
					wo_count += 1
				if sod_hrs > 0:
					so_count += 1

			except Exception as e:
				frappe.log_error(f"Error in calculate_salesperson_totals for {sp.name}: {str(e)}", "Totals Calculation Error")
				continue

		return {
			'quoted_wo': total_quoted,
			'approved_wo': total_approved,
			'days_wo': total_days_wo,
			'quoted_so': total_quoted2,
			'approved_so': total_approved2,
			'days_so': total_days_so,
			'wo_count': wo_count,
			'so_count': so_count
		}
	except Exception as e:
		frappe.log_error(f"Error in calculate_salesperson_totals for {sp.name}: {str(e)}", "Totals Calculation Error")
		return {}

def render_cumulative_table(q_wo, a_wo, p_wo, d_wo, q_so, a_so, p_so, d_so):
	"""Render the cumulative summary table."""
	
	# Determine colors based on percentages
	color_wo = get_color(p_wo)
	color_so = get_color(p_so)
	
	return f"""
	<br>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse; margin-top:10px;">
		<tr>
			<td colspan="10" align="center" style="background-color:#0e86d4; color:white; font-size:14px; font-weight:bold; padding:8px;">
				CUMULATIVE SUMMARY
			</td>
		</tr>
		<tr style="background-color:#145da0; color:white; font-weight:bold;">
			<td colspan="3" style="text-align:center; padding:8px; font-size:12px; border-right:1px solid white;color:white;">JOB ORDER</td>
			<td colspan="3" style="text-align:center; padding:8px; font-size:12px;color:white">SUPPLY ORDER</td>
		</tr>
		<tr style="background-color:#f0f0f0; font-weight:bold;">
			<td style="padding:8px; text-align:center; font-size:11px;">Quoted (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Approved (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">% Approved</td>
			
			
			<td style="padding:8px; text-align:center; font-size:11px;">Quoted (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">Approved (KWD)</td>
			<td style="padding:8px; text-align:center; font-size:11px;">% Approved</td>
			
		</tr>
		<tr style="font-size:14px;">
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{q_wo:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{a_wo:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:{color_wo}; font-weight:bold;">{round(p_wo)}%</td>
		  
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{q_so:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:#D3D3D3; font-weight:bold;">{a_so:,.0f}</td>
			<td style="padding:10px; text-align:center; background-color:{color_so}; font-weight:bold;">{round(p_so)}%</td>
			
		</tr>
	</table>
	<br>
	"""

def render_header(company, formatted_date):
	"""Generate the report header HTML."""
	logo_path = "/files/Cyrix Logo.png"
	country_label = "Kuwait" if "Kuwait" in company else "UAE"

	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td style="width:30%; border-color:#000000;"><img src="{logo_path}" width="200"></td>
			<td style="width:40%; border-color:#000000; font-size:16px; color:#055c9d; text-align:center; font-weight:bold;">
				<br>TSL Company<br>JO & SO Approval Percentage by Amount
			</td>
			<td style="width:30%; border-color:#000000;">
				<center><img src="/files/kuwait flag.jpg" width="140" height="80"></center>
			</td>
		</tr>
	</table>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td align="left" style="width:30%;border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Branch - {country_label}
			</td>
			<td align="center" style="width:40%;border-right:hidden; border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Currency - KWD
			</td>
			<td align="right" style="width:30%;border-color:#000000; background-color:#0e86d4; color:white; font-size:12px; font-weight:bold;">
				Generation Date: {formatted_date}
			</td>
		</tr> 
	</table>
	"""

def render_header2(company, formatted_date):
	"""Generate the report header HTML."""
	return f"""
	<br>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td colspan="7" align="center" style="border-color:#000000; background-color:#0e86d4; color:white; font-size:14px; font-weight:bold;">
				CUMULATIVE SUMMARY
			</td>
		</tr> 
	</table>
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
	"""

def render_table_header(company):
	"""Render the table column headers depending on company."""
	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse; margin-top:10px;">
		<tr>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%"></td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%"></td>
			<td colspan="4" style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;">JOB ORDER</td>
			<td colspan="4" style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;">SUPPLY ORDER</td>
		</tr>
		<tr>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Sales</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Quoted Month</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Quoted</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">% of Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Approval Days</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Quoted</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">% of Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:10px; text-align:center;" width="10%">Approval Days</td>
		</tr>
	"""

def render_table_header2(company):
	"""Render the table column headers depending on company."""
	return f"""
	<table border="1" width="100%" style="border-color:#000000; border-collapse:collapse;">
		<tr>
			<td colspan="3" style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;">JOB ORDER</td>
			<td colspan="4" style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;">SUPPLY ORDER</td>
		</tr>
		<tr>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Quoted</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Approved</td>
			<td style="background-color:#145da0; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">% of Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Quoted</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">Approved</td>
			<td style="background-color:#0e86d4; color:white; font-weight:bold; font-size:12px; text-align:center;" width="12%">% of Approved</td>
		</tr>
	"""

def generate_salesperson_rows(sp, company, months):
	"""Generate monthly sales data for a single salesperson."""
	try:
		rows = []
		total_quoted = 0
		total_approved = 0
		total_quoted2 = 0
		total_approved2 = 0
		total_days_wo = 0
		total_days_so = 0
		wo_count = 0
		so_count = 0

		for month_name, year in months:
			try:
				month_num = datetime.strptime(month_name, "%B").month
				first_day = datetime(year, month_num, 1).date()
				last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

				quoted, approved, quoted2, approved2, wod_hrs, sod_hrs = get_monthly_sales(
					sp.name, first_day, last_day, company
				)

				total_quoted += quoted or 0
				total_approved += approved or 0
				total_quoted2 += quoted2 or 0
				total_approved2 += approved2 or 0
				total_days_wo += wod_hrs or 0
				total_days_so += sod_hrs or 0
				
				if wod_hrs > 0:
					wo_count += 1
				if sod_hrs > 0:
					so_count += 1

				# Calculate percentages
				percent1 = round((approved / quoted) * 100) if quoted and quoted > 0 else 0
				percent2 = round((approved2 / quoted2) * 100) if quoted2 and quoted2 > 0 else 0

				# Set colors based on percentages
				color4 = get_color(percent1)
				color3 = get_color(percent2)

				rows.append(f"""
				<tr>
					<td style="text-align:center; border-bottom:hidden; color:#145da0; font-weight:bold;">{sp.name if month_name == "June" else ''}</td>
					<td style="font-size:10px; text-align:center; font-weight:bold;">{month_name}</td>
					<td style="font-size:10px; text-align:center;">{quoted:,.0f}</td>
					<td style="font-size:10px; text-align:center;">{approved:,.0f}</td>
					<td style="font-size:10px; text-align:center; background-color:{color4}; font-weight:bold;">{percent1}%</td>
					<td style="font-size:10px; text-align:center;">{wod_hrs}</td>
					<td style="font-size:10px; text-align:center;">{quoted2:,.0f}</td>
					<td style="font-size:10px; text-align:center;">{approved2:,.0f}</td>
					<td style="font-size:10px; text-align:center; background-color:{color3}; font-weight:bold;">{percent2}%</td>
					<td style="font-size:10px; text-align:center;">{sod_hrs}</td>
				</tr>
				
				""")
			except Exception as e:
				frappe.log_error(f"Error processing month {month_name} for {sp.name}: {str(e)}", "Month Processing Error")
				continue

		# Calculate totals
		total_percent = round((total_approved / total_quoted) * 100) if total_quoted and total_quoted > 0 else 0
		total_percent2 = round((total_approved2 / total_quoted2) * 100) if total_quoted2 and total_quoted2 > 0 else 0

		# Get colors for totals
		color1 = get_color(total_percent)
		color2 = get_color(total_percent2)

		# Calculate average days
		avg_days_wo = round(total_days_wo / wo_count) if wo_count > 0 else 0
		avg_days_so = round(total_days_so / so_count) if so_count > 0 else 0

		rows.append(f"""
		<tr>
			<td></td>
			<td><center><b>Total</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_quoted:,.0f}</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_approved:,.0f}</b></center></td>
			<td style="background-color:{color1};"><center><b>{total_percent}%</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{avg_days_wo}</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_quoted2:,.0f}</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{total_approved2:,.0f}</b></center></td>
			<td style="background-color:{color2};"><center><b>{total_percent2}%</b></center></td>
			<td style="background-color:#D3D3D3"><center><b>{avg_days_so}</b></center></td>
		</tr>
		<tr><td colspan="10"><center><b>-</b></center></td></tr>
		""")

		# Return both rows and totals
		totals = {
			'quoted_wo': total_quoted,
			'approved_wo': total_approved,
			'days_wo': avg_days_wo,
			'quoted_so': total_quoted2,
			'approved_so': total_approved2,
			'days_so': avg_days_so
		}
		
		return [rows, totals]
	except Exception as e:
		frappe.log_error(f"Error in generate_salesperson_rows for {sp.name}: {str(e)}", "Salesperson Error")
		return [[], {}]

def get_color(percentage):
	"""Return color based on percentage."""
	if percentage < 60:
		return "#FF7074"
	elif percentage < 80:
		return "#FFFF8F"
	else:
		return "#98FB98"

def get_monthly_sales(sales_user, from_date, to_date, company):
	"""
	Calculates total quoted and approved amounts per distinct WOD, with correct discount handling.
	Uses net_amount for 2026 onwards.
	"""
	try:
		if not sales_user:
			return 0, 0, 0, 0, 0, 0

		# Get WOD list
		wod_list = frappe.db.sql("""
			SELECT DISTINCT qi.job_order_data as jo
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Repair', 'Customer Quotation - R - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.job_order_data != ''
		""", (sales_user,company,from_date,to_date), as_dict=True)

		# Get WOD count
		w_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT qi.job_order_data) as ct
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Repair', 'Customer Quotation - R - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.job_order_data IS NOT NULL
			AND qi.job_order_data != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		wod_count = w_count[0]["ct"] if w_count else 0

		total_quoted = 0
		total_approved = 0
		ddf1 = 0
		approved_count = 0

		# Process each WOD
		for wod in wod_list:
			jo = wod["jo"]

			# Get transaction year
			year_check = frappe.db.sql("""
				SELECT YEAR(q.transaction_date) as trans_year
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.job_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
				LIMIT 1
			""", (sales_user, jo, from_date, to_date), as_dict=True)

			is_2026_or_later = year_check and year_check[0].get("trans_year", 0) >= 2026

			# Get Quoted Amount
			# if is_2026_or_later:
			quoted_rows = frappe.db.sql("""
				SELECT qi.net_amount as amount
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.job_order_data = %s
				AND q.workflow_state IN ('Approved by Customer', 'Quoted to Customer', 'Rejected by Customer')
				AND q.quotation_type IN ('Customer Quotation - Repair','Customer Quotation - R - Revised')
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user,jo, from_date, to_date), as_dict=True)
			if quoted_rows and quoted_rows[0].get("amount"):
				total_quoted += quoted_rows[0]["amount"] or 0


			

			# Check if approved
			rev_check = frappe.db.sql("""
				SELECT DISTINCT qi.job_order_data
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND q.workflow_state IN ('Approved by Customer',"Quoted to Customer","Rejected by Customer")
				AND q.quotation_type IN ('Customer Quotation - Repair','Customer Quotation - R - Revised')
				AND qi.job_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user, jo, from_date, to_date), as_dict=True)

			if rev_check:
				# Get Approved Amount
				# if is_2026_or_later:
				approved_rows = frappe.db.sql("""
					SELECT SUM(qi.net_amount) as amount, 
							q.transaction_date, q.approval_date
					FROM `tabQuotation` q
					INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
					WHERE q.sales_person = %s
					AND qi.job_order_data = %s
					AND q.workflow_state = 'Approved by Customer'
					AND q.quotation_type IN ('Customer Quotation - Repair', 'Customer Quotation - R - Revised')
					AND q.transaction_date BETWEEN %s AND %s
					GROUP BY q.name
				""", (sales_user, jo, from_date, to_date), as_dict=True)
				
				if approved_rows:
					for row in approved_rows:
						if row.get("approval_date") and row.get("transaction_date"):
							date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
							ddf1 += date_diff
							approved_count += 1
						total_approved += row.get("amount") or 0
				# else:
				#     approved_rows = frappe.db.sql("""
				#         SELECT q.is_multiple_quotation, q.default_discount_percentage,
				#                q.after_discount_cost, qi.unit_price,
				#                q.transaction_date, q.approval_date
				#         FROM `tabQuotation` q
				#         INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				#         WHERE q.sales_person = %s
				#         AND qi.job_order_data = %s
				#         AND q.workflow_state = 'Approved By Customer'
				#         AND q.quotation_type IN ('Customer Quotation - Repair', 'Customer Quotation - R - Revised')
				#         AND q.transaction_date BETWEEN %s AND %s
				#     """, (sales_user, jo, from_date, to_date), as_dict=True)
					
				#     if approved_rows:
				#         row = approved_rows[0]
				#         if row.get("approval_date") and row.get("transaction_date"):
				#             date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
				#             ddf1 += date_diff
				#             approved_count += 1
						
				#         if row.get("is_multiple_quotation"):
				#             discount = row.get("default_discount_percentage") or 0
				#             total_approved += row.get("unit_price", 0) * (1 - discount / 100)
				#         else:
				#             total_approved += row.get("after_discount_cost") or 0

		# SOD Section
		sod_list = frappe.db.sql("""
			SELECT DISTINCT qi.supply_order_data as sod
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.supply_order_data IS NOT NULL
			AND qi.supply_order_data != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		s_count = frappe.db.sql("""
			SELECT COUNT(DISTINCT qi.supply_order_data) as sod
			FROM `tabQuotation` q
			INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			WHERE q.sales_person = %s
			AND q.company = %s
			AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
			AND q.transaction_date BETWEEN %s AND %s
			AND qi.supply_order_data IS NOT NULL
			AND qi.supply_order_data != ''
		""", (sales_user, company, from_date, to_date), as_dict=True)

		sod_count = s_count[0]["sod"] if s_count else 0

		total_quoted2 = 0
		total_approved2 = 0
		ddf2 = 0
		approved_count2 = 0

		# Process each SOD
		for s in sod_list:
			sod_no = s["sod"]

			# Get transaction year
			year_check = frappe.db.sql("""
				SELECT YEAR(q.transaction_date) as trans_year
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.supply_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
				LIMIT 1
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			is_2026_or_later = year_check and year_check[0].get("trans_year", 0) >= 2026

			# Get Quoted Amount
			# if is_2026_or_later:
			quoted_rows2 = frappe.db.sql("""
				SELECT q.name, SUM(qi.net_amount) as net_amount
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND qi.supply_order_data = %s
				AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
				AND q.quotation_type IN ('Customer Quotation - Supply')
				AND q.transaction_date BETWEEN %s AND %s
				GROUP BY q.name
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			if quoted_rows2:
				for row in quoted_rows2:
					total_quoted2 += row.get("net_amount") or 0
			# else:
			# 	quoted_rows2 = frappe.db.sql("""
			# 		SELECT q.name, q.is_multiple_quotation, q.default_discount_percentage,
			# 			   q.after_discount_cost, qi.unit_price, qi.qty
			# 		FROM `tabQuotation` q
			# 		INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
			# 		WHERE q.sales_person = %s
			# 		AND qi.supply_order_data = %s
			# 		AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer', 'Rejected by Customer')
			# 		AND q.quotation_type IN ('Customer Quotation - Supply')
			# 		AND q.transaction_date BETWEEN %s AND %s
			# 	""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			# 	if quoted_rows2:
			# 		for row in quoted_rows2:
			# 			if row.get("is_multiple_quotation"):
			# 				discount = row.get("default_discount_percentage") or 0
			# 				dis_amt = (row.get("unit_price", 0) * discount) / 100
			# 				amt = (row.get("unit_price", 0) - dis_amt) * (row.get("qty") or 1)
			# 				total_quoted2 += amt
			# 			else:
			# 				total_quoted2 += row.get("after_discount_cost") or 0

			# Check if approved
			rev_check2 = frappe.db.sql("""
				SELECT DISTINCT qi.supply_order_data
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE q.sales_person = %s
				AND q.workflow_state IN ('Approved By Customer')
				AND q.quotation_type IN ('Customer Quotation - Supply','Customer Quotation - S - Revised')
				AND qi.supply_order_data = %s
				AND q.transaction_date BETWEEN %s AND %s
			""", (sales_user, sod_no, from_date, to_date), as_dict=True)

			if rev_check2:
				# Get Approved Amount
				# if is_2026_or_later:
				approved_rows2 = frappe.db.sql("""
					SELECT q.name, SUM(qi.net_amount) as net_amount,
							q.transaction_date, q.approval_date
					FROM `tabQuotation` q
					INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
					WHERE q.sales_person = %s
					AND qi.supply_order_data = %s
					AND q.workflow_state = 'Approved By Customer'
					AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
					AND q.transaction_date BETWEEN %s AND %s
					GROUP BY q.name
				""", (sales_user, sod_no, from_date, to_date), as_dict=True)

				if approved_rows2:
					for row in approved_rows2:
						if row.get("approval_date") and row.get("transaction_date"):
							date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
							ddf2 += date_diff
							approved_count2 += 1
						total_approved2 += row.get("net_amount") or 0
				# else:
				# 	approved_rows2 = frappe.db.sql("""
				# 		SELECT q.name, q.is_multiple_quotation, q.default_discount_percentage,
				# 			   q.after_discount_cost, qi.unit_price, qi.qty,
				# 			   q.transaction_date, q.approval_date
				# 		FROM `tabQuotation` q
				# 		INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				# 		WHERE q.sales_person = %s
				# 		AND qi.supply_order_data = %s
				# 		AND q.workflow_state = 'Approved By Customer'
				# 		AND q.quotation_type IN ('Customer Quotation - Supply', 'Customer Quotation - S - Revised')
				# 		AND q.transaction_date BETWEEN %s AND %s
				# 	""", (sales_user, sod_no, from_date, to_date), as_dict=True)

				# 	if approved_rows2:
				# 		for row in approved_rows2:
				# 			if row.get("approval_date") and row.get("transaction_date"):
				# 				date_diff = (getdate(row["approval_date"]) - getdate(row["transaction_date"])).days
				# 				ddf2 += date_diff
				# 				approved_count2 += 1
							
				# 			if row.get("is_multiple_quotation"):
				# 				discount = row.get("default_discount_percentage") or 0
				# 				dis_amt = (row.get("unit_price", 0) * discount) / 100
				# 				amt = (row.get("unit_price", 0) - dis_amt) * (row.get("qty") or 1)
				# 				total_approved2 += amt
				# 			else:
				# 				total_approved2 += row.get("after_discount_cost") or 0

		# Calculate average days
		wod_hrs = round(ddf1 / approved_count) if approved_count > 0 else 0
		sod_hrs = round(ddf2 / approved_count2) if approved_count2 > 0 else 0

		return (
			round(total_quoted or 0),
			round(total_approved or 0),
			round(total_quoted2 or 0),
			round(total_approved2 or 0),
			wod_hrs,
			sod_hrs
		)
	except Exception as e:
		frappe.log_error(f"Error in get_monthly_sales for {sales_user}: {str(e)}", "Monthly Sales Error")
		return 0, 0, 0, 0, 0, 0



import frappe
import json
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
	today,
)
from frappe.utils.file_manager import save_file
from frappe.utils.file_manager import get_file
from frappe.utils import add_to_date
import requests
from datetime import datetime
from erpnext.setup.utils import get_exchange_rate
from frappe.utils.csvutils import read_csv_content

frappe.whitelist()
def sales_summary(from_date, to_date, company,brnch):
	import frappe
	from datetime import datetime
	from frappe.utils import add_days, today, getdate
	
	d = datetime.now().date()
	ogdate = datetime.strptime(str(d), "%Y-%m-%d")
	formatted_date = ogdate.strftime("%d-%m-%Y")

	data = ''
	data += '<div class="table-container">'
	data += '<table class="table table-bordered" style="width: 100%; border-collapse: collapse;">'
	data += '<tr>'
	
	# Branch and currency mapping
	branch_map = {
		"TSL COMPANY - Kuwait": "Kuwait",
		"TSL COMPANY - UAE": "UAE", 
		"TSL COMPANY - KSA": "KSA"
	}
	currency_map = {
		"TSL COMPANY - Kuwait": "KWD",
		"TSL COMPANY - UAE": "AED",
		"TSL COMPANY - KSA": "SAR"
	}
	
	# branch = branch_map.get(company, "")
	currency = currency_map.get(company, "")

	# Header with logo
	data += '<td colspan="3" style="border-color:#000000;"><img src="/files/Cyrix Logo.png" align="left" width="200"></td>'
	data += '<td colspan="5" style="border-color:#000000;"><h2><center><b style="color:#055c9d;">Cyrix TSL<br>Branch - %s<br>Currency - %s</b></center></h2></td>' % (brnch,"KWD")
	
	
	# Flag based on company
	if company == "Cyrix TSL - Kuwait":
		data += '<td colspan="3" style="border-color:#000000;"><center><img src="/files/kuwait flag.jpg" width="150"></center></td>'
	elif company == "TSL COMPANY - UAE":
		data += '<td colspan="3" style="border-color:#000000;"><center><br><img src="/files/Flag_of_the_United_Arab_Emirates.svg.jpg" width="80"></center></td>'

	data += '</tr>'

	# Title row
	data += '<tr>'
	data += '<td colspan="3" style="border-right:hidden;border-color:#000000;"><b></b></td>'
	data += '<td colspan="5" align="center" style="border-color:#000000;"><b>QUOTED, RS, RSC & RSI SUMMARY</b></td>'
	data += '<td colspan="3" align="right" style="border-left:hidden;border-color:#000000;"><b>Generation Date : %s</b></td>' % formatted_date
	data += '</tr>'

	# Column headers
	data += '<tr>'
	data += '<td colspan="1" style="border-color:#000000;background-color:#0e86d4;"><center><b></b></center></td>'
	data += '<td colspan="2" style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">Quoted - Amount</b></center></td>'
	data += '<td colspan="2" style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">RS - Amount</b></center></td>'
	data += '<td colspan="2" style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">RSC - Amount</b></center></td>'
	data += '<td colspan="2" style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">RSI - Amount</b></center></td>'
	data += '<td colspan="2" style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">More than 3 Months(RSI)</b></center></td>'
	data += '</tr>'
	
	# Get sales persons - use parameterized query
	wo = frappe.db.sql(""" SELECT DISTINCT name FROM `tabSales Person`  where custom_branch = '%s' """ %(brnch) , as_dict=1)
	
	# Company-specific header rows
	header_rows = {
		"Cyrix TSL - Kuwait": """
		<tr>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">Salesman</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>  
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>  
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>	
		</tr>
		""",
		"TSL COMPANY - UAE": """
		<tr>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">Salesman</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>  
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>	
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">JO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#145da0;color:white;"><center><b style="color:white;">SO</b></center></td>
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO</b></center></td>  
			<td style="border-color:#000000;width:9%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO</b></center></td>	
		</tr>
		""",
		"TSL COMPANY - KSA": """
		<tr>
			<td style="border-color:#000000;width:10%;background-color:#0e86d4;color:white;"><center><b style="color:white;">Salesman</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#145da0;color:white;"><center><b style="color:white;">JO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#145da0;color:white;"><center><b style="color:white;">SO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#145da0;color:white;"><center><b style="color:white;">JO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#145da0;color:white;"><center><b style="color:white;">SO(in SAR)</b></center></td>
			<td style="border-color:#000000;width:10%;background-color:#0e86d4;color:white;"><center><b style="color:white;">JO(in SAR)</b></center></td>  
			<td style="border-color:#000000;width:10%;background-color:#0e86d4;color:white;"><center><b style="color:white;">SO(in SAR)</b></center></td>	
		</tr>
		"""
	}
	
	if company in header_rows:
		data += header_rows[company]

	Week_start = from_date
	current_date = to_date
	today_date = today()
	cutoff_date_90 = add_days(today_date, -90)
	
	# Excluded salespersons
	excluded = {'Sales Team', 'Walkin', 'OMAR', '', 'Mazz', 'Abdullah', 'karoline', 
				'Dilshad', 'Dhinesh', 'Karoline', 'Nour', 'Mohannad', 'Samar Moussa', 
				'Rana Ali', 'Michael Veniston', 'Nidhin'}
	
	# Initialize totals
	total_rsi = 0
	total_rsi2 = 0
	total_rsc = 0
	total_rs = 0
	total_quot = 0
	s_invoiced = 0
	s_invoiced2 = 0
	s_delivered = 0
	s_received = 0
	sup_quoted_sod = 0
	
	# Department mapping
	dept_repair = "Kuwait - Repair - CT-K" if company == "Cyrix TSL - Kuwait" else "Repair - TSL-UAE"
	dept_supply = "Kuwait - Supply - CT-K" if company == "Cyrix TSL - Kuwait" else "Supply - TSL-UAE"
	
	# Batch process salespersons
	for i in wo:
		sp_name = i["name"]
		if not sp_name or sp_name in excluded:
			continue
			
		sales = frappe.get_value("Sales Person", sp_name, ["user", "name"], as_dict=True)
		if not sales:
			continue
			
		sales_person = sales.get('name')
		sales_name = sales.get('name')
		
		# Initialize ALL variables for this salesperson with default values
		gt = 0
		gt2 = 0
		st = 0
		st2 = 0
		# total_rsi_old = 0
		# total_rsi_old2 = 0
		# soinv_old = 0
		# soinv_old2 = 0
		# sodel_old = 0
		# sorec_old = 0
		# soq_old = 0  # CRITICAL: Initialize this variable
		# rsc_old = 0
		# rs_old = 0
		# q_old = 0
		q_m = 0
		q_m_2 = 0
		rs_am = 0
		rs_am_2 = 0
		quot_am = 0
		quot_am_2 = 0
		sp_del = 0
		sp_del_2 = 0
		sp_rec = 0
		sp_rec_2 = 0
		sp_qted = 0
		sp_qted_2 = 0
		
		# Get Sales Invoices in batch
		invoice_filters = {
			'sales_person': sales_person,
			'status': ['in', ['Unpaid', 'Overdue', 'Partly Paid']]
		}

		# RSI - current period
		gr = frappe.get_all("Sales Invoice", {
			**invoice_filters,
			'cost_center': dept_repair,
			'posting_date': ['between', (Week_start, current_date)]
		}, ['outstanding_amount'])
		if gr:
			gt = sum(inv.outstanding_amount for inv in gr)
		
		# RSI - old (>90 days)
		gr2 = frappe.get_all("Sales Invoice", {
			**invoice_filters,
			'cost_center': dept_repair,
			'posting_date': ['<=', cutoff_date_90]
		}, ['outstanding_amount'])
		if gr2:
			gt2 = sum(inv.outstanding_amount for inv in gr2)
		
		# Supply Invoices - current
		sr = frappe.get_all("Sales Invoice", {
			**invoice_filters,
			'cost_center': dept_supply,
			'posting_date': ['between', (Week_start, current_date)]
		}, ['outstanding_amount'])
		if sr:
			st = sum(inv.outstanding_amount for inv in sr)
		
		# Supply Invoices - old
		sr2 = frappe.get_all("Sales Invoice", {
			**invoice_filters,
			'cost_center': dept_supply,
			'posting_date': ['<=', cutoff_date_90]
		}, ['outstanding_amount'])
		if sr2:
			st2 = sum(inv.outstanding_amount for inv in sr2)
		
		# Job Order Data - batch fetch
		wo_statuses = ['RSI-Repaired and Shipped Invoiced', 'RSC-Repaired and Shipped Client', 
					   'RS-Repaired and Shipped', 'Q-Quoted']
		
		# Fetch all WO data in one go for current period
		if wo_statuses:
			placeholders = ','.join(['%s'] * len(wo_statuses))
			# wo_data = frappe.db.sql(f"""
			#     SELECT 
			#         status,
			#         SUM(COALESCE(old_wo_q_amount, 0) + COALESCE(old_wo_vat, 0)) as old_amount
			#     FROM `tabJob Order Data`
			#     WHERE sales_person = %s
			#         AND status IN ({placeholders})
			#         AND posting_date BETWEEN %s AND %s
			#     GROUP BY status
			# """, tuple([sales_name] + wo_statuses + [Week_start, current_date]), as_dict=True)
			
			# # Process WO data for current period
			# for w in wo_data:
			#     if w.status == 'RSI-Repaired and Shipped Invoiced':
			#         total_rsi_old = w.old_amount or 0
			#     elif w.status == 'RSC-Repaired and Shipped Client':
			#         rsc_old = w.old_amount or 0
			#     elif w.status == 'RS-Repaired and Shipped':
			#         rs_old = w.old_amount or 0
			#     elif w.status == 'Q-Quoted':
			#         q_old = w.old_amount or 0
		
		# Fetch old WO data (>90 days)
		# wo_data_old = frappe.db.sql(f"""
		#     SELECT 
		#         SUM(COALESCE(old_wo_q_amount, 0) + COALESCE(old_wo_vat, 0)) as old_amount
		#     FROM `tabJob Order Data`
		#     WHERE sales_person = %s
		#         AND status = 'RSI-Repaired and Shipped Invoiced'
		#         AND posting_date <= %s
		# """, (sales_name, cutoff_date_90), as_dict=True)
		
		# if wo_data_old and wo_data_old[0].get('old_amount'):
		#     total_rsi_old2 = wo_data_old[0]['old_amount'] or 0
		
		# Supply Order Data - batch fetch
		so_statuses = ['Invoiced', 'Delivered', 'Received', 'Quoted']
		
		# Fetch old SO data with currency conversion (>90 days)
		if so_statuses:
			placeholders = ','.join(['%s'] * len(so_statuses))
			# so_data_old = frappe.db.sql(f"""
			#     SELECT 
			#         status,
			#         so_currency_old,
			#         COALESCE(so_old_total_amt, 0) as so_old_total_amt
			#     FROM `tabSupply Order Data`
			#     WHERE sales_person = %s
			#         AND status IN ({placeholders})
			#         AND posting_date <= %s
			# """, tuple([sales_name] + so_statuses + [cutoff_date_90]), as_dict=True)
			
			# # Process old SO data with currency conversion
			# for s in so_data_old:
			#     amt = s.so_old_total_amt or 0
			#     if s.so_currency_old == "USD":
			#         exr = get_exchange_rate("USD", "AED")
			#         if exr:
			#             amt = amt * exr
				
			#     if s.status == 'Invoiced':
			#         soinv_old2 += amt
		
		# Fetch current SO data
		# so_data = frappe.db.sql(f"""
		#     SELECT 
		#         status,
		#         so_currency_old,
		#         COALESCE(so_old_total_amt, 0) as so_old_total_amt
		#     FROM `tabSupply Order Data`
		#     WHERE sales_person = %s
		#         AND status IN ({placeholders})
		#         AND posting_date BETWEEN %s AND %s
		# """, tuple([sales_name] + so_statuses + [Week_start, current_date]), as_dict=True)
		
		# Process current SO data with currency conversion
		# for s in so_data:
		#     amt = s.so_old_total_amt or 0
		#     if s.so_currency_old == "USD":
		#         exr = get_exchange_rate("USD", "AED")
		#         if exr:
		#             amt = amt * exr
			
		#     if s.status == 'Invoiced':
		#         soinv_old += amt
		#     elif s.status == 'Delivered':
		#         sodel_old += amt
		#     elif s.status == 'Received':
		#         sorec_old += amt
		#     elif s.status == 'Quoted':
		#         soq_old += amt  # Now this is safe because soq_old is initialized
		
		# Get WOD lists for detailed calculations
		wods_rsc = frappe.get_all("Job Order Data", {
			"sales_person": sales_name,
			"status": "RSC-Repaired and Shipped Client",
			"posting_date": ["between", (Week_start, current_date)]
		}, ["name"])
		
		wods_rs = frappe.get_all("Job Order Data", {
			"sales_person": sales_name,
			"status": "RS-Repaired and Shipped",
			"posting_date": ["between", (Week_start, current_date)]
		}, ["name"])
		
		wods_quot = frappe.get_all("Job Order Data", {
			"sales_person": sales_name,
			"project_1": 0,
			"status": "Q-Quoted",
			"posting_date": ["between", (Week_start, current_date)]
		}, ["name"])
		
		# Batch process quotations for WODs
		if wods_rsc:
			wod_names = [w.name for w in wods_rsc]
			placeholders = ','.join(['%s'] * len(wod_names))
			query = f"""
				SELECT 
					qi.job_order_data,
					q.name as q_name,
				   
					q.transaction_date as td,
					q.workflow_state,
				   
					qi.net_amount as am,
					qi.tax_amount as vat
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.job_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Repair', 'Revised Quotation - Repair')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = wod_names + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			# Process quotation data
			
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
				if row.workflow_state == "Approved By Customer":
					q_m += amt
				else:
					q_m_2 += amt
		
		# Calculate RSC total
		rsc_total = q_m + q_m_2
		
		# Batch process for RS
		if wods_rs:
			wod_names = [w.name for w in wods_rs]
			placeholders = ','.join(['%s'] * len(wod_names))
			query = f"""
				SELECT 
					qi.job_order_data,
					q.name as q_name,
				   
					q.transaction_date as td,
					q.workflow_state,
				   
					qi.net_amount as am,
					qi.tax_amount as vat
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.job_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Repair', 'Revised Quotation - Repair')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = wod_names + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			# Process quotation data
			date_obj = datetime.strptime("01-03-2025", "%d-%m-%Y").date()
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
			
				if row.workflow_state == "Approved By Customer":
					rs_am += amt
				else:
					rs_am_2 += amt
		
		rs_total = rs_am + rs_am_2
		
		# Batch process for Quoted
		if wods_quot:
			wod_names = [w.name for w in wods_quot]
			placeholders = ','.join(['%s'] * len(wod_names))
			query = f"""
				SELECT 
					qi.job_order_data,
					q.name as q_name,
				   
					q.transaction_date as td,
					q.workflow_state,
				  
					qi.net_amount as am,
					qi.tax_amount as vat,
					q.grand_total as gt
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.job_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Repair', 'Revised Quotation - Repair')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = wod_names + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			# Process quotation data
			date_obj = datetime.strptime("01-03-2025", "%d-%m-%Y").date()
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
				
				if row.workflow_state == "Approved By Customer":
					quot_am += amt
				else:
					quot_am_2 += amt
		
		wd_total_quot = quot_am + quot_am_2
		
		# Batch process for Supply Orders
		sods = frappe.get_all("Supply Order Data", {
			"sales_person": sales_name,
			"status": ["in", ["Delivered", "Received", "Quoted"]],
			"posting_date": ["between", (Week_start, current_date)]
		}, ["name", "status"])
		
		# Group by status for batch processing
		sod_by_status = {'Delivered': [], 'Received': [], 'Quoted': []}
		for sod in sods:
			if sod.status in sod_by_status:
				sod_by_status[sod.status].append(sod.name)
		
		# Process Delivered
		if sod_by_status['Delivered']:
			placeholders = ','.join(['%s'] * len(sod_by_status['Delivered']))
			query = f"""
				SELECT 
					qi.supply_order_data,
					q.name as q_name,
					q.transaction_date as td,
					q.workflow_state,
					qi.net_amount as am,
					qi.tax_amount as vat,
					qi.qty
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.supply_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Supply', 'Revised Quotation - Supply')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = sod_by_status['Delivered'] + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			date_obj = datetime.strptime("01-03-2025", "%d-%m-%Y").date()
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
				
				if row.workflow_state == "Approved By Customer":
					sp_del += amt
				else:
					sp_del_2 += amt
		
		# Process Received
		if sod_by_status['Received']:
			placeholders = ','.join(['%s'] * len(sod_by_status['Received']))
			query = f"""
				SELECT 
					qi.supply_order_data,
					q.name as q_name,
				  
					q.transaction_date as td,
					q.workflow_state,
					
					qi.net_amount as am,
					qi.tax_amount as vat,
					qi.qty
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.supply_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Supply', 'Revised Quotation - Supply')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = sod_by_status['Received'] + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			date_obj = datetime.strptime("01-03-2025", "%d-%m-%Y").date()
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
				
				if row.workflow_state == "Approved By Customer":
					sp_rec += amt
				else:
					sp_rec_2 += amt
		
		# Process Quoted
		if sod_by_status['Quoted']:
			placeholders = ','.join(['%s'] * len(sod_by_status['Quoted']))
			query = f"""
				SELECT 
					qi.supply_order_data,
					q.name as q_name,
					
				   
					q.transaction_date as td,
					q.workflow_state,
				  
					qi.net_amount as am,
					qi.tax_amount as vat,
					qi.qty
				FROM `tabQuotation` q
				INNER JOIN `tabQuotation Item` qi ON q.name = qi.parent
				WHERE qi.supply_order_data IN ({placeholders})
					AND q.workflow_state IN ('Approved By Customer', 'Quoted to Customer')
					AND q.quotation_type IN ('Customer Quotation - Supply', 'Revised Quotation - Supply')
					AND q.transaction_date BETWEEN %s AND %s
			"""
			params = sod_by_status['Quoted'] + [Week_start, current_date]
			quot_data = frappe.db.sql(query, tuple(params), as_dict=True)
			
			
			for row in quot_data:
				amt = 0
				amt = (row.am or 0) + (row.vat or 0)
				if row.workflow_state == "Approved By Customer":
					sp_qted += amt
				else:
					sp_qted_2 += amt
		
		s_del_total = sp_del + sp_del_2
		s_rec_total = sp_rec + sp_rec_2
		sup_quoted_total = sp_qted + sp_qted_2 # Now soq_old is safe

		# Add row for this salesperson
		data += '<tr>'
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % sales_name
		
		wd_total_quot = round(wd_total_quot)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{wd_total_quot:,}" if wd_total_quot else "0")
		sup_quoted_total = round(sup_quoted_total)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{sup_quoted_total:,}" if sup_quoted_total else "0")
		
		rs_total = round(rs_total)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{rs_total:,}" if rs_total else "0")
		s_rec_total = round(s_rec_total)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{s_rec_total:,}" if s_rec_total else "0")
		
		rsc_total = round(rsc_total)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{rsc_total:,}" if rsc_total else "0")
		s_del_total = round(s_del_total)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{s_del_total:,}" if s_del_total else "0")
		
		gt = round(gt)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{gt:,}" if gt else "0")
		st = round(st)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{st:,}" if st else "0")

		gt2 = round(gt2) 
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{round(gt2):,}" if gt2 else "0")
		st2 = round(st2)
		data += '<td style="border-color:#000000;"><center><b>%s</b></center></td>' % (f"{st2:,}" if st2 else "0")
		
		# Update totals
		total_rsi += gt
		total_rsi2 += gt2
		total_rsc += rsc_total
		total_rs += rs_total
		total_quot += wd_total_quot

		s_invoiced += st
		s_invoiced2 += st2
		s_delivered += s_del_total
		s_received += s_rec_total
		sup_quoted_sod += sup_quoted_total

		data += '</tr>'

	# Add total row
	data += '<tr>'
	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">Total</b></center></td>'

	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(total_quot):,}" if total_quot else "0")
	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(sup_quoted_sod):,}" if sup_quoted_sod else "0")

	data += '<td style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(total_rs):,}" if total_rs else "0")
	data += '<td style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(s_received):,}" if s_received else "0")

	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(total_rsc):,}" if total_rsc else "0")
	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(s_delivered):,}" if s_delivered else "0")

	data += '<td style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(total_rsi):,}" if total_rsi else "0")
	data += '<td style="border-color:#000000;background-color:#145da0;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(s_invoiced):,}" if s_invoiced else "0")

	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(total_rsi2):,}" if total_rsi2 else "0")
	data += '<td style="border-color:#000000;background-color:#0e86d4;color:white;"><center><b style="color:white;">%s</b></center></td>' % (f"{round(s_invoiced2):,}" if s_invoiced2 else "0")
	data += '</tr>'

	data += '</table>'
	data += '</div>'
	
	return data


@frappe.whitelist()
def weekly_report(company,branch):
	
	d = datetime.today().date()
	ogdate = datetime.strptime(str(d),"%Y-%m-%d")

	# Format the date as a string in the desired format
	formatted_date = ogdate.strftime("%d-%m-%Y")
	
	from_date = add_days(d,-7)
	br = ""
	if company == "Cyrix TSL - Kuwait":
		br = "Kuwait"
	
		

	data= ""
	data += '<div class="table-container">'
	data += '<table class="table table-bordered">'
	data += '<tr>'
	data += '<td colspan = 1 align = center style="border-color:#000000;"><img src = "/files/TSL LOGO.png" align="left" width ="250"></td>'
	data += '<td colspan = 2 style="border-color:#000000;"><h2><center><b style="color:#055c9d;" >%s</b></center></h2></td>' %(company)
	
	if company == "Cyrix TSL - Kuwait":
		data += '<td colspan = 1 style="border-color:#000000;"><center><img src = "/files/kuwait flag.jpg" width ="140"></center></td>'
	# if company == "TSL COMPANY - UAE":
	# 	data += '<td colspan = 1 style="border-color:#000000;"><center><img src = "/files/Flag_of_the_United_Arab_Emirates.svg.jpg" width ="140"></center></td>'
		
	# if company == "TSL COMPANY - KSA":
	# 	data += '<td colspan = 1 style="border-color:#000000;"><center><img src = "/files/640px-Flag_of_Saudi_Arabia.svg(1).png" width ="140"></center></td>'
		



	data += '<tr>'
	data += '<td colspan = 4 style="border-color:#000000;padding:1px;font-size:20px;background-color:#0e86d4;color:white;"><b style = "color:white;" >%s</b></td>' %(formatted_date)
	data += '</tr>'

	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;width:25%;"><center><b style = "color:white;" >Status</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;width:25%;"><center><b style = "color:white;" >WOD Count</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;width:25%;"><center><b style = "color:white;" >More than a Week</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;width:25%;"><center><b style = "color:white;" >Remarks</b><center></td>'

	data += '</tr>'

	ne_1 =  frappe.db.count("Job Order Data",{"status":"NE-Need Evaluation","branch":branch,"company":company,})
	ner_1 =  frappe.db.count("Job Order Data",{"status":"NER-Need Evaluation Return","branch":branch,"company":company})
	ue_1 =  frappe.db.count("Job Order Data",{"status":"UE-Under Evaluation","branch":branch,"company":company,})
	utr_1 =  frappe.db.count("Job Order Data",{"status":"UTR-Under Technician Repair","branch":branch,"company":company})
	tr_1 =  frappe.db.count("Job Order Data",{"status":"TR-Technician Repair","branch":branch,"company":company})
	sp_1 =  frappe.db.count("Job Order Data",{"status":"SP-Searching Parts","branch":branch,"company":company})
	wp_1 =  frappe.db.count("Job Order Data",{"status":"WP-Waiting Parts","branch":branch,"company":company})

	
	ne = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "NE-Need Evaluation"
	AND `tabJob Order Data`.status = "NE-Need Evaluation"
	AND `tabJob Order Data`.company = '%s' and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s'
	""" % (company,branch,from_date), as_dict=1)


	
	ner = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "NER-Need Evaluation Return"
	AND `tabJob Order Data`.status = "NER-Need Evaluation Return"
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	and DATE(`tabStatus Duration Details`.date) BETWEEN '%s' AND '%s';
	""" % (company,branch,from_date,d), as_dict=1)


	
	ue = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = 'UE-Under Evaluation'
	AND `tabJob Order Data`.status = 'UE-Under Evaluation'
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s'
	""" % (company,branch,from_date), as_dict=1)


	utr = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "UTR-Under Technician Repair"
	AND `tabJob Order Data`.status = "UTR-Under Technician Repair"
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s' AND DATE(`tabStatus Duration Details`.date) > '%s'
	""" % (company,branch,from_date,from_date), as_dict=1)

	
	tr = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "TR-Technician Repair"
	AND `tabJob Order Data`.status = "TR-Technician Repair"
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s'
	""" % (company,branch,from_date), as_dict=1)

	
	sp = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "SP-Searching Parts"
	AND `tabJob Order Data`.status = "SP-Searching Parts"
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s'
	""" % (company,branch,from_date), as_dict=1)

	
	wp = frappe.db.sql("""
	SELECT COUNT(DISTINCT `tabJob Order Data`.name) AS wd
	FROM `tabJob Order Data`
	LEFT JOIN `tabStatus Duration Details` ON `tabJob Order Data`.name = `tabStatus Duration Details`.parent
	WHERE `tabStatus Duration Details`.status = "WP-Waiting Parts"
	AND `tabJob Order Data`.status = "WP-Waiting Parts"
	AND `tabJob Order Data`.company = '%s'  and `tabJob Order Data`.branch = '%s' 
	AND DATE(`tabStatus Duration Details`.date) < '%s'
	""" % (company,branch,from_date), as_dict=1)

	# frappe.errprint(ner[0]["wd"])
	ner_3 = ner_1-ner[0]["wd"]

	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>NE</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ne_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ne[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'
	data += '</tr>'

	
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>NER</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ner_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ner_3)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'
	data += '</tr>'
	
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>UE</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ue_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(ue[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'

	data += '</tr>'
		
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>UTR</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(utr_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(utr[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'

	data += '</tr>'

	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>TR</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(tr_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(tr[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b></b><center></td>'

	data += '</tr>'
		
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>SP</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(sp_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(sp[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'

	data += '</tr>'
	
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b>WP</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(wp_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;"><center><b>%s</b><center></td>' %(wp[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;"><center><b></b><center></td>'

	data += '</tr>'
	
	data += '<tr>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;width:25%;background-color:#0e86d4;color:white;"><center><b style = "color:white;">Total</b><center></td>'
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;"><center><b style = "color:white;">%s</b><center></td>' %(ne_1 + ner_1 + ue_1 + utr_1 + sp_1 + tr_1 + wp_1)
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;"><center><b style = "color:white;">%s</b><center></td>' %(ne[0]["wd"] + ner_3 + ue[0]["wd"] + utr[0]["wd"] + tr[0]["wd"] + sp[0]["wd"] + wp[0]["wd"])
	data += '<td style="border-color:#000000;padding:1px;font-size:16px;background-color:#0e86d4;color:white;width:25%;"><center><b></b><center></td>'

	data += '</tr>'
	data += '</table>'



	data += '</div>'
	return data


import frappe

@frappe.whitelist()
def get_sales_details3(company=None):
	"""
	Get sales persons grouped by branch for a given company
	"""
	# Sales persons to exclude from the report
	excluded = [
		"Sales Team", "Walkin", "Sales","Abdullah",
		"Karoline", "Nour", "Samar Moussa", "Rana Ali",
		"Salma Zaza ", "Nidhin", "MOHAMED MOSAAD ALY DIAB",
		"Amro Reda Emam Mohamed", "Michael Veniston",
		"TSL", "Mazz", "Dilshad", "Dhinesh", "Hadeel Suleiman"
	]

	# Get all active sales persons with their branch (excluding the excluded list)
	# Note: Add a filter for status="Active" if you have an status field
	sales = frappe.get_all(
		"Sales Person",
		fields=["name", "user", "custom_branch"],
		filters={
			"name": ["not in", excluded],
			# "status": "Active"  # Uncomment if you have a status field
		},
		order_by="name"
	)

	# Group sales persons by branch
	branch_map = {}

	for sp in sales:
		# Skip if no branch assigned
		if not sp.custom_branch:
			continue
		
		# Get username and clean it
		username = ""
		if sp.user:
			user = frappe.get_value("User", {"name": sp.user}, ["username"])
			if user:
				username = user
		
		# If username is empty, use sales person name (cleaned)
		if not username:
			username = sp.name
		
		# Remove "Mr." and "Mr " from the name
		username = username.replace("Mr.", "").replace("Mr ", "").strip()
		
		# Add sales person to branch
		if sp.custom_branch not in branch_map:
			branch_map[sp.custom_branch] = []
		
		branch_map[sp.custom_branch].append({
			"sales_name": username,
			"name": sp.name,
			"user_id": sp.user
		})

	# Function to get branch order priority
	def get_branch_order(branch_name):
		order_map = {
			"kuwait": 1,
			"dubai": 2,
			"riyadh": 3,
			"dammam": 4,
			"jeddah": 5
		}
		
		name_lower = branch_name.lower()
		for keyword, priority in order_map.items():
			if keyword in name_lower:
				return priority
		return 999  # High number for other branches

	# Sort branches by custom order
	sorted_branch_keys = sorted(branch_map.keys(), key=lambda x: get_branch_order(x))

	# Return sorted list of branches with their sales persons
	return [
		{"branch": b, "sales_persons": branch_map[b]}
		for b in sorted_branch_keys
	]
	
@frappe.whitelist()
def target_master(branch=None, company=None, from_date=None, to_date=None, sales_person=None):
	from frappe.utils import get_year_start, nowdate, getdate

	start_date = get_year_start(nowdate())
	end_date = nowdate()

	start = getdate(start_date)
	end = getdate(end_date)

	c_month_range = (end.year - start.year) * 12 + (end.month - start.month) + 1
		
	# Main report function that generates HTML
	com_map = {
		"Cyrix TSL - Kuwait": "Kuwait",
		"Cyrix TSL - UAE": "Dubai", 
		"Company Al-Halloul Faniye Medical": "Riyadh"
	}
	com = com_map.get(company, "")

	# Helper function for number formatting
	def format_number(value):
		return "{:,.0f}".format(round(value)) if value else "0"
	
	# Helper function to get percentage color
	def get_percentage_color(pct):
		if pct >= 80:
			return "color: #27ae60; font-weight: bold;"  # Green
		elif pct >= 60:
			return "color: #f39c12; font-weight: bold;"  # Yellow/Orange
		else:
			return "color: #e74c3c; font-weight: bold;"  # Red

	# Helper function to extract country name from branch
	def get_country_from_branch(branch_name):
		# Extract first word before any separator
		if " - " in branch_name:
			return branch_name.split(" - ")[0]
		elif "-" in branch_name:
			return branch_name.split("-")[0]
		elif " " in branch_name:
			return branch_name.split(" ")[0]
		return branch_name
	
	# Helper function to get currency for branch
	def get_branch_currency(branch_name):
		branch_lower = branch_name.lower()
		if "dubai" in branch_lower:
			return "AED"
		elif "kuwait" in branch_lower:
			return "KWD"
		else:
			# Riyadh, Dammam, Jeddah
			return "SAR"
	
	# Helper function to get currency symbol position
	def get_currency_display(currency):
		if currency == "AED":
			return "Currency in AED (Inc. VAT)"
		elif currency == "SAR":
			return "Currency in SAR (Inc. VAT)"
		elif currency == "KWD":
			return ""
		else:
			return f"Currency in {currency} (Inc. VAT)"

	# Calculate number of months between from_date and to_date
	def calculate_months_diff(start_date, end_date):
		if not start_date or not end_date:
			return 1  # Default to 1 month if dates not provided
		
		from datetime import datetime
		
		# Convert string dates to datetime objects
		start = datetime.strptime(start_date, "%Y-%m-%d")
		end = datetime.strptime(end_date, "%Y-%m-%d")
		
		# Calculate months difference
		months_diff = (end.year - start.year) * 12 + (end.month - start.month)
		
		# Add 1 to include both start and end months
		return max(1, months_diff + 1)

	# Calculate months range
	months_range = calculate_months_diff(from_date, to_date)
	

	data = """
	<style>
		.main-report-title {
			font-size: 20px;
			font-weight: bold;
			text-align: center;
			margin: 20px 0;
			color: #2c3e50;
		}
		.branch-title {
			font-size: 16px;
			font-weight: bold;
			margin: 20px 0 10px;
			padding: 8px;
			background: #a9a9a9;
			border-left: 5px solid #2e86de;
			text-align: center;
		}
		.main-table-container {
			width: 100%;
			margin-bottom: 20px;
			overflow-x: auto;
		}
		.main-table {
			width: 100%;
			border-collapse: collapse;
			font-size: 12px;
		}
		.main-table th, .main-table td {
			border: 1px solid #ddd;
			padding: 5px;
			text-align: center;
		}
		.main-table th { 
			background: #2e86de;
			color: #fff;
			font-weight: bold;
		}
		.sales-person { 
			text-align: left;
			background: #f8f9f9;
		}
		.total-row td {
			font-weight: bold;
			background: #f4f6f7;
		}
		.section-header {
			background: #f8f9f9;
			font-weight: bold;
		}
		.percentage-cell {
			font-weight: bold;
		}
		.period-info {
			font-size: 12px;
			color: #666;
			margin: 5px 0 15px;
			padding: 5px;
			background: #f8f9fa;
			border-left: 3px solid #2e86de;
		}
		.salesperson-filter-info {
			font-size: 14px;
			color: #2e86de;
			margin: 10px 0 15px;
			padding: 10px;
			background: #e8f4fc;
			border-left: 4px solid #2e86de;
			border-radius: 4px;
		}
		.currency-header {
			background: #e8f4fc;
			font-weight: bold;
			text-align: center;
			padding: 5px;
			border: 1px solid #ddd;
		}
		.cumulative-bg {
			background: #e8f4fc;
		}
		.branch-header-table {
			width: 100%;
			border: none;
			margin-bottom: 10px;
		}
		.branch-header-table td {
			border: none;
			padding: 5px;
		}
	</style>
	"""

	# Add main report title
	data += '''
	<div class="main-report-title">
		Sales Performance Report
	</div>
	'''

	# Add period information
	data += f'''
	<div class="period-info">
		Period: {from_date} to {to_date} ({months_range} month{'' if months_range == 1 else 's'})
	</div>
	'''

	# If sales person is selected, show filter info
	if sales_person:
		data += f'''
		<div class="salesperson-filter-info">
			Showing data for: <strong>{sales_person}</strong>
		</div>
		'''

	# Get sales persons grouped by branch
	sales_data = get_sales_details3(company)
	
	# ===================================
	# INDIVIDUAL BRANCH TABLES
	# ===================================
	# Track if we have any data to display
	has_data_to_display = False

	for br in sales_data:
		# Filter by branch if specified
		if branch and branch != br["branch"]:
			continue
		
		# Check if this branch has the selected sales person
		has_selected_sales_person = False
		if sales_person:
			# Check if the selected sales person exists in this branch
			for sp in br["sales_persons"]:
				if sp["sales_name"] == sales_person:
					has_selected_sales_person = True
					break
			# Skip this branch if it doesn't have the selected sales person
			if not has_selected_sales_person:
				continue
		
		# If we reach here, we have data to display
		has_data_to_display = True
		
		# Extract country name from branch
		country_name = get_country_from_branch(br["branch"])
		branch_currency = get_branch_currency(br["branch"])
		currency_display = get_currency_display(branch_currency)
		
		# Determine flag image based on country
		flag_image = ""
		if country_name == "Kuwait":
			flag_image = "/files/kuwait flag.jpg"
		elif country_name == "Dubai":
			flag_image = "/files/Flag_of_the_United_Arab_Emirates.svg.jpg"
		elif country_name in ["Riyadh", "Dammam", "Jeddah"]:
			flag_image = "/files/640px-Flag_of_Saudi_Arabia.svg(1).png"
		
		# Add branch header with flag
		data += f'''
		<div>
			<table class="branch-header-table">
				<tr>
					<td style="width:20%;"><img src="/files/Cyrix Logo.png" align="left" width="150"></td>
					<td style="width:60%; font-size:25px; font-weight:bold; vertical-align:middle; text-align:center;">Branch - {country_name}</td>
					<td style="width:20%;text-align:right"><img src="{flag_image}" width="110"></td>
				</tr>
			</table>
		</div>
		
		<div class="main-table-container">
		<table class="main-table">
			<tr>
				<td colspan="13" class="currency-header">{currency_display}</td>
			</tr>
			<tr>
				<th rowspan="1" class="sales-person">Sales Person</th>
				<th colspan="2">Approval</th>
				<th colspan="2">Invoicing</th>
				<th colspan="2">Collection</th>
				<th colspan="2">Cumulative Approval</th>
				<th colspan="2">Cumulative Invoicing</th>
				<th colspan="2">Cumulative Collection</th>
			</tr>
			<tr class="section-header">
				<th></th>
				<th>Actual</th>
				<th>Target</th>
				<th>Actual</th>
				<th>Target</th>
				<th>Actual</th>
				<th>Target</th>
				<th class="cumulative-bg">Actual</th>
				<th class="cumulative-bg">Target</th>
				<th class="cumulative-bg">Actual</th>
				<th class="cumulative-bg">Target</th>
				<th class="cumulative-bg">Actual</th>
				<th class="cumulative-bg">Target</th>
			</tr>
		'''

		# Reset totals for each branch
		total_inv = total_target_inv = 0
		total_app = total_target_app = 0
		total_col = total_target_col = 0
		total_inv2 = total_target_inv2 = 0
		total_app2 = total_target_app2 = 0
		total_col2 = total_target_col2 = 0

		for sp in br["sales_persons"]:
			# Filter by sales person if specified
			if sales_person and sales_person != sp["sales_name"]:
				continue

			sales_person_name = sp["name"]
			
			sales_target_doc = frappe.get_value("Sales Target",{"sales":sales_person_name},"name")

			monthly_approval_target = 0
			monthly_invoice_target = 0
			monthly_collection_target = 0

			monthly_approval_target2 = 0
			monthly_invoice_target2 = 0
			monthly_collection_target2 = 0

			if sales_target_doc:
				from_date = frappe.utils.getdate(from_date)
				to_date = frappe.utils.getdate(to_date)
				
				doc = frappe.get_doc("Sales Target", sales_target_doc)

				for row in doc.target_table:
					# row.from_date, row.to_date

					# ✅ check if month falls inside selected range
					if row.from_date and row.to_date:
						if row.from_date >= from_date and row.to_date <= to_date:

							monthly_approval_target += row.quotation_approval_target or 0
							monthly_invoice_target += row.invoice_target or 0
							monthly_collection_target += row.collection_target or 0

					# ✅ current year till current month (c_month_range logic replacement)
					# today = frappe.utils.today()
					today = datetime.today().date()
					month_end = frappe.utils.get_last_day(frappe.utils.getdate())
					if row.from_date and row.to_date:
						if row.from_date >= datetime(today.year, 1, 1).date() and row.to_date <= month_end:

							monthly_approval_target2 += row.quotation_approval_target or 0
							monthly_invoice_target2 += row.invoice_target or 0
							monthly_collection_target2 += row.collection_target or 0

			# Get actual values (current month range - year start to now)
			app_result2 = frappe.db.sql("""
				SELECT SUM(grand_total) as total
				FROM `tabQuotation`
				WHERE sales_person=%s and workflow_state in ("Approved by Customer")
				AND approval_date BETWEEN %s AND %s
			""", (sp["name"], start_date, end_date), as_dict=True)
			app2 = app_result2[0]["total"] or 0 if app_result2 else 0

			inv_result2 = frappe.db.sql("""
				SELECT SUM(grand_total) as total
				FROM `tabSales Invoice`
				WHERE sales_person=%s AND status != "Cancelled"
				AND posting_date BETWEEN %s AND %s
			""", (sp["name"], start_date, end_date), as_dict=True)
			inv2 = inv_result2[0]["total"] or 0 if inv_result2 else 0

			col_result2 = frappe.db.sql("""
			SELECT
				SUM(per.allocated_amount) AS total
			FROM `tabPayment Entry` pe
			INNER JOIN `tabPayment Entry Reference` per
				ON per.parent = pe.name
			INNER JOIN `tabSales Invoice` si
				ON si.name = per.reference_name
			WHERE pe.posting_date BETWEEN %s AND %s
			AND pe.docstatus = 1
			AND pe.payment_type = 'Receive'
			AND si.sales_person = %s
			""", (start_date, end_date, sp["name"]), as_dict=True)
			col2 = col_result2[0]["total"] or 0 if col_result2 else 0

			# Get actual values (cumulative - date range)
			app_result = frappe.db.sql("""
				SELECT SUM(grand_total) as total
				FROM `tabQuotation`
				WHERE sales_person=%s and workflow_state in ("Approved by Customer")
				AND approval_date BETWEEN %s AND %s
			""", (sp["name"], from_date, to_date), as_dict=True)
			app = app_result[0]["total"] or 0 if app_result else 0

			inv_result = frappe.db.sql("""
				SELECT SUM(grand_total) as total
				FROM `tabSales Invoice`
				WHERE sales_person=%s AND status != "Cancelled"
				AND posting_date BETWEEN %s AND %s
			""", (sp["name"], from_date, to_date), as_dict=True)
			inv = inv_result[0]["total"] or 0 if inv_result else 0

			col_result = frappe.db.sql("""
			SELECT
				SUM(per.allocated_amount) AS total
			FROM `tabPayment Entry` pe
			INNER JOIN `tabPayment Entry Reference` per
				ON per.parent = pe.name
			INNER JOIN `tabSales Invoice` si
				ON si.name = per.reference_name
			WHERE pe.posting_date BETWEEN %s AND %s
			AND pe.docstatus = 1
			AND pe.payment_type = 'Receive'
			AND si.sales_person = %s
			""", (from_date, to_date, sp["name"]), as_dict=True)
			col = col_result[0]["total"] or 0 if col_result else 0

			# Calculate percentages (current month range)
			pct_app2 = round((app2 / monthly_approval_target2) * 100) if monthly_approval_target2 else 0
			pct_inv2 = round((inv2 / monthly_invoice_target2) * 100) if monthly_invoice_target2 else 0
			pct_col2 = round((col2 / monthly_collection_target2) * 100) if monthly_collection_target2 else 0

			# Calculate percentages (cumulative)
			pct_app = round((app / monthly_approval_target) * 100) if monthly_approval_target else 0
			pct_inv = round((inv / monthly_invoice_target) * 100) if monthly_invoice_target else 0
			pct_col = round((col / monthly_collection_target) * 100) if monthly_collection_target else 0

			# Get colors
			app_color2 = get_percentage_color(pct_app2)
			inv_color2 = get_percentage_color(pct_inv2)
			col_color2 = get_percentage_color(pct_col2)

			app_color = get_percentage_color(pct_app)
			inv_color = get_percentage_color(pct_inv)
			col_color = get_percentage_color(pct_col)

			# Update totals
			total_app2 += app2
			total_target_app2 += monthly_approval_target2
			total_inv2 += inv2
			total_target_inv2 += monthly_invoice_target2
			total_col2 += col2
			total_target_col2 += monthly_collection_target2

			total_app += app
			total_target_app += monthly_approval_target
			total_inv += inv
			total_target_inv += monthly_invoice_target
			total_col += col
			total_target_col += monthly_collection_target

			# Add row for this sales person
			data += f'''
				<tr>
					<td rowspan="2" class="sales-person">{sp["sales_name"]}</td>
					<td>{format_number(app)}</td>
					<td>{format_number(monthly_approval_target)}</td>
					<td>{format_number(inv)}</td>
					<td>{format_number(monthly_invoice_target)}</td>
					<td>{format_number(col)}</td>
					<td>{format_number(monthly_collection_target)}</td>
					<td class="cumulative-bg">{format_number(app2)}</td>
					<td class="cumulative-bg">{format_number(monthly_approval_target2)}</td>
					<td class="cumulative-bg">{format_number(inv2)}</td>
					<td class="cumulative-bg">{format_number(monthly_invoice_target2)}</td>
					<td class="cumulative-bg">{format_number(col2)}</td>
					<td class="cumulative-bg">{format_number(monthly_collection_target2)}</td>
				</tr>
				<tr>
					<td colspan="2" style="{app_color}">{pct_app}%</td>
					<td colspan="2" style="{inv_color}">{pct_inv}%</td>
					<td colspan="2" style="{col_color}">{pct_col}%</td>
					<td class="cumulative-bg" colspan="2" style="{app_color2}">{pct_app2}%</td>
					<td class="cumulative-bg" colspan="2" style="{inv_color2}">{pct_inv2}%</td>
					<td class="cumulative-bg" colspan="2" style="{col_color2}">{pct_col2}%</td>
				</tr>
			'''

		# Calculate total percentages for the branch
		total_pct_app2 = round((total_app2 / total_target_app2) * 100) if total_target_app2 else 0
		total_pct_inv2 = round((total_inv2 / total_target_inv2) * 100) if total_target_inv2 else 0
		total_pct_col2 = round((total_col2 / total_target_col2) * 100) if total_target_col2 else 0

		total_pct_app = round((total_app / total_target_app) * 100) if total_target_app else 0
		total_pct_inv = round((total_inv / total_target_inv) * 100) if total_target_inv else 0
		total_pct_col = round((total_col / total_target_col) * 100) if total_target_col else 0

		# Get colors for total percentages
		total_app_color2 = get_percentage_color(total_pct_app2)
		total_inv_color2 = get_percentage_color(total_pct_inv2)
		total_col_color2 = get_percentage_color(total_pct_col2)

		total_app_color = get_percentage_color(total_pct_app)
		total_inv_color = get_percentage_color(total_pct_inv)
		total_col_color = get_percentage_color(total_pct_col)

		# Add total row for the branch
		data += f'''
			<tr class="total-row">
				<td><strong>Total</strong></td>
				<td><strong>{format_number(total_app)}</strong></td>
				<td><strong>{format_number(total_target_app)}</strong></td>
				<td><strong>{format_number(total_inv)}</strong></td>
				<td><strong>{format_number(total_target_inv)}</strong></td>
				<td><strong>{format_number(total_col)}</strong></td>
				<td><strong>{format_number(total_target_col)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_app2)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_target_app2)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_inv2)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_target_inv2)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_col2)}</strong></td>
				<td class="cumulative-bg"><strong>{format_number(total_target_col2)}</strong></td>
			</tr>
			<tr class="total-row">
				<td><strong></strong></td>
				<td colspan="2" style="{total_app_color}"><strong>{total_pct_app}%</strong></td>
				<td colspan="2" style="{total_inv_color}"><strong>{total_pct_inv}%</strong></td>
				<td colspan="2" style="{total_col_color}"><strong>{total_pct_col}%</strong></td>
				<td class="cumulative-bg" colspan="2" style="{total_app_color2}"><strong>{total_pct_app2}%</strong></td>
				<td class="cumulative-bg" colspan="2" style="{total_inv_color2}"><strong>{total_pct_inv2}%</strong></td>
				<td class="cumulative-bg" colspan="2" style="{total_col_color2}"><strong>{total_pct_col2}%</strong></td>
			</tr>
			</table>
		</div>
		<br>
		'''

	# Show "No data found" message if no data to display
	if not has_data_to_display:
		data += '''
		<div style="text-align:center; padding:40px; color:#666; font-size:16px;">
			No data found for the selected filters.
		</div>
		'''

	return data

@frappe.whitelist()
def get_technician_service_report(doc_name):
	technician_names = set()
	try:
		doc = frappe.get_doc("Technical Report", doc_name)

		for tech_row in doc.technician:
			if tech_row.technician:
				# Get the actual technician name from linked Technician ID
				tech_name = frappe.db.get_value("Technician ID", tech_row.technician, "technician")
				if tech_name:
					technician_names.add(tech_name)

		return ", ".join(sorted(technician_names)) if technician_names else "-"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Technicians Error")
		return "-"

@frappe.whitelist()
def check_wo_ap():
	from_date = "2026-01-01"
	to_date = "2026-04-30"
	sales_person_name = "Yazeed"
			
	sales_target_doc = frappe.get_value("Sales Target",{"sales":sales_person_name},"name")

	monthly_approval_target = 0
	monthly_invoice_target = 0
	monthly_collection_target = 0

	monthly_approval_target2 = 0
	monthly_invoice_target2 = 0
	monthly_collection_target2 = 0

	if sales_target_doc:
		from_date = frappe.utils.getdate(from_date)
		to_date = frappe.utils.getdate(to_date)
		
		doc = frappe.get_doc("Sales Target", sales_target_doc)

		for row in doc.target_table:
			
			# row.from_date, row.to_date

			# ✅ check if month falls inside selected range
			if row.from_date and row.to_date:
				if row.from_date >= from_date and row.to_date <= to_date:
					print(row.quotation_approval_target)

					monthly_approval_target += row.quotation_approval_target or 0
					monthly_invoice_target += row.invoice_target or 0
					monthly_collection_target += row.collection_target or 0

			# ✅ current year till current month (c_month_range logic replacement)
			# today = frappe.utils.today()
			today = datetime.today().date()
			if row.from_date and row.to_date:
				if row.from_date >= datetime(today.year, 1, 1).date() and row.to_date <= today:

					monthly_approval_target2 += row.quotation_approval_target or 0
					monthly_invoice_target2 += row.invoice_target or 0
					monthly_collection_target2 += row.collection_target or 0

	# print(monthly_approval_target)



import frappe
from datetime import datetime

@frappe.whitelist()
def get_receivable(customer, from_date, to_date, company):

    data = ''

    # 🔹 Premium Styling (Enterprise look)
    data += """
    <style>
    .table-receivable {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, sans-serif;
        color: #2c3e50;
    }

    .table-receivable th {
        background-color: #1a4d8c !important;
        color: #ffffff !important;
        font-size: 12px;
        font-weight: 600;
        padding: 10px 8px;
        text-align: center;
        border-bottom: 2px solid #163d6b;
        letter-spacing: 0.3px;
    }

    .table-receivable td {
        font-size: 11px;
        padding: 8px 6px;
        border-bottom: 1px solid #e6e9ef;
    }

    .table-receivable tr:nth-child(even) {
        background-color: #fbfcfe;
    }

    .table-receivable tr:hover {
        background-color: #f1f6ff;
    }

    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .bold { font-weight: 600; }

    .invoice-link {
        text-decoration: none;
        color: #1a4d8c;
        font-weight: 600;
    }

    .invoice-link:hover {
        text-decoration: underline;
    }

    .total-row td {
        border-top: 2px solid #1a4d8c;
        background-color: #f4f7fb;
        font-size: 12px;
    }

    .currency {
        color: #7f8c8d;
        font-weight: 500;
    }
    </style>
    """

    # 🔹 Table Start
    data += '<table class="table-receivable">'

    # 🔹 Header (INLINE color for PDF safety)
    data += """
    <tr>
        <th style="color:#fff !important;">Due Date</th>
        <th style="color:#fff !important;">Invoice No</th>
        <th style="color:#fff !important;">Ref(WOD)</th>
        <th style="color:#fff !important;">Ref(PO)</th>
        <th style="color:#fff !important;">Invoiced</th>
        <th style="color:#fff !important;">Paid</th>
        <th style="color:#fff !important;">Outstanding</th>
    </tr>
    """

    # 🔹 Fetch Data
    si_list = frappe.get_all(
        "Sales Invoice",
        filters={
            "company": company,
            "status": ["in", ["Overdue", "Unpaid"]],
            "customer": customer,
            "posting_date": ["between", (from_date, to_date)]
        },
        fields=["name", "due_date", "grand_total", "outstanding_amount", "po_no"],
        order_by="posting_date asc"
    )

    total_outstanding = 0

    for i in si_list:

        # Skip return invoices
        if frappe.db.exists("Sales Invoice", {"return_against": i.name}):
            continue

        total_outstanding += i.outstanding_amount

        # 🔹 Date Format
        formatted_due_date = datetime.strptime(
            str(i.due_date), "%Y-%m-%d"
        ).strftime("%d-%m-%Y")

        # 🔹 WOD Fetch
        jo_data = frappe.db.sql("""
            SELECT DISTINCT job_order_data AS jo
            FROM `tabSales Invoice Item`
            WHERE parent = %s
        """, (i.name,), as_dict=1)

        jods = []
        for j in jo_data:
            if j.get("jo"):
                jods.append(str(j["jo"])[7:])  # trimming prefix

        jod = ', '.join(jods) if jods else ''
        po_no = i.po_no or ''

        # 🔹 Amounts
        gt = "{:,.3f}".format(i.grand_total)
        paid = "{:,.3f}".format(i.grand_total - i.outstanding_amount)
        outs = "{:,.3f}".format(i.outstanding_amount)

        # 🔹 Default link (avoid undefined variable)
        link = "#"

        if company == "Cyrix TSL - Kuwait":
            link = f"https://erp.cyrix-tsl.com/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={i.name}&format=INV/KW/V2&no_letterhead=0&letterhead=0"

        elif company == "Company Al-Halloul Faniye Medical":
            link = f"https://erp.cyrix-tsl.com/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={i.name}&format=INV/KSA&no_letterhead=0&letterhead=0"

        # 🔹 Row
        data += f"""
        <tr>
            <td>{formatted_due_date}</td>
            <td class="text-center">
                <a href="{link}" class="invoice-link" target="_blank">{i.name}</a>
            </td>
            <td class="text-center">{jod}</td>
            <td class="text-center">{po_no}</td>
            <td class="text-right">{gt}</td>
            <td class="text-right">{paid}</td>
            <td class="text-right bold">{outs}</td>
        </tr>
        """

    # 🔹 Total Row
    currency = frappe.get_value("Company", company, "default_currency")
    total_formatted = "{:,.3f}".format(total_outstanding)

    data += f"""
    <tr class="total-row">
        <td colspan="6" class="text-right bold">
            Balance Due <span class="currency">({currency})</span>
        </td>
        <td class="text-right bold">{total_formatted}</td>
    </tr>
    """

    data += '</table>'
    data += '<p></p>'

    return data