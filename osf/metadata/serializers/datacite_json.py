import json

from osf.metadata.definitions.datacite.builder import DataciteMetadataBuilder
from osf.metadata.serializers import _base


# lil helper for building nested json
def _add_json_child(parent, tag_name: str, *, is_list=False, text=None, attrib=None):
    assert isinstance(parent, (list, dict)), (
        f'expected parent to be list or dict, got type {type(parent)} (parent={parent})'
    )
    parent_is_list = isinstance(parent, list)
    if is_list:
        assert not parent_is_list
        if (text is None) and (attrib is None):
            child = []  # normal is_list case
        else:
            # HACK (part 1) to support datacite `affiliation` (repeated item without list wrapper)
            child = _json_object(tag_name, text, attrib)
    elif text and not attrib and not parent_is_list:
        child = text
    else:
        child = _json_object(tag_name, text, attrib)
    if parent_is_list:
        parent.append(child)
    else:
        if is_list and isinstance(child, dict):
            # HACK (part 2)
            parent.setdefault(tag_name, []).append(child)
        else:
            parent[tag_name] = child
    return child


def _json_object(tag_name, text, attrib) -> dict:
    json_obj = {}
    if text is not None:
        json_obj[tag_name] = text
        language = getattr(text, 'language', None)
        if language:
            json_obj['lang'] = language
    if attrib is not None:
        assert tag_name not in attrib
        json_obj.update(attrib)
    return json_obj


class DataciteJsonMetadataSerializer(_base.MetadataSerializer):
    mediatype = 'application/json'

    def filename_for_itemid(self, itemid: str):
        return f'{itemid}-datacite.json'

    def serialize(self) -> str:
        return json.dumps(
            self.metadata_as_dict(),
            indent=2,
            sort_keys=True,
        )

    def metadata_as_dict(self) -> dict:
        builder = DataciteMetadataBuilder(self.basket, _add_json_child)
        metadata_dict = {}
        builder.build(metadata_dict, self.serializer_config.get('doi_value'))
        return metadata_dict
