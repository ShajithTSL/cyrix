import frappe

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
	data+= '<th class="text-center" ><b style = "color:#4a5568" >WO</b></th>'
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

