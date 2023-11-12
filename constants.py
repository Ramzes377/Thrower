from dataclasses import dataclass
from collections import UserString


class String(UserString):

    def __call__(self, *args, **kwargs):
        return self.data.format(**kwargs)


@dataclass(slots=True)
class Constants:
    db_request: String = "{table_name} ({specs})"

    track_switch: String = 'Воспроизведение {status}! \nПользователь: {mention}'
    skip_track_msg: String = 'Пропущено воспроизведение трека {title}! \nПользователь: {mention}'
    empty_favorite_list: String = 'У вас нет избранных треков. Возможно, вы не ставили никаких треков.'
    choose_track: String = 'Выберите трек для добавления в очередь'
    send_favorite_list: String = 'Список избранных треков отправлен в ЛС'
    force_exit: String = 'Принудительно завершено исполнение!'
    nothing_found: String = 'Ничего не найдено!'
    playlist_add_to_queue: String = 'Плейлист добавлен в очередь!'
    track_add_to_queue: String = 'Трек добавлен в очередь!'
    login_first: String = 'Сначала войдите в голосовой канал!'
    must_same_voice: String = 'Вы должны быть в том же голосовом чате!'
    youtube_thumbnail: String = "http://i3.ytimg.com/vi/{identifier}/maxresdefault.jpg"
    search_query: String = 'ytsearch:{query}'

    duration: String = 'sum(COALESCE(CAST(24 * 60 * 60 * (julianday(a."end") - julianday(a.begin)) AS INTEGER),0))'
    duration_query: String = \
        """
            SELECT a.id app_id, {duration} seconds
                FROM activity a
                    WHERE a.member_id = {member_id}
                GROUP BY a.id, a.member_id
        """.format(duration=duration, member_id='{member_id}')

    concrete_duration_query: String = \
        """
            SELECT a.id app_id, {duration} seconds
            FROM activity a
                JOIN role r ON r.id = {role_id} and r.app_id = a.id
                WHERE a.member_id = {member_id}
            GROUP BY a.id, a.member_id
        """.format(duration=duration, member_id='{member_id}',
                   role_id='{role_id}')

    wait_cooldown: String = 'Для создания нужно подождать {cooldown} секунд!'
    already_created: String = 'Каналы уже созданы!'
    cleaning_started: String = 'Начата очистка переписки . . .'
    successfully_deleted: String = 'Успешно удалено {counter} сообщений!'
    game_embed_header: String = 'Зарегистрировано в игре '
    game_request: String = "Запрос по игре {name}"
    game_not_played_header: String = 'Вы не играли в эту игру или Discord не смог это обнаружить'
    game_not_played_body: String = 'Если вам нужна эта функция, то зайдите в Настройки пользователя\\Игровая активность\\Отображать в статусе игру в которую сейчас играете'
    channel_creation_error: String = 'Ошибка: {error}'
    successfully_created_channels: String = 'Успешно созданы каналы!'
    messages_to_delete: String = 'Будет удалено {n} сообщений!'
    incorrect_gamerole_mention: String = 'Неверный формат упоминания игровой роли!'
    bot_signature: String = 'Великий бот - {name}'
    added_to_queue: String = '{name} - {count} треков'
    session_name: String = "Сессия {name}'а"
    cog_started: String = 'Cog {name} have been started!'
    active_session: String = "Активен сеанс: {name}"
    log_reflect_begin: String = 'Begin reflect execution of coro fabric: {coro_fabric}'
    log_reflect_main_response: String = 'Response of main session: {response}'
    log_reflect_execution: String = 'Reflect execution with session: {session}'
    log_object_creation: String = 'Trying to create object: {object}'
    log_unique_error: String = 'Object already exists!'
    log_creation_error: String = 'Error on object creation: {error}'
    log_get_object: String = 'Trying to get object: {filters}'
    log_success_get: String = 'Succesfully get object: {object}!'
    log_unavailable_object: String = "Can't access to object: {details}!"
    log_all_rows: String = 'Request to get all rows of type: {request}, filter: {filter}'
    log_success_all_get: String = 'Successfully get {count} of objects of type {type}!'
    log_update_object: String = 'Trying to update object of type: {type} with params: {params}'
    log_success_updated: String = 'Successfully update object!'
    log_error_on_update: String = 'Error when object updating: {error}'
    log_delete_object: String = 'Trying to delete object: {filters}'
    log_cant_delete: String = "Can't delete object!"


def wrap_attributes(instance):
    for attribute, default_value in instance.__annotations__.items():
        value: str = getattr(instance, attribute)
        setattr(instance, attribute, default_value(value))

    return instance


constants = wrap_attributes(Constants())
