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

**MMTP**: MMT Protocol - the packet layer of MMT (ISO 23008-1 Clause 9)

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
  Reserved (2),
  Packet ID (16),
  Timestamp (32),
  Packet Sequence Number (32),
  [Packet Counter (32)],       // Present if C=1
  [Header Extension (..)]      // Present if X=1
}
~~~

The fixed fields sum to 96 bits (three 32-bit words).  Byte 0 is
version(2) | packet_counter_flag(1) | FEC_type(2) | reserved(1) |
extension_flag(1) | RAP_flag(1); byte 1 is packet_type(6) |
reserved(2), i.e. the packet type occupies the HIGH six bits of the
second byte ([@!ISO.23008-1] Clause 9.2).

Key fields for MoQ mapping:

- **Packet ID**: Maps to MoQ track within namespace
- **Timestamp**: UTC wallclock send time in NTP short format,
  carried inside the object payload.  MoQ Transport defines no
  per-object timestamp field; receivers needing the send time read
  it from the preserved MMTP packet header (see Section 10.1 for
  the format and its wrap period)
- **Packet Sequence Number**: per-`packet_id`, monotonic across the
  flow ([@!ISO.23008-1] Clause 9.2.2); carried inside the object payload
  for MMTP-layer loss/ordering detection.  NOT the MoQ Object ID —
  Object IDs are the per-MFU fragment index within a subgroup
  (Section 4.1), which resets per subgroup.
- **FEC Type**: 0=no AL-FEC, 1=AL-FEC source packet (a 4-byte
  Source FEC Payload ID trails the packet, [@!MOQ-FEC] Section 8.5),
  2=AL-FEC repair packet (ssbg_mode0), 3=AL-FEC repair packet
  (mode 1; not used by this mapping)
- **RAP Flag**: 1 indicates Random Access Point

# MoQ Object Mapping

## Track Structure

An MMT stream maps to MoQ tracks as follows:

| MMT Component | MoQ Mapping |
|---------------|-------------|
| Asset (stream) | Namespace |
| Packet ID (video) | Track "video" |
| Packet ID (audio) | Track "audio" |
| MPU (one MPU per group) | Group; number derived from media time (Section 4.4.1) |
| MFU within MPU (and Init metadata) | Subgroup ID |
| MMTP packet (fragment) within MFU | Object ID |
| AL-FEC repair | Track "video/repair" |

## Object Payload

Each MoQ object carries one complete MMTP packet:

~~~
MoQ Object Payload {
  MMTP Packet Header (12+ bytes),
  MMTP Payload (MPU-mode payload header,
                then MPU metadata or MFU fragment),
  [Source FEC Payload ID (32)],   // trails FEC Type=1 packets
}
~~~

Throughout this document, "MMTP packet" means the header-included
wire unit and "MMTP payload" means the bytes that follow the packet
header, per [@!ISO.23008-1].  Both MMTP header layers are always
preserved: the packet header carries the FEC Type, RAP Flag, and
timestamp, and the MPU-mode payload header (the first bytes of the
MMTP payload) carries the Fragmentation Indicator and MPU sequence
number that receivers and the FEC layer depend on.  This document
does not define a
header-stripped delivery mode.  A publisher that wishes to deliver
raw ISOBMFF fragments without MMTP encapsulation publishes the track
with CMAF packaging per [@!I-D.wilaw-moq-cmafpackaging] instead (an
MPU corresponds to a CMAF Fragment and an MFU to a CMAF Chunk; see
Section 4.3).

## Group Boundaries

This section defines the object layout of mfu mode
(`mmtpMode: "mfu"`, Section 12.1) — the only object layout this
document fully specifies and the only one deployments to date use.

Group boundaries align with MPU boundaries, and subgroup boundaries
align with MFU boundaries:

- Each group contains all objects of exactly one MPU: a change of MPU
  sequence number starts a new group.  The group's *number* is not the
  MPU sequence number; it is derived from media time by the formula in
  Section 4.4.1.
- Subgroup 0 of each group carries the MPU metadata (mmpu/moov boxes)
  as its single object.
- Subgroups 1..M each carry exactly one MFU.  The objects within an MFU
  subgroup are that MFU's MMTP packets in fragment order: a single
  object with Fragmentation Indicator FI=0 (a complete, unfragmented
  MFU), or objects with FI=1 (first), FI=2 (zero or more middle), and
  FI=3 (last) for an MFU fragmented across packets.
- The first media object of each group SHOULD have RAP Flag = 1.

The MPU sequence number remains present in-band (in the MMTP payload
header of every MPU fragment) and delimits which packets belong to the
same group, but it is NOT the MoQ Group number.  Publishers MUST NOT
copy the MPU sequence number into the Group number, and subscribers
MUST NOT derive media time or switching decisions from it.  (The MPU
sequence number is a per-encoder counter with an arbitrary starting
value; two independently started encoders of the same content disagree
on it, so counter-based group numbering cannot satisfy the switching-set
alignment requirements of Section 4.4.  Implementations that predate
this document and number groups by such a counter interoperate only
with themselves and only outside switching sets; this is legacy
behavior, not a conforming mode.)

This realizes the Chunk-to-Object mode of [@!I-D.wilaw-moq-cmafpackaging]
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
media (e.g., an ABR ladder), they form a switching set: a set of
alternate tracks that MUST be time-aligned per
[@!I-D.ietf-moq-msf] Section 4.2 (the same construct that
[@?I-D.ietf-moq-cmsf] Section 3.2 applies to CMAF tracks).  MoQ
Group numbers MUST be media-time-aligned across all tracks of a
switching set so that subscribers can switch at group boundaries
without discontinuity.

Switching-set membership is declared in the catalog via the
per-track field:

~~~
altGroup (OPTIONAL, unsigned integer)
~~~

defined by [@!I-D.ietf-moq-msf] Section 5.2.12: an integer
identifying a group of tracks that are alternate versions of one
another.  This document does not redefine the field; it profiles
membership exactly.
Two tracks are members of the same switching set if and only if both
carry the `altGroup` field and the values are equal.  A track that
omits `altGroup` is a member of no switching set, and the
switching-set requirements of this section do not bind it.  Every
normative statement in this document that ranges over "tracks of a
switching set" (or "the same switching set") ranges over exactly this
membership.  A repair track (Section 8.2) protecting a member track
carries the same `altGroup` value as the track it protects.

### Group Number Formula

The Group number of every mmtp-packaged track MUST be computed from
media time by the formula in this section.  This single definition is
what makes group boundaries align across the renditions of a
switching set, and what lets the FEC interleave window (Section 7.1)
map deterministically onto whole groups:

~~~
group_number = floor(ticks / groupDurationTicks)    if ticks >= 0
group_number = 0                                    if ticks <  0
~~~

where:

- `ticks` is the presentation timestamp of the group's first sample
  in decode order (under B-frame reordering, the first sample in
  decode order — not the sample with the minimum presentation
  timestamp), expressed in the track's `timescale` (Hz, Section
  4.4.2) as a signed integer.
- `groupDurationTicks` is the per-track group duration expressed
  in the same `timescale`, as a positive integer.  The catalog
  signals it via Section 4.4.2; conversion from the integer-millisecond
  form is exact by construction (the catalog publisher rejects
  non-exact pairs and uses the integer-tick override instead).
- Negative `ticks` (which can occur during encoder start-up or on
  B-frame reorder near the start of the timeline) MUST clamp to
  group number 0, as shown above.

Timeline origin: `ticks` is measured on the track's media
presentation timeline; all tracks of a switching set share one such
timeline.  Tick 0 is the start of the presentation — the earliest
presentation time the publisher assigns to any sample of the
switching set (or, for a track in no switching set, of the track
itself) — NOT an NTP or wall-clock epoch, and NOT the Timestamp
field of the MMTP packet header (which is NTP-derived and unrelated
to this formula).  For ISOBMFF-derived MPU content this is the media
composition timeline carried by the MPU's movie fragment metadata.
All tracks of a switching set MUST publish sample timestamps on this
common timeline; a publisher that resets the timeline (a timeline
discontinuity) MUST reset it identically, at the same media instant,
across all tracks of the switching set.

All arithmetic is in integers: `ticks` and `groupDurationTicks` are
integers, `floor(ticks / groupDurationTicks)` is integer division,
and implementations MUST NOT compute the group number in floating
point or apply any tolerance.  An input held in another unit
(seconds, milliseconds, a different timescale) MUST be converted to
an exact integer tick count before the formula is applied; if that
conversion is not exact, the publisher's timescale or group-duration
choice is wrong (Section 4.4.2) — implementations MUST NOT round to
compensate.

The same `(ticks, groupDurationTicks)` pair, fed through this
formula, MUST produce the same group number in every implementation
that participates in the switching set.

Worked example.  A switching set of two video renditions of the same
content: rendition A with `timescale: 90000`, rendition B with
`timescale: 44100`, both with `groupDurationMs: 2000` in the catalog
(Section 4.4.2).  The sample that is 10.5 seconds into the shared
presentation timeline has an integer timestamp in both timescales:

~~~
A: groupDurationTicks = 2000 * 90000 / 1000 = 180000
B: groupDurationTicks = 2000 * 44100 / 1000 =  88200

Same media instant, t = 10.5 s on the shared timeline:
A: ticks = 945000   ->  floor(945000 / 180000) = 5
B: ticks = 463050   ->  floor(463050 /  88200) = 5
~~~

Both renditions place the instant in group 5.  No intermediate value
is shared between the two computations — only the integer results
agree — which is exactly the property group-boundary switching
requires.

### Catalog Signaling of Group Duration

For a subscriber to apply the formula in Section 4.4.1, the catalog
MUST publish the group duration for every mmtp-packaged track.
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
([@!I-D.ietf-moq-msf] Section 5.2.4, REQUIRED), NOT a `container`
field.  The base specification defines the value `loc` (among
others); [@?I-D.ietf-moq-cmsf] Section 3.5.1 extends the allowed
values with `cmaf`; and this document adds `mmtp` in the same
manner (Section 12.1).  ("container kind" is used informally below
as a synonym for the `packaging` value.)  Per-track codec is
carried in the flat, top-level `codec` field
([@!I-D.ietf-moq-msf] Section 5.2.18), as are the other rendition
parameters (Section 12.1); there is no nested parameter object.

The timescale is carried in the per-track `timescale` field —
defined by [@!I-D.ietf-moq-msf] Section 5.2.21 ("the number of time
units that pass per second") and OPTIONAL there — for every
container kind; no container kind uses a differently named or
nested field.  The subscriber resolves it per the track's container
kind:

| Container | Timescale source |
|-----------|------------------|
| `mmtp`    | The `timescale` field, which this document profiles as REQUIRED for mmtp tracks (Section 12.1).  ISO 23008-1 Annex A.4 lists 90 000 Hz only as a video convention; the catalog does not infer audio timescales, so leaving the field unset is a catalog error. |
| `cmaf`    | The `timescale` field.  [@?I-D.ietf-moq-cmsf] leaves it OPTIONAL, so this document makes it REQUIRED for any cmaf track to which this section applies (a member of a switching set governed by Section 4.4.1); leaving it unset on such a track is a catalog error. |
| `loc`     | The `timescale` field; when absent, 1 000 000 — LOC timestamps are expressed in microseconds [@?I-D.ietf-moq-loc]. |
| (absent or unrecognized `packaging`) | 1 000 000 (microseconds).  This row covers track entries from legacy publishers predating this document whose `packaging` value is missing or unrecognized; the convention is fixed by this document and does NOT derive from [@!I-D.ietf-moq-transport]. |

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

Publishers signal MPU metadata (mmpu/moov) inline, as the single
object of Subgroup 0 of each group (the form defined in
Section 4.3).  The catalog field `initMode` (values: "inline" |
"track") records the signaling mode; subscribers determine the
active mode from the catalog before issuing SUBSCRIBE.  "inline" is
the default, the only mode deployments to date use, and the only
mode subscribers are REQUIRED to implement.

The value "track" — MPU metadata carried on a separate init track
per [@!I-D.wilaw-moq-cmafpackaging] Section 6.2 — is preserved as an
optional extension point and is at risk of removal: this document
does not specify how per-group MPU metadata (which changes with
every group, since it carries the MPU sequence number) maps onto
that document's single-object init track, nor whether Subgroup 0 is
still present, so "track" mode cannot be used interoperably without
a companion specification.  A subscriber MAY reject a track whose
`initMode` names a mode it does not implement.

In addition, publishers SHOULD carry decoder initialization data
directly in the catalog via the per-track field:

~~~
initData (OPTIONAL, string)
~~~

`initData` is the base64 encoding of an ISOBMFF initialization
segment (`ftyp` + `moov`) sufficient to initialize the decoder for
the track (including the codec configuration record, e.g. avcC or
hvcC).  The field name and carriage — a base64 string in the
track's catalog entry — are those of the `initData` field defined
by [@?I-D.ietf-moq-cmsf] Section 3.1 for CMAF headers; this
document applies the same field to mmtp-packaged tracks and
constrains its decoded content as below.  (The base catalog
[@!I-D.ietf-moq-msf] Sections 5.1.7 and 5.2.13 additionally define
an indirected `initDataList`/`initRef` mechanism; this document
does not use the indirection — mmtp tracks carry `initData`
inline.)  It lets a subscriber initialize its decoder at
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
MPU Mode (optional extension point; informative sketch,
Section 12.1):
  Group N / Subgroup 0 / Object 0:
    [MMTP][PH][MPU: mmpu+moov+moof+mdat containing all frames]

MFU Mode (one subgroup per MFU):
  Group N / Subgroup 0 / Object 0: [MMTP][PH][MPU meta: mmpu+moov]
  Group N / Subgroup 1 / Object 0: [MMTP][PH FI=0][MFU: IDR NALUs]
  Group N / Subgroup 2 / Object 0: [MMTP][PH FI=0][MFU: P NALUs]
  ...

MFU Mode, IDR fragmented across packets (Section 5.1):
  Group N / Subgroup 1 / Object 0: [MMTP][PH FI=1][IDR fragment 1]
  Group N / Subgroup 1 / Object 1: [MMTP][PH FI=2][IDR fragment 2]
  Group N / Subgroup 1 / Object 2: [MMTP][PH FI=3][IDR fragment 3]

[MMTP] = 12-byte MMTP packet header (Section 3.1).
[PH]   = MPU-mode payload header, which carries the Fragmentation
         Indicator (FI); the FI is NOT in the MMTP packet header.
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
   object within that MFU's subgroup (Section 4.3), preserving the
   MMTP packet header and the MPU-mode payload header.  Those headers
   carry the Fragmentation Indicator
   and MPU sequence number; the reconstructed MoQ Object ID
   (Section 4.6) gives the fragment order within the subgroup.
2. The publisher MUST NOT interpret or act on the Fragmentation
   Indicator.  It routes each packet to (track, group, subgroup) by
   packet_id, MPU boundary, and MFU index only: a change of MPU
   sequence number starts the next group (Section 4.3), whose number
   comes from the formula in Section 4.4.1.
3. The receiver MUST reassemble each MFU from the objects of its
   subgroup before media processing, ordering by reconstructed Object
   ID:
   - A single object with FI=0 is a complete, unfragmented MFU.
   - Objects with FI=1 (first), FI=2 (zero or more middle), and FI=3
     (last) reassemble, in Object ID order, into one MFU by
     concatenating each fragment's media bytes, delimited as defined
     below.
   - The reassembled MFU's RAP flag is taken from its FI=1 (or FI=0)
     object.

   The bytes concatenated are each fragment's media (data unit)
   bytes only — NOT everything after the MMTP packet header.  Every
   fragment begins with the 12-byte MMTP packet header followed by
   the 8-byte MPU-mode payload header (payload_length (16),
   fragment_type (4), timed_flag (1), fragmentation_indicator (2),
   aggregation_flag (1), fragment_counter (8),
   MPU_sequence_number (32); [@!ISO.23008-1]); both are stripped from
   every fragment.  The MFU header (the DU header: 14 bytes for
   timed media — movie_fragment_sequence_number (32),
   sample_number (32), offset (32), priority (8),
   dep_counter (8) — or 4 bytes for non-timed media) follows the
   payload header on an FI=0 object and on the FI=1 first fragment;
   it is likewise stripped rather than concatenated into the media
   stream.  When the packet's FEC Type is 1, the trailing 4-byte
   Source FEC Payload ID ([@!MOQ-FEC] Section 8.5) is excluded as
   well.  Concatenating the raw post-packet-header bytes of the
   fragments would interleave per-fragment payload-header bytes
   into the reassembled MFU and corrupt it.
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

1. **Catalog.** Fetch and validate the catalog (the track named
   `catalog`, Section 12).  Validation includes
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

4. **Repair track.** If the subscriber wants FEC protection and the
   catalog signals FEC for the track, it SHOULD subscribe to the
   repair track (Section 8.2) at the same time as the source track,
   so that the first FEC block spanning the join point is
   repairable.  Repair-track subscription is selective and optional
   ([@!MOQ-FEC] Section 6.2).

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
RaptorQ [@!RFC6330] and Reed-Solomon [@?RFC5510],
with parameters signaled via MMTP signaling messages or, in
ATSC 3.0, via S-TSID (which is part of the ROUTE transport layer).
For MoQ, RaptorQ is the mandatory-to-implement and only fully
specified scheme ([@!MOQ-FEC] Section 4.3), and FEC repair uses the
model defined in [@!MOQ-FEC]:

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

Default interleave window (`interleaveDepthMs`, milliseconds) varies
by application; the equivalent frame count D follows from the frame
duration ([@!MOQ-FEC] Section 8.3):

- ATSC 3.0: 1000-2000 ms (30-60 frames at 30fps)
- ARIB STD-B60: 2000 ms (60 frames at 30fps)
- Low-latency: 133-267 ms (4-8 frames at 30fps)

## OTI Signaling

The S-TSID table contains RaptorQ OTI (Object Transmission Info):

~~~
S-TSID {
  source_filter (S,G address),
  fec_oti {
    transfer_length (40 bits),
    reserved (8 bits),
    symbol_size (16 bits),
    num_source_blocks (8 bits),
    num_sub_blocks (16 bits),
    alignment (8 bits),
  }
}
~~~

For MoQ, no OTI is carried in-session: receivers derive the
complete RaptorQ OTI from the catalog `fec` fields per
[@!MOQ-FEC] Section 4.2 (Transfer Length F = K x T, Symbol Size T,
Z = 1 source block, N = 1 sub-block, Al = 8).  The S-TSID
`fec_oti` above is an ingest-side input only; Section 12.2 defines
its conversion to catalog fields.

# FEC Parameter Signaling

FEC parameters for mmtp-packaged tracks are signaled in the catalog
`fec` object, defined normatively in [@!MOQ-FEC] Section 5 — the
sole normative FEC signaling mechanism.  There is no in-session FEC
signaling; the legacy FEC_CONFIG control message is non-normative
and preserved for archival purposes in Appendix C of [@!MOQ-FEC].
This document does not redefine the catalog fields but specifies
MMT-specific considerations for their use.

## MMT-Specific FEC Parameters

When used with MMT packaging, the catalog `fec` fields map as
follows:

- **algorithm**: Typically "raptorq" for ATSC 3.0 ingest,
  or as specified in MMTP AL-FEC signaling
- **sourceSymbols**: The number of MMTP packets (source symbols)
  per FEC block; on the MMT path the canonical FEC source symbol is
  one whole MMTP packet ([@!MOQ-FEC] Section 7.3)
- **interleaveDepthMs**: The FEC interleave window in milliseconds —
  the time span of each FEC block ([@!MOQ-FEC]
  Section 5.1).  The number of MPU frames per block is derived as
  D = ceil(interleaveDepthMs / groupDurationMs), using the
  `groupDurationMs` field of Section 12.1.  When ingesting broadcast
  content, set the window to the time span of the original broadcast
  FEC interleave (its frame count multiplied by the frame duration)
- **OTI**: Not signaled.  Receivers derive the RaptorQ OTI
  (F = K x T, Z = 1, N = 1, Al = 8) from the catalog fields per
  [@!MOQ-FEC] Section 4.2

See [@!MOQ-FEC] for the complete catalog field definitions, the
algorithm registry, and the OTI derivation.

## Repair Track Discovery

When FEC is enabled, the repair track uses the naming convention
defined in [@!MOQ-FEC] Section 6.1:

~~~
Source Track:  [namespace, track_name]
Repair Track:  [namespace, track_name, "repair"]
~~~

Subscription to the repair track is selective and optional, per the
subscription model of [@!MOQ-FEC] Section 6.2 (the normative
statement of that model): a subscriber that wants FEC protection
issues its own, separate subscription for the repair track, and
subscribers are never required to subscribe to it.  The repair
track uses a lower-precedence priority than the source track it
protects.  Priorities are expressed in the MoQ Transport scale —
8-bit values 0-255 where a numerically LOWER value is delivered
with HIGHER precedence — so lower precedence means a numerically
GREATER value (e.g. 240 for the repair track against a source
track at the default 128; [@!MOQ-FEC] Section 10), and repair
symbols are dropped first under congestion.

## FEC Signaling for Multicast Delivery

For multicast (SSM/ASM) delivery there is no bidirectional
signaling channel; this is one of the reasons the catalog is the
sole normative signaling mechanism.  FEC parameters reach multicast
receivers via:

1. **MoQ Catalog Extension** (normative for MoQ receivers):
   out-of-band delivery via catalog JSON:

~~~ json
{
  "tracks": [{
    "name": "video",
    "fec": {
      "algorithm": "raptorq",
      "sourceSymbols": 32,
      "repairSymbols": 8,
      "interleaveDepthMs": 133,
      "symbolSize": 1312,
      "repairTrack": "video/repair"
    }
  }]
}
~~~

2. **MMTP AL-FEC Signaling (message_id=0x0203)**: in-band delivery
   per ISO/IEC 23008-1:2023 Amendment 1:2025, for native broadcast
   (ATSC 3.0, ARIB STD-B60) receivers

With frame-grouped MMTP delivery at 30 fps (33.33 ms per group), the
133 ms interleave window derives D = ceil(133 / 33.33) = 4 groups
per block, each contributing K / D = 32 / 4 = 8 source symbols;
block capacity is K x T = 32 x 1312 = 41,984 bytes per 133 ms
(about 2.5 Mbit/s of source data).

# Multicast Integration

MMT content can be delivered via IP multicast (SSM, AMT) and TreeDN
for scalable distribution.  Platform-specific delivery paths, the
multicast endpoint catalog extension, and TreeDN/AMT integration are
defined in [@!MOQ-MULTICAST].

When MMT is delivered over multicast, each UDP datagram carries one
complete MMTP packet, standard MMTP packet header included.  MoQ relays
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
UTC send time of the packet.  MoQ Transport defines no per-object
timestamp field; the send time remains available to receivers from
the preserved MMTP packet header (Section 4.2).

The MMTP Timestamp uses NTP short format (32-bit: 16-bit seconds +
16-bit fractional seconds relative to the NTP epoch):

~~~
Send time (seconds) = Timestamp upper 16 bits
                      + (lower 16 bits / 65536)
~~~

Because the seconds part is 16 bits, the value wraps every 65 536
seconds (about 18.2 hours): it identifies the send time modulo that
period and MUST NOT be interpreted as an absolute wallclock time
without an out-of-band era reference.

Note: This differs from MPEG-2 TS, which uses a 90kHz PTS/DTS clock.

# Transport Hierarchy

Clients SHOULD attempt transports in preference order.  The transport
hierarchy for native clients (TV, mobile) and browser clients is
defined in [@!MOQ-MULTICAST] Section 3.

For MMT-specific deployments, AL-FEC (Section 7) is essential on
SSM/AMT paths since there is no retransmission.  On MoQ/QUIC paths,
FEC reduces retransmission latency but QUIC provides a reliable
fallback.

# Catalog Signaling

The MoQ catalog indicates MMT packaging and multicast endpoints.

The catalog of this suite is an MSF catalog: the root object and
its fields (`version`, `generatedAt`, `tracks`, ...), the
requirement that parsers ignore fields they do not understand, and
the base per-track fields are those of [@!I-D.ietf-moq-msf]
Section 5.  The catalog is delivered as a MoQ track whose
case-sensitive Track Name is `catalog` ([@!I-D.ietf-moq-msf]
Section 5); [@!MOQ-MULTICAST] Section 4 gives transitional-alias
guidance for legacy deployments that used other names.  The
documents of this suite extend the base in the same manner as
[@?I-D.ietf-moq-cmsf] extends it: this document adds the packaging
value `mmtp` and the mmtp track fields (Section 12.1), [@!MOQ-FEC]
adds the per-track `fec` object and the `fec-repair` packaging
value, and [@!MOQ-MULTICAST] adds the root-level `multicast`
member.  Every catalog field this suite uses is defined either by
[@!I-D.ietf-moq-msf] or locally by a document of this suite (with
`cmaf` tracks and `initData` per [@?I-D.ietf-moq-cmsf]); no field
is defined by any other catalog specification.

## Packaging Value and Track Fields

This document defines a single packaging value:

~~~
packaging: "mmtp"
~~~

carried in the per-track `packaging` field of the catalog
([@!I-D.ietf-moq-msf] Section 5.2.4).  The value extends the
allowed packaging values of that specification in the same manner
as the `cmaf` value of [@?I-D.ietf-moq-cmsf] Section 3.5.1; see
Section 14 for the registry request.  Object payloads of an
mmtp-packaged track are whole MMTP packets per Section 4.2.

Earlier mapping variants are expressed without additional packaging
values: raw ISOBMFF delivery (formerly "isobmff") is CMAF packaging
per [@!I-D.wilaw-moq-cmafpackaging] (Section 4.2 of this document),
and MFU mode (formerly "mfu") is a mode of mmtp packaging signaled
by the `mmtpMode` field below.

Per-track catalog fields for mmtp packaging:

| Field | Status | Type | Description |
|-------|--------|------|-------------|
| `packaging` | REQUIRED | String | MUST be "mmtp" |
| `mmtpMode` | REQUIRED | String | "mfu" (required to implement) or "mpu" (optional, at risk; Section 5); defined by this document |
| `timescale` | REQUIRED | Number | Media timescale in Hz ([@!I-D.ietf-moq-msf] Section 5.2.21, profiled REQUIRED here; Section 4.4.2) |
| `groupDurationMs` | REQUIRED | Number | Group duration, integer ms (Section 4.4.2); defined by this document |
| `groupDurationTicks` | OPTIONAL | Number | Integer-tick override (Section 4.4.2); defined by this document |
| `altGroup` | OPTIONAL | Number | Switching-set membership key ([@!I-D.ietf-moq-msf] Section 5.2.12, profiled in Section 4.4) |
| `keyframeIntervalMs` | OPTIONAL | Number | Keyframe/GOP cadence, integer ms; advisory, video only (Section 4.4.3); defined by this document |
| `keyframeIntervalTicks` | OPTIONAL | Number | Integer-tick override for the keyframe interval (Section 4.4.3); defined by this document |
| `initMode` | OPTIONAL | String | "inline" (default) or "track" (optional, at risk; Section 4.5); defined by this document |
| `initData` | OPTIONAL | String | Base64 ftyp+moov init segment ([@?I-D.ietf-moq-cmsf] Section 3.1, profiled in Section 4.5) |
| `fec` | OPTIONAL | Object | AL-FEC parameters, defined in [@!MOQ-FEC] Section 5 (Section 8) |

All other base track fields of [@!I-D.ietf-moq-msf] Section 5.2
apply unchanged.  In particular `name` and the rendition
parameters — `codec` ([@!I-D.ietf-moq-msf] Section 5.2.18; required
for media tracks per that section), `framerate`, `width`, `height`,
`samplerate`, `channelConfig`, `bitrate`, and `lang` — are flat,
top-level fields of the track object.  An earlier revision of this
suite nested the rendition parameters under a `selectionParams`
object taken from an expired catalog proposal; that form was never
emitted or parsed by any implementation and is removed.  Publishers
MUST emit the flat fields, and receivers MUST NOT expect a
`selectionParams` object.

`mmtpMode` selects the object layout.  "mfu" delivers one subgroup
per MFU as defined in Sections 4.3 and 5; it is the only layout
this document fully specifies, the only mode deployments to date
use, and the only mode subscribers are REQUIRED to implement.
"mpu" names a whole-MPU-per-object layout that is preserved as an
optional extension point and is at risk of removal: this document
does not further specify it (its group/subgroup layout, RAP
signaling, and interaction with the retention rules of Section 6.2
are undefined here, and the sketch in Section 5 is informative), so
it cannot be used interoperably without a companion specification.
A subscriber MUST reject a track whose `mmtpMode` is absent,
carries an unknown value, or names a mode the subscriber does not
implement — the object layout cannot be inferred safely from
received objects.  Per [@!I-D.ietf-moq-msf] Section 5, parsers MUST
ignore fields they do not understand.

Example:

~~~ json
{
  "tracks": [{
    "name": "video",
    "packaging": "mmtp",
    "mmtpMode": "mfu",
    "timescale": 90000,
    "groupDurationMs": 1000,
    "codec": "avc1.64001f",
    "width": 1920,
    "height": 1080,
    "framerate": 30
  }]
}
~~~

## S-TSID to MoQ Catalog Conversion

This section and its inverse (Section 12.3) are informative: they
document a mapping for ingesting ATSC 3.0 broadcast signaling into
MoQ catalogs and exporting it back, and impose no interoperability
requirements on MoQ publishers or subscribers.  Deployments to date
do not implement these conversions; the mapping is retained as
ingest and export guidance.  A converter's output catalog is
subject to the normative catalog requirements of Section 12.1 like
any other catalog.

When ingesting ATSC 3.0 content delivered via ROUTE, generate MoQ
catalog from the S-TSID signaling table (defined in ATSC A/331
[@?ATSC-A331] for the ROUTE transport layer).  For MMT-delivered
content, equivalent parameters are obtained from MMTP signaling
messages (MPT/MPI).  A complete worked example is given in
Appendix A.

The `multicast` field in the output uses the multicast endpoint format
defined in [@!MOQ-MULTICAST] Section 4.1.  Conversion rules:

- `RS@sIpAddr` -> `multicast.endpoints[].sourceAddress`
- `RS@dIpAddr` -> `multicast.endpoints[].groupAddress`
- `RS@dPort` -> `multicast.endpoints[].port`
- each `LS` SrcFlow and RepairFlow -> a distinct
  `multicast.endpoints[].tracks[]` entry, with `packetId` assigned per
  the rule below
- `LS@bw` -> `bitrate` ([@!I-D.ietf-moq-msf] Section 5.2.22)
- `FECParameters@overhead` -> `fec.repairSymbols` (computed as
  K x overhead / 100)
- `fecOTI` F,T -> `fec.sourceSymbols` (K = ceil(F / T)),
  `fec.symbolSize` (T)
- `FECParameters@maximumDelay` -> `fec.interleaveDepthMs` (both are
  durations in integer milliseconds; the RFC 6330 Z parameter — the
  number of source blocks — is unrelated to interleaving and does
  not map to any catalog FEC field)

No OTI is carried in the output catalog.  The MoQ-side decoder
configuration is re-derived from the catalog fields as
F = K x T, Z = 1, N = 1, Al = 8 ([@!MOQ-FEC] Section 4.2).  When the
ingested F is not a multiple of T, the final source symbol is
zero-padded to T under the fixed-T construction ([@!MOQ-FEC]
Section 7.3), and the re-derived transfer length K x T exceeds the
ingested F by exactly the padding length.

`packetId` is assigned per flow, not per `tsi`.  An `LS` (ROUTE
transport session) carrying both a SrcFlow and its RepairFlow yields
two `tracks[]` entries, and `packetId` is required to be unique
within the (sourceAddress, groupAddress, port) tuple by Section 4.1
of [@!MOQ-MULTICAST]; reusing `tsi` directly would collide for a
repair flow that shares its source's `tsi`.  The converter assigns
`packetId`
sequentially in `tsi` order, emitting each source flow immediately
before its repair flow (so `tsi` 1 source -> packetId 1, its repair ->
packetId 2, `tsi` 2 source -> packetId 3).  Flows sharing one
(sourceAddress, groupAddress, port) tuple collapse into a single
endpoint whose `tracks[]` array lists them all.

`timescale`, `groupDurationMs`, and `mmtpMode` are not carried in
S-TSID; the converter obtains them from MMTP signaling (asset
descriptors and MPU presentation duration in the MPT/MPI tables) and
populates them in the output catalog, since they are REQUIRED
fields (Section 12.1).

## MoQ Catalog to S-TSID Conversion

When generating ATSC-compatible output, convert the MoQ catalog to
S-TSID by inverting the mapping of Section 12.2.  Conversion rules:

- `multicast.endpoints[].sourceAddress` -> `RS@sIpAddr`
- `fec.repairSymbols / fec.sourceSymbols x 100` -> `FECParameters@overhead`
- `fec.interleaveDepthMs` -> `FECParameters@maximumDelay` (both are
  durations in milliseconds; no scaling by frame duration)
- `fec.sourceSymbols x fec.symbolSize` -> `fecOTI` F, with
  T = `fec.symbolSize`, Z = 1, N = 1, Al = 8 — the exported OTI is
  exactly the derived OTI of [@!MOQ-FEC] Section 4.2

## Multicast Endpoint Catalog Extension

The multicast catalog extension is defined in
[@!MOQ-MULTICAST] Section 4.

When converting S-TSID to MoQ catalog (Section 12.2), the `multicast`
field in the output catalog conforms to the multicast endpoint format
defined in [@!MOQ-MULTICAST] Section 4.1, using the
`endpoints` array to represent per-TSI multicast groups.

# Security Considerations

MMT content protection uses Common Encryption (CENC) which is
preserved through MoQ transport.  The MMTP packet and payload
headers are not encrypted by CENC, allowing relays and receivers to
inspect packet type, sequence, and fragmentation metadata without
accessing media sample content.

## Multicast Security

Multicast-specific security considerations (source authentication,
replay protection, AMT relay trust) are defined in
[@!MOQ-MULTICAST] Section 7.

# IANA Considerations

This document defines the catalog `packaging` value "mmtp"
(Section 12.1), extending the allowed packaging values of the MoQ
Streaming Format [@!I-D.ietf-moq-msf] Section 5.2.4 in the same
manner as [@?I-D.ietf-moq-cmsf].  If a registry of packaging
values is established for that format, this document requests
registration of:

| Value | Description | Reference |
|-------|-------------|-----------|
| "mmtp" | MMTP packets carrying MPU/MFU payloads | This document |

This document requests no MoQ message type registrations.  FEC
signaling is catalog-only ([@!MOQ-FEC] Section 5); the legacy
FEC_CONFIG control message is non-normative, is described only in
Appendix C of [@!MOQ-FEC], and has no codepoint registered or
claimed by any document in this suite.

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

This appendix is informative, like the conversion mapping it
illustrates (Section 12.2).

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
                       fecOTI="F=1000000;T=1000;Z=1;N=1;Al=8">
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
  "version": "draft-01",
  "tracks": [
    {
      "name": "video/1080p",
      "packaging": "mmtp",
      "mmtpMode": "mfu",
      "timescale": 90000,
      "groupDurationMs": 1000,
      "codec": "avc1.64001f",
      "width": 1920,
      "height": 1080,
      "framerate": 30,
      "bitrate": 8000000,
      "lang": "en",
      "fec": {
        "algorithm": "raptorq",
        "sourceSymbols": 1000,
        "repairSymbols": 250,
        "symbolSize": 1000,
        "interleaveDepthMs": 1000,
        "repairTrack": "video/1080p/repair"
      }
    },
    {
      "name": "video/1080p/repair",
      "packaging": "fec-repair",
      "priority": 240
    },
    {
      "name": "audio/stereo",
      "packaging": "mmtp",
      "mmtpMode": "mfu",
      "timescale": 48000,
      "groupDurationMs": 1000,
      "codec": "mp4a.40.2",
      "samplerate": 48000,
      "channelConfig": "2",
      "bitrate": 128000,
      "lang": "en"
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
    "networkSource": [{
      "type": "amt",
      "discovery": "driad"
    }]
  }
}
~~~

The catalog envelope is the MSF root ([@!I-D.ietf-moq-msf]
Section 5.1); the `version` value names the MSF revision the
catalog conforms to.  The converter publishes the catalog under the
namespace derived from the ingested service, and the track entries
inherit that namespace from the catalog track
([@!I-D.ietf-moq-msf] Section 5.2.2).  Rendition parameters
(`codec`, `width`, `bitrate`, `lang`, ...) are the flat base track
fields of [@!I-D.ietf-moq-msf] Section 5.2 (Section 12.1).

The FEC fields recompute from the S-TSID as follows:

- `sourceSymbols`: K = ceil(F / T) = ceil(1,000,000 / 1,000) = 1000
- `repairSymbols`: K x overhead / 100 = 1000 x 25 / 100 = 250
- `interleaveDepthMs`: `maximumDelay` = 1000 ms (both are durations)
- Derived MoQ OTI ([@!MOQ-FEC] Section 4.2):
  F = K x T = 1000 x 1000 = 1,000,000 bytes, Z = 1, N = 1, Al = 8 —
  identical to the ingested `fecOTI`, so the round trip is lossless

The converted parameters are internally consistent: with
`groupDurationMs` of 1000, the 1000 ms interleave window derives
D = ceil(1000 / 1000) = 1, so each MoQ Group is one FEC block and
SBN = Group_ID ([@!MOQ-FEC] Section 8).  Block capacity
K x T = 1000 x 1000 = 1,000,000 bytes exactly matches the source
data per window, `LS@bw` x 1.0 s / 8 = 8,000,000 / 8 = 1,000,000
bytes.
