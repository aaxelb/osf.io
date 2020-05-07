#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Populate development database with Institution fixtures."""

import argparse
import logging
import sys
from future.moves.urllib.parse import quote

import django
from django.db import transaction

django.setup()

from website import settings
from website.app import init_app
from osf.models import Institution
from website.search.search import update_institution

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ENVS = [
    "prod",
    "stage",
    "stage2",
    "stage3",
    "test",
]

# TODO: Store only the Entity IDs in OSF DB and move the URL building process to CAS
SHIBBOLETH_SP_LOGIN = "{}/Shibboleth.sso/Login?entityID={{}}".format(
    settings.CAS_SERVER_URL
)
SHIBBOLETH_SP_LOGOUT = "{}/Shibboleth.sso/Logout?return={{}}".format(
    settings.CAS_SERVER_URL
)

# Using optional args instead of positional ones to explicitly set them
parser = argparse.ArgumentParser()
parser.add_argument(
    "-e", "--env", help="select the server: prod, test, stage, stage2 or stage3"
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-i", "--ids", nargs="+", help="select the institution(s) to add or update"
)
group.add_argument(
    "-a", "--all", action="store_true", help="add or update all institutions"
)


def encode_uri_component(val):
    return quote(val, safe="~()*!.'")


def update_or_create(inst_data):
    inst = Institution.load(inst_data["_id"])
    if inst:
        for key, val in inst_data.items():
            setattr(inst, key, val)
        inst.save()
        print("Updated {}".format(inst.name))
        update_institution(inst)
        return inst, False
    else:
        inst = Institution(**inst_data)
        inst.save()
        print("Added new institution: {}".format(inst._id))
        update_institution(inst)
        return inst, True


def main(default_args=False):

    if default_args:
        args = parser.parse_args(["--env", "test", "--all"])
    else:
        args = parser.parse_args()

    server_env = args.env
    update_ids = args.ids
    update_all = args.all

    if not server_env or server_env not in ENVS:
        logger.error("A valid environment must be specified: {}".format(ENVS))
        sys.exit(1)
    institutions = INSTITUTIONS[server_env]

    if not update_all and not update_ids:
        logger.error(
            "Nothing to update or create. Please either specify a list of institutions "
            "using --ids or run for all with --all"
        )
        sys.exit(1)
    elif update_all:
        institutions_to_update = institutions
    else:
        institutions_to_update = [
            inst for inst in institutions if inst["_id"] in update_ids
        ]
        diff_list = list(
            set(update_ids) - set([inst["_id"] for inst in institutions_to_update])
        )
        if diff_list:
            logger.error(
                "One or more institution ID(s) provided via -i or --ids do not match any "
                "existing records: {}.".format(diff_list)
            )
            sys.exit(1)

    with transaction.atomic():
        for inst_data in institutions_to_update:
            update_or_create(inst_data)
        for extra_inst in Institution.objects.exclude(
            _id__in=[x["_id"] for x in institutions]
        ):
            logger.warn(
                "Extra Institution : {} - {}".format(extra_inst._id, extra_inst.name)
            )


INSTITUTIONS = {
    "prod": [
        {
            "_id": "a2jlab",
            "name": "Access to Justice Lab",
            "description": 'Based within Harvard Law School, the <a href="https://a2jlab.org/">Access to Justice Lab</a> works with court administrators, legal service providers, and other stakeholders in the U.S. legal system to design and implement randomized field experiments evaluating interventions that impact access to justice.',
            "banner_name": "a2jlab-banner.png",
            "logo_name": "a2jlab-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["a2jlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "asu",
            "name": "Arizona State University",
            "description": '<a href="https://asu.edu">Arizona State University</a>',
            "banner_name": "asu-banner.png",
            "logo_name": "asu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:asu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.asu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "brown",
            "name": "Brown University",
            "description": 'A Research Project Management and Publication Tool for the Brown University Research Community in partnership with <a href="https://library.brown.edu/info/data_management">Brown University Library Research Data Management Services</a> | <a href="https://www.brown.edu/research/home">Research at Brown</a> | <a href="https://it.brown.edu/computing-policies/policy-handling-brown-restricted-information">Brown Restricted Information Handling Policy</a> | <a href="https://www.brown.edu/about/administration/provost/policies/privacy">Research Privacy Policy</a>',
            "banner_name": "brown-banner.png",
            "logo_name": "brown-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.brown.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.brown.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bt",
            "name": "Boys Town",
            "description": 'A research data service provided by the BTNRH Research Technology Core. Please do not use this service to store or transfer personally identifiable information or personal health information. For assistance please contact <a href="mailto:Christine.Hammans@boystown.org">Christine.Hammans@boystown.org</a>.',
            "banner_name": "bt-banner.png",
            "logo_name": "bt-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/e2ab7419-36ab-4a95-a19f-ee90b6a9b8ac/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://myapps.microsoft.com")
            ),
            "domains": ["osf.boystownhospital.org"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bu",
            "name": "Boston University",
            "description": "A Research Project Management Tool for BU",
            "banner_name": "bu-banner.png",
            "logo_name": "bu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.bu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.bu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "busara",
            "name": "Busara Center for Behavioral Economics",
            "description": 'The <a href="http://www.busaracenter.org/">Busara Center</a> for Behavioral Economics',
            "banner_name": "busara-banner.png",
            "logo_name": "busara-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["busaracenter.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "callutheran",
            "name": "California Lutheran University",
            "description": "",
            "banner_name": "callutheran-banner.png",
            "logo_name": "callutheran-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.callutheran.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "capolicylab",
            "name": "California Policy Lab",
            "description": 'The <a href="https:www.capolicylab.org">California Policy Lab</a> pairs trusted experts from UCLA and UC Berkeley with policymakers to solve our most urgent social problems, including homelessness, poverty, crime, and education inequality.',
            "banner_name": "capolicylab-banner.png",
            "logo_name": "capolicylab-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["capolicylab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cfa",
            "name": "Center for Astrophysics | Harvard & Smithsonian",
            "description": 'Open Source Project Management Tools for the CfA Community: About <a href="https://cos.io/our-products/osf/">OSF</a> | <a href="https://www.cfa.harvard.edu/researchtopics">Research at the CfA</a> | <a href="https://library.cfa.harvard.edu/">CfA Library</a> | <a href="https://openscience.zendesk.com/hc/en-us">Get Help</a>',
            "banner_name": "cfa-banner.png",
            "logo_name": "cfa-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["cfa.harvard.edu"],
            "delegation_protocol": "",
        },
        {
            "_id": "clrn",
            "name": "Character Lab Research Network",
            "description": ' Projects listed below are run through the <a href="https://www.characterlab.org/research-network">Character Lab Research Network</a>, a consortium of trailblazing schools and elite scientists that develop and test activities designed to help students thrive. Character Lab Research Network is a proud supporter of the Student Privacy Pledge to safeguard student privacy. For more details on the Research Network privacy policy, you can refer to the <a href="https://www.characterlab.org/student-privacy">Research Network student privacy policy</a> and <a href="https://www.characterlab.org/student-privacy/faqs">FAQs</a>.',
            "banner_name": "clrn-banner.png",
            "logo_name": "clrn-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["characterlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cmu",
            "name": "Carnegie Mellon University",
            "description": 'A Project Management Tool for the CMU Community: <a href="https://l'
            'ibrary.cmu.edu/OSF">Get Help at CMU</a> | <a href="https://cos.io/o'
            'ur-products/osf/">About OSF</a> | <a href="https://osf.io/support/"'
            '>OSF Support</a> | <a href="https://library.cmu.edu/OSF/terms-of-us'
            'e">Terms of Use</a>',
            "banner_name": "cmu-banner.png",
            "logo_name": "cmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.cmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.library.cmu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "colorado",
            "name": "University of Colorado Boulder",
            "description": 'This service is supported by the Center for Research Data and Digital Scholarship, which is led by <a href="https://www.rc.colorado.edu/">Research Computing</a> and the <a href="http://www.colorado.edu/libraries/">University Libraries</a>.',
            "banner_name": "colorado-banner.png",
            "logo_name": "colorado-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fedauth.colorado.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cord",
            "name": "Concordia College",
            "description": '<a href="https://www.concordiacollege.edu/">Concordia College</a> | <a href="https://www.concordiacollege.edu/academics/library/">Carl B. Ylvisaker Library</a> | <a href="https://cord.libguides.com/?b=s">Research Guides</a>',
            "banner_name": "cord-banner.png",
            "logo_name": "cord-shield.png",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.cord.edu"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "cornell",
            "name": "Cornell University",
            "description": 'Supported by the Cornell Research Data Management Service Group and the Cornell University Library. The OSF service may not be used to store or transfer personally identifiable, confidential/restricted, HIPPA-regulated or any other controlled unclassified information. Learn more at <a href="https://data.research.cornell.edu">https://data.research.cornell.edu</a> | <a href="mailto:rdmsg-help@cornell.edu">rdmsg-help@cornell.edu</a>.',
            "banner_name": "cornell-banner.png",
            "logo_name": "cornell-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibidp.cit.cornell.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cos",
            "name": "Center For Open Science",
            "description": 'COS is a non-profit technology company providing free and open services to increase inclusivity and transparency of research. Find out more at <a href="https://cos.io">cos.io</a>.',
            "banner_name": "cos-banner.png",
            "logo_name": "cos-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "csic",
            "name": "Spanish National Research Council",
            "description": "Related resources are in the institutional intranet web site only.",
            "banner_name": "csic-banner.png",
            "logo_name": "csic-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://www.rediris.es/sir/csicidp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cwru",
            "name": "Case Western Reserve University",
            "description": 'This site is provided as a partnership of the <a href="http://library.case.edu/ksl/">Kelvin Smith Library</a>, <a href="https://case.edu/utech/">University Technology</a>, and the <a href="https://case.edu/research/">Office of Research and Technology Management</a> at <a href="https://case.edu/">Case Western Reserve University</a>. Projects must abide by the <a href="https://case.edu/utech/departments/information-security/policies">University Information Security Policies</a> and <a href="https://case.edu/compliance/about/privacy-management/privacy-related-policies-cwru">Data Privacy Policies</a>.',
            "banner_name": "cwru-banner.png",
            "logo_name": "cwru-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:case.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "duke",
            "name": "Duke University",
            "description": 'A research data service provided by <a href="https://library.duke.edu/data/data-management">Duke Libraries</a>.',
            "banner_name": "duke-banner.png",
            "logo_name": "duke-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:duke.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ecu",
            "name": "East Carolina University",
            "description": 'In partnership with Academic Library Services and Laupus Health Sciences Library. Contact <a href="mailto:scholarlycomm@ecu.edu">scholarlycomm@ecu.edu</a> for more information. Researchers are individually responsible for abiding by university policies. ',
            "banner_name": "ecu-banner.png",
            "logo_name": "ecu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.ecu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "esip",
            "name": "Federation of Earth Science Information Partners (ESIP)",
            "description": '<a href="http://www.esipfed.org/">ESIP\'s</a> mission is to support the networking and data dissemination needs of our members and the global Earth science data community by linking the functional sectors of observation, research, application, education and use of Earth science.',
            "banner_name": "esip-banner.png",
            "logo_name": "esip-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["esipfed.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "ferris",
            "name": "Ferris State University",
            "description": 'In partnership with the <a href="https://www.ferris.edu/research/">Office of Research and Sponsored Programs</a>, the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/index.htm">Provost and Vice President for Academic Affairs</a>, and the <a href="https://www.ferris.edu/library/">FLITE Library</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), intellectual property (IP) or any other controlled unclassified information (CUI). All projects must abide by the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/Forms_Policies/Documents/Policy_Letters/AA-Intellectual-Property-Rights.pdf">FSU Intellectual Property Rights and Electronic Distance Learning Materials</a> letter of agreement.',
            "banner_name": "ferris-banner.png",
            "logo_name": "ferris-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.ferris.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "fsu",
            "name": "Florida State University",
            "description": 'This service is supported by the <a href="https://www.lib.fsu.edu/">FSU Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). FSU\'s <a href="http://regulations.fsu.edu/sites/g/files/upcbnu486/files/policies/research/FSU%20Policy%207A-26.pdf">Research Data Management Policy</a> applies. For assistance please contact the FSU Libraries <a href="mailto:lib-datamgmt@fsu.edu">Research Data Management Program</a>.',
            "banner_name": "fsu-banner.png",
            "logo_name": "fsu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.fsu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gmu",
            "name": "George Mason University",
            "description": 'This service is supported on campus by <a href="https://oria.gmu.edu/">Research Development, Integrity and Assurance</a> (RDIA), <a href="https://library.gmu.edu/"> The Office of Research Computing</a> (ORC), and <a href="https://orc.gmu.edu/">University Libraries</a>. Users should abide by all requirements of Mason\'s <a href="https://universitypolicy.gmu.edu/policies/data-stewardship/">Data Stewardship Policy</a> including not using this service to store or transfer highly sensitive data or any controlled unclassified information. For assistance please contact <a href="mailto:datahelp@gmu.edu">Wendy Mann</a>, Director of Mason\'s Digital Scholarship Center.',
            "banner_name": "gmu-banner.png",
            "logo_name": "gmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibboleth.gmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gwu",
            "name": "The George Washington University",
            "description": 'This service is supported by the <a href="https://library.gwu.edu/">GW Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. Always abide by the <a href="https://compliance.gwu.edu/research-policies">GW Research Policies</a>. Contact the <a href="https://libguides.gwu.edu/prf.php?account_id=151788">GW Data Services Librarian</a> for support.',
            "banner_name": "gwu-banner.png",
            "logo_name": "gwu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://singlesignon.gwu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ibhri",
            "name": "Integrative Behavioral Health Research Institute",
            "description": '<a href="https://www.ibhri.org/">The Integrative Behavioral Health Research Institute</a>',
            "banner_name": "ibhri-banner.png",
            "logo_name": "ibhri-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.ibhri.org"],
            "email_domains": ["ibhri.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "icarehb",
            "name": "ICArEHB",
            "description": '<a href="https://www.icarehb.com">Interdisciplinary Center for Archaeology and Evolution of Human Behaviour</a>',
            "banner_name": "icarehb-banner.png",
            "logo_name": "icarehb-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["icarehb.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "icer",
            "name": "Institute for Clinical and Economic Review",
            "description": "",
            "banner_name": "icer-banner.png",
            "logo_name": "icer-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.icer-review.org"],
            "email_domains": ["icer-review.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "igdore",
            "name": "Institute for Globally Distributed Open Research and Education (IGDORE)",
            "description": "Institute for Globally Distributed Open Research and Education "
            "(IGDORE) is an independent research institute dedicated to improve "
            "the quality of science, science education, and quality of life for "
            "scientists, students, and their families.",
            "banner_name": "igdore-banner.png",
            "logo_name": "igdore-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["igdore.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "iit",
            "name": "Illinois Institute of Technology ",
            "description": "A research data service provided by Illinois Tech Libraries",
            "banner_name": "iit-banner.png",
            "logo_name": "iit-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.iit.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.iit.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "itb",
            "name": "Institut Teknologi Bandung",
            "description": "Institut Teknologi Bandung - OSF Repository",
            "banner_name": "itb-banner.png",
            "logo_name": "itb-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.itb.ac.id/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jhu",
            "name": "Johns Hopkins University",
            "description": 'A research data service provided by the <a href="https://www.library.jhu.edu/">Sheridan Libraries</a>.',
            "banner_name": "jhu-banner.png",
            "logo_name": "jhu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:johnshopkins.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.data.jhu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jmu",
            "name": "James Madison University",
            "description": 'This service is supported on campus by the Office of Research and Scholarship, Central IT, and Libraries and Educational Technology for the JMU campus community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Data Services Coordinator at <a href="mailto:shorisyl@jmu.edu">shorisyl@jmu.edu</a>.',
            "banner_name": "jmu-banner.png",
            "logo_name": "jmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:jmu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.jmu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jpal",
            "name": "J-PAL",
            "description": '<a href="https://www.povertyactionlab.org">https://www.povertyactionlab.org</a>',
            "banner_name": "jpal-banner.png",
            "logo_name": "jpal-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.povertyactionlab.org"],
            "email_domains": ["povertyactionlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "ljaf",
            "name": "Laura and John Arnold Foundation",
            "description": 'Projects listed below are for grants awarded by the Foundation. Please see the <a href="http://www.arnoldfoundation.org/wp-content/uploads/Guidelines-for-Investments-in-Research.pdf">LJAF Guidelines for Investments in Research</a> for more information and requirements.',
            "banner_name": "ljaf-banner.png",
            "logo_name": "ljaf-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["arnoldfoundation.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "mit",
            "name": "Massachusetts Institute of Technology",
            "description": 'A research data service provided by the <a href="https://libraries.mit.edu/">MIT Libraries</a>. Learn more about <a href="https://libraries.mit.edu/data-management/">MIT resources for data management</a>. Please abide by the Institution\'s policy on <a href="https://policies-procedures.mit.edu/privacy-and-disclosure-personal-information/protection-personal-privacy">Privacy and Disclosure of Information</a>.',
            "banner_name": "mit-banner.png",
            "logo_name": "mit-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:mit.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "mq",
            "name": "Macquarie University",
            "description": 'In partnership with the Office of the Deputy Vice-Chancellor (Research) and the University Library. Learn more about <a href="https://staff.mq.edu.au/research/strategy-priorities-and-initiatives/data-science-and-eresearch">Data Science and eResearch</a> at Macquarie University.',
            "banner_name": "mq-banner.png",
            "logo_name": "mq-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("http://www.okta.com/exk2dzwun7KebsDIV2p7")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.mq.edu.au"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame",
            "description": 'In <a href="https://research.nd.edu/news/64035-notre-dame-center-for-open-science-partner-to-advance-open-science-initiatives/">partnership</a> with the <a href="https://crc.nd.edu">Center for Research Computing</a>, <a href="http://esc.nd.edu">Engineering &amp; Science Computing</a>, and the <a href="https://library.nd.edu">Hesburgh Libraries</a>',
            "banner_name": "nd-banner.png",
            "logo_name": "nd-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.nd.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.nd.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nyu",
            "name": "New York University",
            "description": 'A Research Project and File Management Tool for the NYU Community: <a href="https://www.nyu.edu/research.html">Research at NYU</a> | <a href="http://guides.nyu.edu/data_management">Research Data Management Planning</a> | <a href="https://library.nyu.edu/services/research/">NYU Library Research Services</a> | <a href="https://nyu.qualtrics.com/jfe6/form/SV_8dFc5TpA1FgLUMd">Get Help</a>',
            "banner_name": "nyu-banner.png",
            "logo_name": "nyu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:nyu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://shibboleth.nyu.edu/idp/profile/Logout")
            ),
            "domains": ["osf.nyu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "okstate",
            "name": "Oklahoma State University",
            "description": '<a href="http://www.library.okstate.edu/research-support/research-data-services/">OSU Library Research Data Services</a>',
            "banner_name": "okstate-banner.png",
            "logo_name": "okstate-shield.png",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.library.okstate.edu"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "ou",
            "name": "The University of Oklahoma",
            "description": '<a href="https://www.ou.edu">The University of Oklahoma</a> | <a href="https://libraries.ou.edu">University Libraries</a>',
            "banner_name": "ou-banner.png",
            "logo_name": "ou-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.ou.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ou.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "sc",
            "name": "University of South Carolina Libraries",
            "description": 'Brought to you by <a href="http://library.sc.edu/">University Libraries</a> at the University of South Carolina.',
            "banner_name": "sc-banner.png",
            "logo_name": "sc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:sc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.sc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "temple",
            "name": "Temple University",
            "description": 'Projects must abide by Temple University\'s <a href="https://www.temple.edu/privacy-statement">Privacy Statement</a>, <a href="https://its.temple.edu/technology-usage-policy">Technology Usage Policy</a>, <a href="https://its.temple.edu/classification-and-handling-protected-data">University Classification and Handling of Protected Data</a>, and <a href="https://its.temple.edu/guidelines-storing-and-using-personally-identifiable-information-non-production-environments">Guidelines for Storing and Using Personally Identifiable Information in Non-Production Environments</a>.',
            "banner_name": "temple-banner.png",
            "logo_name": "temple-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fim.temple.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "thelabatdc",
            "name": "The Lab @ DC",
            "description": 'The Lab @ DC is an entity of the <a href="https://mayor.dc.gov/">Executive Office of the Mayor of the District of Columbia Government</a>. We work in the <a href="https://oca.dc.gov/">Office of the City Administrator</a> and in partnership with a network of universities and research centers to apply the scientific method into day-to-day governance.',
            "banner_name": "thelabatdc-banner.png",
            "logo_name": "thelabatdc-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["dc.gov"],
            "delegation_protocol": "",
        },
        {
            "_id": "tufts",
            "name": "Tufts University",
            "description": '<a href="http://researchguides.library.tufts.edu/RDM">Research Data Management &#64; Tufts</a>',
            "banner_name": "tufts-banner.png",
            "logo_name": "tufts-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib-idp.tufts.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ua",
            "name": "University of Arizona",
            "description": 'A service supported by the <a href="http://www.library.arizona.edu/">University of Arizona Libraries</a>. For more information, please refer to the <a href="http://data.library.arizona.edu/osf">UA Data Management Page</a>.',
            "banner_name": "ua-banner.png",
            "logo_name": "ua-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:arizona.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.arizona.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ubc",
            "name": "University of British Columbia",
            "description": 'Users are reminded to ensure their use of this service is in compliance with all <a href="https://universitycounsel.ubc.ca/policies/">UBC Policies and Standards</a>. Please refer specifically to <a href="https://universitycounsel.ubc.ca/files/2015/08/policy85.pdf">Policy 85</a>, <a href="https://universitycounsel.ubc.ca/files/2013/06/policy104.pdf">Policy 104</a>, and the <a href="https://cio.ubc.ca/node/1073">Information Security Standards</a>. Find out more about <a href="http://openscience.ubc.ca">OSF</a>. Get help with <a href="https://researchdata.library.ubc.ca/">Research Data Management</a>.',
            "banner_name": "ubc-banner.png",
            "logo_name": "ubc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://authentication.ubc.ca")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.openscience.ubc.ca"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uc",
            "name": "University of Cincinnati",
            "description": 'In partnership with the <a href="https://research.uc.edu/home/officeofresearch/administrativeoffices.aspx">Office of Research</a>, <a href="https://www.libraries.uc.edu/">UC Libraries</a> and <a href="https://www.uc.edu/ucit.html">IT&#64;UC</a>. Projects must abide by <a href="http://www.uc.edu/infosec/policies.html">Security (9.1.27) and Data Protection (9.1.1) Policies.</a> Learn more by visiting <a href="https://libraries.uc.edu/digital-scholarship/data-services.html">Research Data & GIS services</a>.',
            "banner_name": "uc-banner.png",
            "logo_name": "uc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.uc.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucla",
            "name": "UCLA",
            "description": 'A research data service provided by the <a href="https://www.library.ucla.edu/">UCLA Library</a>. Please do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact <a href="mailto:data@library.ucla.edu">data@library.ucla.edu</a>.',
            "banner_name": "ucla-banner.png",
            "logo_name": "ucla-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucla.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucla.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucsd",
            "name": "University of California San Diego",
            "description": 'This service is supported on campus by the UC San Diego Library for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Research Data Curation Program at <a href="mailto:research-data-curation@ucsd.edu">research-data-curation@ucsd.edu</a>.',
            "banner_name": "ucsd-banner.png",
            "logo_name": "ucsd-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucsd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucsd.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucr",
            "name": "University of California Riverside",
            "description": 'Policy prohibits storing PII or HIPAA data on this site, please see C&amp;C\'s <a href="http://cnc.ucr.edu/security/researchers.html">security site</a> for more information.',
            "banner_name": "ucr-banner.png",
            "logo_name": "ucr-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucr.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucr.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uct",
            "name": "University of Cape Town",
            "description": '<a href="http://www.lib.uct.ac.za/">UCT Libraries</a>, <a href="http://www.eresearch.uct.ac.za/">UCT eResearch</a> &amp; <a href="http://www.icts.uct.ac.za/">ICTS</a> present the UCT OSF institutional service to UCT affiliated students, staff and researchers. The UCT OSF facility should be used in conjunction with the institution\'s <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm-policy">Research Data Management (RDM) Policy</a>, <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">Open Access Policy</a> and <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">IP Policy</a>. Visit the <a href="http://www.digitalservices.lib.uct.ac.za/">UCT Digital Library Services</a> for more information and/or assistance with <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm">RDM</a> and <a href="http://www.digitalservices.lib.uct.ac.za/dls/data-sharing-guidelines">data sharing</a>. We also encourage the use of UCT Libraries\'s Data Management Planning tool, <a href="http://dmp.lib.uct.ac.za/about_us">DMPonline</a>',
            "banner_name": "uct-banner.png",
            "logo_name": "uct-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("http://adfs.uct.ac.za/adfs/services/trust")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uct.ac.za"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugent",
            "name": "Universiteit Gent",
            "description": None,
            "banner_name": "ugent-banner.png",
            "logo_name": "ugent-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://identity.ugent.be/simplesaml/saml2/idp/metadata.php"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ugent.be"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugoe",
            "name": "University of Göttingen",
            "description": 'In partnership with <a href="https://www.sub.uni-goettingen.de/">Göttingen State and University Library</a>, the <a href="http://www.eresearch.uni-goettingen.de/">Göttingen eResearch Alliance</a> and the <a href="https://www.gwdg.de/">Gesellschaft für wissenschaftliche Datenverarbeitung Göttingen</a>.',
            "banner_name": "ugoe-banner.png",
            "logo_name": "ugoe-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth-idp.uni-goettingen.de/uni/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uni-goettingen.de"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "unc",
            "name": "University of North Carolina at Chapel Hill",
            "description": 'This service is supported by <a href="https://odum.unc.edu/">The Odum Institute for Research in Social Science</a> and <a href="https://library.unc.edu">University Libraries at the University of North Carolina at Chapel Hill</a>. Please do not store or transfer personally identifiable information, personal health information, or any other sensitive or proprietary data in the OSF. Projects should follow applicable <a href="https://unc.policystat.com/">UNC policies</a>. Contact the <a href="mailto:odumarchive@unc.edu">Odum Institute Data Archive</a> with any questions.',
            "banner_name": "unc-banner.png",
            "logo_name": "unc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:unc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "universityofkent",
            "name": "University of Kent",
            "description": 'Collaboration Platform for University of Kent Research | <a href="https://www.kent.ac.uk/governance/policies-and-procedures/documents/Information-security-policy-v1-1.pdf">Information Security policy</a> | <a href="mailto:researchsupport@kent.ac.uk">Help and Support</a>',
            "banner_name": "universityofkent-banner.png",
            "logo_name": "universityofkent-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.id.kent.ac.uk/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "usc",
            "name": "University of Southern California",
            "description": 'Projects must abide by <a href="http://policy.usc.edu/info-security/">USC\'s Information Security Policy</a>. Data stored for human subject research repositories must abide by <a href="http://policy.usc.edu/biorepositories/">USC\'s Biorepository Policy</a>. The OSF may not be used for storage of Personal Health Information that is subject to <a href="http://policy.usc.edu/hipaa/">HIPPA regulations</a>.',
            "banner_name": "usc-banner.png",
            "logo_name": "usc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:usc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.usc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ush",
            "name": "Universal Sustainability Hub",
            "description": '<a href="https://uvers.ac.id/">Universal Sustainability Hub for Universal Family</a>',
            "banner_name": "ush-banner.png",
            "logo_name": "ush-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["uvers.ac.id"],
            "delegation_protocol": "",
        },
        {
            "_id": "utdallas",
            "name": "The University of Texas at Dallas",
            "description": 'In partnership with the Office of Research. Learn more about <a href="https://data.utdallas.edu/">UT Dallas resources for computational and data-driven research</a>. Projects must abide by university security and data protection policies.',
            "banner_name": "utdallas-banner.png",
            "logo_name": "utdallas-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.utdallas.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.utdallas.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uva",
            "name": "University of Virginia",
            "description": 'In partnership with the <a href="http://www.virginia.edu/vpr/">Vice President for Research</a>, <a href="http://dsi.virginia.edu">Data Science Institute</a>, <a href="https://www.hsl.virginia.edu">Health Sciences Library</a>, and <a href="http://data.library.virginia.edu">University Library</a>. Learn more about <a href="http://cadre.virginia.edu">UVA resources for computational and data-driven research</a>. Projects must abide by the <a href="http://www.virginia.edu/informationpolicy/security.html">University Security and Data Protection Policies</a>.',
            "banner_name": "uva-banner.png",
            "logo_name": "uva-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:virginia.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.virginia.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uw",
            "name": "University of Washington",
            "description": 'This service is supported by the University of Washington Libraries. Do not use this service to store or transfer personally identifiable information or personal health information. Questions? Email the Libraries Research Data Services Unit at <a href="mailto:libdata@uw.edu">libdata@uw.edu</a>.',
            "banner_name": "uw-banner.png",
            "logo_name": "uw-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:washington.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uwstout",
            "name": "University of Wisconsin - Stout",
            "description": 'A Research Project and File Management Tool for the UW-Stout Community: <a href="https://wwwcs.uwstout.edu/rs/index.cfm">Office of Research and Sponsored Programs</a> | <a href="https://wwwcs.uwstout.edu/lib/">University Library</a>',
            "banner_name": "uwstout-banner.png",
            "logo_name": "uwstout-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://smidp.uwstout.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["open.uwstout.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vcu",
            "name": "Virginia Commonwealth University",
            "description": 'This service is supported by the VCU Libraries and the VCU Office of Research and Innovation for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). VCU\'s policy entitled "<a href="http://www.policy.vcu.edu/sites/default/files/Research%20Data%20Ownership,%20Retention,%20Access%20and%20Securty.pdf">Research Data Ownership, Retention, Access and Security</a>" applies. For assistance please contact the <a href="https://www.library.vcu.edu/services/data/">VCU Libraries Research Data Management Program</a>.',
            "banner_name": "vcu-banner.png",
            "logo_name": "vcu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibboleth.vcu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.research.vcu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vt",
            "name": "Virginia Tech",
            "description": 'Made possible by the <a href="https://www.lib.vt.edu">University Libraries</a> in partnership with <a href="https://secure.hosting.vt.edu/www.arc.vt.edu/">Advanced Research Computing</a> and the <a href="https://research.vt.edu/">Office of the Vice President for Research</a>. Using the Virginia Tech login to OSF provides your name and VT email address to the Center for Open Science. Please see their <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">terms of service</a>.',
            "banner_name": "vt-banner.png",
            "logo_name": "vt-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:vt.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "wustl",
            "name": "Washington University in St. Louis",
            "description": 'This service is supported by the <a href="https://library.wustl.edu">Washington University in St. Louis Libraries</a>. Please abide by the University policy on <a href="https://informationsecurity.wustl.edu/resources/information-security-solutions/data-classification/">information security</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). | For assistance please contact the <a href="http://gis.wustl.edu/dgs">WU Libraries Data & GIS Services</a>.',
            "banner_name": "wustl-banner.png",
            "logo_name": "wustl-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.wustl.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.wustl.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
    ],
    "stage": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage]",
            "description": "Center for Open Science [Stage]",
            "banner_name": "cos-banner.png",
            "logo_name": "cos-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame [Stage]",
            "description": "University of Notre Dame [Stage]",
            "banner_name": "nd-banner.png",
            "logo_name": "nd-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login-test.cc.nd.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://staging.osf.io/goodbye")
            ),
            "domains": ["staging-osf-nd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "google",
            "name": "Google [Stage]",
            "description": "Google [Stage]",
            "banner_name": "google-banner.png",
            "logo_name": "google-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["gmail.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "yahoo",
            "name": "Yahoo [Stage]",
            "description": "Yahoo [Stage]",
            "banner_name": "yahoo-banner.png",
            "logo_name": "yahoo-shield.png",
            "login_url": None,
            "domains": [],
            "email_domains": ["yahoo.com"],
            "delegation_protocol": "",
        },
    ],
    "stage2": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage2]",
            "description": "Center for Open Science [Stage2]",
            "banner_name": "cos-banner.png",
            "logo_name": "cos-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging2-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
    ],
    "stage3": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage3]",
            "description": "Center for Open Science [Stage3]",
            "banner_name": "cos-banner.png",
            "logo_name": "cos-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging3-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
    ],
    "test": [
        {
            "_id": "a2jlab",
            "name": "Access to Justice Lab [Test]",
            "description": 'Based within Harvard Law School, the <a href="https://a2jlab.org/">Access to Justice Lab</a> works with court administrators, legal service providers, and other stakeholders in the U.S. legal system to design and implement randomized field experiments evaluating interventions that impact access to justice.',
            "banner_name": "a2jlab-banner.png",
            "logo_name": "a2jlab-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["a2jlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "asu",
            "name": "Arizona State University [Test]",
            "description": '<a href="https://asu.edu">Arizona State University</a>',
            "banner_name": "asu-banner.png",
            "logo_name": "asu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:asu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-asu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "brown",
            "name": "Brown University [Test]",
            "description": 'A Research Project Management and Publication Tool for the Brown University Research Community in partnership with <a href="https://library.brown.edu/info/data_management">Brown University Library Research Data Management Services</a> | <a href="https://www.brown.edu/research/home">Research at Brown</a> | <a href="https://it.brown.edu/computing-policies/policy-handling-brown-restricted-information">Brown Restricted Information Handling Policy</a> | <a href="https://www.brown.edu/about/administration/provost/policies/privacy">Research Privacy Policy</a>',
            "banner_name": "brown-banner.png",
            "logo_name": "brown-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.brown.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-brown.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bt",
            "name": "Boys Town [Test]",
            "description": 'A research data service provided by the BTNRH Research Technology Core. Please do not use this service to store or transfer personally identifiable information or personal health information. For assistance please contact <a href="mailto:Christine.Hammans@boystown.org">Christine.Hammans@boystown.org</a>.',
            "banner_name": "bt-banner.png",
            "logo_name": "bt-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/e2ab7419-36ab-4a95-a19f-ee90b6a9b8ac/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://myapps.microsoft.com")
            ),
            "domains": ["test-osf-bt.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bu",
            "name": "Boston University [Test]",
            "description": "A Research Project Management Tool for BU",
            "banner_name": "bu-banner.png",
            "logo_name": "bu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.bu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-bu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "busara",
            "name": "Busara Center for Behavioral Economics [Test]",
            "description": 'The <a href="http://www.busaracenter.org/">Busara Center</a> for Behavioral Economics',
            "banner_name": "busara-banner.png",
            "logo_name": "busara-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["busaracenter.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "callutheran",
            "name": "California Lutheran University SAML-SSO [Test]",
            "description": "",
            "banner_name": "callutheran-banner.png",
            "logo_name": "callutheran-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.callutheran.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-callutheran.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "callutheran2",
            "name": "California Lutheran University CAS-SSO [Test]",
            "description": "",
            "banner_name": "callutheran-banner.png",
            "logo_name": "callutheran-shield.png",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-callutheran2.cos.io"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "capolicylab",
            "name": "California Policy Lab [Test]",
            "description": 'The <a href="https:www.capolicylab.org">California Policy Lab</a> pairs trusted experts from UCLA and UC Berkeley with policymakers to solve our most urgent social problems, including homelessness, poverty, crime, and education inequality.',
            "banner_name": "capolicylab-banner.png",
            "logo_name": "capolicylab-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["capolicylab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cfa",
            "name": "Center for Astrophysics | Harvard & Smithsonian [Test]",
            "description": 'Open Source Project Management Tools for the CfA Community: About <a href="https://cos.io/our-products/osf/">OSF</a> | <a href="https://www.cfa.harvard.edu/researchtopics">Research at the CfA</a> | <a href="https://library.cfa.harvard.edu/">CfA Library</a> | <a href="https://openscience.zendesk.com/hc/en-us">Get Help</a>',
            "banner_name": "cfa-banner.png",
            "logo_name": "cfa-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["cfa.harvard.edu"],
            "delegation_protocol": "",
        },
        {
            "_id": "clrn",
            "name": "Character Lab Research Network [Test]",
            "description": ' Projects listed below are run through the <a href="https://www.characterlab.org/research-network">Character Lab Research Network</a>, a consortium of trailblazing schools and elite scientists that develop and test activities designed to help students thrive. Character Lab Research Network is a proud supporter of the Student Privacy Pledge to safeguard student privacy. For more details on the Research Network privacy policy, you can refer to the <a href="https://www.characterlab.org/student-privacy">Research Network student privacy policy</a> and <a href="https://www.characterlab.org/student-privacy/faqs">FAQs</a>.',
            "banner_name": "clrn-banner.png",
            "logo_name": "clrn-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["characterlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cmu",
            "name": "Carnegie Mellon University [Test]",
            "description": 'A Project Management Tool for the CMU Community: <a href="https://l'
            'ibrary.cmu.edu/OSF">Get Help at CMU</a> | <a href="https://cos.io/o'
            'ur-products/osf/">About OSF</a> | <a href="https://osf.io/support/"'
            '>OSF Support</a> | <a href="https://library.cmu.edu/OSF/terms-of-us'
            'e">Terms of Use</a>',
            "banner_name": "cmu-banner.png",
            "logo_name": "cmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.cmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "colorado",
            "name": "University of Colorado Boulder [Test]",
            "description": 'This service is supported by the Center for Research Data and Digital Scholarship, which is led by <a href="https://www.rc.colorado.edu/">Research Computing</a> and the <a href="http://www.colorado.edu/libraries/">University Libraries</a>.',
            "banner_name": "colorado-banner.png",
            "logo_name": "colorado-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fedauth.colorado.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cornell",
            "name": "Cornell University [Test]",
            "description": 'Supported by the Cornell Research Data Management Service Group and the Cornell University Library. The OSF service may not be used to store or transfer personally identifiable, confidential/restricted, HIPPA-regulated or any other controlled unclassified information. Learn more at <a href="https://data.research.cornell.edu">https://data.research.cornell.edu</a> | <a href="mailto:rdmsg-help@cornell.edu">rdmsg-help@cornell.edu</a>.',
            "banner_name": "cornell-banner.png",
            "logo_name": "cornell-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibidp.cit.cornell.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cornell.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cord",
            "name": "Concordia College [Test]",
            "description": '<a href="https://www.concordiacollege.edu/">Concordia College</a> | <a href="https://www.concordiacollege.edu/academics/library/">Carl B. Ylvisaker Library</a> | <a href="https://cord.libguides.com/?b=s">Research Guides</a>',
            "banner_name": "cord-banner.png",
            "logo_name": "cord-shield.png",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cord.cos.io"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "cos",
            "name": "Center For Open Science [Test]",
            "description": 'COS is a non-profit technology company providing free and open services to increase inclusivity and transparency of research. Find out more at <a href="https://cos.io">cos.io</a>.',
            "banner_name": "cos-banner.png",
            "logo_name": "cos-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "csic",
            "name": "Spanish National Research Council [Test]",
            "description": "Related resources are in the institutional intranet web site only.",
            "banner_name": "csic-banner.png",
            "logo_name": "csic-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://www.rediris.es/sir/shibtestidp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cwru",
            "name": "Case Western Reserve University [Test]",
            "description": 'This site is provided as a partnership of the <a href="http://library.case.edu/ksl/">Kelvin Smith Library</a>, <a href="https://case.edu/utech/">University Technology</a>, and the <a href="https://case.edu/research/">Office of Research and Technology Management</a> at <a href="https://case.edu/">Case Western Reserve University</a>. Projects must abide by the <a href="https://case.edu/utech/departments/information-security/policies">University Information Security Policies</a> and <a href="https://case.edu/compliance/about/privacy-management/privacy-related-policies-cwru">Data Privacy Policies</a>.',
            "banner_name": "cwru-banner.png",
            "logo_name": "cwru-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:case.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cwru.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "duke",
            "name": "Duke University [Test]",
            "description": 'A research data service provided by <a href="https://library.duke.edu/data/data-management">Duke Libraries</a>.',
            "banner_name": "duke-banner.png",
            "logo_name": "duke-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:duke.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ecu",
            "name": "East Carolina University [Test]",
            "description": 'In partnership with Academic Library Services and Laupus Health Sciences Library. Contact <a href="mailto:scholarlycomm@ecu.edu">scholarlycomm@ecu.edu</a> for more information. Researchers are individually responsible for abiding by university policies. ',
            "banner_name": "ecu-banner.png",
            "logo_name": "ecu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.ecu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "esip",
            "name": "Federation of Earth Science Information Partners (ESIP) [Test]",
            "description": '<a href="http://www.esipfed.org/">ESIP\'s</a> mission is to support the networking and data dissemination needs of our members and the global Earth science data community by linking the functional sectors of observation, research, application, education and use of Earth science.',
            "banner_name": "esip-banner.png",
            "logo_name": "esip-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["esipfed.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "ferris",
            "name": "Ferris State University [Test]",
            "description": 'In partnership with the <a href="https://www.ferris.edu/research/">Office of Research and Sponsored Programs</a>, the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/index.htm">Provost and Vice President for Academic Affairs</a>, and the <a href="https://www.ferris.edu/library/">FLITE Library</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), intellectual property (IP) or any other controlled unclassified information (CUI). All projects must abide by the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/Forms_Policies/Documents/Policy_Letters/AA-Intellectual-Property-Rights.pdf">FSU Intellectual Property Rights and Electronic Distance Learning Materials</a> letter of agreement.',
            "banner_name": "ferris-banner.png",
            "logo_name": "ferris-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.ferris.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "fsu",
            "name": "Florida State University [Test]",
            "description": 'This service is supported by the <a href="https://www.lib.fsu.edu/">FSU Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). FSU\'s <a href="http://regulations.fsu.edu/sites/g/files/upcbnu486/files/policies/research/FSU%20Policy%207A-26.pdf">Research Data Management Policy</a> applies. For assistance please contact the FSU Libraries <a href="mailto:lib-datamgmt@fsu.edu">Research Data Management Program</a>.',
            "banner_name": "fsu-banner.png",
            "logo_name": "fsu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-fsu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gmu",
            "name": "George Mason University [Test]",
            "description": 'This service is supported on campus by <a href="https://oria.gmu.edu/">Research Development, Integrity and Assurance</a> (RDIA), <a href="https://library.gmu.edu/"> The Office of Research Computing</a> (ORC), and <a href="https://orc.gmu.edu/">University Libraries</a>. Users should abide by all requirements of Mason\'s <a href="https://universitypolicy.gmu.edu/policies/data-stewardship/">Data Stewardship Policy</a> including not using this service to store or transfer highly sensitive data or any controlled unclassified information. For assistance please contact <a href="mailto:datahelp@gmu.edu">Wendy Mann</a>, Director of Mason\'s Digital Scholarship Center.',
            "banner_name": "gmu-banner.png",
            "logo_name": "gmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibboleth.gmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-gmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gwu",
            "name": "The George Washington University [Test]",
            "description": 'This service is supported by the <a href="https://library.gwu.edu/">GW Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. Always abide by the <a href="https://compliance.gwu.edu/research-policies">GW Research Policies</a>. Contact the <a href="https://libguides.gwu.edu/prf.php?account_id=151788">GW Data Services Librarian</a> for support.',
            "banner_name": "gwu-banner.png",
            "logo_name": "gwu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://singlesignon.gwu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-gwu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ibhri",
            "name": "Integrative Behavioral Health Research Institute [Test]",
            "description": '<a href="https://www.ibhri.org/">The Integrative Behavioral Health Research Institute</a>',
            "banner_name": "ibhri-banner.png",
            "logo_name": "ibhri-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-ibhri.cos.io"],
            "email_domains": ["ibhri.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "icarehb",
            "name": "ICArEHB [Test]",
            "description": '<a href="https://www.icarehb.com">Interdisciplinary Center for Archaeology and Evolution of Human Behaviour</a>',
            "banner_name": "icarehb-banner.png",
            "logo_name": "icarehb-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icarehb.cos.io"],
            "email_domains": ["icarehb.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "icer",
            "name": "Institute for Clinical and Economic Review [Test]",
            "description": "",
            "banner_name": "icer-banner.png",
            "logo_name": "icer-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icer.cos.io"],
            "email_domains": ["icer-review.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "igdore",
            "name": "Institute for Globally Distributed Open Research and Education [Test]",
            "description": "Institute for Globally Distributed Open Research and Education "
            "(IGDORE) is an independent research institute dedicated to improve "
            "the quality of science, science education, and quality of life for "
            "scientists, students, and their families.",
            "banner_name": "igdore-banner.png",
            "logo_name": "igdore-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icer.igdore.io"],
            "email_domains": ["igdore.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "iit",
            "name": "Illinois Institute of Technology [Test]",
            "description": "A research data service provided by Illinois Tech Libraries",
            "banner_name": "iit-banner.png",
            "logo_name": "iit-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.iit.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-iit.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "itb",
            "name": "Institut Teknologi Bandung [Test]",
            "description": "Institut Teknologi Bandung - OSF Repository",
            "banner_name": "itb-banner.png",
            "logo_name": "itb-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login-dev3.itb.ac.id/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-itb.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jhu",
            "name": "Johns Hopkins University [Test]",
            "description": 'A research data service provided by the <a href="https://www.library.jhu.edu/">Sheridan Libraries</a>.',
            "banner_name": "jhu-banner.png",
            "logo_name": "jhu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:johnshopkins.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-jhu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jmu",
            "name": "James Madison University [Test]",
            "description": 'This service is supported on campus by the Office of Research and Scholarship, Central IT, and Libraries and Educational Technology for the JMU campus community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Data Services Coordinator at <a href="mailto:shorisyl@jmu.edu">shorisyl@jmu.edu</a>.',
            "banner_name": "jmu-banner.png",
            "logo_name": "jmu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:jmu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-jmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jpal",
            "name": "J-PAL [Test]",
            "description": '<a href="https://www.povertyactionlab.org">https://www.povertyactionlab.org</a>',
            "banner_name": "jpal-banner.png",
            "logo_name": "jpal-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-jpal.cos.io"],
            "email_domains": ["povertyactionlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "ljaf",
            "name": "Laura and John Arnold Foundation [Test]",
            "description": 'Projects listed below are for grants awarded by the Foundation. Please see the <a href="http://www.arnoldfoundation.org/wp-content/uploads/Guidelines-for-Investments-in-Research.pdf">LJAF Guidelines for Investments in Research</a> for more information and requirements.',
            "banner_name": "ljaf-banner.png",
            "logo_name": "ljaf-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["arnoldfoundation.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "mit",
            "name": "Massachusetts Institute of Technology [Test]",
            "description": 'A research data service provided by the <a href="https://libraries.mit.edu/">MIT Libraries</a>. Learn more about <a href="https://libraries.mit.edu/data-management/">MIT resources for data management</a>. Please abide by the Institution\'s policy on <a href="https://policies-procedures.mit.edu/privacy-and-disclosure-personal-information/protection-personal-privacy">Privacy and Disclosure of Information</a>.',
            "banner_name": "mit-banner.png",
            "logo_name": "mit-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:mit.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-mit.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "mq",
            "name": "Macquarie University [Test]",
            "description": 'In partnership with the Office of the Deputy Vice-Chancellor (Research) and the University Library. Learn more about <a href="https://staff.mq.edu.au/research/strategy-priorities-and-initiatives/data-science-and-eresearch">Data Science and eResearch</a> at Macquarie University.',
            "banner_name": "mq-banner.png",
            "logo_name": "mq-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("http://www.okta.com/exkebok0cpJxGzMKz0h7")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-mq.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame [Test]",
            "description": 'In <a href="https://research.nd.edu/news/64035-notre-dame-center-for-open-science-partner-to-advance-open-science-initiatives/">partnership</a> with the <a href="https://crc.nd.edu">Center for Research Computing</a>, <a href="http://esc.nd.edu">Engineering &amp; Science Computing</a>, and the <a href="https://library.nd.edu">Hesburgh Libraries</a>',
            "banner_name": "nd-banner.png",
            "logo_name": "nd-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login-test.cc.nd.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-nd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nyu",
            "name": "New York University [Test]",
            "description": 'A Research Project and File Management Tool for the NYU Community: <a href="https://www.nyu.edu/research.html">Research at NYU</a> | <a href="http://guides.nyu.edu/data_management">Research Data Management Planning</a> | <a href="https://library.nyu.edu/services/research/">NYU Library Research Services</a> | <a href="https://nyu.qualtrics.com/jfe6/form/SV_8dFc5TpA1FgLUMd">Get Help</a>',
            "banner_name": "nyu-banner.png",
            "logo_name": "nyu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibbolethqa.es.its.nyu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component(
                    "https://shibbolethqa.es.its.nyu.edu/idp/profile/Logout"
                )
            ),
            "domains": ["test-osf-nyu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "okstate",
            "name": "Oklahoma State University [Test]",
            "description": '<a href="http://www.library.okstate.edu/research-support/research-data-services/">OSU Library Research Data Services</a>',
            "banner_name": "okstate-banner.png",
            "logo_name": "okstate-shield.png",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-library-okstate.cos.io"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "ou",
            "name": "The University of Oklahoma [Test]",
            "description": '<a href="https://www.ou.edu">The University of Oklahoma</a> | <a href="https://libraries.ou.edu">University Libraries</a>',
            "banner_name": "ou-banner.png",
            "logo_name": "ou-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.ou.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ou.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "sc",
            "name": "University of South Carolina Libraries [Test]",
            "description": 'Brought to you by <a href="http://library.sc.edu/">University Libraries</a> at the University of South Carolina.',
            "banner_name": "sc-banner.png",
            "logo_name": "sc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:sc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-sc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "temple",
            "name": "Temple University [Test]",
            "description": 'Projects must abide by the <a href="https://computerservices.temple.edu/classification-and-handling-protected-data">University Classification and Handling of Protected Data</a> and <a href="https://computerservices.temple.edu/guidelines-storing-and-using-personally-identifiable-information-non-production-environments">Guidelines for Storing and Using Personally Identifiable Information in Non-Production Environments</a>.',
            "banner_name": "temple-banner.png",
            "logo_name": "temple-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fim.temple.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-temple.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "thelabatdc",
            "name": "The Lab @ DC",
            "description": 'The Lab @ DC is an entity of the <a href="https://mayor.dc.gov/">Executive Office of the Mayor of the District of Columbia Government</a>. We work in the <a href="https://oca.dc.gov/">Office of the City Administrator</a> and in partnership with a network of universities and research centers to apply the scientific method into day-to-day governance.',
            "banner_name": "thelabatdc-banner.png",
            "logo_name": "thelabatdc-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["dc.gov"],
            "delegation_protocol": "",
        },
        {
            "_id": "tufts",
            "name": "Tufts University [Test]",
            "description": '<a href="http://researchguides.library.tufts.edu/RDM">Research Data Management &#64; Tufts</a>',
            "banner_name": "tufts-banner.png",
            "logo_name": "tufts-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib-idp.tufts.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-tufts.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ua",
            "name": "University of Arizona [Test]",
            "description": 'A service supported by the <a href="http://www.library.arizona.edu/">University of Arizona Libraries</a>. For more information, please refer to the <a href="http://data.library.arizona.edu/osf">UA Data Management Page</a>.',
            "banner_name": "ua-banner.png",
            "logo_name": "ua-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:arizona.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ua.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ubc",
            "name": "University of British Columbia [Test]",
            "description": 'Users are reminded to ensure their use of this service is in compliance with all <a href="https://universitycounsel.ubc.ca/policies/">UBC Policies and Standards</a>. Please refer specifically to <a href="https://universitycounsel.ubc.ca/files/2015/08/policy85.pdf">Policy 85</a>, <a href="https://universitycounsel.ubc.ca/files/2013/06/policy104.pdf">Policy 104</a>, and the <a href="https://cio.ubc.ca/node/1073">Information Security Standards</a>. Find out more about <a href="http://openscience.ubc.ca">OSF</a>. Get help with <a href="https://researchdata.library.ubc.ca/">Research Data Management</a>.',
            "banner_name": "ubc-banner.png",
            "logo_name": "ubc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://authentication.stg.id.ubc.ca")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ubc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uc",
            "name": "University of Cincinnati [Test]",
            "description": 'In partnership with the <a href="https://research.uc.edu/home/officeofresearch/administrativeoffices.aspx">Office of Research</a>, <a href="https://www.libraries.uc.edu/">UC Libraries</a> and <a href="https://www.uc.edu/ucit.html">IT&#64;UC</a>. Projects must abide by <a href="http://www.uc.edu/infosec/policies.html">Security (9.1.27) and Data Protection (9.1.1) Policies.</a> Learn more by visiting <a href="https://libraries.uc.edu/digital-scholarship/data-services.html">Research Data & GIS services</a>.',
            "banner_name": "uc-banner.png",
            "logo_name": "uc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.uc.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucla",
            "name": "UCLA [Test]",
            "description": 'A research data service provided by the <a href="https://www.library.ucla.edu/">UCLA Library</a>. Please do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact <a href="mailto:data@library.ucla.edu">data@library.ucla.edu</a>.',
            "banner_name": "ucla-banner.png",
            "logo_name": "ucla-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucla.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucla.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucsd",
            "name": "University of California San Diego [Test]",
            "description": 'This service is supported on campus by the UC San Diego Library for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Research Data Curation Program at <a href="mailto:research-data-curation@ucsd.edu">research-data-curation@ucsd.edu</a>.',
            "banner_name": "ucsd-banner.png",
            "logo_name": "ucsd-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucsd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucsd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucr",
            "name": "University of California Riverside [Test]",
            "description": 'Policy prohibits storing PII or HIPAA data on this site, please see C&amp;C\'s <a href="http://cnc.ucr.edu/security/researchers.html">security site</a> for more information.',
            "banner_name": "ucr-banner.png",
            "logo_name": "ucr-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucr.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucr.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uct",
            "name": "University of Cape Town [Test]",
            "description": '<a href="http://www.lib.uct.ac.za/">UCT Libraries</a>, <a href="http://www.eresearch.uct.ac.za/">UCT eResearch</a> &amp; <a href="http://www.icts.uct.ac.za/">ICTS</a> present the UCT OSF institutional service to UCT affiliated students, staff and researchers. The UCT OSF facility should be used in conjunction with the institution\'s <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm-policy">Research Data Management (RDM) Policy</a>, <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">Open Access Policy</a> and <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">IP Policy</a>. Visit the <a href="http://www.digitalservices.lib.uct.ac.za/">UCT Digital Library Services</a> for more information and/or assistance with <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm">RDM</a> and <a href="http://www.digitalservices.lib.uct.ac.za/dls/data-sharing-guidelines">data sharing</a>. We also encourage the use of UCT Libraries\'s Data Management Planning tool, <a href="http://dmp.lib.uct.ac.za/about_us">DMPonline</a>',
            "banner_name": "uct-banner.png",
            "logo_name": "uct-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("http://adfs.uct.ac.za/adfs/services/trust")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uct.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugent",
            "name": "Universiteit Gent [Test]",
            "description": None,
            "banner_name": "ugent-banner.png",
            "logo_name": "ugent-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://ideq.ugent.be/simplesaml/saml2/idp/metadata.php"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ugent.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugoe",
            "name": "University of Göttingen [Test]",
            "description": 'In partnership with <a href="https://www.sub.uni-goettingen.de/">Göttingen State and University Library</a>, the <a href="http://www.eresearch.uni-goettingen.de/">Göttingen eResearch Alliance</a> and the <a href="https://www.gwdg.de/">Gesellschaft für wissenschaftliche Datenverarbeitung Göttingen</a>.',
            "banner_name": "ugoe-banner.png",
            "logo_name": "ugoe-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth-idp.uni-goettingen.de/uni/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ugoe.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uit",
            "name": "UiT The Arctic University of Norway [Test]",
            "description": "UiT The Arctic University of Norway is a medium-sized research "
            "university that contributes to knowledge-based development at the "
            "regional, national and international level.",
            "banner_name": "uit-banner.png",
            "logo_name": "uit-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-uit.cos.io"],
            "email_domains": ["uit.no"],
            "delegation_protocol": "",
        },
        {
            "_id": "unc",
            "name": "University of North Carolina at Chapel Hill [Test]",
            "description": 'This service is supported by <a href="https://odum.unc.edu/">The Odum Institute for Research in Social Science</a> and <a href="https://library.unc.edu">University Libraries at the University of North Carolina at Chapel Hill</a>. Please do not store or transfer personally identifiable information, personal health information, or any other sensitive or proprietary data in the OSF. Projects should follow applicable <a href="https://unc.policystat.com/">UNC policies</a>. Contact the <a href="mailto:odumarchive@unc.edu">Odum Institute Data Archive</a> with any questions.',
            "banner_name": "unc-banner.png",
            "logo_name": "unc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:unc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-unc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "universityofkent",
            "name": "University of Kent [Test]",
            "description": 'Collaboration Platform for University of Kent Research | <a href="https://www.kent.ac.uk/governance/policies-and-procedures/documents/Information-security-policy-v1-1.pdf">Information Security policy</a> | <a href="mailto:researchsupport@kent.ac.uk">Help and Support</a>',
            "banner_name": "universityofkent-banner.png",
            "logo_name": "universityofkent-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.id.kent.ac.uk/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-universityofkent.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "usc",
            "name": "University of Southern California [Test]",
            "description": 'Projects must abide by <a href="http://policy.usc.edu/info-security/">USC\'s Information Security Policy</a>. Data stored for human subject research repositories must abide by <a href="http://policy.usc.edu/biorepositories/">USC\'s Biorepository Policy</a>. The OSF may not be used for storage of Personal Health Information that is subject to <a href="http://policy.usc.edu/hipaa/">HIPPA regulations</a>.',
            "banner_name": "usc-banner.png",
            "logo_name": "usc-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:usc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-usc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ush",
            "name": "Universal Sustainability Hub [Test]",
            "description": '<a href="https://uvers.ac.id/">Universal Sustainability Hub for Universal Family</a>',
            "banner_name": "ush-banner.png",
            "logo_name": "ush-shield.png",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-ush.cos.io"],
            "email_domains": ["uvers.ac.id"],
            "delegation_protocol": "",
        },
        {
            "_id": "utdallas",
            "name": "The University of Texas at Dallas [Test]",
            "description": 'In partnership with the Office of Research. Learn more about <a href="https://data.utdallas.edu/">UT Dallas resources for computational and data-driven research</a>. Projects must abide by university security and data protection policies.',
            "banner_name": "utdallas-banner.png",
            "logo_name": "utdallas-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.utdallas.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-utdallas.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uva",
            "name": "University of Virginia [Test]",
            "description": 'In partnership with the <a href="http://www.virginia.edu/vpr/">Vice President for Research</a>, <a href="http://dsi.virginia.edu">Data Science Institute</a>, <a href="https://www.hsl.virginia.edu">Health Sciences Library</a>, and <a href="http://data.library.virginia.edu">University Library</a>. Learn more about <a href="http://cadre.virginia.edu">UVA resources for computational and data-driven research</a>. Projects must abide by the <a href="http://www.virginia.edu/informationpolicy/security.html">University Security and Data Protection Policies</a>.',
            "banner_name": "uva-banner.png",
            "logo_name": "uva-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibidp-test.its.virginia.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-virginia.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uw",
            "name": "University of Washington [Test]",
            "description": 'This service is supported by the University of Washington Libraries. Do not use this service to store or transfer personally identifiable information or personal health information. Questions? Email the Libraries Research Data Services Unit at <a href="mailto:libdata@uw.edu">libdata@uw.edu</a>.',
            "banner_name": "uw-banner.png",
            "logo_name": "uw-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:washington.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uwstout",
            "name": "University of Wisconsin - Stout [Test]",
            "description": 'A Research Project and File Management Tool for the UW-Stout Community: <a href="https://wwwcs.uwstout.edu/rs/index.cfm">Office of Research and Sponsored Programs</a> | <a href="https://wwwcs.uwstout.edu/lib/">University Library</a>',
            "banner_name": "uwstout-banner.png",
            "logo_name": "uwstout-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://smidp.uwstout.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uwstout.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vcu",
            "name": "Virginia Commonwealth University [Test]",
            "description": 'This service is supported by the VCU Libraries and the VCU Office of Research and Innovation for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). VCU\'s policy entitled "<a href="http://www.policy.vcu.edu/sites/default/files/Research%20Data%20Ownership,%20Retention,%20Access%20and%20Securty.pdf">Research Data Ownership, Retention, Access and Security</a>" applies. For assistance please contact the <a href="https://www.library.vcu.edu/services/data/">VCU Libraries Research Data Management Program</a>.',
            "banner_name": "vcu-banner.png",
            "logo_name": "vcu-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shibboleth.vcu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-research-vcu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vt",
            "name": "Virginia Tech [Test]",
            "description": 'Made possible by the <a href="https://www.lib.vt.edu">University Libraries</a> in partnership with <a href="https://secure.hosting.vt.edu/www.arc.vt.edu/">Advanced Research Computing</a> and the <a href="https://research.vt.edu/">Office of the Vice President for Research</a>. Using the Virginia Tech login to OSF provides your name and VT email address to the Center for Open Science. Please see their <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">terms of service</a>.',
            "banner_name": "vt-banner.png",
            "logo_name": "vt-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:vt.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "wustl",
            "name": "Washington University in St. Louis [Test]",
            "description": 'This service is supported by the <a href="https://library.wustl.edu">Washington University in St. Louis Libraries</a>. Please abide by the University policy on <a href="https://informationsecurity.wustl.edu/resources/information-security-solutions/data-classification/">information security</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). | For assistance please contact the <a href="http://gis.wustl.edu/dgs">WU Libraries Data & GIS Services</a>.',
            "banner_name": "wustl-banner.png",
            "logo_name": "wustl-shield.png",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.wustl.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-wustl.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
    ],
}


if __name__ == "__main__":

    init_app(routes=False)
    main(default_args=False)
