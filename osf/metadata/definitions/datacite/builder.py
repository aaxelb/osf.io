import datetime
import logging
import re
import typing

import rdflib

from osf.exceptions import MetadataSerializationError
from osf.metadata import gather
from osf.metadata.rdfutils import (
    RDF,
    DCTERMS,
    DOI,
    FOAF,
    ORCID,
    OSF,
    ROR,
    without_namespace,
)


logger = logging.getLogger(__name__)


RELATED_IDENTIFIER_TYPE_MAP = {
    DCTERMS.hasPart: 'HasPart',
    DCTERMS.hasVersion: 'HasVersion',
    DCTERMS.isPartOf: 'IsPartOf',
    DCTERMS.isVersionOf: 'IsVersionOf',
    DCTERMS.references: 'References',
    DCTERMS.relation: 'References',
    OSF.archivedAt: 'IsIdenticalTo',
    OSF.hasRoot: 'IsPartOf',
    OSF.isContainedBy: 'IsPartOf',
    OSF.supplements: 'IsSupplementTo',
    OSF.isSupplementedBy: 'IsSupplementedBy',
    OSF.hasDataResource: 'References',
    OSF.hasAnalyticCodeResource: 'References',
    OSF.hasMaterialsResource: 'References',
    OSF.hasPapersResource: 'References',
    OSF.hasSupplementalResource: 'References',
}
DATE_TYPE_MAP = {
    DCTERMS.created: 'Created',
    DCTERMS.modified: 'Updated',
    DCTERMS.dateSubmitted: 'Submitted',
    DCTERMS.dateAccepted: 'Valid',
    DCTERMS.available: 'Available',
    DCTERMS.date: 'Other',
    OSF.withdrawn: 'Withdrawn',
}
PUBLICATION_YEAR_FALLBACK_ORDER = (
    DCTERMS.available,
    DCTERMS.dateAccepted,
    DCTERMS.created,
    DCTERMS.modified,
)
CONTRIBUTOR_TYPE_MAP = {
    # TODO: contributor roles
    # DCTERMS.contributor: 'ProjectMember',
    OSF.HostingInstitution: 'HostingInstitution',
}
BEPRESS_SUBJECT_SCHEME = 'bepress Digital Commons Three-Tiered Taxonomy'
RESOURCE_TYPES_GENERAL = {
    'Audiovisual',
    'Book',
    'BookChapter',
    'Collection',
    'ComputationalNotebook',
    'ConferencePaper',
    'ConferenceProceeding',
    'DataPaper',
    'Dataset',
    'Dissertation',
    'Event',
    'Image',
    'InteractiveResource',
    'Journal',
    'JournalArticle',
    'Model',
    'OutputManagementPlan',
    'PeerReview',
    'PhysicalObject',
    'Preprint',
    'Report',
    'Service',
    'Software',
    'Sound',
    'Standard',
    'Text',
    'Workflow',
    'Other',
}


class DataciteMetadataBuilder:
    def __init__(self, basket: gather.Basket, add_child_fn: typing.Callable):
        self.basket = basket
        # expected signature for add_child_fn:
        #   def add_child_fn(
        #       parent: typing.Any,
        #       child_tag_name: str,
        #       *,
        #       is_list: bool = False,
        #       text: str = None,
        #       attrib: dict = None,
        #   )
        # (return value may be passed as `parent` in later invocations)
        self._add = add_child_fn

    def build(self, root: typing.Any, explicit_doi=None):
        # root only passed to self._add, not otherwise touched
        self._add_identifier(root, explicit_doi=explicit_doi)
        self._add_creators(root, self.basket.focus.iri)
        self._add_titles(root, self.basket.focus.iri)
        self._add_publisher(root, self.basket.focus.iri)
        self._add_publication_year(root, self.basket.focus.iri)
        self._add_subjects(root)
        self._add_contributors(root, self.basket.focus.iri)
        self._add_dates(root)
        self._add_language(root)
        self._add_resource_type(root)
        self._add_alternate_identifiers(root)
        self._add_format(root)
        self._add_rights(root)
        self._add_descriptions(root, self.basket.focus.iri)
        self._add_funding_references(root)
        self._add_related(root)

    def _add_identifier(self, parent_el, *, explicit_doi=None):
        if explicit_doi is None:
            identifier_type, identifier_value = self._identifier_type_and_value(
                self._get_one_identifier(self.basket.focus.iri),
            )
        else:
            identifier_type = 'DOI'
            identifier_value = explicit_doi
        self._add(parent_el, 'identifier', text=identifier_value, attrib={
            'identifierType': identifier_type,
        })

    def _add_creators(self, parent_el, focus_iri):
        creator_iris = set(self.basket[focus_iri:DCTERMS.creator])
        if (not creator_iris) and ((focus_iri, RDF.type, OSF.File) in self.basket):
            creator_iris.update(self.basket[focus_iri:OSF.hasFileVersion / DCTERMS.creator])
        if not creator_iris:
            creator_iris.update(self.basket[focus_iri:OSF.isContainedBy / DCTERMS.creator])
        if not creator_iris:
            creator_iris.update(self.basket[focus_iri:DCTERMS.isPartOf / DCTERMS.creator])
        if not creator_iris:
            creator_iris.update(self.basket[focus_iri:DCTERMS.contributor])
        if not creator_iris:
            creator_iris.update(self.basket[focus_iri:OSF.isContainedBy / DCTERMS.contributor])
        if not creator_iris:
            creator_iris.update(self.basket[focus_iri:DCTERMS.isPartOf / DCTERMS.contributor])
        if not creator_iris:
            raise ValueError(f'gathered no creators or contributors around {focus_iri}')
        creators_el = self._add(parent_el, 'creators', is_list=True)
        for creator_iri in creator_iris:  # TODO: "priority order"
            creator_el = self._add(creators_el, 'creator')
            for name in self.basket[creator_iri:FOAF.name]:
                self._add(creator_el, 'creatorName', text=name, attrib={
                    'nameType': self._get_name_type(creator_iri),
                })
            self._add_name_identifiers(creator_el, creator_iri)
            self._add_affiliations(creator_el, creator_iri)

    def _identifier_type_and_value(self, iri):
        if iri.startswith(DOI):
            return ('DOI', without_namespace(iri, DOI))
        elif iri.startswith(ROR):
            return ('ROR', iri)  # ROR keeps the full IRI
        elif iri.startswith(ORCID):
            return ('ORCID', without_namespace(iri, ORCID))
        elif '://' in iri:
            return ('URL', iri)
        raise ValueError(f'does not look like an iri: {iri}')

    def _get_name_type(self, agent_iri):
        if (agent_iri, DCTERMS.type, FOAF.Person) in self.basket:
            return 'Personal'
        if (agent_iri, DCTERMS.type, FOAF.Organization) in self.basket:
            return 'Organizational'
        raise MetadataSerializationError(f'could not determine nameType for {agent_iri}')

    def _add_alternate_identifiers(self, parent_el):
        alt_ids_el = self._add(parent_el, 'alternateIdentifiers', is_list=True)
        for identifier in sorted(self.basket[DCTERMS.identifier]):
            identifier_type, identifier_value = self._identifier_type_and_value(identifier)
            if identifier_type != 'DOI':
                self._add(alt_ids_el, 'alternateIdentifier', text=identifier_value, attrib={
                    'alternateIdentifierType': identifier_type,
                })

    def _add_titles(self, parent_el, focus_iri):
        titles_el = self._add(parent_el, 'titles', is_list=True)
        for title in self.basket[focus_iri:DCTERMS.title]:
            self._add(titles_el, 'title', text=title)
        if (not len(titles_el)) and (OSF.File in self.basket[focus_iri:RDF.type]):
            self._add(titles_el, 'title', text=next(self.basket[focus_iri:OSF.fileName]))

    def _add_descriptions(self, parent_el, focus_iri):
        descriptions_el = self._add(parent_el, 'descriptions', is_list=True)
        for description in self.basket[focus_iri:DCTERMS.description]:
            self._add(descriptions_el, 'description', text=description, attrib={
                'descriptionType': 'Abstract',  # TODO: other description types?
            })

    def _add_publisher(self, parent_el, focus_iri):
        publisher_name = next(self.basket[focus_iri:DCTERMS.publisher / FOAF.name], 'OSF')
        self._add(parent_el, 'publisher', text=publisher_name)

    def _agent_name_type(self, agent_iri):
        agent_types = set(self.basket[agent_iri:DCTERMS.type])
        if FOAF.Person in agent_types:
            return 'Personal'
        if FOAF.Organization in agent_types:
            return 'Organizational'
        raise ValueError(f'unknown agent type for {agent_iri}')

    def _add_contributors(self, parent_el, focus_iri):
        contributors_el = self._add(parent_el, 'contributors', is_list=True)
        for osfmap_iri, datacite_contributor_type in CONTRIBUTOR_TYPE_MAP.items():
            for contributor_iri in self.basket[focus_iri:osfmap_iri]:
                contributor_el = self._add(contributors_el, 'contributor', attrib={
                    'contributorType': datacite_contributor_type,
                })
                for name in self.basket[contributor_iri:FOAF.name]:
                    self._add(contributor_el, 'contributorName', text=name, attrib={
                        'nameType': self._get_name_type(contributor_iri),
                    })
                self._add_name_identifiers(contributor_el, contributor_iri)
                self._add_affiliations(contributor_el, contributor_iri)

    def _add_rights(self, parent_el):
        rights_list_el = self._add(parent_el, 'rightsList', is_list=True)
        for rights_iri in self.basket[DCTERMS.rights]:
            name = next(self.basket[rights_iri:FOAF.name], '')
            try:
                attrib = {
                    'rightsURI': next(self.basket[rights_iri:DCTERMS.identifier]),
                }
            except StopIteration:
                attrib = {}
            self._add(rights_list_el, 'rights', text=name, attrib=attrib)

    def _add_affiliations(self, parent_el, focus_iri):
        for institution_iri in self.basket[focus_iri:OSF.affiliatedInstitution]:
            try:
                name = next(self.basket[institution_iri:FOAF.name])
            except StopIteration:
                raise MetadataSerializationError(f'need foaf:name for affiliated "{focus_iri}"')
            affiliation_attrib = {}
            try:
                identifier = self._get_one_identifier(institution_iri)
            except ValueError:
                pass  # don't need affiliationIdentifier
            else:
                identifier_type, identifier_value = self._identifier_type_and_value(identifier)
                affiliation_attrib['affiliationIdentifier'] = identifier_value
                affiliation_attrib['affiliationIdentifierScheme'] = identifier_type
            self._add(parent_el, 'affiliation', text=name, attrib=affiliation_attrib, is_list=True)

    def _add_dates(self, parent_el):
        dates_el = self._add(parent_el, 'dates', is_list=True)
        for date_predicate, datacite_datetype in DATE_TYPE_MAP.items():
            for date_str in self.basket[date_predicate]:
                self._add(dates_el, 'date', text=date_str, attrib={
                    'dateType': datacite_datetype,
                })

    def _add_funding_references(self, parent_el):
        fundrefs_el = self._add(parent_el, 'fundingReferences', is_list=True)
        for funding_ref in self.basket[OSF.funder]:
            fundref_el = self._add(fundrefs_el, 'fundingReference')
            self._add(fundref_el, 'funderName', text=next(self.basket[funding_ref:FOAF.name], ''))
            self._add(
                fundref_el,
                'funderIdentifier',
                text=next(self.basket[funding_ref:DCTERMS.identifier], ''),
                attrib={
                    'funderIdentifierType': next(self.basket[funding_ref:OSF.funderIdentifierType], ''),
                },
            )
            self._add(
                fundref_el,
                'awardNumber',
                text=next(self.basket[funding_ref:OSF.awardNumber], ''),
                attrib={
                    'awardURI': next(self.basket[funding_ref:OSF.awardUri], ''),
                },
            )
            self._add(fundref_el, 'awardTitle', text=next(self.basket[funding_ref:OSF.awardTitle], ''))

    def _add_publication_year(self, parent_el, focus_iri):
        year_copyrighted = next(self.basket[focus_iri:DCTERMS.dateCopyrighted], None)
        if year_copyrighted and re.fullmatch(r'\d{4}', year_copyrighted):
            self._add(parent_el, 'publicationYear', text=year_copyrighted)
        else:
            for date_predicate in PUBLICATION_YEAR_FALLBACK_ORDER:
                date_str = next(self.basket[focus_iri:date_predicate], None)
                if date_str:
                    extracted_year = str(datetime.datetime.strptime(date_str, '%Y-%m-%d').year)
                    self._add(parent_el, 'publicationYear', text=extracted_year)
                    break  # only one allowed

    def _add_language(self, parent_el):
        try:
            language = next(self.basket[DCTERMS.language])
        except StopIteration:
            pass
        else:
            self._add(parent_el, 'language', text=language)

    def _add_format(self, parent_el):
        try:
            format_val = next(self.basket[DCTERMS['format']])
        except StopIteration:
            pass
        else:
            self._add(parent_el, 'format', text=format_val)

    def _get_one_identifier(self, resource_id):
        try:  # prefer DOI if there is one
            identifier = next(
                iri
                for iri in self.basket[resource_id:DCTERMS.identifier]
                if iri.startswith(DOI)
            )
        except StopIteration:
            try:  # ...but any URL will do
                identifier = next(self.basket[resource_id:DCTERMS.identifier])
            except StopIteration:
                if isinstance(resource_id, rdflib.URIRef):
                    identifier = str(resource_id)
                else:
                    raise ValueError(f'no iri found for {resource_id}')
        return identifier

    def _add_related_identifier_and_item(self, identifier_parent_el, item_parent_el, related_iri, datacite_relation_type):
        try:
            identifier = self._get_one_identifier(related_iri)
        except ValueError:
            identifier = None  # can add relatedItem without identifier
        related_item_el = self._add(item_parent_el, 'relatedItem', attrib={
            'relationType': datacite_relation_type,
            'relatedItemType': self._get_resource_type_general(related_iri),
        })
        if identifier is not None:
            identifier_type, identifier_value = self._identifier_type_and_value(identifier)
            self._add(related_item_el, 'relatedItemIdentifier', text=identifier_value, attrib={
                'relatedItemIdentifierType': identifier_type,
            })
            self._add(identifier_parent_el, 'relatedIdentifier', text=identifier_value, attrib={
                'relatedIdentifierType': identifier_type,
                'relationType': datacite_relation_type,
            })
        self._add_titles(related_item_el, related_iri)
        self._add_publication_year(related_item_el, related_iri)
        self._add_publisher(related_item_el, related_iri)

    def _add_related(self, parent_el):
        relation_pairs = set()
        for relation_iri, datacite_relation in RELATED_IDENTIFIER_TYPE_MAP.items():
            for related_iri in self.basket[relation_iri]:
                relation_pairs.add((datacite_relation, related_iri))
        related_identifiers_el = self._add(parent_el, 'relatedIdentifiers', is_list=True)
        related_items_el = self._add(parent_el, 'relatedItems', is_list=True)
        for datacite_relation, related_iri in relation_pairs:
            self._add_related_identifier_and_item(
                related_identifiers_el,
                related_items_el,
                related_iri,
                datacite_relation,
            )

    def _add_name_identifiers(self, parent_el, agent_iri):
        for identifier in sorted(self.basket[agent_iri:DCTERMS.identifier]):
            identifier_type, identifier_value = self._identifier_type_and_value(identifier)
            self._add(parent_el, 'nameIdentifier', text=identifier_value, attrib={
                'nameIdentifierScheme': identifier_type,
            })

    def _add_subjects(self, parent_el):
        subjects_el = self._add(parent_el, 'subjects', is_list=True)
        for subject in self.basket[DCTERMS.subject]:
            self._add(subjects_el, 'subject', text=subject, attrib={
                'subjectScheme': BEPRESS_SUBJECT_SCHEME,
            })
        for keyword in self.basket[OSF.keyword]:
            self._add(subjects_el, 'subject', text=keyword)

    def _add_resource_type(self, parent_el):
        resource_type_text = ''
        focustype = self.basket.focus.rdftype
        if focustype.startswith(OSF):
            if focustype == OSF.Registration:
                # for back-compat until datacite 4.5 adds resourceTypeGeneral='StudyRegistration'
                resource_type_text = 'Pre-registration'
            else:
                resource_type_text = without_namespace(focustype, OSF)
        self._add(parent_el, 'resourceType', text=resource_type_text, attrib={
            'resourceTypeGeneral': self._get_resource_type_general(self.basket.focus.iri),
        })

    def _get_resource_type_general(self, focus_iri):
        resource_type_general = 'Text'  # default
        for general_type in self.basket[focus_iri:DCTERMS.type]:
            if isinstance(general_type, rdflib.Literal):
                general_type = str(general_type)
                if general_type in RESOURCE_TYPES_GENERAL:
                    resource_type_general = general_type
        return resource_type_general
