"""

might be considered an extension of bagit,
or an application of bagit's conceptual model
(bagit: https://www.rfc-editor.org/rfc/rfc8493.html)

a bagit:bag (slightly simplified) consists of:
    - a manifest of files in a `data/` directory (bagit:manifest)
    - a manifest of files NOT in a `data/` directory (bagit:tagmanifest)
    - some way to access file content, given a bagit:manifest-entry
        - could be a request via bagit:fetch.txt
        - could be a local filesystem directory (using the entry path)
        - could be a content-addressed archive (using the entry hash)

a bagit:manifest-entry consists of:
    - a '/'-delimited file path
    - a hash of file content
"""

from .bag import Bag

__all__ = ('Bag',)
