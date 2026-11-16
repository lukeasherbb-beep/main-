# Fight Era — Thompson Video: Claude Code Handoff

## PROJECT
Fight Era (FE) MMA YouTube video about Stephen "Wonderboy" Thompson's career and retirement at UFC 334 (Nov 14, 2026, Madison Square Garden). He KO'd Charles Radtke with a spinning wheel kick in Round 3.

## SCRIPT
`/home/claude/vid/thompson_script.md` — full narrated script with [CLIP], [FE CARD], [LET IT PLAY] markers. 27 clip moments, ~2.5 min total LET IT PLAY time.

## CHANNEL RULES
- Brand color: #C48E16 (gold)
- FE logo cover for first **4 seconds** (not 10)
- No section headers in TTS scripts (TTS voice would read them aloud)
- **All clips full screen, no background** — clips are NOT framed in a panel; they fill 1920x1080
- Clips play a bigger role than previous videos — more clips, longer holds, more moments where narration stops
- Mix real clips with FE cards and Faceless Studio template graphics
- Source labels readable on mobile
- Never >30s without something new on screen
- Let some clips' own audio play while narration stops (LET IT PLAY markers)
- Dark backgrounds for setbacks/serious passages
- Gold (#C48E16) cards for chapter headings and major numbers
- Channel: © FightEraTv, contact: fight.eracontact1@gmail.com
- Based in Bowling Green, Kentucky

## VIDEO DESCRIPTION FORMAT
Example from Perry/Ngannou video (`/home/claude/vid/description2.txt`):
- Opening paragraph summarizing the video hook
- Additional context paragraphs
- Timestamped chapter list (0:00 format)
- Channel boilerplate paragraph
- 📩 Business Inquiries: fight.eracontact1@gmail.com
- © FightEraTv
- Hashtag line

## BUILD PIPELINE (reference: Perry/Ngannou video)
The previous video used this pipeline:

1. **Script** → written, reviewed, humanized for TTS
2. **TTS voiceover** → ElevenLabs, exported as MP3
3. **Silence detection** → ffmpeg silencedetect on the voiceover to find gaps between sentences
4. **DP sentence alignment** → `/home/claude/vid/pn/align.py` — aligns script sentences to audio segments using dynamic programming. Takes `gaps.txt` (silence boundaries) and `vo.txt` (script paragraphs), outputs `sent.json` (per-sentence start/end times)
5. **Beat plan** → `pn_build.py` defines BEATS list: (narration_time, kind, payload, headline, options). Kinds:
   - `card` — PIL-rendered text/stats card with gold FE background
   - `photo` — full-screen photo with frame, headline, source label
   - `clip` — user-provided video clip in a framed panel with background
   - `brk` — clip plays with its OWN audio, narration pauses (break)
   - `fx` / `fxfull` — Faceless Studio template graphic
6. **Card rendering** → `build7.py` renders each beat as a short .mp4 clip (card on animated gold/dark background with whip transitions)
7. **FX rendering** → `fx_render.py` + `fx_specs.py` → calls `node /home/claude/fx/render_effect.mjs` for template graphics
8. **Audio assembly** → narration split at break points, break clips' own audio inserted, everything delayed to match video timeline
9. **Concat + mux** → all beat clips concatenated, muxed with assembled audio

## KEY DIFFERENCE FOR THIS BUILD
**Clips are full screen with NO background.** In `pn_build.py`, clips used `video_beat()` which placed them in a framed panel on top of the animated gold background. For Thompson, clips should fill the entire 1920x1080 frame — scale to fill, no panel frame, no gold background behind them. The `full=True` path in `video_beat()` is closer to what we want (it does full-screen with just a watermark overlay), but needs to be the default for all clips.

## KEY FILES
| File | Purpose |
|------|---------|
| `thompson_script.md` | The script with visual markers |
| `pn_build.py` | Perry/Ngannou builder (reference for beat structure, audio assembly, concat) |
| `build7.py` | Card/photo/clip rendering library (PIL + ffmpeg) |
| `draw4.py` | Font helpers, text wrapping, card renderers |
| `fx_render.py` | Template graphic renderer (calls Node.js) |
| `fx_specs.py` | FX name → (effect_id, overrides) mapping |
| `pn/align.py` | DP sentence alignment (gaps.txt + vo.txt → sent.json) |
| `logo.png` | FE logo |
| `v6/bg2_a.mp4`, `bg2_b.mp4`, `bg2_d.mp4`, `bg_dark.mp4` | Pre-rendered animated backgrounds |

## CARD TYPE HELPERS (from build7.py)
```python
T(head, sub=None, kicker=None, **k)  # Text card
Q(quote, attr)                        # Quote card
S(kicker, items, note=None)           # Stats card — items = [("18", "Wins"), ...]
V(kicker, side_a, side_b)             # Versus card
Ls(kicker, rows)                      # List card
TL(kicker, events)                    # Timeline card
```

## FX TEMPLATE IDS AVAILABLE
stacked-highlight, question-focus, chapter-number, territory-date, ribbon-profile, two-bars, milestone-path, quote-profile, paired-profiles, icon-bullets, scribble-title

## NEXT STEPS
1. User provides clips (27 items on the shopping list in the script)
2. Write TTS-clean version of the script (strip all bracket markers)
3. Generate voiceover via ElevenLabs
4. Run silence detection + DP alignment
5. Build the beat plan (thompson_build.py)
6. Render all beats
7. Assemble audio with break points
8. Concat + mux → final .mp4
9. Write YouTube description with timestamps
