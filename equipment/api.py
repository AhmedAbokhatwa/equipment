import frappe
from frappe.utils import today, getdate ,add_days

@frappe.whitelist()
def auto_generate_rent_invoices():
    contracts = frappe.get_all("Equipment Lease Contract", filters={"docstatus": 1})

    for contract in contracts:
        contract_doc = frappe.get_doc("Equipment Lease Contract", contract.name)
        lessee = contract_doc.lessee
        for payment in contract_doc.payment_schedule_table:
            due_date = getdate(payment.due_date)
            if due_date <= getdate(today()) and not payment.invoice:
                create_rent_invoice(
                    lessee=lessee,
                    rent_item=contract_doc.rent_item,
                    owner_amount=payment.owner_amount,
                    platform_commission_amount=payment.platform_commission_amount,
                    platform_commission_item="Platform Commission Income",
                    contract=contract_doc,
                    payment=payment
                )
        contract_doc.save(ignore_permissions=True)

def get_item_name(item_code):
    return frappe.db.get_value("Item", item_code, "item_name") or item_code

def create_rent_invoice(lessee, rent_item, owner_amount, platform_commission_amount, platform_commission_item, contract, payment):
    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = lessee
    invoice.posting_date = payment.due_date
    add_due_date = add_days(getdate(payment.due_date), 1)
    invoice.due_date = add_due_date

    invoice.set_posting_time = 1
    invoice.posting_time = "00:00:00"

    invoice.append("items", {
        "item_code": rent_item,
        "item_name": get_item_name(rent_item),
        "qty": 1,
        "rate": owner_amount,
        "asset": contract.leased_equipment ,
        "income_account": "5111 - تكلفة البضاعة المباعة - ES"
    })
    invoice.append("items", {
        "item_code": platform_commission_item,
        "item_name": get_item_name(platform_commission_item),
        "qty": 1,
        "rate": platform_commission_amount,
        "asset": contract.leased_equipment ,
        "income_account": "5202 - عمولة على المبيعات - ES"
    })

    invoice.update({
        # "custom_equipment_lease_contract": contract.name,
        "asset": contract.leased_equipment 
    })
    invoice.insert(ignore_permissions=True)
    invoice.submit()
    payment.invoice = invoice.name


@frappe.whitelist()
def update_payment_schedule_status():
    contracts = frappe.get_all("Equipment Lease Contract", filters={"docstatus": 1})
    for contract in contracts:
        contract_doc = frappe.get_doc("Equipment Lease Contract", contract.name)
        changed = False
        for payment in contract_doc.payment_schedule_table:
            if payment.invoice:
                invoice_status = frappe.db.get_value("Sales Invoice", payment.invoice, "status")
                if payment.status != invoice_status:
                    payment.status = invoice_status
                    changed = True
        if changed:
            contract_doc.save(ignore_permissions=True)