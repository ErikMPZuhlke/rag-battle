# Workshop Introduction — Slide Deck (13 slides)

This document is the source content for an HTML slide deck (built next). Every
slide has three parts: **on-slide text** (what's rendered), **speaker notes**
(what the presenter says), and an **image prompt** (for an image-generation
model). All facts are pulled verbatim from [WORKSHOP_BRIEF.md](WORKSHOP_BRIEF.md),
[PARTICIPANT_RULES.md](PARTICIPANT_RULES.md), and the [README](../README.md).

## Shared visual style (apply to every image prompt below)

Consistent world so the deck feels like one coherent story, not 13 random
images:

- **Format**: 16:9, high readability at presentation distance, board-friendly.
- **Metaphor**: Acme Cloud "battle arena" — a semi-isometric competition floor
  where teams (small glowing pods/stations) work on a shared assembly line
  that turns raw documents into answers.
- **Palette/lighting**: dark-to-light gradient left→right (moody navy/charcoal
  on the left, warming to bright cyan/amber on the right) signaling
  progress from "raw problem" to "polished result."
- **Overlay**: faint engineering-blueprint grid lines, schematic annotations,
  and small labeled callouts — like a technical diagram, not a cartoon.
- **Typography in-image**: minimal, only short labels/titles; all detailed
  text lives on the slide itself, not baked into the image.
- **Recurring icons**: document stack (corpus), funnel (retrieval), chat
  bubble with citation tag (answer + sources), gauge/meter (budget), trophy
  (leaderboard).

---

## Slide 1 — Title

**On-slide text**
- RAG Battle Royale
- Build the best Acme Cloud knowledge assistant
- [team/event names, date — placeholder]

**Speaker notes**
Welcome everyone — today you're not attending a lecture, you're entering a
competition. In the next two hours you'll take a working but mediocre RAG
system and turn it into the best knowledge assistant you can build.

**Image prompt**
Create a 16:9 title slide illustration: a glowing arena floor at night seen
from a high semi-isometric angle, dark navy background with a faint
engineering-blueprint grid. In the center, a bold architectural sign reads
"RAG BATTLE ROYALE" rendered as illuminated signage. Around the arena,
several small glass-walled team pods glow with distinct accent colors, each
containing a miniature pipeline of icons (documents → funnel → chat bubble).
Left side of the image is darker/moodier, right side brighter with warm
cyan-amber light spilling out, hinting at the transformation to come. No
body text other than the title signage. Cinematic, technical, board-friendly.

---

## Slide 2 — Mission

**On-slide text**
- You are the new AI team at Acme Corp
- Acme Cloud's internal knowledge base has grown — engineers can't find
  accurate answers fast
- Your mission: build an AI knowledge assistant that actually works
- Highest score wins

**Speaker notes**
Picture yourselves as a newly formed AI team inside Acme Corp. Support and
engineering teams are drowning in internal docs and can't get quick, correct
answers. That's the problem you're hired to solve today — and you're
competing against every other team doing the same job.

**Image prompt**
16:9 semi-isometric illustration: a sprawling corporate "knowledge city"
made of tall document-stack towers (labeled faintly: engineering, security,
product, people, operations) with tangled cables and question-mark clouds
hovering above confused stick-figure engineers at their desks, dark
blueprint-overlay style on the left. On the right, a small confident team
of 4-5 glowing avatar silhouettes stands at a control console with a clean
holographic interface, calmly organizing the chaos into a single stream of
light flowing toward a "?" turning into a "✓". Dark-to-light gradient
left-to-right. Minimal text, just faint labels on the towers.

---

## Slide 3 — The API contract

**On-slide text**
- One endpoint: `POST /ask`
- Request: `{ "question": "..." }`
- Response: `{ "answer": "...", "sources": [{ "document", "section" }] }`
- This contract never changes — rebuild anything behind it

**Speaker notes**
No matter what you change internally — retrieval, prompts, reranking — this
is the one contract that must stay stable: you take a question in, you
return an answer plus the sources that back it up.

**Image prompt**
16:9 technical schematic illustration, blueprint style on dark background:
a single labeled input pipe on the left marked "POST /ask" feeding a glowing
JSON packet "{ question }" into a sealed black-box module in the center
labeled "YOUR SYSTEM" (customizable/interchangeable, shown with dashed
edit-lines and gear icons to signal it can be rebuilt). On the right, a
clean output pipe emits a glowing JSON packet labeled "{ answer, sources[] }"
attaching small document-tag icons. Dark-to-light gradient left to right.
Precise engineering-diagram feel, arrows showing one-directional flow,
minimal but legible in-image labels.

---

## Slide 4 — The corpus

**On-slide text**
- ~40 markdown documents, shared by every team
- Five domains: Engineering · Security · Product · People · Operations
- `data/knowledge-base/` — read-only, identical for everyone
- Nobody gets an advantage from the data — only from what you build

**Speaker notes**
Everyone starts from the exact same forty-ish documents split across five
domains — engineering, security, product, people, and operations. The
corpus is frozen and read-only; your edge comes entirely from your
retrieval and generation pipeline, not from the data.

**Image prompt**
16:9 semi-isometric illustration of five labeled document-stack towers of
equal height arranged in a row on a factory floor, each tower a different
accent color and icon: "Engineering" (gear), "Security" (shield), "Product"
(box), "People" (person), "Operations" (dial/gauge). Each stack sits behind
a faint glass case with a small padlock icon to signal "read-only, shared
by all teams." Blueprint grid overlay, dark-to-light gradient left to
right, subtle glowing conveyor belt beneath all five towers feeding into a
single funnel toward the right edge of the frame. Board-friendly, minimal
text (just the five domain labels).

---

## Slide 5 — The baseline

**On-slide text**
- You start from a working baseline RAG system
- Intentionally mediocre — roughly 65–70% quality
- Same baseline, same corpus, same rules for every team
- Your job: make it meaningfully better

**Speaker notes**
We're giving every team the exact same starting point — a baseline that
works but is deliberately unimpressive, scoring around 65 to 70 percent.
That's the floor. The only question is how much higher you can push it in
the time you have.

**Image prompt**
16:9 semi-isometric illustration of a plain, slightly rusty grey machine in
the center labeled "BASELINE" with a small gauge dial reading "~65-70%" in
dim amber light, positioned on the darker/left portion of the frame. Faint
dashed arrows point from the machine toward the right side of the image,
where a brighter, upgraded, glowing version of the same machine silhouette
is sketched in blueprint outline (not yet built) with a gauge dial trending
toward green/high values, symbolizing the improvement path. Engineering
blueprint overlay throughout, dark-to-light gradient, minimal text limited
to the two gauge readouts.

---

## Slide 6 — What you can change

**On-slide text**
- Chunking & embeddings
- Retrieval: top-k, metadata filtering, hybrid search, reranking
- Query rewriting & context compression
- Prompts, context formatting, citation strategy
- Caching — even replace the whole architecture, if `POST /ask` still holds

**Speaker notes**
Almost everything under `app/` is fair game: how you chunk and embed
documents, how you retrieve and rerank, how you prompt the model, how you
format citations, even caching strategies. You can rip out the entire
baseline architecture as long as the API contract stays intact.

**Image prompt**
16:9 semi-isometric illustration of an open control panel / workbench
covered in interchangeable glowing modules the viewer can "swap in": labeled
tiles for "Chunking", "Embeddings", "Retrieval / Rerank", "Query Rewriting",
"Prompting", "Citations", "Caching" — each tile shown as a hexagonal glowing
block that can slot into a central chassis. A pair of holographic hands
(engineering blueprint style, dashed outline) hovers above, actively
rearranging tiles. Dark-to-light gradient left to right, blueprint grid
overlay, tiles brighten in color the closer to the right edge. Minimal
text limited to the tile labels.

---

## Slide 7 — What you can't do

**On-slide text**
- ❌ Modify anything under `data/knowledge-base/`
- ❌ Hard-code answers to specific questions
- ❌ Access or guess the hidden evaluation questions
- ❌ Send the entire corpus to the LLM every request
- ❌ Collaborate with other teams during the battle

**Speaker notes**
A short list of hard rules: the corpus is off-limits, no hard-coding
answers, no peeking at or guessing the hidden questions, no dumping the
whole corpus into every prompt, and no collaborating across teams. Break
these and your results don't count.

**Image prompt**
16:9 semi-isometric illustration in a stern, official blueprint style: a
red-outlined restricted zone in the center-left containing the document
towers from earlier, wrapped in glowing red warning tape with small icon
badges around it: a padlock crossed out ("no edits"), a magnifying glass
crossed out over a question mark ("no peeking"), a chat bubble crossed out
("no hard-coded answers"), a funnel overloaded and crossed out ("no full
corpus dump"), and two team pods connected by a crossed-out cable ("no
collusion"). Dark, high-contrast, mostly cool tones with red accent glow.
Minimal in-image text, icons should carry the meaning.

---

## Slide 8 — Budget constraints

**On-slide text**
- Every question is metered — no unlimited spending
- Max **3 LLM calls**
- Max **10 retrieval operations**
- Max **4,000 input tokens**
- Exceed any limit → `429 Budget Exceeded`

**Speaker notes**
Every single request runs against a hard budget: at most three LLM calls,
ten retrieval operations, and four thousand input tokens. Cross any of
those lines and the request is rejected with a 429. This forces real
engineering trade-offs instead of brute-forcing quality with unlimited
spend.

**Image prompt**
16:9 semi-isometric illustration of a glowing industrial dashboard with
three large circular gauge meters mounted side by side, each with a
red-lined maximum: gauge 1 labeled "LLM CALLS — max 3", gauge 2 labeled
"RETRIEVALS — max 10", gauge 3 labeled "INPUT TOKENS — max 4,000". Needles
sit near but under the red line, glowing amber-to-green. Behind the
dashboard, a small warning light labeled "429" flashes red, connected by a
dashed line to a needle that has crossed into the red zone on a faded
ghost/example gauge. Blueprint overlay, dark-to-light gradient, precise
technical-instrument-panel aesthetic.

---

## Slide 9 — Scoring

**On-slide text**
- Answer correctness — **50%**
- Retrieval quality — **20%**
- Groundedness — **15%**
- Citations — **10%**
- Latency — **5%**

**Speaker notes**
Here's exactly how you're scored: correctness is worth half the grade,
retrieval quality is twenty percent, groundedness fifteen, citations ten,
and latency the remaining five. Optimize accordingly — a fast but wrong
answer scores far worse than a slightly slower correct one.

**Image prompt**
16:9 illustration of a clean semi-isometric weighted balance/pie
instrument glowing on a dark blueprint background: a large horizontal bar
chart made of five stacked glowing blocks of decreasing size, left to
right, each labeled with a percentage and short name: "Correctness 50%"
(largest, brightest), "Retrieval 20%", "Groundedness 15%", "Citations 10%",
"Latency 5%" (smallest). Each block emits a soft glow proportional to its
size. Dark-to-light gradient background, precise technical chart aesthetic,
minimal supporting text beyond the five labels.

---

## Slide 10 — Agenda

**On-slide text**
- 0–10 min — Introduction + rules
- 10–20 min — Baseline demo
- 20–80 min — 🔥 Battle: build
- 80–90 min — Final testing / freeze
- 90–110 min — Hidden evaluation
- 110–120 min — Leaderboard + winners

**Speaker notes**
Here's how the next two hours break down: ten minutes of intro, ten minutes
watching the baseline in action, sixty minutes of heads-down building, ten
minutes to freeze and do final testing, twenty minutes of hidden
evaluation you won't see happening, and finally the leaderboard reveal.

**Image prompt**
16:9 semi-isometric illustration of a glowing horizontal timeline/conveyor
track running left to right across the frame, divided into six clearly
labeled segments of proportional width, each with a small icon: "Intro"
(megaphone), "Baseline Demo" (screen/play button), "Battle: Build" (hammer
and wrench, largest segment, brightest glow), "Freeze / Test" (checklist),
"Hidden Evaluation" (masked eye icon), "Leaderboard" (trophy). Dark-to-light
gradient left to right matching the timeline's progress. Blueprint grid
overlay, minimal text limited to segment labels and time ranges.

---

## Slide 11 — Winning levers

**On-slide text**
- Retrieval quality beats prompt cleverness — fix what you fetch first
- Say "I don't know" — the no-answer text beats a hallucination every time
- Cite precisely: `{ document, section }`, not just the file name
- Spend your budget on the highest-value call, not every call
- Test against the public questions constantly, not just at the end

**Speaker notes**
A few practical tips from past runs: most quality problems are retrieval
problems, not prompting problems — fix what you fetch before you fix how
you phrase it. When in doubt, say the documentation doesn't specify it;
that beats guessing every time. Cite precisely, spend your limited budget
wisely, and test continuously against the public questions instead of
waiting until the end.

**Image prompt**
16:9 semi-isometric illustration of a strategist's war-room table viewed
from above at an angle, glowing blueprint schematics laid out showing five
labeled strategy cards arranged like a hand of cards: "Fix Retrieval
First" (funnel icon), "Say 'I Don't Know'" (shield with question mark),
"Cite Precisely" (tag/label icon), "Spend Budget Wisely" (gauge icon),
"Test Continuously" (looping arrows icon). A glowing hand (dashed
blueprint-style) hovers over the cards as if choosing the next move.
Dark-to-light gradient, chess/strategy-game undertone, minimal text beyond
the five card titles.

---

## Slide 12 — Hidden evaluation & leaderboard

**On-slide text**
- Your system is frozen, then tested on questions you've never seen
- Same evaluator, same questions, for every team
- Scores roll up into a single leaderboard
- Highest score wins — no partial credit for effort

**Speaker notes**
Once the clock stops, your code is frozen and run against a hidden
question set nobody has seen — same questions, same evaluator, for every
team, so it's a level playing field. The results feed one shared
leaderboard, and whoever scores highest wins.

**Image prompt**
16:9 semi-isometric illustration of a sealed glass vault in the center
labeled "HIDDEN QUESTIONS" with a padlock icon, glowing faintly. Beams of
light travel from the vault into several identical evaluator machines (one
per team, shown as small glowing kiosks in a row), each machine outputting
a single glowing numeric score upward into a large rising leaderboard
podium/bar-chart on the right side of the frame, brightest and warmest
lighting concentrated there. Dark-to-light gradient left to right,
blueprint overlay, trophy icon glowing at the top of the tallest bar.
Minimal text limited to "HIDDEN QUESTIONS" and "LEADERBOARD".

---

## Slide 13 — Close

**On-slide text**
- The clock starts now
- Same corpus. Same rules. Same budget.
- Build the assistant Acme Cloud actually needs
- Good luck — may the best RAG win

**Speaker notes**
That's everything you need to know. Same corpus, same rules, same budget
for every team — from here it's all about what you build. Go build the
knowledge assistant Acme Cloud actually needs. Good luck, and let the
battle begin.

**Image prompt**
16:9 semi-isometric illustration of the same arena floor from the title
slide, now fully lit and warm (bright cyan-amber glow throughout, no more
dark/moody half), all team pods actively glowing and humming with
activity, small progress bars rising above each pod. A large illuminated
countdown/start banner overhead reads "GO". Confetti-like light particles
drift in the air. Blueprint overlay faded to a subtle background texture
rather than dominant, signaling readiness over analysis. Minimal text,
just the "GO" banner.
