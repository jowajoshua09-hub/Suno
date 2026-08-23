import os, re, json, aiohttp, urllib.parse, threading, random, io
from dotenv import load_dotenv
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
def home(): return "Suno STAR Live", 200
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

def main_menu_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔥 Trending Ideas")],
        [KeyboardButton("🤖 AI Generate Full Song")],
        [KeyboardButton("✍️ Own Lyrics")],
        [KeyboardButton("🎼 Full Custom")],
        [KeyboardButton("🎲 Surprise Me")]
    ], resize_keyboard=True)

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
    def make_long_lyrics(topic):
        return f"""[Intro]
Yeah, Star! Al MJ

[Verse 1]
{topic} you dey for my mind every night I no fit sleep
Harare city lights but na you be the light wey deep
I been dey search for love wey real no be play
Since you come my heart dey beat fast everyday
Girl you sweet like honey for my mouth
You take me from the north to the south

[Pre-Chorus]
No more lonely nights when you dey with me
All my sorrow gone you set me free
Na you I choose among all the girls I see
Baby no go leave me abeg stay with me

[Chorus]
{topic} hold me close no let go
You be the rhythm wey make my heart beat slow
When world cold your love e keep me warm
We go dance till morning comes
{topic} na you be my only home

[Verse 2]
Whispers for the dark na we two dey hear
Your heartbeat for my chest e clear
Every other girl don fade comot for my eye
Na only you I want till I die
You my Shona queen you my African star
You heal my wound you heal my scar
For you I go hustle everyday
For you I go work make we find our way

[Bridge]
Ooh baby stay make you no go far
You be my moon you be my star
If you comot my life e go spoil

[Chorus - Final]
{topic} hold me close no ever let go
You be the one wey make my life dey glow
When e dark you be my light for night
{topic} forever

[Outro]
Yeah yeah ooh StarDev"""
    long_title = f"{idea.title()} Star Anthem"
    long_style = "Afro Amapiano x Zim Dancehall, Al MJ vibe, soulful vocal, log drums, 108 BPM"
    for api_url in AI_ENDPOINTS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(api_url, json={"q": prompt}, timeout=90) as r:
                    data = await r.json()
                    txt = ""
                    res = data.get("result")
                    if isinstance(res, dict): txt = res.get("answer","") or ""
                    elif isinstance(res, str): txt = res
                    else: txt = data.get("response") or str(data)
                    if len(txt) > 300:
                        title_match = re.search(r'TITLE:\s*(.+)', txt, re.I)
                        style_match = re.search(r'STYLE:\s*(.+)', txt, re.I)
                        lyrics_match = re.search(r'LYRICS:\s*(.+)', txt, re.I|re.S)
                        title = title_match.group(1).strip()[:80] if title_match else long_title
                        style = style_match.group(1).strip()[:200] if style_match else long_style
                        lyrics = lyrics_match.group(1).strip()[:4000] if lyrics_match else txt[:4000]
                        if len(lyrics) >= 300: return title, style, lyrics
        except: continue
    return long_title, long_style, make_long_lyrics(idea)

async def call_suno(title, style, lyrics):
    url = f"{SUNO_API}?action=generate&prompt={urllib.parse.quote(lyrics)}&title={urllib.parse.quote(title)}&isInstrumental=false&musicStyle={urllib.parse.quote(style)}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=180) as r:
                data = await r.json()
                tracks = None
                if data.get("data",{}).get("tracks"): tracks = data["data"]["tracks"]
                elif data.get("tracks"): tracks = data["tracks"]
                elif data.get("data"): tracks = [data["data"]]
                if tracks:
                    t = tracks[0]
                    audio = t.get('musicFile') or t.get('audioUrl') or t.get('url') or t.get('audio_url')
                    if audio: t['audioUrl'] = audio; return t
    except Exception as e: print(f"SUNO ERROR {e}")
    return None

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_verified(update.effective_user.id) and await is_joined(update.effective_user.id, ctx):
        await update.message.reply_text("🎵 *Suno STAR Ready* ⭐\nPick from bottom menu 👇", parse_mode="Markdown", reply_markup=main_menu_kb())
        return
    await update.message.reply_text("Join first 👇", reply_markup=verify_kb())

async def on_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if await is_joined(q.from_user.id, ctx):
        set_verified(q.from_user.id)
        await q.edit_message_text("✅ Verified!")
        await ctx.bot.send_message(q.message.chat_id, "🎵 Welcome! Use menu 👇", reply_markup=main_menu_kb())
    else: await q.answer("Not joined", show_alert=True)

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if text == "🔥 Trending Ideas":
        await update.message.reply_text("🔥 Pick idea:", reply_markup=ideas_kb()); return
    elif text == "🤖 AI Generate Full Song":
        idea=ctx.user_data.get('idea','sad love in Harare')
        await update.message.reply_text(f"🎧 Creating *{idea}*...", parse_mode="Markdown")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics; ctx.user_data['idea']=idea
        await update.message.reply_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb()); return
    elif text == "✍️ Own Lyrics":
        ctx.user_data['state']="await_own_lyrics"
        await update.message.reply_text("Send your Lyrics:"); return
    elif text == "🎼 Full Custom":
        ctx.user_data['state']="await_full_title"
        await update.message.reply_text("Send Title:"); return
    elif text == "🎲 Surprise Me":
        idea=random.choice(TRENDING_IDEAS); ctx.user_data['idea']=idea
        await update.message.reply_text(f"🎲 Surprise: *{idea}*...", parse_mode="Markdown")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await update.message.reply_text(f"Title: {title}\nStyle: {style}\nLyrics:\n{lyrics[:3500]}", reply_markup=continue_kb()); return

    if not is_verified(uid):
        if not await is_joined(uid, ctx):
            await update.message.reply_text("Join first 👇", reply_markup=verify_kb()); return
        set_verified(uid)

    state = ctx.user_data.get('state')
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
        await update.message.reply_text(f"Updated!\nTitle: {ctx.user_data.get('title')}", reply_markup=continue_kb()); return

    idea = re.sub(r'^(suno|song)\s*','', text, flags=re.I).strip()
    if len(idea) < 2: return
    ctx.user_data['idea']=idea
    await update.message.reply_text(f"Idea: *{idea}*", parse_mode="Markdown", reply_markup=mode_kb())

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
        await q.edit_message_text(f"🎧 Generating *{title}*... please wait 40s", parse_mode="Markdown")
        await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VOICE)
        track = await call_suno(title, style, lyrics)
        if track and track.get('audioUrl'):
            audio_url = track['audioUrl']
            print(f"Downloading audio: {audio_url}")
            try:
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(audio_url, timeout=120) as resp:
                        audio_data = await resp.read()
                        if len(audio_data) < 10000:
                            raise Exception("Audio too small")

                        audio_file = io.BytesIO(audio_data)
                        audio_file.name = f"{title}.mp3"

                        await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VOICE)
                        await ctx.bot.send_audio(
                            chat_id=chat_id,
                            audio=audio_file,
                            title=title,
                            performer="SUNO STAR",
                            filename=f"{title}.mp3"
                        )
                        await ctx.bot.send_message(chat_id, f"✅ *{title}* Done! 🔥", parse_mode="Markdown", reply_markup=main_menu_kb())
            except Exception as e:
                print(f"DOWNLOAD SEND FAIL: {e}")
                await ctx.bot.send_message(chat_id, f"❌ Upload failed, retrying... {e}")
                # Retry direct link as last resort but HIDDEN
                try:
                    await ctx.bot.send_audio(chat_id=chat_id, audio=audio_url, title=title, performer="SUNO STAR")
                except:
                    await ctx.bot.send_message(chat_id, "❌ Busy, click ▶️ Generate Audio again", reply_markup=continue_kb())
        else:
            await ctx.bot.send_message(chat_id, "❌ Suno busy, click ▶️ Generate Audio again", reply_markup=continue_kb())
    elif data.startswith("edit_"):
        ctx.user_data['state']=data
        await q.edit_message_text(f"Send new {data.replace('edit_','')}:")
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
    async def post_init(application):
        await application.bot.delete_webhook(drop_pending_updates=True)
    app.post_init = post_init
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_verify, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(on_button, pattern="^(mode_|continue|edit_|regen|cancel|trending|idea_|surprise|back_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("✅ Bot Live - Fixed Audio Upload")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
