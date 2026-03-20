# Domain Model — FHIR Alignment

This document records the renaming of domain model classes to align with FHIR R4 resource
names, in preparation for a future FHIR migration. It covers every class, the FHIR resources
considered, the final choice and its rationale, and where applicable the reasons a candidate
resource was rejected.

---

## `PreindicationData` → `ConditionData`

**FHIR resource chosen:** `Condition`
**FHIR URL:** https://hl7.org/fhir/R4/condition.html

The original name `PreindicationData` was an internal, implementation-specific term
describing the clinical indication that motivated the genomic test (structured as a
hierarchical code: `cat_key` / `cat_name` for the category, `key` / `name` for the
specific indication).

### Candidates considered

**`Organization`** (original annotation in the code) — **Rejected.**
`Organization` represents a healthcare institution (hospital, laboratory, clinic).
It has no semantic relationship to a clinical indication. This annotation was simply wrong.
https://hl7.org/fhir/R4/organization.html

**`CodeableConcept`** — **Considered but not chosen.**
`CodeableConcept` is a FHIR data type (not a resource) that represents a coded value from
a terminology system. It would be appropriate if the indication were a flat code. However,
our model carries a two-level hierarchy (category + specific indication), which maps more
naturally to `Condition` with its `category` and `code` fields.
https://hl7.org/fhir/R4/datatypes.html#CodeableConcept

**`Condition`** — **Chosen.**
`Condition` represents a clinical condition, problem, diagnosis, or other event that has
a `code` (the specific condition) and a `category` (the clinical category), matching the
`key`/`name` and `cat_key`/`cat_name` structure of our model exactly.
https://hl7.org/fhir/R4/condition.html

---

## `RCPData` → `CareTeamData`

**FHIR resource chosen:** `CareTeam`
**FHIR URL:** https://hl7.org/fhir/R4/careteam.html

The RCP (Réunion de Concertation Pluridisciplinaire) is a French multidisciplinary
clinical meeting that groups several specialists (oncologist, geneticist, pathologist, etc.)
to review a patient case. The original name `RCPData` was a French-specific acronym
with no internationally recognisable meaning.

### Candidates considered

**`Team`** (original annotation in the code) — **Rejected.**
`Team` is not a FHIR resource. It was used as an informal annotation pointing in the
right direction but is not part of the FHIR R4 specification.

**`CareTeam`** — **Chosen.**
`CareTeam` documents all people and organisations planning to participate in the
coordination and delivery of care for a patient. It directly models a multidisciplinary
meeting via its `participant` array (each member with their `role`), its `name` field
(the RCP name), its `identifier`, and its `period` (when the meeting takes place).
The `reasonCode` / `reasonReference` fields capture the clinical justification for
convening the team.
https://hl7.org/fhir/R4/careteam.html

---

## `PatientData` — unchanged

**FHIR resource:** `Patient`
**FHIR URL:** https://hl7.org/fhir/R4/patient.html

`PatientData` already aligned with the FHIR `Patient` resource. No rename was needed.
The class represents the index patient (the person whose genome is being analysed),
corresponding directly to FHIR `Patient` demographics: `identifier`, `name`, `gender`,
`birthDate`.

---

## `PersonData` — retained

**FHIR resource:** `Person`
**FHIR URL:** https://hl7.org/fhir/R4/person.html

`PersonData` holds references to two practitioners involved in the report: the prescriber
(`prescripteur`) and the RCP member (`membreRCP`). The FHIR `Person` resource represents
a generic person record that can link across Patient, Practitioner, and RelatedPerson
resources. It was retained as `PersonData` as it acts as a cross-cutting container for
person-level references that do not cleanly belong to a single more specific resource.

### Candidates considered

**`Practitioner`** — **Considered but not chosen.**
`Practitioner` represents a healthcare worker directly involved in care provisioning, with
fields for identity (`identifier`, `name`) and credentials (`qualification`). Both
`prescripteur` and `membreRCP` are practitioners, but housing two distinct practitioners
in a single class named `PractitionerData` would be semantically ambiguous — a
`Practitioner` is a single individual, not a container for two.
https://hl7.org/fhir/R4/practitioner.html

**`PractitionerRole`** — **Considered but not chosen.**
`PractitionerRole` links a `Practitioner` to an `Organization` and describes the role they
play. It would be appropriate when modelling the prescriber's context, but adds a layer of
indirection not needed at this stage.
https://hl7.org/fhir/R4/practitionerrole.html

**`Person`** — **Retained.**
`Person` is a master record that can link to multiple typed resources (Patient, Practitioner,
RelatedPerson). It is appropriate here as a container for person-level references where the
specific role (prescriber, RCP member) is captured via the field name rather than the
resource type.
https://hl7.org/fhir/R4/person.html

---

## `AnalysisData` → `ProcedureData`

**FHIR resource chosen:** `Procedure`
**FHIR URL:** https://hl7.org/fhir/R4/procedure.html

`AnalysisData` carried a single field: `analysis_id`, the identifier of the bioinformatics
analysis pipeline run that processed the genomic sequencing data. The original name was
vague and HL7v2-centric (it mapped to the PRT-10 Device field). `analysis_id` identifies
a pipeline execution — something that was performed — which maps to `Procedure`.

### Candidates considered

**`ServiceRequest`** — **Considered but not chosen.**
`ServiceRequest` represents an order or proposal for a clinical service, placed *before*
work occurs. `analysis_id` identifies the pipeline run that *was performed*, not the
upstream order. The FHIR genomics implementation guide does use `ServiceRequest` as the
entry point for genomic test orders, but that is a different concept from the identifier
of the analysis execution itself.
https://hl7.org/fhir/R4/servicerequest.html

**`Observation`** — **Considered but not chosen.**
`Observation` captures measurements and findings (genomic variants, expression results).
`analysis_id` identifies the process that produced those observations, not an observation
itself.
https://hl7.org/fhir/R4/observation.html

**`DiagnosticReport`** — **Considered but not chosen.**
`DiagnosticReport` aggregates findings from one or more Observations into a structured
report. `analysis_id` identifies the pipeline execution, not the aggregated report.
https://hl7.org/fhir/R4/diagnosticreport.html

**`Procedure`** — **Chosen.**
`Procedure` documents an action that was or is being performed. A bioinformatics analysis
pipeline run is a performed action with an identifier (`Procedure.identifier`), a type
(`Procedure.code`), and a status. The HL7v2 PRT-10 "Participation Device" field, where
`analysis_id` is written, identifies a system or process that participated in producing
the result — consistent with a `Procedure` performed by an automated pipeline.
https://hl7.org/fhir/R4/procedure.html

---

## `TimingData` → `PeriodData`

**FHIR resource chosen:** `Period` (data type)
**FHIR URL:** https://hl7.org/fhir/R4/datatypes.html#Period

`TimingData` held two timestamps: `date_creation` (when the record was opened) and
`date_cloture` (when it was closed). This maps exactly to a start/end interval.

### Candidates considered

**`Instant`** (original annotation in the code) — **Rejected.**
`Instant` is a FHIR primitive data type representing a single point in time (e.g.,
`2024-01-15T14:30:00Z`). It cannot represent a duration or interval between two
timestamps. Using it for a class holding two datetime values is semantically incorrect.
https://hl7.org/fhir/R4/datatypes.html#instant

**`Timing`** — **Considered but not chosen.**
`Timing` is a complex data type for recurring schedules (e.g., "every 8 hours for 5 days").
It is designed for dosing schedules and recurring events, not for a simple start/end
administrative lifecycle window.
https://hl7.org/fhir/R4/datatypes.html#Timing

**`Period`** — **Chosen.**
`Period` is a time interval with an inclusive `start` and an `end`. The specification
explicitly states that if `end` is absent, the period is ongoing — which elegantly handles
the case where `date_cloture` is not yet known. It is the standard FHIR data type for
administrative lifecycle intervals such as employment periods, service validity windows,
and record open/close timestamps.
https://hl7.org/fhir/R4/datatypes.html#Period

---

## `ResultsData` → `ObservationData`

**FHIR resource chosen:** `Observation`
**FHIR URL:** https://hl7.org/fhir/R4/observation.html

`ResultsData` held result information from the source system, specifically the `membre_lmg`
field (the LMG member associated with the result). Genomic findings are the canonical use
case for FHIR `Observation`.

### Candidates considered

**`DiagnosticReport`** — **Considered but not chosen.**
`DiagnosticReport` aggregates multiple `Observation` resources into a structured report.
Since `ResultsData` holds individual result-level data rather than an aggregated report,
`Observation` is the more granular and appropriate choice.
https://hl7.org/fhir/R4/diagnosticreport.html

**`Observation`** — **Chosen.**
`Observation` captures measurements, findings, and assertions. It is the central FHIR
resource for genomic findings, and is referenced by FHIR's genomics implementation guide
for representing sequence variants, gene expression results, and molecular markers.
https://hl7.org/fhir/R4/observation.html

---

## `ConsentData` — unchanged

**FHIR resource:** `Consent`
**FHIR URL:** https://hl7.org/fhir/R4/consent.html

`ConsentData` already aligned directly with the FHIR `Consent` resource. No rename was
needed. The class records whether the patient's data may be reused for research
(`is_data_reusable_for_research`), the date of consent, and the consenter's identity —
mapping to `Consent.provision.purpose`, `Consent.dateTime`, and `Consent.performer`
respectively.

---

## `NextOfKinData` → `RelatedPersonData`

**FHIR resource chosen:** `RelatedPerson`
**FHIR URL:** https://hl7.org/fhir/R4/relatedperson.html

In genomics trio analysis, the father and mother of the index patient are included because
their genomic data is sequenced alongside the proband's. `NextOfKinData` was an HL7v2-centric
name (NK1 segment) with no meaning outside that context.

### Candidates considered

**`Person`** — **Considered and rejected as a replacement, but kept for `PersonData`.**
FHIR `Person` is a master record that can link across `Patient`, `Practitioner`, and
`RelatedPerson`. It does not carry relationship semantics on its own — it has no
`relationship` field and no mandatory reference to a patient. It cannot express "this
person is the father of patient X".
https://hl7.org/fhir/R4/person.html

**`Patient`** — **Considered but not chosen.**
In a genomics trio, the parents do have their own genomic files and could each be modelled
as a full `Patient`. However, collapsing `RelatedPersonData` into `PatientData` would
erase the semantic distinction between the index patient (the subject of the test) and the
related individuals (who are included for comparative sequencing). The aggregate root
`CompositionData` needs to distinguish these two roles explicitly.
https://hl7.org/fhir/R4/patient.html

**`RelatedPerson`** — **Chosen.**
`RelatedPerson` explicitly models a person who is involved in the care or has a family
relationship with the patient, without being the patient themselves. Its mandatory
`patient` reference (cardinality 1..1) links the related person to the index patient,
and its `relationship` field (CodeableConcept from the `v3-RoleCode` value set) carries
the family relationship code — mapping directly to `relationship_code` (`FTH`/`MTH`).
Fields `name`, `gender`, `birthDate` map one-to-one. The `patient_id` field maps to
`RelatedPerson.patient` (the reference to the index `Patient`).

### Why `RelatedPersonData` was not folded into `PatientData`

The index patient and the related persons play fundamentally different roles in the model:

- The index patient is **the subject of the genomic test** — all clinical data, the
  prescription, the consent, and the HL7v2 message are centred on them.
- The related persons (père, mère) are **sequenced for comparison** — they appear in the
  NK1 segments and have their own genomic files, but they are not the subject of the
  clinical workflow.

Merging them into a single class would require a discriminator field ("is this person the
index patient or a relative?"), turning a clear semantic boundary into an implicit
convention. FHIR itself maintains this separation for the same reason: `Patient` and
`RelatedPerson` are distinct resources, with `RelatedPerson.patient` providing the
explicit link. Our model mirrors that boundary.

---

## `ParsedReportData` → `CompositionData`

**FHIR resource chosen:** `Composition`
**FHIR URL:** https://hl7.org/fhir/R4/composition.html

`ParsedReportData` was a purely internal name for the aggregate root — the top-level
object holding all parsed data for a single genomic report. It had no alignment with any
standard terminology.

### Candidates considered

**`DocumentReference`** (original annotation in the code) — **Not chosen as the primary mapping.**
`DocumentReference` is used to reference an existing document from outside FHIR (e.g., a
PDF or a CDA document). It is appropriate when the genomic report already exists as an
external document and needs to be indexed. Since our model *constructs* the report content
rather than referencing a pre-existing document, `DocumentReference` is not the right fit
at the content level.
https://hl7.org/fhir/R4/documentreference.html

**`Composition`** — **Chosen.**
`Composition` is the foundational FHIR structure for assembled clinical documents. It
holds structured sections that reference other resources — exactly what `CompositionData`
does (it aggregates `PatientData`, `CareTeamData`, `ConditionData`, `ServiceRequest`,
`PeriodData`, `ObservationData`, `ConsentData`, and `RelatedPersonData` into a single
report). The `Composition.subject` maps to the index patient, and `Composition.section`
can reference all other resources, matching our nested dataclass structure.
https://hl7.org/fhir/R4/composition.html
