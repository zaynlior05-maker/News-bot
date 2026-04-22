import requests
import random
import asyncio
from datetime import datetime
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

# ✅ Get clean image (fix ugly images)
def get_image(article):
    url = article.get("urlToImage")

    if url and url.startswith("http"):
        return url

    # fallback image
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c"


# ✅ Get news
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
        if article["title"] not in posted_titles:
            posted_titles.add(article["title"])
            return article

    return None


# ✅ Clean + professional message (NO crypto alert text)
def format_message(article, category):
    tag = {
        "crypto": "CRYPTO UPDATE",
        "uk": "🇬🇧 UK ECONOMY",
        "world": "🌍 GLOBAL NEWS"
    }

    title = article["title"]
    desc = article["description"] or ""

    # shorten description
    if len(desc) > 180:
        desc = desc[:180] + "..."

    time_now = datetime.now().strftime("%H:%M")

    return f"""⚡ HEISEN NEWS

{tag[category]}

📰 *{title}*

{desc}

🕒 {time_now} | 🌍 Global Desk

_The world moves in silence… we report it._"""


# ✅ Send news
async def send_news():
    global category_index

    category = categories[category_index]
    category_index = (category_index + 1) % len(categories)

    article = get_news(category)

    if not article:
        return

    message = format_message(article, category)
    image = get_image(article)

    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=image,
            caption=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(e)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )


# ✅ Loop every 30 minutes
async def main():
    while True:
        await send_news()
        await asyncio.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main())
