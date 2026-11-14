from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from helpdesk import netex_validator_service as service
from helpdesk.services import netex_example_generator as generator

NETEX_CHUNK = {
    "repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx",
    "sourcePath": "xsd/netex_framework/netex_reusableComponents/netex_vehicleType_version.xsd",
    "chunkId": "c1",
    "text": "PassengerCapacity: SeatingCapacity, StandingCapacity",
}
FRAME = (
    '<ResourceFrame version="1" id="hd:RF:1"><vehicleTypes><VehicleType version="1" id="hd:VT:1">'
    "<SeatingCapacity>50</SeatingCapacity><StandingCapacity>20</StandingCapacity></VehicleType></vehicleTypes>"
    "</ResourceFrame>"
)
BUS = "Show me a NeTEx example for a bus with 50 seats and 20 standing places"


def _reply(xml: str) -> str:
    return json.dumps({"xml": xml})


class TriggerTests(SimpleTestCase):
    def test_example_with_values_in_netex_scope(self):
        self.assertTrue(generator.wants_generated_example(BUS, ["NeTEx"]))

    def test_needs_concrete_values(self):
        self.assertFalse(generator.wants_generated_example("Show me a NeTEx example for a bus", ["NeTEx"]))

    def test_needs_an_example_request(self):
        self.assertFalse(generator.wants_generated_example("How many seats can a NeTEx bus with 50 seats have?", ["NeTEx"]))

    def test_needs_netex(self):
        self.assertFalse(generator.wants_generated_example("Show a SIRI example for line 6", ["SIRI"]))

    @override_settings(NETEX_EXAMPLE_GENERATOR_ENABLED=False)
    def test_can_be_switched_off(self):
        self.assertFalse(generator.wants_generated_example(BUS, ["NeTEx"]))

    def test_requested_values_are_numbers_and_quoted_names(self):
        self.assertEqual(
            generator.requested_values('A stop place named "Ljubljana Bus Station" with 2 quays'),
            ["Ljubljana Bus Station", "2"],
        )

    def test_one_character_quoted_values_and_no_quote_across_two(self):
        self.assertEqual(
            generator.requested_values('A line with public code "6" operated by the operator "LPP"'), ["6", "LPP"]
        )
        self.assertEqual(generator.requested_values("Don't show a stop named “Kongresni trg”"), ["Kongresni trg"])

    def test_names_without_quotes_and_number_words(self):
        question = "Show me a NeTEx example for Ljubljana Bus Station with two quays"
        self.assertTrue(generator.wants_generated_example(question, ["NeTEx"]))
        self.assertEqual(generator.requested_values(question), ["Ljubljana Bus Station"])
        self.assertEqual(generator.counted_words(question), ["two"])

    def test_names_keep_joining_words_and_capitals(self):
        self.assertEqual(generator.named_values("NeTEx example for the Gare de Lyon station"), ["Gare de Lyon"])
        self.assertEqual(generator.named_values("Show a NeTEx line operated by LPP in Ljubljana"), ["LPP", "Ljubljana"])

    def test_not_names(self):
        # The first word of a sentence, standard names, identifiers, short abbreviations and concept labels.
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {"netex:StopPlace": {"stop place"}}):
            generator._concept_label_words._cache = None
            self.assertEqual(generator.named_values("Show me a NeTEx example of a VehicleType"), [])
            self.assertEqual(generator.named_values("Show a SIRI SX example"), [])
            self.assertEqual(generator.named_values("A NeTEx example of a Stop Place"), [])
            self.assertEqual(generator.named_values("A NeTEx example of a Stop"), [])
        generator._concept_label_words._cache = None

    def test_value_places_say_which_element_holds_each_value(self):
        fragment = (
            '<ResourceFrame version="1" id="hd:RF"><vehicleTypes><VehicleType version="1" id="hd:VT"><Name>Coach</Name>'
            '<capacities><PassengerCapacity version="1" id="hd:PC"><SeatingCapacity>49</SeatingCapacity>'
            "<WheelchairPlaceCapacity>1</WheelchairPlaceCapacity></PassengerCapacity></capacities></VehicleType>"
            "</vehicleTypes></ResourceFrame>"
        )
        places = generator.value_places(fragment, ["49", "1", "absent"])
        self.assertEqual([(p["value"], p["element"]) for p in places], [("49", "SeatingCapacity"), ("1", "WheelchairPlaceCapacity")])
        self.assertEqual(places[0]["path"], ["ResourceFrame", "vehicleTypes", "VehicleType", "capacities", "PassengerCapacity"])
        self.assertEqual(generator.value_places('<SiteFrame version="1" id="hd:A3"/>', ["hd:A3"])[0]["element"], "SiteFrame/@id")

    def test_value_elements_come_first_and_names_are_left_out(self):
        example = {
            "valid": True,
            "valuePlaces": [{"value": "Coach", "element": "Name", "path": []}, {"value": "49", "element": "SeatingCapacity", "path": []}],
            "elementNotes": [{"name": n, "documentation": "."} for n in ["ResourceFrame", "VehicleType", "SeatingCapacity"]],
        }
        self.assertEqual(generator.value_element_names(example), ["SeatingCapacity"])
        self.assertEqual(generator.example_element_names(example), ["SeatingCapacity", "ResourceFrame", "VehicleType"])

    def test_example_element_names_skip_generic_elements(self):
        example = {
            "valid": True,
            "elementNotes": [{"name": n, "documentation": "..."} for n in ["ResourceFrame", "VehicleType", "Name", "Description", "PassengerCapacity", "SeatingCapacity"]],
        }
        self.assertEqual(generator.example_element_names(example), ["ResourceFrame", "VehicleType", "PassengerCapacity", "SeatingCapacity"])
        self.assertEqual(generator.example_element_names({"valid": False, "errors": []}), [])
        self.assertEqual(generator.example_element_names(None), [])

    def test_values_must_be_whole_element_or_attribute_contents(self):
        self.assertEqual(generator.missing_values("<SeatingCapacity>500</SeatingCapacity>", ["50"]), ["50"])
        self.assertEqual(generator.missing_values("<SeatingCapacity> 50 </SeatingCapacity>", ["50"]), [])
        self.assertEqual(generator.missing_values('<Quay id="50"/>', ["50"]), [])
        self.assertEqual(generator.missing_values("<Name>Ljubljana Bus Station</Name>", ["Ljubljana Bus Station"]), [])
        # Mentioned in a sentence: the value is not modelled.
        self.assertEqual(generator.missing_values("<Description>Bus with 50 seats</Description>", ["50"]), ["50"])
        self.assertEqual(generator.missing_values("<Name>Ljubljana Bus Station (main)</Name>", ["Ljubljana Bus Station"]), ["Ljubljana Bus Station"])
        # Not XML: whole words.
        self.assertEqual(generator.missing_values("<Seats>50", ["50", "20"]), ["20"])


class QuestionWordTests(SimpleTestCase):
    def test_content_words_singular_without_stopwords(self):
        question = "Show a NeTEx example of a coach with 49 seats and 1 wheelchair area"
        self.assertEqual(generator._question_words(question), ["coach", "seat", "wheelchair", "area"])
        self.assertEqual(generator._counted_question_words(question), ["seat", "wheelchair"])

    def test_declarations_block(self):
        block = generator.declarations_block(
            [
                {"name": "SeatingCapacity", "parents": ["PassengerCapacity"], "documentation": "The seating capacity."},
                {"name": "Quay", "parents": [], "documentation": "A place."},
            ]
        )
        self.assertIn("- SeatingCapacity (child of PassengerCapacity): The seating capacity.", block)
        self.assertIn("- Quay: A place.", block)


@override_settings(LLM_ENABLED=True)
class GenerationTests(SimpleTestCase):
    def setUp(self):
        patcher = patch.object(generator, "schema_declarations", return_value=[])
        self.declarations = patcher.start()
        self.addCleanup(patcher.stop)
        values_patcher = patch.object(generator, "value_element_declarations", return_value=[])
        values_patcher.start()
        self.addCleanup(values_patcher.stop)
        asked_patcher = patch.object(generator, "asked_element", return_value="")
        asked_patcher.start()
        self.addCleanup(asked_patcher.stop)

    def test_schema_declarations_go_to_the_model_only_after_a_failed_attempt(self):
        self.declarations.return_value = [
            {"name": "SeatingCapacity", "parents": ["PassengerCapacity"], "documentation": "The seating capacity."}
        ]
        replies = [_reply(FRAME.replace("SeatingCapacity", "NumberOfSeats")), _reply(FRAME)]
        verdicts = [{"valid": False, "errors": ["line 1: Element 'NumberOfSeats': This element is not expected."]}, {"valid": True, "errors": []}]
        with patch.object(generator, "_ask_model", side_effect=replies) as ask, patch.object(
            generator, "validate_fragment", side_effect=verdicts
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        first_prompt = ask.call_args_list[0].args[0][1]["content"]
        self.assertNotIn("SCHEMA DECLARATIONS", first_prompt)
        feedback = ask.call_args_list[1].args[0][-1]["content"]
        self.assertIn("SCHEMA DECLARATIONS", feedback)
        self.assertIn("SeatingCapacity (child of PassengerCapacity)", feedback)
        self.declarations.assert_called_once()
        self.assertEqual(result["schemaDeclarations"], 1)

    def test_no_declarations_fetched_when_the_first_attempt_is_valid(self):
        with patch.object(generator, "_ask_model", return_value=_reply(FRAME)), patch.object(
            generator, "validate_fragment", return_value={"valid": True, "errors": []}
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.declarations.assert_not_called()
        self.assertEqual(result["schemaDeclarations"], 0)

    def test_valid_first_attempt(self):
        elements = [
            {"name": "SeatingCapacity", "parent": "PassengerCapacity", "documentation": "The seating capacity of vehicles of the type."},
            {"name": "SeatingCapacity", "parent": "Other", "documentation": "Another declaration."},
            {"name": "Name", "parent": "VehicleType", "documentation": ""},
        ]
        with patch.object(generator, "_ask_model", return_value=_reply(FRAME)), patch.object(
            generator,
            "validate_fragment",
            return_value={"valid": True, "errors": [], "schemaVersion": "2.0", "commit": "abc", "elements": elements},
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertTrue(result["valid"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["xml"], generator.indented_fragment(FRAME))
        self.assertIn("<dataObjects>", result["document"])
        self.assertEqual((result["schemaVersion"], result["schemaCommit"]), ("2.0", "abc"))
        # One note per element name, the first occurrence; nothing for an element without documentation.
        self.assertEqual(
            result["elementNotes"],
            [{"name": "SeatingCapacity", "documentation": "The seating capacity of vehicles of the type."}],
        )
        self.assertIn("generationMs", result)
        self.assertIn("validationMs", result)

    def test_validator_errors_go_back_to_the_model(self):
        replies = [_reply(FRAME.replace("SeatingCapacity", "NumberOfSeats")), _reply(FRAME)]
        verdicts = [
            {"valid": False, "errors": ["line 1: Element 'NumberOfSeats': This element is not expected."]},
            {"valid": True, "errors": []},
        ]
        with patch.object(generator, "_ask_model", side_effect=replies) as ask, patch.object(
            generator, "validate_fragment", side_effect=verdicts
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertTrue(result["valid"])
        self.assertEqual(result["attempts"], 2)
        feedback = ask.call_args_list[1].args[0][-1]["content"]
        self.assertIn("NumberOfSeats", feedback)

    def test_a_valid_fragment_without_the_values_is_retried(self):
        with patch.object(generator, "_ask_model", return_value=_reply(FRAME.replace(">20<", ">25<"))), patch.object(
            generator, "validate_fragment", return_value={"valid": True, "errors": []}
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertFalse(result["valid"])
        self.assertEqual(result["attempts"], generator.MAX_ATTEMPTS)
        self.assertTrue(result["errors"][0].startswith("the value 20 from the question is missing"), result["errors"])
        self.assertNotIn("xml", result)

    def test_a_failed_model_call_is_retried(self):
        with patch.object(generator, "_ask_model", side_effect=[TimeoutError("The read operation timed out"), _reply(FRAME)]) as ask, patch.object(
            generator, "validate_fragment", return_value={"valid": True, "errors": []}
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertTrue(result["valid"])
        self.assertEqual((result["attempts"], ask.call_count), (2, 2))

    def test_model_failing_every_time_gives_no_example(self):
        with patch.object(generator, "_ask_model", side_effect=TimeoutError("timed out")) as ask:
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertFalse(result["valid"])
        self.assertEqual(ask.call_count, generator.MAX_ATTEMPTS)
        self.assertTrue(result["errors"][0].startswith("generation failed"))

    def test_validator_down_gives_no_example(self):
        with patch.object(generator, "_ask_model", return_value=_reply(FRAME)), patch.object(
            generator, "validate_fragment", side_effect=generator.ValidatorUnavailable("validator unreachable")
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertFalse(result["valid"])
        self.assertNotIn("xml", result)

    def test_no_netex_evidence(self):
        siri = {**NETEX_CHUNK, "repositoryUrl": "https://github.com/TransmodelEcosystem/SIRI"}
        with patch.object(generator, "_ask_model") as ask:
            result = generator.generate_netex_example(BUS, [siri], ["NeTEx"])
        ask.assert_not_called()
        self.assertFalse(result["valid"])

    def test_not_requested_returns_none(self):
        self.assertIsNone(generator.generate_netex_example("What is a VehicleType?", [NETEX_CHUNK], ["NeTEx"]))

    def test_fragment_read_from_a_reply_that_is_not_json(self):
        self.assertEqual(generator._extract_fragment("Here it is:\n" + FRAME + "\nDone."), FRAME)

    def test_json_after_a_sentence_is_read_as_json(self):
        # Verbatim start of the passing-time reply of 2026-11-10 (run 1, attempt 3): the regex fallback took
        # the JSON-escaped XML and the validator said `AttValue: " or ' expected`.
        frame = '<TimetableFrame version="any" id="hd:TF_1"><Name>T</Name></TimetableFrame>'
        reply = (
            "The frame drops the `TimingPointInJourneyPatternRef`, since it pointed to a pattern that is not defined "
            "in this frame. The `ArrivalTime` of 08:30:00 remains as the only content of the timetabled passing time."
            "\n\n" + json.dumps({"xml": frame}) + "\nDone."
        )
        self.assertEqual(generator.parse_reply(reply), (frame, "json"))

    def test_fenced_json_and_braces_before_it(self):
        reply = 'Use {curly} braces? No.\n```json\n' + json.dumps({"xml": FRAME}) + "\n```"
        self.assertEqual(generator.parse_reply(reply), (FRAME, "json"))

    def test_bare_xml_reply_and_escaped_xml_without_json(self):
        self.assertEqual(generator.parse_reply(FRAME), (FRAME, "xml"))
        # A JSON reply cut off before its end does not decode; the XML in it is unescaped.
        broken = '{"xml": "' + FRAME.replace('"', '\\"') + '"'
        self.assertEqual(generator.parse_reply(broken), (FRAME, "xml"))
        self.assertEqual(generator.parse_reply("no frame here"), ("", ""))

    def test_prompt_asks_for_the_json_object_only(self):
        self.assertIn("no text before or after it", generator._PROMPT)


@override_settings(LLM_ENABLED=True)
class AttemptLogTests(SimpleTestCase):
    def setUp(self):
        patcher = patch.object(generator, "schema_declarations", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)
        values_patcher = patch.object(generator, "value_element_declarations", return_value=[])
        values_patcher.start()
        self.addCleanup(values_patcher.stop)
        asked_patcher = patch.object(generator, "asked_element", return_value="")
        asked_patcher.start()
        self.addCleanup(asked_patcher.stop)

    def test_error_classes_of_the_verbatim_messages(self):
        cases = {
            "line 12: Element 'FarePrice': This element is not expected. Expected is one of ( FarePriceRef, FareProductPriceRef ).": "not-expected",
            "line 5: Element 'ArrivalTime': This element is not expected. Expected is one of ( validityConditions, DatedVehicleJourneyRef ).": "not-expected",
            "line 9: Element 'StopPointInJourneyPatternRef': No match found for key-sequence ['hd:spijp_1', 'any'] of keyref 'StopPointInJourneyPattern_KeyRef'.": "keyref",
            "line 7: Element 'pointsInSequence': Missing child element(s). Expected is one of ( PointInJourneyPattern ).": "min-count",
            "Not well-formed XML: AttValue: \" or ' expected, line 1, column 25": "malformed",
            "the reply contained no XML frame": "malformed",
            "the value 5 from the question is missing: it must be the whole content of an element": "value",
            "generation failed: timed out": "model-error",
            "line 1: Element 'X': [facet 'pattern'] The value 'a' is not accepted.": "other",
            "": "",
        }
        for message, expected in cases.items():
            self.assertEqual(generator.error_class(message), expected, message)

    def test_each_attempt_is_logged(self):
        replies = ["Here: " + _reply(FRAME.replace("SeatingCapacity", "NumberOfSeats")), _reply(FRAME)]
        verdicts = [
            {"valid": False, "errors": ["line 1: Element 'NumberOfSeats': This element is not expected."]},
            {"valid": True, "errors": []},
        ]
        with patch.object(generator, "_ask_model", side_effect=replies), patch.object(
            generator, "validate_fragment", side_effect=verdicts
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        log = result["attemptLog"]
        self.assertEqual([(e["attempt"], e["parsed"], e["errorClass"]) for e in log], [(1, "json", "not-expected"), (2, "json", "")])
        self.assertTrue(all("ms" in e and "completionTokens" in e for e in log))

    def test_failed_runs_carry_the_log(self):
        with patch.object(generator, "_ask_model", side_effect=TimeoutError("timed out")):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        self.assertEqual([e["errorClass"] for e in result["attemptLog"]], ["model-error"] * generator.MAX_ATTEMPTS)


class ExampleBenchmarkSummaryTests(SimpleTestCase):
    def test_summary_counts(self):
        from helpdesk.management.commands.run_example_benchmark import summarize

        rows = [
            {"valid": True, "attempts": 1, "seconds": 4.0, "attemptLog": [{"parsed": "json", "errorClass": "", "completionTokens": 100}]},
            {"valid": True, "attempts": 2, "seconds": 9.0, "attemptLog": [
                {"parsed": "xml", "errorClass": "malformed", "completionTokens": 50},
                {"parsed": "json", "errorClass": "", "completionTokens": 70},
            ]},
            {"valid": False, "attempts": 3, "seconds": 20.0, "attemptLog": [{"parsed": "json", "errorClass": "keyref"}] * 3},
        ]
        summary = summarize(rows)
        self.assertEqual((summary["runs"], summary["valid"], summary["firstAttempt"]), (3, 2, 1))
        self.assertEqual((summary["meanAttempts"], summary["meanSeconds"]), (2.0, 11.0))
        self.assertEqual(summary["failuresByClass"], {"keyref": 3, "malformed": 1})
        self.assertEqual((summary["notJson"], summary["completionTokens"]), (1, 220))

    def test_outage_runs_are_counted_apart(self):
        from helpdesk.management.commands.run_example_benchmark import summarize

        outage = {"valid": True, "origin": "standard", "attempts": 3, "seconds": 7.0,
                  "attemptLog": [{"parsed": "", "errorClass": "model-error"}] * 3}
        rows = [
            {"valid": True, "attempts": 1, "seconds": 4.0, "attemptLog": [{"parsed": "json", "errorClass": ""}]},
            outage,
            # One failed call among good ones is the generator's run, not an outage.
            {"valid": True, "attempts": 2, "seconds": 8.0, "attemptLog": [
                {"parsed": "", "errorClass": "model-error"}, {"parsed": "json", "errorClass": ""}]},
        ]
        summary = summarize(rows)
        self.assertEqual((summary["runs"], summary["outages"], summary["valid"], summary["firstAttempt"]), (2, 1, 2, 1))
        self.assertEqual((summary["meanAttempts"], summary["meanSeconds"]), (1.5, 6.0))
        self.assertEqual(summarize([outage])["runs"], 0)


class ReplayRepairsTests(SimpleTestCase):
    """The offline replay of stored failed attempts (plan 2026-11-13, P0)."""

    def test_distinct_structural_fragments_from_every_kind_of_file(self):
        from helpdesk.management.commands import replay_example_repairs as replay

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        log = [{"errorClass": "order", "diagnostics": ["order"], "fragment": "<A/>"},
               {"errorClass": "link", "fragment": "<B/>"}, {"errorClass": "wrong-parent", "fragment": ""}]
        (root / "bench.json").write_text(json.dumps({"runs": [{"attemptLog": log}, {"attemptLog": log[:1]}]}))
        (root / "prod.jsonl").write_text(json.dumps({"ex": {"attemptLog": [{"errorClass": "keyref", "fragment": "<C/>"}]}}) + "\nnot json\n")
        (root / "failed.json").write_text(json.dumps([{"cls": "wrong-parent", "fragment": "<D/>"}, {"cls": "order", "fragment": "<A/>"}]))
        items = replay.corpus([root])
        self.assertEqual(sorted((i["errorClass"], i["fragment"]) for i in items),
                         [("keyref", "<C/>"), ("order", "<A/>"), ("wrong-parent", "<D/>")])
        answers = {"<A/>": {"valid": True, "repaired": "order", "fragment": "<A></A>"},
                   "<C/>": {"valid": False, "diagnostics": [{"kind": "keyref"}]},
                   "<D/>": {"valid": False, "diagnostics": [{"kind": "wrong-parent"}, {"kind": "order"}]}}
        report = replay.replay(items, validate=lambda fragment: answers[fragment])
        self.assertEqual(report["byClass"]["order"]["validNow"], 1)
        self.assertEqual(report["byClass"]["order"]["repaired"], {"order": 1})
        self.assertEqual(report["byClass"]["wrong-parent"]["diagnosticsAfter"], {"wrong-parent": 1, "order": 1})
        self.assertEqual((report["total"]["fragments"], report["total"]["validNow"]), (3, 1))
        self.assertEqual(next(r for r in report["records"] if r["fragment"] == "<A/>")["repairedFragment"], "<A></A>")


TINY_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.netex.org.uk/netex"
  targetNamespace="http://www.netex.org.uk/netex" elementFormDefault="qualified" version="2.0">
  <xsd:element name="PublicationDelivery">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="PublicationTimestamp" type="xsd:dateTime"/>
      <xsd:element name="ParticipantRef" type="xsd:string"/>
      <xsd:element name="dataObjects"><xsd:complexType><xsd:sequence>
        <xsd:element name="ResourceFrame" type="ResourceFrameStructure">
          <xsd:annotation><xsd:documentation>A coherent set of reference values.</xsd:documentation></xsd:annotation>
        </xsd:element>
      </xsd:sequence></xsd:complexType></xsd:element>
    </xsd:sequence><xsd:attribute name="version" type="xsd:string"/></xsd:complexType>
  </xsd:element>
  <xsd:complexType name="ResourceFrameStructure"><xsd:complexContent>
    <xsd:extension base="FrameStructure"><xsd:sequence>
      <xsd:element name="Capacity" type="xsd:string" minOccurs="0">
        <xsd:annotation><xsd:documentation>Capacity of the frame's vehicles.</xsd:documentation></xsd:annotation>
      </xsd:element>
    </xsd:sequence></xsd:extension>
  </xsd:complexContent></xsd:complexType>
  <xsd:complexType name="FrameStructure"><xsd:sequence>
    <xsd:group ref="NameGroup"/>
  </xsd:sequence><xsd:attribute name="id" type="xsd:string"/></xsd:complexType>
  <xsd:group name="NameGroup"><xsd:sequence>
    <xsd:element name="Name" type="xsd:string">
      <xsd:annotation><xsd:documentation>Name of the frame.</xsd:documentation></xsd:annotation>
    </xsd:element>
  </xsd:sequence></xsd:group>
  <xsd:group name="OtherGroup"><xsd:sequence>
    <xsd:element name="Capacity" type="xsd:string">
      <xsd:annotation><xsd:documentation>Capacity of something else.</xsd:documentation></xsd:annotation>
    </xsd:element>
  </xsd:sequence></xsd:group>
</xsd:schema>
"""


class ValidatorServiceTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.checkout = Path(directory.name)
        (self.checkout / "xsd").mkdir()
        (self.checkout / service.SCHEMA_ENTRY).write_text(TINY_XSD)
        git = self.checkout / ".git" / "refs" / "heads"
        git.mkdir(parents=True)
        (self.checkout / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (git / "main").write_text("1234abcd\n")
        self.holder = service.SchemaHolder(self.checkout)
        self.holder.load()

    def test_loads_the_checkout_schema_and_commit(self):
        status = self.holder.status()
        self.assertEqual((status["status"], status["schemaVersion"], status["commit"]), ("ok", "2.0", "1234abcd"))

    def test_valid_fragment(self):
        result = self.holder.validate('<ResourceFrame id="hd:RF:1"><Name>Bus</Name></ResourceFrame>')
        self.assertEqual(result["valid"], True)

    def test_a_valid_fragment_comes_with_each_element_in_the_schema_words(self):
        result = self.holder.validate('<ResourceFrame id="hd:RF:1"><Name>Bus</Name><Capacity>50</Capacity></ResourceFrame>')
        self.assertEqual(
            result["elements"],
            [
                {"name": "ResourceFrame", "parent": "dataObjects", "documentation": "A coherent set of reference values."},
                # Declared in a group reached through the frame's base type.
                {"name": "Name", "parent": "ResourceFrame", "documentation": "Name of the frame."},
                # Declared twice; the declaration reachable from the parent's type wins over OtherGroup's.
                {"name": "Capacity", "parent": "ResourceFrame", "documentation": "Capacity of the frame's vehicles."},
            ],
        )

    def test_search_declarations_by_word_with_their_parents(self):
        found = self.holder.element_docs.search(["capacity"])
        # The matches, then the declarations of their parents (so the model sees what ResourceFrame is).
        self.assertEqual(
            [(d["name"], d["parents"]) for d in found],
            [("Capacity", ["ResourceFrame"]), ("Capacity", []), ("ResourceFrame", ["dataObjects"])],
        )
        self.assertEqual(found[0]["documentation"], "Capacity of the frame's vehicles.")
        self.assertEqual(found[2]["documentation"], "A coherent set of reference values.")
        # A word in the name counts double: "frame" is in ResourceFrame's name and in Name's text.
        self.assertEqual(self.holder.element_docs.search(["frame"])[0]["name"], "ResourceFrame")
        self.assertEqual(self.holder.element_docs.search(["xyz"]), [])

    def test_counted_words_prefer_number_valued_elements(self):
        docs = self.holder.element_docs
        docs.docs["SeatingCapacity"] = [("CapacityGroup", "The seating capacity of vehicles.")]
        docs.docs["SeatEquipment"] = [("EquipmentGroup", "A seat.")]
        docs.element_type["SeatingCapacity"] = "NumberOfPassengers"
        docs.element_type["SeatEquipment"] = "SeatEquipment_VersionStructure"
        self.assertEqual(docs.search(["seat"])[0]["name"], "SeatEquipment")  # both in name and text; shorter text wins
        self.assertEqual(docs.search(["seat"], counted=["seat"])[0]["name"], "SeatingCapacity")

    def test_structure_of_an_element(self):
        result = self.holder.element_docs.structure("ResourceFrame")
        self.assertTrue(result["found"])
        self.assertEqual(result["documentation"], "A coherent set of reference values.")
        self.assertEqual(result["source"], "xsd/NeTEx_publication.xsd")
        self.assertEqual(
            [(g["owner"], g["inherited"], [c["name"] for c in g["children"]]) for g in result["groups"]],
            # Its own declarations (ResourceFrameStructure), then those of its base type FrameStructure (via NameGroup).
            [("ResourceFrame", False, ["Capacity"]), ("Frame", True, ["Name"])],
        )
        self.assertEqual(result["groups"][0]["children"][0]["documentation"], "Capacity of the frame's vehicles.")
        self.assertEqual(result["attributes"], [{"name": "id", "documentation": "", "owner": "Frame"}])

    def test_required_children_at_the_end_of_a_path(self):
        found = service.required_children(self.holder, ["PublicationDelivery", "dataObjects", "ResourceFrame"])
        self.assertEqual(found["required"], [{"label": "Name", "names": ["Name"], "min": 1}])
        self.assertFalse(service.required_children(self.holder, ["ResourceFrame"])["found"])  # not a global element

    def test_structure_of_an_unknown_element(self):
        self.assertEqual(self.holder.element_docs.structure("Nothing")["found"], False)

    def test_element_documentation_fallbacks(self):
        docs = self.holder.element_docs
        # Not reachable from the parent, declarations disagree: no note rather than a wrong one.
        self.assertEqual(docs.documentation("Capacity", "Unknown"), "")
        # Not reachable, but every declaration says the same (first sentence).
        docs.docs["Code"] = [("A", "Code of the thing. Extra."), ("B", "Code of the thing.")]
        self.assertEqual(docs.documentation("Code", "Unknown"), "Code of the thing.")
        # Nearer declaration wins over a farther one.
        docs.docs["Name"].append(("ResourceFrameStructure", "Name of the resource frame."))
        self.assertEqual(docs.documentation("Name", "ResourceFrame"), "Name of the resource frame.")

    def test_errors_name_the_element_and_count_lines_from_the_fragment(self):
        result = self.holder.validate('<ResourceFrame id="hd:RF:1">\n<Seats>50</Seats>\n</ResourceFrame>')
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"][0].startswith("line 2: Element 'Seats'"), result["errors"])

    def test_malformed_xml(self):
        result = self.holder.validate("<ResourceFrame><Name>Bus</ResourceFrame>")
        self.assertFalse(result["valid"])
        self.assertIn("Not well-formed", result["errors"][0])

    def test_entities_are_not_expanded(self):
        fragment = '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><ResourceFrame><Name>&e;</Name></ResourceFrame>'
        result = self.holder.validate(fragment)
        self.assertFalse(result["valid"])
        self.assertNotIn("root:", json.dumps(result))

    def test_reload_when_the_commit_moves(self):
        (self.checkout / ".git" / "refs" / "heads" / "main").write_text("5678ef\n")
        self.holder._checked = 0
        with patch.object(service.threading, "Thread") as thread:
            self.holder.reload_if_moved()
        thread.assert_called_once()


class FormattingTests(SimpleTestCase):
    def test_fragment_is_indented_without_a_namespace(self):
        self.assertEqual(
            generator.indented_fragment('<ResourceFrame id="hd:RF:1"><Name>Bus</Name></ResourceFrame>'),
            '<ResourceFrame id="hd:RF:1">\n  <Name>Bus</Name>\n</ResourceFrame>',
        )

    def test_document_is_the_wrapped_fragment(self):
        document = generator.publication_document('<ResourceFrame id="hd:RF:1"><Name>Bus</Name></ResourceFrame>')
        self.assertTrue(document.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<PublicationDelivery xmlns="http://www.netex.org.uk/netex"'))
        self.assertIn("<dataObjects>\n    <ResourceFrame", document)


class CompositionTests(SimpleTestCase):
    def test_other_question_is_the_part_besides_the_example(self):
        self.assertEqual(
            generator.other_question("How do you describe a stop place in NeTEx? Show me an example with two quays."),
            "How do you describe a stop place in NeTEx?",
        )
        self.assertEqual(generator.other_question("What is a Quay and show me an example of one"), "What is a Quay")
        self.assertEqual(generator.other_question("Show me a NeTEx example for a bus with 50 seats"), "")

    def test_counted_shapes_and_nouns(self):
        self.assertEqual(generator.counted_shapes("a stop place with two quays and 3 entrances"), [(2, "two", "quays"), (3, "3", "entrances")])
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {}):
            self.assertEqual(generator.element_for_noun("quays")[0], "Quay")
            self.assertEqual(generator.element_for_noun("facilities")[0], "Facility")

    def test_count_places_and_counts_satisfy_numbers(self):
        fragment = (
            '<SiteFrame version="1" id="hd:SF"><stopPlaces><StopPlace version="1" id="hd:SP"><quays>'
            '<Quay version="1" id="hd:Q1"/><Quay version="1" id="hd:Q2"/></quays></StopPlace></stopPlaces></SiteFrame>'
        )
        with patch("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {}):
            places = generator.count_places(fragment, "a stop place with 2 quays")
            self.assertEqual([(p["value"], p["element"], p["count"]) for p in places], [("2", "Quay", 2)])
            self.assertEqual(places[0]["path"], ["SiteFrame", "stopPlaces", "StopPlace", "quays"])
            # "2" is not element content but is met as a count, so the fragment is not sent back.
            self.assertEqual(generator._unmet_values(fragment, ["2"], "a stop place with 2 quays"), [])
            self.assertEqual(generator._unmet_values(fragment, ["3"], "a stop place with 3 quays"), ["3"])

    def test_standard_example_only_for_counts_without_values(self):
        # A name the standard's examples will not have: generate, without looking.
        with patch("helpdesk.models.SourceChunk.objects") as objects:
            self.assertIsNone(generator.standard_example("Show a NeTEx example of Ljubljana Bus Station with two quays"))
            self.assertIsNone(generator.standard_example("Show a NeTEx example of a bus"))
        objects.filter.assert_not_called()

    def test_tag_condition_matches_exact_element_names(self):
        condition = str(generator.has_tag("Seat"))
        self.assertIn("'<Seat>'", condition)
        self.assertIn("'<Seat '", condition)
        self.assertNotIn("'<Seat'", condition)

    def test_non_english_question_triggers_on_its_english_rendering(self):
        question = "Pokaži mi NeTEx primer za avtobus s 50 sedeži in 20 stojišči"
        self.assertFalse(generator.wants_generated_example(question, ["NeTEx"]))
        with patch.object(generator, "_from_standard", return_value=None), patch.object(
            generator, "_ask_model", return_value=_reply(FRAME)
        ), patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}), override_settings(LLM_ENABLED=True):
            result = generator.generate_netex_example(
                question, [NETEX_CHUNK], ["NeTEx"], english_question="Show me a NeTEx example for a bus with 50 seats and 20 standing places"
            )
        self.assertTrue(result["valid"])
        self.assertEqual(result["origin"], "generated")


class SnippetTests(SimpleTestCase):
    def test_snippets_become_whole_elements(self):
        from helpdesk.services.llm_generator import OMISSION_MARKER, _complete_xml_snippets, complete_xml_elements

        cut = '<Quay version="any" id="q1">\n  <Centroid>\n    <Location/>\n  </Centroid>\n  <Lighting>wellLit</Lighting>'
        whole = complete_xml_elements(cut)
        self.assertTrue(whole.endswith(f"{OMISSION_MARKER}\n</Quay>"), whole)
        self.assertEqual(complete_xml_elements("<IsFoldup>true</IsFoldup>\n</SeatEquipment>\n<A>1</A>"), "<A>1</A>")
        self.assertEqual(complete_xml_elements("</a></b>"), "")
        self.assertEqual(complete_xml_elements("<siri:Foo>1</siri:Foo>"), "<siri:Foo>1</siri:Foo>")
        self.assertEqual(_complete_xml_snippets("Text.\n\n```xml\n</b>\n```\n\nMore."), "Text.\n\nMore.")


class PartTests(SimpleTestCase):
    def test_parts_and_subject(self):
        question = "Show me a NeTEx example for a stop place with an elevator."
        self.assertEqual(generator.wanted_parts(question), ["elevator"])
        self.assertEqual(generator.example_subject(question), "stop place")
        self.assertEqual(generator.wanted_parts("an example of a vehicle type with a deck plan"), ["deck plan"])
        self.assertEqual(generator.wanted_parts("a stop place with two quays"), [])
        self.assertTrue(generator.wants_generated_example(question, ["NeTEx"]))

    def test_pruned_keeps_simple_children_the_path_and_the_target(self):
        from lxml import etree

        obj = etree.fromstring(
            "<StopPlace id='s'><Name>W</Name><levels><Level/></levels><pathLinks><SitePathLink id='p'><Name>L</Name>"
            "<placeEquipments><LiftEquipment id='l'><Width>1.5</Width></LiftEquipment><Ramp/></placeEquipments>"
            "</SitePathLink><SitePathLink id='q'/></pathLinks></StopPlace>"
        )
        lift = obj.find(".//LiftEquipment")
        pruned = etree.tostring(generator._pruned(obj, {lift}, lambda t: t), encoding="unicode")
        self.assertIn("<Name>W</Name>", pruned)
        self.assertIn("<LiftEquipment id=\"l\"><Width>1.5</Width></LiftEquipment>", pruned)
        self.assertNotIn("<levels>", pruned)
        self.assertNotIn("id=\"q\"", pruned)
        self.assertIn("<!-- … -->", pruned)

    def test_part_places(self):
        fragment = (
            '<SiteFrame version="1" id="f"><stopPlaces><StopPlace version="1" id="s"><placeEquipments>'
            '<LiftEquipment version="1" id="l"/></placeEquipments></StopPlace></stopPlaces></SiteFrame>'
        )
        with patch.object(generator, "resolve_element", return_value="LiftEquipment"):
            places = generator.part_places(fragment, "a stop place with an elevator")
        self.assertEqual([(p["value"], p["element"]) for p in places], [("an elevator", "LiftEquipment")])
        self.assertEqual(places[0]["path"], ["SiteFrame", "stopPlaces", "StopPlace", "placeEquipments"])


LIFT = "How do I describe a lift in a station in NeTEx? Show me an example in XML."


class PlainExampleRequestTests(SimpleTestCase):
    """An example request without values, counts or parts (prod req-mw8cczxw, 2026-11-08): an excerpt of the
    class the question is about, from the standard's own example files."""

    def test_uses_the_concept_element(self):
        found = {"valid": True, "origin": "standard", "validated": True, "sourcePath": "examples/a.xml"}
        with patch.object(generator, "concept_elements", return_value=["LiftEquipment"]) as elements, patch.object(
            generator, "_from_standard", return_value=found
        ) as standard:
            self.assertIs(generator.generate_netex_example(LIFT, [], ["NeTEx"]), found)
        elements.assert_called_once()
        self.assertEqual(standard.call_args.args[2], "LiftEquipment")

    def test_no_concept_no_example(self):
        with patch.object(generator, "concept_elements", return_value=[]), patch.object(generator, "_from_standard") as standard:
            self.assertIsNone(generator.generate_netex_example(LIFT, [], ["NeTEx"]))
        standard.assert_not_called()

    def test_concept_matching_failure_is_no_example(self):
        with patch.object(generator, "concept_elements", side_effect=RuntimeError("no index")):
            self.assertIsNone(generator.generate_netex_example(LIFT, [], ["NeTEx"]))

    def test_not_an_example_request(self):
        with patch.object(generator, "concept_elements") as elements:
            self.assertIsNone(generator.generate_netex_example("What is a StopPlace in NeTEx?", [], ["NeTEx"]))
        elements.assert_not_called()

    def test_a_valid_excerpt_is_preferred(self):
        invalid = {"validated": False, "sourcePath": "examples/old.xml"}
        valid = {"validated": True, "sourcePath": "examples/new.xml"}
        with patch.object(generator, "_from_standard", side_effect=[invalid, valid]) as standard:
            self.assertIs(generator._plain_standard_example(LIFT, ["NeTEx"], ["LiftEquipment"]), valid)
        # The second try leaves out the file of the first.
        self.assertEqual(standard.call_args_list[1].args[3], frozenset({"examples/old.xml"}))

    def test_without_a_valid_excerpt_the_first_is_shown(self):
        invalid = {"validated": False, "sourcePath": "examples/old.xml"}
        def lookup(question, scope, element, exclude, max_between):
            return invalid if not exclude and element == "LiftEquipment" else None

        with patch.object(generator, "_from_standard", side_effect=lookup):
            self.assertIs(generator._plain_standard_example(LIFT, ["NeTEx"], ["LiftEquipment", "LiftCallEquipment"]), invalid)


from django.test import TestCase  # noqa: E402


class PlainStandardExcerptTests(TestCase):
    NESTED = (
        '<PublicationDelivery xmlns="http://www.netex.org.uk/netex"><dataObjects><SiteFrame version="1" id="x:SF">'
        '<stopPlaces><StopPlace version="1" id="x:SP" dataSourceRef="x:DS"><pathLinks><SitePathLink version="1" id="x:PL">'
        '<placeEquipments><LiftEquipment version="1" id="x:L1"><Name>Deep lift</Name></LiftEquipment></placeEquipments>'
        "</SitePathLink></pathLinks></StopPlace></stopPlaces></SiteFrame></dataObjects></PublicationDelivery>"
    )
    SHALLOW = (
        '<PublicationDelivery xmlns="http://www.netex.org.uk/netex"><dataObjects><SiteFrame version="1" id="y:SF">'
        '<stopPlaces><StopPlace version="1" id="y:SP" dataSourceRef="y:DS"><placeEquipments>'
        '<LiftEquipment version="1" id="y:L1"><Name>Station lift</Name></LiftEquipment></placeEquipments>'
        "</StopPlace></stopPlaces></SiteFrame></dataObjects></PublicationDelivery>"
    )

    def setUp(self):
        from helpdesk.models import SourceChunk

        self.root = tempfile.TemporaryDirectory()
        repo = Path(self.root.name) / "NeTEx" / "examples"
        repo.mkdir(parents=True)
        for name, text in (("a_deep.xml", self.NESTED), ("b_shallow.xml", self.SHALLOW)):
            (repo / name).write_text(text)
            SourceChunk.objects.create(
                repository_url="https://github.com/TransmodelEcosystem/NeTEx", commit_sha="abc", source_path=f"examples/{name}",
                chunk_id=name, text=text, embedding_vector=[0.0] * 1535 + [1.0],
            )

    def tearDown(self):
        self.root.cleanup()

    def test_depth_limit_exclusion_and_shell_references_dropped(self):
        with override_settings(SOURCE_CHECKOUT_DIR=self.root.name):
            shallow = generator.standard_example(LIFT, ["NeTEx"], "LiftEquipment", max_between=2)
            none_direct = generator.standard_example(LIFT, ["NeTEx"], "LiftEquipment", max_between=0)
            deep = generator.standard_example(LIFT, ["NeTEx"], "LiftEquipment", exclude=frozenset({"examples/b_shallow.xml"}))
            deep_limited = generator.standard_example(
                LIFT, ["NeTEx"], "LiftEquipment", exclude=frozenset({"examples/b_shallow.xml"}), max_between=2
            )
        self.assertEqual(shallow["sourcePath"], "examples/b_shallow.xml")
        self.assertIn("<StopPlace", shallow["fragment"])
        self.assertIn("Station lift", shallow["fragment"])
        # The stop place is a shell around the lift: its reference to a data source outside the excerpt goes.
        self.assertNotIn("dataSourceRef", shallow["fragment"])
        self.assertIsNone(none_direct)
        self.assertEqual(deep["sourcePath"], "examples/a_deep.xml")
        self.assertIsNone(deep_limited)


PRICES_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.netex.org.uk/netex"
  targetNamespace="http://www.netex.org.uk/netex" elementFormDefault="qualified" version="2.0">
  <xsd:element name="PublicationDelivery">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="PublicationTimestamp" type="xsd:dateTime"/>
      <xsd:element name="ParticipantRef" type="xsd:string"/>
      <xsd:element name="dataObjects"><xsd:complexType><xsd:sequence>
        <xsd:element ref="FareFrame" maxOccurs="unbounded"/>
      </xsd:sequence></xsd:complexType></xsd:element>
    </xsd:sequence><xsd:attribute name="version" type="xsd:string"/></xsd:complexType>
  </xsd:element>
  <xsd:element name="FareFrame">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="prices" type="prices_RelStructure" minOccurs="0"/>
      <xsd:element name="pointsInSequence" type="points_RelStructure" minOccurs="0"/>
      <xsd:element name="passingTimes" type="passingTimes_RelStructure" minOccurs="0"/>
    </xsd:sequence><xsd:attribute name="id" type="xsd:string"/><xsd:attribute name="version" type="xsd:string"/></xsd:complexType>
  </xsd:element>
  <xsd:complexType name="prices_RelStructure"><xsd:sequence>
    <xsd:element ref="FarePrice_Dummy" maxOccurs="unbounded"/>
  </xsd:sequence></xsd:complexType>
  <xsd:element name="FarePrice_Dummy" type="PriceStructure" abstract="true"/>
  <xsd:element name="FarePrice" type="PriceStructure" abstract="true" substitutionGroup="FarePrice_Dummy"/>
  <xsd:element name="FareProductPrice" type="PriceStructure" substitutionGroup="FarePrice_Dummy"/>
  <xsd:element name="UsageParameterPrice" type="PriceStructure" substitutionGroup="FarePrice_Dummy"/>
  <xsd:complexType name="PriceStructure"><xsd:sequence>
    <xsd:element name="Amount" type="xsd:decimal" minOccurs="0"/>
    <xsd:element name="Currency" type="xsd:string" minOccurs="0"/>
  </xsd:sequence><xsd:attribute name="id" type="xsd:string"/></xsd:complexType>
  <xsd:complexType name="points_RelStructure"><xsd:choice minOccurs="2" maxOccurs="unbounded">
    <xsd:element name="StopPoint" type="xsd:string"/>
    <xsd:element name="TimingPoint" type="xsd:string"/>
  </xsd:choice></xsd:complexType>
  <xsd:complexType name="passingTimes_RelStructure"><xsd:sequence>
    <xsd:element name="PassingTime" type="PassingTimeStructure" maxOccurs="unbounded"/>
  </xsd:sequence></xsd:complexType>
  <xsd:complexType name="BaseStructure"><xsd:sequence>
    <xsd:element name="Name" type="xsd:string" minOccurs="0"/>
  </xsd:sequence></xsd:complexType>
  <xsd:complexType name="PassingTimeStructure"><xsd:complexContent><xsd:extension base="BaseStructure"><xsd:sequence>
    <xsd:element ref="PointRef"/>
    <xsd:element name="ArrivalTime" type="xsd:time" minOccurs="0"/>
  </xsd:sequence></xsd:extension></xsd:complexContent></xsd:complexType>
  <xsd:element name="PointRef" type="xsd:string" abstract="true"/>
  <xsd:element name="StopPointRef" type="xsd:string" substitutionGroup="PointRef"/>
</xsd:schema>
"""


class ValidatorDiagnosticsTests(SimpleTestCase):
    """The validator's diagnostics on the failure kinds of 2026-11-10 (plan §2), on a small schema with the
    same shapes: an abstract price, a required reference before ArrivalTime, a choice of at least two."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        checkout = Path(directory.name)
        (checkout / "xsd").mkdir()
        (checkout / service.SCHEMA_ENTRY).write_text(PRICES_XSD)
        (checkout / "examples").mkdir()
        # UsageParameterPrice is used more often than FareProductPrice in the examples: named first.
        (checkout / "examples" / "a.xml").write_text("<UsageParameterPrice/><UsageParameterPrice/><FareProductPrice/>")
        self.holder = service.SchemaHolder(checkout)
        self.holder.load()

    def kinds(self, fragment: str) -> dict:
        result = self.holder.validate(fragment)
        self.assertFalse(result["valid"])
        return {d["kind"]: d for d in result["diagnostics"]}

    def test_abstract_element_names_its_concrete_replacements(self):
        found = self.kinds('<FareFrame id="f"><prices><FarePrice id="p"><Amount>5</Amount></FarePrice></prices></FareFrame>')
        detail = found["abstract"]["detail"]
        self.assertIn("`FarePrice` is abstract", detail)
        self.assertLess(detail.index("UsageParameterPrice"), detail.index("FareProductPrice"))
        self.assertEqual((found["abstract"]["element"], found["abstract"]["parent"]), ("FarePrice", "prices"))

    def test_required_sibling_missing_before_the_written_one(self):
        found = self.kinds('<FareFrame id="f"><passingTimes><PassingTime><ArrivalTime>08:30:00</ArrivalTime></PassingTime></passingTimes></FareFrame>')
        detail = found["missing-required"]["detail"]
        self.assertIn("needs PointRef (one of: StopPointRef) before `ArrivalTime`", detail)
        # The base type's content comes first (extension), the required one is marked.
        self.assertIn("Name?, PointRef (one of: StopPointRef) (required), ArrivalTime?", detail)

    def test_choice_with_a_minimum_count(self):
        found = self.kinds('<FareFrame id="f"><pointsInSequence><StopPoint>a</StopPoint></pointsInSequence></FareFrame>')
        self.assertIn("needs at least 2 of one of (StopPoint, TimingPoint); the fragment has 1", found["min-count"]["detail"])

    def test_order_wrong_parent_and_undeclared(self):
        # The order together with another problem (a missing required reference): sorted all the same (plan
        # 2026-11-13, A1), and the sorted frame's problem explained.
        result = self.holder.validate('<FareFrame id="f"><passingTimes><PassingTime><ArrivalTime>08:30:00</ArrivalTime></PassingTime></passingTimes><prices><FareProductPrice/></prices></FareFrame>')
        self.assertEqual((result["valid"], result["repaired"]), (False, ["order"]))
        self.assertTrue(result["fragment"].startswith('<FareFrame id="f"><prices>'), result["fragment"])
        self.assertEqual([d["kind"] for d in result["diagnostics"]], ["missing-required"])
        self.assertIn("This element is not expected", result["repairedErrors"][0])
        # A child with no place in its parent: that parent is not sorted, the others are.
        result = self.holder.validate(
            '<FareFrame id="f"><passingTimes><PassingTime><ArrivalTime>08:30:00</ArrivalTime><StopPointRef>s</StopPointRef>'
            '<Amount>5</Amount></PassingTime></passingTimes><prices><FareProductPrice><Currency>EUR</Currency><Amount>5</Amount>'
            '</FareProductPrice></prices></FareFrame>'
        )
        self.assertEqual(result["repaired"], ["order"])
        self.assertIn("<prices><FareProductPrice><Amount>5</Amount><Currency>EUR</Currency>", result["fragment"])
        self.assertIn("<ArrivalTime>08:30:00</ArrivalTime><StopPointRef>s</StopPointRef><Amount>", result["fragment"])
        found = self.kinds('<FareFrame id="f"><prices><FareProductPrice><Amount>5</Amount></FareProductPrice><Amount>5</Amount></prices></FareFrame>')
        self.assertIn("`Amount` is not a child of `prices`; it belongs under one of:", found["wrong-parent"]["detail"])
        self.assertIn("FareProductPrice", found["wrong-parent"]["detail"])
        found = self.kinds('<FareFrame id="f"><prices><PriceList/></prices></FareFrame>')
        self.assertIn("`PriceList` is not an element of the NeTEx schema", found["undeclared"]["detail"])

    def test_order_alone_is_repaired(self):
        # Plan 2026-11-12 revision 3, S2: the children sorted into schema order, at every level, text kept.
        result = self.holder.validate(
            '<FareFrame id="f">\n  <passingTimes><PassingTime><StopPointRef>s</StopPointRef></PassingTime></passingTimes>\n'
            '  <prices><FareProductPrice><Currency>EUR</Currency><Amount>5</Amount></FareProductPrice></prices>\n</FareFrame>'
        )
        self.assertEqual((result["valid"], result["errors"], result["repaired"]), (True, [], ["order"]))
        self.assertEqual(
            result["fragment"],
            '<FareFrame id="f">\n  <prices><FareProductPrice><Amount>5</Amount><Currency>EUR</Currency></FareProductPrice></prices>\n'
            '  <passingTimes><PassingTime><StopPointRef>s</StopPointRef></PassingTime></passingTimes>\n</FareFrame>',
        )
        self.assertTrue(result["repairedErrors"])
        self.assertTrue(self.holder.validate(result["fragment"])["valid"])

    def test_a_repaired_fragment_keeps_every_frame(self):
        # Two sibling frames without a CompositeFrame: the repaired fragment had only the first.
        result = self.holder.validate(
            '<FareFrame id="f"><prices><FareProductPrice><Currency>EUR</Currency><Amount>5</Amount></FareProductPrice></prices></FareFrame>\n'
            '<FareFrame id="g"><prices><UsageParameterPrice/></prices></FareFrame>'
        )
        self.assertEqual((result["valid"], result["repaired"]), (True, ["order"]))
        self.assertEqual(result["fragment"], (
            '<FareFrame id="f"><prices><FareProductPrice><Amount>5</Amount><Currency>EUR</Currency></FareProductPrice></prices></FareFrame>\n'
            '<FareFrame id="g"><prices><UsageParameterPrice/></prices></FareFrame>'
        ))

    def test_no_repair_when_a_child_has_no_place(self):
        from lxml import etree

        document = etree.fromstring(service.wrap_fragment(
            '<FareFrame id="f"><passingTimes><PassingTime><StopPointRef>s</StopPointRef></PassingTime></passingTimes>'
            "<prices><FareProductPrice/></prices><Amount>5</Amount></FareFrame>"
        ).encode())
        before = etree.tostring(document)
        self.assertFalse(service.repair_order(self.holder.content, document))
        self.assertEqual(etree.tostring(document), before)
        models = self.holder.content
        self.assertIsNone(models.ordered_children(models.type_of(document.find(".//{*}FareFrame")), ["passingTimes", "Amount"]))
        self.assertEqual(models.ordered_children(models.type_of(document.find(".//{*}FareFrame")), ["passingTimes", "prices"]), [1, 0])

    def test_keyref_suggests_a_versionless_reference(self):
        from lxml import etree

        document = etree.fromstring(service.wrap_fragment(
            '<FareFrame id="f"><passingTimes><PassingTime><StopPointRef ref="hd:sp_1" version="any">s</StopPointRef>'
            "</PassingTime></passingTimes></FareFrame>"
        ).encode())
        line = next(n.sourceline for n in document.iter() if isinstance(n.tag, str) and n.tag.endswith("StopPointRef"))
        message = "Element 'StopPointRef': No match found for key-sequence ['hd:sp_1', 'any'] of keyref 'StopPoint_KeyRef'."
        found = service.diagnostics(self.holder.content, document, [(line, message)], 0)
        self.assertEqual(found[0]["kind"], "keyref")
        self.assertIn("Either define a `StopPoint` with that id and version", found[0]["detail"])
        self.assertIn('leave out the version attribute: <StopPointRef ref="hd:sp_1"/>', found[0]["detail"])

    def test_valid_fragment_has_no_diagnostics(self):
        result = self.holder.validate('<FareFrame id="f"><prices><FareProductPrice><Amount>5</Amount></FareProductPrice></prices></FareFrame>')
        self.assertTrue(result["valid"], result["errors"])
        self.assertNotIn("diagnostics", result)

    def test_content_model_audit_on_a_document(self):
        from helpdesk.netex_content_model import audit

        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        good = directory / "good.xml"
        good.write_text(service.wrap_fragment('<FareFrame id="f"><prices><FareProductPrice><Amount>5</Amount><Currency>EUR</Currency></FareProductPrice></prices></FareFrame>'))
        bad = directory / "bad.xml"
        bad.write_text(service.wrap_fragment('<FareFrame id="f"><prices><FareProductPrice><Currency>EUR</Currency><Amount>5</Amount></FareProductPrice></prices></FareFrame>'))
        checked, fitting, kinds = audit(self.holder.content, [good])
        self.assertEqual(checked, fitting)
        checked, fitting, kinds = audit(self.holder.content, [bad])
        self.assertEqual((checked - fitting, dict(kinds)), (1, {"order": 1}))


class StandardExampleOrderTests(SimpleTestCase):
    """The content models against the standard's own example files (plan P1: the children's order of every
    object must fit the computed slots). Needs the NeTEx checkout; 2026-11-10 at 98365bd: 294,332 of
    294,341 elements in 292 files fit (the nine others are SIRI request elements)."""

    def test_example_files_fit_the_content_models(self):
        import os

        from helpdesk.netex_content_model import ContentModels, audit

        checkout = Path(os.environ.get("NETEX_VALIDATOR_CHECKOUT", "/app/repos/NeTEx"))
        files = sorted((checkout / "examples").rglob("*.xml"))[:40] if (checkout / "examples").is_dir() else []
        if not files or not (checkout / "xsd").is_dir():
            self.skipTest("no NeTEx checkout")
        models = ContentModels()
        models.load_directory(checkout / "xsd")
        checked, fitting, kinds = audit(models, files)
        self.assertGreater(checked, 1000)
        self.assertGreaterEqual(fitting / checked, 0.99, kinds)


@override_settings(LLM_ENABLED=True)
class FeedbackTests(SimpleTestCase):
    def test_diagnostics_replace_the_errors_they_explain(self):
        checked = {"diagnostics": [{"line": 5, "element": "FarePrice", "kind": "abstract", "detail": "`FarePrice` is abstract; use FareProductPrice."}]}
        errors = [
            "line 5: Element 'FarePrice': This element is not expected. Expected is one of ( FarePriceRef ).",
            "line 9: Element 'X': [facet 'pattern'] The value 'a' is not accepted.",
        ]
        self.assertEqual(
            generator.feedback_lines(checked, errors),
            ["line 5: `FarePrice` is abstract; use FareProductPrice.", errors[1]],
        )
        self.assertEqual(generator.feedback_lines({}, errors), errors)

    def test_retry_message_carries_the_diagnostics_and_the_log_their_kind(self):
        verdicts = [
            {"valid": False, "errors": ["line 1: Element 'SeatingCapacity': This element is not expected."],
             "diagnostics": [{"line": 1, "element": "SeatingCapacity", "parent": "VehicleType", "kind": "wrong-parent",
                              "detail": "`SeatingCapacity` is not a child of `VehicleType`; it belongs under one of: PassengerCapacity."}]},
            {"valid": True, "errors": []},
        ]
        with patch.object(generator, "schema_declarations", return_value=[]), patch.object(
            generator, "value_element_declarations", return_value=[]
        ), patch.object(generator, "asked_element", return_value=""), patch.object(
            generator, "_ask_model", side_effect=[_reply(FRAME), _reply(FRAME)]
        ) as ask, patch.object(
            generator, "validate_fragment", side_effect=verdicts
        ):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        feedback = ask.call_args_list[1].args[0][-1]["content"]
        self.assertIn("it belongs under one of: PassengerCapacity", feedback)
        self.assertNotIn("This element is not expected", feedback)
        self.assertEqual(result["attemptLog"][0]["errorClass"], "wrong-parent")

    def test_declarations_also_by_the_elements_holding_the_values(self):
        fragment = '<FareFrame version="1" id="hd:F"><priceGroups><PriceGroup version="1" id="hd:G"><Amount>5</Amount><Currency>EUR</Currency></PriceGroup></priceGroups></FareFrame>'
        payload = json.dumps({"declarations": [
            {"name": "Amount", "parents": ["FareProductPrice"], "documentation": "Amount."},
            {"name": "AmountOfPriceUnitProduct", "parents": [], "documentation": "Other."},
            {"name": "Currency", "parents": ["FareProductPrice"], "documentation": "Currency."},
        ]}).encode()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return payload

        with patch("urllib.request.urlopen", return_value=Response()) as urlopen, self.settings(NETEX_VALIDATOR_URL="http://v"):
            found = generator.value_element_declarations(fragment, ["5", "EUR"])
        self.assertIn("q=Amount+Currency", urlopen.call_args.args[0])
        self.assertEqual([d["name"] for d in found], ["Amount", "Currency"])

    def test_prompt_asks_for_versionless_references_to_outside_objects(self):
        self.assertIn("NO version attribute", generator._PROMPT)
        self.assertNotIn("define that object too", generator._PROMPT)


class TemporalValueTests(SimpleTestCase):
    def test_times_and_dates_are_one_value_each(self):
        self.assertEqual(generator.requested_values("NeTEx example of a timetabled passing time arriving at 08:30"), ["08:30"])
        self.assertEqual(generator.requested_values("a service journey departing at 7:15 with 3 stops"), ["07:15", "3"])
        self.assertEqual(generator.requested_values("Show a NeTEx example of a dated service journey on 2026-12-01"), ["2026-12-01"])

    def test_a_time_or_date_is_held_by_its_xsd_forms(self):
        fragment = (
            '<TimetableFrame version="1" id="hd:TF"><vehicleJourneys><ServiceJourney version="1" id="hd:SJ">'
            "<passingTimes><TimetabledPassingTime version=\"1\" id=\"hd:T\"><ArrivalTime>08:30:00</ArrivalTime>"
            "</TimetabledPassingTime></passingTimes></ServiceJourney></vehicleJourneys></TimetableFrame>"
        )
        self.assertEqual(generator.missing_values(fragment, ["08:30"]), [])
        self.assertEqual(generator.value_places(fragment, ["08:30"])[0]["element"], "ArrivalTime")
        self.assertEqual(generator.missing_values(fragment, ["08:45"]), ["08:45"])
        self.assertTrue(generator.holds_value("2026-12-01T00:00:00", "2026-12-01"))
        self.assertTrue(generator.holds_value("2026-12-01", "2026-12-01"))
        self.assertTrue(generator.holds_value("2026-12-01T07:15:00Z", "07:15"))
        self.assertFalse(generator.holds_value("2026-12-011", "2026-12-01"))
        self.assertFalse(generator.holds_value("08:30:15", "08:30"))
FARE_PRODUCT = (
    '<FareFrame version="1" id="hd:FF_1"><fareProducts><PreassignedFareProduct version="1" id="hd:PFP_1">'
    '<Name>Adult single</Name><prices><FareProductPrice version="1" id="hd:FPP_1"><Amount>5</Amount>'
    "<Currency>EUR</Currency></FareProductPrice></prices></PreassignedFareProduct></fareProducts></FareFrame>"
)
PRICE_GROUP = (
    '<FareFrame version="1" id="hd:FF_1"><fareProducts><PreassignedFareProduct version="1" id="hd:PFP_1">'
    "<Name>Adult single</Name></PreassignedFareProduct></fareProducts><priceGroups><PriceGroup version=\"1\" "
    'id="hd:PG_1"><members><FareProductPrice version="1" id="hd:FPP_1"><Amount>5</Amount><Currency>EUR</Currency>'
    "</FareProductPrice></members></PriceGroup></priceGroups></FareFrame>"
)


class AskedObjectTests(SimpleTestCase):
    def test_subjects_of_the_benchmark_shapes(self):
        cases = {
            "Create a NeTEx XML example for a fare product for adult for 5 EUR.": "fare product",
            "NeTEx example of a timetabled passing time arriving at 08:30": "timetabled passing time",
            'NeTEx example of a route named "Route 1 outbound"': "route",
            "Show a NeTEx example of a tram vehicle type with a length of 32 metres": "tram vehicle type",
            "Show a NeTEx example of a dated service journey on 2026-12-01": "dated service journey",
            'Show a NeTEx example of a line with public code "6" operated by the operator "LPP"': "line",
            "Give me a NeTEx example of a service journey departing at 07:15": "service journey",
            "Show me a NeTEx example for Ljubljana Bus Station with two quays": "",
            "Show me a NeTEx example of a stop place.": "stop place",
            # prod req-mwdzf8px-3qfhdl, 2026-11-12: no subject before "from"
            "Give me a NeTEx example of a bus line from Maribor to Ptuj that runs only on school days and uses "
            "low-floor vehicles.": "bus line",
            "Show me a NeTEx example for a line between Maribor and Ljubljana.": "line",
            "Show a NeTEx example of a ferry line via Koper": "ferry line",
            "Show a NeTEx example of a service journey which runs on Sundays": "service journey",
            # "to" does not end a subject: "point to point" stays whole or unmatched, never "point"
            "Show a NeTEx example of a point to point fare": "",
        }
        for question, subject in cases.items():
            self.assertEqual(generator.asked_subject(question), subject, question)

    def test_resolution_takes_objects_used_in_the_examples_and_concrete_members(self):
        generator._ASKED_CACHE.clear()
        known = {
            "FareProduct": [{"name": "PreassignedFareProduct", "object": True}, {"name": "SaleDiscountRight", "object": True}],
            "VehicleType": [{"name": "VehicleType", "object": True}],
            "Coach": None,
            "Fare": None,
            "Product": None,
            "Name": [{"name": "Name", "object": False}],
        }
        with patch.object(generator, "concrete_elements", side_effect=lambda name: known.get(name)), patch.object(
            generator, "_in_examples", side_effect=lambda name: name != "SaleDiscountRight"
        ):
            self.assertEqual(generator.asked_element("Create a NeTEx XML example for a fare product for adult for 5 EUR."), "PreassignedFareProduct")
            self.assertEqual(generator.asked_element("Show a NeTEx example of a tram vehicle type with a length of 32 metres"), "VehicleType")
            self.assertEqual(generator.asked_element("Show a NeTEx example of a coach with 49 seats and 1 wheelchair area"), "")
            self.assertEqual(generator.asked_element("Show a NeTEx example of a name with 5 letters"), "")

    def test_asked_object_check(self):
        self.assertEqual(generator.asked_object_problem(FARE_PRODUCT, "PreassignedFareProduct", ["5", "EUR"]), "")
        problem = generator.asked_object_problem(PRICE_GROUP, "PreassignedFareProduct", ["5", "EUR"])
        self.assertTrue(problem.startswith("the question asks for a PreassignedFareProduct: the values 5, EUR are neither in it"), problem)
        # A price that refers to the product is linked to it.
        linked = PRICE_GROUP.replace('<Amount>5</Amount>', '<Amount>5</Amount>').replace(
            "<Currency>EUR</Currency></FareProductPrice>", '<Currency>EUR</Currency><PreassignedFareProductRef ref="hd:PFP_1"/></FareProductPrice>'
        )
        self.assertEqual(generator.asked_object_problem(linked, "PreassignedFareProduct", ["5", "EUR"]), "")
        self.assertEqual(generator.error_class(problem), "asked-object")
        missing = generator.asked_object_problem(PRICE_GROUP.replace("PreassignedFareProduct", "SaleDiscountRight"), "PreassignedFareProduct", ["5"])
        self.assertIn("the frame has none", missing)
        # One of the values inside is enough: a line's operator may be an object of its own next to it.
        self.assertEqual(generator.asked_object_problem(PRICE_GROUP, "PreassignedFareProduct", ["Adult single", "5"]), "")

    def test_missing_asked_object_feedback_names_the_reference_and_two_frames(self):
        # The values sit in objects of one kind of frame that refer to the asked object, which the standard puts
        # in another kind of frame: the feedback names the reference and says how both frames go together.
        frame = (
            '<ThingFrame version="1" id="hd:FB"><things><Thing version="1" id="hd:T1"><Time>14:00:00</Time>'
            '<WidgetRef ref="hd:W1"/></Thing><Thing version="1" id="hd:T2"><Time>14:00:00</Time>'
            '<WidgetRef ref="hd:W1"/></Thing></things></ThingFrame>'
        )
        problem = generator.asked_object_problem(frame, "Widget", [])
        self.assertTrue(problem.startswith("the question asks for a Widget; the frame has none, only a reference to one (hd:W1)."), problem)
        self.assertIn("write a CompositeFrame whose <frames> holds both: the Widget in its frame, the objects you wrote in this ThingFrame", problem)
        self.assertEqual(generator.error_class(problem), "asked-object")
        # Without a reference: no reference named, the two-frame advice stays.
        plain = generator.asked_object_problem(frame.replace("WidgetRef", "GadgetRef"), "Widget", [])
        self.assertNotIn("only a reference", plain)
        self.assertIn("CompositeFrame", plain)
        # A composite frame already holds several frames: no advice to write one.
        composite = f'<CompositeFrame version="1" id="hd:CF"><frames>{frame}</frames></CompositeFrame>'
        self.assertNotIn("write a CompositeFrame", generator.asked_object_problem(composite, "Widget", []))

    def test_values_in_linked_objects_times_and_counts(self):
        parking = (
            '<SiteFrame version="1" id="hd:SF"><stopPlaces><StopPlace version="1" id="hd:SP"><Name>S</Name></StopPlace>'
            '</stopPlaces><parkings><Parking version="1" id="hd:P"><ParentSiteRef ref="hd:SP"/><TotalCapacity>40</TotalCapacity>'
            "</Parking></parkings></SiteFrame>"
        )
        self.assertEqual(generator.asked_object_problem(parking, "StopPlace", ["40"]), "")
        vehicle = (
            '<ResourceFrame version="1" id="hd:RF"><vehicleTypes><VehicleType version="1" id="hd:VT"><DeckPlanRef ref="hd:DP"/>'
            '</VehicleType></vehicleTypes><deckPlans><DeckPlan version="1" id="hd:DP"><Name>Upper 7</Name></DeckPlan></deckPlans></ResourceFrame>'
        )
        self.assertEqual(generator.asked_object_problem(vehicle, "VehicleType", ["Upper 7"]), "")
        # A count is not a value to find ("2 decks" is two Deck elements).
        self.assertEqual(generator.asked_object_problem(vehicle, "VehicleType", ["2"], "a vehicle type with a deck plan of 2 decks"), "")
        journey = (
            '<TimetableFrame version="1" id="hd:TF"><vehicleJourneys><ServiceJourney version="1" id="hd:SJ">'
            "<DepartureTime>07:15:00</DepartureTime></ServiceJourney></vehicleJourneys></TimetableFrame>"
        )
        self.assertEqual(generator.asked_object_problem(journey, "ServiceJourney", ["07:15"]), "")

    def test_skeleton_keeps_two_of_repeated_children_and_no_foreign_attributes(self):
        from lxml import etree

        document = etree.fromstring(
            '<JourneyPattern xmlns="http://www.netex.org.uk/netex" xmlns:x="urn:x" id="jp" x:extra="1"><pointsInSequence>'
            + "".join(f'<StopPointInJourneyPattern id="p{i}" order="{i}"/>' for i in range(5))
            + "</pointsInSequence><!-- note --></JourneyPattern>"
        )
        tree = generator._skeleton_tree(document, lambda tag: etree.QName(tag).localname if isinstance(tag, str) else "")
        xml = etree.tostring(tree, encoding="unicode")
        self.assertEqual(xml.count("<StopPointInJourneyPattern"), 2)
        self.assertNotIn("extra", xml)
        self.assertNotIn("note", xml)


@override_settings(LLM_ENABLED=True)
class SkeletonGenerationTests(SimpleTestCase):
    def setUp(self):
        for name, value in (("schema_declarations", []), ("value_element_declarations", [])):
            patcher = patch.object(generator, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_skeleton_goes_first_and_a_fragment_without_the_asked_object_is_retried(self):
        skeleton = {"xml": FARE_PRODUCT, "element": "PreassignedFareProduct", "sourcePath": "examples/fares/a.xml",
                    "repositoryUrl": "https://github.com/NeTEx-CEN/NeTEx", "valid": True}
        question = "Create a NeTEx XML example for a fare product for adult for 5 EUR."
        with patch.object(generator, "asked_element", return_value="PreassignedFareProduct"), patch.object(
            generator, "skeleton_for", return_value=skeleton
        ), patch("helpdesk.services.retrieval_gateway.shown_example_chunk", return_value=None), patch.object(
            generator, "_ask_model", side_effect=[_reply(PRICE_GROUP), _reply(FARE_PRODUCT)]
        ) as ask, patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}):
            result = generator.generate_netex_example(question, [NETEX_CHUNK], ["NeTEx"])
        first = ask.call_args_list[0].args[0][1]["content"]
        self.assertIn("SKELETON: a PreassignedFareProduct", first)
        self.assertLess(first.index("SKELETON"), first.index("EVIDENCE BLOCKS"))
        # A price group nothing links to the fare product: retried with the link feedback (plan 2026-11-12 R1).
        self.assertIn("PriceGroup (hd:PG_1) that nothing links to the PreassignedFareProduct", ask.call_args_list[1].args[0][-1]["content"])
        self.assertTrue(result["valid"])
        self.assertEqual((result["attempts"], result["askedObject"], result["askedObjectPresent"]), (2, "PreassignedFareProduct", True))
        self.assertEqual(result["skeletonSourcePath"], "examples/fares/a.xml")
        self.assertEqual(result["attemptLog"][0]["errorClass"], "link")

    def test_unresolved_question_has_no_skeleton_and_no_check(self):
        with patch.object(generator, "asked_element", return_value=""), patch.object(generator, "skeleton_for") as skeleton, patch.object(
            generator, "_ask_model", return_value=_reply(FRAME)
        ) as ask, patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}):
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        skeleton.assert_not_called()
        self.assertNotIn("SKELETON", ask.call_args_list[0].args[0][1]["content"])
        self.assertEqual((result["valid"], result["askedObject"], result["askedObjectPresent"]), (True, "", False))


@override_settings(LLM_ENABLED=True)
class StandardFallbackTests(SimpleTestCase):
    def setUp(self):
        for name, value in (("schema_declarations", []), ("value_element_declarations", []), ("skeleton_for", None)):
            patcher = patch.object(generator, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def standard(self):
        return {
            "valid": True, "origin": "standard", "validated": True, "attempts": 0,
            "xml": generator.indented_fragment(FARE_PRODUCT.replace(">5<", ">2.40<").replace(">EUR<", ">GBP<")),
            "sourcePath": "examples/fares/a.xml", "sourceUrl": "u", "repositoryUrl": "r", "valuePlaces": [],
            "elementNotes": [{"name": "PreassignedFareProduct", "documentation": "A product."}],
        }

    def test_failed_generation_shows_the_standard_object_labelled_without_the_values(self):
        question = "Create a NeTEx XML example for a fare product for adult for 5 EUR."
        verdict = {"valid": False, "errors": ["line 1: Element 'FarePrice': This element is not expected."]}
        with patch.object(generator, "asked_element", return_value="PreassignedFareProduct"), patch.object(
            generator, "_ask_model", return_value=_reply(PRICE_GROUP)
        ), patch.object(generator, "validate_fragment", return_value=verdict), patch.object(
            generator, "_plain_standard_example", return_value=self.standard()
        ) as plain:
            result = generator.generate_netex_example(question, [NETEX_CHUNK], ["NeTEx"])
        # Looked up by the element alone: the question's values would rule every file out.
        self.assertEqual(plain.call_args.args[0], "example of preassigned fare product")
        self.assertEqual(plain.call_args.args[2], ["PreassignedFareProduct"])
        self.assertEqual((result["origin"], result["holdsValues"], result["missingValues"]), ("standard", False, ["5", "EUR"]))
        self.assertEqual(result["valuePlaces"], [])
        self.assertEqual(result["generationErrors"], verdict["errors"])
        self.assertEqual(len(result["attemptLog"]), generator.MAX_ATTEMPTS)
        self.assertEqual(generator.example_origin(result), "standard-without-values")

    def test_no_fallback_without_a_resolved_object(self):
        verdict = {"valid": False, "errors": ["line 1: Element 'X': This element is not expected."]}
        with patch.object(generator, "asked_element", return_value=""), patch.object(
            generator, "_ask_model", return_value=_reply(FRAME)
        ), patch.object(generator, "validate_fragment", return_value=verdict), patch.object(generator, "_plain_standard_example") as plain:
            result = generator.generate_netex_example(BUS, [NETEX_CHUNK], ["NeTEx"])
        plain.assert_not_called()
        self.assertFalse(result["valid"])

    def test_answer_rule_for_an_example_without_the_values(self):
        from helpdesk.services.llm_generator import generated_example_rule

        rule = generated_example_rule(["PreassignedFareProduct"], "<FareFrame/>", "", "standard-without-values")
        self.assertIn("it does NOT contain the question's values", rule)
        self.assertIn("do not claim the example holds them", rule)
        self.assertNotIn("which element holds each value", rule)
        self.assertEqual(generator.example_origin({"origin": "standard"}), "standard")
        self.assertEqual(generator.example_origin({"valid": True}), "generated")


VALUE_TYPES_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.netex.org.uk/netex"
  targetNamespace="http://www.netex.org.uk/netex" elementFormDefault="qualified">
  <xsd:simpleType name="CurrencyType"><xsd:restriction base="xsd:NMTOKEN">
    <xsd:minLength value="3"/><xsd:maxLength value="3"/><xsd:pattern value="[A-Z][A-Z][A-Z]"/>
  </xsd:restriction></xsd:simpleType>
  <xsd:simpleType name="CurrencyAmountType"><xsd:restriction base="xsd:decimal"/></xsd:simpleType>
  <xsd:simpleType name="GroupingTypeEnumeration"><xsd:restriction base="xsd:NMTOKEN">
    <xsd:enumeration value="AND"/><xsd:enumeration value="XOR"/>
  </xsd:restriction></xsd:simpleType>
  <xsd:simpleType name="ColourValueType"><xsd:restriction base="xsd:hexBinary"><xsd:length value="3"/></xsd:restriction></xsd:simpleType>
  <xsd:complexType name="MultilingualString"><xsd:simpleContent><xsd:extension base="xsd:string">
    <xsd:attribute name="lang" type="xsd:language"/>
  </xsd:extension></xsd:simpleContent></xsd:complexType>
  <xsd:complexType name="PriceStructure"><xsd:sequence>
    <xsd:element name="Name" type="MultilingualString" minOccurs="0"/>
    <xsd:element name="Amount" type="CurrencyAmountType" minOccurs="0"/>
    <xsd:element name="Currency" type="CurrencyType" minOccurs="0"/>
    <xsd:element name="GroupingType" type="GroupingTypeEnumeration" minOccurs="0"/>
    <xsd:element name="Colour" type="ColourValueType" minOccurs="0"/>
    <xsd:element name="StartTime" type="xsd:time" minOccurs="0"/>
    <xsd:element name="FromDate" type="xsd:dateTime" minOccurs="0"/>
  </xsd:sequence></xsd:complexType>
  <xsd:element name="FareProductPrice" type="PriceStructure"/>
</xsd:schema>
"""


class ValueHolderTests(SimpleTestCase):
    """Which elements the schema lets hold a question's value (validator /accepting): specific types only."""

    def setUp(self):
        from lxml import etree

        from helpdesk.netex_content_model import ContentModels

        self.models = ContentModels()
        self.models.add_schema(etree.fromstring(VALUE_TYPES_XSD.encode()))

    def accepting(self, value):
        from helpdesk.netex_content_model import accepting_elements

        return accepting_elements(self.models, value)

    def test_a_currency_code_fits_the_currency_not_the_name_nor_an_enumeration(self):
        self.assertEqual(self.accepting("EUR"), {"Currency"})
        self.assertEqual(self.accepting("XOR"), {"Currency", "GroupingType"})

    def test_numbers_dates_and_times_fit_their_types(self):
        self.assertEqual(self.accepting("5"), {"Amount"})
        self.assertEqual(self.accepting("08:30"), {"StartTime", "FromDate"})
        self.assertEqual(self.accepting("2026-12-01"), {"FromDate"})

    def test_free_text_fits_no_specific_element(self):
        self.assertEqual(self.accepting("Ljubljana"), frozenset())
        self.assertEqual(self.accepting("Adult"), frozenset())  # not hexBinary: Colour stays out

    def test_value_holders_leave_out_broad_and_empty_sets(self):
        generator._HOLDERS_CACHE.clear()
        payload = {"found": True, "accepting": {
            "EUR": ["Currency", "DefaultCurrency"], "5": [f"E{i}" for i in range(generator.MAX_VALUE_HOLDERS + 1)],
            "Ljubljana": [], "GBP": ["Currency", "DefaultCurrency"],
        }}

        class Reply:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(payload).encode()

        with patch("urllib.request.urlopen", return_value=Reply()):
            holders = generator.value_holders(["5", "EUR", "Ljubljana", "GBP"])
        self.assertEqual(holders, [frozenset({"Currency", "DefaultCurrency"})])


# A fare product without a price, as in 72 of the 73 example files with one; the price is in a price group
# that refers to it; a user profile also refers to it and holds a number.
LINKED_PRICE_FILE = (
    '<PublicationDelivery xmlns="http://www.netex.org.uk/netex"><dataObjects>'
    '<FareFrame version="1" id="x:FF"><usageParameters><UserProfile version="1" id="x:UP"><MinimumAge>11</MinimumAge>'
    '<PreassignedFareProductRef version="1" ref="x:P"/></UserProfile></usageParameters>'
    '<fareProducts><PreassignedFareProduct version="1" id="x:P"><Name>Single</Name>'
    '<OrganisationRef version="1" ref="x:Elsewhere"/></PreassignedFareProduct></fareProducts>'
    '<priceGroups><PriceGroup version="1" id="x:PG"><members><FareProductPrice version="1" id="x:FPP">'
    '<Amount>1.25</Amount><Currency>USD</Currency><PreassignedFareProductRef version="1" ref="x:P"/>'
    "</FareProductPrice></members></PriceGroup></priceGroups></FareFrame></dataObjects></PublicationDelivery>"
)


class LinkedSkeletonTests(SimpleTestCase):
    """The skeleton brings the object linked to the asked one that holds elements for the question's values."""

    def parts(self, holders):
        from lxml import etree

        root = etree.fromstring(LINKED_PRICE_FILE.encode())
        local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
        return generator.skeleton_parts(root, "PreassignedFareProduct", holders, local), local

    def test_the_price_that_refers_to_the_product_comes_along(self):
        (obj, frame, companion, protect, covered), local = self.parts([frozenset({"Currency", "DefaultCurrency"})])
        self.assertEqual((local(obj.tag), local(companion.tag), covered), ("PreassignedFareProduct", "FareProductPrice", 1))
        xml = generator.skeleton_xml(obj, frame, companion, protect, local)
        # In the file's order, with the list wrappers; the user profile is left out.
        self.assertLess(xml.index("<fareProducts>"), xml.index("<priceGroups>"))
        self.assertIn("<members><FareProductPrice", xml)
        self.assertNotIn("UserProfile", xml)
        # A reference to the product in the skeleton keeps its version; one to an object outside loses it.
        self.assertIn('<PreassignedFareProductRef version="1" ref="x:P"/>', xml)
        self.assertIn('<OrganisationRef ref="x:Elsewhere"/>', xml)

    def test_without_values_the_object_comes_alone(self):
        (obj, frame, companion, protect, covered), local = self.parts([])
        self.assertIsNone(companion)
        self.assertNotIn("priceGroups", generator.skeleton_xml(obj, frame, companion, protect, local))

    def test_the_value_path_survives_the_size_cut(self):
        from lxml import etree

        root = etree.fromstring(LINKED_PRICE_FILE.encode())
        local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
        price = next(n for n in root.iter() if local(n.tag) == "FareProductPrice")
        currency = next(n for n in price.iter() if local(n.tag) == "Currency")
        tree = generator._skeleton_tree(price, local, frozenset({currency}), limit=2)
        self.assertEqual([local(n.tag) for n in tree.iter()], ["FareProductPrice", "Currency"])

    def test_the_prompt_names_the_linked_object(self):
        block = generator.skeleton_block({"element": "PreassignedFareProduct", "sourcePath": "examples/a.xml",
                                          "xml": "<FareFrame/>", "companion": "FareProductPrice"})
        self.assertIn("also holds a FareProductPrice from the same file that refers to the PreassignedFareProduct", block)
        self.assertNotIn("also holds", generator.skeleton_block({"element": "Line", "sourcePath": "a", "xml": "<X/>", "companion": ""}))


class _JsonReply:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class AskedFromPartsTests(SimpleTestCase):
    """An object named by no noun ("a coach with 49 seats") resolved from the elements of its counted parts."""

    def test_part_holders_match_the_noun_and_a_number_type(self):
        accepting = {"49": ["SeatingCapacity", "Seats", "Altitude", "NumberOfWheelchairAreas"],
                     "2": ["SeatingCapacity", "NumberOfWheelchairAreas", "WheelchairPlaceCapacity"]}
        with patch("urllib.request.urlopen", return_value=_JsonReply({"found": True, "accepting": accepting})) as opened:
            sets = generator.part_holders("Show a NeTEx example of a coach with 49 seats and 1 wheelchair area")
        self.assertEqual(sets, [frozenset({"SeatingCapacity", "Seats"}), frozenset({"NumberOfWheelchairAreas", "WheelchairPlaceCapacity"})])
        # 1 is also a boolean: looked up as 2.
        self.assertIn("value=2", opened.call_args.args[0])
        self.assertNotIn("value=1&", opened.call_args.args[0] + "&")

    def test_no_counts_no_lookup(self):
        with patch("urllib.request.urlopen") as opened:
            self.assertEqual(generator.part_holders("Show a NeTEx example of a coach"), [])
        opened.assert_not_called()

    def test_parts_side_by_side_are_closer_than_parts_far_apart(self):
        from lxml import etree

        together = etree.fromstring(
            "<VehicleType><PassengerCapacity><SeatingCapacity>5</SeatingCapacity>"
            "<WheelchairPlaceCapacity>1</WheelchairPlaceCapacity></PassengerCapacity></VehicleType>"
        )
        apart = etree.fromstring(
            "<StopPlace><a><b><SeatEquipment><Seats>5</Seats></SeatEquipment></b></a>"
            "<c><d><Equip><WheelchairTurningCircle>1</WheelchairTurningCircle></Equip></d></c></StopPlace>"
        )
        group = lambda root, name: [n for n in root.iter() if n.tag == name]  # noqa: E731
        near = generator._part_spread([group(together, "SeatingCapacity"), group(together, "WheelchairPlaceCapacity")])
        far = generator._part_spread([group(apart, "Seats"), group(apart, "WheelchairTurningCircle")])
        self.assertEqual(near, 2)
        self.assertGreater(far, near)

    @override_settings(LLM_ENABLED=True)
    def test_an_unresolved_noun_takes_the_object_of_its_parts(self):
        parts = [frozenset({"SeatingCapacity"})]
        with patch.object(generator, "schema_declarations", return_value=[]), patch.object(
            generator, "value_element_declarations", return_value=[]
        ), patch.object(generator, "asked_element", return_value=""), patch.object(
            generator, "asked_from_parts", return_value=("VehicleType", parts)
        ), patch.object(generator, "skeleton_for", return_value=None) as skeleton, patch.object(
            generator, "_ask_model", return_value=_reply(FRAME)
        ), patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}):
            result = generator.generate_netex_example(
                "Show a NeTEx example of a coach with 49 seats", [NETEX_CHUNK], ["NeTEx"]
            )
        self.assertEqual(skeleton.call_args.args[0], "VehicleType")
        self.assertEqual(skeleton.call_args.args[2], parts)
        self.assertEqual(result["askedObject"], "VehicleType")


STOP_PLACE_WITH_PARKING_FILE = """<PublicationDelivery xmlns="http://www.netex.org.uk/netex"><dataObjects>
<SiteFrame version="1" id="x:SF"><stopPlaces>
  <StopPlace version="1" id="x:SP"><Name>Stop</Name>
    <privateCodes><PrivateCode>7</PrivateCode></privateCodes></StopPlace>
</stopPlaces><parkings>
  <Parking version="1" id="x:Big"><Name>Big</Name><TotalCapacity>400</TotalCapacity><Covered>covered</Covered></Parking>
  <Parking version="1" id="x:Small"><TotalCapacity>20</TotalCapacity></Parking>
</parkings></SiteFrame></dataObjects></PublicationDelivery>"""


class NamedPartSkeletonTests(SimpleTestCase):
    """A part the question names as an object ("a stop place with a parking") comes into the skeleton."""

    def test_a_named_object_in_the_same_frame_comes_along_unlinked(self):
        from lxml import etree

        root = etree.fromstring(STOP_PLACE_WITH_PARKING_FILE.encode())
        local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
        obj, frame, companion, protect, covered = generator.skeleton_parts(root, "StopPlace", [frozenset({"Parking"})], local)
        # Not referring to the stop place: the smallest parking in the frame.
        self.assertEqual((local(companion.tag), companion.get("id"), covered), ("Parking", "x:Small", 1))
        xml = generator.skeleton_xml(obj, frame, companion, protect, local)
        self.assertLess(xml.index("</stopPlaces>"), xml.index("<parkings><Parking"))

    def test_an_object_counts_as_its_own_holder(self):
        from lxml import etree

        root = etree.fromstring(STOP_PLACE_WITH_PARKING_FILE.encode())
        local = lambda tag: etree.QName(tag).localname if isinstance(tag, str) else ""  # noqa: E731
        stop = next(n for n in root.iter() if local(n.tag) == "StopPlace")
        self.assertEqual(generator._holder_leaves(stop, [frozenset({"Parking"})], local), {})
        self.assertEqual(local(generator._holder_leaves(stop, [frozenset({"StopPlace"})], local)[0].tag), "StopPlace")

    def test_the_prompt_says_where_an_unlinked_part_goes(self):
        block = generator.skeleton_block({"element": "StopPlace", "sourcePath": "a", "xml": "<SiteFrame/>",
                                          "companion": "Parking", "companionLinked": False})
        self.assertIn("as its own object in the frame next to the StopPlace, not inside it", block)
        self.assertNotIn("refers to", block)


class EmptiedSkeletonTests(SimpleTestCase):
    """Elements the size cut left without a needed child are dropped until the skeleton validates."""

    def test_emptied_wrappers_are_dropped(self):
        fragment = "<SiteFrame><stopPlaces><StopPlace id='a'><privateCodes/><Name>N</Name></StopPlace></stopPlaces></SiteFrame>"
        replies = [
            {"valid": False, "errors": ["line 1: Element '{http://www.netex.org.uk/netex}privateCodes': Missing child element(s). Expected is ( PrivateCode )."]},
            {"valid": True, "errors": []},
        ]
        with patch.object(generator, "validate_fragment", side_effect=replies) as validate:
            fixed, valid = generator._without_emptied(fragment)
        self.assertTrue(valid)
        self.assertNotIn("privateCodes", fixed)
        self.assertIn("<Name>N</Name>", fixed)
        self.assertEqual(validate.call_count, 2)

    def test_other_errors_are_left_alone(self):
        with patch.object(generator, "validate_fragment", return_value={"valid": False, "errors": ["line 1: Element 'X': This element is not expected."]}):
            self.assertEqual(generator._without_emptied("<X/>"), ("<X/>", False))


FERRY = (
    "I want to map a ferry service into a NeTEx TemplateServiceJourney. The ferry operates between two sides of the "
    "river when there is demand, it takes 3 minutes from side to side. Can you create an XML file modelling such "
    "TemplateServiceJourney?"
)
CROSSING = (
    '<TimetableFrame version="1" id="hd:TF"><vehicleJourneys><TemplateServiceJourney version="1" id="hd:TSJ">'
    '<DepartureTime>10:00:00</DepartureTime><calls>'
    '<Call version="1" id="hd:C1" order="1"><ScheduledStopPointRef ref="hd:A"/><Departure><Time>10:00:00.0Z</Time></Departure></Call>'
    '<Call version="1" id="hd:C2" order="2"><ScheduledStopPointRef ref="hd:B"/><Arrival><Time>10:03:00.0Z</Time></Arrival></Call>'
    "</calls></TemplateServiceJourney></vehicleJourneys></TimetableFrame>"
)


class XmlRequestTests(SimpleTestCase):
    """Requests to produce XML without an example word (prod req-mwb6auo0-n3jh83, 2026-11-10)."""

    def test_requests_to_produce_xml_trigger(self):
        for question in (
            FERRY,
            "The ferry takes 3 minutes. Can you give an XML snipped modelling such TemplateServiceJourney in NeTEx?",
            "Can you write the XML for a NeTEx FlexibleLine?",
            "Create NeTEx XML for a TemplateServiceJourney that runs every 10 minutes between 06:00 and 22:00.",
            "Please generate a NeTEx XML document for a stop place with two quays.",
        ):
            self.assertTrue(generator.asks_for_netex_example(question, ["NeTEx"]), question)

    def test_questions_about_xml_do_not_trigger(self):
        for question in (
            "How do I validate a NeTEx XML file?",
            "What does the header of a NeTEx XML file contain?",
            "Which XML schema does NeTEx use?",
            "How do I write the XML header in NeTEx?",
            "Can you show me which XML elements hold the price in NeTEx?",
        ):
            self.assertFalse(generator.asks_for_netex_example(question, ["NeTEx"]), question)

    def test_the_request_is_not_another_question(self):
        self.assertEqual(generator.other_question(FERRY), "")
        self.assertEqual(
            generator.other_question("What is a FlexibleLine? Can you write the XML for one in NeTEx?"), "What is a FlexibleLine?"
        )

    def test_xml_for_names_the_subject(self):
        self.assertEqual(generator.asked_subject("Show me the XML for a stop place with two quays in NeTEx"), "stop place")


class NamedElementTests(SimpleTestCase):
    def setUp(self):
        generator._ASKED_CACHE.clear()
        self.addCleanup(generator._ASKED_CACHE.clear)
        known = {
            "TemplateServiceJourney": [{"name": "TemplateServiceJourney", "object": True}],
            "ServiceJourney": [{"name": "ServiceJourney", "object": True}],
            "FareProduct": [{"name": "PreassignedFareProduct", "object": True}],
            "StopPlace": [{"name": "StopPlace", "object": True}],
            "AccessSpace": [{"name": "AccessSpace", "object": True}],
            "PassengerCapacity": [{"name": "PassengerCapacity", "object": False}],
        }
        for target, kwargs in (
            ("concrete_elements", {"side_effect": lambda name: known.get(name)}),
            ("_in_examples", {"return_value": True}),
        ):
            patcher = patch.object(generator, target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_the_named_object_is_asked_when_there_is_no_subject_phrase(self):
        self.assertEqual(generator.asked_element(FERRY), "TemplateServiceJourney")

    def test_most_often_named_first_abstract_names_their_member_and_properties_are_no_objects(self):
        self.assertEqual(
            generator.named_elements("A ServiceJourney or a TemplateServiceJourney? I need the TemplateServiceJourney XML"),
            ["TemplateServiceJourney", "ServiceJourney"],
        )
        self.assertEqual(generator.named_elements("Write the XML of a FareProduct in NeTEx"), ["PreassignedFareProduct"])
        self.assertEqual(generator.named_elements("Write NeTEx XML with a PassengerCapacity"), [])
        self.assertEqual(generator.named_elements("Write the NeTEx XML file"), [])

    def test_a_named_part_is_not_the_object(self):
        question = "Create NeTEx XML for a StopPlace with two AccessSpaces"
        self.assertEqual(generator.named_elements(question), ["StopPlace"])
        self.assertEqual(generator.named_elements("Create the NeTEx XML file of a StopPlace with an AccessSpace"), ["StopPlace"])

    def test_the_subject_phrase_still_comes_first(self):
        question = "Show a NeTEx example of a service journey, not a TemplateServiceJourney"
        self.assertEqual(generator.asked_element(question), "ServiceJourney")

    def test_a_plain_request_shows_the_named_object_before_the_nearest_concept(self):
        found = {"valid": True, "origin": "standard", "validated": True, "sourcePath": "examples/a.xml"}
        with patch.object(generator, "concept_elements", return_value=["Line"]), patch.object(
            generator, "_from_standard", return_value=found
        ) as standard:
            generator.generate_netex_example("Can you write the XML for a NeTEx TemplateServiceJourney?", [], ["NeTEx"])
        self.assertEqual(standard.call_args.args[2], "TemplateServiceJourney")


class DurationTests(SimpleTestCase):
    def test_durations_as_xsd_durations(self):
        self.assertEqual(
            generator.durations("3 minutes, a 3-minute crossing, 30 sec, 1.5 hours, two hours, 2 days"),
            [
                ("3 minutes", 180, "PT3M"), ("3-minute", 180, "PT3M"), ("30 sec", 30, "PT30S"),
                ("1.5 hours", 5400, "PT5400S"), ("two hours", 7200, "PT2H"), ("2 days", 172800, "P2D"),
            ],
        )
        self.assertEqual(generator.durations("3 minibuses and 2 secretaries"), [])

    def test_a_duration_is_one_value_and_not_a_count(self):
        self.assertEqual(generator.requested_values(FERRY), ["PT3M"])
        self.assertEqual(generator.counted_shapes(FERRY), [(2, "two", "sides")])
        self.assertEqual(
            generator.requested_values("A TemplateServiceJourney every 10 minutes between 06:00 and 22:00"),
            ["06:00", "22:00", "PT10M"],
        )
        self.assertTrue(generator.wants_generated_example(FERRY, ["NeTEx"]))

    def test_xsd_duration_values_compare_in_seconds(self):
        for text in ("PT3M", "PT180S", "PT3M0S", "PT0H3M"):
            self.assertTrue(generator.holds_value(text, "PT3M"), text)
        for text in ("3", "PT3H", "PT", "P", "PT30M"):
            self.assertFalse(generator.holds_value(text, "PT3M"), text)
        self.assertIsNone(generator.duration_seconds("P1Y"))

    def test_a_duration_is_met_by_two_times_that_far_apart_in_one_object(self):
        self.assertEqual(generator._unmet_values(CROSSING, ["PT3M"], FERRY), [])
        self.assertEqual(generator._unmet_values(CROSSING, ["PT5M"], "it takes 5 minutes"), ["PT5M"])
        # Across midnight in dateTimes, and times in two unrelated objects do not count.
        overnight = CROSSING.replace("10:00:00.0Z", "2026-12-01T23:59:00").replace("10:03:00.0Z", "2026-12-02T00:02:00")
        self.assertEqual(generator._unmet_values(overnight, ["PT3M"], FERRY), [])
        apart = (
            '<TimetableFrame version="1" id="hd:TF"><vehicleJourneys>'
            '<ServiceJourney version="1" id="hd:J1"><DepartureTime>10:00:00</DepartureTime></ServiceJourney>'
            '<ServiceJourney version="1" id="hd:J2"><DepartureTime>10:03:00</DepartureTime></ServiceJourney>'
            "</vehicleJourneys></TimetableFrame>"
        )
        self.assertEqual(generator._unmet_values(apart, ["PT3M"], FERRY), ["PT3M"])
        self.assertEqual(generator.asked_object_problem(CROSSING, "TemplateServiceJourney", ["PT3M"], FERRY), "")

    def test_places_and_prompt_say_the_duration_as_written(self):
        places = generator._places(CROSSING, ["PT3M"], FERRY)
        self.assertEqual(places, [{"value": "3 minutes", "element": "Time", "path": [
            "TimetableFrame", "vehicleJourneys", "TemplateServiceJourney", "calls", "Call", "Arrival"]}])
        held = CROSSING.replace("<calls>", "<JourneyDuration>PT180S</JourneyDuration><calls>")
        self.assertEqual(generator._places(held, ["PT3M"], FERRY)[0]["element"], "JourneyDuration")
        self.assertIn("3 minutes (an xs:duration PT3M", generator.values_line(["PT3M", "EUR"], FERRY))
        self.assertTrue(generator.missing_value_error("PT3M", FERRY).startswith("the duration 3 minutes (PT3M) from the question is missing"))
        self.assertTrue(generator.missing_value_error("5", "5 EUR").startswith("the value 5 from the question is missing"))

    @override_settings(LLM_ENABLED=True)
    def test_the_ferry_question_is_generated_for_its_named_object_in_one_attempt(self):
        with patch.object(generator, "asked_element", return_value="TemplateServiceJourney"), patch.object(
            generator, "skeleton_for", return_value=None
        ), patch.object(generator, "_from_standard", return_value=None), patch.object(
            generator, "conditions_block", return_value=""
        ), patch.object(generator, "schema_declarations", return_value=[]), patch.object(
            generator, "_ask_model", return_value=_reply(ON_DEMAND_FERRY)
        ) as ask, patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}):
            result = generator.generate_netex_example(FERRY, [NETEX_CHUNK], ["NeTEx"])
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["askedObject"], "TemplateServiceJourney")
        self.assertEqual(result["valuePlaces"][0]["value"], "3 minutes")
        self.assertIn("Values to use: 3 minutes (an xs:duration PT3M", ask.call_args.args[0][1]["content"])


ON_DEMAND_FERRY = CROSSING.replace(
    "</calls>",
    '</calls><FlexibleServiceProperties version="1" id="hd:FSP"><FlexibleServiceType>dynamicPassingTimes</FlexibleServiceType>'
    "</FlexibleServiceProperties>",
)
FLEXIBLE_STRUCTURE = {
    "element": "FlexibleServiceProperties",
    "documentation": "Additional characteristics of a FLEXIBLE SERVICE.",
    "groups": [
        {"owner": "FlexibleServiceProperties", "inherited": False, "children": [
            {"name": "JourneyRef", "documentation": "Reference to a JOURNEY."},
            {"name": "FlexibleServiceType", "documentation": "Flexible service type is DynamicPassingTimes/…",
             "values": ["dynamicPassingTimes", "fixedHeadwayFrequency"]},
            {"name": "CancellationPossible", "documentation": "Whether cancellation is always possible."},
        ]},
        {"owner": "DataManagedObject", "inherited": True, "children": [{"name": "keyList", "documentation": ""}]},
    ],
}
STANDARD_FLEXIBLE = {
    "parent": "ServiceJourney", "after": "calls", "sourcePath": "examples/functions/timetable/Netex_07.2.xml",
    "xml": '<FlexibleServiceProperties version="1" id="x:1">\n  <BookingAccess>public</BookingAccess>\n</FlexibleServiceProperties>',
}


class ServiceConditionTests(SimpleTestCase):
    """How a service runs, modelled by an object of its own (prod req-mwb6auo0-n3jh83: a ferry that runs
    "when there is demand", modelled with FlexibleServiceProperties on Andrej's decision, 2026-11-10)."""

    def test_on_demand_phrases(self):
        for question in (FERRY, "an on-demand bus", "a demand-responsive service", "a dial-a-ride minibus",
                         "the line runs on request", "it only runs when booked", "a flexible service"):
            self.assertEqual([e for _, e in generator.service_conditions(question)], ["FlexibleServiceProperties"], question)
        self.assertEqual(generator.service_conditions(FERRY)[0][0], "when there is demand")
        for question in ("How much demand is there for the ferry?", "a flexible line", "a bus with flexible seats"):
            self.assertEqual(generator.service_conditions(question), [], question)

    def test_a_condition_alone_asks_for_a_generated_example(self):
        self.assertTrue(generator.wants_generated_example("Show me a NeTEx example of an on-demand ServiceJourney", ["NeTEx"]))

    def test_the_condition_must_be_modelled_with_content(self):
        conditions = generator.service_conditions(FERRY)
        self.assertEqual(generator.condition_problems(ON_DEMAND_FERRY, conditions), [])
        missing = generator.condition_problems(CROSSING, conditions)
        self.assertTrue(missing[0].startswith("the question says the service runs “when there is demand”"), missing)
        self.assertEqual(generator.error_class(missing[0]), "condition")
        empty = CROSSING.replace("</calls>", '</calls><FlexibleServiceProperties version="1" id="hd:FSP"/>')
        self.assertIn("is empty", generator.condition_problems(empty, conditions)[0])
        self.assertEqual(generator.error_class(generator.condition_problems(empty, conditions)[0]), "condition")

    def test_the_place_of_the_condition(self):
        places = generator.condition_places(ON_DEMAND_FERRY, generator.service_conditions(FERRY))
        self.assertEqual(places, [{"value": "when there is demand", "element": "FlexibleServiceProperties",
                                   "path": ["TimetableFrame", "vehicleJourneys", "TemplateServiceJourney"]}])

    def test_the_prompt_places_it_inside_the_asked_object_after_the_standard_s_sibling(self):
        with patch.object(generator, "_structure", return_value=FLEXIBLE_STRUCTURE), patch.object(
            generator, "_declared_parents", return_value=["ServiceJourney", "TemplateServiceJourney", "flexibleServiceProperties"]
        ), patch.object(generator, "condition_example", return_value=STANDARD_FLEXIBLE):
            block = generator.conditions_block(generator.service_conditions(FERRY), "TemplateServiceJourney")
        self.assertIn("write one FlexibleServiceProperties element inside the TemplateServiceJourney, right after its calls", block)
        self.assertIn("its values are that file's, not the question's", block)
        self.assertIn("FlexibleServiceType: Flexible service type is DynamicPassingTimes/… Allowed values: dynamicPassingTimes, fixedHeadwayFrequency.", block)
        # References back and inherited children are left out.
        self.assertNotIn("JourneyRef", block)
        self.assertNotIn("keyList", block)

    @override_settings(LLM_ENABLED=True)
    def test_the_on_demand_ferry_is_generated_with_the_condition_and_retried_without_it(self):
        replies = [_reply(CROSSING), _reply(ON_DEMAND_FERRY)]
        with patch.object(generator, "asked_element", return_value="TemplateServiceJourney"), patch.object(
            generator, "skeleton_for", return_value=None
        ), patch.object(generator, "_from_standard") as standard, patch.object(
            generator, "conditions_block", return_value="HOW THE SERVICE RUNS: …"
        ), patch.object(generator, "_ask_model", side_effect=replies) as ask, patch.object(
            generator, "validate_fragment", return_value={"valid": True, "errors": []}
        ):
            result = generator.generate_netex_example(FERRY, [NETEX_CHUNK], ["NeTEx"])
        standard.assert_not_called()  # the standard's own journeys need not model the condition
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["attempts"], 2)
        self.assertIn("HOW THE SERVICE RUNS", ask.call_args_list[0].args[0][1]["content"])
        self.assertIn("when there is demand", ask.call_args_list[1].args[0][-1]["content"])
        self.assertEqual(result["serviceConditions"], [{"phrase": "when there is demand", "element": "FlexibleServiceProperties"}])
        self.assertEqual([p["value"] for p in result["valuePlaces"]], ["3 minutes", "when there is demand"])


ENUM_XSD = TINY_XSD.replace(
    '<xsd:element name="Capacity" type="xsd:string" minOccurs="0">',
    '<xsd:element name="Kind" type="KindEnumeration" minOccurs="0"/><xsd:element name="Capacity" type="xsd:string" minOccurs="0">',
).replace(
    "</xsd:schema>",
    '<xsd:simpleType name="KindEnumeration"><xsd:restriction base="xsd:string"><xsd:enumeration value="dynamicPassingTimes"/>'
    '<xsd:enumeration value="fixedPassingTimes"/></xsd:restriction></xsd:simpleType>\n</xsd:schema>',
)


class StructureValuesTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.checkout = Path(directory.name)
        (self.checkout / "xsd").mkdir()
        (self.checkout / service.SCHEMA_ENTRY).write_text(ENUM_XSD)
        git = self.checkout / ".git" / "refs" / "heads"
        git.mkdir(parents=True)
        (self.checkout / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (git / "main").write_text("1234abcd\n")
        self.holder = service.SchemaHolder(self.checkout)
        self.holder.load()

    def test_enumerated_children_carry_their_values(self):
        found = service.structure_with_values(self.holder, "ResourceFrame")
        children = {c["name"]: c for g in found["groups"] for c in g["children"]}
        self.assertEqual(children["Kind"]["values"], ["dynamicPassingTimes", "fixedPassingTimes"])
        self.assertNotIn("values", children["Capacity"])


class IdentifierTests(SimpleTestCase):
    """Ids named after the question, not copied from the standard's file (prod req-diag-ferry-0974: the ferry's
    stop points were mybus:SSP_001 and mybus:SSP_002 from a bus example; 6 of 93 benchmark runs copied ids)."""

    def test_the_skeleton_s_ids_are_that_file_s(self):
        block = generator.skeleton_block({"element": "ServiceJourney", "sourcePath": "examples/a.xml", "xml": "<ServiceJourney/>"})
        self.assertIn("Its ids are that file's: do not reuse them", block)
        self.assertIn("'hd:SSP_SideA' and 'hd:SSP_SideB' for the two sides of a river", block)
        self.assertIn("references to the standard's shared codes (TypeOf…) may stay", block)
        self.assertIn("An id names an object and holds none of the question's values", block)


# Prod req-mwdzf8px-3qfhdl (2026-11-12), shortened: valid, but nothing refers to anything.
UNLINKED_LINE = (
    '<CompositeFrame version="1.0" id="hd:CF"><frames>'
    '<ResourceFrame version="1.0" id="hd:RF"><vehicleTypes><VehicleType version="any" id="hd:VT_LowFloor">'
    "<Name>Low-floor bus</Name></VehicleType></vehicleTypes></ResourceFrame>"
    '<ServiceCalendarFrame version="1.0" id="hd:SCF"><dayTypes><FareDayType version="any" id="hd:school_day">'
    "<Name>School day</Name></FareDayType></dayTypes></ServiceCalendarFrame>"
    '<ServiceFrame version="1.0" id="hd:SF"><lines><Line version="any" id="hd:LN"><Name>Line 1</Name></Line></lines>'
    '<scheduledStopPoints><ScheduledStopPoint version="any" id="hd:SSP_Maribor"><Name>Maribor</Name></ScheduledStopPoint>'
    '<ScheduledStopPoint version="any" id="hd:SSP_Ptuj"><Name>Ptuj</Name></ScheduledStopPoint></scheduledStopPoints>'
    "</ServiceFrame></frames></CompositeFrame>"
)
LINKED_LINE = (
    '<CompositeFrame version="1.0" id="hd:CF"><frames>'
    '<ResourceFrame version="1.0" id="hd:RF"><vehicleTypes><VehicleType version="any" id="hd:VT">'
    "<LowFloor>true</LowFloor></VehicleType></vehicleTypes></ResourceFrame>"
    '<ServiceFrame version="1.0" id="hd:SF"><lines><Line version="any" id="hd:LN"><Name>Line 1</Name></Line></lines>'
    '<scheduledStopPoints><ScheduledStopPoint version="any" id="hd:SSP_1"><Name>Maribor</Name></ScheduledStopPoint>'
    '<ScheduledStopPoint version="any" id="hd:SSP_2"><Name>Ptuj</Name></ScheduledStopPoint>'
    "</scheduledStopPoints></ServiceFrame>"
    '<TimetableFrame version="1.0" id="hd:TF"><vehicleJourneys><ServiceJourney version="any" id="hd:SJ">'
    '<VehicleTypeRef ref="hd:VT" version="any"/><LineRef ref="hd:LN" version="any"/><calls><Call id="hd:C1" order="1">'
    '<ScheduledStopPointRef ref="hd:SSP_1" version="any"/></Call><Call id="hd:C2" order="2">'
    '<ScheduledStopPointRef ref="hd:SSP_2" version="any"/></Call></calls></ServiceJourney></vehicleJourneys>'
    "</TimetableFrame></frames></CompositeFrame>"
)
STOP_PLACE_WITH_QUAYS = (
    '<SiteFrame version="1" id="hd:SF"><stopPlaces><StopPlace version="1" id="hd:SP"><Name>Celje</Name><quays>'
    '<Quay version="1" id="hd:Q1"><Name>Quay 1</Name></Quay></quays></StopPlace></stopPlaces></SiteFrame>'
)


class LinkedObjectTests(SimpleTestCase):
    def test_objects_nothing_links_to_the_asked_object(self):
        found = [(item["element"], item["id"]) for item in generator.unlinked_objects(UNLINKED_LINE, "Line")]
        self.assertEqual(found, [("VehicleType", "hd:VT_LowFloor"), ("FareDayType", "hd:school_day"),
                                 ("ScheduledStopPoint", "hd:SSP_Maribor"), ("ScheduledStopPoint", "hd:SSP_Ptuj")])

    def test_links_through_another_object_and_nesting_count(self):
        self.assertEqual(generator.unlinked_objects(LINKED_LINE, "Line"), [])
        self.assertEqual(generator.unlinked_objects(STOP_PLACE_WITH_QUAYS, "StopPlace"), [])

    def test_no_asked_object_no_check(self):
        self.assertEqual(generator.unlinked_objects(UNLINKED_LINE, ""), [])
        self.assertEqual(generator.unlinked_objects(UNLINKED_LINE, "StopPlace"), [])

    def test_feedback_names_the_linking_object_shared_by_several_kinds(self):
        journey = {"holder": "ServiceJourney", "toElement": ["VehicleTypeRef"], "toAsked": ["LineRef"], "sourcePath": "a.xml", "files": 6}
        block = {"holder": "Block", "toElement": ["VehicleTypeRef"], "toAsked": ["coursesOfJourneys", "CourseOfJourneys", "LineRef"], "sourcePath": "b.xml", "files": 7}
        stops = {"holder": "ServiceJourney", "toElement": ["calls", "Call", "ScheduledStopPointRef"], "toAsked": ["LineRef"], "sourcePath": "c.xml", "files": 5}
        examples = {
            "VehicleType": {**block, "holders": {"Block": block, "ServiceJourney": journey}},
            "ScheduledStopPoint": {**stops, "holders": {"ServiceJourney": stops}},
            "FareDayType": None,
        }
        question = "Give me a NeTEx example of a bus line from Maribor to Ptuj that runs only on school days and uses low-floor vehicles."
        with patch.object(generator, "link_example", side_effect=lambda element, asked: examples[element]):
            problems = generator.link_problems(UNLINKED_LINE, "Line", question, ["Maribor", "Ptuj"])
        self.assertEqual(len(problems), 3)
        self.assertIn("through a ServiceJourney (a.xml): ServiceJourney > VehicleTypeRef and ServiceJourney > LineRef", problems[0])
        self.assertIn("Link it to the Line by a reference", problems[1])
        self.assertIn("(hd:SSP_Maribor, hd:SSP_Ptuj)", problems[2])
        self.assertIn("ServiceJourney > calls > Call > ScheduledStopPointRef", problems[2])
        # Asked for by the question (low-floor, school day, the values): never "remove it".
        self.assertFalse(any("remove it" in problem for problem in problems))
        self.assertEqual(generator.error_class(problems[0]), "link")

    def test_an_object_the_question_does_not_name_may_be_removed(self):
        with patch.object(generator, "link_example", return_value=None):
            problems = generator.link_problems(UNLINKED_LINE, "Line", "Show a NeTEx example of a line from Maribor to Ptuj", ["Maribor", "Ptuj"])
        self.assertTrue(problems[0].endswith("or remove it if the question does not need it."))  # VehicleType
        self.assertFalse(problems[2].endswith("does not need it."))  # the stop points hold the values


@override_settings(LLM_ENABLED=True)
class LinkRetryTests(SimpleTestCase):
    def setUp(self):
        for name, value in (("schema_declarations", []), ("value_element_declarations", []), ("skeleton_for", None),
                            ("asked_element", "Line"), ("link_example", None), ("_from_standard", None)):
            patcher = patch.object(generator, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    QUESTION = "Give me a NeTEx example of a bus line from Maribor to Ptuj that runs only on school days and uses low-floor vehicles."

    def _run(self, replies):
        with patch.object(generator, "_ask_model", side_effect=[_reply(xml) for xml in replies]) as ask, patch.object(
            generator, "validate_fragment", return_value={"valid": True, "errors": []}
        ), patch.object(generator, "asked_object_problem", return_value=""):
            return generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"]), ask

    def test_unlinked_objects_are_retried(self):
        result, ask = self._run([UNLINKED_LINE, LINKED_LINE])
        self.assertIn("that nothing links to the Line", ask.call_args_list[1].args[0][-1]["content"])
        self.assertEqual((result["valid"], result["attempts"]), (True, 2))
        self.assertNotIn("unlinkedObjects", result)
        self.assertEqual(result["attemptLog"][0]["errorClass"], "link")
        self.assertEqual(result["attemptLog"][0]["fragment"], UNLINKED_LINE)

    def test_last_attempt_with_only_unlinked_objects_is_shown_and_names_them(self):
        # One extra attempt, as an acceptable fragment is in hand (revision 2, R3).
        total = generator.MAX_ATTEMPTS + generator.SOFT_EXTRA_ATTEMPTS
        result, _ = self._run([UNLINKED_LINE] * total)
        self.assertEqual((result["valid"], result["origin"], result["attempts"]), (True, "generated", total))
        self.assertEqual([item["element"] for item in result["unlinkedObjects"]],
                         ["VehicleType", "FareDayType", "ScheduledStopPoint", "ScheduledStopPoint"])

    def test_an_acceptable_unlinked_fragment_survives_a_broken_last_attempt(self):
        broken = {"valid": False, "errors": ["line 1: Element 'Y': This element is not expected."]}
        with patch.object(generator, "_ask_model", side_effect=[_reply(UNLINKED_LINE)] * 4), patch.object(
            generator, "validate_fragment",
            side_effect=[{"valid": False, "errors": ["line 1: Element 'X': This element is not expected."]},
                         {"valid": True, "errors": []}, broken, broken],
        ):
            result = generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        self.assertEqual((result["valid"], result["origin"], result["attempts"]), (True, "generated", 4))
        self.assertEqual(len(result["unlinkedObjects"]), 4)
        self.assertEqual([entry["errorClass"] for entry in result["attemptLog"]], ["not-expected", "link", "not-expected", "not-expected"])

    def test_the_extra_attempt_can_link(self):
        broken = {"valid": False, "errors": ["line 1: Element 'serviceJourneys': This element is not expected."]}
        with patch.object(generator, "_ask_model", side_effect=[_reply(UNLINKED_LINE), _reply(UNLINKED_LINE), _reply(LINKED_LINE), _reply(LINKED_LINE)]), patch.object(
            generator, "validate_fragment", side_effect=[broken, {"valid": True, "errors": []}, broken, {"valid": True, "errors": []}]
        ), patch.object(generator, "asked_object_problem", return_value=""):
            result = generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        self.assertEqual((result["valid"], result["attempts"]), (True, 4))
        self.assertNotIn("unlinkedObjects", result)

    def test_no_extra_attempt_without_an_acceptable_fragment(self):
        broken = {"valid": False, "errors": ["line 1: Element 'Y': This element is not expected."]}
        with patch.object(generator, "_ask_model", side_effect=[_reply(UNLINKED_LINE)] * 4) as ask, patch.object(
            generator, "validate_fragment", return_value=broken
        ):
            generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        self.assertEqual(ask.call_count, generator.MAX_ATTEMPTS)

    def test_the_fragment_with_fewer_unlinked_objects_is_kept(self):
        two = UNLINKED_LINE.replace('<ScheduledStopPoint version="any" id="hd:SSP_Maribor"><Name>Maribor</Name></ScheduledStopPoint>', "")
        two = two.replace("<Line version=\"any\" id=\"hd:LN\"><Name>Line 1</Name></Line>",
                          '<Line version="any" id="hd:LN"><Name>Maribor</Name></Line>')
        result, _ = self._run([UNLINKED_LINE, two, UNLINKED_LINE])
        self.assertEqual([item["id"] for item in result["unlinkedObjects"]], ["hd:VT_LowFloor", "hd:school_day", "hd:SSP_Ptuj"])

    def test_a_missing_value_stays_a_hard_failure(self):
        without_values = UNLINKED_LINE.replace(">Maribor<", ">Stop 1<").replace(">Ptuj<", ">Stop 2<")
        result, ask = self._run([without_values] * generator.MAX_ATTEMPTS)
        self.assertNotIn("unlinkedObjects", result)
        self.assertEqual([entry["errorClass"] for entry in result["attemptLog"]], ["value"] * generator.MAX_ATTEMPTS)


class UnlinkedTextTests(SimpleTestCase):
    def test_sentence_matches_the_frontend_wording(self):
        example = {"askedObject": "Line", "unlinkedObjects": [
            {"element": "VehicleType", "id": "a"}, {"element": "ScheduledStopPoint", "id": "b"}, {"element": "ScheduledStopPoint", "id": "c"}]}
        self.assertEqual(generator.unlinked_text(example), "In this example nothing links the VehicleType and 2 ScheduledStopPoints to the Line.")
        self.assertEqual(generator.unlinked_text({"askedObject": "Line", "unlinkedObjects": []}), "")
        self.assertEqual(generator.unlinked_text(None), "")

    def test_the_narrator_is_told_not_to_contradict_it(self):
        from helpdesk.services.llm_generator import generated_example_rule

        note = "In this example nothing links the DayType to the Line."
        rule = generated_example_rule(["Line"], "<ServiceFrame/>", "", "generated", note)
        self.assertIn(f"With the example the user is also told: “{note}” Do not contradict this", rule)
        self.assertNotIn("also told", generated_example_rule(["Line"], "<ServiceFrame/>"))


@override_settings(LLM_ENABLED=True)
class SkeletonSkipTests(SimpleTestCase):
    """Plan 2026-11-12 revision 3, S1: no skeleton when two or more values have no known holder."""

    def setUp(self):
        for name, value in (("schema_declarations", []), ("value_element_declarations", []), ("asked_element", "Line"),
                            ("link_example", None), ("_from_standard", None)):
            patcher = patch.object(generator, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run(self, question, holders):
        skeleton = {"xml": "<ServiceFrame/>", "element": "Line", "sourcePath": "examples/line/a.xml", "valid": True}
        with patch.object(generator, "value_holders", return_value=holders), patch.object(
            generator, "skeleton_for", return_value=skeleton
        ) as skeleton_for, patch("helpdesk.services.retrieval_gateway.shown_example_chunk", return_value=None), patch.object(
            generator, "_ask_model", return_value=_reply(LINKED_LINE)
        ) as ask, patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}):
            result = generator.generate_netex_example(question, [NETEX_CHUNK], ["NeTEx"])
        return result, skeleton_for, ask.call_args_list[0].args[0][1]["content"]

    def test_two_values_without_a_holder_get_no_skeleton(self):
        result, skeleton_for, prompt = self._run("Give me a NeTEx example of a bus line from Maribor to Ptuj", [])
        skeleton_for.assert_not_called()
        self.assertNotIn("SKELETON", prompt)
        self.assertEqual(result["skeletonSkipped"], "values")

    def test_one_value_without_a_holder_keeps_the_skeleton(self):
        result, skeleton_for, prompt = self._run('Show a NeTEx example of a line named "Maribor"', [])
        skeleton_for.assert_called_once()
        self.assertIn("SKELETON", prompt)
        self.assertNotIn("skeletonSkipped", result)

    def test_values_with_a_holder_keep_the_skeleton(self):
        result, skeleton_for, _ = self._run('Show a NeTEx example of a line with public code "6" operated by "LPP"', [frozenset({"PublicCode"})])
        skeleton_for.assert_called_once()
        self.assertNotIn("skeletonSkipped", result)

    def test_no_validator_keeps_the_skeleton(self):
        _, skeleton_for, _ = self._run("Give me a NeTEx example of a bus line from Maribor to Ptuj", None)
        skeleton_for.assert_called_once()


# Prod req-diag-s1-1794542419 (2026-11-13), attempts 2 and 3: the joined name the value check refused, and the split
# the model wrote to pass it.
JOINED_LINE = (
    '<ServiceFrame version="1.0" id="hd:SF_1"><lines><Line version="any" id="hd:LN_1"><Name>Maribor - Ptuj</Name>'
    "<Description>School days only, low-floor vehicles</Description><TransportMode>bus</TransportMode></Line></lines>"
    "</ServiceFrame>"
)
SPLIT_LINE = JOINED_LINE.replace("<Name>Maribor - Ptuj</Name>", "<Name>Maribor</Name><ShortName>Ptuj</ShortName>")


class SharedNameTests(SimpleTestCase):
    """Plan 2026-11-12 revision 4, T1-T4: two of the question's values are not two names of one object."""

    QUESTION = LinkRetryTests.QUESTION
    VALUES = ["Maribor", "Ptuj"]

    def test_two_values_as_name_and_short_name_of_one_line_are_found(self):
        found = generator.shared_name_values(SPLIT_LINE, self.VALUES, self.QUESTION)
        self.assertEqual(found, [{"element": "Line", "id": "hd:LN_1", "holders": {"Name": "Maribor", "ShortName": "Ptuj"}}])
        problems = generator.shared_name_problems(SPLIT_LINE, self.VALUES, self.QUESTION)
        self.assertEqual(len(problems), 1)
        self.assertIn("Maribor and Ptuj from the question are written as the Name and ShortName of the one Line", problems[0])
        self.assertIn("link that object to the Line", problems[0])
        self.assertEqual(generator.error_class(problems[0]), "value")

    def test_name_and_description_count_too(self):
        fragment = SPLIT_LINE.replace("<ShortName>Ptuj</ShortName>", "").replace(
            "School days only, low-floor vehicles", "Ptuj")
        self.assertEqual(generator.shared_name_values(fragment, self.VALUES, self.QUESTION)[0]["holders"],
                         {"Name": "Maribor", "Description": "Ptuj"})

    def test_each_value_in_its_own_object_is_clean(self):
        self.assertEqual(generator.shared_name_values(LINKED_LINE, self.VALUES, self.QUESTION), [])

    def test_a_field_the_question_names_does_not_count(self):
        question = 'Show a NeTEx example of a stop place "Celje Bus Station" with short name "Celje AP"'
        fragment = ('<SiteFrame version="1" id="hd:SF"><stopPlaces><StopPlace version="1" id="hd:SP"><Name>Celje Bus Station'
                    "</Name><ShortName>Celje AP</ShortName></StopPlace></stopPlaces></SiteFrame>")
        self.assertEqual(generator.shared_name_values(fragment, ["Celje Bus Station", "Celje AP"], question), [])

    def test_a_value_in_a_code_is_not_a_name(self):
        question = 'Show a NeTEx example of a line "12" named "City Express"'
        fragment = ('<ServiceFrame version="1" id="hd:SF"><lines><Line version="1" id="hd:LN"><Name>City Express</Name>'
                    "<PublicCode>12</PublicCode></Line></lines></ServiceFrame>")
        self.assertEqual(generator.shared_name_values(fragment, ["12", "City Express"], question), [])

    def test_a_joined_name_gets_the_own_object_advice(self):
        message = generator.missing_value_error("Maribor", self.QUESTION, JOINED_LINE, self.VALUES)
        self.assertTrue(message.startswith("the value Maribor from the question is missing"))
        self.assertIn("The Line's Name “Maribor - Ptuj” joins it with other values from the question", message)
        self.assertIn("give it its own object with Maribor as its Name, and link that object to the Line", message)

    def test_one_value_inside_a_longer_name_keeps_the_plain_message(self):
        fragment = JOINED_LINE.replace("Maribor - Ptuj", "Maribor bus line")
        message = generator.missing_value_error("Maribor", self.QUESTION, fragment, self.VALUES)
        self.assertNotIn("joins it", message)
        self.assertTrue(message.endswith("not part of a Name or Description text"))

    def test_the_value_rule_for_the_first_prompt(self):
        self.assertEqual(generator.values_rule([]), "")
        plain = generator.values_rule(["50"])
        self.assertIn("whole content of an element or attribute", plain)
        self.assertNotIn("two names of one object", plain)
        own = generator.values_rule(self.VALUES, "Line", own_objects=True)
        self.assertIn("are not two names of one object", own)
        self.assertIn("link those objects to the Line.", own)

    def test_benchmark_counts_the_split(self):
        from helpdesk.management.commands.run_example_benchmark import summarize

        rows = [
            {"valid": True, "origin": "generated", "attempts": 3, "xml": SPLIT_LINE, "question": self.QUESTION},
            {"valid": True, "origin": "generated", "attempts": 1, "xml": LINKED_LINE, "question": self.QUESTION,
             "unlinkedObjects": [{"element": "VehicleType", "id": "a"}]},
            {"valid": True, "origin": "standard", "attempts": 3, "xml": SPLIT_LINE, "question": self.QUESTION},
        ]
        summary = summarize(rows)
        self.assertEqual((summary["generated"], summary["unlinked"], summary["sharedName"]), (2, 1, 1))


@override_settings(LLM_ENABLED=True)
class SharedNameRetryTests(SimpleTestCase):
    """The split is a hard failure: retried, and never shown as the generated example."""

    QUESTION = LinkRetryTests.QUESTION
    setUp = LinkRetryTests.setUp
    _run = LinkRetryTests._run

    def test_the_split_is_retried_with_the_own_object_advice(self):
        result, ask = self._run([SPLIT_LINE, LINKED_LINE])
        self.assertIn("has one name", ask.call_args_list[1].args[0][-1]["content"])
        self.assertEqual((result["valid"], result["origin"], result["attempts"]), (True, "generated", 2))
        self.assertEqual(result["attemptLog"][0]["errorClass"], "value")

    def test_a_split_on_every_attempt_is_not_shown(self):
        result, _ = self._run([SPLIT_LINE] * generator.MAX_ATTEMPTS)
        self.assertFalse(result.get("valid") and result.get("origin") == "generated")
        self.assertEqual([entry["errorClass"] for entry in result["attemptLog"]], ["value"] * generator.MAX_ATTEMPTS)

    def test_the_first_prompt_says_where_the_values_go(self):
        with patch.object(generator, "value_holders", return_value=[]):
            _, ask = self._run([LINKED_LINE])
        prompt = ask.call_args_list[0].args[0][1]["content"]
        self.assertIn("whole content of an element or attribute", prompt)
        self.assertIn("are not two names of one object", prompt)


@override_settings(LLM_ENABLED=True)
class OrderRepairGenerationTests(SimpleTestCase):
    """The generator goes on with the validator's repaired frame (plan 2026-11-12 revision 3, S2)."""

    QUESTION = LinkRetryTests.QUESTION
    setUp = LinkRetryTests.setUp

    def test_a_repaired_attempt_is_accepted_with_the_repaired_frame(self):
        repaired = {"valid": True, "errors": [], "repaired": "order", "fragment": LINKED_LINE, "repairedErrors": ["line 1: …"]}
        written = LINKED_LINE.replace("<LowFloor>true</LowFloor>", "<LowFloor>true</LowFloor>")  # what the model sent
        with patch.object(generator, "_ask_model", return_value=_reply(written)) as ask, patch.object(
            generator, "validate_fragment", return_value=repaired
        ), patch.object(generator, "asked_object_problem", return_value=""):
            result = generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        self.assertEqual((result["valid"], result["origin"], result["attempts"]), (True, "generated", 1))
        self.assertEqual(result["attemptLog"][0]["repaired"], "order")
        self.assertEqual(result["xml"], generator.indented_fragment(LINKED_LINE))
        self.assertEqual(ask.call_count, 1)

    def test_later_feedback_shows_the_model_the_repaired_frame(self):
        split = {"valid": True, "errors": [], "repaired": "order", "fragment": SPLIT_LINE}
        with patch.object(generator, "_ask_model", side_effect=[_reply(JOINED_LINE), _reply(LINKED_LINE)]) as ask, patch.object(
            generator, "validate_fragment", side_effect=[split, {"valid": True, "errors": []}]
        ), patch.object(generator, "asked_object_problem", return_value=""):
            result = generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        history = ask.call_args_list[1].args[0]
        self.assertEqual(json.loads(history[-2]["content"])["xml"], SPLIT_LINE)
        self.assertIn("has one name", history[-1]["content"])
        self.assertEqual([entry.get("repaired", "") for entry in result["attemptLog"]], ["order", ""])

    def test_a_sorted_but_invalid_frame_is_what_the_model_sees_next(self):
        # Plan 2026-11-13, A1: sorted with another problem left; the next turn starts from the sorted frame.
        sorted_frame = {"valid": False, "errors": ["line 1: Element 'Line': Missing child element(s)."],
                        "diagnostics": [{"kind": "missing-required", "element": "Line", "detail": "`Line` is missing the required Name."}],
                        "repaired": ["order"], "fragment": LINKED_LINE}
        with patch.object(generator, "_ask_model", side_effect=[_reply(JOINED_LINE), _reply(LINKED_LINE)]) as ask, patch.object(
            generator, "validate_fragment", side_effect=[sorted_frame, {"valid": True, "errors": []}]
        ), patch.object(generator, "asked_object_problem", return_value=""):
            result = generator.generate_netex_example(self.QUESTION, [NETEX_CHUNK], ["NeTEx"])
        history = ask.call_args_list[1].args[0]
        self.assertEqual(json.loads(history[-2]["content"])["xml"], LINKED_LINE)
        self.assertIn("missing the required Name", history[-1]["content"])
        first = result["attemptLog"][0]
        self.assertEqual((first["repaired"], first["errorClass"], first["fragment"]), ("order", "missing-required", JOINED_LINE))

    def test_benchmark_counts_repaired_attempts(self):
        from helpdesk.management.commands.run_example_benchmark import summarize

        rows = [{"valid": True, "attempts": 2, "attemptLog": [
            {"parsed": "json", "errorClass": "wrong-parent", "repaired": "order"},
            {"parsed": "json", "errorClass": "", "repaired": "order"}]}]
        self.assertEqual((summarize(rows)["repairedOrder"], summarize(rows)["repairedOrderFailed"]), (2, 1))


SERVICE_JOURNEY_EXAMPLE = (
    '<CompositeFrame xmlns="http://www.netex.org.uk/netex" id="c"><frames><TimetableFrame id="t"><vehicleJourneys>'
    '<ServiceJourney id="sj"><Name>Morning</Name><dayTypes><DayTypeRef ref="d"/></dayTypes>'
    '<JourneyPatternView><LineRef ref="l"/></JourneyPatternView>'
    '<calls><Call id="c1"><ScheduledStopPointRef ref="a"/><Arrival><Time>08:00:00</Time></Arrival></Call>'
    '<Call id="c2"><ScheduledStopPointRef ref="b"/></Call></calls></ServiceJourney>'
    "</vehicleJourneys></TimetableFrame></frames></CompositeFrame>"
)


class LinkShapeTests(SimpleTestCase):
    """Plan 2026-11-12 revision 2, R3: the link feedback says where the linking object sits and shows its shape."""

    def test_place_and_shape_of_the_linking_object(self):
        from lxml import etree

        root = etree.fromstring(SERVICE_JOURNEY_EXAMPLE)
        journey = root.find(".//{*}ServiceJourney")
        shape = generator._holder_shape(
            journey, [["calls", "Call", "ScheduledStopPointRef"], ["JourneyPatternView", "LineRef"]], required=lambda path: []
        )
        self.assertEqual(shape["place"], ["TimetableFrame", "vehicleJourneys"])
        self.assertEqual(shape["excerpt"], (
            '<ServiceJourney id="sj">\n  <JourneyPatternView>\n    <LineRef ref="l"/>\n  </JourneyPatternView>\n'
            '  <calls>\n    <Call id="c1">\n      <ScheduledStopPointRef ref="a"/>\n    </Call>\n  </calls>\n</ServiceJourney>'
        ))
        self.assertIsNotNone(root.find(".//{*}Name"))  # the example itself is not changed

    def test_the_feedback_names_the_place_and_shows_the_shape_once(self):
        bridge = {"holder": "ServiceJourney", "toElement": ["calls", "Call", "ScheduledStopPointRef"],
                  "toAsked": ["JourneyPatternView", "LineRef"], "sourcePath": "examples/a.xml", "files": 3,
                  "place": ["TimetableFrame", "vehicleJourneys"], "excerpt": "<ServiceJourney>…</ServiceJourney>"}
        found = {**bridge, "holders": {"ServiceJourney": bridge}}
        with patch.object(generator, "link_example", return_value=found):
            problems = generator.link_problems(UNLINKED_LINE, "Line", LinkRetryTests.QUESTION, ["Maribor", "Ptuj"])
        self.assertTrue(all("where the example has it: TimetableFrame > vehicleJourneys > ServiceJourney" in p for p in problems))
        self.assertEqual(sum("Its shape there" in p for p in problems), 1)
        self.assertEqual(generator.error_class(problems[0]), "link")


STOP_ASSIGNMENT_JOURNEY = (
    '<ServiceJourney xmlns="http://www.netex.org.uk/netex" id="sj"><LineRef ref="l"/><calls>'
    '<Call id="c1"><ScheduledStopPointRef ref="a"/><Arrival><ForAlighting>false</ForAlighting>'
    '<QuayAssignmentView><StopPlaceRef ref="sp"/><QuayName>Platform 4</QuayName></QuayAssignmentView></Arrival>'
    '<Departure><Time>14:20:00</Time></Departure></Call></calls></ServiceJourney>'
)
UNLINKED_STOP_PLACES = (
    '<CompositeFrame version="1.0" id="hd:CF"><frames>'
    '<SiteFrame version="1.0" id="hd:SF"><stopPlaces><StopPlace version="1.0" id="hd:SP_Maribor"><Name>Maribor</Name>'
    '</StopPlace></stopPlaces></SiteFrame>'
    '<ServiceFrame version="1.0" id="hd:SVF"><lines><Line version="1.0" id="hd:LN"><Name>Maribor - Ptuj</Name></Line>'
    "</lines></ServiceFrame></frames></CompositeFrame>"
)


class LinkShapeRequiredTests(SimpleTestCase):
    """Plan 2026-11-13, B1: the excerpt keeps the children the schema requires at every kept element."""

    TO_STOP_PLACE = ["calls", "Call", "Arrival", "QuayAssignmentView", "StopPlaceRef"]

    def test_a_required_sibling_of_the_path_is_kept(self):
        from lxml import etree

        required = lambda path: [(frozenset({"ScheduledStopPointRef", "ScheduledStopPointView"}), 1)] if path[-1] == "Call" else []  # noqa: E731
        shape = generator._holder_shape(etree.fromstring(STOP_ASSIGNMENT_JOURNEY), [self.TO_STOP_PLACE, ["LineRef"]], required=required)
        self.assertIn('<ScheduledStopPointRef ref="a"/>', shape["excerpt"])
        self.assertNotIn("ForAlighting", shape["excerpt"])  # optional children still go
        self.assertNotIn("Departure", shape["excerpt"])
        self.assertEqual(shape["requiredRefs"], [{"parent": "Call", "ref": "ScheduledStopPointRef"}])

    def test_a_required_slot_the_paths_fill_adds_nothing(self):
        from lxml import etree

        required = lambda path: [(frozenset({"ScheduledStopPointRef"}), 1)] if path[-1] == "Call" else []  # noqa: E731
        shape = generator._holder_shape(
            etree.fromstring(STOP_ASSIGNMENT_JOURNEY), [["calls", "Call", "ScheduledStopPointRef"], ["LineRef"]], required=required
        )
        self.assertEqual(shape["requiredRefs"], [])
        self.assertEqual(shape["excerpt"].count("ScheduledStopPointRef"), 1)

    def test_the_feedback_says_which_object_a_required_reference_needs(self):
        bridge = {"holder": "ServiceJourney", "toElement": self.TO_STOP_PLACE, "toAsked": ["LineRef"],
                  "sourcePath": "examples/a.xml", "files": 1, "place": ["TimetableFrame", "vehicleJourneys"],
                  "excerpt": "<ServiceJourney>…</ServiceJourney>", "requiredRefs": [{"parent": "Call", "ref": "ScheduledStopPointRef"}]}
        found = {**bridge, "holders": {"ServiceJourney": bridge}}
        with patch.object(generator, "link_example", return_value=found):
            problems = generator.link_problems(UNLINKED_STOP_PLACES, "Line", LinkRetryTests.QUESTION, ["Maribor", "Ptuj"])
            self.assertIn("A Call also needs a ScheduledStopPointRef: define a ScheduledStopPoint for each Call and refer to it.", problems[0])
            # The fragment already defines one: nothing to add.
            defined = UNLINKED_STOP_PLACES.replace(
                "</lines>", '</lines><scheduledStopPoints><ScheduledStopPoint version="1.0" id="hd:SSP"/></scheduledStopPoints>'
            )
            problems = generator.link_problems(defined, "Line", LinkRetryTests.QUESTION, ["Maribor", "Ptuj"])
        self.assertNotIn("also needs", " ".join(problems))

    def test_the_sentence_comes_also_when_the_shape_was_shown_for_another_kind(self):
        vehicle = {"holder": "ServiceJourney", "toElement": ["VehicleTypeRef"], "toAsked": ["LineRef"], "sourcePath": "examples/v.xml",
                   "files": 2, "place": ["TimetableFrame", "vehicleJourneys"], "excerpt": "<ServiceJourney>…</ServiceJourney>",
                   "requiredRefs": []}
        stop = {**vehicle, "toElement": self.TO_STOP_PLACE, "sourcePath": "examples/s.xml",
                "requiredRefs": [{"parent": "Call", "ref": "ScheduledStopPointRef"}]}
        examples = {"VehicleType": {**vehicle, "holders": {"ServiceJourney": vehicle}},
                    "StopPlace": {**stop, "holders": {"ServiceJourney": stop}}}
        # The VehicleType comes first, so its line shows the ServiceJourney's shape.
        fragment = UNLINKED_STOP_PLACES.replace(
            "<frames>", '<frames><ResourceFrame version="1.0" id="hd:RF"><vehicleTypes><VehicleType version="1.0" id="hd:VT">'
            "<Name>Low-floor bus</Name></VehicleType></vehicleTypes></ResourceFrame>"
        )
        with patch.object(generator, "link_example", side_effect=lambda element, asked: examples[element]):
            problems = generator.link_problems(fragment, "Line", LinkRetryTests.QUESTION, ["Maribor", "Ptuj"])
        self.assertEqual([("Its shape there" in p, "A Call also needs a ScheduledStopPointRef" in p) for p in problems],
                         [(True, False), (False, True)])

    def test_the_standard_example_excerpt_keeps_the_stop_point_reference(self):
        """Against the NeTEx checkout: the excerpt of Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml's
        ServiceJourney (StopPlace <-> Line) has a valid shape, its Call with the ScheduledStopPointRef."""
        import os

        from lxml import etree

        from helpdesk.netex_content_model import ContentModels

        checkout = Path(os.environ.get("NETEX_VALIDATOR_CHECKOUT", "/app/repos/NeTEx"))
        path = checkout / "examples/functions/timetable/Netex_01.5_Bus_SimpleTimetable_StopAssignment.xml"
        if not path.is_file() or not (checkout / "xsd").is_dir():
            self.skipTest("no NeTEx checkout")
        models = ContentModels()
        models.load_directory(checkout / "xsd")
        required = lambda steps: [(frozenset(s.names), s.min) for s in models.slots(models.type_at(list(steps))) if s.min >= 1]  # noqa: E731
        journey = etree.parse(str(path)).getroot().find(".//{*}ServiceJourney")
        shape = generator._holder_shape(journey, [self.TO_STOP_PLACE, ["LineRef"]], required=required)
        self.assertIn("ScheduledStopPointRef", shape["excerpt"])
        excerpt = etree.fromstring(shape["excerpt"].replace("<ServiceJourney", '<ServiceJourney xmlns="http://www.netex.org.uk/netex"', 1))
        for node in excerpt.iter():
            names = [etree.QName(child).localname for child in node]
            steps = [etree.QName(n).localname for n in reversed([node, *node.iterancestors()])]
            self.assertEqual(models.match_children(models.type_at(steps), names), [], steps)


PLACEMENT_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.netex.org.uk/netex"
  targetNamespace="http://www.netex.org.uk/netex" elementFormDefault="qualified" version="2.0">
  <xsd:element name="PublicationDelivery">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="PublicationTimestamp" type="xsd:dateTime"/>
      <xsd:element name="ParticipantRef" type="xsd:string"/>
      <xsd:element name="dataObjects"><xsd:complexType><xsd:choice maxOccurs="unbounded">
        <xsd:element ref="CompositeFrame"/><xsd:element ref="ServiceFrame"/><xsd:element ref="SiteFrame"/>
      </xsd:choice></xsd:complexType></xsd:element>
    </xsd:sequence><xsd:attribute name="version" type="xsd:string"/></xsd:complexType>
  </xsd:element>
  <xsd:attributeGroup name="Ids"><xsd:attribute name="id" type="xsd:string"/><xsd:attribute name="version" type="xsd:string"/></xsd:attributeGroup>
  <xsd:element name="CompositeFrame"><xsd:complexType><xsd:sequence>
    <xsd:element name="frames" minOccurs="0"><xsd:complexType><xsd:choice maxOccurs="unbounded">
      <xsd:element ref="ServiceFrame"/><xsd:element ref="SiteFrame"/>
    </xsd:choice></xsd:complexType></xsd:element>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:element name="ServiceFrame"><xsd:complexType><xsd:sequence>
    <xsd:element name="operators" type="operators_RelStructure" minOccurs="0"/>
    <xsd:element name="lines" minOccurs="0"><xsd:complexType><xsd:sequence>
      <xsd:element ref="Line" maxOccurs="unbounded"/>
    </xsd:sequence></xsd:complexType></xsd:element>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:element name="SiteFrame"><xsd:complexType><xsd:sequence>
    <xsd:element name="operators" type="operators_RelStructure" minOccurs="0"/>
    <xsd:element name="stopPlaces" minOccurs="0"><xsd:complexType><xsd:sequence>
      <xsd:element ref="StopPlace" maxOccurs="unbounded"/>
    </xsd:sequence></xsd:complexType></xsd:element>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:complexType name="operators_RelStructure"><xsd:sequence>
    <xsd:element ref="Operator" maxOccurs="unbounded"/>
  </xsd:sequence></xsd:complexType>
  <xsd:element name="Line"><xsd:complexType><xsd:sequence>
    <xsd:element name="Name" type="xsd:string"/>
    <xsd:element name="OperatorRef" type="Reference" minOccurs="0" maxOccurs="unbounded"/>
    <xsd:element name="QuayRef" type="Reference" minOccurs="0"/>
    <xsd:element name="StopPlaceRef" type="Reference" minOccurs="0"/>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:complexType name="Reference"><xsd:attribute name="ref" type="xsd:string"/><xsd:attribute name="version" type="xsd:string"/></xsd:complexType>
  <xsd:element name="Operator"><xsd:complexType><xsd:sequence>
    <xsd:element name="Name" type="xsd:string"/>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:element name="StopPlace"><xsd:complexType><xsd:sequence>
    <xsd:element name="Name" type="xsd:string"/>
    <xsd:element name="quays" minOccurs="0"><xsd:complexType><xsd:sequence>
      <xsd:element ref="Quay" maxOccurs="unbounded"/>
    </xsd:sequence></xsd:complexType></xsd:element>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
  <xsd:element name="Quay"><xsd:complexType><xsd:sequence>
    <xsd:element name="Name" type="xsd:string"/>
  </xsd:sequence><xsd:attributeGroup ref="Ids"/></xsd:complexType></xsd:element>
</xsd:schema>
"""

PLACEMENT_EXAMPLE = (
    '<PublicationDelivery xmlns="http://www.netex.org.uk/netex"><dataObjects><CompositeFrame id="c"><frames>'
    '<SiteFrame id="s"><operators><Operator id="o1"/></operators><stopPlaces><StopPlace id="sp1"/><StopPlace id="sp2"/>'
    '<StopPlace id="sp3"/></stopPlaces></SiteFrame>'
    '<ServiceFrame id="f"><operators><Operator id="o2"/></operators><lines><Line id="l1"/></lines>'
    # Placed where the schema has no such list: not a placement.
    '<stopPlaces><StopPlace id="sp9"/><StopPlace id="sp8"/><StopPlace id="sp7"/><StopPlace id="sp6"/></stopPlaces>'
    "</ServiceFrame></frames></CompositeFrame></dataObjects></PublicationDelivery>"
)


class PlacementRepairTests(SimpleTestCase):
    """Plan 2026-11-13, A2: objects in the wrong frame or list go where the standard's examples put them."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        checkout = Path(directory.name)
        (checkout / "xsd").mkdir()
        (checkout / service.SCHEMA_ENTRY).write_text(PLACEMENT_XSD)
        (checkout / "examples").mkdir()
        (checkout / "examples" / "a.xml").write_text(PLACEMENT_EXAMPLE)
        self.holder = service.SchemaHolder(checkout)
        self.holder.load()

    def test_placements_are_the_examples_confirmed_by_the_schema(self):
        models = self.holder.content
        self.assertEqual(models.placement("StopPlace"), ("SiteFrame", "stopPlaces"))  # 3 there, 4 in a list ServiceFrame lacks
        self.assertEqual(models.placement("Line"), ("ServiceFrame", "lines"))
        # Operator: once in each frame, so its place is not clear unless the draft has one of the frames.
        self.assertIsNone(models.placement("Operator"))
        self.assertEqual(models.placement("Operator", {"ServiceFrame"}), ("ServiceFrame", "operators"))
        self.assertIsNone(models.placement("Quay"))  # only nested in the examples

    def test_a_list_in_the_wrong_frame_moves_to_a_new_frame(self):
        result = self.holder.validate(
            '<ServiceFrame version="2" id="f"><stopPlaces><StopPlace version="2" id="sp"><Name>Koper</Name><quays>'
            '<Quay id="q"><Name>1</Name></Quay></quays></StopPlace></stopPlaces>'
            '<lines><Line id="l"><Name>Koper - Piran</Name></Line></lines></ServiceFrame>'
        )
        self.assertEqual((result["valid"], result["repaired"]), (True, ["placement"]))
        self.assertEqual(result["fragment"], (
            '<CompositeFrame version="2" id="hd:CompositeFrame_1"><frames>'
            '<ServiceFrame version="2" id="f"><lines><Line id="l"><Name>Koper - Piran</Name></Line></lines></ServiceFrame>'
            '<SiteFrame version="2" id="hd:SiteFrame_1"><stopPlaces><StopPlace version="2" id="sp"><Name>Koper</Name><quays>'
            '<Quay id="q"><Name>1</Name></Quay></quays></StopPlace></stopPlaces></SiteFrame></frames></CompositeFrame>'
        ))

    def test_a_frame_the_moves_empty_is_removed_and_an_existing_frame_is_used(self):
        result = self.holder.validate('<ServiceFrame id="f"><stopPlaces><StopPlace id="sp"><Name>Koper</Name></StopPlace></stopPlaces></ServiceFrame>')
        self.assertEqual(result["fragment"], '<SiteFrame version="1" id="hd:SiteFrame_1"><stopPlaces><StopPlace id="sp"><Name>Koper</Name></StopPlace></stopPlaces></SiteFrame>')
        result = self.holder.validate(
            '<CompositeFrame id="c"><frames><SiteFrame id="s"><lines><Line id="l"><Name>A</Name></Line></lines>'
            '<stopPlaces><StopPlace id="sp"><Name>B</Name></StopPlace></stopPlaces></SiteFrame>'
            '<ServiceFrame id="f"><operators><Operator id="o"><Name>C</Name></Operator></operators></ServiceFrame></frames></CompositeFrame>'
        )
        self.assertTrue(result["valid"], result)
        self.assertIn('<ServiceFrame id="f"><operators><Operator id="o"><Name>C</Name></Operator></operators><lines><Line id="l">', result["fragment"])

    def test_what_the_schema_accepts_or_has_no_place_is_left_alone(self):
        from lxml import etree

        models = self.holder.content
        # An Operator directly in dataObjects with no frame of either kind: its place is not clear.
        document = etree.fromstring(service.wrap_fragment('<Operator id="o"><Name>C</Name></Operator>').encode())
        self.assertFalse(service.repair_placement(models, document))
        # Accepted where it is: an Operator in the SiteFrame stays though the draft also has a ServiceFrame.
        fragment = ('<SiteFrame id="s"><operators><Operator id="o"><Name>C</Name></Operator></operators></SiteFrame>'
                    '<ServiceFrame id="f"><lines><Line id="l"><Name>A</Name></Line></lines></ServiceFrame>')
        document = etree.fromstring(service.wrap_fragment(fragment).encode())
        self.assertFalse(service.repair_placement(models, document))
        # The Operator directly in dataObjects, with a ServiceFrame in the draft: into it.
        result = self.holder.validate('<ServiceFrame id="f"><lines><Line id="l"><Name>A</Name></Line></lines></ServiceFrame><Operator id="o"><Name>C</Name></Operator>')
        self.assertEqual((result["valid"], result["repaired"]), (True, ["placement", "order"]))
        self.assertEqual(result["fragment"], '<ServiceFrame id="f"><operators><Operator id="o"><Name>C</Name></Operator></operators><lines><Line id="l"><Name>A</Name></Line></lines></ServiceFrame>')

    def test_references_follow_their_target(self):
        # Plan 2026-11-13, A3: the version of the target, and the reference element of the target's kind where the
        # parent has one; a reference to an object outside the draft, or to a kind the parent has no reference
        # for, is left as written.
        from lxml import etree

        fragment = (
            '<SiteFrame version="1" id="s"><operators><Operator version="2" id="o"><Name>C</Name></Operator></operators>'
            '<stopPlaces><StopPlace version="3" id="sp"><Name>B</Name><quays><Quay id="q"><Name>1</Name></Quay></quays>'
            "</StopPlace></stopPlaces></SiteFrame>"
            '<ServiceFrame id="f"><lines><Line version="1" id="l"><Name>A</Name><OperatorRef version="1" ref="o"/>'
            '<AuthorityRef version="1" ref="o"/><QuayRef version="1" ref="sp"/><StopPlaceRef ref="elsewhere"/></Line></lines></ServiceFrame>'
        )
        document = etree.fromstring(service.wrap_fragment(fragment).encode())
        self.assertTrue(service.repair_references(self.holder.content, document))
        line = document.find(".//{*}Line")
        self.assertEqual(
            [(etree.QName(n).localname, n.get("version")) for n in line if n.get("ref")],
            # AuthorityRef: undeclared, and Line has an OperatorRef: renamed. QuayRef points to a StopPlace, which
            # Line has no reference for: left (only its version follows).
            [("OperatorRef", "2"), ("OperatorRef", "2"), ("QuayRef", "3"), ("StopPlaceRef", None)],
        )


class BenchmarkViaApiTests(SimpleTestCase):
    """Plan 2026-11-13, step C: the benchmark can ask through the app's answer endpoint."""

    def test_the_example_comes_from_the_answer_response(self):
        from io import BytesIO

        from helpdesk.management.commands import run_example_benchmark as bench

        class Response(BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        sent = {}

        def urlopen(http_request, timeout=0):
            sent.update(url=http_request.full_url, body=json.loads(http_request.data), headers=dict(http_request.header_items()))
            return Response(json.dumps({"answer": "…", "generatedExample": {"valid": True, "origin": "generated", "attempts": 2}}).encode())

        with patch("urllib.request.urlopen", side_effect=urlopen):
            result = bench.example_via_api("Show a NeTEx example of a Line", "http://app/api/v1/", "tok", "bench-1")
        self.assertEqual(result, {"valid": True, "origin": "generated", "attempts": 2})
        self.assertEqual(sent["url"], "http://app/api/v1/questions/answer")
        self.assertEqual(sent["body"], {"question": "Show a NeTEx example of a Line"})
        self.assertEqual((sent["headers"]["Authorization"], sent["headers"]["X-request-id"]), ("Bearer tok", "bench-1"))

    def test_an_answer_without_an_example_is_a_failed_run(self):
        from io import BytesIO

        from helpdesk.management.commands import run_example_benchmark as bench

        class Response(BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch("urllib.request.urlopen", return_value=Response(b'{"answer": "no example"}')):
            result = bench.example_via_api("q", "http://app/api/v1", "tok", "bench-2")
        self.assertEqual((result["valid"], result["attempts"]), (False, 0))


# The validator's /concrete answers for the element names the count tests look up: objects, a property, and
# names the schema does not have (prod question "a line with 2 service journeys", 2026-11-13).
_CONCRETE = {
    "ServiceJourney": [{"name": "ServiceJourney", "object": True}],
    "Deck": [{"name": "Deck", "object": True}],
    "Quay": [{"name": "Quay", "object": True}],
    "Journey": [{"name": "VehicleJourney", "object": True}, {"name": "ServiceJourney", "object": True}],
    "Departure": [{"name": "Departure", "object": False}],
}
LINE_WITH_JOURNEYS = (
    '<TimetableFrame version="1" id="hd:TF"><vehicleJourneys>'
    '<ServiceJourney version="1" id="hd:SJ1"><LineRef ref="hd:L"/></ServiceJourney>'
    '<ServiceJourney version="1" id="hd:SJ2"><LineRef ref="hd:L"/></ServiceJourney>'
    "</vehicleJourneys></TimetableFrame>"
)
ONE_JOURNEY_AND_A_STRAY_2 = (
    '<TimetableFrame version="1" id="hd:TF"><Description>2</Description><vehicleJourneys>'
    '<ServiceJourney version="1" id="hd:SJ1"><LineRef ref="hd:L"/></ServiceJourney>'
    "</vehicleJourneys></TimetableFrame>"
)


@override_settings(LLM_ENABLED=True)
class ObjectCountTests(SimpleTestCase):
    """A number in digits before a kind of object is how many of it to write, not a value to place."""

    def setUp(self):
        for target, value in (("helpdesk.services.semantic_graph.GRAPH_CONCEPT_ALIASES", {}),):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(generator, "concrete_elements", side_effect=lambda name: _CONCRETE.get(name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_number_before_a_kind_of_object_is_a_count(self):
        self.assertEqual(
            generator.object_counts("Show me a NeTEx example for a line with 2 service journeys."),
            [(2, "2", "service journeys", ["ServiceJourney"])],
        )
        self.assertEqual(generator.object_counts("a vehicle type with a deck plan of 2 decks"), [(2, "2", "decks", ["Deck"])])
        # An abstract element stands for its concrete objects.
        self.assertEqual(generator.object_counts("a line with 3 journeys")[0][3], ["VehicleJourney", "ServiceJourney"])

    def test_a_number_before_a_value_or_unknown_words_is_a_value(self):
        for question in (
            "Show me a NeTEx example for a bus with 50 seats and 20 standing places",
            "Show a NeTEx example of a coach with 49 seats and 1 wheelchair area",
            "Show me a NeTEx example of a parking with 120 spaces",
            "Show a NeTEx example of a tram vehicle type with a length of 32 metres",
            "Create a NeTEx XML example for a fare product for adult for 5 EUR.",
            "a line with 2 departures",  # Departure is a property, not an object
            'Show a NeTEx example of a service journey on line "12" that runs only on public holidays.',
            "A TemplateServiceJourney every 10 minutes between 06:00 and 22:00",
        ):
            self.assertEqual(generator.object_counts(question), [], question)

    def test_number_words_are_left_as_they_were(self):
        # "two quays" was never a value; only digits are taken out of the values.
        self.assertEqual(generator.object_counts("a stop place with two quays"), [])

    def test_a_count_is_taken_out_of_the_values(self):
        question = "Show me a NeTEx example for a line with 2 service journeys."
        counts = generator.object_counts(question)
        self.assertEqual(generator.counted_out(generator.requested_values(question), question, counts), [])
        # The same number also given as a value stays a value.
        question = "a line 2 with 2 service journeys"
        self.assertEqual(generator.counted_out(["2"], question, generator.object_counts(question)), ["2"])
        bus = "a bus with 50 seats and 20 standing places"
        self.assertEqual(generator.counted_out(generator.requested_values(bus), bus, generator.object_counts(bus)), ["50", "20"])

    def test_the_count_is_checked_as_objects_in_one_parent(self):
        counts = generator.object_counts("a line with 2 service journeys")
        self.assertEqual(generator.count_problems(LINE_WITH_JOURNEYS, counts), [])
        places = generator.object_count_places(LINE_WITH_JOURNEYS, counts)
        self.assertEqual([(p["value"], p["element"], p["count"], p["path"]) for p in places],
                         [("2", "ServiceJourney", 2, ["TimetableFrame", "vehicleJourneys"])])
        problems = generator.count_problems(ONE_JOURNEY_AND_A_STRAY_2, counts)
        self.assertEqual(len(problems), 1)
        self.assertIn("write exactly 2 ServiceJourney objects", problems[0])
        self.assertEqual(generator.error_class(problems[0]), "count")

    def test_generation_asks_for_the_objects_not_the_value(self):
        question = "Show me a NeTEx example for a line with 2 service journeys."
        with patch.object(generator, "_ask_model", side_effect=[_reply(ONE_JOURNEY_AND_A_STRAY_2), _reply(LINE_WITH_JOURNEYS)]) as ask, \
                patch.object(generator, "validate_fragment", return_value={"valid": True, "errors": []}), \
                patch.object(generator, "asked_element", return_value=""), \
                patch.object(generator, "asked_from_parts", return_value=("", [])), \
                patch.object(generator, "_from_standard", return_value=None), \
                patch.object(generator, "schema_declarations", return_value=[]), \
                patch.object(generator, "value_element_declarations", return_value=[]):
            result = generator.generate_netex_example(question, [NETEX_CHUNK], ["NeTEx"])
        prompt = ask.call_args_list[0].args[0][1]["content"]
        self.assertIn("Objects to write, each defined with its own id: 2 ServiceJourney", prompt)
        self.assertNotIn("Write each value as the whole content", prompt)
        self.assertEqual((result["valid"], result["attempts"]), (True, 2))
        self.assertEqual(result["attemptLog"][0]["errorClass"], "count")
        self.assertEqual([(p["value"], p["element"]) for p in result["valuePlaces"]], [("2", "ServiceJourney")])


@override_settings(LLM_ENABLED=True)
class NamedObjectPartTests(SimpleTestCase):
    """A part the question names by an object's element name must be defined in the frame."""

    def setUp(self):
        concrete = {**_CONCRETE, "StopPlace": [{"name": "StopPlace", "object": True}], "WaitTime": [{"name": "WaitTime", "object": False}]}
        patcher = patch.object(generator, "concrete_elements", side_effect=lambda name: concrete.get(name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_part_named_by_an_object_element_is_found(self):
        question = "Show me an example of line with a stop place departure described in NeTEx XML?"
        self.assertEqual(generator.named_object_parts(question, "Line"), [("stop place", ["StopPlace"])])
        self.assertEqual(generator.parts_line([("stop place", ["StopPlace"])]), "StopPlace (“stop place”)")

    def test_a_property_unknown_words_and_the_asked_object_are_not_parts(self):
        self.assertEqual(generator.named_object_parts("a ServiceJourney with a wait time of 30 seconds", "ServiceJourney"), [])
        self.assertEqual(generator.named_object_parts("a sales offer package with a price of 10 EUR", "SalesOfferPackage"), [])
        self.assertEqual(generator.named_object_parts("a stop place with a quay", "Quay"), [])

    def test_a_frame_without_the_part_gets_feedback(self):
        parts = [("stop place", ["StopPlace"])]
        line_only = '<ServiceFrame version="1" id="hd:SF"><lines><Line version="1" id="hd:L"><Name>Line 1</Name></Line></lines></ServiceFrame>'
        problems = generator.part_problems(line_only, parts, "Line")
        self.assertEqual(len(problems), 1)
        self.assertIn("defines no StopPlace", problems[0])
        self.assertEqual(generator.error_class(problems[0]), "part")
        with_stop = '<SiteFrame version="1" id="hd:S"><stopPlaces><StopPlace version="1" id="hd:SP"/></stopPlaces></SiteFrame>'
        self.assertEqual(generator.part_problems(with_stop, parts, "Line"), [])
        # A reference alone does not define the part.
        ref_only = '<ServiceFrame version="1" id="hd:SF"><StopPlaceRef ref="x"/></ServiceFrame>'
        self.assertEqual(len(generator.part_problems(ref_only, parts, "Line")), 1)
