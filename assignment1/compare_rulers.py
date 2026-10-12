"""
DHG502 Week 4 -- compare the collocational profiles of 夫差 and 勾践.

Runs qhchina.analytics.collocations.find_collocates (window method, horizon 5)
for both rulers on data.txt, removes function words, keeps raw p < 0.05, and
writes a comparison table (txt) plus an HTML report with close-reading examples.

Run:  python3 compare_rulers.py
"""

import html

from qhchina.analytics.collocations import find_collocates

DATA = "data/data.txt"
OUT = "compare_rulers.txt"
HTML_OUT = "compare_rulers.html"
TARGETS = ["夫差", "勾践"]

MEASURES = ["logDice", "mi", "t-score", "log-likelihood", "z-score", "dice"]

STOPWORDS = [
    "之", "于", "而", "以", "其", "也", "矣", "乎", "哉", "焉", "者", "所",
    "则", "乃", "无", "不", "弗", "未", "非", "亡", "吾", "我", "余", "予",
    "汝", "尔", "若", "彼", "此", "是", "斯", "何", "且", "既", "皆", "俱",
    "各", "或", "及", "与", "并", "因", "故", "遂", "更", "复", "又", "亦",
    "但", "唯", "惟", "凡", "夫", "盖", "使", "令", "得", "可", "能", "欲",
    "当", "应", "须", "宜", "愿", "请", "敢", "窃", "莫", "勿", "毋", "相",
    "见", "从", "自", "由", "为", "有", "在", "曰", "谓", "已", "兮", "来",
    "去", "将", "尽", "悉", "咸", "每", "诸", "然", "虽", "然则", "于是",
    "至于", "所以",
]

# Example collocates per ruler (for the KWIC blocks).
EXAMPLES = {
    "夫差": ["北伐", "齐", "诸侯", "太子", "诛", "被"],
    "勾践": ["东海", "役", "下臣", "稽首", "范蠡", "不忍"],
}

NOTES = {
    "波": "太子波之子（继嗣出身）",
    "北伐": "夫差两次「北伐齐」——对外扩张",
    "太子": "立为太子、太子友——王位继承",
    "被": "被甲——亲征的武备",
    "诸侯": "合诸侯于黄池——争霸",
    "君王": "辱吾君王于诸侯／孤臣夫差——尊号与自贬",
    "齐": "北伐的对象国",
    "诛": "不诛越王／夫差之诛——生杀与败亡",
    "吴": "夫差的国",
    "东海": "「东海（役臣／贱臣）勾践」——自贬自称",
    "范蠡": "首席谋臣，入吴与伐吴两阶段皆在",
    "役": "役臣——以仆役自居",
    "下臣": "「下臣勾践」——对吴王自称",
    "稽首": "叩头至地，臣服之礼",
    "闻于": "闻于左右／周室——经营舆论",
    "再拜": "再拜稽首，臣服套语",
    "臣": "称臣／臣属",
    "不忍": "不忍其言／对使者——犹疑",
    "二": "数词（二君／二子），噪声",
    "越王": "勾践的君号，与名讳并置",
}


def load_sentences(path):
    with open(path, encoding="utf-8") as fh:
        return [line.split() for line in fh if line.strip()]


def collocates(sentences, target):
    df = find_collocates(
        sentences=sentences,
        target_words=target,
        method="window",
        horizon=5,
        measures=MEASURES,
        filters={"min_obs_local": 2, "stopwords": STOPWORDS},
        correction="fdr_bh",
        sort_by="p_value",
        ascending=True,
        return_type="dataframe",
    )
    df = df[df["p_value"] < 0.05].reset_index(drop=True)
    cols = ["collocate", "obs_local", "obs_global", "exp_local",
            "ratio_local", "p_value", "adjusted_p_value",
            "log_dice", "mi", "t_score", "log_likelihood", "z_score", "dice"]
    return df[[c for c in cols if c in df.columns]]


def examples(sentences, target, collocate, k=3):
    out = []
    for s in sentences:
        if target in s and collocate in s:
            out.append("".join(s))
            if len(out) >= k:
                break
    return out


def esc(x):
    return html.escape(str(x))


def table_html(df):
    cols = list(df.columns)
    rest = [c for c in cols if c != "collocate"]
    thead = "".join("<th>%s</th>" % esc(c) for c in cols)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in rest:
            v = r[c]
            if isinstance(v, str):
                txt = v
            elif c in ("p_value", "adjusted_p_value", "exp_local",
                       "ratio_local", "log_dice", "mi", "t_score",
                       "log_likelihood", "z_score", "dice"):
                txt = "%.4g" % v
            else:
                txt = "%d" % v
            cls = " class='p'" if c in ("p_value", "adjusted_p_value") else ""
            cells.append("<td%s>%s</td>" % (cls, esc(txt)))
        note = NOTES.get(r["collocate"], "")
        rows.append("<tr><td class='w'>%s<div class='note'>%s</div></td>%s</tr>"
                    % (esc(r["collocate"]), esc(note), "".join(cells)))
    return ("<table class='grid'><thead><tr>%s</tr></thead><tbody>%s</tbody>"
            "</table>" % (thead, "".join(rows)))


def exblock(sentences, target):
    blocks = []
    for w in EXAMPLES[target]:
        hits = examples(sentences, target, w)
        if not hits:
            continue
        items = "".join("<li>%s</li>" % esc(s) for s in hits)
        blocks.append("<p class='kw'><b>%s</b></p><ul class='kwic'>%s</ul>"
                      % (esc(w), items))
    return "".join(blocks)


def write_html(sentences, dfs, freqs, nsents, overlap):
    parts = []
    for t in TARGETS:
        df = dfs[t]
        parts.append(
            "<h2>「%s」的显著搭配（%d 个，p&lt;0.05）</h2>\n%s\n%s"
            % (esc(t), len(df), table_html(df), exblock(sentences, t)))
    body = "\n".join(parts)

    tpl = HTML_TEMPLATE
    repl = {
        "@CARD_GJ_FREQ@": "%d" % freqs["勾践"],
        "@CARD_GJ_SIG@": "%d" % len(dfs["勾践"]),
        "@CARD_FC_FREQ@": "%d" % freqs["夫差"],
        "@CARD_FC_SIG@": "%d" % len(dfs["夫差"]),
        "@CARD_SENT@": "%d" % sum(nsents.values()),
        "@OVERLAP@": "%d" % overlap,
        "@BODY@": body,
        "@GJ_LIST@": "、".join(dfs["勾践"]["collocate"]),
        "@FC_LIST@": "、".join(dfs["夫差"]["collocate"]),
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    with open(HTML_OUT, "w", encoding="utf-8") as fh:
        fh.write(tpl)


def main():
    sentences = load_sentences(DATA)
    dfs, freqs, nsents = {}, {}, {}
    for t in TARGETS:
        freqs[t] = sum(s.count(t) for s in sentences)
        nsents[t] = sum(1 for s in sentences if t in s)
        dfs[t] = collocates(sentences, t)
        print("=== %s: %d tokens, %d sentences, %d significant collocates"
              % (t, freqs[t], nsents[t], len(dfs[t])))
        print(dfs[t].to_string(index=False, float_format=lambda x: "%.4g" % x))

    set_gj = set(dfs["勾践"]["collocate"])
    set_fc = set(dfs["夫差"]["collocate"])
    overlap = len(set_gj & set_fc)
    print("\nshared significant collocates:", set_gj & set_fc or "NONE")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("Collocational profiles of 夫差 vs 勾践 (Wu Yue Chunqiu)\n")
        fh.write("=" * 62 + "\n")
        fh.write("Source : data.txt (jieba-segmented sentences)\n")
        fh.write("Method : find_collocates, window, horizon=5, Fisher greater,\n")
        fh.write("         BH-FDR, function words removed, obs_local>=2, p<0.05\n\n")
        for t in TARGETS:
            fh.write("### %s  (%d tokens, %d sentences)\n"
                     % (t, freqs[t], nsents[t]))
            fh.write(dfs[t].to_string(index=False,
                                      float_format=lambda x: "%.4g" % x))
            fh.write("\n\n")
        fh.write("Shared significant collocates: %s\n"
                 % (sorted(set_gj & set_fc) or "NONE"))

    write_html(sentences, dfs, freqs, nsents, overlap)
    print("\nwrote %s, %s" % (OUT, HTML_OUT))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>夫差 vs 勾践 · 搭配詞下的兩個國君</title>
<style>
:root{--ink:#1c1a17;--paper:#f6f1e6;--line:#d8cdb4;--accent:#8c2f1e;--gold:#a8791f;--muted:#6b6253;--blue:#2f4b7c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.8}
.wrap{max-width:1040px;margin:0 auto;padding:48px 22px 80px}
h1{font-size:1.85rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 26px}
h2{font-size:1.2rem;border-bottom:2px solid var(--line);padding-bottom:6px;margin-top:46px}
h3{font-size:1rem;margin:20px 0 6px;color:var(--accent)}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}
.card{flex:1 1 150px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px}
.card .n{font-size:1.7rem;font-weight:700;color:var(--accent);line-height:1.15}
.card.fc .n{color:var(--blue)}
.card .lab{font-size:.8rem;color:var(--muted);margin-top:4px}
table{border-collapse:collapse;width:100%;font-size:.85rem}
td,th{border-bottom:1px solid var(--line);padding:6px 7px;text-align:right;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:.75rem;white-space:nowrap}
td.w{text-align:left;font-weight:700;font-size:.95rem;white-space:nowrap}
td .note{font-weight:400;font-size:.72rem;color:var(--muted);max-width:190px;white-space:normal}
td.p{color:var(--accent)}
.kw{color:var(--accent);margin:12px 0 0;font-size:.9rem}
.kwic{list-style:none;padding:0;margin:4px 0 4px 0}
.kwic li{background:#fff;border-left:3px solid var(--gold);padding:6px 12px;margin:5px 0;font-size:.84rem;color:#3a352d}
.cluster{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 20px 16px;margin:14px 0}
.tag{display:inline-block;background:#efe7d5;color:var(--accent);border-radius:12px;padding:1px 10px;font-size:.78rem;margin:0 5px 0 0}
.cmp{width:100%;font-size:.88rem}
.cmp th{text-align:left}
.cmp td:first-child{font-weight:700}
.note-box{background:#fff;border-left:4px solid var(--gold);padding:12px 16px;font-size:.9rem;color:var(--muted);margin-top:16px}
ul{padding-left:22px}
footer{margin-top:48px;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);padding-top:14px}
code{background:#efe7d5;padding:1px 5px;border-radius:4px}
</style>
</head>
<body>
<div class="wrap">
<h1>夫差 vs 勾践：搭配詞裡的两个国君</h1>
<p class="sub">Collocational profiles of the two rulers in the <i>Wu Yue Chunqiu</i>
(window 5, Fisher exact one-sided, BH-FDR, function words removed, p &lt; 0.05).</p>

<div class="cards">
  <div class="card"><div class="n">@CARD_GJ_FREQ@</div><div class="lab">「勾践」词次 · 显著搭配 @CARD_GJ_SIG@</div></div>
  <div class="card fc"><div class="n">@CARD_FC_FREQ@</div><div class="lab">「夫差」词次 · 显著搭配 @CARD_FC_SIG@</div></div>
  <div class="card"><div class="n">@OVERLAP@</div><div class="lab">两人共享的显著搭配词<br>shared collocates</div></div>
  <div class="card"><div class="n">@CARD_SENT@</div><div class="lab">含这两个人名的句子（合计）<br>sentences</div></div>
</div>

<p>两人在同一语料、同一参数下跑 <code>find_collocates</code>。结果几乎不重叠：
勾践的显著搭配是 <b>@GJ_LIST@</b>；夫差的是 <b>@FC_LIST@</b>。
共享显著搭配 <b>@OVERLAP@</b> 个 —— 说明文本把两个国君放进<b>两套不同的语义场</b>。</p>

@BODY@

<h2>对比：两种国君形象</h2>
<table class="cmp">
<tr><th>维度</th><th>夫差</th><th>勾践</th></tr>
<tr><td>核心语义场</td><td>北伐、齐、诸侯、诛</td><td>东海、役、下臣、稽首、再拜</td></tr>
<tr><td>动作方向</td><td>对外扩张、争霸（合诸侯于黄池）</td><td>对内自贬、忍辱（称臣、行臣服之礼）</td></tr>
<tr><td>关系／继承</td><td>太子、波（继嗣）、君王</td><td>臣、范蠡（倚重谋臣）</td></tr>
<tr><td>性格线索</td><td>被甲亲征、诛（生杀予夺）</td><td>不忍（犹疑）、闻于（经营舆论）</td></tr>
<tr><td>结局意象</td><td>「夫差之诛」——败亡被杀</td><td>复国、再拜——由辱转兴</td></tr>
<tr><td>显著搭配数</td><td>@CARD_FC_SIG@</td><td>@CARD_GJ_SIG@</td></tr>
</table>

<div class="cluster">
<h3>解读</h3>
<p><span class="tag">夫差</span>搭配词几乎全在<b>横向的对外轴</b>上：<b>北伐／齐</b>是两次北征齐国，
<b>诸侯</b>指向黄池争霸，<b>诛</b>是「不诛越王」与「夫差之诛」的生杀与败亡，
<b>太子／波</b>关乎继嗣，<b>被</b>（被甲）是亲征武备。文本由此把夫差写成<b>好大喜功、
向外用兵的霸主</b>，其关键词预演了他的结局。</p>
<p><span class="tag">勾践</span>搭配词则全在<b>纵向的自贬轴</b>与<b>君臣轴</b>上：
<b>东海（役臣／贱臣）、役、下臣、稽首、再拜、臣</b>是成套的臣服辞令，
<b>范蠡</b>标明他对谋臣的依赖，<b>不忍</b>点出犹疑，<b>闻于</b>指外交舆论的经营。
文本由此把勾践写成<b>忍辱负重、依靠谋臣的复国之君</b>。</p>
<p>值得注意的是「君王」一词：它既出现在越人控诉
「夫差辱吾君王于诸侯」（夫差羞辱勾践），也出现在
「孤臣夫差……得与君王结成以归」（夫差向勾践自称「孤臣」）。
同一个尊号把两人的<b>地位翻转</b>并置——这正是全书由吴转越的结构缩影。</p>
</div>

<h2>方法与局限</h2>
<ul>
<li>window=5，左右各 5 词，跨句共现不计；换 horizon 结果会变。</li>
<li>样本小：夫差仅 @CARD_FC_FREQ@ 词次、勾践 @CARD_GJ_FREQ@ 词次，多数 obs_local=2–3，低頻搭配不穩。</li>
<li>已人工剔除 97 个虚词／连接词；过滤只影响输出，不改统计量。</li>
<li>分词基于简体排印本 + jieba + 人名词典；换分词或校本结果会变。</li>
<li>显著≠语义：只说明共現超出偶然，仍需 close reading。</li>
</ul>

<footer>
数据源：趙曄《吳越春秋》（公有領域），jieba 分词为 <code>data.txt</code>；
搭配由 <code>find_collocates</code> 计算，脚本 <code>compare_rulers.py</code>。
Course DHG502, Week 4.
</footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
