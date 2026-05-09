from sqlmodel import SQLModel
from uuid import UUID


class CustomerRead(SQLModel):
    id: UUID
    name: str

class CustomerLogin(SQLModel):
    name: str
    password: str