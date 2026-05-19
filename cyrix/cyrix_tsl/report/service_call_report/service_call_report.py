# Copyright (c) 2024, Tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime,timedelta

def execute(filters=None):
	columns=get_columns(filters)
	data = get_data(filters) 
	return columns, data

def get_columns(filters):

	columns = [
		_("Service Call Form") + ":Link/Service Call Form:160",
		_("Quotation") + ":Link/Quotation:160",
		_("Description") + ":Small Text:200",
		_("Date") + ":Date:120",
		_("Site Visit Date") + ":Date:110",
		_("Status") + ":Data:150",
		_("Customer") + ":Data:150",
		_("Sales Man") + ":Data:150",
		_("Technician") + ":Data:150",
		_("Branch") + ":Data:110",
		_("Plant") + ":Data:110",
		_("Amount") + ":Data:125",
		_("Currency") + ":Data:100",
	
	
	
		
	]	
	return columns

def get_data(filters):
	data = []
	
	sc = frappe.get_all("Service Call Form",{"company":filters.company},["*"])
	for i in sc:
		
		q = frappe.db.exists("Quotation",{"service_call_form":i.name,"workflow_state":["in",["Approved By Customer","Quoted to Customer"]]})
		if q:
			tech = ""
			technicians = frappe.db.sql('''
			SELECT 
				tl.email as user
			FROM 
				`tabTechnician List` AS tl
			WHERE 
				tl.parent = '%s'  AND tl.parenttype = 'Service Call Form' ''' %(i.name), as_dict=True)

			if technicians:
				# Join all technician user emails into one comma-separated string
				tech = ', '.join([t['user'] for t in technicians])
				# frappe.errprint(f"{i.name} → {tech}")
			
			des = frappe.db.sql(''' select `tabQuotation Item`.description from `tabQuotation` 
				left join `tabQuotation Item` on `tabQuotation`.name = `tabQuotation Item`.parent
				where `tabQuotation`.name = %s ''',q,as_dict=1)
			
			frappe.errprint(des)
			qu = frappe.get_value("Quotation",{"name":q},["grand_total"])
			qdate= frappe.get_value("Quotation",{"name":q},["transaction_date"])
			s = frappe.get_value("User",{"name":i.salesman_name},["username"])
			t = frappe.get_value("User",{"name":i.technician_name},["username"])
			cur = frappe.get_value("Quotation",{"name":q},["currency"])
			row = [i.name,q,des[0]["description"],qdate,i.cus_date,i.status,i.customer,i.salesman_name,tech,i.branch,i.plant,qu,cur]
			data.append(row) 
	return data

	





