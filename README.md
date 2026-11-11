# Onboard

[![Build and Publish Docker Image](https://github.com/traefikturkey/onboard/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/traefikturkey/onboard/actions/workflows/docker-publish.yml)

Onboard is a self-hosted Flask dashboard that combines RSS/Atom feeds, bookmark collections, header links, and embedded pages in a configurable tab-and-column layout.

## Features

- YAML-defined tabs, rows, columns, and widgets
- Feed widgets with caching, filtering, scheduled refreshes, and optional processing
- Bookmark bar and section-based bookmark widgets
- Bookmark CRUD, import/export, move, and reorder APIs
- Iframe widgets for embedding other dashboards
- HTMX partial updates with Alpine-powered bookmark management
- Click tracking and automatic favicon retrieval
- Production container and VS Code devcontainer targets

## Run with Docker

The published image listens on port 9830:

```bash
docker run --rm --name onboard \
  -p 9830:9830 \
  ghcr.io/traefikturkey/onboard:latest
```

Open <http://localhost:9830>. Check container health at <http://localhost:9830/api/healthcheck>.

The command above uses ephemeral application data. Add named volumes to preserve configuration and feed caches between containers:

```bash
docker run --rm --name onboard \
  -p 9830:9830 \
  -v onboard-config:/srv/app/configs \
  -v onboard-working:/srv/app/.working \
  ghcr.io/traefikturkey/onboard:latest
```

On first startup, files from `app/defaults/` are copied into the empty runtime configuration directory.

> [!WARNING]
> Onboard does not provide an authentication layer. Do not expose it to an untrusted network without authentication and access controls in front of it.

## Run from source

### Requirements

- Python 3.15 (the repository pins 3.15.0)
- [uv](https://docs.astral.sh/uv/)
- GNU Make for the repository Make targets
- Docker for container builds and integration tests

Install the development environment and start the app:

```bash
uv sync --dev
uv run python run.py
```

Open <http://localhost:9830>. The first run creates ignored runtime files under `app/configs/`, `app/.working/`, and `app/static/assets/`.

The Make target can also run Gunicorn when `ONBOARD_PORT` is set:

```bash
ONBOARD_PORT=9830 make run
```

## Configuration

Runtime configuration is stored under `app/configs/`:

- `layout.yml` defines headers, tabs, nested rows and columns, and widgets.
- `bookmarks.json` stores bookmark-bar entries and named bookmark sections.

Tracked examples live under `app/defaults/`. Edit the runtime copies, not the defaults, for local use. The application reloads the layout when `layout.yml` changes. Bookmark data can also be managed at <http://localhost:9830/bookmarks/manage>.

A minimal feed layout follows the same structure as the tracked default:

```yaml
schema_version: 2

headers:
  - name: Project
    link: https://example.com/

tabs:
  - tab: Home
    columns:
      - column:
        widgets:
          - name: Example feed
            type: feed
            link: https://example.com/
            feed_url: https://example.com/feed.xml
```

Supported widget types in the current models and defaults are:

- `feed`: reads an RSS/Atom URL and caches articles.
- `bookmarks`: renders a named section from `bookmarks.json` using `bookmarks_section`.
- `iframe`: embeds a page using `src`.

### Presentation settings without image rebuilds

Changes to `layout.yml` and `bookmarks.json` take effect on the next page load;
no container restart or image rebuild is needed. Existing configurations retain
their appearance when the optional settings below are omitted. New templates or
JavaScript functionality still require an image update.

```yaml
ui:
  header_icon_size: 16px
  header_icon_gap: 4px
  header_link_padding_x: 8px
  header_link_padding_y: 0.5rem
  feed_height: 300px
  page_background: '#2a2a2c'

headers:
  - name: Example
    link: https://example.com/
    favicon: /static/assets/icons/example.ico
    bookmarks_section: example-searches
    hover_delay_ms: 2000
    multiColumn: 2
    openInNewTab: true

tabs:
  - tab: Home
    columns:
      - flex: 2
        widgets:
          - name: Useful links
            type: bookmarks
            bookmarks_section: useful-links
            columns: 2
            show_favicons: false
      - flex: 1
        widgets: []
```

Header dropdowns can reference any flat section in `bookmarks.json`, including
sections edited through the bookmark manager. The section wins when both
`bookmarks_section` and legacy inline `contents` are present. Inline entries
continue to use `href`; section entries use `link`. A header label opens its site;
hovering opens its dropdown after `hover_delay_ms` (0–60000). The adjacent button
and Arrow Down open it immediately. `multiColumn` accepts 1–10 columns;
`openInNewTab` applies to the header and its dropdown links and defaults to true.

The `favicon` field accepts an HTTP(S) URL, a root-relative URL, or a bundled image
filename such as `gmail.ico` (resolved under `/static/img/`). Header icons use the
explicit value first, then compatibility defaults for the original utility links,
then an available cached favicon. Bookmark-bar links honor the same explicit
field. Bookmark widgets display icons only when `show_favicons: true`, preserving
the existing text-only default. To keep custom files across image updates, mount
an icon directory at `/srv/app/static/assets/icons` and reference its files with
`/static/assets/icons/<filename>`.

Column `flex` is a positive numeric proportion (for example, 2 and 1 produce a
2:1 split). Bookmark widget `columns` accepts 1–10 and defaults to 1; it does not
require splitting one bookmark section into multiple sections.

Supported `ui` length settings are `header_icon_size`, `header_icon_gap`,
`header_link_padding_x`, `header_link_padding_y`, `widget_padding`,
`list_item_margin`, `list_item_padding_bottom`, and `feed_height`. Values are
nonnegative lengths using `px`, `rem`, `em`, `vh`, `vw`, or `%`, or the string
`'0'`.

Color settings are `header_background`, `header_link_background`,
`header_link_hover_background`, `header_text_color`, `page_background`,
`text_color`, `link_color`, `link_hover_color`, `visited_link_color`,
`bookmark_link_color`, and `widget_header_background`. Values are 3-, 4-, 6-, or
8-digit hex colors, `transparent`, or `currentColor`. Quote hex colors in YAML.
Unknown `ui` keys or invalid presentation values keep the previous valid layout
active and show the existing layout error notice. Presentation values are not
arbitrary CSS or JavaScript.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ONBOARD_PORT` | `9830` | Local application port used by `run.py` and `make run` |
| `ONBOARD_SITE_TITLE` | `OnBoard` | Browser page title |
| `ONBOARD_PAGE_TIMEOUT` | `600` | Rendered-page cache timeout in seconds |
| `WORKING_STORAGE` | `app/.working` | Feed-cache working directory |
| `ONBOARD_DISABLE_SCHEDULER` | `False` | Prevent background scheduler startup when set to `true` |
| `ONBOARD_FEED_FORCE_UPDATE` | unset | Force feed refresh checks when set to `true`, `1`, or `yes` |
| `ONBOARD_STRIP_URL_LENGTH` | `25` | URL-length threshold used by the long-URL processor |
| `FLASK_ENV` | `development` | Select development or production startup behavior |
| `FLASK_DEBUG` | `True` in `run.py` | Toggle local Flask debug behavior |

The production image binds Gunicorn to container port 9830 regardless of `ONBOARD_PORT`; change the host side of the Docker `-p` mapping to publish a different host port.

## Development commands

Run commands from the repository root.

| Task | Command |
| --- | --- |
| Sync development dependencies | `uv sync --dev` |
| Run a focused test | `uv run pytest tests/path/to/test_file.py` |
| Run non-integration and Behave tests with coverage | `make test` |
| Run all tests, including integration tests | `make test-all` |
| Format Python | `make format` |
| Format, then lint with Flake8 | `make lint` |
| Check dependency declarations | `make deptry` |
| Build the production image | `make build` |
| Validate the production image | `make test-build-prod` |

`make lint` runs the formatter before Flake8 and can modify files. Integration tests require Docker; they build the production image, start Selenium and application containers, and remove matching test containers.

## Project structure

```text
app/
  api/          Flask blueprints and Pydantic request/response models
  defaults/     Tracked seed layout and bookmark data
  models/       Layout, feed, widget, cache, and scheduler models
  processors/   Optional feed processors
  services/     Bookmark, favicon, migration, Docker, and tracking services
  static/       Source styles and static files
  templates/    Jinja templates and browser-side behavior
notebooks/      Exploratory notebooks with a separate pyproject.toml
scripts/        Bookmark migration and screenshot utilities
tests/          Unit, Behave, and Docker/Selenium integration tests
run.py          Runtime entry point imported by Gunicorn
```

Production exports the Flask app from `app/main.py`, which calls the injectable factory in `app/factory.py`. Production and tests share the same routes and initialization code.

## Testing

Pytest is configured in `pytest.ini` with strict markers and excludes `integration` tests by default. Shared fixtures in `tests/conftest.py` inject mock layout, bookmark manager, and click tracker dependencies.

For a normal change, run the narrowest relevant test first, then `make test` when practical. Run `make test-all` only when Docker-backed integration coverage is needed.
