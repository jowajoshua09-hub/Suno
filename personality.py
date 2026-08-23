import datetime

OWNER_NAME = "StarDev-il"
OWNER_ID = 8695184641

PERSONALITIES = {
    "default": "Modern, creative songwriter, balanced",
    "sad": "Sad, heartbreak, lo-fi hip hop, piano, soft 808s, female vocal, rainy, 85 BPM, emotional",
    "hype": "Hype, aggressive, Phonk, Trap, distorted 808s, dark choir, gym, warrior, 140 BPM, powerful male vocal",
    "love": "Romantic, sweet love, piano, acoustic guitar, soft male vocal, soulful, 90 BPM",
    "anime": "Epic anime opening, Japanese taiko drums, cinematic orchestra, powerful choir, 150 BPM",
    "afro": "Afrobeat Amapiano, log drums, African percussion, dance, joyful, 110 BPM",
}

def get_suno_prompt(user_idea: str):
    idea_lower = user_idea.lower()
    if any(w in idea_lower for w in ["sad","cry","pain","heartbreak","lonely"]):
        mode = "sad"
    elif any(w in idea_lower for w in ["hype","gym","demon","warrior","oni","phonk","fight"]):
        mode = "hype"
    elif any(w in idea_lower for w in ["love","romantic","baby"]):
        mode = "love"
    elif any(w in idea_lower for w in ["anime","japan"]):
        mode = "anime"
    elif any(w in idea_lower for w in ["afro","amapiano","dance"]):
        mode = "afro"
    else:
        mode = "default"

    vibe = PERSONALITIES[mode]

    return f"""You are Suno Music Data Generator API - Personality Mode: {mode} - Vibe: {vibe}
Task: Create original song data for idea: "{user_idea}"
You MUST output ONLY:
TITLE: <catchy 2-5 words matching {mode} vibe, max 80 chars>
STYLE: <must include this vibe: {vibe}, max 120 chars>
LYRICS:
[Intro]
...
[Verse 1]
...
[Chorus]
...

RULES: Output must start with TITLE:, no markdown, no emojis, Lyrics must match {vibe}
Generate now in {mode} personality.
"""

def get_chat_prompt():
    date = datetime.datetime.now().strftime("%B %d, %Y")
    return f"""You are Suno Bot by {OWNER_NAME}. Date: {date}. Help create songs."""

def get_personality_list():
    return PERSONALITIES