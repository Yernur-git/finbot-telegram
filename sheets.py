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

    cur_month = datetime.now().strftime("%m.%Y")
    month_rows = []
    for r in rows:
        if len(r) >= 5 and r[0].endswith(cur_month[-7:].replace(".", ".")[-5:]):
            month_rows.append(r)

    # filter by current month (DD.MM.YYYY format)
    cur_m = datetime.now().strftime("%m.%Y")
    filtered = [r for r in rows if len(r) >= 5 and ".".join(r[0].split(".")[1:]) == cur_m]

    income = sum(float(r[4]) for r in filtered if r[1] == "Доход")
    expense = sum(float(r[4]) for r in filtered if r[1] == "Расход")
    balance = income - expense
    goal = 200000

    if raw:
        lines = "\n".join([f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}₸" for r in filtered])
        return (
            f"Месяц: {datetime.now().strftime('%B %Y')}\n"
            f"Доход: {income:,.0f}₸\nРасход: {expense:,.0f}₸\nОстаток: {balance:,.0f}₸\n\n"
            f"Детали:\n{lines or 'Нет записей'}"
        )

    pct = int(income / goal * 100) if goal else 0
    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    return (
        f"📊 {datetime.now().strftime('%B %Y')}\n\n"
        f"💚 Доход:   {income:>10,.0f}₸\n"
        f"🔴 Расход:  {expense:>10,.0f}₸\n"
        f"💰 Остаток: {balance:>10,.0f}₸\n\n"
        f"🎯 Цель 200 000₸\n"
        f"[{bar}] {pct}%\n"
        f"Осталось: {max(0, goal-income):,.0f}₸"
    ).replace(",", " ")
