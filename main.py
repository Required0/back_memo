from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from models import Task, Timezone, Base

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


#проверка есть ли часового пояс у данного пользователя 
@app.get("/check_timezone")
async def check_timezone(user_id: int):
 if user_id in time_zone:
        print("У текущего пользователя уже установлен часовой пояс")
        return {"timezone_str": time_zone[user_id]} 
 else:
    raise HTTPException(status_code=404, detail="У текущего пользователя еще не установлен часовой пояс")


#установка часового пояса для конкретного польззователя 
@app.post("/set_timezone", response_model=Timezone)
async def set_timezone(timezone: Timezone):
    
    if timezone.user_id in time_zone:
        print("У текущего пользователя уже установлен часовой пояс")
        time_zone[timezone.user_id] = timezone.timezone_str 
        print("новый пояс установлен")
        return timezone
    else:
        time_zone[timezone.user_id] = timezone.timezone_str 
        print("новый пояс установлен")
        print(f"Пользователь: {timezone.user_id}\nЧасовой пояс: {timezone.timezone_str}")
        return timezone