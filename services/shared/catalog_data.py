"""Display metadata for the demo catalog -- single source of truth.
Used by:
  - scripts/seed.py (via volume mount) to populate display_metadata on item creation
  - item-service lifespan (via COPY shared/) to backfill existing rows
"""

DISPLAY_METADATA: dict[str, dict[str, str]] = {
    "ALC-001": {"price": "64.99", "emoji": "\U0001f377", "description": "Full-bodied Napa Valley Cabernet"},
    "CHEM-001": {"price": "89.99", "emoji": "\U0001f9ea", "description": "Pool chlorine stabilizer tabs"},
    "FIRE-001": {"price": "49.99", "emoji": "\U0001f386", "description": "Assorted consumer fireworks"},
    "SUPP-001": {"price": "24.99", "emoji": "\U0001f48a", "description": "Dietary supplement capsules"},
    "FIRE-002": {"price": "449.99", "emoji": "\U0001f3af", "description": "12-gauge pump-action shotgun"},
    "CHEM-002": {"price": "7.99", "emoji": "\U0001fab2", "description": "Aerosol insecticide spray"},
    "ELEC-001": {"price": "799.99", "emoji": "\U0001f4f1", "description": "Flagship Android smartphone"},
    "ALC-002": {"price": "34.99", "emoji": "\U0001f943", "description": "Kentucky straight bourbon whiskey"},
    "PHARM-001": {"price": "9.99", "emoji": "\U0001f48a", "description": "Pseudoephedrine decongestant 24ct"},
    "GROC-001": {"price": "5.49", "emoji": "\U0001f95b", "description": "USDA organic whole milk 1 gallon"},
    "CLOTH-001": {"price": "59.99", "emoji": "\U0001f456", "description": "Classic straight-fit denim jeans"},
    "TOY-001": {"price": "79.99", "emoji": "\U0001f9f1", "description": "Building block construction set"},
    "HOME-001": {"price": "89.99", "emoji": "\U0001f372", "description": "Multi-function pressure cooker 6qt"},
    "ELEC-002": {"price": "349.99", "emoji": "\U0001f3a7", "description": "Wireless noise-cancelling headphones"},
    "ALC-003": {"price": "19.99", "emoji": "\U0001f379", "description": "Hard seltzer variety 12-pack"},
}
