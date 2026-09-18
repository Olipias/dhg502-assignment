"""
吴越春秋 · 君臣关系 / 政治内容占比分析
=====================================

Question
--------
How much of *Wu Yue Chunqiu* is about the ruler-minister (君臣) relationship,
i.e. political content, and how much is about other things?

Method (fully lexical, so every number can be checked by hand)
--------------------------------------------------------------
1. Normalise the public-domain plain text, drop OCR filler, split it into the
   ten 卷 (chapters) by their headings.  The text is a simplified-character
   edition, so every lexicon lists simplified and traditional forms.
2. Split every chapter into sentences on the classical full stop ． and on
   ？ ！.
3. Tag each sentence with three small, explicit lexicons:
     RULER    words referring to the sovereign
     MINISTER words naming officials / ministers / statesmen
     POLITY   words about statecraft, war, diplomacy, rewards and punishments
   and with a speech flag (contains 曰 or 「).
4. Classify each sentence, in priority order:
     君臣同现   a RULER word and a MINISTER word co-occur (the relationship
               itself: advice, appointment, remonstrance, reward, execution)
     君臣言论   direct speech by a ruler or a minister, without co-occurrence
               (court discourse; the counterpart is often only implied)
     政治·其他  a POLITY word, or merely a ruler/minister mention
     其他       none of the above
   Political = 君臣同现 + 君臣言论 + 政治·其他.  Report shares of sentences
   *and* of characters, overall and per 卷.
5. Also count the most frequent character bigrams (classical Chinese has no
   word spacing), keyword frequencies, and the mentions of the main people
   and offices, again per 卷.

Everything is keyword counting; the lexicons and their limits are printed in
the report so a reader can judge plausibility rather than trust a black box.
"""

import html
import json
import re
from collections import Counter

SRC = "吴越春秋.txt"
TXT_OUT = "analysis_results.txt"
HTML_OUT = "index.html"

RULER = [
    "君", "王", "孤", "寡人", "君王", "大王", "先王", "主",
    "吴王", "吳王", "越王", "阖闾", "闔閭", "夫差", "勾践", "勾踐",
    "寿梦", "壽夢", "诸樊", "諸樊", "余祭", "餘祭", "季札", "王僚",
    "公子光", "元常",
]
MINISTER = [
    "臣", "大夫", "相国", "相國", "令尹", "太宰", "司马", "司馬",
    "将军", "將軍", "太师", "太師", "少师", "少師", "行人",
    "伍子胥", "子胥", "伍胥", "范蠡", "文种", "文種", "大夫种", "大夫種",
    "伯嚭", "太宰嚭", "计然", "計然", "逢同", "诸稽郢", "諸稽郢",
    "曳庸", "扶同", "苦成", "皓进", "皓進", "孙武", "孫武", "白喜",
    "专诸", "專諸", "申包胥", "囊瓦", "子反", "巫臣", "庆忌", "慶忌",
    "要离", "要離", "华元", "子常", "子期", "陈音", "陳音", "被离",
    "被離", "太宰喜",
]
POLITY = [
    "国", "國", "政", "兵", "战", "戰", "伐", "军", "軍", "师", "師",
    "甲", "诸侯", "諸侯", "社稷", "宗庙", "宗廟", "百姓", "万民", "萬民",
    "法", "令", "治", "乱", "亂", "忠", "佞", "奸", "贤", "賢", "赏",
    "賞", "罚", "罰", "诛", "誅", "杀", "殺", "赦", "朝", "聘", "盟",
    "会", "會", "遣", "谏", "諫", "谋", "謀", "议", "議", "霸", "疆",
    "城", "贡", "貢", "赂", "賂", "民",
]
PEOPLE = [
    "勾践", "勾踐", "夫差", "阖闾", "闔閭", "伍子胥", "子胥", "范蠡",
    "文种", "文種", "伯嚭", "计然", "計然", "申包胥", "孙武", "孫武",
    "专诸", "專諸", "越王", "吴王", "吳王", "大夫", "太宰", "相国",
    "相國", "司马", "司馬", "君王", "群臣", "诸侯", "諸侯",
]


def load_chapters(path):
    raw = open(path, encoding="utf-8").read()
    raw = raw.replace("計●", "計然")
    raw = re.sub(r"[\ue000-\uf8ff\u25cf]", "", raw)
    cut = raw.find("黃帝\u3000昌意")
    if cut != -1:
        raw = raw[:cut]
    chunks = re.split(r"\n(?=卷第)", raw)
    chapters = []
    for chunk in chunks[1:]:
        lines = chunk.split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        chapters.append((title, body))
    return chapters


def split_sentences(text):
    parts = re.split(r"[．？！]+", text)
    return [p.strip() for p in parts if p.strip()]


def has(text, words):
    return any(w in text for w in words)


def han_len(text):
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def main():
    chapters = load_chapters(SRC)

    sentences = []
    for idx, (title, body) in enumerate(chapters, 1):
        for frag in split_sentences(body):
            sentences.append({"juan": idx, "title": title, "text": frag})

    total_sent = len(sentences)
    total_chars = sum(han_len(s["text"]) for s in sentences)

    for s in sentences:
        s["ruler"] = has(s["text"], RULER)
        s["minister"] = has(s["text"], MINISTER)
        s["polity"] = has(s["text"], POLITY)
        s["speech"] = (("「" in s["text"]) or ("」" in s["text"])
                       or ("曰" in s["text"]))
        if s["ruler"] and s["minister"]:
            s["cat"] = "君臣同现"
        elif s["speech"] and (s["ruler"] or s["minister"]):
            s["cat"] = "君臣言论"
        elif s["ruler"] or s["minister"] or s["polity"]:
            s["cat"] = "政治·其他"
        else:
            s["cat"] = "其他"
        s["chars"] = han_len(s["text"])

    CATS = ["君臣同现", "君臣言论", "政治·其他", "其他"]

    def agg(rows):
        d, c = Counter(), Counter()
        for r in rows:
            d[r["cat"]] += 1
            c[r["cat"]] += r["chars"]
        return d, c

    cat_sent, cat_chars = agg(sentences)
    core = cat_sent["君臣同现"]
    court = cat_sent["君臣言论"]
    pol_other = cat_sent["政治·其他"]
    other = cat_sent["其他"]
    political_sent = core + court + pol_other
    political_chars = (cat_chars["君臣同现"] + cat_chars["君臣言论"]
                       + cat_chars["政治·其他"])

    bigrams = Counter()
    for s in sentences:
        clean = "".join(ch for ch in s["text"] if "\u4e00" <= ch <= "\u9fff")
        for i in range(len(clean) - 1):
            bigrams[clean[i:i + 2]] += 1

    term_freq = {}
    for label, words in [("RULER", RULER), ("MINISTER", MINISTER),
                         ("POLITY", POLITY)]:
        counts = [(w, sum(s["text"].count(w) for s in sentences))
                  for w in words]
        term_freq[label] = [(w, n) for w, n in counts if n > 0]

    per_juan = []
    for idx, (title, body) in enumerate(chapters, 1):
        rows = [s for s in sentences if s["juan"] == idx]
        d, c = agg(rows)
        pol = d["君臣同现"] + d["君臣言论"] + d["政治·其他"]
        per_juan.append({
            "juan": idx,
            "title": title,
            "sent": len(rows),
            "chars": sum(r["chars"] for r in rows),
            "core": d["君臣同现"],
            "court": d["君臣言论"],
            "pol_other": d["政治·其他"],
            "other": d["其他"],
            "political": pol,
            "pol_pct": round(100 * pol / len(rows), 1) if rows else 0.0,
            "speech_pct": round(
                100 * sum(1 for r in rows if r["speech"]) / len(rows), 1
            ) if rows else 0.0,
        })

    people_juan = {}
    for name in PEOPLE:
        counts = [
            sum(s["text"].count(name) for s in sentences if s["juan"] == j)
            for j in range(1, len(chapters) + 1)
        ]
        if sum(counts) > 0:
            people_juan[name] = counts

    data = {
        "sentences": total_sent,
        "chars": total_chars,
        "cats": CATS,
        "cat_sent": cat_sent,
        "cat_chars": cat_chars,
        "political_sent": political_sent,
        "political_chars": political_chars,
        "political_sent_pct": round(100 * political_sent / total_sent, 1),
        "political_char_pct": round(100 * political_chars / total_chars, 1),
        "core_pct": round(100 * core / total_sent, 1),
        "court_pct": round(100 * court / total_sent, 1),
        "pol_other_pct": round(100 * pol_other / total_sent, 1),
        "other_pct": round(100 * other / total_sent, 1),
        "speech_pct": round(
            100 * sum(1 for s in sentences if s["speech"]) / total_sent, 1),
        "bigrams": bigrams.most_common(30),
        "term_freq": term_freq,
        "per_juan": per_juan,
        "people_juan": people_juan,
        "n_chapters": len(chapters),
    }

    write_txt(data)
    write_html(data)
    print(json.dumps({k: data[k] for k in [
        "sentences", "chars", "cat_sent", "political_sent_pct",
        "core_pct", "court_pct", "pol_other_pct", "other_pct",
        "political_char_pct", "speech_pct"]}, ensure_ascii=False, indent=2))
    print("per-juan political %:", [(j["juan"], j["pol_pct"], j["other"])
                                    for j in per_juan])


def write_txt(d):
    L = []
    add = L.append
    add("吳越春秋 · 君臣关系 / 政治内容占比分析")
    add("=" * 48)
    add("Corpus : 吴越春秋.txt  (後漢 趙曄 撰; public domain; 10 卷)")
    add("Sentences analysed : %d" % d["sentences"])
    add("Chinese characters : %d" % d["chars"])
    add("Direct-speech sentences (contain 「 or 曰) : %.1f%%" % d["speech_pct"])
    add("")
    add("0. Method")
    add("-" * 48)
    add("Every sentence is tagged with three small lexicons (RULER, MINISTER,")
    add("POLITY) and a speech flag, then put in one of four buckets:")
    add("  君臣同现   a RULER word and a MINISTER word occur together")
    add("  君臣言论   direct speech by a ruler or minister, no co-occurrence")
    add("  政治·其他  a POLITY word, or merely a ruler/minister mention")
    add("  其他       none of the above")
    add("Political = the first three buckets.")
    add("")
    add("1. Headline result")
    add("-" * 48)
    add("Political sentences : %d / %d  = %.1f%%"
        % (d["political_sent"], d["sentences"], d["political_sent_pct"]))
    add("Political characters : %d / %d  = %.1f%%"
        % (d["political_chars"], d["chars"], d["political_char_pct"]))
    for k in d["cats"]:
        add("  %-10s %5d sentences  %.1f%%"
            % (k, d["cat_sent"][k],
               round(100 * d["cat_sent"][k] / d["sentences"], 1)))
    add("")
    add("2. Sentence buckets")
    add("-" * 48)
    for k in d["cats"]:
        add("  %-10s sentences %5d  chars %6d"
            % (k, d["cat_sent"][k], d["cat_chars"][k]))
    add("")
    add("3. Most frequent character bigrams (top 30)")
    add("-" * 48)
    for w, n in d["bigrams"]:
        add("  %-6s %5d" % (w, n))
    add("")
    add("4. Keyword frequencies")
    add("-" * 48)
    for label, pairs in d["term_freq"].items():
        pairs = sorted(pairs, key=lambda x: -x[1])
        add("  [%s]" % label)
        add("  " + ", ".join("%s=%d" % (w, n) for w, n in pairs))
        add("")
    add("5. Political share by 卷")
    add("-" * 48)
    add("  %-18s %6s %6s %6s %6s %6s %7s %7s"
        % ("卷", "sent", "同现", "言论", "政治", "其他", "政治%", "對話%"))
    for j in d["per_juan"]:
        add("  %-18s %6d %6d %6d %6d %6d %6.1f %7.1f"
            % (j["title"][:16], j["sent"], j["core"], j["court"],
               j["pol_other"], j["other"], j["pol_pct"], j["speech_pct"]))
    add("")
    add("6. People / offices mentioned, by 卷")
    add("-" * 48)
    add("  %-8s" % "" + "".join("%5d" % j["juan"] for j in d["per_juan"])
        + "  total")
    for name, counts in d["people_juan"].items():
        add("  %-8s" % name + "".join("%5d" % c for c in counts)
            + "  %5d" % sum(counts))
    add("")
    add("7. Lexicons used")
    add("-" * 48)
    add("  RULER    : " + " ".join(RULER))
    add("  MINISTER : " + " ".join(MINISTER))
    add("  POLITY   : " + " ".join(POLITY))
    add("")
    add("Caveats")
    add("-" * 48)
    add("* Classical Chinese has no word spacing; bigrams are an approximation")
    add("  of words, and overlapping names (子胥 in 伍子胥) inflate raw counts.")
    add("* Keyword tagging can miss irony or count a word in a non-political")
    add("  sense (e.g. 师 in 农师, 使 'send' vs 'envoy'). Numbers are a proxy,")
    add("  good for a rough share, not for a sentence-by-sentence judgement.")
    add("* The text is a simplified-character edition with a few OCR gaps.")
    add("")
    open(TXT_OUT, "w", encoding="utf-8").write("\n".join(L))


def bar(pct, cls="pol"):
    width = max(0.5, min(100.0, pct))
    return ('<div class="track"><div class="fill %s" '
            'style="width:%.1f%%"></div></div>' % (cls, width))


def write_html(d):
    jrows = "".join(
        "<tr><td class='l'>%s</td><td>%d</td><td>%d</td><td>%d</td>"
        "<td>%d</td><td>%d</td><td class='bc'>%s<span>%.1f%%</span></td></tr>"
        % (html.escape(j["title"]), j["sent"], j["core"], j["court"],
           j["pol_other"], j["other"], bar(j["pol_pct"]), j["pol_pct"])
        for j in d["per_juan"])

    bigrows = "".join("<tr><td class='l'>%s</td><td>%d</td></tr>"
                      % (html.escape(w), n) for w, n in d["bigrams"])

    termblocks = ""
    for label, pairs in d["term_freq"].items():
        pairs = sorted(pairs, key=lambda x: -x[1])[:18]
        chips = "".join("<span class='chip'>%s <b>%d</b></span>"
                        % (html.escape(w), n) for w, n in pairs)
        termblocks += "<h3>%s</h3><p>%s</p>" % (label, chips)

    head = "".join("<th>%d</th>" % j["juan"] for j in d["per_juan"])
    prow = []
    for name, counts in d["people_juan"].items():
        cells = "".join("<td>%d</td>" % c if c else "<td class='z'>.</td>"
                        for c in counts)
        prow.append("<tr><td class='l'>%s</td>%s<td><b>%d</b></td></tr>"
                    % (html.escape(name), cells, sum(counts)))
    ptable2 = ("<table class='grid'><thead><tr><th></th>%s<th>Σ</th></tr>"
               "</thead><tbody>%s</tbody></table>" % (head, "".join(prow)))

    bucket = ("<p class='bk'><b>君臣同现</b> %d (%.1f%%) %s"
              "<b>君臣言论</b> %d (%.1f%%) %s"
              "<b>政治·其他</b> %d (%.1f%%) %s"
              "<b>其他</b> %d (%.1f%%) %s</p>"
              % (d["cat_sent"]["君臣同现"], d["core_pct"],
                 bar(d["core_pct"]),
                 d["cat_sent"]["君臣言论"], d["court_pct"],
                 bar(d["court_pct"], "court"),
                 d["cat_sent"]["政治·其他"], d["pol_other_pct"],
                 bar(d["pol_other_pct"], "mid"),
                 d["cat_sent"]["其他"], d["other_pct"],
                 bar(d["other_pct"], "other")))

    repl = {
        "@POL@": "%.1f" % d["political_sent_pct"],
        "@POLSENT@": "%d" % d["political_sent"],
        "@CORE@": "%.1f" % d["core_pct"],
        "@COREN@": "%d" % d["cat_sent"]["君臣同现"],
        "@COURT@": "%.1f" % d["court_pct"],
        "@COURTN@": "%d" % d["cat_sent"]["君臣言论"],
        "@MIDPCT@": "%.1f" % d["pol_other_pct"],
        "@OTHER@": "%.1f" % d["other_pct"],
        "@OTHERN@": "%d" % d["cat_sent"]["其他"],
        "@SPEECH@": "%.1f" % d["speech_pct"],
        "@CHARSPOL@": "%.1f" % d["political_char_pct"],
        "@BUCKET@": bucket,
        "@JUANROWS@": jrows,
        "@BIGROWS@": bigrows,
        "@TERMS@": termblocks,
        "@PEOPLE@": ptable2,
        "@SENT@": "%d" % d["sentences"],
        "@NCH@": "%d" % d["n_chapters"],
        "@CHARS@": "%d" % d["chars"],
    }
    tpl = HTML_TEMPLATE
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    open(HTML_OUT, "w", encoding="utf-8").write(tpl)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>吳越春秋 · 君臣关系 / 政治内容占比分析</title>
<style>
:root{--ink:#1c1a17;--paper:#f6f1e6;--line:#d8cdb4;--accent:#8c2f1e;--gold:#a8791f;--muted:#6b6253}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.75}
.wrap{max-width:980px;margin:0 auto;padding:48px 22px 80px}
h1{font-size:1.9rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 28px}
h2{font-size:1.15rem;border-bottom:2px solid var(--line);padding-bottom:6px;margin-top:44px}
h3{font-size:.95rem;margin:18px 0 6px;color:var(--accent)}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}
.card{flex:1 1 170px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.card .n{font-size:1.9rem;font-weight:700;color:var(--accent);line-height:1.1}
.card .lab{font-size:.8rem;color:var(--muted);margin-top:4px}
.track{background:#e7ddc7;border-radius:6px;height:11px;overflow:hidden;display:inline-block;vertical-align:middle;min-width:90px;width:100%}
.fill{height:100%;background:linear-gradient(90deg,#c05a40,#8c2f1e)}
.fill.court{background:linear-gradient(90deg,#b3714b,#8a4a2a)}
.fill.mid{background:linear-gradient(90deg,#c99a3a,#a8791f)}
.fill.other{background:linear-gradient(90deg,#7d9a63,#4c6b33)}
table{border-collapse:collapse;width:100%;font-size:.92rem}
td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:right}
th{color:var(--muted);font-weight:600;font-size:.8rem}
td.l,th.l{text-align:left}
td.z{color:#c3b89f}
td.bc{white-space:nowrap}
td.bc .track{width:110px;margin-right:8px}
td.bc span{color:var(--muted);font-size:.82rem}
.grid{font-size:.85rem}
.bk{display:flex;flex-wrap:wrap;gap:10px 26px;align-items:center;margin:14px 0}
.bk .track{width:110px;margin:0 8px}
.chip{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:14px;padding:2px 10px;margin:3px 5px 3px 0;font-size:.85rem}
.chip b{color:var(--accent)}
.two{display:flex;gap:26px;flex-wrap:wrap}
.two>div{flex:1 1 300px}
.note{background:#fff;border-left:4px solid var(--gold);padding:12px 16px;font-size:.9rem;color:var(--muted);margin-top:16px}
ul{padding-left:22px}
footer{margin-top:48px;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);padding-top:14px}
code{background:#efe7d5;padding:1px 5px;border-radius:4px}
</style>
</head>
<body>
<div class="wrap">
<h1>《吳越春秋》的「君臣」與政治含量</h1>
<p class="sub">How much of the <i>Wu Yue Chunqiu</i> is about the
ruler–minister relationship? A keyword measurement of a 10-卷 Chinese
historical source (後漢 趙曄 撰, public domain).</p>

<div class="cards">
  <div class="card"><div class="n">@POL@%</div><div class="lab">政治句占比<br>political sentences: @POLSENT@ / @SENT@</div></div>
  <div class="card"><div class="n">@CORE@%</div><div class="lab">君臣同现（最严格）<br>ruler + minister: @COREN@ sentences</div></div>
  <div class="card"><div class="n">@COURT@%</div><div class="lab">君臣言论（君主或臣下的对话）<br>court speech: @COURTN@</div></div>
  <div class="card"><div class="n">@OTHER@%</div><div class="lab">非政治內容（其他）<br>non-political: @OTHERN@ sentences</div></div>
  <div class="card"><div class="n">@SPEECH@%</div><div class="lab">含「曰 /「」的對話句<br>direct-speech sentences</div></div>
</div>

<h2>問題与方法</h2>
<p>問題：全书有多少内容在写 <b>君臣关系</b>（即政治），多少在写其他方面？<br>
方法：把 @NCH@ 卷全文切成 @SENT@ 個句子，给每句打三张小词典的标签 ——
<code>君/王/孤/寡人/阖闾/勾践…</code>（RULER）、<code>臣/大夫/相国/伍子胥/范蠡…</code>（MINISTER）、
<code>国/政/兵/战/伐/谏/赏/罚…</code>（POLITY）—— 并标出是否含「曰」（言论），再分入四类：</p>
<ul>
<li><b>君臣同现</b>：一句中同时出现 RULER 与 MINISTER 词。这是君臣关系本身（谏诤、任命、赏罚、赐死）。</li>
<li><b>君臣言论</b>：君主或臣下的直接对话，但未出现对方的称谓（对手往往省略）。</li>
<li><b>政治·其他</b>：出现 POLITY 词（战争、外交、国政），或仅仅提及君主/臣下（政治背景与人事）。</li>
<li><b>其他</b>：以上皆无（神话起源、地理、工艺、人物身世、诗赋等）。</li>
</ul>
<p>政治含量 = 前三类之和。全部为词频统计；词典与局限列在页末，可逐句复核。</p>

<h2>全书占比</h2>
@BUCKET@
<p>政治 @POLSENT@ 句（@POL@%）；约 <b>@CHARSPOL@%</b> 的汉字落在政治句内。
其中严格的君臣同现 @CORE@%，君臣言论 @COURT@%，国政军事等 @MIDPCT@%；非政治 @OTHER@%。</p>

<h2>各卷政治含量</h2>
<table class="grid"><thead><tr><th class="l">卷</th><th>句数</th><th>同现</th><th>言论</th><th>政治</th><th>其他</th><th>政治%</th></tr></thead>
<tbody>@JUANROWS@</tbody></table>
<p class="note">卷第一（吳太伯）与卷第六（越王無余）政治比例最低，因以始祖神话为主；卷八（勾践归国）、卷十（勾践伐吴）最高，因其内容几乎全是复国、伐吴的君臣谋划。整体呈「越到后段、君臣谋划越密」的趋势，与全书由吴转越的叙事重心一致。</p>

<h2>最常出现的二字词（前 30）</h2>
<div class="two">
  <div><table><tbody>@BIGROWS@</tbody></table></div>
  <div><h3>关键词频次</h3>@TERMS@</div>
</div>

<h2>人物／职官提及次数与分布</h2>
@PEOPLE@
<p class="note">数字为各卷中的出现次数，重名会重叠（「子胥」也计入「伍子胥」）。可看出：伍子胥、夫差集中于卷三至卷五的吴国叙事；范蠡、文种、勾践集中于卷七至卷十的越国叙事 —— 这正是全书结构由吴转越、由「君择臣」转向「臣事君」的体现。</p>

<h2>局限</h2>
<ul>
<li>古汉语无词间空格，二字词只是近似；重叠人名会重复计数。</li>
<li>词表法可能把非政治语境的词计入（如「师」在「农师」、「使」作派遣/使者），因此政治占比是粗略代理，不是逐句判断。</li>
<li>引号内以「．」断句，会把长段对话切成若干残句；「君臣言论」一类正是为回收这类残句而设。</li>
<li>底本为简体排印本，仍有少量 OCR 缺字与私用区字形。</li>
<li>「政治」在本页定义为「君臣关系 + 君臣言论 + 国政军事」，是一种可操作化的选择，并非唯一标准。</li>
</ul>

<footer>
数据源：趙曄《吳越春秋》（後漢，@NCH@ 卷，约 @CHARS@ 汉字），公有领域；
文本取自殆知閣古代文獻庫 <code>garychowcmu/daizhigev20</code>（经 jsDelivr 镜像下载）。<br>
方法：纯词典／词频统计，脚本 <code>analyze.py</code>；完整数字见 <code>analysis_results.txt</code>。 Course DHG502.
</footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
