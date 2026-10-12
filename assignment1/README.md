# DHG502 — Assignment 1

**What collocations of two kings, 夫差 and 勾践, reveal in the *Wu Yue Chunqiu*.**

This folder contains the data, the analysis scripts and the results used for the
Assignment-1 report (`report.md` / `report.pdf`).

---

## Research question

Does an automated **collocation analysis** of the two central rulers of the
*Wu Yue Chunqiu* — **勾践** (king of Yue) and **夫差** (king of Wu) — show that the
text characterises them differently? Specifically: (1) which words are
*statistically significant* collocates of each name, (2) where the *frequency*
ranking and the *significance/strength* ranking disagree, and (3) what the two
collocational profiles imply about the images of the two kings.

## Source

- **Text:** 趙曄 (Zhao Ye), 《吳越春秋》 (*Wu Yue Chunqiu*), 後漢 (Eastern Han),
  10 卷, c. 38,700 Chinese characters.
- **Rights:** public domain. The author died in the 1st–2nd century CE; the
  digital file is a plain-text transcription, not a copyrighted critical edition.
- **Where it came from:** the plain-text edition in the 殆知閣古代文獻庫 (Daizhige
  corpus), GitHub repository
  [`garychowcmu/daizhigev20`](https://github.com/garychowcmu/daizhigev20),
  path `史藏/载记/吴越春秋.txt`, downloaded via the jsDelivr mirror on 2026-09-18.
  Copy kept at [`data/吴越春秋.txt`](data/吴越春秋.txt).
- **Part used:** the **whole text** (all ten 卷). Nothing was selected or omitted;
  the corpus after cleaning is **2,470 sentences / 23,308 word tokens / 9,200 word
  types**. The 卷 headings and the running head are removed, and one OCR gap is
  repaired (`计●` → `计然`).

## Files

| File | What it is |
| --- | --- |
| `data/吴越春秋.txt` | the source text (plain text, UTF-8, 10 卷) |
| `data/data.txt` | the analysis corpus: jieba-segmented, one sentence per line, words space-separated (produced by `collocation.py`) |
| `collocation.py` | cleans + segments the text; corpus-level collocation statistics |
| `goujian_collocates.py` | significant collocates of **勾践** + HTML |
| `compare_rulers.py` | collocates of **夫差** and **勾践**, side-by-side + comparison HTML |
| `concordances.py` | KWIC concordance lines for every collocate discussed in the report |
| `collocation_results.txt` | run 1: corpus-level bigram/trigram tables (`collocation.py`) |
| `goujian_collocates.txt` / `.html` | run 2: collocates of 勾践 |
| `compare_rulers.txt` / `.html` | run 3: 夫差 vs 勾践 comparison |
| `concordances.txt` | run 4: concordance lines (evidence for the close readings) |
| `report.md` / `report.pdf` | the report (1,000–1,500 words, English) |
| `AI-USE.md` | AI-use statement (course requirement) |
| `requirements.txt` | Python dependencies |

## How to run

From **inside this `assignment1/` folder**:

```bash
pip install -r requirements.txt

python3 collocation.py         # -> data/data.txt, collocation_results.txt
python3 goujian_collocates.py  # -> goujian_collocates.txt, .html
python3 compare_rulers.py      # -> compare_rulers.txt, .html
python3 concordances.py        # -> concordances.txt
```

All scripts are deterministic (fixed corpus, no random seeds). Re-running them
reproduces every number in the report.

## Method in one line

`find_collocates` from **qhchina** (`method="window"`, `horizon=5`); for each
candidate a 2×2 contingency table is tested with a one-sided **Fisher exact**
test and Benjamini–Hochberg FDR; function words are removed and only raw
`p < 0.05` is kept. Strength is reported separately with **logDice** and **MI**,
because p-values measure *reliability*, not *strength*.

## Open the comparison page

`compare_rulers.html` (open in a browser) shows the two rulers' significant
collocates side by side; the two lists share **no** significant collocate.
