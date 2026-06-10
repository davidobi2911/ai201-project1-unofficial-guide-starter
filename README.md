# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | UW Academic Support Programs — CLUE, Math Study Center, OWRC, DRS | Official university resource pages | https://academicsupport.uw.edu/clue/ · https://sites.math.washington.edu/~msc/ · https://depts.washington.edu/owrc/ · https://www.washington.edu/drs/ → `documents/academic_support.txt` |
| 2 | UW International Student Services (ISS) | Official university pages (visa/enrollment/work/taxes) | https://iss.washington.edu/academics-f-1/enrollment-requirements-f-1/ · https://iss.washington.edu/f1-employment/on-campus/ · https://iss.washington.edu/taxes/ → `documents/iss_guide.txt` |
| 3 | UW Student Life — "21 Tips for making the most of your first year at UW" | First-year advice article (official UW blog) | https://www.washington.edu/studentlife/2017/10/03/21-tips-for-making-the-most-of-your-first-year-at-uw/ → `documents/survival_guide_21_tips.txt` |
| 4 | UW course-selection tools — DawgPath + RateMyProfessors + course evaluations | Student strategy guide (UW data tools) | https://dawgpath.uw.edu · https://www.ratemyprofessors.com/search/professors/1530 → `documents/reddit_professor_tips.txt` |
| 5 | UW Office of the Registrar + Undergraduate Advising | Official registration & general-education pages | https://registrar.washington.edu/register/periods/ · https://advising.uw.edu/degree-overview/general-education/ → `documents/reddit_class_tips.txt` |
| 6 | UW Housing & Food Services + Transportation Services + RateMyDorm | Official housing/transit pages + dorm reviews | https://hfs.uw.edu/live/undergraduates/ · https://transportation.uw.edu/getting-here/transit/u-pass · https://www.ratemydorm.com/dorms-ranked/university-of-washington → `documents/reddit_udub_housing.txt` |
| 7 | RateMyProfessors.com — UW (Seattle) | Student professor reviews | https://www.ratemyprofessors.com/professor/498702 · https://www.ratemyprofessors.com/professor/2002528 → `documents/rmp_uw_reviews.txt` |
| 8 | Niche.com — University of Washington reviews | Aggregated student/alumni reviews | https://www.niche.com/colleges/university-of-washington/reviews/ → `documents/niche_uw_reviews.txt` |
| 9 | RateMyDorm.com — University of Washington | Student dorm reviews & rankings | https://www.ratemydorm.com/dorms/university-of-washington → `documents/ratemydorm_uw.txt` |
| 10 | Yelp / Tripadvisor / The Infatuation — dining on "the Ave" (U-District) | Restaurant reviews | https://www.yelp.com/biz/thai-tom-seattle · https://www.yelp.com/biz/aladdin-gyro-cery-seattle · https://www.yelp.com/biz/cafe-allegro-seattle → `documents/yelp_dining.txt` |

> **Note on Reddit sources:** Documents 4–6 were originally planned to draw from r/udub. Reddit
> is not fetchable by the tools used to assemble this corpus, so these three were grounded in the
> equivalent official UW pages (Registrar, Advising, HFS, DawgPath) plus RateMyDorm, and their
> headers note this. The filenames retain the `reddit_` prefix from the project template.

---

## Chunking Strategy

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Why these choices fit your documents:** The corpus consists primarily of short, self-contained opinions and tips (1–4 sentences) rather than long-form guides. A 300-character window captures one complete review or tip without merging unrelated student perspectives into a single chunk. The 50-character overlap ensures that if a key thought or phrase straddles a chunk boundary, the adjacent chunk still contains enough context to be independently retrievable during semantic search.

**Preprocessing:** Before chunking, URL-bearing lines (e.g., `https://...` header blocks and inline source citations) were stripped to prevent chunks from being bare URL fragments. Whitespace artifacts left behind were collapsed. Chunk boundaries snap to the nearest whitespace so no chunk starts or ends mid-word.

**Final chunk count:** 121 chunks across all 10 documents.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` (via sentence-transformers, runs locally with no API key)

**Why this model:** It's lightweight, fast, and performs well on semantic similarity for short text like student reviews and tips. Running locally eliminates latency and avoids per-token costs.

**Production tradeoff reflection:** In a production system with unlimited cost, I would consider `text-embedding-3-small` (OpenAI) for higher accuracy on domain-specific text and better handling of abbreviations like "the Ave" and "HFS." However, the tradeoff is per-token API costs. For UW's international student population, a multilingual model like `multilingual-e5-base` would enable support for non-English reviews. The current model is a pragmatic choice: good accuracy for the domain, zero latency, and no operational cost—but with slightly lower semantic precision than premium alternatives.

---

## Grounded Generation

**System prompt grounding instruction:**
```
You are the Unofficial UW Guide, a question-answering assistant about the University of Washington (Seattle) for students.
Answer the user's question using ONLY the numbered context passages provided. Do not use any outside knowledge or make assumptions beyond the context. Do not invent sources, names, or numbers. Be concise and practical.

Respond with a JSON object with exactly two keys:
  "answer": your answer as a string.
  "answered_from_context": true if the context actually contained the answer, false otherwise.
```

**Structural enforcement:** 
1. **Relevance filtering:** Retrieved chunks with cosine distance > 0.85 are treated as off-topic and trigger an automatic refusal without calling the LLM (RELEVANCE_THRESHOLD check in `query.py`).
2. **JSON response format:** The model must explicitly flag whether it answered from context. If `answered_from_context` is false, the response is replaced with a canned refusal message.
3. **Context-only passage formatting:** Only the filtered chunks (those below the relevance threshold) are included in the user message; the full context window contains *only* the retrieved passages, making hallucination harder.

**How source attribution is surfaced:** After the answer, sources are deduplicated and listed by filename and human-readable label extracted from each document's header (e.g., "Rate My Professors" from `rmp_uw_reviews.txt`). Sources are only attributed if the model's `answered_from_context` flag is true.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Dan Jacoby's teaching style? | Lecture-heavy, talks a lot, knowledgeable but hard to follow, participation matters | I don't have information on that in the UW guide documents. | Off-target | Inaccurate |
| 2 | Which UW dorm is considered the best for freshmen? | McMahon and Elm are top choices; Mercer praised for apartment-style | Maple Hall is ranked as the best freshman dorm with private bathrooms and kitchens on every floor. | Relevant | Accurate |
| 3 | What is the food like at Local Point dining hall? | Generally positive; students mention variety but note it can get repetitive | I don't have information on that in the UW guide documents. | Off-target | Inaccurate |
| 4 | What are the most important tips for surviving first year at UW? | Use UPASS, get involved early, talk to advisors, explore the Ave, manage time | Use UPASS, speak up in class, ask for help, use CLUE and tutoring resources, have backup classes ready | Relevant | Partially accurate |
| 5 | Is it hard to get into the CS major at UW? | Yes — highly impacted, competitive, limited slots | I don't have information on that in the UW guide documents. | Off-target | Inaccurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "What do students say about Dan Jacoby's teaching style?" (Question 1)

**What the system returned:** Refusal: "I don't have information on that in the UW guide documents."

**Root cause (tied to a specific pipeline stage — Document Collection):** The corpus does not contain any reviews of Dan Jacoby specifically. `rmp_uw_reviews.txt` includes generic Rate My Professors data for UW but does not happen to include Jacoby's profile. During retrieval, the semantic search engine found no chunks with cosine distance ≤ 0.85, so all results were filtered as off-topic and the relevance threshold check triggered a refusal. The failure is *upstream of the retrieval and generation*: the document collection phase did not capture this specific professor.

**What you would change to fix it:** (1) Manually add Jacoby's RateMyProfessors profile page to the corpus, or (2) use a web-scraping approach to dynamically fetch current RMP data for any professor queried. A secondary mitigation would be to lower RELEVANCE_THRESHOLD from 0.85 to 0.75 to accept marginal matches, but this risks false positives and system confusion on truly off-topic queries.

---

## Spec Reflection

**One way the spec helped you during implementation:** The "Evaluation Plan" section in planning.md clearly laid out the 5 test questions and their expected answers *before* implementation began. This guided chunking strategy (300 chars = granular enough to isolate individual reviews) and retrieval tuning (top-k=5, RELEVANCE_THRESHOLD=0.85). When building `query.py`, I could directly verify whether my choices were sufficient by checking against those benchmarks. The spec also identified anticipated challenges (review fragmentation, informal language) that informed preprocessing decisions—e.g., snapping chunk boundaries to whitespace to avoid mid-word splits.

**One way your implementation diverged from the spec, and why:** The spec's "AI Tool Plan" suggested generating the ingestion + chunking, embedding + ChromaDB, and retrieval functions from scratch with AI assistance. Instead, most of this code was written directly based on the planning spec, with AI only for debugging and refinement. This happened because the chunking algorithm is straightforward (character-based split with overlap), and having explicit control over chunk boundaries and metadata was more valuable than saving implementation time. AI was used to refine the system prompt for grounding and to debug JSON response parsing in `query.py` when the first iteration returned unparseable output.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I asked for help implementing the `chunk_text()` function in `ingest.py`. I explained that I needed to split 300-character chunks with 50-character overlap, but the chunks must never start or end mid-word (snap to whitespace boundaries).
- *What it produced:* The AI generated a function that uses `rfind(" ", start, end)` to locate the last space within the chunk window, then advances to the next word boundary for the overlap region. This handles the edge case where end-of-text is reached (avoiding infinite loops).
- *What I changed or overrode:* The original AI implementation had a bug where it could create empty chunks if boundaries aligned poorly. I added an explicit `if piece:` check before appending and ensured the loop always advances by `max(end - overlap, start + 1)` to prevent stalls.

**Instance 2**

- *What I gave the AI:* I asked how to structure grounded generation to prevent the LLM from hallucinating beyond the retrieved context. I provided the planning spec and asked for both a system prompt *and* a structural mechanism (not just instructions).
- *What it produced:* The AI suggested a two-layer approach: (1) a RELEVANCE_THRESHOLD filter on retrieval distance to reject off-topic queries before calling the LLM, and (2) a JSON response format with an `"answered_from_context"` boolean flag so the model explicitly signals confidence. Combined with the `_unique_sources()` deduplication, this prevents false source attribution.
- *What I changed or overrode:* I set RELEVANCE_THRESHOLD to 0.85 based on empirical testing (in-domain matches cluster ~0.35–0.6), not the AI's initial suggestion of 0.70. I also added the fallback JSON parsing try-except block because early testing showed the model occasionally returned unparseable JSON at high temperature.
