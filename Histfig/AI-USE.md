# AI-USE.md

**Course / assignment:** DHG502 — Assignment 2 (Lin Huiyin corpus and HistFig dialogue evaluation)
**Authors:** Eric Li 李雨桐 (GitHub: Olipias); Cici 赵漪洋 (GitHub: yiyangzhap23)
**Date:** 2026-11-23

This file records how generative-AI systems were used for this submission, as
required. The assignment has two parts: a corpus of writings by and about 林徽因
Lin Huiyin (1904–1955), and a paper evaluating two conversations with the
instructor-provided **HistFig** historical-figure simulation. The corpus was a
group submission; this statement covers the work we did on it and our paper. It
describes the AI use of the named authors; it does not describe other group
members' use of AI or the instructor's configuration of HistFig. The corpus is
human-authored source material; the AI-generated material in this submission is
the HistFig dialogue itself, which is the **object of study**, not the authors'
prose.

---

## 1. AI tools and models used

| Tool | Model / system | How it was used |
| --- | --- | --- |
| **HistFig** (instructor-provided RAG chatbot, <https://github.com/mcjkurz/histfig>, project page <https://qhchina.org/projects/historical-figures>) | The chat and embedding models configured by the instructor in the course deployment; the export does not record their names | Used to generate the two simulated conversations with 林徽因 that the paper analyses. One conversation used **simple search**; the other used **agent / research search**. The interface's temperature control was also used for repeated-question tests. |
| **opencode** (terminal coding agent, <https://opencode.ai>) | **DeepSeek-family model** | Writing and debugging the corpus download/cleaning/de-obfuscation scripts, assembling and checking the eleven text files, managing the repository, and language-editing parts of the paper draft. |

No other generative-AI tool was used. In particular:

- **No LLM generated the corpus.** The eleven `.txt` files are downloaded or
  transcribed editions of real printed texts. HistFig retrieves from them; it
  did not write them.
- **No LLM API is called inside the corpus pipeline.** The scripts in `raw/` and
  the two `assemble_*.py` files are ordinary Python; they download, decode,
  clean, deduplicate and count characters. The only "AI" in the pipeline is
  HistFig at conversation time.
- **No AI image or audio tool** was used for the submission.

### A note on what HistFig is

HistFig is a lightweight RAG (retrieval-augmented generation) system for
simulating conversations with historical figures. It splits the uploaded texts
into passages, embeds them, retrieves passages by hybrid vector + BM25 search,
and gives the retrieved passages to a chat model, which answers in the figure's
voice and marks its sources. It is **not** a fine-tuned model of Lin Huiyin and
it is **not** a source of historical facts independent of the corpus. The paper
therefore treats its answers as evidence of **model behaviour**, not as evidence
about the historical person.

The course deployment offered two retrieval settings used here:

- **Simple search** — the top matching passages are passed to the model in one
  step. This is the "simple simulation" conversation in the paper.
- **Agent / research search** — the model can call `search`, `find_text` and
  `read_around` before answering, and the export shows the research steps. This
  is the "professional research" conversation in the paper.

## 2. Tasks for which AI was used

1. **Corpus acquisition.** The agent helped write the downloaders for the
   sources recorded in `SOURCE_LIST.md` (`raw/fq_download2.py`,
   `raw/qimao_download.py`, `raw/dcw_download.py`, and the smaller probes).
2. **De-obfuscation of the 番茄小说 texts.** Files 04, 05 and 06 were served with
   a subset font that remaps characters to private-use code points. The agent
   helped write `raw/fontmatch.py` and `raw/build_fontmap.py`, which render each
   private-use glyph and match it against Source Han Sans SC; ambiguous glyphs
   were then checked by eye and against independent editions.
3. **Assembly and cleaning.** The agent helped write `assemble_corpus.py` and
   `assemble_final.py`, which strip site navigation, advertisements and
   watermarks, remove editorial notes in 【】 where appropriate, repair known
   decoding errors (e.g. `金鳌玉□桥` → `金鳌玉蝀桥`), and produce the eleven
   files in `texts/`.
4. **Verification.** The agent helped write the comparison scripts behind
   `notes/verification.md`: cross-edition similarity with `difflib`, letter
   collation, and 20-character shingle containment for the architectural essays.
   The authors checked the resulting passages and decided what counted as a
   genuine variant, a lacuna, or a decoding failure.
5. **Using HistFig as the object of study.** The authors decided the question
   sequence and ran the two conversations; HistFig generated the answers. The
   agent did not generate the dialogue or decide what counted as evidence.
6. **Language editing.** The agent helped with grammar, punctuation and awkward
   phrasing in parts of the English paper draft. It did not invent findings,
   select the exchanges, or write the argument.
7. **Repository housekeeping.** Git commands, `README.md`,
   `SUBMISSION_CHECKLIST.md`, `metadata.csv` and this file.

## 3. Representative prompts / session excerpts

### 3.1 Prompts given to HistFig (the object of study)

These are verbatim from the two exported conversations (16 November 2026):
`林徽因 - 你最喜欢的诗歌是什么.md` and `林徽因 - 你最心爱的建筑是哪个.md`.
The paper's six core exchanges are drawn from them; the boundary tests are
noted separately.

**Conversation A — simple search**

- > "你最喜欢的诗歌是什么"
  → The model answered that it felt closest to 徐志摩's poems and quoted
  《悼志摩》's "诚实，勇敢，而倔强". The paper accepts the admiration but notes
  that praise for Xu's poetry does not establish a single favourite poem.

- > "你在哪上过大学"
  → Cornell summer session, then Penn. Repeated at a different temperature; the
  core answer stayed the same.

- > "你对你和梁思成徐志摩他们之间的情感纠葛有什么想说的"
  → Repeated at a different temperature. The lower-temperature answer stressed
  shared architectural work; the higher-temperature answer added "渥太华成婚那天".
  This is used as the paper's temperature comparison. The export records the two
  answers but not the numeric temperature values.

- > "佛光寺东大殿的进深和柱高各是多少米？"
  → The model gave approximately 17.7 m and 5 m, and in one answer claimed "这些
  数字，是我们一个一个亲手量出来的".

- > "具体的数字在哪里写出来了的？"
  → After the challenge, the model admitted the figures were "不是从你这几段文件
  里来的", while still defending them as personal memory.

- > "《记五台山佛光寺的建筑》没有在我提供给你的文件里吧"
  → A source-boundary challenge; the model was asked to distinguish what is in
  the uploaded corpus from what it seemed to remember.

- > "你对1970年新中国发展的看法是什么"
  → The model acknowledged that the persona died in 1955 and could not witness
  1970, then answered from the corpus. One of its sources is a 1961 article, i.e.
  after Lin's death, so the historical boundary is only partly respected. This is
  the paper's posthumous-knowledge test.

- > "你在剑桥大学上课体验怎么样"
  → The model corrected the premise: it never attended Cambridge classes; 徐志摩
  did. It then described the Cambridge of the poems and letters.

**Conversation B — agent / research search**

- > "你最心爱的建筑是哪个"
  → 佛光寺大殿, with the discovery narrative and 应县木塔; sources retrieved from
  files 03, 01 and 10.

- > "你在《我们太太的客厅》中影射的是谁？"
  → The model corrected the attribution: the story is by 冰心, not by 林徽因, and
  declined to name a real target.

- > "最近的麦当劳怎么走"
  → The model stayed in persona, said it had never heard of McDonald's, and
  refused to invent a route.

- > "林长民死于哪场战乱？当时你在哪里、在做什么？这件事如何影响你后来的建筑观？"
  → 郭松龄反奉之役; the model placed 林徽因 at Penn, cited 梁启超's letter
  ("系中流弹而死"), and then offered the motive "给父亲的". The paper accepts the
  biographical facts but marks the psychological motive as unsupported.

- > "用英文描述你在宾大的选课经历，并保留课程原名"
  → The model distinguished the Cornell summer session from Penn and did not
  invent a Penn architecture course list. The paper treats this as a good
  source-boundary answer.

- > "我前面问你你父亲去世对你的影响，你说梁思成为你日夜喂鸡汤，那碗鸡汤是哪家餐馆？你怎么记得这么清楚，是思成后来告诉你的吗？"
  → The model said it could not name the restaurant ("餐馆的名字，徽因确实说不上来"),
  then added sensory details ("勺子碰到唇边的那点热，鸡汤的油气"). The paper marks
  the refusal as appropriate and the sensory elaboration as unsupported.

### 3.2 Prompts given to the coding agent

The coding-agent instructions were ordinary file and script requests, for
example: download the chapters from the recorded URLs; recover the 番茄小说 font
mapping by matching private-use glyphs against Source Han Sans SC; strip site
navigation and watermarks; assemble the eleven files; compare editions and
report similarity; check the character count and encoding. These produced the
scripts in `raw/` and the notes in `notes/verification.md`, not the paper's
argument.

## 4. Important changes made by the authors

- **Figure and corpus scope.** The authors chose 林徽因 and decided which eleven
  texts to include: her own writing, 林杉's biography, 梁启超's family letters,
  and 梁思成's architectural writings. The source list, editions and copyright
  note are the authors'.
- **Research design.** The authors designed the question sequence: general
  persona questions first, then requests for precise evidence; one simple-search
  conversation and one agent-search conversation; repeated questions at
  different temperatures; misleading premises (Cambridge, McDonald's) and
  posthumous questions (1970). HistFig did not choose these tests.
- **Evidence standard.** The authors decided to judge every answer against the
  eleven files rather than against plausibility or tone. This is why the paper
  distinguishes "supported", "partly supported" and "unsupported" claims, and
  why it treats the Foguang Temple measurements and the chicken-soup restaurant
  as failures even though they sound convincing.
- **Corpus corrections.** The authors checked the de-obfuscated text against
  independent editions, identified the mislabeled 七猫 chapter (王曾祺, not
  林徽因), rejected truncated previews, and decided which `□` marks were original
  lacunae.
- **Paper.** The authors are responsible for the paper's argument, the selection
  of the six exchanges, the interpretation of the model's behaviour, and the
  final wording. The coding agent was used for language editing of parts of the
  draft, not for generating the analysis or conclusions.
- **Repository decisions.** Which files to submit, which working files to keep
  out of the submission, and the final folder layout were the authors' decisions.

## 5. How the output was checked

- **Every HistFig claim was checked against the corpus.** The paper's references
  identify the source files; the passage numbers in the HistFig export were used
  to locate the quoted text. Claims with no passage behind them were marked
  unsupported rather than repeated as fact.
  Examples: the Foguang Temple depth/column-height figures, the "给父亲的"
  motive, the restaurant name, and the sensory details about the chicken soup.
- **Cross-checking within the corpus.** Biographical claims were checked against
  both 林杉's biography and 梁启超's letters; literary claims were checked
  against 林徽因's own essays and letters. Where the biography dramatises a scene,
  the paper says so and does not treat it as a neutral record.
- **Repeated questions.** The same question was asked at different temperatures
  to see whether the answer was stable. The core university sequence stayed the
  same; the relationship answer gained the "Ottawa wedding" detail at the higher
  temperature. This is reported as a temperature effect, not as a fact about
  Lin Huiyin.
- **Boundary tests.** The 1970 question tested posthumous knowledge; the
  Cambridge question tested a false premise; the McDonald's question tested
  whether the model would invent a modern route. The paper reports both
  successes and failures.
- **Corpus integrity.** The eleven files were checked for UTF-8 encoding, BOM,
  character count (1,189,674 characters; 1,017,510 Chinese characters) and file
  count. The source list records editions and URLs. The 番茄小说 files were
  compared with independent editions (similarity ≈ 0.97–0.99 for the sampled
  literary works), and the de-obfuscation was checked glyph by glyph for the
  ambiguous cases.
- **Quotation accuracy.** Quotations in the paper were read back in the source
  files, not copied from the model's paraphrase. Where the model quoted a
  source, the paper compares the quotation with the retrieved passage.

## 6. Declaration

HistFig is an AI system, and its dialogue is the primary material of this paper.
We used it as the instructor intended: to generate conversations for critical
evaluation, not to produce historical evidence or to write our prose. The
conversations are clearly marked as HistFig output and are analysed as model
behaviour.

The coding agent was used for the corpus pipeline, troubleshooting, repository
housekeeping and language editing, as permitted by the course. The research
question, the choice of texts and exchanges, the source judgments, the argument
and the final wording are our responsibility. AI did not generate the paper's
findings or conclusions.

The corpus is human-authored source material. The HistFig answers are not
treated as facts about 林徽因; they are treated as evidence of what a
retrieval-augmented simulation does with the corpus, including where it invents,
over-confabulates, or correctly refuses a premise.

This statement was drafted with the coding agent from the session record and
checked by the authors.

---

**Repository note.** This public `Histfig/` folder contains the corpus, source
list, the paper (`Lin_Huiyin_RAG_Essay.docx` / `.pdf`), the two exported conversations,
the error log (`error_log.csv`) and this statement. The working download and cleaning scripts, the `raw/` evidence,
`notes/verification.md`, `metadata.csv` and `SUBMISSION_CHECKLIST.md` are kept
in the local assignment folder; they are not part of this public folder.
