import os
import asyncio
import feedparser
import random
import hashlib
from datetime import datetime
from telegram import Bot
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TOKEN          = os.environ["TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
API_ID         = int(os.environ["API_ID"])
API_HASH       = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
YOUR_HANDLE    = os.environ.get("YOUR_HANDLE", "@HeisenC")
SOURCE_CHANNEL = "DWCusers"
POST_HOURS     = [8, 11, 14, 17, 20, 23, 2, 5]

# ─────────────────────────────────────────────
# DUPLICATE PREVENTION
# ─────────────────────────────────────────────

posted_titles = []   # stores last 100 cleaned titles
post_lock = asyncio.Lock()

def clean_title(title: str) -> set:
    """Turn title into a set of important words for comparison."""
    skip_words = {
        "a", "an", "the", "is", "in", "on", "at", "to", "for",
        "of", "and", "or", "with", "from", "by", "over", "after",
        "using", "via", "new", "says", "amid", "its", "as", "how",
        "that", "this", "was", "are", "been", "has", "have", "into",
        "not", "but", "be", "it", "he", "she", "we", "they",
    }
    words = title.lower().replace("'", "").replace(",", "").replace(".", "")
    return set(w for w in words.split() if w not in skip_words and len(w) > 2)

def is_duplicate(title: str) -> bool:
    """Returns True if this title is too similar to a recently posted one."""
    new_words = clean_title(title)
    if not new_words:
        return False
    for old_title in posted_titles:
        old_words = clean_title(old_title)
        if not old_words:
            continue
        # Overlap score: shared words / smaller set
        shared = len(new_words & old_words)
        smaller = min(len(new_words), len(old_words))
        if smaller > 0 and shared / smaller >= 0.6:
            print(f"[DUPLICATE] '{title[:50]}' too similar to '{old_title[:50]}'")
            return True
    return False

def mark_posted(title: str):
    posted_titles.append(title)
    if len(posted_titles) > 100:
        posted_titles.pop(0)

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
# NEWS SOURCES
# ─────────────────────────────────────────────

def fetch_rekt() -> dict | None:
    try:
        feed = feedparser.parse("https://rekt.news/feed/")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            title = e.get("title", "")
            if is_duplicate(title): continue
            if is_relevant(title, e.get("summary", "")):
                return {"title": title, "link": e.get("link", ""), "source": "Rekt.news"}
    except Exception as ex:
        print(f"[Rekt error] {ex}")
    return None

def fetch_cointelegraph() -> dict | None:
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            title = e.get("title", "")
            if is_duplicate(title): continue
            if is_relevant(title, e.get("summary", "")):
                return {"title": title, "link": e.get("link", ""), "source": "CoinTelegraph"}
    except Exception as ex:
        print(f"[CoinTelegraph error] {ex}")
    return None

def fetch_coindesk() -> dict | None:
    try:
        feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            title = e.get("title", "")
            if is_duplicate(title): continue
            if is_relevant(title, e.get("summary", "")):
                return {"title": title, "link": e.get("link", ""), "source": "CoinDesk"}
    except Exception as ex:
        print(f"[CoinDesk error] {ex}")
    return None

def fetch_theblock() -> dict | None:
    try:
        feed = feedparser.parse("https://www.theblock.co/rss/all")
        entries = feed.entries[:]
        random.shuffle(entries)
        for e in entries:
            title = e.get("title", "")
            if is_duplicate(title): continue
            if is_relevant(title, e.get("summary", "")):
                return {"title": title, "link": e.get("link", ""), "source": "The Block"}
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
# POST
# ─────────────────────────────────────────────

bot = Bot(token=TOKEN)

async def post_article(label: str = ""):
    async with post_lock:
        article = get_next_article()
        if not article:
            print(f"[{label}] No new articles found.")
            return
        msg = format_message(article)
        print(f"[{label}] Posting: {article['title'][:70]}")
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            mark_posted(article["title"])
        except Exception as e:
            print(f"[Post error] {e}")

# ─────────────────────────────────────────────
# SCHEDULE
# ─────────────────────────────────────────────

async def schedule_loop():
    posted_this_hour = set()
    now = datetime.now()
    if now.hour not in POST_HOURS:
        print("[Startup] Posting first article...")
        await post_article("Startup")
    else:
        posted_this_hour.add(now.hour)
        print("[Startup] Skipping — scheduled hour will handle it")

    while True:
        now = datetime.now()
        hr  = now.hour
        if hr in POST_HOURS and hr not in posted_this_hour:
            await post_article(f"Scheduled {now.strftime('%H:%M')}")
            posted_this_hour.add(hr)
        if hr == 0 and len(posted_this_hour) > 1:
            posted_this_hour.clear()
        await asyncio.sleep(60)

# ─────────────────────────────────────────────
# DWC MONITOR
# ─────────────────────────────────────────────

reader = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

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
    if is_duplicate(text[:100]):
        print(f"[DWC DUPLICATE] Skipping")
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
        mark_posted(text[:100])
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
