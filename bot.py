import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_client import get_ai_response
from sheets import append_transaction, get_monthly_summary

logging.basicConfig(level=logging.INFO)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я финансовый трекер.\n\n"
        "Просто пиши:\n"
        "• доход монтаж 45000\n"
        "• расход еда 3000\n"
        "• расход транспорт 1500 такси\n\n"
        "Команды:\n"
        "/месяц — сводка за текущий месяц\n"
        "/анализ — AI анализ твоих финансов\n"
        "/помощь — категории"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Категории доходов:\n"
        "стипендия, монтаж, фото, видео, фриланс, другое\n\n"
        "Категории расходов:\n"
        "еда, транспорт, жилье, связь, техника, учеба, развлечения, другое\n\n"
        "Примеры:\n"
        "• доход монтаж 45000\n"
        "• расход еда 2500 обед\n"
        "• доход стипендия 51000"
    )

async def month_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Загружаю данные...")
    summary = get_monthly_summary()
    await update.message.reply_text(summary)

async def analysis_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Анализирую...")
    summary = get_monthly_summary(raw=True)
    prompt = (
        f"Вот финансы студента-фрилансера за текущий месяц:\n\n{summary}\n\n"
        f"Цель: 200 000₸ в месяц. Дай краткий анализ и 2-3 конкретных совета."
    )
    response = get_ai_response(prompt)
    await update.message.reply_text(response)

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    
    # Parse: [тип] [категория] [сумма] [описание?]
    words = text.split()
    if len(words) < 3:
        await update.message.reply_text(
            "Не понял. Пример:\nдоход монтаж 45000\nрасход еда 3000"
        )
        return

    type_map = {
        "доход": "Доход", "income": "Доход",
        "расход": "Расход", "расходы": "Расход", "expense": "Расход"
    }
    cat_map = {
        "стипендия": "Стипендия", "монтаж": "Монтаж",
        "фото": "Фото-съемка", "видео": "Видео-съемка",
        "фриланс": "Фриланс",
        "еда": "Еда", "транспорт": "Транспорт", "жилье": "Жилье",
        "связь": "Связь/подписки", "техника": "Техника",
        "учеба": "Учеба", "развлечения": "Развлечения",
        "другое": "Другое", "другой": "Другой доход"
    }

    tx_type = type_map.get(words[0])
    if not tx_type:
        await update.message.reply_text("Начни с 'доход' или 'расход'")
        return

    cat = cat_map.get(words[1], words[1].capitalize())
    
    amount = None
    for w in words[2:]:
        try:
            amount = float(w.replace(",", "").replace("₸", ""))
            break
        except ValueError:
            continue
    
    if not amount:
        await update.message.reply_text("Не нашел сумму. Пример: доход монтаж 45000")
        return

    desc_words = [w for w in words[3:] if not w.replace(",","").replace("₸","").isdigit()]
    desc = " ".join(desc_words) if desc_words else ""

    today = datetime.now().strftime("%d.%m.%Y")
    
    try:
        append_transaction(today, tx_type, cat, desc, amount)
        sign = "+" if tx_type == "Доход" else "-"
        emoji = "💚" if tx_type == "Доход" else "🔴"
        await update.message.reply_text(
            f"{emoji} Записал!\n"
            f"{tx_type} | {cat}\n"
            f"{sign}{int(amount):,}₸".replace(",", " ")
            + (f"\n📝 {desc}" if desc else "")
        )
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Ошибка записи в таблицу. Проверь настройки.")

def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("месяц", month_cmd))
    app.add_handler(CommandHandler("анализ", analysis_cmd))
    app.add_handler(CommandHandler("помощь", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
