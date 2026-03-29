---
title: "Web 4.0 Is Open Databases"
date: 2026-03-29
tags: [ai, agents, web, data, mcp, open-data]
summary: "I asked my AI agent to plan a family escape from Chiang Mai's burning season. It reverse-engineered a proprietary air quality encoding, scraped flights, checked fuel costs, and compared 15 cities across 10 years of data. This is what Web 4.0 actually looks like: open databases + agents that query them."
---

Every spring, Chiang Mai turns into a gas chamber. Farmers across northern Thailand and neighboring countries burn crop residue, and the AQI climbs to 200-300+. I have asthma. I have three young kids. Every year I ask the same question: should we escape somewhere for two weeks?

This year I asked my AI agent instead of opening 12 browser tabs.

## What Actually Happened

I told Claude Code: "Compare air quality across Thai cities for April, find me the cheapest way to get there with a family of 6, and figure out if it's worth the money."

What followed was a four-hour session where the agent:

1. **Scraped live AQI data from aqicn.org.** The site is JavaScript-rendered, so a simple HTTP request gets nothing. The agent spun up a headless browser, extracted the data, then discovered the historical data was encoded in a proprietary format baked into their minified JS.

2. **Reverse-engineered the encoding.** The agent read aqicn.org's minified JavaScript, figured out their custom data packing scheme, and built a decoder tool — I called it `aqi-liberator`. It took four different approaches before one worked. The first three failed — simple HTTP got nothing (JS-rendered), the search API timed out, the Chrome DevTools MCP couldn't connect. On the fourth try, the agent used a raw CDP websocket to a headless Chromium, intercepted the XHR requests, found the data endpoint, and reverse-engineered the encoding from the minified source.

3. **Compared 15 cities across 10 years of daily AQI data.** Not a vibe check — actual statistical comparison. April means, medians, 95th percentiles. Chiang Mai: mean 139, 79% of days unhealthy, zero good days. Phuket: mean 57, 3% unhealthy. Rayong: 62, 7% unhealthy. The agent built a complete ranking sorted by air quality per dollar per drive-hour.

4. **Cross-referenced with flight prices.** Scraped Google Flights for all 32 destinations from Chiang Mai. CNX to Surat Thani: $153/person RT. CNX to Phuket: $168. But multiply by 6 people (kids are same price on Thai LCCs) and flying anywhere costs $900-1,000 in airfare alone.

5. **Checked driving costs.** The agent discovered that Thailand had just cut fuel subsidies by 22% *that same week* — found the Bloomberg article, recalculated with the new fuel prices. Chiang Mai to Rayong: 900 km each way, roughly 9,000 THB in fuel post-hike for our SUV, plus tolls, two overnight stops in Tak, and road food for 6 people.

6. **Checked accommodation.** Scraped Airbnb via headless browser for 3-bedroom places in Rayong that could fit 6. My wife found a great deal separately — about $750 for two weeks.

Total trip cost: roughly $1,450. The agent compared driving vs flying for a family of 6, including the car rental penalty (you need a car with kids — Grab with 3 car seats doesn't work). Flying 6 people to Phuket + renting a 7-seater for 2 weeks came to $2,500+. Driving won.

All through conversation. No dashboards. No context-switching between Google Flights, Airbnb, AQI websites, news sites, and a spreadsheet.

To be fair: this wasn't push-button. The session cost maybe $15 in API usage, I had a flight-scanning codebase already built, and I nudged the agent through several dead ends. This is closer to pair-programming with a very fast research assistant than to "AI plans your vacation." But even with the friction, it compressed two days of research into one session.

## The Shape of What's Coming

Strip away the specifics and look at what the agent actually did. It queried multiple data sources, joined the results on a common key (city + date range), applied filters, ranked the output, and presented it in the format I needed.

That's a SQL query. Distributed across the internet.

```
SELECT city, avg_aqi, flight_price, hotel_price, drive_cost
FROM aqi_data
JOIN flight_prices ON city = destination AND month = 'April'
JOIN accommodation ON city = location AND type = '3br'
JOIN fuel_costs ON route = CONCAT('CNX-', city)
WHERE avg_aqi < 75
ORDER BY (flight_price + hotel_price * 14) ASC
LIMIT 3;
```

The difference: there's no database. Each "table" is a different website, API, or scraped dataset with its own format, authentication, and access pattern. The agent is the query engine.

This is what Web 4.0 actually looks like. Not a new protocol. Not a blockchain. Not a headset. It's: **open databases + agents that query them + natural language as the interface.**

## The Paid Data Web

In a mature version of this, the data layer looks like pay-per-query APIs:

| Query | Source | Cost |
|-------|--------|------|
| Cities with AQI < 50 in April | AQI API | $0.001 |
| Flights CNX to those cities, cheapest | Amadeus/Flights API | $0.01 |
| Hotels rated > 8, < $80/night | Accommodation API | $0.01 |
| Temperature, rain probability | Weather API | $0.001 |

The agent JOINs the results. Ranks. Presents three options. Total data cost: $0.03.

Some of this already exists. Amadeus has a flight API. OpenWeatherMap charges per call. Schema.org and JSON-LD provide a common vocabulary for structured data. MCP (Model Context Protocol) is emerging as the way agents discover and call APIs.

The pieces are on the table. They just aren't assembled yet.

## What's Actually Missing

**Most data owners won't open up.** Airbnb's moat IS the aggregation. They spent billions building a two-sided marketplace — publishing a $0.01/query API would commoditize their entire business overnight. Same for Booking.com, same for most OTAs. Their value isn't the data; it's the lock-in.

**No universal payment rail for agents.** Specs like x402 propose HTTP-native micropayments — agent sends a request, gets a 402 Payment Required, pays, gets data. The mechanism (crypto, Stripe, carrier billing) matters less than the fact that none of it works today. My agent can't pay $0.001 for an AQI query.

**No discovery mechanism.** How does an agent find out that some startup in Bangkok has a Thai hotel pricing API? MCP helps with tool discovery if you already know the server exists. But there's no registry. No DNS for data APIs.

**Who builds the databases that don't want to be built?** Hotels won't publish real-time pricing. Airlines charge a fortune through GDS intermediaries. Airbnb will never expose an API. The most valuable data is precisely the data that's most profitable to keep proprietary.

## The Uncomfortable Middle

So my agent didn't use clean APIs. It scraped. It reverse-engineered. It bypassed JavaScript rendering. It decoded proprietary formats.

This is the reality of "open data" today. Most of it is:
- Technically accessible but behind JS rendering (requires headless browser)
- Encoded in custom formats (requires reverse engineering)
- Behind auth walls (requires session management)
- Rate-limited (requires patience and retries)
- Spread across HTML meant for humans (requires parsing)

The agent is the lockpick. And that's both the promise and the problem.

There are two paths forward:

**Path 1: Liberation.** Someone builds the `aqi-liberator` for everything. Scrape it, normalize it, serve it through clean APIs. Legal gray area. Constant cat-and-mouse with anti-bot measures. Fragile. But it works today.

**Path 2: Persuasion.** Convince data owners that earning $0.01/query from a million agents beats protecting a walled garden that's slowly losing traffic to agent-mediated experiences anyway. If users stop visiting Booking.com because their agent checks prices directly, the walled garden strategy is already failing.

My bet: Path 1 forces Path 2. Once enough data gets liberated through scraping, the original sources will realize they might as well monetize the access directly rather than fighting it. The music industry fought piracy for a decade before Spotify proved that convenient paid access beats enforcement. The same economics apply here — it's cheaper to serve an API than to fight scrapers.

## The Part No Dataset Covers

Here's the twist. The agent did its job brilliantly. Four hours of work that would have taken me two full days of tab-switching. The data clearly said: go to Rayong. Clean air, cheapest option for 6 people, decent accommodation. The optimal answer given the data.

We stayed in Chiang Mai.

Why? I'm building a startup. My wife's entire support network — the babysitter, classes, playgrounds, other moms — is here. Pulling three kids out of their routine for two weeks has costs that don't show up in any API. The stress of packing and traveling with young children is not a queryable metric. And honestly, with an air purifier, it's survivable.

The agent can tell you the optimal move. It can't tell you whether the optimal move is the right one. Data-driven decision making has a ceiling, and it's lower than the data evangelists want to admit. The last 20% is judgment — context about your life that no dataset covers and no prompt can fully convey.

The future isn't agents making decisions for us. It's agents collapsing the research phase from days to minutes so humans can spend their time on the part that actually matters: deciding what to do with imperfect information, competing priorities, and the messy reality of being a person with obligations that don't fit in a spreadsheet.

That's Web 4.0. Not replacing human judgment. Giving it better inputs, faster.
