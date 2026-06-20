# Changelog

## [0.2.0] - 2026-06-20

### Added
- Themed word presets: named themes (e.g. "Animal · City", "Mountain · River")
  that combine one random word from each curated category, with a Random/Themed
  mode toggle in the UI
- In-memory `ThemeService` loading presets and category word lists from `themes/`
- `GET /themes` and `POST /themed` API endpoints

### Changed
- Moved the "View on GitHub" link into the footer for cleaner layout

## [0.1.0] - 2024-03-xx

### Added
- Initial Flask application setup
- Word generation with configurable length and count
- Web interface with dark mode support
- PWA support with offline capability
- Automated icon generation system
- Installation scripts for production deployment
- Development environment setup scripts
- Nginx and systemd service configuration
- GitHub Actions for testing
- Code coverage reporting

### Features
- Random word generation
- Dark/Light mode toggle
- PWA installation support
- Responsive design
- SQLite database for word storage
- REST API endpoints
- System service installation
- Development tools and documentation 