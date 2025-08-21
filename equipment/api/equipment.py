import frappe
from frappe.utils import nowdate
from frappe.exceptions import DoesNotExistError, ValidationError

@frappe.whitelist(allow_guest=True)
def check_item_exists(item_code: str):
    """تحقق إذا كان العنصر موجود في النظام"""
    try:
        item = frappe.get_doc("Item", item_code)
        frappe.logger().info(f"✅ العنصر موجود: {item_code}")
        return {"exists": True, "item": item}
    except DoesNotExistError:
        frappe.logger().warning(f"❌ العنصر غير موجود: {item_code}")
        return {"exists": False, "item": None}
    except Exception as e:
        frappe.logger().error(f"⚠️ خطأ أثناء التحقق من العنصر: {str(e)}")
        return {"exists": False, "item": None, "error": str(e)}
    
    
@frappe.whitelist(allow_guest=False, methods=["POST"])
def create_item_if_not_exists(**args):
    """ينشئ Item لو مش موجود"""
    item_code = args['item_code']   
    item_name = args.get("item_name")
    item_group = args.get("item_group")
    stock_uom = args.get("stock_uom")
    asset_category = args.get("asset_category")
    check = check_item_exists(item_code)
    if check["exists"]:
        return {
            "message":f"item is Exist {item_code}",
            "status":check["item"],
            "exists": check["exists"]
            }

    try:
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_name,
            "item_group": item_group,
            "asset_category": asset_category,
            "stock_uom":stock_uom,
            "is_stock_item" : 0,
            "is_fixed_asset": 1
        })
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"✅ تم إنشاء العنصر الجديد: {item_code}")
        return {
            "exists": False,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "asset_category": item.asset_category,
            "message": f"Item {item_code} created successfully"
        }

    except ValidationError as e:
        frappe.logger().error(f"❌ خطأ تحقق أثناء إنشاء العنصر: {str(e)}")
        raise
    except Exception as e:
        frappe.logger().error(f"❌ خطأ غير متوقع أثناء إنشاء العنصر: {str(e)}")
        raise

@frappe.whitelist(allow_guest=True)
def create_asset_with_item(asset_name: str, item_code: str, item_name: str, location: str,
                           purchase_date: str = None, available_for_use_date: str = None,   
                           gross_purchase_amount: float = 0.0, supplier: str = "Samy"):
    """يتأكد من وجود Item ثم ينشئ Asset"""
    
    try:
        # تأكد أن الـ Item موجود أو أنشئه
        item = create_item_if_not_exists(**{
            "item_code": item_code,
            "item_name": item_name
        })


        # في حالة كان dict (العنصر موجود مسبقًا)
        if isinstance(item, dict):
            item_doc = item["status"]
        else:  # في حالة تم إنشاء عنصر جديد
            item_doc = item
        existing_asset = frappe.db.exists("Asset", {
            "asset_name": asset_name,
            "item_code": item_code
        })
        
        if existing_asset:
            return {"success": False, "error": f"Asset already exists: {existing_asset}"}
        # تواريخ
        if not purchase_date:
            purchase_date = nowdate()
        if not available_for_use_date:
            available_for_use_date = nowdate()

        # إنشاء الأصل
        asset = frappe.get_doc({
            "doctype": "Asset",
            "asset_name": asset_name,
            "item_code": item_doc.item_code,
            "asset_category": item_doc.asset_category or "Default",
            "company": frappe.defaults.get_user_default("Company"),
            "location": location,
            "purchase_date": purchase_date,
            "available_for_use_date": available_for_use_date,
            "gross_purchase_amount": gross_purchase_amount,
            "asset_owner": "Supplier",
            "supplier": supplier,
            "is_existing_asset": 1,
        })
        asset.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info(f"✅ تم إنشاء الأصل بنجاح: {asset_name}")
        return {"success": True, "asset": asset.name, "item": item_doc.item_code}

    except Exception as e:
        frappe.logger().error(f"❌ خطأ أثناء إنشاء الأصل: {str(e)}")
        return {"success": False, "error": str(e)}
