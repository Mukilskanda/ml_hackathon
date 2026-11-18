# Submission handoff

## Official deliverables

1. Public GitHub repository with complete source, experiment results, configuration, saved model assets where size permits, dependency pins and run instructions.
2. One consolidated `output/pdf/PathSnap_Technical_Report.pdf`.

## Before submission

- Replace `team.json` placeholders and verify actual contribution statements.
- Review every report claim, especially derived-reference accuracy, novelty and unverified deployment steps.
- Add genuine receiving-console screenshots after the physical two-laptop test; do not label local browser/API evidence as physical deployment evidence.
- Confirm the official scoring convention for `.route` alignment with organizers.
- Follow event rules for AI assistance disclosure. The code/report were developed with AI assistance; experiments and screenshots are real execution outputs. Team members must independently review and defend the work.
- Create the public GitHub repository using the team's account, add its remote, push, and verify the URL is accessible to evaluators. No public URL has been created by this local build.
- Do not commit raw datasets, cache files, credentials, private keys, environments or archive ZIPs. `.gitignore` covers these. Trained artifacts and result logs are included; inspect large-file sizes before publishing.

## Publication location and commands

Use the curated snapshot at `packages/PathSnap_Publication_Source/`, not this private development history. Exact initialization/push and logged-out verification steps are in `docs/PUBLICATION.md`. No public URL is verified. Do not put account tokens in README files, remote URLs or command history. The separate report is still required; confirm public redistribution permission for dataset-derived maps/report outputs.

## Transfer to Laptop 2

Transfer exactly `packages/PathSnap_Laptop2_UI.zip`. Application files are `ui/index.html`, `ui/style.css`, `ui/app.js` and `run_ui.cmd`, plus handoff/setup/demo guides and source-commit provenance. Python's standard-library static server is enough. Keep model artifacts and all reference data on Laptop 1. See `FINAL_HANDOFF.md` and `docs/CONSOLE_SCREENSHOT_CHECKLIST.md`.
