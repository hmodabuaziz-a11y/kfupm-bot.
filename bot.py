import os
import asyncio
import pdfplumber
from datetime import datetime, timedelta
from telegram import Bot

TOKEN      = os.getenv(“TELEGRAM_TOKEN”)
MY_CHAT_ID = os.getenv(“CHAT_ID”)
PDF_PATH   = “Calendar-252.pdf”

def fmt_date(d):
“””
تحويل التاريخ لصيغة تطابق الـ PDF تماماً.
الأشهر في الملف: Jan. Feb. Mar. Apr. → بنقطة
May  Jun            → بدون نقطة
“””
s = d.strftime(”%b. %-d”)                              # “Apr. 30”، “May 10”
s = s.replace(“May. “, “May “).replace(“Jun. “, “Jun “)
return s

def get_kfupm_data():
if not os.path.exists(PDF_PATH):
return None

```
today      = datetime.now().date()
term_start = datetime(2026, 1, 11).date()
term_end   = datetime(2026, 5, 21).date()

total_days      = (today - term_start).days
total_term_days = (term_end - term_start).days
percentage      = int(((total_days + 1) / total_term_days) * 100)
remaining       = (term_end - today).days

event_text     = ""
reminder_text  = ""
week_from_file = ""

today_fmt       = fmt_date(today)
tomorrow_fmt    = fmt_date(today + timedelta(days=1))
in_two_days_fmt = fmt_date(today + timedelta(days=2))

try:
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                # الجدول عنده 5 أعمدة: [DAY, WEEK, HIJRI, GREGORIAN, EVENTS]
                if not row or len(row) < 5:
                    continue

                d_val      = str(row[3])                          # العمود [3] = التاريخ الميلادي
                event_desc = str(row[4]).replace('\n', ' ') if row[4] else ""  # [4] = الحدث
                if not event_desc.strip():
                    continue

                # حدث اليوم
                if today_fmt in d_val:
                    if row[1]:
                        week_from_file = str(row[1]).split('\n')[0]
                    event_text = event_desc

                # تذكير: غداً أو بعد غد
                if tomorrow_fmt in d_val and not reminder_text:
                    reminder_text = f"Tomorrow: {event_desc}"
                elif in_two_days_fmt in d_val and not reminder_text:
                    reminder_text = f"In 2 days: {event_desc}"

except Exception as e:
    print(f"PDF error: {e}")

# حساب الأسبوع (مع استثناء إجازة العيد 12 يوم)
holiday_start = datetime(2026, 3, 15).date()
academic_days = total_days
if today >= holiday_start:
    academic_days -= 12

final_week = week_from_file if week_from_file else str((academic_days // 7) + 1)

return percentage, total_days + 1, total_term_days, remaining, final_week, event_text, reminder_text
```

async def main():
data = get_kfupm_data()
if not data:
return

```
p, passed, total, remain, week, event, reminder = data
bar = "▓" * int(p / 5) + "░" * (20 - int(p / 5))

message_parts = [
    f"[{bar}] {p}%",
    f"{remain} days left ⏳",
    f"Week {week}/17 📆",
    f"{passed}/{total} days passed ✅",
]

if event:
    message_parts.append(f"📌 Today: {event}")
if reminder:
    message_parts.append(f"🔔 {reminder}")

message_parts.append("#KFUPM")

msg = "\n\n".join(message_parts)
bot = Bot(token=TOKEN)
await bot.send_message(chat_id=MY_CHAT_ID, text=msg)
```

if **name** == “**main**”:
asyncio.run(main())