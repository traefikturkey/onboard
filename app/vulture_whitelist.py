# Whitelist for vulture: names exposed to templates or used indirectly
# Generated from vulture output and curated
# Keep context processors and route-handling symbols that are referenced from templates

# Functions / names to ignore
INCLUDED_NAMES = [
    "inject_current_date",
    "index",
    "click_events",
    "track",
    "refresh",
    "healthcheck",
]

# Methods/attributes on internal classes (use wildcard patterns with vulture's --ignore-names)
WILDCARD_NAMES = [
    "_.handle_starttag",
    "_.handle_startendtag",
    "_.handle_endtag",
    "_.handle_data",
    "_.handle_comment",
    "_.handle_entityref",
    "_.handle_charref",
    "_.accesslog",
    "_.errorlog",
    "_.loglevel",
    "_.bind",
]

# Flatten to a single list for convenience
ALL_IGNORE = INCLUDED_NAMES + WILDCARD_NAMES
