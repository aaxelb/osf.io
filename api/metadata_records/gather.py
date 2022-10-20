import rdflib

from osf.models import Guid


OSF_IO = rdflib.Namespace('https://osf.io/')
OSF = rdflib.Namespace('https://osf.io/vocab/2022')
DCT = rdflib.DCTERMS


def contextualized_graph():
    g = rdflib.Graph()
    g.bind('osf', OSF)
    g.bind('osf.io', OSF_IO)
    g.bind('dct', DCT)
    return g


class MetadataGatherer:
    def __init__(self, guid_id, sparse=True):
        self.guid_irl = OSF_IO[guid_id]
        self.guid_instance = Guid.load(guid_id)
        self.sparse = sparse

    def gather(self, into_graph=None):
        graph = into_graph or contextualized_graph()
        for triple in self._gather_core_triples():
            graph.add(triple)
        return graph

    def _gather_core_triples(self):
        return [
            (self.guid_irl, DCT.identifier, self.guid_irl),
            (self.guid_irl, DCT.title, rdflib.Literal(self.guid_instance.referent.title)),
        ]
        # dct:creator
        # dct:title
        # dct:publisher
        # dct:available
        # dct:subject
        # dct:contributor
        # dct:date
        # dct:language
        # dc:type
        # osf:resourcetypegeneral
        # dct:extent
        # dct:format
        # osf:version
        # dct:rights
        # dct:description
        # osf:affiliatedInstitution
        # osf:funder
        # osf:relatedIdentifier
        # osf:keyword
        # dct:hasPart
        # dct:relation
        # osf:hasChild
