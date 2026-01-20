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
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_session, engine, Base # Наша функция подключения
from table import TaskModel, UserTimezone   # Наша таблица
import uuid
import random
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
  # Код ниже создает таблицы, если их еще нет
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  print("База данных готова (таблицы проверены/созданы)")
  yield

app = FastAPI(lifespan=lifespan)

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
    
    tasks_db[chat_id]["tasks"].pop(local_id, None)
    print(f"Задача {local_id} удалена из временной базы так как была выполнена")




#принятие и установка напоминания на таймер 
@app.post("/tasks", response_model=Task)
async def create_task(
  task: Task, 
  db: AsyncSession = Depends(get_session) # <--- Внедряем базу данных
):
  print(f"\nБэкенд: Получен POST-запрос на /tasks.")

  # 1. Генерируем системный UUID
  generated_uuid = str(uuid.uuid4())

  # 2. Определяем часовой пояс
  # (Предполагаю, что словарь time_zone у тебя остался глобальным, как в старом коде)
  current_tz = time_zone.get(task.user_id, "UTC")

  # 3. Генерируем уникальный local_id (100-999) через проверку в БД
  local_id = 0
  while True:
    local_id = random.randint(100, 999)

    # SQL: SELECT 1 FROM tasks WHERE user_id=... AND local_id=...
    query = select(TaskModel).where(
      TaskModel.user_id == task.user_id,
      TaskModel.local_id == local_id
    )
    result = await db.execute(query)

    # Если ничего не нашли (None) — значит номер свободен
    if result.scalar_one_or_none() is None:
      break

  # 4. Создаем объект для базы данных
  new_db_task = TaskModel(
    task_uuid=generated_uuid,
    user_id=task.user_id,
    local_id=local_id,
    task_text=task.task_text,
    task_time=task.task_time,
    time_zone=current_tz # Сохраняем и TZ тоже
  )

  # 5. Сохраняем в MySQL
  db.add(new_db_task)
  await db.commit()       # Физически записываем на диск
  await db.refresh(new_db_task) # Получаем обратно обновленные данные

  # 6. Добавляем задачу в планировщик (APScheduler)
  # Логика остается прежней
  scheduler.add_job(
    send_reminder,
    trigger='date',
    run_date=task.task_time,
    timezone=current_tz,
    args=[task.user_id, task.task_text, local_id],
    id=f"job_{generated_uuid}"
  )

  print(f"Бэкенд: Задача №{local_id} сохранена в MySQL для {task.user_id}. UUID: {generated_uuid}")

  # 7. Возвращаем ответ в формате Pydantic (как и раньше)
  # Мы берем данные из входящей задачи и добавляем сгенерированные ID
  response_data = task.model_dump()
  response_data["id"] = generated_uuid  # Твой строковый UUID
  response_data["local_id"] = local_id  # Твой короткий номер

  return Task(**response_data)




#получения всех задач из бд
@app.get("/get_all_tasks", response_model=List[Task])
async def get_tasks(user_id: int, db: AsyncSession = Depends(get_session)):
  # 1. Формируем запрос: "Выбрать всё из таблицы TaskModel, где user_id совпадает"
  query = select(TaskModel).where(TaskModel.user_id == user_id)

  # 2. Выполняем запрос
  result = await db.execute(query)

  # 3. Получаем список объектов
  user_tasks = result.scalars().all()

  # 4. Проверяем, нашли ли хоть что-то
  if not user_tasks:
    raise HTTPException(
      status_code=404, 
      detail=f"У пользователя {user_id} нет напоминаний"
    )

  return user_tasks


#удаление опредленной задачи 
@app.delete("/delete_task")
async def delete_task(task: Task, db: AsyncSession = Depends(get_session)):
  # 1. Извлекаем нужные ID из входящих данных
  local_id = task.local_id
  user_id = task.user_id
  task_uuid = task.task_uuid # Это наш UUID для планировщика

  # 2. Формируем команду на удаление в БД
  # "Удали запись из TaskModel, где совпадает user_id и local_id"
  query = delete(TaskModel).where(
    TaskModel.user_id == user_id, 
    TaskModel.local_id == local_id
  )

  # 3. Выполняем удаление
  result = await db.execute(query)
  await db.commit() # ВАЖНО: подтверждаем изменения в базе

  # 4. Проверяем, было ли что-то удалено (rowcount — количество затронутых строк)
  if result.rowcount > 0:
    print(f"Задача №{local_id} удалена из БД")

    # 5. Пытаемся удалить задачу из планировщика (если она там была)
    try:
      scheduler.remove_job(f"job_{task_uuid}")
      print(f"Уведомление job_{task_uuid} отменено")
    except:
      pass # Если задачи в планировщике нет (уже сработала), просто идем дальше

    return {"status": "success", "message": "Задача удалена"}

  return {"status": "error", "message": "Задача не найдена в базе"}


#проверка есть ли часового пояс у данного пользователя 
@app.get("/check_timezone")
async def check_timezone(user_id: int, session: AsyncSession = Depends(get_session)):
  # Ищем пользователя в БД по user_id
  query = select(UserTimezone).where(UserTimezone.user_id == user_id)
  result = await session.execute(query)
  user = result.scalar_one_or_none()

  if user and user.timezone:
    print(f"У пользователя {user_id} найден пояс: {user.timezone}")
    return {"timezone_str": user.timezone}

  # Если пользователя нет или поле timezone пустое
  raise HTTPException(
    status_code=404, 
    detail="У текущего пользователя еще не установлен часовой пояс"
  )




#установка часового пояса для конкретного пользователя 
@app.post("/set_timezone", response_model=Timezone)
async def set_timezone(timezone: Timezone, session: AsyncSession = Depends(get_session)):
  # 1. Ищем, есть ли уже такой пользователь в базе
  query = select(UserTimezone).where(UserTimezone.user_id == timezone.user_id)
  result = await session.execute(query)
  user = result.scalar_one_or_none()

  if user:
    # 2. Если пользователь найден — обновляем его часовой пояс
    print(f"У пользователя {user.user_id} уже был пояс, обновляем на: {timezone.timezone_str}")
    user.timezone = timezone.timezone_str
  else:
    # 3. Если пользователя нет — создаем новую запись
    print(f"Создаем новую запись для пользователя: {timezone.user_id}")
    new_user = UserTimezone(
      user_id=timezone.user_id,
      timezone=timezone.timezone_str
    )
    session.add(new_user)

  # 4. Сохраняем изменения в БД
  await session.commit()

  return timezone


