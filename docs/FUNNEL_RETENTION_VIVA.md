# Funnel and Retention Viva Notes

## Funnel analysis

### 1. What is funnel analysis?

Funnel analysis measures how users progress through a defined sequence of
product steps. It reports how many users reach each step and where users leave
the sequence.

### 2. Why use an ordered funnel?

An ordered funnel counts a later step only when the same user completed the
preceding steps in order. For this project, the sequence is Signup, Onboarding
Completed, Trial Started, and Paid. This avoids counting a payment or trial
that occurred before the qualifying earlier steps.

### 3. What is conversion rate?

Conversion rate is the share of users in a defined starting group who reach a
specified next step. Step-to-step conversion is the users at the current step
divided by users at the previous step, multiplied by 100.

### 4. What is drop-off?

Drop-off is the users who reached a funnel step but did not reach the next
step, using the ordered funnel's stage counts.

### 5. What is the difference between absolute and percentage drop-off?

Absolute drop-off is the difference in users between consecutive stages.
Percentage drop-off is that difference divided by the previous stage's users,
multiplied by 100. The absolute count shows volume; the percentage makes
drop-off comparable across stages or groups of different sizes.

## Cohort retention

### 6. What is cohort analysis?

Cohort analysis groups users by a shared starting characteristic and measures
their later behavior. Here, users are grouped by the month of signup.

### 7. Why use signup-month cohorts?

Signup month provides a consistent acquisition starting point. Comparing
cohorts can show whether retention differs for users who started in different
months, while keeping each cohort's users together.

### 8. What is D1 retention?

D1 retention is the percentage of eligible users who have an `app_open` event
exactly one calendar day after their signup date.

### 9. What is D7 retention?

D7 retention is the percentage of eligible users who have an `app_open` event
exactly seven calendar days after their signup date.

### 10. What is D30 retention?

D30 retention is the percentage of eligible users who have an `app_open` event
exactly 30 calendar days after their signup date.

### 11. Why are complete observation windows important?

A user cannot be fairly counted as not retained if the data ends before the
retention day arrives. Each metric therefore includes only users whose signup
date is at least 1, 7, or 30 days before the latest event date, respectively.
This keeps incomplete follow-up from understating retention.

### 12. How does conversion differ from retention?

Conversion measures movement to another defined action, such as starting a
trial after onboarding. Retention measures whether users return or remain
active at a later time. A product can have strong conversion and weak
retention, or the reverse.

### 13. Why compare retention by acquisition channel?

Different channels may bring users with different expectations or intent.
Comparing retention can help assess whether channel cohorts continue using the
product, in addition to how many users they initially acquire.

### 14. Why compare retention by platform?

The app experience and usage patterns can differ between platforms. Comparing
retention by platform can highlight a possible difference in ongoing use that
may warrant investigation; the comparison alone does not establish its cause.

## Likely viva questions

1. **What is the project's funnel?**  
   Signup → Onboarding Completed → Trial Started → Paid, in that order for the
   same user.

2. **How is signup-to-paid conversion calculated?**  
   Ordered-funnel paid users divided by signup users, multiplied by 100.

3. **Does D7 mean activity at any time during the first week?**  
   No. In this project, D7 requires an `app_open` exactly seven calendar days
   after signup.

4. **What is the denominator for D30 retention?**  
   Users whose signup date is at least 30 days before the event data's latest
   date.

5. **Why can cohort size differ from the retention denominator?**  
   Cohort size counts all signups in that month; each retention denominator
   excludes users without a complete observation window for that metric.

6. **What does a high absolute drop-off tell you?**  
   Many users were lost between those stages, though the count should be
   considered alongside the stage's percentage drop-off.

7. **Can a funnel identify why users drop off?**  
   No. It locates where progression decreases. Additional investigation is
   needed to determine causes.

8. **Why should retention comparisons use the same definition?**  
   Consistent event and timing rules make cohort, channel, and platform
   comparisons interpretable rather than mixing different measures.

9. **Does higher retention by channel prove that the channel caused it?**  
   No. It is an observed difference and may be influenced by user mix or other
   factors; it does not by itself prove causation.

10. **Why are the output CSVs header-only?**  
    The required BigQuery tables are not available in the local project files,
    so no results were executed or invented. The headers describe the expected
    result schema for exported query results.

## Execution and output note

The SQL queries reference the project's BigQuery tables. The CSV files in
`outputs/funnel/` and `outputs/retention/` are schema templates only; they
contain no analytical results. Run the corresponding queries in BigQuery and
export each result set to its matching CSV. The cohort retention script returns
three result sets in the order documented in `sql/11_cohort_retention.sql`.
