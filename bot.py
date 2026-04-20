import os
import asyncio
import pdfplumber
from datetime import datetime
from telegram import Bot

# جلب البيانات من "أسرار جيت هاب" لضمان الأمان
TOKEN      = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("CHAT_ID")
PDF_PATH   = "Calendar-252.pdf"

def get_kfupm_data():
    if not os.path.exists(PDF_PATH):
        return None
    
    today = datetime.now().date()
    term_start = datetime(2026, 1, 11).date() 
    term_end   = datetime(2026, 5, 21).date() 
    
    # 1. حسبة الأيام والنسبة
    total_days = (today - term_start).days
    total_term_days = (term_end - term_start).days
    percentage = int(((total_days + 1) / total_term_days) * 100)
    remaining = (term_end - today).days

    # 2. استخراج الحدث والأسبوع من الملف
    event_text = ""
    week_from_file = ""
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                for row in table:
                    if not row or len(row) < 6: continue
                    d_val = str(row[4])
                    # البحث عن تاريخ اليوم أو نطاق التسجيل الحالي
                    if today.strftime("%b. %d") in d_val or "Apr. 18-Apr. 26" in d_val:
                        if row[2]: week_from_file = str(row[2]).split('\n')[0]
                        event_text = str(row[5]).replace('\n', ' ')
    except:
        pass

    # 3. الحل الذكي لحساب الأسبوع (خصم إجازة العيد 14 يوم)
    holiday_start = datetime(2026, 3, 15).date()
    academic_days = total_days
    if today >= holiday_start:
        academic_days -= 14
    
    # إذا لم يجد الأسبوع في الملف، نستخدم الحسبة المستنتجة
    final_week = week_from_file if week_from_file else str((academic_days // 7) + 1)

    return percentage, total_days + 1, total_term_days, remaining, final_week, event_text

async def main():
    data = get_kfupm_data()
    if not data: return
    
    p, passed, total, remain, week, event = data
    bar = "▓" * int(p/5) + "░" * (20 - int(p/5))
    
    # التعديل هنا: إضافة مسافات (\n\n) بين كل سطر لتصبح الرسالة مريحة للعين
    msg = f"[{bar}]{p}%\n\n"
    msg += f"{remain} days left ⏳\n\n"
    msg += f"Week {week}/18 📆"
    msg += f"{passed}/{total} days passed ✅\n\n"
    
    if event:
        msg += f"\n\nToday: {event} 💡"
        
    msg += "\n\n#KFUPM"

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=MY_CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
