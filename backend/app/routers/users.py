from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

class UserResponse(BaseModel):
    id: str
    name: str
    role: str
    avatar: str

@router.get("", response_model=List[UserResponse])
def get_users():
    """
    Returns available mock users for local DBA session switching.
    Matches frontend User type and persona definitions.
    """
    return [
        UserResponse(id="usr-1", name="Priya Sharma", role="DBA", avatar="PS"),
        UserResponse(id="usr-2", name="Arjun Patel", role="ENGINEER", avatar="AP"),
        UserResponse(id="usr-3", name="Alex Vance", role="VIEWER", avatar="AV"),
    ]
