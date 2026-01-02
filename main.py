from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from models import Task, Timezone, Base
from aiogram import Bot
import asyncio
import random 
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uuid
from conf import TOKEN


app = FastAPI()

bot = Bot(token=TOKEN)


scheduler = AsyncIOScheduler()
scheduler.start()

# имитируем бд
tasks_db: Dict[int, Dict] = {}

time_zone = {}


#функция для отправки напоминания по времени
async def send_reminder(chat_id, text, local_id):
    print(f" ОТПРАВКА: Пользователю {chat_id} сообщение: {text}")
    await bot.send_message( chat_id=chat_id,  text=f"Ваше напоминание: {text}")
    
    global tasks_db
    
    tasks_db[chat_id]["tasks"].pop(local_id, None)
    print(f"Задача {local_id} удалена из временной базы так как была выполнена")




#принятие и установка напоминания на таймер 
@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    print(f"\nБэкенд: Получен POST-запрос на /tasks.")

    # 1. Генерируем системный UUID
    task_id = str(uuid.uuid4())

    # 2. Превращаем модель в словарь и добавляем UUID
    new_task_data = task.model_dump()
    new_task_data["id"] = task_id
    # 3. Извлекаем данные для удобства
    id_chat = new_task_data["user_id"]
    text = new_task_data["text"]
    run_time = new_task_data["time"]
    current_tz = time_zone.get(id_chat, "UTC") # Берем TZ или ставим UTC по дефолту
   
    if id_chat not in tasks_db:
        # Если юзера нет, создаем ему структуру
        tasks_db[id_chat] = {"counter": 0, "tasks": {}}

    current_user_tasks = tasks_db[id_chat]["tasks"] 
   
    while True:
     local_id = random.randint(100, 999) 
     if local_id not in current_user_tasks:
       break
      
    new_task_data["local_id"] = local_id # Записываем номер в саму задачу

    # 5. Добавляем задачу в планировщик
    scheduler.add_job(
        send_reminder,
        trigger='date',
        run_date=run_time,
        timezone=current_tz,
        args=[id_chat, text, local_id],
        id=f"job_{task_id}" # Используем UUID для уникальности в системе
    )

    # 6. Сохраняем задачу в наш "ящик" пользователя
   
    tasks_db[id_chat]["tasks"][local_id] = new_task_data


    print(f"Бэкенд: Задача №{local_id} сохранена для {id_chat}. UUID: {task_id}")

    # Возвращаем обновленные данные (включая local_id)
    return Task(**new_task_data)




#получения всех задач из бд
@app.get("/get_all_tasks", response_model=List[Task])
async def get_task(user_id: int):
    user_data = tasks_db.get(user_id)
    
    print(user_data)

    if user_data and user_data["tasks"]:
        return list(user_data["tasks"].values())


    raise HTTPException(status_code=404, detail="У текущего пользователя нет напоминаний")


#удаление опредленной задачи 
@app.delete("/delete_task")
async def delete_task(task: Task):
    new_task_data = task.model_dump()
    
    local_ID = new_task_data["local_id"] 
    id_chat = new_task_data["user_id"] 
    task_uuid = new_task_data.get("id")

    removed = tasks_db[id_chat]["tasks"].pop(local_ID, None)
    print(f"Задача {local_ID} удалена из временной базы так как была выполнена")
    try:
      scheduler.remove_job(f"job_{task_uuid}")
    except:
      pass

    if removed:
      print(f"Задача №{local_ID} удалена")
      return {"status": "success", "message": "Задача удалена"}
    return {"status": "error", "message": "Задача не найдена"}


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