from fastapi import FastAPI
from typing import List, Dict,Optional
from models import Task, Timezone

app = FastAPI()

# имитируем бд
tasks_db: List[Dict] = []

time_zone = {}

next_task_id = 1



#принятие и установка напоминания на таймер 
@app.post("/tasks", response_model=Task)
async def create_task(task: Task):

    global next_task_id 

    print(f"\nБэкенд: Получен POST-запрос на /tasks.")
    print(f"Бэкенд: Входящие данные (валидированы Pydantic): Text={task.text}, Time={task.time}, Completed={task.completed}")
     
    task_id = next_task_id
    next_task_id += 1 
    
    new_task_data = task.model_dump()
    new_task_data["id"] = task_id 
    print(new_task_data)

    tasks_db.append(new_task_data) #записываем напоминание как словарь в бд
    print(f"Бэкенд: Задача ID={task_id} сохранена: {new_task_data}")

    return Task(**new_task_data)


#получения всех задач из бд
@app.get("/get_all_tasks", response_model=List[Task])
async def get_task():
    return [Task(**task_data) for task_data in tasks_db]



@app.post("/set_timezone", response_model=Timezone)
async def set_timezone(timezone: Timezone):
    time_zone[timezone.user_id] = timezone.timezone_str 

    print("новый пояс установлен")
    print(f"Пользователь: {timezone.user_id}\nЧасовой пояс: {timezone.timezone_str}")
    return timezone