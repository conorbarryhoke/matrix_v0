#!/usr/bin/env python3
"""
Scrape D&D 5e spells from dnd5e.wikidot.com and save to CSV.

Usage:
    python scripts/scrape_spells.py

Output:
    data/spells.csv
"""

import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path


BASE_URL = "https://dnd5e.wikidot.com"
SPELLS_INDEX_URL = f"{BASE_URL}/spells"
REQUEST_DELAY = 0.5  # seconds between requests


def get_spell_links():
    """Fetch the spells index page and extract all spell URLs."""
    print(f"Fetching spell index from {SPELLS_INDEX_URL}...")
    response = requests.get(SPELLS_INDEX_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links that match /spell:spell-name pattern
    spell_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('/spell:'):
            spell_name = link.get_text(strip=True)
            full_url = BASE_URL + href
            spell_links.append((spell_name, full_url))

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for name, url in spell_links:
        if url not in seen:
            seen.add(url)
            unique_links.append((name, url))

    print(f"Found {len(unique_links)} unique spells")
    return unique_links


def parse_level(level_text):
    """Parse spell level from text like '3rd-level evocation' or 'Evocation cantrip'."""
    level_text = level_text.lower()
    if 'cantrip' in level_text:
        return 0

    # Match patterns like "1st-level", "2nd-level", "3rd-level", "4th-level", etc.
    match = re.search(r'(\d+)(?:st|nd|rd|th)-level', level_text)
    if match:
        return int(match.group(1))

    return None


def parse_school(level_text):
    """Extract school from level text."""
    schools = ['abjuration', 'conjuration', 'divination', 'enchantment',
               'evocation', 'illusion', 'necromancy', 'transmutation']
    level_text = level_text.lower()
    for school in schools:
        if school in level_text:
            return school.capitalize()
    return None


def scrape_spell(url):
    """Scrape a single spell page and return structured data."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main content div
    content = soup.find('div', {'id': 'page-content'})
    if not content:
        return None

    spell_data = {}

    # Get spell name from page title
    title_elem = soup.find('div', class_='page-title')
    if title_elem:
        spell_data['spell_name'] = title_elem.get_text(strip=True)

    full_text = content.get_text('\n', strip=True)
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]

    # Extract source
    for line in lines:
        if line.startswith('Source:'):
            spell_data['source'] = line.replace('Source:', '').strip()
            break

    # Extract level and school from the level line (e.g., "3rd-level evocation")
    for line in lines:
        level = parse_level(line)
        if level is not None:
            spell_data['level'] = level
            spell_data['school'] = parse_school(line)
            break

    # Extract stats - values are on the line AFTER the label
    stat_labels = ['Casting Time:', 'Range:', 'Components:', 'Duration:']
    stat_keys = ['casting_time', 'range', 'components', 'duration']

    for i, line in enumerate(lines):
        for label, key in zip(stat_labels, stat_keys):
            if line == label and i + 1 < len(lines):
                spell_data[key] = lines[i + 1]

    # Find key indices
    duration_idx = None
    higher_levels_idx = None
    spell_lists_idx = None

    for i, line in enumerate(lines):
        if line == 'Duration:':
            duration_idx = i
        if line.startswith('At Higher Levels'):
            higher_levels_idx = i
        if line.startswith('Spell Lists'):
            spell_lists_idx = i

    # Extract description - starts 2 lines after Duration (skip the duration value)
    # ends at "At Higher Levels" or "Spell Lists"
    if duration_idx is not None:
        desc_start = duration_idx + 2  # Skip "Duration:" and its value
        desc_end = higher_levels_idx or spell_lists_idx or len(lines)
        desc_lines = lines[desc_start:desc_end]
        spell_data['description'] = ' '.join(desc_lines)

    # Extract "At Higher Levels" text
    if higher_levels_idx is not None:
        end_idx = spell_lists_idx or len(lines)
        higher_lines = lines[higher_levels_idx + 1:end_idx]
        spell_data['level_scaling'] = ' '.join(higher_lines)
    else:
        spell_data['level_scaling'] = ''

    # Extract spell lists - collect all lines after "Spell Lists." until end
    if spell_lists_idx is not None:
        spell_list_lines = lines[spell_lists_idx + 1:]
        # Join with comma, handling the case where commas are on separate lines
        spell_lists_text = ' '.join(spell_list_lines)
        # Clean up the formatting
        spell_lists_text = spell_lists_text.replace(' ,', ',').replace('  ', ' ')
        spell_data['spell_lists'] = spell_lists_text.strip()
    else:
        spell_data['spell_lists'] = ''

    return spell_data


def main():
    """Main function to scrape all spells and save to CSV."""
    # Get all spell URLs
    spell_links = get_spell_links()

    # Scrape each spell
    spells = []
    total = len(spell_links)

    for i, (name, url) in enumerate(spell_links):
        print(f"[{i+1}/{total}] Scraping {name}...")

        try:
            spell_data = scrape_spell(url)
            if spell_data:
                spells.append(spell_data)
            else:
                print(f"  Warning: Could not parse {name}")
        except Exception as e:
            print(f"  Error scraping {name}: {e}")

        # Rate limiting
        if i < total - 1:
            time.sleep(REQUEST_DELAY)

    print(f"\nSuccessfully scraped {len(spells)} spells")

    # Create DataFrame
    columns = ['spell_name', 'source', 'level', 'school', 'casting_time',
               'range', 'components', 'duration', 'description',
               'level_scaling', 'spell_lists']

    df = pd.DataFrame(spells)

    # Ensure all columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = ''

    # Reorder columns
    df = df[columns]

    # Save to CSV
    output_path = Path(__file__).parent.parent / 'data' / 'spells.csv'
    output_path.parent.mkdir(exist_ok=True)

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

    # Print summary
    print(f"\nSummary:")
    print(f"  Total spells: {len(df)}")
    print(f"  Cantrips: {len(df[df['level'] == 0])}")
    for level in range(1, 10):
        count = len(df[df['level'] == level])
        if count > 0:
            print(f"  Level {level}: {count}")


if __name__ == '__main__':
    main()
