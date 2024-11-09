import structlog
from unit_of_work.unit_of_work import UnitOfWork
from services.novel import NovelService

logger = structlog.get_logger()

class PaymentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def process_payment(
        self,
        user_id: int,
        payload: str,
        amount: int,
        novel_service: NovelService
    ) -> None:
        """Обработка успешного платежа"""
        try:
            if payload == "novel_restart":
                novel_state = await novel_service.get_novel_state(user_id)
                if novel_state:
                    novel_state.needs_payment = False
                    await novel_service.update_novel_state(novel_state)
                    logger.info(f"Processed restart payment for user {user_id}")
            
            # Здесь можно добавить обработку других типов платежей
            
            async with self.uow as uow:
                # Сохраняем информацию о платеже
                await uow.payments.create(
                    user_id=user_id,
                    amount=amount,
                    payload=payload
                )
                await uow.commit()
                
        except Exception as e:
            logger.error(f"Error processing payment: {e}", exc_info=True)
            raise 