"""Source documents fed to import scenarios, shared by both runners.

These are inputs to be imported, not proposals — they carry no mechanical
oracle, so they live here rather than in `tests/fixtures/`. Personal data is
obviously fake, following the same rule as the fixture corpus.

Kept free of eval-framework imports so the dev runner can use them too.
"""

MESSY_SOURCE = """PROPOSAL - CONFIDENTIAL - INTERNAL USE ONLY
Student: Erika Musterfrau, Matriculation 00000000, erika@example.org
Supervisor: Prof. Example (prof@example.org)

1 Motivation
Smart irrigation wastes water because schedules ignore soil data. Our project
will build a better controller. We reference the survey by Rivera et al. 2023
(doi:10.5555/fake.survey) and the LoRa study of Tanaka 2024.

2 Goals and Approach
We will implement the controller and test it on a farm.

3 Work Plan and Milestones
Start October 2026, submission March 2027.
Month 1-2 literature, month 3-5 implementation, month 6 writing.
"""

MESSY_REQUEST = (
    "I could not attach the PDF, so here is the pasted text of my old "
    "proposal — please import it:\n\n" + MESSY_SOURCE
)
