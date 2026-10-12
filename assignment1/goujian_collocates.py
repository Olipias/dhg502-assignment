"""
DHG502 Week 4 -- statistically significant collocates of 勾践.

Uses qhchina.analytics.collocations.find_collocates (window method) on the
jieba-segmented sentences in data.txt, removes function words, keeps raw
p < 0.05, and writes a plain-text table plus an HTML report.

Run:  python3 goujian_collocates.py
"""

import html

from qhchina.analytics.collocations import find_collocates

DATA = "data/data.txt"
OUT = "goujian_collocates.txt"
HTML_OUT = "goujian_collocates.html"
TARGET = "勾践"

MEASURES = ["logDice", "mi", "t-score", "log-likelihood", "z-score", "dice"]

# Function words / connectives to keep out of the collocate list.
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

# Short glosses used in the HTML table / analysis.
NOTES = {
    "东海": "「东海（役臣／贱臣）勾践」——向吴王自贬时的固定自称",
    "范蠡": "勾践的首席谋臣，贯穿入吴与伐吴两个阶段",
    "役": "役臣／役使，自我定位为吴国的仆役",
    "下臣": "「下臣勾践」——对吴王自称，臣属语",
    "稽首": "叩头至地，臣服之礼",
    "闻于": "闻于左右／闻于周室，经营名声与舆论",
    "再拜": "再拜稽首，臣服与献礼的礼仪套语",
    "臣": "称臣／臣属，勾践的自我定位",
    "不忍": "不忍其言／不忍对使者，性格中的犹疑",
    "二": "数词（二君／二子），语义解释力弱",
    "越王": "勾践的君号，与名讳并置",
}


def load_sentences(path):
    with open(path, encoding="utf-8") as fh:
        return [line.split() for line in fh if line.strip()]


def examples(sentences, collocate, k=3):
    out = []
    for s in sentences:
        if TARGET in s and collocate in s:
            out.append("".join(s))
            if len(out) >= k:
                break
    return out


def esc(x):
    return html.escape(str(x))


def write_html(df, sentences, raw_rows, target_freq, target_sents):
    cols = list(df.columns)
    rest = [c for c in cols if c != "collocate"]
    thead = "".join("<th>%s</th>" % esc(c) for c in cols)
    trows = []
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
        trows.append("<tr><td class='w'>%s<div class='note'>%s</div></td>%s</tr>"
                     % (esc(r["collocate"]), esc(note), "".join(cells)))
    table = ("<table class='grid'><thead><tr>%s</tr></thead><tbody>%s"
             "</tbody></table>" % (thead, "".join(trows)))

    def exlist(collocate, k=3):
        items = "".join("<li>%s</li>" % esc(s) for s in examples(sentences, collocate, k))
        return "<ul class='kwic'>%s</ul>" % items

    tpl = HTML_TEMPLATE
    repl = {
        "@TARGET@": esc(TARGET),
        "@TARGET_FREQ@": "%d" % target_freq,
        "@TARGET_SENTS@": "%d" % target_sents,
        "@NSIG@": "%d" % len(df),
        "@NCAND@": "%d" % raw_rows,
        "@TABLE@": table,
        "@EX_HAI@": exlist("东海"),
        "@EX_YI@": exlist("役"),
        "@EX_XIACHEN@": exlist("下臣"),
        "@EX_JISHOU@": exlist("稽首"),
        "@EX_FANLI@": exlist("范蠡"),
        "@EX_BUREN@": exlist("不忍"),
        "@EX_WENYU@": exlist("闻于"),
        "@EX_YUEWANG@": exlist("越王"),
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    with open(HTML_OUT, "w", encoding="utf-8") as fh:
        fh.write(tpl)


def main():
    sentences = load_sentences(DATA)
    target_freq = sum(s.count(TARGET) for s in sentences)
    target_sents = sum(1 for s in sentences if TARGET in s)
    print("sentences: %d, tokens: %d, 勾践: %d tokens in %d sentences"
          % (len(sentences), sum(len(s) for s in sentences),
             target_freq, target_sents))

    raw = find_collocates(
        sentences=sentences,
        target_words=TARGET,
        method="window",
        horizon=5,
        measures=MEASURES,
        filters={"min_obs_local": 2},
        correction="fdr_bh",
        sort_by="p_value",
        ascending=True,
        return_type="dataframe",
    )
    raw_rows = len(raw)

    df = find_collocates(
        sentences=sentences,
        target_words=TARGET,
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
    df = df[[c for c in cols if c in df.columns]]

    print("\nCollocates of '%s' (window, horizon=5, obs_local>=2, "
          "function words removed, p<0.05)" % TARGET)
    print(df.to_string(index=False, float_format=lambda x: "%.4g" % x))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("Statistically significant collocates of %s\n" % TARGET)
        fh.write("=" * 60 + "\n")
        fh.write("Source : data.txt (吴越春秋, jieba-segmented sentences)\n")
        fh.write("Method : find_collocates, method='window', horizon=5\n")
        fh.write("Tests  : Fisher exact (greater), Benjamini-Hochberg FDR\n")
        fh.write("Filter : obs_local >= 2, function words removed, p < 0.05\n")
        fh.write("Rows   : %d\n\n" % len(df))
        fh.write(df.to_string(index=False, float_format=lambda x: "%.4g" % x))
        fh.write("\n")

    write_html(df, sentences, raw_rows, target_freq, target_sents)
    print("\nwrote %s, %s" % (OUT, HTML_OUT))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>《吳越春秋》「勾践」的显著搭配</title>
<style>
:root{--ink:#1c1a17;--paper:#f6f1e6;--line:#d8cdb4;--accent:#8c2f1e;--gold:#a8791f;--muted:#6b6253}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.8}
.wrap{max-width:1000px;margin:0 auto;padding:48px 22px 80px}
h1{font-size:1.85rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 26px}
h2{font-size:1.15rem;border-bottom:2px solid var(--line);padding-bottom:6px;margin-top:44px}
h3{font-size:1rem;margin:20px 0 6px;color:var(--accent)}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}
.card{flex:1 1 150px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px}
.card .n{font-size:1.7rem;font-weight:700;color:var(--accent);line-height:1.15}
.card .lab{font-size:.8rem;color:var(--muted);margin-top:4px}
table{border-collapse:collapse;width:100%;font-size:.86rem}
td,th{border-bottom:1px solid var(--line);padding:6px 7px;text-align:right;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:.76rem;white-space:nowrap}
td.w{text-align:left;font-weight:700;font-size:.95rem;white-space:nowrap}
td .note{font-weight:400;font-size:.72rem;color:var(--muted);max-width:200px;white-space:normal}
td.p{color:var(--accent)}
.grid td:first-child,.grid th:first-child{position:sticky;left:0;background:var(--paper)}
.kwic{list-style:none;padding:0;margin:10px 0 4px}
.kwic li{background:#fff;border-left:3px solid var(--gold);padding:7px 12px;margin:6px 0;font-size:.85rem;color:#3a352d}
.cluster{background:#fff;border:1px solid var(--line);border-radius:10px;padding:6px 20px 16px;margin:14px 0}
.tag{display:inline-block;background:#efe7d5;color:var(--accent);border-radius:12px;padding:1px 10px;font-size:.78rem;margin:0 5px 0 0}
.note-box{background:#fff;border-left:4px solid var(--gold);padding:12px 16px;font-size:.9rem;color:var(--muted);margin-top:16px}
ul{padding-left:22px}
footer{margin-top:48px;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);padding-top:14px}
code{background:#efe7d5;padding:1px 5px;border-radius:4px}
</style>
</head>
<body>
<div class="wrap">
<h1>《吳越春秋》「@TARGET@」的显著搭配</h1>
<p class="sub">Statistically significant collocates of <b>@TARGET@</b> —
window method (horizon 5), Fisher exact test (one-sided), Benjamini–Hochberg FDR,
function words removed, p &lt; 0.05.</p>

<div class="cards">
  <div class="card"><div class="n">@TARGET_FREQ@</div><div class="lab">「勾践」全篇词次<br>token frequency</div></div>
  <div class="card"><div class="n">@TARGET_SENTS@</div><div class="lab">含「勾践」的句子<br>sentences</div></div>
  <div class="card"><div class="n">@NSIG@</div><div class="lab">显著搭配词（p&lt;0.05）<br>significant collocates</div></div>
  <div class="card"><div class="n">@NCAND@</div><div class="lab">去连接词前候选<br>candidates before stopwords</div></div>
</div>

<h2>方法与参数</h2>
<p>用 <code>qhchina.analytics.collocations.find_collocates</code> 的
<b>window</b> 方法：以「勾践」为中心左右各取 5 个词构成窗口，窗口内共现的词即为候选搭配。
每个候选与「勾践」构成 2×2 列联表，用 Fisher 精确检验（单侧 greater）求 p 值，
经 Benjamini–Hochberg 控制 FDR。<code>obs_local</code> 为窗口共现次数，
<code>obs_global</code> 为搭配词全篇词频，<code>ratio_local = obs_local / exp_local</code>
（&gt;1 表示互相吸引），<code>logDice</code> 与 <code>MI</code> 为搭配强度。
先剔除「之／于／而／不／也／从／曰／谓」等虚词连接词，再保留原始 p &lt; 0.05。</p>

<h2>结果表</h2>
@TABLE@
<p class="note-box">p 值越小、ratio 與 logDice 越大，表示「勾践」與該詞的共現越不可能出於偶然。
注意 <code>obs_local</code> 普遍只有 2–6 次，故個別數值不宜過度解讀。</p>

<h2>这些搭配说明了什么</h2>

<div class="cluster">
<h3><span class="tag">臣服套語</span> 东海 · 役 · 下臣 · 臣 · 稽首 · 再拜</h3>
<p>最显著的一批词几乎全部来自勾践向吴王自贬、称臣、行礼的<b>固定外交辞令</b>：
「东海役臣勾践」「东海贱臣勾践」「下臣勾践」「稽首再拜称臣」。它们不是随意出现的实词，
而是同一套屈辱语域的组成部分。可见文本对勾践的第一重塑造是<b>被侮辱、被羁押的罪臣</b>：
他先以仆役自居，再以「稽首再拜」完成臣服仪节。勾践的君王身份在此被暂时悬置。</p>
@EX_HAI@
@EX_YI@
@EX_XIACHEN@
@EX_JISHOU@
</div>

<div class="cluster">
<h3><span class="tag">君臣網絡</span> 范蠡 · 越王 · 臣</h3>
<p>「范蠡」是勾践最稳定的共现者之一（6 次，ratio 7.6，logDice 10.8）。
从卷第七「与大夫种、范蠡入臣于吴」，到归国后「复问范蠡曰：可伐矣」，
范蠡贯穿了<b>受辱</b>与<b>复仇</b>两个阶段。统计上的强关联，正对应叙事上
「君依赖臣」的结构：勾践的重大抉择几乎都与范蠡商议而定。
而「越王」与「勾践」同现，则显示同一人物在<b>君号与名讳</b>之间被反复并置——</p>
@EX_FANLI@
@EX_YUEWANG@
</div>

<div class="cluster">
<h3><span class="tag">性格／輿論</span> 不忍 · 闻于</h3>
<p>「不忍」只出现 2 次却达显著：一次是不忍听吴使乞成之言，一次是不忍面对吴使。
这与范蠡、文种的果决形成对照，透露出勾践性格中的<b>犹疑与妇人之仁</b>，
也解释了为何灭吴的最后一步常由臣下推动。「闻于」则多出现在
「闻于左右」「闻于周室」等句中，指向勾践对<b>名声与外交舆论</b>的经营：
卑辞以事吴、示义于周室，都是复国策略的一部分。</p>
@EX_BUREN@
@EX_WENYU@
</div>

<div class="cluster">
<h3><span class="tag">需存疑</span> 二</h3>
<p>「二」是数词，多出自「二君」「二子」等结构，语义解释力弱，
更可能是窗口切分与高频词造成的统计噪声，宜忽略。</p>
</div>

<h2>总体解读</h2>
<p>勾践的显著搭配几乎<b>不含战场实词</b>（伐、战、兵、军等都没有进入显著名单），
却密集地落在「臣服礼仪」与「君臣谋划」两类词上。这一分布提示：
在《吳越春秋》的叙事中，勾践的核心形象不是战将，而是<b>忍辱负重、依靠谋臣的复国之君</b>。
他的君王性通过两套动作实现——对外以「东海役臣／下臣」的姿态蛰伏，
对内以「问范蠡」的方式运筹。军事行动的执行更多落在越王（君号）、范蠡、文种身上，
而「勾践」这个名字则被牢牢绑定在屈辱与谋划的语境里。</p>

<h2>方法与局限</h2>
<ul>
<li><b>窗口法</b>：只看勾践左右各 5 词，跨句共现不计；换 horizon 结果会变。</li>
<li><b>小样本</b>：勾践全篇仅 @TARGET_FREQ@ 词次，候选 <code>obs_local</code> 多为 2–6，
p 值与 logDice 波动大，低頻搭配不穩定。</li>
<li><b>切词影响</b>：底本为简体排印本，经 jieba 分词并加入人名词典；分词不同，搭配亦不同。</li>
<li><b>虚词过滤</b>：已剔除 97 个虚词／连接词（<code>goujian_collocates.py</code> 中 <code>STOPWORDS</code>），
过滤只影响输出，不改变统计量。</li>
<li><b>显著 ≠ 语义</b>：Fisher 显著只说明共現超出偶然，仍需回读上下文判断是否構成真正的「搭配」。</li>
</ul>

<footer>
数据源：趙曄《吳越春秋》（後漢，公有領域），经 jieba 分词为 <code>data.txt</code>；
搭配分析由 <code>find_collocates</code> 完成，脚本 <code>goujian_collocates.py</code>。
Course DHG502, Week 4.
</footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    main()
