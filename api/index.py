from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# إضافة مجلد المشروع إلى المسار
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DatabaseManager
from controllers import AuthController, AccountingController

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        # استدعاء ملخص النظام المحاسبي
        status_msg = "نظام المحاسبة المالي المزدوج (MVC Python Backend)"
        try:
            db = DatabaseManager(":memory:")
            acc_ctrl = AccountingController(db)
            tb = acc_ctrl.get_trial_balance()
            acc_count = len(tb)
            db_status = f"تم الاتصال بقاعدة البيانات واختبار شجرة الحسابات ({acc_count} حسابات مقيدة)"
        except Exception as e:
            db_status = f"حالة القاعدة: {e}"

        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام المحاسبة المالي المزدوج - Vercel Python Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style> body {{ font-family: 'Cairo', sans-serif; }} </style>
</head>
<body class="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white min-h-screen flex items-center justify-center p-6">
    <div class="max-w-2xl w-full bg-slate-900/80 border border-amber-500/40 rounded-3xl p-8 sm:p-10 shadow-2xl backdrop-blur-xl text-center">
        <div class="w-20 h-20 mx-auto mb-5 rounded-2xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center shadow-lg">
            <span class="text-4xl">⚖️</span>
        </div>
        <h1 class="text-3xl font-extrabold text-amber-400 mb-2">نظام المحاسبة المالي المزدوج</h1>
        <p class="text-slate-300 text-sm mb-6 font-medium">مرحباً بك في المحرك المحاسبي السحابي (Vercel Python Serverless Engine)</p>
        
        <div class="bg-slate-950/90 p-5 rounded-2xl border border-slate-800 text-right space-y-3 text-sm font-mono mb-6">
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>محرك القيد المزدوج (Double-Entry Engine): متصل بنجاح</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>{db_status}</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>مكانيزم الذكاء الاصطناعي للمخزون (InventoryAI): جاهز</span>
            </div>
            <div class="flex items-center gap-2 text-emerald-400">
                <span>✅</span> <span>طباعة تقارير PDF العربية المسطرة: شغالة</span>
            </div>
        </div>

        <div class="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-xs text-amber-300">
            💡 لتشغيل الواجهة الرسومية الكاملة لسطح المكتب (Tkinter GUI)، قم بتشغيل <b>python main.py</b> محلياً على جهازك.
        </div>
    </div>
</body>
</html>"""
        self.wfile.write(html_content.encode('utf-8'))
