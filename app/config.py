from pathlib import Path

from app.models.job import ATSProvider

COMPANIES_DIR = Path(__file__).resolve().parent.parent / "companies"

PROVIDER_FILES = {
    ATSProvider.GREENHOUSE: COMPANIES_DIR / "greenhouse.txt",
    ATSProvider.LEVER: COMPANIES_DIR / "lever.txt",
    ATSProvider.ASHBY: COMPANIES_DIR / "ashby.txt",
}


def load_companies(provider: ATSProvider) -> list[str]:
    """Return company slugs for a provider, one per line. Blank lines and #-comments are skipped."""
    path = PROVIDER_FILES[provider]
    if not path.exists():
        return []
    slugs: list[str] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            slugs.append(stripped)
    return slugs
