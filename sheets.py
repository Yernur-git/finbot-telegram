import os
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
RECORDS_RANGE = "Записи!A:E"

def _service():
    creds_json = os.environ.get("GOOGLE_CREDS_JSON", "")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds).spreadsheets()

def append_transaction(date, tx_type, category, desc, amount):
    svc = _service()
    svc.values().append(
        spreadsheetId=SHEET_ID,
        range=RECORDS_RANGE,
        valueInputOption="USER_ENTERED",
        body={"values": [[date, tx_type, category, desc, amount]]}
    ).execute()

def get_monthly_summary(raw=False):
    svc = _service()
    result = svc.values().get(
        spreadsheetId=SHEET_ID,
        range=RECORDS_RANGE
    ).execute()
    rows = result.get("values", [])[1:]  # skip header

    now = datetime.now()
    cur_month = now.month
    cur_year = now.year

    filtered = []
    for r in rows:
        if len(r) >= 5 and r[0]:
            try:
                parts = r[0].split(".")
                if len(parts) == 3:
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if m == cur_month and y == cur_year:
                        filtered.append(r)
            except:
                continue

    def parse_amt(s):
        return float(str(s).replace("\xa0","").replace(" ","").replace(",","."))
    income  = sum(parse_amt(r[4]) for r in filtered if len(r)>4 and r[1] == "Доход")
    expense = sum(parse_amt(r[4]) for r in filtered if len(r)>4 and r[1] == "Расход")
    balance = income - expense
    goal    = 200000

    if raw:
        lines = "\n".join([f"{r[0]} | {r[1]} | {r[2]} | {r[3] if len(r)>3 else ''} | {r[4]}₸" for r in filtered])
        return (
            f"Месяц: {now.strftime('%B %Y')}\n"
            f"Доход: {int(income):,}₸\nРасход: {int(expense):,}₸\nОстаток: {int(balance):,}₸\n\n"
            f"Детали:\n{lines or 'Нет записей'}"
        ).replace(",", " ")

    pct = int(income / goal * 100) if goal else 0
    bar_filled = min(10, int(pct / 10))
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    return (
        f"📊 {now.strftime('%B %Y')}\n\n"
        f"💚 Доход:   {int(income):,}₸\n"
        f"🔴 Расход:  {int(expense):,}₸\n"
        f"💰 Остаток: {int(balance):,}₸\n\n"
        f"🎯 Цель 200 000₸\n"
        f"[{bar}] {pct}%\n"
        f"До цели: {max(0, int(goal-income)):,}₸"
    ).replace(",", " ")
