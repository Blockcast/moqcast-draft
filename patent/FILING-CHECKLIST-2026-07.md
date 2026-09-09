# USPTO Filing Checklist — July 2026 package

**STATUS UPDATE 2026-07-17: FILED 2026-07-10 — three provisionals (App 1
FEC Methods + Appendices, App 2 Broadcast Bridge, App 3 Wallet-Cert).
Filing receipts are authoritative for application numbers and the exact
date; conversion deadline 2027-07-10. Historical pre-filing text below is
retained unchanged.**

## Filed applications (recorded 2026-08-09)

Transcribed from the filing confirmations on Paperclip BLO-14531 (Apps 1–2)
and BLO-14673 (App 3). Note the series is **64/**, not the `63/xxx,xxx` the
pre-filing text below predicted.

| App | Number | Title | Receipt (ET) | Conf # | Patent Center # |
|---|---|---|---|---|---|
| 1 | **64/109,453** | Forward Error Correction Methods for Publish/Subscribe Media Transport with Multi-Path Delivery (incl. appendices: claims A–F / A4–A6 + IFC) | 2026-07-10 21:44:05 | 3880 | 78596812 |
| 2 | **64/109,460** | Broadcast-to-Unicast Media Bridge with FEC Preservation + Hierarchical FEC Catalog Signaling | 2026-07-10 21:54 | 9637 | — |
| 3 | **64/109,478** | Wallet-Rooted Device Certificate Issuance with Offline Claim Verification and Threshold-Signature Custody | 2026-07-10 22:23:08 | 7569 | 78598593 |

All three: provisional under 35 U.S.C. 111(b), inventor Omar Ramadan,
applicant/assignee Blockcast Inc., small entity, $130 fee each.
**One shared priority date: 2026-07-10. Conversion deadline 2027-07-10.**

⚠ These are the *acknowledgement* numbers from filing. The formal Filing
Receipts under 37 CFR 1.54 issue separately — verify inventor and title data
on them in Patent Center and correct this table if they differ.

**Status (as written pre-filing): PREPARED, NOT FILED.** No provisional or non-provisional is on file as of
2026-07-10 (Patent Center check confirmed nothing under the April 11, 2026 date the
earlier drafts carried). Repo is private and no draft is on the IETF datatracker, so
no public-disclosure bar date is running. **Do not publish any moqcast draft until a
filing receipt is in hand** (IETF submission is an absolute worldwide disclosure).

## Package contents (this directory)

| File | Role |
|---|---|
| `APPLICATION-1-FEC-METHODS.pdf` | Specification 1: FEC methods for pub/sub media transport with multi-path delivery (Claims A–D, F basis) |
| `APP1-FIGURES.pdf` | Figures for Application 1 |
| `APPLICATION-1-APPENDICES.pdf` | **Filed with App 1**: Appendix A = prioritized claim set (A–F + A4–A6 + prior-art analysis); Appendices B–D = Intrinsic Fragment Coordinate design disclosure + draft claims + reassembly section |
| `APPLICATION-2-BROADCAST-BRIDGE.pdf` | Specification 2: broadcast-to-unicast bridge with FEC preservation + hierarchical FEC catalog signaling (Claims E, F basis) |
| `APP2-FIGURES.pdf` | Figures for Application 2 |
| `APPLICATION-3-WALLET-CERT.pdf` | Specification 3: wallet-rooted device certificate issuance — offline claim token, wallet-slug SAN, MPC transparency, wallet-gated rotation, browser mTLS with non-extractable keys. **0 drawing sheets.** Separate invention family (device identity / PKI), not a continuation of Apps 1–2 |
| `NON-PROVISIONAL-ADDITIONS.md` | Claims to add at conversion (per-layer progressive-codec FEC); recompute the 12-month deadline from the ACTUAL filing date |

## Cover sheet data (form SB/16, one per application)

- Inventor: Omar Ramadan (add residence city/state on the form)
- Applicant/Assignee: Blockcast, Inc.
- Title App 1: "Forward Error Correction Methods for Publish/Subscribe Media
  Transport with Multi-Path Delivery"
- Title App 2: "Broadcast-to-Unicast Media Bridge with FEC Preservation and
  Hierarchical FEC Catalog Signaling"
- Entity status: small entity presumed (verify: <500 employees, no license
  obligations to a large entity). Micro entity unlikely (corporate applicant +
  gross-income test).
- Attachments App 1: specification PDF + figures PDF + appendices PDF
- Attachments App 2: specification PDF + figures PDF

## Filing steps (Patent Center, ~30 min total)

1. Sign in at patentcenter.uspto.gov (USPTO.gov account; register if needed).
2. "New submission" → "Provisional application under 35 U.S.C. 111(b)".
3. Upload the PDFs for App 1 (spec + figures + appendices) + completed SB/16.
4. Pay provisional filing fee (small entity ≈ $130; Patent Center shows the exact
   current amount at checkout).
5. Repeat for App 2.
6. Save both filing receipts (application numbers are 63/xxx,xxx). Provisionals
   are never published or examined.
   <!-- Superseded 2026-08-09: three applications were filed, not two, and the
        assigned series was 64/, not 63/. Actuals are in "Filed applications"
        at the top of this file. Left unedited as pre-filing history. -->

## Immediately after filing

1. Comment application numbers + actual filing date on **BLO-14531**, close it →
   unblocks **BLO-14541** (IETF publication; still needs BLO-14538 spec edits).
2. Update `NON-PROVISIONAL-ADDITIONS.md` deadline: non-provisional or PCT due
   **filing date + 12 months** (can convert earlier — see BLO-14542).
3. Calendar the 12-month date with a 2-month-early counsel checkpoint.

## Provisional vs. direct non-provisional (decision record)

Provisional-first chosen because: (1) Claim B (multi-path combining) has no
implementation yet — H1/PathMux (BLO-14536) is its reduction-to-practice and will
materially improve the enablement + claim language; (2) IFC claims are explicitly
draft-status; (3) the catalog fields the claims recite are being renamed/changed
this month (workstreams A/B/F) — non-provisional claims filed now would recite a
moving target, and post-filing additions require a CIP with a later priority date
anyway; (4) NON-PROVISIONAL-ADDITIONS.md already plans claims to ADD at conversion;
(5) 12 months of additional effective patent term at the end of life; (6) $130 and
same-day unblocks publication vs. weeks + counsel fees. Conversion can happen ANY
time within 12 months — early conversion (+ Track One if speed matters) remains
available once H1 lands and spec fields settle.

Patent-safe spec changes already vetted (no claim recites them): dropping
FEC_CONFIG control message (Claim F is catalog-based — strengthened), and moving
the repair header to the ISO 23008-1 §C.5.3 payload-ID form.
