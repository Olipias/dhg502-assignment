# What Do the Collocations of Two Kings, 夫差 and 勾践, Reveal in the *Wu Yue Chunqiu*?

## Abstract and Source

This report intends to show what the book *Wu Yue Chunqiu* 《吴越春秋》 reveals
through a search of the collocations of two target words: 夫差, the king of Wu,
and 勾践, the king of Yue. With the help of AI to clean and sort the data, I then
calculated the statistical significance of the collocations. The results show
that the characteristics of the two kings are different — or, rather, that the
writer intends to describe them differently. The collocation results indicate
that 夫差's collocates form a profile of campaigns, overlordship, succession and
killing, whereas 勾践's collocates form a profile of submission, ministerial
reliance, hesitation and reputation-management. Combined with the fact that the
writer of the *Wu Yue Chunqiu* was born in 会稽山阴, the district mainly ruled by
Yue, the words suggest that the writer had a partiality for Yue, praising Yue for
its successful revenge while also criticizing the tragedy that befell its
ministers.

The main source of this report is the *Wu Yue Chunqiu* (a .txt file, 145 KB),
attributed to Zhao Ye of the Eastern Han. It is a literary reconstruction of
Spring-and-Autumn-period Wu–Yue history, and it is a public-domain
simplified-character edition taken from the Daizhige 殆知阁, a database of
ancient Chinese texts. It is not a critical edition, because the text is a
later, rhetorically shaped retelling rather than a contemporary record; its
content mainly concerns how the story is told, not merely what happened. After
cleaning, the corpus holds 2,470 sentences / 23,308 word tokens / 9,200 word
types.

## Processing and Method

First, the text of the *Wu Yue Chunqiu* was cleaned with an LLM agent. At the
very beginning I deleted the running head and the ten 卷 (chapter titles), and
then used jieba (a Chinese text segmenter) to segment the text, one line per
sentence, using the most common segmentation without forcing lengths, each word
separated by a space.

Because co-occurrence was measured with `find_collocates` from `qhchina` (a
toolkit for Chinese-language analysis), I chose the horizon of my target words to
be 5, meaning that I extracted the five words on each side of the target word,
requiring at least two window co-occurrences. I then used a contingency table to
calculate and sort the collocations by significance and strength. For each target
word, a 2×2 contingency table is built relative to the target.

Here, using the p-value alone (a p-value is the probability of seeing a
co-occurrence at least this strong if the two events were independent; if the
value is below 0.05, the pair can be called statistically significant) is not
enough to check whether a collocation is strongly connected to my target word,
because p measures reliability, not strength: it rises with both effect size and
frequency. Strength is reported separately by logDice and mutual information
(MI), which depend only on how tightly the two words are associated.

## Results and Interpretation

In the outcome, 勾践 occurs 44 times in 43 sentences and 夫差 23 times in 21
sentences. 夫差 has 9 significant collocates — 波, 北伐, 太子, 被, 诸侯, 君王, 齐,
诛, 吴 — while 勾践 has 11 — 东海, 范蠡, 役, 下臣, 稽首, 闻于, 再拜, 臣, 不忍,
二, 越王. The two share no significant collocates, which means the descriptions
of the two are strongly contrasted, at least in this book. In an early run, 卷 and
外传 were not cleaned completely and so became significant collocates; this was
later corrected. At the beginning I also required each sentence to be six words
long, but I changed it to segment sentences as they are commonly read and used,
and the candidates changed in that run. After that I found that the collocations
contained many function words such as 从 and 不, so I removed all the connectives
and deleted the collocations whose raw p-value was above 0.05.

Some collocates show a contradictory condition, as with 勾践 + 役 (役臣) and
范蠡. 役 is by far the strongest partner of 勾践 (MI 6.38, ratio 83), yet its
p-value (1.44×10⁻⁴) is no smaller than that of 范蠡 (1.43×10⁻⁴), whose MI is less
than half (2.92). Reading the original text, 役 occurs only twice, both times in
the phrase 东海役臣勾践 / 东海役臣臣孤勾践, which is why its MI is high; 范蠡
occurs 6 times throughout the whole story of Yue, for example 下臣勾践从小臣范蠡 /
乃使相国范蠡进曰：越王勾践窃有二遗女 / 范蠡从吴欲去，恐勾践未返. This means 范蠡
has less exclusivity than 役, but he is also significant with 勾践 because 范蠡 is
a narrative collocation. 役 refers to 勾践's self-degraded status after his defeat
by Wu, showing that this set of humiliating terms is a performative diplomatic
register. 范蠡 points to the relationship between 勾践 and his ministers: he is a
character rather than a term, appearing in various stories, so statistically he
is not as closely associated with 勾践. This is one part of the contradictory
ranking of significance and strength; other parts also show that this is
precisely why significance and strength must be read together.

The distinct profiles emerging from the collocation data strongly support the
hypothesis that the *Wu Yue Chunqiu* constructs sharply contrasting images for
the two kings. For 夫差, the significant collocates such as 北伐, 诸侯 and 诛 form
a clear semantic field of military aggression, hegemonic ambition and violent
retribution. These words paint a portrait of a ruler defined by external
conquest and a desire for dominance. Conversely, 勾践's collocations are
different: words such as 役, 稽首 and 不忍 reveal a narrative of submission,
humiliation and extreme patience, so 勾践's profile is diplomatic and
endurance-oriented. This is also supported by the bamboo manuscript *Yue gong qi
shi* 越公其事. Yuri Pines (*Early China* 45, 2022) argues that this text transmits
勾践's story as a didactic historical narrative centred on self-strengthening:
the king's recovery rests on his own example and conduct, not on impersonal law.
Pines identifies 勾践's "five policies": promoting agriculture, securing trust,
attracting immigrants, enlarging the army, and disciplining the people. That two
early texts (*Yue gong qi shi* and the *Wu Yue Chunqiu*) both show a positive view
of 勾践's endurance and revenge is precisely the character-centred framing that my
collocation results detect.

## Limitations

These results are suggestive, not decisive. For example, the window can be changed
to any other number; if it is set to 3 or 10, the significant collocations might
be different. Also, both target words I chose are low-frequency (44 and 23
tokens), so most collocates rest on only two or three observations, which may
lead to unstable statistical values. Finally, and most importantly, collocations
cannot show meaning, causation or intent. They show only that two words co-occur
more than chance predicts.

## Reference

Pines, Yuri. "Didactic Narrative and the Art of Self-Strengthening: Reading the
Bamboo Manuscript *Yue gong qi shi* 越公其事." *Early China* 45 (2022): 375–412.
https://doi.org/10.1017/eac.2022.2.
