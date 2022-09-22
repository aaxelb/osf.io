import abc
import collections
import re


class ManifestEntry(collections.namedtuple(
        'BaseManifestEntry',
        ('file_hash', 'file_path'),
)):
    HEXADECIMAL_RE = re.compile(r'[0-9a-f]+')

    @property
    def is_hex_hash(self):
        return ManifestEntry.HEXADECIMAL_RE.fullmatch(self.file_hash)

    @property
    def is_data_path(self):
        return self.file_hash.startswith('data/')

    def to_line(self):
        return ' '.join(self.file_hash, self.file_path)


@abc.ABC
class BaseManifest:
    @classmethod
    def from_lines(cls, lines):
        manifest = cls()
        entries = (
            # assumes structurally valid lines: [hash][space][path]
            ManifestEntry(*line.split(maxsplit=1))
            for line in lines
        )
        manifest.__by_hash = {
            entry.file_hash: entry
            for entry in entries
        }
        manifest.__by_path = {
            entry.file_path: entry
            for entry in manifest.__by_hash.values()
        }
        if not manifest.all_file_paths_valid():
            raise ValueError('invalid path in there')
        return manifest

    def __init__(self):
        self.__by_hash = {}
        self.__by_path = {}

    def to_lines(self):
        for entry in sorted(self.entries()):
            yield entry.to_line()

    def add_entry(self, manifest_entry):
        self.__by_hash[manifest_entry.file_hash] = manifest_entry
        self.__by_path[manifest_entry.file_path] = manifest_entry

    def entries(self):
        yield from self.__by_hash.values()

    def get_file_path(self, file_hash):
        try:
            return self.__by_hash[file_hash].file_path
        except KeyError:
            return None

    def get_file_hash(self, file_path):
        try:
            return self.__by_path[file_path].file_path
        except KeyError:
            return None

    def all_entries_valid(self) -> bool:
        return all(
            self._entry_is_valid(entry)
            for entry in self.entries()
        )

    @abc.abstractmethod
    def _entry_is_valid(self, entry) -> bool:
        return NotImplementedError


class BagDataManifest(BaseManifest):
    def _entry_is_valid(self, entry):
        return (
            entry.is_hex_hash
            and entry.is_data
        )


class BagTagManifest(BaseManifest):
    def _entry_is_valid(self, entry):
        return (
            entry.is_hex_hash
            and not entry.is_data
        )
