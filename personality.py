import datetime

OWNER_NAME = "StarDev-il"
OWNER_ID = 8695184641

PERSONALITIES = ["default"]

def get_suno_prompt(idea: str):
    return f"""SYSTEM: Respond ONLY in English. No Indonesian.

You are professional Suno songwriter. Create REAL full song (not 3 lines). 200+ words.

Idea: "{idea}"

You MUST output EXACTLY like this, with long lyrics:

TITLE: {idea[:30].title()} Nights
STYLE: Afro Amapiano fusion, soulful male vocal, log drums, warm bass, emotional, 105 BPM, Harare vibe

LYRICS:
[Intro]
Yeah, yeah, yeah...
Ooh, ooh...

[Verse 1]
Late nights in the city, thinking 'bout you
Neon lights don't shine bright like you do
Every memory we made, replay in my mind
Searching for your love, girl, I can't deny

[Pre-Chorus]
And when you call my name, I feel alive
Every touch, every whisper, I survive

[Chorus]
{idea}, hold me close don't ever let go
You are the rhythm in my heart, the highs and lows
When the world gets cold, your love keeps me warm
Dancing through the storm, till the morning comes

[Verse 2]
Whispers in the dark, secrets that we keep
Your heartbeat on my chest, lulls me to sleep
I tried to run away, but you pull me back
You are the melody I never had

[Chorus]
{idea}, hold me close don't ever let go
You are the rhythm in my heart, the highs and lows
When the world gets cold, your love keeps me warm
Dancing through the storm, till the morning comes

[Bridge]
Ooh baby, stay with me tonight
Let me hold you till the sunrise light
No more pain, no more tears
Just you and I, through the years

[Chorus - Big]
{idea}, hold me close don't ever let go
You are the rhythm in my heart, the highs and lows
When the world gets cold, your love keeps me warm
Dancing through the storm, till the morning comes

[Outro]
Yeah, Harare nights...
{idea}, my love, forever...
Ooh, yeah...

RULES:
- TITLE: line 1, STYLE: line 2, LYRICS: line 3
- Lyrics MUST be 20+ lines with Verse, Chorus, Bridge
- Never write short like "Verse 1 love song"
- Language English only
"""
