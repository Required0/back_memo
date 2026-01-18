import datetime
from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base # Импортируем Базу, которую создали в database.py

class TaskModel(Base):
  # Это имя таблицы, которое будет в MySQL
  __tablename__ = "tasks"

  # --- КОЛОНКИ (СТОЛБЦЫ) ---

  # 1. ID записи в базе (1, 2, 3...). 
  # primary_key=True значит, что это главный уникальный номер.
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

  # 2. Твой UUID (уникальный ключ задачи)
  # String(36) — строка длиной 36 символов.
  task_uuid: Mapped[str] = mapped_column(String(36), unique=True)

  # 3. ID пользователя в Телеграм (он длинный, поэтому BigInteger)
  user_id: Mapped[int] = mapped_column(BigInteger)

  # 4. Короткий номер (100-999) для кнопок
  local_id: Mapped[int] = mapped_column()

  # 5. Текст задачи (до 1000 символов)
  task_text: Mapped[str] = mapped_column(String(1000))

  # 6. Время напоминания
  task_time: Mapped[datetime.datetime] = mapped_column(DateTime)

    # 7. Часовой пояс (НОВОЕ ПОЛЕ)
  # Храним как строку: "Europe/Moscow", "UTC" и т.д.
  time_zone: Mapped[str] = mapped_column(String(50), default="UTC")

  # 8. Время создания записи (ставится само через func.now())
  created_at: Mapped[datetime.datetime] = mapped_column(
    DateTime, server_default=func.now()
  )
