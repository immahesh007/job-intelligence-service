import re

from app.services.matching.taxonomy.aliases import SKILL_ALIASES, resolve_skill as _resolve_from_taxonomy

# ---------------------------------------------------------------------------
# Skills taxonomy — grouped by category for readability
# ---------------------------------------------------------------------------

_SKILL_CATEGORIES: dict[str, set[str]] = {
    "languages": {
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "ruby", "php", "swift", "kotlin", "scala", "dart",
        "perl", "r", "matlab", "lua", "groovy", "bash", "shell",
        "powershell", "elixir", "clojure", "haskell", "erlang", "f#",
        "objective-c", "c", "assembly", "fortran", "cobol", "apex",
    },
    "web_frameworks": {
        "react", "react.js", "angular", "vue", "vue.js", "svelte", "next.js",
        "nuxt", "gatsby", "redux", "jquery", "django", "flask", "fastapi",
        "spring", "spring boot", "express", "express.js", "nestjs", "laravel",
        "rails", "ruby on rails", "phoenix", "gin", ".net", "asp.net",
        "blazor", "node.js", "deno", "bun", "htmx", "alpine.js",
        "tailwind", "bootstrap", "material-ui", "chakra", "ant design",
        "graphql", "rest", "grpc", "websocket", "soap",
    },
    "cloud_devops": {
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "kubernetes", "k8s", "docker", "terraform", "ansible", "puppet",
        "chef", "jenkins", "github actions", "gitlab ci", "circleci",
        "argocd", "prometheus", "grafana", "datadog", "splunk", "elk",
        "nginx", "apache", "haproxy", "cloudflare", "helm", "istio", "envoy",
        "openshift", "serverless", "lambda", "cloudformation", "pulumi",
        "travis ci", "teamcity", "bamboo", "octopus deploy", "vault",
        "consul", "packer", "vagrant",
    },
    "databases": {
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "cockroachdb", "neo4j",
        "oracle", "sql", "sql server", "mariadb", "couchbase", "firebase",
        "supabase", "snowflake", "bigquery", "redshift", "clickhouse",
        "duckdb", "timescaledb", "scylladb", "couchdb", "rethinkdb",
        "fauna", "planetscale", "vitess",
    },
    "data_ml": {
        "spark", "hadoop", "airflow", "dbt", "kafka", "rabbitmq",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "tableau", "looker", "power bi", "metabase", "jupyter",
        "mlflow", "kubeflow", "dagster", "prefect", "hive", "presto",
        "trino", "flink", "beam", "emr", "glue", "sqs", "sns", "s3",
        "ml", "machine learning", "deep learning", "nlp", "computer vision",
        "llm", "large language model", "generative ai", "langchain",
        "llamaindex", "vector database", "pinecone", "weaviate", "chromadb",
        "embeddings", "rag", "stable diffusion", "hugging face",
        "gradient boosting", "xgboost", "lightgbm", "random forest",
        "neural network", "cnn", "rnn", "lstm", "transformer",
        "nltk", "spacy", "opencv", "scipy", "matplotlib", "seaborn",
        "plotly", "datalab", "databricks",
    },
    "mobile": {
        "ios", "android", "swiftui", "uikit", "jetpack", "jetpack compose",
        "react native", "flutter", "xamarin", "ionic", "cordova",
        "kotlin multiplatform",
    },
    "tools_platforms": {
        "git", "github", "gitlab", "bitbucket", "linux", "unix",
        "jira", "confluence", "slack", "figma", "zeplin", "salesforce",
        "servicenow", "wordpress", "shopify", "magento", "contentful",
        "strapi", "sanity", "drupal", "joomla", "wix", "squarespace",
        "zapier", "make", "ifttt",
    },
    "concepts": {
        "microservices", "monolith", "api", "rest api", "restful",
        "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "bdd",
        "oauth", "jwt", "saml", "openid", "sso", "rbac",
        "etl", "elt", "data warehouse", "data lake", "data mesh",
        "event driven", "event sourcing", "cqrs", "domain driven design",
        "clean architecture", "hexagonal architecture",
    },
}

# ---------------------------------------------------------------------------
# Build lookup structures
# ---------------------------------------------------------------------------

# Alias map is now sourced from the shared taxonomy module.
# Legacy alias map kept for extractor-internal multi-word canonicalization
# that differs from the taxonomy (e.g., "machine learning" → "ml" for extraction,
# while taxonomy keeps "machine learning" for matching).
_ALIAS_MAP: dict[str, str] = {
    "golang": "go",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "large language model": "llm",
    "react.js": "react",
    "vue.js": "vue",
    "express.js": "express",
    "node.js": "node.js",
    "alpine.js": "alpine.js",
    ".net": ".net",
    "asp.net": "asp.net",
    "ruby on rails": "rails",
    "machine learning": "ml",
    "deep learning": "deep learning",
    "computer vision": "computer vision",
    "neural network": "neural network",
    "gradient boosting": "gradient boosting",
}

# Merge taxonomy aliases into extractor's alias map for consistency.
# Taxonomy aliases take precedence for matching consistency.
_ALIAS_MAP.update(SKILL_ALIASES)

# All unique skill strings (lowercase)
ALL_SKILLS: set[str] = set()
for _skills in _SKILL_CATEGORIES.values():
    ALL_SKILLS.update(_skills)

# Split into: single alphanumeric words (fast set lookup) vs special/multi-word (regex)
_ALPHA_WORD = re.compile(r"^[a-z0-9]+$")

_SIMPLE_SKILLS: set[str] = set()       # single alphanumeric words → set intersection
_COMPLEX_SKILLS: list[tuple[str, re.Pattern]] = []  # multi-word or special chars → regex

for _s in ALL_SKILLS:
    if _ALPHA_WORD.match(_s):
        _SIMPLE_SKILLS.add(_s)
    else:
        _COMPLEX_SKILLS.append((_s, re.compile(re.escape(_s), re.IGNORECASE)))

# ---------------------------------------------------------------------------
# Seniority extraction
# ---------------------------------------------------------------------------

_TITLE_SENIORITY = [
    # High seniority first (more specific matches take priority)
    (re.compile(r"\b(distinguished|fellow|executive)\b", re.IGNORECASE), "staff"),
    (re.compile(r"\b(director|vp|vice president|head of|chief)\b", re.IGNORECASE), "lead"),
    (re.compile(r"\b(principal|staff|architect)\b", re.IGNORECASE), "staff"),
    (re.compile(r"\b(senior|sr\.?|sr)\b", re.IGNORECASE), "senior"),
    (re.compile(r"\b(lead|tech lead|team lead)\b", re.IGNORECASE), "lead"),
    # Junior patterns
    (re.compile(r"\b(junior|jr\.?|jr|associate|intern|entry.level|entry level|new grad|graduate)\b", re.IGNORECASE), "junior"),
]

_YEARS_PATTERN = re.compile(r"(\d+)[\+]*\s*years?", re.IGNORECASE)


def _resolve_skill(name: str) -> str:
    """Return canonical display name for a matched skill.

    First checks the shared taxonomy, then the extractor-local alias map.
    """
    resolved = _resolve_from_taxonomy(name)
    if resolved != name:
        return resolved
    return _ALIAS_MAP.get(name, name)


def extract_skills(title: str, description: str | None = None) -> list[str]:
    """Extract skills from job title and description text.

    Returns a sorted list of canonical skill names.
    """
    text = title.lower()
    if description:
        text += " " + description.lower()

    # 1. Fast path: extract all lowercase words, match against simple skills
    words = set(re.findall(r"\b[a-z][a-z0-9+#]*\b", text))
    found = {_resolve_skill(s) for s in words if s in _SIMPLE_SKILLS}

    # 2. Complex skills (multi-word, special chars) — regex match
    for name, pattern in _COMPLEX_SKILLS:
        if pattern.search(text):
            found.add(_resolve_skill(name))

    return sorted(found)


def extract_seniority(title: str, description: str | None = None) -> str | None:
    """Extract seniority level from job title and optional description.

    Returns one of: 'junior', 'mid', 'senior', 'lead', 'staff', or None.
    """
    # 1. Title-based detection (primary signal)
    title_lower = title.lower()
    for pattern, level in _TITLE_SENIORITY:
        if pattern.search(title_lower):
            return level

    # 2. Years-of-experience fallback from description
    if description:
        years_match = _YEARS_PATTERN.findall(description)
        if years_match:
            max_years = max(int(y) for y in years_match)
            if max_years >= 8:
                return "senior"
            elif max_years >= 5:
                return "senior"
            elif max_years >= 3:
                return "mid"
            else:
                return "junior"

    return None
