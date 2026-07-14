%%%
title = "MPEG Media Transport (MMT) Packaging for Media over QUIC"
abbrev = "MMT for MoQ"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
keyword = ["MMT", "MMTP", "MoQ", "ATSC 3.0", "FEC"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-mmt-00"
stream = "IETF"
status = "standard"

[[author]]
initials = "O."
surname = "Ramadan"
fullname = "Omar Ramadan"
organization = "Blockcast"
  [author.address]
  email = "omar@blockcast.net"
%%%

.# Abstract

This document specifies the use of MPEG Media Transport (MMT) as a
container format for Media over QUIC (MoQ).  MMT provides a unified
framework for streaming media over heterogeneous networks including
broadcast (ATSC 3.0, ARIB STD-B60), multicast (SSM), and unicast
(QUIC/WebTransport).  This specification defines the mapping of MMT
packets to MoQ objects, interaction with Application-Layer FEC,
bidirectional conversion between S-TSID and MoQ catalogs, and
compatibility considerations for both ATSC 3.0 and ARIB STD-B60
systems.

{mainmatter}

# Introduction

MPEG Media Transport (MMT) [@!ISO.23008-1] is a transport protocol
designed for delivery of multimedia content over heterogeneous
networks.  MMT is supported as an alternative transport in ATSC 3.0
broadcast television (Americas, South Korea) alongside the primary
ROUTE/DASH transport, and is the basis for ARIB STD-B60 (Japan).
MMT provides native support for:

- Media Processing Units (MPU, branded "mpuf" in ISOBMFF) as the
  media container, with structural similarities to fMP4
- Application-Layer FEC (AL-FEC) supporting multiple schemes
  including RaptorQ and Reed-Solomon
- Cross-layer signaling for adaptive streaming
- Hybrid delivery combining broadcast and broadband

This document defines how MMT-encapsulated media can be transported
over MoQ [@!I-D.ietf-moq-transport], enabling:

1. **Broadcast-to-Unicast bridging**: Content from ATSC 3.0 or ARIB STD-B60
   broadcasts can be relayed to MoQ subscribers without transcoding
2. **Unified FEC**: MMT's AL-FEC integrates with MoQ FEC repair tracks
   per [@!MOQ-FEC]
3. **Multicast promotion**: MoQ clients can receive SSM multicast
   directly when available, per [@!MOQ-MULTICAST]
4. **Bidirectional signaling**: Convert between S-TSID (ATSC) and MoQ
   catalogs for seamless interoperability

## Relationship to Other MoQ Media Formats

This specification complements existing MoQ packaging formats:

| Format | Container | Primary Use Case | FEC Support |
|--------|-----------|------------------|-------------|
| MSF (LOC) | WebCodecs chunks | Low-latency unicast | No |
| CMSF | CMAF fMP4 | Adaptive streaming | No |
| CARP | CMAF fMP4 | ABR delivery | No |
| This spec (MMT) | MMTP + MPU (ISOBMFF) | Broadcast bridge | Yes |

MMT packaging is RECOMMENDED when:

- Ingesting ATSC 3.0 or ARIB STD-B60 broadcasts
- FEC protection is required for multicast delivery
- Hybrid broadcast/unicast architectures are deployed
- Interoperability with broadcast receivers is needed

CMAF packaging (CMSF/CARP) is RECOMMENDED when:

- Content originates as DASH/HLS
- No multicast delivery is planned
- Interoperability with existing CDN infrastructure is needed

# Terminology

The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**",
"**SHALL NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**",
"**NOT RECOMMENDED**", "**MAY**", and "**OPTIONAL**" in this document
are to be interpreted as described in BCP 14 [@!RFC2119] [@!RFC8174] when,
and only when, they appear in all capitals, as shown here.

**MMTP**: MMT Protocol - the packet layer of MMT (ISO 23008-1 Clause 8)

**MPU**: Media Processing Unit - a self-contained media segment in MMT,
typically aligned with a Group of Pictures (GOP)

**MFU**: Media Fragment Unit - a single coded media frame within an MPU

**AL-FEC**: Application-Layer Forward Error Correction

**S-TSID**: Service-based Transport Session Instance Description -
ATSC 3.0 signaling table containing transport and FEC parameters

**SLT**: Service Layer Table - ATSC 3.0 bootstrap signaling

**MPT**: MMT Package Table - signaling table containing MMT asset info

**MPI**: MMT Presentation Information - presentation timing table

# MMT Overview

MMT uses a layered architecture:

~~~
+---------------------------------------------+
|              Application Layer              |
+---------------------------------------------+
|  MPU (Media Processing Unit)                |
|  +---------+---------+---------+---------+  |
|  |  MFU 0  |  MFU 1  |  MFU 2  |   ...   |  |
|  | (IDR)   | (P)     | (P)     |         |  |
|  +---------+---------+---------+---------+  |
+---------------------------------------------+
|  MMTP (MMT Protocol)                        |
|  +-----------------------------------------+|
|  | MMTP Header | Payload (MPU fragment)    ||
|  | 12 bytes    | Variable                  ||
|  +-----------------------------------------+|
+---------------------------------------------+
|  Transport: UDP/IP (broadcast/multicast)    |
|             QUIC/WebTransport (unicast)     |
+---------------------------------------------+
~~~

## MMTP Header Format

~~~
MMTP Header (12 bytes minimum) {
  Version (2),
  Packet Counter Flag (C) (1),
  FEC Type (F) (2),
  Reserved (1),
  Extension Flag (X) (1),
  RAP Flag (R) (1),
  Packet Type (6),
  Packet ID (16),
  Timestamp (32),
  Packet Sequence Number (32),
  [Packet Counter (32)],       // Present if C=1
  [Header Extension (..)]      // Present if X=1
}
~~~

Key fields for MoQ mapping:

- **Packet ID**: Maps to MoQ track within namespace
- **Timestamp**: UTC wallclock time in NTP short format, maps to MoQ object timestamp
- **Packet Sequence Number**: per-`packet_id`, monotonic across the
  flow ([@ISO.23008-1] Clause 9.2.2); carried inside the object payload
  for MMTP-layer loss/ordering detection.  NOT the MoQ Object ID —
  Object IDs are the per-MFU fragment index within a subgroup
  (Section 4.1), which resets per subgroup.
- **FEC Type**: 0=no AL-FEC, 1=AL-FEC source packet,
  2=AL-FEC repair packet, 3=reserved
- **RAP Flag**: 1 indicates Random Access Point

# MoQ Object Mapping

## Track Structure

An MMT stream maps to MoQ tracks as follows:

| MMT Component | MoQ Mapping |
|---------------|-------------|
| Asset (stream) | Namespace |
| Packet ID (video) | Track "video" |
| Packet ID (audio) | Track "audio" |
| MPU sequence | Group ID |
| MFU within MPU (and Init metadata) | Subgroup ID |
| MMTP packet (fragment) within MFU | Object ID |
| AL-FEC repair | Track "video/repair" |

## Object Payload

Each MoQ object carries one MMTP packet:

~~~
MoQ Object Payload {
  MMTP Header (12+ bytes),
  MPU Fragment (MPU metadata or MFU payload),
}
~~~

The MMTP header is always preserved: it carries the FEC Type, RAP
Flag, Fragmentation Indicator, and timestamp metadata that receivers
and the FEC layer depend on.  This document does not define a
header-stripped delivery mode.  A publisher that wishes to deliver
raw ISOBMFF fragments without MMTP encapsulation publishes the track
with CMAF packaging per [@!I-D.wilaw-moq-cmafpackaging] instead (an
MPU corresponds to a CMAF Fragment and an MFU to a CMAF Chunk; see
Section 4.3).

## Group Boundaries

Group boundaries align with MPU boundaries, and subgroup boundaries
align with MFU boundaries:

- Group N contains all objects of MPU N.
- Subgroup 0 of each group carries the MPU metadata (mmpu/moov boxes)
  as its single object.
- Subgroups 1..M each carry exactly one MFU.  The objects within an MFU
  subgroup are that MFU's MMTP packets in fragment order: a single
  object with Fragmentation Indicator FI=0 (a complete, unfragmented
  MFU), or objects with FI=1 (first), FI=2 (zero or more middle), and
  FI=3 (last) for an MFU fragmented across packets.
- The first media object of each group SHOULD have RAP Flag = 1.

This realizes the Chunk-to-Object mode of [@I-D.wilaw-moq-cmafpackaging]
when the source is CMAF: an MMT MPU corresponds to a CMAF Fragment and
each MFU corresponds to a CMAF Chunk.  Because a CMAF Fragment generally
contains multiple Chunks, an MPU generally contains multiple MFUs, each
in its own subgroup.  A Chunk that the encoder fragmented across
multiple MMTP packets is published as multiple objects within that
MFU's subgroup; the receiver reassembles them (Section 5.1).

Mapping each MFU to its own subgroup makes an MFU the unit of in-order
delivery, loss, and FEC.  To preserve this, relays and subgroup readers
MUST be able to deliver objects from multiple concurrently-open
subgroups of the same group, and MUST NOT let a later MFU's subgroup
starve an earlier, still-open subgroup of the same group.  This governs
delivery scheduling, not congestion response: under unrecoverable
congestion a relay MAY drop an MFU's subgroup, in which case the
receiver's bounded reassembly (Section 5.1) and FEC (Section 7) handle
the loss.

## Switching Sets

When multiple tracks represent alternative renditions of the same
media (e.g., an ABR ladder), they form a switching set as defined
in [@I-D.wilaw-moq-cmafpackaging].  MoQ Group numbers MUST be
media-time-aligned across all tracks of a switching set so that
subscribers can switch at group boundaries without discontinuity.

### Group Number Formula

For interoperability across senders, relays, and subscribers, the
group number for a given media time within a switching set is
computed as:

~~~
group_number = base + floor(ticks / groupDurationTicks)
~~~

where:

- `ticks` is the presentation timestamp expressed in the catalog's
  media `timescale` (Hz), as a signed integer.  Values less than or
  equal to zero (which can occur during encoder start-up, on B-frame
  reorder, or after an epoch reseed) MUST clamp to `base`.
- `groupDurationTicks` is the per-track group duration expressed
  in the same `timescale`, as a positive integer.  The catalog
  signals it via Section 4.4.2; conversion from the integer-millisecond
  form is exact by construction (the catalog publisher rejects
  non-exact pairs and uses the integer-tick override instead).
- `base` is a non-negative integer offset assigned to the switching
  set, defaulting to 0 unless the catalog specifies otherwise.

Integer math is normative.  Implementations MAY accept seconds-form
inputs at API boundaries, but the seconds-to-ticks conversion MUST
preserve the integer formula above (e.g. via `ticks =
round(seconds * timescale)`); a float-domain `floor` is RECOMMENDED
to apply a tolerance (e.g. `1e-9` seconds) to prevent ULP-class
boundary mis-bucketing.

The same `(ticks, timescale, groupDurationTicks)` triple, fed
through this formula, MUST produce the same group number in every
implementation that participates in the switching set.

### Catalog Signaling of Group Duration

For a subscriber to apply the formula in Section 4.4.1, the catalog
MUST publish the group duration to each track in the switching set.
This document defines a single per-track field:

~~~
groupDurationMs (REQUIRED, unsigned integer, milliseconds)
~~~

Rationale for the chosen unit:

- Integer milliseconds is unambiguous across catalog encodings (JSON,
  CBOR) and avoids the float-vs-integer tension that motivated the
  integer-ticks form of the formula in the first place.
- Most segment-aligned ABR ladders deployed today pick group
  durations in whole-millisecond multiples (e.g. 100, 1000, 2000,
  4000), and the publisher-side configuration in current
  implementations already operates in milliseconds.  Catalog and
  encoder agree without conversion in the common case.
- The primary use case for the integer-tick override (below) is
  per-frame group durations at non-integer-millisecond cadences
  (e.g. 1/30 s = 33.333... ms, 1/60 s = 16.666... ms), which cannot be
  expressed in integer milliseconds at all and which low-latency
  MoQ deployments routinely need.

A track's container kind is carried in the catalog `packaging` field
([@!I-D.ietf-moq-msf]), NOT a `container` field: the spec
defines values `cmaf` and `loc`, and this document defines the value
`mmtp`.  ("container kind" is used informally below as a synonym for
the `packaging` value.)  Per-track codec is carried in
`selectionParams.codec` (a nested object), not a top-level `codec`
field.

The subscriber converts to ticks using the timescale appropriate to
the track's container kind:

| Container | Timescale source |
|-----------|------------------|
| `cmaf`    | `container.timescale` (per-track field, REQUIRED). |
| `mmtp`    | Per-track field; mmtp tracks MUST publish an explicit timescale.  ISO 23008-1 Annex A.4 lists 90 000 Hz only as a video convention; the catalog does not infer audio timescales, so leaving the field unset is a catalog error. |
| `loc`     | Per-track `Timescale` property, per [@?I-D.ietf-moq-loc]; defaults to 1 000 000 (microseconds) only when the property is absent. |
| `legacy`  | 1 000 000 (microseconds).  This is the encoding convention applied by current moq-transport implementations to opaque object payloads; it is fixed by this document and does NOT derive from [@I-D.ietf-moq-transport]. |

Conversion is `groupDurationTicks = groupDurationMs * timescale / 1000`.
The catalog publisher MUST choose a `groupDurationMs` such that the
resulting tick count is exact (i.e. `(groupDurationMs * timescale) %
1000 == 0`).  If this cannot be satisfied, the catalog MUST publish
ticks directly via the optional override field:

~~~
groupDurationTicks (OPTIONAL, unsigned integer)
~~~

If both `groupDurationMs` and `groupDurationTicks` are present,
`groupDurationTicks` wins.  Cases where the override is required
include:

- Per-frame group durations at a 30 fps cadence (`1/30 s = 33.333... ms`)
  on any timescale: expressing this in integer ms is impossible, so
  publishers set `groupDurationTicks: timescale / 30` directly
  (e.g. `3000` at 90 000 Hz, `1500` at 45 000 Hz).
- Audio sample-rate timescales not divisible by 1000 Hz, such as
  44 100 Hz: `333 ms x 44 100 / 1000 = 14 685.3` is non-integer; a
  publisher selecting a 333 ms audio group MUST publish ticks.

Switching-set agreement: every track in the same switching set MUST
publish the same effective `groupDurationTicks` (after timescale
conversion).  Subscribers SHOULD validate this at catalog load and,
on disagreement, SHOULD reject the catalog and signal a
catalog-validation error to the application.  Subscribers that
proceed despite disagreement are non-conformant for switching across
the affected tracks; ABR transitions on such tracks will produce
group-boundary discontinuities.

### Catalog Signaling of Keyframe Interval

The group duration above describes the cadence of MMTP media groups
(one frame per group in the frame-grouped mode of Section 4.3).  It
does NOT describe how often the stream carries a keyframe (a random
access point).  A subscriber recovering from loss needs the latter to
bound how long it must wait for the next decodable refresh point
before it can, for example, arm a keyframe-loss repair timer or decide
to request a fresh init.  This document defines an OPTIONAL per-track
field for the keyframe (GOP) cadence:

~~~
keyframeIntervalMs (OPTIONAL, unsigned integer, milliseconds)
~~~

`keyframeIntervalMs` is the interval between consecutive video
keyframes, in integer milliseconds.  It is ADVISORY and semantically
DISTINCT from `groupDurationMs`: `groupDurationMs` is the per-frame
MMTP media-group duration, whereas `keyframeIntervalMs` is the
keyframe/GOP repair cadence (typically many groups long — e.g. a
1000 ms keyframe interval over a 33 ms per-frame group duration).  The
field applies to video tracks only; a publisher that cannot determine
the cadence simply omits it.

Because the field is advisory, its absence is not a catalog error:
subscribers that rely on it (for keyframe-loss repair or refresh
scheduling) simply leave that behavior disabled when it is absent, and
MUST NOT reject a catalog solely because it is missing.  When present,
`keyframeIntervalMs` MUST be a positive integer; a zero value is a
catalog error (it would drive a receiver's derived repair timeout to
zero).

As with the group duration, the integer-millisecond form cannot
express a keyframe cadence whose tick count is non-integer on the
track's timescale.  A publisher MAY publish an exact override:

~~~
keyframeIntervalTicks (OPTIONAL, unsigned integer)
~~~

expressed in the same timescale as `groupDurationTicks` (Section 4.4.2,
selected by the track's container kind).  If both
`keyframeIntervalMs` and `keyframeIntervalTicks` are present,
`keyframeIntervalTicks` wins.  Unlike `groupDurationTicks`, this
document places NO switching-set agreement requirement on the keyframe
interval: it is a per-track advisory hint, and tracks in a switching
set MAY carry different keyframe cadences.

## Init Segment Signaling

Publishers MAY signal MPU metadata (mmpu/moov) either inline as the
single object of Subgroup 0 of each group (the default form in
Section 4.3), or as a separate init track per
[@I-D.wilaw-moq-cmafpackaging] Section 4.2.  The catalog field
`initMode` (values: "inline" | "track") selects between the two;
subscribers determine the active mode from the catalog before issuing
SUBSCRIBE.

In addition, publishers SHOULD carry decoder initialization data
directly in the catalog via the per-track field:

~~~
initData (OPTIONAL, string)
~~~

`initData` is the base64 encoding of an ISOBMFF initialization
segment (`ftyp` + `moov`) sufficient to initialize the decoder for
the track (including the codec configuration record, e.g. avcC or
hvcC).  `initData` is defined by this document as a flat base64
string carried on mmtp-packaged tracks; it is analogous in purpose
to the `initDataList`/`initRef` mechanism of [@?I-D.ietf-moq-cmsf],
but is not identical to it.  It lets a subscriber initialize its decoder at
catalog load,
before the first MPU metadata object or init-track object arrives,
removing one delivery round trip from the join path (Section 6.1).

`initData` is a join optimization, not a replacement for in-band
metadata: the per-group MPU metadata (or init track) remains
authoritative, and a receiver MUST adopt in-band metadata when it
differs from `initData`.  Catalog content is untrusted input; a
receiver MUST validate that decoded `initData` is a well-formed
`ftyp` + `moov` sequence before passing it to a decoder, and MUST
discard it otherwise.

## Object Identifier Reconstruction

Within a subgroup, MoQ Object IDs increase monotonically, but the
increment between successive objects is not guaranteed to be one;
depending on the transport encoding an object's ID may be carried as a
delta from the previous object rather than as an explicit absolute
value.  A receiver MUST reconstruct each object's absolute Object ID by
maintaining a running value per subgroup; it MUST NOT assume successive
objects differ by a fixed nonzero step, nor that an absolute Object ID
is carried explicitly.

This makes receivers robust both to publishers that emit a constant
zero delta (relying on a relay to re-sequence Object IDs on egress)
and to direct publisher-to-subscriber topologies where no relay
re-sequencing occurs.  Within an MFU subgroup the reconstructed Object
IDs give the fragment order used for reassembly (Section 5.1).

# Media Fragment Unit (MFU) Mode

For ultra-low-latency applications, MMT supports MFU mode where
each video frame is delivered as a separate unit:

~~~
Standard MPU Mode (whole MPU in one object):
  Group N / Subgroup 0 / Object 0:
    [MMTP][MPU: mmpu+moov+moof+mdat containing all frames]

MFU Mode (one subgroup per MFU):
  Group N / Subgroup 0 / Object 0: [MMTP][MPU metadata: mmpu+moov]
  Group N / Subgroup 1 / Object 0: [MMTP FI=0][MFU: IDR frame NALUs]
  Group N / Subgroup 2 / Object 0: [MMTP FI=0][MFU: P frame NALUs]
  ...

MFU Mode, IDR fragmented across packets (Section 5.1):
  Group N / Subgroup 1 / Object 0: [MMTP FI=1][IDR fragment 1]
  Group N / Subgroup 1 / Object 1: [MMTP FI=2][IDR fragment 2]
  Group N / Subgroup 1 / Object 2: [MMTP FI=3][IDR fragment 3]
~~~

MFU mode enables:

- Per-frame FEC protection
- Frame-level prioritization (IDR vs P/B)
- Lower end-to-end latency

## MFU Fragmentation (Raw Passthrough)

A single MFU frequently exceeds the path MTU.  A 4K or 8K intra-coded
frame is hundreds of kilobytes to several megabytes and is fragmented
by the encoder into hundreds or thousands of MMTP packets.  Requiring
the publisher to reassemble such an MFU before forming a MoQ object
would force every receiver to re-fragment it for its own decoder
pipeline and would defeat per-fragment FEC and prioritization.

Therefore each MMTP packet maps to exactly one MoQ object, and the
publisher MUST NOT reassemble MFU fragments:

1. The publisher MUST publish each MMTP packet of an MFU as a separate
   object within that MFU's subgroup (Section 4.3), preserving the MMTP
   and MPU headers.  Those headers carry the Fragmentation Indicator
   and MPU sequence number; the reconstructed MoQ Object ID
   (Section 4.6) gives the fragment order within the subgroup.
2. The publisher MUST NOT interpret or act on the Fragmentation
   Indicator.  It routes each packet to (track, group, subgroup) by
   packet_id, MPU sequence, and MFU index only.
3. The receiver MUST reassemble each MFU from the objects of its
   subgroup before media processing, ordering by reconstructed Object
   ID:
   - A single object with FI=0 is a complete, unfragmented MFU.
   - Objects with FI=1 (first), FI=2 (zero or more middle), and FI=3
     (last) reassemble, in Object ID order, into one MFU by
     concatenating their payloads.
   - The reassembled MFU's RAP flag is taken from its FI=1 (or FI=0)
     object.
4. The receiver MUST bound the memory used for in-flight reassembly and
   MUST discard an MFU whose objects do not all arrive (for example
   under loss that FEC cannot repair), rather than buffer without
   limit.

For very large frames where FEC cannot recover the loss, receivers
SHOULD support resolution-tier fallback (subscribe to a lower-resolution
track of the switching set and upscale) rather than stalling.

# Subscriber Join and Relay Behavior

This section defines the join procedure for subscribers and the
retention behavior relays apply so that late joiners reach first
frame without waiting for the next group boundary.  Both are derived
from deployed implementations of this mapping; the retention rules in
Section 6.2 are purely positional (group, subgroup, and object
identifiers plus the Subgroup 0 convention of Section 4.3), so relays
remain container-blind and never parse MMTP.

## Subscriber Join Procedure

A subscriber joins a live mmtp-packaged track as follows:

1. **Catalog.** Fetch and validate the catalog.  Validation includes
   the per-track REQUIRED fields of Section 12.1 and the
   switching-set agreement check of Section 4.4.2.  A subscriber
   MUST NOT issue SUBSCRIBE for a track whose catalog entry fails
   validation.

2. **Decoder initialization.** If the track carries `initData`
   (Section 4.5) and it validates, initialize the decoder from it
   immediately.  Otherwise initialization completes when the first
   init-track object (`initMode: "track"`) or Subgroup 0 MPU-metadata
   object (`initMode: "inline"`) arrives.

3. **Subscribe at a group boundary.** Issue SUBSCRIBE requesting
   delivery from the start of the newest available group, not from
   the latest object.  The group start carries the MPU metadata
   (Subgroup 0) and the RAP-bearing first media subgroup
   (Section 4.3); a mid-group start position yields objects that
   cannot be decoded until the next group.  Where the relay retains
   the current group (Section 6.2), starting at the newest group
   boundary gives immediate decodability; otherwise the subscriber
   waits for the next group boundary.

4. **Repair track.** If the catalog signals FEC for the track, the
   subscriber SHOULD subscribe to the repair track (Section 8.2) at
   the same time as the source track, so that the first FEC block
   spanning the join point is repairable.

5. **Presentation gate.** A subscriber MUST NOT submit media to the
   decoder until it has (a) decoder initialization data (step 2) and
   (b) a completely reassembled MFU whose RAP flag is set
   (Section 5.1).  Objects received before that point are buffered
   or discarded according to the receiver's reassembly bounds.

6. **Loss and discontinuity.** If a RAP MFU is discarded under
   unrepairable loss (Section 5.1, step 4), the subscriber MUST
   treat the track as discontinuous and MUST NOT resume presentation
   before the next completely reassembled RAP MFU (normally the
   start of the next group).

## Relay Retention for Late Joiners

A relay that admits subscribers mid-stream SHOULD retain, for each
track it serves, all objects of the current (most recent) group.  At
minimum it SHOULD retain:

- the Subgroup 0 MPU-metadata object of the current group, and
- every object of the current group's first RAP-bearing media
  subgroup.

When a subscription joins mid-group, the relay SHOULD deliver the
retained objects of the current group from the group start —
including objects of subgroups that were already complete or still
open at join time — in subgroup and object order, ahead of or
interleaved with newly arriving objects.  A relay that holds earlier
objects of the current group MUST NOT deliver only objects published
after the join; doing so strands the subscriber until the next group
boundary and defeats retention.

Two completeness rules apply to replayed subgroups:

1. The relay MUST track which retained subgroups are finalized
   (closed by the publisher) and, when replaying a finalized
   subgroup, MUST deliver it completely; replaying a partial prefix
   of a finalized subgroup and silently omitting the remainder
   produces an MFU the receiver can never reassemble and is
   indistinguishable from network loss.
2. The relay SHOULD deliver the Subgroup 0 MPU-metadata object
   before media subgroups of the same group, so receivers without
   `initData` can initialize before media arrives.

Retention of groups older than the current group (for example to
serve FETCH-based catch-up) is permitted but out of scope for this
document.  Under cache pressure a relay MAY evict retained objects;
eviction converts a late join into a wait for the next group
boundary, which is the same behavior as a relay that retains nothing.

# FEC Integration

MMT's AL-FEC framework supports multiple FEC schemes including
RaptorQ [@!RFC6330] and Reed-Solomon [@!RFC5510],
with parameters signaled via MMTP signaling messages or, in
ATSC 3.0, via S-TSID (which is part of the ROUTE transport layer).
For MoQ, FEC repair uses the model defined in
[@MOQ-FEC]:

~~~
Source Track: video
  +-- Objects: MMTP packets with FEC Type=0 or 1 (source)

Repair Track: video/repair
  +-- Objects: MMTP packets with FEC Type=2 (repair)
~~~

## Interleaving

MMT AL-FEC interleaves source symbols across multiple MFUs:

~~~
MFU:        0    1    2    3    4    5    6    7
            |    |    |    |    |    |    |    |
Block 0:    S0   S1   S2   S3   ----------------->  R0, R1
Block 1:                        S4   S5   S6   S7 > R2, R3
~~~

Default interleave depth varies by application:

- ATSC 3.0: 30-60 frames (~1-2 seconds at 30fps)
- ARIB STD-B60: 60 frames (~2 seconds at 30fps)
- Low-latency: 4-8 frames (~130-270ms at 30fps)

## OTI Signaling

The S-TSID table contains RaptorQ OTI (Object Transmission Info):

~~~
S-TSID {
  source_filter (S,G address),
  fec_oti {
    transfer_length (40 bits),
    symbol_size (16 bits),
    num_source_blocks (8 bits),
    num_sub_blocks (16 bits),
    alignment (8 bits),
  }
}
~~~

For MoQ, OTI is signaled via FEC_CONFIG message per
[@MOQ-FEC] Section 4.

# FEC_CONFIG Message

The FEC_CONFIG message and its wire format are defined normatively
in [@MOQ-FEC] Section 4.1.  This document does not
redefine FEC_CONFIG but specifies MMT-specific considerations for
its use.

## MMT-Specific FEC_CONFIG Usage

When used with MMT packaging, the FEC_CONFIG fields map as follows:

- **FEC Algorithm**: Typically 0x01 (RaptorQ) for ATSC 3.0 ingest,
  or as specified in MMTP AL-FEC signaling
- **Source Symbols Per Block**: Corresponds to the number of MFUs
  (or MMTP packets) covered by one FEC block
- **Interleave Depth**: Number of MPU frames spanned by each FEC
  block, matching the original broadcast FEC interleave depth
- **OTI**: For RaptorQ, the 12-byte concatenation of Common FEC OTI
  and Scheme-Specific FEC OTI per [@RFC6330]

See [@MOQ-FEC] for the complete message format, field
definitions, algorithm registry, and precedence rules.

## Repair Track Discovery

When FEC is enabled, the repair track uses the naming convention
defined in [@MOQ-FEC] Section 6.1:

~~~
Source Track:  [namespace, track_name]
Repair Track:  [namespace, track_name, "repair"]
~~~

The subscriber MUST subscribe to the repair track separately.
The repair track uses lower priority (typically 7) so repair
symbols are dropped first under congestion.

## Multicast Delivery of FEC_CONFIG

For multicast (SSM/ASM) delivery where bidirectional signaling is
not available, FEC_CONFIG parameters are conveyed via:

1. **MMTP AL-FEC Signaling (message_id=0x0203)**: In-band delivery
   per ISO/IEC 23008-1:2023 Amendment 1:2025

2. **MoQ Catalog Extension**: Out-of-band delivery via catalog JSON:

~~~ json
{
  "tracks": [{
    "name": "video",
    "fec": {
      "algorithm": "raptorq",
      "sourceSymbols": 32,
      "repairSymbols": 8,
      "interleaveDepthMs": 1000,
      "symbolSize": 1312,
      "repairTrack": "video/repair"
    }
  }]
}
~~~

# Multicast Integration

MMT content can be delivered via IP multicast (SSM, AMT) and TreeDN
for scalable distribution.  Platform-specific delivery paths, the
multicast endpoint catalog extension, and TreeDN/AMT integration are
defined in [@MOQ-MULTICAST].

When MMT is delivered over multicast, MMTP packets are transmitted
as UDP datagrams with the standard MMTP header intact.  MoQ relays
at network edges terminate the multicast path and bridge MMTP
content into the MoQ application layer via QUIC/WebTransport.

For ATSC 3.0 and ARIB STD-B60 receivers, MMTP over SSM is the
native delivery path and requires no protocol translation.

# ARIB STD-B60 Compatibility

ARIB STD-B60 [@?ARIB-B60] (Japan's MMT-based broadcasting standard)
uses the same ISO 23008-1 foundation as ATSC 3.0.  Publishers SHOULD
preserve the original FEC parameters when ingesting ARIB STD-B60
content; ARIB deployments typically use larger source blocks and
deeper interleaving than ATSC 3.0 (Section 7).

## Clock Reference

ARIB STD-B60 uses UTC wallclock timestamps in NTP short format,
consistent with ISO 23008-1.  The MMTP Timestamp field carries the
UTC send time of the packet, which maps to MoQ object timestamps.

The MMTP Timestamp uses NTP short format (32-bit: 16-bit seconds +
16-bit fractional seconds relative to NTP epoch):

~~~
MoQ Timestamp (seconds) = MMTP Timestamp upper 16 bits
                          + (lower 16 bits / 65536)
~~~

Note: This differs from MPEG-2 TS, which uses a 90kHz PTS/DTS clock.

# Transport Hierarchy

Clients SHOULD attempt transports in preference order.  The transport
hierarchy for native clients (TV, mobile) and browser clients is
defined in [@MOQ-MULTICAST] Section 3.

For MMT-specific deployments, AL-FEC (Section 7) is essential on
SSM/AMT paths since there is no retransmission.  On MoQ/QUIC paths,
FEC reduces retransmission latency but QUIC provides a reliable
fallback.

# Catalog Signaling

The MoQ catalog indicates MMT packaging and multicast endpoints.

## Packaging Value and Track Fields

This document defines a single packaging value:

~~~
packaging: "mmtp"
~~~

carried in the per-track `packaging` field of the catalog
[@I-D.ietf-moq-catalogformat].  The same value is intended for any
packaging registry established by the MoQ Streaming Format
[@?I-D.ietf-moq-msf]; see Section 14.  Object payloads of an
mmtp-packaged track are whole MMTP packets per Section 4.2.

Earlier mapping variants are expressed without additional packaging
values: raw ISOBMFF delivery (formerly "isobmff") is CMAF packaging
per [@I-D.wilaw-moq-cmafpackaging] (Section 4.2 of this document),
and MFU mode (formerly "mfu") is a mode of mmtp packaging signaled
by the `mmtpMode` field below.

Per-track catalog fields for mmtp packaging:

| Field | Status | Type | Description |
|-------|--------|------|-------------|
| `packaging` | REQUIRED | String | MUST be "mmtp" |
| `mmtpMode` | REQUIRED | String | "mpu" or "mfu" (Section 5) |
| `timescale` | REQUIRED | Number | Media timescale in Hz (Section 4.4.2) |
| `groupDurationMs` | REQUIRED | Number | Group duration, integer ms (Section 4.4.2) |
| `groupDurationTicks` | OPTIONAL | Number | Integer-tick override (Section 4.4.2) |
| `keyframeIntervalMs` | OPTIONAL | Number | Keyframe/GOP cadence, integer ms; advisory, video only (Section 4.4.3) |
| `keyframeIntervalTicks` | OPTIONAL | Number | Integer-tick override for the keyframe interval (Section 4.4.3) |
| `initMode` | OPTIONAL | String | "inline" (default) or "track" (Section 4.5) |
| `initData` | OPTIONAL | String | Base64 ftyp+moov init segment (Section 4.5) |
| `fec` | OPTIONAL | Object | AL-FEC parameters (Section 8.3) |
| `selectionParams` | REQUIRED | Object | Codec and rendition parameters per [@I-D.ietf-moq-msf] |

`mmtpMode` selects the object layout: "mpu" delivers each whole MPU
as a single object; "mfu" delivers one subgroup per MFU as defined
in Sections 4.3 and 5.  A subscriber MUST reject a track whose
`mmtpMode` is absent or carries an unknown value — the object layout
cannot be inferred safely from received objects.  Per
[@I-D.ietf-moq-catalogformat], parsers MUST ignore unrecognized
fields.

Example:

~~~ json
{
  "tracks": [{
    "name": "video",
    "packaging": "mmtp",
    "mmtpMode": "mfu",
    "timescale": 90000,
    "groupDurationMs": 1000,
    "selectionParams": {
      "codec": "avc1.64001f",
      "width": 1920,
      "height": 1080,
      "framerate": 30
    }
  }]
}
~~~

## S-TSID to MoQ Catalog Conversion

When ingesting ATSC 3.0 content delivered via ROUTE, generate MoQ
catalog from the S-TSID signaling table (defined in ATSC A/331
[@?ATSC-A331] for the ROUTE transport layer).  For MMT-delivered
content, equivalent parameters are obtained from MMTP signaling
messages (MPT/MPI).  A complete worked example is given in
Appendix A.

The `multicast` field in the output uses the multicast endpoint format
defined in [@MOQ-MULTICAST] Section 4.1.  Conversion rules:

- `RS@sIpAddr` -> `multicast.endpoints[].sourceAddress`
- `RS@dIpAddr` -> `multicast.endpoints[].groupAddress`
- `RS@dPort` -> `multicast.endpoints[].port`
- each `LS` SrcFlow and RepairFlow -> a distinct
  `multicast.endpoints[].tracks[]` entry, with `packetId` assigned per
  the rule below
- `LS@bw` -> `selectionParams.bitrate`
- `FECParameters@overhead` -> `fec.repairSymbols` (computed as
  K x overhead / 100)
- `fecOTI` K,T -> `fec.sourceSymbols`, `fec.symbolSize`
- `fecOTI` Z (source blocks) x GOP duration -> `fec.interleaveDepthMs`

`packetId` is assigned per flow, not per `tsi`.  An `LS` (ROUTE
transport session) carrying both a SrcFlow and its RepairFlow yields
two `tracks[]` entries, and `packetId` MUST be unique within the
(sourceAddress, groupAddress, port) tuple (Section 4.1 of
[@MOQ-MULTICAST]); reusing `tsi` directly would collide for a repair
flow that shares its source's `tsi`.  The converter assigns `packetId`
sequentially in `tsi` order, emitting each source flow immediately
before its repair flow (so `tsi` 1 source -> packetId 1, its repair ->
packetId 2, `tsi` 2 source -> packetId 3).  Flows sharing one
(sourceAddress, groupAddress, port) tuple collapse into a single
endpoint whose `tracks[]` array lists them all.

`timescale`, `groupDurationMs`, and `mmtpMode` are not carried in
S-TSID; the converter obtains them from MMTP signaling (asset
descriptors and MPU presentation duration in the MPT/MPI tables) and
MUST populate them in the output catalog, since they are REQUIRED
fields (Section 12.1).

## MoQ Catalog to S-TSID Conversion

When generating ATSC-compatible output, convert the MoQ catalog to
S-TSID by inverting the mapping of Section 12.2.  Conversion rules:

- `multicast.endpoints[].sourceAddress` -> `RS@sIpAddr`
- `fec.repairSymbols / fec.sourceSymbols x 100` -> `FECParameters@overhead`
- `fec.interleaveDepthMs` -> `FECParameters@maximumDelay`

## Multicast Endpoint Catalog Extension

The multicast catalog extension is defined in
[@MOQ-MULTICAST] Section 4.

When converting S-TSID to MoQ catalog (Section 12.2), the `multicast`
field in the output catalog MUST conform to the multicast endpoint format
defined in [@MOQ-MULTICAST] Section 4.1, using the
`endpoints` array to represent per-TSI multicast groups.

# Security Considerations

MMT content protection uses Common Encryption (CENC) which is
preserved through MoQ transport.  The MMTP header is not encrypted,
allowing relays to inspect packet type and sequence without
accessing media content.

## Multicast Security

Multicast-specific security considerations (source authentication,
replay protection, AMT relay trust) are defined in
[@MOQ-MULTICAST] Section 7.

# IANA Considerations

This document defines the catalog `packaging` value "mmtp"
(Section 12.1) for use with [@I-D.ietf-moq-catalogformat].  If the
MoQ Streaming Format [@I-D.ietf-moq-msf] or the catalog format
establishes a registry of packaging values, this document requests
registration of:

| Value | Description | Reference |
|-------|-------------|-----------|
| "mmtp" | MMTP packets carrying MPU/MFU payloads | This document |

This document also requests registration of MoQ message type
(shared with [@MOQ-FEC]):

| Type | Name | Reference |
|------|------|-----------|
| 0x50 | FEC_CONFIG | This document |

{backmatter}

<reference anchor='ISO.23008-1'>
  <front>
    <title>Information technology - High efficiency coding and media delivery in heterogeneous environments - Part 1: MPEG media transport (MMT)</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2023'/>
  </front>
  <seriesInfo name='ISO/IEC' value='23008-1:2023'/>
</reference>

<reference anchor='MOQ-FEC'>
  <front>
    <title>Forward Error Correction for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-00'/>
</reference>

<reference anchor='MOQ-MULTICAST'>
  <front>
    <title>Multicast Delivery and Endpoint Discovery for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-multicast-00'/>
</reference>

<reference anchor='ATSC-A331' target='https://www.atsc.org/atsc-documents/3312017-signaling-delivery-synchronization-error-protection/'>
  <front>
    <title>Signaling, Delivery, Synchronization, and Error Protection</title>
    <author>
      <organization>ATSC</organization>
    </author>
    <date year='2025' month='February'/>
  </front>
  <seriesInfo name='ATSC' value='A/331:2025'/>
</reference>

<reference anchor='ARIB-B60'>
  <front>
    <title>MMT-Based Media Transport Scheme in Digital Broadcasting Systems</title>
    <author>
      <organization>ARIB</organization>
    </author>
    <date/>
  </front>
  <seriesInfo name='ARIB STD-B60' value='Version 1.14'/>
</reference>

# S-TSID Conversion Example

Complete example showing bidirectional conversion between
ATSC S-TSID and MoQ catalog for a multi-track service.

## Original ATSC S-TSID

~~~ xml
<?xml version="1.0" encoding="UTF-8"?>
<S-TSID
    xmlns="tag:atsc.org,2016:XMLSchemas/ATSC3/Delivery/S-TSID/1.0/">
  <RS sIpAddr="10.0.0.1" dIpAddr="232.1.1.10" dPort="5000">
    <!-- Video 1080p -->
    <LS tsi="1" bw="8000000">
      <SrcFlow rt="true" minBuffSize="8000000">
        <ContentInfo>
          <MediaInfo contentType="video" repId="1080p" lang="en"/>
        </ContentInfo>
        <EFDT>
          <FDT-Instance Expires="4294967295">
            <File Content-Location="video/1080p/init.mp4" TOI="1"/>
          </FDT-Instance>
        </EFDT>
        <Payload codePoint="128" formatId="2" srcFecPayloadId="6"/>
      </SrcFlow>
      <RepairFlow>
        <FECParameters maximumDelay="1000" overhead="25"
                       fecOTI="F=32;T=1312;Z=30;N=1;Al=8">
          <ProtectedObject tsi="1">
            <SourceTOI x="0" y="65535"/>
          </ProtectedObject>
        </FECParameters>
      </RepairFlow>
    </LS>
    <!-- Audio Stereo -->
    <LS tsi="2" bw="128000">
      <SrcFlow rt="true">
        <ContentInfo>
          <MediaInfo contentType="audio" repId="stereo" lang="en"/>
        </ContentInfo>
        <Payload codePoint="128" formatId="2"/>
      </SrcFlow>
    </LS>
  </RS>
</S-TSID>
~~~

## Converted MoQ Catalog

~~~ json
{
  "version": 1,
  "namespace": "atsc/service_broadcast",
  "generatedAt": "2026-07-15T10:30:00Z",
  "tracks": [
    {
      "name": "video/1080p",
      "packaging": "mmtp",
      "mmtpMode": "mfu",
      "timescale": 90000,
      "groupDurationMs": 1000,
      "selectionParams": {
        "codec": "avc1.64001f",
        "width": 1920,
        "height": 1080,
        "framerate": 30,
        "bitrate": 8000000,
        "lang": "en"
      },
      "fec": {
        "algorithm": "raptorq",
        "sourceSymbols": 32,
        "repairSymbols": 8,
        "symbolSize": 1312,
        "interleaveDepthMs": 1000,
        "repairTrack": "video/1080p/repair"
      }
    },
    {
      "name": "video/1080p/repair",
      "packaging": "fec-repair",
      "priority": 7
    },
    {
      "name": "audio/stereo",
      "packaging": "mmtp",
      "mmtpMode": "mfu",
      "timescale": 48000,
      "groupDurationMs": 1000,
      "selectionParams": {
        "codec": "mp4a.40.2",
        "samplerate": 48000,
        "channelConfig": "2",
        "bitrate": 128000,
        "lang": "en"
      }
    }
  ],
  "multicast": {
    "endpoints": [{
      "protocol": "ssm",
      "sourceAddress": "10.0.0.1",
      "groupAddress": "232.1.1.10",
      "port": 5000,
      "tracks": [
        { "name": "video/1080p",        "packetId": 1 },
        { "name": "video/1080p/repair", "packetId": 2 },
        { "name": "audio/stereo",        "packetId": 3 }
      ]
    }],
    "networkSource": {
      "type": "amt",
      "discovery": "driad"
    }
  }
}
~~~
