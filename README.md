# ⚖️ نظام المحاسبة المالي المزدوج الاحترافي (Double-Entry Accounting System)

نظام محاسبي احترافي ومتكامل مبني بمعمارية **MVC (Model-View-Controller)** يعتمد على مبدأ القيد المزدوج المحاسبي الفعلي (Double-Entry Accounting)، مزود بشرائح تنبؤ المخزون الذكية، ومحرك تقارير PDF باللغة العربية، وواجهات ويب ملكية أسلوب (Glassmorphic UI).

---

## 🚀 المميزات الرئيسية (Core Features)

1. **نظام القيد المزدوج الصارم (Double-Entry Engine)**:
   - تحقق تلقائي من توازن القيد (`المدين = الدائن`).
   - ترحيل تلقائي لجميع حركات المصروفات والفواتير والمشتريات والمبيعات إلى شجرة الحسابات واليومية العامة.

2. **معمارية موديولار نظيفة (MVC Architecture)**:
   - `models.py`: قاعدة البيانات SQLite3، الهيكل، الفهارس، التحديث التلقائي الهيكلي (Database Migrations).
   - `controllers.py`: منطق الأعمال المحاسبي، المصادقة بتشفير `bcrypt`، وتنبؤ المخزون الذكي (`InventoryAI`).
   - `views.py`: الواجهات الرسومية، عمليات التعديل والحذف الكاملة (Full CRUD)، والتعبئة التلقائية.
   - `pdf_engine.py`: محرك توليد تقارير PDF باللغة العربية الكاملة والتسطير والترويسات الملكية.

3. **واجهة الويب الملكية (Royal Glassmorphism Web Interface)**:
   - تصميم فاخر بـ Tailwind CSS و FontAwesome 6 ودعم كامل للوضع الليلي والنهاري، وتبديل اللغات (RTL/LTR).

---

## 🛠️ كيفية التشغيل المحلي (Local Setup)

1. **تثبيت المتطلبات**:
   ```bash
   pip install -r requirements.txt
   ```

2. **تشغيل تطبيق سطح المكتب (Desktop App)**:
   ```bash
   python main.py
   ```

3. **تشغيل واجهة الويب (Web App)**:
   ```bash
   python -m http.server 8000
   ```
   ثم افتح المتصفح على: `http://localhost:8000/login.html`

---

## 🌐 خطوة بخطوة: رفع المشروع على GitHub

1. افتح الموجه النصي (Terminal) في المجلد وسجل الأوامر التالية:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Professional Double Entry Accounting System"
   ```

2. أنشئ المستودع في حسابك على GitHub، ثم اربطه وادفعه:
   ```bash
   git remote add origin https://github.com/USERNAME/double-entry-accounting-system.git
   git branch -M main
   git push -u origin main
   ```

---

## ⚡ خطوة بخطوة: الرفع والنشر المباشر على Vercel

1. اذهب إلى منصة **[Vercel.com](https://vercel.com)** وسجل الدخول بحساب GitHub الخاص بك.
2. اضغط على زر **Add New Project**.
3. اختر المستودع الخاص بالمرجعية من القائمة (**double-entry-accounting-system**).
4. انقر على **Deploy** دون الحاجة لتغيير أي إعدادات (ملف `vercel.json` مهيأ بالكامل).
5. خلال ثوانٍ معدودة ستحصل على رابط مباشر مجاني يعمل عالمياً على الويب! 🌐

---

&copy; 2026 جميع الحقوق محفوظة - وسام Sys للنظم المحاسبية المزدوجة
