import os
import re
import asyncio
import pdfplumber
from datetime import datetime, timedelta
from telegram import Bot
TOKEN      = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("CHAT_ID")
PDF_PATH   = "Calendar-252.pdf"
TERM_START    = datetime(2026, 1, 11).date()
TERM_END      = datetime(2026, 5, 21).date()
HOLIDAY_START = datetime(2026, 3, 15).date()
HOLIDAY_END   = datetime(2026, 3, 26).date()
TOTAL_WEEKS   = 17
MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}
def parse_dates(raw: str):
    raw = raw.replace('\n', ' ').strip()
    dates = []
    yr = 2026
    # "Jan. 25, 2026 - Feb. 5, 2026"
    m = re.fullmatch(
        r'([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})\s*[-]\s*([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(3)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(6)), MONTH_MAP[m.group(4)[:3]], int(m.group(5))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates
    # "Apr. 18 - Apr. 26"
    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)\s*[-]\s*([A-Za-z]+)\.?\s+(\d+)', raw)
    if m:
        d1 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(yr, MONTH_MAP[m.group(3)[:3]], int(m.group(4))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates
    # "Mar. 1-12, 2026"
    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)-(\d+),?\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates
    # "Mar. 15 - 26"
    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)\s*[-]\s*(\d+)', raw)
    if m:
        d1 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates
    # "May 11 - 20"
    m = re.fullmatch(r'([A-Za-z]+)\s+(\d+)\s*[-]\s*(\d+)', raw)
    if m:
        d1 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates
    # "Jan. 11, 2026" or "Apr 30, 2026"
    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})', raw)
    if m:
        dates.append(datetime(int(m.group(3)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date())
        return dates
    return dates
def build_calendar_from_pdf():
    date_events = {}
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                # 5 columns: [DAY, WEEK, HIJRI, GREGORIAN_DATE, EVENT]
                if not row or len(row) < 5:
                    continue
                raw_date = str(row[3] or '').replace('\n', ' ').strip()
                event    = str(row[4] or '').replace('\n', ' ').strip()
                if not raw_date or not event or raw_date == 'GREGORIAN DATE':
                    continue
                for d in parse_dates(raw_date):
                    date_events.setdefault(d, []).append(event)
    return date_events
def get_kfupm_data():
    if not os.path.exists(PDF_PATH):
        return None
    today           = datetime.now().date()
    total_term_days = (TERM_END - TERM_START).days
    days_passed     = (today - TERM_START).days
    remaining       = (TERM_END - today).days
    percentage      = min(100, int(((days_passed + 1) / total_term_days) * 100))
    if today <= HOLIDAY_END:
        week_num = (days_passed // 7) + 1
    else:
        pre      = (HOLIDAY_START - TERM_START).days
        post     = (today - HOLIDAY_END).days - 1
        week_num = (pre // 7) + (post // 7) + 1
    week_num = max(1, min(week_num, TOTAL_WEEKS))
    date_events  = build_calendar_from_pdf()
    today_events = date_events.get(today, [])
    event_text   = " | ".join(today_events) if today_events else ""
    reminder_text = ""
    for delta in range(1, 4):
        future = today + timedelta(days=delta)
        evs    = date_events.get(future, [])
        if evs:
            label         = "Tomorrow" if delta == 1 else f"In {delta} days"
            reminder_text = f"{label} ({future.strftime('%b %d')}): {' | '.join(evs)}"
            break
    return percentage, days_passed + 1, total_term_days, remaining, week_num, event_text, reminder_text
async def main():
    data = get_kfupm_data()
    if not data:
        return
    p, passed, total, remain, week, event, reminder = data
    bar = "▓" * int(p / 5) + "░" * (20 - int(p / 5))
    message_parts = [
        f"[{bar}] {p}%",
        f"{remain} days left ",
        f"Week {week}/{TOTAL_WEEKS} ",
        f"{passed}/{total} days passed ",
    ]
    if event:
        message_parts.append(f" Today: {event}")
    if reminder:
        message_parts.append(f" {reminder}")
    message_parts.append("#KFUPM")
    msg = "\n\n".join(message_parts)
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=MY_CHAT_ID, text=msg)
if __name__ == "__main__":
    asyncio.run(main())
