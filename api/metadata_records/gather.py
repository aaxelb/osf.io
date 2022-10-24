import itertools
import rdflib

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from osf import models
from osf.utils.identifiers import DOIValidator

from website import settings


OSF = rdflib.Namespace('https://osf.io/vocab/2022/')
DCT = rdflib.DCTERMS
A = rdflib.RDF.type


def contextualized_graph():
    g = rdflib.Graph()
    g.bind('osf', OSF)
    g.bind('dct', DCT)
    return g


def guid_irl(guid):
    if hasattr(guid, 'guids'):  # quacks like a Guid referent
        guid = guid.guids.first()
    if hasattr(guid, '_id'):  # quacks like a Guid instance
        guid = guid._id
    if not guid:
        return None  # politely skipple this triple
    if not isinstance(guid, str):
        raise ValueError('guid_irl expects str, guid instance, or guid referent')
    return rdflib.URIRef(guid, base=settings.DOMAIN)


def guid_from_irl(irl):
    if isinstance(irl, rdflib.URIRef) and irl.startswith(settings.DOMAIN):
        path = irl[len(settings.DOMAIN):].strip('/')
        if '/' not in path:
            return path
    return None


def checksum_urn(checksum_algorithm, checksum_hex):
    # TODO: register "checksum" urn namespace with iana i guess
    #       (using iana's "hash function textual names" registry)
    urn = f'urn:checksum:{checksum_algorithm}:{checksum_hex}'
    return rdflib.URIRef(urn)


def gather_guid_graph(guid_id, sparse=True):
    guids_visited = set()
    guids_to_visit = {guid_id}
    graph = contextualized_graph()
    while guids_to_visit:
        guid = guids_to_visit.pop()
        if guid in guids_visited:
            continue
        guids_visited.add(guid)

        gatherer = MetadataGatherer(guid, sparse=sparse)
        for triple in gatherer.gather_triples():
            graph.add(triple)
            if not sparse:
                obj_guid = guid_from_irl(triple[2])
                print(f'>> got {obj_guid} from {triple}')
                if obj_guid:
                    guids_to_visit.add(obj_guid)
    return graph


class MetadataGatherer:
    def __init__(self, guid_id, sparse=True):
        self.sparse = sparse
        self.subject_irl = guid_irl(guid_id)
        self.subject = models.Guid.load(guid_id).referent

    def gather_triples(self):
        all_triples = itertools.chain(
            self._gather_type(),
            self._gather_simple_properties(),
            self._gather_identifiers(),
            self._gather_keywords(),
            self._gather_license(),
            self._gather_disciplines(),
            self._gather_parts(),
            self._gather_related(),
            self._gather_file_versions(),
            self._gather_agents(),
        )
        for triple in all_triples:
            clean_triple = self._clean_triple(triple)
            if clean_triple is not None:
                yield clean_triple

    def _gather_type(self):
        # TODO: use rdf classes built from osf-map shapes
        # osf:resourcetypegeneral

        # TODO: map types explicitly, don't expose class names
        yield (A, OSF[self.subject.__class__.__name__])

        if isinstance(self.subject, models.AbstractNode):
            yield (DCT.type, DCT.Collection)
        category = getattr(self.subject, 'category', None)
        if category:
            yield (DCT.type, OSF[category])

    def _gather_simple_properties(self):
        return (
            (DCT.title, getattr(self.subject, 'title', None)),
            (DCT.title, getattr(self.subject, 'name', None)),
            (DCT.description, getattr(self.subject, 'description', None)),
            (DCT.created, getattr(self.subject, 'created', None)),
            (DCT.modified, getattr(self.subject, 'modified', None)),
            (OSF.file_path, getattr(self.subject, 'materialized_path', None)),
            # TODO:
            # dct:language
        )

    def _gather_identifiers(self):
        for guid in self.subject.guids.all().values_list('_id', flat=True):
            yield (DCT.identifier, guid_irl(guid))
        try:
            doi_irl = self.subject.get_identifier_irl('doi')
        except AttributeError:
            pass
        else:
            if doi_irl:
                yield (DCT.identifier, rdflib.URIRef(doi_irl))

    def _gather_keywords(self):
        try:
            tag_names = (
                self.subject.tags
                .filter(system=False)
                .values_list('name', flat=True)
            )
        except AttributeError:
            pass
        else:
            for tag_name in tag_names:
                yield (OSF.keyword, tag_name)

    def _gather_license(self):
        license_record = getattr(self.subject, 'node_license', None)
        if license_record is not None:
            # TODO: check handling of dct:dateCopyrighted and dct:available
            yield (DCT.dateCopyrighted, license_record.year)
            yield (DCT.available, license_record.year)
            for copyright_holder in license_record.copyright_holders:
                yield (DCT.rightsHolder, copyright_holder)
            license = license_record.node_license  # yes, it's subject.node_license.node_license
            if license is not None and license.url:
                yield (DCT.rights, rdflib.URIRef(license.url))

    def _gather_disciplines(self):
        # terminally confusing terminology:
        #   - in this file, "subject" mostly means "the thing this metadata describes",
        #     as in the "subject, predicate, object" of an rdf triple.
        #   - "subject" is also used to mean "field of study" or "discipline",
        #     as in osf.models.Subject and "dct:subject" (which is, of course, a predicate).
        try:
            subjects = self.subject.subjects.all()
        except AttributeError:
            pass
        else:
            for subject in subjects:
                # TODO: irl, not just text
                yield (DCT.subject, subject.path)
                if subject.bepress_subject:
                    yield (DCT.subject, subject.bepress_subject.path)

    def _gather_parts(self):
        files_with_guids = (
            models.BaseFileNode.active
            .filter(
                target_object_id=self.subject.id,
                target_content_type=ContentType.objects.get_for_model(self.subject),
            )
            .annotate(num_guids=Count('guids'))
            .filter(num_guids__gt=0)
        )
        for file in files_with_guids:
            yield (DCT.hasPart, guid_irl(file))

        try:
            children = self.subject.children.all()
        except AttributeError:
            pass
        else:
            for child in children:
                yield (DCT.hasPart, guid_irl(child))
                # TODO? yield (OSF.hasChild, guid_irl(child))

        parent = getattr(self.subject, 'parent_node', None)
        if parent:
            yield (DCT.isPartOf, guid_irl(parent))
            # TODO? yield (OSF.isChildOf, guid_irl(parent))

    def _gather_related(self):
        related_article_doi = getattr(self.subject, 'article_doi', None)
        if related_article_doi:
            yield (DCT.relation, DOIValidator().as_irl(related_article_doi))

        if isinstance(self.subject, models.Registration):
            for outcome_artifact in models.OutcomeArtifact.objects.for_registration(self.subject):
                artifact_irl = rdflib.URIRef(outcome_artifact.identifier.as_irl())
                yield (DCT.references, artifact_irl)
                yield (artifact_irl, DCT.title, outcome_artifact.title)
                yield (artifact_irl, DCT.description, outcome_artifact.description)
        # TODO: what do with title/description/tags/etc on osf.models.Outcome?

    def _gather_file_versions(self):
        try:
            versions = self.subject.versions.all()
            # TODO: past versions, dct:hasVersion
        except AttributeError:
            checksums = getattr(self.subject, '_hashes', {})
            for checksum_algorithm, checksum_value in checksums.items():
                yield (OSF.has_content, checksum_urn(checksum_algorithm, checksum_value))
        else:
            for version in versions:
                version_ref = rdflib.BNode()
                yield (DCT.hasVersion, version_ref)
                yield (version_ref, OSF.version_number, version.identifier)
                yield (version_ref, OSF.has_content, checksum_urn('sha256', version.location_hash))
                yield (version_ref, DCT.format, version.content_type)
                yield (version_ref, DCT.created, version.created)
                # TODO: dct:extent definition recommends megabytes (should it be a string with unit?)
                yield (version_ref, DCT.extent, version.size)

    def _gather_agents(self):
        for osf_user in getattr(self.subject, 'visible_contributors', ()):
            yield (DCT.creator, guid_irl(osf_user))
        try:
            institutions = self.subject.affiliated_institutions.all()
        except AttributeError:
            pass
        else:
            for osf_institution in institutions:
                yield (OSF.affiliatedInstitution, osf_institution.name)  # TODO: irl
        # TODO:
        # dct:contributor (roles)
        # osf:funder

    def _clean_triple(self, triple):
        if len(triple) == 2:  # allow implicit subject
            triple = (self.subject_irl, *triple)
        if len(triple) != 3:
            raise ValueError(f'{self.__class__.__name__}._clean_triple: triple not a triple (got {triple})')
        if any((v is None or v == '') for v in triple):
            return None  # politely skipple this triple
        subj, pred, obj = triple
        # unless already rdf'd, assume each triple's object is a literal
        if not isinstance(obj, rdflib.term.Identifier):
            obj = rdflib.Literal(obj)
        return (subj, pred, obj)
