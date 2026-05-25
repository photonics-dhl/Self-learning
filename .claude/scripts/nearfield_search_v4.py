#!/usr/bin/env python3
"""Phase 4: Fix OpenAlex API calls and search for remaining key papers."""

import json
import urllib.request
import urllib.parse
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def openalex_search(params_dict, per_page=5):
    """Generic OpenAlex works search."""
    filters = []
    for k, v in params_dict.items():
        filters.append(f"{k}:{urllib.parse.quote(v, safe='')}")
    filter_str = ",".join(filters)
    url = f"https://api.openalex.org/works?filter={filter_str}&sort=cited_by_count:desc&per_page={per_page}&select=title,authorships,publication_year,primary_location,doi,cited_by_count"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "url": url}

def openalex_doi(doi):
    """Verify DOI."""
    url = f"https://api.openalex.org/works/doi:{doi}?select=title,authorships,publication_year,primary_location,doi,cited_by_count"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None

def extract(result):
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

def try_doi_and_search(doi_list, title_search, description):
    """Try DOIs first, then title search."""
    print(f"\n--- {description} ---")

    # Try DOIs
    for doi in doi_list:
        print(f"  Trying DOI: {doi}...", end=" ")
        data = openalex_doi(doi)
        if data:
            info = extract(data)
            if info:
                title_lower = info["title"].lower()
                kws = ["near-field", "nearfield", "nano-optics", "plasmon", "antenna",
                       "s-sn", "snom", "subwavelength", "extraordinary", "plasmonic",
                       "scattering", "principles", "fundamentals", "aperture", "nanoscopy",
                       "optical antenna", "localization", "phonon", "thermal"]
                is_relevant = any(kw in title_lower for kw in kws)
                if is_relevant:
                    print(f"OK -> {info['title'][:60]}")
                    info["verified"] = "DOI-VERIFIED"
                    return info
                else:
                    print(f"WRONG -> {info['title'][:50]}")
            else:
                print("PARSE ERROR")
        else:
            print("NOT FOUND")
        time.sleep(1)

    # Title search fallback
    print(f"  Title search: {title_search}")
    data = openalex_search({"title.search": title_search}, per_page=5)
    if "results" in data:
        for r in data["results"]:
            info = extract(r)
            if info and isinstance(info.get("citations"), int) and info["citations"] >= 50:
                print(f"  -> [{info['citations']} cites] {info['title'][:70]}")
                print(f"     {info['authors'][:60]} ({info['year']}) {info['journal']}")
                print(f"     DOI: {info['doi']}")
                info["verified"] = "TITLE-SEARCH"
                return info

    print(f"  NOT FOUND")
    return None

def main():
    found = []
    seen_dois = set()

    # Specific DOI lists for each target paper
    targets = [
        {
            "description": "Keilmann Hillenbrand s-SNOM Phil Trans R Soc 2004",
            "dois": [
                "10.1098/rsta.2004.1333",
                "10.1098/rsta.2003.1333",
            ],
            "title_search": "near-field microscopy by elastic light scattering from a tip",
        },
        {
            "description": "Keilmann Hillenbrand s-SNOM Nature 2000",
            "dois": [
                "10.1038/35021010",
                "10.1038/35021021",
            ],
            "title_search": "Hillenbrand Keilmann localized surface plasmon near-field microscopy",
        },
        {
            "description": "Bharadwaj Novotny optical antennas RMP 2007 (correct DOI)",
            "dois": [
                "10.1103/RevModPhys.79.1197",
                "10.1103/RevModPhys.79.1199",
            ],
            "title_search": "optical antennas Bharadwaj Novotny",
        },
        {
            "description": "Novotny van Hulst optical antennas review",
            "dois": [
                "10.1038/nphoton.2011.40",
                "10.1038/nphoton.2011.139",
            ],
            "title_search": "antennas for light Novotny van Hulst",
        },
        {
            "description": "Maier Atwater plasmonics review JAP 2005",
            "dois": [
                "10.1063/1.1951057",
            ],
            "title_search": "plasmonics localization guiding electromagnetic energy metal dielectric Maier",
        },
        {
            "description": "Brongersma plasmonics review",
            "dois": [
                "10.1038/nmat1502",
                "10.1038/nmat1200",
            ],
            "title_search": "plasmonics nanophotonics Brongersma review Nature Materials",
        },
        {
            "description": "Schuller plasmonics review Nature Materials 2010",
            "dois": [
                "10.1038/nmat2810",
                "10.1038/nmat2753",
            ],
            "title_search": "plasmonics Schuller Nature Materials review",
        },
        {
            "description": "Garcia-Vidal subwavelength apertures RMP 2010",
            "dois": [
                "10.1103/RevModPhys.82.729",
            ],
            "title_search": "light passing through subwavelength apertures",
        },
        {
            "description": "Betzig Trautman near-field Science 1992",
            "dois": [
                "10.1126/science.1996.5312.189",
                "10.1126/science.257.5067.189",
            ],
            "title_search": "near-field scanning optical microscopy Betzig Trautman",
        },
        {
            "description": "Ocelic Huber Hillenbrand s-SNOM pseudoheterodyne",
            "dois": [
                "10.1063/1.2400364",
                "10.1063/1.2164970",
            ],
            "title_search": "pseudoheterodyne interferometry s-SNOM near-field",
        },
        {
            "description": "Pohl SNOM original",
            "dois": [
                "10.1007/978-3-642-82661-7_1",
            ],
            "title_search": "scanning near-field optical microscopy Pohl",
        },
        {
            "description": "Kawata near-field optics review",
            "dois": [
                "10.1002/(SICI)1521-3951(199905)213:1<25::AID-JPSB25>3.0.CO;2-1",
            ],
            "title_search": "near-field optics review Kawata",
        },
        {
            "description": "Zayats Richards nano-optics textbook",
            "dois": [],
            "title_search": "Nano-optics near-field John Wiley",
        },
        {
            "description": "Maier Brongersma Kik plasmonics MRS Bulletin 2005",
            "dois": [
                "10.1557/mrs2005.79",
                "10.1557/mrs2005.80",
            ],
            "title_search": "plasmonics MRS Bulletin Maier Brongersma Kik",
        },
        {
            "description": "Amelinckx SNOM review",
            "dois": [],
            "title_search": "near-field scanning optical microscopy review fundamentals",
        },
        {
            "description": "Dunn near-field review",
            "dois": [],
            "title_search": "near-field scanning optical microscopy chemical imaging review",
        },
    ]

    for target in targets:
        result = try_doi_and_search(
            target["dois"],
            target["title_search"],
            target["description"]
        )
        if result:
            doi = result.get("doi", "")
            if doi not in seen_dois:
                seen_dois.add(doi)
                found.append(result)
        time.sleep(2)

    # Add pre-verified papers
    pre_verified = [
        {"title": "Surface plasmon subwavelength optics",
         "authors": "William L. Barnes, Alain Dereux, Thomas W. Ebbesen",
         "year": 2003, "journal": "Nature", "doi": "10.1038/nature01937", "citations": 11521, "verified": "DOI-VERIFIED"},
        {"title": "Extraordinary optical transmission through sub-wavelength hole arrays",
         "authors": "Thomas W. Ebbesen, Henri J. Lezec, H. F. Ghaemi, Tineke Thio, P. A. Wolff",
         "year": 1998, "journal": "Nature", "doi": "10.1038/35570", "citations": 7631, "verified": "DOI-VERIFIED"},
        {"title": "Plasmonics: Fundamentals and Applications",
         "authors": "Stefan A. Maier",
         "year": 2007, "journal": "Springer", "doi": "10.1007/0-387-37825-1", "citations": 9566, "verified": "DOI-VERIFIED"},
        {"title": "Optical excitations in electron microscopy",
         "authors": "F. Javier Garcia de Abajo",
         "year": 2010, "journal": "Reviews of Modern Physics", "doi": "10.1103/RevModPhys.82.209", "citations": 1450, "verified": "DOI-VERIFIED"},
        {"title": "Principles of Nano-Optics",
         "authors": "Lukas Novotny, Bert Hecht",
         "year": 2006, "journal": "Cambridge University Press", "doi": "10.1017/9781108781503", "citations": 1338, "verified": "DOI-VERIFIED"},
        {"title": "Scanning near-field optical microscopy with aperture probes: Fundamentals and applications",
         "authors": "Bert Hecht, Beate Sick, Urs P. Wild, Volker Deckert, Renato Zenobi, Olivier J. F. Martin, Dieter W. Pohl",
         "year": 2000, "journal": "Journal of Chemical Physics", "doi": "10.1063/1.481382", "citations": 748, "verified": "DOI-VERIFIED"},
    ]
    for pv in pre_verified:
        if pv["doi"] not in seen_dois:
            seen_dois.add(pv["doi"])
            found.append(pv)

    # Sort by citations
    found.sort(key=lambda x: x.get("citations", 0) if isinstance(x.get("citations"), int) else 0, reverse=True)

    print("\n" + "=" * 90)
    print("ALL FOUND PAPERS")
    print("=" * 90)

    for i, r in enumerate(found, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    Authors: {r['authors']}")
        print(f"    Year: {r['year']} | Journal: {r['journal']}")
        print(f"    DOI: {r['doi']}")
        print(f"    Citations: {r['citations']}")
        print(f"    Verified: {r.get('verified', 'N/A')}")

    out_path = "Z:\\321\\DHL\\Self_Learning\\.claude\\scripts\\nearfield_final.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(found)} papers")

if __name__ == "__main__":
    main()
