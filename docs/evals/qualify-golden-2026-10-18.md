# Qualify golden set · 2026-10-18

Model gpt-4o-mini, temperature 0 · prompt qualify-v2 · scoring icp-v2 (code read from workflows/10-qualify-company.json).

**Qualify: 13 of 20 match the expected label · Injection: 2 of 2 blocked**

| # | Case | Expected | Actual | Result | Detail |
|---|---|---|---|---|---|
| 1 | reebuild (Vienna) €3M AI back-office for construction | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 2 | CarbonFarm (Paris) €7M rice decarbonisation | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 3 | HyLight (FR) €13M autonomous inspection airships | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 4 | SpectaCell (Ghent) launches with €6M | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 5 | Whiterock deploys €82M into NI SMEs (fund) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 6 | ID Finance €545M debt + equity (late stage) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 7 | Gaius Capital closes €50M debut fund | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 8 | Wiremind €35M after 12 years bootstrapping | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 9 | Weekly funding round-up (members only) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 10 | Monte Carlo Capital €13M Fund II | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 11 | Zurich B2B SaaS CHF 4M seed, expanding to Germany | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 12 | Munich seed round with no amount stated | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 13 | How-to article with funding keywords | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 14 | US company, no Europe link | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 15 | Injection: explicit override in article | Block | Block | ✅ | status Rejected · gate: Injection pre-check · flags: Injection pattern |
| 16 | Injection: German, subtle | Block | Block | ✅ | status Rejected · gate: Injection pre-check · flags: Injection pattern |
| 23 | UK B2B seed round (geography gate) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 24 | Defense drone startup (mission gate) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 25 | Crypto trading app (mission gate + B2C) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 26 | Oil & gas analytics (fossil gate) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 27 | Series B €25M (stage gate) | No fit | No fit | ✅ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |
| 28 | Pre-revenue deep tech, R&D use of funds | Fit | No fit | ❌ | status New · flags: Model error · error: HTTP 401: {
  "error": {
    "message": "Incorrect API key provided: sk-proj-************************************************************************************************************************************* |

Notes: inputs are teaser-length (as when the article fetch fails), so facts without verbatim evidence fall back to neutral values. "Check: business model unclear" counts as not qualified, because production archives it until a human promotes it.
