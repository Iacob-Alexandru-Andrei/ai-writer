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

    print("\n=== All probes complete ===")


if __name__ == "__main__":
    main()
