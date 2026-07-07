# BuryadVoiceBot

> Телеграм-бот для сбора корпуса бурятского языка для [Mozilla Common Voice](https://commonvoice.mozilla.org/).

Помогает силами сообщества собирать данные: переводить предложения, предлагать новые фразы и озвучивать их голосом. Простой пайплайн сбора данных, который легко расширить до веб-админки или API.

## Возможности

- **Переводы** — перевод предложений, выгруженных из Common Voice
- **Предложения** — пользователи предлагают новые фразы на бурятском (с модерацией)
- **Озвучка** — запись голоса для одобренных предложений
- **Согласие с политикой** — обязательное принятие перед использованием (middleware)
- **Хранение в MongoDB** — отдельные коллекции под каждую сущность

## Стек

- Python 3.12
- [aiogram 3.x](https://docs.aiogram.dev/) — асинхронный фреймворк для Telegram Bot API
- MongoDB + [Motor](https://motor.readthedocs.io/) (async-драйвер)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — конфигурация
- uvloop, systemd (для продакшена)

## Команды бота

| Команда | Описание |
| --- | --- |
| `/start` | Приветствие и согласие с политикой |
| `/suggest` | Предложить новое предложение (на модерацию) |
| `/voice` | Озвучить одобренные предложения |
| `/policy` | Прочитать условия использования данных |

## Структура проекта

```
BuryadVoiceBot/
├── bot.py                  # точка входа
├── config.py               # настройки (pydantic-settings)
├── requirements.txt
├── .env                    # секреты
│
├── handlers/               # обработчики команд
│   ├── start.py
│   ├── suggest.py
│   ├── voice.py
│   ├── policy.py
│   └── unknown.py
├── middlewares/
│   └── agreement.py        # проверка принятия политики
├── services/               # бизнес-логика
├── database/
│   ├── mongo.py            # подключение и индексы
│   ├── models.py           # pydantic-модели
│   └── repositories/       # доступ к коллекциям
├── keyboards/              # клавиатуры
├── filters/                # кастомные фильтры
├── utils/
└── systemd/
    └── buryadvoice-bot.service
```

## Установка и запуск

### 1. Клонировать и создать окружение

```bash
git clone <repo-url>
cd BuryadVoiceBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Поднять MongoDB

Через Docker:

```bash
docker run -d --name buryad-mongo -p 27017:27017 mongo:7
```

### 3. Настроить `.env`

Создай файл `.env` на основе `.env.example`:

```env
BOT_TOKEN=<токен от @BotFather>
MONGO_URI=mongodb://localhost:27017
MONGO_DB=commonvoice
ADMIN_IDS=[1234567]
LOG_LEVEL=INFO
```

> ⚠️ `ADMIN_IDS` — это JSON-массив. Пиши `[]` или `[123,456]`, иначе pydantic не примет значение.

### 4. Запустить

```bash
python bot.py
```

При успехе в логах появится `Bot started`.

## Схема базы данных

<details>
<summary>Коллекции MongoDB</summary>

**users**

```json
{ "telegram_id": 123, "username": "erzhena", "agreed": true, "agreed_at": "...", "created_at": "..." }
```

**suggested_sentences** — предложенные фразы (`pending` / `approved` / `rejected`)

```json
{ "text": "...", "author": 123, "status": "pending", "moderator": null, "created_at": "..." }
```

**voice_records** — записи голоса

```json
{ "sentence_id": "...", "telegram_id": 123, "telegram_file_id": "...", "duration": 8, "status": "pending" }
```

Индексы: `users.telegram_id` (unique), `suggested_sentences.status`, `voice_records.sentence_id`, `voice_records.telegram_id`.

</details>

## Деплой (systemd)

```bash
sudo cp systemd/buryadvoice-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now buryadvoice-bot
sudo systemctl status buryadvoice-bot
```

## Дорожная карта

- [ ] Модерация переводов (совпадения от разных пользователей)
- [ ] Админские команды (`/admin_stats`, `/approve`, `/reject`)
- [ ] Статистика и лидерборд

## Лицензия

MIT