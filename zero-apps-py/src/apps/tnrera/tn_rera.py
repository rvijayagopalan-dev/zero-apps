def scrape_project_rows(url):
    """Return list of dicts: {'project':..., 'builder':..., 'price':..., 'address':...}"""
    print(f"Scraping {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        return []

    # pick the largest table
    table = max(tables, key=lambda t: len(t.find_all(["tr","td","th"])))
    rows = table.find_all("tr")
    results = []

    for r in rows[1:]:  # skip header
        cols = [td.get_text(separator=" ", strip=True) for td in r.find_all(["td","th"])]

        if not cols:
            continue

        # Heuristic mapping:
        # [0] = Serial No, [1] = Project Name, [2] = Builder, [3] = Price, [4] = Address
        project = cols[1] if len(cols) > 1 else ""
        builder = cols[2] if len(cols) > 2 else ""
        price = cols[3] if len(cols) > 3 else "N/A"
        address = cols[4] if len(cols) > 4 else cols[-1] if cols else ""

        results.append({
            "source_url": url,
            "raw_cols": cols,
            "project": project,
            "builder": builder,
            "price": price,
            "address": address,
            "full_text": " | ".join(cols)
        })
    return results
