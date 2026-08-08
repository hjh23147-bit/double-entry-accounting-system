import tkinter as tk
import ttkbootstrap as ttk
import logging

from models import DatabaseManager
from controllers import AuthController, AccountingController, InventoryAI
from views import AccountingAppGUI

def main():
    logging.info("بدء تشغيل النظام المحاسبي المزدوج (MVC Accounting System)")
    
    # 1. تهيئة قاعدة البيانات والهيكل القياسي
    db_manager = DatabaseManager(db_path="accounting.db")

    # 2. تهيئة المتحكمات والمنطق المحاسبي والذكاء الاصطناعي
    auth_controller = AuthController(db_manager)
    accounting_controller = AccountingController(db_manager)
    inventory_ai = InventoryAI(db_manager)

    # 3. تشغيل الواجهة الرسومية
    root = tk.Tk()
    app = AccountingAppGUI(root, auth_controller, accounting_controller, inventory_ai)
    root.mainloop()

if __name__ == "__main__":
    main()
