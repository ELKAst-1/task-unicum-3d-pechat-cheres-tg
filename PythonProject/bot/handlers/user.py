from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.states import UserStates
from bot.utils.config import GROUPS, PRINT_PURPOSES
import os
import uuid

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    from bot.utils.config import ADMIN_CHAT_IDS

    if user.id in ADMIN_CHAT_IDS:
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n\n"
            f"Вы вошли как администратор.\n"
            f"Используйте /admin для управления заявками."
        )
    else:
        await update.message.reply_text(
    f"Привет, {user.first_name}!\n\n"
    f"Я помогу вам создать заявку на 3D-печать.\n\n"
    f"🛠️ Доступные команды:\n"
    f"• /new_request — создать новую заявку\n"
    f"• /my_requests — посмотреть ваши заявки\n"
    f"• /cancel — отменить текущее действие\n\n"
    f"Начните с /new_request, когда будете готовы!"
)
    return ConversationHandler.END

async def new_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Давайте создадим заявку на 3D-печать.\n\n"
        "Введите ваше имя:"
    )
    return UserStates.FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("Введите вашу фамилию:")
    return UserStates.LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    
    groups = context.bot_data.get('groups', [])
    
    if not groups:
        await update.message.reply_text(
            "Список групп пуст. Обратитесь к администратору."
        )
        return ConversationHandler.END
    
    keyboard = [[group] for group in groups]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Выберите вашу группу:",
        reply_markup=reply_markup
    )
    return UserStates.GROUP

async def get_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['group'] = update.message.text
    
    purposes = context.bot_data.get('purposes', [])
    
    if not purposes:
        await update.message.reply_text(
            "Список целей печати пуст. Обратитесь к администратору."
        )
        return ConversationHandler.END
    
    keyboard = [[purpose] for purpose in purposes]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Выберите цель печати:",
        reply_markup=reply_markup
    )
    return UserStates.PURPOSE

async def get_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['purpose'] = update.message.text
    
    await update.message.reply_text(
        "Отлично! Теперь прикрепите .stl файл для печати:",
        reply_markup=ReplyKeyboardRemove()
    )
    return UserStates.FILE

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    if not document or not document.file_name.endswith('.stl'):
        await update.message.reply_text(
            "Пожалуйста, прикрепите файл с расширением .stl"
        )
        return UserStates.FILE
    
    db = context.bot_data.get('db')
    
    if not db:
        await update.message.reply_text(
            "Ошибка: база данных не инициализирована. Обратитесь к администратору."
        )
        return ConversationHandler.END
    
    try:
        request_id = str(uuid.uuid4())[:8]
        
        file = await context.bot.get_file(document.file_id)
        
        os.makedirs('uploads', exist_ok=True)
        final_filename = f"{request_id}_{document.file_name}"
        file_path = f"uploads/{final_filename}"
        await file.download_to_drive(file_path)
        
        request_data = {
            'id': request_id,
            'first_name': context.user_data['first_name'],
            'last_name': context.user_data['last_name'],
            'group': context.user_data['group'],
            'purpose': context.user_data['purpose'],
            'file_path': file_path,
            'file_name': final_filename,
            'telegram_id': update.effective_user.id,
            'username': update.effective_user.username or ''
        }
        
        db.add_request(request_data)
        
        pending_count = db.get_pending_count()
        queue_position = pending_count
        
        await update.message.reply_text(
            f"✅ Заявка принята!\n\n"
            f"ID заявки: {request_id}\n"
            f"Перед вами в очереди: {queue_position-1} человек(а)\n\n"
            f"Вы получите уведомление при изменении статуса."
        )
        
        from bot.utils.config import ADMIN_CHAT_IDS

        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"📬 Новая заявка #{request_id}\n"
                         f"От: {request_data['first_name']} {request_data['last_name']}\n"
                         f"Группа: {request_data['group']}\n"
                         f"Цель: {request_data['purpose']}\n"
                         f"Файл: {final_filename}"
                )
            except Exception as e:
                print(f"Не удалось отправить админу {admin_id}: {e}")
                
    except Exception as e:
        print(f"Ошибка при обработке заявки: {e}")
        
        error_message = "Произошла ошибка при обработке заявки."
        
        if "quota" in str(e).lower():
            error_message += "\n\n⚠️ Превышена квота хранилища.\nОбратитесь к администратору."
        else:
            error_message += "\nПопробуйте позже или обратитесь к администратору."
        
        await update.message.reply_text(error_message)
    
    return ConversationHandler.END

async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих заявок"""
    user_id = update.effective_user.id
    db = context.bot_data.get('db')
    
    if not db:
        await update.message.reply_text("Ошибка: база данных не инициализирована.")
        return
    
    all_requests = db.get_all_requests()
    user_requests = [req for req in all_requests if str(req.get('telegram_id')) == str(user_id)]
    
    if not user_requests:
        await update.message.reply_text(
            "📋 У вас пока нет заявок.\n\n"
            "Используйте /new_request чтобы создать новую заявку."
        )
        return
    
    text = "📋 Ваши заявки:\n\n"
    
    for req in user_requests:
        status_emoji = {
            'В очереди': '⚪',
            'В работе': '🟡',
            'Готово': '🟢'
        }.get(req.get('status', ''), '⚪')
        
        text += (
            f"{status_emoji} Заявка #{req.get('id')[:8]}\n"
            f"📚 Группа: {req.get('group')}\n"
            f"🎯 Цель: {req.get('purpose')}\n"
            f"📅 Дата: {req.get('date')}\n"
            f"📊 Статус: {req.get('status')}\n"
        )
        
        comment = req.get('comment', '')
        if comment:
            text += f"💬 Комментарий: {comment}\n"
        
        text += "───────────────\n"
    
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Создание заявки отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
