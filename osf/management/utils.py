import datetime


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


# same as datetime.date.fromisoformat in py3.7+
def date_fromisoformat(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
