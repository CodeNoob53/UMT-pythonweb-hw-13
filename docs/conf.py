import sys
import os

sys.path.insert(0, os.path.abspath(".."))

# Minimal env vars so settings can be imported during docs build.
# REDIS_URL and CORS_ORIGINS have no defaults in Settings, so they must be set here.
os.environ.setdefault("DB_URL", "postgresql+asyncpg://postgres:postgres@localhost/contacts_db")
os.environ.setdefault("JWT_SECRET", "docs-build-secret-key-placeholder")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("MAIL_USERNAME", "docs@example.com")
os.environ.setdefault("MAIL_PASSWORD", "placeholder")
os.environ.setdefault("MAIL_FROM", "docs@example.com")
os.environ.setdefault("CLD_NAME", "placeholder")
os.environ.setdefault("CLD_API_KEY", "0")
os.environ.setdefault("CLD_API_SECRET", "placeholder")

project = "Contacts REST API"
copyright = "2026"
author = "hw-13"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "nature"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
