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
        <xsd:element ref="FareFrame"/>
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
        found = self.kinds('<FareFrame id="f"><passingTimes><PassingTime><StopPointRef>s</StopPointRef></PassingTime></passingTimes><prices><FareProductPrice/></prices></FareFrame>')
        self.assertIn("`prices` is out of order in `FareFrame`", found["order"]["detail"])
        found = self.kinds('<FareFrame id="f"><prices><FareProductPrice><Amount>5</Amount></FareProductPrice><Amount>5</Amount></prices></FareFrame>')
        self.assertIn("`Amount` is not a child of `prices`; it belongs under one of:", found["wrong-parent"]["detail"])
        self.assertIn("FareProductPrice", found["wrong-parent"]["detail"])
        found = self.kinds('<FareFrame id="f"><prices><PriceList/></prices></FareFrame>')
        self.assertIn("`PriceList` is not an element of the NeTEx schema", found["undeclared"]["detail"])

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
        ), patch.object(generator, "_ask_model", side_effect=[_reply(FRAME), _reply(FRAME)]) as ask, patch.object(
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
