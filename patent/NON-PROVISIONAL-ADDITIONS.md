# Claims to Add in Non-Provisional Filing (within 12 months)

## Progressive/Scalable Codec Personalization with Per-Layer FEC

**Dependent on:** Application 2, Claims 7-9 (hierarchical catalog, per-track algorithm)

**Claim sketch:**
The method of Claim 7/9, wherein different FEC configurations are
applied to different layers of a progressive or scalable codec
(e.g., SVC, AV1 scalability modes, LCEVC, MPEG-5 Part 2), wherein:
- a base layer track receives a first FEC algorithm with a first
  repair ratio (e.g., raptorq with 50% repair overhead);
- one or more enhancement layer tracks receive a second, lighter
  FEC algorithm or lower repair ratio (e.g., raptorq with 12.5%
  repair, or "none");
- the catalog hierarchical defaults specify base-layer protection,
  and per-track overrides reduce protection for enhancement layers;
- a receiver that experiences loss recovers the base layer via FEC
  while gracefully degrading enhancement layers.

**Distinction from ISO 23008-1 Amd 1 (2025) Adaptive FEC:**
ISO adaptive FEC (C.2.4) assigns priority classes WITHIN a single
FEC block (same source block, different repair sub-blocks per class).
This claim assigns different FEC configurations ACROSS tracks
(per-layer), which:
- Works across heterogeneous transports (base via multicast+FEC,
  enhancement via unicast best-effort)
- Enables personalization (different viewers get different
  enhancement layers based on bandwidth/device)
- Uses catalog signaling (not MMTP-level packet priority bits)

**Prior art gap:** ISO adaptive FEC is intra-block. This is inter-track.
No standard combines progressive codecs with per-track FEC catalog
configuration across heterogeneous transport paths.

## Priority Date
Provisionals filed 2026-07-10 (three applications; USPTO filing receipts are
authoritative for numbers and exact date). Non-provisional or PCT due
**2027-07-10** (filing date + 12 months). Counsel checkpoint by 2027-05-10.
The earlier April 11, 2027 date belonged to the never-filed April package.

## Additional Claims Queued 2026-07-17 (post spec-batch + fleet audit)

Full drafting notes live in the "Patent Updates — 2026-07-17" review doc
(shared Drive) and in PATENT-CLAIMS.md "CONVERSION UPDATES".

- **Derived OTI (dependent under Claim F):** receiver derives complete
  RFC 6330 OTI as F = K x T, Z = 1, N = 1, Al = 8 from two catalog
  integers; no OTI octets on the wire (distinct from FLUTE FDT).
- **Media-time block agreement (sibling to A4):** Group Number Formula
  floor(presentation_ticks / groupDurationTicks) with shared
  presentation-epoch and negative clamp, combined with SBN = floor(G / D),
  yields identical FEC block boundaries across independent encoders with
  no NTP dependency.
- **IFC publishing-side subgroup keying (IFC claim set):** mapping
  intrinsic MFU identity (timed: movie_fragment_sequence_number +
  sample_number; non-timed: Item_ID; Subgroup 0 = MPU metadata) onto
  transport subgroup identifiers, enabling relays to retain/replay/drop
  at MFU granularity without parsing media.
- **Interleave-window semantics (dependent under A/D):** the millisecond
  window is the full block span, making recovery latency K-independent;
  D = round(interleaveDepthMs / groupDurationMs).
- **bc-provenance source authentication (candidate NEW application):**
  per-group BLAKE3 manifest signing over MoQ (Ed25519, previousKey
  rotation, compaction, enforcement modes). File before the rewritten
  multicast auth section publishes.
- **DSR replay gate (dependent under Application 2):** proof-of-group-start
  admission for late-join replay, including init-led group starts under
  datagram loss.
- **Claim B reduction-to-practice (unblocks early conversion):** multi-path
  combining is implemented — libmmt fec-manager feedSymbolFromSource keys
  (packetId, SBN, ESI) first-arrival-wins across multicast/MoQ paths into
  a single per-block decoder; deployed configuration matches Claim B1
  (multicast source + reliable-QUIC repair).

---

# Application 3 — Wallet-Rooted Device Certificate Issuance (64/109,478)

**Everything above this line concerns Applications 1–2 (FEC / broadcast
bridge). Application 3 is a separate invention family — device identity and
PKI — and had no conversion notes until now.**

Filed 2026-07-10 as "Wallet-Rooted Device Certificate Issuance with Offline
Claim Verification and Threshold-Signature Custody." Same 2027-07-10 deadline,
same 2027-05-10 counsel checkpoint.

## Conversion notes recorded at filing

From the filing comment on Paperclip BLO-14673:

- Fold the claim-sketch appendix into counsel's draft.
- **§4 (browser mTLS enablement) strengthens when IWA Phase 0 lands** — the
  WASM TLS client. Until then that section describes an enabling mechanism
  we have not reduced to practice.

## Developments since 2026-07-10 — raw material, NOT a novelty assessment

⚠ **Read this as an engineering changelog for counsel to triage, not as a
claim of patentability.** Whether any item is new matter, already covered by
the provisional's disclosure, or unpatentable is counsel's call. Several of
these were design decisions rather than implementations, and a provisional's
priority only reaches what it actually disclosed.

**Certificate identity extraction — a third path, with explicit precedence.**
The deployed system reads subscriber identity from two different places and
they disagree: `AuthenticateMTLS` reads the UID OID
`0.9.2342.19200300.100.1.1`, while `deliverySessionMTLSRelayID` reads
`Subject.CommonName`. Neither reads a **URI SAN**. Work in progress adds a
third extractor reading the URI SAN and documents a precedence order among
the three. The wallet-slug SAN in §2 of the specification is the URI-SAN
mechanism; the operational question of *precedence when multiple identity
encodings are present in one certificate* is not something the provisional
addresses.

**Fail-closed parsing of the identity URI.** A separate implementation
distinguishes "no Blockcast identity URI present" from "two identity URIs
that disagree" and fails closed on the second, rather than picking one.

**Binding a credential to the node that will serve it, before issuance.**
The session-broker design binds a relay identifier into the ticket at mint
time and requires the broker to publish that binding to the serving relay
**synchronously, before the ticket is returned to the client** — so a holder
cannot present a valid credential at a node that has never been told about
it. Renewal extends validity locally and must not re-publish. A failed
publication is an error, never a fall-back to unattributed access. This is an
ordering constraint on issuance rather than a property of the certificate,
which may or may not be within the filed disclosure.

**Wallet proof as enrollment-only, with a distinct long-lived credential.**
Ratified 2026-08-08: the wallet signature authenticates *enrollment*; the
registered challenge key is the actual long-lived credential thereafter.
Deliberately **not** characterized as two-factor — the wallet is not a second
factor at authentication time because it is not present at authentication
time. If the provisional's offline-claim-token mechanism is read as covering
this separation, that reading should be made explicit at conversion.

**Credential lifetimes and concurrency, as reduced to practice.** Ticket TTL
5 minutes; certificate TTL 24 hours renewed at ~50% of life with jitter; a
cap of 3 concurrent credentials per subscriber per feed, sized for primary +
standby + migration overlap.

**Staged enforcement as a deployment property.** A three-state per-endpoint
mode (`off` / `log-only` / `enforced`) allowing certificate enforcement to be
introduced against live traffic without a flag-flip that changes
authentication for every caller at once. Likely closer to operational
practice than invention, but it is the mechanism by which the filed scheme
becomes deployable.

**Explicitly out of scope — stated so it is not claimed by accident.**
Downstream re-fan-out by an authorized holder is accepted as undetectable and
is handled as a contract term, not a technical control. Nothing in this work
detects or prevents it, and no claim should imply otherwise.

## Open item

The specification's §4 depends on browser-mTLS with non-extractable keys.
Track whether IWA Phase 0 lands before 2027-05-10 — if it does, the
enablement argument for §4 is materially stronger at conversion; if it does
not, counsel should know §4 rests on an unimplemented mechanism.

