import frappe
import requests
from erpnext.setup.utils import get_exchange_rate

def on_cancel(self, method):
    for i in self.get("items"):
        eval_list = frappe.db.sql("""select name from `tabEvaluation Report` where job_order_data = '%s' and docstatus = 1 """%(i.job_order_data),as_dict=1)
        for d in eval_list:
            doc = frappe.get_doc("Evaluation Report",d.name)
            for j in doc.get("items"):
                if j.part == i.item_code and j.qty == i.qty:
                    j.price_ea = 0
                    j.total = 0
            doc.save(ignore_permissions=True)

def update_price(self,method):
    if self.job_order_data:
        evl = frappe.get_value("Evaluation Report",{"job_order_data":self.job_order_data})
        if evl:
            doc = frappe.get_doc("Evaluation Report",evl)
            for i in self.get("items"):
                com_cur = frappe.get_value("Company",self.company,"default_currency")
                ex_rate = get_exchange_rate(self.currency,com_cur)
                rate = i.rate * ex_rate
                for j in doc.get("items"):
                    if j.part == i.item_code:
                        j.price_ea = rate
                        j.total = rate * j.qty
            add = 0
            for i in doc.items:
                add += j.total
            doc.total_amount = add

            doc.save(ignore_permissions=True)

def update_eval_report_status(doc,method):
    for i in doc.items:
        if i.job_order_data:
            doc = frappe.db.sql("""select name,status,job_order_data from `tabEvaluation Report` where job_order_data = '%s' and docstatus != 2 """%(i.job_order_data),as_dict=1)
            for d in doc:
                eval = frappe.get_doc("Evaluation Report",d.name)
                eval.status = "Supplier Quoted"
                eval.save()

def update_job_order_status(doc,method):
    for i in doc.items:
        if i.job_order_data:
            jo = frappe.get_doc("Job Order Data",i.job_order_data)
            jo.status = "Parts Priced"
            jo.save()

    if doc.custom_replacement_unit:
        rep = frappe.get_doc("Job Order Data",doc.custom_replacement_unit)
        rep.status = "Parts Priced"
        rep.save()

    
        r = frappe.get_doc("Replacement Unit",doc.custom_replacement_unit)
        r.status = "Parts Priced"
        r.save()
        

def update_supply_order_data(self,method):
    for i in self.get('items'):
        if i.supply_order_data:
            doc = frappe.get_doc("Supply Order Data",i.supply_order_data)
            for j in doc.get('material_list'):
                if j.item_code == i.item_code:
                    j.price = i.rate     
                    j.amount = i.rate * float(j.quantity)
                    j.supplier_quotation = self.name
            doc.status = "Parts Priced"
            doc.save(ignore_permissions=True)

def update_budgetary_quotation(self,method):
    for i in self.get('items'):
        if i.budgetary_quotation:
            doc = frappe.get_doc("Budgetary Quotation",i.budgetary_quotation)
            for j in doc.get('items'):
                if j.sku == i.item_code:
                    j.rate = i.base_net_rate
            doc.status = "Parts Priced"
            doc.save(ignore_permissions=True)


def update_price_for_replacement(self,method):
    frappe.errprint(self.custom_replacement_unit)
    sq_item = frappe.db.sql("""
    SELECT 
        sqi.base_rate,
        sqi.base_amount,
        sq.custom_replacement_unit
    FROM `tabSupplier Quotation Item` sqi
    LEFT JOIN `tabSupplier Quotation` sq
        ON sq.name = sqi.parent
    WHERE sq.custom_replacement_unit = %s
    """, (self.custom_replacement_unit), as_dict=True)

    if sq_item:
        print(sq_item)

        # base_rate = sq_item[0].base_rate or 0
        # base_amount = sq_item[0].base_amount or 0
        # replacement_unit = sq_item[0].custom_replacement_unit

        # frappe.db.sql("""
        #     UPDATE `tabItem Price Details`
        #     SET
        #         price = %s,
        #         amount = %s
        #     WHERE parent = %s
        #      """, (
        #     base_rate,
        #     base_amount,
        #     replacement_unit
        # ))

        # frappe.db.commit()

         