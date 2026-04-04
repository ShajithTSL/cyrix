from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'budgetary_quotation',
		# 'non_standard_fieldnames': {
		# 	'Quotation': 'budgetary_quotation',
		# 	'Job Order Data': 'parent_jo'
		# },
		'transactions': [
			{
				'label': _(''),
				'items': ['Quotation']
			},
			{
				'label': _(''),
				'items': ['Request for Quotation']
			},
			{
				'label': _(''),
				'items': ['Supplier Quotation']
			},
			{
				'label': _(''),
				'items': ['Purchase Order']
			},
			{
				'label': _(''),
				'items': ['Purchase Receipt']
			},
			{
				'label': _(''),
				'items': ['Sales Invoice']
			},
			{
				'label': _(''),
				'items': ['Delivery Note']
			},
			{
                'label': _(''),
                'items': ['Payment Entry']
            },
		]
	}
