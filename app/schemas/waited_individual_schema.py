from pydantic import BaseModel, Field
from typing import List, Optional


class WaitedVictim(BaseModel):
    name: str
    occupation: str
    gender: str
    age: int


class UpdateWaitedVictimsRequest(BaseModel):
    victims: List[WaitedVictim]


class WaitedIndividualOut(BaseModel):
    _id: str
    case_id: str
    victims: List[WaitedVictim]
