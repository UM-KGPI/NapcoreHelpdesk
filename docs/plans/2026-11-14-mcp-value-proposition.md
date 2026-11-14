# Plan: find out where the Model Context Protocol gives the Helpdesk value

Written 2026-11-14 against 0.97.218. This is a plan to find a value proposition, not to build one: each step is a
cheap test with a decision rule, and nothing is built for users before its test has passed. Each claim is labelled
**measured**, **believed** or **assumed**.

## 1. The question

The Model Context Protocol (MCP) lets an AI assistant call a service's functions as tools. For the Helpdesk that
can mean two different things, with different users and different value:

- **A. Tools for developing the Helpdesk.** The user is whoever works on the code with an assistant. The value
  would be time: lookups that are scripted by hand today become one tool call.
- **B. The Helpdesk as a tool for others.** The user is a NAPCORE partner whose assistant asks the Helpdesk about
  the standards, validates a file or gets an example. The value would be reach: the standards knowledge is used
  inside the tools people already work in, not only on our web page.

The two are tested separately. A can pay off without B, and B is a product decision that A does not settle.

## 2. What is known

- **Measured** (web search, 2026-11-14): I found no MCP server for NeTEx, Transmodel, SIRI, DATEX II or a National
  Access Point. What exists: servers over GTFS feeds of single operators or countries (Auckland, Ireland, France's
  transport.data.gouv.fr, Transitland), generic or domain XSD validators (e-invoices, bank statements), and a
  community read-only server for GraphDB (SPARQL, GPL-3.0). Three searches, not a survey of the registries.
- **Measured** (this repository): the app's API has the pieces B would wrap — an answer endpoint with citations, a
  NeTEx example generator with schema validation, and a validator service with lookups (`/concrete`,
  `/accepting`). The validator has no published port.
- **Measured** (one working day, 2026-11-14): reviewing 21 benchmark entries against the standard's examples took
  12 one-off scripts over the NeTEx checkout, each answering "where is X defined, what refers to it, what holds
  it". The same kind of lookup is done in every fix of the example generator.
- **Measured** (same day): a fault on prod — a Slovenian question answered with an empty text, because the answer
  validator dropped a grounded answer twice — was found by chance, while checking something else.
- **Known blockers for B** (from the generator-API note of 2026-11-11): prod has no real authentication (the
  token is issued to anyone), and every answer or generated example costs model calls we pay for.
- **Assumed**: partners use AI assistants in their work on the standards. Nobody has asked for an MCP server.

## 3. Hypotheses and their tests

Each test is small enough to finish in a day or less, and each has a rule that says when to stop.

### A1. Lookups over the standard's examples and schema are worth a tool

- Claim: a few read-only tools over the NeTEx checkout and the validator ("where is this element defined and
  referenced", "what links A to B in the examples", "is this an object, what may it hold") cut the work of a
  lookup clearly.
- Test: build the tools as a prototype (no deployment, local only); replay 10 of the 12 lookups of 2026-11-14 with
  and without them; count tool calls, time and tokens, and check that the answers agree.
- Rule: keep and maintain it if the replay needs at most half the calls and gives the same answers; otherwise
  keep the scripts as a small library in the repository and stop.
- Before building: look in the MCP registries for an XML or XSD server that already does this over a local
  checkout. **Not checked.**

### A2. Prod needs a regular look, and a tool is the way to take it

- Claim: faults like the dropped Slovenian answer are frequent enough to look for on purpose.
- Test (needs no MCP): one sweep of the prod question log for answers with empty text, a dropped answer, a
  fallback to the standard's example, or a failed generation; count them over the last month.
- Rule: if the count is a few per hundred questions or more, a regular check is worth having. Whether it is an MCP
  tool, a management command or a line on the editor's page is then a second, smaller decision: the simplest form
  that gets looked at wins. If the count is negligible, stop.

### B1. Somebody would use the Helpdesk through their assistant

- Claim: there are partners who would connect an assistant to the Helpdesk if they could.
- Test: ask, before building. Five short questions to the T4.3 testers and the T5.2 group: do you use an AI
  assistant when working with the standards, which one, for what, what does it get wrong, would you connect it to
  a NAPCORE source. And one look at the prod log for clients that are not browsers.
- Rule: go on to B2 only with at least three named people or organisations who say they would use it and can say
  for what. Fewer: record the answers and stop; the web page serves them.

### B2. Validation is a safe first tool

- Claim: "validate this NeTEx against the schema" can be offered without the two blockers: it calls no model and
  returns a result anyone can check.
- Test: a prototype tool in front of the validator, tried by the people found in B1 on their own files; note what
  they expected "valid" to mean (schema only, or a profile such as EPIP).
- Rule: offer it if the testers use it more than once and the answer to "what does valid mean" can be stated in
  one sentence on the tool. If they expect profile validation, that is the finding, and the tool waits for it.
- Open, to check first: general NeTEx validators exist (Entur's, for one; **not checked**). If one already serves
  this need, our value is not validation but validation next to the standards knowledge.

### B3. Answers and examples through MCP (only after B1 and B2)

- Claim: the answer endpoint and the example generator are worth offering as tools.
- This step is not tested before real authentication exists and a cost limit per user is decided. It is listed so
  that B1 and B2 are not mistaken for the whole of B.

### C. A place in the work programme

- Claim: "the standards as a tool for AI assistants" fits a work item of T5.2 (Tools) in the 2027 programme, next
  to the browsers.
- Test: read the programme text for a fitting item; raise it at a T5.2 meeting only with the answers of B1 in hand.
- Rule: propose it if B1 found users. Without them it would be a tool looking for a need, which is what I asked
  the browser items to avoid.

## 4. The statement this plan should end with

For each of A and B, one sentence of this form, or the finding that there is none:

> For (who), who (does what today, at what cost), the Helpdesk's (tool) gives (what), which (the alternative)
> does not, shown by (the measurement).

## 5. Order and cost

1. A2's sweep of the prod log (hours; useful whatever MCP turns out to be).
2. A1's registry check and prototype (a day).
3. B1's questions (an email and a meeting slot; the answers take weeks to arrive, so send early).
4. B2 only on B1's rule; B3 and C after that.

A1 and A2 cost little and their worth is measured in our own time. B is where the larger value could be, and it
is the part that cannot be found out from the code.

## 6. Not planned

- Building a public server before B1 has named users.
- Offering model-backed tools before authentication and a cost limit exist.
- An MCP server where a script or a page does the same job with less to maintain.

## 7. Risks

- **A tool nobody calls.** On the development side a tool only helps sessions that use it; A1's replay measures
  that before anything is kept.
- **Asking the wrong people.** T4.3 and T5.2 are the partners I can reach, not all users of the standards. B1's
  answers are a floor, not a market study.
- **MCP itself moving.** The protocol and its clients change quickly. Everything under A and B2 is a thin layer
  over functions that exist anyway, so little is lost if the interface changes.

## 8. Results

(Each step records its numbers here.)
