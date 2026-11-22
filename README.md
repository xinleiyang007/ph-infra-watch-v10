# PH Infra Watch V10 — Philippine Energy & ICT Intelligence Desk

A **static-site-first, multi-source intelligence aggregator**: publisher RSS and public indexes → filtering/deduplication → source-audited bilingual metadata → candidate project matching → refreshed GitHub Pages feed, project map, company directory and CSV exports.

- `index.html` + `assets/`: no client API key, single-page interface.
- `config/news_sources.json`: 25 configured sources, directly labeled RSS vs index.
- `scripts/collect_news.py`: source-attributed RSS candidate discovery and strict-title deduplication.
- `scripts/collect_documents.py`: PDF and XLSX metadata extraction (not unreviewed publication as project facts).
- `scripts/translate_news.py`: optional Argos offline English→Chinese model download.
- `scripts/ai_enrich.py`: optional key-protected Gemini bilingual **short excerpt** summarization.
- `.github/workflows/collect-and-deploy.yml`: scheduled collection + Pages deployment without committing generated data back to `main`.

**User refresh button** re-fetches the most recently deployed JSON, and does **not** run the remote crawler. To run a new crawl, log in to GitHub and use Actions → Run workflow.

The included 266 projects and company profiles are historical sourced records, not a comprehensive/current tender database. Initial news feed is empty until the first online collection. Missing translation and failed feeds are explicitly indicated. See `README_中文安装指南.md` for the full deployment walkthrough.
