from pydantic import BaseModel

class LeaseInput(BaseModel):
    # TODO: replace with your real fields later
    amount: float = 0.0
    currency: str = "USD"

    class Config:
        extra = "allow"  # accept any extra fields until we finalize the schema
