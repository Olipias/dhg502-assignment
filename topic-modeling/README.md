# Mao Zedong Selected Works — LDA analysis

## Data

Raw corpus (5.4 MB, 31,854 lines):

`https://raw.githubusercontent.com/mcjkurz/qhchina-data/main/corpora/%E9%80%89%E9%9B%86/%E6%AF%9B%E6%B3%BD%E4%B8%9C%E9%80%89%E9%9B%86.txt`

The file contains volumes 1–5 plus the unofficial 静火 editions of volumes 6–7.

## Method

1. **Document segmentation.** An article date is a line beginning with `（` and a
   Chinese-numeral year, e.g. `（一九二五年十二月一日）`. The title is
   reconstructed from the lines above it. In this edition the boundary before a
   title is five blank lines; title lines themselves may be separated by one or
   two blank lines. Subsection dates (`序`, `跋`, `引言`, `结论`, dated
   subsections, etc.) are excluded.
2. **Footnote removal.** The body is cut at the `注　　释` heading. Inline
   numeric markers such as `〔12〕` are removed.
3. **Tokenization.** `jieba.lcut`, keeping tokens of two or more characters.
   Stopwords are removed with `qhchina.load_stopwords("zh_sim")`. Tokens with no
   Chinese character (pure punctuation/numbers) are discarded.
4. **Length filter.** Documents with fewer than 100 tokens after cleaning are
   dropped.
5. **Topic model.** `qhchina.analytics.topicmodels.LDAGibbsSampler` with
   `n_topics=10`, `iterations=200`, `random_state=42`, `min_word_count=5`,
   `min_word_length=2`.

The appendix 《关于若干历史问题的决议》 is retained as one document because it
has a title and date. It appears out of chronological order in volume 3; source
order is preserved.

## Run

```bash
uv venv --python 3.12 .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python analyze_mao.py
```

If the raw file is absent:

```bash
.venv/bin/python analyze_mao.py --download
```

## Outputs

- `output/documents.tsv` — 388 parsed documents with volume, year, date, title,
  token count, and whether the document entered the LDA.
- `output/lda_topics.txt` — summary, dropped-document list, and the 10 topics
  with their top 10 words and two most typical documents.
- `output/topics_by_decade.png` — stacked bar chart of the mean topic
  proportion in each decade; the legend gives each topic number and its top 3
  words.
- `output/topics_by_decade.tsv` — the values plotted in the chart.
- `output/report.html` — a self-contained HTML report of all findings, with the
  chart embedded as base64.

## Result summary

- Parsed documents: **388**
- Documents with at least 100 tokens: **350**
- Dropped for length: **38** (mostly short telegrams, slogans, and instructions)
- Vocabulary after `min_word_count=5`: **7,586**
