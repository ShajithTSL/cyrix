// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance Requests", {
    before_save: function(frm) {
        if (!navigator.geolocation) {
            frappe.msgprint("Geolocation not supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(function(position) {
            let lat = position.coords.latitude;
            let lon = position.coords.longitude;
            let punch_type = frm.doc.miss_punch_type; // "In" or "Out" (you need a select field)

            if (punch_type === 'IN') {
                frm.set_value('latitude', lat);
                frm.set_value('longitude', lon);
            } else if (punch_type === 'OUT') {
                frm.set_value('latitude_out', lat);
                frm.set_value('longitude_out', lon);
            }

            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.attendance_requests.attendance_requests.get_location_name",
                args: {
                    lat: lat,
                    lon: lon
                },
                callback: function(r) {
                    if (r.message) {
                         if (punch_type === 'IN') {
                            frm.set_value('location', r.message)
                        } else if (punch_type === 'OUT') {
                           rm.set_value('location_out', r.message)
                        }
                    }
                }
            });
        }, function(error) {
            frappe.msgprint("Please enable location to submit punch request");
        });
    },
    after_save: function(frm) {

        if (!navigator.geolocation) {
            frappe.msgprint("Geolocation not supported");
            return;
        }

        navigator.geolocation.getCurrentPosition(function(position) {

            let lat = position.coords.latitude;
            let lon = position.coords.longitude;
            let punch_type = frm.doc.miss_punch_type;

            if (punch_type === 'IN') {
                frm.set_value('latitude', lat);
                frm.set_value('longitude', lon);
            } else if (punch_type === 'OUT') {
                frm.set_value('latitude_out', lat);
                frm.set_value('longitude_out', lon);
            }

            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.attendance_requests.attendance_requests.get_location_name",
                args: {
                    lat: lat,
                    lon: lon
                },
                callback: function(r) {
                    if (r.message) {
                        if (punch_type === 'IN') {
                            frm.set_value('location', r.message);
                        } else if (punch_type === 'OUT') {
                            frm.set_value('location_out', r.message);
                        }

                        // save again to persist values
                        frm.save();
                    }
                }
            });

        }, function(error) {
            frappe.msgprint("Please enable location to submit punch request");
        });
    }
    
});

