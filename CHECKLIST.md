## Fresh Finder Checklist (Status)

All items below have been implemented and committed.

### Immediate (Quick Fixes)

- [x] Team profile works but search stats do not
- [x] Make box score look better
- [x] Team search opens the proper Team Search (no redirect confusion)
- [x] Normalize dimensions for 100% zoom
- [x] Add loading spinners or indicators
- [x] Handle no results state more cleanly
- [x] Default date range for searches (last 7 days)
- [x] Make team logos in tables clickable to open team profile
- [x] Make right-side nav font weight bold to match branding

### Later (Big Changes)

- [x] Chart.js: add more visualizations (team trends, shooting, summary, advanced radar)
- [x] Caching: file-based caching in place
- [x] Advanced Metrics: expanded (Player PER, TS%, eFG%, WS, WS/48; Team Off/Def/Net Rating, TS%, eFG%, Pace, etc.)
- [x] Pagination/Filtering: Player filtering/pagination; Team pagination

### Diagnostics & Resilience (added)

- [x] JSON debug mode for routes (`?debug=1` or `Accept: application/json`)
- [x] Traceback logging and graceful fallbacks for player/team routes
- [x] Global 500 handler returning JSON in debug mode

No remaining items on the current checklist.
