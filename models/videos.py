from bson import ObjectId
from pydantic import BaseModel, Field, validator
from typing import Dict

class Video(BaseModel):
    link: str
    id: int
    word_id: int
    status: int
    
    @validator('status')
    def status_validator(cls, value):
        # scraped -> accepted -> downloaded -> clipped -> filtered
        if value not in {0, 1, 2, 3, 4}:
            raise ValueError('status must be 0, 1, 2, 3 or 4')
        return value

class Clip(BaseModel):
    link: str
    id: int
    video_id:int
    word_id : int
    attributes: Dict = Field(default_factory=dict)

class Word(BaseModel):
    query: str
    id: int
    searched: bool
    scroll_ahead: int