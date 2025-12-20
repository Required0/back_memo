from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from models import Task, Timezone, Base
from aiogram import Bot
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uuid


app = FastAPI()

TOKEN = "8340933216:AAG2A_Vx_wM_WEqySDH498IW1LNvb83YBd0"
bot = Bot(token=TOKEN)


scheduler = AsyncIOScheduler()
scheduler.start()

# имитируем бд
tasks_db: List[Dict] = []

time_zone = {}


#функция для отправки напоминания по времени
async def send_reminder(chat_id, text, task_id):
    print(f" ОТПРАВКА: Пользователю {chat_id} сообщение: {text}")
    await bot.send_message("Ваше напоминание: ", chat_id=chat_id, text=text)
    
    global tasks_db
    
    tasks_db = [t for t in tasks_db if t.get('task_id') != task_id]
    print(f"Задача {task_id} удалена из временной базы так как была выполнена")



#принятие и установка напоминания на таймер 
@app.post("/tasks", response_model=Task)
async def create_task(task: Task):

    global next_task_id 

    print(f"\nБэкенд: Получен POST-запрос на /tasks.")
    print(f"Бэкенд: Входящие данные (валидированы Pydantic): Text={task.text}, Time={task.time}")
     
    task_id = task_id = str(uuid.uuid4()) 
    
    new_task_data = task.model_dump()
    new_task_data["id"] = task_id #номер задачи

    print(new_task_data)

    
    id_chat = new_task_data["user_id"]
    text = new_task_data["text"]
    time = new_task_data["time"]
    current_tz = time_zone.get(id_chat) 

    print(id, text, time, current_tz)
    

 
    scheduler.add_job(
        send_reminder,      # Какую функцию запустить
        trigger='date',     # Тип: выполнить один раз в указанную дату
        run_date=time,  # КОГДА запустить (объект datetime)
        timezone=current_tz,   # В каком часовом поясе считать это время
        args=[id_chat, text, task_id], # Аргументы для функции
        id=f"job_{id}" # (Опционально) ID задачи, чтобы потом её можно было удалить
    )



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


#установка часового пояса для конкретного пользователя 
@app.post("/set_timezone", response_model=Timezone)
async def set_timezone(timezone: Timezone):
    
    if timezone.user_id in time_zone:
        print("У текущего пользователя уже установлен часовой пояс")
        time_zone[timezone.user_id] = timezone.timezone_str 
        print("новый пояс установлен")
        print(timezone.timezone_str )
        return timezone
    else:
        time_zone[timezone.user_id] = timezone.timezone_str 
        print("новый пояс установлен")
        print(f"Пользователь: {timezone.user_id}\nЧасовой пояс: {timezone.timezone_str}")
        return timezone