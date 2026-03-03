from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'job_order_data',
		'non_standard_fieldnames': {
			'Quotation': 'job_order_data',
			'Job Order Data': 'parent_jo',
			'Service Call Form': 'related_doc'
		},
		'transactions': [
			{
				'label': _(''),
				'items': ['Quotation'],
				'disable_create_buttons': 1
			},
			{
				'label': _(''),
				'items': ['Evaluation Report']
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
				'items': ['Sales Invoice']
			},
			{
				'label': _(''),
				'items': ['Delivery Note']
			},
			{
				'label': _(''),
				'items': ['Stock Entry']
			},
			{
                'label': _(''),
                'items': ['Payment Entry']
            },
			{
				'label': _(''),
                'items': ['Return Note']
			},
			{
				'label': _(''),
                'items': ['Service Call Form']
			},
			{
                'label': _('Boards'),
                'items': ['Job Order Data']
            },
		]
	}
