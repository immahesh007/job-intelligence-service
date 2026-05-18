"""Skill alias mapping — normalizes variant spellings to canonical names.

This is the authoritative alias map shared by the skill extractor and the matching engine.
"""

# Mapping: variant → canonical
SKILL_ALIASES: dict[str, str] = {
    # Short forms → full
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "go": "go",
    "golang": "go",
    "rb": "ruby",
    "kt": "kotlin",
    "sw": "swift",
    "rs": "rust",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    "objc": "objective-c",
    "obj-c": "objective-c",

    # DevOps / cloud
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "cloud": "cloud computing",

    # Frameworks
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "next.js": "next.js",
    "nextjs": "next.js",
    "nuxt.js": "nuxt",
    "nuxtjs": "nuxt",
    "fast api": "fastapi",
    "express.js": "express",
    "expressjs": "express",
    "node.js": "node.js",
    "nodejs": "node.js",
    "node": "node.js",
    ".net": ".net",
    "dotnet": ".net",
    "asp.net": "asp.net",
    "aspnet": "asp.net",
    "ruby on rails": "rails",
    "ror": "rails",
    "spring boot": "spring",
    "spring framework": "spring",
    "flask": "flask",
    "django": "django",

    # ML / Data
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "cv": "computer vision",
    "computer vision": "computer vision",
    "llm": "large language model",
    "large language model": "large language model",
    "llms": "large language model",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "generative ai": "generative ai",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "dl": "deep learning",

    # Databases
    "pg": "postgresql",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "es": "elasticsearch",
    "elastic": "elasticsearch",
    "ddb": "dynamodb",
    "dynamo": "dynamodb",
    "cdb": "cockroachdb",
    "cockroach": "cockroachdb",
    "snow": "snowflake",
    "bq": "bigquery",
    "ch": "clickhouse",

    # Tools
    "tf": "terraform",
    "terraform": "terraform",
    "gh actions": "github actions",
    "github actions": "github actions",
    "glab": "gitlab ci",
    "gitlab": "gitlab",
    "bitbucket": "bitbucket",
    "jira": "jira",

    # Concepts
    "microservices": "microservices",
    "micro service": "microservices",
    "micro-services": "microservices",
    "event driven": "event driven",
    "event-driven": "event driven",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "rest": "rest api",
    "restful": "rest api",
    "grpc": "grpc",
    "graphql": "graphql",
    "oauth": "oauth",
    "oauth2": "oauth",
    "jwt": "jwt",
    "tdd": "tdd",
    "bdd": "bdd",
    "ddd": "domain driven design",
    "domain driven design": "domain driven design",

    # Mobile
    "rn": "react native",
    "react-native": "react native",
    "ios": "ios",
    "android": "android",

    # Other
    "sdet": "test automation",
    "qa": "test automation",
    "quality assurance": "test automation",
    "devops": "devops",
    "dev ops": "devops",
    "sre": "site reliability engineering",
    "site reliability": "site reliability engineering",
    "platform engineering": "platform engineering",
    "dx": "developer experience",
    "devx": "developer experience",
    "developer experience": "developer experience",
    "ux": "user experience",
    "user experience": "user experience",
    "ui": "user interface",
    "scm": "supply chain management",
    "gitops": "gitops",

    # Senior / role aliases
    "sde": "software engineer",
    "swe": "software engineer",
    "software developer": "software engineer",
    "software development engineer": "software engineer",
    "backend engineer": "backend developer",
    "back end engineer": "backend developer",
    "backend developer": "backend developer",
    "back-end developer": "backend developer",
    "frontend engineer": "frontend developer",
    "front end engineer": "frontend developer",
    "frontend developer": "frontend developer",
    "front-end developer": "frontend developer",
    "fullstack engineer": "fullstack developer",
    "full stack engineer": "fullstack developer",
    "fullstack developer": "fullstack developer",
    "full-stack developer": "fullstack developer",
    "ml engineer": "machine learning engineer",
    "ml ops": "mlops",
    "mlops": "mlops",
    "data engineer": "data engineer",
    "data scientist": "data scientist",
    "devops engineer": "devops engineer",
    "platform engineer": "platform engineer",
    "security engineer": "security engineer",
    "appsec": "application security",
    "infosec": "information security",
    "netsec": "network security",
}


def resolve_skill(name: str) -> str:
    """Return the canonical name for a skill, lowercased."""
    key = name.lower().strip()
    return SKILL_ALIASES.get(key, key)


def normalize_skill_set(skills: list[str]) -> set[str]:
    """Normalize a list of skill strings to canonical names."""
    return {resolve_skill(s) for s in skills}


def is_skill_match(candidate_skill: str, job_skill: str) -> bool:
    """Check if two skills match after normalization."""
    return resolve_skill(candidate_skill) == resolve_skill(job_skill)
