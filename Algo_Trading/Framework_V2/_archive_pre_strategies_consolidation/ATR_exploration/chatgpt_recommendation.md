Yes—and that's actually an important detail.

Using **Simple ATR (rolling mean of TR)** instead of **Wilder's ATR (RMA)** changes what I'd prioritize.

## The first thing I'd do

Before adding any new stop/target logic, I would run **one A/B test**.

Everything stays identical except:

```
Current
Simple ATR(14)

↓

Test

Wilder ATR(14)
```

Don't change:

* Entry
* Exit logic
* SL_MULT
* TP_MULT
* EOD logic
* Universe

Literally only change the ATR calculation.

This is a very "clean" experiment because you'll know exactly what caused any difference.

---

## Why I think it's worth testing

Your strategy is unusual.

It enters after a rejection candle.

That means ATR is being sampled immediately after a volatility event.

Simple ATR reacts differently than Wilder ATR.

Example

Suppose TR values are

```
1
1
1
1
1
7  ← rejection candle
1
1
```

Simple ATR

```
1.43

↓

1.43

↓

1.43

↓

suddenly

1.00
```

Wilder ATR

```
1.43

↓

1.39

↓

1.35

↓

1.31
```

Much smoother.

That means

* stop distances change less
* target distances change less
* fewer abrupt changes between consecutive trades

For systematic strategies, that's generally desirable.

---

# I would actually change my research roadmap slightly

Earlier I said:

1. Hybrid Stop
2. ATR Period
3. Swing TP
4. Volatility Filter
5. Time Exit

Now I'd do:

## Phase 1 — ATR Research

These are cheap experiments.

### Experiment A

```
Simple ATR14
```

vs

```
Wilder ATR14
```

---

### Experiment B

```
Simple ATR10

Simple ATR14

Simple ATR20
```

---

### Experiment C

```
Wilder ATR10

Wilder ATR14

Wilder ATR20
```

After those 6 runs you'll know whether smoothing itself is providing an edge.

---

# Then move to exit research

Only after the ATR study would I investigate

* Hybrid SL
* Structure SL
* Swing TP
* Time exits

Otherwise you won't know whether an improvement came from the exit logic or simply from a better volatility estimate.

---

# One experiment I think is missing completely

Looking through your code, I noticed this line:

```python
atr = row['atr14']
```

Notice where ATR is taken from.

It comes from the **signal candle**.

Not the entry candle.

Not the current bar.

The signal bar.

That opens up another interesting research question.

Test these three:

### Model A

```
ATR = Signal Candle ATR
```

(current)

---

### Model B

```
ATR = Entry Candle ATR
```

---

### Model C

```
ATR = Average(
Signal ATR,
Entry ATR
)
```

The difference is usually small (only one 5-minute bar), but because your setup is triggered by a rejection candle—which can itself have elevated true range—the signal candle's ATR may systematically produce wider stops than the entry candle's ATR. It's worth verifying whether that's helping or hurting.

---

## If this were my own project

These are the **five experiments I'd run next**, in order:

| Priority | Experiment                                            | Why                                                 |
| -------- | ----------------------------------------------------- | --------------------------------------------------- |
| ⭐⭐⭐⭐⭐    | **Simple ATR vs Wilder ATR**                          | Cheapest, cleanest comparison                       |
| ⭐⭐⭐⭐⭐    | **ATR Period (10/14/20) using Wilder**                | May outperform your current baseline                |
| ⭐⭐⭐⭐☆    | **Signal ATR vs Entry ATR**                           | Tests whether the rejection bar biases stop size    |
| ⭐⭐⭐⭐☆    | **Hybrid Stop (max(ATR stop, Signal High + buffer))** | Respects both volatility and technical invalidation |
| ⭐⭐⭐⭐☆    | **Volatility filter (minimum ATR or ATR percentile)** | Filters out weak rejection setups                   |

One final suggestion: because you're using Claude Code and already have a modular backtesting engine, I'd separate the ATR calculation into its own pluggable component. Something like:

```python
atr_mode = "sma" | "wilder" | "ema"
atr_period = 10 | 14 | 20
atr_source = "signal" | "entry"
```

That lets you reuse the same engine for all future strategies and makes this entire class of experiments easy to automate. I think that architectural change will pay off more than hard-coding individual ATR variants.
