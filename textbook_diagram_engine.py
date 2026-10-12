"""
Textbook diagram retrieval engine for Physics Mentor AI.

This module reads the cleaned candidate index created by
clean_textbook_diagram_index.py. It intentionally distinguishes candidate
matches from visually verified diagrams.

Usage:
    from textbook_diagram_engine import search_textbook_diagrams, render_diagram_results

    matches = search_textbook_diagrams(
        query="vernier caliper least count",
        class_name="XI",
        volume="Volume I",
        limit=3,
    )
    render_diagram_results(matches)

The module does not modify app.py. Integrate it only after manually checking
the displayed source pages against the figure captions.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "data" / "textbook_diagrams" / "diagram_index_cleaned.json"


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _first(record: dict, *names: str, default=None):
    for name in names:
        value = record.get(name)
        if value not in (None, ""):
            return value
    return default


def _normalise_record(record: dict) -> dict:
    class_name = _first(record, "class", "class_name", "standard", default="")
    volume = _first(record, "volume", "volume_name", default="")
    caption = _norm(_first(record, "caption", "figure_caption", "title", "description", default=""))
    figure_number = _norm(_first(record, "figure_number", "figure", "figure_no", "fig_no", default=""))
    pdf_page = _first(record, "pdf_page", "pdf_page_number", "page", "page_number")
    pdf_path = _first(record, "pdf_path", "textbook_pdf", "source_pdf")
    image_path = _first(
        record, "rendered_image", "image_path", "rendered_page", "page_image", "image"
    )
    unit = _norm(_first(record, "unit_folder", "unit", "unit_name", "chapter", default=""))
    status = _norm(_first(record, "verification_status", "status", default="CANDIDATE_NOT_VISUALLY_VERIFIED"))
    return {
        **record,
        "_class": _norm(class_name).upper(),
        "_volume": _norm(volume).lower(),
        "_caption": caption,
        "_figure_number": figure_number,
        "_pdf_page": int(pdf_page) if str(pdf_page or "").isdigit() else None,
        "_pdf_path": _norm(pdf_path),
        "_image_path": _norm(image_path),
        "_unit": unit,
        "_status": status or "CANDIDATE_NOT_VISUALLY_VERIFIED",
    }


def load_textbook_diagram_index(index_path: str | Path | None = None) -> list[dict]:
    path = Path(index_path) if index_path else INDEX_PATH
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise FileNotFoundError(
            f"Diagram index not found: {path}. Run build_textbook_diagram_index.py "
            "and clean_textbook_diagram_index.py first."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return [_normalise_record(item) for item in raw if isinstance(item, dict)]


def _query_terms(query: str) -> list[str]:
    # Keep useful physics tokens and discard common English filler words.
    stop = {
        "what", "is", "are", "the", "a", "an", "of", "for", "to", "in", "on",
        "explain", "describe", "show", "draw", "diagram", "figure", "about",
        "with", "and", "how", "does", "do", "why", "class", "volume", "unit",
    }
    terms = re.findall(r"[a-zA-Z0-9]+", query.lower())
    return [t for t in terms if len(t) > 1 and t not in stop]


def search_textbook_diagrams(
    query: str,
    class_name: str | None = None,
    volume: str | None = None,
    unit: str | None = None,
    limit: int = 5,
    index_path: str | Path | None = None,
) -> list[dict]:
    """Return ranked candidate figure records; results are not automatically verified."""
    if limit < 1:
        return []
    records = load_textbook_diagram_index(index_path)
    terms = _query_terms(query)
    target_class = _norm(class_name).upper() if class_name else ""
    target_volume = _norm(volume).lower() if volume else ""
    target_unit = _norm(unit).lower() if unit else ""
    ranked = []

    for record in records:
        if target_class and record["_class"] != target_class:
            continue
        if target_volume and target_volume not in record["_volume"]:
            continue
        if target_unit and target_unit not in record["_unit"].lower():
            # Permit matching against the source text file path too.
            source_file = _norm(_first(record, "unit_text_file", "source_text_file", "source_file", default="")).lower()
            if target_unit not in source_file:
                continue

        haystack = " ".join([
            record["_caption"],
            record["_figure_number"],
            record["_unit"],
            _norm(_first(record, "source_title", "textbook_title", default="")),
            _norm(_first(record, "unit_text_file", "source_text_file", "source_file", default="")),
        ]).lower()

        score = 0
        for term in terms:
            if term in haystack:
                score += 3 if term in record["_caption"].lower() else 1
        if target_unit and target_unit in record["_unit"].lower():
            score += 4
        if not terms and not target_unit:
            score = 1

        if score > 0:
            image_path = record["_image_path"]
            if image_path:
                resolved = Path(image_path)
                if not resolved.is_absolute():
                    resolved = ROOT / resolved
                record["resolved_image_path"] = str(resolved)
                record["image_exists"] = resolved.exists()
            else:
                record["resolved_image_path"] = ""
                record["image_exists"] = False
            record["match_score"] = score
            record["is_visually_verified"] = (
                "VISUALLY_VERIFIED" in record["_status"].upper()
                and "NOT_VISUALLY" not in record["_status"].upper()
                and "CANDIDATE" not in record["_status"].upper()
                and "REVIEW_" not in record["_status"].upper()
            )
            ranked.append(record)

    ranked.sort(
        key=lambda r: (
            -r["match_score"],
            not r["image_exists"],
            r["_pdf_page"] or 10**9,
            r["_caption"].lower(),
        )
    )
    return ranked[:limit]


def render_diagram_results(results: list[dict], st_module=None) -> None:
    """Render candidate textbook pages in Streamlit with clear verification labels."""
    if st_module is None:
        import streamlit as st_module

    if not results:
        st_module.info("No matching textbook figure was found in the current index.")
        return

    st_module.subheader("📘 Related textbook figure/page")
    for result in results:
        caption = result.get("_caption") or "Textbook figure"
        figure_no = result.get("_figure_number") or "Figure number unavailable"
        class_name = result.get("_class") or "Class unavailable"
        volume = result.get("_volume") or "Volume unavailable"
        page = result.get("_pdf_page")
        status = result.get("_status", "CANDIDATE_NOT_VISUALLY_VERIFIED")
        st_module.markdown(f"**{figure_no} — {caption}**")
        st_module.caption(f"{class_name} · {volume} · PDF page {page if page else 'unknown'}")
        if result.get("is_visually_verified"):
            st_module.success("This figure mapping has been visually verified.")
        else:
            st_module.warning(
                "Candidate textbook page — verify the figure and caption before treating "
                "this as a confirmed diagram."
            )
        image_path = result.get("resolved_image_path")
        if image_path and Path(image_path).exists():
            st_module.image(str(image_path), caption=f"Original textbook PDF page {page or ''}", use_container_width=True)
        else:
            st_module.info("Rendered page image is missing. Check the diagram index image path.")
        st_module.divider()
