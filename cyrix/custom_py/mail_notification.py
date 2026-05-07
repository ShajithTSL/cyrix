import frappe

@frappe.whitelist()
def purchase_msg_to_info(com,branch,ev,sender):
    frappe.errprint(branch)
    frappe.errprint(com)
    info = "karthiksrinivasan1996.ks@gmail.com"
    if com == "Cyrix TSL - Kuwait":
        info = "info@cyrix-tsl.com"
        
    if com == "Company Al-Halloul Faniye Medical":
        info = "info-sa@cyrix-tsl.com"
        
   
    frappe.sendmail(recipients=[info],
			sender = sender,
			subject="Part sheet Comments",
			message=""" <b>Dear Lab Coordinator,</b><br>
            Kindly find the comment for the Evaluation report  <b>%s</b> . Please take action to  <a href="https://erp.tsl-me.com/app/evaluation-report/%s"target="_blank">click here.</a>
		   
			""" %(ev,ev)
			)
    frappe.msgprint("Message sent Successfully")
            

    