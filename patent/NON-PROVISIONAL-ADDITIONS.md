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
Must file non-provisional by: April 11, 2027 (12 months from provisional)
