app_name = "cyrix"
app_title = "Cyrix TSL"
app_publisher = "tsl"
app_description = "Custom app for CYRIX"
app_email = "shajith@tsl-me.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "cyrix",
# 		"logo": "/assets/cyrix/logo.png",
# 		"title": "Cyrix TSL",
# 		"route": "/cyrix",
# 		"has_permission": "cyrix.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cyrix/css/cyrix.css"
app_include_js = [
	"cyrix.bundle.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/cyrix/css/cyrix.css"
# web_include_js = "/assets/cyrix/js/cyrix.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "cyrix/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Delivery Note" : ["custom_js/delivery_note.js"],
    "Purchase Order" : ["custom_js/purchase_order.js"],
    "Payment Entry" : ["custom_js/payment_entry.js"],
    "Quotation" : ["custom_js/quotation.js"],
    "Sales Invoice" : ["custom_js/sales_invoice.js"],
    "Request for Quotation" : ["custom_js/request_for_quotation.js"],
    "Supplier Quotation" : ["custom_js/supplier_quotation.js"],
    "Company" : ["custom_js/company.js"]
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "cyrix/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
        "cyrix.custom_py.jinja.get_technicians",
		"cyrix.custom_py.jinja.show_address",
		"cyrix.custom_py.jinja.get_mt",
		"cyrix.custom_py.jinja.get_labour",
		"cyrix.custom_py.jinja.get_material_cost",
		"cyrix.custom_py.jinja.get_invoice_details",
		"cyrix.custom_py.jinja.get_pi",
		"cyrix.custom_py.jinja.get_sales",
		"cyrix.custom_py.jinja.sales_summary",
		"cyrix.custom_py.jinja.weekly_report",
		"cyrix.custom_py.jinja.target_master",
        "cyrix.custom_py.jinja.get_technician_service_report",
		"cyrix.cyrix_tsl.doctype.wo_approval.wo_approval.weekly_sales",
		"cyrix.cyrix_tsl.doctype.wo_approval.wo_approval.daily_sales"

	]
}

# Installation
# ------------

# before_install = "cyrix.install.before_install"
# after_install = "cyrix.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "cyrix.uninstall.before_uninstall"
# after_uninstall = "cyrix.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "cyrix.utils.before_app_install"
# after_app_install = "cyrix.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "cyrix.utils.before_app_uninstall"
# after_app_uninstall = "cyrix.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cyrix.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Supplier Quotation": {
		"validate": [
			"cyrix.custom_py.supplier_quotation.update_eval_report_status",
			"cyrix.custom_py.supplier_quotation.update_price"
		],
		"on_submit": [
			"cyrix.custom_py.supplier_quotation.update_job_order_status",
			"cyrix.custom_py.supplier_quotation.update_supply_order_data",
			"cyrix.custom_py.supplier_quotation.update_budgetary_quotation"
		],
        "on_cancel": [
			"cyrix.custom_py.supplier_quotation.on_cancel",
		]
	},
    "Quotation": {
		"validate": [
            "cyrix.custom_py.quotation.fetch_item_price_details",
            "cyrix.custom_py.quotation.update_job_order_status",
            'cyrix.custom_py.quotation.update_budgetary_quotation_status'
		],
        "on_submit": [
            "cyrix.custom_py.quotation.update_job_order_status",
            'cyrix.custom_py.quotation.update_service_call_form',
            'cyrix.custom_py.quotation.update_budgetary_quotation_status'
		],
        "on_update_after_submit": [
            "cyrix.custom_py.quotation.on_update_after_submit",
            "cyrix.custom_py.quotation.update_supply_order_status"
		],
		"on_update": "cyrix.custom_py.quotation.update_supply_order_status"
	},
    
	"Purchase Order": {
		"on_submit": [
			"cyrix.custom_py.purchase_order.update_job_order_status",
			"cyrix.custom_py.purchase_order.update_supply_order_status",
            "cyrix.custom_py.purchase_order.update_budgetary_quotation_status"
		],
		"on_cancel": [
			"cyrix.custom_py.purchase_order.update_supply_order_status_on_cancel"
		]
	},
    
	"Purchase Receipt": {
		"on_submit": [
			"cyrix.custom_py.purchase_receipt.update_job_order_status",
			"cyrix.custom_py.purchase_receipt.update_supply_order_status",
		],
        "on_cancel": [
			"cyrix.custom_py.purchase_receipt.update_received_percentage",
			"cyrix.custom_py.purchase_receipt.update_job_order_status",
		]
	},

	"Delivery Note": {
        "on_submit": [
			"cyrix.custom_py.delivery_note.update_job_order_status",
            "cyrix.custom_py.delivery_note.update_supply_order_status",			
            'cyrix.custom_py.delivery_note.update_budgetary_quotation_status'
		],
		"on_update_after_submit": ["cyrix.custom_py.delivery_note.update_supply_order_status"],
		"on_cancel": [
			"cyrix.custom_py.delivery_note.update_so_qty_on_cancel",
			"cyrix.custom_py.delivery_note.update_bq_qty_on_cancel"
		]
	},

	"Sales Invoice": {
        "on_submit": [
            "cyrix.custom_py.sales_invoice.update_jo_so_status",
            "cyrix.custom_py.sales_invoice.update_service_call_form",
            "cyrix.custom_py.sales_invoice.update_invoice_percentage"		
		],
		"on_cancel": [
			"cyrix.custom_py.sales_invoice.update_jo_so_status_on_cancel",
			"cyrix.custom_py.sales_invoice.update_invoice_percentage_on_cancel"			
		]
	},
    
	"Payment Entry": {
        "on_submit": [
            "cyrix.custom_py.payment_entry.update_payment_reference"			
		],
        "on_cancel": [
            "cyrix.custom_py.payment_entry.update_payment_reference_cancel"			
		]
	},
	"Contact": {
		"before_save": [
			"cyrix.custom_py.contact.before_save"
		]
	},
	"Stock Entry":{
		"on_submit":[
			"cyrix.custom_py.stock_entry.validate_awaiting_parts"
		],
		"on_update":[
			"cyrix.custom_py.stock_entry.validate_awaiting_parts"
		],
		"on_cancel":[
			"cyrix.custom_py.stock_entry.validate_awaiting_parts"
		],
		"on_trash":[
			"cyrix.custom_py.stock_entry.validate_awaiting_parts"
		]
	},
    
	"Item": {
		"before_insert": "cyrix.custom_py.item.set_item_code_series"
	}
}

# Monkey Patch
from frappe import boot as core
from cyrix.custom_py import boot as custom
core.get_bootinfo = custom.get_bootinfo


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"cyrix.tasks.all"
# 	],
# 	"daily": [
# 		"cyrix.tasks.daily"
# 	],
# 	"hourly": [
# 		"cyrix.tasks.hourly"
# 	],
# 	"weekly": [
# 		"cyrix.tasks.weekly"
# 	],
# 	"monthly": [
# 		"cyrix.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "cyrix.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.create_journal_entry_bts": "cyrix.custom_py.bank_reconciliation_tool.create_journal_entry_bts",
	"erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.create_payment_entry_bts": "cyrix.custom_py.bank_reconciliation_tool.create_payment_entry_bts",
}


from erpnext.selling.doctype.quotation import quotation
from cyrix.custom_py import quotation as custom_quotation
quotation._make_sales_invoice = custom_quotation._make_sales_invoice

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "cyrix.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["cyrix.utils.before_request"]
# after_request = ["cyrix.utils.after_request"]

# Job Events
# ----------
# before_job = ["cyrix.utils.before_job"]
# after_job = ["cyrix.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"cyrix.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

