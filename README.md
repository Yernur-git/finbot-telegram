# Финансовый Telegram-бот

## Использование
Пиши боту:
- `доход монтаж 45000`
- `расход еда 3000 обед`
- `/месяц` — сводка
- `/анализ` — AI анализ

## Настройка

### 1. Telegram бот
1. Напиши @BotFather в Telegram
2. /newbot → введи название → получи TOKEN

### 2. Google Sheets API
1. Открой console.cloud.google.com
2. Создай проект → Включи Google Sheets API
3. IAM → Service Accounts → Create → скачай JSON
4. Открой свою таблицу finance_final.xlsx в Google Sheets
5. Поделись таблицей с email из JSON (вида xxx@xxx.iam.gserviceaccount.com)
6. Скопируй ID таблицы из URL (между /d/ и /edit)

### 3. AI ключ
- Claude: console.anthropic.com
- OpenAI: platform.openai.com
- Gemini: aistudio.google.com

### 4. Deploy на Railway
1. Залей папку в GitHub репо
2. Зайди на railway.app → New Project → Deploy from GitHub
3. Variables → добавь все переменные из .env.example
4. Deploy → бот работает 24/7
