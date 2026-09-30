# A/B Testing Viva Notes

## Experiment at a glance

The experiment, `onboarding_flow_v2`, compared the existing onboarding flow
(control) with a shorter revised flow (treatment). The primary metric was
onboarding completion. Paid conversion within 14 days of assignment was a
downstream guardrail.

The analysis assigns users to groups by their experiment assignment
(intention-to-treat), checks for Sample Ratio Mismatch, uses two-sided
two-proportion z-tests and 95% confidence intervals, and applies the existing
Holm correction to secondary metrics. It does not apply the secondary-metric
correction to the pre-defined primary metric.

| Metric | Control users | Treatment users | Control rate | Treatment rate | Absolute uplift | Relative uplift | 95% CI for uplift | Raw p-value | Adjusted p-value | Significant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Onboarding completion (primary) | 5,677 | 5,785 | 53.20% | 56.54% | +3.35 pp | +6.29% | [+1.52, +5.17] pp | 0.000319 | 0.000319 | Yes |
| Paid conversion (guardrail) | 5,677 | 5,785 | 10.15% | 9.46% | -0.69 pp | -6.81% | [-1.78, +0.40] pp | 0.213614 | 0.660628 | No |

The paid-conversion result is not statistically significant. Its confidence
interval includes both zero and a potentially meaningful negative change, so
the experiment does not establish that paid conversion is protected against
business-relevant harm. Statistical significance on onboarding completion
alone is not sufficient reason to roll out the treatment; business impact and
the guardrail need consideration too. No acceptable paid-conversion loss
threshold was specified, so the analysis cannot decide whether a particular
loss is acceptable.

## Concepts and viva questions

### 1. What is an A/B test?

- **Definition:** A controlled experiment that compares two versions of a
  product experience by assigning users to groups and comparing outcomes.
- **Project use:** Users assigned to `onboarding_flow_v2` received either the
  existing or shorter revised onboarding flow.
- **Likely viva question:** What was changed in this experiment?  
  **Answer:** The treatment used a shorter revised onboarding flow.

### 2. What is the control group?

- **Definition:** The group that receives the existing experience or baseline
  against which a change is evaluated.
- **Project use:** The control group received the existing onboarding flow.
- **Likely viva question:** Why do we need a control group?  
  **Answer:** It provides a baseline for comparison with the revised flow.

### 3. What is the treatment group?

- **Definition:** The group assigned to receive the proposed product change.
- **Project use:** The treatment group received the shorter revised onboarding
  flow.
- **Likely viva question:** What does the treatment represent here?  
  **Answer:** Assignment to the shorter revised onboarding flow.

### 4. What is the primary metric?

- **Definition:** The main outcome chosen before analysis to evaluate whether
  the experiment achieved its objective.
- **Project use:** Onboarding completion was the primary metric; the experiment
  compares 53.20% in control with 56.54% in treatment.
- **Likely viva question:** Why identify a primary metric in advance?  
  **Answer:** It keeps the main evaluation focused and reduces the temptation
  to select a favorable result after seeing the data.

### 5. What is a guardrail metric?

- **Definition:** A measure monitored to check that an improvement does not
  harm another important outcome.
- **Project use:** Paid conversion within 14 days of assignment was the
  downstream guardrail. Its rate was 10.15% in control and 9.46% in treatment.
- **Likely viva question:** Why is paid conversion a useful guardrail?  
  **Answer:** Easier onboarding could increase completion without increasing,
  or while reducing, downstream paid conversion.

### 6. What is a null hypothesis?

- **Definition:** The starting statistical assumption that the groups have no
  difference in the population conversion rates.
- **Project use:** For each two-sided test, the null hypothesis is that
  treatment and control have equal conversion rates for that metric.
- **Likely viva question:** What is the null hypothesis for onboarding
  completion?  
  **Answer:** The true onboarding completion rates are equal for treatment and
  control.

### 7. What is an alternative hypothesis?

- **Definition:** The hypothesis that the population rates differ; in a
  two-sided test, it does not specify which group is higher.
- **Project use:** The notebook uses two-sided tests, so it tests whether the
  rates differ in either direction.
- **Likely viva question:** Does the alternative hypothesis assume treatment
  must be better?  
  **Answer:** No. This project's test is two-sided and allows either an
  increase or a decrease.

### 8. What is a p-value?

- **Definition:** Assuming the null hypothesis is true, the probability of
  observing a result at least as extreme as the one measured. It is not the
  probability that the null hypothesis is true.
- **Project use:** The primary onboarding p-value is 0.000319. The paid
  guardrail has a raw p-value of 0.213614 and a Holm-adjusted p-value of
  0.660628.
- **Likely viva question:** Does a p-value of 0.000319 mean there is a 0.0319%
  chance that the null hypothesis is true?  
  **Answer:** No. It is the probability of data this extreme under the null
  hypothesis, not the probability of the hypothesis itself.

### 9. What is a confidence interval?

- **Definition:** A range estimated from sample data using a method that, over
  repeated samples, would cover the true effect at the stated rate.
- **Project use:** The notebook reports 95% confidence intervals for the
  treatment-minus-control difference in conversion rates. The primary interval
  is [+1.52, +5.17] percentage points; the paid interval is [-1.78, +0.40]
  percentage points.
- **Likely viva question:** What does it mean that the paid interval includes
  zero?  
  **Answer:** The data are compatible with no difference as well as effects
  in either direction; this test does not establish a paid-conversion change.

### 10. What is statistical significance?

- **Definition:** Whether a result meets a pre-set statistical decision rule,
  such as a p-value below 0.05, under the assumed test.
- **Project use:** The primary metric uses the raw p-value; secondary metrics,
  including the guardrail, use the existing Holm-adjusted p-values. Onboarding
  is statistically significant; paid conversion is not.
- **Likely viva question:** Is the paid-conversion change statistically
  significant?  
  **Answer:** No. Its raw p-value is 0.213614 and its Holm-adjusted p-value is
  0.660628.

### 11. What is practical or business significance?

- **Definition:** Whether the size and consequences of an effect are
  meaningful enough to matter to product or business goals.
- **Project use:** The onboarding lift is statistically clear, but paid
  conversion has an uncertain estimate that includes a potentially meaningful
  decline. No acceptable paid-conversion loss threshold was defined.
- **Likely viva question:** Can a statistically significant result be too
  small to matter?  
  **Answer:** Yes. Statistical significance addresses evidence against a
  no-difference hypothesis, while business significance depends on effect size,
  costs, benefits, and product priorities.

### 12. What is absolute uplift?

- **Definition:** The treatment conversion rate minus the control conversion
  rate. For rates expressed as percentages, the difference is in percentage
  points.
- **Project use:** Onboarding absolute uplift is +3.35 percentage points;
  paid-conversion absolute uplift is -0.69 percentage points.
- **Likely viva question:** Is the onboarding uplift of 3.35 pp the same as
  3.35% relative growth?  
  **Answer:** No. It is a difference of 3.35 percentage points between the
  rates.

### 13. What is relative uplift?

- **Definition:** Absolute uplift divided by the control rate, expressed as a
  percentage. It describes the change relative to the baseline.
- **Project use:** Onboarding relative uplift is +6.29%; paid-conversion
  relative uplift is -6.81%.
- **Likely viva question:** How do you calculate relative uplift?  
  **Answer:** Divide the treatment-minus-control rate difference by the
  control rate and multiply by 100.

### 14. Why use a two-proportion test for conversion?

- **Definition:** A two-proportion z-test compares the proportions of successes
  between two independent groups.
- **Project use:** Each assigned user contributes a binary outcome for
  onboarding completion or paid conversion, so the notebook compares the
  treatment and control proportions with a two-sided test.
- **Likely viva question:** What is one example of a success in this analysis?  
  **Answer:** A user assigned to a group who completed onboarding, or who
  converted to paid within the defined guardrail window.

### 15. What is intention-to-treat analysis?

- **Definition:** Analyze users in the groups to which they were assigned,
  regardless of whether they fully experienced or followed the treatment.
- **Project use:** Experiment groups are based on assignment. Conflicting
  variant assignments were excluded upstream, as documented in the existing
  analysis.
- **Likely viva question:** Why analyze users by assignment?  
  **Answer:** It preserves the randomized group comparison and avoids
  reassigning users based on behavior after assignment.

### 16. What is Sample Ratio Mismatch?

- **Definition:** A difference between observed experiment group sizes and the
  allocation ratio expected by the experiment, such as 50/50.
- **Project use:** The notebook checks the control and treatment assignment
  counts for a 50/50 split; the existing analysis reports no evidence of
  abnormal allocation.
- **Likely viva question:** What might an SRM indicate?  
  **Answer:** It can indicate assignment, logging, or data-quality problems
  that should be investigated before interpreting the experiment.

### 17. Why might an improved onboarding rate not improve paid conversion?

- **Definition:** The primary action and a later business outcome represent
  different stages and can respond differently to a product change.
- **Project use:** Onboarding completion increased, while paid conversion
  decreased by an estimated 0.69 percentage points; the paid estimate is
  uncertain and not statistically significant.
- **Likely viva question:** Does this result prove the shorter onboarding caused
  lower paid conversion?  
  **Answer:** No. The observed paid decrease is not statistically established;
  its interval includes zero and negative as well as positive effects.

### 18. Why should downstream metrics be monitored?

- **Definition:** Later outcomes help determine whether an earlier funnel
  improvement also supports the product's broader goals and does not cause
  unintended harm.
- **Project use:** Paid conversion checks whether improved onboarding
  completion is accompanied by a safe downstream commercial outcome.
- **Likely viva question:** Should the treatment be automatically rolled out
  because onboarding is significant?  
  **Answer:** No. Consider the size and business value of the primary lift,
  uncertainty in the paid guardrail, and an explicitly chosen acceptable
  guardrail threshold before making a rollout decision.

## Interpretation guidance

Statistical significance asks whether the observed difference would be unusual
under the null hypothesis. Business significance asks whether the size of the
change matters enough to justify a product decision. These are different
questions: a small change can be statistically significant, and an uncertain
change can still have a confidence interval that includes business-relevant
effects.

A guardrail is important because optimizing onboarding completion alone could
miss harm to later conversion. Here, the primary improvement is statistically
significant, but the paid-conversion estimate is negative and uncertain. Do
not treat either the primary result or a non-significant guardrail test as
automatic proof that rollout is safe. The project does not define a specific
acceptable loss threshold, so no threshold-based safety conclusion can be
made.

## Reproducing the summary

Run `python python/ab_test_summary.py` from the project root. The script reads
the existing assignment-level dataset and the existing notebook results,
recalculates both requested metrics with the notebook's two-proportion test
and confidence-interval formulas, checks them against the existing result
rows (including the established Holm-adjusted significance for the secondary
guardrail), and writes `outputs/experiments/ab_test_summary.csv`. It does not
modify either input file.
