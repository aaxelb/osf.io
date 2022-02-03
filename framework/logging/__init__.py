import logging
import logging.config

try:
    import colorlog
    use_color = True
except ImportError:
    use_color = False

from website import settings

handler = logging.StreamHandler()

if settings.DEBUG_MODE and use_color:
    log_colors = colorlog.default_log_colors
    log_colors['DEBUG'] = 'cyan'

    formatter = colorlog.ColoredFormatter(
        '%(log_color)s[%(name)s]  %(levelname)s:%(reset)s %(message)s',
        reset=True,
        log_colors=log_colors,
    )
else:
    formatter = logging.Formatter(
        '[%(name)s]  %(levelname)s: %(message)s',
    )

handler.setFormatter(formatter)

mw_handler = logging.handlers.HTTPHandler(
    host='morningwhale:8666',
    url='/v0/logged-event/',
)

logger = logging.getLogger()
logger.addHandler(handler)
logger.addHandler(mw_handler)
logger.setLevel(settings.LOG_LEVEL)
