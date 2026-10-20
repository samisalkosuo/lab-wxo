"""Mock release manifest. Static; all data in this package is invented for the demo."""

# Fixed "today" for the mock world, so ages in days never drift between runs.
AS_OF = "2025-09-15"

RELEASES = {
    "rel-2025-q3": {
        "release_id": "rel-2025-q3",
        "name": "Q3 2025 release",
        "planned_date": "2025-09-18",
        "components": ["payments", "orders_api", "frontend"],
    },
}


def get_release(release_id: str):
    return RELEASES.get(release_id)
