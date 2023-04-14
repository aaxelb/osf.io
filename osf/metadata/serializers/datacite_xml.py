import logging

from lxml import etree

from osf.metadata.definitions import DataciteXmlschemaDefinition
from osf.metadata.definitions.datacite.builder import DataciteMetadataBuilder
from osf.metadata.serializers import _base


logger = logging.getLogger(__name__)


DATACITE_NS = 'http://datacite.org/schema/kernel-4'
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def _add_xml_child(parent, tag_name, *, is_list=False, text=None, attrib=None):
    child = etree.SubElement(parent, etree.QName(DATACITE_NS, tag_name), attrib=attrib or {})
    if text is not None:
        child.text = text
        language = getattr(text, 'language', None)
        if language:
            child.attrib[XML_LANG] = language
    return child


class DataciteXmlMetadataSerializer(_base.MetadataSerializer):
    mediatype = 'application/xml'

    def filename_for_itemid(self, itemid):
        return f'{itemid}-datacite.xml'

    def serialize(self) -> bytes:
        xml_tree = self.metadata_as_etree()
        return etree.tostring(
            xml_tree,
            encoding='utf-8',
            pretty_print=True,
            xml_declaration=True,
        )

    def metadata_as_etree(self):
        builder = DataciteMetadataBuilder(self.basket, _add_xml_child)
        xml_root = etree.Element(
            etree.QName(DATACITE_NS, 'resource'),
            nsmap={None: DATACITE_NS},
        )
        builder.build(xml_root, self.serializer_config.get('doi_value'))
        xml_tree = etree.ElementTree(xml_root)
        DataciteXmlschemaDefinition().raise_objections(xml_tree)
        return xml_tree
