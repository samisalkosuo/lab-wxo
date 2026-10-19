"""Hand-keyed rates from 'Valtion matkustussaanto 2026' (VM julkaisuja 2025:63).

Source: Valtiovarainministerio, CC BY-NC-ND 4.0, https://urn.fi/URN:ISBN:978-952-367-397-7
Only a small subset is keyed here. Every value carries its section reference.
The amounts are valid 1.1.-31.12.2026; amounts for 2027 are agreed separately.
"""

SOURCE_TITLE = "Valtion matkustussääntö 2026"
EFFECTIVE_FROM = "2026-01-01"
EFFECTIVE_UNTIL = "2026-12-31"

# --- Domestic per diem (10 §, 11 §) ---------------------------------------
PARTIAL_PER_DIEM_EUR = 25          # 11 § 1 mom.; trip over 6 h (10 §)
FULL_PER_DIEM_EUR = 54             # 11 § 2 mom.; trip over 10 h (10 §)
PARTIAL_PER_DIEM_MIN_HOURS = 6     # 10 § 1 mom.
FULL_PER_DIEM_MIN_HOURS = 10       # 10 § 2 mom.
PER_DIEM_MIN_DISTANCE_KM = 15      # 9 §

# --- Free meals (13 §) -----------------------------------------------------
FREE_MEAL_REDUCTION = 0.5          # 13 § 1 mom.: per diem reduced by 50 percent
FREE_MEALS_NEEDED_FULL = 2         # 13 § 2 mom.: full per diem needs two meals
FREE_MEALS_NEEDED_PARTIAL = 1      # 13 § 2 mom.: partial per diem needs one meal

# --- Foreign partial-day shares (12 §) -------------------------------------
FOREIGN_SHARE_OVER_2H = 0.35       # over 2 h past last full travel day
FOREIGN_SHARE_OVER_10H = 0.65      # over 10 h past last full travel day

# --- Other allowances ------------------------------------------------------
MEAL_ALLOWANCE_FRACTION = 0.25     # 14 §: one quarter of the full per diem
NIGHT_ALLOWANCE_EUR = 16           # 16 §
TRAVEL_DAY_DOMESTIC_EUR = 55       # 19 §
TRAVEL_DAY_ABROAD_EUR = 150        # 19 §

# --- Mileage, car (6 §) ----------------------------------------------------
CAR_KM_FIRST_BLOCK = 5000
CAR_EUR_PER_KM_FIRST = 0.55
CAR_EUR_PER_KM_AFTER = 0.49

# --- Foreign per diem, subset of the annex (Liite) -------------------------
# key: ISO code -> (Finnish name, English name, amount EUR per full travel day)
FOREIGN_PER_DIEM = {
    "BE": ("Belgia", "Belgium", 81),
    "DE": ("Saksa", "Germany", 78),
    "SE": ("Ruotsi", "Sweden", 70),
    "EE": ("Viro", "Estonia", 82),
    "US": ("Yhdysvallat", "United States", 86),
    "GB": ("Britannia", "United Kingdom", 84),
    "FR": ("Ranska", "France", 80),
    "NO": ("Norja", "Norway", 72),
}

# Extra names accepted by the lookup (lower case)
COUNTRY_ALIASES = {
    "belgia": "BE", "belgium": "BE", "bryssel": "BE", "brussels": "BE",
    "saksa": "DE", "germany": "DE", "berliini": "DE", "berlin": "DE",
    "frankfurt": "DE",
    "ruotsi": "SE", "sweden": "SE", "tukholma": "SE", "stockholm": "SE",
    "viro": "EE", "estonia": "EE", "tallinna": "EE", "tallinn": "EE",
    "yhdysvallat": "US", "usa": "US", "united states": "US",
    "britannia": "GB", "uk": "GB", "united kingdom": "GB", "iso-britannia": "GB",
    "ranska": "FR", "france": "FR",
    "norja": "NO", "norway": "NO",
}

# Section references by topic, used in tool output so the agent need not guess.
SECTION_REFS = {
    "partial_per_diem": "11 § 1 mom.; 10 § 1 mom.",
    "full_per_diem": "11 § 2 mom.; 10 § 2 mom.",
    "per_diem_distance": "9 §",
    "free_meals": "13 §",
    "foreign_per_diem": "12 § ja liite (Ulkomaanpäivärahakorvaukset vuodelle 2026)",
    "meal_allowance": "14 §",
    "night_allowance": "16 §",
    "travel_day": "19 §",
    "mileage_car": "6 §",
    "travel_mode": "5 §",
    "official_trip": "3 §",
    "leave_combination": "3 § ja 4 §",
    "claim_deadline": "21 §",
}
