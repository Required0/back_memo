from pydantic import BaseModel
from typing import List, Dict,Optional
from datetime import datetime
from database import Base, engine 

class Base(BaseModel):
    user_id: Optional[int] = None 


class Task(Base):  
    local_id: Optional[int] = None 
    task_text: str 
    task_time: datetime   # Время в UTC
    task_uuid: Optional[str] = None 


class Timezone(Base):
    timezone_str: str | None = None # Оригинальный часовой пояс пользователя
