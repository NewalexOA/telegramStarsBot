import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluent.runtime import FluentLocalization

# Declare router
router = Router()
router.message.filter(F.chat.type == "private")

# Declare logger
logger = structlog.get_logger()

# Declare handlers
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("hello-msg"))


@router.message(Command("donate", "donat", "донат"))
async def cmd_donate(message: Message, command: CommandObject, l10n: FluentLocalization):
    # проверяем, что в команду передан аргумент кол-ва. звёзд для доната
    # если нет, то не обрабатываем команду и возвращаем сообщение с ошибкой
    # также проверяем, чтобы кол-во. звёзд для доната было не менее 1 и не более 2500
    # (текущие лимиты в Telegram API)
    if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
        await message.answer(l10n.format_value("donate-input-error"))
        return

    # сумма доната
    amount = int(command.args)

    # формируем клавиатуру
    # это можно не делать, ТГ сам добавит клавиатуру
    # но если нужна кастомная, то можно добавить свою
    # (вхождение XTR и эмоджик ⭐️ ТГ автоматически поменяет на иконку ТГ звёзд)
    # ВАЖНО! у кнопки платежа надо поставить аргумент pay=True
    kb = InlineKeyboardBuilder()
    kb.button(
        text=l10n.format_value("donate-button-pay", {"amount": amount}),
        pay=True # важный параметр!
    )
    kb.button(
        text=l10n.format_value("donate-button-cancel"),
        callback_data="donate_cancel"
    )
    kb.adjust(1) # все кнопки в 1 ряд

    # ФОРМИРУЕМ ИНВОЙС
    # для платежей Telegram Stars список цен
    # обязан состоять только из 1 элемента
    prices = [LabeledPrice(label="XTR", amount=amount)]

    await message.answer_invoice(
        title=l10n.format_value("donate-invoice-title"),
        description=l10n.format_value("donate-invoice-description", {"amount": amount}),
        prices=prices,

        # provider_token оставляем пустым
        provider_token="",

        # тут передаем любые данные (пэйлоад)
        # например, идентификатор услуги которую покупает юзер
        # или уровень подписки
        # или еще что-то такое
        # мы же передадим кол-во. задоначенных звёзд (просто так)
        payload=f"{amount}_stars",

        # XTR - это код валюты Telegram Stars
        currency="XTR",

        # не забываем передать нашу кастомную клавиатуру
        # напоминаю, что это можно не делать
        # ТГ сам добавит кнопку оплаты, если тут ничего не передавать
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery, l10n: FluentLocalization):
    await callback.answer(l10n.format_value("donate-cancel-payment"))

    await callback.message.delete()


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("donate-paysupport-message"))


@router.message(Command("refund"))
async def cmd_refund(message: Message, bot: Bot, command: CommandObject, l10n: FluentLocalization):
    # ID транзакции для рефанда
    # по ней можно понять, какой товар/услугу возвращает человек
    # и по правилам ТГ, вы можете ОТКАЗАТЬ в рефанде
    # но только в том случае, если условия отказа прописаны в Terms of Service вашего бота
    # ...
    # для примера, мы будем разрешать любой возврат звезд в любое время
    t_id = command.args

    # чекаем, указан ли ID транзакции
    if t_id is None:
        await message.answer(l10n.format_value("donate-refund-input-error"))
        return

    # пытаемся сделать рефанд
    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=t_id
        )
        await message.answer(l10n.format_value("donate-refund-success"))

    except TelegramBadRequest as e:
        err_text = l10n.format_value("donate-refund-code-not-found")

        if "CHARGE_ALREADY_REFUNDED" in e.message:
            err_text = l10n.format_value("donate-refund-already-refunded")

        await message.answer(err_text)
        return


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery, l10n: FluentLocalization):
    # смысл on_pre_checkout_query такой же, как и в любых других платежах
    # бот должен ответить в течение 10 секунд
    # ..
    # тут можно/нужно проверить доступность товара/услуги, прямо перед оплатой
    # ..
    # так как у нас просто донат, мы просто всегда отвечаем положительно
    await query.answer(ok=True)

    # либо вот так, если по какой-то причине надо отказать в проведении платежа
    #await query.answer(
    #    ok=False,
    #    error_message="Причина почему отказывем (прим. кончился товар)"
    #)


@router.message(F.successful_payment)
async def on_successfull_payment(message: Message, l10n: FluentLocalization):
    # И наконец обработка УСПЕШНОГО ПЛАТЕЖА
    # тут мы получаем объект message.successful_payment
    # в котором содержится ID транзакции, пэйлод который мы указывали при создании инвойса
    # и все такое прочее
    # ..
    # мы же просто передаем сообщение об успешном донате

    await message.answer(
        l10n.format_value(
            "donate-successful-payment",
            {"t_id": message.successful_payment.telegram_payment_charge_id}
        ),

        # добавляем к сообщению эффект "сердечка" из стандартных реакций
        message_effect_id="5159385139981059251",

        # другие реакции (если надо)
        # 🔥 огонь - 5104841245755180586
        # 👍 лайк - 5107584321108051014
        # 👎 дизлайк - 5104858069142078462
        # ❤️ сердечко - 5159385139981059251
        # 🎉 праздник - 5046509860389126442
        # 💩 какаха - 5046589136895476101
    )





