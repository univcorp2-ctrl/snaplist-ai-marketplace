# CODEX.md

## Mission
SnapList AI turns product photos into normalized, editable, marketplace-ready listing drafts.

## Engineering rules
- Prefer official marketplace APIs.
- Unsupported consumer marketplaces remain assisted-draft connectors.
- Never store marketplace passwords or bypass CAPTCHA/MFA.
- Keep the no-key demo path working.
- Add tests for API changes and static PWA behavior.
- Secrets belong in environment variables only.

## Commands
```bash
pip install -e '.[dev]'
ruff check app tests
pytest
uvicorn app.main:app --reload
```
