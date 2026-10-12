# AI-USE.md

**Course / assignment:** DHG502 — Assignment 1 (collocation analysis of *Wu Yue
Chunqiu*)
**Author:** Eric Li 李雨桐 (GitHub: Olipias)
**Date:** 2026-10-12

This file records how generative-AI tools were used for this submission, as
required. The assignment states that AI may be used for *code and
troubleshooting*; the prose of the report is the author's own, with AI used only
for language correction.

---

## 1. AI tools and models used

| Tool | Model | How it was used |
| --- | --- | --- |
| **opencode** (terminal coding agent, <https://opencode.ai>) | **`deepseek/deepseek-flash`** | Writing and debugging the Python analysis scripts, installing/verifying dependencies, running the collocation queries, generating the HTML pages, and grammar-editing the report draft. |

No other generative-AI tool was used for this assignment. **No LLM API is called
inside the analysis pipeline**: once written, the scripts run offline and the only
external packages they use are `jieba` and `qhchina` (both ordinary Python
libraries, not AI services). The "cleaning" of the text was performed by ordinary
regular-expression code that the agent wrote, not by an LLM at run time.

## 2. Tasks for which AI was used

1. **Text preparation.** The agent wrote the cleaning/segmentation script
   (`collocation.py`): it strips the running head and the ten 卷 headings,
   deletes private-use OCR glyphs, repairs the `计● → 计然` gap, splits sentences
   on ．？！, and segments each sentence with `jieba` (plus a custom name
   dictionary), writing one sentence per line to `data/data.txt`.
2. **Analysis code.** The agent wrote `goujian_collocates.py` and
   `compare_rulers.py`, which call `find_collocates` (from `qhchina`) with the
   window method and print the 2×2 contingency tables, Fisher p-values, FDR
   adjustment and association measures.
3. **Debugging / troubleshooting.** It diagnosed the chapter-heading bug (see §4),
   fixed relative paths after the repository was reorganised, and helped install
   `jieba` and `qhchina` in an environment without `pip`.
4. **Presentation.** It generated the two HTML pages (`goujian_collocates.html`,
   `compare_rulers.html`) from the results and produced the concordance file
   (`concordances.py`).
5. **Language editing.** It corrected grammar, spelling and punctuation in the
   report draft written by the author (see §4), and formatted the reference.
6. **Repository housekeeping.** git commands, `requirements.txt`, `README.md` and
   this file.

## 3. Representative prompts / session excerpts

Verbatim instructions given to the agent (English/Chinese as typed), with the
kind of output produced:

- > "for the collocation file in week4: use 吴越春秋.txt to do collocation
  > analysis. but first plz split the text into words using jieba, then save the
  > file as data.txt, one line per sentence, each separated by space."
  → produced the `jieba` segmentation pipeline and `data.txt`.

- > "use find_collocates from qhchina.analytics.collocations.find_collocates,
  > find me the collocations' statistically significance of the word '勾践'"
  → produced the first `find_collocates` run for 勾践 (window method).

- > "把搭配词里像'从''不''也'这类连接词去掉，再把 p-value<0.05 的也去掉"
  → added the function-word stoplist and the p-value filter to the script.

- > "要不再做一个关于夫差的搭配词查询，然后比较这两个国君在这本书里的形象"
  → produced `compare_rulers.py` and the 夫差-vs-勾践 comparison page.

- > "前面找到的搭配词里有没有显著性和强度这两个指标相矛盾的情况"
  → the agent tabulated the two rankings and identified 役 vs 范蠡.

- > "用这个 pdf 替换掉你生成的那个 pdf 文件并 push"
  → replaced `report.pdf` and pushed (the agent also flagged a possible typo,
  "a earch", which the author then fixed).

## 4. Important changes made by the author

- **Research question and target words.** The author chose 勾践 and 夫差 and the
  comparative framing (the agent did not pick the topic).
- **Method decisions.** Window method with `horizon = 5`, the `obs_local ≥ 2`
  filter, the choice to remove function words, and keeping only raw p < 0.05 were
  the author's decisions.
- **Author's own code edits.** The author wrote and edited the report itself
  (`report.md` / `report.pdf`); the agent only corrected grammar and typos. In
  particular the author's phrase "cleaned by an LLM agent" was kept, and the
  author rewrote the sentence that now cites Pines (2022).
- **Bug discovered and fixed.** An early run left some 卷 headings
  (`卷第七勾践入臣外传`) in the corpus, which produced the spurious collocates
  卷 / 外传; the author and agent fixed the cleaning rule and re-ran.
- **Repository decisions.** Moving the paper into `assignment1/`, renaming
  `week4 → assignment1`, removing the `.docx`/`.pptx` from the public repo, and
  which reference PDFs NOT to publish (copyright) were decided by the author.

## 5. How the output was checked

- **Against the primary text.** Every collocate discussed in the report was read
  back in context in `concordances.txt` (the KWIC lines), to confirm the claimed
  phrase really occurs (e.g. `东海役臣勾践`, `勾践復問范蠡曰可伐矣`, `夫差北伐齊`).
- **Re-running.** All scripts were re-run after the repository reorganisation and
  produced the same numbers; earlier runs were compared to see what changed
  (headings removed; stopwords reducing the number of tests).
- **Internal consistency.** The `obs_local`, p-values and logDice quoted in
  `report.md` were spot-checked against `goujian_collocates.txt`,
  `compare_rulers.txt` and `collocation_results.txt`.
- **Statements, not just statistics.** Each interpretive claim (e.g. "显著性与
  强度不一致") was verified by reading the concordance lines, since collocations
  alone cannot show meaning.
- **Citation.** The Pines (2022) reference was checked against the source PDF
  (`Early China` 45, pp. 375–412).

## 6. Declaration

AI was used for code, troubleshooting, and proofreading, as permitted by the
assignment. The analysis pipeline is deterministic and reproducible from
`data/`; the research question, the argument of the report, and the final
wording are the author's responsibility.
