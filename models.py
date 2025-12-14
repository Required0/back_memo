from pydantic import BaseModel
from typing import List, Dict,Optional
from datetime import datetime

class Base(BaseModel):
    user_id: Optional[int] = None 


class Task(Base):  
    text: str 
    time: datetime   # Время в UTC
    completed: bool = False


class Timezone(Base):
    timezone_str: str | None = None # Оригинальный часовой пояс пользователя
