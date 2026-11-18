# Screenshot evidence index

All images below are genuine browser captures from actual local API execution. They demonstrate application behavior on separate local origins, not two physical laptops. The consolidated report includes the representative views needed to explain the implementation.

| File under results/screenshots/ | Evidence | Report use |
|---|---|---|
| ui_desktop.png | Student-test trip 00000052 with reference comparison, prediction and direct continuity | Section 7 |
| experiment_bench.png | Nine model configurations and five decoder comparisons from recorded development experiments | Section 7.1 |
| evaluator_ui_desktop.png | Reserved trip 00000023 with prediction/aggregate scoring; reference layer blocked | Section 7.2 |
| ui_mobile_top.png | Genuine 390 x 844 top viewport with settings, trip selection and metrics | Section 7.3 |
| ui_mobile_map.png | Same student-test route after scrolling to the map in a 390 x 844 viewport | Section 7.3 |
| api_documentation.png | Actual local FastAPI/OpenAPI page | Section 7.4, supplementary API documentation evidence |
| folium_development_map.png | Actual Folium student-test map with GPS, graph, reference and prediction layers | Section 6 |
| ui_mobile.png | Full mobile page, retained for inspection | Supporting asset |
| evaluator_ui_mobile.png | Full mobile reserved-mode page with no reference geometry | Supporting asset |
| evaluator_experiment_bench.png | Same development comparison table while reserved partition is active | Supporting asset; scores remain development scores |

## Mandatory missing image

Deliverables.pdf p6 requires successful API response evidence on the receiving laptop's CMD. The user confirmed that no genuine screenshot has yet been captured. Local browser/API documentation captures and copied log text do not replace this.

Use two actual laptops on a shared LAN or private VPN. Capture Laptop 1's actual receiving CMD after a request from Laptop 2, with matching request ID/trip ID and successful POST. Preserve the original image under submission_evidence/ and follow docs/CONSOLE_SCREENSHOT_CHECKLIST.md. The screenshot must be reviewed and added to the consolidated report once available. Do not relabel a same-laptop rehearsal as physical two-laptop evidence.
