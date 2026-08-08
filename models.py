import sqlite3
import logging
import bcrypt
from datetime import datetime

# إعداد السجل الرئيسي للنظام المحاسبي
logging.basicConfig(filename="accounting_app.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, db_path="accounting.db"):
        import os
        if os.environ.get("VERCEL"):
            self.db_path = ":memory:"
        else:
            self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.migrate_tables()
        self.create_tables()
        self.seed_default_data()

    def connect(self):
        """فتح الاتصال وتفعيل المفاتيح الأجنبية بشكل صريح"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.cursor = self.conn.cursor()
            logging.info("تم الاتصال بقاعدة البيانات وتفعيل المفاتيح الأجنبية (Foreign Keys)")
        except sqlite3.Error as e:
            logging.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            raise e

    def get_connection(self):
        """الحصول على اتصال دائم ومعالجة إعادة الاتصال إن لزم الأمر"""
        if self.conn is None:
            self.connect()
        return self.conn

    def migrate_tables(self):
        """الترقية والتحديث التلقائي لجداول قاعدة البيانات القديمة لضمان مطابقة الأعمدة الجديدة"""
        try:
            # 1. فحص أعمدة جدول invoices
            self.cursor.execute("PRAGMA table_info(invoices)")
            inv_cols = [row[1] for row in self.cursor.fetchall()]
            if inv_cols and 'total_amount' not in inv_cols:
                self.cursor.execute("DROP TABLE invoices")
                logging.info("تمت ترقية هيكل جدول الفواتير (invoices) لتشغيل القيد المزدوج بنجاح")

            # 2. فحص أعمدة جدول expenses
            self.cursor.execute("PRAGMA table_info(expenses)")
            exp_cols = [row[1] for row in self.cursor.fetchall()]
            if exp_cols and 'expense_account_id' not in exp_cols:
                self.cursor.execute("DROP TABLE expenses")
                logging.info("تمت ترقية هيكل جدول المصروفات (expenses) لتشغيل القيد المزدوج بنجاح")

            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"خطأ أثناء ترقية قاعدة البيانات: {e}")

    def create_tables(self):
        """إنشاء الهيكل المحاسبي القياسي مع قيود السلامة والمرجعية"""
        try:
            # 1. جدول المستخدمين (نظام مصادقة وتشفير)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash BLOB NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TEXT NOT NULL
                )
            ''')

            # 2. جدول شجرة الحسابات (Chart of Accounts)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS chart_of_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    account_type TEXT CHECK(account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')) NOT NULL,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES chart_of_accounts(id) ON DELETE SET NULL
                )
            ''')

            # 3. جدول رؤوس قيود اليومية العامة (Journal Entries Header)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    reference TEXT,
                    created_by TEXT DEFAULT 'system'
                )
            ''')

            # 4. جدول أسطر قيود اليومية العامة (Journal Entry Lines - Double Entry)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS journal_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_entry_id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    debit REAL DEFAULT 0.0 CHECK(debit >= 0),
                    credit REAL DEFAULT 0.0 CHECK(credit >= 0),
                    remarks TEXT,
                    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
                    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE RESTRICT
                )
            ''')

            # 5. جدول الموردين (Suppliers)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT,
                    net REAL DEFAULT 0.0,
                    delivery_fee REAL DEFAULT 0.0,
                    kilo_price REAL DEFAULT 0.0,
                    kilo_amount REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    account_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE SET NULL
                )
            ''')

            # 6. جدول العملاء (Clients)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT,
                    weight REAL DEFAULT 0.0,
                    kilo_price REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    paid REAL DEFAULT 0.0,
                    remaining REAL DEFAULT 0.0,
                    account_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE SET NULL
                )
            ''')

            # 7. جدول الموظفين (Employees)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    position TEXT,
                    department TEXT,
                    hire_date TEXT,
                    salary REAL DEFAULT 0.0,
                    account_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE SET NULL
                )
            ''')

            # 8. جدول المخزون (Inventory Items)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT NOT NULL UNIQUE,
                    quantity REAL DEFAULT 0.0 CHECK(quantity >= 0),
                    min_threshold REAL DEFAULT 5.0,
                    unit_price REAL DEFAULT 0.0,
                    account_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES chart_of_accounts(id) ON DELETE SET NULL
                )
            ''')

            # 9. جدول حركات المخزون (Inventory Transactions - للذكاء الاصطناعي)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inventory_id INTEGER NOT NULL,
                    transaction_type TEXT CHECK(transaction_type IN ('IN', 'OUT')) NOT NULL,
                    quantity REAL NOT NULL CHECK(quantity > 0),
                    transaction_date TEXT NOT NULL,
                    FOREIGN KEY (inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
                )
            ''')

            # 10. جدول المصروفات (Expenses)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    asset_account_id INTEGER NOT NULL,
                    expense_account_id INTEGER NOT NULL,
                    journal_entry_id INTEGER,
                    FOREIGN KEY (asset_account_id) REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
                    FOREIGN KEY (expense_account_id) REFERENCES chart_of_accounts(id) ON DELETE RESTRICT,
                    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
                )
            ''')

            # 11. جدول الفواتير (Invoices)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_type TEXT CHECK(party_type IN ('CLIENT', 'SUPPLIER')) NOT NULL,
                    party_id INTEGER NOT NULL,
                    invoice_date TEXT NOT NULL,
                    invoice_type TEXT CHECK(invoice_type IN ('CASH', 'CREDIT')) NOT NULL,
                    total_amount REAL NOT NULL CHECK(total_amount >= 0),
                    paid_amount REAL DEFAULT 0.0 CHECK(paid_amount >= 0),
                    remaining_amount REAL DEFAULT 0.0 CHECK(remaining_amount >= 0),
                    remarks TEXT,
                    journal_entry_id INTEGER,
                    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
                )
            ''')

            self.conn.commit()
            logging.info("تم إنشاء وتحديث الجداول بنجاح مع ربط المفاتيح الأجنبية")
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"خطأ في إنشاء الجداول: {e}")
            raise e

    def seed_default_data(self):
        """إدخال شجرة الحسابات القياسية وحساب المدير الافتراضي"""
        try:
            # إدخال شجرة الحسابات الأساسية
            default_accounts = [
                ("1000", "الأصول", "ASSET", None),
                ("1100", "الصندوق والبنك (النقدية)", "ASSET", None),
                ("1200", "العملاء (ذمم مدينة)", "ASSET", None),
                ("1300", "المخزون السلعي", "ASSET", None),
                ("2000", "الالتزامات", "LIABILITY", None),
                ("2100", "الموردين (ذمم دائنة)", "LIABILITY", None),
                ("3000", "حقوق الملكية", "EQUITY", None),
                ("3100", "رأس المال", "EQUITY", None),
                ("4000", "الإيرادات", "REVENUE", None),
                ("4100", "إيرادات المبيعات", "REVENUE", None),
                ("5000", "المصروفات", "EXPENSE", None),
                ("5100", "مصروفات عامة وإدارية", "EXPENSE", None),
                ("5200", "مصروف الرواتب والأجور", "EXPENSE", None),
                ("5300", "تكلفة البضاعة المباعة", "EXPENSE", None),
            ]

            for code, name, acc_type, parent in default_accounts:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO chart_of_accounts (code, name, account_type, parent_id)
                    VALUES (?, ?, ?, ?)
                ''', (code, name, acc_type, parent))

            # إدخال مستخدم admin افتراضي بكلمة مرور 2252101 مشفرة بـ bcrypt إذا كان الجدول فارغاً
            self.cursor.execute("SELECT COUNT(*) FROM users")
            if self.cursor.fetchone()[0] == 0:
                hashed_pw = bcrypt.hashpw("2252101".encode('utf-8'), bcrypt.gensalt())
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute('''
                    INSERT INTO users (username, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?)
                ''', ("admin", hashed_pw, "admin", created_at))
                logging.info("تم إضافة حساب admin الافتراضي بنجاح")

            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"خطأ أثناء تهيئة البيانات الافتراضية: {e}")

    def close(self):
        """إغلاق اتصال قاعدة البيانات بأمان"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("تم إغلاق الاتصال بقاعدة البيانات")
