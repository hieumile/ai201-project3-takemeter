# takemeter - planning.md

---

## Milestone 1: Community and Labels

### Community

**r/CryptoCurrency** — one of the largest crypto discussion forums on Reddit (~8M members). The community discusses a wide range of topics: market movements, new projects, investment decisions, and industry news. Discourse is highly varied: some posts are detailed on-chain breakdowns, some are "should I buy X?" threads, and some are links to news articles. These three types of content are meaningful and distinguishable to community members, making this a good fit for a classification task.

### Labels

**analysis** — A post that makes a structured argument about a cryptocurrency, market trend, or technology, supported by specific data, charts, metrics, or logical reasoning. The post draws a conclusion from evidence.

> Example 1: "BTC's realized cap has crossed $500B for the first time while MVRV sits at 1.8 — historically, values below 2.0 have preceded bull runs. On-chain data suggests we're still in accumulation."
>
> Example 2: "ETH's TVL dropped 23% this quarter while daily active addresses are up 15%. This divergence suggests users are moving to L2s rather than leaving the ecosystem entirely."

**advice** — A post that recommends a specific course of action — what to buy, sell, hold, or do — directed at the reader or the community. The post is prescriptive rather than descriptive; the primary intent is to guide behavior.

> Example 1: "If you're just starting out, put 70% in BTC/ETH and the rest in 2–3 mid-caps max. Don't touch memecoins until you understand what you own."
>
> Example 2: "Stop trying to time the market. Set a DCA schedule and stick to it. Checking prices hourly is how you make emotional decisions."

**news** — A post that reports or links to a recent event, development, or announcement in the crypto space. The primary intent is to inform, not argue or recommend. Little to no personal interpretation of what the event means.

> Example 1: "Coinbase just received approval to operate in the EU under MiCA regulations." (link to article)
>
> Example 2: "SEC has delayed its decision on the spot Ethereum ETF by another 45 days."

**opinion** — A post that expresses a personal view or belief about a cryptocurrency, market, or industry topic without backing the claim with data or evidence, and without recommending a specific action to the reader. The post asserts rather than argues.

> Example 1: "ETH is still the most undervalued asset in crypto. The developer ecosystem alone is worth more than its current market cap implies."
>
> Example 2: "I think the memecoin era is finally over. The market is getting smarter and people are tired of rugs."

---

## Milestone 2: Planning Spec

### 1. Community

r/CryptoCurrency is a good fit for a classification task because it generates high volumes of text-heavy posts that fall into naturally distinct categories: people sharing market analysis, people asking for or giving investment guidance, and people posting news. These distinctions matter to the community — members frequently complain about low-effort posts and distinguish "actual analysis" from "shill posts" or "just news." The community is large enough to collect 200+ examples without hitting the same author twice, and posts are public.

### 2. Labels

See definitions and examples in Milestone 1 above.

### 3. Hard Edge Cases

**Hardest boundary: analysis vs. advice**

A post can cite data *and* recommend an action. Example: *"BTC dominance is at 56% and rising — historically this means altcoins underperform for the next 2–3 months. I'd hold off on rotating into alts right now."* This post provides evidence (analysis behavior) but ends with a recommendation (advice behavior).

**Decision rule:** If the post's primary conclusion is a recommendation to the reader ("you should do X"), label it **advice** — even if it cites data. If the post draws an interpretive conclusion about the market without telling the reader what to do, label it **analysis**. The framing of the final sentence is usually the signal: "this suggests X is happening" → analysis; "you should do X" → advice.

**Second boundary: news vs. analysis**

A post might link to a news article and then add interpretation. Example: *"BlackRock just filed for a Bitcoin ETF (link). This is huge — institutional access at this scale hasn't been possible before and will likely drive the next wave of inflows."* The first sentence is news; the second is analysis.

**Decision rule:** If the post contains substantive interpretation beyond restating the event, label it **analysis**. A one-line reaction ("this is huge!") doesn't count as analysis — that's still **news**. The threshold is: does the post build an argument about what the event means, with specific reasoning?

**Third boundary: opinion vs. analysis**

Both express a view about crypto, but analysis backs it with evidence. Example: *"ETH will flip BTC this cycle — the fundamentals are just better."* vs. *"ETH will flip BTC this cycle — staking yield is 4% while BTC generates no income, and ETH transaction volume has exceeded BTC's for 6 straight months."*

**Decision rule:** If the post's claim could stand or fall on specific, verifiable data cited in the post, label it **analysis**. If removing the numbers or references wouldn't weaken the argument (or there are none), label it **opinion**. One throwaway stat used for rhetorical effect is still **opinion** — the evidence has to be doing real argumentative work.

### 4. Data Collection Plan

**Source:** r/CryptoCurrency — posts from the top 3 feed tabs (Hot, Top/Month, New) to get a range of content types and post ages.

**Target distribution:** ~52 examples per label (208 total across 4 labels), aiming for roughly equal representation.

**Collection method:** Manual — read each post, copy the text (title + body, or title alone for link posts), and label it immediately. Save to a CSV with columns: `text`, `label`, `notes`.

**If a label is underrepresented after 200 examples:**
- *advice* is likely underrepresented since r/CryptoCurrency discourages pure "what should I buy" posts. If so, supplement by collecting from the Daily Discussion threads and comment sections, where advice-giving is more common.
- *opinion* may be the easiest to find but hardest to distinguish from analysis — prioritize clean, evidence-free opinion posts and avoid borderline cases.
- *news* may be overrepresented since link posts dominate the front page. If so, deprioritize link-only posts and seek out more text posts for the other labels.
- Do not pad with borderline examples just to hit a count — better to have 45 clean examples than 52 noisy ones.

### 5. Evaluation Metrics

**Primary metric: macro-averaged F1**
Since we have 4 classes and the goal is for the model to learn all four distinctions equally well, macro-F1 is more informative than accuracy alone. Accuracy is misleading if the class distribution is skewed — a model predicting "news" for everything could get 25% accuracy while being useless. Macro-F1 treats each class equally regardless of size.

**Per-class F1**
Report F1 separately for analysis, advice, news, and opinion. A high macro-F1 can hide a single class with near-zero F1 — per-class reporting makes that visible. This matters because the four classes serve different user needs; a model that can't identify "advice" posts at all isn't useful even if it classifies the other labels correctly.

**Confusion matrix**
Required to understand *which* classes are being confused and in which direction. The analysis/advice boundary is expected to be the hardest — the confusion matrix will confirm or refute that.

**Accuracy**
Reported for comparison with the zero-shot baseline, but not used as the primary success criterion.

### 6. Definition of Success

A classifier is genuinely useful if a community moderator or tool could trust it to pre-sort posts without reviewing every example manually. That requires:

- **Macro-averaged F1 ≥ 0.72** on the test set for the fine-tuned model
- **No single class F1 below 0.60** — a model that completely fails one label isn't deployable
- **Fine-tuned model outperforms zero-shot baseline by at least 10 percentage points on macro-F1** — if fine-tuning doesn't help, there's a data or label quality problem worth diagnosing

If the fine-tuned model achieves macro-F1 ≥ 0.72 with all three class F1s above 0.60, I'd consider the classifier good enough for a "soft tagging" use case (suggesting a label to a user, not enforcing it automatically). For fully automated moderation, the bar would be higher (~0.85+), which is unlikely to be achievable with 200 examples.

---

## AI Tool Plan

**Label stress-testing (before annotation)**
Paste the three label definitions and the two decision rules (analysis vs. advice; news vs. analysis) into Claude and ask it to generate 10–15 posts that sit at the boundary between two labels. If any generated posts can't be cleanly classified using the decision rules, tighten the rule before starting annotation. This is worth doing before annotating a single example — fixing a boundary definition costs minutes; fixing 200 mislabeled examples costs hours.

**Annotation assistance**
Annotation will be done manually without AI pre-labeling. This is a deliberate choice: with only 200 examples, skimming AI-labeled posts risks propagating systematic errors. Manual labeling also forces close reading of every example, which tends to surface boundary cases that improve label definitions.

**Failure analysis (after fine-tuning)**
After collecting wrong predictions from the fine-tuned model, paste the misclassified examples into Claude with the prompt: "Here are posts my classifier got wrong. Identify any systematic patterns — are certain topics, post lengths, or structural features associated with misclassification?" Then verify each proposed pattern by re-reading the examples manually before including it in the evaluation report. The AI pattern-finding is a starting point, not a conclusion.

---

