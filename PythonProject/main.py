import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from bot.handlers import user, admin
from bot.services.local_db import LocalDatabase
from bot.services.scheduler import SchedulerService
from bot.utils.states import UserStates, AdminStates
from bot.utils.config import TELEGRAM_BOT_TOKEN
# main.py

from bot.handlers.admin import (
    admin_menu,
    view_requests,
    view_request_detail,
    accept_request,
    complete_request,
    archive_request,
    send_file_to_admin,
    start_add_comment,
    save_comment,
    start_message_user,
    send_message_to_user,
    view_archive,
    cleanup_requests,
    navigate_pages,
    back_to_admin_menu,
    manage_groups,
    manage_purposes,
    add_group,
    save_group,
    remove_group,
    delete_group,
    add_purpose,
    save_purpose,
    remove_purpose,
    delete_purpose,
    export_to_excel  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
   
    application.bot_data['groups'] = ['ИВТ-21', 'ИВТ-22', 'ИВТ-23', 'ИВТ-24']
    application.bot_data['purposes'] = ['Учебный проект', 'Курсовая работа', 'Диплом', 'Личное использование', 'Другое']
    
    try:
        db = LocalDatabase('data/requests.json', 'data/archive.json')
        application.bot_data['db'] = db
        logger.info("Локальная база данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    try:
        scheduler_service = SchedulerService(db)
        scheduler_service.start()
        application.bot_data['scheduler_service'] = scheduler_service
        logger.info("Планировщик задач запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска планировщика: {e}")
    
    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_request', user.new_request)],
        states={
            UserStates.FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.get_first_name)],
            UserStates.LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.get_last_name)],
            UserStates.GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.get_group)],
            UserStates.PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user.get_purpose)],
            UserStates.FILE: [MessageHandler(filters.Document.ALL, user.get_file)],
        },
        fallbacks=[CommandHandler('cancel', user.cancel)]
    )
    
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin.admin_menu)],
        states={
            AdminStates.VIEW_REQUESTS: [
                CallbackQueryHandler(admin.view_requests, pattern='^view_requests$'),
                CallbackQueryHandler(admin.view_request_detail, pattern='^detail_'),
                CallbackQueryHandler(admin.view_archive, pattern='^view_archive$'),
                CallbackQueryHandler(admin.cleanup_requests, pattern='^cleanup_requests$'),
                CallbackQueryHandler(admin.manage_groups, pattern='^manage_groups$'),
                CallbackQueryHandler(admin.manage_purposes, pattern='^manage_purposes$'),
                CallbackQueryHandler(admin.accept_request, pattern='^accept_'),
                CallbackQueryHandler(admin.complete_request, pattern='^complete_'),
                CallbackQueryHandler(admin.archive_request, pattern='^archive_'),
                CallbackQueryHandler(admin.send_file_to_admin, pattern='^send_file_admin_'),
                CallbackQueryHandler(admin.start_add_comment, pattern='^add_comment_'),
                CallbackQueryHandler(admin.start_message_user, pattern='^message_user_'),
                CallbackQueryHandler(admin.navigate_pages, pattern='^(next_page|prev_page)$'),
                CallbackQueryHandler(admin.back_to_admin_menu, pattern='^admin_main_menu$'),
                CallbackQueryHandler(export_to_excel, pattern='^export_excel$'),
                CallbackQueryHandler(admin.add_group, pattern='^add_group$'),
                CallbackQueryHandler(admin.remove_group, pattern='^remove_group$'),
                CallbackQueryHandler(admin.delete_group, pattern='^delete_group_'),
                CallbackQueryHandler(admin.add_purpose, pattern='^add_purpose$'),
                CallbackQueryHandler(admin.remove_purpose, pattern='^remove_purpose$'),
                CallbackQueryHandler(admin.delete_purpose, pattern='^delete_purpose_'),
            ],
            AdminStates.MANAGE_GROUPS: [
                CallbackQueryHandler(admin.add_group, pattern='^add_group$'),
                CallbackQueryHandler(admin.remove_group, pattern='^remove_group$'),
                CallbackQueryHandler(admin.delete_group, pattern='^delete_group_'),
                CallbackQueryHandler(admin.back_to_admin_menu, pattern='^admin_main_menu$'),
                CallbackQueryHandler(admin.manage_groups, pattern='^manage_groups$'),
            ],
            AdminStates.MANAGE_PURPOSES: [
                CallbackQueryHandler(admin.add_purpose, pattern='^add_purpose$'),
                CallbackQueryHandler(admin.remove_purpose, pattern='^remove_purpose$'),
                CallbackQueryHandler(admin.delete_purpose, pattern='^delete_purpose_'),
                CallbackQueryHandler(admin.back_to_admin_menu, pattern='^admin_main_menu$'),
                CallbackQueryHandler(admin.manage_purposes, pattern='^manage_purposes$'),
            ],
            AdminStates.ADDING_GROUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.save_group)
            ],
            AdminStates.ADDING_PURPOSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.save_purpose)
            ],
            AdminStates.ADDING_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.save_comment)
            ],
            AdminStates.MESSAGING_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.send_message_to_user)
            ],
        },
        fallbacks=[CommandHandler('cancel', user.cancel)],
        per_message=False
        
    )
    
    application.add_handler(CommandHandler('start', user.start))
    application.add_handler(CommandHandler('my_requests', user.my_requests))
    application.add_handler(user_conv_handler)
    application.add_handler(admin_conv_handler)
    
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
