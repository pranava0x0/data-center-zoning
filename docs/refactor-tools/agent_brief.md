# Split each state's all_sources.py into one module per issuing source

Project: /Users/pranava/Projects/local ordinance zoning (not a git repo; other agents are editing OTHER state folders at the same time).
Each state folder scripts/collectors/<state>/ has an `all_sources.py` (for this round: `history.py`) that collects permit history from several government
sources (a state agency register, a city's permit GIS layer, council minutes, ...) in one file. Goal: a reader can tell from
the file names which issuer/register each piece covers.

## Reference example (already done; read it first)
scripts/collectors/minnesota/: eqb_environmental_reviews.py, minneapolis_building_permits.py, chaska_council_decisions.py,
history.py. Each source module has a docstring naming the issuer and register, `download()` (live fetch, code moved
verbatim) and `rows()` (offline build, code moved verbatim; may also return audit counts). history.py is the entry point:
`--refresh` (use the SAME live flag the old file used, e.g. --refresh or --fetch, and keep every other CLI flag) calls each
source's download, then combines rows in the ORIGINAL order and writes outputs exactly as before.

## Rules
- Output must be byte-identical. Move code verbatim; keep record order, IDs, every file the old script wrote, and validation
  JSON contents. Do not "improve" logic, dates, wording, or formatting.
- Edit ONLY scripts/collectors/<your states>/. Never edit scripts/lib/, other states, Makefile, data/, docs/, tests/, or
  data/jurisdiction_registry.json (the coordinator updates those).
- Imports: lib/ modules and files in the same state folder only (dotted, e.g. `from collectors.texas import harris_county_permits`).
  Keep the bootstrap line `import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))` at
  the top of every new module (after the docstring).
- Naming: lowercase, `<issuer>_<register>.py`, e.g. `deq_air_permits.py`, `honolulu_building_permits.py`,
  `phoenix_planning_cases.py`, `epa_icis_npdes.py` (for the shared EPA ICIS join). Statewide agencies use the agency's
  short name; cities and counties use their name.
- If the file has only one source, or its sources are so intertwined that splitting would change behavior, do NOT force a
  split: rename all_sources.py to history.py and give it a docstring naming the issuers. Say so in your report.
- Other modules in the same state folder that import `collectors.<state>.all_sources` (e.g. new_york/decisions.py) must be
  updated to import from the new modules.
- Shared CLI behaviour: `python3 scripts/collectors/<state>/history.py` (offline) and the live flag must still work.
  You cannot test live mode (the network must stay blocked); keep download code verbatim.

## Verify every state before deleting its all_sources.py
1. Write the new modules and history.py while all_sources.py still exists.
2. Run: `python3 docs/refactor-tools/verify_state.py <state>`
   It runs history.py twice with the network blocked and compares every file the old collector wrote to the published bytes.
   It must print PASS. If it fails, fix it; do not edit data/ or output/ files to make it pass. If a run modifies a target
   file, restore it by running the ORIGINAL all_sources.py offline (same proxy env) before continuing.
3. Run the static check: `python3 docs/refactor-tools/undef.py scripts/collectors/<state>/*.py` (must print nothing for your new files).
4. Only after PASS, delete all_sources.py.

## Report (final message, concise)
Per state: new files with one-line purpose each; PASS/FAIL line from the verifier; anything not split and why; anything
you were unsure of in live (download) code.
