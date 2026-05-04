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
        "/month — сводка за текущий месяц\n"
        "/analysis — AI анализ твоих финансов\n"
        "/help — категории"
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
    try:
        summary = get_monthly_summary()
        await update.message.reply_text(summary)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"Ошибка: {e}")

async def analysis_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Анализирую...")
    try:
        summary = get_monthly_summary(raw=True)
        prompt = (
            f"Вот финансы студента-фрилансера (съемка/монтаж) за текущий месяц:\n\n{summary}\n\n"
            f"Цель: 200 000₸ в месяц. Дай краткий анализ (3-4 предложения) и 2-3 конкретных совета."
        )
        response = get_ai_response(prompt)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"Ошибка: {e}")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
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
        "стипендия": "Стипендия",
        "монтаж": "Монтаж",
        "фото": "Фото-съемка", "фотосъемка": "Фото-съемка",
        "видео": "Видео-съемка", "видеосъемка": "Видео-съемка",
        "фриланс": "Фриланс",
        "еда": "Еда", "продукты": "Еда",
        "транспорт": "Транспорт", "такси": "Транспорт",
        "жилье": "Жилье", "аренда": "Жилье",
        "связь": "Связь/подписки", "подписки": "Связь/подписки",
        "техника": "Техника",
        "учеба": "Учеба",
        "развлечения": "Развлечения",
        "другое": "Другое", "другой": "Другой доход"
    }

    tx_type = type_map.get(words[0])
    if not tx_type:
        await update.message.reply_text("Начни с 'доход' или 'расход'")
        return

    cat = cat_map.get(words[1], words[1].capitalize())

    amount = None
    amount_idx = None
    for i, w in enumerate(words[2:], 2):
        try:
            amount = float(w.replace(",", "").replace("₸", "").replace(" ", ""))
            amount_idx = i
            break
        except ValueError:
            continue

    if not amount:
        await update.message.reply_text("Не нашел сумму. Пример: доход монтаж 45000")
        return

    desc_words = [w for i, w in enumerate(words) if i > 1 and i != amount_idx
                  and not w.replace(",","").replace("₸","").replace(".","").isdigit()]
    desc = " ".join(desc_words[1:]) if len(desc_words) > 1 else ""

    today = datetime.now().strftime("%d.%m.%Y")

    try:
        append_transaction(today, tx_type, cat, desc, int(amount))
        sign = "+" if tx_type == "Доход" else "-"
        emoji = "💚" if tx_type == "Доход" else "🔴"
        msg = f"{emoji} Записал!\n{tx_type} | {cat}\n{sign}{int(amount):,}₸".replace(",", " ")
        if desc:
            msg += f"\n📝 {desc}"
        await update.message.reply_text(msg)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"Ошибка записи: {e}")

def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("month", month_cmd))
    app.add_handler(CommandHandler("analysis", analysis_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
