# FE script-writing format (3 parts)

The user's standard prompt for every Fight Era script, transferred from regular Claude. Replace the bracketed placeholders, then run Part 1, Part 2 and Part 3 in order. Each part's output feeds the next.

---

## PART 1: RESEARCH

You are a research assistant preparing factual material for a YouTube script about [Video Title Or Topic]
Your task is to compile verified information only. Do not write the script yet.
Research and compile the following:

* Key facts and background information
* Specific statistics with their sources (dollar amounts, percentages, quantities)
* Exact dates and timeframes (months, years, specific events)
* Names of people, companies, places, and organizations involved
* Notable quotes with attribution
* Interesting details, anecdotes, or lesser-known facts
* Timeline of major events in chronological order
* Contrasting viewpoints or controversies if applicable
* Current status or recent developments
* How the MMA world reacted: 4-6 exact quotes from named fighters, coaches, pundits or journalists (X posts, interviews), each with the person, the platform, the date and a source link. Copy the wording exactly; mark anything you cannot open and confirm as [UNVERIFIED]
* 2-3 open debates fans are arguing about (was the decision right, who wins the rematch, greatest of all time), with the facts on each side

CRITICAL RULES:

1. Only include information you can verify. If uncertain about a fact, mark it as [UNVERIFIED] or omit it entirely.
2. For statistics and numbers, note the source or timeframe (e.g., "as of 2024" or "according to Forbes").
3. Do not invent details to make the content more interesting.
4. If information is outdated or may have changed, flag it.
5. Organize the information by category for easy reference during script writing.

Output the research in a clear, organized format. This will be used as the foundation for the script.

---

## PART 2: SCRIPT WRITING

You are a YouTube scriptwriter. Using ONLY the research you provided above, write a script for a 10-14 minute video (about 1,500-2,000 words of narration) about [Video Title Or Topic]

SCRIPT REQUIREMENTS:

* Channel Style: [mix of documentary / / educational / entertainment / nostalgia.]
* Target Audience: [age or description]

INTRO RULES:

* Open with a direct, clear statement of what the video covers
* Use this format: "These are [number] [subject] who [compelling contrast or outcome]" OR "This is [the story/the reason/what happened when] [specific premise]"
* No narrative scene-setting, no "imagine this," no fictional openings, no dramatic storytelling hooks
* State the premise within the first two sentences then move into the content
* The very first sentence carries the payoff (the result, the shock, the number), because the video opens on a cold-open clip and viewers decide in the first 5-10 seconds whether to stay
* Suggest the cold-open moment (the single strongest clip from the story) on a line above the script, marked COLD OPEN, so the build places it before the logo

STRUCTURE:

* Clear narrative arc with beginning, middle, and end
* Organized sections that flow logically
* Natural transition sentences between sections
* End with a conclusion that ties back to the premise
* Include a "how the MMA world reacted" passage using 4-6 of the verified quotes from the research, each attributed by name (where it fits the story, usually right after the main event)

ENGAGEMENT RULES (added Nov 17, 2026 after studying Full Mount, MMA Zone and MMA Talk):

* Subscribe ask: one plain sentence right after the premise, within the first 30 seconds (for example, "If you're new here, subscribing helps the channel and costs you nothing.")
* Viewer questions: exactly 2 or 3 direct questions to the viewer, written as real questions with a question mark, each about one of the open debates in the research, placed at the end of a section or in the outro, each followed by a short comment prompt ("Tell me in the comments.")
* Opinion: each section may carry one clear line where the narrator takes a side or makes a light aside. Label it as opinion through wording ("I think", "for my money"), never present it as fact
* Outro: one comment prompt tied to the last viewer question, then point to the next video. Do not promise an upload schedule the channel does not keep
* These are the only questions allowed in the script; no rhetorical questions anywhere else

CRITICAL ACCURACY RULE: Do NOT add any facts, statistics, dates, numbers, or claims that are not explicitly included in the research above. If the research doesn't provide a specific detail, do not invent one. Use only what has been verified.

Write the full script with speaker text only. No visual directions unless specifically requested.

---

## PART 3: HUMANIZATION PASS

You are a script editor specializing in making AI-generated content sound natural and human while optimizing for text-to-speech delivery. Your job is to rewrite the following script to feel authentic and perform well when read by AI voice software like ElevenLabs.

SCRIPT TO REWRITE: [INSERT SCRIPT FROM PART 2]

CRITICAL ACCURACY RULE: Do NOT fabricate or invent any new details. Every fact, statistic, date, name, and claim in your rewritten version must already exist in the original script. You are restructuring and rephrasing, not adding new information.

TRANSFORMATION RULES:

### 1. ELIMINATE AI VOCABULARY
Remove or replace these words and phrases that signal AI-generated text:
- Transition words: "furthermore," "moreover," "in conclusion," "consequently," "in summary," "as such," "hence," "thus," "therefore," "accordingly," "additionally"
- Hedge phrases: "it may seem," "on the other hand," "it remains to be seen," "while it is true," "some might argue," "it is important to note"
- Buzzwords: "delve," "crucial," "comprehensive," "robust," "landscape," "paradigm," "leverage," "innovative," "cutting-edge," "game-changer," "groundbreaking," "transformative," "holistic," "seamless," "dynamic," "multifaceted," "pivotal"
- Filler phrases: "in today's world," "in the realm of," "at the end of the day," "the fact of the matter is," "it goes without saying," "needless to say," "a testament to"
- Overused descriptors: "plethora," "myriad," "paramount," "invaluable," "remarkable," "significant," "substantial," "profound," "essential," "vital"

Replace with plain, direct language.

### 2. OPTIMIZE FOR TEXT-TO-SPEECH
This script will be read by AI voice software. Write for smooth spoken delivery:

* Write in complete, flowing sentences rather than fragments
* Connect related short ideas with commas instead of periods
* Avoid one-word sentences and two-word sentences entirely
* Do not use rhetorical questions. Keep the 2-3 direct viewer questions from Part 2 exactly as questions (they are the only ones allowed)
* Minimize em-dashes as they create awkward pauses
* Do not use ellipses
* Vary sentence length naturally between 10-30 words but avoid extremes in either direction
* Write the way a calm, knowledgeable narrator would actually speak out loud

BAD EXAMPLE (will sound choppy in TTS): "March 1953. Disney terminated his contract. Sixteen years old. The official reason? Severe acne. Required too much makeup."

GOOD EXAMPLE (flows naturally in TTS): "In March of 1953, Disney terminated his contract when he was just sixteen years old, and the official reason given was that his severe acne required too much makeup to cover on camera."

### 3. CREATE NATURAL ENTROPY WITHOUT FRAGMENTS
To avoid AI detection patterns while maintaining TTS quality:

* Use unexpected but accurate word choices instead of predictable phrasing
* Vary how you introduce facts (don't start every sentence with "He" or "She" or "The")
* Include specific details from the research and position them for emphasis
* Use natural spoken transitions like "and that's when," "which meant," "but here's the thing," "the result was," "what nobody expected was"
* Let the narrator have a point of view through word choice, and keep the one clearly worded opinion line per section from Part 2
* Combine multiple facts into single flowing sentences where it makes sense

### 4. REMOVE HEDGING LANGUAGE
Cut non-committal phrases entirely. State things directly:

* Cut: "It could be argued that..."
* Cut: "Some experts believe..."
* Cut: "It is generally accepted that..."
* Cut: "Perhaps..." / "Potentially..." / "Possibly..."
* Cut: "It's worth noting that..."
* Cut: "Interestingly enough..."

### 5. PRESERVE THE INTRO FORMAT
Keep the direct premise-stating intro from Part 2. Do not convert it into a narrative or storytelling hook. The first two sentences should still clearly state what the video is about. Keep the subscribe sentence, the viewer questions, the comment prompts and the reaction quotes (quotes stay word for word).

### 6. PRESERVE TONE AND STYLE
Match the channel style specified in Part 2. You are making the voice less predictable and more natural, not changing the voice itself.

### 7. MANDATORY REWRITE REQUIREMENTS (DO NOT SKIP)
This is not a light polish. You must make substantial changes to every paragraph. Follow these rules strictly:

**SENTENCE STARTER VARIATION**
* Go through the script and highlight every sentence that starts with "He," "She," "The," "In," "By," "His," "Her," "It," or "At"
* If more than two sentences in any paragraph start with the same word, rewrite them
* Use these alternative openings: name of person, year/date, location, action verb, specific detail, consequence of previous sentence
* Example: Instead of "He filed for bankruptcy in 1962. He was married eight times. He had a gambling problem." write "Bankruptcy came in 1962, the same year he'd earned twelve million dollars. Eight marriages drained him further, and a gambling habit he described as losing his fortune again and again finished the job."

**SENTENCE COMBINING REQUIREMENT**
* Find every instance of two or three consecutive short sentences (under 12 words each) that share the same subject
* Combine them into one flowing sentence of 20-35 words
* You must combine at least 3-5 sentence groups per section

**RHYTHM VARIATION REQUIREMENT**
* Every paragraph must contain at least one sentence under 15 words AND one sentence over 25 words
* Do not allow more than three sentences in a row to be similar length (within 5 words of each other)
* After a long sentence, follow with a short punchy one, and vice versa

**WORD CHOICE VARIATION**
* Find generic verbs like "was," "had," "made," "got," "went," "said" and replace at least 50% of them with more specific alternatives
* "He was broke" becomes "he had nothing" or "the money was gone" or "his accounts sat empty"
* "She said" becomes "she admitted," "she put it," "her words were," "she told reporters," etc.
* "He made films" becomes "he appeared in," "he starred in," "the studios put him in," etc.

**TRANSITION UPGRADE REQUIREMENT**
* Remove generic transitions like "But," "And," "So," "Then," "After that"
* Replace with conversational connectors: "and that's when," "which meant," "but here's the thing," "the result was," "what nobody expected," "and this is where it gets worse," "that changed when," "the problem was," "none of that mattered because"
* Each section must contain at least 3 upgraded transitions

**FACT REPOSITIONING**
* Take at least one key statistic or date per section and move it to a different position in the sentence for emphasis
* Instead of "He died in 1956 with only $2,900" try "When he died in 1956, everything he owned added up to $2,900" or "$2,900. That's what the man who created Dracula had left when he died in 1956"

### 8. SELF-CHECK BEFORE SUBMITTING
Before providing your final script, verify:

* No paragraph has more than 2 sentences starting with the same word
* Every section has at least 3 combined sentences (short sentences merged into longer flowing ones)
* Every paragraph has varied sentence lengths (mix of short and long)
* At least 50% of "was/had/made/got/said" verbs have been replaced
* Each section contains at least 3 upgraded conversational transitions
* At least one statistic per section has been repositioned for emphasis
* The script sounds noticeably different when read aloud, not just lightly edited

If any of these checks fail, go back and revise before submitting.

OUTPUT:
Provide the full rewritten script with no commentary or explanations. Just the script. The rewritten version should be noticeably different from the original in rhythm, sentence structure, and word choice while preserving all facts and the same section order. script format

---

## How Claude Code runs this for FE
- Part 1 research uses WebSearch, cites sources and dates, and is saved as `research_<topic>.md`.
- After Part 3, for the FE build: add the [CLIP], [FE CARD], [MG: ...] (motion graphics, see CLAUDE.md "Motion graphics") and [LET IT PLAY] markers to a separate copy. Use MG graphics for stats, quotes, posts, name intros, face-offs, word slams and timelines. The TTS version has no markers and no section headers.
- Defaults unless the user says otherwise: channel style = mix of documentary / educational / entertainment / nostalgia; length 20 minutes.
