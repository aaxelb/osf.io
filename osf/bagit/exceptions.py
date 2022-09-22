class BagitError(Exception):
    pass


class InvalidTagManifest(BagitError):
    pass


class CannotFindContentForEntry(BagitError):
    pass
