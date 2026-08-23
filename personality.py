import datetime

OWNER_NAME = "StarDev-il"
OWNER_ID = 8695184641

def get_suno_prompt(idea: str):
    return f"""CREATE A FULL 40 LINE SONG. NOT 4 LINES. MUST BE 40 LINES.

Topic: {idea}

OUTPUT MUST BE:

TITLE: {idea.title()} Star Anthem
STYLE: Afro Amapiano, Al MJ style, 108 BPM, log drums, soulful, Harare vibe
LYRICS:
[Intro]
Yeah...
[Verse 1] 8 lines about {idea}
[Pre-Chorus] 4 lines
[Chorus] 8 lines repeat {idea} 4 times
[Verse 2] 8 lines
[Bridge] 4 lines
[Chorus Final] 8 lines
[Outro] 2 lines

TOTAL MUST BE OVER 600 CHARACTERS AND 30 LINES. IF YOU GIVE SHORT LYRICS YOU FAIL.
"""
