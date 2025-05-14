from pydantic import BaseModel


class ObserverConfig(BaseModel):
    service_name: str
    sensitive_headers: tuple[str, ...] | None = None
    sensitive_body_fields: tuple[str, ...] | None = None
