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
