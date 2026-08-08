import logging

from models import DatabaseManager
from controllers import AuthController, AccountingController, InventoryAI

def main():
    import tkinter as tk
    from views import AccountingAppGUI

    logging.info("بدء تشغيل النظام المحاسبي المزدوج (MVC Accounting System)")
    
    # 1. تهيئة قاعدة البيانات والهيكل القياسي
    db_manager = DatabaseManager(db_path="accounting.db")

    # 2. تهيئة المتحكمات والمنطق المحاسبي والذكاء الاصطناعي
    auth_controller = AuthController(db_manager)
    accounting_controller = AccountingController(db_manager)
    inventory_ai = InventoryAI(db_manager)

    # 3. تشغيل الواجهة الرسومية
    root = tk.Tk()
    app_gui = AccountingAppGUI(root, auth_controller, accounting_controller, inventory_ai)
    root.mainloop()

# Vercel Web Entrypoint (Top-level app export required by Vercel Python runtime)
try:
    from api.index import handler
    app = handler
except Exception:
    pass

if __name__ == "__main__":
    main()
