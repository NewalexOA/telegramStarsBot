hello-msg =
    <b>Добро пожаловать в Novell AI — интерактивную визуальную новеллу, стирающую границы между пользователем и игрой</b>

    <b>ЧТО ТЕБЯ ЖДЁТ?</b>

    🕊️ <b>Свобода выбора.</b> Здесь нет заранее написанных ответов — выражай свои мысли так, как считаешь нужным.

    📝 <b>Влияние на сюжет.</b> Каждый ответ формирует развитие истории и влияет на отношения с героями.

    🔀 <b>Эмоциональная связь.</b> Персонажи будут говорить с тобой напрямую, раскрывая свои мысли и чувства. Они живут, дышат и реагируют на твои решения.

    ❗️<b>Первое прохождение новеллы бесплатно для каждого пользователя.</b> Перепройти историю можно за ⭐️, чтобы узнать, как изменятся события и взаимоотношения.

    👥 <b>Получить скидку можно, пригласив друга по реферальной ссылке.</b>

    🫰🏻<b>Проект в самом начале пути, и твоя поддержка очень важна для роста.</b> Если тебе понравилась игра, можешь поддержать нас, нажав на кнопку “Донат”. Будем очень признательны!

    💌 <b>Наши донатеры получат доступ к тестированию новых глав и сюжетов до их релиза.</b> Стань частью команды первооткрывателей!

    🙋 <b>Нам важно твоё мнение!</b> Делись своими впечатлениями, предлагай идеи, отправляй свои истории — мы открыты к твоим предложениям. Напиши нам: @novelladmin

    💬 <b>Готов погрузиться в мир Novell AI и узнать, каким будет твой путь? Тогда вперёд!</b>


donate-invoice-title =
    Донат автору

donate-invoice-description =
    Отблагодарить суммой в {$amount ->
        [one] {$amount} звезду
        [few] {$amount} звезды
       *[other] {$amount} звёзд
    }

donate-button-pay =
    Оплатить {$amount} XTR

donate-button-cancel =
    Отменить операцию

donate-input-error =
    Пожалуйста, введите сумму в формате <code>/donate</code> [ЧИСЛО], где [ЧИСЛО] это сумма доната, от ⭐️ 1 до ⭐️ 2500.

    Примеры:
    <code>/donate 100</code> - задонатить 100 ⭐️
    <code>/donate 500</code> - задонатить 500 ⭐️
    <code>/donate 1000</code> - задонатить 1000 ⭐️

donate-paysupport-tid-tip =
    <blockquote>Получить его вы можете после того, как оплатите донат.
    Просто нажмите на сообщение <b>"Вы успешно перевели ⭐️ .."</b> и скопируйте оттуда ID транзакции.</blockquote>

donate-paysupport-message =
    Если вы хотите оформить рефанд, воспользуйтесь командой /refund

    🤓 Вам понадобится ID транзакции.
    {donate-paysupport-tid-tip}

donate-refund-input-error =
    Пожалуйста, укажите идентификатор транзакции в формате <code>/refund [id]</code>, где [id] это идентификатор транзакции, который вы получили после доната.

    {donate-paysupport-tid-tip}

donate-refund-success =
    Рефанд произведен успешно. Потраченные звёзды уже вернулись на ваш счёт в Telegram.

donate-refund-code-not-found =
    Транзакция с указанным идентификатором не найдена. Пожалуйста, проверьте введенные данные и повторите ещё раз.

donate-refund-already-refunded =
    Рефанд по этой транзакции уже был ранее произведен.

# no html etc. (msg for callback answer)
donate-cancel-payment =
    😢 Донат отменен.

donate-successful-payment =
    <b>🫡 Спасибо!</b>
    Ваш донат успешно принят.

hello-owner =
    <b>👊 Hello, owner!</b>

ping-msg =
    <b>👊 Up & Running!</b>

media-msg =
    <b>🫡 Nice media <i>(I guess)</i>!</b>

subscription-required =
    Для использования бота необходимо подписаться на наш канал:

subscription-confirmed =
    Спасибо за подписку! Теперь вы можете использовать бота

subscription-check-failed =
    Вы все еще не подписаны на канал 😢

novel-started = Новелла запущена! Давай познакомимся...
novel-error = Произошла ошибка при запуске новеллы. Пожалуйста, попробуйте позже.

menu-novel = 🎮 Новелла
menu-donate = 💝 Донат
menu-restart = 🔄 Рестарт
menu-help = ❓ Помощь

menu-choose = Выберите действие:

help = 
    <b>Доступные команды:</b>
    
    🎮 <b>Новелла</b> - Начать или продолжить историю
    💝 <b>Донат</b> - Поддержать автора
    🔄 <b>Рестарт</b> - Начать новую игру
    ❓ <b>Помощь</b> - Показать это сообщение
    
    <i>Для начала игры подпишитесь на канал и нажмите кнопку "Запустить новеллу"</i>

restart-invoice-title = 
    Перезапуск новеллы

restart-invoice-description = 
    Оплата повторного прохождения новеллы

restart-button-pay = 
    Оплатить {$amount} XTR

restart-button-cancel = 
    Отменить

restart-cancel-payment = 
    Оплата рестарта отменена

referral-link-msg =
    🔗 Вот ваша реферальная ссылка:
    
    <code>{$link}</code>
    
    {$reward}

referral-link-error =
    😢 Не удалось сгенерировать реферальную ссылку. Пожалуйста, попробуйте позже.

# Добавляем новые строки для очистки базы
clear-db-button = 🗑 Очистить базу
clear-db-confirm = ⚠️ Вы уверены, что хотите очистить базу данных? Это действие необратимо.
clear-db-success = База данных успешно очищена
clear-db-error = Ошибка при очистке базы данных: {$error}
