import os, re, json, aiohttp, urllib.parse, threading, asyncio
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
AI_BASE = "https://api.hostify.indevs.in/api/ai/grok"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Suno Bot Live - StarDev-il", 200

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
            if m.status in ["member","administrator","creator","owner"]: return True
        except: continue
    return False

def verify_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=GROUP_LINK)],
                                 [InlineKeyboardButton("✅ Verify / Done", callback_data="verify")]])

def mode_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI Generate Full Song", callback_data="mode_ai")],
        [InlineKeyboardButton("✍️ I Have Own Lyrics", callback_data="mode_custom")],
        [InlineKeyboardButton("🎼 Full Custom Title/Style/Lyrics", callback_data="mode_full_custom")]
    ])

def continue_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Continue - Generate Audio", callback_data="continue")],
        [InlineKeyboardButton("✏️ Edit Title", callback_data="edit_title"), InlineKeyboardButton("🎨 Edit Style", callback_data="edit_style")],
        [InlineKeyboardButton("📝 Edit Lyrics", callback_data="edit_lyrics"), InlineKeyboardButton("🔄 Regenerate", callback_data="regen")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

async def generate_fields(idea: str):
    prompt = get_suno_prompt(idea)
    for _ in range(3):
        try:
            async with aiohttp.ClientSession() as s:
                # FIXED: POST + handle result.answer format from your screenshot
                async with s.post(AI_BASE, json={"q": prompt}, timeout=60) as r:
                    data = await r.json()
                    print(f"AI RAW: {data}")

                    txt = ""
                    res = data.get("result")
                    if isinstance(res, dict):
                        txt = res.get("answer", "") or res.get("response", "")
                    elif isinstance(res, str):
                        txt = res
                    else:
                        txt = data.get("response") or data.get("answer") or str(data)

                    if "TITLE:" in txt and "STYLE:" in txt and "LYRICS:" in txt:
                        title = re.search(r'TITLE:\s*(.+)', txt, re.I).group(1).strip()[:80]
                        style = re.search(r'STYLE:\s*(.+)', txt, re.I).group(1).strip()[:120]
                        lyrics = re.search(r'LYRICS:\s*(.+)', txt, re.I|re.S).group(1).strip()[:3000]
                        return title, style, lyrics
                    else:
                        print(f"AI didn't return TITLE/STYLE/LYRICS, got: {txt[:200]}")
        except Exception as e:
            print(f"AI error {e}")
            await asyncio.sleep(1)
            continue
    return f"{idea[:30].title()} Vibes", "Afro Amapiano, log drums, emotional, 110 BPM", f"[Verse 1]\n{idea}\n[Chorus]\n{idea}\n[Verse 2]\nHold you close till morning light\n[Outro]\nYeah..."

async def call_suno(title, style, lyrics):
    url = f"{SUNO_API}?action=generate&prompt={urllib.parse.quote(lyrics)}&title={urllib.parse.quote(title)}&isInstrumental=false&musicStyle={urllib.parse.quote(style)}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=180) as r:
            try:
                data = await r.json()
                print(f"SUNO RAW: {data}")
                if data.get("data",{}).get("tracks"):
                    return data["data"]["tracks"][0]
            except Exception as e:
                print(f"Suno error {e}")
    return None

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_verified(update.effective_user.id) and await is_joined(update.effective_user.id, ctx):
        await update.message.reply_text("🎵 *Suno Bot Ready*\nChoose mode:", parse_mode="Markdown", reply_markup=mode_kb())
        return
    await update.message.reply_text("⚠️ Join channel first 👇", reply_markup=verify_kb())

async def on_verify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await ctx.bot.send_chat_action(q.message.chat_id, ChatAction.TYPING)
    if await is_joined(q.from_user.id, ctx):
        set_verified(q.from_user.id)
        await q.edit_message_text("✅ Verified! Choose mode:", reply_markup=mode_kb())
    else:
        await q.answer("Not joined yet!", show_alert=True)

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_verified(uid):
        if not await is_joined(uid, ctx):
            await update.message.reply_text("Join first 👇", reply_markup=verify_kb()); return
        set_verified(uid)

    state = ctx.user_data.get('state')
    text = update.message.text.strip()

    if state == "await_full_title":
        ctx.user_data['title'] = text[:80]; ctx.user_data['state'] = "await_full_style"
        await update.message.reply_text(f"✅ Title: *{text}*\n\n2️⃣ Now send Style:", parse_mode="Markdown"); return
    elif state == "await_full_style":
        ctx.user_data['style'] = text[:120]; ctx.user_data['state'] = "await_full_lyrics"
        await update.message.reply_text(f"✅ Style: *{text}*\n\n3️⃣ Now send Lyrics with [Verse] [Chorus]:", parse_mode="Markdown"); return
    elif state == "await_full_lyrics":
        ctx.user_data['lyrics'] = text[:3000]; ctx.user_data['state'] = None
        await update.message.reply_text(f"*Song Title:*\n{ctx.user_data['title']}\n\n*Style Prompt:*\n{ctx.user_data['style']}\n\n*Full Lyrics:*\n{text[:3500]}", parse_mode="Markdown", reply_markup=continue_kb()); return

    elif state == "await_own_lyrics":
        ctx.user_data['lyrics'] = text[:3000]; ctx.user_data['state'] = "await_own_title"
        await update.message.reply_text("✅ Lyrics saved!\n\n2️⃣ Now send *Title*:", parse_mode="Markdown"); return
    elif state == "await_own_title":
        ctx.user_data['title'] = text[:80]; ctx.user_data['state'] = "await_own_style"
        await update.message.reply_text(f"✅ Title: *{text}*\n\n3️⃣ Now send *Style*:", parse_mode="Markdown"); return
    elif state == "await_own_style":
        ctx.user_data['style'] = text[:120]; ctx.user_data['state'] = None
        await update.message.reply_text(f"*Song Title:*\n{ctx.user_data['title']}\n\n*Style Prompt:*\n{text}\n\n*Full Lyrics:*\n{ctx.user_data['lyrics'][:3500]}", parse_mode="Markdown", reply_markup=continue_kb()); return

    elif state in ["edit_title","edit_style","edit_lyrics"]:
        key = state.split("_")[1]; ctx.user_data[key] = text[:3000]; ctx.user_data['state']=None
        t = ctx.user_data.get('title'); s = ctx.user_data.get('style'); l = ctx.user_data.get('lyrics')
        await update.message.reply_text(f"*Song Title:*\n{t}\n\n*Style Prompt:*\n{s}\n\n*Full Lyrics:*\n{l[:3500]}", parse_mode="Markdown", reply_markup=continue_kb()); return

    idea = re.sub(r'^(suno|sonu|song|music)\s*','', text, flags=re.I).strip()
    ctx.user_data['idea'] = idea or text
    await update.message.reply_text(f"Idea: *{ctx.user_data['idea']}*\nChoose:", parse_mode="Markdown", reply_markup=mode_kb())

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    data = q.data
    chat_id = q.message.chat_id

    if data == "mode_ai":
        idea = ctx.user_data.get('idea','love song')
        await ctx.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await q.edit_message_text(f"🤖 Creating for *{idea}*... ⏳", parse_mode="Markdown")
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"*Song Title:*\n{title}\n\n*Style Prompt:*\n{style}\n\n*Full Lyrics:*\n{lyrics[:3500]}", parse_mode="Markdown", reply_markup=continue_kb())

    elif data == "mode_custom":
        ctx.user_data['state']="await_own_lyrics"
        await q.edit_message_text("✍️ *Own Lyrics Mode*\n\n1️⃣ Send your *Lyrics*:", parse_mode="Markdown")

    elif data == "mode_full_custom":
        ctx.user_data['state']="await_full_title"
        await q.edit_message_text("🎼 *Full Custom Mode*\n\n1️⃣ Send *Title*:", parse_mode="Markdown")

    elif data == "continue":
        title = ctx.user_data.get('title'); style = ctx.user_data.get('style'); lyrics = ctx.user_data.get('lyrics')
        if not title: await q.edit_message_text("Expired"); return

        await q.edit_message_text(f"🎧 Generating *{title}*... ~60s", parse_mode="Markdown")
        await ctx.bot.send_chat_action(chat_id, ChatAction.RECORD_VOICE)

        track = await call_suno(title, style, lyrics)
        if track and track.get('musicFile'):
            user_name = q.from_user.first_name or "StarDev-il"
            safe_title = re.sub(r'[^a-zA-Z0-9 ]','', title)[:30].strip() or "Suno Song"
            file_name = f"{safe_title} - {user_name}.mp3"

            if track.get('coverImage'):
                try:
                    await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
                    await ctx.bot.send_photo(chat_id, track['coverImage'], caption=f"🎵 {title}\n👤 {user_name}\n🎨 {style}")
                except: pass

            try:
                await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)
                await ctx.bot.send_audio(
                    chat_id,
                    audio=track['musicFile'],
                    title=title,
                    performer=user_name,
                    file_name=file_name
                )
                await ctx.bot.send_message(chat_id, f"✅ *{title}* by {user_name} done!", parse_mode="Markdown", reply_markup=mode_kb())
            except Exception as e:
                await ctx.bot.send_message(chat_id, f"Here file: {track['musicFile']}\nError: {e}")
        else:
            await ctx.bot.send_message(chat_id, "❌ Suno failed, try again", reply_markup=continue_kb())

    elif data.startswith("edit_"):
        ctx.user_data['state']=data
        await q.edit_message_text(f"Send new {data.replace('edit_','')}:")
    elif data == "regen":
        idea = ctx.user_data.get('idea','love')
        await ctx.bot.send_chat_action(chat_id, ChatAction.TYPING)
        title, style, lyrics = await generate_fields(idea)
        ctx.user_data['title']=title; ctx.user_data['style']=style; ctx.user_data['lyrics']=lyrics
        await q.edit_message_text(f"*Song Title:*\n{title}\n\n*Style Prompt:*\n{style}\n\n*Full Lyrics:*\n{lyrics[:3500]}", parse_mode="Markdown", reply_markup=continue_kb())
    elif data == "cancel":
        ctx.user_data.clear()
        await q.edit_message_text("Cancelled. Send new idea.")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_verify, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(on_button, pattern="^(mode_|continue|edit_|regen|cancel)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print("✅ Suno Bot Fixed Live - POST API")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
