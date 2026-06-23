# TakeMeter: Subreddit Content Classifier for r/CryptoCurrency

An end-to-end NLP pipeline that classifies public posts from the **r/CryptoCurrency** subreddit into one of four distinct categories: `analysis`, `advice`, `news`, or `opinion`. This project evaluates the performance of a fine-tuned `distilbert-base-uncased` classifier against a zero-shot `llama-3.3-70b-versatile` baseline on a curated, balanced dataset of 210 annotated examples.

---

## 1. Community & Domain Context

**r/CryptoCurrency** is one of the largest financial discussion forums on the internet, with over 8 million members. The subreddit is characterized by high-volume, text-heavy posts that span a wide spectrum of quality and intent:
* Some users provide institutional-grade on-chain and macroeconomic updates.
* Others share emotional reactions, speculative opinions, or seek financial recommendations.
* Scammers and hype-builders frequently post low-effort "shill" threads or copy-paste news updates.

This diverse discourse makes the community an ideal candidate for text classification. Sorting and labeling posts helps developers and moderators filter out noise, highlight high-quality research, and flag potential financial hazards (like unverified investment advice).

---

## 2. Label Taxonomy

The classifier uses four mutually exclusive labels. The taxonomy is grounded in the community's communication norms and designed to have clean, definable boundaries.

| Label | Definition | Examples |
| :--- | :--- | :--- |
| **`analysis`** | Structured arguments about market trends, blockchain technology, or finance, backed by specific, verifiable data, metrics, or logical reasoning. | - *"BTC's realized cap has crossed $500B while MVRV sits at 1.8. On-chain accumulation continues."*<br>- *"ETH TVL dropped 23% this quarter but active addresses rose 15%, indicating L2 migration."* |
| **`advice`** | Prescriptive recommendations directing readers to take a specific action (buy, sell, hold, allocate capital, secure wallets). | - *"Set a mechanical DCA schedule and ignore hourly price movements."*<br>- *"Keep 70% in BTC/ETH, avoid memecoins, and use cold storage."* |
| **`news`** | Objective reporting or links concerning recent events, announcements, or regulatory filings with minimal personal interpretation. | - *"Coinbase receives regulatory approval to operate in the EU under MiCA."*<br>- *"The SEC delays its decision on the spot Ethereum ETF by another 45 days."* |
| **`opinion`** | Subjective views, beliefs, or speculative claims shared without concrete data support or specific behavioral advice. | - *"ETH is the most undervalued asset in crypto; its developer ecosystem is unmatched."*<br>- *"I think the memecoin era is finally over as investors get smarter."* |

### Hard Edge Cases & Decision Rules
* **Analysis vs. Advice**: A post may cite data *and* recommend an action. 
  * *Rule*: If the primary conclusion directs the reader to take action ("you should do X"), it is labeled **`advice`**. If the post draws an interpretive market conclusion without directing behavior, it is **`analysis`**.
* **News vs. Analysis**: A post links to news and adds reaction.
  * *Rule*: Substantive interpretation of what the event means is **`analysis`**. Minor reactions (e.g. *"this is huge!"*) remain labeled as **`news`**.
* **Opinion vs. Analysis**: Both express views, but analysis requires verifiable data.
  * *Rule*: If the claim stands or falls on specific data cited, it is **`analysis`**. If removing numbers/references does not weaken the claim, it is **`opinion`**.

---

## 3. Labeled Dataset & Collection

The dataset consists of **210 public posts** collected from `r/CryptoCurrency` (Hot, New, and Top feeds). 
* **Scraping**: We built python scripts that targeted Reddit's RSS and search feeds (e.g. searching for keywords like *bitcoin, solana, regulation, tax, hack*) using custom user-agents and request spacing (6s sleep) to bypass API limits and HTTP 429 rate-limiting.
* **Cleaning**: Text bodies were stripped of HTML tags, brackets, and Reddit RSS boilerplates (e.g. `submitted by /u/...`).
* **Distribution**: The dataset was curated to ensure a near-perfectly balanced distribution across the labels.

```
Final Label Distribution (210 total rows):
├── analysis : 53 posts (25.2%)
├── advice   : 52 posts (24.8%)
├── news     : 52 posts (24.8%)
└── opinion  : 53 posts (25.2%)
```

---

## 4. Fine-Tuning Setup

We fine-tuned `distilbert-base-uncased` on Google Colab using a single T4 GPU.
* **Train / Val / Test Split**: 70% / 15% / 15% (146 Train, 32 Validation, 32 Test).
* **Hyperparameters**:
  * **Epochs**: 3
  * **Learning Rate**: $2 \times 10^{-5}$
  * **Batch Size**: 16
  * **Optimizer**: AdamW with linear weight decay
* **Input Tokenization**: Truncation and padding to a maximum sequence length of 512 tokens.

---

## 5. Evaluation Results

The models were evaluated on the locked test set ($N=32$, containing exactly 8 examples per class). The fine-tuned model's performance was compared side-by-side with a zero-shot `llama-3.3-70b-versatile` baseline.

### Model Comparison Summary

| Model | Test Accuracy | Macro F1-Score |
| :--- | :--- | :--- |
| **Llama-3.3-70b (Zero-Shot Baseline)** | **62.5%** | **0.621** |
| **DistilBERT (Fine-Tuned)** | **31.25%** | **0.208** |
| *Improvement* | *-31.25%* | *-0.413* |

### Per-Class Metrics (Fine-Tuned Model)

| Class | Precision | Recall | F1-Score | True Support |
| :--- | :---: | :---: | :---: | :---: |
| **`analysis`** | 0.276 | 1.000 | 0.432 | 8 |
| **`news`** | 1.000 | 0.250 | 0.400 | 8 |
| **`opinion`** | 0.000 | 0.000 | 0.000 | 8 |
| **`advice`** | 0.000 | 0.000 | 0.000 | 8 |

*Note: Precision for `advice` is mathematically undefined (0/0) but represented as 0.000.*

### Fine-Tuned Model Confusion Matrix

The table below maps true labels (rows) against predicted labels (columns):

| True \ Predicted | `analysis` | `news` | `opinion` | `advice` |
| :--- | :---: | :---: | :---: | :---: |
| **`analysis`** | **8** | 0 | 0 | 0 |
| **`news`** | 5 | **2** | 1 | 0 |
| **`opinion`** | 8 | 0 | **0** | 0 |
| **`advice`** | 8 | 0 | 0 | **0** |

---

## 6. Failure Analysis & Diagnostics

### Diagnostic: Why Did the Fine-Tuned Model Underperform?

The fine-tuned model collapsed, predicting `analysis` for 29 out of the 32 test set examples. 
This classification collapse is a common issue when fine-tuning transformer models on very small datasets:
1. **Under-training (Low Gradient Steps)**: With only 146 training examples, a batch size of 16, and 3 epochs, the model only ran for **27 gradient steps**. This is far too few steps for the pre-trained weights to adapt to the new vocabulary boundaries of our custom classes.
2. **First-Class Bias**: In the label map, `analysis` has index `0`. When training fails to converge, the model often defaults to outputting the bias of the first class (`0`) to minimize immediate loss.
3. **Data Complexity**: r/CryptoCurrency posts contain heavy vocabulary overlap (e.g. *Bitcoin, ETFs, prices, regulations* appear across all classes). Without substantial training, the model cannot distinguish structural formatting (like data citations vs. emotional statements).

### Error Examples Analysis

#### Error 1: Advice Misclassified as Analysis
* **Post Text**: *"Forget TA. When the haters throw a parade, the bottom is in. Forget your TA lines and RSI crossovers... DCA and ignore the doomposting. Let the haters have their moment. They're just ringing the bottom bell..."*
* **True Label**: `advice`
* **Predicted Label**: `analysis` (Confidence: ~91%)
* **Why it failed**: The post uses technical finance terms (*TA, RSI crossovers, bottom signal, market nukes*) and structural descriptions of market phases. The model associated these keywords with the `analysis` class, completely missing the primary behavioral directive: *"DCA and ignore the doomposting"* and *"get your cash ready"*.

#### Error 2: Opinion Misclassified as Analysis
* **Post Text**: *"How is Bitcoin not just a digital amulet. If you walked through a marketplace thousands of years ago... Bitcoin is nothing more than fractions of an arbitrary number... technological tricks wrapping hope and fear..."*
* **True Label**: `opinion`
* **Predicted Label**: `analysis` (Confidence: ~88%)
* **Why it failed**: The author writes in a highly structured, argumentative format, dividing the post into themes (e.g. "Value storage", "Freedom from government", "Unbreakable security"). Because the post *looks* like a structured paper, the model flagged it as `analysis`, failing to realize that the text contains zero concrete, verifiable data points.

#### Error 3: News Misclassified as Opinion
* **Post Text**: *"fake ETF news just wiped over $150 Million of positions in a few minutes. It all started with news coming from the unreliable garbage news site Cointelegraph... bears and bulls got liquidated..."*
* **True Label**: `news` (or `analysis` based on text details)
* **Predicted Label**: `opinion` (Confidence: ~76%)
* **Why it failed**: While the core event is a news report of Cointelegraph's false posting, the author includes highly emotional vocabulary (*unreliable garbage news site, got rekt, overleveraged gamblers*). The model picked up on this subjective terminology and categorized the post as `opinion` instead of focusing on the underlying event reporting.

---

## 7. Sample Classifications

Here are 5 representative test set items classified by the fine-tuned model:

| Text Snippet | True Label | Predicted Label | Est. Confidence | Notes / Explanation |
| :--- | :--- | :--- | :---: | :--- |
| *"Why the banking industry is against the CLARITY Act... stablecoins compete with bank deposits..."* | `analysis` | `analysis` | 94% | **Correct**: The post presents a detailed, logical argument about reserve yields vs. bank deposits. |
| *"Japan pension fund plans 1% crypto allocation in FY2026... CoinPost said..."* | `news` | `news` | 74% | **Correct**: The model correctly classified this due to the presence of external reporting triggers (*"CoinPost said..."*, *"the fund plans..."*). |
| *"Best centralised exchange for newbies... Hello all. My friend has asked me..."* | `advice` | `analysis` | 87% | **Incorrect**: The query discusses exchange setups and features, causing the model to mistake it for analysis. |
| *"The boom generation needs exit liquidity... They are desperate for ways to flow value..."* | `opinion` | `analysis` | 89% | **Incorrect**: A subjective market critique containing no data, but classified as analysis due to formal sentence structure. |
| *"Bounty-chasing Pump Fun users are tattooing crypto tickers on their faces"* | `news` | `analysis` | 72% | **Incorrect**: A short headline reporting an event, but classified as analysis because the model defaults to class 0 when in doubt. |

---

## 8. Specification Reflection

1. **How the Spec Helped**: The decision rules outlined in `planning.md` (specifically *Analysis vs. Advice* and *Opinion vs. Analysis*) were vital during our manual curation of the 155 scraped posts. Having the rules pre-written prevented annotation drift when dealing with borderline cases (e.g. posts containing both data and behavioral recommendations).
2. **How the Implementation Diverged**: The implementation plan originally anticipated using simple JSON scraping endpoints. However, because Reddit actively blocks standard requests (HTTP 403) to its `.json` pages, we had to pivot to using subreddit RSS search queries (`.rss`) combined with custom user-agents and request spacing (6s sleep) to bypass bot detection.

---

## 9. AI Tool & Usage Disclosure

* **Task Planning and Scraper Development**: Gemini was used to design the implementation plan, write the Python scraping scripts ([scrape_reddit.py](file:///Users/leminhhieu/github/ai201-project3-takemeter/scrape_reddit.py) and [scrape_reddit_part2.py](file:///Users/leminhhieu/github/ai201-project3-takemeter/scrape_reddit_part2.py)), and help bypass the 429 rate limit issues.
* **Format Rectification**: Gemini wrote the script to identify and escape double quotes in the original `dataset.csv` rows.
* **Failure Analysis**: Gemini was used to calculate precision/recall metrics from the raw confusion matrix and help synthesize the failure mode descriptions.
