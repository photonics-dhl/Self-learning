#!/usr/bin/env python3
"""Phase 3: Author-based precise search for near-field optics papers via OpenAlex API."""

import json
import urllib.request
import urllib.parse
import time
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def fetch_works(filter_params, sort="cited_by_count:desc", per_page=5):
    """Fetch works from OpenAlex with specific filters."""
    base = "https://api.openalex.org/works?"
    params = []
    for k, v in filter_params.items():
        params.append(f"filter={k}:{urllib.parse.quote(v)}")
    params.append(f"sort={sort}")
    params.append(f"per_page={per_page}")
    params.append("select=title,authorships,publication_year,primary_location,doi,cited_by_count")
    url = base + "&".join(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "url": url}

def search_title(title_query, per_page=3):
    """Search by title."""
    return fetch_works({"title.search": title_query}, per_page=per_page)

def search_author_title(author, title_query, per_page=5):
    """Search by author + title keywords."""
    base = "https://api.openalex.org/works?"
    filter_str = f"author.display_name.search:{urllib.parse.quote(author)},title.search:{urllib.parse.quote(title_query)}"
    url = f"{base}filter={filter_str}&sort=cited_by_count:desc&per_page={per_page}&select=title,authorships,publication_year,primary_location,doi,cited_by_count"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def search_author(author, per_page=10, year_range=None):
    """Get top papers by author."""
    filter_parts = [f"author.display_name.search:{urllib.parse.quote(author)}"]
    if year_range:
        filter_parts.append(f"publication_year:{year_range}")
    filter_str = ",".join(filter_parts)
    url = f"https://api.openalex.org/works?filter={filter_str}&sort=cited_by_count:desc&per_page={per_page}&select=title,authorships,publication_year,primary_location,doi,cited_by_count"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def extract(result):
    """Extract clean info."""
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

def main():
    results = []

    # Define specific searches: (search_type, params)
    searches = [
        # ---- 1. Keilmann & Hillenbrand s-SNOM ----
        ("author+title", "Keilmann", "near-field microscopy scattering"),
        ("author+title", "Hillenbrand", "near-field nanoscopy"),
        ("author+title", "Hillenbrand", "near-field scattering infrared"),
        ("title", "near-field microscopy thermal radiation"),
        # ---- 2. Bharadwaj & Novotny optical antennas ----
        ("author+title", "Bharadwaj", "optical antennas"),
        ("author", "Bharadwaj Novotny"),
        # ---- 3. Novotny & van Hulst ----
        ("author+title", "Novotny", "optical antennas"),
        ("author+title", "van Hulst", "optical antennas"),
        # ---- 4. Barnes plasmonics ----
        # Already verified: 10.1038/nature01937
        # ---- 5. Maier Atwater plasmonics ----
        ("author+title", "Maier Atwater", "plasmonics"),
        # ---- 6. Brongersma ----
        ("author+title", "Brongersma", "plasmonics nanophotonics"),
        ("author+title", "Brongersma", "plasmonics review"),
        # ---- 7. Schuller plasmonics ----
        ("author+title", "Schuller", "plasmonics"),
        # ---- 8. Novotny & Hecht textbook ----
        ("title", "Principles of Nano-Optics"),
        # ---- 9. Garcia de Abajo ----
        # Already verified: 10.1103/RevModPhys.82.209
        # ---- 10. Ebbesen extraordinary transmission ----
        # Already verified: 10.1038/35570
        # ---- 11. Garcia-Vidal subwavelength apertures ----
        ("author+title", "Garcia-Vidal", "subwavelength apertures"),
        # ---- 12. Betzig Trautman ----
        ("author+title", "Betzig", "near-field optical microscopy"),
        # ---- 13. Ocelic Huber s-SNOM ----
        ("author+title", "Ocelic", "near-field interferometry"),
        ("author+title", "Huber", "s-SNOM pseudoheterodyne"),
        # ---- 14. Maier plasmonics JAP ----
        ("author+title", "Maier", "plasmonics localization guiding"),
        # ---- 15. NSOM/SNOM reviews ----
        ("title", "scanning near-field optical microscopy review"),
        # ---- 16. Pohl ----
        ("author+title", "Pohl", "near-field optical microscopy"),
        # ---- 17. Novotny & Hecht 2nd edition ----
        ("title", "Principles of Nano-Optics 2nd edition"),
        # ---- 18. Zayats Richards nano-optics ----
        ("author+title", "Zayats", "nano-optics near-field"),
        # ---- 19. Kawata near-field ----
        ("author+title", "Kawata", "near-field optics review"),
        # ---- 20. Dunn near-field ----
        ("author+title", "Dunn", "near-field scanning optical microscopy review"),
    ]

    seen_dois = set()
    all_found = []

    for search_spec in searches:
        search_type = search_spec[0]
        if search_type == "author+title":
            _, author, title_q = search_spec
            print(f"\nSearching: author={author}, title={title_q}")
            data = search_author_title(author, title_q, per_page=3)
        elif search_type == "title":
            _, title_q = search_spec
            print(f"\nSearching title: {title_q}")
            data = search_title(title_q, per_page=3)
        elif search_type == "author":
            _, author = search_spec
            print(f"\nSearching author: {author}")
            data = search_author(author, per_page=5)

        if "results" not in data:
            print(f"  Error: {data.get('error', 'unknown')}")
            time.sleep(1.5)
            continue

        for r in data["results"]:
            info = extract(r)
            if not info:
                continue
            doi = info.get("doi", "")
            if doi in seen_dois:
                continue
            # Check relevance by title keywords
            title_lower = info["title"].lower()
            relevant_kws = ["near-field", "nearfield", "nano-optics", "plasmon", "antenna",
                           "s-sn", "snom", "subwavelength", "extraordinary", "plasmonic",
                           "scattering", "principles", "fundamentals", "aperture"]
            is_relevant = any(kw in title_lower for kw in relevant_kws)
            if is_relevant and isinstance(info["citations"], int) and info["citations"] >= 20:
                seen_dois.add(doi)
                all_found.append(info)
                print(f"  -> [{info['citations']} cites] {info['title'][:70]}")
                print(f"     {info['authors'][:60]} ({info['year']}) {info['journal']}")
                print(f"     DOI: {info['doi']}")

        time.sleep(1.5)

    # Also add the already-verified papers from Phase 1
    pre_verified = [
        {"title": "Surface plasmon subwavelength optics",
         "authors": "William L. Barnes, Alain Dereux, Thomas W. Ebbesen",
         "year": 2003, "journal": "Nature", "doi": "10.1038/nature01937", "citations": 11521},
        {"title": "Extraordinary optical transmission through sub-wavelength hole arrays",
         "authors": "Thomas W. Ebbesen, Henri J. Lezec, H. F. Ghaemi, Tineke Thio, P. A. Wolff",
         "year": 1998, "journal": "Nature", "doi": "10.1038/35570", "citations": 7631},
        {"title": "Plasmonics: Fundamentals and Applications",
         "authors": "Stefan A. Maier",
         "year": 2007, "journal": "Springer", "doi": "10.1007/0-387-37825-1", "citations": 9566},
        {"title": "Optical excitations in electron microscopy",
         "authors": "F. Javier Garcia de Abajo",
         "year": 2010, "journal": "Reviews of Modern Physics", "doi": "10.1103/RevModPhys.82.209", "citations": 1450},
    ]
    for pv in pre_verified:
        if pv["doi"] not in seen_dois:
            seen_dois.add(pv["doi"])
            all_found.append(pv)

    # Sort by citations
    all_found.sort(key=lambda x: x.get("citations", 0) if isinstance(x.get("citations"), int) else 0, reverse=True)

    print("\n" + "=" * 90)
    print("ALL FOUND PAPERS (sorted by citations)")
    print("=" * 90)

    for i, r in enumerate(all_found, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    Authors: {r['authors']}")
        print(f"    Year: {r['year']} | Journal: {r['journal']}")
        print(f"    DOI: {r['doi']}")
        print(f"    Citations: {r['citations']}")

    # Save
    out_path = "Z:\\321\\DHL\\Self_Learning\\.claude\\scripts\\nearfield_all_found.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_found, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_found)} papers to nearfield_all_found.json")

if __name__ == "__main__":
    main()
