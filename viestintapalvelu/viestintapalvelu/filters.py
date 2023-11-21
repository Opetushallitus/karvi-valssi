from logging import Filter

from django.conf import settings


class DisableLoggingInTestingFilter(Filter):
    def filter(self, record):
        return not settings.TESTING
