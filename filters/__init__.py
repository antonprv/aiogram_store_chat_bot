# В файлах is_user и is_admin смотрим на id пользователя,
# отправившего сообщение, и проверяем, кто он.
# Для этого используем функционал filters у диспетчера aiogram.
from .is_admin import IsAdmin
from .is_user import IsUser
