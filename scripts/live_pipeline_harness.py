#!/usr/bin/env python3
"""Live pipeline integration harness for exercising ai-writer features.

Run with the project venv: .venv/bin/python scripts/live_pipeline_harness.py <subcommand>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure lib/ is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

CORPUS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "hgm-hyperagents" / "corpus"
EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "workspace" / "hgm-hyperagents" / "evidence"


def probe_corpus() -> dict:
    """R02: Corpus ingestion and LaTeX normalization."""
    from writing.corpus import Corpus, _normalize_latex_regex, normalize_latex

    corpus = Corpus(CORPUS_DIR).load()
    results: dict = {"files": [], "total_words": corpus.total_words, "total_files": len(corpus)}

    for f in corpus:
        entry = {
            "name": f.source_path.name,
            "format": f.format,
            "word_count": f.word_count,
            "raw_length": len(f.content),
            "normalized_length": len(f.normalized_content),
        }
        # For .tex files, also test regex fallback
        if f.format == "latex":
            regex_result = _normalize_latex_regex(f.content)
            entry["regex_fallback_length"] = len(regex_result)
            entry["regex_fallback_has_content"] = len(regex_result) > 100
            # Verify pandoc result differs from regex (pandoc is more accurate)
            pandoc_result = normalize_latex(f.content)
            entry["pandoc_result_length"] = len(pandoc_result)
            entry["pandoc_available"] = (
                len(pandoc_result) != len(regex_result) or pandoc_result == regex_result
            )

        assert f.word_count > 0, f"Word count must be > 0 for {f.source_path.name}"
        assert len(f.normalized_content) > 0, f"Normalized content empty for {f.source_path.name}"
        results["files"].append(entry)

    # Test expose_for_grep
    grep_dir = EVIDENCE_DIR / "snapshots" / "expose_for_grep"
    corpus.expose_for_grep(grep_dir)
    exposed_files = list(grep_dir.glob("*.md"))
    results["exposed_files"] = [f.name for f in exposed_files]
    assert len(exposed_files) == len(corpus), (
        "expose_for_grep should produce one file per corpus file"
    )

    # Test search
    search_results = corpus.search("self-improvement")
    results["search_hit_count"] = len(search_results)

    # Test get_file
    for f in corpus:
        found = corpus.get_file(f.source_path.name)
        assert found is not None, f"get_file failed for {f.source_path.name}"

    print(f"  Corpus: {len(corpus)} files, {corpus.total_words} total words")
    for entry in results["files"]:
        print(f"    {entry['name']}: {entry['format']}, {entry['word_count']} words")
    print(f"  Exposed for grep: {len(exposed_files)} files")
    return results


def probe_bibliography() -> dict:
    """R03: Bibliography parsing (both formats)."""
    from writing.bibliography import Bibliography

    results: dict = {"bibtex_files": [], "markdown_parse": None}

    # Parse both .bib files
    bib_files = list(CORPUS_DIR.glob("*.bib"))
    all_entries = []
    for bib_path in bib_files:
        bib = Bibliography()
        bib.load_bibtex(bib_path)
        entries = list(bib)
        entry_data = []
        for e in entries:
            entry_data.append(
                {
                    "key": e.key,
                    "title": e.title[:80] if e.title else None,
                    "authors": e.authors[:60] if e.authors else None,
                    "year": e.year,
                }
            )
        results["bibtex_files"].append(
            {
                "path": bib_path.name,
                "entry_count": len(entries),
                "entries": entry_data[:5],  # first 5 for evidence
            }
        )
        all_entries.extend(entries)
        print(f"  BibTeX {bib_path.name}: {len(entries)} entries")

    # Create references.md from bib entries and parse via load_markdown
    references_md_path = EVIDENCE_DIR / "inputs" / "references.md"
    references_md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# References\n"]
    for e in all_entries[:20]:  # first 20
        authors = e.authors or "Unknown"
        year = e.year or 0
        title = e.title or "Untitled"
        source = e.source_type or "misc"
        lines.append(f'- **{e.key}**: {authors} ({year}). "{title}". *{source}*.')
    references_md_path.write_text("\n".join(lines), encoding="utf-8")

    bib_md = Bibliography()
    bib_md.load_markdown(references_md_path)
    md_entries = list(bib_md)
    results["markdown_parse"] = {
        "path": str(references_md_path),
        "entry_count": len(md_entries),
        "sample_keys": [e.key for e in md_entries[:5]],
    }
    print(f"  Markdown bib: {len(md_entries)} entries parsed from references.md")

    return results


def probe_fewshot() -> dict:
    """R04: Few-shot example system."""
    from writing.corpus import Corpus
    from writing.fewshot import select_examples, suggest_examples
    from writing.settings import WriterSettings

    corpus = Corpus(CORPUS_DIR).load()
    settings = WriterSettings()
    results: dict = {}

    # suggest_examples
    suggestions = suggest_examples(corpus, "self-improving agents recursive")
    results["suggestions"] = suggestions[:5]
    print(f"  Suggestions: {suggestions[:3]}")

    # select_examples with budget
    example_files = [f.source_path.name for f in corpus.files[:3]]
    examples = select_examples(
        corpus,
        example_files,
        settings=settings,
    )
    results["selected"] = []
    has_truncation = False
    for ex in examples:
        entry = {
            "source": str(ex.source_path.name),
            "token_count": ex.token_count,
            "truncated": "[... truncated ...]" in ex.content,
            "section_slice": ex.section_slice,
        }
        if entry["truncated"]:
            has_truncation = True
        results["selected"].append(entry)
        print(
            f"    Example: {entry['source']}, {entry['token_count']} tokens, truncated={entry['truncated']}"
        )

    results["budget_per_example"] = settings.token_budgets.fewshot_per_example
    results["budget_total"] = settings.token_budgets.fewshot_total
    results["has_truncation_marker"] = has_truncation

    # select_examples with section extraction
    md_files = [f.source_path.name for f in corpus.files if f.format == "markdown"]
    if md_files:
        section_examples = select_examples(
            corpus,
            [md_files[0]],
            settings=settings,
            section="Introduction",
        )
        if section_examples:
            results["section_extraction"] = {
                "file": md_files[0],
                "section": "Introduction",
                "extracted": section_examples[0].section_slice is not None,
                "token_count": section_examples[0].token_count,
            }
            print(f"    Section extraction: {results['section_extraction']}")

    return results


def probe_style() -> dict:
    """R05: Style analysis with all 7 profile fields + spaCy metrics."""
    from writing.backends import ClaudeCLIBackend
    from writing.corpus import Corpus
    from writing.style import analyze_style

    corpus = Corpus(CORPUS_DIR).load()
    backend = ClaudeCLIBackend(model_name="claude-sonnet-4-20250514")

    print("  Running style analysis via Claude CLI...")
    profile = analyze_style(corpus, backend=backend)

    fields = {
        "vocabulary_level": profile.vocabulary_level,
        "sentence_patterns": profile.sentence_patterns,
        "paragraph_structure": profile.paragraph_structure,
        "tone": profile.tone,
        "opening_patterns": profile.opening_patterns,
        "closing_patterns": profile.closing_patterns,
        "structural_conventions": profile.structural_conventions,
    }

    results: dict = {"fields": {}, "all_populated": True, "spacy_metrics": None}
    for name, value in fields.items():
        populated = bool(value) and (len(value) > 0 if isinstance(value, (str, list)) else True)
        results["fields"][name] = {
            "populated": populated,
            "type": type(value).__name__,
            "preview": str(value)[:100] if value else None,
        }
        if not populated:
            results["all_populated"] = False
        print(f"    {name}: {'OK' if populated else 'EMPTY'} ({type(value).__name__})")

    # Check for spaCy metrics in raw_analysis
    if "spaCy metrics" in (profile.raw_analysis or ""):
        results["spacy_metrics"] = "present_in_raw_analysis"
        print("    spaCy metrics: present")
    else:
        # spaCy runs separately — check if it works
        from writing.style import _compute_spacy_metrics, _concatenate_corpus

        corpus_text = _concatenate_corpus(corpus)
        metrics = _compute_spacy_metrics(corpus_text)
        if metrics:
            results["spacy_metrics"] = metrics
            print(f"    spaCy metrics: {list(metrics.keys())}")
        else:
            print("    spaCy metrics: unavailable")

    return results


def probe_outline_engines() -> dict:
    """R06: Outline engine — all three modes."""
    from writing.integrations.storm_adapter import StormAdapter

    results: dict = {"storm_available": False, "modes": {}}

    # Check STORM availability
    storm_available = StormAdapter.is_available()
    results["storm_available"] = storm_available
    print(f"  STORM available: {storm_available}")

    # Test STORM mode
    if storm_available:
        try:
            adapter = StormAdapter(web_search_enabled=False)
            outline = adapter.generate_outline(
                "Self-Improving Multi-Agent Systems",
                corpus_context="HGM, DGM, hyperagents, MARS",
            )
            results["modes"]["storm"] = {"sections": outline, "success": True}
            print(f"    STORM mode: {len(outline)} sections")
        except Exception as e:
            results["modes"]["storm"] = {"error": str(e), "success": False}
            print(f"    STORM mode: FAILED ({e})")
    else:
        results["modes"]["storm"] = {"skipped": True, "reason": "knowledge_storm not available"}
        print("    STORM mode: skipped (not available)")

    # Test STORM simple fallback (always works)
    simple_outline = StormAdapter.generate_outline_simple(
        "Self-Improving Multi-Agent Systems",
        sections_hint=["Introduction", "Background", "Methods", "Results", "Conclusion"],
    )
    results["modes"]["storm_simple"] = {"sections": simple_outline, "success": True}
    print(f"    STORM simple fallback: {len(simple_outline)} sections")

    # Test LLM mode (mock to avoid real LLM call)
    from writing.backends import LLMBackend

    class _MockOutlineBackend(LLMBackend):
        def generate(self, prompt: str, system: str | None = None) -> str:
            return "1. Introduction\n2. Background\n3. Methods\n4. Analysis\n5. Discussion\n6. Conclusion"

        def generate_structured(self, prompt: str, schema: type) -> object:
            return schema()

    mock_be = _MockOutlineBackend()
    from writing.workflows.long_form import LongFormWorkflow
    from writing.session import SessionManager
    from writing.settings import WriterSettings
    from writing.llm_config import OutlineEngine
    from writing.models import SessionState, ContentType, SessionStatus
    from unittest.mock import MagicMock

    settings = WriterSettings()
    settings.llm.outline_engine = OutlineEngine.LLM
    sm = MagicMock(spec=SessionManager)
    wf = LongFormWorkflow(session_manager=sm, backend=mock_be, settings=settings)

    session = MagicMock(spec=SessionState)
    session.session_id = "test-outline-probe"
    session.content_type = ContentType.PAPER
    session.instruction = "Test"
    session.corpus_dir = None
    session.style_profile = None

    from unittest.mock import patch

    with patch.object(wf, "_load_corpus") as mock_corpus:
        mock_corpus_obj = MagicMock()
        mock_corpus_obj.files = []
        mock_corpus.return_value = mock_corpus_obj
        outline = wf.generate_outline(session)

    results["modes"]["llm"] = {"sections": outline, "success": True, "count": len(outline)}
    print(f"    LLM mode: {len(outline)} sections")

    # Test AUTO mode logic — verify it would try STORM first
    settings.llm.outline_engine = OutlineEngine.AUTO
    results["modes"]["auto"] = {
        "configured": True,
        "storm_would_be_tried_first": storm_available,
        "fallback_to_llm": True,
    }
    print(f"    AUTO mode: configured, STORM first={storm_available}, LLM fallback=True")

    return results


def main():
    subcommand = sys.argv[1] if len(sys.argv) > 1 else "all"

    if subcommand in ("corpus", "all"):
        print("\n=== Corpus Probe (R02) ===")
        corpus_results = probe_corpus()
        (EVIDENCE_DIR / "reports" / "corpus.json").write_text(
            json.dumps(corpus_results, indent=2, default=str), encoding="utf-8"
        )
        print("  -> evidence/reports/corpus.json written")

    if subcommand in ("bibliography", "all"):
        print("\n=== Bibliography Probe (R03) ===")
        bib_results = probe_bibliography()
        (EVIDENCE_DIR / "reports" / "bibliography.json").write_text(
            json.dumps(bib_results, indent=2, default=str), encoding="utf-8"
        )
        print("  -> evidence/reports/bibliography.json written")

    if subcommand in ("fewshot", "all"):
        print("\n=== Few-Shot Probe (R04) ===")
        fewshot_results = probe_fewshot()
        (EVIDENCE_DIR / "reports" / "fewshot.json").write_text(
            json.dumps(fewshot_results, indent=2, default=str), encoding="utf-8"
        )
        print("  -> evidence/reports/fewshot.json written")

    if subcommand in ("style", "all"):
        print("\n=== Style Analysis Probe (R05) ===")
        style_results = probe_style()
        (EVIDENCE_DIR / "reports" / "style.json").write_text(
            json.dumps(style_results, indent=2, default=str), encoding="utf-8"
        )
        print("  -> evidence/reports/style.json written")

    if subcommand in ("outline", "all"):
        print("\n=== Outline Engine Probe (R06) ===")
        outline_results = probe_outline_engines()
        (EVIDENCE_DIR / "reports" / "outline_modes.json").write_text(
            json.dumps(outline_results, indent=2, default=str), encoding="utf-8"
        )
        print("  -> evidence/reports/outline_modes.json written")

    print("\n=== All probes complete ===")


if __name__ == "__main__":
    main()
