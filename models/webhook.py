from pydantic import BaseModel
from typing import Any

class Parameters(BaseModel):
    nome5: str | None = None
    cpf5: str | None = None
    unidadelot: str | None = None
    foto5: Any | None = None
    fotorosto5: Any | None = None
    Sim: str | None = None
    nome7: str | None = None
    cpf7: str | None = None
    unidadelot2: str | None = None
    fotodoc7: Any | None = None
    fotorosto7: Any | None = None
    sim: str | None = None

class QueryResult(BaseModel):
    parameters: Parameters

class Webhook(BaseModel):
    queryResult: QueryResult
    session: str