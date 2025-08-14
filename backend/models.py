from pydantic import BaseModel

<<<<<<< HEAD
||||||| (empty tree)
=======

>>>>>>> 2fd963e (chore: Koyeb Procfile/runtime, env-driven CORS, frontend .envs, calc engine & tests)
class LeaseInput(BaseModel):
    # TODO: replace with your real fields later
    amount: float = 0.0
    currency: str = "USD"

    class Config:
        extra = "allow"  # accept any extra fields until we finalize the schema
