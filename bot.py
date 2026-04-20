import os
import pdfplumber
from datetime import datetime
from telegram import Bot

# --- البيانات الأساسية ---
TOKEN      = "8556739658:AAFxPynSrtd7COAfraLuEaTpqEUlVwFOK-M"
MY_CHAT_ID = "687288636"
PDF_PATH   = "Calendar-252.pdf" if os.path.exists("Calendar-252.pdf") else "../Calendar-252.pdf"

def get_best_kfupm_data():
    if not os.path.exists(PDF_PATH):
        return None
    
    today = datetime.now().date()
    term_start = None
    term_end = None
    event_text = ""
    week_num = ""

    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            
            for row in table:
                if not row or len(row) < 6:
                    continue
                
                # تنظيف البيانات لتسهيل البحث
                w_val = str(row[2]).strip() if row[2] else ""
                d_val = str(row[4]).strip() if row[4] else ""
                e_val = str(row[5]).strip() if row[5] else ""

                # 1. استخراج تواريخ الترم الأساسية
                if "Classes begin" in e_val or "REGISTRATION CONFIRMATION" in e_val:
                    term_start = datetime(2026, 1, 11).date()
                if "Last day for faculty" in e_val:
                    term_end = datetime(2026, 5, 21).date()

                # 2. البحث عن أحداث اليوم
                search_date = today.strftime("%b. %-d")
                if search_date in d_val or "Apr. 18-Apr. 26" in d_val:
                    # سحب رقم الأسبوع من الملف إذا وجد وكان غير فارغ
                    if w_val and w_val != "None":
                        week_num = w_val.split(' ')[0].split('-')[0].split('\n')[0]
                    event_text = e_val.replace('\n', ' ')

    # --- الحسابات الديناميكية الدقيقة ---
    s_date = term_start if term_start else datetime(2026, 1, 11).date()
    e_date = term_end if term_end else datetime(2026, 5, 21).date()
    
    # حساب الأيام الكلية للمؤشر
    total_days = (today - s_date).days
    total_term_days = (e_date - s_date).days
    
    # حساب الأسبوع مع خصم إجازة العيد
    holiday_start = datetime(2026, 3, 15).date()
    academic_days_passed = total_days
    
    if today >= holiday_start:
        academic_days_passed -= 14
    
    # حساب الأسبوع استنتاجياً إذا لم ينجح سحبه من الملف
    if not week_num or week_num == "" or week_num == "N/A":
        week_num = str((academic_days_passed // 7) + 1)
        
    # النسبة المئوية والأيام المتبقية
    percentage = int(((total_days + 1) / total_term_days) * 100)
    remaining = (e_date - today).days

    return percentage, total_days + 1, total_term_days, remaining, week_num, event_text

async def send_final_update():
    data = get_best_kfupm_data()
    if not data:
        print(f"❌ لم يتم العثور على الملف في المسار: {PDF_PATH}")
        return

    p, passed, total, remain, week, event = data
    bar = "▓" * int(p / 5) + "░" * (20 - int(p / 5))
    
    msg = (
        f"[{bar}] {p}%\n\n"
        f"{passed}/{total} days passed ✅\n\n"
        f"{remain} days left ⏳\n\n"
        f"Week {week}/18 📆"
    )

    if event:
        msg += f"\n\nToday: {event} 💡"

    msg += "\n\n#KFUPM"

    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=MY_CHAT_ID, text=msg)
        print(f"✅ تم الإرسال بنجاح! الأسبوع الدقيق هو: {week}")
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {e}")

# تشغيل البوت
await send_final_update()
