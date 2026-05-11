import re
from collections import Counter
from functools import lru_cache


SKILL_CATALOG = {
    "python": "Programming",
    "django": "Backend",
    "flask": "Backend",
    "fastapi": "Backend",
    "javascript": "Frontend",
    "typescript": "Frontend",
    "react": "Frontend",
    "node.js": "Backend",
    "html": "Frontend",
    "css": "Frontend",
    "bootstrap": "Frontend",
    "tailwind": "Frontend",
    "sql": "Database",
    "mysql": "Database",
    "postgresql": "Database",
    "mongodb": "Database",
    "redis": "Database",
    "rest api": "API",
    "graphql": "API",
    "docker": "DevOps",
    "kubernetes": "DevOps",
    "aws": "Cloud",
    "azure": "Cloud",
    "gcp": "Cloud",
    "git": "Tools",
    "github": "Tools",
    "ci/cd": "DevOps",
    "machine learning": "AI",
    "deep learning": "AI",
    "nlp": "AI",
    "natural language processing": "AI",
    "scikit-learn": "AI",
    "sklearn": "AI",
    "tensorflow": "AI",
    "pytorch": "AI",
    "pandas": "Data",
    "numpy": "Data",
    "matplotlib": "Data",
    "power bi": "Analytics",
    "tableau": "Analytics",
    "excel": "Analytics",
    "data analysis": "Data",
    "data visualization": "Data",
    "agile": "Process",
    "scrum": "Process",
    "unit testing": "Testing",
    "pytest": "Testing",
    "selenium": "Testing",
    "api testing": "Testing",
    "communication": "Soft Skill",
    "leadership": "Soft Skill",
    "problem solving": "Soft Skill",
}

SECTION_ALIASES = {
    "summary": ["summary", "profile", "objective"],
    "skills": ["skills", "technical skills", "core skills"],
    "experience": ["experience", "work experience", "employment", "projects"],
    "education": ["education", "academic"],
}

STOP_WORDS = {
    "and",
    "or",
    "the",
    "with",
    "for",
    "from",
    "this",
    "that",
    "you",
    "your",
    "will",
    "are",
    "our",
    "have",
    "has",
    "into",
    "using",
    "work",
    "team",
    "role",
    "job",
    "candidate",
    "experience",
}


def extract_skills(text: str) -> list[str]:
    normalized_text = _normalize(text)
    found = set()
    for skill in SKILL_CATALOG:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, normalized_text):
            found.add(_canonical_skill(skill))
    return sorted(found)


def extract_education(text: str) -> list[str]:
    degree_patterns = [
        r"\b(b\.?tech|bachelor(?:'s)?|bsc|bs|be)\b[^.|\n]{0,90}",
        r"\b(m\.?tech|master(?:'s)?|msc|ms|me|mba)\b[^.|\n]{0,90}",
        r"\b(ph\.?d|doctorate)\b[^.|\n]{0,90}",
        r"\b(diploma|certification|certificate)\b[^.|\n]{0,90}",
    ]
    matches = []
    for pattern in degree_patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    if not matches:
        return []

    snippets = []
    for pattern in degree_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            snippets.append(_clean_phrase(match.group(0)))
    return sorted(set(snippets))[:6]


def extract_experience_years(text: str) -> float:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience",
        r"experience\s+(?:of\s+)?(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)",
    ]
    values = []
    for pattern in patterns:
        values.extend(float(value) for value in re.findall(pattern, text, flags=re.IGNORECASE))
    return max(values) if values else 0.0


def extract_keywords(text: str, top_n: int = 25) -> list[str]:
    normalized = _normalize(text)
    tokens = [token for token in _tokens(normalized) if token not in _stop_words()]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=max(top_n * 2, 30),
        )
        matrix = vectorizer.fit_transform([normalized])
        scores = zip(vectorizer.get_feature_names_out(), matrix.toarray()[0])
        ranked = sorted(scores, key=lambda item: item[1], reverse=True)
        return [_clean_phrase(term) for term, score in ranked if score > 0][:top_n]
    except Exception:
        counts = Counter(tokens)
        return [_clean_phrase(term) for term, _ in counts.most_common(top_n)]


def similarity_score(resume_text: str, job_text: str) -> float:
    resume_text = _normalize(resume_text)
    job_text = _normalize(job_text)
    if not resume_text or not job_text:
        return 0.0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([resume_text, job_text])
        return float(cosine_similarity(matrix[0], matrix[1])[0][0])
    except Exception:
        resume_terms = set(resume_text.split())
        job_terms = set(job_text.split())
        union = resume_terms | job_terms
        return len(resume_terms & job_terms) / len(union) if union else 0.0


def section_coverage(text: str) -> dict[str, bool]:
    normalized = _normalize(text)
    coverage = {}
    for section, aliases in SECTION_ALIASES.items():
        coverage[section] = any(alias in normalized for alias in aliases)
    return coverage


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _tokens(text: str) -> list[str]:
    try:
        nlp = _spacy_pipeline()
        document = nlp(text)
        return [
            token.text.lower()
            for token in document
            if not token.is_space and not token.is_punct and len(token.text) > 2
        ]
    except Exception:
        return re.findall(r"[a-z][a-z0-9+#.-]{2,}", text)


@lru_cache(maxsize=1)
def _spacy_pipeline():
    import spacy

    try:
        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except OSError:
        return spacy.blank("en")


@lru_cache(maxsize=1)
def _stop_words() -> set[str]:
    try:
        from nltk.corpus import stopwords

        return STOP_WORDS | set(stopwords.words("english"))
    except Exception:
        return STOP_WORDS


def _canonical_skill(skill: str) -> str:
    aliases = {
        "sklearn": "scikit-learn",
        "natural language processing": "nlp",
    }
    return aliases.get(skill, skill)


def _clean_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" .,-").lower()
