# StatQuest — ROC and AUC, Clearly Explained

Video: https://youtu.be/4jRBRDbJemM
Watched: 2026-09-02, fv2 session

## Summary

Actual topic is ROC/AUC (threshold evaluation + model comparison), not logistic
regression itself — logistic regression is only the illustrative example (builds on
separate StatQuest videos: confusion matrix, sensitivity/specificity, logistic regression).

- **Logistic regression example used**: classifying mice as obese/not-obese by weight.
  Fits a probability curve (not a hard line), then applies a threshold (default 0.5) to
  convert "probability of obese" into a binary decision.
- **ROC curve**: plots true positive rate (sensitivity) vs. false positive rate
  (1-specificity), across every possible threshold from 0 to 1. Summarizes every
  threshold's confusion matrix in one picture, instead of comparing many separately.
- **AUC (Area Under the Curve)**: single number summarizing the whole ROC curve — used
  to compare different *models* (e.g., logistic regression vs. random forest) regardless
  of which specific threshold you'd eventually pick. Higher AUC = better classifier.
- **Precision-recall curves**: mentioned as an alternative to ROC when there's heavy
  class imbalance (e.g., rare-disease studies) — precision ignores true negatives, so
  it's less distorted by imbalance than the false-positive-rate axis ROC uses.

## Possible relevance to this project

If a regime-filter classifier is ever built (flagging good/bad days for the MA-short
strategy's entries — see #53's reframing discussion, 2026-09-02), ROC/AUC would be the
natural way to evaluate its threshold choice and compare it against alternative filters,
rather than picking one fixed cutoff arbitrarily.
