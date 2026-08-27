import frappe
import requests
from erpnext.setup.utils import get_exchange_rate
from frappe.core.doctype.communication.email import make
from frappe.utils import now
from frappe import _
from frappe.core.doctype.communication.email import _make as make_communication


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
                rate = i.get("base_net_rate")
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

@frappe.whitelist()
def revert_approved_orders(supplier_quotation):

    sq = frappe.get_doc("Supplier Quotation", supplier_quotation)

    for item in sq.items:

        # Job Order Data
        if item.job_order_data:
            jo = frappe.get_doc("Job Order Data", item.job_order_data)

            if jo.is_approved:
                jo.status = "Parts Priced"
                jo.save()

        # Supply Order Data
        if item.supply_order_data:
            so = frappe.get_doc("Supply Order Data", item.supply_order_data)

            if so.is_approved:
                so.status = "Parts Priced"
                so.save()

def update_job_order_status(doc,method):
    for i in doc.items:
        if i.job_order_data:
            jo = frappe.get_doc("Job Order Data",i.job_order_data)
            if not jo.is_approved:
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
                    j.price = i.get("base_net_rate")     
                    j.amount = i.get("base_net_rate") * float(j.quantity)
                    j.supplier_quotation = self.name
            if not doc.is_approved:
                doc.status = "Parts Priced"
            doc.save(ignore_permissions=True)

def update_budgetary_quotation(self,method):
    for i in self.get('items'):
        if i.budgetary_quotation:
            doc = frappe.get_doc("Budgetary Quotation",i.budgetary_quotation)
            for j in doc.get('items'):
                if j.sku == i.item_code:
                    j.rate = i.get("base_net_rate")
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
            "price": i.get("base_net_rate"),
            "amount":i.get("base_net_amount"),
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
        sq.terms,

        sqi.item_code,
        sqi.qty,
        sqi.net_rate as rate,
        sqi.net_amount as amount,
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
            AND sq.docstatus != 2

        ORDER BY sq.name, ptc.idx
        """, (so,), as_dict=True)
    

    return data



@frappe.whitelist()
def get_sq_details_for_bq(bq):

    data = frappe.db.sql("""
    SELECT
        sq.name,
        sq.currency,
        sq.supplier,
        sq.shipping_cost,
        sq.grand_total,
        sq.terms,

        sqi.item_code,
        sqi.qty,
        sqi.net_rate as rate,
        sqi.net_amount as amount,
        sqi.model_number AS  model,
        sqi.item_name,

        ptc.description,
        ptc.tax_amount

        FROM `tabSupplier Quotation` sq

        LEFT JOIN `tabSupplier Quotation Item` sqi
            ON sqi.parent = sq.name

        LEFT JOIN `tabPurchase Taxes and Charges` ptc
            ON ptc.parent = sq.name

        WHERE sq.budgetary_quotation = %s

        ORDER BY sq.name, ptc.idx
        """, (bq,), as_dict=True)
    

    return data

def get_sq_details1():

    sq_data = frappe.db.sql("""
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
            sqi.model_number AS model,
            sqi.item_name

        FROM `tabSupplier Quotation` sq
        LEFT JOIN `tabSupplier Quotation Item` sqi
            ON sqi.parent = sq.name
        WHERE sq.supply_order_data = %s
        ORDER BY sq.name
    """, ('SO-DU26-02839',), as_dict=True)

    tax_data = frappe.db.sql("""
        SELECT
            parent,
            charge_type,
            account_head,
            description,
            rate,
            tax_amount,
            total,
            base_tax_amount,
            base_total
        FROM `tabPurchase Taxes and Charges`
        WHERE parent IN (
            SELECT name
            FROM `tabSupplier Quotation`
            WHERE supply_order_data = %s
        )
        ORDER BY parent, idx
    """, ('SO-DU26-02839',), as_dict=True)

    frappe.errprint(tax_data)

    return {
        "items": sq_data,
        "taxes": tax_data
    }


@frappe.whitelist()
def update_so_status(self,method):
    info = ""
    if self.branch:
        br_info = frappe.get_value("Branch",self.branch,"customer_support")
        if br_info:
            info = br_info
    if self.supply_order_data and self.workflow_state == "On Review":

        quotation_exists = frappe.db.sql("""
        SELECT q.name
        FROM `tabQuotation Item` qi
        INNER JOIN `tabQuotation` q
            ON q.name = qi.parent
        WHERE qi.supply_order_data = %s
          AND q.quotation_type IN ('Customer Quotation - Supply','Internal Quotation - Supply')
        LIMIT 1
        """, (self.supply_order_data,))

        if not quotation_exists:
            so = frappe.get_doc("Supply Order Data", self.supply_order_data)
            so.status = "Supplier Quoted"
            so.save(ignore_permissions=True)

        
               
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
            "recipients": info
        }).insert(ignore_permissions=True)

        # Send Email
        frappe.sendmail(
            recipients=[info],
            subject=subject,
            sender=frappe.session.user,
            message=message
        )

        frappe.msgprint("Notified successfully")


@frappe.whitelist()
def update_jo_status(self,method):
    info = ""
    if self.branch:
        br_info = frappe.get_value("Branch",self.branch,"customer_support")
        if br_info:
            info = br_info
    if self.job_order_data and self.workflow_state == "On Review":

        quotation_exists = frappe.db.sql("""
        SELECT q.name
        FROM `tabQuotation Item` qi
        INNER JOIN `tabQuotation` q
            ON q.name = qi.parent
        WHERE qi.job_order_data = %s
          AND q.quotation_type IN ('Customer Quotation - Repair','Internal Quotation - Repair')
        LIMIT 1
        """, (self.job_order_data,))

        if not quotation_exists:
            jo = frappe.get_doc("Job Order Data", self.Job_order_data)
            jo.status = "Supplier Quoted"
            jo.save(ignore_permissions=True)

        
               
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
            "recipients": info
        }).insert(ignore_permissions=True)

        # Send Email
        frappe.sendmail(
            recipients=[info],
            subject=subject,
            message=message
        )

        frappe.msgprint("Notified successfully")



@frappe.whitelist()
def update_bq_status(self,method):
    info = ""
    if self.branch:
        br_info = frappe.get_value("Branch",self.branch,"customer_support")
        if br_info:
            info = br_info
    if self.budgetary_quotation and self.workflow_state == "On Review":
        quotation_exists = frappe.db.sql("""
        SELECT q.name
        FROM `tabQuotation Item` qi
        INNER JOIN `tabQuotation` q
        ON q.name = qi.parent
        WHERE qi.budgetary_quotation = %s
        AND q.quotation_type IN ('Customer Quotation - BQ','Internal Quotation - BQ')
        LIMIT 1
        """, (self.budgetary_quotation,))

        if not quotation_exists:
            bq = frappe.get_doc("Budgetary Quotation",self.budgetary_quotation)
            bq.status = "Supplier Quoted"
            bq.save(ignore_permissions=True)

        
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
            "recipients": info
        }).insert(ignore_permissions=True)

        # Send Email
        frappe.sendmail(
            recipients=[info],
            subject=subject,
            message=message
        )

        frappe.msgprint("Notified successfully")

        
   
# @frappe.whitelist()
# def update_so(self,method):
#     info = ""
#     if self.branch:
#         br_info = frappe.get_value("Branch",self.branch,"customer_support")
#         if br_info:
#             info = br_info

#     if self.supply_order_data and self.workflow_state == "Notified":
#         so = frappe.get_doc("Supply Order Data",self.supply_order_data)
#         subject = f"Supplier Quotation Created - {self.name}"
#         message = f"""
#             Dear Info,

#             <br><br>

#             Supplier quotation <b>{self.name}</b> has been created.

#             <br><br>

#             <b>Supplier :</b> {self.supplier}<br>
#             <b>Grand Total :</b> {self.grand_total}

#             <br><br>

#             Regards,<br>
#             ERP System
#         """

#         make_communication(
#             communication_type="Communication",
#             communication_medium="Email",
#             sent_or_received="Sent",
#             subject=subject,
#             content=message,
#             sender=frappe.session.user,
#             recipients="support@cyrix-tsl.com",
#             reference_doctype=self.doctype,
#             reference_name=self.name
#         )

#         frappe.sendmail(
#             recipients=[info],
#             subject=subject,
#             message=message
#         )
#         frappe.msgprint("Purchaser notified successfully")


import frappe
from frappe.core.doctype.communication.email import make

@frappe.whitelist()
def update_so(self, method):
    info = ""

    if self.branch:
        br_info = frappe.get_value("Branch", self.branch, "customer_support")
        if br_info:
            info = br_info

    if self.supply_order_data and self.workflow_state == "Notified":

        subject = f"Supplier Quotation Created - {self.name}"

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

        # Create Communication
        comm = frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "sent_or_received": "Sent",
            "subject": subject,
            "content": message,
            "sender": frappe.session.user,
            "recipients": info,
            "reference_doctype": self.doctype,
            "reference_name": self.name
        })
        comm.insert(ignore_permissions=True)

        # Send Email
        if info:
            frappe.sendmail(
                recipients=[info],
                subject=subject,
                message=message
            )

        frappe.msgprint("Notified successfully")
    

         