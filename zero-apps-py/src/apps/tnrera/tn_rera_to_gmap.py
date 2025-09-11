#!/usr/bin/env python3
"""
tn_rera_to_gmap.py

Pipeline:
1. Scrape TNRERA registered projects pages (example: Building 2025/2024).
2. Parse Project name & address.
3. Geocode addresses (Google Geocoding API preferred, Nominatim fallback).
4. Generate tn_rera_map.html using gmplot (Google Maps JS).
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import sqlite3
import time
import os
import argparse

import dotenv
dotenv.load_dotenv()  # load .env if present

import logging
logging.basicConfig(level=logging.INFO) 

# --- Optional geocoders ---
# Google geocoder via googlemaps package (preferred if you have key)
try:
    import googlemaps
except Exception:
    googlemaps = None

# Nominatim fallback from geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# gmplot for producing Google Map HTML
import gmplot

# -----------------------
# Config / defaults
# -----------------------
TNRERA_BASE = "https://rera.tn.gov.in"
# Example project pages (building lists by year). We'll scrape multiple year pages.
TNRERA_PROJECT_PAGES = [
    "https://rera.tn.gov.in/cms/reg_projects_tamilnadu/Building/2025.php"
    #"https://rera.tn.gov.in/cms/reg_projects_tamilnadu/Building/2024.php"
    #"https://rera.tn.gov.in/cms/reg_projects_tamilnadu/Building/2023.php",
    # add more year pages if needed
]

DB_FILE = "geocache.db"

# -----------------------
# Utilities: caching DB
# -----------------------
def init_cache(db_file=DB_FILE):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS geocache (
            address TEXT PRIMARY KEY,
            lat REAL,
            lng REAL,
            provider TEXT,
            timestamp INTEGER
        )
    """)
    conn.commit()
    return conn

def cache_get(conn, address):
    cur = conn.cursor()
    cur.execute("SELECT lat, lng FROM geocache WHERE address = ?", (address,))
    r = cur.fetchone()
    return (r[0], r[1]) if r else None

def cache_set(conn, address, lat, lng, provider):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO geocache(address, lat, lng, provider, timestamp) VALUES (?, ?, ?, ?, ?)",
        (address, lat, lng, provider, int(time.time()))
    )
    conn.commit()

# -----------------------
# Scraper for TNRERA table pages
# (these pages generally list projects in HTML tables)
# -----------------------
def scrape_project_rows(url):
    """Return a list of dicts: {'project':..., 'address':..., 'extra': ...}"""
    print(f"Scraping {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # The TNRERA pages usually have project listings in <table> rows.
    # We'll attempt a generic approach: find the largest table and parse rows.
    tables = soup.find_all("table")
    if not tables:
        # fallback: some pages present entries in <div> or <p>
        text_blocks = soup.find_all(["p","div"])
        # naive fallback: return empty
        return []

    # pick the largest table by cell count
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

        logging.info("Cols:", cols)

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

# -----------------------
# Geocoding function with cache + provider choice
# -----------------------
def geocode_address(address, conn, google_api_key=None, sleep_between=1.0):
    # clean
    address = address.strip()
    if not address:
        return None
    cached = cache_get(conn, address)
    if cached:
        return cached

    # Try Google if key provided
    if google_api_key and googlemaps:
        try:
            gmaps = googlemaps.Client(key=google_api_key)
            geocode_result = gmaps.geocode(address + ", Tamil Nadu, India")  # bias to Tamil Nadu
            if geocode_result:
                loc = geocode_result[0]["geometry"]["location"]
                cache_set(conn, address, loc["lat"], loc["lng"], "google")
                time.sleep(sleep_between)
                return (loc["lat"], loc["lng"])
        except Exception as e:
            print("Google geocode failed:", e)

    # Fallback: Nominatim (OpenStreetMap) via geopy
    try:
        geolocator = Nominatim(user_agent="tn_rera_mapper/1.0")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)
        location = geocode(address + ", Tamil Nadu, India")
        if location:
            cache_set(conn, address, location.latitude, location.longitude, "nominatim")
            return (location.latitude, location.longitude)
    except Exception as e:
        print("Nominatim failed:", e)

    return None

# -----------------------
# Map rendering (gmplot)
# -----------------------
def create_gmap_html(df, output_html="tn_rera_map.html", google_api_key=None):
    # center map on mean lat/lng
    mean_lat = df["lat"].mean()
    mean_lng = df["lng"].mean()
    # gmplot takes API key in the HTML script include for Google Maps JS
    gmap = gmplot.GoogleMapPlotter(mean_lat, mean_lng, 11, apikey=google_api_key)

    # Add markers
    for _, row in df.iterrows():
        lat, lng = row["lat"], row["lng"]
        hover_info = (
            f"<b>Builder:</b> {row['builder']}<br>"
            f"<b>Project:</b> {row['project']}<br>"
            f"<b>Price:</b> {row['price']}<br>"
            f"<b>Location:</b> {row['address']}"
        )
        gmap.marker(lat, lng, title=row['project'])

    # Draw initial HTML
    gmap.draw(output_html)

    """
    # add markers
    for _, row in df.iterrows():
        lat, lng = row["lat"], row["lng"]
        info = f"{row['project']}<br/>{row['address']}<br/><small>Source: {row['source_url']}</small>"
        # gmplot has a marker function, and we can add info windows by adding a little JS at the end.
        gmap.marker(lat, lng, title=row['project'])
    # draw
    gmap.draw(output_html)
    """
    # Insert simple JS for clickable info windows (improves user experience).
    # gmplot's simple draw doesn't automatically add info windows; we'll append JS to the HTML.
    with open(output_html, "r", encoding="utf8") as f:
        html = f.read()
    # Build simple markers array JS
    markers_js = []
    for i, row in df.iterrows():
        markers_js.append(
            "{{lat:{lat}, lng:{lng}, title:{title!r}, info:{info!r}}}".format(
                lat=row["lat"], lng=row["lng"],
                title=row["project"], info=(row["project"] + "<br/>" + row["address"])
            )
        )
    markers_array = "[" + ",\n".join(markers_js) + "]"
    extra_js = f"""
<script>
function addInfoWindows(map){{
  var markers = {markers_array};
  var infowindow = new google.maps.InfoWindow();
  for (var i=0; i<markers.length; i++) {{
    (function(m) {{
      var marker = new google.maps.Marker({{
        position: {{lat: m.lat, lng: m.lng}},
        map: map,
        title: m.title
      }});
      google.maps.event.addListener(marker, 'click', (function(markerCopy, mCopy) {{
          return function() {{
              infowindow.setContent(mCopy.info);
              infowindow.open(map, markerCopy);
          }}
      }})(marker, m));
    }})(markers[i]);
  }}
}}
/* Wait for the Google map to load and then call addInfoWindows */
if (typeof google !== "undefined" && google.maps && google.maps.event) {{
  google.maps.event.addListenerOnce(window, 'load', function() {{
    // find the map object created by gmplot (it uses window.map_0)
    if (window.map_0) {{
      addInfoWindows(window.map_0);
    }}
  }});
}}
</script>
"""
    # append before </body>
    html = html.replace("</body>", extra_js + "\n</body>")
    with open(output_html, "w", encoding="utf8") as f:
        f.write(html)
    print(f"Map written to {output_html}")

# -----------------------
# Main pipeline
# -----------------------
def main(args):
    conn = init_cache(DB_FILE)
    all_rows = []
    for page in TNRERA_PROJECT_PAGES:
        try:
            rows = scrape_project_rows(page)
            all_rows.extend(rows)
        except Exception as e:
            print("Failed to scrape", page, e)

    # Create dataframe
    df = pd.DataFrame(all_rows)
    if df.empty:
        print("No projects scraped. Exiting.")
        return

    # Attempt to geocode each address
    lat_list = []
    lng_list = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Geocoding"):
        address = row.get("address") or row.get("project") or row.get("full_text", "")
        cached = cache_get(conn, address)
        if cached:
            lat, lng = cached
        else:
            latlng = geocode_address(address, conn, google_api_key=args.google_key)
            if latlng:
                lat, lng = latlng
            else:
                lat, lng = None, None
        lat_list.append(lat)
        lng_list.append(lng)
    df["lat"] = lat_list
    df["lng"] = lng_list

    # Filter out failed geocodes
    df_valid = df.dropna(subset=["lat", "lng"]).copy()
    if df_valid.empty:
        print("No geocoded points available.")
        return

    # Save CSV
    out_csv = args.out_csv or "tn_rera_projects_geocoded.csv"
    df_valid.to_csv(out_csv, index=False)
    print("Saved geocoded projects to", out_csv)

    # Create Google Map HTML
    create_gmap_html(df_valid, output_html=args.out_html or "tn_rera_map.html", google_api_key=args.google_key)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--google-key", default=os.getenv("GOOGLE_MAPS_API_KEY"), help="Google Maps Geocoding + JS API key")
    p.add_argument("--out-html", default="tn_rera_map.html")
    p.add_argument("--out-csv", default="tn_rera_projects_geocoded.csv")
    args = p.parse_args()

    #logging.info("API_KEY %s",os.getenv('GOOGLE_MAPS_API_KEY'))

    main(args)