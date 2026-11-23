# Assignment 2 — Lin Huiyin Text Corpus

This folder contains the group's Part 1 submission: a UTF-8 plain-text corpus of
writings by and about 林徽因 Lin Huiyin (1904–1955), together with a source list.

## Quick facts

- **Figure:** 林徽因 Lin Huiyin
- **Files:** 11 `.txt` files in `texts/`
- **Total size:** **1,189,674 characters** (1,171,569 excluding whitespace; 1,017,510 Chinese characters)
- **Target:** at least 1,000,000 characters
- **Encoding:** UTF-8 (no BOM)
- **Language:** Simplified Chinese
- **Source list:** `SOURCE_LIST.md`
- **Machine-readable metadata:** `metadata.csv`

## Directory contents

```
assignment2_linhuiyin/
├── README.md                 ← this file
├── SOURCE_LIST.md            ← required source list, with editions and URLs
├── metadata.csv              ← one row per text file
├── texts/                    ← the 11 files to submit
│   ├── 01_lin_huiyin_wenji_235k.txt
│   ├── 02_lin_huiyin_zhuan_linshan.txt
│   ├── 03_liang_sicheng_jianzhu_20jiang.txt
│   ├── 04_liang_sicheng_zhongguo_jianzhushi.txt
│   ├── 05_lin_huiyin_jianzhu_wencui.txt
│   ├── 06_liang_qichao_jiashu.txt
│   ├── 07_liang_sicheng_chuantong_jianzhu.txt
│   ├── 08_lin_huiyin_shuxinji_qimao.txt
│   ├── 09_lin_huiyin_jubenji_qimao.txt
│   ├── 10_lin_huiyin_zhongguo_gudai_jianzhukao.txt
│   └── 11_lin_huiyin_sanwen_xiaoshuo_qimao.txt
├── raw/                      ← working copies and download evidence (not for submission)
└── notes/                    ← scripts and working notes (not for submission)
```

## What is in the corpus

1. **Lin Huiyin's own writing** — poems, essays, short stories, the complete play
   《梅真同他们》, selected letters, and architectural essays (files 01, 05, 08,
   09, 10, 11).
2. **A biography** — 林杉's 《林徽因传：一代才女的心路历程》 (file 02), used for
   narrative context and clearly marked as secondary literature.
3. **Family letters** — 梁启超's letters to his children, including 梁思成 and
   林徽因 (file 06).
4. **Liang Sicheng's architectural writings** — the technical and historical
   context of the couple's joint work (files 03, 04, 07).

## How the texts were prepared

- All files were converted to UTF-8 and stripped of website navigation,
  advertisements and watermarks.
- The 番茄小说 texts use a subset font that remaps characters to private-use
  code points. The mapping was recovered by matching glyphs against Source Han
  Sans SC and then checked against independent editions.
- Chapters that were locked by a platform are **listed as omitted** in
  `SOURCE_LIST.md`; they are not silently replaced with invented text.
- Truncated previews, one mislabeled chapter, and website navigation pages were
  removed. The reasons are recorded in `SOURCE_LIST.md`.

## Verification

The group checked several works across independent editions:

| Work | Editions compared | Result |
|---|---|---|
| 《山西通信》 | file 01 vs. 番茄 edition | ≈ 0.98 similarity; differences are punctuation |
| 《窗子以外》 | file 01 vs. 番茄 edition | ≈ 0.99 similarity |
| 《那一晚》 | file 01 vs. 番茄 edition | ≈ 0.97–0.99 similarity |
| 《笑》 | file 01 vs. 番茄 edition | ≈ 0.97–0.99 similarity |
| Letters to 沈从文 / 胡适 | file 08 vs. file 01 | same text, minor punctuation variants |
| 《你是人间的四月天》 | file 01 vs. file 11 | same text, punctuation variants |

The remaining `□` marks inside stone inscriptions are original lacunae in the
inscriptions, not decoding failures.

## For the in-class RAG exercise

Suggested question types:

- **Factual:** Where was Lin Huiyin born? When did she die? Where did she study?
- **Architectural:** What did she and Liang Sicheng argue about the preservation
  of Beijing's city wall? What is “建筑意”?
- **Literary:** Who is the addressee of 《你是人间的四月天》? What is the plot of
  《九十九度中》?
- **Source-critical:** Compare the biography's account of an event with Lin
  Huiyin's own letter about it. Which is more reliable?

Because the corpus contains multiple editions, a good test is to ask the same
question and see whether the system retrieves the same passage from different
files. If the editions disagree, check the print source before trusting the
answer.

## Files added for the paper

- `Lin_Huiyin_RAG_Essay.docx` — the paper (Word version).
- `Lin_Huiyin_RAG_Essay.pdf` — the paper (PDF version).
- `AI-USE.md` — AI-use statement for the paper.
- `error_log.csv` — error log for the two exported HistFig conversations.
- `林徽因 - 你最喜欢的诗歌是什么.md` — exported conversation A (simple search).
- `林徽因 - 你最心爱的建筑是哪个.md` — exported conversation B (agent / research search).

## Submission

Submit the contents of `texts/` (the eleven `.txt` files) together with
`SOURCE_LIST.md` through Moodle. The `raw/` and `notes/` folders are working
material and need not be submitted.
