---
title: "12Go competitors: why 12Go is hard to beat in Asia"
date: 2026-11-26
draft: false
tags: [12go, travelier, ground-transport, ai-search, marketplaces]
summary: "12Go holds the sales channel, the operator software and the AI answer at once. A newcomer cannot win one without the other two."
---

In Southeast Asia, one group holds three positions at once: a major sales channel for transport operators through 12Go, the operator software that feeds that channel through seatOS, and the default recommendation that AI assistants give to travellers. Because those three parts reinforce one another, a new competitor cannot win one position without also taking the other two. I was CTO at 12Go for ten years, and every number in this post comes from public pages and tests I ran in November 2026, not from inside the company.

## Is 12Go part of Travelier? 12Go vs Bookaway

Anyone researching the market often starts by comparing 12Go and Bookaway as if they were rival startups fighting for the same routes. In reality, 12Go vs Bookaway is a comparison between two brands owned by one company. The parent company is Travelier, which is the former Bookaway Group after it was renamed in 2023.

According to the Travelier rebrand press release on prnewswire.com, along with coverage on travolution.com and information on seatos.com, Travelier owns both consumer booking brands and the underlying software used by transport operators. On the consumer side, it owns 12Go and Bookaway. On the software side, it owns seatOS, which provides operator software in Asia, and Sisorg, an operator software provider in Latin America that was bought with a reported 100+ operator customers. When a traveller or an operator looks at the market, they are looking at a single group operating across multiple layers of the industry.

## AI assistants name 12Go in 4 of 5 answers

To see what travellers are told when they plan a trip today, I ran an AI answer test on 24 November 2026. The test covered 10 Asian ground routes, ranging from busy tourist corridors to long-tail routes such as Luang Prabang to Nong Khiaw. I tested five assistant lanes, collecting 10 answers in each lane for a total of 50 answers. The five lanes were GPT-4.1 with web search, GPT-5.6 with web search, Claude Sonnet 5.5 with web search, Gemini 2.5 Flash-Lite with Google grounding, and Google AI Mode.

12Go was named in 40 of the 50 answers. The breakdown across the five assistant lanes shows how consistent this result is:

| Assistant lane | Answers naming 12Go (out of 10) |
| :--- | :--- |
| Claude Sonnet 5.5 with web search | 8 |
| Gemini 2.5 Flash-Lite with Google grounding | 6 |
| Google AI Mode | 9 |
| GPT-4.1 with web search | 9 |
| GPT-5.6 with web search | 8 |
| **Total** | **40 of 50** |

No other aggregator came close to that frequency across the 50 answers. Individual transport operators were named only on their own specific routes, so no single operator acted as a default recommendation across the region.

| Brand named | Category | Mentions across 50 answers |
| :--- | :--- | :--- |
| 12Go | Aggregator | 40 |
| Baolau | Aggregator | 8 |
| Klook | Aggregator | 7 |
| Giant Ibis | Operator (own route only) | 7 |
| Lomprayah | Operator (own route only) | 6 |
| Thai Railway | Operator (own route only) | 6 |
| Trip.com | Aggregator | 5 |
| Direct Ferries | Aggregator | 5 |
| Bookaway | Aggregator | 4 |

## Why the AI names 12Go: the pages it reads

The assistants do not invent these recommendations on their own. When answering route questions, they rely heavily on existing travel guide and blog pages, citing sites such as seat61.com, visitthailandtoday.com, and backpackerswanderlust.com. To see what was feeding the assistants, I read 140 of the guide and blog pages that the assistants cited in their answers.

Out of those 140 cited pages, 50 pages (36%) link directly to 12Go. Of those 50 links to 12Go, 29 carry an affiliate or partner tag. Other travel brands appear far less often on the exact same set of pages:

| Linked brand | Pages linking (out of 140 cited pages) |
| :--- | :--- |
| 12Go | 50 (29 with affiliate or partner tags) |
| Booking.com | 23 |
| GetYourGuide | 19 |
| Trip.com | 16 |
| Klook | 7 |
| Bookaway | 4 |

The lesson from these citations is straightforward. An affiliate network of travel guide sites, built over years to rank well in Google search, is now the exact source material that decides which brand an AI assistant recommends. The affiliate payout has become the price of being named by the assistant.

## 12Go costs the traveller nothing extra

A common way to challenge an online travel agency is to tell travellers that booking directly with the bus or ferry company is cheaper. To test whether that is true here, I checked prices live in a browser on 24 November 2026 for departures on 10 December 2026 and 12 December 2026.

I looked at Lomprayah, a large Thai ferry and bus operator, across five routes and two dates: Khaosan to Koh Tao, Pinklao to Koh Tao, Samui to Koh Tao, Samui to Phangan, and Chumphon Train station to Koh Tao by van and catamaran. Across nine checkout totals opened, 12Go's price equalled Lomprayah's own price, coming out to THB 0 to 1 more at checkout. For example, the Khaosan to Koh Tao departure at 22:00 cost THB 1,250 on Lomprayah's own website and THB 1,251 at 12Go checkout. One listing at THB 1,550 that at first looked like a markup turned out to be Lomprayah's own VIP bus, which also costs THB 1,550 on Lomprayah's website.

For a large operator like Lomprayah, the traveller saves nothing by going direct. Smaller operators were not measured in this test because none of them had a same-class, same-date price available online on their own websites.

## The operator software belongs to the same group

Even if a competitor matches the consumer website, the software that operators use to run their daily business sits inside the same parent group. On seatos.com, seatOS describes itself as "the operating system for ground and sea transport" and claims in self-reported figures to operate "across 9 countries, from Thailand and Indonesia to Egypt and South Africa". Its listed address reads "SeatOS (Travelier Group)" in Bangkok.

The product covers the full daily workflow of a transport company. Its modules include inventory, distribution, reservations, operations, finance, analytics, counter, kiosk and handheld hardware, plus an API for online travel agencies and agents. It sells by demo and shows no public pricing. Because of this setup, the system an operator uses to manage its seats belongs to the same group that sells those seats to travellers.

Public pages show how central this software is to the group's plans. A February 2026 job post asks for someone to "shape SeatOS Connect, our new channel product" and to "make SeatOS the default distribution and digital transformation platform for the region". Meanwhile, seatos.com invites OTAs, GDSs, resellers, and agents to "connect once and sell 230+ operators across 9 countries". Travelier's own press page summarizes the setup by calling the company "OTA, GDS and TMS, integrated vertically".

## The neutral supply layer already exists

A founder looking at this market might think about building a neutral business-to-business distribution layer that connects bus and ferry operators to every travel website without competing for the end consumer. That business already exists. Distribusion operates as a neutral business-to-business distribution layer for ground transport, working with 1,200+ operators in 75+ countries and connecting them to 150+ OTAs, including 40+ operators in Thailand and 100+ operators in Indonesia.

The existence of Distribusion shows two things for anyone planning to enter the space. First, the idea of a neutral supply aggregator for buses and ferries is already taken. Second, having the supply connections does not cause AI assistants to recommend your brand to travellers. Supply alone does not win the market. Owning the cited guide pages and the consumer demand is what wins the answer.

## 12Go competitors outside Southeast Asia

To see how far this position reaches, I ran the same AI answer test across 24 routes outside Southeast Asia, generating 120 answers. Even outside its home region, 12Go was still the most named aggregator, appearing in 19 of the 120 answers. It already shows up on routes such as Colombo to Ella, Tashkent to Samarkand, Tbilisi to Yerevan, and Cairo to Luxor, sometimes appearing alongside Bookaway.

On other routes, regional or global competitors hold the answers:
- Kotor to Dubrovnik: FlixBus was named in 5 of 5 answers.
- Istanbul to Goreme: FlixBus was named in 4 answers and Obilet in 4 answers.
- Cartagena to Santa Marta: redBus was named in 4 answers.
- Cusco to Puno: redBus was named in 3 answers.

There is also a clear group of routes where no aggregator was named in most answers, including Bishkek to Karakol, Accra to Cape Coast, Amman to Petra, Marrakech to Merzouga, Dar es Salaam to Zanzibar, and Nairobi to Mombasa. On several of these routes, the assistants name one national operator instead, such as JETT in Jordan, Supratours and CTM in Morocco, and Azam Marine to Zanzibar. Because one or two well-known operators handle the route, there is less fragmented supply for an aggregator to pull together.

## Where 12Go is weaker

The test results also point to the places where 12Go has less hold on the market. It is weaker on routes where foreign tourist demand is small, and on routes where a single national operator already dominates the conversation. In addition, smaller operators had no same-class, same-date price of their own online, so their direct prices were not measured, so whether 12Go sells above their direct prices remains unknown.

Messaging apps are another open question. Operators in Asia already sell tickets directly over chat apps. Lomprayah, for instance, sells direct to passengers over LINE, WhatsApp, and WeChat. In August 2026, Meta launched Meta Business Agent in Indonesia, offering a free AI chat assistant for businesses inside WhatsApp. Whether these automated chat assistants will pull bookings away from aggregators and back to direct operator channels is still unmeasured.

## What this means if you want to compete

The barrier protecting 12Go is not the consumer booking code on its website. The barrier is the combination of years of affiliate links on travel blogs that both Google and AI assistants read, the operator software that manages the seat inventory, and retail price parity on major operators, all held by one corporate group.

The arrival of AI search did not reset the market or open an easy path for new entrants. Instead, AI assistants repeated the old search rankings because they read the exact same guide pages that ranked in traditional search. Competing head-on in Southeast Asia would require rebuilding that network of guide pages before you could even get named in the answers. A newcomer has a much clearer path in regions where nobody holds the consumer demand yet, or in a different category where one company has not already locked together the content network, the operator software, and the consumer checkout.
