import hashlib


BAGIT_HASH_ALGORITHMS = {
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512,
    'md5': hashlib.md5,
}
