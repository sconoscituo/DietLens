# 데이터베이스 설정
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import DATABASE_URL

# SQLite 전용 connect_args (다른 DB에는 적용하지 않음)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """모든 모델의 기본 클래스"""
    pass


async def get_db() -> AsyncSession:
    """DB 세션 의존성 주입"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """테이블 생성 및 초기 데이터 로드"""
    from app.models import Food, Meal, MealItem, DailyLog, Goal  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
