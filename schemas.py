from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordUpdate(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class About(BaseModel):
    name: str
    version: str
    developer: str


class ComponentBase(BaseModel):
    digikey_pn: Optional[str] = None
    manufacturer_pn: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    quantity: int = 0
    location: Optional[str] = None
    notes: Optional[str] = None
    raw_barcode: Optional[str] = None


class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(ComponentBase):
    pass


class Component(ComponentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Backup(BaseModel):
    version: str
    exported_at: datetime
    component_count: int
    components: List[Component]


class RestoreRequest(BaseModel):
    # Accepts a backup document; extra fields (version, exported_at, …) are ignored.
    components: List[ComponentBase]
