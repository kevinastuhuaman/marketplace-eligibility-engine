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
    "HOME-002": {"price": "129.99", "emoji": "\U0001f9c3", "description": "Certified kitchen blender for Mexico launch"},
    "HOME-003": {"price": "12.99", "emoji": "\U0001f9ea", "description": "Bilingual measuring cup with metric markings"},
    "HOME-004": {"price": "9.99", "emoji": "\U0001f964", "description": "Imperial-only kitchen measuring cup"},
    "HOME-005": {"price": "119.99", "emoji": "\U0001f4e6", "description": "Imported blender missing final NOM certificate"},
    "HOME-006": {"price": "79.99", "emoji": "\U0001f4a8", "description": "Zero-stock demo item for diagnosis flows"},
    "ALC-004": {"price": "14.99", "emoji": "\U0001f379", "description": "Spanish-labeled sugary hard soda for Mexico"},
    "ALC-005": {"price": "14.99", "emoji": "\U0001f379", "description": "English-only sugary hard soda for compare demos"},
    "GROC-002": {"price": "6.49", "emoji": "\U0001f95c", "description": "Chile cereal with black-label packaging"},
    "GROC-003": {"price": "5.99", "emoji": "\U0001f375", "description": "RTCA-regulated beverage used for VAT scenarios"},
    "ELEC-003": {"price": "149.99", "emoji": "\U0001f6f8", "description": "Lithium battery pack requiring import certificate"},
}
