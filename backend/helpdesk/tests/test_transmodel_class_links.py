"""Transmodel definitions in answers link to the class page in the published EA HTML export (#151, #82)."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.api.views import _citation_url, _citations_from_prompt_order
from helpdesk.services.ontology_evidence import (
    TRANSMODEL_SOURCE_URL,
    format_definitions_as_chunks,
    transmodel_class_url,
)
from helpdesk.services.policy_guard import evaluate_policy

HTML_BASE_URL = "https://helpdesk.example/transmodel"
# GUID of tm:STOP_PLACE in docs/ontology/standards/transmodel.ttl
STOP_PLACE_PAGE = f"{HTML_BASE_URL}/index.htm?guid=06B01244-7E43-4925-8610-0B0B61508E7D"


def _stop_place_definition() -> dict:
    return {
        "concept": "https://transmodel-cen.eu/6.2/STOP_PLACE",
        "type": "http://www.w3.org/2002/07/owl#Class",
        "definition": "A place comprising one or more locations where vehicles may stop.",
        "prefLabel": "STOP PLACE",
        "altLabels": [],
    }


@override_settings(TRANSMODEL_HTML_BASE_URL=HTML_BASE_URL)
class TransmodelClassUrlTests(SimpleTestCase):
    def test_class_page_is_opened_by_its_guid(self):
        self.assertEqual(transmodel_class_url("STOP_PLACE"), STOP_PLACE_PAGE)

    def test_class_without_guid_has_no_page(self):
        self.assertEqual(transmodel_class_url("NOT_A_TRANSMODEL_CLASS"), "")

    @override_settings(TRANSMODEL_HTML_BASE_URL="")
    def test_no_page_when_no_export_is_configured(self):
        self.assertEqual(transmodel_class_url("STOP_PLACE"), "")

    def test_definition_chunk_links_to_the_class_page_and_keeps_the_file_as_source(self):
        (chunk,) = format_definitions_as_chunks([_stop_place_definition()])

        self.assertEqual(chunk["sourceUrl"], STOP_PLACE_PAGE)
        # Citation selection groups sources by repositoryUrl; all definitions still count as one source.
        self.assertEqual(chunk["repositoryUrl"], TRANSMODEL_SOURCE_URL)


@override_settings(TRANSMODEL_HTML_BASE_URL=HTML_BASE_URL, LLM_MAX_EVIDENCE_CHUNKS=4)
class TransmodelCitationTests(SimpleTestCase):
    def test_citation_links_to_the_class_page(self):
        (chunk,) = format_definitions_as_chunks([_stop_place_definition()])

        (citation,) = _citations_from_prompt_order([chunk], "A stop place is a place [E1].")

        self.assertEqual(citation["repositoryUrl"], STOP_PLACE_PAGE)

    def test_chunk_without_source_url_links_to_the_file(self):
        url = _citation_url(
            {"repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx/blob/v2.0/xsd/a.xsd", "commitSha": "v2.0"}
        )

        self.assertEqual(url, "https://github.com/TransmodelEcosystem/NeTEx/blob/v2.0/xsd/a.xsd")

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_policy_accepts_class_pages_of_the_configured_export_only(self):
        self.assertTrue(evaluate_policy("Grounded answer.", [{"repositoryUrl": STOP_PLACE_PAGE}])["allowed"])

        other_site = "https://elsewhere.example/transmodel/index.htm?guid=06B01244-7E43-4925-8610-0B0B61508E7D"
        self.assertFalse(evaluate_policy("Grounded answer.", [{"repositoryUrl": other_site}])["allowed"])
