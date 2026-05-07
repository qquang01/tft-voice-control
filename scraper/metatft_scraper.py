"""Scraper for metatft.com/tables data.

Uses Playwright via CDP to connect to a running Chrome instance and extract
all TFT tables data (shop odds, pool sizes, loot tables, augment distributions, etc.)
from https://www.metatft.com/tables.

Output: JSON files in scraper/data/ directory.

Usage:
    python scraper/metatft_scraper.py

Requirements:
    pip install playwright
    A Chrome instance must be running with --remote-debugging-port
    (default CDP endpoint: http://localhost:9222)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from playwright.async_api import Page, async_playwright

# All known table pages on metatft.com/tables
TABLE_PAGES: Dict[str, str] = {
    "Shop Odds & Pool Sizes": "https://www.metatft.com/tables/shop-odds",
    "Augment Distributions": "https://www.metatft.com/tables/augment-distibutions",
    "Opening Encounter Odds": "https://www.metatft.com/tables/portal-odds",
    "Space Gods": "https://www.metatft.com/tables/space-gods",
    "Anima Rewards and Weapons (Set 17)": "https://www.metatft.com/tables/anima",
    "Booster Pack Augment": "https://www.metatft.com/tables/booster-pack-augment",
    "Ixtal Cashout Loot Tables": "https://www.metatft.com/tables/ixtal",
    "Bilgewater Shop": "https://www.metatft.com/tables/bilgewater",
    "Xerath Charms": "https://www.metatft.com/tables/xerath-charms",
    "Yordle Loot": "https://www.metatft.com/tables/yordle-loot",
    "World Runes": "https://www.metatft.com/tables/world-runes",
    "Piltover Items": "https://www.metatft.com/tables/piltover-items",
    "Power Up Possibilities": "https://www.metatft.com/tables/powerups",
    "Crystal Gambit": "https://www.metatft.com/tables/crystal-gambit",
    "Twisted Fate Bounties": "https://www.metatft.com/tables/twisted-fate-bounties",
    "Golden Quest Loot Tables": "https://www.metatft.com/tables/golden-quest",
    "Exalted Adventure": "https://www.metatft.com/tables/exalted-adventure",
    "Golden Egg": "https://www.metatft.com/tables/golden-egg",
    "Anima Squad Weapons": "https://www.metatft.com/tables/anima-squad",
    "Augment Hacks": "https://www.metatft.com/tables/augment-hacks",
    "Treasure Dragon Loot Tables": "https://www.metatft.com/tables/treasure-dragon",
    "Cypher Loot Tables": "https://www.metatft.com/tables/cypher-loot",
    "Headliner Odds": "https://www.metatft.com/tables/headliner-odds",
    "Heartsteel Loot Tables": "https://www.metatft.com/tables/heartsteel",
    "8-bit Loot Tables": "https://www.metatft.com/tables/8bit",
    "Superfan Items": "https://www.metatft.com/tables/superfan",
}

DEFAULT_CDP_ENDPOINT = "http://localhost:9222"
PAGE_LOAD_WAIT_MS = 5000
MAX_RETRIES = 3
RETRY_DELAY_MS = 2000


async def extract_page_data(page: Page) -> Dict[str, Any]:
    """Extract all structured data from a single metatft table page.

    Extracts:
    - Page title and description
    - HTML tables (with headers and rows)
    - List items (e.g. pool sizes, loot drops)
    - Section headings for context
    - Image-labeled items (champion/item icons with text)
    """
    data = await page.evaluate('''() => {
        const result = {
            title: document.title,
            url: window.location.href,
            sections: [],
            tables: [],
            lists: [],
            labeled_items: []
        };

        // Extract page heading and description
        const mainContent = document.querySelector('.DropTablePageContent, .TablePageContent, [class*="PageContent"]');
        const root = mainContent || document.body;

        // Extract section headings
        const headings = root.querySelectorAll('h1, h2, h3, h4');
        headings.forEach(h => {
            const text = h.innerText.trim();
            if (text) {
                result.sections.push({
                    level: parseInt(h.tagName.substring(1)),
                    text: text
                });
            }
        });

        // Extract HTML tables
        const tables = root.querySelectorAll('table');
        tables.forEach((table, idx) => {
            const tableData = { index: idx, headers: [], rows: [] };

            // Get headers from thead or first row
            const headerCells = table.querySelectorAll('thead th, thead td');
            if (headerCells.length > 0) {
                tableData.headers = Array.from(headerCells).map(th => th.innerText.trim());
            }

            // Get all body rows
            const bodyRows = table.querySelectorAll('tbody tr');
            bodyRows.forEach(tr => {
                const cells = Array.from(tr.querySelectorAll('td, th')).map(td => {
                    // Check for images (champion/item icons)
                    const img = td.querySelector('img');
                    const imgAlt = img ? (img.alt || img.title || '') : '';
                    const text = td.innerText.trim();
                    return imgAlt ? `${text} [${imgAlt}]`.trim() : text;
                });
                if (cells.length > 0) {
                    tableData.rows.push(cells);
                }
            });

            // Fallback: if no thead, treat first row as header
            if (tableData.headers.length === 0 && tableData.rows.length > 0) {
                const firstRowCells = table.querySelector('tr');
                if (firstRowCells) {
                    const cells = Array.from(firstRowCells.querySelectorAll('td, th')).map(c => c.innerText.trim());
                    if (cells.some(c => c && isNaN(parseFloat(c.replace('%', ''))))) {
                        tableData.headers = cells;
                        tableData.rows.shift();
                    }
                }
            }

            if (tableData.rows.length > 0 || tableData.headers.length > 0) {
                result.tables.push(tableData);
            }
        });

        // Extract unordered/ordered lists
        const listElements = root.querySelectorAll('ul, ol');
        listElements.forEach(list => {
            const items = Array.from(list.querySelectorAll(':scope > li')).map(li => {
                const text = li.innerText.trim();
                const img = li.querySelector('img');
                const imgAlt = img ? (img.alt || img.title || '') : '';
                return imgAlt ? `${text} [${imgAlt}]`.trim() : text;
            });
            if (items.length > 0) {
                result.lists.push(items);
            }
        });

        // Extract card/tile-based data (many pages use icon grids)
        const cardSelectors = [
            '.DropTableItem', '.DropTableRow', '.LootTableItem',
            '.TableItem', '.OddsItem', '[class*="DropTable"] [class*="Item"]',
            '[class*="LootTable"] [class*="Item"]',
            '[class*="TableRow"]', '[class*="OddsRow"]'
        ];

        cardSelectors.forEach(selector => {
            try {
                const cards = root.querySelectorAll(selector);
                cards.forEach(card => {
                    const text = card.innerText.trim();
                    const imgs = card.querySelectorAll('img');
                    const imgNames = Array.from(imgs).map(i => i.alt || i.title || '').filter(Boolean);

                    if (text || imgNames.length > 0) {
                        result.labeled_items.push({
                            text: text,
                            images: imgNames,
                            selector: selector
                        });
                    }
                });
            } catch (e) {
                // Selector might not be valid, skip
            }
        });

        // Extract any paragraph text that contains useful info
        const paragraphs = root.querySelectorAll('p, .description, [class*="Description"]');
        const descriptions = [];
        paragraphs.forEach(p => {
            const text = p.innerText.trim();
            if (text && text.length > 10 && !text.includes('Download') && !text.includes('Patreon')) {
                descriptions.push(text);
            }
        });
        if (descriptions.length > 0) {
            result.description = descriptions.join('\\n');
        }

        return result;
    }''')
    return data


async def scrape_all_tables(
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
    output_dir: str = "scraper/data",
    pages: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Scrape all table pages from metatft.com.

    Args:
        cdp_endpoint: Chrome DevTools Protocol endpoint URL.
        output_dir: Directory to save JSON output files.
        pages: Optional dict of {name: url} to scrape. Defaults to TABLE_PAGES.

    Returns:
        Dict containing all scraped data with metadata.
    """
    if pages is None:
        pages = TABLE_PAGES

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    abs_output_dir = os.path.join(project_root, output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    all_data: Dict[str, Any] = {
        "metadata": {
            "source": "https://www.metatft.com/tables",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_pages": len(pages),
        },
        "pages": {},
    }

    async with async_playwright() as p:
        print(f"Connecting to Chrome via CDP at {cdp_endpoint}...")
        browser = await p.chromium.connect_over_cdp(cdp_endpoint)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()

        for i, (name, url) in enumerate(pages.items()):
            print(f"[{i + 1}/{len(pages)}] Scraping: {name}")
            print(f"  URL: {url}")

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    await page.goto(url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(PAGE_LOAD_WAIT_MS)

                    data = await extract_page_data(page)
                    data["name"] = name

                    all_data["pages"][name] = data

                    table_count = len(data.get("tables", []))
                    list_count = len(data.get("lists", []))
                    item_count = len(data.get("labeled_items", []))
                    print(f"  Found: {table_count} tables, {list_count} lists, {item_count} labeled items")
                    break

                except Exception as e:
                    if attempt < MAX_RETRIES:
                        print(f"  Attempt {attempt} failed: {e}")
                        print(f"  Retrying in {RETRY_DELAY_MS}ms...")
                        await page.wait_for_timeout(RETRY_DELAY_MS)
                    else:
                        print(f"  ERROR after {MAX_RETRIES} attempts: {e}")
                        all_data["pages"][name] = {
                            "name": name,
                            "url": url,
                            "error": str(e),
                        }

        await page.close()

    # Save combined data
    combined_path = os.path.join(abs_output_dir, "metatft_all_tables.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved combined data to {combined_path}")

    # Save individual page data
    for name, data in all_data["pages"].items():
        slug = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)
        slug = slug.strip("_")
        file_path = os.path.join(abs_output_dir, f"{slug}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_data['pages'])} individual files to {abs_output_dir}/")

    # Print summary
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    total_tables = sum(
        len(d.get("tables", [])) for d in all_data["pages"].values()
    )
    total_lists = sum(
        len(d.get("lists", [])) for d in all_data["pages"].values()
    )
    total_items = sum(
        len(d.get("labeled_items", [])) for d in all_data["pages"].values()
    )
    errors = sum(
        1 for d in all_data["pages"].values() if "error" in d
    )
    print(f"Pages scraped: {len(all_data['pages'])}")
    print(f"Total tables:  {total_tables}")
    print(f"Total lists:   {total_lists}")
    print(f"Total items:   {total_items}")
    print(f"Errors:        {errors}")
    print(f"Output dir:    {abs_output_dir}")
    print("=" * 60)

    return all_data


def main():
    """CLI entry point."""
    cdp_endpoint = os.environ.get("CDP_ENDPOINT", DEFAULT_CDP_ENDPOINT)

    if len(sys.argv) > 1:
        cdp_endpoint = sys.argv[1]

    print(f"MetaTFT Tables Scraper")
    print(f"CDP Endpoint: {cdp_endpoint}")
    print(f"Pages to scrape: {len(TABLE_PAGES)}")
    print()

    asyncio.run(scrape_all_tables(cdp_endpoint=cdp_endpoint))


if __name__ == "__main__":
    main()
