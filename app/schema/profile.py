from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class UserProfile(BaseModel):
    name: str