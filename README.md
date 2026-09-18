# 吳越春秋 — 君臣关系 / 政治内容占比分析

**Name:** Olipias
**Course code:** DHG502
**One-sentence description:** I measured how much of the Han-dynasty historical
text 《吳越春秋》 (*Wu Yue Chunqiu*) is about the ruler–minister (君臣)
relationship and politics, rather than other topics, with a small keyword-based
Python script, and published the result as a web page.

## Source and citation

> 趙曄 (Zhao Ye), 《吳越春秋》 (*Wu Yue Chunqiu*), 後漢 (Eastern Han), 10 卷.
> Public domain. Plain-text edition from 殆知閣古代文獻庫 (Daizhige corpus),
> GitHub repository [`garychowcmu/daizhigev20`](https://github.com/garychowcmu/daizhigev20),
> path `史藏/载记/吴越春秋.txt`, downloaded via the jsDelivr mirror on 2026-09-18.

The text is public domain (author died in the 1st–2nd century CE; the digital
edition is a transcription, not a copyrighted critical edition).

## Files

| File | What it is |
| --- | --- |
| `吴越春秋.txt` | the source text (plain text, UTF-8, 10 卷, ~38,700 Chinese characters) |
| `analyze.py` | the analysis script (Python 3, standard library only) |
| `analysis_results.txt` | the full numeric results |
| `index.html` | a one-page presentation of the results (published via GitHub Pages) |
| `README.md` | this file |

## How to run

```bash
python3 analyze.py
```

It reads `吴越春秋.txt` and rewrites `analysis_results.txt` and `index.html`.

## What the code does

1. Loads the text, removes OCR filler, and splits it into the ten 卷 by their
   headings.
2. Splits each 卷 into sentences on the classical full stop `．` and on `？ ！`.
3. Tags every sentence with three small, explicit lexicons:
   * **RULER** — the sovereign: `君 / 王 / 孤 / 寡人 / 越王 / 吴王 / 阖闾 / 勾践 …`
   * **MINISTER** — officials and statesmen: `臣 / 大夫 / 相国 / 太宰 / 伍子胥 / 范蠡 / 文种 …`
   * **POLITY** — statecraft, war, diplomacy, rewards and punishments:
     `国 / 政 / 兵 / 战 / 伐 / 谏 / 赏 / 罚 …`
   and with a speech flag (contains `曰`, `「`, or `」`).
4. Puts each sentence in one of four buckets:
   * **君臣同现** — a RULER and a MINISTER word occur together (the relationship
     itself: advice, appointment, remonstrance, reward, execution);
   * **君臣言论** — direct speech by a ruler or a minister, without
     co-occurrence (the counterpart is often only implied);
   * **政治·其他** — a POLITY word, or merely a ruler/minister mention;
   * **其他** — none of the above (myth, geography, crafts, poems, personal
     narrative).
   *Political* = the first three buckets.
5. Counts character bigrams (classical Chinese has no word spacing), keyword
   frequencies, and mentions of people/offices, per 卷.

Every number is therefore a transparent keyword count, and the lexicons and
their limitations are printed in `analysis_results.txt` so a reader can check
plausibility instead of trusting a black box.

## Result

* **74.3 %** of sentences (and **80.8 %** of characters) are political; **25.7 %**
  are other.
* Only **16.5 %** show a strict ruler-and-minister co-occurrence; **21.3 %** are
  ruler/minister speech; **36.5 %** are other political context.
* The share rises across the book: the founding-myth chapters (卷第一 吳太伯,
  卷第六 越王無余) are the least political (~42–45 %), while the chapters on
  Goujian's return and the conquest of Wu (卷第八, 卷第十) are the most
  political (~80 %). This matches the shift of the narrative from Wu to Yue.

## Candidate analyses considered

Following the assignment, several possible analyses were weighed before
choosing one:

1. **Most frequent words** — done as a side product (top character bigrams),
   since the text has no word spaces.
2. **Named people / places / offices and their distribution across the text** —
   done for the main people and offices (section 6 of the results), because it
   directly shows the Wu → Yue structural shift.
3. **Extract the "treacherous officials" (奸臣)** — feasible, but this text
   marks Pibo 伯嚭 as 佞 rather than 奸, so a 奸-only query would have been
   misleading; it is treated inside the POLITY list (`佞`, `奸`).
4. **Ruler–minister relationship vs other content** — chosen as the main
   question; it is the theme of the book and can be operationalised cleanly
   with the three lexicons above.

## Notes

* No API key is stored in this repository. The model was only used to discuss
  possible analyses; the code and numbers here are generated locally.
* The source is public domain.
* This is a deliberately simple, explainable method: a keyword proxy, not a
  literary judgement.
