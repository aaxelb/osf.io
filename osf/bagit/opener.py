import abc
import io
import pathlib
import urllib

from .manifest import ManifestEntry


@abc.ABC
class BagOpener:
    # TODO: asyncio
    def open_file(self, entry: ManifestEntry):
        raise NotImplementedError


# TODO: class FetchDotTxtBagOpener(BagOpener):
# TODO: class OsfFileVersionBagOpener(BagOpener):


class InmemoryBagOpener(BagOpener):
    def __init__(self, entry_to_content_dict=None):
        self._entry_to_content = entry_to_content_dict or {}

    def add_inmemory_file(self, manifest_entry, file_content):
        self._entry_to_content[manifest_entry] = file_content

    def open_file(self, manifest_entry):
        file_content = self._entry_to_content.get(manifest_entry)
        yield from io.StringIO(file_content)


class LocalFileBagOpener(BagOpener):
    def __init__(self, base_dir):
        self._base_dir = base_dir

    def open_file(self, entry):
        local_path = pathlib.Path(self._base_dir) / entry.file_path
        with open(local_path, 'rb') as file:
            yield from file


class ContentAddressedArchiveBagOpener(BagOpener):
    def __init__(self, base_url):
        self._base_url = base_url.strip('/')  # guarantee no trailing slash

    def open_file(self, entry):
        full_url = f'{self._base_url}/{entry.file_hash}'
        with urllib.request.urlopen(full_url) as response:
            yield from response
