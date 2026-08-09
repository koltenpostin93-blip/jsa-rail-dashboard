"""
USDA Rail Dashboard Updater
----------------------------
Fetches live data from the USDA AMS API and rebuilds the dashboard HTML.

Usage: double-click "Update Dashboard.bat" or run directly with Python.
"""

import pandas as pd
import json
import re
import sys
import os
import shutil
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
HTML_FILE  = r'C:\Users\KoltenPostin\John Stewart and Associates\JSA - Documents\Research Analyst\Rail Shipment Project\USDA_Rail_Dashboard.html'
SHEET_NAME = 'Data'
USDA_APP_TOKEN = None   # Optional — paste free token from agtransport.usda.gov
# ──────────────────────────────────────────────────────────────────────────────

VALID_STATES = [
    'AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY',
    'LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM',
    'NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA',
    'WI','WV','WY'
]

MONTHS = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]

def log(msg):
    print(f"  {msg}")

def fmt_num(n):
    return f"{n:,}"

# ── Step 1: Load data from USDA API ──────────────────────────────────────────
print("\nUSDA Rail Dashboard Updater")
print("=" * 40)

if not os.path.exists(HTML_FILE):
    print(f"\nERROR: Dashboard HTML not found at:\n   {HTML_FILE}")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Load data from API
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import usda_api
    log("Fetching data from USDA AMS API...")
    df_api = usda_api.load_usda_data(app_token=USDA_APP_TOKEN)
    # Keep only rows with valid 2-letter state codes (excludes KCS national total)
    df_clean = df_api[df_api['State'].isin(VALID_STATES)].copy()
    data_source = "USDA API"
    log(f"API fetch successful.")
except Exception as e:
    print(f"\nERROR: Failed to fetch data from USDA API:\n   {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

df_clean['MY Week'] = pd.to_numeric(df_clean['MY Week'], errors='coerce')

total_rows   = len(df_clean)
railroads    = sorted(df_clean['Railroad'].dropna().unique().tolist())
market_years = sorted(df_clean['Market Year'].dropna().unique().tolist())

log(f"Source:       {data_source}")
log(f"Rows:         {fmt_num(total_rows)}")
log(f"Railroads:    {', '.join(railroads)}")
log(f"Market years: {market_years[0]} to {market_years[-1]}")
print()

# ── Step 2: Aggregate ──────────────────────────────────────────────────────────
log("Aggregating monthly data...")
monthly_rr = df_clean.groupby(['Calendar Month','Railroad'])['Est Bushels'].sum().reset_index()
monthly_data = {}
for month in MONTHS:
    monthly_data[month] = {}
    for rr in railroads:
        val = monthly_rr[(monthly_rr['Calendar Month']==month) & (monthly_rr['Railroad']==rr)]['Est Bushels'].sum()
        monthly_data[month][rr] = int(val)

log("Aggregating monthly data by year...")
monthly_by_year = {}
for year in market_years:
    df_yr = df_clean[df_clean['Market Year']==year]
    monthly_by_year[year] = {}
    for month in MONTHS:
        monthly_by_year[year][month] = {}
        for rr in railroads:
            val = df_yr[(df_yr['Calendar Month']==month) & (df_yr['Railroad']==rr)]['Est Bushels'].sum()
            monthly_by_year[year][month][rr] = int(val)

log("Aggregating state data...")
state_rr = df_clean.groupby(['State','Railroad'])['Est Bushels'].sum().reset_index()
state_data = {}
for state in VALID_STATES:
    state_data[state] = {}
    for rr in railroads:
        val = state_rr[(state_rr['State']==state) & (state_rr['Railroad']==rr)]['Est Bushels'].sum()
        state_data[state][rr] = int(val)

log("Aggregating state data by year...")
grp_yr = df_clean.groupby(['Market Year','State','Railroad'])['Est Bushels'].sum().reset_index()
state_data_by_year = {}
for year in market_years:
    state_data_by_year[year] = {}
    for state in VALID_STATES:
        state_data_by_year[year][state] = {}
        for rr in railroads:
            val = grp_yr[(grp_yr['Market Year']==year) & (grp_yr['State']==state) & (grp_yr['Railroad']==rr)]['Est Bushels'].sum()
            state_data_by_year[year][state][rr] = int(val)

log("Aggregating state data by month...")
grp_mo = df_clean.groupby(['Calendar Month','State','Railroad'])['Est Bushels'].sum().reset_index()
state_data_by_month = {}
for month in MONTHS:
    state_data_by_month[month] = {}
    for state in VALID_STATES:
        state_data_by_month[month][state] = {}
        for rr in railroads:
            val = grp_mo[(grp_mo['Calendar Month']==month) & (grp_mo['State']==state) & (grp_mo['Railroad']==rr)]['Est Bushels'].sum()
            state_data_by_month[month][state][rr] = int(val)

log("Aggregating state data by year + month...")
grp_ym = df_clean.groupby(['Market Year','Calendar Month','State','Railroad'])['Est Bushels'].sum().reset_index()
state_data_by_year_month = {}
for year in market_years:
    state_data_by_year_month[year] = {}
    for month in MONTHS:
        state_data_by_year_month[year][month] = {}
        for state in VALID_STATES:
            state_data_by_year_month[year][month][state] = {}
            for rr in railroads:
                val = grp_ym[
                    (grp_ym['Market Year']==year) &
                    (grp_ym['Calendar Month']==month) &
                    (grp_ym['State']==state) &
                    (grp_ym['Railroad']==rr)
                ]['Est Bushels'].sum()
                state_data_by_year_month[year][month][state][rr] = int(val)

log("Aggregating weekly data by marketing year...")
weekly_rr = df_clean.groupby(['Market Year','MY Week'])['Est Bushels'].sum().reset_index()
weekly_data = {}
for year in market_years:
    df_yr = weekly_rr[weekly_rr['Market Year']==year].sort_values('MY Week')
    weekly_data[year] = {int(row['MY Week']): int(row['Est Bushels']) for _, row in df_yr.iterrows()}

log("Aggregating weekly data by railroad...")
grp_rr_wk = df_clean.groupby(['Railroad','Market Year','MY Week'])['Est Bushels'].sum().reset_index()
weekly_data_by_rr = {}
for rr in railroads:
    weekly_data_by_rr[rr] = {}
    for year in market_years:
        rows = grp_rr_wk[(grp_rr_wk['Railroad']==rr) & (grp_rr_wk['Market Year']==year)].sort_values('MY Week')
        weekly_data_by_rr[rr][year] = {int(r['MY Week']): int(r['Est Bushels']) for _, r in rows.iterrows()}

log("Aggregating weekly data by state...")
grp_st_wk = df_clean.groupby(['State','Market Year','MY Week'])['Est Bushels'].sum().reset_index()
weekly_data_by_state = {}
for state in VALID_STATES:
    weekly_data_by_state[state] = {}
    for year in market_years:
        rows = grp_st_wk[(grp_st_wk['State']==state) & (grp_st_wk['Market Year']==year)].sort_values('MY Week')
        weekly_data_by_state[state][year] = {int(r['MY Week']): int(r['Est Bushels']) for _, r in rows.iterrows()}

log("Aggregating weekly data by railroad + state...")
grp_rs_wk = df_clean.groupby(['Railroad','State','Market Year','MY Week'])['Est Bushels'].sum().reset_index()
weekly_data_by_rr_state = {}
for rr in railroads:
    weekly_data_by_rr_state[rr] = {}
    for state in VALID_STATES:
        weekly_data_by_rr_state[rr][state] = {}
        for year in market_years:
            rows = grp_rs_wk[(grp_rs_wk['Railroad']==rr) & (grp_rs_wk['State']==state) & (grp_rs_wk['Market Year']==year)].sort_values('MY Week')
            weekly_data_by_rr_state[rr][state][year] = {int(r['MY Week']): int(r['Est Bushels']) for _, r in rows.iterrows()}

states_with_data = [s for s in VALID_STATES if any(state_data[s].get(rr, 0) > 0 for rr in railroads)]

# ── Progress Tab Data ──────────────────────────────────────────────────────────
log("Computing progress tab data (MYtD vs LY vs 6-yr Olympic Avg)...")

current_year  = market_years[-1]
last_year_p   = market_years[-2] if len(market_years) >= 2 else None
max_wk_p      = int(df_clean[df_clean['Market Year'] == current_year]['MY Week'].max())

# 6 most recent complete years before current for olympic pool
prior_yrs_p   = [y for y in market_years if y != current_year]
oly_pool_p    = prior_yrs_p[-6:] if len(prior_yrs_p) >= 6 else prior_yrs_p

def _oly_avg(vals):
    v = sorted([x for x in vals if x > 0])
    if len(v) >= 4: v = v[1:-1]   # drop highest and lowest
    return int(sum(v) / len(v)) if v else 0

def _pct(curr, base):
    if not base: return None
    return round((curr / base - 1) * 100, 1)

# Efficient: pre-slice the dataframes once
_c = df_clean[(df_clean['Market Year'] == current_year) & (df_clean['MY Week'] <= max_wk_p)]
_l = df_clean[(df_clean['Market Year'] == last_year_p)  & (df_clean['MY Week'] <= max_wk_p)] if last_year_p else df_clean.iloc[0:0]
_po = df_clean[df_clean['Market Year'].isin(oly_pool_p)  & (df_clean['MY Week'] <= max_wk_p)]

def _rr_metric(rr=None):
    def _s(d): return int((d[d['Railroad']==rr] if rr else d)['Est Bushels'].sum())
    curr = _s(_c); ly = _s(_l)
    pool = [_s(_po[_po['Market Year']==y]) for y in oly_pool_p]
    oly  = _oly_avg(pool)
    return {'current': curr, 'ly': ly, 'olympic_avg': oly,
            'pct_ly': _pct(curr, ly), 'pct_avg': _pct(curr, oly)}

def _state_metric(state, rr=None):
    def _s(d):
        d = d[d['State']==state]
        return int((d[d['Railroad']==rr] if rr else d)['Est Bushels'].sum())
    curr = _s(_c)
    if curr == 0: return None
    ly   = _s(_l)
    pool = [_s(_po[_po['Market Year']==y]) for y in oly_pool_p]
    oly  = _oly_avg(pool)
    return {'current': curr, 'ly': ly, 'olympic_avg': oly,
            'pct_ly': _pct(curr, ly), 'pct_avg': _pct(curr, oly)}

prog_rr = {'All': _rr_metric()}
for _rr in railroads:
    prog_rr[_rr] = _rr_metric(_rr)

prog_state = {}
for _rk in ['All'] + railroads:
    _ra = None if _rk == 'All' else _rk
    prog_state[_rk] = {}
    for _st in VALID_STATES:
        _m = _state_metric(_st, _ra)
        if _m: prog_state[_rk][_st] = _m

progress = {
    'current_year':  current_year,
    'last_year':     last_year_p,
    'max_week':      max_wk_p,
    'olympic_years': oly_pool_p,
    'rr_summary':    prog_rr,
    'state_summary': prog_state,
}

output = {
    'railroads':               railroads,
    'market_years':            market_years,
    'months':                  MONTHS,
    'monthly_data':            monthly_data,
    'monthly_by_year':         monthly_by_year,
    'state_data':              state_data,
    'state_data_by_year':      state_data_by_year,
    'state_data_by_month':     state_data_by_month,
    'state_data_by_year_month':state_data_by_year_month,
    'weekly_data':             weekly_data,
    'states_with_data':        states_with_data,
    'weekly_data_by_rr':       weekly_data_by_rr,
    'weekly_data_by_state':    weekly_data_by_state,
    'weekly_data_by_rr_state': weekly_data_by_rr_state,
    'progress':                progress,
}

# ── Step 3: Inject into HTML ───────────────────────────────────────────────────
log("Injecting data into dashboard HTML...")

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

new_data_js = f'const DATA = {json.dumps(output, separators=(",", ":"))};'

# Locate and replace the DATA block using string search (not regex),
# so it can never accidentally consume JavaScript code that follows.
data_start = html.find('const DATA = {')
data_end   = html.find('};', data_start) + 2  # +2 includes the '};'
count = 0
if data_start != -1 and data_end > data_start:
    updated_html = html[:data_start] + new_data_js + html[data_end:]
    count = 1
else:
    updated_html = html

if count == 0:
    # Diagnostic: show what the file actually has near "const DATA"
    idx = html.find('const DATA')
    if idx == -1:
        print("\n[ERROR] ERROR: 'const DATA' not found anywhere in the HTML file.")
        print("   The script may be pointing at the wrong file.")
    else:
        snippet = html[idx:idx+120].replace('\n','↵').replace('\r','')
        print("\n[ERROR] ERROR: Found 'const DATA' but pattern did not match.")
        print(f"   Found at char {idx}: {snippet!r}")
        print("   Expected format: const DATA = {{...}};")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Update the subtitle date range in the header
date_range = f"{market_years[0]} – {market_years[-1]}"
updated_html = re.sub(
    r'Data: \d{4}/\d{2} &ndash; \d{4}/\d{2}',
    f'Data: {date_range}',
    updated_html
)

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(updated_html)

# Also write a copy to the publish folder as index.html (for Netlify)
PUBLISH_DIR = os.path.join(os.path.dirname(HTML_FILE), 'publish')
os.makedirs(PUBLISH_DIR, exist_ok=True)
PUBLISH_FILE = os.path.join(PUBLISH_DIR, 'index.html')
with open(PUBLISH_FILE, 'w', encoding='utf-8') as f:
    f.write(updated_html)

# Copy logo into publish folder so Netlify can serve it
LOGO_SRC = os.path.join(os.path.dirname(HTML_FILE), 'logo.png')
LOGO_DST = os.path.join(PUBLISH_DIR, 'logo.png')
if os.path.exists(LOGO_SRC):
    shutil.copy2(LOGO_SRC, LOGO_DST)
    log("Logo copied to publish folder")

for favicon_file in ['favicon.ico', 'favicon-32.png', 'apple-touch-icon.png']:
    src = os.path.join(os.path.dirname(HTML_FILE), favicon_file)
    dst = os.path.join(PUBLISH_DIR, favicon_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        log(f"{favicon_file} copied to publish folder")

size_kb = os.path.getsize(HTML_FILE) / 1024
print()
print("[OK] Dashboard updated successfully!")
log(f"File size: {size_kb:.0f} KB")
log(f"Updated:   {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
log(f"Publish copy: {PUBLISH_FILE}")
print()
pass  # non-interactive safe
