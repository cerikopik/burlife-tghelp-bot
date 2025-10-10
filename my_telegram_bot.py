import os
import re
import asyncio
from telegram import Bot, ReactionTypeEmoji, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackQueryHandler

# --- СЕКРЕТНЫЕ ДАННЫЕ БЕРУТСЯ ИЗ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

if not BOT_TOKEN or not GROUP_CHAT_ID:
    raise ValueError("Не найдены переменные окружения BOT_TOKEN или GROUP_CHAT_ID!")

GROUP_CHAT_ID = int(GROUP_CHAT_ID)
# --- КОНЕЦ БЛОКА С ДАННЫМИ ---


async def start(update, context):
    """Отправляет приветственное сообщение в ответ на команду /start."""
    user_name = update.message.from_user.first_name
    welcome_text = (
        f"Здравствуйте, {user_name}!\n\n"
        "Я бот для связи с администрацией сайта. "
        "Пожалуйста, введите ваш код (4 символа) или отправьте фотографию."
    )
    await update.message.reply_text(welcome_text)


async def forwarder(update, context):
    """Пересылает сообщение пользователя и добавляет информацию о нем с кнопками."""
    user = update.message.from_user
    first_name = escape_markdown(user.first_name, version=2)
    last_name = escape_markdown(user.last_name or '', version=2)
    user_id = user.id
    username = escape_markdown(user.username or 'не указан', version=2)
    
    user_info = (
        f"📩 Новое сообщение от пользователя:\n\n"
        f"👤 Имя: {first_name} {last_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🔗 Юзернейм: @{username}"
    )

    # ⭐ 1. Создаем две кнопки в одном ряду
    keyboard = [
        [
            InlineKeyboardButton("✅ Ответить шаблоном", callback_data=f"reply_to_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_to_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=user_info,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    
    await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    await update.message.reply_text("Спасибо! Ваше сообщение принято. Мы скоро с вами свяжемся.")


# ↓↓↓ ОСНОВНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ ↓↓↓
async def button_handler(update, context):
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = int(data.split("_")[2])
    preset_message = ""
    success_reaction = ""

    # ⭐ 2. Определяем, какая кнопка была нажата, и готовим сообщение
    if data.startswith("reply_to_"):
        preset_message = "📧Ваша [ПРИГЛАСИТЕЛЬНАЯ ССЫЛКА](https://t\\.me/\\+k2dfZY9KPAowNjM6) в телеграм канал\\. После перехода по ссылке нажмите подать заявку, и она будет одобрена автоматически 👌"
        success_reaction = "👍"
    
    elif data.startswith("decline_to_"):
        preset_message = "К сожалению, ваша заявка была отклонена. Попробуйте позже."
        success_reaction = "👎"

    # ⭐ 3. Отправляем выбранное сообщение и обновляем интерфейс
    if preset_message:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=preset_message,
                parse_mode='MarkdownV2'
            )
            
            # Убираем обе кнопки
            await query.edit_message_reply_markup(reply_markup=None)
            # Ставим соответствующую реакцию
            await query.message.set_reaction(reaction=ReactionTypeEmoji(success_reaction))

        except Exception as e:
            await query.edit_message_reply_markup(reply_markup=None)
            print(f"Не удалось отправить ответ пользователю {user_id}. Ошибка: {e}")


def main():
    """Запускает бота и настраивает все обработчики."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.Chat(chat_id=GROUP_CHAT_ID), forwarder))
    
    print("Бот запущен (с двумя кнопками)...")
    application.run_polling()


if __name__ == '__main__':
    main()
