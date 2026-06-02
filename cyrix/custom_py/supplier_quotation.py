import frappe
import requests
from erpnext.setup.utils import get_exchange_rate
from frappe.core.doctype.communication.email import make
from frappe.utils import now
from frappe import _

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

    if doc.get("custom_replacement_unit"):
        rep = frappe.get_doc("Job Order Data",doc.get("custom_replacement_unit"))
        rep.status = "Parts Priced"
        rep.save()

    
        r = frappe.get_doc("Replacement Unit",doc.get("custom_replacement_unit"))
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
    if self.custom_replacement_unit:
        rp = frappe.get_doc("Replacement Unit",self.get("custom_replacement_unit"))
        rp.status =  "Parts Priced"
        rp.save(ignore_permissions = 1)

        
        so = frappe.get_doc("Job Order Data",self.get("custom_replacement_unit"))
        so.unit_status = ""
        so.status = "Parts Priced"
        for i in self.items:
            so.append("item_price_details",{
            "supplier":self.supplier,
            "price": i.base_rate,
            "amount":i.base_amount,
            "job_order_data":self.get("custom_replacement_unit"),
            "item":i.item_code,
            "model":i.model_number,
            "item_source":"Supplier",
            "supplier_quotation":self.name
            })
        so.save(ignore_permissions = 1)



@frappe.whitelist()
def get_sq_details(so):

    data = frappe.db.sql("""
    SELECT
        sq.name,
        sq.currency,
        sq.supplier,
        sq.shipping_cost,
        sq.grand_total,

        sqi.item_code,
        sqi.qty,
        sqi.rate,
        sqi.amount,
        sqi.model_number AS  model,
        sqi.item_name,

        ptc.description,
        ptc.tax_amount

        FROM `tabSupplier Quotation` sq

        LEFT JOIN `tabSupplier Quotation Item` sqi
            ON sqi.parent = sq.name

        LEFT JOIN `tabPurchase Taxes and Charges` ptc
            ON ptc.parent = sq.name

        WHERE sq.supply_order_data = %s

        ORDER BY sq.name, ptc.idx
        """, (so,), as_dict=True)
    

    return data

def get_sq_details1():

    data = frappe.db.sql("""
    SELECT
        sq.name,
        sq.currency,
        sq.supplier,
        sq.shipping_cost,
        sq.grand_total,

        sqi.item_code,
        sqi.qty,
        sqi.rate,
        sqi.amount,
        sqi.model_number  model,
        sqi.item_name,

        ptc.description,
        ptc.tax_amount

        FROM `tabSupplier Quotation` sq

        LEFT JOIN `tabSupplier Quotation Item` sqi
            ON sqi.parent = sq.name

        LEFT JOIN `tabPurchase Taxes and Charges` ptc
            ON ptc.parent = sq.name

        WHERE sq.supply_order_data = %s

        ORDER BY sq.name, ptc.idx
        """, ('SO-R26-11468',), as_dict=True)
    

    print(data)


@frappe.whitelist()
def update_so_status(self,method):
    info = ""
    if self.branch:
        br_info = frappe.get_value("Branch",self.branch,"customer_support")
        if br_info:
            info = br_info
    if self.supply_order_data and self.workflow_state == "On Review":
        so = frappe.get_doc("Supply Order Data",self.supply_order_data)
        so.status = "Supplier Quoted"
        so.save(ignore_permissions = 1)

        
       
        subject = f"Supplier Quotation Created - {self.name}"

        message = f"""
        Dear Info,

        <br><br>

        Supplier Quotation <b>{self.name}</b> has been created successfully.

        <br><br>

        <b>Supplier :</b> {self.supplier}<br>
        <b>Grand Total :</b> {self.grand_total}<br>
        <b>Currency :</b> {self.currency}

        <br><br>

        Regards,<br>
        ERP System
        """
        
        # Create Communication
        frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "sent_or_received": "Sent",
            "subject": subject,
            "content": message,
            "reference_doctype": self.doctype,
            "reference_name": self.name,
            "sender": frappe.session.user,
            "recipients": "support@cyrix-tsl.com"
        }).insert(ignore_permissions=True)

        # Send Email
        frappe.sendmail(
            recipients=[info],
            subject=subject,
            message=message
        )

        frappe.msgprint("Purchaser notified successfully")
   
@frappe.whitelist()
def update_so(self,method):
    info = ""
    if self.branch:
        br_info = frappe.get_value("Branch",self.branch,"customer_support")
        if br_info:
            info = br_info

    if self.supply_order_data and self.workflow_state == "Notified":
        so = frappe.get_doc("Supply Order Data",self.supply_order_data)
        
        message = f"""
            Dear Info,

            <br><br>

            Supplier quotation <b>{self.name}</b> has been created.

            <br><br>

            <b>Supplier :</b> {self.supplier}<br>
            <b>Grand Total :</b> {self.grand_total}

            <br><br>

            Regards,<br>
            ERP System
        """

        make_communication(
            communication_type="Communication",
            communication_medium="Email",
            sent_or_received="Sent",
            subject=subject,
            content=message,
            sender=frappe.session.user,
            recipients="support@cyrix-tsl.com",
            reference_doctype=self.doctype,
            reference_name=self.name
        )

        frappe.sendmail(
            recipients=[info],
            subject=subject,
            message=message
        )
        frappe.msgprint("Purchaser notified successfully")



    

         