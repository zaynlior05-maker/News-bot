import requests
import asyncio
import feedparser
import random
from datetime import datetime
from telegram import Bot
from telethon import TelegramClient, events

# ─────────────────────────────────────────────
# CONFIG — only 5 things to fill in
# ─────────────────────────────────────────────

TOKEN          = "8749522431:AAHycEzpn-ydZEOU20TDU1uRklXoSj0pMBs"      # from @BotFather
CHAT_ID        = "-1003297925821"       # your channel e.g. -1002xxxxxxx
API_ID         = 32999267                    # from my.telegram.org/apps
API_HASH       = "b5e284bcd42eeca07957dc118b59382a"      # from my.telegram.org/apps
YOUR_HANDLE = "@HeisenUpdates | @HeisenCE0"

SOURCE_CHANNEL = "DWCusers"

# ─────────────────────────────────────────────
# SCHEDULE — posts at these hours daily
# ─────────────────────────────────────────────

POST_HOURS = [8, 11, 14, 17, 20, 23, 2, 5]

# ─────────────────────────────────────────────
# KEYWORDS
# ─────────────────────────────────────────────

KEEP_KEYWORDS = [
    "exploit", "exploited", "hack", "hacked", "hacker",
    "drained", "stolen", "theft", "steal", "heist",
    "rug pull", "rugpull", "rug", "scam", "fraud",
    "zachxbt", "zach xbt", "investigation",
    "arrested", "indicted", "charged",
    "sec ", "lawsuit", "legal action",
    "vulnerability", "bug", "flash loan",
    "coinbase", "binance", "kraken", "bybit",
    "breach", "attack", "phishing",
    "money laundering", "sanction", "rekt",
    "unauthorized access", "social engineering",
]

SKIP_KEYWORDS = [
    "price prediction", "buy now", "best crypto to buy",
    "top 10", "music", "nft drop", "mint", "presale",
    "new token", "meme coin launch", "sponsored",
    "advertisement", "partner", "ico launch",
]

def is_relevant(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    if any(kw in text for kw in SKIP_KEYWORDS):
        return False
    return any(kw in text for kw in KEEP_KEYWORDS)

# ─────────────────────────────────────────────
# NEWS SOURCES (all free, no API key needed)
# ─────────────────────────────────────────────

posted_ids = set()

def fetch_rekt() -> dict | None:
    """Rekt.news — DeFi exploits only."""
    try:
        feed = feedparser.parse("https://rekt.news/feed/")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            uid = e.get("id", e.get("link", ""))
            if uid in posted_ids:
                continue
            if is_relevant(e.get("title", ""), e.get("summary", "")):
                posted_ids.add(uid)
                return {"title": e["title"], "link": e.get("link", ""), "source": "Rekt.news"}
    except Exception as ex:
        print(f"[Rekt error] {ex}")
    return None

def fetch_cointelegraph() -> dict | None:
    """CoinTelegraph RSS."""
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            uid = e.get("id", e.get("link", ""))
            if uid in posted_ids:
                continue
            if is_relevant(e.get("title", ""), e.get("summary", "")):
                posted_ids.add(uid)
                return {"title": e["title"], "link": e.get("link", ""), "source": "CoinTelegraph"}
    except Exception as ex:
        print(f"[CoinTelegraph error] {ex}")
    return None

def fetch_coindesk() -> dict | None:
    """CoinDesk RSS."""
    try:
        feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            uid = e.get("id", e.get("link", ""))
            if uid in posted_ids:
                continue
            if is_relevant(e.get("title", ""), e.get("summary", "")):
                posted_ids.add(uid)
                return {"title": e["title"], "link": e.get("link", ""), "source": "CoinDesk"}
    except Exception as ex:
        print(f"[CoinDesk error] {ex}")
    return None

def fetch_theblock() -> dict | None:
    """The Block RSS — covers hacks, SEC, arrests."""
    try:
        feed = feedparser.parse("https://www.theblock.co/rss/all")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            uid = e.get("id", e.get("link", ""))
            if uid in posted_ids:
                continue
            if is_relevant(e.get("title", ""), e.get("summary", "")):
                posted_ids.add(uid)
                return {"title": e["title"], "link": e.get("link", ""), "source": "The Block"}
    except Exception as ex:
        print(f"[TheBlock error] {ex}")
    return None

def get_next_article() -> dict | None:
    sources = [fetch_rekt, fetch_cointelegraph, fetch_coindesk, fetch_theblock]
    random.shuffle(sources)
    for source in sources:
        article = source()
        if article:
            return article
    return None

# ─────────────────────────────────────────────
# FORMAT
# ─────────────────────────────────────────────

def format_message(article: dict) -> str:
    time_now = datetime.now().strftime("%H:%M")
    return (
        f"⚡ HEISEN NEWS\n\n"
        f"🚨 *{article['title']}*\n\n"
        f"🔗 [Read full story]({article['link']})\n\n"
        f"📡 {article['source']} | 🕒 {time_now}\n\n"
        f"_{YOUR_HANDLE}_"
    )

# ─────────────────────────────────────────────
# SCHEDULED LOOP
# ─────────────────────────────────────────────

bot = Bot(token=TOKEN)

async def post_article():
    article = get_next_article()
    if not article:
        print("[Scheduled] Nothing relevant found.")
        return
    msg = format_message(article)
    print(f"[POST] {article['title'][:70]}")
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=msg,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"[Post error] {e}")

async def schedule_loop():
    posted_this_hour = set()
    while True:
        now = datetime.now()
        hr  = now.hour
        if hr in POST_HOURS and hr not in posted_this_hour:
            print(f"[{now.strftime('%H:%M')}] Posting...")
            await post_article()
            posted_this_hour.add(hr)
        if hr == 0 and len(posted_this_hour) > 1:
            posted_this_hour.clear()
        await asyncio.sleep(60)

# ─────────────────────────────────────────────
# DWC MONITOR
# ─────────────────────────────────────────────

reader = TelegramClient("heisen_reader", API_ID, API_HASH)

NEWS_TRIGGERS = [
    "just in", "breaking", "update:", "⚠️", "🚨",
    "zachxbt", "exploit", "hacked", "hack", "drained",
    "stolen", "rug pull", "scam alert", "investigation",
    "fraud", "arrested", "sec ", "lawsuit", "indicted",
    "coinbase", "binance", "kraken", "vulnerability",
    "flash loan", "scam", "phishing", "breach", "unauthorized",
]

AD_FILTERS = [
    "giveaway", "paid ad", "(paid ad)", "sponsored",
    "affiliate link", "rakeback", "rainbet", "casino",
    "sportsbook", "non-kyc", "raffle", "prize pool",
    "weekly race", "daily race", "promo code", "use code",
    "use our", "referral", "winners:", "congrats @",
    "claim your prize", "entries:", "airdrop", "free crypto",
]

def should_repost(text: str) -> bool:
    if not text or len(text.strip()) < 40:
        return False
    lower = text.lower()
    if any(kw in lower for kw in AD_FILTERS):
        return False
    return any(kw in lower for kw in NEWS_TRIGGERS)

def clean_text(text: str) -> str:
    for tag in ["@scammed / @DWCusers", "@scammed/@DWCusers", "@DWCusers", "@scammed"]:
        text = text.replace(tag, "")
    return f"{text.strip()}\n\n{YOUR_HANDLE}"

@reader.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def dwc_handler(event):
    msg  = event.message
    text = msg.text or ""
    if not should_repost(text):
        print(f"[DWC SKIP] {text[:50]!r}")
        return
    cleaned = clean_text(text)
    print(f"[DWC POST] {cleaned[:60]!r}")
    try:
        if msg.photo:
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=await msg.download_media(bytes),
                caption=cleaned,
                parse_mode="Markdown"
            )
        else:
            await bot.send_message(chat_id=CHAT_ID, text=cleaned, parse_mode="Markdown")
    except Exception as e:
        print(f"[DWC error] {e}")
        try:
            await bot.send_message(chat_id=CHAT_ID, text=cleaned)
        except:
            pass

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

async def main():
    await reader.start()
    print("✅ Heisen News Bot is live")
    print(f"📅 Posts at: {POST_HOURS}")
    print(f"👁️  Watching: {SOURCE_CHANNEL}")
    await asyncio.gather(
        schedule_loop(),
        reader.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
