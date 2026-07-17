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
      symbolSize, and interleaveDepthMs;
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
