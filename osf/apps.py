from __future__ import unicode_literals
import logging

from django.apps import AppConfig as BaseAppConfig
from django.db.models.signals import post_migrate
from osf.migrations import update_permission_groups


class AppConfig(BaseAppConfig):
    name = 'osf'
    app_label = 'osf'
    managed = True

    def ready(self):
        super(AppConfig, self).ready()
        post_migrate.connect(
            update_permission_groups,
            dispatch_uid='osf.apps.update_permissions_groups'
        )
        from framework.logging import logger
        logger.addHandler(MetricLogHandler())


class MetricLogHandler(logging.Handler):
    def emit(self, record):
        from osf.metrics import LogEvent
        LogEvent.record(
            func_name=record.funcName,
            log_level=record.levelname,
            log_message_unformatted=record.msg,
            source_ref=f'{record.pathname}:{record.lineno}',
        )
