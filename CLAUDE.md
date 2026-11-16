# Fight Era (FE): faceless MMA YouTube channel

Claude Code makes this channel's videos. Read this file first; it holds the decisions, formats and rules agreed so far.

## Channel
- **Name:** Fight Era (FE). Copyright line: © FightEraTv. Contact: fight.eracontact1@gmail.com. ("Fight Scope" was an earlier name idea, replaced.)
- **Earlier videos** were built in regular Claude (claude.ai), e.g. a Perry/Ngannou video. Its build files must be uploaded here: `pn_build.py` (build pipeline), `build7.py` (card rendering), `fx_render.py` + `fx_specs.py` (template effects), `pn/align.py` (DP alignment of narration to script).

## FE video rules (from the user)
- Brand color: #C48E16 (gold).
- FE logo cover for the first 4 seconds.
- No section headers in TTS scripts.
- Clips and images sit in gold-framed boxes (#C48E16 outline, with drop shadow) on a moving background, NOT full screen (user, Nov 16; this reverses the earlier full-screen rule).
- Clips play a big role: ~2.5 min of LET IT PLAY time where narration stops.
- Mix real clips with FE cards and Faceless Studio template graphics.
- Source labels readable on mobile.
- Never more than 30 s without something new on screen.
- Transition sounds (user, Nov 16): whoosh on every visual change (as the box flies in), pop when a boxed card lands (0.3 s in). Mixed under the narration by `mix_sfx` in `thompson_build.py` (whoosh gain 0.45, pop 0.35).
- Dark backgrounds for setbacks and serious passages; gold cards for chapter headings and major numbers.
- Channel is based in Bowling Green, Kentucky.
- Voiceover: ElevenLabs, exported as MP3. The user generates it in ElevenLabs and uploads the MP3 (no API key here).
- Scripts: always follow the 3-part format in `SCRIPT_PROMPT.md` (research → script → humanization pass for TTS).
- Humanization targets: `HUMANIZATION.md`. Run `python3 script_metrics.py <script>` and hit every target before delivering a script.
- Blocked words and phrases: `blocklist.txt`. Run `python3 check_script.py <script>` on every script before it goes to the user or to ElevenLabs; it must print "Clean". Rewrite any hit naturally instead of swapping in a synonym.
- Full build pipeline, card helpers, FX template IDs and description format: see `HANDOFF_thompson.md` in this folder (handoff from regular Claude).
- **Niche:** MMA stories, fighter breakdowns, stats, MMA business. Faceless: narration over original visuals, licensed photos and stock B-roll.
- **Strategy doc:** https://claude.ai/artifact/UmBzVPLzKJgfYCX26dSRcV (niche, policy risks, tool stack, pipeline, 90-day plan).
- **History:** The user first considered basketball (NBA/college) and dropped it because of footage rights. MMA was chosen next with the same rule: no fight footage.

## Hard rules
1. **Claude does not download or rip UFC/broadcast fight footage** from YouTube, UFC Fight Pass, social media or ripper sites. The user sources clips themselves and uploads them; Claude edits what the user supplies. Remind the user once per video that long uncut UFC clips (e.g. LET IT PLAY sections) are the most likely to be claimed or struck: the UFC enforces Content ID aggressively, and 3 strikes delete the channel.
2. Fight moments are shown with **licensed photos** (Getty Images / Imagn, bought by the user), **original animated diagrams** and **stats graphics**.
3. Social-media photos of fighters or their families need the owner's permission; skip them otherwise (especially photos of children).
4. Verify every fact before narration; flag anything unconfirmed.
5. Keep human checkpoints: the user approves the topic, the edited script and the final render, and publishes manually. Upload as **private** via the API.
6. Tick YouTube's "altered or synthetic content" box only for realistic AI depictions of real people or events.
7. Avoid ad-unfriendly content: no gory injury close-ups or blood in thumbnails, no "brutal/bloody/destroyed" in titles, no strong profanity in the first seconds.

## Formats
| | Long-form | Shorts (also TikTok + Reels) |
|---|---|---|
| Aspect / size | 16:9, 1920x1080 | 9:16, 1080x1920 |
| Length | 8-15 min (8+ allows mid-roll ads) | 20-60 s |
| Script | 1,200-2,200 words | 60-150 words |
| Hook | Payoff stated in the first 15-30 s | First 1-2 s |
| Captions | SRT upload, optional burn-in | Big word-by-word burned-in captions |

Write the long script first, then cut 3-5 Shorts from its strongest moments, each re-rendered vertically with its own hook.

## Pipeline
Topic (user) -> script draft (Claude) -> edit and verify (user) -> voiceover -> Whisper word timings -> visuals -> FFmpeg render 16:9 + 9:16 -> review (user) -> upload private (YouTube Data API) -> schedule (user, in Studio) -> analytics every 2 weeks.

## Tools and access in the cloud environment
- **Pixabay:** API key in env var `PIXABAY_API_KEY`. Requests need a `User-Agent` header (default Python UA gets 403). Pixabay Content License: commercial use OK, no credit required.
- **Pexels:** hosts allowed, no API key yet (the user couldn't add one).
- **Wikimedia Commons:** hosts allowed, but the API returned HTTP 429 to this environment. Retry later; use only CC0 / PD / CC BY / CC BY-SA files and record the attribution.
- **Installed:** ffmpeg, ImageMagick, Python with Pillow.
- **Not set up yet:** voiceover (ElevenLabs or OpenAI TTS; edge-tts as free fallback), Claude API key, YouTube Data API OAuth.
- Cloud containers are wiped after inactivity, so tell the user to download finished media.

## Current project: "Wonderboy" Stephen Thompson retirement video
**Verified facts (sources: ESPN, Bloody Elbow, Sherdog, Last Word on MMA):**
- UFC 334, Nov 14, 2026, Madison Square Garden. Thompson KO'd Charles Radtke with a spinning kick at 2:54 of Round 3. Referee Marc Goddard stopped it.
- Thompson is 43 and retired after the fight, following three straight losses (Shavkat Rakhmonov, Joaquin Buckley, Gabriel Bonfim).
- He said he predicted the kick beforehand. Joe Rogan cried on the broadcast.
- Final record reported as 18-9-1 (double-check).
- Coverage calls it both a "spinning wheel kick" and a "spin hook kick": pick one name.
- Earlier career: TUF 21 Finale, July 12, 2015, Las Vegas: spinning kick KO of Jake Ellenberger at 4:29 of Round 1 (ref John McCarthy). UFC 205 vs Tyron Woodley (Nov 2016) was a majority draw; Woodley won the UFC 209 rematch (Mar 2017). KO losses: Anthony Pettis (UFC Nashville, Mar 2019), Joaquin Buckley (UFC 307, Oct 5, 2024).

**Not yet verified, so check before narrating:** a Round 1 Radtke takedown, a Round 2 stagger, gloves left in the octagon, the Tenacious D "Wonderboy" walkout song.

**Story spine:** the Ellenberger spinning kick (2015) mirrors the Radtke spinning kick ending (2026).

**Visual plan:** the user's original 26-item list was UFC footage. It is replaced by:
- Licensed photos of the key moments (kick, kneeling, gloves, mic, walk out), bought by the user.
- An original side-by-side animated diagram of the Ellenberger kick vs the Radtke kick (top priority, not yet made).
- Animated stat cards and a career timeline (not yet made).
- Stock B-roll (downloaded, below).

**B-roll downloaded:** `/home/user/wonderboy-broll/pixabay/` (19 clips, ~330 MB), with credits in `/home/user/wonderboy-broll/credits.csv`. Covers karate roots, training, arena/crowd, New York for MSG, and the retirement ending (walking into light, beach at sunset). Pixabay had no usable real-person kick footage.

**Script status (Nov 15, 2026):** corrected and fact-checked.
- `thompson/thompson_tts.txt`: the voiceover text for ElevenLabs (no markers).
- `thompson/thompson_build.md`: the same narration with CLIP / FE CARD / FX / LET IT PLAY markers and the clip shopping list (#1-30), 160 s of LET IT PLAY.
- `thompson/factcheck.md`: what was fixed, confirmed and cut.
- v2 (humanized per HUMANIZATION.md) is current; v1 kept as `*_v1.*`. `tools/make_build_thompson.py` regenerates the build version from the TTS text and verifies the narration matches.
The build version's narration must stay word-for-word identical to the TTS version, because alignment depends on it.

**Build status (Nov 15, 2026):** first draft rendered: `thompson/build/thompson_draft.mp4` (11:19, voiceover + FE cards + stock B-roll, no real clips yet).
- `tools/align.py`: pause-based sentence alignment (voiceover matched `thompson_tts.txt`, 0.37 s mean error). `tools/fe_cards.py`: stand-in card renderer (the original build7.py and Faceless Studio templates were never uploaded). `thompson/thompson_build.py`: builder; reads markers from `thompson_build.md`.
- Clips go in `thompson/clips/`, named by shopping-list number (`06_ellenberger.mp4`, `20a.mp4`, `20b.mp4`). Re-run `python3 thompson_build.py`: CLIP slots replace the stock B-roll, LET IT PLAY slots pause narration and play clip audio. `build/missing_clips.txt` lists empty slots; `build/timeline.txt` has timestamps.
- The LET IT PLAY path is untested until a real clip is supplied.

**Draft v2 (Nov 16):** user rejected stock B-roll ("clips have to be UFC related and tied to Wonderboy") and slow-zoom cards. Now: no stock footage; empty clip slots show Wonderboy-specific "moment" cards (`MOMENT` in `thompson_build.py`); all cards are white-framed panels that whip in over an animated background (`tools/fe_bg.py` → `assets/bg_gold.mp4`, `bg_dark.mp4`: gold dry-brush band on dark textured paper, chevrons, octagons, plus-grid), modelled on two reference recordings the user sent (Full Mount / MMA Talk style). Widescreen clips stay full screen; vertical or square clips sit in a framed panel on the background.

**Draft v3 (Nov 16):** Faceless Studio packs uploaded. Effects renderer installed at `fx/effects` (`npm --prefix fx/effects ci` after a fresh clone; 108 templates, `node fx/effects/render_effect.mjs --list-short`). The build uses `chapter-number` (6 chapters) and `territory-date` (Simpsonville map) full screen; other cards stay FE panels. Most templates need images, so use more once the user supplies photos. Per the user, ALL clips now sit in white-framed boxes on the moving background (may change later). Pexels key never got set up (user dropped it). Full packs kept in `vendor/` (not in git: licensed, do not redistribute; keep the repo private).

**Draft v4 (Nov 16, current):** `thompson/build/thompson_draft.mp4`, 11:23. Uses the new 4 s logo intro (with riser) as a pre-roll before narration, the four new backgrounds (cards rotate by chapter via `BG_ORDER`; clips: wide → torn_split, vertical → torn_panels, square → brush_chevrons), gold-framed boxes with drop shadows that whip in, whoosh + pop SFX, and photo cards (`PHOTOS` in the builder: WONDERBOY stance photo, Weidman/Machado pair, Helwani quote with portrait, NMF belt close-up + hand-over). Clips received (cleaned copies in `thompson/clips/`, not in git): 09 Woodley I range, 10 Woodley rematch celebration, 11 Masvidal, 16 walkout (vertical, TikTok), 17 weigh-in face-off. Clip rules: plain files fill narrated CLIP slots; LET IT PLAY slots only take files with "lip" in the name; a slot longer than the footage plays what's left, then a moment card (`fit_clips`). No LET IT PLAY clips yet, so the 160 s of LET IT PLAY is still empty. The user plans to rearrange once the rest of the missing clips arrive.

**Old next steps:** user records the voiceover in ElevenLabs and uploads the MP3, uploads the build files from regular Claude (`pn_build.py`, `build7.py`, `draw4.py`, `fx_render.py`, `fx_specs.py`, `pn/align.py`, logo, `v6/` backgrounds, fonts, `/home/claude/fx/`), and supplies the clips → silence detection + alignment → `thompson_build.py` beat plan → render → mux → YouTube description.

## Brand assets (`assets/`)
- `logo_square.png`, `logo_banner.png`: the real FE logo (user-supplied, Nov 16).
- `fe_logo_intro.mp4`: 4 s logo ident in the Full Mount style (scratched dark board, gold plus clusters, grey octagon, paper corner, logo slam + shine, corner bug) with the riser underneath; the logo lands on the riser peak at 1.7 s. Rebuild: `python3 tools/fe_logo_intro.py assets/fe_logo_intro.mp4 4`. Used as the pre-roll in draft v4.
- **Palette rule (user, Nov 16): every background uses the logo intro's colouring**: the intro's near-black board (WITHOUT scratches in backgrounds, user Nov 16; the intro itself still has them), light grey paper for big shapes, brand gold #C48E16 for plus signs and highlights (darker gold 150,104,12 over paper), dark grey 70,70,74 for outlines. No other colours.
- `bg_gold.mp4` / `bg_dark.mp4` (`tools/fe_bg.py`): RETIRED by the user (Nov 16, "scrap the last 2"). No longer used by the build; do not use them for new work.
- `sfx/`: sound effects cut from a "Top 10 sound effects for creators" TikTok (@sasvisuals) the user supplied: whoosh, pop, click, camera_flash, keyboard_typing, ding, riser (intro), bass_drop, chime, glitch. Use them for transitions and hits in future videos (e.g. whoosh on card whip-ins, bass_drop on big reveals, glitch on chapter cuts). Their original licence is unknown.
- `bg_torn_split.mp4`, `bg_brush_chevrons.mp4`, `bg_gradient_streak.mp4`, `bg_torn_panels.mp4` (`tools/fe_bg2.py`, 8 s loops): second background set; layouts modelled on Full Mount / MMA Talk / MMA Zone references the user sent, in the intro palette. These four are THE background set going forward. Pairing: torn_split for wide clips and photos, brush_chevrons for square clips, gradient_streak and torn_panels for vertical (phone/interview) clips. Each carries subtle branding: torn_split a vertical scrolling FIGHT ERA ticker on the left edge plus a ghost logo printed into the paper; brush_chevrons a large faint FIGHT ERA wordmark drifting along the bottom of the board; gradient_streak a ghost logo right of the streak; torn_panels FIGHT ERA tickers running through the grey torn strips. Plus the gold logo badge in a corner. `bg_preview_reel.mp4` shows the four with sample gold-framed boxes. Used by the Thompson build from draft v4.
- Box sizes vary by card type (data cards large, titles/quotes/moments smaller and off-center); the logo is never boxed.
