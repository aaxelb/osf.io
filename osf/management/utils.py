from functools import wraps
import hashlib
import logging

from django.db import connection
from django.utils.six.moves import input
import sqlparse


logger = logging.getLogger(__name__)


def print_sql(sql):
    """Pretty-print a SQL string. Also works with Django Query objects.

    >>> qs = User.objects.all()
    >>> print_sql(qs.query)
    """
    print(sqlparse.format(str(sql), reindent=True))


# From https://stackoverflow.com/a/39257511/1157536
def ask_for_confirmation(question, default=None):
    """Ask for confirmation before proceeding.
    """
    result = input('{} '.format(question))
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in 'yn':
        result = input('Please answer yes or no: ')
    return result[0].lower() == 'y'


def one_at_a_time(lock_name):
    """Decorator for a function that will conflict with itself.

    Guarantee only one instance of the function runs at any one time, enforced
    using the given `lock_name` and PostgreSOL's session-level advisory locks.
    (see https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS )

    If the decorated function is called while the lock is already held elsewhere,
    it returns `None` immediately, without calling the inner function at all.
    """
    def _decorator(inner_fn):
        @wraps(inner_fn)
        def _decorated_fn(*args, **kwargs):
            # identify the lock with a 64-bit (8-byte) hash of the given lock name
            lock_name_hash = hashlib.blake2b(bytes(lock_name), digest_size=8)
            lock_id = int(lock_name_hash.hexdigest(), base=16)

            with connection.cursor() as lock_cursor:
                lock_cursor.execute('SELECT pg_try_advisory_lock(%s);', [lock_id])
                lock_is_mine = lock_cursor.fetchone()[0]

                if not lock_is_mine:
                    logger.info('one_at_a_time: "%s" (%s) already locked; exiting happily.', [lock_name, lock_id])
                    return None

                try:
                    return inner_fn(*args, **kwargs)
                finally:
                    lock_cursor.execute('SELECT pg_advisory_unlock(%s)', [lock_id])

        return _decorated_fn
    return _decorator
