import re, sys
tts = open(sys.argv[1]).read()
# (anchor text that starts a sentence/paragraph, marker block inserted BEFORE it). "END" = append at end.
M = [
 ("This is the story of Stephen", "[FE LOGO COVER — 4 seconds]\n[LET IT PLAY: #2 Radtke KO, UFC 334, real time — 8s, arena audio. Cold open: the kick lands, crowd erupts]"),
 ("In nineteen ninety-eight, that kid", "[FX: territory-date — SIMPSONVILLE, SOUTH CAROLINA · 1998]"),
 ("Twenty-eight years later", "[FE CARD: T(\"WONDERBOY\") — gold, Thompson fighting-stance photo silhouette (#1)]"),
 ("Stephen Randall Thompson was born", "[CLIP: #16 Thompson walkout at UFC 334]\n[FX: chapter-number — 01 · THE KARATE KID]"),
 ("The family tree only gets more", "[FX: paired-profiles — CHRIS WEIDMAN (brother Tony's brother-in-law) · CARLOS MACHADO (sister Lindsay's husband, his BJJ coach)]"),
 ("All those hours in his dad's", "[CLIP: #3 Young Thompson training at Upstate Karate (photo or footage)]"),
 ("From there the record got ridiculous.", "[FE CARD: S(\"KICKBOXING\", [(\"57-0\", \"Combined record\"), (\"37-0\", \"Amateur\"), (\"20-0\", \"Pro\")]) — gold]"),
 ("Sixteen amateur titles came with it", "[FX: icon-bullets — 16 amateur titles · 2005 world champion · #1 World Combat League]"),
 ("There was nobody left to beat", "[CLIP: #3 Kickboxing-era footage or photo]"),
 ("February fourth, two thousand and twelve", "[CLIP: #4 UFC 143 debut KO, Feb 2012]"),
 ("Seven straight wins followed.", "[FX: chapter-number — 02 · THE RUN]"),
 ("Robert Whittaker, a future", "[FE CARD: TL(\"THE RUN\", [(\"2014\", \"Whittaker — TKO R1\"), (\"2015\", \"Ellenberger — KO R1\"), (\"2016\", \"Hendricks — TKO R1\"), (\"2016\", \"MacDonald — UD\")])]\n[CLIP: #5 Whittaker TKO, UFC 170]"),
 ("July of two thousand and fifteen brought", "[CLIP: #6 Ellenberger fight, TUF 21 Finale — Ellenberger's right hand drops Thompson]"),
 ("Remember that kick.", "[LET IT PLAY: #6 Ellenberger spinning wheel kick KO — 10s, arena audio]"),
 ("Johny Hendricks, a former", "[CLIP: #7 Hendricks TKO, Feb 2016]"),
 ("Seven in a row made him", "[CLIP: #8 MacDonald striking exchanges, June 2016]"),
 ("Most people remember UFC two oh five", "[FX: chapter-number — 03 · MADISON SQUARE GARDEN]"),
 ("For long stretches Thompson picked", "[FE CARD: V(\"UFC 205 · WELTERWEIGHT TITLE\", \"WOODLEY\", \"THOMPSON\")]\n[CLIP: #9 Woodley vs Thompson I — Thompson working from the outside]"),
 ("Twenty-five minutes, three judges", "[LET IT PLAY: #9 Woodley I, Round 4 — knockdowns and guillotine escape — 20s, arena audio]"),
 ("They ran it back at UFC two oh nine", "[LET IT PLAY: #9 Woodley I scorecards read — 8s, arena audio]\n[FE CARD: S(\"MAJORITY DRAW\", [(\"47-47\", \"\"), (\"47-47\", \"\"), (\"48-47\", \"Woodley\")]) — split screen Woodley vs Thompson]"),
 ("Two title fights.", "[CLIP: #10 Woodley celebrating after UFC 209]"),
 ("That kind of thing breaks fighters.", "[CLIP: #11 Masvidal fight, UFC 217]"),
 ("The next stretch was rougher.", "[FX: chapter-number — 04 · THE HARD YEARS] — dark background from here"),
 ("There were still good nights", "[LET IT PLAY: #12 Pettis KO, 2019 — 6s, arena audio]"),
 ("In December of two thousand and twenty-two he put", "[CLIP: NEW #27 Holland fight, Dec 2022]"),
 ("Shavkat Rakhmonov submitted him", "[CLIP: NEW #28 Rakhmonov fight, UFC 296]"),
 ("Ten months later, Joaquin Buckley", "[CLIP: #13 Buckley KO, UFC 307 — narration over]"),
 ("In July of two thousand and twenty-five, at UFC Nashville", "[CLIP: NEW #29 Bonfim fight, UFC Nashville]"),
 ("That was the picture heading into November.", "[FE CARD: T(\"1-5\", sub=\"IN HIS LAST 6 FIGHTS\") — dark background]"),
 ("Thompson had become a dad", "[CLIP: #14 Thompson with his daughter (only with permission; else skip)]\n[FX: chapter-number — 05 · WONDERDAD]"),
 ("About the belt, he was blunt", "[FX: quote-profile — \"I don't see the title anymore.\" — Stephen Thompson to Ariel Helwani]"),
 ("He picked his exit himself.", "[FE CARD: T(\"WONDERDAD\") — warm gold]"),
 ("The UFC gave him Charles Radtke", "[FE CARD: V(\"UFC 334 · MADISON SQUARE GARDEN\", \"THOMPSON 17-9-1\", \"RADTKE 12-5\")]\n[CLIP: #17 Radtke highlight or weigh-in face-off]"),
 ("Round one went the way", "[FX: chapter-number — 06 · ONE LAST TIME]\n[LET IT PLAY: #18 Round 1 — Radtke takedown — 10s, arena audio]"),
 ("Thompson scrambled back up", "[CLIP: #18 Thompson back to his feet, Round 1]"),
 ("Round two opened with another", "[CLIP: NEW #30 Round 2 — Radtke takedown against the fence]"),
 ("Thompson got back to his feet and dug", "[LET IT PLAY: NEW #30 Round 2 body kick hurts Radtke — 8s, arena audio]"),
 ("Radtke kept hunting takedowns", "[FE CARD: T(\"ROUND 3\") — gold on dark]"),
 ("Some outlets are calling it", "[LET IT PLAY: #20 Spinning wheel kick KO, real time — 10s, full arena audio]\n[LET IT PLAY: #20 Slow-motion replay, alternate angle — 10s]\n[LET IT PLAY: #21 Goddard stops the fight, Thompson reacts — 10s]\n[FX: stacked-highlight — SPIN HOOK KICK / WHEEL KICK]"),
 ("The stats from that fight are strange.", "[FX: two-bars — SIGNIFICANT STRIKES: Thompson 67 · Radtke 11 / CONTROL TIME: Radtke 4:47]"),
 ("Thompson had told himself", "[CLIP: #22 Thompson emotional in the octagon]"),
 ("On the mic, he thanked", "[LET IT PLAY: #22 Thompson emotional in the octagon — 12s]\n[LET IT PLAY: #23 Gloves placed in the center — 10s]"),
 ("Joe Rogan was crying", "[LET IT PLAY: #24 Thompson on the mic (\"spin hook kick to the dome… my fans, y'all\") — 20s]"),
 ("He'd also predicted the finish", "[LET IT PLAY: #25 Joe Rogan reaction — 8s]"),
 ("That night hit people the way", "[FE CARD: Q(\"The greatest retirement fight victory in UFC history.\", \"Forbes, Nov 14, 2026\")]"),
 ("In a sport that runs on trash talk", "[FE CARD: T(\"THE NMF\") — belt graphic]"),
 ("Between fights, he was back home", "[CLIP: #15 Thompson teaching kids at Upstate Karate]"),
 ("He walks away with a professional", "[FE CARD: S(\"FINAL RECORD\", [(\"18-9-1\", \"Pro MMA\"), (\"13-9-1\", \"UFC\"), (\"57-0\", \"Kickboxing\")]) — championship gold]"),
 ("Numbers only cover part of it.", "[CLIP: #1 Career montage]"),
 ("You don't have to be the villain", "[LET IT PLAY: #26 Thompson walks out of the octagon for the final time, waving — 10s, arena audio]"),
 ("END", "[FE CARD: T(\"THANK YOU, WONDERBOY\") — gold on black, FE logo in corner]"),
]
out = tts.rstrip("\n")
for anchor, block in M:
    if block is None: continue
    if anchor == "END":
        out += "\n\n" + block + "\n"; continue
    n = out.count(anchor); assert n == 1, (anchor, n)
    i = out.index(anchor)
    before = out[:i]
    if before.endswith("\n\n") or i == 0:
        out = before + block + "\n" + out[i:]
    else:  # mid-paragraph: break the paragraph at this sentence
        out = before.rstrip(" ") + "\n" + block + "\n" + out[i:]
open(sys.argv[2], "w").write("The UFC Let Him Fight One More Time. He Made It Count.\n\n" + out)
# verify narration text is identical
strip = lambda s: " ".join(l for l in s.split() )
body = "\n".join(l for l in out.splitlines() if not l.startswith("["))
assert strip(body) == strip(tts), "narration mismatch"
lip = sum(int(x) for x in re.findall(r"LET IT PLAY:[^\]]*?— (\d+)s", out))
print("narration identical; LET IT PLAY total", lip, "s")
