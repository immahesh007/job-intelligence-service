"""Skill hierarchy — parent-child relationships for partial-credit matching.

When a candidate has a parent skill (e.g., "machine learning") and the job
requires a child skill (e.g., "tensorflow"), partial credit is awarded.
"""

# Parent → set of children
SKILL_HIERARCHY: dict[str, set[str]] = {
    "frontend": {
        "react", "angular", "vue", "svelte", "next.js", "gatsby",
        "redux", "jquery", "bootstrap", "tailwind", "material-ui",
        "chakra", "ant design", "htmx", "alpine.js",
    },
    "backend": {
        "django", "flask", "fastapi", "spring", "express", "nestjs",
        "laravel", "rails", "phoenix", "gin", ".net", "asp.net",
    },
    "machine learning": {
        "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost",
        "lightgbm", "random forest", "gradient boosting", "neural network",
        "cnn", "rnn", "lstm", "transformer", "hugging face", "spacy",
        "nltk", "opencv",
    },
    "cloud computing": {
        "aws", "azure", "gcp", "lambda", "cloudformation", "cloudflare",
        "s3", "ec2", "sqs", "sns", "emr", "glue", "bigquery", "redshift",
    },
    "devops": {
        "docker", "kubernetes", "terraform", "ansible", "puppet", "chef",
        "jenkins", "github actions", "gitlab ci", "circleci", "argocd",
        "prometheus", "grafana", "datadog", "helm", "istio", "envoy",
    },
    "database": {
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "cockroachdb", "neo4j", "snowflake",
        "bigquery", "clickhouse", "duckdb",
    },
    "data engineering": {
        "spark", "hadoop", "airflow", "dbt", "kafka", "rabbitmq",
        "hive", "presto", "trino", "flink", "beam", "dagster", "prefect",
        "pandas", "numpy",
    },
    "mobile": {
        "ios", "android", "swiftui", "uikit", "jetpack compose",
        "react native", "flutter", "xamarin",
    },
    "natural language processing": {
        "nltk", "spacy", "hugging face", "transformer", "lstm",
        "rnn", "large language model", "llm", "langchain", "llamaindex",
        "embeddings", "rag",
    },
    "test automation": {
        "selenium", "cypress", "playwright", "jest", "mocha",
        "pytest", "junit", "testng", "cucumber",
    },
}

# Build reverse index: child → set of parents
_CHILD_TO_PARENTS: dict[str, set[str]] = {}
for _parent, _children in SKILL_HIERARCHY.items():
    for _child in _children:
        _CHILD_TO_PARENTS.setdefault(_child, set()).add(_parent)


def get_parents(skill: str) -> set[str]:
    """Return the parent categories for a given skill."""
    return _CHILD_TO_PARENTS.get(skill.lower(), set())


def get_children(parent: str) -> set[str]:
    """Return child skills for a given parent category."""
    return SKILL_HIERARCHY.get(parent.lower(), set())


def compute_hierarchical_overlap(
    candidate_skills: set[str],
    job_skills: set[str],
) -> set[str]:
    """Find skills where candidate has a parent and job has a child (or vice versa).

    Returns the set of matched skills (after hierarchical expansion).
    """
    matched: set[str] = set()

    for c_skill in candidate_skills:
        c_lower = c_skill.lower()
        # Direct match
        if c_lower in job_skills:
            matched.add(c_lower)
            continue

        # Candidate has parent → job has child
        children = SKILL_HIERARCHY.get(c_lower, set())
        if children & job_skills:
            matched.add(c_lower)
            continue

        # Candidate has child → job has parent
        parents = _CHILD_TO_PARENTS.get(c_lower, set())
        if parents & job_skills:
            matched.add(c_lower)

    return matched
