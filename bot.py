import os
import re
import asyncio
import pdfplumber
from datetime import datetime, timedelta
from telegram import Bot

TOKEN      = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("CHAT_ID")
PDF_PATH   = "Calendar-261.pdf"

TERM_START    = datetime(2026, 8, 19).date()
TERM_END      = datetime(2026, 12, 24).date()
HOLIDAY_START = datetime(2026, 10, 20).date()
HOLIDAY_END   = datetime(2026, 10, 24).date()
AUTUMN_START  = datetime(2026, 11, 22).date()
AUTUMN_END    = datetime(2026, 11, 23).date()
TOTAL_WEEKS   = 15

# جدول الأسابيع مباشرة من البلانر
WEEK_SCHEDULE = [
    (1,  datetime(2026,  8, 16).date(), datetime(2026,  8, 22).date()),
    (2,  datetime(2026,  8, 23).date(), datetime(2026,  8, 29).date()),
    (3,  datetime(2026,  8, 30).date(), datetime(2026,  9,  5).date()),
    (4,  datetime(2026,  9,  6).date(), datetime(2026,  9, 12).date()),
    (5,  datetime(2026,  9, 13).date(), datetime(2026,  9, 19).date()),
    (6,  datetime(2026,  9, 20).date(), datetime(2026,  9, 26).date()),
    (7,  datetime(2026,  9, 27).date(), datetime(2026, 10,  3).date()),
    (8,  datetime(2026, 10,  4).date(), datetime(2026, 10, 10).date()),
    (9,  datetime(2026, 10, 11).date(), datetime(2026, 10, 17).date()),
    (10, datetime(2026, 10, 18).date(), datetime(2026, 10, 31).date()),  # إجازة + استئناف
    (11, datetime(2026, 11,  1).date(), datetime(2026, 11,  7).date()),
    (12, datetime(2026, 11,  8).date(), datetime(2026, 11, 14).date()),
    (13, datetime(2026, 11, 15).date(), datetime(2026, 11, 21).date()),
    (14, datetime(2026, 11, 22).date(), datetime(2026, 12,  5).date()),  # إجازة خريف + استئناف
    (15, datetime(2026, 12,  6).date(), datetime(2026, 12, 12).date()),
]

MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}


def get_week_num(today):
    for week, start, end in WEEK_SCHEDULE:
        if start <= today <= end:
            return week
    # أسابيع الامتحانات
    if datetime(2026, 12, 13).date() <= today <= datetime(2026, 12, 24).date():
        return "Final"
    return "-"


def parse_dates(raw: str):
    raw = raw.replace('\n', ' ').strip()
    dates = []
    yr = 2026

    m = re.fullmatch(
        r'([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})\s*[-]\s*([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(3)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(6)), MONTH_MAP[m.group(4)[:3]], int(m.group(5))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(
        r'([A-Za-z]+)\.?\s+(\d+),?\s+(\d{4})\s*-\s*([A-Za-z]+)\.?\s+(\d+),\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(3)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(6)), MONTH_MAP[m.group(4)[:3]], int(m.group(5))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)\s*[-]\s*([A-Za-z]+)\.?\s+(\d+)', raw)
    if m:
        d1 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(yr, MONTH_MAP[m.group(3)[:3]], int(m.group(4))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+),\s+(\d{4})\s*-\s*([A-Za-z]+)\.?\s+(\d+),\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(3)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(6)), MONTH_MAP[m.group(4)[:3]], int(m.group(5))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)-(\d+)\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)-(\d+),?\s+(\d{4})', raw)
    if m:
        d1 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(int(m.group(4)), MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

    m = re.fullmatch(r'([A-Za-z]+)\.?\s+(\d+)\s*[-]\s*(\d+)', raw)
    if m:
        d1 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(2))).date()
        d2 = datetime(yr, MONTH_MAP[m.group(1)[:3]], int(m.group(3))).date()
        cur = d1
        while cur <= d2:
            dates.append(cur); cur += timedelta(days=1)
        return dates

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

    week_num = get_week_num(today)

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

    week_display = f"Week {week}/{TOTAL_WEEKS}" if isinstance(week, int) else "🎓 Final Examinations"

    message_parts = [
        f"[{bar}] {p}%",
        f"{remain} days left ⏳",
        f"{week_display} 📆",
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


if __name__ == "__main__":
    asyncio.run(main())
