from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# 1. Строка подключения: mysql+aiomysql://ЛОГИН:ПАРОЛЬ@ХОСТ/ИМЯ_БАЗЫ
DATABASE_URL = "mysql+aiomysql://root:HIGHT99900HIGHT@127.0.0.1/my_bot_db"

# 2. Создаем асинхронный движок
engine = create_async_engine(
  DATABASE_URL,
  echo=True, # Ставь False на продакшене (True показывает SQL-запросы в консоли)
)

# 3. Создаем фабрику сессий (через нее будем работать с БД)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# 4. Базовый класс для всех моделей
class Base(DeclarativeBase):
  pass

# 5. Функция-зависимость (Dependency) для FastAPI
# Она выдает сессию для каждого запроса и закрывает её в конце
async def get_session() -> AsyncSession:
  async with async_session_maker() as session:
    yield session
