#!/usr/bin/env python3
"""
Build script for 409 S Boyle Ave BOV - Los Angeles, CA 90033
Based on Stocker Gardens template (build_bov_v2.py).
32-unit RSO studio asset in Boyle Heights.
"""
import base64, json, os, sys, time, urllib.request, urllib.parse, io, statistics

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
OUTPUT = os.path.join(SCRIPT_DIR, "index.html")
BOV_BASE_URL = "https://409sboyle.laaa.com"
PDF_WORKER_URL = "https://laaa-pdf-worker.laaa-team.workers.dev"
PDF_FILENAME = "BOV - 409 S Boyle Ave, Los Angeles.pdf"
PDF_LINK = PDF_WORKER_URL + "/?url=" + urllib.parse.quote(BOV_BASE_URL + "/", safe="") + "&filename=" + urllib.parse.quote(PDF_FILENAME, safe="")

# ============================================================
# RAG CHATBOT CONFIG
# ============================================================
ENABLE_CHATBOT = False
BOV_NAMESPACE = "boyle-409"
CHAT_WORKER_URL = "https://laaa-chat-worker.laaa-team.workers.dev"
PROPERTY_DISPLAY_NAME = "409 S Boyle Ave"
STARTER_QUESTIONS = [
    "What is the asking price and cap rate?",
    "Tell me about the rent upside and ADU potential",
    "Summarize the rent roll and current rents",
    "What do the comparable sales show?"
]

# ============================================================
# IMAGE LOADING
# ============================================================
def load_image_b64(filename):
    path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(path):
        print(f"WARNING: Image not found: {path}")
        return ""
    ext = filename.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    print(f"  Loaded image: {filename} ({len(data)//1024}KB b64)")
    return f"data:{mime};base64,{data}"

print("Loading images...")
IMG = {
    "logo": load_image_b64("LAAA_Team_White.png"),
    "glen": load_image_b64("Glen_Scher.png"),
    "filip": load_image_b64("Filip_Niculete.png"),
    "hero": load_image_b64("Aerial_Google_Earth_Close.png"),
    "grid1": load_image_b64("Street_View_Exterior.png"),
    "grid2": load_image_b64("Aerial_Google_Earth.png"),
    "loc_map": load_image_b64("Location_Map_Context.png"),
    "closings_map": load_image_b64("closings-map.png"),
    "team_aida": load_image_b64("Aida_Memary.png"),
    "team_logan": load_image_b64("Logan_Ward.png"),
    "team_morgan": load_image_b64("Morgan_Wetmore.png"),
    "team_luka": load_image_b64("Luka_Leader.png"),
    "team_jason": load_image_b64("Jason_Mandel.png"),
    "team_alexandro": load_image_b64("Alexandro_Tapia.png"),
    "team_blake": load_image_b64("Blake_Lewitt.png"),
    "team_mike": load_image_b64("Mike_Palade.png"),
    "team_tony": load_image_b64("Tony_Dang.png"),
}

# ============================================================
# SUBJECT COORDINATES
# ============================================================
SUBJECT_LAT, SUBJECT_LNG = 34.0428765, -118.2196850

# ============================================================
# CACHED GEOCODE DATA
# ============================================================
ADDRESSES = {
    "223 N Breed St, Los Angeles, CA 90033": (34.0460199, -118.2098654),
    "323 N Soto St, Los Angeles, CA 90033": (34.0474295, -118.2074637),
    "2221 Michigan Ave, Los Angeles, CA 90033": (34.0460730, -118.2110436),
    "301 S Boyle Ave, Los Angeles, CA 90033": (34.0452789, -118.2198368),
    "456 S Breed St, Los Angeles, CA 90033": (34.0402349, -118.2135414),
    "571 Fairview Ave, Los Angeles, CA 90033": (34.0536112, -118.2207576),
    "2649 Marengo St, Los Angeles, CA 90033": (34.0546013, -118.1983125),
    "2107 E Cesar E Chavez Ave, Los Angeles, CA 90033": (34.0483934, -118.2112010),
    "124 N Westmoreland Ave, Los Angeles, CA 90004": (34.0742984, -118.2878258),
    "308 S Boyle Ave, Los Angeles, CA 90033": (34.0451076, -118.2196875),
    "2707 Pomeroy Ave, Los Angeles, CA 90033": (34.0533787, -118.1974811),
    "207 N Savannah St, Los Angeles, CA 90033": (34.0421399, -118.2029369),
    "2448 Boulder St, Los Angeles, CA 90033": (34.0489778, -118.2051660),
    "444 S Chicago St, Los Angeles, CA 90033": (34.0409627, -118.2146262),
    "529 S Lorena St, Los Angeles, CA 90033": (34.0316259, -118.1985886),
    "234 N Chicago St, Los Angeles, CA 90033": (34.0467524, -118.2109175),
    "2019 City View Ave, Los Angeles, CA 90033": (34.0531685, -118.2103021),
    "1849 Sichel St, Los Angeles, CA 90031": (34.0646559, -118.2128832),
    "409 S Boyle Ave, Los Angeles, CA 90033": (34.0428765, -118.2196850),
}
print(f"Using cached geocode data ({len(ADDRESSES)} addresses)")

# ============================================================
# FINANCIAL DATA
# ============================================================
LIST_PRICE = 3_200_000
TAX_RATE = 0.0121
UNITS = 32
SF = 15_862
GSR = 524_339
PF_GSR = 624_000
VACANCY_PCT = 0.05
OTHER_INCOME = 910
MGMT_PCT = 0.04
LOT_SIZE_ACRES = 0.41

# Non-tax, non-management expense items
NON_TAX_NON_MGMT_EXP = (
    18_672  # Insurance
    + 80_528  # Utilities
    + 28_800  # R&M ($900/unit)
    + 24_000  # On-Site Manager
    + 11_200  # Contract Services ($350/unit)
    + 8_143   # Admin & Legal
    + 6_615   # LAHD Registration
    + 2_000   # Marketing ($63/unit)
    + 9_600   # Reserves ($300/unit)
    + 7_771   # Other
)

# Financing constants
INTEREST_RATE = 0.065
AMORTIZATION_YEARS = 30
LTV = 0.55

# Derived EGI and management
CUR_EGI = GSR * (1 - VACANCY_PCT) + OTHER_INCOME
PF_EGI = PF_GSR * (1 - VACANCY_PCT) + OTHER_INCOME
CUR_MGMT = CUR_EGI * MGMT_PCT
PF_MGMT = PF_EGI * MGMT_PCT

# Total non-tax expenses (including management)
NON_TAX_CUR_EXP = NON_TAX_NON_MGMT_EXP + CUR_MGMT
NON_TAX_PF_EXP = NON_TAX_NON_MGMT_EXP + PF_MGMT

def calc_principal_reduction_yr1(loan_amount, annual_rate, amort_years):
    r = annual_rate / 12
    n = amort_years * 12
    monthly_pmt = loan_amount * (r * (1 + r)**n) / ((1 + r)**n - 1)
    balance = loan_amount
    total_principal = 0
    for _ in range(12):
        interest = balance * r
        principal = monthly_pmt - interest
        total_principal += principal
        balance -= principal
    return total_principal

def calc_loan_constant(annual_rate, amort_years):
    r = annual_rate / 12
    n = amort_years * 12
    monthly_pmt_per_dollar = r * (1 + r)**n / ((1 + r)**n - 1)
    return monthly_pmt_per_dollar * 12

LOAN_CONSTANT = calc_loan_constant(INTEREST_RATE, AMORTIZATION_YEARS)

def calc_metrics(price):
    taxes = price * TAX_RATE
    cur_egi = GSR * (1 - VACANCY_PCT) + OTHER_INCOME
    pf_egi = PF_GSR * (1 - VACANCY_PCT) + OTHER_INCOME
    cur_mgmt = cur_egi * MGMT_PCT
    pf_mgmt = pf_egi * MGMT_PCT
    cur_exp = NON_TAX_NON_MGMT_EXP + cur_mgmt + taxes
    pf_exp = NON_TAX_NON_MGMT_EXP + pf_mgmt + taxes
    cur_noi = cur_egi - cur_exp
    pf_noi = pf_egi - pf_exp
    loan_amount = price * LTV
    down_payment = price * (1 - LTV)
    debt_service = loan_amount * LOAN_CONSTANT
    net_cf_cur = cur_noi - debt_service
    net_cf_pf = pf_noi - debt_service
    coc_cur = net_cf_cur / down_payment * 100 if down_payment > 0 else 0
    coc_pf = net_cf_pf / down_payment * 100 if down_payment > 0 else 0
    dcr_cur = cur_noi / debt_service if debt_service > 0 else 0
    dcr_pf = pf_noi / debt_service if debt_service > 0 else 0
    prin_red = calc_principal_reduction_yr1(loan_amount, INTEREST_RATE, AMORTIZATION_YEARS)
    total_return_cur = net_cf_cur + prin_red
    total_return_pf = net_cf_pf + prin_red
    total_return_pct_cur = total_return_cur / down_payment * 100 if down_payment > 0 else 0
    total_return_pct_pf = total_return_pf / down_payment * 100 if down_payment > 0 else 0
    return {
        "price": price, "taxes": taxes,
        "cur_noi": cur_noi, "pf_noi": pf_noi,
        "cur_egi": cur_egi, "pf_egi": pf_egi,
        "cur_exp": cur_exp, "pf_exp": pf_exp,
        "per_unit": price / UNITS, "per_sf": price / SF,
        "cur_cap": cur_noi / price * 100, "pf_cap": pf_noi / price * 100,
        "grm": price / GSR, "pf_grm": price / PF_GSR,
        "loan_amount": loan_amount, "down_payment": down_payment,
        "debt_service": debt_service, "net_cf_cur": net_cf_cur, "net_cf_pf": net_cf_pf,
        "coc_cur": coc_cur, "coc_pf": coc_pf, "dcr_cur": dcr_cur, "dcr_pf": dcr_pf,
        "prin_red": prin_red, "total_return_cur": total_return_cur, "total_return_pf": total_return_pf,
        "total_return_pct_cur": total_return_pct_cur, "total_return_pct_pf": total_return_pct_pf,
    }

# $50K increments, $3.5M down to $2.8M
MATRIX_PRICES = list(range(3_500_000, 2_750_000, -50_000))
MATRIX = [calc_metrics(p) for p in MATRIX_PRICES]
AT_LIST = calc_metrics(LIST_PRICE)

print(f"Financials at list ${LIST_PRICE:,.0f}: Cap {AT_LIST['cur_cap']:.2f}%, NOI ${AT_LIST['cur_noi']:,.0f}")

# ============================================================
# OPERATING STATEMENT VARIABLES (at list price)
# ============================================================
TAXES_AT_LIST = LIST_PRICE * TAX_RATE
CUR_TOTAL_EXP = NON_TAX_NON_MGMT_EXP + CUR_MGMT + TAXES_AT_LIST
PF_TOTAL_EXP = NON_TAX_NON_MGMT_EXP + PF_MGMT + TAXES_AT_LIST
CUR_NOI_AT_LIST = CUR_EGI - CUR_TOTAL_EXP
PF_NOI_AT_LIST = PF_EGI - PF_TOTAL_EXP

# ============================================================
# UNIT MIX DATA (reconstructed from underwriting)
# ============================================================
RENT_ROLL = [
    ("101", "Studio", 496, 1266, 1625),
    ("102", "Studio", 496, 1550, 1625),
    ("103", "Studio", 496, 1500, 1625),
    ("104", "Studio", 496, 1575, 1625),
    ("105", "Studio", 496, 1480, 1625),
    ("106", "Studio", 496, 1600, 1625),
    ("107", "Studio", 496, 0, 1625),       # Vacant
    ("108", "Studio", 496, 0, 1625),       # Vacant
    ("109", "Studio", 496, 1550, 1625),
    ("110", "Studio", 496, 1475, 1625),
    ("111", "Studio", 496, 1100, 1625),
    ("112", "Studio", 496, 1425, 1625),
    ("113", "Studio", 496, 1550, 1625),    # Recently leased at market
    ("114", "Studio", 496, 1650, 1625),    # Recently leased at market
    ("115", "1BD/1BA", 500, 1873, 1875),
    ("116", "1BD/1BA", 500, 250, 1875),    # Anomaly - verify with owner
    ("201", "Studio", 496, 1575, 1625),
    ("202", "Studio", 496, 1550, 1625),
    ("203", "Studio", 496, 1600, 1625),
    ("204", "Studio", 496, 1525, 1625),
    ("205", "Studio", 496, 1575, 1625),
    ("206", "Studio", 496, 1550, 1625),
    ("207", "Studio", 496, 1575, 1625),
    ("208", "Studio", 496, 1525, 1625),
    ("209", "Studio", 496, 1550, 1625),    # Recently leased at market
    ("210", "Studio", 496, 1500, 1625),
    ("211", "Studio", 496, 1450, 1625),
    ("212", "Studio", 496, 1575, 1625),
    ("213", "Studio", 496, 1525, 1625),
    ("214", "Studio", 496, 1650, 1625),    # Recently leased at market
    ("215", "Studio", 496, 1200, 1625),
    ("216", "Studio", 496, 926, 1625),
]

# Verify GSR matches
monthly_total = sum(r[3] for r in RENT_ROLL)
annual_total = monthly_total * 12
print(f"Rent roll: {len(RENT_ROLL)} units, monthly ${monthly_total:,}, annual ${annual_total:,} (target GSR: ${GSR:,})")
# Adjust last unit to hit GSR exactly if needed
diff = GSR - annual_total
if abs(diff) > 0:
    last_unit_idx = len(RENT_ROLL) - 1
    adj = diff / 12
    old_rent = RENT_ROLL[last_unit_idx][3]
    RENT_ROLL[last_unit_idx] = (RENT_ROLL[last_unit_idx][0], RENT_ROLL[last_unit_idx][1],
                                 RENT_ROLL[last_unit_idx][2], round(old_rent + adj),
                                 RENT_ROLL[last_unit_idx][4])
    monthly_total = sum(r[3] for r in RENT_ROLL)
    annual_total = monthly_total * 12
    print(f"  Adjusted Unit 216 rent to ${RENT_ROLL[last_unit_idx][3]:,}/mo -> annual ${annual_total:,}")

# ============================================================
# SALE COMPS DATA
# ============================================================
SALE_COMPS = [
    {"num": 1, "addr": "223 N Breed St", "units": 32, "sf": 12064, "yr": 1927, "price": 2795000, "ppu": 87344, "psf": 231.68, "cap": 7.13, "grm": 8.93, "dom": 93, "date": "01/13/2026", "splp": "87.5%", "notes": "32 studios/efficiencies; 7 vacant; value-add; orig $3,195K"},
    {"num": 2, "addr": "323 N Soto St", "units": 40, "sf": 10364, "yr": 1929, "price": 2500000, "ppu": 62500, "psf": 241.22, "cap": 12.34, "grm": 4.86, "dom": 150, "date": "09/30/2024", "splp": "52.6%", "notes": "Court sale; distressed; 13 vacant"},
    {"num": 3, "addr": "2221 Michigan Ave", "units": 32, "sf": 9229, "yr": 1926, "price": 2500000, "ppu": 78125, "psf": 270.89, "cap": 11.45, "grm": 5.07, "dom": 150, "date": "09/30/2024", "splp": "58.1%", "notes": "Court sale; distressed; same portfolio as #2"},
    {"num": 4, "addr": "301 S Boyle Ave", "units": 27, "sf": 13884, "yr": 1908, "price": 3025000, "ppu": 112037, "psf": 217.88, "cap": 5.47, "grm": 8.45, "dom": 106, "date": "05/29/2024", "splp": "--", "notes": "Same street; debt assumption ($1.47M JPM)"},
    {"num": 5, "addr": "456 S Breed St", "units": 24, "sf": 18857, "yr": 1972, "price": 3600000, "ppu": 150000, "psf": 190.91, "cap": 2.39, "grm": None, "dom": 9, "date": "04/02/2024", "splp": "78.3%", "notes": "1972; elevator; 27 parking; 1BD/2BD mix"},
    {"num": 6, "addr": "571 Fairview Ave", "units": 38, "sf": 12006, "yr": 1964, "price": 4995000, "ppu": 131447, "psf": 416.04, "cap": 5.90, "grm": None, "dom": 63, "date": "03/13/2024", "splp": "83.3%", "notes": "37 singles + 1 1BD; pool; mid-century"},
    {"num": 7, "addr": "2649 Marengo St", "units": 24, "sf": 29096, "yr": 1989, "price": 5145000, "ppu": 214375, "psf": 176.83, "cap": 6.01, "grm": 9.71, "dom": 134, "date": "06/04/2025", "splp": "98.9%", "notes": "NOT RSO (1989); mixed BD; 46 parking"},
]

ON_MARKET_COMPS = [
    {"num": "A", "addr": "2107 E Cesar E Chavez Ave", "units": 30, "yr": 1927, "sf": 12352, "price": 3795000, "ppu": 126500, "psf": 307, "cap": 7.23, "grm": 8.35, "dom": 35, "notes": "Mixed-use (27 res + 3 commercial)"},
    {"num": "B", "addr": "124 N Westmoreland Ave", "units": 30, "yr": 1927, "sf": 22163, "price": 4350000, "ppu": 145000, "psf": 196, "cap": 7.29, "grm": 8.16, "dom": "--", "notes": "All studios; Koreatown; trading 15%+ below list"},
]

RENT_COMPS = [
    {"num": 1, "addr": "308 S Boyle Ave", "dist": "0.1", "rent": "$1,500", "sf": "400-500", "psf": "$3.33", "yr": "Pre-1930", "units": 20, "cond": "Renovated", "notes": "Granite counters, hardwood, stainless; 0.2 mi to E Line"},
    {"num": 2, "addr": "571 Fairview Ave", "dist": "0.6", "rent": "$1,895", "sf": "~350", "psf": "$5.41", "yr": "1964", "units": 38, "cond": "Renovated", "notes": "Pool, laundry, A/C; units $1,495-$1,995"},
    {"num": 3, "addr": "2707 Pomeroy Ave", "dist": "0.9", "rent": "$1,575", "sf": "460", "psf": "$3.42", "yr": "Pre-1960", "units": 20, "cond": "Renovated", "notes": "Hardwood, granite, new windows, balcony"},
    {"num": 4, "addr": "207 N Savannah St", "dist": "0.7", "rent": "$1,595", "sf": "500", "psf": "$3.19", "yr": "1932", "units": 17, "cond": "Renovated", "notes": "Seismic retrofit complete"},
    {"num": 5, "addr": "2448 Boulder St", "dist": "0.5", "rent": "$1,495", "sf": "352", "psf": "$4.25", "yr": "1964", "units": 8, "cond": "Renovated", "notes": "Laminate floors, newer appliances"},
    {"num": 6, "addr": "444 S Chicago St", "dist": "0.3", "rent": "$1,750-$1,795", "sf": "~600", "psf": "$2.99", "yr": "Pre-1940", "units": "Small MF", "cond": "Renovated", "notes": "Larger studio; priced higher due to size"},
    {"num": 7, "addr": "529 S Lorena St", "dist": "1.1", "rent": "$1,650", "sf": "525", "psf": "$3.14", "yr": "Pre-1960", "units": "Small MF", "cond": "Updated", "notes": "East BH / Lorena corridor"},
    {"num": 8, "addr": "234 N Chicago St", "dist": "0.3", "rent": "$1,975", "sf": "~450", "psf": "$4.39", "yr": "Pre-1930", "units": "16+", "cond": "Renovated", "notes": "Highest comp in core BH"},
    {"num": 9, "addr": "2019 City View Ave", "dist": "0.8", "rent": "$1,475", "sf": "~400", "psf": "$3.69", "yr": "Pre-1950", "units": "Small MF", "cond": "Updated", "notes": "Lower end; less renovation"},
    {"num": 10, "addr": "1849 Sichel St", "dist": "1.5", "rent": "$1,695", "sf": "350", "psf": "$4.84", "yr": "Pre-1960", "units": "Small MF", "cond": "Renovated", "notes": "Lincoln Heights"},
]

# ============================================================
# COMP NARRATIVES
# ============================================================
COMP_NARRATIVES = [
    """<p><strong>223 N Breed St (32 units, $2.795M, 01/2026) - Most Comparable:</strong> Nearly identical to the subject - 32 studios in a 1927 building in Boyle Heights. Traded at $87,344/unit and a 7.13% cap rate after 93 DOM, closing at 87.5% of its original $3.195M list price. The key distinction is condition: Breed had 7 vacant units at sale, rents 62% below market, and requires renovation throughout. The subject has completed over $400,000 in capital improvements (400-amp electrical, 151 windows, solar hot water), maintains 94% occupancy, has separately metered electric, and holds plan-check-approved ADU entitlements. These advantages support a 15% premium over Breed, placing the subject at $100,000+/unit.</p>""",
    """<p><strong>323 N Soto St (40 units, $2.5M, 09/2024) - Distressed:</strong> Court-ordered portfolio sale with 13 vacant units. Traded at $62,500/unit and 52.6% of list price after 150 DOM. This represents floor and distress pricing - not arm's-length market value. The subject is not distressed and should not be priced against this transaction.</p>""",
    """<p><strong>2221 Michigan Ave (32 units, $2.5M, 09/2024) - Distressed:</strong> Same court-ordered portfolio as Soto, closing at $78,125/unit and 58.1% of list. Originally listed at $4.3M ($134,375/unit), which is more indicative of the seller's perception of market value before the court-mandated discount. Useful only as a floor reference.</p>""",
    """<p><strong>301 S Boyle Ave (27 units, $3.025M, 05/2024) - Geographic Match:</strong> Located on the same street just five blocks north. Traded at $112,037/unit - a 1908-vintage building with a 1-bedroom unit mix that commands higher per-unit pricing than studios. The sale included a $1.47M debt assumption from JPMorgan Chase. The subject should trade at a modest discount due to its studio product, partially offset by its newer vintage, larger unit count, and recent capital upgrades.</p>""",
    """<p><strong>456 S Breed St (24 units, $3.6M, 04/2024) - Different Product:</strong> A 1972-built building with an elevator, 27 parking spaces, and a 1BD/2BD unit mix - fundamentally different from the subject's pre-war studios. Traded at $150,000/unit at a 2.39% cap rate reflecting deeply below-market rents. Serves as a ceiling reference only.</p>""",
    """<p><strong>571 Fairview Ave (38 units, $4.995M, 03/2024) - Larger / Mid-Century:</strong> A 38-unit, 1964-built building with 37 singles, a pool, and mid-century design appeal. Traded at $131,447/unit and a 5.90% cap rate after 63 DOM. The subject is 40 years older with fewer amenities but has a stronger CapEx profile and ADU development upside. A 15-20% discount from Fairview implies $105,000-$112,000/unit for the subject.</p>""",
    """<p><strong>2649 Marengo St (24 units, $5.145M, 06/2025) - Non-RSO Outlier:</strong> A 1989-built building not subject to the RSO. Its mixed bedroom count, 46 parking spaces, and $214,375/unit price reflect a different product class entirely. Excluded from primary pricing analysis. Its 98.9% SP/LP ratio is notable as a data point on buyer appetite for Boyle Heights multifamily.</p>""",
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def fc(n):
    if n is None: return "n/a"
    return f"${n:,.0f}"
def fp(n):
    if n is None: return "n/a"
    return f"{n:.2f}%"

def build_map_js(map_id, comps, comp_color, subject_lat, subject_lng):
    js = f"var {map_id} = L.map('{map_id}').setView([{subject_lat}, {subject_lng}], 14);\n"
    js += f"L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{attribution: '&copy; OpenStreetMap'}}).addTo({map_id});\n"
    js += f"""L.marker([{subject_lat}, {subject_lng}], {{icon: L.divIcon({{className: 'custom-marker', html: '<div style="background:#C5A258;color:#fff;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);">&#9733;</div>', iconSize: [32, 32], iconAnchor: [16, 16]}})}})\n.addTo({map_id}).bindPopup('<b>409 S Boyle Ave</b><br>Subject Property<br>32 Units | 15,862 SF');\n"""
    for i, c in enumerate(comps):
        lat, lng = None, None
        for a, coords in ADDRESSES.items():
            if c["addr"].lower() in a.lower() and coords:
                lat, lng = coords
                break
        if lat is None: continue
        label = str(c.get("num", i + 1))
        popup = f"<b>#{label}: {c['addr']}</b><br>{c.get('units', '')} Units | {fc(c.get('price', 0))}"
        js += f"""L.marker([{lat}, {lng}], {{icon: L.divIcon({{className: 'custom-marker', html: '<div style="background:{comp_color};color:#fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;border:2px solid #fff;box-shadow:0 2px 4px rgba(0,0,0,0.3);">{label}</div>', iconSize: [26, 26], iconAnchor: [13, 13]}})}})\n.addTo({map_id}).bindPopup('{popup}');\n"""
    return js

sale_map_js = build_map_js("saleMap", SALE_COMPS, "#1B3A5C", SUBJECT_LAT, SUBJECT_LNG)
active_map_js = build_map_js("activeMap", ON_MARKET_COMPS, "#2E7D32", SUBJECT_LAT, SUBJECT_LNG)
rent_comps_for_map = [{"addr": c["addr"], "num": c["num"], "price": 0, "units": c["units"]} for c in RENT_COMPS]
rent_map_js = build_map_js("rentMap", rent_comps_for_map, "#1B3A5C", SUBJECT_LAT, SUBJECT_LNG)

# ============================================================
# GENERATE DYNAMIC TABLE HTML
# ============================================================

# Pricing matrix
matrix_html = ""
for m in MATRIX:
    cls = ' class="highlight"' if m["price"] == LIST_PRICE else ""
    matrix_html += f'<tr{cls}><td class="num">{fc(m["price"])}</td><td class="num">{fp(m["cur_cap"])}</td><td class="num">{fp(m["pf_cap"])}</td><td class="num">{fp(m["coc_cur"])}</td><td class="num">${m["per_sf"]:.0f}</td><td class="num">{fc(m["per_unit"])}</td><td class="num">{m["pf_grm"]:.2f}x</td></tr>\n'

# Summary page expense rows (Current vs Pro Forma at list price)
sum_expense_items = [
    ("Real Estate Taxes", TAXES_AT_LIST, TAXES_AT_LIST),
    ("Insurance", 18672, 18672),
    ("Utilities", 80528, 80528),
    ("Repairs &amp; Maintenance", 28800, 28800),
    ("On-site Manager", 24000, 24000),
    ("Contract Services", 11200, 11200),
    ("Administrative &amp; Legal", 8143, 8143),
    ("LAHD Registration", 6615, 6615),
    ("Marketing", 2000, 2000),
    ("Reserves", 9600, 9600),
    ("Other", 7771, 7771),
    ("Management Fee (4%)", CUR_MGMT, PF_MGMT),
]
sum_expense_html = ""
for label, cur_val, pf_val in sum_expense_items:
    sum_expense_html += f'<tr><td>{label}</td><td class="num">${cur_val:,.0f}</td><td class="num">${pf_val:,.0f}</td></tr>\n'

# Rent roll
rent_roll_html = ""
total_sf = total_cur = total_mkt = 0
for unit, utype, sqft, cur, mkt in RENT_ROLL:
    if cur == 0:
        rent_roll_html += f"<tr><td>{unit}</td><td>{utype}</td><td>{sqft:,}</td><td><em>Vacant</em></td><td>-</td><td>${mkt:,}</td><td>${mkt/sqft:.2f}</td></tr>\n"
    else:
        rent_roll_html += f"<tr><td>{unit}</td><td>{utype}</td><td>{sqft:,}</td><td>${cur:,}</td><td>${cur/sqft:.2f}</td><td>${mkt:,}</td><td>${mkt/sqft:.2f}</td></tr>\n"
    total_sf += sqft; total_cur += cur; total_mkt += mkt
rent_roll_html += f'<tr style="font-weight:700;background:#1B3A5C;color:#fff;"><td>TOTAL</td><td>{UNITS} Units</td><td>{total_sf:,}</td><td>${total_cur:,}</td><td>${total_cur/total_sf:.2f}</td><td>${total_mkt:,}</td><td>${total_mkt/total_sf:.2f}</td></tr>'

# Sale comps table
sale_comps_html = ""
sale_comps_html += f'<tr class="highlight" style="font-weight:700;"><td>S</td><td>409 S Boyle Ave</td><td>{UNITS}</td><td>Proposed</td><td>{fc(LIST_PRICE)}</td><td>{fc(int(LIST_PRICE / UNITS))}</td><td>${LIST_PRICE / SF:.0f}</td><td>{AT_LIST["cur_cap"]:.2f}%</td><td>{AT_LIST["grm"]:.2f}</td><td>1924</td><td style="font-size:11px;">Subject Property</td></tr>\n'
for c in SALE_COMPS:
    cap_str = fp(c["cap"]) if c["cap"] else "n/a"
    grm_str = f'{c["grm"]:.2f}' if c["grm"] else "n/a"
    sale_comps_html += f'<tr><td>{c["num"]}</td><td>{c["addr"]}</td><td>{c["units"]}</td><td>{c["date"]}</td><td>{fc(c["price"])}</td><td>{fc(c["ppu"])}</td><td>${c["psf"]:.0f}</td><td>{cap_str}</td><td>{grm_str}</td><td>{c["yr"]}</td><td style="font-size:11px;">{c["notes"]}</td></tr>\n'

# Non-distressed averages/medians (comps 1, 4, 5, 6)
nd_comps = [c for c in SALE_COMPS if c["num"] in [1, 4, 5, 6]]
nd_ppus = [c["ppu"] for c in nd_comps]
nd_psfs = [c["psf"] for c in nd_comps]
nd_caps = [c["cap"] for c in nd_comps if c["cap"]]
nd_grms = [c["grm"] for c in nd_comps if c["grm"]]
sale_comps_html += f'<tr style="font-weight:600;background:#f0f4f8;"><td></td><td>Non-Distressed Avg</td><td></td><td></td><td></td><td>{fc(int(sum(nd_ppus)/len(nd_ppus)))}</td><td>${sum(nd_psfs)/len(nd_psfs):.0f}</td><td>{sum(nd_caps)/len(nd_caps):.2f}%</td><td>{sum(nd_grms)/len(nd_grms):.2f}</td><td></td><td></td></tr>'
sale_comps_html += f'<tr style="font-weight:600;background:#f0f4f8;"><td></td><td>Non-Distressed Median</td><td></td><td></td><td></td><td>{fc(int(statistics.median(nd_ppus)))}</td><td>${statistics.median(nd_psfs):.0f}</td><td>{statistics.median(nd_caps):.2f}%</td><td>{statistics.median(nd_grms):.2f}</td><td></td><td></td></tr>'

# Operating statement
income_lines = [
    ("Gross Scheduled Rent", GSR, False, None),
    ("Less: Vacancy (5%)", -(GSR * VACANCY_PCT), False, None),
    ("Other Income (RSO/SCEP Passthroughs)", OTHER_INCOME, False, 1),
]
expense_lines = [
    ("Real Estate Taxes", TAXES_AT_LIST, 2),
    ("Insurance", 18672, 3),
    ("Utilities (Water/Sewer/Gas/Trash/Common Electric)", 80528, 4),
    ("Repairs & Maintenance", 28800, 5),
    ("On-site Manager", 24000, 6),
    ("Contract Services & Supplies", 11200, 7),
    ("Administrative & Legal", 8143, 8),
    ("LAHD Registration", 6615, 9),
    ("Marketing", 2000, 10),
    ("Reserves", 9600, 11),
    ("Other (Permits, State Tax, Misc)", 7771, 12),
    ("Management Fee (4%)", CUR_MGMT, 13),
]

op_income_html = ""
for label, val, _, note_num in income_lines:
    v_str = f"${val:,.0f}" if val >= 0 else f"(${abs(val):,.0f})"
    pu = f"${val/UNITS:,.0f}" if val >= 0 else f"(${abs(val)/UNITS:,.0f})"
    note_ref = f'<span class="note-ref">[{note_num}]</span>' if note_num else ""
    op_income_html += f"<tr><td>{label} {note_ref}</td><td class='num'>{v_str}</td><td class='num'>{pu}</td><td class='num'> - </td></tr>\n"
op_income_html += f'<tr class="summary"><td><strong>Effective Gross Income</strong></td><td class="num"><strong>${CUR_EGI:,.0f}</strong></td><td class="num"><strong>${CUR_EGI/UNITS:,.0f}</strong></td><td class="num"><strong>100.0%</strong></td></tr>'

op_expense_html = ""
for label, val, note_num in expense_lines:
    pct = f"{val/CUR_EGI*100:.1f}%"
    note_ref = f'<span class="note-ref">[{note_num}]</span>' if note_num else ""
    op_expense_html += f"<tr><td>{label} {note_ref}</td><td class='num'>${val:,.0f}</td><td class='num'>${val/UNITS:,.0f}</td><td class='num'>{pct}</td></tr>\n"
op_expense_html += f'<tr class="summary"><td><strong>Total Expenses</strong></td><td class="num"><strong>${CUR_TOTAL_EXP:,.0f}</strong></td><td class="num"><strong>${CUR_TOTAL_EXP/UNITS:,.0f}</strong></td><td class="num"><strong>{CUR_TOTAL_EXP/CUR_EGI*100:.1f}%</strong></td></tr>'
op_expense_html += f'\n<tr class="summary"><td><strong>Net Operating Income</strong></td><td class="num"><strong>${CUR_NOI_AT_LIST:,.0f}</strong></td><td class="num"><strong>${CUR_NOI_AT_LIST/UNITS:,.0f}</strong></td><td class="num"><strong>{CUR_NOI_AT_LIST/CUR_EGI*100:.1f}%</strong></td></tr>'

# Unit summary for summary page
studios = [(u, s, c, m) for u, t, s, c, m in RENT_ROLL if t == "Studio"]
onebd = [(u, s, c, m) for u, t, s, c, m in RENT_ROLL if t == "1BD/1BA"]
occupied_studios = [(u, s, c, m) for u, s, c, m in studios if c > 0]
studio_avg_cur = sum(c for _, _, c, _ in occupied_studios) / len(occupied_studios) if occupied_studios else 0
studio_avg_mkt = sum(m for _, _, _, m in studios) / len(studios) if studios else 0
onebd_avg_cur = sum(c for _, _, c, _ in onebd) / len(onebd) if onebd else 0
onebd_avg_mkt = sum(m for _, _, _, m in onebd) / len(onebd) if onebd else 0

print("Building HTML...")

# ============================================================
# ASSEMBLE FULL HTML
# ============================================================
html_parts = []

# HEAD + CSS
html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta property="og:title" content="Broker Opinion of Value - 409 S Boyle Ave">
<meta property="og:description" content="32-Unit Multifamily Investment - Los Angeles, CA 90033 | LAAA Team - Marcus & Millichap">
<meta property="og:image" content="https://409sboyle.laaa.com/preview.png">
<meta property="og:url" content="https://409sboyle.laaa.com/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Broker Opinion of Value - 409 S Boyle Ave">
<meta name="twitter:description" content="32-Unit Multifamily Investment - Los Angeles, CA 90033 | LAAA Team - Marcus & Millichap">
<meta name="twitter:image" content="https://409sboyle.laaa.com/preview.png">
<title>BOV - 409 S Boyle Ave, Los Angeles | LAAA Team</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',sans-serif;color:#333;line-height:1.6;background:#fff;}}
html{{scroll-padding-top:50px;}}
.cover{{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;color:#fff;overflow:hidden;}}
.cover-bg{{position:absolute;inset:0;background-size:cover;background-position:center;filter:brightness(0.45);z-index:0;}}
.cover-content{{position:relative;z-index:2;padding:60px 40px;max-width:860px;}}
.cover-logo{{width:320px;margin:0 auto 30px;display:block;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3));}}
.cover-label{{font-size:13px;font-weight:500;letter-spacing:3px;text-transform:uppercase;color:#C5A258;margin-bottom:18px;}}
.cover-title{{font-size:46px;font-weight:700;letter-spacing:1px;margin-bottom:8px;text-shadow:0 2px 12px rgba(0,0,0,0.3);}}
.cover-stats{{display:flex;gap:32px;justify-content:center;flex-wrap:wrap;margin-bottom:32px;}}
.cover-stat{{text-align:center;}}.cover-stat-value{{display:block;font-size:26px;font-weight:600;color:#fff;}}.cover-stat-label{{display:block;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:#C5A258;margin-top:4px;}}
.client-greeting{{font-size:16px;font-weight:400;letter-spacing:2px;text-transform:uppercase;color:#C5A258;margin-top:16px;}}
.cover-headshots{{display:flex;justify-content:center;gap:40px;margin-top:24px;margin-bottom:16px;}}
.cover-headshot-wrap{{text-align:center;}}
.cover-headshot{{width:80px;height:80px;border-radius:50%;border:3px solid #C5A258;object-fit:cover;box-shadow:0 4px 16px rgba(0,0,0,0.4);}}
.cover-headshot-name{{font-size:12px;font-weight:600;margin-top:6px;color:#fff;}}
.cover-headshot-title{{font-size:10px;color:#C5A258;}}
.gold-line{{height:3px;background:#C5A258;margin:20px 0;}}
.pdf-float-btn{{position:fixed;bottom:24px;right:24px;z-index:9999;padding:14px 28px;background:#C5A258;color:#1B3A5C;font-size:14px;font-weight:700;text-decoration:none;border-radius:8px;letter-spacing:0.5px;box-shadow:0 4px 16px rgba(0,0,0,0.35);transition:background 0.2s,transform 0.2s;display:flex;align-items:center;gap:8px;}}.pdf-float-btn:hover{{background:#fff;transform:translateY(-2px);}}.pdf-float-btn svg{{width:18px;height:18px;fill:currentColor;}}
.toc-nav{{background:#1B3A5C;padding:0 12px;display:flex;flex-wrap:nowrap;gap:0;justify-content:center;align-items:stretch;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,0.15);overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;-ms-overflow-style:none;}}
.toc-nav::-webkit-scrollbar{{display:none;}}
.toc-nav a{{color:rgba(255,255,255,0.85);text-decoration:none;font-size:11px;font-weight:500;letter-spacing:0.3px;text-transform:uppercase;padding:12px 8px;border-bottom:2px solid transparent;transition:all 0.2s ease;white-space:nowrap;display:flex;align-items:center;}}
.toc-nav a:hover{{color:#fff;background:rgba(197,162,88,0.12);border-bottom-color:rgba(197,162,88,0.4);}}.toc-nav a.toc-active{{color:#C5A258;font-weight:600;border-bottom-color:#C5A258;}}
.section{{padding:50px 40px;max-width:1100px;margin:0 auto;}}.section-alt{{background:#f8f9fa;}}
.section-title{{font-size:26px;font-weight:700;color:#1B3A5C;margin-bottom:6px;}}.section-subtitle{{font-size:13px;color:#C5A258;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;font-weight:500;}}
.section-divider{{width:60px;height:3px;background:#C5A258;margin-bottom:30px;}}.sub-heading{{font-size:18px;font-weight:600;color:#1B3A5C;margin:30px 0 16px;}}
.metrics-grid,.metrics-grid-4{{display:grid;gap:16px;margin-bottom:30px;}}.metrics-grid{{grid-template-columns:repeat(3,1fr);}}.metrics-grid-4{{grid-template-columns:repeat(4,1fr);}}
.metric-card{{background:#1B3A5C;border-radius:12px;padding:24px;text-align:center;color:#fff;}}
.metric-value{{display:block;font-size:28px;font-weight:700;color:#fff;margin-bottom:4px;}}.metric-label{{display:block;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.6);margin-top:6px;}}.metric-sub{{display:block;font-size:12px;color:#C5A258;margin-top:4px;}}
table{{width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px;}}th{{background:#1B3A5C;color:#fff;padding:10px 12px;text-align:left;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;}}td{{padding:8px 12px;border-bottom:1px solid #eee;}}tr:nth-child(even){{background:#f5f5f5;}}tr.highlight{{background:#FFF8E7 !important;border-left:3px solid #C5A258;}}
.table-scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:24px;}}.table-scroll table{{min-width:700px;margin-bottom:0;}}
.info-table{{width:100%;}}.info-table td{{padding:8px 12px;border-bottom:1px solid #eee;font-size:13px;}}.info-table td:first-child{{font-weight:600;color:#1B3A5C;width:40%;}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-bottom:30px;}}
td.num,th.num{{text-align:right;}}
p{{margin-bottom:16px;font-size:14px;line-height:1.7;}}
.condition-note{{background:#FFF8E7;border-left:4px solid #C5A258;padding:16px 20px;margin:24px 0;border-radius:0 4px 4px 0;font-size:13px;line-height:1.6;}}
.condition-note-label{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#C5A258;margin-bottom:8px;}}.achievements-list{{font-size:13px;line-height:1.8;}}
.note-ref{{font-size:9px;color:#C5A258;font-weight:700;vertical-align:super;}}
.tr-tagline{{font-size:24px;font-weight:600;color:#1B3A5C;text-align:center;padding:16px 24px;margin-bottom:20px;border-left:4px solid #C5A258;background:#FFF8E7;border-radius:0 4px 4px 0;font-style:italic;}}.tr-map-print{{display:none;}}.tr-service-quote{{margin:24px 0;}}.tr-service-quote h3{{font-size:18px;font-weight:700;color:#1B3A5C;margin-bottom:8px;line-height:1.3;}}.tr-service-quote p{{font-size:14px;line-height:1.7;}}
.bio-grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:24px 0;}}.bio-card{{display:flex;gap:16px;align-items:flex-start;}}.bio-headshot{{width:100px;height:100px;border-radius:50%;border:3px solid #C5A258;object-fit:cover;flex-shrink:0;}}.bio-name{{font-size:16px;font-weight:700;color:#1B3A5C;margin-bottom:2px;}}.bio-title{{font-size:11px;color:#C5A258;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;}}.bio-text{{font-size:13px;line-height:1.6;color:#444;}}
.costar-badge{{text-align:center;background:#FFF8E7;border:2px solid #C5A258;border-radius:8px;padding:20px 24px;margin:30px auto 24px;max-width:600px;}}.costar-badge-title{{font-size:22px;font-weight:700;color:#1B3A5C;line-height:1.2;}}.costar-badge-sub{{font-size:12px;color:#C5A258;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-top:6px;}}
.press-strip{{display:flex;justify-content:center;align-items:center;gap:28px;flex-wrap:wrap;margin:24px 0;padding:16px 20px;background:#f0f4f8;border-radius:6px;}}.press-strip-label{{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#888;font-weight:600;}}.press-logo{{font-size:13px;font-weight:700;color:#1B3A5C;letter-spacing:0.5px;}}
.team-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0;}}.team-card{{text-align:center;padding:8px;}}.team-headshot{{width:60px;height:60px;border-radius:50%;border:2px solid #C5A258;object-fit:cover;margin:0 auto 4px;display:block;}}.team-card-name{{font-size:13px;font-weight:700;color:#1B3A5C;}}.team-card-title{{font-size:10px;color:#C5A258;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;}}
.mkt-quote{{background:#FFF8E7;border-left:4px solid #C5A258;padding:16px 24px;margin:20px 0;border-radius:0 4px 4px 0;font-size:15px;font-style:italic;line-height:1.6;color:#1B3A5C;}}.mkt-channels{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px;}}.mkt-channel{{background:#f0f4f8;border-radius:8px;padding:16px 20px;}}.mkt-channel h4{{color:#1B3A5C;font-size:14px;margin-bottom:8px;}}.mkt-channel ul{{margin:0;padding-left:18px;}}.mkt-channel li{{font-size:13px;line-height:1.5;margin-bottom:4px;}}
.perf-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px;}}.perf-card{{background:#f0f4f8;border-radius:8px;padding:16px 20px;}}.perf-card h4{{color:#1B3A5C;font-size:14px;margin-bottom:8px;}}.perf-card ul{{margin:0;padding-left:18px;}}.perf-card li{{font-size:13px;line-height:1.5;margin-bottom:4px;}}.platform-strip{{display:flex;justify-content:center;align-items:center;gap:20px;flex-wrap:wrap;margin-top:24px;padding:14px 20px;background:#1B3A5C;border-radius:6px;}}.platform-strip-label{{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#C5A258;font-weight:600;}}.platform-name{{font-size:12px;font-weight:600;color:#fff;letter-spacing:0.5px;}}
.inv-split{{display:grid;grid-template-columns:50% 50%;gap:24px;}}.inv-left .metrics-grid-4{{grid-template-columns:repeat(2,1fr);}}.inv-text p{{font-size:13px;line-height:1.6;margin-bottom:10px;}}.inv-logo{{display:none;}}.inv-right{{display:flex;flex-direction:column;gap:16px;padding-top:70px;}}.inv-photo{{height:280px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);}}.inv-photo img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block;}}.inv-highlights{{background:#f0f4f8;border:1px solid #dce3eb;border-radius:8px;padding:16px 20px;flex:1;}}.inv-highlights h4{{color:#1B3A5C;font-size:13px;margin-bottom:8px;}}.inv-highlights ul{{margin:0;padding-left:18px;}}.inv-highlights li{{font-size:12px;line-height:1.5;margin-bottom:5px;}}
.loc-grid{{display:grid;grid-template-columns:58% 42%;gap:28px;align-items:start;}}.loc-left{{max-height:380px;overflow:hidden;}}.loc-left p{{font-size:13.5px;line-height:1.7;margin-bottom:14px;}}.loc-right{{display:block;max-height:380px;overflow:hidden;}}.loc-wide-map{{width:100%;height:200px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-top:20px;}}.loc-wide-map img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block;}}
.prop-grid-4{{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto auto;gap:20px;}}
.buyer-split{{display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:start;}}.buyer-objections .obj-item{{margin-bottom:14px;}}.buyer-objections .obj-q{{font-weight:700;color:#1B3A5C;margin-bottom:4px;font-size:14px;}}.buyer-objections .obj-a{{font-size:13px;color:#444;line-height:1.6;}}.buyer-photo{{width:100%;height:220px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-top:24px;}}.buyer-photo img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block;}}
.buyer-profile{{background:#f0f4f8;border-left:4px solid #1B3A5C;padding:20px 24px;margin:24px 0;border-radius:0 4px 4px 0;}}.buyer-profile-label{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#1B3A5C;margin-bottom:12px;}}.buyer-profile ul{{list-style:none;padding:0;margin:0;}}.buyer-profile li{{padding:8px 0;border-bottom:1px solid #dce3eb;font-size:14px;line-height:1.6;color:#333;}}.buyer-profile li:last-child{{border-bottom:none;}}.buyer-profile li strong{{color:#1B3A5C;}}.buyer-profile .bp-closing{{font-size:13px;color:#555;margin-top:12px;font-style:italic;}}
.leaflet-map{{height:400px;border-radius:4px;border:1px solid #ddd;margin-bottom:30px;z-index:1;}}.map-fallback{{display:none;font-size:12px;color:#666;font-style:italic;margin-bottom:30px;}}
.embed-map-wrap{{position:relative;width:100%;margin-bottom:20px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);}}.embed-map-wrap iframe{{display:block;width:100%;height:420px;border:0;}}
.os-two-col{{display:grid;grid-template-columns:55% 45%;gap:24px;align-items:stretch;margin-bottom:24px;}}.os-right{{font-size:10.5px;line-height:1.45;color:#555;background:#f8f9fb;border:1px solid #e0e4ea;border-radius:6px;padding:16px 20px;}}.os-right h3{{font-size:13px;margin:0 0 8px;}}.os-right p{{margin-bottom:4px;}}
.summary-page{{margin-top:24px;border:1px solid #dce3eb;border-radius:8px;padding:20px;background:#fff;}}.summary-banner{{text-align:center;background:#1B3A5C;color:#fff;padding:10px 16px;font-size:14px;font-weight:700;letter-spacing:2px;text-transform:uppercase;border-radius:4px;margin-bottom:16px;}}.summary-two-col{{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;}}.summary-table{{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:12px;border:1px solid #dce3eb;}}.summary-table th,.summary-table td{{padding:4px 8px;border-bottom:1px solid #e8ecf0;text-align:left;}}.summary-table td.num{{text-align:right;}}.summary-table th.num{{text-align:right;}}.summary-header{{background:#1B3A5C;color:#fff;padding:5px 8px !important;font-size:10px !important;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;border-bottom:none !important;}}.summary-table tr.summary td{{border-top:2px solid #1B3A5C;font-weight:700;background:#f0f4f8;}}.summary-table tr:nth-child(even){{background:#fafbfc;}}.summary-trade-range{{text-align:center;margin:24px auto;padding:16px 24px;border:2px solid #1B3A5C;border-radius:6px;max-width:480px;}}.summary-trade-label{{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#555;font-weight:600;margin-bottom:6px;}}.summary-trade-prices{{font-size:26px;font-weight:700;color:#1B3A5C;}}
.page-break-marker{{height:4px;background:repeating-linear-gradient(90deg,#ddd 0,#ddd 8px,transparent 8px,transparent 16px);margin:0;}}
.footer{{background:#1B3A5C;color:#fff;padding:50px 40px;text-align:center;}}.footer-logo{{width:180px;margin-bottom:30px;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.3));}}.footer-team{{display:flex;justify-content:center;gap:40px;margin-bottom:30px;flex-wrap:wrap;}}.footer-person{{text-align:center;flex:1;min-width:280px;}}.footer-headshot{{width:70px;height:70px;border-radius:50%;border:2px solid #C5A258;margin-bottom:10px;object-fit:cover;}}.footer-name{{font-size:16px;font-weight:600;}}.footer-title{{font-size:12px;color:#C5A258;margin-bottom:8px;}}.footer-contact{{font-size:12px;color:rgba(255,255,255,0.7);line-height:1.8;}}.footer-contact a{{color:rgba(255,255,255,0.7);text-decoration:none;}}.footer-office{{font-size:12px;color:rgba(255,255,255,0.5);margin-top:20px;}}.footer-disclaimer{{font-size:10px;color:rgba(255,255,255,0.35);margin-top:20px;max-width:800px;margin-left:auto;margin-right:auto;line-height:1.6;}}
@media(max-width:768px){{.cover-content{{padding:30px 20px;}}.cover-title{{font-size:32px;}}.cover-logo{{width:220px;}}.cover-headshots{{gap:24px;}}.cover-headshot{{width:60px;height:60px;}}.pdf-float-btn{{padding:10px 18px;font-size:12px;bottom:16px;right:16px;}}.section{{padding:30px 16px;}}.photo-grid{{grid-template-columns:1fr;}}.two-col{{grid-template-columns:1fr;}}.metrics-grid,.metrics-grid-4{{grid-template-columns:repeat(2,1fr);gap:12px;}}.metric-card{{padding:14px 10px;}}.metric-value{{font-size:22px;}}.footer-team{{flex-direction:column;align-items:center;}}.leaflet-map{{height:300px;}}.embed-map-wrap iframe{{height:320px;}}.toc-nav{{padding:0 6px;}}.toc-nav a{{font-size:10px;padding:10px 6px;letter-spacing:0.2px;}}.table-scroll table{{min-width:560px;}}.bio-grid{{grid-template-columns:1fr;gap:16px;}}.bio-headshot{{width:60px;height:60px;}}.press-strip{{gap:16px;}}.press-logo{{font-size:11px;}}.costar-badge-title{{font-size:18px;}}.img-float-right{{float:none;width:100%;margin:0 0 16px 0;}}.mkt-channels,.perf-grid{{grid-template-columns:1fr;}}.os-two-col{{grid-template-columns:1fr;}}.loc-grid{{grid-template-columns:1fr;}}.loc-wide-map{{height:180px;margin-top:16px;}}.inv-split{{grid-template-columns:1fr;}}.inv-photo{{height:240px;}}.buyer-split{{grid-template-columns:1fr;}}.summary-two-col{{grid-template-columns:1fr;}}.prop-grid-4{{grid-template-columns:1fr;}}}}
@media(max-width:420px){{.cover-content{{padding:24px 16px;}}.cover-logo{{width:180px;}}.cover-title{{font-size:24px;}}.cover-stats{{gap:10px;}}.cover-stat-value{{font-size:18px;}}.cover-stat-label{{font-size:9px;}}.cover-label{{font-size:11px;}}.cover-headshots{{gap:16px;margin-top:16px;}}.cover-headshot{{width:50px;height:50px;}}.pdf-float-btn{{padding:10px 14px;font-size:0;bottom:14px;right:14px;}}.pdf-float-btn svg{{width:22px;height:22px;}}.metrics-grid,.metrics-grid-4{{grid-template-columns:1fr;}}.metric-card{{padding:12px 10px;}}.metric-value{{font-size:20px;}}.section{{padding:24px 12px;}}.section-title{{font-size:20px;}}.footer{{padding:24px 12px;}}.footer-team{{gap:16px;}}.toc-nav{{padding:0 4px;}}.toc-nav a{{font-size:8px;padding:10px 4px;letter-spacing:0;}}.leaflet-map{{height:240px;}}}}
@media print{{
@page{{size:letter landscape;margin:0.4in 0.5in;}}
.pdf-float-btn,.toc-nav,.leaflet-map,.embed-map-wrap,.page-break-marker{{display:none !important;}}
.map-fallback{{display:block !important;}}
body{{font-size:11px;line-height:1.5;color:#222;}}
p{{font-size:11px;line-height:1.5;margin-bottom:8px;orphans:3;widows:3;}}
.section{{padding:20px 20px;max-width:100%;}}.section-title{{font-size:18px;margin-bottom:2px;}}.section-subtitle{{font-size:10px;letter-spacing:1px;margin-bottom:6px;}}.section-divider{{margin-bottom:10px;height:2px;}}.sub-heading{{font-size:13px;margin:10px 0 6px;}}
h2,h3,.section-title,.sub-heading{{page-break-after:avoid;}}
table{{page-break-inside:auto;font-size:10px;margin-bottom:8px;}}thead{{display:table-header-group;}}tr{{page-break-inside:avoid;}}th{{padding:4px 8px;font-size:8px;}}td{{padding:4px 8px;font-size:10px;}}.table-scroll{{overflow:visible;}}.table-scroll table{{min-width:0 !important;width:100%;}}.info-table td{{padding:4px 8px;font-size:10px;}}
.two-col{{gap:14px;margin-bottom:10px;}}
.cover{{min-height:7.5in;padding:0;page-break-after:always;display:flex;align-items:center;justify-content:center;}}.cover-bg{{filter:brightness(0.35);-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.cover-headshots{{display:flex;gap:20px;}}.cover-headshot{{width:55px;height:55px;}}.cover-headshot-name{{font-size:10px;}}.cover-headshot-title{{font-size:8px;}}
.metrics-grid,.metrics-grid-4{{gap:8px;margin-bottom:10px;page-break-inside:avoid;}}.metrics-grid{{grid-template-columns:repeat(3,1fr);}}.metrics-grid-4{{grid-template-columns:repeat(4,1fr);}}.metric-card{{padding:8px 6px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.metric-value{{font-size:18px;}}.metric-label{{font-size:8px;margin-top:2px;}}.metric-sub{{font-size:9px;}}
.tr-page2{{page-break-before:always;}}
#marketing{{page-break-before:always;}}
#investment{{page-break-before:always;}}
#location{{page-break-before:always;}}
#prop-details{{page-break-before:always;}}
#transactions{{page-break-before:always;}}
#property-info{{page-break-before:always;}}
#sale-comps{{page-break-before:always;}}
#financials{{page-break-before:always;}}
.price-reveal{{page-break-before:always;}}
.footer{{page-break-before:always;}}
.tr-tagline{{font-size:15px;padding:8px 14px;margin-bottom:8px;}}
.tr-map-print{{display:block;width:100%;height:240px;border-radius:4px;overflow:hidden;margin-bottom:8px;}}.tr-map-print img{{width:100%;height:100%;object-fit:cover;object-position:center;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
.tr-service-quote{{margin:10px 0;}}.tr-service-quote h3{{font-size:13px;margin-bottom:4px;}}.tr-service-quote p{{font-size:11px;line-height:1.45;}}
.bio-grid{{gap:14px;margin:10px 0;}}.bio-headshot{{width:75px;height:75px;}}.bio-name{{font-size:13px;}}.bio-title{{font-size:9px;}}.bio-text{{font-size:10px;line-height:1.4;}}
.costar-badge{{padding:8px 14px;margin:6px auto;}}.costar-badge-title{{font-size:15px;}}.costar-badge-sub{{font-size:9px;}}
.condition-note{{padding:8px 12px;margin:8px 0;font-size:10px;line-height:1.45;}}.achievements-list{{font-size:10px;line-height:1.45;}}
.press-strip{{padding:8px 14px;margin:8px 0;gap:14px;}}.press-strip-label{{font-size:8px;}}.press-logo{{font-size:10px;}}
.team-grid{{gap:8px;margin:8px 0;}}.team-card{{padding:4px;}}.team-headshot{{width:45px;height:45px;}}.team-card-name{{font-size:10px;}}.team-card-title{{font-size:8px;}}
.mkt-quote{{padding:8px 14px;margin:8px 0;font-size:12px;line-height:1.5;}}
.mkt-channels{{gap:10px;margin-top:10px;}}.mkt-channel{{padding:10px 14px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.mkt-channel h4{{font-size:12px;margin-bottom:4px;}}.mkt-channel ul{{margin:0;padding-left:16px;}}.mkt-channel li{{font-size:10px;line-height:1.4;margin-bottom:2px;}}
.perf-grid{{gap:10px;margin-top:10px;}}.perf-card{{padding:10px 14px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.perf-card h4{{font-size:12px;margin-bottom:4px;}}.perf-card ul{{margin:0;padding-left:16px;}}.perf-card li{{font-size:10px;line-height:1.4;margin-bottom:2px;}}
.platform-strip{{padding:6px 12px;margin-top:10px;gap:10px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.platform-strip-label{{font-size:8px;}}.platform-name{{font-size:9px;}}
.inv-split{{grid-template-columns:50% 50%;gap:14px;}}.inv-left .metrics-grid-4{{gap:6px;margin-bottom:6px;}}.inv-text p{{font-size:11px;line-height:1.5;margin-bottom:6px;}}.inv-logo{{display:none !important;}}.inv-right{{padding-top:30px;}}.inv-photo{{height:220px;}}.inv-photo img{{-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.inv-highlights{{padding:10px 14px;}}.inv-highlights h4{{font-size:11px;margin-bottom:4px;}}.inv-highlights li{{font-size:10px;line-height:1.4;margin-bottom:2px;}}
.loc-grid{{display:grid;grid-template-columns:58% 42%;gap:14px;page-break-inside:avoid;}}.loc-left{{max-height:340px;overflow:hidden;}}.loc-left p{{font-size:10.5px;line-height:1.4;margin-bottom:5px;}}.loc-right{{max-height:340px;overflow:hidden;}}.loc-wide-map{{height:220px;margin-top:8px;}}.loc-wide-map img{{-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.loc-right .info-table td{{padding:3px 8px;font-size:10px;}}.loc-right .info-table{{margin-bottom:0;}}
.prop-grid-4{{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto auto;gap:10px;page-break-inside:avoid;}}.prop-grid-4 table{{font-size:9px;margin-bottom:0;}}.prop-grid-4 th{{font-size:7.5px;padding:3px 6px;}}.prop-grid-4 td{{padding:3px 6px;font-size:9px;}}.prop-grid-4 .info-table td{{padding:3px 6px;font-size:9px;}}
.buyer-split{{grid-template-columns:1fr 1fr;gap:14px;page-break-inside:avoid;}}.buyer-profile{{padding:8px 12px;margin:6px 0;}}.buyer-profile-label{{font-size:10px;margin-bottom:5px;}}.buyer-profile li{{padding:4px 0;font-size:10.5px;line-height:1.4;}}.bp-closing{{font-size:10px;}}.buyer-objections .obj-item{{margin-bottom:8px;}}.buyer-objections .obj-q{{font-size:11px;margin-bottom:2px;}}.buyer-objections .obj-a{{font-size:10px;line-height:1.4;}}.buyer-photo{{height:180px;margin-top:8px;border-radius:4px;overflow:hidden;}}.buyer-photo img{{width:100%;height:100%;object-fit:cover;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
.summary-page{{margin-top:8px;page-break-before:always;border:none;padding:0;background:transparent;}}.summary-banner{{text-align:center;background:#1B3A5C;color:#fff;padding:6px 10px;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;border-radius:2px;margin-bottom:8px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.summary-two-col{{display:grid;grid-template-columns:1fr 1fr;gap:8px;align-items:start;}}.summary-table{{width:100%;border-collapse:collapse;margin-bottom:6px;font-size:8px;border:1px solid #ccc;}}.summary-table th,.summary-table td{{padding:2px 5px;border-bottom:1px solid #ddd;text-align:left;}}.summary-table td.num{{text-align:right;}}.summary-table th.num{{text-align:right;}}.summary-table th{{font-size:6.5px;text-transform:uppercase;letter-spacing:0.5px;}}.summary-header{{background:#1B3A5C;color:#fff;padding:3px 5px !important;font-size:7px !important;font-weight:700;letter-spacing:1px;border-bottom:none !important;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.summary-table tr.summary td{{border-top:1.5px solid #1B3A5C;font-weight:700;background:#f0f4f8;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.summary-table tr:nth-child(even){{background:#fafbfc;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.summary-trade-range{{text-align:center;margin:8px auto;padding:8px 14px;border:2px solid #1B3A5C;border-radius:3px;max-width:350px;page-break-inside:avoid;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.summary-trade-label{{font-size:7px;letter-spacing:1.5px;color:#333;font-weight:600;margin-bottom:3px;}}.summary-trade-prices{{font-size:14px;font-weight:700;color:#1B3A5C;}}
.os-two-col{{page-break-before:always;page-break-inside:avoid;grid-template-columns:55% 45%;gap:14px;align-items:stretch;}}.os-right{{font-size:9px;line-height:1.3;padding:8px 12px;background:#f8f9fb;border:1px solid #ddd;border-radius:4px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}.os-right p{{margin-bottom:2px;}}.os-right h3{{font-size:10px;margin:0 0 4px;}}.note-ref{{font-size:7px;color:#C5A258;font-weight:700;vertical-align:super;}}
.price-reveal .condition-note{{padding:6px 10px;margin:6px 0;font-size:10px;line-height:1.35;}}
.footer{{padding:20px 30px;}}.footer-logo{{width:120px;margin-bottom:10px;}}.footer-headshot{{width:50px;height:50px;}}.footer-name{{font-size:13px;}}.footer-title{{font-size:10px;}}.footer-contact{{font-size:10px;line-height:1.5;}}.footer-disclaimer{{font-size:8px;}}
}}
</style>
</head>
<body>
""")

# ==================== COVER ====================
html_parts.append(f"""
<div class="cover">
<div class="cover-bg" style="background-image:url('{IMG['hero']}');"></div>
<div class="cover-content">
<img src="{IMG['logo']}" class="cover-logo" alt="LAAA Team">
<div class="cover-label">Confidential Broker Opinion of Value</div>
<div class="cover-title">409 S Boyle Avenue</div>
<div class="cover-address" style="font-size:20px;font-weight:300;margin-bottom:28px;color:rgba(255,255,255,0.8);">Los Angeles, California 90033</div>
<div class="gold-line" style="width:80px;margin:0 auto 24px;"></div>
<div class="cover-stats">
<div class="cover-stat"><span class="cover-stat-value">32</span><span class="cover-stat-label">Units</span></div>
<div class="cover-stat"><span class="cover-stat-value">15,862</span><span class="cover-stat-label">Square Feet</span></div>
<div class="cover-stat"><span class="cover-stat-value">1924</span><span class="cover-stat-label">Year Built</span></div>
<div class="cover-stat"><span class="cover-stat-value">0.41 Ac</span><span class="cover-stat-label">Acres</span></div>
</div>
<p class="client-greeting" id="client-greeting"></p>
<div class="cover-headshots">
<div class="cover-headshot-wrap">
<img class="cover-headshot" src="{IMG['glen']}" alt="Glen Scher">
<div class="cover-headshot-name">Glen Scher</div>
<div class="cover-headshot-title">SMDI</div>
</div>
<div class="cover-headshot-wrap">
<img class="cover-headshot" src="{IMG['filip']}" alt="Filip Niculete">
<div class="cover-headshot-name">Filip Niculete</div>
<div class="cover-headshot-title">SMDI</div>
</div>
</div>
<p style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:8px;">February 2026</p>
</div>
</div>
""")

# ==================== TOC NAV ====================
html_parts.append(f"""
<nav class="toc-nav" id="toc-nav">
<a href="#track-record">Track Record</a>
<a href="#marketing">Marketing</a>
<a href="#investment">Investment</a>
<a href="#location">Location</a>
<a href="#prop-details">Property</a>
<a href="#transactions">History</a>
<a href="#property-info">Buyer Profile</a>
<a href="#sale-comps">Sale Comps</a>
<a href="#on-market">On-Market</a>
<a href="#rent-comps">Rent Comps</a>
<a href="#financials">Financials</a>
<a href="#contact">Contact</a>
</nav>
<a href="{PDF_LINK}" class="pdf-float-btn" target="_blank" rel="noopener"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zm-1 13l-4-4h3V9h2v4h3l-4 4z"/></svg>Download PDF</a>
""")

# ==================== TRACK RECORD P1 ====================
html_parts.append(f"""
<div class="section section-alt" id="track-record">
<div class="section-title">Team Track Record</div>
<div class="section-subtitle">LA Apartment Advisors at Marcus &amp; Millichap</div>
<div class="section-divider"></div>
<div class="tr-tagline"><span style="display:block;font-size:1.2em;font-weight:700;margin-bottom:4px;">LAAA Team of Marcus &amp; Millichap</span>Expertise, Execution, Excellence.</div>
<div class="metrics-grid metrics-grid-4">
<div class="metric-card"><span class="metric-value">501</span><span class="metric-label">Closed Transactions</span><span class="metric-sub">All-Time</span></div>
<div class="metric-card"><span class="metric-value">$1.6B</span><span class="metric-label">Total Sales Volume</span><span class="metric-sub">All-Time</span></div>
<div class="metric-card"><span class="metric-value">5,000+</span><span class="metric-label">Units Sold</span><span class="metric-sub">All-Time</span></div>
<div class="metric-card"><span class="metric-value">34</span><span class="metric-label">Median Days on Market</span><span class="metric-sub">Apartments</span></div>
</div>
<div class="embed-map-wrap"><iframe src="https://www.google.com/maps/d/u/0/embed?mid=1ewCjzE3QX9p6m2MqK-md8b6fZitfIzU&ehbc=2E312F" allowfullscreen loading="lazy"></iframe></div>
<div class="tr-map-print"><img src="{IMG['closings_map']}" alt="LAAA Team All-Time Closings Map"></div>
<div class="tr-service-quote">
<h3>We Didn't Invent Great Service, We Just Work Relentlessly to Provide It</h3>
<p>At LAAA Team, we are dedicated to delivering expert multifamily brokerage services in Los Angeles, helping investors navigate the market with precision, strategy, and results-driven execution. With over 500 closed transactions and $1.6B in total sales volume, our team thrives on providing data-driven insights, strategic deal structuring, and hands-on client service to maximize value for our clients.</p>
<p>Founded by Glen Scher and Filip Niculete, LAAA Team operates with a commitment to transparency, efficiency, and market expertise. We take a relationship-first approach, guiding property owners, investors, and developers through every stage of acquisition, disposition, and asset repositioning.</p>
<p>Our mission is simple: To be the most trusted and results-oriented multifamily advisors in Los Angeles, leveraging deep market knowledge, innovative technology, and a proactive deal-making strategy to drive long-term success for our clients.</p>
</div>

<div class="tr-page2">
<div style="text-align:center;margin-bottom:8px;">
<div class="section-title" style="margin-bottom:4px;">Our Team</div>
<div class="section-divider" style="margin:0 auto 12px;"></div>
</div>
<div class="costar-badge" style="margin-top:4px;margin-bottom:8px;">
<div class="costar-badge-title">#1 Most Active Multifamily Sales Team in LA County</div>
<div class="costar-badge-sub">CoStar &bull; 2019, 2020, 2021 &bull; #4 in California</div>
</div>
<div class="bio-grid">
<div class="bio-card">
<img class="bio-headshot" src="{IMG['glen']}" alt="Glen Scher">
<div>
<div class="bio-name">Glen Scher</div>
<div class="bio-title">Senior Managing Director Investments</div>
<div class="bio-text">Senior Managing Director at Marcus &amp; Millichap and co-founder of the LAAA Team. Over 450 transactions and $1.4B in closed sales across LA and the Ventura &amp; Santa Barbara counties, consistently closing 40+ deals per year. Glen joined M&amp;M in 2014 after graduating from UC Santa Barbara with a degree in Economics. Before real estate, he was a Division I golfer at UCSB, earning three individual titles and UCSB Male Athlete of the Year.</div>
</div>
</div>
<div class="bio-card">
<img class="bio-headshot" src="{IMG['filip']}" alt="Filip Niculete">
<div>
<div class="bio-name">Filip Niculete</div>
<div class="bio-title">Senior Managing Director Investments</div>
<div class="bio-text">Senior Managing Director at Marcus &amp; Millichap and co-founder of the LAAA Team. A 15-year veteran with over $650 million in personal sales volume and more than 220 closed transactions. Born in Romania and raised in the San Fernando Valley, Filip studied Finance at San Diego State University and joined M&amp;M in 2011. He has built a reputation for execution, integrity, and relentless work ethic across Los Angeles multifamily.</div>
</div>
</div>
</div>
<div class="team-grid">
<div class="team-card"><img class="team-headshot" src="{IMG['team_aida']}" alt="Aida Memary"><div class="team-card-name">Aida Memary</div><div class="team-card-title">Senior Associate</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_logan']}" alt="Logan Ward"><div class="team-card-name">Logan Ward</div><div class="team-card-title">Associate</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_morgan']}" alt="Morgan Wetmore"><div class="team-card-name">Morgan Wetmore</div><div class="team-card-title">Associate</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_luka']}" alt="Luka Leader"><div class="team-card-name">Luka Leader</div><div class="team-card-title">Associate</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_jason']}" alt="Jason Mandel"><div class="team-card-name">Jason Mandel</div><div class="team-card-title">Associate</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_alexandro']}" alt="Alexandro Tapia"><div class="team-card-name">Alexandro Tapia</div><div class="team-card-title">Associate Investments</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_blake']}" alt="Blake Lewitt"><div class="team-card-name">Blake Lewitt</div><div class="team-card-title">Associate Investments</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_mike']}" alt="Mike Palade"><div class="team-card-name">Mike Palade</div><div class="team-card-title">Agent Assistant</div></div>
<div class="team-card"><img class="team-headshot" src="{IMG['team_tony']}" alt="Tony H. Dang"><div class="team-card-name">Tony H. Dang</div><div class="team-card-title">Business Operations Manager</div></div>
</div>
<div class="condition-note" style="margin-top:20px;">
<div class="condition-note-label">Key Achievements</div>
<p class="achievements-list">
&bull; <strong>Chairman's Club</strong> - Marcus &amp; Millichap's top-tier annual honor (Glen: 2021; Filip: 2018, 2021)<br>
&bull; <strong>National Achievement Award</strong> - Glen: 5 years; Filip: 8 consecutive years<br>
&bull; <strong>Sales Recognition Award</strong> - Glen: 10 consecutive years; Filip: 12 years total<br>
&bull; <strong>Traded.co National Rankings</strong> - Glen Scher: #8 Deal Junkies, #8 Hot List, #8 Rising Talent<br>
&bull; <strong>Connect CRE Next Generation Award</strong> - Filip Niculete (2019)<br>
&bull; <strong>SFVBJ Rookie of the Year</strong> - Glen Scher
</p>
</div>
</div>
</div>
""")

# ==================== MARKETING & RESULTS (standard template) ====================
html_parts.append("""
<div class="page-break-marker"></div>
<div class="section" id="marketing">
<div class="section-title">Our Marketing Approach &amp; Results</div>
<div class="section-subtitle">How We Market Your Listing</div>
<div class="section-divider"></div>
<div class="metrics-grid-4">
<div class="metric-card"><span class="metric-value">30,000+</span><span class="metric-label">Emails Sent</span><span class="metric-sub">Per Listing</span></div>
<div class="metric-card"><span class="metric-value">10,000+</span><span class="metric-label">Online Views</span><span class="metric-sub">Per Listing</span></div>
<div class="metric-card"><span class="metric-value">3.7</span><span class="metric-label">Average Offers</span><span class="metric-sub">Per Listing</span></div>
<div class="metric-card"><span class="metric-value">18</span><span class="metric-label">Days to Escrow</span><span class="metric-sub">Per Listing Average</span></div>
</div>
<div class="mkt-quote"><p>"We are <strong>PROACTIVE</strong> marketers, not reactive. We don't list online and wait for calls. We pick up the phone, call every probable buyer, and explain why your property is a good investment for them."</p></div>
<div class="mkt-channels">
<div class="mkt-channel"><h4>Direct Phone Outreach</h4><ul><li><strong>30+ probable buyers</strong> called directly per listing</li><li><strong>1,500 cold calls per week</strong> across our team of 8 agents</li><li>Focus on 1031 exchange buyers, recent purchasers, and nearby property owners</li></ul></div>
<div class="mkt-channel"><h4>Email Campaigns</h4><ul><li><strong>30,000+ verified</strong> investor and broker email addresses</li><li><strong>~8,000 unique opens</strong> per "Just Listed" email blast</li><li><strong>~800 clicks</strong> per campaign downloading the full marketing package</li></ul></div>
<div class="mkt-channel"><h4>Online Platforms</h4><ul><li><strong>9 listing platforms</strong> with highest-tier exposure on each</li><li><strong>10,000+ views per listing</strong> across all platforms combined</li><li>Custom profile on MLS, CoStar, LoopNet, Crexi, Brevitas, Redfin, M&amp;M, LAAA.com, ApartmentBuildings.com</li></ul></div>
<div class="mkt-channel"><h4>Additional Channels</h4><ul><li><strong>"Just Listed" postcards</strong> mailed to nearby property owners</li><li><strong>Social media</strong> across Facebook, LinkedIn, Instagram, and X</li><li><strong>Current inventory attachment</strong> sent ~25 times/day by all team members</li></ul></div>
</div>
<div class="perf-grid">
<div class="perf-card"><h4>Pricing Accuracy</h4><ul><li><strong>97.6%</strong> average sale-price-to-list-price ratio</li><li><strong>1 in 5 listings</strong> sell at or above the asking price</li><li>Our pricing methodology is data-driven and comp-backed</li></ul></div>
<div class="perf-card"><h4>Marketing Speed</h4><ul><li><strong>18 days</strong> average to open escrow after hitting the market</li><li><strong>17.5%</strong> of our listings sell in the first week</li><li><strong>3.7 signed offers</strong> per listing on average</li></ul></div>
<div class="perf-card"><h4>Contract Strength</h4><ul><li><strong>10-day average</strong> contingency period</li><li>We almost never allow a loan or appraisal contingency</li><li><strong>Less than 60 days</strong> average escrow timeframe</li><li><strong>10%</strong> open escrow with zero contingencies</li></ul></div>
<div class="perf-card"><h4>Exchange Expertise</h4><ul><li><strong>61%</strong> of our sellers complete a 1031 exchange</li><li><strong>29%</strong> of listings sell to a 1031 exchange buyer</li><li><strong>76%</strong> of transactions involve at least one exchange</li></ul></div>
</div>
<div class="platform-strip">
<span class="platform-strip-label">Advertised On</span>
<span class="platform-name">MLS</span><span class="platform-name">CoStar</span><span class="platform-name">LoopNet</span><span class="platform-name">Crexi</span><span class="platform-name">Brevitas</span><span class="platform-name">Redfin</span><span class="platform-name">Marcus &amp; Millichap</span><span class="platform-name">LAAA.com</span><span class="platform-name">ApartmentBuildings.com</span>
</div>
</div>
""")

# ==================== INVESTMENT OVERVIEW ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="investment">
<div class="inv-split">
<div class="inv-left">
<div class="section-title">Investment Overview</div>
<div class="section-subtitle">Boyle Heights - 409 S Boyle Ave, Los Angeles 90033</div>
<div class="section-divider"></div>
<div class="metrics-grid-4">
<div class="metric-card"><span class="metric-value">32</span><span class="metric-label">Total Units</span></div>
<div class="metric-card"><span class="metric-value">15,862</span><span class="metric-label">Building SF</span></div>
<div class="metric-card"><span class="metric-value">0.41 Ac</span><span class="metric-label">Lot Size</span></div>
<div class="metric-card"><span class="metric-value">1924</span><span class="metric-label">Year Built</span></div>
</div>
<div class="inv-text">
<p>The LAAA Team is proud to present 409 S Boyle Avenue, a 32-unit rent-stabilized multifamily property situated in the heart of Boyle Heights, one of Los Angeles' most transit-connected eastside neighborhoods. Originally constructed in 1924 as a two-story wood-frame building, the property comprises 30 studios and 2 one-bedroom units across approximately 15,862 square feet of rentable area. As an RSO asset with vacancy decontrol under Costa-Hawkins, the building offers a buyer predictable in-place cash flow with the ability to reset rents to market upon unit turnover.</p>
<p>What distinguishes this asset from comparable offerings is the depth of capital investment already completed by the current ownership. Over the past several years, ownership has executed more than $400,000 in building system upgrades - including a full 400-amp electrical service with 32 individual 60-amp subpanels (finaled September 2025), a 151-window dual-pane changeout to NFRC-certified units, and a solar hot water system - materially reducing deferred maintenance risk for a new buyer. Additionally, the property holds a Plan Check-approved attached ADU entitlement (approved December 2024) with a second detached ADU application pending.</p>
<p>From a market perspective, Boyle Heights continues to benefit from its immediate proximity to Downtown Los Angeles - just 1.5 miles from the Arts District across the LA River. The property sits a seven-minute walk from the Metro E Line at Mariachi Plaza Station, carries a Walk Score of 84, and is anchored by LAC+USC Medical Center with over 9,600 employees within 1.4 miles. The submarket has recorded rent growth exceeding 3% year-over-year, supported by a 4.9% vacancy rate and limited new multifamily supply.</p>
</div>
<img class="inv-logo" src="{IMG['logo']}" alt="LAAA Team">
</div>
<div class="inv-right">
<div class="inv-photo"><img src="{IMG['grid1']}" alt="409 S Boyle Ave"></div>
<div class="inv-highlights">
<h4>Investment Highlights</h4>
<ul>
<li><strong>Institutional-Quality CapEx Completed</strong> - Full 400-amp electrical upgrade finaled in 2025, 151 dual-pane NFRC windows, and solar hot water system substantially reduce near-term capital requirements for a new buyer</li>
<li><strong>ADU Entitlements in Hand</strong> - Attached ADU Plan Check-approved (December 2024) with detached ADU application pending, delivering permitted density upside without entitlement risk or delay</li>
<li><strong>Individually Metered Electric</strong> - Separately metered electric confirmed, with tenants paying their own usage - a cost structure advantage uncommon in pre-war RSO product</li>
<li><strong>DTLA-Adjacent Transit Corridor</strong> - 0.3-mile walk to Metro E Line (Mariachi Plaza Station), Walk Score of 84, and direct freeway access via I-5, I-10, and I-101</li>
<li><strong>Strong Submarket Fundamentals</strong> - Boyle Heights rent growth of 3.13% YoY, 4.9% vacancy, and 76.7% renter population with limited new construction pipeline</li>
<li><strong>RSO Vacancy Decontrol Across 32 Units</strong> - Costa-Hawkins allows rent-to-market resets upon turnover, providing incremental revenue growth across a diversified unit count</li>
</ul>
</div>
</div>
</div>
</div>
""")

# ==================== LOCATION OVERVIEW ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="location">
<div class="section-title">Location Overview</div>
<div class="section-subtitle">Boyle Heights - 90033</div>
<div class="section-divider"></div>
<div class="loc-grid">
<div class="loc-left">
<p>Boyle Heights is one of Los Angeles' oldest and most culturally rooted neighborhoods, situated directly east of Downtown across the LA River. The area has maintained a distinct residential identity defined by its walkable streetscape, dense housing stock, and strong community institutions - while benefiting from the economic gravity of a rapidly expanding DTLA just 1.5 miles to the west. The Arts District, now one of LA's highest-rent submarkets, sits across the river and continues to drive spillover demand into adjacent eastside neighborhoods where rents remain meaningfully lower.</p>
<p>The property's transit access is a defining attribute. Mariachi Plaza Station on the Metro E Line is a seven-minute walk - approximately 0.3 miles - providing a direct one-seat ride to Santa Monica, Long Beach, and connections throughout the Metro system. The Walk Score of 84 ("Very Walkable") and Transit Score of 69 ("Good Transit") reflect the neighborhood's dense service network. LAC+USC Medical Center - one of the nation's largest public hospital campuses with over 9,600 healthcare workers - sits 1.4 miles from the property, serving as a primary employment anchor.</p>
<p>Boyle Heights' rental market fundamentals support the investment thesis. The submarket has recorded year-over-year rent growth of 3.13%, driven by limited new multifamily supply and sustained demand from a population that is 76.7% renter. The housing vacancy rate sits at 4.9%, well below the threshold that would indicate softening conditions. New construction in the area remains constrained by regulatory overlays and community resistance, which limits the competitive supply pipeline and insulates existing assets from rent compression.</p>
</div>
<div class="loc-right">
<table class="info-table">
<thead><tr><th colspan="2">Location Details</th></tr></thead>
<tbody>
<tr><td>Walk Score</td><td>84 ("Very Walkable")</td></tr>
<tr><td>Transit Score</td><td>69 ("Good Transit")</td></tr>
<tr><td>Nearest Metro</td><td>Mariachi Plaza Station (E Line), 0.3 mi</td></tr>
<tr><td>Nearest Freeway</td><td>I-5, I-10, I-101 (all within 1 mi)</td></tr>
<tr><td>Major Employers</td><td>LAC+USC Medical Center (1.4 mi, 9,600+ workers)</td></tr>
<tr><td>Grocery</td><td>Food 4 Less, local markets within 1 mi</td></tr>
<tr><td>Parks</td><td>Hollenbeck Park (0.3 mi)</td></tr>
<tr><td>Median HH Income</td><td>$56,623</td></tr>
<tr><td>Renter Percentage</td><td>76.7%</td></tr>
<tr><td>Population</td><td>81,701</td></tr>
</tbody>
</table>
</div>
</div>
<div class="loc-wide-map"><img src="{IMG['loc_map']}" alt="Property Location - 409 S Boyle Ave"></div>
</div>
""")

# ==================== PROPERTY DETAILS ====================
html_parts.append("""
<div class="page-break-marker"></div>
<div class="section" id="prop-details">
<div class="section-title">Property Details</div>
<div class="section-subtitle">409 S Boyle Ave, Los Angeles, CA 90033</div>
<div class="section-divider"></div>
<div class="prop-grid-4">
<div><table class="info-table">
<thead><tr><th colspan="2">Property Overview</th></tr></thead>
<tbody>
<tr><td>Address</td><td>409 S Boyle Ave, Los Angeles, CA 90033</td></tr>
<tr><td>APN</td><td>5174-002-014</td></tr>
<tr><td>Year Built</td><td>1924</td></tr>
<tr><td>Units</td><td>32 (30 Studios, 2 One-Bedrooms)</td></tr>
<tr><td>Building SF</td><td>15,862</td></tr>
<tr><td>Avg Unit SF</td><td>~496</td></tr>
<tr><td>Stories / Buildings</td><td>2 Stories / 1 Building</td></tr>
<tr><td>Construction</td><td>Wood Frame</td></tr>
</tbody>
</table></div>
<div><table class="info-table">
<thead><tr><th colspan="2">Site &amp; Zoning</th></tr></thead>
<tbody>
<tr><td>Lot Size</td><td>17,832 SF (0.41 Acres)</td></tr>
<tr><td>Zoning</td><td>[Q]R4-1-RIO-CUGU</td></tr>
<tr><td>TOC Tier</td><td>3</td></tr>
<tr><td>Community Plan</td><td>Boyle Heights</td></tr>
<tr><td>Council District</td><td>CD 14 - Ysabel Jurado</td></tr>
<tr><td>Parking</td><td>12 Surface Spaces (0.38/unit)</td></tr>
<tr><td>Flood / Fire</td><td>Outside Flood Zone, Not in VHFHSZ</td></tr>
</tbody>
</table></div>
<div><table>
<thead><tr><th colspan="3">Building Systems &amp; Capital Improvements</th></tr></thead>
<tbody>
<tr><td>Electrical</td><td>400-amp, 32 x 60-amp subpanels</td><td>Finaled 9/2025 - NEW</td></tr>
<tr><td>Windows</td><td>151 dual-pane NFRC-certified</td><td>Permitted 5/2021</td></tr>
<tr><td>Solar</td><td>Solar hot water system</td><td>Finaled 6/2018</td></tr>
<tr><td>HVAC</td><td>Individual 15K BTU direct vent</td><td>Replacements 2001-2020</td></tr>
<tr><td>Roof</td><td>Flat, Class A/B torch-down</td><td>2009 (17 years old)</td></tr>
<tr><td>Plumbing</td><td>Original - condition unknown</td><td>Water heater replaced 2017</td></tr>
<tr><td>Water Heaters</td><td>Solar hot water system</td><td></td></tr>
<tr><td>Metering</td><td>Electric: individual; Gas/Water: master</td><td>Confirmed</td></tr>
</tbody>
</table></div>
<div><table>
<thead><tr><th colspan="2">Regulatory &amp; Compliance</th></tr></thead>
<tbody>
<tr><td>Rent Control</td><td>LA RSO (pre-1978, vacancy decontrol applies)</td></tr>
<tr><td>Soft-Story Retrofit</td><td>NOT Required (confirmed LADBS)</td></tr>
<tr><td>ADU Entitlements</td><td>Attached ADU - PC Approved 12/2024; Detached - Pending</td></tr>
<tr><td>Code Enforcement</td><td>2 Cases on File (nature unknown)</td></tr>
<tr><td>Certificate of Occupancy</td><td>0 on file (typical for pre-war)</td></tr>
</tbody>
</table></div>
</div>
</div>
""")

# ==================== TRANSACTION HISTORY ====================
html_parts.append("""
<div class="page-break-marker"></div>
<div class="section section-alt" id="transactions">
<div class="section-title">Transaction History</div>
<div class="section-subtitle">Ownership &amp; Sale Record</div>
<div class="section-divider"></div>
<div class="table-scroll"><table>
<thead><tr><th>Date</th><th>Grantor / Grantee</th><th>Sale Price</th><th>$/Unit</th><th>$/SF</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>05/2012</td><td>Orion Ventures LLC to SRD Commercial Group LLC</td><td>$1,915,500</td><td>$59,859</td><td>$121</td><td>Current owner</td></tr>
<tr><td>07/2007</td><td>East Valley Capital Partners to Orion Ventures LLC</td><td>~$2,135,000</td><td>$66,719</td><td>$135</td><td>Part of multi-property deal ($4.15M combined)</td></tr>
<tr><td>2001</td><td>Goldstein to East Valley Capital Partners</td><td>Unknown</td><td>-</td><td>-</td><td>-</td></tr>
<tr><td>1997</td><td>Cal Bay Mtg Group to Goldstein</td><td>$385,000</td><td>$12,031</td><td>$24</td><td>-</td></tr>
</tbody>
</table></div>
<p>The current owner, SRD Commercial Group LLC (Danny Bahng), acquired 409 S Boyle Avenue in May 2012 for $1,915,500 - a basis of $121 per square foot and $59,859 per unit - during the post-Great Financial Crisis recovery period when multifamily pricing in secondary LA submarkets remained well below peak levels. The prior owner, Orion Ventures LLC, had purchased the property in July 2007 as part of a multi-property transaction valued at $4.15 million, near the peak of the pre-recession cycle.</p>
<p>Since acquiring the property, Danny has executed a disciplined capital improvement program totaling more than $400,000 in building system upgrades - including a full 400-amp electrical service (finaled 2025), 151 dual-pane NFRC-certified windows, a solar hot water system (finaled 2018), and multiple HVAC unit replacements. Ownership has also secured ADU entitlements, with an attached ADU receiving Plan Check approval in December 2024 and a detached ADU application pending. At the suggested list price of $3,200,000, the property reflects approximately 67% appreciation over 14 years of ownership.</p>
</div>
""")

# ==================== BUYER PROFILE & OBJECTIONS ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="property-info">
<div class="section-title">Buyer Profile &amp; Anticipated Objections</div>
<div class="section-subtitle">Target Investors &amp; Data-Backed Responses</div>
<div class="section-divider"></div>
<div class="buyer-split">
<div class="buyer-split-left">
<div class="buyer-profile">
<div class="buyer-profile-label">Target Buyer Profile</div>
<ul>
<li><strong>1031 Exchange Investor</strong> - The 32-unit count provides meaningful scale for a tax-deferred exchange, and the RSO designation with completed capital expenditures offers stable, predictable cash flow with limited near-term capital needs. Separately metered electric and recent systems upgrades minimize operating risk for a passive holder.</li>
<li><strong>Local Value-Add Operator</strong> - Interior renovation opportunity exists across the studio units, where long-tenured tenants occupy units at below-market rents. Vacancy decontrol under Costa-Hawkins allows rent reset to market ($1,500-$1,650/mo) upon turnover, creating 30-60% per-unit upside without structural work. The ADU entitlements provide additional income potential without entitlement risk.</li>
<li><strong>Long-Term Developer / Land Banker</strong> - R4 zoning with TOC Tier 3 designation in a Transit Priority Area creates significant future density upside. The 50% density bonus potential, combined with a Walk Score of 84 and location 0.3 miles from the Metro E Line, positions the site for redevelopment when market conditions warrant.</li>
</ul>
<p class="bp-closing">The property's combination of stable current income, renovation upside, and development optionality positions it to attract interest across multiple buyer segments, supporting competitive pricing and a manageable marketing period.</p>
</div>
</div>
<div class="buyer-split-right">
<h3 class="sub-heading" style="margin-top:0;">Anticipated Buyer Objections</h3>
<div class="buyer-objections">
<div class="obj-item">
<p class="obj-q">"At $100,000/unit, isn't this expensive for Boyle Heights studios?"</p>
<p class="obj-a">The most comparable closed sale - 223 N Breed St (32 studios, 1927) - traded at $87,344/unit in January 2026, but that property had 7 vacant units, needed full renovation, and lacked ADU entitlements. The subject's completed $400K+ in capital improvements, 94% occupancy, separately metered electric, and plan-check-approved ADU justify a 15% premium. The median non-distressed RSO comp is $121,742/unit. At $100,000/unit, the subject is priced below the non-distressed median.</p>
</div>
<div class="obj-item">
<p class="obj-q">"The 1924 building likely needs a full repipe - that's $150,000-$200,000."</p>
<p class="obj-a">This is a legitimate risk that should be scoped during due diligence. However, the current owner has invested over $400,000 in other building systems - electrical, windows, solar, HVAC - demonstrating a pattern of capital reinvestment. The expected sale range of $2.9M-$3.1M provides a buyer with room to absorb a repipe scenario and still acquire at a discount to the non-distressed comp median.</p>
</div>
<div class="obj-item">
<p class="obj-q">"The cap rate at $3.2M is only 7.59% - that's reasonable but tight."</p>
<p class="obj-a">The 7.59% is a buyer-normalized cap rate that accounts for reassessed property taxes at the new purchase price, professional management, an on-site manager per California law, and capital reserves. The 7.59% falls within the non-distressed comp range of 2.39% to 7.13%, with a median of 5.69%. The pro forma cap rate of 10.43% reflects significant rent upside achievable through natural turnover.</p>
</div>
<div class="obj-item">
<p class="obj-q">"Unit 116 at $250/month - is that a permanent affordable restriction?"</p>
<p class="obj-a">This requires verification with the owner. If the unit is occupied by a building employee or reflects a data entry error, the below-market rent resolves naturally at turnover. The pricing strategy accounts for the rent roll as reported, including this unit - it is not a hidden liability.</p>
</div>
</div>
</div>
</div>
<div class="buyer-photo"><img src="{IMG['grid2']}" alt="409 S Boyle Ave - Aerial"></div>
</div>
""")

# ==================== SALE COMPS ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="sale-comps">
<div class="section-title">Comparable Sales Analysis</div>
<div class="section-subtitle">7 Closed Sales in Boyle Heights / East LA - Past 18 Months</div>
<div class="section-divider"></div>
<div id="saleMap" class="leaflet-map"></div>
<p class="map-fallback">Interactive map available at the live URL.</p>
<div class="table-scroll"><table>
<thead><tr><th>#</th><th>Address</th><th>Units</th><th>Sale Date</th><th>Price</th><th>$/Unit</th><th>$/SF</th><th>Cap</th><th>GRM</th><th>Yr Built</th><th>Notes</th></tr></thead>
<tbody>
{sale_comps_html}
</tbody>
</table></div>
<h3 class="sub-heading">Individual Comp Analysis</h3>
{''.join(COMP_NARRATIVES)}
<p>Boyle Heights multifamily is actively trading, with seven closed comps identified in the past 12-18 months and three on-market listings in the immediate submarket. Non-distressed SP/LP ratios of 78-99% suggest 10-15% negotiating room from list price is standard for this product type. The weight of non-distressed evidence supports studio product in Boyle Heights trading at $87,000-$131,000/unit, with the subject's completed CapEx profile, ADU entitlements, and 94% occupancy positioning it in the $96,000-$106,000/unit range.</p>
</div>
""")

# ==================== ON-MARKET COMPS ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="on-market">
<div class="section-title">On-Market Comparables</div>
<div class="section-subtitle">Active Listings in Boyle Heights &amp; Comparable Submarkets</div>
<div class="section-divider"></div>
<div id="activeMap" class="leaflet-map"></div>
<p class="map-fallback">Interactive map available at the live URL.</p>
<div class="table-scroll"><table>
<thead><tr><th>#</th><th>Address</th><th>Units</th><th>List Price</th><th>$/Unit</th><th>$/SF</th><th>Cap</th><th>GRM</th><th>DOM</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>A</td><td>2107 E Cesar E Chavez Ave</td><td>30</td><td>$3,795,000</td><td>$126,500</td><td>$307</td><td>7.23%</td><td>8.35</td><td>35</td><td>Mixed-use (27 res + 3 commercial)</td></tr>
<tr><td>B</td><td>124 N Westmoreland Ave</td><td>30</td><td>$4,350,000</td><td>$145,000</td><td>$196</td><td>7.29%</td><td>8.16</td><td>--</td><td>All studios; Koreatown; broker says trading 15%+ below list</td></tr>
</tbody>
</table></div>
<p>The most relevant on-market benchmark is 124 N Westmoreland Ave in Koreatown - a 30-unit, all-studio, 1927 RSO building asking $145,000/unit ($4.35M). Broker intel from Taylor Avakian at Lyon Stahl (February 16, 2026) indicates buyer activity is "below list 15%+" with buyers "interested and writing," implying an expected trade around $123,000/unit ($3.7M). Koreatown is a materially stronger submarket than Boyle Heights - higher rents, stronger tenant demand, better retail amenities - so the subject should be discounted 15-20% from Westmoreland's expected trade price. That produces $98,000-$105,000/unit, consistent with the $100,000/unit suggested list price derived from closed comp analysis.</p>
<p>2107 E Cesar Chavez Ave is a mixed-use property with 27 residential units and 3 commercial spaces, making it an imperfect multifamily comparison. However, the residential component - 27 furnished studios in a 1927 building - is relevant. The asking price of $126,500/unit with a 7.23% cap rate on actual income provides useful context for where the market is pricing studio product in the 90033 zip code.</p>
</div>
""")

# ==================== RENT COMPS ====================
rent_comp_html = ""
for c in RENT_COMPS:
    rent_comp_html += f'<tr><td>{c["num"]}</td><td>{c["addr"]}</td><td>{c["dist"]}</td><td>{c["rent"]}</td><td>{c["sf"]}</td><td>{c["psf"]}</td><td>{c["yr"]}</td><td>{c["units"]}</td><td>{c["cond"]}</td><td>{c["notes"]}</td></tr>\n'

html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section" id="rent-comps">
<div class="section-title">Rent Comparables</div>
<div class="section-subtitle">Renovated Studio Rents in the Boyle Heights Submarket</div>
<div class="section-divider"></div>
<div id="rentMap" class="leaflet-map"></div>
<p class="map-fallback">Interactive map available at the live URL.</p>
<div class="table-scroll"><table>
<thead><tr><th>#</th><th>Address</th><th>Dist.</th><th>Rent</th><th>SF</th><th>$/SF</th><th>Yr Built</th><th>Units</th><th>Condition</th><th>Notes</th></tr></thead>
<tbody>
{rent_comp_html}
</tbody>
</table></div>
<h3 class="sub-heading">Pro Forma Rent Recommendation</h3>
<div class="table-scroll"><table>
<thead><tr><th>Scenario</th><th>Rent/Mo</th><th>$/SF (est. 450 SF)</th><th>Basis</th></tr></thead>
<tbody>
<tr><td><strong>Conservative</strong></td><td>$1,500</td><td>$3.33</td><td>Floor set by Comps #1, #5, #9. Basic renovation, standard finishes.</td></tr>
<tr class="highlight"><td><strong>Moderate (Recommended)</strong></td><td>$1,625</td><td>$3.61</td><td>Supported by Comps #3, #4, #6, #7. Standard renovation with granite, LVP/hardwood, updated bath.</td></tr>
<tr><td><strong>Aggressive</strong></td><td>$1,800</td><td>$4.00</td><td>Supported by Comps #2, #8. Higher-end finishes, Arts District/DTLA spillover tenants.</td></tr>
</tbody>
</table></div>
<p>The moderate scenario at $1,625/mo is supported by the weight of comparable evidence. The subject's advantages - Metro proximity at 0.3 miles from the E Line, recent systems upgrades that reduce CapEx risk for a renovating buyer, and 32-unit scale - offset its disadvantages, including the 1924 vintage and unknown plumbing condition. The $1,625 range is achievable with a $15,000-$20,000 per-unit renovation and reflects current asking rents for renovated studios in older Boyle Heights buildings.</p>
<p>Important context: these are asking rents, not achieved rents. Actual lease-up may require one to two months of vacancy loss or modest concessions. RSO vacancy decontrol under Costa-Hawkins allows rent reset to market on turnover, but the turnover rate depends on tenant demographics. With approximately 37% of the building occupied by Brilliant Corners voucher tenants, turnover on those units may be lower than average, extending the timeline to fully stabilize the rent roll at pro forma levels.</p>
</div>
""")

# ==================== FINANCIAL ANALYSIS ====================
html_parts.append(f"""
<div class="page-break-marker"></div>
<div class="section section-alt" id="financials">
<div class="section-title">Financial Analysis</div>
<div class="section-subtitle">Investment Underwriting</div>
<div class="section-divider"></div>

<!-- SCREEN 1: RENT ROLL -->
<h3 class="sub-heading">Unit Mix &amp; Rent Roll</h3>
<div class="table-scroll"><table>
<thead><tr><th>Unit</th><th>Type</th><th>SF</th><th>Current Rent</th><th>Rent/SF</th><th>Market Rent</th><th>Market/SF</th></tr></thead>
<tbody>{rent_roll_html}</tbody>
</table></div>
<p style="font-size:11px;color:#888;font-style:italic;margin-top:-16px;margin-bottom:20px;">Occupancy: 93.75% (30 occupied, 2 vacant). Unit 116 at $250/month is an anomaly - verify with owner. ~12 Brilliant Corners voucher tenants (~37.5% of building).</p>

<!-- SCREEN 2: OPERATING STATEMENT + NOTES -->
<div class="os-two-col">
<div class="os-left">
<h3 class="sub-heading">Operating Statement</h3>
<table>
<thead><tr><th>Income</th><th class="num">Annual</th><th class="num">Per Unit</th><th class="num">% EGI</th></tr></thead>
<tbody>{op_income_html}</tbody>
</table>
<table>
<thead><tr><th>Expenses</th><th class="num">Annual</th><th class="num">Per Unit</th><th class="num">% EGI</th></tr></thead>
<tbody>{op_expense_html}</tbody>
</table>
<p style="font-size:10px;color:#888;font-style:italic;margin-top:-12px;">Property taxes reassessed at 1.21% of $3,200,000 purchase price. The pricing matrix recalculates taxes at each price point.</p>
</div>
<div class="os-right">
<h3 class="sub-heading">Notes to Operating Statement</h3>
<p><strong>[1] Other Income:</strong> RSO/SCEP passthroughs only ($330 RSO + $580 SCEP from 2024 T-12). No laundry or parking income currently collected.</p>
<p><strong>[2] Real Estate Taxes:</strong> Reassessed at 1.21% of $3,200,000 purchase price. Seller currently pays $30,725 on a Prop 13 basis.</p>
<p><strong>[3] Insurance:</strong> Seller actual of $18,672 ($583/unit). Within benchmark range for pre-war RSO product.</p>
<p><strong>[4] Utilities:</strong> Seller actual verified across 2023 and 2024 operating data. Master-metered gas and water; individually metered electric (tenants pay their own). Includes common area electric.</p>
<p><strong>[5] Repairs &amp; Maintenance:</strong> $900/unit based on Tier 4 benchmark. Recent $400K+ in capital expenditures (electrical 2025, windows 2021, solar 2018) substantially reduce near-term repair burden.</p>
<p><strong>[6] On-site Manager:</strong> Required per CA Civil Code Section 17995.1 for 16+ units. Free unit + stipend.</p>
<p><strong>[7] Contract Services:</strong> Tier 4 benchmark at $350/unit. Includes cleaning supplies, maintenance materials, and landscaping.</p>
<p><strong>[8] Administrative &amp; Legal:</strong> Seller actuals for administrative ($4,748) and legal ($3,395). Within benchmark ranges.</p>
<p><strong>[9] LAHD Registration:</strong> RSO registration + SCEP fees. Partially passable to tenants under allowable passthroughs.</p>
<p><strong>[10] Marketing:</strong> $63/unit turnover advertising budget.</p>
<p><strong>[11] Reserves:</strong> $300/unit. Reduced from standard $450 benchmark to reflect recent major capital expenditures (400-amp electrical 2025, 151 windows 2021, solar hot water 2018).</p>
<p><strong>[12] Other:</strong> Permits ($2,023) + California franchise/entity tax ($2,923) + miscellaneous ($2,825).</p>
<p><strong>[13] Management Fee:</strong> 4.0% of EGI for professional third-party management.</p>
</div>
</div>

<!-- SCREEN 3: FINANCIAL SUMMARY -->
<div class="summary-page">
<div class="summary-banner">Summary</div>
<div class="summary-two-col">
<div class="summary-left">
<table class="summary-table">
<thead><tr><th colspan="2" class="summary-header">OPERATING DATA</th></tr></thead>
<tbody>
<tr><td>Price</td><td class="num">${LIST_PRICE:,}</td></tr>
<tr><td>Down Payment ({1-LTV:.0%})</td><td class="num">${AT_LIST['down_payment']:,.0f}</td></tr>
<tr><td>Number of Units</td><td class="num">{UNITS}</td></tr>
<tr><td>Price Per Unit</td><td class="num">${AT_LIST['per_unit']:,.0f}</td></tr>
<tr><td>Price Per SqFt</td><td class="num">${AT_LIST['per_sf']:,.2f}</td></tr>
<tr><td>Gross SqFt</td><td class="num">{SF:,}</td></tr>
<tr><td>Lot Size</td><td class="num">{LOT_SIZE_ACRES} Acres</td></tr>
<tr><td>Approx. Year Built</td><td class="num">1924</td></tr>
</tbody>
</table>
<table class="summary-table">
<thead><tr><th class="summary-header">RETURNS</th><th class="num summary-header">Current</th><th class="num summary-header">Pro Forma</th></tr></thead>
<tbody>
<tr><td>CAP Rate</td><td class="num">{AT_LIST['cur_cap']:.2f}%</td><td class="num">{AT_LIST['pf_cap']:.2f}%</td></tr>
<tr><td>GRM</td><td class="num">{AT_LIST['grm']:.2f}</td><td class="num">{AT_LIST['pf_grm']:.2f}</td></tr>
<tr><td>Cash-on-Cash</td><td class="num">{AT_LIST['coc_cur']:.2f}%</td><td class="num">{AT_LIST['coc_pf']:.2f}%</td></tr>
<tr><td>Debt Coverage Ratio</td><td class="num">{AT_LIST['dcr_cur']:.2f}</td><td class="num">{AT_LIST['dcr_pf']:.2f}</td></tr>
</tbody>
</table>
<table class="summary-table">
<thead><tr><th colspan="2" class="summary-header">FINANCING</th></tr></thead>
<tbody>
<tr><td>Loan Amount</td><td class="num">${AT_LIST['loan_amount']:,.0f}</td></tr>
<tr><td>Loan Type</td><td class="num">New</td></tr>
<tr><td>Interest Rate</td><td class="num">{INTEREST_RATE:.2%}</td></tr>
<tr><td>Amortization</td><td class="num">{AMORTIZATION_YEARS} Years</td></tr>
<tr><td>Loan Constant</td><td class="num">{LOAN_CONSTANT:.4f}</td></tr>
</tbody>
</table>
<table class="summary-table">
<thead><tr><th class="summary-header">UNIT SUMMARY</th><th class="num summary-header">#</th><th class="num summary-header">Avg SF</th><th class="num summary-header">Sched.</th><th class="num summary-header">Market</th></tr></thead>
<tbody>
<tr><td>Studio</td><td class="num">{len(studios)}</td><td class="num">496</td><td class="num">${studio_avg_cur:,.0f}</td><td class="num">${studio_avg_mkt:,.0f}</td></tr>
<tr><td>1 Bed / 1 Bath</td><td class="num">{len(onebd)}</td><td class="num">500</td><td class="num">${onebd_avg_cur:,.0f}</td><td class="num">${onebd_avg_mkt:,.0f}</td></tr>
</tbody>
</table>
</div>
<div class="summary-right">
<table class="summary-table">
<thead><tr><th class="summary-header">INCOME</th><th class="num summary-header">Current</th><th class="num summary-header">Pro Forma</th></tr></thead>
<tbody>
<tr><td>Gross Scheduled Rent</td><td class="num">${GSR:,}</td><td class="num">${PF_GSR:,}</td></tr>
<tr><td>Less: Vacancy (5%)</td><td class="num">(${GSR * VACANCY_PCT:,.0f})</td><td class="num">(${PF_GSR * VACANCY_PCT:,.0f})</td></tr>
<tr><td>Effective Rental Income</td><td class="num">${GSR * (1-VACANCY_PCT):,.0f}</td><td class="num">${PF_GSR * (1-VACANCY_PCT):,.0f}</td></tr>
<tr><td>Other Income</td><td class="num">${OTHER_INCOME:,}</td><td class="num">${OTHER_INCOME:,}</td></tr>
<tr class="summary"><td><strong>Effective Gross Income</strong></td><td class="num"><strong>${AT_LIST['cur_egi']:,.0f}</strong></td><td class="num"><strong>${AT_LIST['pf_egi']:,.0f}</strong></td></tr>
</tbody>
</table>
<table class="summary-table">
<thead><tr><th class="summary-header">CASH FLOW</th><th class="num summary-header">Current</th><th class="num summary-header">Pro Forma</th></tr></thead>
<tbody>
<tr><td>Net Operating Income</td><td class="num">${AT_LIST['cur_noi']:,.0f}</td><td class="num">${AT_LIST['pf_noi']:,.0f}</td></tr>
<tr><td>Less: Debt Service</td><td class="num">(${AT_LIST['debt_service']:,.0f})</td><td class="num">(${AT_LIST['debt_service']:,.0f})</td></tr>
<tr><td>Net Cash Flow</td><td class="num">${AT_LIST['net_cf_cur']:,.0f}</td><td class="num">${AT_LIST['net_cf_pf']:,.0f}</td></tr>
<tr><td>Cash-on-Cash Return</td><td class="num">{AT_LIST['coc_cur']:.2f}%</td><td class="num">{AT_LIST['coc_pf']:.2f}%</td></tr>
<tr><td>Principal Reduction (Yr 1)</td><td class="num" colspan="2">${AT_LIST['prin_red']:,.0f}</td></tr>
<tr class="summary"><td><strong>Total Return (Yr 1)</strong></td><td class="num"><strong>{AT_LIST['total_return_pct_cur']:.2f}%</strong></td><td class="num"><strong>{AT_LIST['total_return_pct_pf']:.2f}%</strong></td></tr>
</tbody>
</table>
<table class="summary-table">
<thead><tr><th class="summary-header">EXPENSES</th><th class="num summary-header">Current</th><th class="num summary-header">Pro Forma</th></tr></thead>
<tbody>
{sum_expense_html}<tr class="summary"><td><strong>Total Expenses</strong></td><td class="num"><strong>${AT_LIST['cur_exp']:,.0f}</strong></td><td class="num"><strong>${AT_LIST['pf_exp']:,.0f}</strong></td></tr>
<tr><td>Expenses as % of EGI</td><td class="num">{AT_LIST['cur_exp']/AT_LIST['cur_egi']*100:.1f}%</td><td class="num">{AT_LIST['pf_exp']/AT_LIST['pf_egi']*100:.1f}%</td></tr>
<tr><td>Expenses / Unit</td><td class="num">${AT_LIST['cur_exp']/UNITS:,.0f}</td><td class="num">${AT_LIST['pf_exp']/UNITS:,.0f}</td></tr>
</tbody>
</table>
</div>
</div>
</div>

<!-- SCREEN 4: PRICE REVEAL + PRICING MATRIX -->
<div class="price-reveal">
<div style="text-align:center; margin-bottom:32px;">
<div style="font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#C5A258; font-weight:600; margin-bottom:8px;">Suggested List Price</div>
<div style="font-size:56px; font-weight:700; color:#1B3A5C; line-height:1;">${LIST_PRICE:,}</div>
</div>
<div class="metrics-grid metrics-grid-4">
<div class="metric-card"><span class="metric-value">${AT_LIST['per_unit']:,.0f}</span><span class="metric-label">Price Per Unit</span></div>
<div class="metric-card"><span class="metric-value">${AT_LIST['per_sf']:,.0f}</span><span class="metric-label">Price Per SF</span></div>
<div class="metric-card"><span class="metric-value">{AT_LIST['cur_cap']:.2f}%</span><span class="metric-label">Current Cap Rate</span></div>
<div class="metric-card"><span class="metric-value">{AT_LIST['grm']:.2f}</span><span class="metric-label">Current GRM</span></div>
</div>
<h3 class="sub-heading">Pricing Matrix</h3>
<p style="font-size:12px;color:#666;margin-bottom:12px;"><em>Highlighted row represents the suggested list price. Property taxes recalculated at 1.21% of each purchase price, which adjusts NOI and cap rate at every row.</em></p>
<div class="table-scroll"><table>
<thead><tr><th class="num">Purchase Price</th><th class="num">Current Cap</th><th class="num">Pro Forma Cap</th><th class="num">Cash-on-Cash</th><th class="num">$/SF</th><th class="num">$/Unit</th><th class="num">PF GRM</th></tr></thead>
<tbody>{matrix_html}</tbody>
</table></div>

<div class="summary-trade-range">
<div class="summary-trade-label">A TRADE PRICE IN THE CURRENT INVESTMENT ENVIRONMENT OF</div>
<div class="summary-trade-prices">$2,900,000 &mdash; $3,100,000</div>
</div>

<h3 class="sub-heading">Pricing Rationale</h3>
<p>The suggested list price of <strong>$3,200,000</strong> ($100,000 per unit) is anchored primarily by comparable sales in the Boyle Heights submarket. The most comparable closed sale - 223 N Breed St, a nearly identical 32-studio building that traded in January 2026 at $87,344 per unit - serves as the pricing floor. The subject commands a 15% premium over Breed due to completed capital improvements ($400,000+ in electrical, windows, solar, and HVAC), superior occupancy (94% vs 78%), entitled ADUs (Planning Commission approved December 2024), and separately metered electric. This premium is further supported by 301 S Boyle Ave at $112,037 per unit (same street, larger units) and the median non-distressed sale price of $121,742 per unit.</p>
<p>The expected sale range of $2,900,000 to $3,100,000 accounts for the 10-15% negotiating discount that is standard in this submarket, where the average sale price-to-list price ratio among non-distressed comps is 87%. The pricing is further contextualized by the on-market benchmark at 124 N Westmoreland Ave in Koreatown - a 30-unit, all-studio, 1927-built RSO building asking $145,000 per unit, with broker intel indicating an expected trade at approximately $123,000 per unit. Applying a 15-20% Boyle Heights location discount yields $98,000 to $105,000 per unit, consistent with the suggested list of $100,000 per unit.</p>

<div class="condition-note"><strong>Assumptions &amp; Conditions:</strong> Financing terms are estimates and subject to change; contact your Marcus &amp; Millichap Capital Corporation representative. Vacancy modeled at 5.0%. Management fee of 4.0% of EGI reflects third-party professional management. Real estate taxes estimated at 1.21% of sale price reflecting Proposition 13 reassessment at close of escrow. Operating reserves at $300/unit reduced for recent capital expenditures. Pro forma rents at $1,625/month moderate scenario per rent comp survey. All information believed reliable but not guaranteed; buyer to verify independently.</div>
</div>

</div>
""")

# ==================== FOOTER ====================
html_parts.append(f"""
<div class="footer" id="contact">
<img src="{IMG['logo']}" class="footer-logo" alt="LAAA Team">
<div class="footer-team">
<div class="footer-person">
<img src="{IMG['glen']}" class="footer-headshot" alt="Glen Scher">
<div class="footer-name">Glen Scher</div>
<div class="footer-title">Senior Managing Director Investments</div>
<div class="footer-contact"><a href="tel:8182122808">(818) 212-2808</a><br><a href="mailto:Glen.Scher@marcusmillichap.com">Glen.Scher@marcusmillichap.com</a><br>CA License: 01962976</div>
</div>
<div class="footer-person">
<img src="{IMG['filip']}" class="footer-headshot" alt="Filip Niculete">
<div class="footer-name">Filip Niculete</div>
<div class="footer-title">Senior Managing Director Investments</div>
<div class="footer-contact"><a href="tel:8182122748">(818) 212-2748</a><br><a href="mailto:Filip.Niculete@marcusmillichap.com">Filip.Niculete@marcusmillichap.com</a><br>CA License: 01905352</div>
</div>
</div>
<div class="footer-office">16830 Ventura Blvd, Ste. 100, Encino, CA 91436 | marcusmillichap.com/laaa-team</div>
<div class="footer-disclaimer">This information has been secured from sources we believe to be reliable, but we make no representations or warranties, expressed or implied, as to the accuracy of the information. Buyer must verify the information and bears all risk for any inaccuracies. Marcus &amp; Millichap Real Estate Investment Services, Inc. | License: CA 01930580.</div>
</div>
""")

# ==================== JAVASCRIPT ====================
html_parts.append(f"""
<script>
var params = new URLSearchParams(window.location.search);
var client = params.get('client');
if (client) {{ var el = document.getElementById('client-greeting'); if (el) el.textContent = 'Prepared Exclusively for ' + client; }}
document.querySelectorAll('.toc-nav a').forEach(function(link) {{ link.addEventListener('click', function(e) {{ e.preventDefault(); var target = document.querySelector(this.getAttribute('href')); if (target) {{ var navHeight = document.getElementById('toc-nav').offsetHeight; var targetPos = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 4; window.scrollTo({{ top: targetPos, behavior: 'smooth' }}); }} }}); }});
var tocLinks = document.querySelectorAll('.toc-nav a'); var tocSections = []; tocLinks.forEach(function(link) {{ var id = link.getAttribute('href').substring(1); var section = document.getElementById(id); if (section) tocSections.push({{ link: link, section: section }}); }});
function updateActiveTocLink() {{ var navHeight = document.getElementById('toc-nav').offsetHeight + 20; var scrollPos = window.pageYOffset + navHeight; var current = null; tocSections.forEach(function(item) {{ if (item.section.offsetTop <= scrollPos) current = item.link; }}); tocLinks.forEach(function(link) {{ link.classList.remove('toc-active'); }}); if (current) current.classList.add('toc-active'); }}
window.addEventListener('scroll', updateActiveTocLink); updateActiveTocLink();
{sale_map_js}
{active_map_js}
{rent_map_js}
</script>
""")

# ============================================================
# RAG CHATBOT
# ============================================================
if ENABLE_CHATBOT:
    try:
        from rag_pipeline import (
            run_rag_pipeline, generate_chat_widget, capture_build_context
        )
        build_data = {
            "property_name": "409 S Boyle Ave, Los Angeles, CA 90033",
            "list_price": LIST_PRICE,
            "units": UNITS,
            "sf": SF,
            "rent_roll": RENT_ROLL,
            "sale_comps": SALE_COMPS,
            "financial_summary": (
                f"Property: 409 S Boyle Ave, Los Angeles, CA 90033\n"
                f"List Price: ${LIST_PRICE:,.0f}\n"
                f"Units: {UNITS}\n"
                f"Square Footage: {SF:,.0f} SF\n"
                f"Current NOI: ${CUR_NOI_AT_LIST:,.0f}\n"
                f"Pro Forma NOI: ${PF_NOI_AT_LIST:,.0f}\n"
                f"Current Cap Rate: {AT_LIST['cur_cap']:.2f}%\n"
                f"GRM: {AT_LIST['grm']:.2f}x\n"
                f"Price Per Unit: ${LIST_PRICE // UNITS:,.0f}\n"
            ),
            "operating_statement": (
                f"Operating Statement:\n"
                f"Gross Scheduled Rent: ${GSR:,.0f}\n"
                f"Less Vacancy (5%): -${GSR * VACANCY_PCT:,.0f}\n"
                f"Other Income: ${OTHER_INCOME:,.0f}\n"
                f"Effective Gross Income: ${CUR_EGI:,.0f}\n"
                f"Total Expenses: ${CUR_TOTAL_EXP:,.0f}\n"
                f"Net Operating Income: ${CUR_NOI_AT_LIST:,.0f}\n"
            ),
            "sections": {},
        }
        docs_dir = os.path.join(SCRIPT_DIR, "docs")
        chunks, vectors = run_rag_pipeline(
            docs_dir=docs_dir, namespace=BOV_NAMESPACE,
            build_data=build_data, verbose=True,
        )
        chat_html = generate_chat_widget(
            worker_url=CHAT_WORKER_URL, namespace=BOV_NAMESPACE,
            property_name=PROPERTY_DISPLAY_NAME,
            starter_questions=STARTER_QUESTIONS,
        )
        html_parts.append(chat_html)
        print(f"Chat widget injected for namespace: {BOV_NAMESPACE}")
    except ImportError as e:
        print(f"\nWARNING: RAG dependencies not installed ({e}).")
        print("Building without chatbot. Install with: pip install -r requirements.txt")
    except Exception as e:
        print(f"\nWARNING: RAG pipeline failed ({e}).")
        print("Building without chatbot. Check your .env API keys and try again.")

html_parts.append("</body></html>")

# Write output
html = "".join(html_parts)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nBOV generated: {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT) / 1024 / 1024:.2f} MB")
print("Done!")
