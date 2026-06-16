# Changelog

All notable changes to `inv2digikey` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Guidelines:
- Add a new entry under `## [Unreleased]` as you work — no batching up for release day.
- Group entries under: Added, Changed, Deprecated, Removed, Fixed, Security.
- Reference the spec slug and PR number:  "Added dark mode (spec: dark-mode, #42)".
- On release, rename `[Unreleased]` to the new version with the release date,
  and open a fresh `[Unreleased]` section at the top.
- The release-drafter workflow auto-populates draft release notes from PRs —
  keep PR titles tidy so they flow straight into here.
-->

## [Unreleased]

### Added
- Main menu hub linking every feature from the inventory header (spec: app-industrialization).
- Settings page with a light/dark mode toggle, persisted in localStorage (spec: app-industrialization).
- Inventory backup & restore: `GET /api/backup` and `POST /api/restore` (merge/replace) (spec: app-industrialization).
- CSV export: `GET /api/components/export/csv` (spec: app-industrialization).
- User management: `GET/POST /api/users`, `DELETE /api/users/{id}`, `PUT /api/users/{id}/password` (spec: app-industrialization).
- About page and `GET /api/about` exposing app version and developer (Eduardo Arana) (spec: app-industrialization).
- TME (tme.eu) QR label parsing — extracts quantity, manufacturer, MPN, and TME order symbol (spec: tme-barcode-support).

### Changed
- Standardized navigation back buttons on a consistently sized SVG arrow that returns to a defined in-app view instead of relying on browser history (spec: app-industrialization).
- Moved the label parser out of `static/index.html` into `static/parser.js` (ES module) with Node regression tests (spec: tme-barcode-support).

### Deprecated
-

### Removed
-

### Fixed
-

### Security
-

---

## [0.1.0] — YYYY-MM-DD

### Added
- Initial release.

[Unreleased]: https://github.com/arananet/inv2digikey/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/arananet/inv2digikey/releases/tag/v0.1.0
