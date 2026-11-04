---
title: "Copies of Copies: Why AI Answers Drift, and Why Facts Need a Source Attached"
date: 2026-11-04
draft: false
tags: [ai, search, ai-overviews, provenance, misinformation, ai-agents]
images: [/images/copies-of-copies.png]
summary: "Google's AI Mode said a UK travel permit is embedded in your passport chip. That is false, and it is built from two true sentences on GOV.UK. Here is how a fact changes each time it is copied, why the copies now get the credit, and what it takes for a fact to carry its source."
---

On 4 November 2026 I asked Google's AI Mode for the difference between an eVisa and an ETA. Part of its answer said a UK electronic travel authorisation (ETA) "is digitally embedded directly into your passport's electronic chip."

That is false, and it is built from two true facts. GOV.UK [says](https://www.gov.uk/guidance/using-the-uk-eta-app) the ETA "is linked to your passport digitally". The same page tells people applying through the UK ETA app to "scan a passport biometric chip". The chip is read when you apply. Nothing is written to it. A passport chip is written by the country that issued the passport, and the UK has no way to add to it.

The answer listed its sources. None was a government page. They were visa application services, visa news sites, a YouTube video and a college website. Somewhere between the government and the answer, two true sentences were joined into one wrong one. I cannot tell whether a copy did it first or the AI did. Nobody had to lie.

This post is about how that drift works, why the copies now get the credit, and what it takes to stop it.

## An original and its copies

An original is a page written by whoever knows the fact firsthand. For a travel permit, that is the government. For a product's weight, it is the maker's datasheet. For a law, it is the text of the law.

A copy is any page that repeats the fact in its own words. Travel agents, comparison sites, news rewrites and AI answers are all copies. So is a blog post someone writes from an AI answer.

Copies are useful. Most people never read the original, and a good copy saves them the trouble. The problem is what happens to the fact on the way.

![A UK ETA fact drifts across three copies. Many copies of one mistake then look like agreement. With a source record, each copy can be checked against the one original.](/images/copies-of-copies.png)

*The chain in the picture is simplified. The count of 24 copies is an illustration, not a measurement.*

## What each copy does to the fact

Every copy is a small edit. Four kinds are common.

**It drops conditions.** The UK rule is that an ETA "lasts for 2 years or until your passport expires, whichever is sooner." A copy says "valid for 2 years". The short version is mostly true. It fails the traveller whose passport expires next spring. The edit is so natural that GOV.UK's own [check page](https://www.gov.uk/check-eta) makes it, with "An ETA lasts for 2 years and is linked to your passport."

**It merges things that sound alike.** "Linked to your passport digitally" and "scan a passport biometric chip" are both about the passport and both sound technical. Join them carelessly and you get "embedded in the chip". The word "eVisa" is another trap. In many countries it means a visa you apply for online. In the UK it also means your [online immigration status](https://www.gov.uk/evisa). A copy that mixes the two gives advice that fits neither.

**It fills gaps.** The original says the ETA is linked to the passport you applied with. It does not spell out what happens when you renew that passport. A copy that wants to sound complete might guess that the ETA moves to the new one. The page gives no support for that guess.

**It drops the link.** The copy cites the copy before it, or nothing at all. After two or three steps, nobody can tell where the fact came from.

None of these edits needs bad intent. Each one makes the text shorter, clearer or more complete. That is why they survive. AI answers make the same edits people do, only faster.

## Why the copies now get the credit

Copying is old. Here is why it does more damage now.

**Copies outnumber originals.** A government writes one page about a rule. Visa services, travel blogs and AI-written sites write many pages about the same rule. Each one is cheap to make and can earn traffic, and AI makes them cheaper still.

**Repetition looks like agreement.** Fifty pages that say the same thing look like fifty sources. If they all copied one page, they are one source. Wikipedia editors know this loop well. A wrong claim moves from Wikipedia into the press, and the press story is then cited back as proof. They call it citogenesis, after [xkcd 978](https://xkcd.com/978/), and keep a [list of incidents](https://en.wikipedia.org/wiki/Wikipedia:List_of_citogenesis_incidents). More copies mean more false agreement.

**AI answers cite the copies.** The AI Mode answer above cited no government page. In March 2025 the [Tow Center at Columbia](https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php) gave eight AI search tools excerpts from news articles. It asked each tool to name the article and its publisher. Together they got it wrong in more than 60% of 1,600 queries. Perplexity was wrong 37% of the time, and Grok 3 was wrong 94% of the time. The tools often credited a reprint on Yahoo News or AOL instead of the publisher that wrote the story.

**The careful middle loses readers.** Government pages do not depend on clicks. The careful writers between them and the reader do, such as newsrooms and specialist sites that read the rule and explain it well. [Pew Research](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/) tracked the Google searches of 900 US adults in March 2025. When an AI summary appeared, people clicked a regular result on 8% of visits. Without a summary, they clicked on 15%. They clicked a link inside the summary on 1% of visits. Pew measured clicks, not income. But fewer clicks mean less money for the sites that do the careful work.

**Models learn from the copies.** Model-written text is now part of the web that new models train on. A 2024 [paper in Nature](https://www.nature.com/articles/s41586-024-07566-y) by Shumailov and colleagues trained each model only on the output of the one before. Rare details disappeared first. Over the generations, the models forgot what the original data looked like. A [study from the same year](https://arxiv.org/abs/2404.01413) found that keeping the original data in the mix, instead of replacing it, largely avoids this. So the damage is not certain. It depends on whether the originals stay in the mix.

Together these form a loop. AI answers are built from copies. People publish the AI answers. Those pages become the copies the next answer is built from. Each turn moves further from the original.

## Why checking more pages does not help

The obvious fix is to compare many sources and go with the majority. That works when the sources are independent. Copies are not. A majority of copies counts one source many times.

When the sources may be copies, the check that works is against the original. Good fact-checkers work this way. They ask who said it first, and whether that person was in a position to know.

That check is slow for a person, and most people never make it. It also gets harder with every copy, because each one is less likely to say where the fact came from.

## What a truth layer is

A truth layer keeps a record of each fact next to its original, in a form a program can read. The record holds four things.

1. **Who stated it.** The party that knows firsthand, such as the government or the maker.
2. **The exact words.** The full quoted sentence from the original, not a paraphrase.
3. **Where.** The address of the page or document, down to the page number.
4. **When it was checked.** The date someone last confirmed the quote is still there.

For the ETA, the record would look like this.

```yaml
fact: How long a UK ETA lasts
value: 2 years, or until the passport expires, whichever is sooner
stated_by: UK government (GOV.UK)
quote: "An ETA lasts for 2 years or until your passport expires, whichever is sooner."
source: https://www.gov.uk/eta/apply
checked: 2026-11-04
```

A program can open the page, confirm the quote is still there and compare it with a claim. For numbers, dates and names, that comparison is mechanical. Set copy 1's "2 years" beside the recorded value, and the missing "or until your passport expires" is plain to see.

Looser claims are harder. Deciding whether any sentence supports "embedded in the chip" takes a model or a person. That is the hard half of the problem. But with a record, it is a check against a few sentences from one page, not a vote among fifty copies.

Source links have always had one weakness. A copier gains nothing by keeping the source, so the link gets dropped. A truth layer cannot stop that. It changes the reader instead. An AI answer or an agent can be built to use only facts that come with a record it can check. When a copy has no record, the reader can ask the party that knows. When no record exists, the reader says "unverified" instead of guessing.

There is a limit worth stating. A record proves the original says it. It does not prove the original is right. Originals can be wrong, and they change. What the record buys is that a wrong fact can be traced to one owner and fixed in one place, and that a changed page can be noticed.

None of this is new. Science runs on citations. Courts keep a chain of custody for evidence. Wikidata references can already hold the source, the address, the date retrieved and a supporting quote. Photos are starting to carry [Content Credentials](https://c2pa.org/), a signed record of who made the image and how it was edited. The pieces exist. What has been missing is readers that insist on them.

## Why it matters more when agents act

A person can check a wrong AI answer, though most do not. An AI agent that books a trip or orders a part does not doubt anything unless it is built to. It acts on what it reads. A dropped condition becomes a refused boarding. A guessed spec becomes a part that does not fit.

As agents do more booking, buying and research, copies of copies get more expensive. Doubt has to be built into the agent as a rule. Check the record before you act, and treat a fact without one as unverified.

I work on this for product facts at [AirShelf](https://airshelf.com), where we tie product facts to quotes on the maker’s own page.
