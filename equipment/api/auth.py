import frappe
from frappe.auth import check_password
from frappe.utils import now
import secrets
import string

@frappe.whitelist(allow_guest=True)
def authenticate_and_generate_api_key(username, password):
    """
    Authenticate user and generate API key for login
    
    Args:
        username (str): Username or email of the user
        password (str): User's password
    
    Returns:
        dict: Response containing success status, message, and API credentials if successful
    """
    
    try:
        # Step 1: Check if user exists in User doctype
        user_doc = None
        
        # Try to find user by username or email
        if frappe.db.exists("User", username):
            user_doc = frappe.get_doc("User", username)
        elif frappe.db.exists("User", {"email": username}):
            user_doc = frappe.get_doc("User", {"email": username})
        else:
            return {
                "success": False,
                "message": "User not found",
                "error_code": "USER_NOT_FOUND"
            }
        
        # Check if user is enabled
        if user_doc.enabled == 0:
            return {
                "success": False,
                "message": "User account is disabled",
                "error_code": "USER_DISABLED"
            }
        
        # Step 2: Verify password
        try:
            check_password(user_doc.name, password)
        except frappe.AuthenticationError:
            return {
                "success": False,
                "message": "Invalid password",
                "error_code": "INVALID_PASSWORD"
            }
        
        # Step 3: Generate API Key and Secret
        # api_key, api_secret = generate_api_credentials(user_doc.name)
        api_key, api_secret = generate_api_credentials()
        # Step 4: Update user document with API credentials
        user_doc.api_key = api_key
        user_doc.api_secret = api_secret
        user_doc.save(ignore_permissions=True)
        # Log successful authentication
        frappe.logger().info(f"API credentials generated for user: {user_doc.name}")
        
        return {
            "success": True,
            "message": "Authentication successful",
            "data": {
                "user": user_doc.name,
                "full_name": user_doc.full_name,
                "email": user_doc.email,
                "api_key": api_key,
                "api_secret": api_secret,
                "generated_at": now(),
                "sid": frappe.session.sid,
                "user_id":user_doc.email,
                "email": user_doc.email,    
                "user_type": user_doc.user_type,
                "role":frappe.get_roles(user_doc.email),
            }
        }
        
    except Exception as e:
        frappe.logger().error(f"Authentication error: {str(e)}")
        return {
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "error_details": str(e) if frappe.conf.get("developer_mode") else None
        }

# def generate_api_credentials(user):
#     """
#     Generate API key and secret for user
    
#     Args:
#         user (str): Username
        
#     Returns:
#         tuple: (api_key, api_secret)
#     """
    
#     # Generate random API key (32 characters)
#     api_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
#     # Generate random API secret (64 characters)
#     api_secret = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(64))
    
    # return api_key, api_secret
def generate_api_credentials():
    """
    Generate API key and secret for user
    
    Args:
        user (str): Username
        
    Returns:
        tuple: (api_key, api_secret)
    """
    
    # Generate random API key (32 characters)

    # if not user_doc.api_key:
    api_key = frappe.generate_hash(length=15)
    # if not user_doc.api_secret:
    api_secret = frappe.generate_hash(length=15)
    # user_doc.save(ignore_permissions=True)
    
    return api_key, api_secret
    
@frappe.whitelist()
def regenerate_api_key(user=None):
    """
    Regenerate API credentials for current user or specified user
    
    Args:
        user (str, optional): Username (only for administrators)
        
    Returns:
        dict: New API credentials
    """
    
    # If no user specified, use current user
    if not user:
        user = frappe.session.user
    
    # Check permissions - only allow regeneration for self or if user is Administrator
    if user != frappe.session.user and not frappe.has_permission("User", "write"):
        frappe.throw("Not permitted to regenerate API key for other users")
    
    try:
        # Get user document
        user_doc = frappe.get_doc("User", user)
        
        # Generate new credentials
        api_key, api_secret = generate_api_credentials(user)
        
        # Update user document
        user_doc.api_key = api_key
        user_doc.api_secret = api_secret
        user_doc.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "API credentials regenerated successfully",
            "data": {
                "api_key": api_key,
                "api_secret": api_secret,
                "generated_at": now()
            }
        }
        
    except Exception as e:
        frappe.logger().error(f"API regeneration error: {str(e)}")
        return {
            "success": False,
            "message": "Failed to regenerate API credentials",
            "error": str(e)
        }

@frappe.whitelist()
def get_user_api_credentials():
    """
    Get current user's API credentials
    
    Returns:
        dict: User's API credentials
    """
    
    try:
        user_doc = frappe.get_doc("User", frappe.session.user)
        
        return {
            "success": True,
            "data": {
                "user": user_doc.name,
                "api_key": user_doc.api_key,
                "has_api_secret": bool(user_doc.api_secret),
                "api_secret": user_doc.api_secret if frappe.has_permission("User", "write") else "***hidden***"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to retrieve API credentials",
            "error": str(e)
        }

# Usage example for API authentication
@frappe.whitelist(allow_guest=True)
def api_login_example():
    """
    Example of how to use the generated API credentials for authentication
    
    To use the API credentials, send requests with headers:
    - Authorization: token {api_key}:{api_secret}
    
    Or as query parameters:
    - ?cmd=your_method&api_key={api_key}&api_secret={api_secret}
    """
    
    return {
        "message": "This endpoint demonstrates API authentication usage",
        "examples": {
            "header_auth": "Authorization: token your_api_key:your_api_secret",
            "query_auth": "?cmd=your_method&api_key=your_api_key&api_secret=your_api_secret"
        }
    }