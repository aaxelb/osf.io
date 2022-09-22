from .exceptions import InvalidTagManifest
from .hash import BAGIT_HASH_ALGORITHMS
from .manifest import BagDataManifest, BagTagManifest, ManifestEntry
from .opener import BagOpener


class Bag:

    @classmethod
    def load_existing_bag_from_tagmanifest_hash(
        cls,
        opener,
        tagmanifest_hash,
        hash_algorithm_name,
    ):
        entry_of_tagmanifest = ManifestEntry(
            f'tagmanifest-{hash_algorithm_name}.txt',
            tagmanifest_hash,
        )
        tagmanifest = BagTagManifest.from_lines(
            opener.open_file(entry_of_tagmanifest)
        )

        manifest = None
        manifest_entry = tagmanifest.get_file_hash(
            f'manifest-{hash_algorithm_name}.txt',
        )
        if manifest_entry:
            manifest = BagDataManifest.from_lines(
                opener.open_file(manifest_entry)
            )

        bag = cls(opener)
        bag._manifest = manifest
        bag._tagmanifest = tagmanifest
        return bag

    @classmethod
    def generate_bag_for_osfstorage(cls, osfstorage_root):
        manifest = BagDataManifest()
        tagmanifest = BagDataManifest()
        # add manifest entry for latest version of each file
        # add tagmanifest entry for node tagfiles and file tagfiles
        # store complete manifests... somewhere

    def __init__(self, opener: BagOpener):
        self._opener = opener
        self._manifest = BagDataManifest()
        self._tagmanifest = BagTagManifest()

        # TODO: handle multiple/different hash algorithms
        self._hash_algorithm_name = 'sha256'

    def _hash_file_content(self, file_content):
        if not isinstance(file_content, (bytes, str)):
            got_type = type(file_content)
            raise ValueError(f'Bag._hash_file_content expected bytes or str (got {got_type})')

        file_bytes = (
            file_content
            if isinstance(file_content, bytes)
            else bytes(file_content, encoding='utf')
        )
        return BAGIT_HASH_ALGORITHMS[self._hash_algorithm_name](file_bytes).hexdigest()

    @property
    def data_address(self):
        data_manifest_file_path = f'manifest-{self.hash_algorithm_name}.txt'
        try:
            return self.get_file_hash(file_path=data_manifest_file_path)
        except KeyError:
            raise InvalidTagManifest('missing manifest-<algorithm>.txt file')

    def put_tagfile(self, tagfile_path, tagfile_content):
        tagfile_entry = ManifestEntry(
            file_hash=self._hash_file_content(tagfile_content),
            file_path=tagfile_path,
        )
        if tagfile_entry.is_data_path:
            raise ValueError(f'cannot add a tagfile in the `data/` directory! `tagfile_path` must not start with "data/" (got "{tagfile_path}")')
        self._tagmanifest.add_entry(tagfile_entry)

    def put_data_file_entry(self, file_path, file_hash):
        file_entry = ManifestEntry(file_path, file_hash)
        if not file_entry.is_data_path:
            raise ValueError(f'cannot add a data file outside of the `data/` directory! `file_path` must start with "data/" (got "{file_path}")')
        self._manifest.add_entry(file_entry)

    def put_file_metadata(self, file_entry, tagfile_name, tagfile_content):
        if not file_entry.is_data_path:
            raise ValueError(f'cannot add a file-specific tagfile for another tagfile! `file_entry.file_path` must start with "data/" (entry: {file_entry})')
        if '/' in tagfile_name:
            raise ValueError(f'cannot add a file-specific tagfile with a "/" in its name (got "{tagfile_name}")')

        self.put_tagfile(
            tagfile_path=f'meta{file_entry.file_path}/{tagfile_name}',
            tagfile_content=tagfile_content,
        )
