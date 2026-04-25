import os
import asyncio
import pdfplumber
from datetime import datetime, timedelta
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
    
    total_days = (today - term_start).days
    total_term_days = (term_end - term_start).days
    percentage = int(((total_days + 1) / total_term_days) * 100)
    remaining = (term_end - today).days

    event_text = ""
    reminder_text = ""
    week_from_file = ""
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                for row in table:
                    if not row or len(row) < 6: continue

                    d_val = str(row[4])
                    event_desc = str(row[5]).replace('\n', ' ') if row[5] else ""

                    # Today's event
                    if today.strftime("%b. %d") in d_val or "Apr. 18-Apr. 26" in d_val:
                        if row[2]: week_from_file = str(row[2]).split('\n')[0]
                        event_text = event_desc

                    # Reminder: tomorrow or in 2 days
                    tomorrow     = (today + timedelta(days=1)).strftime("%b. %d")
                    in_two_days  = (today + timedelta(days=2)).strftime("%b. %d")

                    if tomorrow in d_val and not reminder_text:
                        reminder_text = f"Tomorrow: {event_desc}"
                    elif in_two_days in d_val and not reminder_text:
                        reminder_text = f"In 2 days: {event_desc}"

    except:
        pass

    holiday_start = datetime(2026, 3, 15).date()
    academic_days = total_days
    if today >= holiday_start:
        academic_days -= 14
    
    final_week = week_from_file if week_from_file else str((academic_days // 7) + 1)

    return percentage, total_days + 1, total_term_days, remaining, final_week, event_text, reminder_text

async def main():
    data = get_kfupm_data()
    if not data: return
    
    p, passed, total, remain, week, event, reminder = data
    bar = "▓" * int(p/5) + "░" * (20 - int(p/5))
    
    message_parts = [
        f"[{bar}]{p}%",
        f"{remain} days left ⏳",
        f"Week {week}/17 📆",
        f"{passed}/{total} days passed ✅"
    ]
    
    if event:
        message_parts.append(f"Today: {event}")

    if reminder:
        message_parts.append(reminder)
        
    message_parts.append("#KFUPM")
    
    msg = "\n\n".join(message_parts)

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=MY_CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
