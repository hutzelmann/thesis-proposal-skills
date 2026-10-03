# Where the supervise feedback rules come from

`proposal-supervise` checks its own claims before handing feedback over, judges the plan's workload before the tier, keeps format remarks out of the student's text, and offers cut options rather than adding work. This page records the evidence behind those rules (change `verified-scoped-supervise-feedback`, 2026-10-03), so that "why does the skill do that?" gets a citation instead of a shrug.

Two kinds of evidence carry the design.

**The skill's own run.** A real supervise run on 2026-10-03 on a Bachelor's proposal took six minutes and read no abstract and no standard's text. Fresh verifiers then confirmed about 45 distinct problems in its draft:

| Problem | Count |
|---|---|
| Claims about standards and regulations made from memory | 9 |
| Claims about the student's own references judged from titles | 10 |
| Planned work reported as missing, and quotes cut short | 13 |
| Contradictions between the opening and the strengths | 5 |
| Review vocabulary reaching the student | 8 |

Rewrites introduced 13 more, five of them verifier corrections adopted without checking. The professor had to raise the size of the plan before the skill did. On the same proposal's earlier version (2026-09-01), the professor had already rejected the same format paragraph once before.

**The literature.** Every source below was resolved through Crossref, doi.org or the publisher's page on 2026-10-03, and was read at least to its abstract. The run's own notes on which full texts were read are not reproduced here; where only an abstract supports a claim, the claim stays at what an abstract can say.

## Few points, each with its reason

- **Prioritize, and check the total work the points add up to.** The supervision literature favours a few prioritized issues over exhaustive lists. Sources:
  - Shute, *Focus on Formative Feedback*, Review of Educational Research 78(1), 2008 (https://doi.org/10.3102/0034654307313795).
  - Nicol & Macfarlane-Dick, Studies in Higher Education 31(2), 2006 (https://doi.org/10.1080/03075070600572090).
  - Bitchener, Basturkmen, East & Meyer, *Best Practice in Supervisor Feedback to Thesis Students*, Ako Aotearoa, 2011, questionnaires from 35 supervisors and 53 students with follow-up interviews of a subset (https://ako.ac.nz/assets/Knowledge-centre/NPF-08-002-Best-Practice-in-Supervisor-Feedback-to-Thesis-Writers/RESEARCH-REPORT-Best-Practice-in-Supervisor-Feedback-to-Thesis-Students.pdf).

  No study gives an optimal number of points or an optimal length. The three-to-five cap and the 1,200-word target are design choices consistent with this guidance, not derived from it.
- **Give the reason behind each judgement, and look forward.** The design follows the feed-up/feed-back/feed-forward model of Hattie & Timperley, *The Power of Feedback*, Review of Educational Research 77(1), 2007 (https://doi.org/10.3102/003465430298487), with meta-analytic support from Wisniewski, Zierer & Hattie, Frontiers in Psychology 10, 2020 (https://doi.org/10.3389/fpsyg.2019.03087). A bare "RQ2 is sound as it stands" is the failure this rule removes.
- **Diagnose directly, leave the remedy and the choice with the student.**
  - Straub, College Composition and Communication 47(2), 1996, on directive and facilitative commentary (https://doi.org/10.2307/358794).
  - Winstone et al., Educational Psychologist 52(1), 2017, on learners' agency in using feedback (https://doi.org/10.1080/00461520.2016.1207538).

  The skill's rules follow from these: "direction, not a prescribed fix", and the cut options with the choice left to the student.
- **Feedback about the task, not the person.** Kluger & DeNisi, Psychological Bulletin 119(2), 1996 (https://doi.org/10.1037/0033-2909.119.2.254); Hattie & Timperley 2007. This matches the voice block and the strengths block's "information, not encouragement".
- **Substance before surface.** Sommers, *Responding to Student Writing*, College Composition and Communication 33(2), 1982 (https://doi.org/10.58680/ccc198215854), observes that surface marks beside content questions send a mixed message about priorities. The Ako report records supervisors who leave the systematic clean-up to the student. This is why format and convention findings stay in the review.
- **Accuracy decides credibility.**
  - Ferris, TESOL Quarterly 31(2), 1997 (https://doi.org/10.2307/3588049): students act on most comments, and some comments make the text worse.
  - Telio, Regehr & Ajjawi, Medical Education 50(9), 2016 (https://doi.org/10.1111/medu.13063): learners judge a feedback source's credibility and discount it accordingly.

  No study measures the effect of supervisors' factual errors in thesis feedback directly; the inference is the design's.

## Workload belongs to the supervisor, cuts to the student

- **Limiting scope is the supervisor's duty, and workload is the program's.**
  - The ECTS Users' Guide 2015 sets 25–30 hours per credit (https://doi.org/10.2766/87192).
  - The KMK model ordinance, §8, gives Bachelor's theses 6–12 credits (https://www.kmk.org/fileadmin/Dateien/veroeffentlichungen_beschluesse/2024/2024_11_21-Musterrechtsverordnung.pdf).
  - Examination regulations such as Mainz's B.Sc. Informatik require the supervisor to limit topic and scope so the deadline can be met (https://download.uni-mainz.de/verwaltung-sl/ordnungen/PO_BSc_Informatik_aktuell.pdf).

  The ranges differ by a factor of two within one level, so the skill takes no workload constant of its own (see also `docs/degree-level-sources.md`).
- **List the packages; name the unknown sizes.**
  - Kruger & Evans, Journal of Experimental Social Psychology 40(5), 2004 (https://doi.org/10.1016/j.jesp.2003.11.001): unpacking a task into parts reduces the planning fallacy.
  - Buehler, Griffin & Ross, JPSP 67(3), 1994 (https://doi.org/10.1037/0022-3514.67.3.366), and Halkjelsvik & Jørgensen, Psychological Bulletin 138(2), 2012 (https://doi.org/10.1037/a0025996), on systematically optimistic time estimates.

  This is why the review carries a work-package table with unknowns rather than a judgement sentence. It also explains why the estimates are labelled estimates and no overrun factor is applied.
- **Cut to one core, keep the evaluation inside it.**
  - Crossley & Maini, *Ten simple rules for early-career researchers supervising short-term student projects*, PLOS Computational Biology 21(11), 2025 (https://doi.org/10.1371/journal.pcbi.1013690).
  - Knauss, ICSE-SEET 2021, on separating the thesis from what an industry partner wants delivered (https://doi.org/10.1109/ICSE-SEET52601.2021.00021).
- **Offer options, keep the verdict clear.**
  - Overall, Deane & Peterson, HERD 30(6), 2011 (https://doi.org/10.1080/07294360.2010.535508): autonomy support combined with academic guidance.
  - de Kleijn et al., Studies in Higher Education 37(8), 2012 (https://doi.org/10.1080/03075079.2011.556717): the relation between supervisor control and outcomes is not monotonic.

  The skill states plainly that the plan must shrink and lets the student choose how. No study measures supervisor-added scope creep. The net-workload budget is an inference from the session and from the prioritization literature above.

## Check claims against sources, with a fresh pass

- **Self-correction without external evidence fails.**
  - Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*, ICLR 2024 (https://arxiv.org/abs/2310.01798).
  - Kamoi et al., TACL 12, 2024 (https://doi.org/10.1162/tacl_a_00713).
  - Panickssery, Bowman & Feng, NeurIPS 2024, on evaluators favouring their own generations (https://doi.org/10.52202/079017-2197).

  This is why the skill checks against fetched sources and gives one fresh verifier the finished text. Rereading the draft is not the check.
- **Split the text into claims and check each one separately.**
  - Min et al., *FActScore*, EMNLP 2023 (https://doi.org/10.18653/v1/2023.emnlp-main.741).
  - Wei et al., *Long-form factuality in large language models*, NeurIPS 2024 (https://arxiv.org/abs/2403.18802).
  - Dhuliawala et al., *Chain-of-Verification*, Findings of ACL 2024 (https://doi.org/10.18653/v1/2024.findings-acl.212).

  This is the basis for the claim ledger and its classes. When no helper runs, the questions are asked one at a time.
- **References and legal claims are where models fail.**
  - Walters & Wilder, Scientific Reports 13, 2023, on fabricated and erroneous citations (https://doi.org/10.1038/s41598-023-41032-5).
  - Dahl et al., *Large Legal Fictions*, Journal of Legal Analysis 16(1), 2024 (https://doi.org/10.1093/jla/laae003).

  These are behind the rules that the student's references are judged by their abstracts and that no clause of a standard or regulation comes from memory.
- **"Missing" claims need a search, not recall.** Liu et al., *Lost in the Middle*, TACL 12, 2024 (https://doi.org/10.1162/tacl_a_00638). Jergas & Baethge, PeerJ 3, 2015, on how often quotations misstate their source (https://doi.org/10.7717/peerj.1364).
- **LLM feedback is useful but weakest on novelty and method design.** Liang et al., NEJM AI 1(8), 2024 (https://doi.org/10.1056/AIoa2400196). The professor stays the accountable author, and the skill stays draft-only.
- **Report the exceptions, briefly.**
  - Buçinca, Malaya & Gajos, Proc. ACM HCI 5 (CSCW1), 2021 (https://doi.org/10.1145/3449287).
  - Kim et al., FAccT 2024 (https://doi.org/10.1145/3630106.3658941).

  Cognitive forcing and expressed uncertainty reduce overreliance, but long verification records get skipped. That is why the review's verification section lists only the contradicted and unverifiable claims, and the wrap-up names the unverified ones.

## Known gaps

- No study measures error rates in LLM-drafted thesis-supervisor feedback, or compares a fresh verifier with same-context self-review on long-form feedback. The case for the verifier rests on the session above and on the indirect evidence in the last section.
- No empirical basis exists for a verification budget in claims, searches or tokens. The skill bounds it by consequence: load-bearing claims are verified; claims that are neither load-bearing nor cheap to verify are dropped.
- The European Commission's living guidelines on generative AI in research (third version, May 2026, https://research-and-innovation.ec.europa.eu/document/download/2b6cf7e5-36ac-41cb-aab5-0d32050143dc_en?filename=ec_rtd_ai-guidelines.pdf) advise against substantial AI use when evaluating research proposals. Thesis supervision is formative rather than a funding decision. Even so, the skill keeps the professor as the accountable author: the feedback is a draft, it carries an AI disclosure, and the proposal never leaves the professor's machine as lookup text.
