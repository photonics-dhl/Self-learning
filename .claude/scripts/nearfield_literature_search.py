#!/usr/bin/env python3
"""Phase 2: Precise search for near-field optics landmark papers via OpenAlex API."""

import json
import urllib.request
import urllib.parse
import time
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def search_openalex(query, per_page=3, filter_journal=None):
    """Search OpenAlex for papers with optional journal filter."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={encoded}&per_page={per_page}&sort=cited_by_count:desc&select=title,authorships,publication_year,primary_location,doi,cited_by_count"
    if filter_journal:
        url += f"&filter=primary_location.source.display_name.search:{urllib.parse.quote(filter_journal)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def verify_doi(doi):
    """Verify a specific DOI exists in OpenAlex."""
    url = f"https://api.openalex.org/works/doi:{doi}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data
    except Exception as e:
        return None

def extract(result):
    """Extract clean info from OpenAlex result."""
    if not result or "error" in result:
        return None
    authors_list = []
    for a in result.get("authorships", [])[:5]:
        name = a.get("author", {}).get("display_name", "?")
        authors_list.append(name)
    authors_str = ", ".join(authors_list)
    if len(result.get("authorships", [])) > 5:
        authors_str += " et al."
    loc = result.get("primary_location") or {}
    source = loc.get("source") or {}
    journal = source.get("display_name", "N/A")
    doi = result.get("doi", "N/A")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    return {
        "title": result.get("title", "N/A"),
        "authors": authors_str,
        "year": result.get("publication_year", "N/A"),
        "journal": journal,
        "doi": doi,
        "citations": result.get("cited_by_count", "N/A"),
    }

def search_and_pick(query, per_page=5, min_citations=100):
    """Search and return top result."""
    data = search_openalex(query, per_page)
    if "results" not in data:
        return None
    for r in data["results"]:
        info = extract(r)
        if info and isinstance(info["citations"], int) and info["citations"] >= min_citations:
            return info
    # Return top result even if below threshold
    if data["results"]:
        info = extract(data["results"][0])
        return info
    return None

# Define the target papers with precise search queries
TARGETS = [
    # ---- s-SNOM / SNOM ----
    {
        "topic": "s-SNOM",
        "queries": [
            "Keilmann Hillenbrand near-field microscopy thermal radiation Reviews Modern Physics",
            "Hillenbrand Keilmann near-field scattering scanning optical microscopy",
        ],
        "dois_to_try": [
            "10.1103/RevModPhys.82.1803",
        ],
    },
    {
        "topic": "s-SNOM elastic scattering tip",
        "queries": [
            "Keilmann near-field microscopy elastic light scattering tip Phil Trans",
        ],
        "dois_to_try": [
            "10.1098/rsta.2004.1333",
        ],
    },
    {
        "topic": "SNOM aperture probes fundamentals",
        "queries": [
            "Hecht scanning near-field optical microscopy aperture probes fundamentals applications Journal Chemical Physics",
        ],
        "dois_to_try": [
            "10.1063/1.481382",
        ],
    },
    {
        "topic": "Near-field nanoscopy s-SNOM review",
        "queries": [
            "near-field nanoscopy s-SNOM scattering review Nature Materials OR Nature Photonics OR Science",
        ],
        "dois_to_try": [],
    },
    # ---- Optical antennas ----
    {
        "topic": "Optical antennas review",
        "queries": [
            "Bharadwaj Novotny optical antennas Reviews Modern Physics",
            "Bharadwaj Novotny Bouhelier optical antennas",
        ],
        "dois_to_try": [
            "10.1103/RevModPhys.79.235",
        ],
    },
    {
        "topic": "Novotny optical antennas review",
        "queries": [
            "Novotny van Hulst optical antennas review Nature Photonics",
        ],
        "dois_to_try": [],
    },
    # ---- Plasmonics ----
    {
        "topic": "Plasmonics fundamentals Nature",
        "queries": [
            "Barnes Dereux Ebbesen surface plasmon subwavelength optics Nature",
        ],
        "dois_to_try": [
            "10.1038/nature01937",
        ],
    },
    {
        "topic": "Plasmonics Nature Materials review",
        "queries": [
            "Brongersma Shalaev plasmonics nanophotonics review Nature Materials OR Nature Photonics",
        ],
        "dois_to_try": [],
    },
    {
        "topic": "Schuller plasmonics review",
        "queries": [
            "Schuller plasmonics review Nature Materials",
        ],
        "dois_to_try": [],
    },
    {
        "topic": "Maier plasmonics review",
        "queries": [
            "Maier Atwater plasmonics review Nature Materials OR MRS Bulletin",
        ],
        "dois_to_try": [],
    },
    # ---- Extraordinary transmission ----
    {
        "topic": "Ebbesen extraordinary transmission",
        "queries": [
            "Ebbesen extraordinary optical transmission sub-wavelength hole arrays Nature",
        ],
        "dois_to_try": [
            "10.1038/35570",
        ],
    },
    # ---- Near-field textbooks ----
    {
        "topic": "Novotny Hecht textbook",
        "queries": [
            "Novotny Hecht Principles Nano-Optics Cambridge University Press",
        ],
        "dois_to_try": [
            "10.1017/9781316424970",
            "10.1017/CBO9780511813535",
        ],
    },
    {
        "topic": "Maier Plasmonics textbook",
        "queries": [
            "Maier Plasmonics Fundamentals Applications Springer",
        ],
        "dois_to_try": [
            "10.1007/0-387-37825-1",
            "10.1007/978-0-387-37825-7",
        ],
    },
    # ---- Garcia de Abajo RMP ----
    {
        "topic": "Garcia de Abajo optical excitations",
        "queries": [
            "Garcia de Abajo optical excitations electron microscopy Reviews Modern Physics",
        ],
        "dois_to_try": [
            "10.1103/RevModPhys.82.209",
        ],
    },
    # ---- Betzig seminal ----
    {
        "topic": "Betzig near-field seminal",
        "queries": [
            "Betzig Trautman near-field scanning optical microscopy Science",
        ],
        "dois_to_try": [],
    },
    # ---- Ocelic Huber Hillenbrand s-SNOM ----
    {
        "topic": "Ocelic Huber s-SNOM",
        "queries": [
            "Ocelic Huber Hillenbrand s-SNOM pseudoheterodyne interferometry",
        ],
        "dois_to_try": [],
    },
]

def main():
    verified = []

    print("=" * 90)
    print("PHASE 2: PRECISE NEAR-FIELD OPTICS LITERATURE SEARCH")
    print("=" * 90)

    for target in TARGETS:
        topic = target["topic"]
        print(f"\n--- Searching: {topic} ---")

        found = None

        # Try DOIs first
        for doi in target["dois_to_try"]:
            print(f"  Trying DOI: {doi}...", end=" ")
            data = verify_doi(doi)
            if data and "error" not in data:
                info = extract(data)
                if info:
                    # Verify title contains relevant keywords
                    title_lower = info["title"].lower()
                    keywords = ["near-field", "nearfield", "nano-optics", "plasmon", "antenna",
                               "optical antenna", "s-sn", "snom", "som", "subwavelength",
                               "extraordinary", "plasmonic", "scattering", "light scattering"]
                    is_relevant = any(kw in title_lower for kw in keywords)
                    if is_relevant:
                        info["topic"] = topic
                        info["verified"] = "DOI-VERIFIED"
                        verified.append(info)
                        found = info
                        print(f"OK -> {info['title'][:60]}")
                        break
                    else:
                        print(f"WRONG PAPER -> {info['title'][:50]}")
            else:
                print("NOT FOUND")
            time.sleep(1)

        if not found:
            # Try keyword searches
            for query in target["queries"]:
                print(f"  Searching: {query[:60]}...")
                info = search_and_pick(query, per_page=5, min_citations=50)
                if info:
                    info["topic"] = topic
                    info["verified"] = "SEARCH-FOUND"
                    verified.append(info)
                    found = info
                    print(f"  -> {info['title'][:60]}")
                    print(f"     {info['authors'][:60]} ({info['year']}) {info['journal']}")
                    print(f"     DOI: {info['doi']}, Citations: {info['citations']}")
                    break
                time.sleep(1.5)

            if not found:
                print(f"  !! NOT FOUND for {topic}")

    # Deduplicate by DOI
    seen_dois = set()
    final = []
    for r in verified:
        doi = r.get("doi", "")
        if doi not in seen_dois:
            seen_dois.add(doi)
            final.append(r)

    # Sort by citations descending
    final.sort(key=lambda x: x.get("citations", 0) if isinstance(x.get("citations"), int) else 0, reverse=True)

    print("\n" + "=" * 90)
    print("FINAL VERIFIED RESULTS")
    print("=" * 90)

    for i, r in enumerate(final, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    Authors: {r['authors']}")
        print(f"    Year: {r['year']} | Journal: {r['journal']}")
        print(f"    DOI: {r['doi']}")
        print(f"    Citations: {r['citations']}")
        print(f"    Topic: {r['topic']} | Status: {r['verified']}")

    # Save JSON
    out_path = "Z:\\321\\DHL\\Self_Learning\\.claude\\scripts\\nearfield_verified.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(final)} papers to nearfield_verified.json")

if __name__ == "__main__":
    main()
