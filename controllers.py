import bcrypt
import sqlite3
import logging
import numpy as np
from datetime import datetime

class AuthController:
    def __init__(self, db_manager):
        self.db = db_manager

    def authenticate(self, username, password):
        """التحقق من اسم المستخدم وكلمة المرور المشفرة باستخدام bcrypt"""
        if not username or not password:
            raise ValueError("يرجى إدخال اسم المستخدم وكلمة المرور")
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username.strip(),))
        row = cursor.fetchone()

        if row:
            user_id, uname, stored_hash, role = row
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                logging.info(f"تم تسجيل الدخول بنجاح للمستخدم: {username}")
                return {"id": user_id, "username": uname, "role": role}
        
        logging.warning(f"محاولة تسجيل دخول فاشلة للمستخدم: {username}")
        return None

    def register_user(self, username, password, role="user"):
        """إضافة مستخدم جديد وتشفير كلمة المرور"""
        if not username or not password:
            raise ValueError("اسم المستخدم وكلمة المرور مطلوبان")
            
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username.strip(), hashed, role, created_at))
            conn.commit()
            logging.info(f"تم إنشاء المستخدم {username} بنجاح")
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError("اسم المستخدم موجود بالفعل، اختر اسماً آخر")


class AccountingController:
    def __init__(self, db_manager):
        self.db = db_manager

    # ---------------- إدارة قيود اليومية والقيد المزدوج ----------------
    def create_journal_entry(self, entry_date, description, reference, lines, created_by="admin"):
        """
        إنشاء قيد يومية عامة مع التحقق الصارم من مبدأ القيد المزدوج (المدين = الدائن).
        lines عبارة عن قائمة من القواميس:
        [{"account_id": 1, "debit": 100.0, "credit": 0.0, "remarks": ""}, ...]
        """
        if not lines or len(lines) < 2:
            raise ValueError("يجب أن يحتوي القيد المحاسبي على طرفين على الأقل (مدين ودائن)")

        total_debit = sum(float(line.get('debit', 0.0)) for line in lines)
        total_credit = sum(float(line.get('credit', 0.0)) for line in lines)

        # التحقق من توازن القيد المحاسبي (القيد المزدوج)
        if abs(total_debit - total_credit) > 0.001:
            raise ValueError(f"القيد المحاسبي غير متوازن! مجموع المدين ({total_debit:.2f}) لا يساوي مجموع الدائن ({total_credit:.2f})")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # 1. إدراج رأس القيد
            cursor.execute('''
                INSERT INTO journal_entries (entry_date, description, reference, created_by)
                VALUES (?, ?, ?, ?)
            ''', (entry_date, description, reference, created_by))
            entry_id = cursor.lastrowid

            # 2. إدراج أسطر القيد
            for line in lines:
                cursor.execute('''
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, remarks)
                    VALUES (?, ?, ?, ?, ?)
                ''', (entry_id, line['account_id'], line.get('debit', 0.0), line.get('credit', 0.0), line.get('remarks', '')))

            conn.commit()
            logging.info(f"تم ترحيل قيد يومية متوازن رقم: {entry_id} بمبلغ إجمالي: {total_debit}")
            return entry_id

        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"فشل ترحيل قيد اليومية: {e}")
            raise sqlite3.OperationalError(f"حدث خطأ أثناء ترحيل القيد: {e}")

    # ---------------- الترحيل التلقائي للمصروفات والفواتير ----------------
    def post_expense_entry(self, expense_date, description, amount, asset_account_id, expense_account_id):
        """توليد قيد يومية متوازن للمصروف وتسجيل المصروف تلقائياً"""
        if amount <= 0:
            raise ValueError("يجب أن يكون مبلغ المصروف أكبر من الصفر")

        # القيد المحاسبي للمصروف:
        # مدين: حساب المصروف (Expense Account)
        # دائن: حساب النقدية/الأصول (Asset Account)
        lines = [
            {"account_id": expense_account_id, "debit": amount, "credit": 0.0, "remarks": f"مصروف: {description}"},
            {"account_id": asset_account_id, "debit": 0.0, "credit": amount, "remarks": f"سداد مصروف: {description}"}
        ]

        entry_id = self.create_journal_entry(expense_date, f"مصروف - {description}", "EXP", lines)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (expense_date, description, amount, asset_account_id, expense_account_id, journal_entry_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (expense_date, description, amount, asset_account_id, expense_account_id, entry_id))
        conn.commit()
        return entry_id

    def post_invoice_entry(self, party_type, party_id, invoice_date, invoice_type, total_amount, paid_amount=0.0, remarks=""):
        """توليد قيد يومية متوازن للفواتير مع الترحيل التلقائي لجميع الحسابات"""
        if total_amount <= 0:
            raise ValueError("يجب أن يكون إجمالي الفاتورة أكبر من الصفر")

        paid_amount = min(paid_amount, total_amount)
        remaining_amount = total_amount - paid_amount

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # استدعاء الحسابات الشائعة
        cursor.execute("SELECT id FROM chart_of_accounts WHERE code = '1100'") # نقدية
        cash_acc = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM chart_of_accounts WHERE code = '1200'") # عملاء
        receivable_acc = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM chart_of_accounts WHERE code = '2100'") # موردين
        payable_acc = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM chart_of_accounts WHERE code = '4100'") # مبيعات
        sales_acc = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM chart_of_accounts WHERE code = '1300'") # مخزون/مشتريات
        inventory_acc = cursor.fetchone()[0]

        lines = []
        if party_type == 'CLIENT':
            # فاتورة مبيعات عميل:
            # مدين: النقدية (بالمدفوع) + الذمم المدينة (بالباقي)
            # دائن: الإيرادات (بالإجمالي)
            if paid_amount > 0:
                lines.append({"account_id": cash_acc, "debit": paid_amount, "credit": 0.0, "remarks": "تحصيل نقدية فاتورة مبيعات"})
            if remaining_amount > 0:
                lines.append({"account_id": receivable_acc, "debit": remaining_amount, "credit": 0.0, "remarks": "آجل فاتورة مبيعات"})
            lines.append({"account_id": sales_acc, "debit": 0.0, "credit": total_amount, "remarks": "إيراد مبيعات عميل"})

        elif party_type == 'SUPPLIER':
            # فاتورة مشتريات مورد:
            # مدين: المخزون/المشتريات (بالإجمالي)
            # دائن: النقدية (بالمدفوع) + الذمم الدائنة (بالباقي)
            lines.append({"account_id": inventory_acc, "debit": total_amount, "credit": 0.0, "remarks": "مشتريات/مخزون مورد"})
            if paid_amount > 0:
                lines.append({"account_id": cash_acc, "debit": 0.0, "credit": paid_amount, "remarks": "سداد نقدية فاتورة مشتريات"})
            if remaining_amount > 0:
                lines.append({"account_id": payable_acc, "debit": 0.0, "credit": remaining_amount, "remarks": "آجل فاتورة مشتريات"})

        entry_id = self.create_journal_entry(invoice_date, f"فاتورة {party_type} - {remarks}", "INV", lines)

        cursor.execute('''
            INSERT INTO invoices (party_type, party_id, invoice_date, invoice_type, total_amount, paid_amount, remaining_amount, remarks, journal_entry_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (party_type, party_id, invoice_date, invoice_type, total_amount, paid_amount, remaining_amount, remarks, entry_id))
        conn.commit()
        return entry_id

    # ---------------- التقارير المالية وميزان المراجعة ----------------
    def get_trial_balance(self):
        """حساب ميزان المراجعة لجميع الحسابات بناءً على أسطر اليومية العامة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.code, c.name, c.account_type,
                   COALESCE(SUM(l.debit), 0.0) as total_debit,
                   COALESCE(SUM(l.credit), 0.0) as total_credit
            FROM chart_of_accounts c
            LEFT JOIN journal_lines l ON c.id = l.account_id
            GROUP BY c.id
            ORDER BY c.code
        ''')
        return cursor.fetchall()

    # ---------------- دوال الحذف والتعديل العام والربط المرجي ----------------
    def delete_record(self, table_name, record_id):
        """حذف سجل من جدول محدد مع مراعاة المفاتيح الأجنبية والاستثناءات المحاسبية"""
        allowed_tables = ['suppliers', 'clients', 'employees', 'inventory', 'expenses', 'invoices', 'chart_of_accounts', 'journal_entries']
        if table_name not in allowed_tables:
            raise ValueError("اسم الجدول غير مسموح به للحذف")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            conn.commit()
            logging.info(f"تم حذف السجل رقم {record_id} من الجدول {table_name} بنجاح")
            return True
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logging.error(f"فشل حذف السجل بسبب ارتباطات في الجداول الأخرى: {e}")
            raise ValueError("لا يمكن حذف هذا السجل لأنه مرتبط بحركات أو سجلات أخرى في النظام (قيود أمان المفاتيح الأجنبية).")
        except sqlite3.Error as e:
            conn.rollback()
            raise sqlite3.OperationalError(f"حدث خطأ في قاعدة البيانات أثناء الحذف: {e}")

    # ---------------- محرك استخراج التقارير المفلترة حسب الفترات (يومي، شهري، سنوي) ----------------
    def get_periodical_report_data(self, section, period_type="ALL", date_val=None):
        """
        جلب بيانات التقرير مفلترة حسَب القسم والفترة (DAILY, MONTHLY, ANNUAL, ALL)
        Section: 'SUPPLIERS', 'CLIENTS', 'EMPLOYEES', 'EXPENSES', 'INVOICES', 'INVENTORY', 'TRIAL_BALANCE'
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if not date_val:
            date_val = datetime.now().strftime("%Y-%m-%d")

        # تحديد صيغة التاريخ بحسب نوع الفترة
        if period_type == "DAILY":
            date_filter = date_val[:10]
        elif period_type == "MONTHLY":
            date_filter = date_val[:7] # YYYY-MM
        elif period_type == "ANNUAL":
            date_filter = date_val[:4] # YYYY
        else:
            date_filter = ""

        headers = []
        rows = []
        summary = ""

        if section == 'SUPPLIERS':
            headers = ["ID", "اسم المورد", "التاريخ", "الصافي", "التوصيل", "سعر الكيلو", "الكمية", "الإجمالي"]
            query = "SELECT id, name, date, net, delivery_fee, kilo_price, kilo_amount, total FROM suppliers"
            if date_filter:
                query += " WHERE date LIKE ?"
                cursor.execute(query, (f"{date_filter}%",))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            tot = sum(r[7] for r in rows) if rows else 0.0
            summary = f"إجمالي حركات الموردين للفترة: {tot:.2f} ريال"

        elif section == 'CLIENTS':
            headers = ["ID", "اسم العميل", "التاريخ", "الوزن", "سعر الكيلو", "الإجمالي", "المدفوع", "المتبقي"]
            query = "SELECT id, name, date, weight, kilo_price, total, paid, remaining FROM clients"
            if date_filter:
                query += " WHERE date LIKE ?"
                cursor.execute(query, (f"{date_filter}%",))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            tot = sum(r[5] for r in rows) if rows else 0.0
            rem = sum(r[7] for r in rows) if rows else 0.0
            summary = f"إجمالي المبيعات: {tot:.2f} ريال | المتبقي الآجل: {rem:.2f} ريال"

        elif section == 'EMPLOYEES':
            headers = ["ID", "اسم الموظف", "الوظيفة", "القسم", "تاريخ التعيين", "الراتب"]
            query = "SELECT id, name, position, department, hire_date, salary FROM employees"
            if date_filter:
                query += " WHERE hire_date LIKE ?"
                cursor.execute(query, (f"{date_filter}%",))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            tot_salary = sum(r[5] for r in rows) if rows else 0.0
            summary = f"إجمالي الرواتب الشهرية: {tot_salary:.2f} ريال"

        elif section == 'EXPENSES':
            headers = ["ID", "التاريخ", "بيان المصروف", "المبلغ", "رقم القيد"]
            query = "SELECT id, expense_date, description, amount, journal_entry_id FROM expenses"
            if date_filter:
                query += " WHERE expense_date LIKE ?"
                cursor.execute(query, (f"{date_filter}%",))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            tot_exp = sum(r[3] for r in rows) if rows else 0.0
            summary = f"إجمالي المصروفات للفترة: {tot_exp:.2f} ريال"

        elif section == 'INVOICES':
            headers = ["ID", "الطرف", "التاريخ", "النوع", "الإجمالي", "المدفوع", "المتبقي", "رقم القيد"]
            query = "SELECT id, party_type, invoice_date, invoice_type, total_amount, paid_amount, remaining_amount, journal_entry_id FROM invoices"
            if date_filter:
                query += " WHERE invoice_date LIKE ?"
                cursor.execute(query, (f"{date_filter}%",))
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            tot_inv = sum(r[4] for r in rows) if rows else 0.0
            summary = f"إجمالي الفواتير الصادرة للفترة: {tot_inv:.2f} ريال"

        elif section == 'INVENTORY':
            headers = ["ID", "اسم الصنف", "الكمية المتوفرة", "حد إعادة الطلب"]
            cursor.execute("SELECT id, item, quantity, min_threshold FROM inventory")
            rows = cursor.fetchall()
            tot_items = len(rows)
            summary = f"إجمالي عدد أصناف المخزون المسجلة: {tot_items} صنف"

        elif section == 'TRIAL_BALANCE':
            headers = ["رمز الحساب", "اسم الحساب", "نوع الحساب", "إجمالي المدين", "إجمالي الدائن", "الرصيد"]
            tb_data = self.get_trial_balance()
            tot_d = sum(r[3] for r in tb_data)
            tot_c = sum(r[4] for r in tb_data)
            rows = [[r[0], r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.2f}", f"{(r[3]-r[4]):.2f}"] for r in tb_data]
            summary = f"مجموع اليومية العامة - المدين: {tot_d:.2f} | الدائن: {tot_c:.2f}"

        return {
            "section": section,
            "period_type": period_type,
            "filter_date": date_val,
            "headers": headers,
            "rows": rows,
            "summary": summary
        }


class InventoryAI:
    def __init__(self, db_manager):
        self.db = db_manager

    def record_transaction(self, inventory_id, transaction_type, quantity):
        """تسجيل حركة مخزون (إدخال IN أو سحب/استهلاك OUT)"""
        if quantity <= 0:
            raise ValueError("يجب أن تكون الكمية أكبر من الصفر")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
            INSERT INTO inventory_transactions (inventory_id, transaction_type, quantity, transaction_date)
            VALUES (?, ?, ?, ?)
        ''', (inventory_id, transaction_type, quantity, date_str))

        # تحديث كمية الصنف في جدول المخزون
        if transaction_type == 'IN':
            cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ?", (quantity, inventory_id))
        else:
            cursor.execute("UPDATE inventory SET quantity = MAX(0, quantity - ?) WHERE id = ?", (quantity, inventory_id))

        conn.commit()

    def forecast_item_inventory(self, inventory_id):
        """
        تنبؤ ذكي لكل صنف على حدة بناءً على معدل السحب والاستهلاك الفعلي للصنف الصادر (OUT)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # قراءة الكمية الحالية والحد الأدنى
        cursor.execute("SELECT item, quantity, min_threshold FROM inventory WHERE id = ?", (inventory_id,))
        item_data = cursor.fetchone()
        if not item_data:
            return {"error": "الصنف غير موجود"}

        item_name, current_qty, min_threshold = item_data

        # قراءة جميع حركات السحب الخاصة بهذا الصنف الصريح
        cursor.execute('''
            SELECT quantity FROM inventory_transactions
            WHERE inventory_id = ? AND transaction_type = 'OUT'
            ORDER BY id DESC LIMIT 30
        ''', (inventory_id,))
        rows = cursor.fetchall()

        if not rows:
            return {
                "item_name": item_name,
                "current_qty": current_qty,
                "avg_daily_consumption": 0.0,
                "estimated_days_left": "لا تتوفر حركات استهلاك سابقة",
                "recommended_reorder_qty": round(min_threshold * 1.5, 2)
            }

        consumptions = np.array([r[0] for r in rows])
        avg_consumption = np.mean(consumptions)

        if avg_consumption > 0:
            days_left = round(current_qty / avg_consumption, 1)
        else:
            days_left = 999.0

        recommended_reorder = round(max(0, (min_threshold * 2) - current_qty + (avg_consumption * 7)), 2)

        return {
            "item_name": item_name,
            "current_qty": current_qty,
            "avg_consumption": round(avg_consumption, 2),
            "estimated_days_left": days_left,
            "recommended_reorder_qty": recommended_reorder,
            "needs_reorder": current_qty <= min_threshold
        }
