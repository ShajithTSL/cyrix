
import './navbar.html';

frappe.ui.form.on('*', { // '*' means all DocTypes
    onload: function(frm) {
        console.log("Vanakkam")
        // // Example: Apply to 'customer' field everywhere
        // if (frm.fields_dict['customer']) {
        //     frm.set_query('customer', function() {
        //         return {
        //             filters: {
        //                 status: 'Active'
        //             }
        //         };
        //     });
        // }

        // // Example: Apply to 'item_code' in child table 'items'
        // if (frm.fields_dict['items']) {
        //     frm.set_query('item_code', 'items', function() {
        //         return {
        //             filters: {
        //                 is_sales_item: 1
        //             }
        //         };
        //     });
        // }
    }
});
