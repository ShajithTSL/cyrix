import json
import frappe

@frappe.whitelist()
def get_jo_so_details(references):

    references = json.loads(references)
    jo_so_info = []

    for i in references:
        if i.get("reference_name"):
            jo_details = frappe.db.sql("""
                SELECT DISTINCT 
                    `tabSales Invoice Item`.job_order_data AS job_order_data,
                    `tabSales Invoice Item`.supply_order_data AS supply_order_data,
                    `tabSales Invoice Item`.budgetary_quotation AS budgetary_quotation,

                    `tabSales Invoice`.maintenance_contract AS parent_maintenance_contract,
                    `tabSales Invoice Item`.maintenance_contract AS maintenance_contract
                    
                FROM `tabSales Invoice`
                LEFT JOIN `tabSales Invoice Item` 
                    ON `tabSales Invoice`.name = `tabSales Invoice Item`.parent 
                WHERE `tabSales Invoice`.name = %s
            """, (i["reference_name"],), as_dict=1)
            for jo_entry in jo_details:
                job_order_name = jo_entry.get("job_order_data")
                if job_order_name:
                    job_order_doc = frappe.db.get_value(
                        "Job Order Data", job_order_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if job_order_doc:
                        remaining = (job_order_doc.invoiced_value or 0) - (job_order_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Job Order Data",
                            "reference_name": job_order_name,
                            "invoiced_value": job_order_doc.invoiced_value or 0,
                            "advance_payment_amount": job_order_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })

                supply_order_name = jo_entry.get("supply_order_data")
                if supply_order_name:
                    supply_order_doc = frappe.db.get_value(
                        "Supply Order Data", supply_order_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if supply_order_doc:
                        remaining = (supply_order_doc.invoiced_value or 0) - (supply_order_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Supply Order Data",
                            "reference_name": supply_order_name,
                            "invoiced_value": supply_order_doc.invoiced_value or 0,
                            "advance_payment_amount": supply_order_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })

                bq_name = jo_entry.get("budgetary_quotation")
                if bq_name:
                    bq_doc = frappe.db.get_value(
                        "Budgetary Quotation", bq_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if bq_doc:
                        remaining = (bq_doc.invoiced_value or 0) - (bq_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Budgetary Quotation",
                            "reference_name": bq_name,
                            "invoiced_value": bq_doc.invoiced_value or 0,
                            "advance_payment_amount": bq_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })

                mc_name = jo_entry.get("maintenance_contract") or jo_entry.get("parent_maintenance_contract")
                if mc_name:
                    mc_doc = frappe.db.get_value(
                        "Maintenance Contract", mc_name,
                        ["invoiced_value", "advance_payment_amount"],
                        as_dict=True
                    )
                    if mc_doc:
                        remaining = (mc_doc.invoiced_value or 0) - (mc_doc.advance_payment_amount or 0)
                        paid = 0
                        if remaining == 0:
                            paid = 1
                        
                        jo_so_info.append({
                            "reference_type": "Maintenance Contract",
                            "reference_name": mc_name,
                            "invoiced_value": mc_doc.invoiced_value or 0,
                            "advance_payment_amount": mc_doc.advance_payment_amount or 0,
                            "remaining_to_be_paid": remaining,
                            "paid": paid
                        })
    return jo_so_info


@frappe.whitelist()
def create_payment(bg):
    bg_doc = frappe.get_doc("BG", bg)
    je = frappe.new_doc("Journal Entry")
    
    je.company = bg_doc.company
    je.voucher_type = "Bank Entry"
    je.paid_amount = bg_doc.bid_bg_value
    je.custom_bg = bg
    
    # bg_account = ""
    # account = frappe.get_value("Account",{"company":bg_doc.company},"name")
    # if account:
    #     bg_account = account

    je.append("accounts", {
        "reference_doctype": "BG",
        "supply_order_data": bg_doc.supply_order,
        "work_order_data": bg_doc.job_order,
        "debit_in_account_currency":bg_doc.bid_bg_value,
        "account":"1020701 - Bank Guarantees - CT-K",
        "party_type":"Customer",
        "party":bg_doc.customer,
        "cost_center":bg_doc.department,
        "bank_account":bg_doc.bank_account,


    })

    return je


@frappe.whitelist()
def send_finance(bg):

    doc = frappe.get_doc("BG", bg)

    data = f"""
    <p>Dear Finance Team,</p>

    <p>
        Kindly find below the Bank Guarantee details for your review and further processing.
    </p>

    <table border="1" cellpadding="8" cellspacing="0"
        style="border-collapse:collapse; width:100%; font-family:Arial; font-size:13px;">

        <tr style="background-color:#d9eaf7;">
            <th colspan="2">BG Information</th>
            <th colspan="2">Customer Information</th>
        </tr>

        <tr>
            <td><b>Bank Guarantee Type</b></td>
            <td>{doc.bg_type or ""}</td>

            <td><b>Document Type</b></td>
            <td>{doc.document_type or ""}</td>
        </tr>

        <tr>
            <td><b>Type</b></td>
            <td>{doc.type or ""}</td>

            <td><b>Supply Order</b></td>
            <td>{doc.supply_order or ""}</td>
        </tr>

        <tr>
            <td><b>Contract Value</b></td>
            <td>{doc.contract_value or ""}</td>

            <td><b>Customer</b></td>
            <td>{doc.customer or ""}</td>
        </tr>

        <tr>
            <td><b>Bid Bond/BG Value</b></td>
            <td>{doc.bid_bg_value or ""}</td>

            <td><b>Customer Ref No</b></td>
            <td>{doc.customer_reference or ""}</td>
        </tr>

        <tr>
            <td><b>BG BID Status</b></td>
            <td>{doc.bg_bid_status or ""}</td>

            <td><b>Check No</b></td>
            <td>{doc.cheque_no or ""}</td>
        </tr>

        <tr>
            <td><b>Status</b></td>
            <td>{doc.status or ""}</td>

            <td><b>Start Date</b></td>
            <td>{doc.start_date or ""}</td>
        </tr>

        <tr>
            <td><b>BG No</b></td>
            <td>{doc.bg_no or ""}</td>

            <td><b>End Date</b></td>
            <td>{doc.end_date or ""}</td>
        </tr>

        <tr>
            <td><b>Department</b></td>
            <td>{doc.department or ""}</td>

            <td><b>Order Value %</b></td>
            <td>{doc.order_value_percent or ""}</td>
        </tr>

    </table>

    <br>

    <p>
        Requesting you to proceed with the necessary finance process related to this BG.
    </p>

    <br>

    Regards,<br>
    <b>{frappe.session.user}</b><br>
    TSL
    """

    frappe.sendmail(
        sender="karthick@tsl-me.com",
        recipients=["karthiksrinivasan1996.ks@gmail.com","yousuf@tsl-me.com"],
        subject=f"Finance Approval Pending - {doc.name}",
        message=data
    )
