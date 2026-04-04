
def get_data():
	return {
		'fieldname': 'supply_order_data',
		'non_standard_fieldnames': {
			'Service Call Form': 'related_doc'
		},
		"internal_links": {
			"Supplier Quotation": ["items", "supply_order_data"]
		},
		'transactions': [
			{
				'items': ['Request for Quotation']
			},
			{
				'items': ['Supplier Quotation']
			},
			{
				'items' : ['Quotation']
			},
			{
				'items' : ['Purchase Order']
			},
			{
				'items' : ['Purchase Receipt']
			},
			{				
				'items': ['Sales Invoice']
			},
			{				
				'items': ['Delivery Note']
			},
			{
				'items': ['Payment Entry']
			},
			{
				'items': ['Service Call Form']
			}
		]
	}
