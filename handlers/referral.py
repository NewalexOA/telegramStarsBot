from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from services.referral import ReferralService
from keyboards.subscription import get_subscription_keyboard
from filters.referral import ReferralCommandFilter

router = Router()

@router.message(Command("ref"))
async def cmd_ref(
    message: Message,
    referral_service: ReferralService,
    l10n
):
    """Получение реферальной ссылки"""
    link = await referral_service.create_referral_link(message.from_user.id)
    if not link:
        await message.answer(l10n.format_value("error-creating-link"))
        return
        
    await message.answer(
        l10n.format_value(
            "your-ref-link",
            {"link": f"https://t.me/{(await message.bot.me()).username}?start=ref_{link.code}"}
        )
    )

@router.message(Command("start"), ReferralCommandFilter())
async def cmd_start_with_ref(
    message: Message,
    referral_service: ReferralService,
    l10n
):
    """Обработка реферальных команд /start ref_code"""
    args = message.text.split()
    ref_code = args[1][4:]  # Убираем префикс 'ref_'
    
    # Обрабатываем реферальный переход
    await referral_service.process_referral_start(
        ref_code,
        message.from_user.id,
        message
    )
    
    # Показываем стандартное приветствие с кнопкой подписки
    await message.answer(
        l10n.format_value("hello-msg"),
        reply_markup=await get_subscription_keyboard(message),
        parse_mode="HTML"
    )

@router.message(F.text == "🔗 Реферальная ссылка")
async def show_ref_link(
    message: Message,
    referral_service: ReferralService,
    l10n
):
    """Показ реферальной ссылки"""
    link = await referral_service.create_referral_link(message.from_user.id)
    if not link:
        await message.answer(l10n.format_value("error-creating-link"))
        return
        
    await message.answer(
        l10n.format_value(
            "your-ref-link",
            {"link": f"https://t.me/{(await message.bot.me()).username}?start=ref_{link.code}"}
        )
    )

@router.message(F.text == "📊 Статистика")
async def show_stats(
    message: Message,
    referral_service: ReferralService,
    l10n
):
    """Показ статистики рефералов"""
    stats = await referral_service.get_user_stats(message.from_user.id)
    
    await message.answer(
        l10n.format_value(
            "referral-stats",
            {
                "total": stats["total_referrals"],
                "rewards": stats["total_rewards"],
                "types": "\n".join(
                    f"- {type_}: {count}" 
                    for type_, count in stats["rewards_by_type"].items()
                )
            }
        )
    )
