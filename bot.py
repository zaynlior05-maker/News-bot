import requests
import random
import asyncio
from telegram import Bot

TOKEN = "8749522431:AAHycEzpn-ydZEOU20TDU1uRklXoSj0pMBs"
CHAT_ID = "-1003297925821"
NEWS_API = "52f409a5a258484a9d980fdc66bcec31"

bot = Bot(token=TOKEN)

posted_titles = set()
category_index = 0

categories = [
    "crypto",
    "uk",
    "world"
]

def get_news(category):
    if category == "crypto":
        url = f"https://newsapi.org/v2/everything?q=crypto&language=en&apiKey={NEWS_API}"
    elif category == "uk":
        url = f"https://newsapi.org/v2/top-headlines?country=gb&category=business&apiKey={NEWS_API}"
    else:
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={NEWS_API}"

    res = requests.get(url).json()

    if res["status"] != "ok":
        return None

    articles = res["articles"]

    random.shuffle(articles)

    for article in articles:
        if article["title"] not in posted_titles and article["urlToImage"]:
            posted_titles.add(article["title"])
            return article

    return None


def format_message(article, category):
    tag = {
        "crypto": "₿ CRYPTO ALERT",
        "uk": "🇬🇧 UK ECONOMY",
        "world": "🌍 GLOBAL NEWS"
    }

    title = article["title"]
    desc = article["description"] or ""

    return f"""⚡ HEISEN NEWS

{tag[category]}

📰 *{title}*

{desc}

_The world moves in silence… we report it._"""


async def send_news():
    global category_index

    category = categories[category_index]
    category_index = (category_index + 1) % len(categories)

    article = get_news(category)

    if not article:
        return

    message = format_message(article, category)

    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=article["urlToImage"],
            caption=message,
            parse_mode="Markdown"
        )
    except:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )


async def main():
    while True:
        await send_news()
        await asyncio.sleep(1800)  # 30 mins


if __name__ == "__main__":
    asyncio.run(main())
