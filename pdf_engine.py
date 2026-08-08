import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import arabic_reshaper
from bidi.algorithm import get_display

class ArabicPDFReport:
    def __init__(self, filename="accounting_report.pdf"):
        self.filename = filename
        self.pagesize = A4
        self.register_arabic_font()

    def register_arabic_font(self):
        """تسجيل الخط العربي لدعم اللغة العربية في ReportLab"""
        font_paths = [
            "arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\tahoma.ttf",
            "C:\\Windows\\Fonts\\tradbdo.ttf"
        ]
        self.arabic_font_name = "Helvetica-Bold"  # الافتراضي عند عدم وجود خط خارجي
        for path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('ArabicFont', path))
                    self.arabic_font_name = 'ArabicFont'
                    break
                except Exception:
                    pass

    def reshape_text(self, text):
        """معالجة النص العربي وتعديل الاتجاه من اليمين إلى اليسار (RTL)"""
        if not text:
            return ""
        text_str = str(text)
        try:
            reshaped = arabic_reshaper.reshape(text_str)
            return get_display(reshaped)
        except Exception:
            return text_str

    def build_report(self, title, section_name, period_name, filter_date, headers, rows, summary_text=""):
        """
        توليد ملف PDF احترافي، مسطر ومنظم بالكامل باللغة العربية
        """
        doc = SimpleDocTemplate(
            self.filename,
            pagesize=self.pagesize,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        elements = []
        styles = getSampleStyleSheet()

        # نمط الترويسة الرئيسية
        title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Heading1'],
            fontName=self.arabic_font_name,
            fontSize=18,
            leading=22,
            alignment=1, # منتصف
            textColor=colors.HexColor('#0f1c3f')
        )

        sub_style = ParagraphStyle(
            'ArabicSubTitle',
            parent=styles['Normal'],
            fontName=self.arabic_font_name,
            fontSize=11,
            leading=15,
            alignment=1, # منتصف
            textColor=colors.HexColor('#475569')
        )

        # 1. الترويسة العلوية والشعار
        header_text = self.reshape_text("وسام Sys - نظام المحاسبة المالي المزدوج")
        elements.append(Paragraph(header_text, title_style))
        elements.append(Spacer(1, 6))

        report_title = self.reshape_text(f"تقرير {section_name} - {period_name}")
        elements.append(Paragraph(report_title, ParagraphStyle('RepTitle', fontName=self.arabic_font_name, fontSize=14, leading=18, alignment=1, textColor=colors.HexColor('#4169E1'))))
        elements.append(Spacer(1, 4))

        date_info = self.reshape_text(f"تاريخ التقرير / الفلترة: {filter_date} | تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        elements.append(Paragraph(date_info, sub_style))
        elements.append(Spacer(1, 15))

        # 2. تجهيز الجدول المسطر
        # عكس ترتيب الأعمدة لتسهيل القراءة بالعربية RTL
        rtl_headers = [self.reshape_text(h) for h in reversed(headers)]
        
        table_data = [rtl_headers]
        for row in rows:
            rtl_row = [self.reshape_text(str(cell)) for cell in reversed(row)]
            table_data.append(rtl_row)

        # حساب العرض التلقائي للأعمدة
        available_width = self.pagesize[0] - 60
        col_count = len(headers)
        col_width = available_width / max(1, col_count)

        table = Table(table_data, colWidths=[col_width] * col_count)

        # تنسيق الجدول المسطر بألوان الأزرق الملكي والرمادي الفاتح
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4169E1')), # أزرق ملكي للترويسة
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')), # شبكة التسطير
        ])

        # صفوف متبادلة الألوان للوضوح
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc'))
            else:
                t_style.add('BACKGROUND', (0, i), (-1, i), colors.white)

        table.setStyle(t_style)
        elements.append(table)
        elements.append(Spacer(1, 15))

        # 3. إجماليات التقرير والتذييل
        if summary_text:
            reshaped_summary = self.reshape_text(summary_text)
            summary_style = ParagraphStyle(
                'SummaryStyle',
                fontName=self.arabic_font_name,
                fontSize=11,
                leading=15,
                alignment=1,
                textColor=colors.HexColor('#0f1c3f')
            )
            elements.append(Paragraph(reshaped_summary, summary_style))
            elements.append(Spacer(1, 10))

        # تذييل الصفحة وتدقيق الحقوق
        footer_text = self.reshape_text("جميع الحقوق محفوظة - تم إصدار هذا التقرير تلقائياً من نظام وسام المحاسبي المالي المزدوج")
        elements.append(Paragraph(footer_text, sub_style))

        doc.build(elements)
        return self.filename
