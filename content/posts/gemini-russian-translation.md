---
title: "Why Gemini Translates Into Russian Better Than Claude and GPT"
date: 2026-10-31
tags: [ai, llm, translation, gemini, russian]
summary: "For months I have sent every Russian translation through Gemini, because Claude's Russian reads like American English. I assumed Google's search index was the reason. The data says Gemini really is ahead, but the lead is one year old, and it is not the index or the tokenizer."
---

Russian is my native language. For months I have sent every Russian translation through the `gemini` CLI, never through Claude. Claude's Russian is correct, but it reads like American English with Russian words. Gemini's reads like a person wrote it.

I had a theory for why. Google has crawled the Russian web for twenty years, and owns Books and YouTube. Or maybe Google has a team that works on Russian. I wanted evidence either way, so I went looking.

## Gemini is ahead, and the best test agrees

The strongest public test of translation is WMT, the yearly machine translation competition. Professional translators score each system's output without knowing which system wrote it. In [WMT25](https://aclanthology.org/2025.wmt-1.22.pdf), English to Russian came out like this:

| Rank | System | Human score |
|------|--------|-------------|
| 1 | Gemini 2.5 Pro | 83.4 |
| 3-5 | GPT-4.1 | 76.2 |
| 3-5 | Claude 4 | 75.9 |
| 6-9 | DeepSeek-V3 | 73.6 |
| 8-10 | Yandex | 72.0 |
| 9-11 | Human reference translation | 70.5 |
| 11-14 | Qwen3-235B | 67.6 |

Gemini was first on its own, with a clear gap. The human reference translation landed behind most of the top machines. The same paper names Gemini 2.5 Pro the best system overall, winning 14 language pairs.

The Russian [LLM Arena](https://llmarena.ru/) points the same way. Russian speakers vote blind between two answers. When I pulled its data on 31 October 2026, Google models held the top four scores out of 112 models. The margins are small, though. Nine models share first place within the error bars, including GPT-5.4 and Claude Opus 4.7.

There is one exception worth knowing. On the arena's creative writing topic, GPT-5.4 leads Gemini 3 Pro, 1219 to 1181. So for translation, Gemini is clearly ahead. For writing original Russian text, it is less clear.

## But a year ago, Claude was ahead

This is where my theory broke. In [WMT24](https://aclanthology.org/2024.wmt-1.1.pdf), the year before, English to Russian looked different:

| System | Human score |
|--------|-------------|
| Human reference | 89.2 |
| Claude 3.5 | 88.2 |
| Yandex | 87.0 |
| Gemini 1.5 Pro | 85.5 |
| GPT-4 | 85.0 |

Gemini 1.5 Pro was behind Claude. Google already had its search index, Books and YouTube in 2024. So those alone cannot be the reason Gemini pulled ahead in 2025.

## What Google says it changed

Google published a language mix only once, in the [PaLM 2 report](https://arxiv.org/abs/2305.10403) from 2023. Russian was 8.73% of the non-English web data, third after Spanish and Chinese. The report also says PaLM 2 trained on parallel text, the same content in English and another language, and that this "ingrains an inherent ability to translate". Google has not published a mix for any Gemini model.

The [Gemini 2.5 report](https://arxiv.org/abs/2507.06261) explains the jump directly:

> This transformation stems from a holistic strategy, meticulously refining pre- and post-training data quality, advancing tokenization techniques, innovating core modeling, and executing targeted capability hillclimbing.

So the gain was deliberate. But the report names Indian, Chinese, Japanese and Korean as the biggest winners. It never mentions Russian.

Translation is also a product goal for Google. Google Translate [started using Gemini](https://blog.google/products-and-platforms/products/search/gemini-capabilities-translation-upgrades/) for text translation in December 2025, and Google cited its WMT25 result when it did.

I found no sign of a team working on Russian specifically. Bard added the Russian language in 2023, while Russia itself stayed off its list of countries. Russian rater jobs exist at the usual vendors, but none of the postings I found names Google or Gemini as the client.

## The web index is not unique to Google

The web corpus does not explain much either. Russian is the second largest language in [Common Crawl](https://commoncrawl.github.io/cc-crawl-statistics/plots/languages), the free web archive that many labs train on. It is 6.3% of pages, behind only English. Every lab can get Russian web text.

Books, YouTube transcripts and Google Translate's store of English-Russian pairs are real advantages that only Google has. I could not find numbers for any of them. They are plausible, but unmeasured.

## The tokenizer is not the reason

A tokenizer splits text into tokens, the pieces a model reads. A tokenizer built mostly for English cuts Russian into many small pieces, and that can hurt quality. I measured this on 2,002 sentence pairs from the WMT20 English-Russian test set. It is the same news content in both languages.

| Tokenizer | Used by | English tokens | Russian tokens |
|-----------|---------|----------------|----------------|
| Gemini | Gemini 2.5 to 3.x | 57,384 | 77,671 |
| o200k_base | GPT-4o, GPT-4.1, GPT-5 | 54,061 | 77,078 |
| DeepSeek-V3 | DeepSeek | 54,855 | 89,055 |
| Llama 3.1 | Llama 3 | 54,787 | 90,289 |
| Qwen3 | Qwen3 | 55,750 | 98,164 |
| cl100k_base | GPT-4, GPT-3.5 | 54,799 | 134,873 |

Gemini and current GPT use almost exactly the same number of Russian tokens. Gemini's own count came from its free `countTokens` API, and it matched Google's open Gemma 3 tokenizer to the token. Against Qwen and DeepSeek, Gemini uses 13-21% fewer tokens for Russian, so the tokenizer may help there. Against GPT it does not. Claude's tokenizer is not public, so I left it out.

There is one more clue. Gemma 3 27B uses the same tokenizer and was trained by the same company, yet it ranked 15th to 16th in WMT25, with a score of 61.7. A good tokenizer and Google's data do not produce good Russian on their own. Model scale and training after the base model do the rest.

## What I believe now

My impression was right. My explanation was wrong. Gemini is ahead on Russian translation, and the best human evaluation available confirms it. The cause looks like Google making translation and multilingual quality an explicit goal for Gemini 2.5. Russian benefits as one of the biggest languages in that effort. It does not look like a Russia-specific project, or Google's search index, or the tokenizer.

I'll keep sending Russian through Gemini. The ranking moved a lot in one year, so I'll check again when WMT26 is published.

To reproduce the token counts:

```bash
uv run --with sacrebleu sacrebleu -t wmt20 -l en-ru --echo src > en.txt
uv run --with sacrebleu sacrebleu -t wmt20 -l en-ru --echo ref > ru.txt
# Count each file with tiktoken (o200k_base, cl100k_base) and with Hugging Face
# tokenizers (unsloth/gemma-3-27b-it, Qwen/Qwen3-8B, deepseek-ai/DeepSeek-V3,
# unsloth/Llama-3.1-8B-Instruct). For Gemini itself, POST the text to the
# models/<model>:countTokens endpoint.
```
