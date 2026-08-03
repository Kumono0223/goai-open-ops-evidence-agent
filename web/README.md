# Static demo

Open `index.html` directly in a browser or serve this directory with any static server. The page is self-contained and makes no network requests.

The browser implementation mirrors the Python evidence contract:

- method and policy versions;
- input SHA-256 and row count;
- z-score evidence IDs;
- deterministic proposed incident IDs;
- explicit human approval and no-production-action boundary;
- downloadable JSON evidence package.

The CSV parser supports ordinary comma-separated records and quoted fields. It is a competition demo, not a replacement for a production historian, CMMS, permissions, or audit service.
