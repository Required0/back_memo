from pydantic import BaseModel
from typing import List, Dict,Optional
from datetime import datetime


class Task(BaseModel):
    id: Optional[int] = None      
    text: str 
    time: datetime   # Время в UTC
    completed: bool = False


class Timezone(BaseModel):
    user_id: Optional[int] = None 
    timezone_str: str | None = None # Оригинальный часовой пояс пользователя
