"""Transform scraped metatft.com data into optimized RAG knowledge base.

Reads JSON data from scraper/data/ and produces structured documents
suitable for upload to Google AI Studio as grounding/RAG context.

Output formats:
- A single consolidated Markdown file (best for Google AI Studio upload)
- A single consolidated JSON file (structured, machine-readable)

Usage:
    python scraper/build_rag_knowledge.py
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def table_to_markdown(headers: List[str], rows: List[List[str]]) -> str:
    """Convert table data to Markdown table format."""
    if not headers and not rows:
        return ""

    cols = headers if headers else (rows[0] if rows else [])
    if not cols:
        return ""

    col_count = len(cols)
    lines = []

    if headers:
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * col_count) + " |")

    for row in rows:
        padded = row + [""] * (col_count - len(row)) if len(row) < col_count else row[:col_count]
        cleaned = [cell.replace("\n", " ").replace("|", "/") for cell in padded]
        lines.append("| " + " | ".join(cleaned) + " |")

    return "\n".join(lines)


def table_to_records(headers: List[str], rows: List[List[str]]) -> List[Dict[str, str]]:
    """Convert table data to list of dicts for JSON output."""
    if not headers:
        return [{"row": row} for row in rows]

    records = []
    for row in rows:
        record = {}
        for i, header in enumerate(headers):
            record[header] = row[i] if i < len(row) else ""
        records.append(record)
    return records


def build_page_markdown(name: str, page_data: Dict[str, Any]) -> str:
    """Build a Markdown section for one table page."""
    parts = []
    parts.append(f"## {name}")
    parts.append(f"Source: {page_data.get('url', 'N/A')}")

    if "error" in page_data:
        parts.append(f"\n*Data unavailable (scrape error)*\n")
        return "\n".join(parts)

    if page_data.get("description"):
        desc = page_data["description"].replace("\\n", "\n")
        parts.append(f"\n{desc}")

    for section in page_data.get("sections", []):
        level = min(section.get("level", 3) + 1, 4)
        parts.append(f"\n{'#' * level} {section['text']}")

    for i, table in enumerate(page_data.get("tables", [])):
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if headers or rows:
            if len(page_data.get("tables", [])) > 1:
                parts.append(f"\n**Table {i + 1}:**")
            parts.append("")
            parts.append(table_to_markdown(headers, rows))

    for i, lst in enumerate(page_data.get("lists", [])):
        if lst:
            parts.append("")
            for item in lst:
                clean_item = item.replace("\n", " ")
                parts.append(f"- {clean_item}")

    parts.append("")
    return "\n".join(parts)


def build_page_json(name: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a structured JSON entry for one table page."""
    entry: Dict[str, Any] = {
        "topic": name,
        "url": page_data.get("url", ""),
    }

    if "error" in page_data:
        entry["status"] = "unavailable"
        return entry

    if page_data.get("description"):
        entry["description"] = page_data["description"].replace("\\n", "\n")

    tables_out = []
    for table in page_data.get("tables", []):
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if headers or rows:
            tables_out.append({
                "headers": headers,
                "data": table_to_records(headers, rows),
            })
    if tables_out:
        entry["tables"] = tables_out

    lists_out = []
    for lst in page_data.get("lists", []):
        if lst:
            lists_out.append(lst)
    if lists_out:
        entry["lists"] = lists_out

    return entry


def build_knowledge_base(data_dir: str, output_dir: str) -> None:
    """Build RAG knowledge base files from scraped data.

    Args:
        data_dir: Path to directory containing scraped JSON files.
        output_dir: Path to directory where knowledge base files will be saved.
    """
    combined_path = os.path.join(data_dir, "metatft_all_tables.json")
    if not os.path.exists(combined_path):
        print(f"ERROR: {combined_path} not found. Run the scraper first.")
        return

    with open(combined_path, encoding="utf-8") as f:
        all_data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    scraped_at = all_data.get("metadata", {}).get("scraped_at", "unknown")

    # === Build Markdown knowledge base ===
    md_parts = []
    md_parts.append("# TFT (Teamfight Tactics) Tables & Odds - Knowledge Base")
    md_parts.append(f"\nData source: https://www.metatft.com/tables")
    md_parts.append(f"Last updated: {scraped_at}")
    md_parts.append("")
    md_parts.append("This document contains all TFT game mechanics data including:")
    md_parts.append("- Shop odds and champion pool sizes at each level")
    md_parts.append("- Augment distribution odds")
    md_parts.append("- Loot tables for various game mechanics")
    md_parts.append("- Opening encounter odds")
    md_parts.append("- Trait-specific reward tables")
    md_parts.append("")
    md_parts.append("---")

    json_entries = []

    for name, page_data in all_data.get("pages", {}).items():
        md_parts.append("")
        md_parts.append(build_page_markdown(name, page_data))
        md_parts.append("---")

        json_entries.append(build_page_json(name, page_data))

    # Save Markdown
    md_path = os.path.join(output_dir, "tft_knowledge_base.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts))
    print(f"Saved Markdown knowledge base: {md_path}")

    # === Build JSON knowledge base ===
    json_kb = {
        "title": "TFT Tables & Odds Knowledge Base",
        "source": "https://www.metatft.com/tables",
        "last_updated": scraped_at,
        "description": (
            "Comprehensive TFT game data including shop odds, pool sizes, "
            "loot tables, augment distributions, and trait-specific mechanics."
        ),
        "topics": json_entries,
    }

    json_path = os.path.join(output_dir, "tft_knowledge_base.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_kb, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON knowledge base: {json_path}")

    # === Build plain text version (most compatible for RAG) ===
    txt_parts = []
    txt_parts.append("TFT (TEAMFIGHT TACTICS) TABLES & ODDS - KNOWLEDGE BASE")
    txt_parts.append(f"Data source: https://www.metatft.com/tables")
    txt_parts.append(f"Last updated: {scraped_at}")
    txt_parts.append("=" * 60)

    for name, page_data in all_data.get("pages", {}).items():
        txt_parts.append("")
        txt_parts.append(f"TOPIC: {name}")
        txt_parts.append(f"URL: {page_data.get('url', 'N/A')}")
        txt_parts.append("-" * 40)

        if "error" in page_data:
            txt_parts.append("Data unavailable (scrape error)")
            continue

        if page_data.get("description"):
            txt_parts.append(page_data["description"].replace("\\n", "\n"))
            txt_parts.append("")

        for table in page_data.get("tables", []):
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if headers:
                txt_parts.append("  " + " | ".join(headers))
                txt_parts.append("  " + "-" * 40)
            for row in rows:
                cleaned = [cell.replace("\n", " ") for cell in row]
                txt_parts.append("  " + " | ".join(cleaned))
            txt_parts.append("")

        for lst in page_data.get("lists", []):
            for item in lst:
                txt_parts.append(f"  * {item.replace(chr(10), ' ')}")
            txt_parts.append("")

    txt_path = os.path.join(output_dir, "tft_knowledge_base.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_parts))
    print(f"Saved plain text knowledge base: {txt_path}")

    # Print summary
    total_pages = len(all_data.get("pages", {}))
    pages_with_data = sum(
        1 for p in all_data["pages"].values()
        if len(p.get("tables", [])) > 0 or len(p.get("lists", [])) > 0
    )
    md_size = os.path.getsize(md_path)
    json_size = os.path.getsize(json_path)
    txt_size = os.path.getsize(txt_path)

    print(f"\n{'=' * 60}")
    print("KNOWLEDGE BASE SUMMARY")
    print(f"{'=' * 60}")
    print(f"Pages with data: {pages_with_data}/{total_pages}")
    print(f"Markdown size:   {md_size / 1024:.1f} KB")
    print(f"JSON size:       {json_size / 1024:.1f} KB")
    print(f"Plain text size: {txt_size / 1024:.1f} KB")
    print(f"\nFiles saved to: {output_dir}/")
    print("  - tft_knowledge_base.md   (best for Google AI Studio)")
    print("  - tft_knowledge_base.json (structured, machine-readable)")
    print("  - tft_knowledge_base.txt  (plain text, most compatible)")
    print(f"{'=' * 60}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "scraper", "data")
    output_dir = os.path.join(project_root, "scraper", "knowledge_base")

    print("Building TFT RAG Knowledge Base...")
    print(f"Input:  {data_dir}")
    print(f"Output: {output_dir}")
    print()

    build_knowledge_base(data_dir, output_dir)


if __name__ == "__main__":
    main()
