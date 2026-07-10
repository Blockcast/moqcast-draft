# APPENDICES TO APPLICATION 1 — FEC METHODS

Filed as part of the provisional disclosure of APPLICATION-1-FEC-METHODS.
Each appendix is incorporated in its entirety into the specification.

---

# APPENDIX A — Prioritized Claim Set (Claims A–F, A4–A6) with Prior-Art Analysis

# Patent Claims — Blockcast MoQ/MMTP/FEC Innovations

## Prior Art Research Summary

Research conducted across RFC corpus, USPTO/EPO patent databases, academic
literature, and ATSC/3GPP/DVB standards. Per-claim analysis below.

---

## TOP 6 CLAIMS (Prioritized by Novelty × Impact)

---

### CLAIM A: ESI Derivation from Publish/Subscribe Object Identifiers

**Prior Art Risk: LOW — strongest candidate**

**Independent Claim:**
A method for forward error correction in a publish/subscribe media
transport system, comprising:

(a) receiving a media object identified by a group identifier G and an
    object identifier O within a named track of a publish/subscribe
    session;

(b) computing an interleave depth D in media units from a time-based
    interleave parameter expressed in milliseconds and a media frame
    duration, wherein said millisecond unit decouples the interleave
    depth from media frame rate;

(c) deriving a Source Block Number SBN = floor(G / D);

(d) deriving an Encoding Symbol ID
    ESI = (G - SBN * D) * ceil(K / D) + O,
    where K is the number of source symbols per FEC block;

(e) using said SBN and ESI to identify the symbol's position within a
    FEC block for encoding or decoding per RFC 6330;

(f) wherein a flat Source Symbol ID SS_ID = SBN * K + ESI is
    independently derivable from said SBN and ESI, and said SS_ID is
    identical to the Source FEC Payload ID carried in MMTP multicast
    packets per ISO 23008-1 Section C.5.2, enabling a receiver to
    combine symbols received via the publish/subscribe transport with
    symbols received via multicast into the same FEC block.

**Dependent Claims:**

A1. The method of Claim A wherein the interleave depth parameter is
    specified in milliseconds in a catalog document, and the receiver
    converts to media units using detected frame duration, making the
    FEC block mapping independent of video frame rate, audio sample
    rate, or other media-specific timing.

A2. The method of Claim A wherein a relay node performs said derivation
    to bridge between a multicast transport carrying SS_ID and a
    publish/subscribe transport carrying (G, O), translating FEC
    coordinates between transport domains without modifying the
    underlying FEC block structure.

A3. The method of Claim A wherein the same derivation is applied
    independently at multiple receivers and relay nodes, producing
    identical (SBN, ESI) coordinates for the same media packet
    regardless of which transport path delivered it.

A4. The method of Claim A wherein the Source Block Number SBN is
    derived from a shared wall-clock reference as
    SBN = floor((ntp_time - epoch) / block_duration), where
    block_duration = K * GOP_duration * D, and epoch is a session
    start time signaled in the catalog or AL-FEC signaling message,
    enabling multiple encoders (hot standby primary/backup or
    simulcast bitrate tiers) to independently produce identical FEC
    block boundaries without direct inter-encoder synchronization,
    such that a receiver combining symbols from any encoder into the
    same FEC block achieves correct recovery.

A5. The method of Claim A4 wherein the Source FEC Payload ID (SS_ID)
    carried in MMTP source packets is decoupled from the MMTP
    packet_sequence_number (PSN), such that an encoder failover that
    restarts PSN does not disrupt the FEC block namespace, and
    receivers identify block membership exclusively from SS_ID
    regardless of PSN discontinuities.

A6. The method of Claim A wherein the Source FEC Payload ID (SS_ID)
    is carried redundantly in a broadcast hint track sample
    (source_fec_payload_id field per ISO 23008-1) that falls within
    the ATSC 3.0 Signed Application (A3SA) signed region per ATSC
    A/360 Section 5.2.2.5, enabling receivers to verify the
    integrity of FEC block assignment using broadcast digital
    signatures without relying on the unsigned trailing 4-byte
    Source FEC Payload ID appended to asset packets.

**Prior Art Analysis:**
- RFC 6330 §4.4: defines SBN/ESI as FEC coordinates but does NOT define
  how they map to any transport-layer identifier. Mapping left to the
  Content Delivery Protocol.
- RFC 5775/6726 (ALC/FLUTE): TOI-based mapping for file objects. No
  formula involving interleave depth or real-time media group/object IDs.
- ISO 23008-1 Annex C: defines SS_ID as flat counter with
  SBN = floor(SS_ID / K), ESI = SS_ID % K. Does NOT bridge to any
  pub/sub transport.
- US9270299B2 (Qualcomm): flexible source block mapping. Dynamic
  assignment, not deterministic formula from transport IDs.
- **Gap**: No prior art maps pub/sub (group_id, object_id) to FEC
  (SBN, ESI) with time-based interleave. The bridging formula that
  produces identical coordinates across MoQ QUIC and MMTP multicast
  is novel.

**Implementation Evidence:**
- Draft: §8.3 (Source Symbol ESI Derivation)
- Code: `libmmt/mmt-fec/src/raptorq.rs` line 101
  `global_ss_id = block_id * K + symbol_id`
- Tests: 12 RaptorQ tests pass including recovery with missing source

---

### CLAIM B: Multi-Path FEC Symbol Combining Across Heterogeneous Transports

**Prior Art Risk: MEDIUM — novel combination of known techniques**

**Independent Claim:**
A method for recovering media data in a streaming system, comprising:

(a) receiving one or more source symbols via a first transport protocol
    selected from: reliable QUIC streams, unreliable QUIC datagrams,
    or multicast UDP;

(b) receiving one or more repair symbols via a second transport
    protocol different from said first transport protocol;

(c) for each received symbol, deriving FEC coordinates (SBN, ESI)
    that are identical regardless of which transport protocol delivered
    the symbol, using a deterministic derivation from the symbol's
    transport-layer identifier;

(d) deduplicating symbols received via multiple transport paths using
    said (SBN, ESI) coordinates as a uniqueness key;

(e) combining deduplicated source and repair symbols from said
    heterogeneous transport protocols into a single FEC block;

(f) performing FEC decoding on said combined block to recover lost
    source symbols when the total number of received symbols
    (source + repair) meets or exceeds K.

**Dependent Claims:**

B1. The method of Claim B wherein source symbols are received via
    multicast UDP and repair symbols are received via reliable QUIC,
    enabling FEC recovery where the unreliable multicast path provides
    bulk source data and the reliable unicast path provides targeted
    repair.

B2. The method of Claim B wherein a receiver maintains a single FEC
    decoder instance per source block that accepts symbols from any
    transport path, and said decoder produces recovered data
    identically regardless of which paths contributed symbols.

B3. The method of Claim B wherein a receiver dynamically switches its
    primary source from one transport protocol to another while
    maintaining FEC block continuity, such that symbols received before
    and after the switch contribute to the same FEC block.

**Prior Art Analysis:**
- US8787153B2 (Cisco): FEC with path diversity — sends source on one
  path, repair on another. CLOSEST prior art. But addresses spatial
  diversity between two paths of the SAME transport type (two IP
  routes), NOT heterogeneous transports (UDP multicast vs QUIC).
- 3GPP TS 26.346 (eMBMS): unicast HTTP used to fetch missing symbols
  after multicast. Retry/request mechanism, NOT real-time combining.
- ATSC 3.0 A/331: broadband HTTP unicast repair as fallback. Same
  retry pattern as 3GPP.
- draft-navarre-quic-flexicast: combines unicast+multicast in QUIC.
  Both paths use QUIC — not heterogeneous transport.
- **Gap**: Real-time symbol combining where one path is reliable QUIC
  and the other is unreliable multicast UDP, unified by shared FEC
  coordinates. No prior art addresses this specific combination.

**Implementation Evidence:**
- Draft: §8.3, §11.1
- Code: `libmmt/packages/container/src/media-router.ts` (source
  arbitration), `fec-manager.ts` (block combining)

---

### CLAIM C: Hybrid Multicast-Unicast Source Arbitration with FEC-Aware Switching

**Prior Art Risk: MEDIUM — novel FEC-aware aspects over known switching**

**Independent Claim:**
A method for media reception in a hybrid delivery system, comprising:

(a) subscribing to a media track via a unicast publish/subscribe
    transport;

(b) simultaneously initiating a multicast group join for the same
    media content;

(c) receiving and rendering media from the unicast transport during
    a multicast join period, providing zero-latency startup;

(d) upon receiving a video keyframe (random access point) via the
    multicast transport, activating multicast as the primary media
    source and suppressing duplicate unicast frames;

(e) during a transition period between unicast and multicast primary
    sources, injecting FEC repair symbols received from the unicast
    transport into FEC blocks whose source symbols were received from
    the multicast transport, enabling cross-transport FEC recovery;

(f) applying hysteresis to the transport switching decision, wherein
    the receiver switches away from multicast only after detecting
    sustained loss exceeding a threshold, and switches back to
    multicast only after stable reception for a configurable period;

(g) upon detecting sustained multicast failure, failing back to
    unicast by re-subscribing with a LatestGroup delivery preference
    to resynchronize to the current media position.

**Dependent Claims:**

C1. The method of Claim C wherein audio multicast activation is gated
    on a separate timer independent of video, allowing audio to
    activate via multicast even if video multicast has not yet
    delivered a keyframe.

C2. The method of Claim C wherein said FEC repair symbol injection
    (step e) uses the same FEC block coordinates derived from the
    ESI derivation formula of Claim A, ensuring symbols from both
    transport paths are correctly assigned to the same FEC block.

C3. The method of Claim C wherein a FEC block lifecycle state machine
    tracks the completeness of each block across both transport paths,
    and said state machine determines when to attempt FEC recovery
    based on combined symbol counts from both transports.

**Prior Art Analysis:**
- US20060200576A1 (Cisco): simultaneous unicast+multicast until
  duplicate frames buffered, then switch. Does NOT address FEC-aware
  switching or keyframe gating.
- US7788393B2 (Cisco): increases unicast rate to buffer ahead, then
  switch to multicast. Buffer management, NOT FEC awareness.
- EP2013987A1: staggercasting with FEC for handover. Server-side
  technique (shifted streams), NOT receiver-side arbitration.
- 3GPP eMBMS: network-initiated handover (eNodeB decides), NOT
  receiver-side FEC-aware arbitration.
- **Gap**: FEC-aware keyframe gating, cross-transport symbol injection
  during transition, receiver-side FEC block completeness-based
  arbitration. These specific FEC mechanisms are not in any found
  prior art.

**Implementation Evidence:**
- Draft: draft-ramadan-moq-multicast-00 §4.1
- Code: `libmmt/packages/container/src/media-router.ts`

---

### CLAIM D: FEC Block Lifecycle State Machine with Codec-Aware Timeout

**Prior Art Risk: LOW — genuinely novel**

**Independent Claim:**
A method for managing forward error correction decoding in a media
receiver, comprising:

(a) maintaining per-block state with three mutually exclusive outcomes:
    - clean: all K source symbols received without loss;
    - recovered: fewer than K source symbols received but FEC decoding
      using repair symbols successfully recovered the block;
    - failed: a timeout expired with insufficient symbols for recovery;

(b) starting a block timeout upon receipt of the first source symbol
    for said block, not upon block creation or first repair receipt;

(c) computing said timeout dynamically as a function of:
    - the interleave depth (number of media frames per FEC block),
    - the detected media frame rate, and
    - a configurable safety multiplier;

(d) marking a block as clean when K source symbols are received before
    the timeout, bypassing FEC decoding entirely for lossless blocks;

(e) attempting FEC decoding when repair symbols arrive for a block
    that has fewer than K source symbols;

(f) marking a block as failed when the timeout expires with fewer
    than K total symbols (source + repair);

(g) maintaining a completed-blocks set that prevents late-arriving
    symbols from restarting timeouts or triggering redundant decoding
    for blocks that have already reached a terminal state;

(h) maintaining per-track FEC decoder instances keyed by media track
    identifier, each with independent K, timeout, and block state,
    enabling different FEC parameters per media type within the same
    session.

**Dependent Claims:**

D1. The method of Claim D further comprising refining the timeout
    computation when the frame rate is first detected from decoder
    output, and propagating said refined timeout to all active
    decoder instances.

D2. The method of Claim D wherein the three-state accounting
    (blocksClean, blocksRecovered, blocksFailed) is exposed as
    real-time statistics for adaptive bitrate selection or quality
    monitoring dashboards.

D3. The method of Claim D wherein a bounded-size completed-blocks set
    is maintained using insertion-order eviction, keeping the most
    recent N blocks and evicting the oldest to prevent unbounded
    memory growth.

**Prior Art Analysis:**
- RFC 6363 (FECFRAME): defines block FEC code framework. Receiver
  groups packets by FEC Payload ID into source blocks, decodes. Does
  NOT define timeout behavior, state machines, or codec-aware timing.
  Receiver behavior explicitly left to implementation.
- RFC 6330 (RaptorQ): defines encoding/decoding algorithms. WS
  parameter limits decoder memory. Does NOT define block timeout,
  lifecycle states, or receiver timing.
- SMPTE 2022-1 (Pro-MPEG FEC): row/column FEC matrix. Defines matrix
  structure but NOT timeout management or lifecycle state machines.
- RFC 8680 (FECFRAME sliding window): mentions source symbol removal
  after delays. Closer to timeout concept but for sliding window, not
  block lifecycle.
- **Gap**: No found prior art defines a three-state block lifecycle
  with codec-aware dynamic timeout, completed-block guard, or
  per-track decoder routing. FEC standards deliberately leave receiver
  behavior unspecified.

**Implementation Evidence:**
- Code: `libmmt/packages/container/src/fec-manager.ts` (FECManager
  class, 319 lines, 3-state accounting, dynamic timeout)
- Tests: 4 NoneCodec tests, verified in E2E 7-point validation

---

### CLAIM E: End-to-End Broadcast-to-Unicast Bridge with FEC Preservation

**Prior Art Risk: LOW-MEDIUM — system claim, novel pipeline**

**Independent Claim:**
A system for bridging broadcast media to unicast streaming, comprising:

(a) a broadcast gateway receiving MMTP packets with application-layer
    FEC via SSM multicast from a broadcast transmitter conforming to
    ATSC 3.0 or ARIB STD-B60;

(b) said gateway performing FEC decoding on received MMTP packets to
    recover source media lost during broadcast transmission;

(c) said gateway converting broadcast signaling from S-TSID XML format
    to a streaming catalog in JSON format, wherein said conversion maps:
    - S-TSID Logical Stream elements to catalog track entries;
    - S-TSID FECParameters to catalog FEC extension fields, with:
      fecSchemeID mapped to algorithm string,
      symbolSize mapped to symbolSize integer,
      maxSourceBlockLength mapped to sourceSymbols integer,
      (maxNumberEncSymbols - maxSourceBlockLength) mapped to
      repairSymbols integer;
    - S-TSID RepairFlow elements to catalog repair track entries;
    - S-TSID RS (Receiving Station) elements to catalog multicast
      endpoint entries;

(d) said gateway publishing recovered source media as tracks in a
    publish/subscribe session over QUIC or WebTransport;

(e) one or more subscribers receiving said tracks without requiring
    MMTP decoding capability, FEC processing, or broadcast receiver
    hardware;

(f) wherein the reverse conversion from streaming catalog to S-TSID
    is also performed, enabling MoQ-originated content to be
    retransmitted via broadcast infrastructure.

**Dependent Claims:**

E1. The system of Claim E wherein the gateway re-encodes recovered
    source media from MMTP packaging to CMAF packaging, producing
    fMP4 segments suitable for HLS or DASH delivery to downstream
    clients.

E2. The system of Claim E wherein the gateway selectively preserves
    FEC by re-publishing both source and repair tracks for subscribers
    that request FEC protection, while publishing source-only tracks
    for subscribers that do not.

E3. The system of Claim E wherein the gateway is deployed at an ISP
    edge router with inline AMT relay capability, forming a TreeDN
    node that receives broadcast via AMT tunnel and re-publishes to
    local subscribers.

**Prior Art Analysis:**
- US20250274499 (CDN offload ATSC 3.0): hybrid DASH broadcast +
  CDN unicast. Uses DASH/ROUTE, NOT MMT/MMTP. No FEC recovery or
  MoQ republishing. No S-TSID conversion.
- Samsung EP2849440A1: MMT hybrid delivery. Predates QUIC/MoQ.
  Does not cover S-TSID↔catalog conversion or relay FEC recovery.
- ADTH ATSC 3.0 Gateway: commercial product converting OTA to
  home network. Does NOT preserve FEC or output MoQ.
- Harmonic/MediaKind gateways: transcoding gateways. Involve
  transcoding, not FEC-preserving bridging.
- **Gap**: The complete pipeline (SSM → FEC recovery → S-TSID→catalog
  conversion → MoQ republish) is not found in any prior art. The
  S-TSID↔MoQ catalog bidirectional conversion is entirely novel.

**Implementation Evidence:**
- Draft: draft-ramadan-moq-mmt-00 §11 (conversion), §8 (multicast),
  Appendix B (example)
- Draft: draft-ramadan-moq-fec-00 §12 (ATSC compatibility)

---

### CLAIM F: Catalog-Based FEC Discovery with Hierarchical Defaults

**Prior Art Risk: LOW — novel signaling model**

**Independent Claim:**
A method for forward error correction parameter signaling in a media
streaming system, comprising:

(a) a catalog document in JSON format containing:
    - a top-level FEC configuration object specifying default FEC
      parameters including algorithm, sourceSymbols, repairSymbols,
      symbolSize, and interleaveDepth;
    - zero or more per-track FEC configuration objects that override
      specific fields from the top-level defaults, wherein unspecified
      fields inherit the top-level values;

(b) said catalog document being fetchable via HTTP prior to
    establishing a streaming session, enabling subscribers to discover
    FEC parameters before committing to subscription;

(c) an in-band FEC_CONFIG control message sent from publisher to
    subscriber after subscription establishment, carrying authoritative
    FEC parameters;

(d) a precedence order wherein: the in-band FEC_CONFIG message
    overrides per-track catalog values, which override top-level
    catalog defaults;

(e) wherein a per-track algorithm field enables different FEC schemes
    per media type within the same catalog, including a "none" value
    that specifies no FEC encoding with an optional jitterBufferMs
    parameter for receiver-side reorder tolerance.

**Dependent Claims:**

F1. The method of Claim F wherein said "none" algorithm with
    jitterBufferMs enables ultra-low-latency media tracks to
    coexist with FEC-protected tracks in the same session, with the
    receiver applying only a reorder buffer (no FEC decode) for
    "none" tracks.

F2. The method of Claim F wherein deferred FEC configuration is merged
    incrementally as track renditions are created in the catalog,
    preserving fields set by earlier configuration calls and applying
    pending defaults to newly created renditions.

F3. The method of Claim F wherein for multicast delivery where no
    back-channel exists for the in-band FEC_CONFIG message, the
    catalog FEC parameters serve as the sole authoritative source.

**Prior Art Analysis:**
- RFC 6364 (SDP FEC): FEC signaling via SDP attributes. Session-level,
  not manifest/catalog-based. Requires SIP/RTSP session. No
  hierarchical defaults.
- DASH MPD: has hierarchical structure (Period > AdaptationSet >
  Representation) with property inheritance. But NO FEC-specific
  properties defined in DASH.
- ATSC A/331 S-TSID: per-flow FEC in XML. Not hierarchical JSON.
  No "none" algorithm. No HTTP pre-discovery.
- MoQ catalog (I-D.ietf-moq-catalogformat): JSON catalog for MoQ.
  Has ZERO FEC provisions. draft-ramadan-moq-fec is the first to
  propose FEC extensions.
- **Gap**: No prior art combines JSON catalog FEC discovery with
  hierarchical defaults, HTTP pre-subscription access, in-band
  override precedence, and per-track algorithm selection including
  "none" mode.

**Implementation Evidence:**
- Draft: draft-ramadan-moq-fec-00 §4.1, §5
- Code: `hang-mmt-fec/rs/hang/src/catalog/root.rs` (top-level fec
  field, pending_video_fec inheritance pattern)
- Code: `hang-mmt-fec/js/hang/src/catalog/root.ts` (RootSchema.fec)
- Tests: top_level_fec_inherits_to_renditions,
  per_rendition_fec_overrides_top_level (both pass)

---

## NEW DEPENDENT CLAIMS (Added 2026-04-14)

### A4: NTP-Synchronized Block IDs for Hot Standby

**Prior Art Risk: LOW** — No prior art combines wall-clock-derived FEC
block boundaries with pub/sub media transport.

**Prior Art Analysis:**
- DVB BlueBook A176: Defines MPEG-2 TS redundancy switching, but no
  FEC block synchronization across encoders. Switching is at TS packet
  level, not FEC block level.
- SMPTE ST 2022-7: Seamless protection switching for SMPTE 2110, but
  operates at RTP/IP layer with hitless merge, not FEC block alignment.
- 3GPP TS 26.346 (MBMS): FEC over FLUTE/ALC with SBN assigned by
  sender. No receiver-derivable SBN from wall clock.
- **Gap:** Deriving SBN from NTP time so that independent encoders
  produce identical block boundaries — enabling receiver-side combining
  of symbols from any encoder — is novel.

**Implementation:** Draft §8.5, FFmpeg `-fec_ntp_sync` (planned)

### A5: PSN-Decoupled SS_ID for Encoder Failover

**Prior Art Risk: LOW** — PSN and SS_ID are separate fields in ISO
23008-1, but no prior art explicitly claims the decoupling as enabling
seamless FEC recovery across encoder transitions.

### A6: A3SA Signed FEC Block Assignment

**Prior Art Risk: LOW** — Carrying SS_ID in the hint track for A3SA
signed-region integrity is a novel combination of ISO 23008-1 hint
tracks (existing) with ATSC A/360 signing (existing) for FEC block
authentication (new use case).

**Implementation:** Draft §8.6, §14.5

---

## CLAIMS NOT IN TOP 6 (Demoted)

### Claim 3 (Relay-Side FEC Recovery) → DEMOTED

**Reason:** RFC 6363 §8 explicitly describes "decoding middlebox" that
performs FEC recovery before forwarding. The core concept has direct
prior art. Fold the MoQ-specific pub/sub subscription model into
Claims B and E as dependent claims.

### Claim 5 (Unified Packet Format) → DEMOTED

**Reason:** Samsung EP2849440A1 covers hybrid broadcast/broadband using
the same MMT packet format. ISO 23008-1 was literally designed for
heterogeneous transport. The QUIC stream vs datagram distinction is
narrow. Risk of rejection against Samsung's portfolio is HIGH.

### Claim 9 (AMT/DRIAD in Catalog) → NARROW SCOPE

**Reason:** Combines two existing protocols (AMT RFC 7450 + DRIAD
RFC 8777) with catalog signaling. Valuable but the combination may be
viewed as obvious. Consider as dependent claim under Claim F.

### Claim 10 (S-TSID Conversion) → FOLDED INTO CLAIM E

**Reason:** The conversion algorithm is the core of Claim E (broadcast
bridge). Stronger as part of the system claim than standalone.

---

## FILING STRATEGY

### Application 1: Core FEC Innovations (File First)

| Claim | Title | Risk |
|-------|-------|------|
| A (independent) | ESI Derivation from Pub/Sub IDs | LOW |
| B (independent) | Multi-Path FEC Combining | MEDIUM |
| C (independent) | Hybrid Source Arbitration | MEDIUM |
| D (independent) | FEC Block Lifecycle State Machine | LOW |
| A1-A3 | ESI derivation dependents | — |
| A4 | NTP-Synchronized Block IDs (hot standby) | LOW |
| A5 | PSN-Decoupled SS_ID (encoder failover) | LOW |
| A6 | A3SA Signed FEC Block Assignment | LOW |
| B1-B3, C1-C3, D1-D3 | Other dependent claims | — |

**Rationale:** Claims A and D are the strongest (lowest prior art risk).
Claims B and C are enabled by Claim A (the ESI derivation formula is
what makes multi-path combining and hybrid switching work). A4-A6
strengthen Claim A with hot standby synchronization and broadcast
signing — critical for carrier-grade deployment and ATSC3 compliance.
Filing together creates a coherent patent on "FEC for publish/subscribe
media transport with multi-path delivery."

### Application 2: System Claims (File Second)

| Claim | Title | Risk |
|-------|-------|------|
| E (independent) | Broadcast-to-Unicast Bridge | LOW-MEDIUM |
| F (independent) | Catalog-Based FEC Discovery | LOW |
| E1-E3, F1-F3 | Dependent claims | — |

**Rationale:** E and F are system/signaling claims that complement the
core FEC methods. E covers the full broadcast bridge pipeline; F covers
the catalog signaling that enables all other claims. Filing as a
continuation-in-part preserves the priority date.

### Prior Art to Distinguish in Prosecution

| Prior Art | What It Covers | Our Novel Contribution |
|-----------|---------------|----------------------|
| RFC 6330 (RaptorQ) | FEC algorithm | Transport mapping (Claim A) |
| RFC 6363 (FECFRAME) | FEC framework, middlebox | Pub/sub model, block lifecycle (Claims B, D) |
| US8787153 (Cisco) | FEC path diversity | Heterogeneous transport combining (Claim B) |
| US20060200576 (Cisco) | Unicast+multicast switching | FEC-aware keyframe gating (Claim C) |
| Samsung EP2849440A1 | MMT hybrid delivery | QUIC binding, MoQ integration (Claims A, B) |
| ISO 23008-1 | MMTP packet format | Pub/sub ESI derivation (Claim A) |
| ATSC A/331 | Broadcast FEC signaling | JSON catalog, bidirectional conversion (Claims E, F) |
| ATSC A/360 (A3SA) | Broadcast signing | Signed FEC block assignment via hint track (Claim A6) |
| SMPTE ST 2022-7 | RTP hitless switching | NTP-derived FEC block sync, not RTP merge (Claim A4) |
| DVB BlueBook A176 | TS redundancy switching | FEC-block-level failover, not TS packets (Claim A4) |
| 3GPP TS 26.346 (MBMS) | FLUTE/ALC FEC | Receiver-derivable SBN from wall clock (Claim A4) |
| RFC 6364 | SDP FEC signaling | Hierarchical JSON catalog (Claim F) |

---

# APPENDIX B — Intrinsic Fragment Coordinate (IFC): Design Disclosure

# Intrinsic Fragment Coordinate (IFC) — design note

**Status:** design sketch (not a submission draft). Source material for an
extensions-draft section and a patent continuation.
**Renamed** from "Generic Fragment Descriptor" — *GFD* collides with MMT's
**Generic File Delivery** mode (ISO/IEC 23008-1 §9.3.3).

Companions: `draft-ramadan-moq-mmt-00.md` (§"MFU Fragmentation"),
`draft-ramadan-moq-fec-00.md` (`(SBN, ESI)` symbol coords),
`patent/APPLICATION-1-FEC-METHODS.md`, and **ISO/IEC 23008-1:2023** (verified
ground truth — see §2).

## 1. Problem

Reassembly of a *fragmented* application object must survive transport disorder,
loss, FEC recovery, multi-path combining, and relay re-sequencing — without
coupling the reassembly layer to a specific media format. We want one reassembler
that works for MMT timed media, MMT non-timed items, generic files, and future
object types, over a MoQ + multicast + FEC transport.

## 2. ISO/IEC 23008-1 ground truth (verified)

MMT **already** defines intrinsic, content-carried fragment coordinates — three
of them, one per object class. IFC is the *unification* of these; it does not
invent new descriptors.

| MMT object class | Where | Object key | Intrinsic offset/order | Extras |
|---|---|---|---|---|
| **Timed media MFU** | §9.3.2.3, Fig 12 (T=1) | `MPU_sequence_number` + `movie_fragment_sequence_number` + `sample_number` | `offset` (within the referenced sample) | `subsample_priority`, `dependency_counter` |
| **Non-timed media MFU** | §9.3.2.3, Fig 13 (T=0) | `Item_ID` | (item-scoped) | `subsample_priority`, `dependency_counter` |
| **Generic File Delivery** | §9.3.3 / §9.3.3.4 | `packet_id` (Asset) + `TOI` | `start_offset` (48-bit, "location of payload in the object") | `CodePoint` |

Fragmentation framing is also ISO-native: `f_i` (00 complete / 01 first / 10
mid / 11 last), `aggregation_flag`, `fragment_counter` (§9.3.2.3). The MMT draft's
FI=1/2/3 reassembly is a direct restatement of this.

**Consequence for `libmmt` #78:** parsing `movie_fragment_sequence_number` /
`sample_number` / `offset` is *exactly* §9.3.2.3 — **spec-conformant, not novel**.
That's the right outcome for the implementation; it just means the *descriptors*
carry no patent weight (see §9).

## 3. Principle

Order and dedup fragments by **intrinsic** (content-carried) coordinates — never
by **extrinsic** (transport-assigned) delivery order. This mirrors the FEC layer,
which already addresses symbols by `(SBN, ESI)` from `SS_ID`, not by arrival. IFC
applies the same idea at the application-object boundary. Extrinsic ordering (MoQ
Object ID) remains the **mandatory floor** for opaque/unfragmented objects.

## 4. Layer position

```
+---------------------------------------------------------------+
| Container / application parsing                                |
|   MMT MPU/MFU, ISOBMFF, DASH seg, JSON, file                  |
+---------------------------------------------------------------+
| Object reassembly   ◄── consumes the Intrinsic Fragment Coordinate
|   orders, dedups, completes fragmented objects (media-agnostic)|
+---------------------------------------------------------------+
| FEC / recovery      ── intrinsic (SBN, ESI) symbol coordinates |
+---------------------------------------------------------------+
| Transport: MoQ objects / multicast UDP / datagrams            |
|   delivers bytes; assigns EXTRINSIC Object IDs                 |
+---------------------------------------------------------------+
```

IFC sits **above FEC** (reassembles recovered source bytes) and **below container
parsing** (hands up a complete, ordered object). The container layer never sees
loss or ordering.

## 5. The coordinate (abstract; MMT supplies the concrete encodings)

| Field | Meaning | MMT source |
|---|---|---|
| `objectKey` | transport-independent identity of the logical object | timed: `MPU_seq:MFSN:sample` · non-timed: `Item_ID` · file: `packet_id:TOI` |
| `fragmentOffset` | byte offset within the object | timed: DU `offset` · file: `start_offset` |
| completion | `objectTotalLength` or last-fragment (`f_i=11`) | `f_i` / `fragment_counter` |
| `rap` | object is a random-access point (decode-gate) | MPU first AU = SAP (§6.4); RAP packets carry full headers (§9) |
| `priority` | recovery/decode precedence | `subsample_priority`, `priority_id`, `transmission_priority` |
| `dependency` | DUs depending on this one | `dependency_counter` |
| `contentHash` *(opt)* | path-independent dedup/integrity | — (transport overlay) |

**Invariants**
- Order = ascending `fragmentOffset` (ignores arrival order and Object ID).
- Dedup = `(objectKey, fragmentOffset)` (and/or `contentHash`).
- Completion = contiguous `[0, total)` coverage.
- Bounded memory = discard incomplete objects on a derived deadline.

## 6. RAP / I-frame handling (per ISO)

- An MPU begins at a **SAP** (§6.4): the first access unit of an MPU is a
  random-access point. So keyframe boundaries = MPU/Group boundaries.
- RAP is signalled by **full-header packets** (§9): the reassembler's `rap` bit
  derives from this, not from a payload bit alone.
- I-frames are **high `subsample_priority` and dependency roots** (high
  `dependency_counter`). IFC surfaces `rap` + `priority` + `dependency` so the
  receiver can: (a) **gate decode start** on a recovered RAP (patent Emb. 3,
  state 402a "keyframe gate"); (b) **prioritize FEC recovery** of RAP/high-priority
  fragments; (c) drop low-priority dependents first under pressure.

## 7. Precedence model (intrinsic-first, extrinsic-floor)

1. Fragments carry an IFC → reassemble by `fragmentOffset`, dedup by
   `(objectKey, offset)`. Robust on FEC / multi-path / relay.
2. No IFC (opaque payload) → fall back to transport **Object ID** order.
3. Whole/unfragmented object → no reassembly; Object ID for delivery + dedup.

This is the shape already in `libmmt mfu-reassembler.ts` (offset-mode when sample
identity present, else counter), generalized off MMT.

## 8. Draft framing (extensions draft, not lean core)

Section: **"Self-Describing Fragment Reassembly."**
- Normative: a receiver MAY use an MMT-native intrinsic coordinate (timed-MFU
  `offset`, GFD `start_offset`, or `Item_ID`), when present, as the authoritative
  reassembly order, **taking precedence over the MoQ Object ID**; it MUST fall
  back to Object-ID order when absent.
- Cite ISO/IEC 23008-1 §9.3.2.3 (DU headers) and §9.3.3 (GFD `start_offset`) as
  the field source — the draft only specifies the **MoQ mapping + precedence rule**,
  not new fields.
- Updates `draft-ramadan-moq-mmt-00` §"MFU Fragmentation": its "order by Object ID"
  becomes the *floor*, with intrinsic-offset precedence on top. Lands in the
  **extensions** draft per the lean-core/low-exposure sequencing.

## 9. Patent-claim outline (re-scoped above ISO prior art)

ISO already defines the descriptors and offset-reassembly (§2), so claims **must
not** read on "use sample/offset/Item_ID/start_offset to reassemble." The novelty
is the **transport reconciliation on a pub/sub + multicast + FEC path** — the
up-layer companion to `APPLICATION-1`'s `(SBN, ESI)` claims.

- **Independent claim.** A method for reassembling a fragmented application object
  delivered over a publish/subscribe transport that assigns extrinsic per-object
  delivery identifiers (e.g., MoQ Object IDs) and over one or more additional paths
  including multicast with forward error correction, comprising: recovering missing
  fragments via FEC such that recovered fragments lack a transport-assigned delivery
  identifier; ordering and deduplicating fragments — including FEC-recovered and
  multi-path-delivered fragments — by an **intrinsic content-carried coordinate**
  (object identity + byte offset) **in precedence over** the transport-assigned
  delivery identifier; signalling completion by contiguous byte coverage; thereby
  reassembling deterministically irrespective of arrival order, path, or recovery.
- **Dependent claims.**
  - intrinsic coordinate sourced from an MMT timed-MFU DU header (`movie_fragment_sequence_number`/`sample_number`/`offset`);
  - …from an MMT non-timed `Item_ID`;
  - …from an MMT Generic File Delivery `start_offset`/`TOI`;
  - …from a transport object **extension header** for non-MMT payloads (the generalization);
  - dedup of multi-path fragments by content hash;
  - **gating decode start** on a FEC-recovered random-access fragment;
  - **prioritizing FEC recovery** by `subsample_priority`/`dependency_counter`;
  - bounded-memory discard on a derived deadline;
  - composition with `(SBN, ESI)` symbol addressing of `APPLICATION-1`.

Positioning: broader and more standards-essential than MMT-only, because the
claimed step is the *intrinsic-over-extrinsic reconciliation across FEC/multi-path*,
which MMT-over-broadcast never needed (no MoQ Object ID, no unicast/multicast FEC
combining) and which ISO therefore does not anticipate.

## 10. Relationship to existing work

- **Conforms to** ISO/IEC 23008-1 §9.3.2 / §9.3.3 (uses its descriptors verbatim).
- **Extends** `draft-ramadan-moq-mmt-00` §"MFU Fragmentation" (adds intrinsic
  precedence over MoQ Object ID; generalizes off MMT).
- **Aligns with** the FEC layer's `(SBN, ESI)` intrinsic addressing — IFC is the
  same idea one layer up.
- **Distinct from** `APPLICATION-1` claims (FEC-*symbol* dedup); IFC is
  application-*object* reassembly over the FEC/MoQ transport → candidate continuation.

---

# APPENDIX C — IFC Draft Claim Language

# Intrinsic Fragment Coordinate reassembly — draft claims (for review)

**Status:** draft claim language for review — *not* a filed application. Companion
/ continuation to `patent/APPLICATION-1-FEC-METHODS.md`.

**Novelty scoping (read first).** ISO/IEC 23008-1:2023 already defines the
*descriptors* — the timed-MFU DU header (§9.3.2.3: `movie_fragment_sequence_number`,
`sample_number`, `offset`), the non-timed `Item_ID`, and the Generic File Delivery
`start_offset` (§9.3.3) — and offset-based reassembly within each. These are prior
art and the claims below do **not** read on them in isolation. The claimed advance
is the **reconciliation**: using an intrinsic, content-carried coordinate, *in
precedence over a transport-assigned object identifier*, to order and de-duplicate
fragments **including FEC-recovered and multi-path-combined fragments**, over a
publish/subscribe plus multicast transport. Broadcast MMT has no MoQ Object IDs and
no unicast/multicast FEC combining, so ISO does not anticipate this step. The claim
set is the application-object-layer companion to APPLICATION-1's FEC-symbol-layer
`(SBN, ESI)` claims.

---

## Independent Claim 1 (method)

A method for reassembling a fragmented application object delivered to a receiver
over (i) a publish/subscribe transport that assigns to delivered objects an
extrinsic, transport-assigned delivery identifier, and (ii) at least one further
delivery path comprising multicast delivery protected by forward error correction
(FEC), the method comprising:

(a) receiving a plurality of fragments of the application object, each fragment
    carrying an intrinsic descriptor comprising an object identity and a byte
    offset of the fragment within the application object, the intrinsic descriptor
    being independent of the transport-assigned delivery identifier;

(b) recovering at least one missing fragment of the application object by FEC
    decoding, the recovered fragment lacking a transport-assigned delivery
    identifier;

(c) ordering the fragments, including the FEC-recovered fragment, by the byte
    offset of the intrinsic descriptor, in precedence over the transport-assigned
    delivery identifier;

(d) de-duplicating the fragments by the intrinsic descriptor, such that a fragment
    whose object identity and byte offset have already been incorporated is
    discarded irrespective of the delivery path on which it arrived;

(e) determining completion of the application object by contiguous byte coverage;
    and

(f) outputting the reassembled application object to a container or application
    parser;

whereby the application object is reassembled deterministically irrespective of
fragment arrival order, delivery path, or FEC recovery.

## Dependent Claim 2

The method of Claim 1, wherein the intrinsic descriptor is carried in a media data
unit header of an MPEG Media Transport (MMT) timed-media media fragment unit and
comprises a movie fragment sequence number, a sample number, and an offset within
the referenced sample.

## Dependent Claim 3

The method of Claim 1, wherein the intrinsic descriptor is carried in a media data
unit header of an MMT non-timed media fragment unit and comprises an item
identifier.

## Dependent Claim 4

The method of Claim 1, wherein the intrinsic descriptor is carried in a generic
file delivery payload header and comprises a transport object identifier and a
start offset.

## Dependent Claim 5

The method of Claim 1, wherein the application object is not an MMT object and the
intrinsic descriptor is carried in an extension header of a transport object of the
publish/subscribe transport.

## Dependent Claim 6

The method of Claim 1, wherein the further delivery path and the publish/subscribe
transport deliver the same application object, and de-duplicating in step (d)
comprises discarding a fragment combined from a second delivery path whose intrinsic
descriptor matches that of a fragment already incorporated from a first delivery
path.

## Dependent Claim 7

The method of Claim 6, wherein de-duplicating further comprises comparing a content
hash carried with, or computed over, each fragment.

## Dependent Claim 8

The method of Claim 1, further comprising gating a start of media decoding on the
completion — including completion by FEC recovery — of an application object that
is a random access point.

## Dependent Claim 9

The method of Claim 1, further comprising prioritising FEC recovery or buffer
retention of fragments according to a priority value or a dependency count carried
in, or associated with, the intrinsic descriptor.

## Dependent Claim 10

The method of Claim 1, further comprising discarding an incompletely-covered
application object upon expiry of a deadline derived from a FEC interleave depth or
a frame duration, thereby bounding reassembly memory.

## Dependent Claim 11

The method of Claim 1, wherein the FEC decoding of step (b) operates on source
symbols addressed by intrinsic FEC coordinates derived as in the method of
APPLICATION-1 Claim 1, such that both the FEC symbol layer and the
application-object reassembly layer order and de-duplicate by intrinsic,
transport-independent coordinates.

## Independent Claim 12 (apparatus)

A receiver comprising one or more processors and a memory storing instructions
that, when executed by the one or more processors, cause the receiver to perform
the method of any of Claims 1 to 11.

## Independent Claim 13 (medium)

A non-transitory computer-readable medium storing instructions that, when executed
by one or more processors, cause the one or more processors to perform the method
of any of Claims 1 to 11.

---

## Notes for the drafter

- Claim 1 step (c) "in precedence over the transport-assigned delivery identifier"
  is the crux distinguishing over ISO/IEC 23008-1 (which has no competing transport
  identifier) and over plain MoQ (which orders by Object ID). Keep it in the
  independent claim.
- Claims 2–5 enumerate the descriptor encodings (MMT timed / non-timed / GFD /
  generic extension header). 2–4 are ISO-sourced encodings; 5 is the generalization
  that extends reach to JSON/file/arbitrary objects — likely the most commercially
  important dependent claim.
- Claim 11 is the explicit tie to APPLICATION-1; consider whether to file as a
  continuation-in-part of APPLICATION-1 or a standalone application that references
  it.
- Consider a method claim variant where step (b) is omitted (no FEC) but multi-path
  combining remains, to cover the unicast-multicast dedup case without FEC.

---

# APPENDIX D — Self-Describing Fragment Reassembly (Specification Section Draft)

<!--
Draft section prose for review — "Self-Describing Fragment Reassembly".
Intended to slot into the extensions draft (or draft-ramadan-moq-mmt) after
the "MFU Fragmentation (Raw Passthrough)" section. RFC 2119 keywords. Cross
references shown as {{...}} are to be wired to the host draft's sections.
Not yet integrated into a submission draft.
-->

# Self-Describing Fragment Reassembly

## Motivation

{{mfu-fragmentation}} reassembles the fragments of a Media Fragment Unit (MFU)
in reconstructed Object ID order ({{object-identifier-reconstruction}}). The
Object ID is assigned by the transport. It is authoritative on a reliable,
in-order delivery path, but it is not authoritative on the paths this mapping
exists to serve:

- A fragment recovered by FEC ({{fec-integration}}) is reconstructed below the
  MoQ object layer and carries no transport-assigned Object ID; its position in
  the object must be re-derived.
- When the same content is combined from more than one path — for example a
  reliable unicast subscription and a multicast group — Object IDs are
  path-relative and cannot serve as a common ordering or de-duplication key.
- A publisher MAY emit a constant zero Object ID delta and rely on a relay to
  re-sequence on egress ({{object-identifier-reconstruction}}); end to end the
  Object ID is then not a stable content identifier.

MMT data units already carry an intrinsic, content-derived coordinate that is
invariant to all of the above. A receiver that treats that coordinate as the
reassembly authority — falling back to Object ID order only when it is absent —
reassembles deterministically irrespective of arrival order, delivery path, or
FEC recovery.

## Intrinsic Fragment Coordinate

For each class of MMT object, ISO/IEC 23008-1:2023 defines an intrinsic
coordinate comprising a transport-independent object identity and a byte
offset. No addition to the MoQ object encoding is required; the fields are
already present in the data unit (DU) header or the payload header.

| Object class            | Object identity                                                       | Byte offset    | Reference            |
|-------------------------|-----------------------------------------------------------------------|----------------|----------------------|
| Timed-media MFU         | MPU_sequence_number + movie_fragment_sequence_number + sample_number  | offset (in the referenced sample) | 23008-1 9.3.2.3 |
| Non-timed media MFU     | Item_ID                                                               | item-scoped    | 23008-1 9.3.2.3      |
| Generic File Delivery   | packet_id + Transport Object Identifier (TOI)                         | start_offset   | 23008-1 9.3.3        |

An object whose fragments carry such a coordinate is said to be
**self-describing**.

## Receiver Behaviour

A receiver reassembling a fragmented object:

1. If every fragment of the object carries an intrinsic byte offset, the
   receiver SHOULD order the fragments by ascending byte offset, and MUST treat
   that order as authoritative in precedence over reconstructed Object ID order.
2. If the intrinsic coordinate is absent, the receiver MUST fall back to
   reconstructed Object ID order ({{object-identifier-reconstruction}}).
3. The receiver MUST de-duplicate fragments by the pair (object identity, byte
   offset). A fragment whose coordinate has already been incorporated MUST be
   discarded, including a duplicate that arrives on a different path or that is
   produced by FEC recovery.
4. The receiver MUST determine completion by contiguous byte coverage of the
   object and MUST NOT emit a partially-covered object to the container or
   application parser.
5. The receiver MUST bound the memory used for in-flight reassembly and MUST
   discard an object whose coverage does not complete within a deadline derived
   from the FEC interleave depth or the frame duration, rather than buffer
   without limit (consistent with {{mfu-fragmentation}}).

## Random Access and Priority

An MPU begins at a Stream Access Point: the first access unit of an MPU is a
random access point (RAP) (ISO/IEC 23008-1:2023, 6.4). Accordingly a receiver:

- SHOULD gate the start of media decoding on the availability of a complete RAP
  object, including a RAP object completed by FEC recovery; and
- SHOULD prioritise FEC recovery and retention of fragments that carry a higher
  subsample_priority or a higher dependency_counter (ISO/IEC 23008-1:2023,
  9.3.2.3), since these are decode-order roots upon which other access units
  depend.

## Relationship to Object Identifier Reassembly

This section refines {{mfu-fragmentation}}. Reconstructed Object ID order
remains the mandatory reassembly order for objects that have no intrinsic
coordinate — for example opaque or unfragmented objects — and is the universal
fallback. Where an intrinsic coordinate is present it takes precedence, because
it is invariant to the transport conditions (loss, multi-path combining, FEC
recovery, and relay re-sequencing) under which Object ID order is not reliable.

The mechanism is not specific to MMT: the same receiver procedure applies to any
fragmented application object whose fragments carry an object identity and a byte
offset, whether sourced from an MMT DU header, an MMT Generic File Delivery
payload header, or a transport object extension header defined for a non-MMT
payload.
