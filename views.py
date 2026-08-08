import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import sqlite3
import logging
from datetime import datetime

from pdf_engine import ArabicPDFReport

# ---------------- مساعدة التحقق من الصحة (Input Validation Helper) ----------------
def parse_float_input(value, field_name, min_val=0.0, allow_zero=True):
    """التحقق من صحة المدخلات الرقمية العشرية وإطلاق استثناء مفصل"""
    val_str = str(value).strip()
    if not val_str:
        if allow_zero:
            return 0.0
        raise ValueError(f"الحقل '{field_name}' مطلوب ولا يمكن أن يكون فارغاً.")
    try:
        val = float(val_str)
        if val < min_val:
            raise ValueError(f"قيمة الحقل '{field_name}' يجب أن تكون أكبر من أو تساوي {min_val}.")
        return val
    except ValueError:
        raise ValueError(f"الحقل '{field_name}' يجب أن يحتوي على رقم صحيح أو عشري (مثال: 10.5).")

def parse_required_string(value, field_name):
    """التحقق من النص المطلوب"""
    val_str = str(value).strip()
    if not val_str:
        raise ValueError(f"الحقل '{field_name}' مطلوب ولا يمكن إبقاؤه فارغاً.")
    return val_str


class AccountingAppGUI:
    def __init__(self, root, auth_controller, accounting_controller, inventory_ai):
        self.root = root
        self.auth_ctrl = auth_controller
        self.acc_ctrl = accounting_controller
        self.ai_ctrl = inventory_ai

        self.root.title("وسام Sys - نظام المحاسبة المزدوج الاحترافي")
        self.root.geometry("1280x750")
        self.root.configure(bg="#f8fafc")
        self.style = ttk.Style("flatly")

        self.current_user = None
        self.menu_bar_created = False

        self.create_login_window()

    def clear_window(self):
        """مسح العناصر الحالية من الشاشة مع بقاء القائمة الرئيسية"""
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()

    # ---------------- 1. شاشة تسجيل الدخول الموحدة الفاخرة (Clean White Theme) ----------------
    def create_login_window(self):
        self.root.config(menu=None)
        self.menu_bar_created = False
        self.clear_window()

        self.style = ttk.Style("flatly")
        self.root.configure(bg="#f8fafc")

        outer_container = ttk.Frame(self.root, padding=40, bootstyle="light")
        outer_container.pack(expand=True)

        card = ttk.Labelframe(outer_container, text="", padding=35, bootstyle="primary")
        card.pack(expand=True, fill="both")

        ttk.Label(card, text="⚖️", font=("Segoe UI Symbol", 46), bootstyle="primary").pack(pady=(5, 0))
        ttk.Label(card, text="نظام المحاسبة المالي المزدوج", font=("Arial", 22, "bold"), bootstyle="dark").pack(pady=(5, 5))
        ttk.Label(card, text="تسجيل الدخول للنظام", font=("Arial", 13, "bold"), bootstyle="secondary").pack(pady=(0, 20))

        user_frame = ttk.Frame(card)
        user_frame.pack(fill="x", pady=8)
        ttk.Label(user_frame, text="👤  اسم المستخدم:", font=("Arial", 12, "bold"), bootstyle="dark").pack(anchor="w", pady=3)
        self.username_entry = ttk.Entry(user_frame, font=("Arial", 13), width=32, bootstyle="primary")
        self.username_entry.pack(fill="x", ipady=4)
        self.username_entry.focus()

        pass_frame = ttk.Frame(card)
        pass_frame.pack(fill="x", pady=8)
        ttk.Label(pass_frame, text="🔒  كلمة المرور:", font=("Arial", 12, "bold"), bootstyle="dark").pack(anchor="w", pady=3)
        
        pass_input_box = ttk.Frame(pass_frame)
        pass_input_box.pack(fill="x")

        self.password_entry = ttk.Entry(pass_input_box, font=("Arial", 13), show="*", bootstyle="primary")
        self.password_entry.pack(side="left", expand=True, fill="x", ipady=4)

        self.is_password_shown = False
        def toggle_pass_show():
            if self.is_password_shown:
                self.password_entry.config(show="*")
                eye_btn.config(text="👁️")
                self.is_password_shown = False
            else:
                self.password_entry.config(show="")
                eye_btn.config(text="🙈")
                self.is_password_shown = True

        eye_btn = ttk.Button(pass_input_box, text="👁️", command=toggle_pass_show, bootstyle="outline-primary", width=4)
        eye_btn.pack(side="right", padx=(5, 0))

        options_frame = ttk.Frame(card)
        options_frame.pack(fill="x", pady=14)
        
        remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="تذكرني", variable=remember_var, bootstyle="primary-round-toggle").pack(side="right")
        
        forgot_lbl = ttk.Label(options_frame, text="نسيت كلمة المرور؟", font=("Arial", 10, "underline"), cursor="hand2", bootstyle="primary")
        forgot_lbl.pack(side="left")
        forgot_lbl.bind("<Button-1>", lambda e: messagebox.showinfo("إعادة التعيين", "يرجى التواصل مع مدير النظام لإعادة تعيين كلمة المرور الخاص بك."))

        ttk.Button(card, text="تسجيل الدخول  ➔", command=self.handle_login, bootstyle="primary", width=28).pack(pady=(20, 10), ipady=6)

        footer_frame = ttk.Frame(card)
        footer_frame.pack(pady=(12, 0))
        ttk.Label(footer_frame, text="ليس لديك حساب؟ ", font=("Arial", 10), bootstyle="secondary").pack(side="right")
        signup_link = ttk.Label(footer_frame, text="أنشئ حساباً جديداً", font=("Arial", 10, "bold", "underline"), cursor="hand2", bootstyle="primary")
        signup_link.pack(side="left")
        signup_link.bind("<Button-1>", lambda e: messagebox.showinfo("إنشاء حساب", "يرجى التواصل مع قسم الموارد البشرية لإنشاء حساب محاسبي جديد."))

    def handle_login(self):
        try:
            uname = parse_required_string(self.username_entry.get(), "اسم المستخدم")
            pword = parse_required_string(self.password_entry.get(), "كلمة المرور")

            user = self.auth_ctrl.authenticate(uname, pword)
            if user:
                self.current_user = user
                self.create_dashboard()
            else:
                messagebox.showerror("خطأ في الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")
        except ValueError as e:
            messagebox.showwarning("تنبيه الإدخال", str(e))
        except sqlite3.Error as e:
            messagebox.showerror("خطأ في قاعدة البيانات", f"تعذر الاتصال بقاعدة البيانات: {e}")

    def show_two_factor_auth(self):
        code = "123456"
        messagebox.showinfo("رمز التحقق (2FA)", f"رمز التحقق المؤقت الخاص بك هو: {code}")

        win = tk.Toplevel(self.root)
        win.title("التحقق الثانوي 2FA")
        win.geometry("350x200")

        ttk.Label(win, text="أدخل رمز التحقق (123456):", font=("Arial", 12)).pack(pady=15)
        code_entry = ttk.Entry(win, font=("Arial", 14), width=15)
        code_entry.pack(pady=5)
        code_entry.focus()

        def verify():
            if code_entry.get().strip() == code:
                win.destroy()
                self.create_dashboard()
            else:
                messagebox.showerror("خطأ", "رمز التحقق غير صحيح")

        ttk.Button(win, text="تأكيد الدخول", command=verify, bootstyle="success").pack(pady=15)

    # ---------------- 2. القائمة الرئيسية ولوحة التحكم ----------------
    def create_menu_bar(self):
        if not self.menu_bar_created:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)

            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="النسخ الاحتياطي", command=self.backup_database)
            file_menu.add_separator()
            file_menu.add_command(label="تسجيل الخروج", command=self.create_login_window)
            file_menu.add_command(label="خروج النهائي", command=self.root.quit)
            menubar.add_cascade(label="ملف", menu=file_menu)

            acc_menu = tk.Menu(menubar, tearoff=0)
            acc_menu.add_command(label="شجرة الحسابات (COA)", command=self.create_coa_window)
            acc_menu.add_command(label="قيود اليومية العامة", command=self.create_journal_window)
            acc_menu.add_command(label="ميزان المراجعة والتقارير الدورية", command=self.create_reports_window)
            menubar.add_cascade(label="المحاسبة العامة", menu=acc_menu)

            manage_menu = tk.Menu(menubar, tearoff=0)
            manage_menu.add_command(label="إدارة الموردين", command=self.create_suppliers_window)
            manage_menu.add_command(label="إدارة العملاء", command=self.create_clients_window)
            manage_menu.add_command(label="إدارة الموظفين", command=self.create_employees_window)
            manage_menu.add_command(label="إدارة الفواتير", command=self.create_invoices_window)
            manage_menu.add_command(label="إدارة المصروفات", command=self.create_expenses_window)
            manage_menu.add_command(label="إدارة المخزون", command=self.create_inventory_window)
            menubar.add_cascade(label="إدارة الحركات", menu=manage_menu)

            self.menu_bar_created = True

    def create_dashboard(self):
        self.clear_window()
        self.create_menu_bar()

        ttk.Label(self.root, text="لوحة التحكم المحاسبية (نظام القيد المزدوج المطور)", font=("Arial", 20, "bold"), bootstyle="primary").pack(pady=15)

        conn = self.acc_ctrl.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clients")
        clients_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM journal_entries")
        entries_count = cursor.fetchone()[0]

        stats_frame = ttk.Frame(self.root, padding=15)
        stats_frame.pack(pady=10)

        ttk.Label(stats_frame, text=f"عدد الموردين: {suppliers_count}", font=("Arial", 13), bootstyle="inverse-primary", padding=12).grid(row=0, column=0, padx=15)
        ttk.Label(stats_frame, text=f"عدد العملاء: {clients_count}", font=("Arial", 13), bootstyle="inverse-info", padding=12).grid(row=0, column=1, padx=15)
        ttk.Label(stats_frame, text=f"إجمالي قيود اليومية: {entries_count}", font=("Arial", 13), bootstyle="inverse-success", padding=12).grid(row=0, column=2, padx=15)

        buttons_frame = ttk.Frame(self.root, padding=20)
        buttons_frame.pack(pady=20)

        ttk.Button(buttons_frame, text="شجرة الحسابات (COA)", command=self.create_coa_window, bootstyle="secondary", width=22).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(buttons_frame, text="قيود اليومية العامة", command=self.create_journal_window, bootstyle="success", width=22).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(buttons_frame, text="التقارير الدورية و PDF", command=self.create_reports_window, bootstyle="warning", width=22).grid(row=0, column=2, padx=10, pady=10)

        ttk.Button(buttons_frame, text="إدارة الموردين (CRUD)", command=self.create_suppliers_window, bootstyle="primary", width=22).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(buttons_frame, text="إدارة العملاء (CRUD)", command=self.create_clients_window, bootstyle="primary", width=22).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(buttons_frame, text="إدارة الموظفين (CRUD)", command=self.create_employees_window, bootstyle="primary", width=22).grid(row=1, column=2, padx=10, pady=10)

        ttk.Button(buttons_frame, text="الفواتير والترحيل", command=self.create_invoices_window, bootstyle="info", width=22).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(buttons_frame, text="المصروفات والترحيل", command=self.create_expenses_window, bootstyle="info", width=22).grid(row=2, column=1, padx=10, pady=10)
        ttk.Button(buttons_frame, text="المخزون والذكاء الاصطناعي", command=self.create_inventory_window, bootstyle="dark", width=22).grid(row=2, column=2, padx=10, pady=10)

    # ---------------- 3. إدارة الموردين مع التعديل والحذف ----------------
    def create_suppliers_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة الموردين (إضافة - تعديل - حذف)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="اسم المورد:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="التاريخ:").grid(row=0, column=2, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="الصافي:").grid(row=1, column=0, padx=5, pady=5)
        net_entry = ttk.Entry(frame)
        net_entry.insert(0, "0.0")
        net_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="رسوم التوصيل:").grid(row=1, column=2, padx=5, pady=5)
        delivery_entry = ttk.Entry(frame)
        delivery_entry.insert(0, "0.0")
        delivery_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="سعر الكيلو:").grid(row=2, column=0, padx=5, pady=5)
        kilo_price_entry = ttk.Entry(frame)
        kilo_price_entry.insert(0, "0.0")
        kilo_price_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="كمية الكيلو:").grid(row=2, column=2, padx=5, pady=5)
        kilo_amount_entry = ttk.Entry(frame)
        kilo_amount_entry.insert(0, "0.0")
        kilo_amount_entry.grid(row=2, column=3, padx=5, pady=5)

        columns = ["ID", "اسم المورد", "التاريخ", "الصافي", "التوصيل", "سعر الكيلو", "الكمية", "الإجمالي"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            name_entry.delete(0, tk.END)
            date_entry.delete(0, tk.END)
            date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            net_entry.delete(0, tk.END); net_entry.insert(0, "0.0")
            delivery_entry.delete(0, tk.END); delivery_entry.insert(0, "0.0")
            kilo_price_entry.delete(0, tk.END); kilo_price_entry.insert(0, "0.0")
            kilo_amount_entry.delete(0, tk.END); kilo_amount_entry.insert(0, "0.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                name_entry.delete(0, tk.END); name_entry.insert(0, vals[1])
                date_entry.delete(0, tk.END); date_entry.insert(0, vals[2])
                net_entry.delete(0, tk.END); net_entry.insert(0, str(vals[3]))
                delivery_entry.delete(0, tk.END); delivery_entry.insert(0, str(vals[4]))
                kilo_price_entry.delete(0, tk.END); kilo_price_entry.insert(0, str(vals[5]))
                kilo_amount_entry.delete(0, tk.END); kilo_amount_entry.insert(0, str(vals[6]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_supplier():
            try:
                name = parse_required_string(name_entry.get(), "اسم المورد")
                d_str = parse_required_string(date_entry.get(), "التاريخ")
                net = parse_float_input(net_entry.get(), "الصافي")
                delivery = parse_float_input(delivery_entry.get(), "التوصيل")
                kilo_price = parse_float_input(kilo_price_entry.get(), "سعر الكيلو")
                kilo_amount = parse_float_input(kilo_amount_entry.get(), "كمية الكيلو")
                total = net + delivery + (kilo_price * kilo_amount)

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO suppliers (name, date, net, delivery_fee, kilo_price, kilo_amount, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, d_str, net, delivery, kilo_price, kilo_amount, total))
                conn.commit()

                if total > 0:
                    self.acc_ctrl.post_invoice_entry('SUPPLIER', cursor.lastrowid, d_str, 'CASH', total, total, f"توريد من {name}")

                messagebox.showinfo("تم", "تمت إضافة المورد وترحيل القيد بنجاح")
                clear_inputs()
                load_suppliers()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def update_supplier():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد مورد من الجدول لتعديله.")
                return
            try:
                name = parse_required_string(name_entry.get(), "اسم المورد")
                d_str = parse_required_string(date_entry.get(), "التاريخ")
                net = parse_float_input(net_entry.get(), "الصافي")
                delivery = parse_float_input(delivery_entry.get(), "التوصيل")
                kilo_price = parse_float_input(kilo_price_entry.get(), "سعر الكيلو")
                kilo_amount = parse_float_input(kilo_amount_entry.get(), "كمية الكيلو")
                total = net + delivery + (kilo_price * kilo_amount)

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE suppliers SET name=?, date=?, net=?, delivery_fee=?, kilo_price=?, kilo_amount=?, total=?
                    WHERE id=?
                ''', (name, d_str, net, delivery, kilo_price, kilo_amount, total, int(selected_id.get())))
                conn.commit()
                messagebox.showinfo("تم التعديل", "تم تعديل بيانات المورد بنجاح.")
                clear_inputs()
                load_suppliers()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_supplier():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد مورد من الجدول لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف المورد رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('suppliers', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف المورد بنجاح.")
                    clear_inputs()
                    load_suppliers()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="إضافة مورد", command=add_supplier, bootstyle="success", width=13).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="تعديل المورد", command=update_supplier, bootstyle="warning", width=13).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="حذف المورد", command=delete_supplier, bootstyle="danger", width=13).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="تنظيف الحقول", command=clear_inputs, bootstyle="secondary", width=13).grid(row=0, column=3, padx=5)

        def load_suppliers():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, date, net, delivery_fee, kilo_price, kilo_amount, total FROM suppliers")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_suppliers()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 4. إدارة العملاء مع التعديل والحذف ----------------
    def create_clients_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة العملاء (إضافة - تعديل - حذف)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="اسم العميل:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="التاريخ:").grid(row=0, column=2, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="الوزن/الكيلو:").grid(row=1, column=0, padx=5, pady=5)
        weight_entry = ttk.Entry(frame)
        weight_entry.insert(0, "0.0")
        weight_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="سعر الكيلو:").grid(row=1, column=2, padx=5, pady=5)
        kilo_price_entry = ttk.Entry(frame)
        kilo_price_entry.insert(0, "0.0")
        kilo_price_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="المدفوع:").grid(row=2, column=0, padx=5, pady=5)
        paid_entry = ttk.Entry(frame)
        paid_entry.insert(0, "0.0")
        paid_entry.grid(row=2, column=1, padx=5, pady=5)

        columns = ["ID", "اسم العميل", "التاريخ", "الوزن", "سعر الكيلو", "الإجمالي", "المدفوع", "المتبقي"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            name_entry.delete(0, tk.END)
            date_entry.delete(0, tk.END); date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            weight_entry.delete(0, tk.END); weight_entry.insert(0, "0.0")
            kilo_price_entry.delete(0, tk.END); kilo_price_entry.insert(0, "0.0")
            paid_entry.delete(0, tk.END); paid_entry.insert(0, "0.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                name_entry.delete(0, tk.END); name_entry.insert(0, vals[1])
                date_entry.delete(0, tk.END); date_entry.insert(0, vals[2])
                weight_entry.delete(0, tk.END); weight_entry.insert(0, str(vals[3]))
                kilo_price_entry.delete(0, tk.END); kilo_price_entry.insert(0, str(vals[4]))
                paid_entry.delete(0, tk.END); paid_entry.insert(0, str(vals[6]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_client():
            try:
                name = parse_required_string(name_entry.get(), "اسم العميل")
                d_str = parse_required_string(date_entry.get(), "التاريخ")
                weight = parse_float_input(weight_entry.get(), "الوزن")
                kilo_price = parse_float_input(kilo_price_entry.get(), "سعر الكيلو")
                paid = parse_float_input(paid_entry.get(), "المدفوع")

                total = weight * kilo_price
                remaining = total - paid

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO clients (name, date, weight, kilo_price, total, paid, remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, d_str, weight, kilo_price, total, paid, remaining))
                conn.commit()

                if total > 0:
                    inv_type = 'CASH' if remaining <= 0 else 'CREDIT'
                    self.acc_ctrl.post_invoice_entry('CLIENT', cursor.lastrowid, d_str, inv_type, total, paid, f"بيع للعميل {name}")

                messagebox.showinfo("تم", "تمت إضافة العميل وترحيل قيد اليومية المتوازن بنجاح")
                clear_inputs()
                load_clients()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def update_client():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد عميل من الجدول لتعديله.")
                return
            try:
                name = parse_required_string(name_entry.get(), "اسم العميل")
                d_str = parse_required_string(date_entry.get(), "التاريخ")
                weight = parse_float_input(weight_entry.get(), "الوزن")
                kilo_price = parse_float_input(kilo_price_entry.get(), "سعر الكيلو")
                paid = parse_float_input(paid_entry.get(), "المدفوع")

                total = weight * kilo_price
                remaining = total - paid

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE clients SET name=?, date=?, weight=?, kilo_price=?, total=?, paid=?, remaining=?
                    WHERE id=?
                ''', (name, d_str, weight, kilo_price, total, paid, remaining, int(selected_id.get())))
                conn.commit()
                messagebox.showinfo("تم التعديل", "تم تعديل بيانات العميل بنجاح.")
                clear_inputs()
                load_clients()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_client():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد عميل لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف العميل رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('clients', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف العميل بنجاح.")
                    clear_inputs()
                    load_clients()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="إضافة عميل", command=add_client, bootstyle="success", width=13).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="تعديل العميل", command=update_client, bootstyle="warning", width=13).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="حذف العميل", command=delete_client, bootstyle="danger", width=13).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="تنظيف الحقول", command=clear_inputs, bootstyle="secondary", width=13).grid(row=0, column=3, padx=5)

        def load_clients():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, date, weight, kilo_price, total, paid, remaining FROM clients")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_clients()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 5. شجرة الحسابات (COA) ----------------
    def create_coa_window(self):
        self.clear_window()
        ttk.Label(self.root, text="شجرة الحسابات القياسية (Chart of Accounts)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="x", padx=20)

        ttk.Label(frame, text="رمز الحساب:").grid(row=0, column=0, padx=5, pady=5)
        code_entry = ttk.Entry(frame)
        code_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="اسم الحساب:").grid(row=0, column=2, padx=5, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="نوع الحساب:").grid(row=0, column=4, padx=5, pady=5)
        type_cb = ttk.Combobox(frame, values=["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"], state="readonly")
        type_cb.grid(row=0, column=5, padx=5, pady=5)
        type_cb.set("ASSET")

        columns = ["ID", "رمز الحساب", "اسم الحساب", "نوع الحساب"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            code_entry.delete(0, tk.END)
            name_entry.delete(0, tk.END)

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                code_entry.delete(0, tk.END); code_entry.insert(0, str(vals[1]))
                name_entry.delete(0, tk.END); name_entry.insert(0, str(vals[2]))
                type_cb.set(vals[3])

        tree.bind("<ButtonRelease-1>", select_item)

        def add_account():
            try:
                code = parse_required_string(code_entry.get(), "رمز الحساب")
                name = parse_required_string(name_entry.get(), "اسم الحساب")
                acc_type = type_cb.get()

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO chart_of_accounts (code, name, account_type) VALUES (?, ?, ?)", (code, name, acc_type))
                conn.commit()
                messagebox.showinfo("تم", "تمت إضافة الحساب بنجاح لشجرة الحسابات")
                clear_inputs()
                load_coa()
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ تكرار", "رمز الحساب هذا مكرر وموجود بالفعل!")
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_account():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد حساب لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الحساب رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('chart_of_accounts', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف الحساب بنجاح.")
                    clear_inputs()
                    load_coa()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=6, padx=10)
        ttk.Button(btn_frame, text="إضافة", command=add_account, bootstyle="success").pack(side="left", padx=2)
        ttk.Button(btn_frame, text="حذف", command=delete_account, bootstyle="danger").pack(side="left", padx=2)
        ttk.Button(btn_frame, text="تنظيف", command=clear_inputs, bootstyle="secondary").pack(side="left", padx=2)

        def load_coa():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name, account_type FROM chart_of_accounts ORDER BY code")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_coa()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 6. قيود اليومية العامة ----------------
    def create_journal_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة قيود اليومية العامة (Double-Entry Journal)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="x", padx=20)

        ttk.Label(frame, text="تاريخ القيد:").grid(row=0, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="البيان/الشرح:").grid(row=0, column=2, padx=5, pady=5)
        desc_entry = ttk.Entry(frame, width=30)
        desc_entry.grid(row=0, column=3, padx=5, pady=5)

        lines_data = []

        lines_frame = ttk.LabelFrame(self.root, text="أسطر القيد المحاسبي", padding=10)
        lines_frame.pack(fill="x", padx=20, pady=10)

        conn = self.acc_ctrl.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, code, name FROM chart_of_accounts ORDER BY code")
        accounts = cursor.fetchall()
        acc_dict = {f"{code} - {name}": acc_id for acc_id, code, name in accounts}

        ttk.Label(lines_frame, text="الحساب:").grid(row=0, column=0, padx=5)
        acc_cb = ttk.Combobox(lines_frame, values=list(acc_dict.keys()), width=25, state="readonly")
        acc_cb.grid(row=0, column=1, padx=5)

        ttk.Label(lines_frame, text="مدين:").grid(row=0, column=2, padx=5)
        debit_entry = ttk.Entry(lines_frame, width=12)
        debit_entry.insert(0, "0.0")
        debit_entry.grid(row=0, column=3, padx=5)

        ttk.Label(lines_frame, text="دائن:").grid(row=0, column=4, padx=5)
        credit_entry = ttk.Entry(lines_frame, width=12)
        credit_entry.insert(0, "0.0")
        credit_entry.grid(row=0, column=5, padx=5)

        lines_tree = ttk.Treeview(lines_frame, columns=["الحساب", "مدين", "دائن"], show="headings", height=4)
        lines_tree.heading("الحساب", text="الحساب")
        lines_tree.heading("مدين", text="مدين")
        lines_tree.heading("دائن", text="دائن")
        lines_tree.grid(row=1, column=0, columnspan=6, pady=10, sticky="ew")

        def add_line():
            try:
                acc_str = acc_cb.get()
                if not acc_str:
                    raise ValueError("يرجى اختيار الحساب")
                acc_id = acc_dict[acc_str]
                deb = parse_float_input(debit_entry.get(), "مدين")
                cred = parse_float_input(credit_entry.get(), "دائن")
                if deb > 0 and cred > 0:
                    raise ValueError("لا يمكن أن يكون السطر مديناً ودائناً في نفس الوقت")

                lines_data.append({"account_id": acc_id, "debit": deb, "credit": cred, "account_str": acc_str})
                lines_tree.insert('', 'end', values=[acc_str, deb, cred])
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        ttk.Button(lines_frame, text="إضافة السطر", command=add_line, bootstyle="info").grid(row=0, column=6, padx=5)

        def save_journal():
            try:
                d_str = parse_required_string(date_entry.get(), "تاريخ القيد")
                desc = parse_required_string(desc_entry.get(), "شرح القيد")
                self.acc_ctrl.create_journal_entry(d_str, desc, "MANUAL", lines_data, self.current_user['username'] if self.current_user else 'admin')
                messagebox.showinfo("تم الترحيل", "تم ترحيل القيد بنجاح وهو متوازن تماماً!")
                lines_data.clear()
                for r in lines_tree.get_children():
                    lines_tree.delete(r)
                load_entries()
            except ValueError as e:
                messagebox.showerror("خطأ في القيد المحاسبي", str(e))

        ttk.Button(frame, text="ترحيل القيد المزدوج", command=save_journal, bootstyle="success", width=20).grid(row=0, column=4, padx=15)

        entries_tree = ttk.Treeview(self.root, columns=["ID", "التاريخ", "البيان", "المرجع", "المُنشيء"], show="headings")
        for c in ["ID", "التاريخ", "البيان", "المرجع", "المُنشيء"]:
            entries_tree.heading(c, text=c)
        entries_tree.pack(expand=True, fill="both", padx=20, pady=10)

        def load_entries():
            for r in entries_tree.get_children():
                entries_tree.delete(r)
            cursor.execute("SELECT id, entry_date, description, reference, created_by FROM journal_entries ORDER BY id DESC")
            for row in cursor.fetchall():
                entries_tree.insert('', 'end', values=row)

        load_entries()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 7. إدارة الموظفين مع التعديل والحذف ----------------
    def create_employees_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة الموظفين والرواتب (CRUD)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="اسم الموظف:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="الوظيفة:").grid(row=0, column=2, padx=5, pady=5)
        pos_entry = ttk.Entry(frame)
        pos_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="القسم:").grid(row=1, column=0, padx=5, pady=5)
        dept_entry = ttk.Entry(frame)
        dept_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="الراتب:").grid(row=1, column=2, padx=5, pady=5)
        salary_entry = ttk.Entry(frame)
        salary_entry.insert(0, "0.0")
        salary_entry.grid(row=1, column=3, padx=5, pady=5)

        columns = ["ID", "اسم الموظف", "الوظيفة", "القسم", "تاريخ التعيين", "الراتب"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            name_entry.delete(0, tk.END)
            pos_entry.delete(0, tk.END)
            dept_entry.delete(0, tk.END)
            salary_entry.delete(0, tk.END); salary_entry.insert(0, "0.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                name_entry.delete(0, tk.END); name_entry.insert(0, vals[1])
                pos_entry.delete(0, tk.END); pos_entry.insert(0, vals[2])
                dept_entry.delete(0, tk.END); dept_entry.insert(0, vals[3])
                salary_entry.delete(0, tk.END); salary_entry.insert(0, str(vals[5]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_employee():
            try:
                name = parse_required_string(name_entry.get(), "اسم الموظف")
                pos = parse_required_string(pos_entry.get(), "الوظيفة")
                dept = parse_required_string(dept_entry.get(), "القسم")
                salary = parse_float_input(salary_entry.get(), "الراتب")
                h_date = datetime.now().strftime("%Y-%m-%d")

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO employees (name, position, department, hire_date, salary)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, pos, dept, h_date, salary))
                conn.commit()
                messagebox.showinfo("تم", "تمت إضافة الموظف بنجاح")
                clear_inputs()
                load_emp()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def update_employee():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد موظف من الجدول لتعديله.")
                return
            try:
                name = parse_required_string(name_entry.get(), "اسم الموظف")
                pos = parse_required_string(pos_entry.get(), "الوظيفة")
                dept = parse_required_string(dept_entry.get(), "القسم")
                salary = parse_float_input(salary_entry.get(), "الراتب")

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE employees SET name=?, position=?, department=?, salary=?
                    WHERE id=?
                ''', (name, pos, dept, salary, int(selected_id.get())))
                conn.commit()
                messagebox.showinfo("تم التعديل", "تم تعديل بيانات الموظف بنجاح.")
                clear_inputs()
                load_emp()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_employee():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد موظف لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الموظف رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('employees', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف الموظف بنجاح.")
                    clear_inputs()
                    load_emp()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="إضافة موظف", command=add_employee, bootstyle="success", width=13).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="تعديل الموظف", command=update_employee, bootstyle="warning", width=13).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="حذف الموظف", command=delete_employee, bootstyle="danger", width=13).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="تنظيف الحقول", command=clear_inputs, bootstyle="secondary", width=13).grid(row=0, column=3, padx=5)

        def load_emp():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, position, department, hire_date, salary FROM employees")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_emp()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 8. إدارة المخزون مع التعديل والحذف والذكاء الاصطناعي ----------------
    def create_inventory_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة المخزون والتنبؤ الذكي للصنف (CRUD)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="اسم الصنف:").grid(row=0, column=0, padx=5, pady=5)
        item_entry = ttk.Entry(frame)
        item_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="الكمية المتوفرة:").grid(row=0, column=2, padx=5, pady=5)
        qty_entry = ttk.Entry(frame)
        qty_entry.insert(0, "0.0")
        qty_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="حد إعادة الطلب:").grid(row=0, column=4, padx=5, pady=5)
        thresh_entry = ttk.Entry(frame)
        thresh_entry.insert(0, "5.0")
        thresh_entry.grid(row=0, column=5, padx=5, pady=5)

        columns = ["ID", "اسم الصنف", "الكمية المتوفرة", "حد إعادة الطلب"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            item_entry.delete(0, tk.END)
            qty_entry.delete(0, tk.END); qty_entry.insert(0, "0.0")
            thresh_entry.delete(0, tk.END); thresh_entry.insert(0, "5.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                item_entry.delete(0, tk.END); item_entry.insert(0, str(vals[1]))
                qty_entry.delete(0, tk.END); qty_entry.insert(0, str(vals[2]))
                thresh_entry.delete(0, tk.END); thresh_entry.insert(0, str(vals[3]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_item():
            try:
                item = parse_required_string(item_entry.get(), "اسم الصنف")
                qty = parse_float_input(qty_entry.get(), "الكمية")
                thresh = parse_float_input(thresh_entry.get(), "حد إعادة الطلب")

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO inventory (item, quantity, min_threshold) VALUES (?, ?, ?)", (item, qty, thresh))
                item_id = cursor.lastrowid
                conn.commit()

                if qty > 0:
                    self.ai_ctrl.record_transaction(item_id, 'IN', qty)

                messagebox.showinfo("تم", "تم إضافة الصنف بنجاح")
                clear_inputs()
                load_inv()
            except sqlite3.IntegrityError:
                messagebox.showerror("تكرار", "هذا الصنف موجود بالفعل بجدول المخزون!")
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def update_item():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد صنف لتعديله.")
                return
            try:
                item = parse_required_string(item_entry.get(), "اسم الصنف")
                qty = parse_float_input(qty_entry.get(), "الكمية")
                thresh = parse_float_input(thresh_entry.get(), "حد إعادة الطلب")

                conn = self.acc_ctrl.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE inventory SET item=?, quantity=?, min_threshold=? WHERE id=?", (item, qty, thresh, int(selected_id.get())))
                conn.commit()
                messagebox.showinfo("تم التعديل", "تم تعديل بيانات الصنف بنجاح.")
                clear_inputs()
                load_inv()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_item():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد صنف لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الصنف رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('inventory', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف الصنف بنجاح.")
                    clear_inputs()
                    load_inv()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="إضافة صنف", command=add_item, bootstyle="success", width=13).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="تعديل الصنف", command=update_item, bootstyle="warning", width=13).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="حذف الصنف", command=delete_item, bootstyle="danger", width=13).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="تنظيف", command=clear_inputs, bootstyle="secondary", width=13).grid(row=0, column=3, padx=5)

        def run_ai_forecast():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "يرجى تحديد صنف من القائمة لإجراء التنبؤ الذكي عليه.")
                return
            item_id = tree.item(selected)['values'][0]
            res = self.ai_ctrl.forecast_item_inventory(item_id)

            win = tk.Toplevel(self.root)
            win.title(f"تقرير التنبؤ الذكي للصنف: {res['item_name']}")
            win.geometry("420x320")

            ttk.Label(win, text=f"تحليل الاستهلاك لصنف: {res['item_name']}", font=("Arial", 14, "bold"), bootstyle="primary").pack(pady=15)
            ttk.Label(win, text=f"الكمية الحالية: {res['current_qty']}", font=("Arial", 12)).pack(pady=5)
            ttk.Label(win, text=f"معدل السحب اليومي: {res.get('avg_consumption', 0)} وحدات", font=("Arial", 12)).pack(pady=5)
            ttk.Label(win, text=f"الأيام المتبقية لنفاد المخزون: {res['estimated_days_left']} يوم", font=("Arial", 12), bootstyle="danger" if res.get('needs_reorder') else "success").pack(pady=5)
            ttk.Label(win, text=f"الكمية الموصى بإعادة طلبها: {res['recommended_reorder_qty']} وحدة", font=("Arial", 12, "bold")).pack(pady=10)

        ttk.Button(self.root, text="التنبؤ الذكي للصنف المحدد (Inventory AI)", command=run_ai_forecast, bootstyle="dark", width=35).pack(pady=5)

        def load_inv():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, item, quantity, min_threshold FROM inventory")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_inv()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 9. إدارة المصروفات مع التعديل والحذف ----------------
    def create_expenses_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة المصروفات مع التترحيل التلقائي لقيد اليومية (CRUD)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="التاريخ:").grid(row=0, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="بيان المصروف:").grid(row=0, column=2, padx=5, pady=5)
        desc_entry = ttk.Entry(frame, width=25)
        desc_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="المبلغ:").grid(row=1, column=0, padx=5, pady=5)
        amt_entry = ttk.Entry(frame)
        amt_entry.insert(0, "0.0")
        amt_entry.grid(row=1, column=1, padx=5, pady=5)

        conn = self.acc_ctrl.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, code, name FROM chart_of_accounts WHERE account_type = 'EXPENSE'")
        exp_accs = {f"{code} - {name}": acc_id for acc_id, code, name in cursor.fetchall()}

        cursor.execute("SELECT id, code, name FROM chart_of_accounts WHERE account_type = 'ASSET'")
        asset_accs = {f"{code} - {name}": acc_id for acc_id, code, name in cursor.fetchall()}

        ttk.Label(frame, text="حساب المصروف (مدين):").grid(row=1, column=2, padx=5, pady=5)
        exp_cb = ttk.Combobox(frame, values=list(exp_accs.keys()), state="readonly", width=22)
        if exp_accs: exp_cb.set(list(exp_accs.keys())[0])
        exp_cb.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="حساب السداد/النقدية (دائن):").grid(row=2, column=0, padx=5, pady=5)
        asset_cb = ttk.Combobox(frame, values=list(asset_accs.keys()), state="readonly", width=22)
        if asset_accs: asset_cb.set(list(asset_accs.keys())[0])
        asset_cb.grid(row=2, column=1, padx=5, pady=5)

        columns = ["ID", "التاريخ", "البيان", "المبلغ", "رقم قيد اليومية"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            date_entry.delete(0, tk.END); date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            desc_entry.delete(0, tk.END)
            amt_entry.delete(0, tk.END); amt_entry.insert(0, "0.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                date_entry.delete(0, tk.END); date_entry.insert(0, str(vals[1]))
                desc_entry.delete(0, tk.END); desc_entry.insert(0, str(vals[2]))
                amt_entry.delete(0, tk.END); amt_entry.insert(0, str(vals[3]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_expense():
            try:
                d_str = parse_required_string(date_entry.get(), "التاريخ")
                desc = parse_required_string(desc_entry.get(), "بيان المصروف")
                amt = parse_float_input(amt_entry.get(), "المبلغ", min_val=0.01)

                exp_acc_id = exp_accs[exp_cb.get()]
                asset_acc_id = asset_accs[asset_cb.get()]

                entry_id = self.acc_ctrl.post_expense_entry(d_str, desc, amt, asset_acc_id, exp_acc_id)
                messagebox.showinfo("تم التلقائي", f"تم تسجيل المصروف وترحيل قيد متوازن رقم ({entry_id}) بنجاح!")
                clear_inputs()
                load_exp()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_expense():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد مصروف لحذفه.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف المصروف رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('expenses', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف المصروف بنجاح.")
                    clear_inputs()
                    load_exp()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="تسجيل المصروف", command=add_expense, bootstyle="success", width=15).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="حذف المصروف", command=delete_expense, bootstyle="danger", width=15).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="تنظيف الحقول", command=clear_inputs, bootstyle="secondary", width=15).grid(row=0, column=2, padx=5)

        def load_exp():
            for r in tree.get_children():
                tree.delete(r)
            cursor.execute("SELECT id, expense_date, description, amount, journal_entry_id FROM expenses")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_exp()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 10. الفواتير والترحيل التلقائي ----------------
    def create_invoices_window(self):
        self.clear_window()
        ttk.Label(self.root, text="إدارة الفواتير والترحيل المحاسبي (CRUD)", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        selected_id = tk.StringVar(value="")

        frame = ttk.Frame(self.root, padding=10)
        frame.pack(pady=5)

        ttk.Label(frame, text="نوع الطرف:").grid(row=0, column=0, padx=5, pady=5)
        party_cb = ttk.Combobox(frame, values=["CLIENT", "SUPPLIER"], state="readonly")
        party_cb.set("CLIENT")
        party_cb.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="نوع الفاتورة:").grid(row=0, column=2, padx=5, pady=5)
        inv_type_cb = ttk.Combobox(frame, values=["CASH", "CREDIT"], state="readonly")
        inv_type_cb.set("CASH")
        inv_type_cb.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="الإجمالي:").grid(row=1, column=0, padx=5, pady=5)
        total_entry = ttk.Entry(frame)
        total_entry.insert(0, "0.0")
        total_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="المدفوع:").grid(row=1, column=2, padx=5, pady=5)
        paid_entry = ttk.Entry(frame)
        paid_entry.insert(0, "0.0")
        paid_entry.grid(row=1, column=3, padx=5, pady=5)

        columns = ["ID", "الطرف", "التاريخ", "النوع", "الإجمالي", "المدفوع", "المتبقي", "رقم القيد"]
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        def clear_inputs():
            selected_id.set("")
            total_entry.delete(0, tk.END); total_entry.insert(0, "0.0")
            paid_entry.delete(0, tk.END); paid_entry.insert(0, "0.0")

        def select_item(event):
            selected = tree.selection()
            if selected:
                vals = tree.item(selected)['values']
                selected_id.set(str(vals[0]))
                party_cb.set(vals[1])
                inv_type_cb.set(vals[3])
                total_entry.delete(0, tk.END); total_entry.insert(0, str(vals[4]))
                paid_entry.delete(0, tk.END); paid_entry.insert(0, str(vals[5]))

        tree.bind("<ButtonRelease-1>", select_item)

        def add_invoice():
            try:
                p_type = party_cb.get()
                inv_type = inv_type_cb.get()
                tot = parse_float_input(total_entry.get(), "الإجمالي", min_val=0.01)
                paid = parse_float_input(paid_entry.get(), "المدفوع")
                d_str = datetime.now().strftime("%Y-%m-%d")

                entry_id = self.acc_ctrl.post_invoice_entry(p_type, 1, d_str, inv_type, tot, paid, "فاتورة مباشرة")
                messagebox.showinfo("تم", f"تم إنشاء الفاتورة وترحيل القيد رقم ({entry_id}) بنجاح")
                clear_inputs()
                load_inv()
            except ValueError as e:
                messagebox.showwarning("تنبيه الإدخال", str(e))

        def delete_invoice():
            if not selected_id.get():
                messagebox.showwarning("تنبيه", "يرجى تحديد فاتورة لحذفها.")
                return
            if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الفاتورة رقم ({selected_id.get()})؟"):
                try:
                    self.acc_ctrl.delete_record('invoices', int(selected_id.get()))
                    messagebox.showinfo("تم الحذف", "تم حذف الفاتورة بنجاح.")
                    clear_inputs()
                    load_inv()
                except ValueError as e:
                    messagebox.showerror("ممنوع الحذف", str(e))

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="إصدار وترحيل الفاتورة", command=add_invoice, bootstyle="success", width=18).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="حذف الفاتورة", command=delete_invoice, bootstyle="danger", width=14).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="تنظيف الحقول", command=clear_inputs, bootstyle="secondary", width=14).grid(row=0, column=2, padx=5)

        def load_inv():
            for r in tree.get_children():
                tree.delete(r)
            conn = self.acc_ctrl.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, party_type, invoice_date, invoice_type, total_amount, paid_amount, remaining_amount, journal_entry_id FROM invoices")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)

        load_inv()
        ttk.Button(self.root, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=25).pack(pady=10)

    # ---------------- 11. واجهة التقارير التفاعلية والدورية الـ PDF ----------------
    def create_reports_window(self):
        self.clear_window()
        ttk.Label(self.root, text="مركز التقارير المحاسبية الدورية واستخراج PDF المعرب", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

        filter_frame = ttk.LabelFrame(self.root, text="إعدادات التقرير والفلترة الدورية", padding=15)
        filter_frame.pack(fill="x", padx=20, pady=5)

        ttk.Label(filter_frame, text="اختر القسم:").grid(row=0, column=0, padx=5, pady=5)
        section_map = {
            "ميزان المراجعة (Trial Balance)": "TRIAL_BALANCE",
            "الموردين (Suppliers)": "SUPPLIERS",
            "العملاء (Clients)": "CLIENTS",
            "الموظفين (Employees)": "EMPLOYEES",
            "المصروفات (Expenses)": "EXPENSES",
            "الفواتير (Invoices)": "INVOICES",
            "المخزون (Inventory)": "INVENTORY"
        }
        section_cb = ttk.Combobox(filter_frame, values=list(section_map.keys()), state="readonly", width=28)
        section_cb.set("ميزان المراجعة (Trial Balance)")
        section_cb.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="الفترة الزمنية:").grid(row=0, column=2, padx=5, pady=5)
        period_map = {
            "الجميع (الكل)": "ALL",
            "تقرير يومي (Daily)": "DAILY",
            "تقرير شهري (Monthly)": "MONTHLY",
            "تقرير سنوي (Annual)": "ANNUAL"
        }
        period_cb = ttk.Combobox(filter_frame, values=list(period_map.keys()), state="readonly", width=22)
        period_cb.set("الجميع (الكل)")
        period_cb.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="تاريخ التقرير:").grid(row=0, column=4, padx=5, pady=5)
        date_entry = ttk.Entry(filter_frame, width=15)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=5, padx=5, pady=5)

        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(expand=True, fill="both", padx=20, pady=10)

        tree = ttk.Treeview(tree_frame, show="headings")
        tree.pack(expand=True, fill="both")

        summary_var = tk.StringVar(value="جاهز لاستخراج تقارير الأقسام...")
        ttk.Label(self.root, textvariable=summary_var, font=("Arial", 12, "bold"), bootstyle="primary").pack(pady=5)

        def apply_filter():
            sec_key = section_map[section_cb.get()]
            per_key = period_map[period_cb.get()]
            d_val = date_entry.get().strip()

            rep_data = self.acc_ctrl.get_periodical_report_data(sec_key, per_key, d_val)

            # إعادة ضبط أعمدة الشجرة
            tree.delete(*tree.get_children())
            tree['columns'] = rep_data['headers']
            for h in rep_data['headers']:
                tree.heading(h, text=h)
                tree.column(h, width=130, anchor="center")

            for r in rep_data['rows']:
                tree.insert('', 'end', values=r)

            summary_var.set(rep_data['summary'])

        ttk.Button(filter_frame, text="عرض التقرير", command=apply_filter, bootstyle="info", width=14).grid(row=0, column=6, padx=10)

        def export_pdf():
            sec_name_ar = section_cb.get()
            sec_key = section_map[sec_name_ar]
            per_name_ar = period_cb.get()
            per_key = period_map[per_name_ar]
            d_val = date_entry.get().strip()

            rep_data = self.acc_ctrl.get_periodical_report_data(sec_key, per_key, d_val)

            filename = f"Report_{sec_key}_{per_key}.pdf"
            try:
                pdf = ArabicPDFReport(filename=filename)
                pdf.build_report(
                    title="تقرير محاسبي",
                    section_name=sec_name_ar,
                    period_name=per_name_ar,
                    filter_date=d_val,
                    headers=rep_data['headers'],
                    rows=rep_data['rows'],
                    summary_text=rep_data['summary']
                )
                messagebox.showinfo("تم تصدير الـ PDF المعرب", f"تم إنشاء التقرير بنجاح وحفظه في:\n{filename}")
            except Exception as e:
                messagebox.showerror("خطأ تصدير PDF", f"تعذر استخراج ملف الـ PDF: {e}")

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="طباعة التقرير الفاخر بصيغة PDF", command=export_pdf, bootstyle="success", width=30).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="القائمة الرئيسية", command=self.create_dashboard, bootstyle="info", width=20).pack(side="right", padx=10)

        apply_filter()

    # ---------------- 12. النسخ الاحتياطي ----------------
    def backup_database(self):
        try:
            backup_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
            if backup_path:
                import shutil
                shutil.copy(self.acc_ctrl.db.db_path, backup_path)
                messagebox.showinfo("تم", "تم عمل النسخ الاحتياطي بنجاح")
        except Exception as e:
            messagebox.showerror("خطأ النسخ الاحتياطي", str(e))
