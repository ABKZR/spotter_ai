# Risk Model Documentation

This document describes the weather risk classification model, load-dependent adjustments, and route recommendation algorithm used in the Weather-Aware Truck Routing application.

## Weather Risk Thresholds

The safety framework defines five risk levels for three weather conditions. This implementation uses a conservative boundary convention where the **higher-risk band owns shared boundary values**.

### Wind Speed (mph)

| Risk Level | Range |
|-----------|-------|
| Low | x < 25 |
| Moderate | 25 ≤ x < 35 |
| High | 35 ≤ x < 45 |
| Severe | 45 ≤ x < 55 |
| No Travel | x ≥ 55 |

### Rain Intensity (inches/hour)

| Risk Level | Range |
|-----------|-------|
| Low | x < 0.10 |
| Moderate | 0.10 ≤ x < 0.25 |
| High | 0.25 ≤ x < 0.50 |
| Severe | 0.50 ≤ x ≤ 1.00 |
| No Travel | x > 1.00 |

### Snowfall Intensity (inches/hour)

| Risk Level | Range |
|-----------|-------|
| Low | x < 0.5 |
| Moderate | 0.5 ≤ x < 1.0 |
| High | 1.0 ≤ x < 2.0 |
| Severe | 2.0 ≤ x ≤ 3.0 |
| No Travel | x > 3.0 |

## Boundary Convention

Shared decimal endpoints in boundary specifications (e.g., 0.25 appearing in both Moderate and High rain) are evaluated using a deterministic convention:

- The **lower band excludes** its upper endpoint when the next band begins at that value
- The **higher-risk band owns** a shared boundary value
- No Travel is applied only at the exact conditions specified

**Rationale:** This is a conservative safety decision. When a measurement falls exactly on a boundary, classifying it into the higher-risk category is safer than the lower one.

## Load-Dependent Wind Rules

Safety policies enforce three additional rules based on cargo weight:

1. **Wind ≥ 55 mph** → No Travel for **any** load weight
2. **Wind 45–54 mph** AND load **> 30,000 lb** → No Travel
3. **Wind 35–44 mph** AND load **> 40,000 lb** → Severe

### Important Details

- Load comparisons use **strict greater-than** (`>`):
  - Exactly 30,000 lb does **not** trigger rule 2
  - Exactly 40,000 lb does **not** trigger rule 3
- Load rules can only **raise** severity, never lower it
- A condition already classified as No Travel **remains** No Travel regardless of load rules
- No Travel overrides **every** other classification

## Multiple Weather Conditions

A checkpoint may experience wind, rain, and snow simultaneously. The overall checkpoint risk is the **highest severity** across all conditions:

```
Low < Moderate < High < Severe < No Travel
```

Individual condition classifications are retained so the UI can explain why a checkpoint received its overall classification.

## Missing Weather Data

Missing data is **not** zero and must **not** be treated as Low risk.

When weather data is unavailable for a checkpoint:
- The specific missing variables are recorded
- The checkpoint is marked as **incomplete** for risk assessment
- No overall "safe" classification is invented
- The missing-data state is surfaced to route scoring and the user

## Route Mileage Estimation

### Assigning Risk to Miles

Each checkpoint represents weather at a sampled location. To estimate risk-affected mileage:

- Each checkpoint's risk is assigned to the **segment ending at the next checkpoint**
- The final checkpoint represents the **final partial segment** to the destination
- This means each interval between consecutive checkpoints gets the risk level of the starting checkpoint

### Severe Miles

Sum of segment distances where the starting checkpoint's overall risk is **Severe or No Travel**.

### High Miles

Sum of segment distances where the starting checkpoint's overall risk is **High, Severe, or No Travel**.

## Average Risk Calculation

The assessment mentions "lowest average risk" as a tie-breaker but does not define a numeric formula.

This implementation uses a **distance-weighted ordinal score**:

| Risk Level | Internal Score |
|-----------|---------------|
| Low | 0 |
| Moderate | 1 |
| High | 2 |
| Severe | 3 |
| No Travel | 4 |

```
average_risk = Σ(segment_distance × segment_risk_score) / Σ(assessed_segment_distance)
```

This score is an **implementation assumption**, not a Spotter-provided formula. It is used solely as a tie-breaker in the ranking algorithm.

## Route Recommendation Algorithm

### Ranking Order (Lexicographic)

Routes eligible for recommendation are sorted by:

1. **Fewest Severe miles** (ascending)
2. **Fewest High miles** (ascending)
3. **Lowest average risk** (ascending)
4. **Shortest travel duration** (ascending)
5. **Route ID** (deterministic final tie-breaker)

This is a strict lexicographic comparison. A shorter travel time **cannot** override fewer Severe miles.

### No Travel Handling

- A route with **any** No Travel checkpoint is **ineligible** for recommendation
- Such routes are still displayed so drivers can see the reason
- If **all** routes have No Travel conditions, the recommendation status is `no_suitable_route`
- The application does not claim to provide certified safety or dispatch authorization

### Incomplete Forecasts

- Routes with missing checkpoint forecasts have their metrics marked as **incomplete**
- Missing segments are **never** counted as Low risk
- Complete-coverage routes are preferred for recommendation
- If incomplete data could change the result, the recommendation may be withheld

## Open Assumptions

The following decisions are not explicitly defined in the assessment PDF and are documented as implementation assumptions:

| Unspecified Detail | Implementation Decision |
|-------------------|------------------------|
| Exact ownership of shared thresholds | Higher-risk band owns boundary |
| Whether No Travel disqualifies a route | Yes — ineligible for recommendation |
| Numeric average-risk formula | Distance-weighted ordinal score |
| How checkpoint risk maps to miles | Segment assignment between samples |
| Missing weather behavior | Incomplete coverage, never Low |
| Slider reference instant | Hours relative to departure |
| Provider returns < 3 routes | Never duplicate; honest partial state |
| Forecast timestamp granularity | Record actual timestamp, disclose approximation |
