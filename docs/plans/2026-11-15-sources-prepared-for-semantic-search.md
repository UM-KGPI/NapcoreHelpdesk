# Plan: all sources prepared for semantic search, with the graph

Written 2026-11-15 against 0.97.226, for the implementer. It follows two records in
`2026-11-15-xml-example-chunks.md` §8 (PR #540): R0, the element cut of XML examples measured on copies of the dev
database, and the audit of every source kind. Their numbers are used here and not repeated in full.
Each claim is labelled **measured**, **believed** or **assumed**.

## 1. The problem

Every source is searched by meaning, but most pieces are not prepared for it. The embedder reads the first 256
tokens of a piece, and most pieces are longer, so a vector describes the beginning of a piece and not the piece.
The search then cannot tell the pieces of one file apart, and the model is given the wrong one.

R0 tried to repair one kind (XML examples) by itself. It fixed the case it was built for and failed its gate,
because the better example pieces pushed schema declarations and READMEs out of the six passages the model reads.
The fault is not in one kind. It is in how all kinds are cut, sized and chosen together, so this plan treats them
together and re-indexes once.

## 2. What is known

- **Measured** (audit): the embedder is `multilingual-e5-small`, input cut at 256 tokens. Share of pieces longer
  than that: XML examples 99 %, NAPCORE pages 94 %, NeTEx text examples 91 %, DATEX II pages 58 %, TN-ITS 53 %,
  INSPIRE 49 %, mobilityDCAT-AP guide 44 %, EU legislation 37 %, DATEX II classes 21 %, READMEs 18 %, schema
  declarations 5 %. Of an XML example piece the embedder reads about 59 %.
- **Measured** (audit): the size limits are in characters (1,200 for examples, 1,500 for prose). 256 tokens are
  about 690 characters of XML; of English prose about 900 to 1,000 (**believed**).
- **Measured** (audit): the heading of a piece is embedded but not shown to the model. For an XML example there is
  no heading at all, and nothing says where in the document the piece sits.
- **Measured** (audit): 92 % of example pieces are cut inside an element. READMEs: pieces of one README are no
  closer to each other than to another README; 8 of 61 are headings without text. DATEX II pages: 74 exact
  duplicates.
- **Measured** (R0): with example pieces cut at element boundaries and a line giving the place in the document,
  the model gets the piece with the count element and answers the late-journeys question 3 of 3 times.
- **Measured** (R0): every variant loses 2 to 3 gold questions and 2 to 3 benchmark questions at file level. In
  the lost questions, example pieces take the places of the schema declaration or README the question file names.
- **Measured** (R0): the variant whose pieces fit the embedder (600 characters) answered most of the answerable
  questions (46 of 69 runs, baseline 40) and answered the fewest questions it must refuse (2 runs, baseline 4). It
  doubled the rows and lost most at file level. **Believed**: differences of this size are partly spread of three
  runs; the spread was not measured.
- **Believed** (a comment in the embedder's code, from the trial of 2026-10-25; not re-measured): reading 512
  tokens of a piece was no better than 256 and twice as slow. So the pieces must fit the embedder; the embedder is
  not made to read more.
- **Measured** (read in the code): the question's concepts are found by meaning (the concept vectors, 3,104
  classes) only for "does the standard have X" questions. Everywhere else the search finds concepts by the words
  of their labels.
- **Measured** (read in the code): the facts of the graph (definitions) are put in front of the passages and take
  some of the six places.
- **Not known**: how much the file-level measure punishes a good change. It counts a question as lost when a named
  file is no longer among the passages, also when another passage holds the same answer.
- **Not known**: the spread of each measure between two runs on the same index.

## 3. The design

1. **A piece is a unit of its source.** XML: whole elements (the cut of R0, which gives back every file exactly).
   Prose: section, then paragraph, then sentence. Schema: one declaration (as today). Turtle: one statement (as
   today). No piece begins or ends inside a unit unless the unit itself is larger than the limit.
2. **A piece fits what the embedder reads.** The limit is counted in tokens, with the embedder's own tokenizer, on
   exactly the text that is embedded. One limit for all kinds.
3. **A piece says where it sits.** One line of place: the path of elements from the root for XML, the path of
   headings for prose. It is embedded and it is shown to the model.
4. **Search small, read large.** The search works on the small pieces. The model is given the found piece together
   with as much of the unit around it as fits the room it has today (1,200 characters a passage). The index does
   not decide how much the model reads.
5. **The six places are shared among kinds of source.** No kind takes all the places while another kind has a
   candidate above the score limit. The rule is about kinds, not about any standard or file.
6. **The graph works with the vectors, in three places:**
   - at indexing, each piece gets the concepts of the ontology it is about (for XML from its element names, for
     prose from the labels and the concept vectors), stored beside the piece;
   - at the question, the concepts are found by meaning for every question, and the pieces that carry them are
     candidates. This replaces the search of paths by label words;
   - after the passages are chosen, the definitions and relations of their concepts are given to the model in a
     block of their own, beside the six passages and not in their place.

Relation questions keep using the graph as today. I do not measure the helpdesk with the graph switched off.

## 4. Principles

- **General.** No rule names an element, a standard, a file or a question.
- **Measured on copies first.** The dev index and the prod index are not rebuilt before the gates of steps 1 to 4
  are met. Copies are made as in R0, with the baseline on a copy as well.
- **One re-index** on dev and one on prod, for everything.
- **No added model call.** The app's models stay as they are.
- **Gates are fixed here** and not changed after the numbers are seen.

## 5. The yardstick

R0 showed that the file-level count alone cannot judge this change. The measures for every step:

- **Answers.** The 23 answerable and the 25 must-refuse questions, 3 runs each. Every answer that is new or
  changed is read against its passages.
- **Files.** Gold (57) and benchmark (141) at file level. Each question lost at file level is read: it counts as
  lost only if the passages given no longer hold what the named file holds for the question.
- **The case.** The late-journeys question, 3 runs, and the 7 questions with a better piece left out, read by hand.
- **Examples.** The example benchmark, all questions, 3 runs: generated, first attempts, linked objects.
- **Cost.** Rows, index size, embedding time, retrieval time.

"Not lower" means not lower than the baseline by more than the spread measured in step 0.

## 6. Steps

### Step 0. The yardstick and the facts (no index change, about 1 day)

- Measure the baseline copy twice, all measures of §5, to get the spread of each.
- Read the gold file once for questions where more than one source holds the answer, and name those sources.
  This is the review that is still open (12 entries marked unsure).
- Prod: free disk, memory of the database container, and the per-file limit set there. Rows will about double
  (**believed**, from R0's 600-character variant: 61,877 to 128,411 with examples alone).
- A token counter in the indexer that gives the same count as the embedder (**measured** in the audit with the
  embedder's tokenizer; the indexer has none today).

No gate. If the spread is larger than the differences R0 saw, I say so before step 1, because then the gates need
more runs.

### Step 1. The prepared index, on a copy (3 to 4 days)

Design points 1 to 4, for every kind, in one build. Near-empty pieces (headings without text) and exact duplicates
are left out.

**Gate 1:**

- share of pieces longer than the embedder reads: under 5 % for every kind; pieces cut inside a unit: under 5 %;
- the case: the model reads a piece with the count element in 3 of 3 runs; of the 7 questions, at least 4 better
  and none worse;
- answers: answerable not lower; must-refuse not answered more often;
- files: questions lost by the rule of §5: none unexplained, and not more than gained;
- examples: not lower;
- retrieval time not more than 0.3 s above the baseline; rows not more than 2.5 times today's, and prod has the
  room for it (step 0).

### Step 2. The six places shared among kinds (about 1 day, code only, on the copy)

Design point 5. Measured against step 1's result.

**Gate 2:** the questions step 1 lost at file level are back, by the same rule; answers and examples not lower;
no kind of question gets worse, read on the changed passages (a random 20).

### Step 3. Concepts on the pieces and concepts by meaning (about 2 days)

Design point 6, first and second part. The labels are written on the copy without a new embedding.

**Gate 3:** the concept benchmark not lower (23 of 26 today); the questions in languages other than English in the
gold and benchmark files not lower; answers, files and examples not lower; retrieval time not higher than step 2
(the search of paths by label words was the slowest part of retrieval on prod).

### Step 4. Facts of the graph in their own block (about 1 day)

Design point 6, third part.

**Gate 4:** the "does the standard have X" questions answered as before, read; answers not lower; the tokens the
model reads per question stated, and not more than a quarter above step 3.

### Step 5. The indexer, and the dev index (1 to 2 days, with my go-ahead)

- The new cut goes into the indexer behind a version stored with each file. The nightly source refresh must not
  re-cut everything on its own; the re-index is its own command.
- A file's old pieces stay until its new ones are embedded, so the search never sees a file without pieces.
- CI builds its own index with the indexer, so from here the CI retrieval benchmark sees the change. Its baseline
  is set anew in the same PR, with the old and new numbers side by side.

**Gate 5:** the numbers of steps 1 to 4 hold on the real dev index; the command can be stopped and started again;
tests of the cut for every kind; the way back is the same command with the old version.

### Step 6. Prod (one night, or a load)

About 130,000 pieces at prod's 3.4 pieces a second are about 11 hours (**believed**, by division): longer than a
night, and the nightly refresh must not run beside it. Two ways, decided in step 5:

- embed on prod over a weekend, or
- build the pieces and vectors on dev from the same source commits as prod and load them on prod through a
  workflow (**assumed** possible: the model is the same, so the vectors are the same; to be proven on one source
  first).

Then check: health, rows, the case and the answer sets through the API, the time it took.

## 7. Not planned

- Another embedding model, or the embedder reading more than 256 tokens.
- A run with the graph switched off.
- The FAQ (3 entries, matched by word stems; **measured** in the audit). Too small to matter now.
- The clarifying questions (#536) and the search of all sources without a scope (#539). Both failed their gates on
  today's index. They may be measured again after step 6, as their own steps.

## 8. Risks

- **Everything that ranks or counts pieces moves at once** (listed in R0, step 0b: the lookup of examples by
  element, element candidates, limits counted in pieces, the quality score). The example benchmark is in every
  gate for this reason.
- **Twice the rows.** Index size and memory on prod. Checked in step 0, before anything is built.
- **Reading by hand decides part of the gates.** It is slower and less exact than a count. The rule is written in
  §5 and the readings go into the record, question by question.
- **Design point 4 changes what the model reads** although the index only got smaller pieces. If the unit around a
  piece is chosen badly, answers get worse while every search measure gets better. Answers are in gate 1 for this.
- **The gain may be small.** R0 gave +6 answered runs of 69 for the variant that fits the embedder, with unknown
  spread. If step 1 shows no more than the case fixed, the plan stops there and nothing is re-indexed.

## 9. Order and cost

Steps 0 to 4 on copies: 8 to 9 working days. Step 5: 1 to 2 days. Step 6: a night or a weekend on prod.

Each build of a copy embeds about 130,000 pieces: about 3.5 hours on my laptop with the embedder at 2 cores
(**measured** in R0: 11 pieces a second). At least three builds are expected (step 1, one repair, step 5). Before
each I decide whether Docker gets more cores for that session.

The four copies R0 left in the dev database server (7.7 GB together) can be dropped once this plan is accepted;
step 0 makes its own.

## 10. Results

(Each step records its numbers here, dated.)

### Step 0 (2026-11-15, dev copy `napcore_helpdesk_s0base`, 0.97.226 with #540 and #542)

<!-- step0-A -->

**B. The gold file, read for further sources.** I went through all 57 questions of `answer-source-questions.yaml`,
not only the ones R0 lost. For each I searched the dev index for passages that hold what the question asks (by the
question's terms and the standard's element names, in every source kind), read every candidate, and added a source
only when the passage I read holds the answer, or the same share of it as the sources already named. No source was
added because a retrieval run returned it, and none was removed. 44 questions got 70 further patterns (each matches
one indexed file, a03's parking pattern two examples; checked against the index). The `unsure` marks stay as they
were. The entries are below for review; the YAML notes say only that a source was added and point here.

| question | pattern added | where in the file | why |
|---|---|---|---|
| a01 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs on the Delegated Regulations, §3.5 "Which formats are considered machine-readable?" | answers the question by name (CSV, XML exports; the formats the Delegated Regulations specify); NAPCORE scope, opt-in |
| a02 | `OpRa/examples/ResponseLateDatedVehicleJourneys.xml` | IndicatorFrame / indicatorLogEntries / LateDatedVehicleJourneyEntry with DelayDuration | an OpRa example file of observed delays, one entry per late journey |
| a02 | `OpRa/examples/CancelledAndLateDatedVehicleJourneys.xml` | indicatorLogEntries (LateDatedVehicleJourneyEntry, DelayDuration) and indicators (LateDatedVehicleJourneyCount) | an OpRa example file of observed delays, entries and counts per delay interval |
| a03 | `Netex_21_Sites_Parking_` | NeTEx examples Netex_21_Sites_Parking_1.xml and _2.xml: parkings / Parking (multistorey car park, on-street parking) with ParkingProperties and ParkingCapacity | a parking defined in NeTEx, element by element |
| a03 | `TN-ITS-Open/OWL/codelists/ParkingSiteTypeCode.ttl` | the code list's skos:definition of each parking site type (e.g. interUrbanParkingSite) | TN-ITS defines kinds of parking sites; another standard's definition |
| a04 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a04 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a04 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a04 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a06 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a06 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a06 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a06 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a21 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a21 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a21 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a21 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a22 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / LiftEquipment (Name, Width, Depth, MaximumLoad) with EquipmentPlace refs | a lift described in a station (EPIAP profile example) |
| a22 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace / … / equipmentPlaces / EquipmentPlace / placeEquipments / LiftEquipment (Lift to Platforms 1-4) | a lift described in a station |
| a22 | `910GWIMBLDN-accessibility` | same LiftEquipment in the Wimbledon accessibility example | a lift described in a station |
| a22 | `Netex_10_StopPlace_withParking_1` | same LiftEquipment (Wimbledon) in the stop place example with parking | a lift described in a station |
| a05 | `Chur_Equipment_Pathlink_V1.0.xml` | StopPlace / placeEquipments / EscalatorEquipment (Rolltreppe …, Width) with EquipmentPlace refs | an escalator described in a station; the only example with EscalatorEquipment |
| a08 | `02007L0002-20241126#art_3$` | INSPIRE Directive Art. 3(6): 'metadata' means information describing spatial data sets and services, to discover, inventory and use them | another act's definition of metadata |
| a08 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP': metadata as the building block that describes datasets on NAPs | says what metadata are for on a NAP |
| b16 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP', opening paragraphs | metadata make NAP datasets accessible, reusable and discoverable: what they are used for |
| b17 | `napcore.eu/metadata` | NAPCORE page 'mobilityDCAT-AP', opening paragraphs | what metadata on a NAP are |
| a09 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | header comment: 'the encoding of a simple bus timetable for a linear route … SERVICE JOURNEYS with CALLS with computed passing times' | says what a bus timetable is in NeTEx terms, with the example |
| a10 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | same header comment | as a09 |
| a10 | `32026R0253#art_3$` | TEL TSI Art. 3(33): 'passenger timetable' means the date and time of passenger rail services … | a legal definition of a timetable (rail) |
| a11 | `DelayedAndCancelledJourneysWithEvents` | indicators / LateDatedVehicleJourneyCount ('Delayed Journey Statistics') with intervals | counts late journeys per journey pattern, as in the example already named |
| a11 | `OpRa/examples/ResponseLateDatedVehicleJourneys.xml` | indicators / LateDatedVehicleJourneyCount with intervals, after the LateDatedVehicleJourneyEntry log | counts late journeys, as in the example already named |
| a12 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | ValueSet TypeOfTravelDocument: paper ticket bought on the bus, m-ticket, contactless (UK fare profile) | bus tickets described in NeTEx, as travel document types |
| a15 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b04 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b05 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| b06 | `D2.2.1_Mapping_EU-based_requirements_final.pdf` | NAPCORE D2.2.1, section 4 'OpRa' (4.1 The need for OpRa) | OpRa's purpose: operational raw data (timestamps, positions, delays, dwell times) linked to planned NeTEx data, for performance monitoring |
| a16 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §2.1.4 'Which data must be provided regarding fares information parameters?' | answers the question for MMTIS: static fare data usable in a route planner, if available |
| b11 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §1.1 'What is a NAP? Why do I need to provide data on the NAPs?' | defines a NAP and its legal basis |
| a03 | `M4.3.5-Technical-mapping-of-multimodal-data-standards` | NAPCORE M4.3.5, the parking section: parking data in Transmodel/NeTEx, SIRI, APDS and DATEX II, and their mappings | surveys how parkings are defined across the standards |
| a20 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs, §3.4 (formats of the delegated regulations: RTTI DATEX II, MMTIS DATEX II/SIRI/NeTEx, SSTP DATEX II, SRTI DATEX II) and §2.3.2 (SRTI in DATEX II) | names the delegated regulations that require DATEX II |
| b08 | `32024R0490#art_1$` | Art. 1 (amended Art. 4 of 2017/1926): 'NeTEx CEN/TS 16614 and subsequent versions' | gives the CEN reference |
| b08 | `32026R0253#app_C$` | TEL TSI Appendix C, [P.1]/[P.2]: CEN/TS 16614-1:2025 … (NeTEx) Part 1, Part 2 | gives the CEN reference with parts |
| b08 | `SIRI/README.md$` | SIRI README overview: 'relates to NeTEx (CEN/TS 16614 series)' | gives the CEN reference |
| b08 | `napcore.eu/multimodal-data` | NAPCORE page 'multimodal data', Static multimodal data: NeTEx parts 1-6 with CEN/TS 16614-1 … -5 | gives the CEN reference per part |
| b03 | `napcore.eu/multimodal-data` | same page, 'NeTEx is a CEN Technical Standard for exchanging Public Transport schedules and related data', its parts | says what NeTEx is |
| b01 | `napcore.eu/multimodal-data` | same page, Dynamic multimodal data: 'SIRI … enables the exchange of information on transport operations between different computer systems' | says what SIRI is for (short) |
| b02 | `napcore.eu/multimodal-data` | as b01 | German form of b01 |
| b05 | `napcore.eu/multimodal-data` | same page: Transmodel, NeTEx (static) and SIRI (dynamic) explained | explains two of the three standards, as each README explains one |
| b09 | `docs.datex2.eu/v3.7/user-guide$` | DATEX II user guide, 'What is DATEX II?': a standard for the traffic and travel information sector to share data … | answers the question by name |
| b09 | `napcore.eu/standards$` | NAPCORE page 'DATEX II': 'the electronic language used in Europe for the exchange of traffic information and traffic data', history and governance | says what DATEX II is |
| b10 | `dataspecification_tn.adoc#L93$` | INSPIRE TN Technical Guidelines, 'General Executive Summary': Directive 2007/2/EC establishes an Infrastructure for Spatial Information in the European Community (INSPIRE) … | says what INSPIRE is |
| b14 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | NAPCORE MMTIS Quality Framework, Table 2: the time and service related data types of 2024/490 by level (S-1 … D-2) | lists the MMTIS data categories |
| a16 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | same Table 2, rows S-2 'basic common standard fares' (fare network data …) | lists the fare data categories of MMTIS |
| b12 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | the guidance-paper passage: 'NeTEx (stop registry, schedules, fares), SIRI (real-time), OJP …' | names NeTEx for static data under MMTIS |
| b13 | `NAPCORE-MMTIS-Quality-Framework_v1_250411.pdf` | as b12 | Norwegian form of b12 |
| b15 | `FAQs-on-the-Delegated-Regulations.pdf` | NAPCORE WG5 FAQs §3.5 'Which formats are considered machine-readable?' | as a01 |
| b20 | `FX-PI-01_UK_FBRI_NETWORK-FARE_WOE-Bristol-pass-(Z2Z)` | FareFrame / distributionChannels / DistributionChannel (First travel shop, Tourist Information Centre, Travelwest outlets) with Description and Url 'where-buy' | where passengers buy tickets, in NeTEx |
| b21 | `FX-PI-01_UK_FBRI_NETWORK-FARE_WOE-Bristol-pass-(Z2Z)` | FareFrame / distributionChannels / DistributionChannel (First travel shop, Tourist Information Centre, Travelwest outlets) with Description and Url 'where-buy' | where passengers buy tickets, in NeTEx |
| b22 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | FareTable 'ArrivaSingleTrip - Cash' / prices / DistanceMatrixElementPrice with Amount per zone pair, for a sales offer package and user profile | a bus fare with its prices, in NeTEx |
| b23 | `FX-PI-01_UK_AMSY_NETWORK_FARE_Arriva-trip_20200417` | FareTable 'ArrivaSingleTrip - Cash' / prices / DistanceMatrixElementPrice with Amount per zone pair, for a sales offer package and user profile | a bus fare with its prices, in NeTEx |
| b24 | `Netex_04_Stops_SimpleStation_1` | header comment and StopPlace: 'a simple station with two platforms encoded in NeTEx XML' (quays, access space, entrance) | how a station is defined in NeTEx, by example |
| b24 | `Netex_10_StopPlace_uk_ComplexStation_Wimbledon_1` | StopPlace of a complex station (levels, quays, equipment places) | how a station is defined in NeTEx, by example |
| b25 | `Netex_01_Stops_SingleStopOnStreet_1` | header comment: a single stop on a street: a STOP PLACE with a QUAY, scheduled stop point and stop assignment | how a stop is described in NeTEx, by example |
| b26 | `Netex_07.1_Bus_FlexibleTimetable_ZonesOnly` | SiteFrame / flexibleStopPlaces / FlexibleStopPlace 'Flexible Zone Sigma' with Centroid and area | a flexible stop defined in NeTEx, by example |
| b27 | `netex_nm_equipmentEnergy_version` | VehicleChargingEquipment: 'Specialisation of PLACE EQUIPMENT for vehicle charging', its type and group | the NeTEx element for charging equipment at a place |
| b28 | `norway/vehicles/submodel-Train.xml` | the Train element: TrainSize, components / TrainComponent / TrainElement (carriage) | a train modelled in NeTEx, by example |
| b29 | `Netex_01.1_Bus_SimpleTimetable_JourneysOnly` | lines / Line 'Line 24' with OperatorRef | the link of an operator to a line, by example |
| b31 | `DelayedAndCancelledJourneysWithEvents` | indicatorLogEntries / CancelledDatedVehicleJourneyEntry ('Cancelled Journey 1: No replacement service') with ControlActionType JourneyCancellation | shows what a cancelled journey is in OpRa, by example |
| b32 | `OpRa/examples/TicketingBasedPassengerCount.xml` | indicators / TicketingBasedPassengerCount with BoardingCount and AlightingCount, from ValidationEntry log entries | passenger counts modelled in OpRa, by example |
| b32 | `OpRa/examples/ExpectedPassengerCount.xml` | indicators / ExpectedPassengerCount per scheduled stop point and time band with BoardingCount | passenger counts modelled in OpRa, by example |

Read and not added (the passage I found does not hold the answer): a07 (examples give values of `SeatingCapacity`, no
meaning; the occupancy enumeration is about free seats), a13 and a14 (no other act defines static or dynamic data; the
NAPCORE quality framework uses the words without defining them), a17, a18, a19 (NAPCORE M4.3.5 names DATEX II and SIRI
side by side for parking, not how they connect), a23, b07, b18, b19, b30, b33 and b34 (one Slovenian timetable
example only). b01/b02 got only the short NAPCORE description of SIRI; the SIRI schema's own documentation of its root
element is one line and was not added.

What it shows (**measured** by reading, not by a run): for 44 of 57 questions more than one indexed source holds the
answer, and most of the further holders are of a kind the old entries did not name: example files for element
questions (a02, a04–a06, a11, a12, b20–b29, b31, b32) and NAPCORE documents for legislation and overview questions
(a01, a15, a16, a20, b03–b06, b08–b17). So the file-level measure did count a question as lost when another passage
held the same answer; how often, the run below says.

**The benchmark question file** (149 questions, 141 with patterns) I did not edit. Its patterns are coarser than the
gold file's (`README.md` matches every README, 55 questions name one pattern), so it already counts many neighbours as
found; two questions have the same text as gold questions (q145 = b04, q147 = b01) and the same additions would apply
to them, but the file is also the CI retrieval benchmark's input and CI's index has no NAPCORE pages, so the rule does
not apply cleanly there. Left for step 1's reading of lost questions (**assumed**: the reading rule of §5 covers it).

**File-level baseline, old and new gold file side by side** (same copy, same code, model off, two runs each;
**measured**):

| | found (of 57) | gained | lost |
|---|---|---|---|
| old gold file (pass 1 and 2, four runs) | 34 / 34 / 34 / 34 | – | – |
| new gold file (two runs) | 39 / 39 | b10, b16, b17, b24, b32 | none |

Still not found with the new file (18): a01, a06, a08, a12, a13, a14, a16, a17, a21, a22, b01, b02, b20, b21, b22, b23,
b26, b30. So 5 of the 23 questions the old file counted as lost had another indexed source among the passages that
holds the answer: the file-level measure undercounted by 5 of 57 (**measured**). Step 1 and later steps measure with the
new file; the old numbers stay here for comparison.

<!-- step0-C -->

**D. A token counter that counts as the embedder does.** How the embedder counts (**measured** by reading
`embedding_service.py` and fastembed 0.9.1 in the embedder image): `load_model` builds fastembed's `TextEmbedding`
for `intfloat/multilingual-e5-small` and sets the model's own `tokenizers` tokenizer (0.23.3, the model's
`tokenizer.json` with fastembed's special-token and padding set-up) to cut at `EMBEDDER_MAX_TOKENS` (256);
`embed_texts` prefixes each text with `passage: ` or `query: ` and fastembed tokenizes it with `encode_batch`, which
adds `<s>` and `</s>`; the model reads the first 256 tokens including those two (fastembed's own `token_count` is the
sum of the attention mask, so it never exceeds 256). The indexer embeds `passage_text` = source path, heading and
text, each on its own line.

Where the counter lives, and why: in the embedding service, as `POST /count`, with a backend call
`count_embedded_tokens(texts, kind)` and `count_passage_tokens(chunks)` in `services/embeddings.py`. The service
counts with a copy of the very tokenizer it embeds with (cut and padding switched off on the copy), on the same
prefix, so the count cannot drift from what is embedded when the model, the library or the cut changes; the backend
and worker images have the `tokenizers` library but not the model's files (they live in the embedder's volume), and
the indexer already calls the embedder for every piece. The cost is an HTTP call per batch of 256 texts, and a cut
that tries many sizes must send its candidates in batches. Nothing calls the counter yet; the indexer's cut and every
index result are unchanged (the counter's functions are referenced only by tests).

Verified (**measured**):

- On 1,500 random indexed chunks spread over all 17 kinds (`doc_type`, `chunk_type`, source; up to 60 per kind,
  the rest at random): the new `/count` handler, built from the model as in production and run with the embedder
  image's fastembed 0.9.1 and tokenizers 0.23.3 and the model files copied from the embedder's volume, gives for
  every chunk the same number as fastembed's own `token_count` on a model whose cut is set above any chunk (1,500 of
  1,500), and cut at 256 the same as fastembed's `token_count` of the model as the service configures it, which is
  what the embedder reads (1,500 of 1,500). The model's tokenizer still cuts after the counter is built.
- Against the running dev embedder: for 93 chunks over 256 tokens from 15 kinds, the text cut right after its 254th
  content token (256 tokens by the counter) gives the same vector as the whole chunk, and the text cut one token
  earlier (255) a different vector, 93 of 93. So the running embedder reads exactly the 256 tokens the counter
  counts.
- Of the 1,500 chunks, 983 are longer than 256 tokens (XML examples 653 of 667, NAPCORE 144 of 149, guides 70 of
  135, regulation 31 of 68, INSPIRE 37 of 107, DATEX II 33 of 98, READMEs 11 of 61, schema declarations 1 of 202),
  in line with the audit.
- Unit tests (`test_embedding_service.py`): the count is of the text with its kind's prefix; `/count` rejects what
  `/embed` rejects; without a tokenizer there is no `/count`; with a small real tokenizer the count includes the
  special tokens and is not cut while the model's tokenizer still cuts and pads; the backend call sends exactly
  `passage_text`, batches by 256, and raises when the service cannot count. 27 tests of the embedding and re-embed
  files pass with `tokenizers` installed (the real-tokenizer test skips without it).
- Not done: the live dev embedder serves `/count` only after it is started again with this code, and prod's after
  the next deploy (the deploy rebuilds the embedder). I did not restart it. The check above ran the new handler on
  the host, with the embedder image's library versions, not inside the running service.
