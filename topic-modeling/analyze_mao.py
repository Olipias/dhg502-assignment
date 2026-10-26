#!/usr/bin/env python3
"""Parse the Mao Zedong Selected Works corpus and fit a 10-topic LDA model.

The raw corpus is the GitHub text file used for the qhchina exercise.  Each
article starts with a title block followed by a date in parentheses, e.g.
``（一九二五年十二月一日）``.  The parser reconstructs the title from the
lines immediately above the date and treats the five-blank-line gap before the
title as the document boundary.  Footnotes are discarded by cutting the text at
the ``注　　释`` heading and by removing inline ``〔12〕`` markers.

Run with ``topic-modeling/.venv/bin/python topic-modeling/analyze_mao.py``.
"""

from __future__ import annotations

import argparse
import base64
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from pathlib import Path

import jieba
import numpy as np
from qhchina import load_stopwords
from qhchina.analytics.topicmodels import LDAGibbsSampler

RAW_URL = (
    "https://raw.githubusercontent.com/mcjkurz/qhchina-data/main/corpora/"
    "%E9%80%89%E9%9B%86/%E6%AF%9B%E6%B3%BD%E4%B8%9C%E9%80%89%E9%9B%86.txt"
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW = BASE_DIR / "毛泽东选集.txt"
DEFAULT_OUT = BASE_DIR / "output"

VOLUME_RE = re.compile(r"^第([一二三四五六七])卷(（静火版）)?$")
VOLUME_NUMBERS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
}

# A date line starts with an opening parenthesis and a Chinese-numeral year.
# Both 〇 and ○ (and occasionally Latin O / digit 0) are used for zero.
YEAR_CHARS = "一二三四五六七八九〇○O0o"
DATE_START_RE = re.compile(rf"^（\s*[{YEAR_CHARS}]{{2,4}}年")
DATE_END_RE = re.compile(r"）\s*$")
NOTE_HEADING_RE = re.compile(r"^注[\u3000\s]+释$")
# Remove numeric footnote markers such as 〔1〕 / 〔12〕, including a few
# malformed variants in the source (〔1）〕).  Do not remove real bracketed
# content such as 〔毛主义〕.
FOOTNOTE_MARK_RE = re.compile(
    r"〔\s*[0-9一二三四五六七八九十百]{1,3}\s*[）)]?[^〕\n]{0,6}〕"
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

# Dates on these headings are dates of subsections, not separate articles.
GENERIC_TITLES = {
    "序",
    "跋",
    "引言",
    "结论",
    "开幕词",
    "序言",
    "序言一",
    "序言二",
    "按语（选辑）",
}

YEAR_TRANSLATION = str.maketrans(
    {
        "〇": "0",
        "○": "0",
        "O": "0",
        "o": "0",
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
    }
)


@dataclass
class Document:
    doc_id: int
    volume: int
    title: str
    date: str
    year: int
    title_start: int
    date_end: int
    region_end: int
    body: str = ""
    tokens: list[str] = field(default_factory=list)

    @property
    def clean_title(self) -> str:
        title_lines = [
            line
            for line in self.title.splitlines()
            if not re.match(r"^[一二三四五六七八九十百]+、", line)
        ]
        title = FOOTNOTE_MARK_RE.sub("", "\n".join(title_lines))
        title = title.replace("*", "").replace("\n", "")
        return re.sub(r"\s+", " ", title).strip()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def is_date_start(line: str) -> bool:
    """Return True if *line* looks like the start of an article date line."""
    stripped = line.strip()
    if not DATE_START_RE.match(stripped):
        return False
    # ``（一）一九六八年...`` is a subsection, not an article date.
    if re.match(r"^[一二三四五六七八九十百]+）", stripped[1:]):
        return False
    return True


def parse_date(lines: list[str], index: int, volume_end: int) -> tuple[str, int] | None:
    """Return the complete date string and its last line index."""
    stripped = lines[index].strip()
    if not is_date_start(stripped):
        return None
    if DATE_END_RE.search(stripped):
        return stripped, index

    # A few dates wrap onto the next non-empty line (the appendix is the only
    # case in this corpus).  Allow a small gap but never run far into the body.
    parts = [stripped]
    for next_index in range(index + 1, min(volume_end, index + 9)):
        candidate = lines[next_index].strip()
        if not candidate:
            continue
        parts.append(candidate)
        if DATE_END_RE.search(candidate):
            return " ".join(parts), next_index
    return None


def extract_title(
    lines: list[str], date_index: int, volume_start: int
) -> tuple[str, int]:
    """Reconstruct the title block immediately above a date line.

    In this edition a new article title is separated from the preceding
    footnote/body by five blank lines.  Title lines may themselves be split by
    one or two blank lines, so only a gap of five or more blank lines ends the
    title block.
    """
    cursor = date_index - 1
    blanks = 0
    parts: list[str] = []
    title_start = date_index

    while cursor > volume_start:
        line = lines[cursor].strip()

        if not line:
            blanks += 1
            if blanks >= 5 and parts:
                break
            cursor -= 1
            continue

        if blanks >= 5:
            break

        # Stop at notes, page furniture, or a body paragraph.
        if line.startswith(("〔", "注", "*")):
            break
        if line.endswith(("。", "；", "：")):
            break
        if len(line) > 120:
            break
        if VOLUME_RE.match(line):
            break

        parts.append(line)
        title_start = cursor
        blanks = 0
        cursor -= 1

    return "\n".join(reversed(parts)).strip(), title_start


def is_real_title(title: str) -> bool:
    """Reject section headings and other non-article date blocks."""
    if not title or title in GENERIC_TITLES:
        return False

    title_lines = title.splitlines()
    if re.match(r"^[一二三四五六七八九十百]+、", title_lines[0]):
        return False
    if any(re.match(r"^（[一二三四五六七八九十百]+）", line) for line in title_lines):
        return False
    # A date embedded in the title block means this is a subsection date.
    if any("年" in line and ("（" in line or "）" in line) for line in title_lines):
        return False
    # Signature block preceding a congratulatory telegram date.
    if title_lines[0].startswith("中国共产党中央委员会主席"):
        return False
    return True


def chinese_year(date: str) -> int:
    match = re.search(rf"([{YEAR_CHARS}]{{4}})年", date)
    if not match:
        raise ValueError(f"Cannot extract a four-character year from {date!r}")
    return int(match.group(1).translate(YEAR_TRANSLATION))


def parse_documents(lines: list[str]) -> list[Document]:
    volume_starts = [
        (index, VOLUME_NUMBERS[VOLUME_RE.match(line.strip()).group(1)])
        for index, line in enumerate(lines)
        if VOLUME_RE.match(line.strip())
    ]
    if not volume_starts:
        raise ValueError("No volume headings found in the source file")

    documents: list[Document] = []
    for position, (volume_start, volume_number) in enumerate(volume_starts):
        if position + 1 < len(volume_starts):
            volume_end = volume_starts[position + 1][0]
        else:
            volume_end = len(lines)

        for index in range(volume_start + 1, volume_end):
            parsed_date = parse_date(lines, index, volume_end)
            if parsed_date is None:
                continue
            date, date_end = parsed_date
            title, title_start = extract_title(lines, index, volume_start)
            if not is_real_title(title):
                continue

            documents.append(
                Document(
                    doc_id=len(documents),
                    volume=volume_number,
                    title=title,
                    date=date,
                    year=chinese_year(date),
                    title_start=title_start,
                    date_end=date_end,
                    region_end=volume_end,
                )
            )

    # The next title starts the next document; the appendix is kept in source
    # order even though its date is earlier than the surrounding articles.
    for position, document in enumerate(documents):
        if position + 1 < len(documents):
            document.region_end = documents[position + 1].title_start

    return documents


def extract_body(lines: list[str], document: Document) -> str:
    """Return cleaned article text without title, date, or footnote section."""
    end = document.region_end
    for index in range(document.date_end + 1, document.region_end):
        if NOTE_HEADING_RE.match(lines[index].strip()):
            end = index
            break

    body = "\n".join(lines[document.date_end + 1 : end])
    body = FOOTNOTE_MARK_RE.sub("", body)
    body = body.replace("〔", "").replace("〕", "").replace("*", "")
    return body.strip()


def tokenize(text: str, stopwords: set[str]) -> list[str]:
    """Tokenize with jieba, keeping 2+ character content words."""
    tokens: list[str] = []
    for token in jieba.lcut(text):
        token = token.strip()
        if len(token) < 2:
            continue
        if token in stopwords:
            continue
        # Drop punctuation, numbers, and other non-Chinese fragments.
        if not CJK_RE.search(token):
            continue
        tokens.append(token)
    return tokens


def build_model(
    documents: list[Document], stopwords: set[str]
) -> tuple[list[Document], LDAGibbsSampler]:
    kept = [document for document in documents if len(document.tokens) >= 100]
    model = LDAGibbsSampler(
        n_topics=10,
        iterations=200,
        random_state=42,
        min_word_count=5,
        min_word_length=2,
        stopwords=stopwords,
    )
    model.fit([document.tokens for document in kept])
    return kept, model


def decade_averages(
    kept: list[Document], model: LDAGibbsSampler
) -> tuple[list[int], list[int], np.ndarray]:
    """Average each topic's proportion over the documents in each decade."""
    if len(model.theta) != len(kept):
        raise ValueError(
            "Model/document count mismatch: some documents were dropped during "
            "vocabulary filtering, so topic proportions cannot be mapped back."
        )
    groups: dict[int, list[int]] = {}
    for doc_id, document in enumerate(kept):
        decade = (document.year // 10) * 10
        groups.setdefault(decade, []).append(doc_id)

    decades = sorted(groups)
    counts = [len(groups[decade]) for decade in decades]
    averages = np.vstack(
        [model.theta[groups[decade]].mean(axis=0) for decade in decades]
    )
    return decades, counts, averages


def write_decade_table(
    path: Path,
    decades: list[int],
    counts: list[int],
    averages: np.ndarray,
) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(
            "decade\tn_docs\t"
            + "\t".join(f"topic_{topic}" for topic in range(averages.shape[1]))
            + "\n"
        )
        for decade, count, row in zip(decades, counts, averages):
            values = "\t".join(f"{value:.6f}" for value in row)
            handle.write(f"{decade}s\t{count}\t{values}\n")


def plot_topics_by_decade(
    kept: list[Document], model: LDAGibbsSampler, output_path: Path
) -> tuple[list[int], list[int], np.ndarray]:
    """Create the stacked bar chart of mean topic proportions by decade."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        from qhchina.helpers import load_font

        load_font()
    except Exception as exc:  # pragma: no cover - depends on network/cache
        print(f"Warning: could not load qhchina font ({exc}); using system CJK fonts.")
        matplotlib.rcParams["font.sans-serif"] = [
            "Noto Sans CJK SC",
            "Noto Sans CJK TC",
            "SimHei",
            "sans-serif",
        ]
        matplotlib.rcParams["font.family"] = "sans-serif"
        matplotlib.rcParams["axes.unicode_minus"] = False

    decades, counts, averages = decade_averages(kept, model)
    topic_words = model.get_topics(n_words=3)

    x = np.arange(len(decades))
    cmap = plt.get_cmap("tab10")
    colors = [cmap(topic) for topic in range(model.n_topics)]

    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    bottom = np.zeros(len(decades))
    for topic in range(model.n_topics):
        label = (
            f"主题 {topic}："
            + "、".join(word for word, _ in topic_words[topic])
        )
        ax.bar(
            x,
            averages[:, topic],
            bottom=bottom,
            width=0.72,
            color=colors[topic],
            edgecolor="white",
            linewidth=0.6,
            label=label,
        )
        bottom += averages[:, topic]

    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{decade}年代\n(n={count})" for decade, count in zip(decades, counts)]
    )
    ax.set_xlabel("年代")
    ax.set_ylabel("平均主题比例")
    ax.set_ylim(0, 1)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_yticklabels([f"{int(value * 100)}%" for value in np.arange(0, 1.01, 0.2)])
    ax.set_title("各年代平均主题比例（LDA，10 个主题）", pad=14)
    ax.grid(axis="y", color="#999999", alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        title="主题编号：Top 3 词",
        bbox_to_anchor=(1.01, 1.0),
        loc="upper left",
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return decades, counts, averages


def write_html_report(
    path: Path,
    documents: list[Document],
    kept: list[Document],
    model: LDAGibbsSampler,
    decades: list[int],
    counts: list[int],
    averages: np.ndarray,
    chart_path: Path,
) -> None:
    """Write a self-contained HTML report with tables and the embedded chart."""
    topic_colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    def color_for(topic: int) -> str:
        return topic_colors[topic % len(topic_colors)]

    def rgb(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    topics = model.get_topics(n_words=10)
    top3 = [topic[:3] for topic in topics]
    dropped = [document for document in documents if len(document.tokens) < 100]
    volume_all = Counter(document.volume for document in documents)
    volume_kept = Counter(document.volume for document in kept)

    min_year = min(document.year for document in documents)
    max_year = max(document.year for document in documents)
    n_docs = len(documents)
    n_kept = len(kept)
    n_dropped = len(dropped)
    n_volumes = len(volume_all)

    stats = [
        (f"{n_docs}", "解析文档"),
        (f"{n_kept}", "进入 LDA"),
        (f"{n_dropped}", "长度不足剔除"),
        (f"{model.n_topics}", "主题数"),
        (f"{model.vocabulary_size:,}", "词表大小"),
        (f"{n_volumes}", "卷数"),
    ]
    stats_html = "".join(
        f'<div class="stat"><span class="stat-number">{value}</span>'
        f'<span class="stat-label">{label}</span></div>'
        for value, label in stats
    )

    topic_cards = []
    for topic in range(model.n_topics):
        color = color_for(topic)
        chips = "".join(
            f'<span class="chip"><span class="chip-word">{escape(word)}</span>'
            f'<span class="chip-prob">{probability * 100:.2f}%</span></span>'
            for word, probability in topics[topic]
        )
        docs_html = []
        for rank, (doc_id, probability) in enumerate(
            model.get_top_documents(topic, n_docs=2), start=1
        ):
            document = kept[doc_id]
            docs_html.append(
                f'<li><span class="doc-rank">{rank}</span>'
                f'<span class="doc-title">{escape(document.clean_title)}</span>'
                f'<span class="doc-year">{document.year}</span>'
                f'<span class="doc-prob">p = {probability:.3f}</span></li>'
            )
        topic_cards.append(
            f"""
            <article class="topic-card" style="--topic-color:{color}">
              <div class="topic-card-head">
                <div class="topic-number"><span class="topic-dot"></span>主题 {topic}</div>
                <div class="topic-top3">{escape("、".join(word for word, _ in top3[topic]))}</div>
              </div>
              <div class="word-chips">{chips}</div>
              <div class="typical">
                <h4>典型文档</h4>
                <ol>{"".join(docs_html)}</ol>
              </div>
            </article>
            """
        )

    matrix_head = "".join(
        f'<th><span class="mini-dot" style="background:{color_for(topic)}"></span>主题 {topic}</th>'
        for topic in range(model.n_topics)
    )
    matrix_rows = []
    for decade, count, row in zip(decades, counts, averages):
        max_topic = int(np.argmax(row))
        cells = []
        for topic, value in enumerate(row):
            r, g, b = rgb(color_for(topic))
            alpha = 0.06 + 0.58 * min(float(value) / 0.45, 1.0)
            text_color = "#ffffff" if value > 0.32 else "#27303a"
            max_class = ' class="is-max"' if topic == max_topic else ""
            cells.append(
                f'<td{max_class} style="background:rgba({r},{g},{b},{alpha:.2f});'
                f'color:{text_color}">{value * 100:.1f}%</td>'
            )
        matrix_rows.append(
            f'<tr><th scope="row">{decade}年代</th><td class="n-cell">{count}</td>'
            f'{"".join(cells)}</tr>'
        )

    highlights = []
    for decade, count, row in zip(decades, counts, averages):
        order = np.argsort(-row)[:2]
        parts = [
            f"主题 {int(topic)}（{row[topic] * 100:.1f}%；"
            f"{escape('、'.join(word for word, _ in top3[int(topic)]))}）"
            for topic in order
        ]
        highlights.append(
            f"<li><strong>{decade}年代</strong>（n={count}）："
            f"{'；'.join(parts)}。</li>"
        )

    volume_rows = []
    for volume in sorted(volume_all):
        total = volume_all[volume]
        used = volume_kept.get(volume, 0)
        volume_rows.append(
            f"<tr><td>第 {volume} 卷</td><td>{total}</td><td>{used}</td>"
            f"<td>{total - used}</td></tr>"
        )
    volume_rows.append(
        f'<tr class="total-row"><td>合计</td><td>{n_docs}</td><td>{n_kept}</td>'
        f"<td>{n_dropped}</td></tr>"
    )

    dropped_rows = "".join(
        f"<tr><td>{document.volume}</td><td>{document.year}</td>"
        f"<td>{escape(document.clean_title)}</td><td>{len(document.tokens)}</td></tr>"
        for document in dropped
    )

    chart_base64 = base64.b64encode(chart_path.read_bytes()).decode("ascii")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    css = r"""
    :root {
      --bg: #f3eee5;
      --paper: #fffdf8;
      --ink: #202a33;
      --muted: #6d747b;
      --line: #e6ded1;
      --accent: #a52a2a;
      --accent-soft: #f3e3df;
      --serif: "Noto Serif CJK SC", "Noto Serif CJK TC", "Source Han Serif SC",
               "Songti SC", "SimSun", serif;
      --sans: "Noto Sans CJK SC", "Noto Sans CJK TC", "Source Han Sans SC",
              "Microsoft YaHei", "PingFang SC", sans-serif;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 0%, rgba(165,42,42,.08), transparent 32rem),
        radial-gradient(circle at 100% 20%, rgba(31,119,180,.06), transparent 30rem),
        var(--bg);
      font-family: var(--sans);
      line-height: 1.75;
      -webkit-font-smoothing: antialiased;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .hero {
      position: relative;
      overflow: hidden;
      color: #fbf7ef;
      background:
        radial-gradient(circle at 85% 12%, rgba(255,255,255,.09), transparent 24rem),
        linear-gradient(135deg, #17202a 0%, #253341 58%, #3b2a2a 100%);
      padding: 4.5rem 1.5rem 3.5rem;
    }
    .hero::after {
      content: "LDA";
      position: absolute;
      right: 3vw;
      bottom: -1.8rem;
      font-family: var(--serif);
      font-size: clamp(7rem, 18vw, 16rem);
      line-height: 1;
      color: rgba(255,255,255,.035);
      letter-spacing: -.08em;
      pointer-events: none;
    }
    .hero-inner, .wrap { width: min(1160px, calc(100% - 2rem)); margin: 0 auto; }
    .eyebrow {
      color: #e7b7a9;
      font-size: .78rem;
      letter-spacing: .18em;
      text-transform: uppercase;
      font-weight: 700;
    }
    h1, h2, h3, h4 { font-family: var(--serif); line-height: 1.25; }
    h1 {
      margin: .45rem 0 .6rem;
      font-size: clamp(2.2rem, 5vw, 4rem);
      font-weight: 700;
      letter-spacing: -.02em;
    }
    .subtitle {
      margin: 0;
      max-width: 46rem;
      color: #d8d2c8;
      font-size: clamp(1rem, 1.8vw, 1.2rem);
    }
    .meta { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.35rem; }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: .4rem;
      padding: .3rem .7rem;
      border: 1px solid rgba(255,255,255,.2);
      border-radius: 999px;
      color: #efe9df;
      font-size: .8rem;
      background: rgba(255,255,255,.04);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: .8rem;
      margin-top: 2.4rem;
    }
    .stat {
      padding: 1rem .9rem .85rem;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 14px;
      background: rgba(255,255,255,.06);
      backdrop-filter: blur(4px);
    }
    .stat-number {
      display: block;
      font-family: var(--serif);
      font-size: clamp(1.5rem, 3vw, 2.1rem);
      font-weight: 700;
      line-height: 1.1;
    }
    .stat-label { display: block; margin-top: .25rem; color: #cfc8bd; font-size: .76rem; }
    .toc {
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(255,253,248,.9);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(10px);
    }
    .toc-inner {
      width: min(1160px, calc(100% - 2rem));
      margin: 0 auto;
      display: flex;
      gap: 1.2rem;
      overflow-x: auto;
      padding: .75rem 0;
      white-space: nowrap;
      font-size: .85rem;
    }
    .toc a { color: #4b555e; font-weight: 600; }
    .toc a:hover { color: var(--accent); text-decoration: none; }
    main { padding: 2.2rem 0 4rem; }
    .section {
      margin: 0 0 1.4rem;
      padding: clamp(1.2rem, 3vw, 2rem);
      border: 1px solid var(--line);
      border-radius: 20px;
      background: var(--paper);
      box-shadow: 0 18px 45px rgba(44,32,20,.06);
    }
    .section-head { margin-bottom: 1.2rem; }
    .section-kicker {
      color: var(--accent);
      font-size: .74rem;
      font-weight: 800;
      letter-spacing: .14em;
      text-transform: uppercase;
    }
    h2 { margin: .15rem 0 .35rem; font-size: clamp(1.55rem, 3vw, 2.15rem); }
    .section-intro { margin: 0; color: var(--muted); max-width: 58rem; }
    .method-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: .9rem;
    }
    .method {
      padding: 1rem;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fbf8f2;
    }
    .method-num {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.8rem;
      height: 1.8rem;
      border-radius: 50%;
      color: #fff;
      background: var(--accent);
      font-weight: 800;
      font-size: .8rem;
    }
    .method h3 { margin: .55rem 0 .25rem; font-size: 1rem; }
    .method p { margin: 0; color: var(--muted); font-size: .86rem; }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: .86rem; }
    th, td { padding: .56rem .7rem; border-bottom: 1px solid #eee7db; text-align: left; }
    thead th {
      position: sticky;
      top: 0;
      background: #f6f1e8;
      color: #4b555e;
      font-size: .78rem;
      letter-spacing: .02em;
      white-space: nowrap;
    }
    tbody tr:last-child td, tbody tr:last-child th { border-bottom: 0; }
    .total-row { font-weight: 800; background: #faf5ec; }
    .topic-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
    }
    .topic-card {
      display: flex;
      flex-direction: column;
      gap: .8rem;
      padding: 1.05rem 1.05rem 1rem;
      border: 1px solid var(--line);
      border-top: 4px solid var(--topic-color);
      border-radius: 14px;
      background: #fffefa;
      box-shadow: 0 8px 22px rgba(44,32,20,.035);
    }
    .topic-card-head { display: flex; align-items: baseline; justify-content: space-between; gap: .8rem; }
    .topic-number {
      display: inline-flex;
      align-items: center;
      gap: .42rem;
      font-family: var(--serif);
      font-size: 1.15rem;
      font-weight: 800;
      white-space: nowrap;
    }
    .topic-dot { width: .7rem; height: .7rem; border-radius: 50%; background: var(--topic-color); }
    .topic-top3 { color: var(--muted); font-size: .78rem; text-align: right; }
    .word-chips { display: flex; flex-wrap: wrap; gap: .4rem; }
    .chip {
      display: inline-flex;
      align-items: baseline;
      gap: .3rem;
      padding: .25rem .55rem;
      border: 1px solid var(--line);
      border-left: 3px solid var(--topic-color);
      border-radius: 999px;
      background: #fbf8f2;
      font-size: .8rem;
    }
    .chip-word { font-weight: 700; }
    .chip-prob { color: var(--muted); font-size: .68rem; }
    .typical { margin-top: auto; padding-top: .35rem; border-top: 1px dashed #e5dccd; }
    .typical h4 { margin: .15rem 0 .35rem; color: var(--muted); font-family: var(--sans); font-size: .74rem; letter-spacing: .1em; text-transform: uppercase; }
    .typical ol { margin: 0; padding: 0; list-style: none; display: grid; gap: .3rem; }
    .typical li { display: grid; grid-template-columns: 1.2rem 1fr auto auto; gap: .45rem; align-items: baseline; font-size: .84rem; }
    .doc-rank { color: var(--topic-color); font-weight: 800; }
    .doc-title { min-width: 0; }
    .doc-year { color: var(--muted); font-variant-numeric: tabular-nums; }
    .doc-prob { color: var(--muted); font-size: .72rem; font-variant-numeric: tabular-nums; }
    figure { margin: 0; }
    .chart-frame { padding: .5rem; border: 1px solid var(--line); border-radius: 16px; background: #fff; }
    .chart-frame img { display: block; width: 100%; height: auto; border-radius: 12px; }
    figcaption { margin-top: .7rem; color: var(--muted); font-size: .82rem; }
    .matrix-wrap { margin-top: 1.2rem; }
    .matrix { font-size: .78rem; }
    .matrix th, .matrix td { padding: .45rem .5rem; text-align: center; white-space: nowrap; }
    .matrix th:first-child, .matrix td:first-child { text-align: left; position: sticky; left: 0; z-index: 1; background: #fbf8f2; }
    .matrix td { font-variant-numeric: tabular-nums; border-left: 1px solid rgba(255,255,255,.28); }
    .matrix td.is-max { font-weight: 800; outline: 2px solid rgba(32,42,51,.18); outline-offset: -2px; }
    .matrix .n-cell { color: var(--muted); }
    .mini-dot { display: inline-block; width: .55rem; height: .55rem; margin-right: .25rem; border-radius: 50%; vertical-align: .02em; }
    .highlights { margin: 1.1rem 0 0; padding-left: 1.2rem; }
    .highlights li { margin: .35rem 0; }
    .note {
      margin-top: 1rem;
      padding: .75rem .9rem;
      border-left: 3px solid var(--accent);
      background: var(--accent-soft);
      border-radius: 0 10px 10px 0;
      color: #5f2d29;
      font-size: .84rem;
    }
    details { margin-top: 1rem; border: 1px solid var(--line); border-radius: 12px; background: #fbf8f2; }
    summary { cursor: pointer; padding: .8rem 1rem; font-weight: 700; color: #4b555e; }
    details .table-wrap { margin: 0 1rem 1rem; }
    .file-list { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; }
    .file-list li { padding: .75rem .9rem; border: 1px solid var(--line); border-radius: 10px; background: #fbf8f2; }
    .file-list a { font-weight: 700; }
    .file-list span { display: block; color: var(--muted); font-size: .78rem; }
    code { padding: .1rem .35rem; border-radius: 5px; background: #f1ece2; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .82em; }
    footer { padding: 1.5rem 0 3rem; color: var(--muted); font-size: .78rem; text-align: center; }
    @media (max-width: 900px) {
      .stats { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .method-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .topic-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 560px) {
      .hero { padding: 3rem 1.1rem 2.2rem; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .method-grid { grid-template-columns: 1fr; }
      .file-list { grid-template-columns: 1fr; }
      .typical li { grid-template-columns: 1rem 1fr; }
      .doc-year, .doc-prob { grid-column: 2; }
    }
    @media print {
      body { background: #fff; }
      .toc { display: none; }
      .hero { background: #17202a !important; print-color-adjust: exact; }
      .section { box-shadow: none; break-inside: avoid; }
      .topic-card { break-inside: avoid; }
    }
    """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>毛泽东选集 · LDA 主题分析</title>
  <style>{css}</style>
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <div class="eyebrow">DH502 · Text Mining · LDA</div>
      <h1>毛泽东选集文本主题分析</h1>
      <p class="subtitle">从 1925 到 1976：文档切分、词频清洗与 10 主题 LDA 模型</p>
      <div class="meta">
        <span class="pill">语料：毛泽东选集（1–5 卷 + 静火版 6–7 卷）</span>
        <span class="pill">{min_year}–{max_year}</span>
        <span class="pill">Gibbs Sampling · 200 iterations</span>
        <span class="pill">random_state = 42</span>
      </div>
      <div class="stats">{stats_html}</div>
    </div>
  </header>

  <nav class="toc" aria-label="目录">
    <div class="toc-inner">
      <a href="#method">方法</a>
      <a href="#corpus">文档与过滤</a>
      <a href="#topics">10 个主题</a>
      <a href="#decades">年代趋势</a>
      <a href="#observations">观察</a>
      <a href="#dropped">剔除文档</a>
      <a href="#files">文件</a>
    </div>
  </nav>

  <main class="wrap">
    <section class="section" id="method">
      <div class="section-head">
        <div class="section-kicker">Method</div>
        <h2>方法</h2>
        <p class="section-intro">原始文本中每篇文章由标题、括号内的日期和正文组成。切分时利用日期行与标题前的固定空行结构；脚注统一在“注　　释”处截断。</p>
      </div>
      <div class="method-grid">
        <div class="method"><span class="method-num">1</span><h3>文档切分</h3><p>识别中文数字日期行，向上回溯标题块；以标题前的五空行作为文档边界，排除“序”“跋”“引言”“结论”等小节日期。</p></div>
        <div class="method"><span class="method-num">2</span><h3>脚注清洗</h3><p>正文在“注　　释”标题处截断，并删除行内 <code>〔12〕</code> 形式的数字脚注标记。附录《关于若干历史问题的决议》保留为 1 篇。</p></div>
        <div class="method"><span class="method-num">3</span><h3>分词与过滤</h3><p>使用 <code>jieba</code> 分词，保留长度 ≥ 2 的词；用 <code>qhchina.load_stopwords("zh_sim")</code> 去除停用词；剔除少于 100 个 token 的文档。</p></div>
        <div class="method"><span class="method-num">4</span><h3>主题模型</h3><p><code>LDAGibbsSampler</code>，10 个主题，200 次迭代，<code>random_state=42</code>，<code>min_word_count=5</code>，<code>min_word_length=2</code>。</p></div>
      </div>
      <div class="note">语料来源：<a href="https://raw.githubusercontent.com/mcjkurz/qhchina-data/main/corpora/%E9%80%89%E9%9B%86/%E6%AF%9B%E6%B3%BD%E4%B8%9C%E9%80%89%E9%9B%86.txt">qhchina-data / 毛泽东选集.txt</a>。第 6–7 卷为静火版，非官方五卷本的一部分；本报告按原文件全部解析。</div>
    </section>

    <section class="section" id="corpus">
      <div class="section-head">
        <div class="section-kicker">Corpus</div>
        <h2>文档数量与长度过滤</h2>
        <p class="section-intro">共解析 {n_docs} 篇文档；其中 {n_kept} 篇达到 100 token 门槛并进入 LDA，{n_dropped} 篇因过短被剔除。最终词表包含 {model.vocabulary_size:,} 个词。</p>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>卷次</th><th>解析文档</th><th>进入 LDA</th><th>剔除</th></tr></thead>
          <tbody>{"".join(volume_rows)}</tbody>
        </table>
      </div>
      <div class="note">剔除的文档主要是短电报、题词、批示和口号。它们仍然保留在 <code>documents.tsv</code> 中，只是不参与主题模型估计。</div>
    </section>

    <section class="section" id="topics">
      <div class="section-head">
        <div class="section-kicker">Topics</div>
        <h2>10 个 LDA 主题</h2>
        <p class="section-intro">每个主题展示概率最高的 10 个词（括号内为词在主题中的概率）以及主题概率最高的 2 篇文档。主题编号本身没有固定语义，顺序由模型输出决定。</p>
      </div>
      <div class="topic-grid">{"".join(topic_cards)}</div>
    </section>

    <section class="section" id="decades">
      <div class="section-head">
        <div class="section-kicker">Decades</div>
        <h2>年代平均主题比例</h2>
        <p class="section-intro">先对每篇文档的主题分布取年代平均，再按主题堆叠；每个年代柱子的总高度为 100%。柱子下方的 n 为该年代进入 LDA 的文档数。</p>
      </div>
      <figure>
        <div class="chart-frame">
          <img src="data:image/png;base64,{chart_base64}" alt="各年代平均主题比例堆叠柱状图">
        </div>
        <figcaption>图例给出每个主题的编号与 Top 3 词；堆叠顺序与图例顺序一致。原始图片：<a href="topics_by_decade.png">topics_by_decade.png</a>。</figcaption>
      </figure>
      <div class="matrix-wrap table-wrap">
        <table class="matrix">
          <thead><tr><th>年代</th><th>n</th>{matrix_head}</tr></thead>
          <tbody>{"".join(matrix_rows)}</tbody>
        </table>
      </div>
      <div class="note">表格数值为百分比；每行最大值加粗显示。1920s 仅有 {counts[0]} 篇文档，1970s 为 {counts[-1]} 篇，这两个年代的均值波动应谨慎解读。</div>
    </section>

    <section class="section" id="observations">
      <div class="section-head">
        <div class="section-kicker">Reading</div>
        <h2>可以读到什么</h2>
        <p class="section-intro">以下只是对平均主题比例的描述性概括，不是因果判断；主题词和典型文档比主题编号更重要。</p>
      </div>
      <ul class="highlights">{"".join(highlights)}</ul>
      <div class="note">LDA 的主题比例受文档长度、语料构成和分词词典影响。短文档被剔除后，剩余文本更偏向长篇文章、报告和讲话。</div>
    </section>

    <section class="section" id="dropped">
      <div class="section-head">
        <div class="section-kicker">Excluded</div>
        <h2>因长度不足被剔除的文档</h2>
        <p class="section-intro">共 {n_dropped} 篇；阈值为清洗后少于 100 个 token。</p>
      </div>
      <details>
        <summary>展开查看 {n_dropped} 篇文档</summary>
        <div class="table-wrap">
          <table>
            <thead><tr><th>卷</th><th>年份</th><th>标题</th><th>tokens</th></tr></thead>
            <tbody>{dropped_rows}</tbody>
          </table>
        </div>
      </details>
    </section>

    <section class="section" id="files">
      <div class="section-head">
        <div class="section-kicker">Outputs</div>
        <h2>文件</h2>
        <p class="section-intro">所有结果都可以从同一脚本复现；HTML 中的图表已内嵌，单个文件即可分享。</p>
      </div>
      <ul class="file-list">
        <li><a href="documents.tsv">documents.tsv</a><span>388 篇文档的卷次、年份、日期、标题、token 数与是否入模</span></li>
        <li><a href="lda_topics.txt">lda_topics.txt</a><span>主题词概率、典型文档、剔除清单的纯文本版</span></li>
        <li><a href="topics_by_decade.tsv">topics_by_decade.tsv</a><span>年代 × 主题的平均比例矩阵</span></li>
        <li><a href="topics_by_decade.png">topics_by_decade.png</a><span>年代平均主题比例堆叠柱状图</span></li>
      </ul>
      <div class="note">复现命令：<code>topic-modeling/.venv/bin/python topic-modeling/analyze_mao.py</code></div>
    </section>
  </main>

  <footer>
    <div class="wrap">生成于 {generated} · 毛泽东选集 LDA 主题分析 · 388 篇解析 / 350 篇入模</div>
  </footer>
</body>
</html>
"""

    path.write_text(html, encoding="utf-8")


def format_report(
    documents: list[Document],
    kept: list[Document],
    model: LDAGibbsSampler,
) -> str:
    lines: list[str] = []
    dropped = [document for document in documents if len(document.tokens) < 100]

    lines.append("Mao Zedong Selected Works — LDA topic model")
    lines.append("=" * 60)
    lines.append(f"Documents parsed from source: {len(documents)}")
    lines.append(f"Documents with >= 100 tokens: {len(kept)}")
    lines.append(f"Documents dropped (< 100 tokens): {len(dropped)}")
    lines.append(f"Vocabulary after min_word_count=5: {model.vocabulary_size}")
    lines.append("Settings: 10 topics, 200 Gibbs iterations, random_state=42")
    lines.append("")

    lines.append("Documents per volume:")
    all_counts = Counter(document.volume for document in documents)
    kept_counts = Counter(document.volume for document in kept)
    lines.append("  volume  parsed  kept")
    for volume in sorted(all_counts):
        lines.append(f"  {volume:>6}  {all_counts[volume]:>6}  {kept_counts[volume]:>4}")
    lines.append("  " + "-" * 20)
    lines.append(f"  {'total':>6}  {len(documents):>6}  {len(kept):>4}")
    lines.append("")

    if dropped:
        lines.append("Dropped documents (< 100 tokens):")
        for document in dropped:
            lines.append(
                f"  [{document.volume}-{document.doc_id:03d}] "
                f"{document.clean_title} ({document.year}) — {len(document.tokens)} tokens"
            )
        lines.append("")

    topics = model.get_topics(n_words=10)
    for topic_id, topic_words in enumerate(topics):
        lines.append(f"Topic {topic_id}")
        lines.append(
            "  Words: "
            + ", ".join(f"{word} ({prob:.4f})" for word, prob in topic_words)
        )
        lines.append("  Typical documents:")
        for rank, (doc_id, probability) in enumerate(
            model.get_top_documents(topic_id, n_docs=2), start=1
        ):
            document = kept[doc_id]
            lines.append(
                f"    {rank}. {document.clean_title} ({document.year}) "
                f"[p={probability:.3f}]"
            )
        lines.append("")

    return "\n".join(lines)


def write_documents_tsv(path: Path, documents: list[Document], kept_ids: set[int]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(
            "doc_id\tvolume\tyear\tdate\ttitle\ttokens\tused_in_lda\n"
        )
        for document in documents:
            title = document.clean_title.replace("\t", " ")
            handle.write(
                f"{document.doc_id}\t{document.volume}\t{document.year}\t"
                f"{document.date}\t{title}\t{len(document.tokens)}\t"
                f"{'yes' if document.doc_id in kept_ids else 'no'}\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the raw corpus if --raw does not exist.",
    )
    args = parser.parse_args()

    if not args.raw.exists():
        if not args.download:
            raise SystemExit(
                f"{args.raw} does not exist; re-run with --download or place the file there."
            )
        args.raw.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {RAW_URL}")
        urllib.request.urlretrieve(RAW_URL, args.raw)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    lines = read_lines(args.raw)
    documents = parse_documents(lines)
    print(f"Parsed {len(documents)} documents; tokenizing ...")

    stopwords = load_stopwords("zh_sim")
    for document in documents:
        document.body = extract_body(lines, document)
        document.tokens = tokenize(document.body, stopwords)

    kept, model = build_model(documents, stopwords)
    report = format_report(documents, kept, model)

    report_path = args.out_dir / "lda_topics.txt"
    report_path.write_text(report, encoding="utf-8")
    write_documents_tsv(
        args.out_dir / "documents.tsv",
        documents,
        {document.doc_id for document in kept},
    )

    decades, counts, averages = plot_topics_by_decade(
        kept, model, args.out_dir / "topics_by_decade.png"
    )
    write_decade_table(
        args.out_dir / "topics_by_decade.tsv", decades, counts, averages
    )
    write_html_report(
        args.out_dir / "report.html",
        documents,
        kept,
        model,
        decades,
        counts,
        averages,
        args.out_dir / "topics_by_decade.png",
    )

    print(report)
    print(f"Wrote {report_path}")
    print(f"Wrote {args.out_dir / 'documents.tsv'}")
    print(f"Wrote {args.out_dir / 'topics_by_decade.png'}")
    print(f"Wrote {args.out_dir / 'topics_by_decade.tsv'}")
    print(f"Wrote {args.out_dir / 'report.html'}")


if __name__ == "__main__":
    main()
