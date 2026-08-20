frappe.pages['create-jo'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Create Job Order',
		single_column: true
	});
}