"""
DHG502 Week 4 -- Collocation analysis of 吳越春秋.

Pipeline
--------
1. Load 吴越春秋.txt, drop the header and the ten 卷 headings, remove OCR
   filler (private-use glyphs, ●) and normalise the known 計● -> 计然 gap.
2. Split the text into sentences on the classical full stop ． and on ？！;.
3. Segment every sentence into words with jieba (the usual modern Chinese
   segmentation), extended with a small 吳越春秋 user dictionary so that
   names such as 阖闾 / 勾践 / 伍子胥 / 太宰嚭 stay in one piece.
4. Write the segmented sentences to data.txt -- one sentence per line,
   words separated by a space.  Sentence length varies naturally; it is not
   forced to a fixed number of words.
5. Collocation analysis:
      * adjacent bigrams and trigrams (never crossing a sentence boundary)
      * word pairs co-occurring inside a window of SPAN words
   with frequency, PMI, t-score, Dice and Dunning log-likelihood, written to
   collocation_results.txt.

Run:  python3 collocation.py
"""

import math
import re
from collections import Counter

import jieba

SRC = "../吴越春秋.txt"
DATA = "data.txt"
OUT = "collocation_results.txt"
SPAN = 5  # max positional distance when counting co-occurring pairs

NAMES = [
    "吴王", "越王", "阖闾", "夫差", "勾践", "伍子胥", "子胥", "范蠡",
    "文种", "大夫种", "太宰嚭", "伯嚭", "计然", "申包胥", "孙武", "孙子",
    "专诸", "要离", "庆忌", "公孙圣", "王孙骆", "白喜", "华元", "囊瓦",
    "子常", "子期", "元常", "季札", "诸樊", "余祭", "寿梦", "无余",
    "太伯", "仲雍", "季历", "勾吴", "欧冶子", "干将", "莫耶", "莫邪",
    "陈音", "西施", "郑旦", "扶同", "苦成", "曳庸", "皓进", "诸稽郢",
    "逢同", "椒丘訢", "被离", "宰嚭", "风湖子", "薛烛", "扈子", "子贡",
    "陈成恒", "昭王", "平王", "庄王", "灵王", "楚王", "吴国", "越国",
    "会稽", "姑苏", "姑胥", "姑胥之台", "太宰", "相国", "大夫", "行人",
    "司马", "少傅", "太傅", "令尹", "将军", "君主", "群臣", "社稷",
    "宗庙", "诸侯", "柰何", "仰天", "之台", "此战",
]

for _n in {n for n in NAMES if len(n) >= 2}:
    jieba.add_word(_n, freq=10_000)

KEEP = re.compile(r"[\u4e00-\u9fff]")
DROP = re.compile(r"[\ue000-\uf8ff\u25cf]")


def load_text(path):
    lines = []
    for line in open(path, encoding="utf-8-sig").read().split("\n"):
        s = line.strip()
        if not s or s.startswith("吴越春秋 后汉"):
            continue
        if re.fullmatch(r"卷第.*传", s):
            continue
        lines.append(s)
    text = "".join(lines).replace("计●", "计然")
    return DROP.sub("", text)


def split_sentences(text):
    parts = re.split(r"[。．.！!？?；;]+", text)
    return [p.strip() for p in parts if p.strip()]


def tokenize(sentence):
    return [t for t in (tok.strip() for tok in jieba.lcut(sentence))
            if t and KEEP.search(t)]


def build_sentences(sentences):
    return [toks for toks in (tokenize(s) for s in sentences) if toks]


# ---------------------------------------------------------------- measures

def xlogx(x):
    return 0.0 if x <= 0 else x * math.log(x)


def log_likelihood(k11, k12, k21, k22):
    n = k11 + k12 + k21 + k22
    if n == 0:
        return 0.0
    row1, row2 = k11 + k12, k21 + k22
    col1, col2 = k11 + k21, k12 + k22
    ll = 2 * (xlogx(k11) + xlogx(k12) + xlogx(k21) + xlogx(k22)
              - xlogx(row1) - xlogx(row2) - xlogx(col1) - xlogx(col2)
              + xlogx(n))
    return max(0.0, ll)


def chi_square(k11, k12, k21, k22):
    n = k11 + k12 + k21 + k22
    if n == 0:
        return 0.0
    row1, row2 = k11 + k12, k21 + k22
    col1, col2 = k11 + k21, k12 + k22
    denom = row1 * row2 * col1 * col2
    if denom == 0:
        return 0.0
    return n * (k11 * k22 - k12 * k21) ** 2 / denom


def bigram_stats(sents):
    counts = Counter()
    for sent in sents:
        for i in range(len(sent) - 1):
            counts[(sent[i], sent[i + 1])] += 1
    left, right, n = Counter(), Counter(), 0
    for (a, b), c in counts.items():
        left[a] += c
        right[b] += c
        n += c
    rows = []
    for (a, b), c in counts.items():
        s = left[a] + right[b]
        pmi = math.log2(c * n / (left[a] * right[b])) if c and n else 0.0
        t = (c - left[a] * right[b] / n) / math.sqrt(c) if c else 0.0
        dice = 2 * c / s if s else 0.0
        ll = log_likelihood(c, left[a] - c, right[b] - c,
                            n - c - (left[a] - c) - (right[b] - c))
        chi = chi_square(c, left[a] - c, right[b] - c,
                         n - c - (left[a] - c) - (right[b] - c))
        rows.append({"a": a, "b": b, "n": c, "pmi": pmi, "t": t,
                     "dice": dice, "ll": ll, "chi2": chi})
    return rows, n


def trigram_counts(sents):
    c = Counter()
    for sent in sents:
        for i in range(len(sent) - 2):
            c[(sent[i], sent[i + 1], sent[i + 2])] += 1
    return c


def window_pairs(sents):
    counts = Counter()
    for sent in sents:
        for i in range(len(sent)):
            for j in range(i + 1, min(i + SPAN + 1, len(sent))):
                a, b = sent[i], sent[j]
                counts[(a, b) if a <= b else (b, a)] += 1
    return counts


# ---------------------------------------------------------------- reports

def top(rows, key, k=25, min_n=1):
    return sorted((r for r in rows if r["n"] >= min_n),
                  key=lambda r: -r[key])[:k]


TABLE_HEAD = ("  %-12s %6s %8s %8s %8s %10s"
              % ("bigram", "freq", "PMI", "t", "Dice", "LL"))


def table(add, rows):
    add(TABLE_HEAD)
    for r in rows:
        add("  %-12s %6d %8.2f %8.2f %8.3f %10.2f"
            % (r["a"] + " " + r["b"], r["n"], r["pmi"], r["t"],
               r["dice"], r["ll"]))


def write_report(sents, word_counts, big_rows, big_n, tri_counts,
                 win_counts):
    lengths = sorted(len(s) for s in sents)
    mid = lengths[len(lengths) // 2]
    L = []
    add = L.append
    add("吳越春秋 · 搭配（collocation）分析")
    add("=" * 56)
    add("Corpus      : 吴越春秋.txt")
    add("Segmentation: jieba (natural words, 吳越春秋 name dictionary)")
    add("Unit        : one punctuation sentence per line, variable length")
    add("Sentences   : %d   words (tokens): %d   types: %d"
        % (len(sents), sum(word_counts.values()), len(word_counts)))
    add("Sentence length: min %d   median %d   max %d   mean %.1f"
        % (lengths[0], mid, lengths[-1],
           sum(lengths) / len(lengths)))
    add("Adjacent bigram tokens: %d   distinct bigrams: %d"
        % (big_n, len(big_rows)))
    add("")
    add("Measures used")
    add("-" * 56)
    add("  freq  raw co-occurrence frequency")
    add("  PMI   log2( f(xy)*N / (f(x)*f(y)) )      -- association strength")
    add("  t     (f(xy)-E)/sqrt(f(xy)), E=f(x)f(y)/N -- confidence")
    add("  Dice  2*f(xy)/(f(x)+f(y))")
    add("  LL    Dunning log-likelihood ratio (2x2)")
    add("  chi2  chi-square (2x2)")
    add("")

    add("1. Most frequent adjacent bigrams")
    add("-" * 56)
    table(add, top(big_rows, "n", 30))
    add("")

    add("2. Strongest adjacent bigrams by PMI  (freq >= 5)")
    add("-" * 56)
    table(add, top(big_rows, "pmi", 30, min_n=5))
    add("")

    add("3. Strongest adjacent bigrams by log-likelihood")
    add("-" * 56)
    table(add, top(big_rows, "ll", 30))
    add("")

    add("4. Strongest adjacent bigrams by t-score  (freq >= 3)")
    add("-" * 56)
    table(add, top(big_rows, "t", 30, min_n=3))
    add("")

    add("5. Most frequent adjacent trigrams")
    add("-" * 56)
    for t, c in tri_counts.most_common(30):
        add("  %-18s %6d" % (" ".join(t), c))
    add("")

    add("6. Word pairs co-occurring within a span of %d words "
        "(top 30)" % SPAN)
    add("-" * 56)
    for (a, b), c in win_counts.most_common(30):
        add("  %-14s %6d" % (a + " / " + b, c))
    add("")

    add("7. Most frequent words")
    add("-" * 56)
    for w, c in word_counts.most_common(40):
        add("  %-8s %6d" % (w, c))
    add("")
    add("Note: frequency alone favours grammatical words; PMI favours rare")
    add("pairs, so read sections 2-4 together. All counts come from the")
    add("segmented sentences in data.txt and can be checked by hand.")

    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    return L


def main():
    text = load_text(SRC)
    sents = build_sentences(split_sentences(text))

    with open(DATA, "w", encoding="utf-8") as fh:
        for sent in sents:
            fh.write(" ".join(sent) + "\n")

    word_counts = Counter(w for sent in sents for w in sent)
    big_rows, big_n = bigram_stats(sents)
    tri_counts = trigram_counts(sents)
    win_counts = window_pairs(sents)

    report = write_report(sents, word_counts, big_rows, big_n,
                          tri_counts, win_counts)

    print("sentences       : %d" % len(sents))
    print("words (tokens)  : %d" % sum(word_counts.values()))
    print("distinct words  : %d" % len(word_counts))
    print("distinct bigrams: %d" % len(big_rows))
    print("wrote           : %s, %s" % (DATA, OUT))
    print()
    print("\n".join(report[:20]))


if __name__ == "__main__":
    main()
