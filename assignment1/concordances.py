"""
DHG502 Assignment 1 -- concordance lines for the collocates discussed in report.md.

Reads the segmented corpus (data/data.txt) and prints, for every target word and
collocate named in the report, the sentences in which both occur, with the target
marked in [brackets].  Output: concordances.txt

Run from the assignment folder:  python3 concordances.py
"""

DATA = "data/data.txt"
OUT = "concordances.txt"

TARGETS = {
    "勾践": ["役", "范蠡", "东海", "下臣", "稽首", "再拜", "闻于", "不忍", "臣", "越王"],
    "夫差": ["北伐", "齐", "诸侯", "太子", "诛", "被", "君王", "波", "吴"],
}


def load_sentences(path):
    with open(path, encoding="utf-8") as fh:
        return [line.split() for line in fh if line.strip()]


def main():
    sentences = load_sentences(DATA)
    lines = []
    lines.append("Concordance lines for the collocates discussed in report.md")
    lines.append("=" * 64)
    lines.append("Source : data/data.txt  (Wu Yue Chunqiu, jieba-segmented)")
    lines.append("Format : one sentence per line; the target word is marked [like this].")
    lines.append("")

    for target, collocates in TARGETS.items():
        lines.append("")
        lines.append("#### target: " + target)
        for col in collocates:
            hits = [s for s in sentences if target in s and col in s]
            lines.append("")
            lines.append("---- %s + %s  (%d) " % (target, col, len(hits)) + "-" * 20)
            for s in hits:
                marked = ["[%s]" % t if t == target else t for t in s]
                lines.append("  " + " ".join(marked))

    text = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote %s (%d lines)" % (OUT, text.count("\n")))


if __name__ == "__main__":
    main()
