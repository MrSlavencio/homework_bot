class TokenNotExist(Exception):
    """Исключение для отсутствующих переменных виртуального окружения."""

    pass


class ResponseCodeError(Exception):
    """Исключение для кода ответа API-сервера отличного от 200."""

    pass


class ResponseIsEmptyDict(Exception):
    """Ответ от сервера - пустой словарь."""

    pass


class HWStatusUnknown(Exception):
    """Статус домашней работы не из словаря."""

    pass


class SendMessageError(Exception):
    """Ошибка при отправке сообщения."""

    pass
