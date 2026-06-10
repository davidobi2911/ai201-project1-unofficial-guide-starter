# Planning: The UW Unofficial Guide

## Domain
This guide covers general student survival knowledge at the University of Washington (Seattle) — the kind of information that doesn't appear in official handbooks. It combines professor reviews, dorm experiences, dining opinions, housing tips, and first-year survival advice sourced entirely from students. This knowledge is valuable because it reflects real student experiences rather than curated university messaging, and it's hard to find in one place — currently scattered across Reddit, Rate My Professors, Niche, Yelp, and various blogs.

## Documents
| Filename | Source | Content |
|---|---|---|
| `rmp_uw_reviews.txt` | Rate My Professors | Student reviews of UW professors |
| `reddit_professor_tips.txt` | r/udub (Reddit) | Threads about professor and class recommendations |
| `reddit_class_tips.txt` | r/udub (Reddit) | Threads about registration, MyPlan, add codes |
| `niche_uw_reviews.txt` | Niche.com | General UW student reviews |
| `ratemydorm_uw.txt` | RateMyDorm.com | Student reviews of UW residence halls |
| `reddit_udub_housing.txt` | r/udub (Reddit) | Threads about dorms and off-campus housing |
| `yelp_dining.txt` | Yelp | Student reviews of UW dining locations |
| `academic_support.txt` | academicsupport.uw.edu | Official UW academic tips written for students |
| `survival_guide_21_tips.txt` | UW Student Life Blog | 21 tips for first-year UW students |
| `iss_guide.txt` | ISS UW Blog | Survival guide written by a UW senior |

## Chunking Strategy
**Chunk size:** 300 characters
**Overlap:** 50 characters

These documents are mostly short, opinion-based reviews (1–4 sentences each) rather than long-form guides. A 300-character chunk captures roughly one complete review or one coherent tip without merging unrelated opinions together. Overlap of 50 characters ensures that if a key thought spans a chunk boundary (e.g. a review that ends mid-sentence), the next chunk still includes enough context to be retrievable on its own. Larger chunks (e.g. 1000 characters) would merge multiple reviews into one embedding, making it harder to match a specific question to a specific opinion.

## Retrieval Approach
**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers (runs locally, no API key needed)
**Vector store:** ChromaDB (local)
**Top-k:** 5 chunks per query

Retrieving 5 chunks gives the LLM enough context to synthesize an answer from multiple student opinions without overwhelming it with loosely related content. Semantic search works here because student reviews use varied language to describe the same things — one student says "easy grader" and another says "never fails anyone," but both embed close to a query like "is this professor lenient?"

**Production tradeoffs to consider:**
- `text-embedding-3-small` (OpenAI) would offer better accuracy but costs money per token
- `multilingual-e5` would support non-English reviews, relevant for UW's international student population
- Local models like `all-MiniLM-L6-v2` have lower latency and no rate limits but slightly lower accuracy on domain-specific text

## Evaluation Plan
| # | Question | Expected Answer |
|---|---|---|
| 1 | What do students say about Dan Jacoby's teaching style? | Lecture-heavy, talks a lot, knowledgeable but hard to follow, participation matters |
| 2 | Which UW dorm is considered the best for freshmen? | McMahon and Elm are frequently cited as top choices; Mercer praised for apartment-style living |
| 3 | What is the food like at Local Point dining hall? | Generally positive; students mention variety but note it can get repetitive |
| 4 | What are the most important tips for surviving first year at UW? | Use UPASS, get involved early, talk to advisors, explore the Ave, manage time with a planner |
| 5 | Is it hard to get into the CS major at UW? | Yes — highly impacted, competitive, limited slots especially for transfers and non-direct admits |

## Anticipated Challenges
1. **Review fragmentation:** Short reviews chunked at 300 characters may split a student's opinion mid-thought, producing chunks that lack enough context to match specific queries accurately.
2. **Source bleed:** Documents cover overlapping topics (e.g. both `reddit_udub_housing.txt` and `ratemydorm_uw.txt` discuss dorms), so retrieval may return redundant chunks from different sources rather than diverse perspectives.
3. **Informal language:** Student slang and abbreviations (e.g. "the Ave," "HFS," "add code") may not embed well against more formal query phrasing.
4. **Outdated reviews:** Some RMP reviews are from 2014–2017 and may not reflect current teaching styles or policies.

## AI Tool Plan
| Pipeline Component | What I'll give the AI | What I expect it to produce |
|---|---|---|
| Ingestion + chunking | This planning.md (Documents + Chunking sections) + file list | A script that loads all 10 `.txt` files, cleans whitespace/artifacts, and splits into 300-char chunks with 50-char overlap |
| Embedding + ChromaDB | Chunking output + Retrieval Approach section + pipeline diagram | Code to embed chunks with `all-MiniLM-L6-v2` and store in ChromaDB with source metadata |
| Retrieval function | ChromaDB setup code + top-k value | A `retrieve(query, k=5)` function returning chunks and source filenames |
| Grounded generation | Retrieval function + grounding requirement + Groq model name | A prompt template and `ask(question)` function that passes chunks as context and returns answer + sources |
| Gradio UI | `ask()` function signature + desired input/output fields | A `app.py` with a question input, answer output, and sources output |

## Architecture

```
┌─────────────────────┐
│   10 .txt Documents  │
│ (RMP, Reddit, Niche, │
│  Yelp, Blogs, etc.)  │
└────────┬────────────┘
         │  load + clean
         ▼
┌─────────────────────┐
│   Chunking Pipeline  │
│  300 chars / 50 overlap│
│  (plain Python)      │
└────────┬────────────┘
         │  chunks + metadata
         ▼
┌─────────────────────┐
│     Embeddings       │
│  all-MiniLM-L6-v2   │
│ (sentence-transformers)│
└────────┬────────────┘
         │  vectors
         ▼
┌─────────────────────┐
│     Vector Store     │
│      ChromaDB        │
│   (local, on disk)   │
└────────┬────────────┘
         │  top-5 chunks
         ▼
┌─────────────────────┐
│  Grounded Generation │
│  Groq LLM            │
│ llama-3.3-70b        │
└────────┬────────────┘
         │  answer + sources
         ▼
┌─────────────────────┐
│     Gradio UI        │
│  Question → Answer   │
│  + Source Attribution│
└─────────────────────┘
```