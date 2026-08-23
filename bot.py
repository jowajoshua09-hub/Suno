import os, re, json, aiohttp, urllib.parse, threading, asyncio, random
from dotenv import load_dotenv
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatAction
from personality import get_suno_prompt

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1004383326043
GROUP_USERNAME = "@startech372"
GROUP_LINK = "https://t.me/startech372"
SUNO_API = "https://api.omegatech.app/api/ai/sonu-pro"
AI_ENDPOINTS = [
    "https://api.hostify.indevs.in/api/ai/gpt-4o",
    "https://api.hostify.indevs.in/api/ai/grok",
    "https://api.hostify.indevs.in/api/ai/gemini-v2",
]

TRENDING_IDEAS = [
    "Sad love in Harare at night", "Amapiano love anthem", "Breakup healing",
    "Crush first love", "Midnight thoughts", "Dancehall queen",
    "Gospel Amapiano", "Hustle motivation", "Heartbreak rain",
    "Shona queen love", "Toxic ex goodbye", "Party all night",
    "Long distance love", "Crying for you", "Afro soul healing"
]

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Suno Bot Live", 200
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

memory = json.load(open("memory.json")) if os.path.exists("memory.json") else {}
def save(): json.dump(memory, open("memory.json","w"))
def is_verified(uid): return memory.get(str(uid),{}).get("verified", False)
def set_verified(uid): memory.setdefault(str(uid),{})["verified"]=True; save()

async def is_joined(uid, ctx):
    for chat in [GROUP_ID, GROUP_USERNAME]:
        try:
            m = await ctx.bot.get_chat_member(chat, uid)
            if m.status in ["member","administrator","creator"]: return True
        except: continue
    return False

def verify_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=GROUP_LINK)],
                                 [InlineKeyboardButton("✅ Verify", callback_data="verify")]])

def mode_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Trending Ideas", callback_data="trending")],
        [InlineKeyboardButton("🤖 AI Generate Full Song", callback_data="mode_ai")],
        [InlineKeyboardButton("✍️ Own Lyrics", callback_data="mode_custom")],
        [InlineKeyboardButton("🎼 Full Custom", callback_data="mode_full_custom")],
        [InlineKeyboardButton("🎲 Surprise Me", callback_data="surprise")]
    ])

def ideas_kb():
    buttons = [[InlineKeyboardButton(t, callback_data=f"idea_{i}")] for i,t in enumerate(TRENDING_IDEAS)]
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_modes")])
    return InlineKeyboardMarkup(buttons)

def continue_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Generate Audio", callback_data="continue")],
        [InlineKeyboardButton("✏️ Title", callback_data="edit_title"), InlineKeyboardButton("🎨 Style", callback_data="edit_style")],
        [InlineKeyboardButton("📝 Lyrics", callback_data="edit_lyrics"), InlineKeyboardButton("🔄 Regen", callback_data="regen")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

async def generate_fields(idea: str):
    prompt = get_suno_prompt(idea)
    fallback_title = f"{idea[:20].title()} Anthem"
    fallback_style = "Afro Amapiano, log drums, soulful vocal, 108 BPM"
    fallback_lyrics = f"""[Intro]
Yeah yeah ooh

[Verse 1]
{idea} you dey my mind every night
City lights Harare you my light
Searching for a love wey real no lie
When you touch me I feel alive

[Pre-Chorus]
No more lonely nights no pain
With you my love I feel no shame

[Chorus]
{idea} hold me close don't let go
You the rhythm wey make my heart beat slow
When world turn cold your love keep me warm
Dancing through night till morning comes

[Verse 2]
Whispers in dark secrets we keep
Your heartbeat on my chest help me sleep
Every other girl don fade away
Na you I want everyday

[Chorus]
{idea} hold me close don't let go
You the rhythm wey make my heart beat slow

[Bridge]
Ooh baby stay make you no go
Let me love you till sunrise glow

[Chorus - Big]
{idea} hold me close don't let go
You my forever you my home

[Outro]
Yeah Harare nights {idea} forever"""

    for api_url in AI_ENDPOINTS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(api_url, json={"q": prompt}, timeout=60) as r:
                    data = await r.json()
                    txt = ""
                    res = data.get("result")
                    if isinstance(res, dict): txt = res.get("answer","") or ""
                    elif isinstance(res, str): txt = res
                    else: txt = data.get("response") or str(data)

                    if "TITLE:" in txt and "STYLE:" in txt and "LYRICS:" in txt and len(txt) > 150:
                        title = re.search(r'TITLE:\s*(.+)', txt, re.I).group(1).strip()[:80]
                        style = re.search(r'STYLE:\s*(.+)', txt, re.I).group(1).strip()[:200]
                        lyrics = re.search(r'LYRICS:\s*(.+)', txt, re.I|re.S).group(1).strip()[:3500]
                        if len(lyrics) > 100:
                            return title, style, lyrics
        except Exception as e:
            print(f"AI {api_url} error {e}")
            continue
    return fallback_title, fallback_style, fallback_lyrics

async def call_suno(title, style, lyrics):
    url = f"{SUNO_API}?action=generate&prompt={urllib.parse.quote(lyrics)}&title={urllib.parse.quote(title)}&isInstrumental=false&musicStyle={urllib.parse.quote(style)}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=180) as r:
                data = await r.json()
                if data.get("data",{}).get("tracks"): return data["data"]["tracks"][0]
                if data.get("tracks"): return data["tracks"][0]
    except: pass
    return None

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_verified(update.effective_user.id) and await is_joined(update.effective_user.id, ctx):
        await update.message.reply_text("🎵 *Suno Ready* - Send idea or pick mode", parse_mode="Markdown", reply_markup=mode_kb())
        return
    await update.message.reply_text("Join first 👇", reply_markup=verify_kb())

async def on_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if await is_joined(q.from_user.id, ctx):
        set_verified(q.from_user.id)
        await q.edit_message_text("✅ Verified! Choose:", reply_markup=mode_kb())
    else:
        await q.answer("Not joined", show_alert=True)

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_verified(uid):
        if not await is_joined(uid, ctx):
            await update.message.reply_text("Join first 👇", reply_markup=verify_kb()); return
        set_verified(uid)
    state = ctx.user_data.get('state')
    text = update.message.text.strip()

    if state == "await_full_title":
        ctx.user_data['title']=text[:80]; ctx.user_data['state']="await_full_style"
        await update.message.reply_text(f"Title: {text}\nNow Style:"); return
    elif state == "await_full_style":
        ctx.user_data['style']=text[:200]; ctx.user_data['state']="await_full_lyrics"
        await update.message.reply_text(f"Style: {text}\nNow Lyrics:"); return
    elif state == "await_full_lyrics":
        ctx.user_data['lyrics']=text[:3500]; ctx.user_data['state']=None
        await update.message.reply_text(f"Title: {ctx.user_data['title']}\nStyle: {ctx.user_data['style']}\nLyrics: {text[:1000]}", reply_markup=continue_kb()); return
    elif state == "await_own_lyrics":
        ctx.user_data['lyrics']=text[:3500]; ctx.user_data['state']="await_own_title"
        await update.message.reply_text("Lyrics saved! Now Title:"); return
    elif state == "await_own_title":
        ctx.user_data['title']=text[:80]; ctx.user_data['state']="await_own_style"
        await update.message.reply_text(f"Title: {text}\nNow Style:"); return
    elif state == "await_own_style":
        ctx.user_data['style']=text[:200]; ctx.user_data['state']=None
        await update.message.reply_text(f"Title: {ctx.user_data['title']}\nStyle: {text}\nLyrics: {ctx.user_data['lyrics'][:1000]}", reply_markup=continue_kb()); return
    elif state and state.startswith("edit_"):
        key=state.split("_")[1]; ctx.user_data[key]=text[:3500]; ctx.user_data['state']=None
        await update.message.reply_text(f"Updated!\nTitle: {ctx.user_data.get('title')}\nStyle: {ctx.user_data.get('style')}\nLyrics: {ctx.user_data.get('lyrics')[:1000]}", reply_markup=continue_kb()); return

    idea = re.sub(r'^(suno|song)\s*','', text, flags=re.I).strip()
    ctx.user_data['idea']=idea or text
    await update.message.reply_text(f"Idea: *{idea}*\nChoose:", parse_mode="Markdown", reply_markup=mode_kb())

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    data = q.data
    chat_id = q.message.chat_id

    if data == "trending":
        await q.edit_message_text("🔥 Pick idea:", reply_markup=ideas_kb())
    elif data.startswith("idea_"):
        idx=int(data.split("_")[1]); idea=TRENDING_IDEAS[idx]
        ctx.user_data['idea']=idea
        await q.edit_message_text(f"Creating *{idea}*...", parse_mode="Markdown")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb())
    elif data == "surprise":
        idea=random.choice(TRENDING_IDEAS); ctx.user_data['idea']=idea
        await q.edit_message_text(f"Surprise: {idea}...")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb())
    elif data == "back_modes":
        await q.edit_message_text("Choose:", reply_markup=mode_kb())
    elif data == "mode_ai":
        idea=ctx.user_data.get('idea','sad love')
        await q.edit_message_text(f"Creating {idea}...")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb())
    elif data == "mode_custom":
        ctx.user_data['state']="await_own_lyrics"
        await q.edit_message_text("Send Lyrics:")
    elif data == "mode_full_custom":
        ctx.user_data['state']="await_full_title"
        await q.edit_message_text("Send Title:")
    elif data == "continue":
        title=ctx.user_data.get('title'); style=ctx.user_data.get('style'); lyrics=ctx.user_data.get('lyrics')
        if not title: await q.edit_message_text("Expired"); return
        await q.edit_message_text(f"🎧 Generating {title}...")
        await ctx.bot.send_chat_action(chat_id, ChatAction.RECORD_VOICE)
        track = await call_suno(title, style, lyrics)
        if track and (track.get('musicFile') or track.get('audioUrl')):
            audio_url = track.get('musicFile') or track.get('audioUrl')
            # FIXED AUDIO - ONLY light.mp3 PLAYABLE
            await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VOICE)
            await ctx.bot.send_audio(
                chat_id=chat_id,
                audio=audio_url,
                title=title,
                filename=f"{title}.mp3"
            )
            await ctx.bot.send_message(chat_id, f"✅ Done: {title}", reply_markup=mode_kb())
        else:
            await ctx.bot.send_message(chat_id, "❌ Busy, try Continue again", reply_markup=continue_kb())
    elif data.startswith("edit_"):
        ctx.user_data['state']=data
        await q.edit_message_text(f"Send new {data}:")
    elif data == "regen":
        idea=ctx.user_data.get('idea','love')
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb())
    elif data == "cancel":
        ctx.user_data.clear()
        await q.edit_message_text("Cancelled", reply_markup=mode_kb())

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_verify, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(on_button, pattern="^(mode_|continue|edit_|regen|cancel|trending|idea_|surprise|back_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("✅ Bot Live - Audio Light.mp3 Fixed")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
