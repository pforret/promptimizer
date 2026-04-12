---
model: openai/gpt-4o
temperature: 0.3
max_tokens: 4000
system: auto
description: List Chinese car brands introduced in Europe in the last 10 years
response_format: json
---

List all Chinese car brands that have been introduced in Europe in the last 10 years.
For each brand, provide the following information.

Respond strictly in the following JSON format:

```json
{
  "chinese_car_brands": [
    {
      "brand": "Brand Name",
      "conglomerate": "Parent company or conglomerate (e.g. Geely, BYD, SAIC, ...)",
      "introduction_year": 2020,
      "cars_sold_europe": 50000,
      "key_models": "Model1, Model2",
      "remarks": "Brief note on market positioning or notable facts"
    }
  ]
}
```

Include all brands you know of, even smaller or very recent entrants.
Sort by introduction year (earliest first).
For `cars_sold_europe`, give cumulative European sales up to end of 2025. If exact figures are unavailable, give your best estimate and add "(est)" in remarks.