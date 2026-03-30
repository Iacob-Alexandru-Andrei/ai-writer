## Overview

Write a comprehensive academic paper on "Self-Improving Multi-Agent Systems: From Clade-Metaproductivity to Hyperagent Architectures" using the ai-writer pipeline, while simultaneously exercising every feature in the codebase as a live integration test. The paper is the primary deliverable; blog, LinkedIn, and Twitter derivatives provide coverage of short-form workflows and all five content types. Every pipeline feature — backends, routing, corpus ingestion, style analysis, outline engines, bibliography handling, few-shot examples, prompt assembly, session management, validation, integrations, slash commands, and templates — is exercised and verified through the writing process itself.

Corpus: 4 source papers (2 `.md`, 2 `.tex`) + 2 `.bib` files in `workspace/hgm-hyperagents/corpus/`.

## Requirements

### R01: Environment preparation
Install all optional dependencies (`knowledge_storm`, `dspy`, `instructor`, `spacy`, `pandoc`) so every integration path is available. Verify slash commands are accessible. Create evidence output directory `workspace/hgm-hyperagents/evidence/`.

### R02: Corpus ingestion and LaTeX normalization
Load all 4 corpus files. Verify `.md` files load directly. Verify `.tex` files are normalized to Markdown — first via pandoc, then verify regex fallback also works. Confirm word counts are computed. Exercise `corpus.expose_for_grep()`.

### R03: Bibliography parsing (both formats)
Parse both `.bib` files via `load_bibtex()`. Create a `references.md` from the bib entries and parse it via `load_markdown()` to exercise both bibliography ingestion paths. Verify all CitationEntry fields are populated.

### R04: Few-shot example system
Run `suggest_examples()` on the corpus to get relevance-ranked suggestions. Call `select_examples()` with user-specified files, including one with `section` extraction. Verify per-example budget (2000 tokens) and total budget cap (6000 tokens). Confirm truncation marker appears when budget is exceeded.

### R05: Style analysis
Run style analysis on the corpus via the LLM backend. Verify the returned StyleProfile has all structured fields populated (vocabulary_level, sentence_patterns, paragraph_structure, tone, opening_patterns, closing_patterns, structural_conventions). If spaCy is available, verify quantitative metrics (POS distribution, avg sentence length, type-token ratio).

### R06: Outline engine — all three modes
Test outline generation in all three OutlineEngine modes:
- `STORM`: Call StormAdapter.generate_outline() directly. Verify it returns a flat list of section titles.
- `LLM`: Set outline_engine=llm, verify STORM is bypassed entirely and outline is generated via the configured LLM backend.
- `AUTO`: Set outline_engine=auto with STORM available, verify STORM is tried first. Then simulate STORM failure to verify fallback to LLM.

### R07: ClaudeCLIBackend with model selection
Use ClaudeCLIBackend with explicit `--model opus-4.6` and `--max-tokens` flags for style analysis and at least 2 paper sections. Verify the constructed command includes the model flag.

### R08: CodexBackend end-to-end
Use CodexBackend with `gpt-5.4` for at least 2 paper sections. Verify codex-run dispatch with 7200s timeout, output file reading, and system prompt folding into user prompt.

### R09: FallbackBackend transport-error recovery
Exercise FallbackBackend by triggering a transport error on the primary backend during one section generation. Verify the secondary backend is invoked and the section is generated successfully. Log the fallback event.

### R10: Auto provider with burn-pressure routing
Set provider=auto for at least one stage. Write `/tmp/orch-routing.json` with `{"primary": "claude"}`, verify Claude is selected. Change to `{"primary": "codex"}`, verify Codex is selected. Verify missing/malformed file defaults to Claude.

### R11: Per-stage model selection
Configure different ModelSpec per stage: style_analysis uses one provider/model, outline uses another, section_generation uses a third. Verify each stage dispatches to the correct backend by checking the session's llm_settings snapshot and backend invocation logs.

### R12: Three-layer config precedence
Start a session with conflicting YAML defaults, env vars (`WRITER_PROVIDER`, `WRITER_MODEL`), and CLI `--llm` overrides. Verify CLI overrides win over env, which wins over YAML. Verify the resolved config is stored in the session.

### R13: Paper writing — full long-form workflow
Write the complete paper via LongFormWorkflow: start() with corpus + bibliography + examples → generate_outline() → generate_section() for all sections → finalize(). Use the `/write paper` and `/write-next` slash commands. The paper has 10 sections covering HGM, CMP, DGM, MARS, hyperagents, frozen critic.

### R14: Prompt assembly with all components
Verify assemble_prompt() includes all components: style_profile, few_shot_examples, bibliography_hints, outline_context, running_context. Dump at least one AssembledPrompt.budget_report to evidence.

### R15: Prompt budget stress test
For one section, set deliberately low context_length (e.g., 50000) and verify cascading truncation fires in priority order (running_context → few_shot → bibliography → style_profile → outline). Verify `[... truncated ...]` markers appear.

### R16: Running context maintenance
Verify running_context grows across sections — first section has empty context, subsequent sections include summaries of prior sections. Verify truncation to `token_budgets.running_context` (4000 tokens default).

### R17: Session management — full lifecycle
Exercise: create(), save(), load(), advance(), set_status(), set_outline(), set_style_profile(). Verify LLM settings snapshot persists across save/load. Exercise list_sessions(), get_latest(), delete() on a smoke session.

### R18: Session resume with LLM override
After generating some sections, resume the session via `/write-next` with `--llm` overrides. Verify the stored LLM config is loaded as base and CLI overrides are merged on top.

### R19: Citation audit
After paper finalization, run citation audit. Verify: LaTeX `\cite{}` keys extracted, Markdown `[@key]` keys extracted, inline `(Author, Year)` pseudo-keys matched via fuzzy matching. Generate and persist the audit report.

### R20: Paper validation
Validate the finalized paper via `validate_content(ContentType.PAPER)`. Verify it checks for required sections (abstract, introduction, conclusion). The paper must pass validation.

### R21: Blog post — long-form derivative
Generate a blog post from the paper topic using the same corpus. Use env-var-only LLM overrides (no CLI). Verify blog template loading, H2 heading validation, word count validation (1500-2500 words). Exercise prompt budget with custom context_length.

### R22: LinkedIn post — short-form workflow
Generate a LinkedIn post via ShortFormWorkflow. Exercise corpus-backed style analysis. Call regenerate(feedback=...) at least once. Validate character limit (3000) and hook length (210). Verify `/write-linkedin` slash command.

### R23: Twitter thread — short-form with auto-retry
Generate a Twitter thread via ShortFormWorkflow. Verify per-tweet limit (280 chars), thread limit (15 tweets), and auto-retry on validation failure. Verify `/write-x-thread` slash command.

### R24: Thesis smoke test
Start a thesis session with the same corpus to verify thesis-specific config, template, and validator (requires intro + conclusion). Generate outline and at least 1 section. Verify `/write-thesis` slash command.

### R25: Integrations — CSW, DSPy, Instructor, OpenDraft
Exercise each optional integration:
- `csw_adapter.py`: Run iterative_revise() on one paper section.
- `dspy_signatures.py`: Load PaperSectionSignature and at least one other signature.
- `instructor_models.py`: Call generate_structured() with an Instructor model.
- `opendraft_patterns.py`: Exercise available patterns.
Graceful fallback if a dependency is unavailable.

### R26: Template and config registry
Load all 6 templates (paper, thesis, blog, linkedin, twitter, style_analysis) via ContentTypeRegistry. Load all 5 content-type configs. Verify each template has correct placeholders and each config has expected fields.

### R27: All slash commands exercised
Exercise every slash command at least once: `/write`, `/write-paper`, `/write-thesis`, `/write-blog`, `/write-linkedin`, `/write-x-thread`, `/write-next`, `/write-status`. Verify argument parsing and output format.

### R28: Evidence collection
Every task writes evidence to `workspace/hgm-hyperagents/evidence/`: session snapshots, backend invocation logs, prompt dumps, validation reports, audit reports, and final artifacts. Evidence is committed to git.

### R29: Fix write-next.md generate path
The generate and regenerate code blocks in write-next.md reconstruct `Pipeline()` without passing `llm_overrides`, losing the overrides parsed in block 1. Fix so overrides are passed through to all Pipeline() calls.

## Dual-Plan Synthesis

### Agreements
- Use the paper as the backbone; derive blog/LinkedIn/Twitter from the finalized paper corpus
- Rotate backend configurations per stage for deterministic coverage
- Collect explicit evidence (session JSON, prompt dumps, validation reports) after each step
- Test all 5 content types and both workflow paths
- Test STORM in isolation before the main paper flow
- Start a fresh session (old session has no llm_settings)

### Divergences
- **Fault injection**: Codex proposed wrapper scripts for deterministic transport failures; Claude relied on natural failures. **Chosen: Codex approach** — wrappers give reproducible coverage without depending on actual backend failures.
- **Integration testing**: Codex proposed a Python harness for features unreachable via slash commands (DSPy, Instructor, CSW, session delete); Claude had these inline. **Chosen: Codex approach** — a harness is cleaner and isolates integration tests from the writing flow.
- **Session strategy**: Claude proposed resuming old session 10c36019e495; Codex starts fresh. **Chosen: Start fresh** — old session lacks llm_settings and was generated with default Sonnet, making it unsuitable for backend coverage.
- **Bug identified**: Codex found write-next.md generate path doesn't forward --llm overrides (R29). Both agree this needs fixing.

## Technical Approach

**Phase 1 — Environment & Preflight**: Install deps, create evidence dirs, verify corpus loads correctly with both normalization paths, parse both bib formats, test few-shot selection.

**Phase 2 — Outline Engine Probes**: Test all three OutlineEngine modes (STORM, LLM, AUTO) in isolation before the main paper flow. This ensures outline generation works regardless of which mode the paper run uses.

**Phase 3 — Paper Writing (backbone)**: Start fresh paper session via `/write paper` with per-stage config overrides. Generate outline, then sections with rotating backends (Claude for some, Codex for others, auto for at least one). Exercise FallbackBackend, session resume, and running context across all 10 sections.

**Phase 4 — Post-Paper Verification**: Finalize, run citation audit, validate, run CSW revision on one section, dump prompt budgets.

**Phase 5 — Derivative Content**: Generate blog (long-form), LinkedIn (short-form + regenerate), Twitter thread (short-form + auto-retry), thesis smoke (long-form different config). Each exercises unique validators and templates.

**Phase 6 — Integration Harness**: Python script exercises features not reachable via slash commands: DSPy signatures, Instructor models, OpenDraft patterns, session CRUD operations, config/template registry loading.

**Phase 7 — Evidence & Verification**: Collect all evidence, verify feature coverage matrix is complete, commit artifacts.

## Edge Cases & Error Handling

- **STORM unavailable**: If `knowledge_storm` fails to import, AUTO mode must fall back to LLM gracefully. Verify by testing with and without the package.
- **Codex timeout**: CodexBackend has 7200s timeout. For testing, sections should complete well within this. If Codex hangs, FallbackBackend catches the timeout and retries with Claude.
- **Prompt budget overflow**: Deliberately low context_length must trigger cascading truncation, not crash. Verify truncation markers present.
- **Empty running context**: First section must handle empty running_context gracefully.
- **Session corruption**: Test that loading a session with missing optional fields (no llm_settings, no style_profile) works.
- **Bibliography format mismatch**: Test that malformed bib entries are skipped with warnings, not crash the parser.
- **Short-form validation retry exhaustion**: If a short-form generation fails validation 3 times, it returns the best attempt rather than crashing.
- **Missing routing file**: Auto provider with no `/tmp/orch-routing.json` defaults to Claude.
- **write-next.md override bug**: Fixed in R29; verify overrides propagate through all Pipeline() calls.

## Acceptance Criteria

### AC01: Corpus and LaTeX normalization
All 4 corpus files load. `.tex` files produce valid Markdown via pandoc. Regex fallback also produces valid Markdown when pandoc is bypassed. Word counts > 0 for all files.

### AC02: Bibliography dual-format
Both `.bib` files parse into CitationEntry lists with populated fields. `references.md` created from bib data parses via `load_markdown()`. Entry counts match between formats.

### AC03: Few-shot budget enforcement
`select_examples()` with 3+ files respects per-example (2000) and total (6000) budgets. At least one example shows `[... truncated ...]` marker when budget exceeded.

### AC04: Style profile completeness
StyleProfile has non-empty values for all 7 structured fields. If spaCy available, quantitative metrics dict is non-empty.

### AC05: Outline engine triple coverage
STORM mode returns section list. LLM mode returns section list without calling StormAdapter. AUTO mode calls STORM first; with simulated STORM failure, falls back to LLM.

### AC06: Backend rotation verified
Session llm_settings snapshot shows different providers/models for different stages. At least 2 sections generated by Claude, at least 2 by Codex, at least 1 via auto routing.

### AC07: FallbackBackend fires
Evidence log shows primary backend failure → secondary backend invocation → successful section generation for at least one section.

### AC08: Config precedence proven
Session created with YAML `provider: auto`, env `WRITER_PROVIDER=claude`, CLI `--llm provider=codex` stores `provider: codex` in llm_settings.

### AC09: Paper complete and valid
10-section paper generated, finalized, passes `validate_content(ContentType.PAPER)` (abstract, introduction, conclusion present). Citation audit report generated.

### AC10: Prompt budget truncation
At least one prompt assembly with low context_length produces budget_report showing truncation. `[... truncated ...]` marker present in at least one component.

### AC11: Running context grows
First section's running_context is empty. Section 5+'s running_context contains summaries of prior sections and is within 4000-token budget.

### AC12: Session round-trip
Session saved with llm_settings, reloaded via resume_session(), llm_settings matches original. CLI overrides on resume are merged correctly.

### AC13: All content types generated
Paper, thesis (at least 1 section), blog, LinkedIn, and Twitter content all generated and finalized. Each passes its type-specific validator.

### AC14: Short-form feedback loop
LinkedIn post regenerated with feedback at least once. Twitter thread triggers at least one validation retry.

### AC15: All slash commands invoked
Evidence shows invocation of: `/write`, `/write-paper`, `/write-thesis`, `/write-blog`, `/write-linkedin`, `/write-x-thread`, `/write-next`, `/write-status`.

### AC16: Integration coverage
CSW iterative_revise() called on at least one section. DSPy signatures loaded. Instructor generate_structured() called (or graceful fallback logged). OpenDraft patterns exercised (or graceful fallback logged).

### AC17: Template and config registry complete
All 6 templates loaded and verified. All 5 content-type configs loaded and verified.

### AC18: Evidence committed
`workspace/hgm-hyperagents/evidence/` contains: session snapshots, prompt dumps, validation reports, citation audit report, and all generated content. Committed to git.

### AC19: write-next.md fix verified
`/write-next` with `--llm provider=codex` uses Codex for the actual generation, not just the status check.
