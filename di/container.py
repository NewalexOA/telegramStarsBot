from typing import Optional
import structlog
from aiogram import Dispatcher
from database.sqlalchemy import SQLAlchemyDatabase
from unit_of_work.unit_of_work import UnitOfWork
from services.novel import NovelService
from services.referral import ReferralService
from services.payment import PaymentService
from services.admin import AdminService

logger = structlog.get_logger()

class Container:
    """Контейнер зависимостей приложения"""
    
    def __init__(self):
        self._db: Optional[SQLAlchemyDatabase] = None
        self._uow: Optional[UnitOfWork] = None
        self._novel_service: Optional[NovelService] = None
        self._referral_service: Optional[ReferralService] = None
        self._payment_service: Optional[PaymentService] = None
        self._admin_service: Optional[AdminService] = None

    @property
    def db(self) -> SQLAlchemyDatabase:
        if self._db is None:
            self._db = SQLAlchemyDatabase()
        return self._db

    @property
    def uow(self) -> UnitOfWork:
        if self._uow is None:
            self._uow = UnitOfWork(self.db.session_factory)
        return self._uow

    @property
    def novel_service(self) -> NovelService:
        if self._novel_service is None:
            self._novel_service = NovelService(self.uow)
        return self._novel_service

    @property
    def referral_service(self) -> ReferralService:
        if self._referral_service is None:
            self._referral_service = ReferralService(self.uow)
        return self._referral_service

    @property
    def payment_service(self) -> PaymentService:
        if self._payment_service is None:
            self._payment_service = PaymentService(self.uow)
        return self._payment_service

    @property
    def admin_service(self) -> AdminService:
        if self._admin_service is None:
            self._admin_service = AdminService(self.uow)
        return self._admin_service

    def setup(self, dp: Dispatcher) -> None:
        """Регистрация зависимостей в диспетчере"""
        logger.info("Setting up dependencies")
        
        # Регистрируем все сервисы в workflow_data
        dp.workflow_data.update({
            "novel_service": self.novel_service,
            "referral_service": self.referral_service,
            "payment_service": self.payment_service,
            "admin_service": self.admin_service,
            "uow": self.uow
        })
        
        logger.info("Dependencies setup completed")

    async def on_startup(self) -> None:
        """Инициализация при запуске"""
        logger.info("Initializing container")
        await self.db.create_all()
        logger.info("Container initialized")

    async def on_shutdown(self) -> None:
        """Очистка при завершении"""
        logger.info("Shutting down container")
        if self._db:
            await self.db.engine.dispose()
        logger.info("Container shut down")