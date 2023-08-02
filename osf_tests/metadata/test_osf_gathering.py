import datetime

from django.test import TestCase
import rdflib
from rdflib import Literal, URIRef

from api_tests.utils import create_test_file
from framework.auth import Auth
from osf.metadata import gather, osf_gathering
from osf.metadata.rdfutils import (
    FOAF,
    OSF,
    OSFIO,
    DCTERMS,
    DCMITYPE,
    DOI,
    OWL,
    RDF,
    SKOS,
    checksum_iri,
    contextualized_graph,
)
from osf import models as osfdb
from osf.utils import permissions
from osf_tests import factories
from website import settings as website_settings


def _get_graph_and_focuses(triples):
    graph = rdflib.Graph()
    focuses = set()
    for (subj, pred, obj) in triples:
        if isinstance(obj, gather.Focus):
            graph.add((subj, pred, obj.iri))
            focuses.add(obj)
        else:
            graph.add((subj, pred, obj))
    return graph, focuses


def _friendly_graph(rdfgraph) -> str:
    graph_to_print = contextualized_graph(rdfgraph)
    delim = '\n\t\t'
    return delim + delim.join(
        ' '.join(map(graph_to_print.namespace_manager.normalizeUri, triple))
        for triple in graph_to_print
    )


def _assert_triples(actual_triples, expected_triples):
    expected_graph, expected_focuses = _get_graph_and_focuses(expected_triples)
    actual_graph, actual_focuses = _get_graph_and_focuses(actual_triples)
    (overlap, expected_but_absent, unexpected_but_present) = rdflib.compare.graph_diff(expected_graph, actual_graph)
    assert not expected_but_absent and not unexpected_but_present, '\n\t'.join((
        'unequal triple-sets!',
        f'overlap size: {len(overlap)}',
        f'expected (but absent): {_friendly_graph(expected_but_absent)}',
        f'unexpected (but present): {_friendly_graph(unexpected_but_present)}',
    ))
    assert expected_focuses == actual_focuses


class TestOsfGathering(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user__admin = factories.UserFactory()
        cls.user__readwrite = factories.UserFactory(
            external_identity={'ORCID': {'1234-4321-5678-8765': 'VERIFIED'}},
        )
        cls.user__readonly = factories.UserFactory(
            external_identity={'ORCID': {'1234-4321-6789-9876': 'CREATE'}},
            social={
                'profileWebsites': ['http://mysite.example', 'http://myothersite.example/foo'],
                'baiduScholar': 'blarg',
            },
        )
        cls.project = factories.ProjectFactory(creator=cls.user__admin, is_public=True)
        cls.project.add_contributor(cls.user__readwrite, permissions=permissions.WRITE)
        cls.project.add_contributor(cls.user__readonly, permissions=permissions.READ, visible=False)
        cls.file_sha256 = '876b99ba1225de6b7f55ef52b068d0da3aa2ec4271875954c3b87b6659ae3823'
        cls.file = create_test_file(
            cls.project,
            cls.user__admin,
            size=123456,
            filename='blarg.txt',
            sha256=cls.file_sha256,
        )
        cls.registration = factories.RegistrationFactory(
            project=cls.project,
            creator=cls.user__admin,
            is_public=True,
        )
        cls.registration.registered_date = datetime.datetime(2121, 2, 1, tzinfo=datetime.timezone.utc)
        cls.registration.save()
        cls.projectfocus = osf_gathering.OsfFocus(cls.project)
        cls.filefocus = osf_gathering.OsfFocus(cls.file)
        cls.registrationfocus = osf_gathering.OsfFocus(cls.registration)
        cls.userfocus__admin = osf_gathering.OsfFocus(cls.user__admin)
        cls.userfocus__readwrite = osf_gathering.OsfFocus(cls.user__readwrite)
        cls.userfocus__readonly = osf_gathering.OsfFocus(cls.user__readonly)

    def test_setupdata(self):
        assert self.projectfocus.iri == OSFIO[self.project._id]
        assert self.projectfocus.rdftype == OSF.Project
        assert self.projectfocus.dbmodel is self.project
        assert self.registrationfocus.iri == OSFIO[self.registration._id]
        assert self.registrationfocus.rdftype == OSF.Registration
        assert self.registrationfocus.dbmodel is self.registration
        assert self.filefocus.iri == OSFIO[self.file.get_guid()._id]
        assert self.filefocus.rdftype == OSF.File
        assert self.filefocus.dbmodel is self.file

    def test_gather_identifiers(self):
        # focus: project
        _assert_triples(osf_gathering.gather_identifiers(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.identifier, Literal(self.projectfocus.iri)),
        })
        self.project.set_identifier_value('doi', '10.dot.ten/mydoi')
        _assert_triples(osf_gathering.gather_identifiers(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.identifier, Literal(self.projectfocus.iri)),
            (self.projectfocus.iri, DCTERMS.identifier, Literal('https://doi.org/10.dot.ten/mydoi')),
            (self.projectfocus.iri, OWL.sameAs, URIRef('https://doi.org/10.dot.ten/mydoi')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_identifiers(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.identifier, Literal(self.registrationfocus.iri)),
        })
        self.registration.set_identifier_value('doi', '10.dot.ten/myreg')
        _assert_triples(osf_gathering.gather_identifiers(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.identifier, Literal(self.registrationfocus.iri)),
            (self.registrationfocus.iri, DCTERMS.identifier, Literal('https://doi.org/10.dot.ten/myreg')),
            (self.registrationfocus.iri, OWL.sameAs, URIRef('https://doi.org/10.dot.ten/myreg')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_identifiers(self.filefocus), {
            (self.filefocus.iri, DCTERMS.identifier, Literal(self.filefocus.iri)),
        })

    def test_gather_flexible_types(self):
        # focus: project
        _assert_triples(osf_gathering.gather_flexible_types(self.projectfocus), {
        })
        self.projectfocus.guid_metadata_record.resource_type_general = 'Book'
        _assert_triples(osf_gathering.gather_flexible_types(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.type, Literal('Book')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_flexible_types(self.registrationfocus), {
        })
        self.registrationfocus.guid_metadata_record.resource_type_general = 'Preprint'
        _assert_triples(osf_gathering.gather_flexible_types(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.type, Literal('Preprint')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_flexible_types(self.filefocus), set())
        self.filefocus.guid_metadata_record.resource_type_general = 'Dataset'
        _assert_triples(osf_gathering.gather_flexible_types(self.filefocus), {
            (self.filefocus.iri, DCTERMS.type, Literal('Dataset')),
        })

    def test_gather_created(self):
        # focus: project
        _assert_triples(osf_gathering.gather_created(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.created, Literal(str(self.project.created.date()))),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_created(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.created, Literal('2121-02-01')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_created(self.filefocus), {
            (self.filefocus.iri, DCTERMS.created, Literal(str(self.file.created.date()))),
        })

    def test_gather_available(self):
        # focus: project
        _assert_triples(osf_gathering.gather_available(self.projectfocus), set())
        # focus: registration
        _assert_triples(osf_gathering.gather_available(self.registrationfocus), set())
        factories.EmbargoFactory(
            target_item=self.registration,
            user=self.user__admin,
            end_date=datetime.datetime(1973, 7, 3, tzinfo=datetime.timezone.utc),
        )
        _assert_triples(osf_gathering.gather_available(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.available, Literal('1973-07-03')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_available(self.filefocus), set())

    def test_gather_modified(self):
        # focus: project
        _assert_triples(osf_gathering.gather_modified(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.modified, Literal(str(self.project.last_logged.date()))),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_modified(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.modified, Literal(str(self.registration.last_logged.date()))),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_modified(self.filefocus), {
            (self.filefocus.iri, DCTERMS.modified, Literal(str(self.file.modified.date()))),
        })

    def test_gather_moderation_dates(self):
        # focus: project
        _assert_triples(osf_gathering.gather_moderation_dates(self.projectfocus), set())
        # focus: registration
        _assert_triples(osf_gathering.gather_moderation_dates(self.registrationfocus), set())
        # focus: file
        _assert_triples(osf_gathering.gather_moderation_dates(self.filefocus), set())
        # TODO: put registration thru moderation

    def test_gather_licensing(self):
        # focus: project
        _assert_triples(osf_gathering.gather_licensing(self.projectfocus), set())
        self.project.node_license = factories.NodeLicenseRecordFactory(
            year='1952-2001',
            copyright_holders=['foo', 'bar', 'baz baz'],
        )
        license_bnode = rdflib.BNode()
        _assert_triples(osf_gathering.gather_licensing(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.dateCopyrighted, Literal('1952-2001')),
            (self.projectfocus.iri, DCTERMS.rightsHolder, Literal('foo')),
            (self.projectfocus.iri, DCTERMS.rightsHolder, Literal('bar')),
            (self.projectfocus.iri, DCTERMS.rightsHolder, Literal('baz baz')),
            (self.projectfocus.iri, DCTERMS.rights, license_bnode),
            (license_bnode, FOAF.name, Literal('No license')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_licensing(self.registrationfocus), set())
        self.registration.node_license = factories.NodeLicenseRecordFactory(
            year='1957-2008',
            copyright_holders=['bar bar', 'baz baz', 'quux'],
            node_license=osfdb.NodeLicense.objects.get(
                name='CC-By Attribution 4.0 International',
            ),
        )
        expected_license_iri = URIRef('https://creativecommons.org/licenses/by/4.0/legalcode')
        _assert_triples(osf_gathering.gather_licensing(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.dateCopyrighted, Literal('1957-2008')),
            (self.registrationfocus.iri, DCTERMS.rightsHolder, Literal('bar bar')),
            (self.registrationfocus.iri, DCTERMS.rightsHolder, Literal('baz baz')),
            (self.registrationfocus.iri, DCTERMS.rightsHolder, Literal('quux')),
            (self.registrationfocus.iri, DCTERMS.rights, expected_license_iri),
            (expected_license_iri, FOAF.name, Literal('CC-By Attribution 4.0 International')),
            (expected_license_iri, DCTERMS.identifier, Literal(expected_license_iri)),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_licensing(self.filefocus), set())

    def test_gather_title(self):
        # focus: project
        _assert_triples(osf_gathering.gather_title(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.title, Literal(self.project.title)),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_title(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.title, Literal(self.registration.title)),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_title(self.filefocus), set())
        self.filefocus.guid_metadata_record.title = 'my title!'
        _assert_triples(osf_gathering.gather_title(self.filefocus), {
            (self.filefocus.iri, DCTERMS.title, Literal('my title!')),
        })

    def test_gather_language(self):
        # focus: project
        _assert_triples(osf_gathering.gather_language(self.projectfocus), set())
        self.projectfocus.guid_metadata_record.language = 'es'
        _assert_triples(osf_gathering.gather_language(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.language, Literal('es')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_language(self.registrationfocus), set())
        self.registrationfocus.guid_metadata_record.language = 'es'
        _assert_triples(osf_gathering.gather_language(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.language, Literal('es')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_language(self.filefocus), set())
        self.filefocus.guid_metadata_record.language = 'es'
        _assert_triples(osf_gathering.gather_language(self.filefocus), {
            (self.filefocus.iri, DCTERMS.language, Literal('es')),
        })

    def test_gather_description(self):
        # focus: project
        _assert_triples(osf_gathering.gather_description(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.description, Literal(self.project.description)),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_description(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.description, Literal(self.registration.description)),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_description(self.filefocus), set())
        self.filefocus.guid_metadata_record.description = 'woop a doo'
        _assert_triples(osf_gathering.gather_description(self.filefocus), {
            (self.filefocus.iri, DCTERMS.description, Literal('woop a doo')),
        })

    def test_gather_keywords(self):
        # focus: project
        _assert_triples(osf_gathering.gather_keywords(self.projectfocus), set())
        self.project.update_tags(['woop', 'a', 'doo'], auth=Auth(self.user__admin))
        _assert_triples(osf_gathering.gather_keywords(self.projectfocus), {
            (self.projectfocus.iri, OSF.keyword, Literal('woop')),
            (self.projectfocus.iri, OSF.keyword, Literal('a')),
            (self.projectfocus.iri, OSF.keyword, Literal('doo')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_keywords(self.registrationfocus), set())
        self.registration.update_tags(['boop', 'a', 'doop'], auth=Auth(self.user__admin))
        _assert_triples(osf_gathering.gather_keywords(self.registrationfocus), {
            (self.registrationfocus.iri, OSF.keyword, Literal('boop')),
            (self.registrationfocus.iri, OSF.keyword, Literal('a')),
            (self.registrationfocus.iri, OSF.keyword, Literal('doop')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_keywords(self.filefocus), set())

    def test_gather_subjects(self):
        # focus: project
        _assert_triples(osf_gathering.gather_subjects(self.projectfocus), set())
        _bloo_subject = factories.SubjectFactory(text='Bloomy')
        self.project.set_subjects([[_bloo_subject._id]], auth=Auth(self.user__admin))
        _bloo_iri = URIRef(_bloo_subject.absolute_api_v2_subject_url)
        _bepress_iri = rdflib.URIRef('https://bepress.com/reference_guide_dc/disciplines/')
        _assert_triples(osf_gathering.gather_subjects(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.subject, _bloo_iri),
            (_bloo_iri, RDF.type, SKOS.Concept),
            (_bloo_iri, SKOS.inScheme, _bepress_iri),
            (_bepress_iri, DCTERMS.title, Literal('bepress Digital Commons Three-Tiered Taxonomy')),
            (_bloo_iri, SKOS.prefLabel, Literal('Bloomy')),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_subjects(self.registrationfocus), set())
        _parent_subj = factories.SubjectFactory(text='Parent')
        _child_subj = factories.SubjectFactory(text='Child', parent=_parent_subj)
        _altparent_subj = factories.SubjectFactory(text='Alt-parent', bepress_subject=_parent_subj)
        _altchild_subj = factories.SubjectFactory(text='Alt-child', parent=_altparent_subj, bepress_subject=_child_subj)
        self.registration.set_subjects([
            [_altchild_subj._id, _altparent_subj._id],
            [_bloo_subject._id],
        ], auth=Auth(self.user__admin))
        _parent_iri = URIRef(_parent_subj.absolute_api_v2_subject_url)
        _child_iri = URIRef(_child_subj.absolute_api_v2_subject_url)
        _assert_triples(osf_gathering.gather_subjects(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.subject, _bloo_iri),
            (self.registrationfocus.iri, DCTERMS.subject, _parent_iri),
            (self.registrationfocus.iri, DCTERMS.subject, _child_iri),
            (_bloo_iri, RDF.type, SKOS.Concept),
            (_parent_iri, RDF.type, SKOS.Concept),
            (_child_iri, RDF.type, SKOS.Concept),
            (_bloo_iri, SKOS.inScheme, _bepress_iri),
            (_parent_iri, SKOS.inScheme, _bepress_iri),
            (_child_iri, SKOS.inScheme, _bepress_iri),
            (_bloo_iri, SKOS.prefLabel, Literal('Bloomy')),
            (_parent_iri, SKOS.prefLabel, Literal('Parent')),
            (_parent_iri, SKOS.altLabel, Literal('Alt-parent')),
            (_child_iri, SKOS.prefLabel, Literal('Child')),
            (_child_iri, SKOS.altLabel, Literal('Alt-child')),
            (_child_iri, SKOS.broader, _parent_iri),
            (_bepress_iri, DCTERMS.title, Literal('bepress Digital Commons Three-Tiered Taxonomy')),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_subjects(self.filefocus), set())

    def test_gather_file_basics(self):
        # focus: project
        _assert_triples(osf_gathering.gather_file_basics(self.projectfocus), set())
        # focus: registration
        _assert_triples(osf_gathering.gather_file_basics(self.registrationfocus), set())
        # focus: file
        _assert_triples(osf_gathering.gather_file_basics(self.filefocus), {
            (self.filefocus.iri, OSF.isContainedBy, osf_gathering.OsfFocus(self.file.target)),
            (self.filefocus.iri, OSF.fileName, Literal(self.file.name)),
            (self.filefocus.iri, OSF.filePath, Literal(self.file.materialized_path)),
        })

    def test_gather_versions(self):
        # focus: project
        _assert_triples(osf_gathering.gather_versions(self.projectfocus), set())
        # focus: registration
        _assert_triples(osf_gathering.gather_versions(self.registrationfocus), set())
        # focus: file
        fileversion = self.file.versions.first()
        fileversion_iri = URIRef(f'{self.filefocus.iri}?revision={fileversion.identifier}')
        _assert_triples(osf_gathering.gather_versions(self.filefocus), {
            (self.filefocus.iri, OSF.hasFileVersion, fileversion_iri),
            (fileversion_iri, RDF.type, OSF.FileVersion),
            (fileversion_iri, DCTERMS.creator, osf_gathering.OsfFocus(fileversion.creator)),
            (fileversion_iri, DCTERMS.created, Literal(str(fileversion.created.date()))),
            (fileversion_iri, DCTERMS.modified, Literal(str(fileversion.modified.date()))),
            (fileversion_iri, DCTERMS['format'], Literal(fileversion.content_type)),
            (fileversion_iri, DCTERMS.extent, Literal('0.118 MB')),
            (fileversion_iri, OSF.versionNumber, Literal(fileversion.identifier)),
            (fileversion_iri, DCTERMS.requires, checksum_iri('sha-256', self.file_sha256))
        })

    def test_gather_files(self):
        # focus: project
        _assert_triples(osf_gathering.gather_files(self.projectfocus), {
            (self.projectfocus.iri, OSF.contains, self.filefocus),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_files(self.registrationfocus), set())
        # focus: file
        _assert_triples(osf_gathering.gather_files(self.filefocus), set())

    def test_gather_parts(self):
        # focus: project
        _assert_triples(osf_gathering.gather_parts(self.projectfocus), set())
        # ...with components:
        component = factories.ProjectFactory(parent=self.project, creator=self.user__admin, is_public=True)
        sibcomponent = factories.ProjectFactory(parent=self.project, creator=self.user__admin, is_public=True)
        subcomponent = factories.ProjectFactory(parent=component, creator=self.user__admin, is_public=True)
        componentfocus = osf_gathering.OsfFocus(component)
        sibcomponentfocus = osf_gathering.OsfFocus(sibcomponent)
        subcomponentfocus = osf_gathering.OsfFocus(subcomponent)
        _assert_triples(osf_gathering.gather_parts(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.hasPart, componentfocus),
            (self.projectfocus.iri, DCTERMS.hasPart, sibcomponentfocus),
        })
        _assert_triples(osf_gathering.gather_parts(componentfocus), {
            (componentfocus.iri, OSF.hasRoot, self.projectfocus),
            (componentfocus.iri, DCTERMS.isPartOf, self.projectfocus),
            (componentfocus.iri, DCTERMS.hasPart, subcomponentfocus),
        })
        _assert_triples(osf_gathering.gather_parts(sibcomponentfocus), {
            (sibcomponentfocus.iri, OSF.hasRoot, self.projectfocus),
            (sibcomponentfocus.iri, DCTERMS.isPartOf, self.projectfocus),
        })
        _assert_triples(osf_gathering.gather_parts(subcomponentfocus), {
            (subcomponentfocus.iri, OSF.hasRoot, self.projectfocus),
            (subcomponentfocus.iri, DCTERMS.isPartOf, componentfocus),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_parts(self.registrationfocus), set())
        # focus: file
        _assert_triples(osf_gathering.gather_parts(self.filefocus), set())

    def test_gather_related_items(self):
        # focus: project
        _assert_triples(osf_gathering.gather_project_related_items(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.hasVersion, self.registrationfocus),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_registration_related_items(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.isVersionOf, self.projectfocus),
        })
        self.registration.article_doi = '10.blarg/blerg'
        doi_iri = DOI[self.registration.article_doi]
        _assert_triples(osf_gathering.gather_registration_related_items(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.relation, doi_iri),
            (doi_iri, DCTERMS.identifier, Literal(doi_iri)),
            (self.registrationfocus.iri, DCTERMS.isVersionOf, self.projectfocus),
        })

    def test_gather_agents(self):
        # focus: project
        _assert_triples(osf_gathering.gather_agents(self.projectfocus), {
            (self.projectfocus.iri, DCTERMS.creator, self.userfocus__admin),
            (self.projectfocus.iri, DCTERMS.creator, self.userfocus__readwrite),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_agents(self.registrationfocus), {
            (self.registrationfocus.iri, DCTERMS.creator, self.userfocus__admin),
            (self.registrationfocus.iri, DCTERMS.creator, self.userfocus__readwrite),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_agents(self.filefocus), set())

    def test_gather_affiliated_institutions(self):
        # focus: project
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.projectfocus), set())
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.userfocus__admin), set())
        institution = factories.InstitutionFactory()
        institution_iri = URIRef(institution.identifier_domain)
        self.user__admin.add_or_update_affiliated_institution(institution)
        self.project.add_affiliated_institution(institution, self.user__admin)
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.projectfocus), {
            (self.projectfocus.iri, OSF.affiliation, institution_iri),
            (institution_iri, RDF.type, DCTERMS.Agent),
            (institution_iri, RDF.type, FOAF.Organization),
            (institution_iri, FOAF.name, Literal(institution.name)),
            (institution_iri, DCTERMS.identifier, Literal(institution.identifier_domain)),
        })
        # focus: user
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.userfocus__admin), {
            (self.userfocus__admin.iri, OSF.affiliation, institution_iri),
            (institution_iri, RDF.type, DCTERMS.Agent),
            (institution_iri, RDF.type, FOAF.Organization),
            (institution_iri, FOAF.name, Literal(institution.name)),
            (institution_iri, DCTERMS.identifier, Literal(institution.identifier_domain)),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.registrationfocus), set())
        # focus: file
        _assert_triples(osf_gathering.gather_affiliated_institutions(self.filefocus), set())

    def test_gather_funding(self):
        # focus: project
        _assert_triples(osf_gathering.gather_funding(self.projectfocus), set())
        self.projectfocus.guid_metadata_record.funding_info = [
            {'funder_name': 'hooray'},
            {
                'funder_name': 'NIH',
                'funder_identifier': 'https://doi.org/10.fake/NIH',
                'funder_identifier_type': 'Crossref Funder ID',
                'award_title': 'big fun',
                'award_uri': 'https://nih.example/award',
                'award_number': '27',
            },
        ]
        _bnode1 = rdflib.BNode()
        _award_uri = URIRef('https://nih.example/award')
        _funder_uri = URIRef('https://doi.org/10.fake/NIH')
        _assert_triples(osf_gathering.gather_funding(self.projectfocus), {
            (self.projectfocus.iri, OSF.funder, _bnode1),
            (_bnode1, RDF.type, DCTERMS.Agent),
            (_bnode1, FOAF.name, Literal('hooray')),
            (self.projectfocus.iri, OSF.funder, _funder_uri),
            (_funder_uri, RDF.type, DCTERMS.Agent),
            (_funder_uri, DCTERMS.identifier, Literal(_funder_uri)),
            (_funder_uri, FOAF.name, Literal('NIH')),
            (_funder_uri, OSF.funderIdentifierType, Literal('Crossref Funder ID')),
            (self.projectfocus.iri, OSF.hasFunding, _award_uri),
            (_award_uri, RDF.type, OSF.FundingAward),
            (_award_uri, DCTERMS.identifier, Literal(_award_uri)),
            (_award_uri, DCTERMS.title, Literal('big fun')),
            (_award_uri, OSF.awardNumber, Literal('27')),
            (_award_uri, DCTERMS.contributor, _funder_uri),
        })
        # focus: registration
        _assert_triples(osf_gathering.gather_funding(self.registrationfocus), set())
        self.registrationfocus.guid_metadata_record.funding_info = [
            {
                'funder_name': 'blooray',
                'funder_identifier': 'https://doi.org/11.bloo',
                'award_title': 'blaward',
            },
        ]
        _funder_uri = rdflib.URIRef('https://doi.org/11.bloo')
        _assert_triples(osf_gathering.gather_funding(self.registrationfocus), {
            (self.registrationfocus.iri, OSF.funder, _funder_uri),
            (_funder_uri, RDF.type, DCTERMS.Agent),
            (_funder_uri, DCTERMS.identifier, Literal(_funder_uri)),
            (_funder_uri, FOAF.name, Literal('blooray')),
            (self.registrationfocus.iri, OSF.hasFunding, _bnode1),
            (_bnode1, RDF.type, OSF.FundingAward),
            (_bnode1, DCTERMS.title, Literal('blaward')),
            (_bnode1, DCTERMS.contributor, _funder_uri),
        })
        # focus: file
        _assert_triples(osf_gathering.gather_funding(self.filefocus), set())
        self.filefocus.guid_metadata_record.funding_info = [
            {
                'funder_name': 'exray',
                'funder_identifier': 'https://doi.org/11.ex',
            },
        ]
        _funder_uri = rdflib.URIRef('https://doi.org/11.ex')
        _assert_triples(osf_gathering.gather_funding(self.filefocus), {
            (self.filefocus.iri, OSF.funder, _funder_uri),
            (_funder_uri, RDF.type, DCTERMS.Agent),
            (_funder_uri, DCTERMS.identifier, Literal(_funder_uri)),
            (_funder_uri, FOAF.name, Literal('exray')),
        })

    def test_gather_user_basics(self):
        # focus: admin user
        _assert_triples(osf_gathering.gather_user_basics(self.userfocus__admin), {
            (self.userfocus__admin.iri, RDF.type, FOAF.Person),
            (self.userfocus__admin.iri, FOAF.name, Literal(self.user__admin.fullname)),
        })
        # focus: readwrite user
        _assert_triples(osf_gathering.gather_user_basics(self.userfocus__readwrite), {
            (self.userfocus__readwrite.iri, RDF.type, FOAF.Person),
            (self.userfocus__readwrite.iri, FOAF.name, Literal(self.user__readwrite.fullname)),
            (self.userfocus__readwrite.iri, DCTERMS.identifier, Literal('https://orcid.org/1234-4321-5678-8765')),
            (self.userfocus__readwrite.iri, OWL.sameAs, URIRef('https://orcid.org/1234-4321-5678-8765')),
        })
        # focus: readonly user
        _assert_triples(osf_gathering.gather_user_basics(self.userfocus__readonly), {
            (self.userfocus__readonly.iri, RDF.type, FOAF.Person),
            (self.userfocus__readonly.iri, FOAF.name, Literal(self.user__readonly.fullname)),
            # orcid not verified, should be excluded
            (self.userfocus__readonly.iri, DCTERMS.identifier, Literal('http://mysite.example')),
            (self.userfocus__readonly.iri, DCTERMS.identifier, Literal('http://myothersite.example/foo')),
            (self.userfocus__readonly.iri, DCTERMS.identifier, Literal('http://xueshu.baidu.com/scholarID/blarg')),
        })

    def test_gather_collection_membership(self):
        _collection_provider = factories.CollectionProviderFactory(
            reviews_workflow='post-moderation',
        )
        _collection = factories.CollectionFactory(provider=_collection_provider)
        osfdb.CollectionSubmission.objects.create(
            guid=self.project.guids.first(),
            collection=_collection,
            creator=self.project.creator,
        )
        _collection_ref = rdflib.URIRef(
            f'{website_settings.DOMAIN}collections/{_collection_provider._id}',
        )
        _assert_triples(osf_gathering.gather_collection_membership(self.projectfocus), {
            (self.projectfocus.iri, OSF.isPartOfCollection, _collection_ref),
            (_collection_ref, DCTERMS.type, DCMITYPE.Collection),
            (_collection_ref, DCTERMS.title, Literal(_collection_provider.name)),
        })
