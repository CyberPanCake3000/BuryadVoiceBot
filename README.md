# BuryadVoiceBot

> Телеграм-бот для сбора корпуса бурятского языка для [Mozilla Common Voice](https://commonvoice.mozilla.org/).

Помогает силами сообщества собирать данные: переводить предложения, предлагать новые фразы и озвучивать их голосом. Простой пайплайн сбора данных, который легко расширить до веб-админки или API.

## Возможности

- **Переводы** — перевод предложений, выгруженных из Common Voice
- **Предложения** — пользователи предлагают новые фразы на бурятском (с модерацией)
- **Озвучка** — запись голоса для одобренных предложений
- **Согласие с политикой** — обязательное принятие перед использованием (middleware)
- **Хранение в MongoDB** — отдельные коллекции под каждую сущность
- **Роли** — обычный пользователь, ревьюер и администратор с разными меню и командами
- **Коллективная модерация** — ревьюеры голосуют за предложения; фраза одобряется, когда за неё больше половины ревьюеров
- **Жалобы и бан** — ревьюер может пожаловаться на фразу; после 3 жалоб её автор исключается из проекта и попадает в чёрный список
- **Памятки-онбординг** — при первом использовании `/suggest` и `/voice` бот показывает правила (один раз)
- **Рейтинг** — `/leaderboard` показывает топ-5 участников

## Стек

- Python 3.12
- [aiogram 3.x](https://docs.aiogram.dev/) — асинхронный фреймворк для Telegram Bot API
- MongoDB + [Motor](https://motor.readthedocs.io/) (async-драйвер)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — конфигурация
- uvloop, systemd (для продакшена)

## Роли
| Роль | Кто это | Доступные команды |
| --- | --- | --- |
| Пользователь | любой, кто согласился с политикой | `/suggest`, `/voice` |
| Ревьюер | добавлен админом через `/addreviewer` | `+ /startreview` |
| Администратор | указан в `ADMIN_IDS` в `.env` | `+ /addreviewer` |

Роль определяется автоматически: админ — по `ADMIN_IDS`, ревьюер — по наличию в коллекции `reviewers`. Меню и приветствие подстраиваются под роль.

## Команды бота

| Команда | Описание |
| --- | --- |
| `/start` | Приветствие и согласие с политикой |
| `/suggest` | Предложить новое предложение (на модерацию) |
| `/voice` | Озвучить одобренные предложения |
| `/policy` | Прочитать условия использования данных |
| `/startreview` | ревьюер | Получить 5 предложений на модерацию |
| `/addreviewer` | админ | Добавить ревьюера (отправить контакт) |
| `/addfortranslation` | админ | Добавить тексты в очередь на перевод |
| `/leaderboard` | все | Топ-5 участников по рейтингу (работает и в группах) |
| `/translate` | ревьюер | Перевести тексты из очереди на перевод |

> Все команды работают в личке с ботом. В групповых чатах доступен только `/leaderboard`.

## Как работает модерация
```
Пользователь: /suggest → фраза сохраняется со статусом pending, reviews: []
        ↓
Ревьюер: /startreview → получает 5 случайных фраз, которые ещё не смотрел
        ↓
жмёт [✅ Принять] / [❌ Отклонить] / [🚫 Пожаловаться]
        ↓
голос пишется в reviews[] самой фразы (повторно проголосовать нельзя)
        ↓
• approve набирает больше половины от всех ревьюеров → статус approved
• complain → автору начисляется жалоба; после 3 жалоб автор банится и блокируется навсегда
        ↓
фраза автоматически попадает в /voice на озвучку
```

## Как работает перевод
```
Админ: /addfortranslation → присылает тексты (каждый с новой строки)
        ↓
тексты попадают в need_translation со статусом pending
        ↓
Ревьюер: /translate → получает пачку непереведённых текстов и вводит перевод
        ↓
перевод сохраняется, статус → translated
```

## Как считается рейтинг (`/leaderboard`)
`рейтинг = предложения + озвучки − отклонённые предложения`. Топ-5 строится агрегацией по коллекциям `suggested_sentences` и `voice_records`, имя берётся из `users`.

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
│   ├── reviewers.py
│   ├── startreview.py
│   ├── addfortranslation.py
│   ├── translate.py
│   ├── leaderboard.py
│   └── unknown.py
├── middlewares/
│   └── agreement.py        # проверка принятия политики
├── services/               # бизнес-логика
│   └── roles.py 
├── database/
│   ├── mongo.py            # подключение и индексы
│   ├── models.py           # pydantic-модели
│   └── repositories/       # доступ к коллекциям
│       ├── users.py
│       ├── reviewers.py
│       ├── sentences.py
│       ├── translations.py
│       ├── voices.py
│       └── stats.py
├── keyboards/              # клавиатуры
│   ├── agreement.py
│   ├── menu.py
│   ├── review.py
│   └── suggest.py 
├── filters/                # кастомные фильтры
│   ├── admin.py
│   ├── reviewer.py 
│   └── agreed.py
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
{
  "telegram_id": 123,
  "username": "erzhena",
  "agreed": true,
  "agreed_at": "...",
  "seen_hints": ["suggest", "voice"],
  "complaints": 0,
  "banned": false,
  "banned_at": null,
  "created_at": "..."
}
```

**reviewers** — модераторы, добавленные админом
```json
{ "telegram_id": 000000, "username": "bulka", "full_name": "Булка", "added_by": 27276331, "created_at": "..." }
```
> `username` заполняется не при добавлении (в контакте Telegram его нет), а когда ревьюер сам напишет боту `/start`.


**suggested_sentences** — предложенные фразы (`pending` / `approved` / `rejected`)

```json
{
  "text": "...",
  "author": 123,
  "status": "pending",
  "reviews": [
    { "reviewer_id": 111, "decision": "approve", "created_at": "..." },
    { "reviewer_id": 222, "decision": "complain", "created_at": "..." }
  ],
  "approved_at": null,
  "created_at": "..."
}
```

> `decision` может быть `approve`, `reject` или `complain`.


**need_translation** — очередь текстов на перевод (`pending` / `translated`)
```json
{
  "text": "...",
  "translation": null,
  "translated_by": null,
  "status": "pending",
  "added_by": 27276331,
  "translated_at": null,
  "created_at": "..."
}
```

**voice_records** — записи голоса

```json
{ "sentence_id": "...", "telegram_id": 123, "telegram_file_id": "...", "duration": 8, "status": "pending" }
```

Индексы:
- `users.telegram_id` (unique)
- `reviewers.telegram_id` (unique)
- `suggested_sentences.status`
- `suggested_sentences.reviews.reviewer_id`
- `voice_records.sentence_id`
- `voice_records.telegram_id`
- `need_translation.status`

</details>

## Деплой (systemd)

```bash
sudo cp systemd/buryadvoice-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now buryadvoice-bot
sudo systemctl status buryadvoice-bot
```

## Лицензия

MIT