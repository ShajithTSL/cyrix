# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff,nowdate
from frappe.core.doctype.communication.email import make


class OfficialDocuments(Document):
	pass

def schedule_email_notifications():
	anniversary = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.cyrix_tsl.doctype.official_documents.official_documents.trigger_mail_notification'})
	if not anniversary:
		sjt1 = frappe.new_doc("Scheduled Job Type")  
		sjt1.update({
			"method" : 'cyrix.cyrix_tsl.doctype.official_documents.official_documents.trigger_mail_notification',
			"frequency" : 'Daily',
		})
		sjt1.save(ignore_permissions=True)

def trigger_mail_notification():
	MAIL_HEADER = '''Dear Mam/Sir,<br><br>{document} is expiring within {days} days.<br><br>'''

	MAIL_BODY = '''This is to inform you that the {document} is due to expire in {days} Days.<br><br>
					HR is requested to initiate the {document} renewal process with the relevant authority in a timely manner to ensure continuity and compliance.<br><br>
					Once the renewal is completed, kindly obtain and file a scanned copy of the renewed {document} and update the expiry date in Official Documents List.<br><br>'''

	notify_days = [45, 30, 15, 3,5]
	today = nowdate()

	official_documents = frappe.db.sql("""
		SELECT 
			de.name as expiry_detail_name,
			de.expiry_date,
			de.status,
			od.name as document_name
		FROM `tabDocuments Expiry Details` de
		LEFT JOIN `tabOfficial Documents` od
			ON de.parent = od.name
		WHERE de.expiry_date IS NOT NULL
		AND de.status = 'Active'
	""", as_dict=1)

	for doc in official_documents:
		expiry_days = date_diff(doc.expiry_date, today)

		if expiry_days == 0:
			subject = f"Document {doc.document_name} has expired."
			message = f"Document <b>{doc.document_name}</b> has expired."
			
			make(
				recipients='hr1@tsl-me.com',
				cc = [
					"yousuf@tsl-me.com"
				],
				sender="no-reply@tsl-me.com",
				reply_to="no-reply@tsl-me.com",
				subject = subject,
				content = message,
				send_email=1
			)

			# Mark as Expired
			frappe.db.set_value(
				"Documents Expiry Details",
				doc.expiry_detail_name,
				"status",
				"Expired"
			)

		elif expiry_days in notify_days:
			subject = f"Document {doc.document_name} is expiring in {expiry_days} days - Cyrix."

			header = MAIL_HEADER.format(days=expiry_days, document=doc.document_name)
			body = MAIL_BODY.format(days=expiry_days, document=doc.document_name)

			message=header + body
			make(
				recipients='hr1@tsl-me.com',
				cc = [
					"yousuf@tsl-me.com"
				],
				sender="no-reply@cyrix-tsl.com",
				reply_to="no-reply@cyrix-tsl.com",
				subject = subject,
				content = message,
				send_email=1
			)