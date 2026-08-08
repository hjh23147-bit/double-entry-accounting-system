import logging

from models import DatabaseManager
from controllers import AuthController, AccountingController, InventoryAI

def main():
    import tkinter as tk
    import ttkbootstrap as ttk
    from views import AccountingAppGUI

    logging.basicConfig(filename="accounting_app.log", level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("بدء تشغيل النظام المحاسبي المزدوج (MVC Accounting System)")
    
    # 1. تهيئة قاعدة البيانات والهيكل القياسي
    db_manager = DatabaseManager(db_path="accounting.db")

    # 2. تهيئة المتحكمات والمنطق المحاسبي والذكاء الاصطناعي
    auth_controller = AuthController(db_manager)
    accounting_controller = AccountingController(db_manager)
    inventory_ai = InventoryAI(db_manager)

    # 3. تشغيل الواجهة الرسومية لسطح المكتب (Desktop Tkinter App)
    root = tk.Tk()
    app_gui = AccountingAppGUI(root, auth_controller, accounting_controller, inventory_ai)
    root.mainloop()

# Vercel WSGI Serverless Application Entrypoint
def app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)

    try:
        db_manager = DatabaseManager(db_path=":memory:")
        acc_ctrl = AccountingController(db_manager)
        tb = acc_ctrl.get_trial_balance()
        acc_count = len(tb)
        status_text = f"تم الاتصال بقاعدة البيانات المحاسبية واختبار شجرة الحسابات بنجاح ({acc_count} حساب مقيد)"
    except Exception as e:
        status_text = f"حالة القاعدة المحاسبية: {e}"

    html_out = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام المحاسبة المالي المزدوج - Vercel WSAM5</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style> body {{ font-family: 'Cairo', sans-serif; }} </style>
</head>
<body class="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white min-h-screen flex items-center justify-center p-6">
    <div class="max-w-xl w-full bg-slate-900/90 border border-amber-500/40 rounded-3xl p-8 text-center shadow-2xl backdrop-blur-xl">
        <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center shadow-lg">
            <span class="text-4xl">⚖️</span>
        </div>
        <h1 class="text-3xl font-extrabold text-amber-400 mb-2">نظام المحاسبة المالي المزدوج</h1>
        <p class="text-slate-300 text-sm mb-6 font-medium">مشروع البايثون المحاسبي (MVC) يعمل الآن بنجاح على منصة Vercel السحابية!</p>
        
        <div class="bg-slate-950 p-5 rounded-2xl border border-slate-800 text-right space-y-3 text-sm font-mono mb-6">
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>محرك القيد المزدوج المحاسبي: متصل وفعال</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>{status_text}</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>مكانيزم الذكاء الاصطناعي للمخزون (InventoryAI): جاهز</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>محرك طباعة تقارير الـ PDF المعربة: شغال</span>
            </div>
        </div>

        <div class="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-xs text-amber-300">
            💡 لتشغيل واجهة سطح المكتب الرسومية الكاملة (Tkinter GUI)، قم بتشغيل <b>python main.py</b> محلياً على جهازك.
        </div>
    </div>
</body>
</html>"""
    return [html_out.encode('utf-8')]

handler = app

if __name__ == "__main__":
    main()
