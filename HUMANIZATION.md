# FE humanization rules (applies to every script, both versions)

From the user's guide "An Internal Breakdown for Script Writers". Goal: high perplexity, high burstiness, high complexity, which in practice means better writing.

## Targets (checked by `python3 script_metrics.py <script>`)
| Metric | Target |
|---|---|
| Sentence-length variation (CV) | ≥ 0.45 |
| Short sentences (<8 words) | ≥ 12% |
| Long sentences (>25 words) | ≥ 15% |
| Similar-length sentences in a row | ≤ 3 |
| Vocabulary diversity (MATTR, 50 words) | ≥ 0.72 |
| Stock AI words, ellipses, 1-2 word sentences | 0 |
| Questions | 2-3, and only direct viewer questions (Nov 17 rule) |
Plus `check_script.py` must print "Clean".

## How
- **Perplexity:** temporal anchors (real dates, event numbers), concrete verified details, less obvious word choices.
- **Burstiness:** mix 3-6 word sentences and fragments ("Nobody gave him a chance.", "A majority draw.") with 25-40 word ones. Break parallel structure.
- **Complexity:** fight-domain terms where accurate (takedown, sprawl, control time, significant strikes, corner stoppage, split decision); no hedging; a narrator with opinions (one clearly worded opinion line per section is allowed).
- **Admitted uncertainty, from the research only:** e.g. "His knockout total changes depending on which source you trust." Never invent personal experiences or sensory details.

## Where the guide and the TTS rules (SCRIPT_PROMPT.md Part 3) conflict, for ElevenLabs:
- Fragments are allowed at **3+ words**; no 1-2 word sentences.
- No ellipses and no em-dashes (the guide suggests them; they make ElevenLabs pause oddly). Use commas.
- No rhetorical questions. The only questions are the 2-3 direct viewer questions from the engagement rules; test how ElevenLabs reads them and rephrase if the intonation sounds off.
- Sentences may start with "And/So/But/Then" at most once or twice per script.
- Accuracy rules always win: no new facts during humanization.
