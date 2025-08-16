// Copyright (c) 2025, Equipment and contributors
// For license information, please see license.txt
frappe.ui.form.on('Equipment Lease Contract', {
    start_date: function(frm) {
        validate_and_calculate(frm);
        calculate_all_durations(frm); 
    },
    end_date: function(frm) {
        validate_and_calculate(frm);
        calculate_all_durations(frm); 
    },
    billing_cycle: function(frm) { 
        calculate_all_durations(frm); 
    },
    lease_amount: function(frm) {
        update_hourly_rate(frm);
    },
    total_agreed_hours: function(frm) {
        update_hourly_rate(frm);
    },
    leased_equipment: function(frm) {
        fetch_and_set_rent_item(frm);
    }
});
function update_hourly_rate(frm) {
    var lease_amount = frm.doc.lease_amount;
    var total_hours = frm.doc.total_agreed_hours;

    if (lease_amount && total_hours && total_hours > 0) {
        var hourly_rate = lease_amount / total_hours;
        frm.set_value('hourly_rate', hourly_rate);
    }
}
function validate_and_calculate(frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
        if (frm.doc.end_date < frm.doc.start_date) {
            frappe.msgprint({
                title: __('Invalid Dates'),
                message: __('End Date cannot be before Start Date'),
                indicator: 'red',
                alert: true
            });
            frm.set_value('end_date', '');
            frm.set_value('contract_duration_days', 0);
            return;
        }

        let start = frappe.datetime.str_to_obj(frm.doc.start_date);
        let end = frappe.datetime.str_to_obj(frm.doc.end_date);
        let diff = frappe.datetime.get_diff(end, start) + 1;
        frm.set_value('contract_duration_days', diff);
    }
}


function calculate_all_durations(frm) {
    var start = frm.doc.start_date;
    var end = frm.doc.end_date;
    var cycle = frm.doc.billing_cycle;

    if (start && end && cycle) {
        var s = new Date(start);
        var e = new Date(end);
        var value = 1;

        if (cycle === "Daily") {
            value = Math.abs(Math.floor((e - s) / (1000 * 60 * 60 * 24))) + 1;
            frm.set_value('contract_duration_days', value);
            frm.set_value('contract_duration_weeks',"");
            frm.set_value('contract_duration_months',"");
            frm.set_value('contract_duration_years',"");
        } else if (cycle === "Weekly") {
            value = Math.ceil((Math.abs(e - s) / (1000 * 60 * 60 * 24) + 1) / 7);
            frm.set_value('contract_duration_days',"");
            frm.set_value('contract_duration_weeks', value);
            frm.set_value('contract_duration_months',"");
            frm.set_value('contract_duration_years',"");
        } else if (cycle === "Monthly") {
            value = (e.getFullYear() - s.getFullYear()) * 12 + (e.getMonth() - s.getMonth()) + 1;
            frm.set_value('contract_duration_days',"");
            frm.set_value('contract_duration_weeks',"");
            frm.set_value('contract_duration_months', value);
            frm.set_value('contract_duration_years',"");
        } else if (cycle === "Yearly") {
            value = (e.getFullYear() - s.getFullYear()) + 1;
            frm.set_value('contract_duration_days',"");
            frm.set_value('contract_duration_weeks',"");
            frm.set_value('contract_duration_months',"");
            frm.set_value('contract_duration_years', value);
        }
    }
}
function fetch_and_set_rent_item(frm) {
    if (frm.doc.leased_equipment) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item",
                filters: {
                    custom_asset: frm.doc.leased_equipment
                },
                fields: ["item_code"]
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    frm.set_value("rent_item", r.message[0].item_code);
                }
            }
        });
    }
}
