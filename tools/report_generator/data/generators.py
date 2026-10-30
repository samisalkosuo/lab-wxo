"""Synthetic parameter generator functions and data lists for report generation tools.

Preserves exact data lists and generation logic from local/report-generator.py.
"""

from datetime import datetime, timedelta
import random

municipalities = [
    "Alajärvi", "Alavieska", "Alavus", "Asikkala", "Askola", "Aura", "Akaa", "Brändö", "Eckerö", "Enonkoski",
    "Enontekiö", "Espoo", "Eura", "Eurajoki", "Evijärvi", "Finström", "Forssa", "Föglö", "Geta", "Haapajärvi",
    "Haapavesi", "Hailuoto", "Halsua", "Hamina", "Hammarland", "Hankasalmi", "Hanko", "Harjavalta", "Hartola",
    "Hattula", "Hausjärvi", "Heinävesi", "Helsinki", "Vantaa", "Hirvensalmi", "Hollola", "Huittinen", "Humppila",
    "Hyrynsalmi", "Hyvinkää", "Hämeenkyrö", "Hämeenlinna", "Heinola", "Ii", "Iisalmi", "Iitti", "Ikaalinen",
    "Ilmajoki", "Ilomantsi", "Inari", "Inkoo", "Isojoki", "Isokyrö", "Imatra", "Janakkala", "Joensuu", "Jokioinen",
    "Jomala", "Joroinen", "Joutsa", "Juuka", "Juupajoki", "Juva", "Jyväskylä", "Jämijärvi", "Jämsä", "Järvenpää",
    "Kaarina", "Kaavi", "Kajaani", "Kalajoki", "Kangasala", "Kangasniemi", "Kankaanpää", "Kannonkoski", "Kannus",
    "Karijoki", "Karkkila", "Karstula", "Karvia", "Kaskinen", "Kauhajoki", "Kauhava", "Kauniainen", "Kaustinen",
    "Keitele", "Kemi", "Keminmaa", "Kempele", "Kerava", "Keuruu", "Kihniö", "Kinnula", "Kirkkonummi", "Kitee",
    "Kittilä", "Kiuruvesi", "Kivijärvi", "Kokemäki", "Kokkola", "Kolari", "Konnevesi", "Kontiolahti", "Korsnäs",
    "Koski Tl", "Kotka", "Kouvola", "Kristiinankaupunki", "Kruunupyy", "Kuhmo", "Kuhmoinen", "Kumlinge", "Kuopio",
    "Kuortane", "Kurikka", "Kustavi", "Kuusamo", "Outokumpu", "Kyyjärvi", "Kärkölä", "Kärsämäki", "Kökar",
    "Kemijärvi", "Kemiönsaari", "Lahti", "Laihia", "Laitila", "Lapinlahti", "Lappajärvi", "Lappeenranta",
    "Lapinjärvi", "Lapua", "Laukaa", "Lemi", "Lemland", "Lempäälä", "Leppävirta", "Lestijärvi", "Lieksa", "Lieto",
    "Liminka", "Liperi", "Loimaa", "Loppi", "Loviisa", "Luhanka", "Lumijoki", "Lumparland", "Luoto", "Luumäki",
    "Lohja", "Parainen", "Maalahti", "Maarianhamina", "Marttila", "Masku", "Merijärvi", "Merikarvia", "Miehikkälä",
    "Mikkeli", "Muhos", "Multia", "Muonio", "Mustasaari", "Muurame", "Mynämäki", "Myrskylä", "Mäntsälä",
    "Mäntyharju", "Mänttä-Vilppula", "Naantali", "Nakkila", "Nivala", "Nokia", "Nousiainen", "Nurmes", "Nurmijärvi",
    "Närpiö", "Orimattila", "Oripää", "Orivesi", "Oulainen", "Oulu", "Padasjoki", "Paimio", "Paltamo", "Parikkala",
    "Parkano", "Pelkosenniemi", "Perho", "Petäjävesi", "Pieksämäki", "Pielavesi", "Pietarsaari", "Pedersören kunta",
    "Pihtipudas", "Pirkkala", "Polvijärvi", "Pomarkku", "Pori", "Pornainen", "Posio", "Pudasjärvi", "Pukkila",
    "Punkalaidun", "Puolanka", "Puumala", "Pyhtää", "Pyhäjoki", "Pyhäjärvi", "Pyhäntä", "Pyhäranta", "Pälkäne",
    "Pöytyä", "Porvoo", "Raahe", "Raisio", "Rantasalmi", "Ranua", "Rauma", "Rautalampi", "Rautavaara", "Rautjärvi",
    "Reisjärvi", "Riihimäki", "Ristijärvi", "Rovaniemi", "Ruokolahti", "Ruovesi", "Rusko", "Rääkkylä", "Raasepori",
    "Saarijärvi", "Salla", "Salo", "Saltvik", "Sauvo", "Savitaipale", "Savonlinna", "Savukoski", "Seinäjoki", "Sievi",
    "Siikainen", "Siikajoki", "Siilinjärvi", "Simo", "Sipoo", "Siuntio", "Sodankylä", "Soini", "Somero", "Sonkajärvi",
    "Sotkamo", "Sottunga", "Sulkava", "Sund", "Suomussalmi", "Suonenjoki", "Sysmä", "Säkylä", "Vaala", "Sastamala",
    "Siikalatva", "Taipalsaari", "Taivalkoski", "Taivassalo", "Tammela", "Tampere", "Tervo", "Tervola", "Teuva",
    "Tohmajärvi", "Toholampi", "Toivakka", "Tornio", "Turku", "Pello", "Tuusniemi", "Tuusula", "Tyrnävä", "Ulvila",
    "Urjala", "Utajärvi", "Utsjoki", "Uurainen", "Uusikaarlepyy", "Uusikaupunki", "Vaasa", "Valkeakoski", "Varkaus",
    "Vehmaa", "Vesanto", "Vesilahti", "Veteli", "Vieremä", "Vihti", "Viitasaari", "Vimpeli", "Virolahti", "Virrat",
    "Vårdö", "Vöyri", "Ylitornio", "Ylivieska", "Ylöjärvi", "Ypäjä", "Ähtäri", "Äänekoski",
]


def random_past_date(days_before_now: int) -> str:
    """Returns a random date string in format 'D.M.YYYY' from the past."""
    now = datetime.now()
    start_date = now - timedelta(days=days_before_now)
    random_date = start_date + timedelta(days=random.randint(0, days_before_now))
    return random_date.strftime("%d.%m.%Y")


def random_year(start_year: int) -> int:
    """Returns a random year between start_year and current year."""
    current_year = datetime.now().year
    return random.randint(start_year, current_year)


def get_industry() -> str:
    industries = [
        "Manufacturing", "Healthcare", "Finance", "Retail", "Energy",
        "Telecommunications", "Transportation", "Education", "Government",
        "Pharmaceuticals", "Construction", "Utilities", "Insurance", "Technology",
    ]
    return random.choice(industries)


def get_project_name(industry: str) -> str:
    project_names = {
        "Manufacturing": [
            "Factory Automation Overhaul", "ERP Modernization Program",
            "Smart Supply Chain Deployment", "Lean Manufacturing Initiative",
        ],
        "Healthcare": [
            "Electronic Health Record Migration", "Patient Portal Implementation",
            "Medical Device Integration Rollout", "Hospital Expansion Project",
        ],
        "Finance": [
            "Core Banking Platform Upgrade", "AI-Powered Fraud Detection System",
            "Regulatory Compliance Automation", "Wealth Management Suite Deployment",
        ],
        "Retail": [
            "Omnichannel Sales System Launch", "POS System Replacement",
            "Warehouse Digitization Project", "Customer Loyalty Platform Upgrade",
        ],
        "Energy": [
            "Smart Grid Rollout", "Green Hydrogen Plant Construction",
            "Pipeline Monitoring System Deployment", "Carbon Capture Pilot Project",
        ],
        "Telecommunications": [
            "5G Tower Infrastructure Buildout", "Fiber Network Expansion",
            "Billing System Replacement", "Customer Self-Service Portal Upgrade",
        ],
        "Transportation": [
            "Fleet Management Platform Implementation", "Airport Baggage System Upgrade",
            "Autonomous Vehicle Pilot", "Rail Scheduling Optimization",
        ],
        "Education": [
            "Digital Classroom Initiative", "Student Records Modernization",
            "Learning Analytics Platform Deployment", "Campus WiFi Upgrade",
        ],
        "Government": [
            "Public Records Digitization", "Smart City Infrastructure Pilot",
            "Civic Engagement Platform", "Cybersecurity Modernization Program",
        ],
        "Pharmaceuticals": [
            "Clinical Trial Data Platform", "Regulatory Submissions Portal",
            "Drug Manufacturing Quality System", "Laboratory Equipment Upgrade",
        ],
        "Construction": [
            "High-Rise Residential Project", "Urban Transit Hub Construction",
            "Modular Housing Development", "New Logistics Center Build",
        ],
        "Utilities": [
            "Smart Meter Installation", "Power Grid Resilience Upgrade",
            "Water Treatment Plant Renovation", "Outage Management System Implementation",
        ],
        "Insurance": [
            "Claims Automation Engine", "Policy Admin System Modernization",
            "Risk Modeling Platform Rollout", "Customer Portal Migration",
        ],
        "Technology": [
            "Cloud Migration Project", "AI Recommendation Engine",
            "Enterprise SaaS Platform Development", "DevOps Toolchain Rollout",
        ],
    }
    return random.choice(project_names.get(industry, ["Generic Strategic Initiative"]))


def get_quarter() -> str:
    current_year = datetime.now().year
    year = random.choice(range(current_year - 2, current_year + 1))
    quarter = random.choice(["Q1", "Q2", "Q3", "Q4"])
    return f"{quarter} {year}"


def get_project_stage() -> str:
    stages = [
        "Initiation", "Requirements Gathering", "Design Phase", "Procurement",
        "Implementation", "System Integration", "Testing", "Deployment",
        "Go-Live", "Post-Go-Live Support", "Monitoring & Evaluation", "Project Closure",
    ]
    return random.choice(stages)


def get_primary_blocker(industry: str) -> str:
    common_blockers = {
        "default": [
            "Budget overruns", "Staff turnover", "Regulatory delays",
            "Stakeholder misalignment", "Scope creep", "Vendor delays",
            "Integration issues", "Lack of executive support", "Insufficient training",
            "Late deliverables", "Data quality issues", "Procurement holdup",
        ],
        "Construction": [
            "Weather-related delays", "Permit approval delays", "Equipment shortages",
            "Labor union disputes", "Site contamination discovered",
        ],
        "Healthcare": [
            "EHR integration issues", "HIPAA compliance challenges",
            "Clinical staff resistance", "Device certification delays",
        ],
        "Finance": [
            "Compliance scope changes", "Data privacy concerns",
            "Delayed third-party audits", "Legacy system constraints",
        ],
        "Energy": [
            "Environmental review holdups", "Specialized labor shortage",
            "Permit delays", "Supply chain instability", "On-site safety incidents",
        ],
    }
    blockers = common_blockers.get(industry, []) + common_blockers["default"]
    return random.choice(blockers)


def get_visit_type() -> str:
    visit_types = [
        "Child welfare check",
        "Elderly care follow-up",
        "Domestic violence risk assessment",
        "Post-hospital discharge visit",
        "Substance abuse support visit",
        "Disability support assessment",
        "Foster family evaluation",
        "Homeless outreach visit",
        "Parental capacity evaluation",
        "Routine family wellbeing visit",
        "Mental health monitoring visit",
        "Newborn and infant safety visit",
        "Unaccompanied minor intake assessment",
        "Follow-up on school truancy report",
        "Household financial hardship review",
        "Immigration case monitoring visit",
        "Family reunification progress check",
        "At-risk youth intervention visit",
        "Refugee integration support visit",
        "Domestic relocation follow-up",
        "Emergency housing verification",
        "Post-abuse recovery support visit",
        "Veteran support service check-in",
        "Support plan review meeting",
        "Juvenile probation compliance visit",
        "Social reintegration assessment",
        "Child visitation supervision report",
        "Safety plan monitoring visit",
        "Parenting education follow-up",
        "Youth mentoring program assessment",
    ]
    return random.choice(visit_types)


def get_household_composition() -> str:
    compositions = [
        "Single mother with three children",
        "Elderly couple living independently",
        "Young adult living alone",
        "Single father with one child",
        "Grandparents caring for grandchildren",
        "Married couple with four children",
        "Teenager in foster care",
        "Mother and newborn infant",
        "Two adult siblings sharing housing",
        "Single adult with physical disability",
        "Elderly woman with early dementia symptoms",
        "Separated couple with shared custody",
        "Unaccompanied minor in temporary housing",
        "Family of five in subsidized apartment",
        "Adult living with severe mental health condition",
        "Young couple expecting their first child",
        "Disabled adult and live-in caregiver",
        "Woman recovering from domestic abuse",
        "Teenager with school attendance issues",
        "Immigrant family recently relocated",
        "Parent with substance use disorder and children",
        "Elderly man living with adult daughter",
        "Refugee family in temporary accommodation",
        "Teenage mother and infant living with parents",
        "Rehabilitated ex-offender reintegrating into society",
        "Multi-generational household with financial difficulties",
        "Single adult with intellectual disability",
        "Two-parent household with reported neglect case",
        "Transitional housing residents post-rehabilitation",
        "Family with history of chronic domestic violence",
        "Cohabiting couple with mental health challenges",
        "Single caregiver supporting elderly parent with dementia",
        "Child living with non-custodial relative",
        "Youth aging out of foster system",
        "Blended family with recent custody changes",
    ]
    return random.choice(compositions)


def get_case_severity() -> str:
    severities = ["Low", "Moderate", "High", "Urgent", "Critical"]
    weights = [0.35, 0.35, 0.15, 0.10, 0.05]
    return random.choices(severities, weights=weights, k=1)[0]


def create_doctor_visit_request() -> dict:
    severity_levels = [1, 2, 3, 4, 5]
    patient_gender = ["male", "female"]
    patient_age = list(range(1, 106))
    return {
        "location": random.choice(municipalities),
        "date": random_past_date(730),
        "patient_age": random.choice(patient_age),
        "patient_gender": random.choice(patient_gender),
        "severity": random.choice(severity_levels),
    }


def create_traffic_incident_request() -> dict:
    number_of_vehicles = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                          3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 5, 6, 7, 8, 9, 10, 11]
    time_of_day = ["night", "morning", "day", "evening"]
    weather_conditions = [
        "Clear and sunny", "Overcast", "Light rain", "Heavy rain", "Foggy",
        "Snowy", "Icy roads", "Windy with gusts", "Thunderstorm",
        "Dry but cold", "Wet and slippery", "Mixed snow and rain",
    ]
    return {
        "municipality": random.choice(municipalities),
        "country": "Finland",
        "date": random_past_date(1000),
        "number_of_vehicles": random.choice(number_of_vehicles),
        "time_of_day": random.choice(time_of_day),
        "weather_conditions": random.choice(weather_conditions),
    }


def create_building_inspection_request() -> dict:
    building_type = ["residential", "commercial", "industrial", "public"]
    return {
        "municipality": random.choice(municipalities),
        "country": "Finland",
        "inspection_date": random_past_date(365),
        "construction_year": random_year(1970),
        "building_type": random.choice(building_type),
    }


def create_project_update_request() -> dict:
    industry = get_industry()
    return {
        "industry": industry,
        "quarter": get_quarter(),
        "primary_blocker": get_primary_blocker(industry),
        "project_name": get_project_name(industry),
        "project_stage": get_project_stage(),
    }


def create_social_services_visit_request() -> dict:
    return {
        "municipality": random.choice(municipalities),
        "country": "Finland",
        "date": random_past_date(365),
        "case_severity": get_case_severity(),
        "household_composition": get_household_composition(),
        "visit_type": get_visit_type(),
    }
