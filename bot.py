import lyricsgenius
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor


TG_TOKEN = "8575843507:AAHRikgK3BH_ZiAczaLPiG5dEgXS1LjwGsk"
GENIUS_TOKEN = "Lq1vx0QZvfJMoshvoLcQdhOFy3lDOAUoRJuOgzJG1Nha9k5x-rn_8xXoJwkP_2B1"
BOT_USERNAME = "songtextgeniusbot"

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)

# Инициализация Genius API клиента
genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    timeout=15,
    retries=3,
    remove_section_headers=True  # убирает [Chorus], [Verse] и т.п.
)


def chunk_text(text, limit=4000):
    """Безопасно разбивает текст на части фиксированной длины."""
    return [text[i:i+limit] for i in range(0, len(text), limit)]


@dp.message_handler(commands=['start', 'help'])
async def start_cmd(message: types.Message):
    await message.reply(
        "Привет! Напиши:\n\n"
        "Исполнитель - Название трека\n\n"
        "Пример: Adele - Hello"
    )


async def search_lyrics(query: str, message: types.Message):
    query = query.strip()

    if not query:
        await message.reply("Пожалуйста, укажи исполнителя и название трека после команды.\nПример:\n/findlyrics Adele - Hello")
        return

    if "-" not in query:
        await message.reply("Используй формат: Исполнитель - Название трека")
        return

    artist, title = [s.strip() for s in query.split("-", 1)]

    print(f"[lyrics search] Пытаюсь найти: title='{title}' artist='{artist}'")
    await message.reply("Ищу текст песни...")

    song = None
    try:
        # Сначала ищем по title → artist
        song = genius.search_song(title, artist)
        print(f"[lyrics search] Поиск title→artist: {'найдено' if song else 'не найдено'}")
        if not song:
            # Пробуем artist → title
            song = genius.search_song(artist, title)
            print(f"[lyrics search] Поиск artist→title: {'найдено' if song else 'не найдено'}")
    except Exception as e:
        await message.reply(f"Ошибка при запросе к Genius API:\n{e}")
        return

    if not song or not getattr(song, 'lyrics', None):
        await message.reply("Не нашёл текст песни на Genius 😕")
        return

    lyrics = song.lyrics.strip()
    if not lyrics:
        await message.reply("Текст песни не найден на Genius 😕")
        return

    print(f"[lyrics] Длина текста: {len(lyrics)} символов")

    # отправляем частями
    for chunk in chunk_text(lyrics):
        await message.reply(chunk)

    await message.reply(f"Найдено: {song.title} — {song.artist}\nИсточник: Genius")


@dp.message_handler(commands=['findlyrics'])
async def findlyrics_cmd(message: types.Message):
    await message.reply(
        "Пожалуйста, отправь исполнителя и название трека в формате:\nИсполнитель - Название трека",
        reply_markup=types.ForceReply(selective=True)
    )


@dp.message_handler(lambda message: message.reply_to_message is not None)
async def reply_handler(message: types.Message):
    if message.reply_to_message.from_user.id == bot.id:
        query = message.text
        await search_lyrics(query, message)


@dp.message_handler()
async def mention_handler(message: types.Message):
    text = message.text or ""
    mention = f"@{BOT_USERNAME}"
    if mention in text:
        # Удаляем упоминание и пробелы
        query = text.replace(mention, "", 1).strip()
        await search_lyrics(query, message)


if __name__ == "__main__":
    print("Бот запущен!")
    executor.start_polling(dp, skip_updates=True)