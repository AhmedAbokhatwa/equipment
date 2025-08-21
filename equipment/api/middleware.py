import frappe
from frappe import _    

@frappe.whitelist(allow_guest=True)
def get_csrf_token():
    csrf_token = frappe.sessions.get_csrf_token()
    if csrf_token:
        return {
            "status": "success",
            "message": csrf_token
        }
    else:
          return {
            "status": "error",
            "message":  _("CSRF Token failed.")
        }
