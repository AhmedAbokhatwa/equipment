# Copyright (c) 2025, Equipment and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import date_diff , getdate , add_days, add_months, add_years

class EquipmentLeaseContract(Document):

    def on_submit(self):
        self.calculate_contract_days()
        # subscription = self.create_subscription()
        # self.link_subscription(subscription)
        # self.update_asset_status()

    def validate(self):
        self.calculate_platform_commission()
        self.calculate_totals()
        self.create_payment_schedule()

    def calculate_platform_commission(self):
        if self.lease_amount and self.platform_commission_percentage:
            commission = self.lease_amount * self.platform_commission_percentage / 100
            self.platform_commission_amount = commission
        else:
            self.platform_commission_amount = 0

    def calculate_contract_days(self):
        if self.start_date and self.end_date:
            days = date_diff(self.end_date, self.start_date) + 1
            self.contract_days = days
    
    def create_payment_schedule(self):
        self.set("payment_schedule_table", [])
        start = getdate(self.start_date)
        end = getdate(self.end_date)
        cycle = self.billing_cycle
        lease_amount = self.lease_amount or 0
        commission_percent = self.platform_commission_percentage or 0

        current = start

        while current <= end:
            if cycle == "Daily":
                due_date = current
                next_date = add_days(current, 1)
            elif cycle == "Weekly":
                due_date = current
                next_date = add_days(current, 7)
            elif cycle == "Monthly":
                due_date = current
                next_date = add_months(current, 1)
            elif cycle == "Yearly":
                due_date = current
                next_date = add_years(current, 1)
            else:
                break

            commission = lease_amount * commission_percent / 100
            owner_amount = lease_amount - commission

            self.append("payment_schedule_table", {
                "due_date": due_date,
                "amount": lease_amount,
                "platform_commission_amount": commission,
                "owner_amount": owner_amount,
                "status": "Unpaid"
            })

            current = next_date
        
    # def create_payment_schedule(self):
    #     self.set("payment_schedule_table", [])
    #     start = getdate(self.start_date)
    #     end = getdate(self.end_date)
    #     cycle = self.billing_cycle 
    #     lease_amount = self.lease_amount or 0
    #     commission_percent = self.platform_commission_percentage or 0

    #     current = start

    #     while current <= end:
    #         if cycle == "Daily":
    #             due_date = current
    #             next_date = add_days(current, 1)
    #         elif cycle == "Weekly":
    #             due_date = current
    #             next_date = add_days(current, 7)
    #         elif cycle == "Monthly":
    #             due_date = current
    #             next_date = add_months(current, 1)
    #         elif cycle == "Yearly":
    #             due_date = current
    #             next_date = add_years(current, 1)
    #         else:
    #             break

    #         commission = lease_amount * commission_percent / 100

    #         self.append("payment_schedule_table", {
    #             "due_date": due_date,
    #             "amount": lease_amount,
    #             "platform_commission_amount": commission,
    #             "status": "Unpaid"
    #         })

    #         current = next_date

        
    def calculate_totals(self):
        cycles = 1
        if self.start_date and self.end_date and self.billing_cycle:
            start = getdate(self.start_date)
            end = getdate(self.end_date)
            days = date_diff(end, start) + 1
            if self.billing_cycle == "Daily":
                cycles = days
            elif self.billing_cycle == "Weekly":
                cycles = days // 7
            elif self.billing_cycle == "Monthly":
                cycles = max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)
            elif self.billing_cycle == "Yearly":
                cycles = max(1, end.year - start.year + 1)
        lease_amount = self.lease_amount or 0
        commission_percent = self.platform_commission_percentage or 0
        self.total_lease_amount = lease_amount * cycles
        self.total_platform_commission_amount = self.total_lease_amount * commission_percent / 100
        self.total_owner_amount = self.total_lease_amount - self.total_platform_commission_amount

    def create_subscription(self):
        subscription = frappe.new_doc("Subscription")
        subscription.customer = self.lessee
        subscription.start_date = self.start_date
        subscription.end_date = self.end_date
        subscription.frequency = "Monthly"
        subscription.payment_terms_template = self.payment_terms
        subscription.related_lease_contract = self.name

        subscription.append("plans", {
            "item": "Equipment Rental Service",
            "rate": self.monthly_lease_amount,
            "qty": 1
        })

        subscription.insert(ignore_permissions=True)
        subscription.submit()
        return subscription

    def link_subscription(self, subscription):
        self.subscription_related = subscription.name
        self.active_is = 1
        self.save(ignore_permissions=True)

    def update_asset_status(self):
        if self.leased_equipment:
            asset = frappe.get_doc("Asset", self.leased_equipment)
            asset.status_asset = "Leased"
            asset.save(ignore_permissions=True)
            frappe.msgprint(f"Asset {asset.name} status changed to Leased", alert=True)
