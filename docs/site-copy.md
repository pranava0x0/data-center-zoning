# Site copy checks

The [build gate](../scripts/pipeline/check_site_copy.py) runs the writing and design trackers copied from the neighboring permittingreform project. The scanner and its tell registry are vendored here so rebuilding never requires another checkout or an AI call. It scans the HTML template, CSS and a generated transcript of ordinance titles, briefs and fallback summaries. Source quotations and agency fields are preserved as published. A separate literal check covers the labels and headings the owner flagged. Warnings are recorded for editorial review; failures stop the build. Nothing is allowlisted to make the report pass.

[Writing findings](../output/writing-check.json) · [Design findings](../output/design-check.json) · [Scanned text](../output/site-copy.md) · [Original trackers](../../permittingreform/tools/)
