# Split of draft-ramadan-moq-fec-01 into a core and companion drafts

Status: in progress, 29 October 2026. Proposed by Marc E. Fiuczynski on 28 October 2026 (mail with
`fec-core-proposal.zip`: a README with the split table and a first cut of the core draft, drafted from -01 and
the design notes and not yet read end to end by him). Carried out on the owner's direction. Nothing here is
posted to the IETF; the posted -01 drafts stay as they are, in the archive and in this repository.

## The documents

| Document | File | Authors | Content |
|---|---|---|---|
| Core mechanism | `draft-ramadan-moq-fec-core-00` | Ramadan, Fiuczynski | Scheme-independent and packaging-independent: scheme requirements, FEC instances, the Protected Object Unit (`moq-object-v1`), SS_IDs and short blocks, object and symbol carriage, repair tracks and layers, the Repair FEC Payload ID, repair Group IDs and FETCH, equal and unequal protection, recovery, the configuration data model, priority, relay considerations, security, IANA registries |
| Block FEC schemes | `draft-ramadan-moq-fec-block-codes-00` | Ramadan | Reed-Solomon over GF(2^8) (mandatory to implement) and RaptorQ (optional): construction, parameters, bounds, layers, decoding cost, test vectors, registrations |
| Catalog binding | `draft-ramadan-moq-fec-catalog-00` | Ramadan | The MSF and CMSF encoding of the core's data model: the `fec` array of instances, the repair and symbol track fields, packaging values, validation, unknown keys, worked catalog |
| FEC for multicast delivery | `draft-ramadan-moq-fec-multicast-00` | Ramadan | Hybrid unicast and multicast delivery, repair-only multicast endpoints, provisional symbols under bc-provenance, the receiver repair policy, multicast FEC security |
| MMT packaging, revision -02 | `draft-ramadan-moq-mmt-02` | Ramadan | Absorbs the `iso-ssbg1-v1` block profile, the Source FEC Payload ID trailer, the MMTP repair packet, the keyframe overlay and its header extension, the ISO interleaving window, ATSC 3.0 and ARIB interworking, the A3SA signed region |
| Multicast delivery, revision -02 | `draft-ramadan-moq-multicast-02` | Ramadan | No content change beyond re-pointing its FEC citations and defining `params_hash` over the binding's per-instance fields |
| Sliding-window schemes | not written | | Marc's proposal names it as research-grade text to be written with Emmanuel Lochin; the core reserves the class |
| Content-aware protection | not written | | Optional and informative in Marc's proposal; the core's guidance on classification without payload access covers the principle |

Names are placeholders, as Marc's README says; the author lists are his for the core and the owner's for the rest.

## Where each section of -01 went

| -01 section | Destination |
|---|---|
| 1, 3, 6-6.3.2, 6.3.5, 6.3.7-6.3.9, 7.2, 7.4-7.6, 8-8.4, 9, 10, 13 (direct cmaf), 14.1-14.3, 14.6, 15.1, 15.2 (registry), 15.4 (registry, `moq-object-v1`), Appendix A | core (Marc's text, with the -01 rules the mapping found missing restored and listed in its Changes appendix) |
| 2 (OTI), 4-4.5, 6.3.2 (overhead numbers), 6.3.3 (scheme part), 6.3.4 rules 6 and 12, 7.1/7.2/7.4 scheme clauses, 14.7, 15.2 (the two registrations), Appendix C | block codes |
| 5-5.2 (encoding), 6.1 (naming convention), 6.3 (republish rule), 6.3.4 (defect table), 13 (CMSF), 15.3, Appendix B | catalog binding |
| 5.1/5.2 multicast notes, 6.3.6, 6.3.9 (admitted-packet anchoring), 7.4 (provisional blocks), 11-11.4.6, 14.3 (join authorization), 14.4 | FEC for multicast delivery |
| 2 (overlay, iso-ssbg1 clauses), 5.1/5.1.1/5.1.2/5.2/5.3 MMTP clauses, 6.3 (AL-FEC), 6.3.4 rule 10, 6.4-6.4.3, 7.1 (MMTP form), 7.3, 8.3/8.4 MMTP clauses, 8.5, 8.5.1, 12, 13 (mmtp rendition), 14.5, 15.4 (`iso-ssbg1-v1`), Appendix B (MPU arithmetic) | MMT -02 |
| Appendix D, the ROUTE scope-out sentence, the closed-list sentence of 4.3, "none" as a scheme identifier | retired |

The mapping evidence (every heading of -01 with its line range and destination, the orphans the split would
otherwise have lost, and the review of Marc's core against -01) was produced on 29 October 2026 and is
summarised in each draft's Changes appendix.

## Decisions taken in the split

1. The split follows Marc's table. Where his table named no home for -01 text (Section 9's conformance
   cases, the worked rebuild example, the message flows, the scheme registrations, the priority range rule, the
   defect table, the `enhancementRepair` tombstone, the `/repair` naming convention, the multicast scoping of
   `moq-object-v1`), the text went to the document that owns the mechanism it belongs to, as the table above
   shows, rather than being dropped.
2. Reed-Solomon stays mandatory to implement and RaptorQ optional; the core says so and cites the block-codes
   draft. Marc's core had left the choice to the working group.
3. Cross-document citations name sections of the new documents, never of -01. Each draft cites the core for
   every generic rule rather than restating it.
4. The core keeps Marc's editor's notes and open questions, and his acknowledgements.
5. The posted -01 files are untouched. The `-02` revisions of the MMT and multicast drafts replace their `-01`
   files in the repository, as earlier revisions did.

## Procedure

Each draft builds with the recipe of `docs/ietf-submissions.md` (mmark 2.2.48, xmllint, xml2rfc, idnits in
submission mode) and the repository tests cover the set: the Reed-Solomon vectors run against every draft that
publishes them, the catalog sweeps accept the binding's shape, the optional `tests/test_raptorq_vectors.py`, added with the
block-codes draft, recomputes the RaptorQ vectors when the `raptorq` package is installed, and `tests/test_fec_split.py` checks front
matter, heading ids, cross-document section pointers, reference blocks, informative text, JSON examples and the
placement of the scheme bounds.
