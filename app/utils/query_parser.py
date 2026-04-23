"""
Rule-based natural language query parser.
No AI/LLMs — pure keyword/pattern matching.
"""

import re

# ---------------------------------------------------------------------------
# Country name → ISO 3166-1 alpha-2
# Includes common aliases, adjectives, and demonyms
# ---------------------------------------------------------------------------
COUNTRY_MAP = {
    # Africa
    "tanzania": "TZ", "tanzanian": "TZ",
    "nigeria": "NG", "nigerian": "NG",
    "uganda": "UG", "ugandan": "UG",
    "sudan": "SD", "sudanese": "SD",
    "madagascar": "MG", "malagasy": "MG",
    "mozambique": "MZ", "mozambican": "MZ",
    "south africa": "ZA", "south african": "ZA",
    "mali": "ML", "malian": "ML",
    "angola": "AO", "angolan": "AO",
    "kenya": "KE", "kenyan": "KE",
    "zambia": "ZM", "zambian": "ZM",
    "namibia": "NA", "namibian": "NA",
    "dr congo": "CD", "democratic republic of congo": "CD",
    "democratic republic of the congo": "CD", "drc": "CD", "congolese": "CD",
    "republic of the congo": "CG", "congo": "CG",
    "gabon": "GA", "gabonese": "GA",
    "rwanda": "RW", "rwandan": "RW",
    "senegal": "SN", "senegalese": "SN",
    "ethiopia": "ET", "ethiopian": "ET",
    "morocco": "MA", "moroccan": "MA",
    "malawi": "MW", "malawian": "MW",
    "ghana": "GH", "ghanaian": "GH",
    "benin": "BJ", "beninese": "BJ",
    "zimbabwe": "ZW", "zimbabwean": "ZW",
    "egypt": "EG", "egyptian": "EG",
    "eritrea": "ER", "eritrean": "ER",
    "burundi": "BI", "burundian": "BI",
    "liberia": "LR", "liberian": "LR",
    "gambia": "GM", "gambian": "GM", "the gambia": "GM",
    "burkina faso": "BF", "burkinabe": "BF",
    "mauritania": "MR", "mauritanian": "MR",
    "somalia": "SO", "somali": "SO", "somalian": "SO",
    "botswana": "BW", "botswanan": "BW", "motswana": "BW",
    "ivory coast": "CI", "ivorian": "CI",
    "cote d'ivoire": "CI", "côte d'ivoire": "CI",
    "western sahara": "EH",
    "cape verde": "CV", "cabo verde": "CV", "cape verdean": "CV",
    "cameroon": "CM", "cameroonian": "CM",
    # Rest of world
    "united states": "US", "usa": "US", "america": "US", "american": "US",
    "united kingdom": "GB", "uk": "GB", "britain": "GB", "british": "GB",
    "england": "GB", "english": "GB",
    "india": "IN", "indian": "IN",
    "france": "FR", "french": "FR",
    "brazil": "BR", "brazilian": "BR",
    "tunisia": "TN", "tunisian": "TN",
    "australia": "AU", "australian": "AU",
    "canada": "CA", "canadian": "CA",
    "china": "CN", "chinese": "CN",
}

# ---------------------------------------------------------------------------
# Age group keywords
# ---------------------------------------------------------------------------
AGE_GROUP_MAP = {
    "child": "child", "children": "child", "kid": "child", "kids": "child",
    "toddler": "child", "toddlers": "child", "infant": "child", "infants": "child",
    "teenager": "teenager", "teenagers": "teenager",
    "teen": "teenager", "teens": "teenager",
    "adolescent": "teenager", "adolescents": "teenager",
    "adult": "adult", "adults": "adult", "grown up": "adult", "grown-up": "adult",
    "senior": "senior", "seniors": "senior",
    "elderly": "senior", "elder": "senior", "elders": "senior",
    "old": "senior", "aged": "senior",
}

# "young" is special — maps to age range 16–24, not a stored age_group
YOUNG_SYNONYMS = {"young", "youth", "youths", "youthful", "juvenile", "juveniles"}

# ---------------------------------------------------------------------------
# Gender keywords
# ---------------------------------------------------------------------------
GENDER_MAP = {
    "male": "male", "males": "male", "man": "male", "men": "male",
    "boy": "male", "boys": "male", "gentleman": "male", "gentlemen": "male",
    "guy": "male", "guys": "male", "lad": "male", "lads": "male",
    "female": "female", "females": "female", "woman": "female", "women": "female",
    "girl": "female", "girls": "female", "lady": "female", "ladies": "female",
    "gal": "female", "gals": "female",
}

# Phrases that mean "both genders" → skip gender filter
BOTH_GENDER_PATTERNS = [
    r"\bmale and female\b", r"\bfemale and male\b",
    r"\bboth genders?\b", r"\ball genders?\b",
    r"\beveryone\b", r"\beverybody\b", r"\bpeople\b",
    r"\bindividuals?\b", r"\bpersons?\b",
]

# ---------------------------------------------------------------------------
# Age range descriptors → (min_age, max_age)
# ---------------------------------------------------------------------------
AGE_DESCRIPTOR_MAP = {
    # young already handled separately
    "middle.aged": (35, 55), "middle age": (35, 55),
    "newborn": (0, 1), "newborns": (0, 1),
    "toddler": (1, 4), "toddlers": (1, 4),
    "school.age": (5, 12), "school age": (5, 12),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_noise(q: str) -> str:
    """Remove filler words that don't carry filter meaning."""
    noise = r"\b(and|or|the|a|an|from|in|of|who|that|are|is|with|aged?|age|between|to|show|me|find|get|list|give|all|some|any)\b"
    return re.sub(noise, " ", q)


def _extract_country(q: str) -> tuple[str | None, str]:
    """Longest-match country extraction. Returns (country_id | None, cleaned_q)."""
    for name in sorted(COUNTRY_MAP, key=len, reverse=True):
        pattern = rf"\b{re.escape(name)}\b"
        if re.search(pattern, q):
            return COUNTRY_MAP[name], re.sub(pattern, " ", q)
    return None, q


def _extract_age_range(q: str) -> tuple[int | None, int | None]:
    """
    Handles patterns like:
      above/over/older than N
      below/under/younger than N
      between N and M  /  N to M  /  N-M
      aged N
    """
    min_age = max_age = None

    # between N and M
    m = re.search(r"between\s+(\d+)\s+(?:and|to|-)\s+(\d+)", q)
    if m:
        min_age, max_age = int(m.group(1)), int(m.group(2))
        return min_age, max_age

    # N-M (bare range like 20-30)
    m = re.search(r"\b(\d{1,3})\s*[-–]\s*(\d{1,3})\b", q)
    if m:
        min_age, max_age = int(m.group(1)), int(m.group(2))
        return min_age, max_age

    # above / over / older than N
    m = re.search(r"\b(?:above|over|older\s+than|at\s+least)\s+(\d+)", q)
    if m:
        min_age = int(m.group(1))

    # below / under / younger than N
    m = re.search(r"\b(?:below|under|younger\s+than|at\s+most|less\s+than)\s+(\d+)", q)
    if m:
        max_age = int(m.group(1))

    # aged N (exact age → treat as min=max)
    m = re.search(r"\baged?\s+(\d+)\b", q)
    if m and min_age is None and max_age is None:
        min_age = max_age = int(m.group(1))

    return min_age, max_age


def _extract_gender(q: str) -> str | None:
    """Returns 'male', 'female', or None (ambiguous/both)."""
    for pattern in BOTH_GENDER_PATTERNS:
        if re.search(pattern, q):
            return None  # explicit both → no filter

    found = set()
    for keyword, gender in GENDER_MAP.items():
        if re.search(rf"\b{re.escape(keyword)}\b", q):
            found.add(gender)

    if len(found) == 1:
        return found.pop()
    return None  # 0 or 2 → no filter


def _extract_age_group(q: str) -> str | None:
    for keyword, group in AGE_GROUP_MAP.items():
        if re.search(rf"\b{re.escape(keyword)}\b", q):
            return group
    return None


def _extract_age_descriptor(q: str) -> tuple[int | None, int | None]:
    for keyword, (lo, hi) in AGE_DESCRIPTOR_MAP.items():
        if re.search(rf"\b{re.escape(keyword)}\b", q):
            return lo, hi
    return None, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_query(q: str) -> dict | None:
    """
    Parse a plain-English query into filter kwargs.
    Returns None if nothing interpretable was found.
    """
    if not q or not q.strip():
        return None

    original = q.strip().lower()

    # --- Country (before stripping noise, needs full phrase matching) ---
    country_id, working = _extract_country(original)

    # --- Strip noise words ---
    working = _strip_noise(working)
    working = re.sub(r"\s+", " ", working).strip()

    filters: dict = {}

    if country_id:
        filters["country_id"] = country_id

    # --- Age range from explicit numeric patterns ---
    min_age, max_age = _extract_age_range(working)

    # --- "young" / youth → 16–24 (only if no numeric range already) ---
    if min_age is None and max_age is None:
        for syn in YOUNG_SYNONYMS:
            if re.search(rf"\b{syn}\b", working):
                min_age, max_age = 16, 24
                break

    # --- Age descriptor phrases (middle-aged, toddler, etc.) ---
    if min_age is None and max_age is None:
        min_age, max_age = _extract_age_descriptor(working)

    if min_age is not None:
        filters["min_age"] = min_age
    if max_age is not None:
        filters["max_age"] = max_age

    # --- Age group ---
    age_group = _extract_age_group(working)
    if age_group:
        filters["age_group"] = age_group

    # --- Gender ---
    gender = _extract_gender(working)
    if gender:
        filters["gender"] = gender

    return filters if filters else None
