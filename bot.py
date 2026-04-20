import os
import asyncio
import pdfplumber
from datetime import datetime
from telegram import Bot

# جلب البيانات من أسرار GitHub (GitHub Secrets) لضمان الأمان
TOKEN      = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("CHAT_ID")
PDF_PATH   = "Calendar-252.pdf"

def get_best_kfupm_data():
    if not os.path.exists(PDF_PATH):
        return None
    
    today = datetime.now().date()
    term_start, term_end = None, None
    event_text, week_num = "", ""

    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table: continue
            for row in table:
                if not row or len(row) < 6: continue
                w_val, d_val, e_val = str(row[2]), str(row[4]), str(row[5])

                if "Classes begin" in e_val or "REGISTRATION CONFIRMATION" in e_val:
                    term_start = datetime(2026, 1, 11).date()
                if "Last day for faculty" in e_val:
                    term_end = datetime(2026, 5, 21).date()

                search_date = today.strftime("%b. %-d")
                if search_date in d_val or "Apr. 18-Apr. 26" in d_val:
                    if row[2]: week_num = w_val.split(' ')[0].split('-')[0].split('\n')[0]
                    event_text = e_val.replace('\n', ' ')

    s_date = term_start if term_start else datetime(2026, 1, 11).date()
    e_date = term_end if term_end else datetime(2026, 5, 21).date()
    
    total_days = (today - s_date).days
    total_term_days = (e_date - s_date).days
    
    # استثناء إجازة العيد
    holiday_start = datetime(2026, 3, 15).date()
    academic_days = total_days
    if today >= holiday_start: academic_days -= 14
    
    if not week_num or week_num == "None":
        week_num = str((academic_days // 7) + 1)
        
    percentage = int(((total_days + 1) / total_term_days) * 100)
    return percentage, total_days + 1, total_term_days, (e_date - today).days, week_num, event_text

async def main():
    data = get_best_kfupm_data()
    if not data: return
    p, passed, total, remain, week, event = data
    bar = "▓" * int(p/5) + "░" * (20 - int(p/5))
    msg = f"[{bar}]{p}%\n\n{passed}/{total} days passed ✅\n{remain} days left 📅\nWeek {week}/18 📆"
    if event: msg += f"\n\nToday: {event} 💡"
    msg += "\n\n#KFUPM"

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=MY_CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())