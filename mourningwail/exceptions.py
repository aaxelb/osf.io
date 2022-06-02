

class MourningwailError(Exception):
    """Base class for morningwail exceptions
    """
    pass


class ReportInvalid(MourningwailError):
    """Tried to save a report with invalid something-or-other
    """
    pass


class WrongYesterday(MourningwailError):
    """Tried to run a report for the present moment, but that moment has passed.
    """
    def __init__(self, wrong_yesterday, *, my_yesterday):
        return super(f'wrong:{wrong_yesterday}, mine:{my_yesterday}')
