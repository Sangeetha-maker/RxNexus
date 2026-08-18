# Suggested DAX measures

```DAX
Opportunity Count = COUNTROWS('08_opportunity_features')
Average Opportunity Score = AVERAGE('08_opportunity_features'[Opportunity_Score])
Total CMS Drug Cost = SUM('08_opportunity_features'[Total_Drug_Cost])
Critical Opportunities = CALCULATE([Opportunity Count], '08_opportunity_features'[Opportunity_Priority] = "Critical")
```

Use `Total CMS Drug Cost` only as aggregate CMS evidence, never as a patient cost. Do not write DAX that relates synthetic medication history to CMS facts without an approved mapping.
