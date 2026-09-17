# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import nowdate, date_diff, add_years, add_days, today, getdate,get_url_to_form
from cyrix.custom_py.boot import get_bootinfo as info
from frappe import _

from cyrix.custom_py.email_notification import sendmail
class AttendanceRequests(Document):
	pass

@frappe.whitelist()
def get_location_name(lat, lon):
	"""
	Reverse geocode latitude & longitude to get a human-readable location in English
	"""
	try:
		url = f"https://nominatim.openstreetmap.org/reverse"
		params = {
			"lat": lat,
			"lon": lon,
			"format": "json",
			"accept-language": "en"  # <-- force English
		}
		headers = {"User-Agent": "frappe-app"}
		res = requests.get(url, headers=headers, params=params)
		
		if res.status_code == 200:
			data = res.json()
			return data.get("display_name")  # English location

	except Exception as e:
		frappe.log_error(str(e), "Location Fetch Error")

	return "Location not found"


@frappe.whitelist()
def check(self,method):
	company_doc = frappe.get_doc("Company", self.company)

	hr_cc = [d.user for d in company_doc.hr_cc] if company_doc.hr_cc else []

	if self.workflow_state == "Under HR":
	
		subject = "Attendance Request"

		attendance_link = f"https://erp.cyrix-tsl.com/app/attendance-requests/{self.name}"

		message = f"""
		<div style="
			font-family: Arial, sans-serif;
			background-color: #f9fafb;
			padding: 20px;
			border: 1px solid #e5e7eb;
			border-radius: 10px;
		">

			<h2 style="
				color: #2563eb;
				margin-bottom: 15px;
			">
				Attendance Request
			</h2>

			<p>
				Dear HR,
			</p>

			<p>
				Please find the attendance regularization request submitted by the employee.
				Kindly review and take the necessary action.
			</p>

			<table style="
				width: 100%;
				border-collapse: collapse;
				margin-top: 15px;
				margin-bottom: 20px;
			">

				<tr>
					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
						background: #f3f4f6;
						font-weight: bold;
						width: 180px;
					">
						Employee Name
					</td>

					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
					">
						{self.employee_name}
					</td>
				</tr>

				<tr>
					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
						background: #f3f4f6;
						font-weight: bold;
					">
						Employee ID
					</td>

					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
					">
						{self.employee}
					</td>
				</tr>

				<tr>
					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
						background: #f3f4f6;
						font-weight: bold;
					">
						Request Type
					</td>

					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
					">
						{self.document_type}
					</td>
				</tr>

				<tr>
					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
						background: #f3f4f6;
						font-weight: bold;
					">
						Reason
					</td>

					<td style="
						padding: 10px;
						border: 1px solid #d1d5db;
					">
						{self.reason}
					</td>
				</tr>

			</table>

			<div style="margin-top:20px;">

				<a href="{attendance_link}"
					style="
						background-color:#2563eb;
						color:white;
						padding:10px 18px;
						text-decoration:none;
						border-radius:6px;
						font-weight:bold;
					">

					Open Attendance Request

				</a>

			</div>

			<br><br>

			<p>
				Kindly do the needful at the earliest.
			</p>

			<br>

			<p>
				Regards,<br>
				<b>{frappe.session.user}</b>
			</p>

		</div>
		"""

		

		
		# Create Communication
		sendmail(
			self,
			message,
			subject,
			sender = "no-reply@cyrix-tsl.com",
			recipients=info().get("hr_cc").get(self.company),
			attachments = None, 
			cc = None
		)

		frappe.msgprint("Attendance request sent successfully to HR")