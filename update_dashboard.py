"""
USDA Rail Dashboard Updater
----------------------------
Run this script anytime you add new data to the Excel file.
It will re-aggregate everything and overwrite the dashboard HTML automatically.

Usage: double-click "Update Dashboard.bat" or run directly with Python.
"""

import pandas as pd
import json
import re
import sys
import os
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
EXCEL_FILE = r'C:\Users\KoltenPostin\John Stewart and Associates\JSA - Documents\Research Analyst\Rail Shipment Project\Rail Data USDA.xlsx'
HTML_FILE  = r'C:\Users\KoltenPostin\John Stewart and Associates\JSA - Documents\Research Analyst\Rail Shipment Project\USDA_Rail_Dashboard.html'
SHEET_NAME = 'Data'
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

# ── Step 1: Read & clean data ──────────────────────────────────────────────────
print("\n🌾 USDA Rail Dashboard Updater")
print("=" * 40)
log(f"Reading: {os.path.basename(EXCEL_FILE)}")

if not os.path.exists(EXCEL_FILE):
    print(f"\n❌ ERROR: Excel file not found at:\n   {EXCEL_FILE}")
    input("\nPress Enter to exit...")
    sys.exit(1)

if not os.path.exists(HTML_FILE):
    print(f"\n❌ ERROR: Dashboard HTML not found at:\n   {HTML_FILE}")
    input("\nPress Enter to exit...")
    sys.exit(1)

df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
df['Est Bushels'] = pd.to_numeric(df['Est Bushels'], errors='coerce').fillna(0)
df_clean = df[df['State'].isin(VALID_STATES)].copy()

total_rows   = len(df)
clean_rows   = len(df_clean)
railroads    = sorted(df_clean['Railroad'].dropna().unique().tolist())
market_years = sorted(df_clean['Market Year'].dropna().unique().tolist())

log(f"Rows read:      {fmt_num(total_rows)}")
log(f"Rows after clean: {fmt_num(clean_rows)}")
log(f"Railroads:      {', '.join(railroads)}")
log(f"Market years:   {market_years[0]} → {market_years[-1]}")
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
        print("\n❌ ERROR: 'const DATA' not found anywhere in the HTML file.")
        print("   The script may be pointing at the wrong file.")
    else:
        snippet = html[idx:idx+120].replace('\n','↵').replace('\r','')
        print("\n❌ ERROR: Found 'const DATA' but pattern did not match.")
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

size_kb = os.path.getsize(HTML_FILE) / 1024
print()
print("✅ Dashboard updated successfully!")
log(f"File size: {size_kb:.0f} KB")
log(f"Updated:   {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
log(f"Publish copy: {PUBLISH_FILE}")
print()
input("Press Enter to close...")
