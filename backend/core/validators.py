import re
from django.core.exceptions import ValidationError


def validate_format(value):
    '''Валидатор, проверяющий строку на соответствие заданному шаблону.'''

    pattern = r'^[\w.@+-]+$'
    if re.match(pattern, value) is None:
        raise ValidationError(f'Формат {value} не соответствует допустимому.')
