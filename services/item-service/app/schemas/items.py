from pydantic import BaseModel


class ItemCreate(BaseModel):
    sku: str
    name: str
    item_type: str = "base"
    category_path: str | None = None
    attributes: dict | None = None
    compliance_tags: list[str] | None = None
    display_metadata: dict | None = None
