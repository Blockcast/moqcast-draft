%%%
title = "MPEG Media Transport (MMT) Packaging for Media over QUIC"
abbrev = "MMT for MoQ"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
date = "2026-10-29T00:00:00Z"
keyword = ["MMT", "MMTP", "MoQ", "ATSC 3.0", "FEC"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-mmt-02"
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
container format for Media over QUIC (MoQ).  MMT carries media over
broadcast (ATSC 3.0, ARIB STD-B60), multicast, and unicast
(QUIC/WebTransport) networks.  This specification defines the mapping of
MMT packets to MoQ objects, the "iso-ssbg1-v1" block profile under which
the Forward Error Correction (FEC) mechanism for MoQ protects MMTP
packets -- its source symbols, its Source FEC Payload ID trailer, its
repair packet and its keyframe overlay -- the derivation of MoQ catalogs
from MMTP signaling, and compatibility considerations for both ATSC 3.0
and ARIB STD-B60 systems, including the ATSC 3.0 signed region.

{mainmatter}

{#introduction}
# Introduction

MPEG Media Transport (MMT) [@!ISO.23008-1] is a transport protocol
designed for delivery of multimedia content over heterogeneous
networks.  MMT is supported as a transport in ATSC 3.0 broadcast
television (Americas, South Korea), and is the basis for ARIB
STD-B60 (Japan).
MMT provides native support for:

- Media Processing Units (MPU, branded "mpuf" in the ISO Base Media
  File Format (ISOBMFF) [@!ISO.14496-12]) as the media container,
  with structural similarities to fMP4
- Application-Layer FEC (AL-FEC) supporting multiple schemes
  including RaptorQ and Reed-Solomon
- Cross-layer signaling for adaptive streaming
- Hybrid delivery combining broadcast and broadband

This document defines how MMT-encapsulated media can be transported
over MoQ [@!I-D.ietf-moq-transport], enabling:

1. **Broadcast-to-Unicast bridging**: Content from ATSC 3.0 or ARIB STD-B60
   broadcasts can be relayed to MoQ subscribers without transcoding
2. **FEC**: MMT's AL-FEC integrates with MoQ FEC repair tracks per
   [@!MOQ-FEC-CORE], under the "iso-ssbg1-v1" block profile that this
   document defines ((#fec-integration))
3. **Multicast promotion**: MoQ clients can receive Source-Specific
   Multicast (SSM) directly when available, per [@!MOQ-MULTICAST]
4. **Broadcast signaling**: Derive MoQ catalogs from MMTP signaling
   (Section 13.2)
5. **Broadcast interworking**: ATSC 3.0 A/331 AL-FEC sessions and the
   ATSC 3.0 signed region ((#atsc-compatibility) and
   (#a3sa-signed-region)), and ARIB STD-B60 ((#arib-compatibility))

{#relationship-to-other-moq-media-formats}
## Relationship to Other MoQ Media Formats

This specification complements existing MoQ packaging formats.  The
MOQT Streaming Format (MSF) [@!I-D.ietf-moq-msf] carries media
packaged with the Low Overhead Media Container (LOC)
[@!I-D.ietf-moq-loc], and CMSF [@?I-D.ietf-moq-cmsf] carries media
packaged in the Common Media Application Format (CMAF):

| Format | Container | Primary Use Case | FEC Block Profile |
|--------|-----------|------------------|-------------------|
| MSF (LOC) | WebCodecs chunks | Low-latency unicast | "moq-object-v1" |
| CMSF | CMAF fMP4 | Adaptive streaming | "moq-object-v1" |
| This spec (MMT) | MMTP + MPU (ISOBMFF) | Broadcast bridge | "iso-ssbg1-v1" |

The last column names the block profile under which the FEC mechanism of
[@!MOQ-FEC-CORE] protects tracks of each packaging. "moq-object-v1" is
the profile of [@!MOQ-FEC-CORE] Section
5.2: each loc or cmaf
object whose Object Status is Normal occupies whole source symbols.
"iso-ssbg1-v1" is the profile that (#iso-ssbg1-v1) of this document
defines: each FEC source packet (FEC Type 1) is one source symbol.  Both
are registered in the "MoQ FEC Block Profiles" registry of
[@!MOQ-FEC-CORE] Section 15.3.

MMT packaging fits these cases:

- Ingesting ATSC 3.0 or ARIB STD-B60 broadcasts
- FEC protection is required for multicast delivery
- Hybrid broadcast/unicast architectures are deployed
- Interoperability with broadcast receivers is needed

CMAF packaging (CMSF) fits these cases:

- Content originates as DASH/HLS
- No multicast delivery is planned
- Interoperability with existing CDN infrastructure is needed

A publisher that offers CMAF content can also carry it as an mmtp track
under "iso-ssbg1-v1", where an MPU corresponds to a CMAF Fragment
((#object-payload)).  Such a track is also how CMAF content reaches
multicast, because a multicast endpoint carries only mmtp tracks
([@!MOQ-MULTICAST] Section 4.1).
The cmaf track and its mmtp rendition are separate FEC instances
([@!MOQ-FEC-CORE] Section 5.1), and symbols of one
never repair the other.

{#relation-to-other-documents}
## Relation to the FEC Documents

This document is a companion of [@!MOQ-FEC-CORE], which defines the
scheme-independent FEC mechanism for MoQ and the configuration data
model that a catalog carries.  [@!MOQ-FEC-BLOCK] specifies the
Reed-Solomon and RaptorQ schemes, [@!MOQ-FEC-CATALOG] the catalog
encoding of the configuration, and [@!MOQ-FEC-MULTICAST] the delivery of
protected tracks over multicast, including the receiver repair policy.
This document defines the "iso-ssbg1-v1" block profile, the part of that
set that is specific to MMTP packets, and the ATSC 3.0 and ARIB STD-B60
interworking that relies on it.  [@!MOQ-MULTICAST] defines multicast
endpoint discovery and the multicast packet format on which the
multicast delivery of mmtp tracks rests.

{#terminology}
# Terminology

The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**",
"**SHALL NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**",
"**NOT RECOMMENDED**", "**MAY**", and "**OPTIONAL**" in this document
are to be interpreted as described in BCP 14 [@!RFC2119] [@!RFC8174] when,
and only when, they appear in all capitals, as shown here.

**MMTP**: MMT Protocol - the packet layer of MMT (ISO 23008-1 Clause 9)

**MPU**: Media Processing Unit - a generic container for independently
decodable timed or non-timed data ([@!ISO.23008-1] Clause 3.1.14)

**MFU**: Media Fragment Unit - a sample or subsample of timed media
data, or an item of non-timed media data, within an MPU
([@!ISO.23008-1] Clause 9.3.1)

**AL-FEC**: Application-Layer Forward Error Correction

**AU**: Access Unit

**SLT**: Service Layer Table - ATSC 3.0 bootstrap signaling

**MPT**: MMT Package Table - signaling table containing MMT asset info

**PA**: Package Access - the signaling message that carries the
tables a receiver needs to consume a Package, among them the MPT
([@!ISO.23008-1] Clause 10.3.2)

**MPI**: Media Presentation Information - signalling table carrying
the presentation information document ([@!ISO.23008-1] Clause 10.3.8)

The FEC terms of this document -- Source Track, Repair Track, Repair
Layer, FEC Instance, Source Symbol, Repair Symbol, Source Block, SS_ID,
SS_Start, SSB_length, RS_ID, RSB_length, Encoding Symbol ID (ESI) and
Block Profile -- are those of [@!MOQ-FEC-CORE] Section
2, and the RS_ID offset O_i and
per-block repair symbol count P_i of layer i are those of
[@!MOQ-FEC-CORE] Section 7.3.1.  Under
"iso-ssbg1-v1" the following take a form of their own, and the remaining
terms are specific to this document:

**Source Symbol**: Under "iso-ssbg1-v1", one FEC source packet framed as
(#iso-ssbg1-v1) specifies.

**Repair Track**: Under "iso-ssbg1-v1", a repair track carries MMTP FEC
repair packets ([@!ISO.23008-1] Section C.4.3; (#repair-packet)). The
layer-0 repair track carries the FEC repair flow ([@!ISO.23008-1] 3.1.9)
that an ISO AL-FEC message names for the source track's FEC encoded flow
(3.1.7); further repair layers and a keyframe overlay are repair tracks
that only the catalog declares (Section 8.3).

**SS_ID**: Under "iso-ssbg1-v1", the 32-bit sequence number of a source
symbol is carried in the Source FEC Payload ID of its FEC source packet
([@!ISO.23008-1] Section C.5.2) and advances by one per FEC source
packet ((#source-fec-payload-id)).

**Source Block**: Under "iso-ssbg1-v1", the ISO source symbol block
([@!ISO.23008-1] 3.1.34), generated from a source packet block (3.1.32).

**FEC Block**: The combination of SSB_length source symbols and P repair
symbols; the ISO encoding symbol block ([@!ISO.23008-1] 3.1.5).

**Keyframe Overlay**: A second, independent FEC instance over a source
track whose source symbols are only the fragments of Random Access
Points, with its own source symbol count, its own repair symbols, and
its own repair track, declared with `"scope": "keyframe"`
((#overlay-instance)).  An overlay is not a repair layer and carries no
layer index.  It is defined only under "iso-ssbg1-v1".

**Base Instance**: Of a source track that a keyframe overlay protects,
the instance that is not the overlay; of any other source track, its
only instance.

**Interleave Depth**: When positive, the complete time span, in
milliseconds, of one FEC source/repair packet block, signaled as
`interleaveDepthMs` ([@!MOQ-FEC-CORE] Section
9.3); the catalog form of
`protection_window_time` in [@!ISO.23008-1] Sections 11.2 and C.6.3.
Zero is not a millisecond span: under "iso-ssbg1-v1" it selects the ISO
packet-count alternative ((#interleaving)).

**Object Transmission Information (OTI)**: Parameters required to
configure a RaptorQ decoder, as defined in [@?RFC6330] and derived by
[@!MOQ-FEC-BLOCK] Section 6.1.

{#mmt-overview}
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

{#mmtp-header-format}
## MMTP Header Format

~~~
MMTP Header (12 bytes minimum) {
  Version (2),
  Packet Counter Flag (C) (1),
  FEC_type (FEC) (2),
  Reserved (1),
  Extension Flag (X) (1),
  RAP Flag (R) (1),
  Reserved (2),
  type (6),
  Packet ID (16),
  Timestamp (32),
  Packet Sequence Number (32),
  [Packet Counter (32)],       // Present if C=1 (never: C=0)
  [Header Extension (..)]      // Present if X=1
}
~~~

The fixed fields sum to 96 bits (three 32-bit words).  Byte 0 is
version(2) | packet_counter_flag(1) | FEC_type(2) | reserved(1) |
extension_flag(1) | RAP_flag(1); byte 1 is reserved(2) |
type(6), i.e. the packet type occupies the low six bits of
the second byte ([@!ISO.23008-1] Clause 9.2).

Senders MUST set all reserved bits in the MMTP packet header to zero.
Receivers MUST ignore their values after validating the header; they
MUST NOT assign private semantics to reserved bits.

Every packet of an MMTP packet flow -- media, repair, and signaling
packets alike, on every delivery path -- MUST set the packet counter
flag C to 0, so no packet carries the Packet Counter field.
[@!ISO.23008-1] Clause 9.2.3 requires all packets of an MMTP flow to
share one setting of C; this profile fixes that setting at 0.  The
MMTP packet header is therefore 12 bytes unless X = 1 adds a header
extension.

This document profiles MMTP version 0 (`V = 00`) of
ISO/IEC 23008-1:2023 as amended by Amd 1:2025.  A packet whose version
is not `00` MUST be rejected before its `type` field is parsed: version
1 uses a different type-field layout and is not defined by this
profile.  The `C = 0` requirement above is also a conformance gate;
packets with `C = 1` MUST be rejected.  An `X = 1` header extension is
parsed according to its declared length, but this document defines no
additional version or packet-counter semantics.

Key fields for MoQ mapping:

- **Packet ID**: Maps to MoQ track within namespace.  This document
  reserves packet_id 0 for the MMTP signaling flow: MMTP packets of
  packet type 0x02 carrying signaling messages, such as the PA message
  of a multicast endpoint flow ([@!MOQ-MULTICAST] Section
  5) and the
  AL-FEC message of Section 8.3.  No MoQ track is advertised for
  the signaling flow, but an mmtp source track MAY carry its AL-FEC
  message as an object (Section 8).  An MMTP packet carrying media
  (packet type 0x00) or a repair symbol (packet type 0x03) MUST NOT use
  packet_id 0; a
  track's packet_id is in the range 1..65535, and on multicast
  delivery it is the `packetId` the endpoint advertises for the
  track ([@!MOQ-MULTICAST] Section
  4.1).  On every delivery path, a
  receiver MUST NOT deliver an MMTP packet on packet_id 0 to a media
  or repair decoder, including one received as the payload of an
  object of a media or repair track: a receiver that processes MMTP
  signaling reads it as a signaling message, and any other receiver
  discards it ([@!MOQ-MULTICAST] Section
  5 states the same rule for
  every unlisted packet_id on multicast)
- **Timestamp**: UTC wallclock send time in the NTP short format of
  [@?RFC5905] Section 6 (32 bits: 16-bit seconds and 16-bit fraction,
  relative to the NTP epoch), carried inside the object payload.  MoQ
  Transport defines no per-object timestamp field; receivers needing the send time read
  it from the preserved MMTP packet header.  Because the seconds part
  is 16 bits, the value wraps every 65 536 seconds (about 18.2
  hours): it identifies the send time modulo that period and MUST NOT
  be interpreted as an absolute wallclock time without an out-of-band
  era reference.  It is used for packet delivery and jitter
  measurement and is never media time: not a decoding timestamp,
  presentation timestamp, duration, media-clock epoch, or
  movie-fragment identifier
- **Packet Sequence Number**: per-`packet_id`, incremented by one modulo
  2^32 across the flow ([@!ISO.23008-1] Clause 9.2.3); carried inside
  the object payload for wrap-aware MMTP-layer loss/ordering detection.
  It is not the MoQ Object ID.  Object IDs number the objects of a
  group in source order, starting at zero in each group (Section 4.6).
- **FEC Type**: 0=no AL-FEC, 1=AL-FEC source packet (exactly one
  4-byte Source FEC Payload ID trails the packet,
  (#source-fec-payload-id)), 2=AL-FEC repair packet for FEC payload
  ID mode 0,
  3=AL-FEC repair packet for FEC payload ID mode 1 (not used by this
  mapping) ([@!ISO.23008-1] Clause 9.2.3)
- **RAP Flag**: 1 indicates Random Access Point.  On a track that the
  catalog protects with a keyframe overlay, a packet with RAP_flag 1
  also carries the overlay's SS_ID in a header extension of type
  0x8B01 ((#overlay-header-extension))

A signaling packet (packet type 0x02, on packet_id 0) MUST carry its
messages in the signaling message mode of [@!ISO.23008-1]
Clause 9.3.4: its MMTP payload begins with the 2-byte payload header
of Clause 9.3.4.2:

~~~
Signaling Message Payload Header {
  f_i (2),                    // fragmentation indicator
  RES (4),                    // reserved, set to 0
  H (1),                      // 1: each MSG_length is 32 bits
  A (1),                      // aggregation_flag
  frag_count (8),             // fragmentation counter
}
~~~

When A = 1, a MSG_length field of 16 bits, or 32 bits when H = 1,
precedes each aggregated message; when A = 0 no MSG_length field is
present.  The signaling message follows ([@!ISO.23008-1]
Clause 10.2), beginning with its message_id.  A packet that carries
one complete signaling message without aggregation has f_i = 00,
A = 0, and frag_count = 0, and its sender sets H = 0 (H has no
effect when A = 0), so its payload header is the two bytes 0x00 0x00
and the message_id immediately follows them.  A receiver ignores H
when A = 0 and parses the header field by field, never by matching
those two bytes.

{#moq-object-mapping}
# MoQ Object Mapping

{#track-structure}
## Track Structure

An MMT stream maps to MoQ tracks as follows:

| MMT Component | MoQ Mapping |
|---------------|-------------|
| Package | Namespace |
| Asset, by Packet ID (video) | Track "video" |
| Asset, by Packet ID (audio) | Track "audio" |
| MPU (one MPU per group) | Group; number derived from media time (Section 4.4.1) |
| MPU data unit (FT=0, FT=1, or FT=2) | Subgroup ID |
| MMTP packet (fragment) within a data unit | Object; Object IDs count the group's objects from 0 in source order (Section 4.6) |
| AL-FEC signaling message (OPTIONAL, packet_id 0) | Object in Subgroup 0 immediately before FT=0 (Section 8) |
| AL-FEC repair | Track "video/repair" |

[@!I-D.ietf-moq-msf] Section 6 maps each object to a new stream.  An
mmtp track does not follow that rule.  It maps each MPU
data unit to one subgroup (Section 4.3), and the objects of a
subgroup share one stream ([@!I-D.ietf-moq-transport] Section 2.2),
so each data unit's fragments travel in order on one stream.  An mmtp
track keeps the Group and Object numbering of [@!I-D.ietf-moq-msf]
Sections 6.1 and 6.2: Group numbers are unique and increase
monotonically (Section 4.4.1), and Object IDs start at zero in each
group and increase by one (Section 4.6).

{#object-payload}
## Object Payload

Each MoQ object carries one complete MMTP packet:

~~~
MoQ Object Payload {
  MMTP Packet Header (12+ bytes),
  MMTP Payload (MPU-mode payload header,
                then an FT=0, FT=1, or FT=2 data-unit fragment),
  [Source FEC Payload ID (32)],   // trails FEC Type=1 packets
}
~~~

The object payload begins at byte zero of the preserved MMTP packet
header.  It has no MoQ-private envelope, length prefix, harness prefix,
or other undocumented bytes before that header.  For an FEC Type 1
packet, the Source FEC Payload ID and any profile-defined MMTP header
extensions remain in their specified wire locations.  No object-layer
prefix, suffix, or private replacement for those fields is permitted.
[@!MOQ-FEC-CORE] Section 5.6 requires
every source object to carry the FEC Source Info Object Property (type
`0x11`); on an mmtp source object its value is the four-byte form of
that section, which names instance 0 and carries the network-byte-order
`SS_ID` of the base instance, the value of the packet's Source FEC
Payload ID ((#source-fec-payload-id)); the property is object metadata
and is not inserted into this payload.

The one exception is the OPTIONAL AL-FEC signaling object of
Section 8: its payload is a complete MMTP signaling packet (packet
type 0x02) on packet_id 0 with FEC Type 0.  Its MMTP payload is the
signaling message payload header of Section 3.1 followed by one
complete AL-FEC message (f_i = 00, A = 0), rather than an MPU-mode
payload header and data-unit fragment, and it carries no Source FEC
Payload ID.  No other object on an mmtp source track uses packet
type 0x02 or packet_id 0.

Throughout this document, "MMTP packet" means the header-included
wire unit and "MMTP payload" means the bytes that follow the packet
header, per [@!ISO.23008-1].  Both MMTP header layers are always
preserved: the packet header carries the FEC Type, RAP Flag, and
timestamp, and the MPU-mode payload header (the first bytes of the
MMTP payload) carries the Fragmentation Indicator and MPU sequence
number that receivers and the FEC layer depend on.  A publisher that
wishes to deliver raw ISOBMFF fragments without MMTP encapsulation
publishes the track with CMAF packaging [@?I-D.ietf-moq-cmsf]
instead.  In this profile an MPU can contain one or more ISOBMFF movie
fragments: FT=1 carries one movie fragment's metadata and each FT=2
data unit carries one whole sample or one producer-authored subsample
of a sample (Section 5.2.1).

{#group-boundaries}
## Group Boundaries

This section defines the object layout of mfu mode
(`mmtpMode: "mfu"`, Section 13.1).

Group boundaries align with MPU boundaries, and subgroup boundaries
align with MPU data-unit boundaries:

- Each group contains all objects of exactly one MPU: a change of MPU
  sequence number starts a new group, numbered per Section 4.4.1.
- Subgroup 0 of each group carries exactly one complete FT=0 MPU
  metadata packet.  Its data unit contains the authored initialization
  boxes, including `ftyp`, `mmpu`, and `moov`, and uses FI=0.  When the
  publisher carries the OPTIONAL AL-FEC signaling object of Section 8,
  that object is in Subgroup 0 of the same group and is the object
  immediately before the FT=0 object; Subgroup 0 then carries exactly
  these two objects.  No other object precedes FT=0, and a group
  carries at most one signaling object.
- Subgroups 1..M each carry exactly one subsequent MPU data unit in
  authored order.  An FT=1 movie-fragment-metadata data unit is one
  complete FI=0 object.  An FT=2 timed sample is either one FI=0 object
  or an FI=1, zero-or-more FI=2, FI=3 object chain.  A timed sample
  whose media exceeds one data unit's capacity is carried as a
  contiguous run of producer-authored subsample data units
  (Section 5.2.1), one subgroup per subsample data unit, in ascending
  `offset` order.  Section 5.2 defines the only permitted
  fragmentation state machine.
- A timed MPU MUST publish its single FT=0 metadata data unit before
  any FT=1 or FT=2 data unit; only the OPTIONAL signaling object of
  Section 8 may precede FT=0.  It then MUST publish each FT=1
  data unit before every FT=2 sample or subsample that references that movie
  fragment.  If an MPU contains multiple movie fragments, the sequence
  repeats as FT=1 followed by its FT=2 samples.  A receiver MUST
  validate and process subgroups in ascending Subgroup ID, not network
  arrival order, and MUST NOT admit an FT=2 sample before its FT=1
  metadata: concurrently delivered subgroups MAY arrive in any order
  and are buffered until their turn.  A missing or duplicate FT=0 invalidates the group; a gap,
  duplicate data-unit identity, or invalid FT=1/FT=2 sequence in that
  logical order invalidates the affected movie fragment.  A receiver
  MUST NOT infer the missing structure.  The signaling object is not a
  data unit: its presence or absence does not affect this validation,
  and a signaling object anywhere other than immediately before FT=0
  in Subgroup 0, or a second one in a group, invalidates the group.
- The FI=0 or FI=1 object that begins the first FT=2 sample of each
  timed group -- for a subsample-partitioned sample, the object that
  begins its offset-0 data unit -- MUST have RAP Flag = 1.

The MPU sequence number remains present in-band (in the MMTP payload
header of every MPU fragment) and delimits which packets belong to the
same group, but it is not the MoQ Group number.  Publishers MUST NOT
copy the MPU sequence number into the Group number, and subscribers
MUST NOT derive media time or switching decisions from it.  (The MPU
sequence number is a per-Asset counter.  It starts at zero for the first
MPU in an Asset and increments by one for every following MPU
([@!ISO.23008-1] Clause 7.3.3), but it is
Asset-local: independently packetized renditions need not assign the
same MPU number to the same media instant.  Counter-based group
numbering therefore cannot satisfy the switching-set alignment
requirements of Section 4.4.)

For an ISOBMFF source, the publisher MUST preserve initialization in
FT=0, MUST copy the authored `moof` and the original `mdat` prefix
through the byte before the first media sample byte-for-byte into FT=1,
and MUST copy the referenced sample bytes byte-for-byte and without
transformation into FT=2.  A receiver can therefore reconstruct the
authored movie fragment without synthesizing box fields, sample timing,
or media bytes (Section 5.1).

Mapping each data unit to its own subgroup makes a complete metadata
unit or sample the unit of in-order delivery, loss, and FEC.  A
publisher MUST send the objects of an mmtp track in subgroups, not as
datagrams: a datagram object belongs to no subgroup
([@!I-D.ietf-moq-transport] Section 2.2) and cannot carry this
mapping.  Subgroups can be delivered concurrently, and a subgroup can
still be lost, for example when its stream is reset on a delivery
timeout ([@!I-D.ietf-moq-transport] Sections 5.2 and 11.3.2); the
resulting gap invalidates the affected movie fragment rather than
authorizing inferred metadata, timing, or cadence.

{#switching-sets}
## Switching Sets

When multiple tracks represent alternative renditions of the same
media (e.g., an adaptive bitrate (ABR) ladder), they form a
switching set: a set of alternate tracks that MUST be time-aligned per
[@!I-D.ietf-moq-msf] Section 4.2 (the same construct that
[@?I-D.ietf-moq-cmsf] Section 3.2 applies to CMAF tracks).  MoQ
Group boundaries MUST be media-time-aligned across all tracks of a
switching set so that subscribers can switch at group boundaries.
Tracks with equal group durations MUST carry the same Group number for the
same media interval.  Only an intra-only mmtp track can have a
shorter group duration than the other tracks, under the exception of
Section 4.4.2, which also defines its Group number mapping.  A cmaf
member keeps equal group durations and the Group number alignment
that [@?I-D.ietf-moq-cmsf] Section 3.2 requires.  The switch is
without discontinuity when the MPUs are closed groups of pictures
(GOPs).  On a join or switch at a Group boundary, leading pictures (Section 4.4.1)
that reference the preceding Group are not decodable, and presentation
of the new track begins at its RAP.  If the old track's next MPU has
leading pictures, neither track has decodable pictures for their
presentation interval, and the receiver conceals that gap.

Switching-set membership is declared in the catalog via the
per-track field:

~~~
altGroup (OPTIONAL, unsigned integer)
~~~

defined by [@!I-D.ietf-moq-msf] Section 5.2.12: an integer
identifying a group of tracks that are alternate versions of one
another.  Two tracks are members of the same switching set if and only if both
carry the `altGroup` field and the values are equal.  A track that
omits `altGroup` is a member of no switching set, and the
switching-set requirements of this section do not bind it.  A repair
track (Section 8.2) carries no `altGroup`.  It is not an alternate
rendition, and its Groups are FEC blocks ([@!MOQ-FEC-CORE] Section
7.6), not media-time-aligned
Groups.  A subscriber finds the repair tracks of the rendition it
selects through the `repairTrack` of each of that rendition's FEC
instances and the `source` fields of its repair tracks
([@!MOQ-FEC-CATALOG] Section 3.2; the data model of
[@!MOQ-FEC-CORE] Section 10.2).

{#group-number-formula}
### Group Number Formula

The Group number of every mmtp-packaged track MUST be computed from
media time by the formula in this section.  This single definition is
what makes group boundaries align across the renditions of a switching
set.  FEC interleave timing is independent of this grouping;
(#interleaving) does not derive FEC block boundaries or a number of
Groups per FEC block from this formula:

~~~
relative_ticks = ticks - presentationAnchorTicks
group_number = floor(relative_ticks / groupDurationTicks)
~~~

where:

- `ticks` is the presentation timestamp (PTS) of the MPU's first AU in
  decode order, expressed in the track's `timescale` (Hz, Section
  4.4.2) as a signed integer.  That AU is first in the MPU payload, as
  ISO/IEC 23008-1 requires, and is the MPU's RAP (Section 4.3).
  Leading pictures, which follow the RAP in decode order but present
  before it, do not select `ticks`, even when they present within the
  preceding MPU's Group interval.
- `groupDurationTicks` is the per-track group duration expressed
  in the same `timescale`, as a positive integer.  The catalog
  signals it either directly or through an exact millisecond
  conversion as specified in Section 4.4.2.
- `presentationAnchorTicks` is the signed timestamp in this track's
  `timescale` that corresponds to presentation time zero.  It includes
  the publisher's edit-list, encoder-priming, and composition-time
  decisions, and MUST be applied before the formula.  A track that is
  intended to be rendered with another audio or video track MUST signal
  this field; a track that is not part of a synchronized presentation
  MAY omit it and use zero as its local origin.

The publisher MUST choose `presentationAnchorTicks` no later than the
smallest `ticks` value of the MPUs it admits for the track.  If an
MPU's `ticks` is earlier than the anchor, the publisher MUST reject
that MPU.  Before the first group is published, the publisher MAY
instead revise the catalog anchor and validate the complete initial
input again; after publication, the anchor is immutable for that track
instance.  It MUST NOT clamp the Group number to zero.  The `floor` in
the formula is mathematical floor (floor division), not truncation
towards zero.  With the anchor requirement, every admitted MPU has a
non-negative `relative_ticks` value.  The requirement binds `ticks`
only; a leading picture of an admitted MPU can present before the
anchor.

Timeline origin: `ticks` is measured on the track's media
presentation timeline; `presentationAnchorTicks` maps that track to
the shared presentation timeline.  For every set of audio and video
tracks intended to be rendered together, the publisher MUST choose one
presentation origin and MUST signal an anchor for each track such that

~~~
presentation_time = (ticks - presentationAnchorTicks) / timescale
~~~

has the same rational value for samples representing the same media
instant.  This is a media-time relation, not an NTP or wall-clock
relation, and it is not the `Timestamp` field of the MMTP packet header
(Section 3.1).  For
ISOBMFF-derived MPU content, the anchor is applied to the composition
timeline after edit-list and priming adjustments.  All tracks of a
switching set MUST use the same presentation origin as well.  A
publisher that resets the timeline (a timeline discontinuity) MUST
reset it identically, at the same media instant, across every affected
audio, video, and switching-set track.  A discontinuity on an existing
track does not reset its Group number sequence.

This Group anchor is a MoQ scheduling and switching key only.  ISO/IEC
23008-1 presentation timing remains authoritative: the presentation time
of an MPU is signaled by the presentation information (or the
`mpu_timestamp_descriptor` when no presentation information is present),
with any applicable `elst` offset, and is not rewritten by this Group
number calculation.

For each track, when the MPU changes, the computed Group number MUST be
strictly greater than the Group number of the preceding admitted MPU.
The publisher MUST NOT put two different MPUs in one Group, reuse a
Group number, or alter authored timestamps to satisfy this rule.  A
publisher that restarts or declares a discontinuity MUST retain the last
Group number for the existing track instance and resume with a greater
number; numeric gaps are allowed.  The publisher SHOULD signal the
skipped numbers with the PRIOR_GROUP_ID_GAP Object Property
([@!I-D.ietf-moq-transport] Section 10.8), as [@!I-D.ietf-moq-msf]
Section 6.1 recommends.  If it cannot resume with a greater number
while preserving the formula and authored timing, it MUST close that
track instance and
start a new track with a distinct (namespace, track name) pair before
emitting the reset MPU.  That new identity is the Group-number
scope for the restarted stream; it MUST NOT be presented as a
continuation of the old track.  Group-number state is transport state;
this document defines no new catalog field for it.

Because its Group numbers follow media time, an mmtp publisher cannot
start a Group early.  It MUST NOT set the DYNAMIC_GROUPS Track
Property ([@!I-D.ietf-moq-transport] Section 10.6) to 1.

For two tracks A and B, a receiver can verify that timestamps describe
the same presentation instant without floating-point conversion:

~~~
(ticksA - presentationAnchorTicksA) * timescaleB ==
    (ticksB - presentationAnchorTicksB) * timescaleA
~~~

The group-duration agreement rule in this section applies after the
same anchor conversion.  Consequently, equal rational values of
`groupDurationTicks / timescale` and correctly paired
`presentationAnchorTicks` values are what align 30-fps video with
audio; per-track `timescale` and `groupDurationTicks` values alone do
not establish synchronization.

All arithmetic is in integers: `relative_ticks` and `groupDurationTicks`
are integers, `floor(relative_ticks / groupDurationTicks)` is integer division,
and implementations MUST NOT compute the group number in floating
point or apply any tolerance.  An input held in another unit
(seconds, milliseconds, a different timescale) MUST be converted to
an exact integer tick count before the formula is applied; if that
conversion is not exact, the publisher's timescale or group-duration
choice is wrong (Section 4.4.2) -- implementations MUST NOT round to
compensate.

For ISOBMFF content, authored composition timestamps use the media
track's `mdhd` timescale.  If that differs from the catalog `timescale`,
the publisher MUST convert the adjusted composition timestamps by the
exact ratio `timescale / mdhd.timescale` before applying this formula.
It MUST reject a timestamp that is not an integer in the selected
catalog clock; it MUST NOT relabel media ticks as asset-clock ticks.

Worked example.  A switching set of two video renditions of the same
content: rendition A with `timescale: 90000`, rendition B with
`timescale: 44100`, both with `presentationAnchorTicks: 0` and
`groupDurationMs: 2000` in the catalog (Section 4.4.2).  The sample
that is 10.5 seconds into the shared presentation timeline has an
integer timestamp in both timescales:

~~~
A: groupDurationTicks = 2000 * 90000 / 1000 = 180000
B: groupDurationTicks = 2000 * 44100 / 1000 =  88200

Same media instant, t = 10.5 s on the shared timeline:
A: relative_ticks = 945000 -> floor(945000 / 180000) = 5
B: relative_ticks = 463050 -> floor(463050 /  88200) = 5
~~~

Both renditions place the instant in group 5.  No intermediate value
is shared between the two computations -- only the integer results
agree -- which is exactly the property group-boundary switching
requires.

Negative authored timestamps use the same rule and are not clamped.  For
one 90 kHz track with `groupDurationTicks: 180000`, choose the shared
presentation anchor `presentationAnchorTicks: -180000`, which is earlier
than the `ticks` of the first admitted MPU:

~~~
MPU 0 ticks = -90000: relative_ticks =  90000 -> group 0
MPU 1 ticks =  90000: relative_ticks = 270000 -> group 1
~~~

The negative authored PTS therefore maps to group 0 through the shared
earlier anchor.  A catalog with the same samples and
`presentationAnchorTicks: 0` is invalid for this profile; the publisher
rejects MPU 0 instead of mapping it to group 0.

With reordered samples, the first AU in decode order selects the
Group number.  This example lists the authored PTS values of the first
three AUs of two consecutive MPUs in decode order.  MPU 0 is a closed
GOP.  MPU 1 is an open GOP: its RAP presents at 180000, and its two
leading pictures present before it, inside Group 0's interval:

~~~ json
{
  "timescale": 90000,
  "presentationAnchorTicks": 0,
  "groupDurationTicks": 180000,
  "mpuSamplePtsInDecodeOrder": [
    [0, 6000, 3000],
    [180000, 174000, 177000]
  ],
  "ticks": [0, 180000],
  "groupNumbers": [0, 1]
}
~~~

`ticks` is the first entry of each MPU's list.  Selecting the minimum
presented PTS instead would give `ticks` 0 and 174000, both in Group 0,
which violates the strictly-greater rule above.

{#catalog-signaling-of-group-duration}
### Catalog Signaling of Group Duration

For a subscriber to apply the formula in Section 4.4.1, the catalog
MUST publish the group duration for every mmtp-packaged track.
The catalog publishes either the millisecond form or the exact tick
form defined here:

~~~
groupDurationMs (REQUIRED unless groupDurationTicks is present,
                positive unsigned integer, milliseconds)
~~~

The timescale is the MSF `timescale` field ([@!I-D.ietf-moq-msf]
Section 5.2.21), resolved per the track's `packaging` value
([@!I-D.ietf-moq-msf] Section 5.2.4; this document adds `mmtp`,
Section 13.1):

| `packaging` | Timescale source |
|-----------|------------------|
| `mmtp`    | The `timescale` field, REQUIRED for mmtp tracks (Section 13.1); absence is a catalog error, and the 90 000 `asset_timescale` default of [@!ISO.23008-1] Clause 10.3.9.3 does not apply. |
| `cmaf`    | The `timescale` field.  [@!I-D.ietf-moq-msf] Section 5.2.21 makes it optional, so this document makes it REQUIRED for any cmaf track to which this section applies (a member of a switching set governed by Section 4.4.1); leaving it unset on such a track is a catalog error. |
| `loc`     | The `timescale` field.  As for cmaf, this document makes it REQUIRED for any loc track to which this section applies; leaving it unset on such a track is a catalog error.  When the publisher also sends the TIMESCALE Property ([@!I-D.ietf-moq-loc] Section 2.3.1.2) on such a track, its value MUST equal the field. |
| (unrecognized `packaging`) | 1 000 000 (microseconds).  This row covers track entries whose `packaging` value is unrecognized; the convention is fixed by this document and does not derive from [@!I-D.ietf-moq-transport].  A track entry without `packaging` is malformed ([@!I-D.ietf-moq-msf] Section 5.2.4) and fails catalog validation (Section 6.1, step 1). |

When `groupDurationTicks` is absent, conversion is
`groupDurationTicks = groupDurationMs * timescale / 1000`.  The
catalog publisher MUST choose a `groupDurationMs` such that the
resulting tick count is a positive integer and the conversion is exact
(i.e. `(groupDurationMs * timescale) % 1000 == 0`).  If this cannot be
satisfied, or if the intended cadence is not an integer number of
milliseconds, the catalog MUST publish ticks directly via the exact
tick field:

~~~
groupDurationTicks (OPTIONAL, positive unsigned integer)
~~~

If both `groupDurationMs` and `groupDurationTicks` are present,
`groupDurationTicks` wins and `groupDurationMs` is informational; it is
not used in the conversion and need not have an exact millisecond
conversion.  Cases where the override is required include:

- An MPU group duration at a 30-per-second cadence
  (`1/30 s = 33.333... ms`): expressing this in integer ms is
  impossible.  If the track `timescale` is divisible by 30, publishers
  set `groupDurationTicks: timescale / 30` directly (e.g. `3000` at
  90 000 Hz, `1500` at 45 000 Hz).  A timescale not divisible by 30
  cannot represent this cadence as an integer tick count and MUST be
  changed or rejected for this profile; it MUST NOT be rounded.
- Audio sample-rate timescales not divisible by 1000 Hz, such as
  44 100 Hz: a 333 ms field would imply
  `333 x 44 100 / 1000 = 14 685.3` ticks.  A publisher whose authored
  cadence is the exact integral cadence of 14 685 ticks MUST publish
  `groupDurationTicks: 14685` (about 332.993 ms); it MUST NOT claim
  that this preserves an exact 333 ms duration.  A publisher that
  requires exactly 333 ms MUST choose a compatible timescale or reject
  that cadence.

For example, this catalog uses the exact 30-per-second cadence on a
44 100 Hz track.  It omits `groupDurationMs` because 33.333... ms is
not an integer millisecond value:

~~~ json
{
  "version": "draft-01",
  "tracks": [{
    "name": "video-30fps",
    "packaging": "mmtp",
    "isLive": true,
    "mmtpMode": "mfu",
    "timescale": 44100,
    "presentationAnchorTicks": 0,
    "groupDurationTicks": 1470,
    "codec": "avc1.64001f",
    "framerate": 30,
    "bitrate": 2000000
  }]
}
~~~

Switching-set agreement: every track in the same switching set MUST
publish the same effective group duration as a rational number of
seconds.  Raw `groupDurationTicks` values need not be equal when track
timescales differ.  For tracks A and B, subscribers validate exact
equality with integer arithmetic:

~~~
A.groupDurationTicks * B.timescale ==
    B.groupDurationTicks * A.timescale
~~~

One exception applies, to mmtp tracks only.  An mmtp track is
intra-only when its `framerate` field is present and its group
duration is one frame period at that rate:

~~~
groupDurationTicks * framerate == timescale
~~~

Because `framerate` need not be an integer (29.97), this comparison is
made within a relative tolerance of 10^-3 of `timescale`; a GOP track
misses it by a factor of at least two.  The tolerance only classifies
a track as intra-only.  It never enters Group number arithmetic: the
remainder test below, the quotient n, and every Group number use
exact integers, and Section 4.4.1 forbids any tolerance there.  Every
other track in the switching set, including every track whose
`packaging` is not `mmtp`, is a GOP track.  Exact equality above is
required between all GOP tracks.  An intra-only track I MAY instead publish a shorter
group duration that divides that of the GOP tracks a whole number of
times.  For every GOP track G in the switching set:

~~~
(G.groupDurationTicks * I.timescale) %
    (I.groupDurationTicks * G.timescale) == 0
~~~

Since an intra-only track has a group boundary at every frame, each GOP
group boundary is also one of its group boundaries, and switching
remains group-aligned.  With quotient
`n = (G.groupDurationTicks * I.timescale) / (I.groupDurationTicks *
G.timescale)` and a shared presentation anchor, Group g of G starts at
the same instant as Group g * n of I.  This mapping is the alternate
mechanism that [@!I-D.ietf-moq-msf] Section 4.2 requires for
time-aligned tracks whose Group IDs differ at the same instant.  A
subscriber can therefore switch
from G to I at any G group boundary.  It can switch from I to G only at
an I group whose number is a multiple of n.  Each intra-only track is
checked only against the GOP tracks, so switching between two
intra-only tracks of one switching set is group-aligned only at GOP
track group boundaries.  The exception does not
apply to a switching set with no GOP track: intra-only tracks with no
GOP peer still require exact equality.

For example, an mmtp 15 fps intra-only base track with `timescale: 90000` and
`groupDurationTicks: 6000` may share a switching set with a 15 fps GOP
track with `timescale: 1000000` and `groupDurationTicks: 1000000`,
because `1000000 * 90000 = 15 * (6000 * 1000000)`.  With
`groupDurationTicks: 1050000` on the GOP track the remainder is non-zero
and the catalog is invalid.  Two GOP tracks with group durations of 2 s
and 1 s are invalid even though one nests in the other.

Subscribers SHOULD validate this at catalog load and, on disagreement,
SHOULD reject the catalog and signal a catalog-validation error to the
application.  Subscribers that proceed despite disagreement are
non-conformant for switching across the affected tracks; ABR transitions
on such tracks will produce group-boundary discontinuities.

{#catalog-signaling-of-keyframe-interval}
### Catalog Signaling of Keyframe Interval

The group duration above describes the cadence of MMTP media groups
(one MPU per group, Section 4.3).  It does not describe whether an MPU
contains additional keyframes after its required group-start random
access point.  This document defines an OPTIONAL per-track field for
the cadence of all keyframes, which the repair policy of
[@!MOQ-FEC-MULTICAST] Section 6.1 uses to
classify FEC blocks:

~~~
keyframeIntervalMs (OPTIONAL, unsigned integer, milliseconds)
~~~

`keyframeIntervalMs` is the interval between consecutive video
keyframes, in integer milliseconds.  It is distinct from
`groupDurationMs`: `groupDurationMs` is the duration of
one MPU/group, whereas `keyframeIntervalMs` describes every keyframe,
including any additional keyframes inside an MPU.  When the only
keyframes are the required group-start RAPs and group duration is
constant, the two values are equal; additional RAPs can make the
keyframe interval shorter.  The field applies to video tracks only; a
publisher that cannot determine the cadence simply omits it.

Its absence is not a catalog error:
subscribers MUST NOT reject a catalog solely because it is missing,
and a receiver MUST NOT substitute a locally chosen or observed
cadence for it.  When present, `keyframeIntervalMs` MUST be a
positive integer; a zero value is a catalog error.

The repair policy of [@!MOQ-FEC-MULTICAST] Section
6.1 relies on a published keyframe interval
to exclude keyframes from part of a group, so when
the field is present it binds every keyframe of the track: the publisher MUST NOT emit a
keyframe other than at a group start or a whole number of intervals
after one.  A publisher whose encoder can place keyframes off that
cadence, for example at scene cuts, omits the field.

As with the group duration, the integer-millisecond form cannot
express a keyframe cadence whose tick count is non-integer on the
track's timescale.  A publisher MAY publish an exact override:

~~~
keyframeIntervalTicks (OPTIONAL, unsigned integer)
~~~

expressed in the same timescale as `groupDurationTicks` (Section 4.4.2,
selected by the track's `packaging`).  If both
`keyframeIntervalMs` and `keyframeIntervalTicks` are present,
`keyframeIntervalTicks` wins.  Unlike
`groupDurationTicks`, this document places no switching-set agreement
requirement on the keyframe interval: it is a per-track hint,
and tracks in a switching set MAY carry different keyframe cadences.

{#init-segment-signaling}
## Init Segment Signaling

Publishers signal MPU metadata inline as the complete FT=0 object in
Subgroup 0 of every group (Section 4.3), preceded in that subgroup only
by the OPTIONAL AL-FEC signaling object of Section 8.  Its data unit contains the
authored initialization boxes, including `ftyp`, `mmpu`, and `moov`.

In addition, publishers SHOULD carry decoder initialization data in
the catalog, using the mechanism of the base catalog that
[@?I-D.ietf-moq-cmsf] Section 3.1 also uses for CMAF headers.  The
data is an entry of the root `initDataList` array
([@!I-D.ietf-moq-msf] Section 5.1.7) whose `type` is "inline" and
whose `data` is the base64 encoding of an ISOBMFF initialization
segment (`ftyp` + `moov`) sufficient to initialize the decoder for
the track (including the codec configuration record, e.g. avcC or
hvcC).  The track's `initRef` field ([@!I-D.ietf-moq-msf]
Section 5.2.13) holds that entry's `id`.  This lets a subscriber
initialize its decoder at catalog load, before the first FT=0 MPU
metadata object arrives, removing one delivery round trip from the
join path (Section 6.1).  A receiver ignores an `initRef` that names
no entry, or names an entry whose `type` is not "inline", and joins
without catalog initialization data.

Catalog initialization data is a join optimization, not a replacement
for in-band metadata: the per-group FT=0 MPU metadata remains
authoritative, and a receiver MUST adopt in-band metadata when it
differs from the catalog's initialization data.  Catalog content is
untrusted input; a receiver MUST validate that the decoded `data` is
a well-formed `ftyp` + `moov` sequence before passing it to a
decoder, and MUST discard it otherwise.

Some implementations carry the same bytes in a per-track string
field, `initData`, which [@!I-D.ietf-moq-msf] does not define.  A
receiver MAY accept `initData` on an mmtp track and validates it in
the same way.  When a track carries both `initRef` and `initData`, the
receiver uses `initRef`.

{#object-identifier-assignment-and-reconstruction}
## Object Identifier Assignment and Reconstruction

The publisher numbers the objects of each group in source order, as
[@!I-D.ietf-moq-msf] Section 6.2 requires.  The first object of the
group has Object ID 0.  It is the AL-FEC signaling object when the
group carries one (Section 8), and the FT=0 object otherwise.  Each
later object, in whichever subgroup, has the Object ID of the object
before it plus one.  An Object ID therefore identifies one object of
its group, as [@!I-D.ietf-moq-transport] Section 2.1 requires, and
the Subgroup ID still identifies the data unit (Section 4.3).  The
packetizer emits each data unit's packets contiguously
(Section 5.2.2), and Subgroup IDs follow source order
(Section 5.3.2), so ascending Object ID order within a group is also
ascending Subgroup ID order.  A FETCH or fill fetch stream, which
sends a group's objects in Object ID order
([@!I-D.ietf-moq-transport] Section 3.2.1), therefore delivers them
in the order that Section 4.3 requires.

MoQ Transport carries Object IDs as deltas on the wire
([@!I-D.ietf-moq-transport] Sections 11.3.1 and 11.4.1.1), and the
objects of every subgroup other than Subgroup 0 have Object IDs
greater than zero.  A receiver MUST reconstruct each object's
absolute Object ID from that encoding.  It MUST NOT assume that a
subgroup's first Object ID is zero, that successive objects differ by
a fixed step, or that an absolute Object ID is carried explicitly.

Object IDs identify preserved source objects
within a group; they do not replace the MMTP packet sequence, FI
countdown, or active-data-unit association required by Sections 5.2
and 5.3.

{#media-fragment-unit-mfu-mode}
# Media Fragment Unit (MFU) Mode

This timed-media profile transports each authored MPU data unit without
rewriting it:

~~~
MFU Mode (one subgroup per MPU data unit):
  Group N:
   [SG 0 / Obj 0: [MMTP type=0x02 id=0][SH][AL-FEC msg]] (Section 8)
    SG 0 / Obj s:   [MMTP][PH FT=0 FI=0][ftyp+mmpu+moov]
    SG 1 / Obj s+1: [MMTP][PH FT=1 FI=0][moof+mdat prefix]
    SG 2 / Obj s+2: [MMTP][PH FT=2 FI=0][DU][sample 1]
    SG 3 / Obj s+3: [MMTP][PH FT=2 FI=0][DU][sample 2]
  ...

Fragmented FT=2 sample (Section 5.2):
  Group N, SG 2:
    Obj s+2: [MMTP][PH FT=2 FI=1][DU][sample part 1]
    Obj s+3: [MMTP][PH FT=2 FI=2][sample part 2]
    Obj s+4: [MMTP][PH FT=2 FI=3][sample part 3]

Subsample-partitioned FT=2 sample (Section 5.2.1): one sample,
two producer-authored subsample data units:
  Group N:
    SG 4 / Obj a..b:   [MMTP][PH FT=2 FI=1][DU offset=0]  ... FI=3
    SG 5 / Obj b+1..c: [MMTP][PH FT=2 FI=1][DU offset=L0] ... FI=3

[MMTP] = MMTP packet header (Section 3.1): 12 bytes, since C = 0,
         plus a header extension when X = 1.
[PH]   = MPU-mode payload header, which carries the Fragmentation
         Indicator (FI); the FI is not in the MMTP packet header.
[SH]   = signaling message payload header (Section 3.1).
[...]  = OPTIONAL signaling object.  When present it is Object 0,
         the first object of SG 0, and FT=0 is the object after it.
s      = 1 when the signaling object is present, 0 when it is
         absent.  Object IDs count the group's objects in source
         order across subgroups (Section 4.6).
~~~

For conformance, an `mmtp` track in this document carries timed media
only.  ISO/IEC 23008-1 Clause 9.3.2.3 defines the Timed Flag as
indicating whether the MPU is timed or non-timed, independently of the
FT value.  Every MPU-mode packet with FT=0, FT=1, or FT=2 in this
profile MUST carry `T = 1`; a packet with `T = 0` MUST be rejected.
Checking only FT=2 would leave metadata packets unchecked.  The ISO
non-timed DU identity and four-byte header remain outside this profile;
no `Item_ID`-based mapping is defined here.

FT=0 initializes the track, FT=1 supplies the authoritative movie
fragment structure and sample table, and FT=2 supplies the exact bytes
of each sample.  That order is a decoder contract, not a hint.

{#authored-movie-fragment-timing}
## Authored Movie-Fragment Timing

For timed media, receivers MUST derive sample timing and layout only
from the authored ISOBMFF metadata carried by FT=0 and FT=1:

1. FT=0 supplies the one media track's `mdhd` timescale and `trex`
   defaults.  It MUST contain a usable `mvex`/`trex` for that track.
2. FT=1 begins with a byte-for-byte copy of the authored `moof` and
   carries a byte-for-byte copy of the original `mdat` prefix through
   the byte before the first media sample.  This includes the original
   `mdat` header and any auxiliary sample information.  The
   `mfhd.sequence_number` identifies the movie fragment referenced by
   subsequent timed-MFU DU headers.
3. For the `traf` whose `tfhd.track_ID` matches the independent media
   track's `tkhd.track_ID`, `tfdt` supplies the first decode time.
   Each sample duration and size is resolved using the ISOBMFF
   precedence rules across `trun`, `tfhd`, and `trex`; composition time
   is decode time plus the authored `trun` composition-time offset.
   Signed offsets MUST remain signed.  Sample byte positions are
   resolved from the authored base-data-offset and `trun.data_offset`
   rules, not from a fixed `mdat`-header guess.
4. Each FT=2 timed DU identifies one sample -- or one producer-authored
   subsample of it -- by `(MPU_sequence_number,
   movie_fragment_sequence_number, sample_number, offset)`.  A
   whole-sample data unit carries `offset` zero; a subsample data unit
   (Section 5.2.1) carries the authored byte position of its first
   media byte within the sample.  Section 5.3.3 defines sample
   completion.

A receiver MUST reject a missing or ambiguous media track, timescale,
movie-fragment sequence, `tfdt`, or sample identity.  It MUST also
reject any sample duration, sample size, byte position, or composition
offset that remains unresolved or invalid after applying all authored
`trun`, `tfhd`, `trex`, and implicit ISOBMFF rules.  An absent
per-sample `trun` composition-time-offset resolves to zero, and an
absent `trun.data_offset` is not by itself an error when the ISOBMFF
base-data-offset and run-continuation rules resolve the byte position.
The receiver MUST reject overlapping sample byte ranges, undeclared
bytes, duplicate samples, duplicate or overlapping subsample data
units (Section 5.2.1), and FT=2 media for which the governing FT=0
or FT=1 has not been accepted.  It MUST NOT synthesize timing from the
MMTP Timestamp, packet or MPU counters, MoQ Object IDs, arrival time,
catalog cadence, codec frame-rate guesses, or previously observed
samples.

The MMTP Timestamp is a send time, not media time (Section 3.1).
Any absolute MMT presentation anchor and edit-list offset are applied
as specified by PI/MPU presentation signalling and ISOBMFF; a receiver
without the required anchor MUST reject that timeline rather than
silently omit the authored adjustment.

{#fragmentation-and-strict-active-du-reassembly}
## Fragmentation and Strict Active-DU Reassembly

A single MFU can exceed the path MTU, but the ISO MPU-mode payload
header does not permit an unbounded number of fragments.  The 8-bit
`fragment_counter` is the number of MMTP payloads containing fragments
of the same data unit that succeed the current payload; it is not a
modulo sequence number.  A complete FI=0 data unit MUST carry zero.
For a fragmented data unit carried in N payloads, where 2 <= N <= 256,
the FI=1 payload MUST carry N - 1, every succeeding payload MUST
decrement the value by one, and the FI=3 payload MUST carry zero.  The
counter MUST NOT wrap or repeat within a data unit.

The mfu mapping defined here carries exactly one data unit per MMTP
payload, so `aggregation_flag` MUST be zero.  The upstream MMTP
packetizer produces conformant data units, and an input MMTP flow used
by this mapping MUST already satisfy the 256-payload bound for every
data unit.  In this profile an FT=2 timed data unit carries one whole
sample, or exactly one producer-authored subsample of it
(Section 5.2.1).  A sample whose media exceeds one data unit's
capacity MUST be partitioned into subsample data units by the origin
packetizer per Section 5.2.1, before this mapping applies -- never by
a relay and never by this mapping, which does not repacketize or
subdivide an input data unit.  Such a sample MUST NOT be carried by
wrapping or extending the counter, silently truncated, or split into a
second MPU, and an access unit MUST NOT be split across multiple MPUs
([@!ISO.23008-1] Section 6.4).  A publisher MUST reject a purported
data unit that exceeds the bound, has an invalid countdown, or uses
aggregation.  It MUST NOT wrap or extend the counter, divide one data
unit's overflow between subgroups, or synthesize MoQ Object IDs to
make a non-conformant MMTP data unit appear valid.

Each MMTP packet maps to exactly one MoQ object, and the publisher
MUST NOT reassemble MFU fragments:

1. The publisher MUST publish each MMTP packet of a data unit as a
   separate object within that data unit's subgroup (Section 4.3), preserving the
   MMTP packet header and the MPU-mode payload header.  Those headers
   carry the Fragmentation Indicator
   and MPU sequence number.  Object IDs identify the preserved source
   packets within the group (Section 4.6) but are not MFU identities
   or media timestamps.
2. The publisher MUST NOT reassemble or reorder fragments based on
   the Fragmentation Indicator.  It routes each packet to (track,
   group, subgroup) by packet_id, MPU boundary, data-unit type, and the
   strict active-DU state of Section 5.3: a change of MPU sequence
   number starts the next group (Section 4.3), and each distinct data
   unit within the group maps to its own subgroup as defined in
   Section 5.3.
3. The receiver MUST reassemble each data unit from the objects of its
   subgroup before media processing.  After restoring serial packet
   order (Section 5.3.3), it applies the FI/counter state machine of
   Section 5.3:
   - A single object with FI=0 is a complete, unfragmented data unit;
     for FT=2 that data unit is one MFU.
   - FT=2 objects with FI=1 (first), FI=2 (zero or more middle), and FI=3
     (last) reassemble, in that restored MMTP order, into one MFU by
     concatenating each fragment's media bytes, delimited as defined
     below.
   - The receiver MUST validate the `fragment_counter` countdown with
     the state machine of Section 5.3.2.  Any missing, repeated,
     wrapped, or non-decrementing count invalidates the entire MFU.
   - The reassembled MFU's RAP flag is taken from its FI=1 (or FI=0)
     object.

   The bytes concatenated are each fragment's media (data unit)
   bytes only -- not everything after the MMTP packet header.  Every
   fragment begins with a 12-or-more-byte MMTP packet header.  The
   receiver MUST parse the C and X flags, packet-counter presence, and
   header-extension length to locate the following 8-byte MPU-mode
   payload header; it MUST NOT assume a fixed offset of 12 bytes.  The
   MPU-mode payload header contains, by [@!ISO.23008-1]
   Clause 9.3.2.3 name with this document's alias in parentheses,
   length (`payload_length`, 16), FT (`fragment_type`, 4), T
   (`timed_flag`, 1), f_i (`fragmentation_indicator`, 2),
   aggregation_flag (1), fragment_counter (8), and
   MPU_sequence_number (32); both headers are stripped from every
   fragment.

   The 16-bit `payload_length` field MUST be encoded and interpreted
   as the number of bytes following that field within the MPU payload,
   as defined by [@!ISO.23008-1].  It therefore includes the remaining
   six bytes of the 8-byte MPU-mode payload header.  For FT=2 packets,
   the declared lengths are:

   ~~~
   FI=0 or FI=1: payload_length = 6 + DU_header_octets + media_octets
   FI=2 or FI=3: payload_length = 6 + media_octets
   ~~~

   `DU_header_octets` is 14 for timed media and 4 for non-timed media,
   and the right-hand side MUST NOT exceed the 16-bit maximum of 65535.
   A trailing Source FEC Payload ID is outside the declared MPU payload
   and MUST NOT be counted.  A publisher MUST NOT encode a media-only or
   DU-plus-media length convention.  A receiver MUST require the
   declared MPU payload to end exactly at the protected MPU boundary
   before the Source FEC Payload ID, when present.  It MUST reject a
   declaration that is too short, cannot contain the required header
   bytes, extends beyond the available MPU payload bytes, leaves
   undeclared bytes before the outer trailer, or consumes that trailer.

   The DU header ([@!ISO.23008-1] Figures 12 and 13: 14 bytes for
   timed media -- movie_fragment_sequence_number (32),
   sample_number (32), offset (32), priority (8),
   dep_counter (8) -- or 4 bytes for non-timed media) follows the
   payload header on an FI=0 object and on the FI=1 first fragment;
   it is likewise stripped rather than concatenated into the media
   stream.  When the packet's FEC Type is 1, the trailing 4-byte
   Source FEC Payload ID ((#source-fec-payload-id)) is excluded as
   well.
4. FT=0 and FT=1 MUST each be unaggregated, complete FI=0 data units
   with `fragment_counter` zero.  Their payload length is six plus the
   metadata octets; they have no DU header.  Fragmented or empty
   metadata is rejected by this profile.
5. The receiver MUST bound both in-flight data-unit memory and pending
   FT=1 sample records.  At either bound it MUST reclaim a slot by
   evicting the least recently admitted incomplete record (an open
   data unit or a parked continuation run) and admit the new one; it
   rejects only when no such record exists.  A record that has
   already completed is never a candidate.  An incomplete data
   unit is discarded on declared discontinuity or unrecoverable loss
   and is never emitted.

For very large frames where FEC cannot recover the loss, receivers
SHOULD support resolution-tier fallback (subscribe to a lower-resolution
track of the switching set and upscale) rather than stalling.

{#subsample-data-units}
### Subsample Data Units

At a given packet size, one data unit carries at most 256 MMTP
payloads of media.  A single intra-coded 4K or 8K sample routinely
exceeds that capacity.  This section defines the only conformant way
to carry such a sample: the origin packetizer partitions it into
subsample data units, using the `offset` field that [@!ISO.23008-1]
Section 9.3.2.3 already defines in the timed-MFU DU header.  The
partition is producer-authored and wire-stated; nothing about it is
inferred.

A subsample data unit is an ordinary FT=2 timed data unit: it has its
own DU header, its own FI chain, and its own `fragment_counter`
countdown bounded by 256 payloads (Section 5.2).  Its identity is
`(packet_id, MPU_sequence_number, movie_fragment_sequence_number,
sample_number, offset)`, where `offset` is the authored byte position
of the data unit's first media byte within the sample.

Origin packetizer requirements:

1. A packetizer MUST emit a sample as a single whole-sample data unit
   (`offset` zero) whenever the sample fits within one data unit's
   capacity.  Subsample partitioning of a sample that fits is not
   conformant.
2. When partitioning, the first subsample data unit MUST carry
   `offset` zero and each subsequent one MUST carry an `offset` equal
   to the sum of the media lengths of all preceding subsample data
   units of that sample: offsets are strictly increasing, with no gap
   and no overlap.
3. Each subsample data unit of one sample MUST be published as its
   own subgroup per Section 5.3.2, contiguously per Section 5.2.2.
4. `priority` and `dep_counter` describe the sample and SHOULD be
   identical across its subsample data units.

Relays and this mapping MUST NOT create, merge, or re-partition
subsample data units.

Receiver sample assembly: a subsample-partitioned sample completes
only when every one of its subsample data units has completed under
the state machine of Section 5.3.2 and, ordered by `offset`, the data
units begin at zero, are byte-adjacent (each `offset` equals the
preceding `offset` plus the preceding data unit's media length), and
their total media length equals the sample's authored size from the
FT=1 record.  A gap, overlap, duplicate `offset`, or length mismatch
invalidates the sample; the receiver MUST NOT emit a partial sample or
synthesize missing bytes.  Completion is a protocol event -- every
constituent subgroup complete -- and on reliable transport a receiver
MUST NOT substitute timers, cadence, buffer occupancy, or successor
arrival for it.  On lossy paths each subsample data unit completes,
possibly after FEC recovery ([@!MOQ-FEC-CORE] Section
9), or is discarded
as incomplete (Section 5.2, item 5), like any other data unit; no
additional sample-level timer is defined or permitted.

The sample's RAP flag is the RAP flag of the FI=0 or FI=1 object of
its offset-0 data unit.  FEC is unaffected by the partition: source
symbols are MMTP packets ((#iso-ssbg1-v1)), and the packet stream's
block and interleave structure does not depend on data-unit boundaries.

{#source-contiguity}
### Source Contiguity

[@!ISO.23008-1] does not prohibit a packetizer from emitting an
unrelated payload of the same `packet_id` between two fragments of one
data unit.  This profile does prohibit it.

An origin packetizer MUST emit every multi-packet unit on consecutive
`packet_sequence_number` values of its `packet_id`, in authored order,
with no other payload of that `packet_id` between its packets: the
fragments of a data unit in FI order, and the subsample data units of
one sample (Section 5.2.1) in ascending `offset` order.  The sequence
numbers of the FI=1 fragment, of each FI=2 fragment, and of the FI=3
fragment MUST be successive values under
modulo-2^32 arithmetic.  A data unit of a different `packet_id` MAY be
emitted at any point, and a further data unit of the same `packet_id`
MAY be emitted once that data unit's FI=3 fragment has been emitted,
subject to the sample-level contiguity above.

The requirement constrains the packetizer's emission order only.  Loss
or reordering on the path does not violate it: the receiver restores
serial packet order before reassembly (Section 5.3.3).  Repair
carried on its own flow bears a different `packet_id` and therefore
cannot interleave.

A violating data unit never completes at the receiver, which
associates continuations only through active data-unit state
(Section 5.3) and evicts the stranded records without a protocol
error (Section 5.2, item 5).  A receiver MUST NOT relax association to
tolerate such a producer: a continuation admitted into the wrong data
unit corrupts media that would otherwise have been discarded.

{#active-data-unit-association-and-subgroup-derivation}
## Active Data-Unit Association and Subgroup Derivation

Object IDs are transport coordinates, not an MMTP continuation key.
A fragment recovered below the MoQ object layer has no Object ID, and
Object IDs from two delivery paths are not comparable.  The MMTP DU
header is also not a per-fragment coordinate: this profile carries it
only in the FI=0 or FI=1 payload ([@!ISO.23008-1] Clause 9.3.2 does
not specify whether FI=2 and FI=3 fragments repeat it).  FI=2 and FI=3
continuations carry media bytes but no movie-fragment sequence, sample
number, or sample offset.

Consequently a receiver MUST associate continuations through the
ordered, bounded active-data-unit state defined here.  It MUST NOT use
an MMTP Timestamp, MoQ Object ID, signaling identifier, packet arrival
time or order, inferred byte offset, recently completed identity, or a
(stream, MPU sequence number) pair or fragment counter alone as a
fallback association.

{#first-fragment-identity}
### First-Fragment Identity

For an FT=2 first or complete fragment, [@!ISO.23008-1] defines a
transport-independent data-unit identity in the DU header:

| Object class          | Data-unit identity                    | [@!ISO.23008-1] |
|-----------------------|---------------------------------------|-----------------|
| Timed-media MFU       | packet_id, MPU_sequence_number, movie_fragment_sequence_number, sample_number, offset | Section 9.3.2.3 |
| Non-timed media MFU   | packet_id, MPU_sequence_number, Item_ID | Section 9.3.2.3 |

For this timed-media profile, `offset` MUST be zero for a whole-sample
data unit and MUST equal the authored subsample byte position for a
subsample data unit (Section 5.2.1);
`movie_fragment_sequence_number` and `sample_number` MUST be non-zero,
and `MPU_sequence_number` MAY be zero (indeed, ISO/IEC 23008-1 requires
zero for the first MPU in an Asset).  The `packet_id` MUST be
non-zero: packet_id 0 is the MMTP signaling flow (Section 3.1) and
carries no media data unit, so a receiver MUST reject an MPU-mode
packet (packet type 0x00) on packet_id 0 rather than admit it to
active state.  A non-zero `packet_id` is validated in the scope of its
MMTP session; on multicast delivery it is validated against the
`packetId` values the endpoint advertises ([@!MOQ-MULTICAST]
Section 5).  A continuation inherits the accepted first-fragment
identity from active state; it does not reconstruct or guess another
copy of the DU header.

{#subgroup-derivation}
### Subgroup Derivation

Section 4.3 assigns Subgroup 0 to FT=0.  The publisher assigns every
following FT=1 or FT=2 data unit the next unused Subgroup ID in source
order.  All packets from one FI=1 through FI=3 chain share that ID.
An FI=2 or FI=3 packet therefore remains in the subgroup opened by the
immediately preceding FI=1 packet on the same `packet_id`; a new data
unit MUST NOT interleave before the chain closes (Section 5.2.2).

The publisher and receiver each maintain at most one active fragmented
data unit per `(packet_id, MPU_sequence_number)` while processing
subgroups in order:

1. FI=0 requires `fragment_counter == 0` and no active data unit.  For
   FT=2 it requires a valid DU header and represents the complete
   sample.  FT=0 and FT=1 are permitted only in this form.
2. FI=1 requires no active data unit, a counter `c` in 1..255, and, for
   FT=2, a valid DU header.  It creates active state containing the
   data-unit type, timed flag, full first-fragment identity, destination
   subgroup, and `next_expected_counter = c - 1`.
3. FI=2 requires exactly one matching active state and a non-zero
   counter equal to the next expected counter.  It appends only the
   declared media bytes and decrements the expected counter.
4. FI=3 requires exactly one matching active state,
   `next_expected_counter == 0`, and a wire counter of zero.  It appends
   the declared media bytes, closes the state, and emits the complete
   data unit only after all size and authored-timing checks succeed.

An FI=0 or FI=1 while state is active is an overlap.  An FI=2 or FI=3
without it is an orphan.  A changed packet ID, MPU sequence, FT, timed
flag, subgroup, skipped/repeated counter, FI=2 at zero, or FI=3 before
the expected counter reaches zero is a mismatch or gap.  The receiver
MUST reject all of these and MUST NOT advance, replace, or consume valid state or pending sample
timing on rejection.  A new MPU arriving while the prior MPU has an
incomplete data unit declares loss and discontinuity; the incomplete
unit is discarded and never emitted.

{#receiver-admission-and-completion}
### Receiver Admission and Completion

A receiver admits a fragment only after its declared MPU payload
boundary, outer FEC trailer, stream scope, subgroup order, and active-DU
transition all validate.  Duplicate packets may be dropped by exact
MMTP packet identity before admission, but a duplicate MUST NOT create
or advance active state.  Multi-path combining and FEC recovery MUST
restore the same per-`packet_id` serial packet order before this state
machine, using modulo-2^32 serial-number arithmetic across
`packet_sequence_number` wrap within a bounded replay window.  The
MMTP-session and MoQ-track scope are part of that ordering state;
neither mechanism may fabricate a missing transition.

Completion is transactional.  For a whole-sample data unit the
receiver first validates the full FI chain and the matching unconsumed
FT=1 sample record; the reassembled FT=2 media length MUST equal that
sample's authored size.  For a subsample-partitioned sample it
additionally requires every constituent subsample data unit to have
completed, with the byte-adjacency and total-length checks of
Section 5.2.1.  Only then may it emit the sample and consume that
record.  Every `(sample, offset)` data unit is admitted at most once,
and every described sample is emitted at most once.  A failed check leaves every pre-existing valid state and timing record
unchanged, except that an explicitly declared discontinuity discards
the incomplete prior unit.

{#random-access-and-priority}
### Random Access and Priority

An MPU begins at a Stream Access Point: the first access unit of an
MPU is a random access point (RAP) ([@!ISO.23008-1] Section 6.4;
Section 4.3).  Accordingly a receiver:

- SHOULD gate the start of media decoding on the availability of a
  complete RAP MFU, including a RAP MFU completed by FEC recovery;
  and
- SHOULD prioritize FEC recovery and retention of fragments whose
  DU header carries a higher priority or dep_counter value
  (Section 5.2; the subsample_priority and dependency_counter of
  [@!ISO.23008-1] Section 9.3.2.3), since these are decode-order
  roots upon which other access units depend.

On a multicast or Automatic Multicast Tunneling (AMT) leg,
[@!MOQ-FEC-MULTICAST] Section 6 specifies
the receiver repair policy this implies.

{#subscriber-join-and-relay-behavior}
# Subscriber Join and Relay Behavior

This section defines the join procedure for subscribers.  A
subscriber reaches its first decodable frame without waiting for the
next group boundary by joining at the start of the current group
with the fill mechanism of [@!I-D.ietf-moq-transport] Section 3.5.
The join needs no relay behavior beyond [@!I-D.ietf-moq-transport],
and relays never parse MMTP (Section 6.2).

{#subscriber-join-procedure}
## Subscriber Join Procedure

A subscriber joins a live mmtp-packaged track as follows:

1. **Catalog.** Subscribe to the catalog track (the track named
   `catalog`, Section 13) as [@!I-D.ietf-moq-msf] Section 5 requires,
   joining at the start of its current group
   ([@!I-D.ietf-moq-transport] Section 3.5), and validate the
   catalog.  Validation includes the per-track REQUIRED fields of
   Section 13.1.  A subscriber MUST NOT issue SUBSCRIBE for a track
   whose catalog entry fails validation.  It also applies the
   switching-set agreement check of Section 4.4.2 and handles a
   disagreement as that section specifies.

2. **Decoder initialization.** If the catalog provides
   initialization data for the track (Section 4.5) and that data
   validates, initialize the decoder from it immediately.  In all
   cases the subscriber MUST accept the
   authoritative FT=0 object in Subgroup 0 before admitting this
   group's FT=1 or FT=2 data units.  An AL-FEC signaling object that
   precedes FT=0 in Subgroup 0 (Section 8) is not decoder
   initialization and does not satisfy this step.

3. **Subscribe at a group boundary.** Join at the start of the
   current group, as [@!I-D.ietf-moq-transport] Section 3.5
   describes.  Send SUBSCRIBE with a LOCATION_FILTER of type 0x05
   (Next Object) and a FILL_PARAMETERS parameter whose
   LOCATION_FILTER has type 0x01 (Relative Start) and StartGroup = 1
   ([@!I-D.ietf-moq-transport] Sections 3.4, 9.20.9, and 9.20.15).
   The publisher sends the current group, from its start up to the
   Largest Object, on a fill fetch stream, and every later object on
   the subscription, so each object arrives once.  The group start
   carries FT=0 initialization (Subgroup 0), the FT=1 metadata
   governing the first samples, and the RAP-bearing first FT=2
   subgroup (Section 4.3); a subscription that starts mid-group
   without a fill yields objects that cannot be decoded until the
   next group.  A data unit that was still open at the join arrives
   partly on the fill fetch stream and partly on its subgroup stream,
   and the receiver combines the two before reassembly (Section 5.2).
   If the fill fails or leaves a gap, the subscriber waits for the
   next group, which the subscription delivers from its start.  A
   subscriber that does not want the current group sends SUBSCRIBE
   with a LOCATION_FILTER of type 0x01 and StartGroup = 0 instead.  A
   NEW_GROUP_REQUEST ([@!I-D.ietf-moq-transport] Section 9.20.19)
   cannot shorten that wait (Section 4.4.1).

4. **Repair track.** If the subscriber wants FEC protection and the
   catalog signals FEC for the track, it SHOULD subscribe to the
   repair track (Section 8.2) at the same time as the source track,
   so that the first FEC block spanning the join point is
   repairable.  Repair-track subscription is selective and optional
   ([@!MOQ-FEC-CORE] Section 7.2).

5. **Presentation gate.** A subscriber MUST NOT submit media to the
   decoder until it has (a) accepted the authoritative FT=0 and FT=1
   data units and (b) a completely reassembled FT=2 sample whose RAP
   flag is set (Section 5.2).  Objects received before that point are buffered
   or discarded according to the receiver's reassembly bounds.

6. **Loss and discontinuity.** If a RAP MFU is discarded under
   unrepairable loss (Section 5.2), the subscriber MUST
   treat the track as discontinuous and MUST NOT resume presentation
   before the next completely reassembled RAP MFU (normally the
   start of the next group).  The same holds when the group's FT=0
   data unit, or the FT=1 data unit governing its RAP, is lost, since
   the RAP then cannot be admitted (Section 4.3).  On a multicast or
   AMT leg, loss that spares those three data units does not make the
   track discontinuous; [@!MOQ-FEC-MULTICAST] Section
   6 specifies its handling.

{#relay-retention-for-late-joiners}
## Relay Retention for Late Joiners

This section is informative.  A relay serves the fill fetch stream of
Section 6.1 from its cache, and fetches from upstream the objects it
does not hold ([@!I-D.ietf-moq-transport] Sections 3.2.3 and 3.4).  A
relay that caches the current group of each track it serves can
therefore start a late joiner without an upstream round trip.  The
join needs no mmtp-specific relay behavior.  A fill fetch stream
sends a group's objects in Object ID order, which is source order on
an mmtp track (Section 4.6), so it delivers Subgroup 0 and each
metadata subgroup before the FT=2 subgroups that depend on them, and
the relay does not parse MMTP.

Retention of groups older than the current group (for example to
serve FETCH-based catch-up) is permitted but out of scope for this
document.

{#fec-integration}
# FEC Integration

MMT's AL-FEC framework supports multiple FEC schemes, with the MMT FEC
codes specified in [@!ISO.23008-10] and parameters signaled via MMTP
signaling messages (Section 8.3); neither the framework nor ATSC 3.0,
which uses it for MMTP sessions ([@?ATSC-A331] Section 8.1.2.5),
requires a particular code, so the codes are specified by
[@!MOQ-FEC-BLOCK]: "reed-solomon", the Reed-Solomon code of
[@!ISO.23008-10] Clause 6 (its Section 5), is the
mandatory-to-implement scheme, and RaptorQ [@?RFC6330] (its Section
6) is OPTIONAL ([@!MOQ-FEC-BLOCK] Section
10).  FEC repair uses the model defined in
[@!MOQ-FEC-CORE] (its Sections 3.1 and
7), under the block profile that (#iso-ssbg1-v1)
defines for mmtp tracks:

~~~
Source Track: video
  +-- Objects: MMTP packets with FEC Type=0 or 1 (source)

Repair Track: video/repair
  +-- Objects: MMTP packets with FEC Type=2 (repair)
~~~

This section defines that profile, "iso-ssbg1-v1": its source symbols,
the Source FEC Payload ID trailer, the MMTP form of the repair packet,
the keyframe overlay and the interleave window.  It states where the
profile deviates from [@!MOQ-FEC-CORE], whose remaining rules apply
unchanged ([@!MOQ-FEC-CORE] Section
5.2).

{#iso-ssbg1-v1}
## The iso-ssbg1-v1 Block Profile

"iso-ssbg1-v1" is the block profile ([@!MOQ-FEC-CORE] Section
5.2) of this document:
the ISO/IEC 23008-1 Annex C profile, all of whose rules a receiver
applies together.  It admits the `mmtp` packaging
((#iana-considerations)).  A source symbol is the ssbg_mode1 framing of
one FEC source packet (below).  A block holds SSB_length source symbols,
with `sourceSymbols` as the upper bound on SSB_length ([@!MOQ-FEC-CORE]
Section 5.4), carried in band as
`maximum_k_for_repair_flow` (Section 8.3).  SS_IDs advance by one per
FEC source packet, blocks are consecutive, and a source symbol is placed
in its block by range membership ([@!MOQ-FEC-CORE] Section
5.5).  SS_ID arithmetic is modulo 2^32,
and a block's repair objects are grouped under its 62-bit extended
SS_Start ([@!MOQ-FEC-CORE] Section
7.6).  An in-band AL-FEC message
that describes such a track carries the coding byte 0x14 (Section 8.3).

The rules of [@!MOQ-FEC-CORE] apply to a track under this profile with
the following deviations, which [@!MOQ-FEC-CORE] Section
5.2 asks a companion
profile to state:

- The unit of protection is the MMTP packet, not the MoQ object: a
  source symbol is formed from one FEC source packet as this section
  specifies, and the Protected Object Unit of [@!MOQ-FEC-CORE] Section
  5.2 is not used.  A
  source object of an mmtp track carries one source symbol, the FEC
  source packet that is its payload, so SS_IDs advance by one per source
  object.

- A source packet carries its SS_ID in a 4-byte trailer, the Source FEC
  Payload ID ((#source-fec-payload-id)), which is the canonical carrier.
  The FEC Source Info Object Property of the object that carries the
  packet restates it in the 4-byte form, which names instance 0
  ([@!MOQ-FEC-CORE] Section 5.6); the
  Property is object metadata, not part of the protected packet, and is
  not recovered with it.  When an object carries a source symbol but no
  FEC Source Info Property, a receiver that parses the packet MAY take
  the SS_ID from the trailer and feed the symbol to the base decoder
  ((#source-fec-payload-id)), a deviation from [@!MOQ-FEC-CORE] Section
  5.6, under which such an object is not
  a source object; a receiver that does not parse the packet has no
  SS_ID for it and feeds it to no decoder.

- A repair object is one complete MMTP repair packet of 12 + 13 + T
  bytes ((#repair-packet)), not the 13 + T byte payload of
  [@!MOQ-FEC-CORE] Section 7.5.

- The keyframe overlay ((#keyframe-overlay)) is this profile's form of
  an overlapping instance ([@!MOQ-FEC-CORE] Section
  8.4), with two differences from that
  section and from [@!MOQ-FEC-CORE] Section 5.1: a
  RAP packet's overlay SS_ID travels in an MMTP header extension, not in
  a second entry of the FEC Source Info Property, and the Property keeps
  the 4-byte form, so a receiver learns a packet's overlay membership
  and overlay SS_ID from that extension, which lies inside the protected
  packet ((#overlay-membership)), rather than from the Property alone;
  and because a recovered packet carries its overlay SS_ID but not its
  base SS_ID, a base recovery places the packet in the overlay instance,
  whereas an overlay recovery counts toward the base instance only where
  the receiver has determined the packet's base SS_ID independently
  ((#iso-ssbg1-v1)).

- `interleaveDepthMs` admits the value zero, with the ISO packet-count
  meaning of (#interleaving), under the permission of [@!MOQ-FEC-CORE]
  Section 10.1 for a block profile to give zero
  a meaning of its own.

- The symbol carriage of [@!MOQ-FEC-CORE] Section
  6.2, and with it the symbol track and the FEC
  Unit Start Property, does not apply to an mmtp track: its source
  symbols reach a receiver inside the track's own objects or as
  multicast datagrams ([@!MOQ-MULTICAST] Section
  5), each carrying one whole FEC
  source packet.

Per [@!ISO.23008-1] Section C.3.3 (signalled per C.6.3, Table C.5), the
FEC block structure is described by the source symbol block generation
(SSBG) mode (ssbg_mode).  This profile uses ssbg_mode1, with the
one-stage FEC coding structure and FEC payload ID mode 0
([@!ISO.23008-1] Clause C.1).

**ssbg_mode1**: One MMTP source packet = one source symbol, which
records the packet's length.  Each MoQ object or multicast UDP datagram
carries exactly one FEC symbol.  Repair symbols are exactly T bytes on
the wire; a source packet MAY be shorter than T on the wire -- the
length field and the zero padding that complete its T-byte source symbol
are applied by the encoder and decoder as part of the source symbol
construction below and are not transmitted.  This is the natural model
for MMTP because packets are sized to fit in UDP datagrams and no
fragmentation or reassembly is needed at the FEC layer.  Every source
symbol is exactly T bytes, so a block of SSB_length source symbols is
exactly SSB_length x T bytes -- the property the derived Transfer Length
of [@!MOQ-FEC-BLOCK] Section 6.1 relies on.  This is
ssbg_mode1 of [@!ISO.23008-1], not ssbg_mode0, which carries no length
and requires every packet of the flow to be exactly one symbol long.

**Source symbol construction**: The protected packet of an FEC source
packet is the complete MMTP packet -- the MMTP packet header, including
any header extension, followed by the MMTP payload -- before its 4-byte
Source FEC Payload ID is appended ([@!ISO.23008-1] Section C.4.2;
(#source-fec-payload-id)).  Its T-byte source symbol is ([@!ISO.23008-1]
Section C.3.3):

~~~
Source Symbol {
  Length (16),                  # protected packet length, octets
  Protected Packet (..),        # Length octets
  Padding (..),                 # zero octets, up to T in total
}
~~~

The Length field is in network byte order and every Padding octet is
zero, so the largest protected packet a symbol can carry is T - 2
octets, and T MUST be at least 14: a shorter symbol carries no protected
packet of the 12-octet MMTP packet header (Section 3.1). (Under
"raptorq", whose T is a multiple of 8, the least T is therefore 16,
[@!MOQ-FEC-BLOCK] Section 6.1.)  A publisher MUST size
every FEC source packet so that its protected packet does not exceed T -
2 octets.  A receiver that observes a source packet whose protected
packet exceeds T - 2 octets MUST NOT feed it to the decoder -- a
truncated symbol would corrupt recovery for the entire block -- but MAY
still deliver the packet as media. On a RAP packet under a keyframe
overlay ((#keyframe-overlay)), the base and the overlay instance form
the symbol from the same protected packet, so the two protect one
identical T-byte symbol.

Recovery yields the block's SSB_length source symbols.  From each, the
receiver takes the Length octets that follow the Length field as the
recovered protected packet, and delivers that packet to the MMTP parser.
A receiver MUST NOT deliver a recovered symbol whose Length is less than
12, the size in bytes of the MMTP packet header (Section 3.1), or points
past the end of the symbol, or whose Padding octets are not all zero:
each means that the symbol is not the one the publisher encoded.

A recovered packet carries no Source FEC Payload ID, of either instance:
the trailer is appended after FEC encoding and is not part of the
protected packet.  A receiver MUST NOT re-append a trailer before
delivering the recovered packet to the MMTP parser, and MUST NOT expect
the recovered bytes to end in a block coordinate.  This holds
identically for a symbol recovered by a keyframe overlay, which the
receiver delivers as media on the strength of the overlay recovery
alone.  The 0x8B01 header extension of a RAP packet under an overlay
((#overlay-header-extension)) is part of the protected packet, by
contrast, and is recovered with it.

The packet's base SS_ID was in the trailer, and this document defines no
mapping from an overlay coordinate to a base one: a receiver MUST NOT
place an overlay-recovered symbol into a base source block unless it has
determined that packet's base SS_ID independently.  Absent that, an
overlay recovery is usable as media but MUST NOT be counted toward base
block recovery, and in particular MUST NOT be treated as reducing the
number of erasures the base decoder still has to solve. The other
direction needs no such determination, because a RAP packet recovered by
the base instance still carries its overlay SS_ID
((#overlay-header-extension)).

**SS_ID**: Every FEC source packet carries a Source FEC Payload ID
((#source-fec-payload-id)), and a receiver that parses the packet takes
each source symbol's SS_ID from that field on every path that delivers
the packet with its trailer.  The SS_ID is also carried alongside the
packet where the packaging says so: on the MoQ path every object
carrying a source symbol carries it in the FEC Source Info Object
Property ([@!MOQ-FEC-CORE] Section 5.6),
under the same value and the same definition, whether or not that object
also delivers the trailer.  A receiver that does not parse the FEC
source packet -- a relay, or a MoQ receiver with no MMTP parser -- takes
the SS_ID from there.  The SS_ID advances by one per FEC source packet,
modulo 2^32, in the order the publisher emits the packets
([@!ISO.23008-1] Section C.5.2), and the blocks of an FEC instance are
consecutive: each starts at the SS_ID that follows the last source
symbol of its predecessor ([@!MOQ-FEC-CORE] Section
5.4).  Every transport path yields the same
SS_ID for the same packet, because each path carries the same MMTP
packet, so receivers MAY combine symbols from any transport path toward
the same FEC block recovery.  A loc or cmaf track reaches multicast only
through a separate mmtp rendition track ([@!MOQ-MULTICAST] Section
4.1), whose symbols belong to
another FEC instance.

**OTI and sub-blocks**: MoQ carries no RaptorQ Object Transmission
Information (OTI, [@?RFC6330] Section 3.3) in-session: receivers derive
it per block from the instance's configuration and the block's
SSB_length per [@!MOQ-FEC-BLOCK] Section 6.1.  The
AL-FEC message of an MMTP session (Section 8.3) carries none either.
When a source block is too large to decode in the decoder's working
memory, RFC 6330 permits dividing each block into N sub-blocks (the
Number of Sub-Blocks field of the OTI).  The derived OTI fixes N = 1, so
catalog-signaled sessions do not use sub-blocks; the AL-FEC message of
[@!ISO.23008-1] carries no OTI, and the split source blocks of its
Clause C.2.2 are the two-stage coding structure, which this profile does
not use.  A publisher using MMTP packaging under this profile therefore
uses ssbg_mode1 without sub-blocks, and never ssbg_mode2.

{#source-fec-payload-id}
## Source FEC Payload ID

Exactly one 4-byte Source FEC Payload ID (SS_ID; ffsrpts_flag = 0, so no
FFSRP_TS, [@!ISO.23008-1] Section C.5.1) is appended at the end of each
MMTP FEC source packet -- following the MMTP payload, outside the MMTP
packet header -- with or without a keyframe overlay
((#overlay-header-extension)).  The trailer lies outside the declared
MPU payload (Section 5.2) and outside the protected packet
((#iso-ssbg1-v1)).

For MoQ-only receivers (no A3SA verification), the trailing 4-byte
Source FEC Payload ID remains the canonical identifier by which a source
packet is placed in its block ([@!MOQ-FEC-CORE] Section
5.5).  QUIC transport encryption provides
equivalent integrity protection.  (#a3sa-signed-region) states why the
ATSC 3.0 signing mechanism does not authenticate the trailer, and what a
receiver that requires authenticated block assignment does instead.

Whatever the receiver's verification posture, the FEC Source Info Object
Property ([@!MOQ-FEC-CORE] Section 5.6)
carries the same value for a receiver that does not parse the packet;
where an object delivers both and they disagree, the trailer is the one
that is canonical, because it is the field the FEC encoder emitted and
the one the receiver locates the symbol by.  The Property restates it at
the MoQ layer.

On an mmtp source object the Property's value is the 4-byte form of
[@!MOQ-FEC-CORE] Section 5.6, which names
instance 0: the sequence number of the source symbol the object carries,
the same value and the same definition that the Source FEC Payload ID
trailer of the FEC source packet carries.  The Property is that
trailer's MoQ-layer carrier: one identifier, one definition, whichever
path the symbol travels.  Both carry the same value and a publisher MUST
make them identical, on every source object, because the object payload
is the whole FEC source packet, trailer included. The Property is wanted
there as well: it places the symbol at the MoQ layer, reachable by a
relay and by a receiver that does not parse MMTP, whereas the trailer is
the field the FEC encoder emitted.  A packet the decoder recovers
carries neither ((#iso-ssbg1-v1)): the Property is not recovered with
the object, and the trailer is appended after FEC encoding, so a
receiver that recovers a packet determines its SS_ID from the block
coordinate that recovered it, within that FEC instance's SS_ID space; an
overlay coordinate does not yield a base SS_ID.

Where a keyframe overlay applies ((#keyframe-overlay)), an object
carrying a Random Access Point fragment is a source symbol of two FEC
instances, whose SS_ID spaces are disjoint, so "the source symbol the
object carries" names two SS_IDs rather than one.  The Property carries
the base instance's SS_ID -- the value the Source FEC Payload ID trailer
carries -- and a publisher MUST NOT place an overlay SS_ID in it.  No
second Property entry conveys the overlay SS_ID: it travels in the
0x8B01 MMTP header extension, which lies inside the MMTP packet header
and is therefore part of the protected packet of both instances
((#overlay-header-extension)), so it rides inside the object's payload
on this path as on any other.  A receiver takes an overlay SS_ID from
that extension and from nothing else, and in particular MUST NOT infer
one from the Property.

An object that carries a source symbol but no FEC Source Info Property
violates the publisher requirement of [@!MOQ-FEC-CORE] Section
5.6.  A receiver that does not parse the
FEC source packet has no SS_ID for it -- at the MoQ layer the Property
is the only carrier -- so it MUST NOT feed such an object to the base
decoder and MUST NOT count it in K or in any base block, and MAY still
deliver it as media.  A receiver that parses the packet MAY take the
SS_ID from the trailer instead, since the packaging delivers it; this is
a deviation from that section, which has no trailer to fall back on.  An
overlay SS_ID is unaffected either way: it travels in the 0x8B01 MMTP
header extension ((#overlay-header-extension)), which the Property does
not carry, and that section alone governs when the overlay decoder may
be fed.

{#repair-packet}
## Repair Packet

Each object on a repair track is one complete MMTP repair packet (packet
type 0x03, FEC Type 2) carrying exactly one repair symbol. Its layout is
the ISO 23008-1 AL-FEC repair packet form -- the MMTP packet header
followed by the 13-byte Repair FEC Payload ID and the repair symbol data
([@!ISO.23008-1] Sections C.4.3 and C.5.3; ssbg_mode1, one-stage FEC
with N = 1, and ffsrpts_flag = 0, so no FFSRP_TS, Section C.5.1) -- so
the same repair packet is valid on MoQ, multicast UDP, and native
broadcast paths without translation, and matches the repair-object
depiction of (#fec-integration).  The layout below reproduces
[@!ISO.23008-1] Section C.5.3 for convenience.  The Repair FEC Payload
ID carries the fields of the repair object of [@!MOQ-FEC-CORE] Section
7.5 with the semantics that section gives them
-- SS_Start, RSB_length, RS_ID and SSB_length -- and this section
defines only the MMTP packet header in front of them:

~~~
Repair Packet {
  MMTP Packet Header (96),      # packet type 0x03, FEC Type 2
  Repair FEC Payload ID {
    SS_Start (32),
    RSB_length (24),
    RS_ID (24),
    SSB_length (24),
  },
  Repair Symbol Data (..),      # exactly one symbol, T bytes
}
~~~

**MMTP Packet Header**: The standard 12-byte MMTP packet header (Section
3.1) with packet type 0x03 (repair) and FEC Type 2; its `packet_id`
routes the repair flow.  Like every packet of its MMTP packet flow,
source and signaling packets included, a repair packet has the packet
counter flag C = 0 (Section 3.1; [@!ISO.23008-1] Clause 9.2.3).  A
repair packet MUST NOT carry a header extension (X = 0).  Because C = 0
and X = 0, the Repair FEC Payload ID always begins at byte offset 12.

A repair object under this profile is therefore 12 + 13 + T bytes long,
not the 13 + T bytes that [@!MOQ-FEC-CORE] Section
7.5 requires of a repair object under
"moq-object-v1"; a receiver MUST discard a repair object of an mmtp
track whose payload is not exactly 12 + 13 + T bytes.  It reads the
Repair FEC Payload ID at byte offset 12, and every other rule of that
section applies to the fields: a receiver routes the packet to the
decoder of the instance that the configuration relates to the repair
track it arrived on, and discards a packet whose RS_ID is not less than
RSB_length or that fails a bound of the instance's scheme
([@!MOQ-FEC-BLOCK] Section 7).

{#keyframe-overlay}
## Keyframe Overlay

A source track MAY additionally be protected by a keyframe overlay: a
second, independent FEC instance whose source symbols are only the
fragments of Random Access Points of that source track.  It is this
profile's form of an overlapping instance ([@!MOQ-FEC-CORE] Section
8.4).  The overlay is defined only for a
source track under "iso-ssbg1-v1", because its membership and its
overlay SS_ID rely on the MMTP `RAP_flag` and header extension
((#overlay-membership) and (#overlay-header-extension)), which a loc or
cmaf object does not have; a track under "moq-object-v1" has no overlay,
and a catalog that declares one for such a track fails the rule of
(#overlay-instance).

Losing part of a Random Access Point makes every dependent frame
undecodable until the next one; the overlay protects RAP fragments
across a block of its own, which can be wider than the base window,
without changing the base instance's latency.

{#overlay-instance}
### Overlay Instance

An overlay is a separate FEC instance over the same source track.  It
has its own `sourceSymbols` (K_overlay) and its own `repairSymbols`,
declared on its own instance entry with its own repair track
([@!MOQ-FEC-CATALOG] Section 3.1), and it shares
the source track's `scheme`, `blockProfile` and `symbolSize`. It does
not share the base instance's K, its block partition, its SS_ID space,
or its RS_ID space.  Because each source packet carries one base SS_ID,
a different K or interleave window needs a separate rendition; the
keyframe overlay is a separate FEC instance, not a layer.

The overlay's instance object carries one member that this document
defines, under the rule of [@!MOQ-FEC-CATALOG] Section
3.4 that lets a block profile's document define
further keys for the tracks it admits, and further exceptions among
them:

**scope** (string, OPTIONAL): When present, MUST be `"keyframe"`, and
declares this instance to be the source track's keyframe overlay.  It is
an unknown-key exception ((#overlay-receiver-behavior)).  An overlay is
defined only for a source track under "iso-ssbg1-v1"
((#keyframe-overlay)).

Every per-block quantity of [@!MOQ-FEC-CORE] -- K, the total repair
count P, SS_ID, ESI, RS_ID, SS_Start, RSB_length, SSB_length, the
short-block rules, the wrap epoch and repair group IDs, and the bounds
of its Section 10.3 -- is defined within one FEC instance
(its Section 5.1).  For the base instance, K is the
source track's `sourceSymbols` and P is the sum of `repairSymbols` over
its published layers ([@!MOQ-FEC-CORE] Section
7.3.1); for an overlay, K and P are the
`sourceSymbols` and `repairSymbols` of its own instance.  A repair
packet belongs to the instance of the track it arrived on
((#overlay-membership)).

An overlay is not a repair layer.  It carries no `repairLayer`, it is
not a member of the layer index chain, and it is excluded from the
contiguity and priority monotonicity rules of [@!MOQ-FEC-CORE] Section
10.3, which order the base layer chain only.  Its
`priority` is independent within 192 to 255 ([@!MOQ-FEC-CORE] Section
10.3, rule 10, and Section
11), and MAY be numerically lower than a
base enhancement layer's so that a keyframe repair symbol is delivered
before an ordinary one.

Overlay ESIs never collide with base ESIs because the two are different
instances decoded by different decoders; a receiver does not feed a
repair symbol of one instance to the decoder of the other, nor reuse a
source symbol's coordinate in one instance as its coordinate in the
other ([@!MOQ-FEC-CORE] Section 5.1).  A RAP source
packet is a source symbol of both instances, at an unrelated coordinate
in each ((#overlay-membership)).

A source track has at most one overlay, a wire constraint explained in
(#overlay-header-extension), and none when its `blockProfile` is
"moq-object-v1"; the overlay instance's repair track carries no
`repairLayer`.  A receiver MUST validate this before starting FEC for an
overlay instance of the source track, and on any violation MUST fail
closed as [@!MOQ-FEC-CORE] Section 10.3 requires for its
own rules: it reports the offending catalog path, does not start FEC for
any overlay instance of that source track, and MUST NOT repair the
catalog by ignoring a track.  An overlay is declared only by the
catalog, never in an in-band AL-FEC message, and only where no FEC
source or repair packet carries FFSRP_TS ((#overlay-header-extension)).

Under "reed-solomon" the overlay has its own bound: K_overlay +
P_overlay is at most 255 ([@!MOQ-FEC-BLOCK] Section
7), whatever the base instance uses, and its rows
and columns of A are numbered within the overlay instance
([@!MOQ-FEC-BLOCK] Section 5.2).  An overlay with
K_overlay 256 and P_overlay 32 has an RS_ID range of 0 to 31, an ESI
range in a full overlay block of 256 to 287, and packets carrying
RSB_length 32; it is valid only under "raptorq", since 256 + 32 = 288
exceeds 255.  Under "reed-solomon", an overlay whose instance declares
`sourceSymbols` 192 and `repairSymbols` 32 is valid, since 192 + 32 =
224.

{#overlay-membership}
### Overlay Membership

The overlay's source symbols are the fragments of the source track that
belong to a Random Access Point, in transmission order.  A publisher
that declares an overlay MUST set `RAP_flag` on a source packet of the
track, MUST include the packet in the overlay instance, and MUST carry
the packet's overlay SS_ID in its 0x8B01 header extension
((#overlay-header-extension)), if and only if that packet's payload
belongs to a keyframe MFU covered by the overlay.

Overlay source symbols are numbered consecutively within the overlay
instance, in the order the publisher emits them: the overlay SS_ID is 0
at the first overlay source symbol of the stream and advances by one per
overlay source symbol, modulo 2^32 ([@!MOQ-FEC-CORE] Section
7.6).  It is the value the RAP
source packet carries in its 0x8B01 header extension
((#overlay-header-extension)).  It lives in the overlay instance's own
SS_ID space, independent of the base instance's, and the two IDs on one
packet are unrelated numbers.  An overlay source block holds at most
K_overlay overlay source symbols, and overlay blocks, including short
ones, are formed, located and wrapped exactly as base blocks are
([@!MOQ-FEC-CORE] Sections 5.4,
5.5 and
7.6), with K_overlay as the upper
bound on their SSB_length.  Because a RAP is a small fraction of the
media, an overlay block spans many base blocks; the overlay's recovery
latency is therefore its own block span and is unrelated to
`interleaveDepthMs`.

A receiver knows that a source packet is an overlay source symbol
because the packet carries the 0x8B01 header extension
((#overlay-header-extension)).  It knows that a repair packet belongs to
the overlay because it arrives on the repair track that the catalog
declares for the overlay instance of this source track, and that track
has its own `packet_id`.  The instance is therefore fixed by the track
the packet arrived on; no field of the repair packet distinguishes the
two, and a receiver does not infer the instance from SS_Start,
RSB_length, or SSB_length, whose values are only interpretable once the
instance is known ([@!MOQ-FEC-CORE] Section
7.5).

{#overlay-header-extension}
### Overlay SS_ID Header Extension

When the catalog declares a keyframe overlay for a source track
((#keyframe-overlay)), a source packet of that track carrying a Random
Access Point fragment is a source symbol of two FEC instances. It
carries its base SS_ID in the one Source FEC Payload ID trailer that
every FEC source packet carries ((#source-fec-payload-id)), and its
overlay SS_ID ((#overlay-membership)) in an MMTP header extension
([@!ISO.23008-1] Clause 9.2.3) of type 0x8B01:

~~~
Source Packet with Overlay {
  MMTP Packet Header {
    ...,                          # X = 1, RAP_flag = 1
    Header Extension {
      Type (16) = 0x8B01,
      Length (16) = 4,
      Overlay SS_ID (32),
    },
  },
  MMTP Payload (..),
  Source FEC Payload ID (32),     # base instance SS_ID
}
~~~

A publisher that declares an overlay MUST carry this extension as the
header extension, with X = 1, of exactly the source packets that it
includes in the overlay instance, that is the packets on which it sets
`RAP_flag` ((#overlay-membership)), and of no other packet of the track.
An MMTP packet carries at most one header extension ([@!ISO.23008-1]
Clause 9.2.3), so the RAP packets of a track under an overlay carry no
other MMTP header extension, and a publisher that needs another header
extension on those packets cannot use the overlay for that track.
[@!ISO.23008-1] specifies no particular header extension and no registry
of header extension types; this document uses the type 0x8B01 for the
overlay SS_ID ((#iana-considerations)).

The trailer is never more than one Source FEC Payload ID.  On a packet
with or without the extension, the last four bytes are the base SS_ID,
as [@!ISO.23008-1] Section C.4.2 places it, so a receiver that does not
implement overlays locates the trailer and the payload as on any other
packet, stepping over the extension by its Length field. The extension
lies inside the MMTP packet header, so it is part of the protected
packet of both instances ((#iso-ssbg1-v1)), which protect one identical
source symbol.  The permission of [@!ISO.23008-1] Clause 9.2.3 to
discard a header extension therefore extends only to a receiver's own
processing: a node that forwards the packet MUST NOT remove or alter the
extension.  A RAP packet recovered by either instance carries its
overlay SS_ID, so a receiver MAY place a RAP packet that the base
instance recovered into the overlay block that the extension locates;
(#iso-ssbg1-v1) states why the converse requires the packet's base
SS_ID.

A receiver that implements overlays takes a packet's overlay SS_ID from
this extension and from nothing else.  It MUST NOT feed the overlay
decoder a source packet that lacks the extension, whatever its
`RAP_flag`, or one whose extension has a Length other than 4, and MUST
NOT infer an overlay SS_ID from `RAP_flag`, from the packet's position,
or from its base SS_ID.

A source track has at most one overlay ((#overlay-instance)) because a
source packet has one header extension, and so carries one overlay
SS_ID; relaxing that bound would be a revision of this document and a
change to the source packet layout, not a catalog-only change.

The overlay is declared only by the catalog: Section 8.3 forbids
describing the overlay's repair flow in an AL-FEC message, which
identifies an FEC source flow by packet_id ([@!ISO.23008-1] Clause
C.6.3) and cannot describe the RAP subset that the overlay protects, so
a receiver that consumes the flow without the catalog uses the base
instance alone.  An overlay is defined only without FFSRP_TS: a
publisher MUST NOT declare an overlay for a source track whose FEC
source or repair packets carry FFSRP_TS (ffsrpts_flag = 1,
[@!ISO.23008-1] Section C.5.1), and the extension carries an SS_ID
alone.

(#a3sa-signed-region) applies to the overlay SS_ID as to the base one:
A3SA signing authenticates neither, and a receiver that requires
authenticated block assignment treats each as that section requires.

{#overlay-receiver-behavior}
### Receiver Behavior

A receiver that implements overlays and has joined the overlay repair
track decodes the two instances independently and MAY use the recovered
RAP fragments even when the base instance failed to recover the block
that carried them.

The overlay is the publisher-side half of keyframe protection.  The
receiver-side half is the repair policy of [@!MOQ-FEC-MULTICAST] Section
6, under which a receiver gives a
keyframe-bearing base block that in-band decoding leaves unrecovered
priority unicast repair; its Section
6.6 states how the two
combine.

A receiver that does not implement overlays MUST fail closed on a
catalog that declares one for a track it intends to consume, that is on
an FEC instance carrying the unknown `scope` key, and MUST NOT ignore
the key and consume the source track anyway.  This is an unknown-key
exception that this document defines ((#overlay-instance)) under
[@!MOQ-FEC-CATALOG] Section 3.4, which lets a block
profile's document define further exceptions: a receiver that ignored
the key could not tell the overlay's repair track from a repair layer of
the base instance, and would feed the base decoder repair symbols of
another FEC instance ((#overlay-membership)).

This mechanism is not backward compatible with receivers that predate
it, for the same reason.  A publisher that must serve such receivers
publishes the overlay on a separate source track, or does not publish
it.

{#interleaving}
## Interleaving

Interleaving and typical interleave windows (`interleaveDepthMs`) follow
[@!MOQ-FEC-CORE] Section 9.3.  A positive
`interleaveDepthMs` is the elapsed source/repair send-span bound for
each actual FEC block; it does not select FEC block boundaries, derive a
number of groups per block, or require a fixed relationship between an
FEC block and a media Group.  A typical window for ARIB STD-B60 content
is 2000 ms.  The receiver's block-abandonment timeout -- how long it
waits for a block's source and repair symbols before declaring the block
unrecoverable -- follows the ISO receiver-buffer model [@!ISO.23008-1]
Section 11.2.

[@!MOQ-FEC-CORE] Section 10.1 admits a positive
`interleaveDepthMs` and lets a block profile give the value zero a
meaning of its own.  Under this profile the field MAY also be zero.  A
value of zero has the ISO meaning of using `protection_window_size`
instead of a time window ([@!ISO.23008-1] Clause C.6.3); this catalog
profile carries no packet-count window. A catalog-only receiver
therefore MUST NOT treat zero as a zero-duration span or use it to
derive a block count, and has no elapsed-time FEC deadline from this
field.  If an applicable ISO packet-count window is accepted in-band, it
governs separate count-based processing; it does not supply a
millisecond deadline, it is not converted to milliseconds without an
independently defined time mapping, and the receiver MUST NOT assume a
media cadence to convert it.  A publisher uses a zero value only with
that ISO `protection_window_size` alternative.  An absent field supplies
no catalog-signaled span; neither an absent nor a zero value supplies an
elapsed-time deadline.  Without an elapsed-time deadline, open-block
state is bounded only by the local policy of [@!MOQ-FEC-CORE] Section
9.4, and on a multicast or AMT leg the receiver
performs no block classification or unicast repair
([@!MOQ-FEC-MULTICAST] Section 6) and
keeps its repair-layer selection fixed (its Section
4).

{#fec-parameter-signaling}
# FEC Parameter Signaling

FEC parameters for mmtp-packaged tracks are signaled in the catalog
`fec` field, whose encoding [@!MOQ-FEC-CATALOG] defines (its Section
3) for the configuration data model of
[@!MOQ-FEC-CORE] Section 10, which is
authoritative for MoQ receivers (that section).  A MoQ receiver requires
no in-session FEC signaling: the catalog carries every FEC parameter it
needs.  This document does not redefine the catalog fields but specifies
MMT-specific considerations for their use.

A publisher MAY also carry the MMTP AL-FEC signaling message of
Section 8.3 on a MoQ mmtp source track, as an object whose payload
is an MMTP signaling packet on packet_id 0 (Section 3.1).  When
present, it is published in Subgroup 0 of an MPU group as the object
immediately before, and in the same subgroup as, that group's FT=0
object, and a group carries at most one such object (Sections 4.2
and 4.3).  On a MoQ
track such an object is a redundant in-band copy of catalog state: the
message MUST NOT signal FEC parameters that contradict the track's
catalog `fec` instances, and where the two disagree the catalog governs,
as [@!MOQ-FEC-CORE] Section 10 requires
of any in-band signaling. The object carries no media data
unit and no repair symbol, so a MoQ receiver MUST NOT deliver it to
a media or repair decoder (Section 3.1); a receiver that does not
process MMTP signaling discards it.

The signaling object is not an FEC source symbol.  Its MMTP packet
has FEC Type 0 and no Source FEC Payload ID; it is not protected by
any repair symbol, is not counted in any FEC block or in
`sourceSymbols` (K), and has no SS_ID and no Encoding Symbol ID.
Because it occupies an Object ID (Object ID 0 of its group,
Section 4.6), Object IDs on an mmtp source track are not positions
in the FEC block: a receiver MUST take each source symbol's SS_ID from
the Source FEC Payload ID that trails its FEC Type 1 packet
((#source-fec-payload-id)), never from its Object ID, and places the
symbol in its block by that SS_ID ([@!MOQ-FEC-CORE] Section
5.5).

A MoQ track carries only the
signaling packets its publisher chose to place on that track, so
the packet_sequence_number values it exhibits on packet_id 0 need
not be contiguous.  A receiver MUST NOT infer loss from a
packet_sequence_number gap on packet_id 0 of a MoQ track, and MUST
NOT defer any packet, including a later packet on packet_id 0,
behind such a gap.

{#mmt-specific-fec-parameters}
## MMT-Specific FEC Parameters

When used with MMT packaging, the instance parameters of
[@!MOQ-FEC-CORE] Section 10.1, as the catalog
encodes them ([@!MOQ-FEC-CATALOG] Section 3.1),
map as follows:

- **scheme**: the scheme identifier ([@!MOQ-FEC-BLOCK] Section
  3) whose [@!ISO.23008-10] code point the
  MMTP AL-FEC message carries in `fec_code_id_for_repair_flow` (Section
  8.3)

- **blockProfile**: "iso-ssbg1-v1" ((#iso-ssbg1-v1); registered in
  [@!MOQ-FEC-CORE] Section 15.3),
  the ISO 23008-1 Annex C block profile, for which an AL-FEC message
  carries the coding byte 0x14 (Section 8.3); REQUIRED on every FEC
  instance, with no default

- **sourceSymbols**: The largest number of MMTP packets (source symbols)
  that an FEC block may hold; each block holds SSB_length of them
  ([@!MOQ-FEC-CORE] Section 5.4).  On the
  MMT path the canonical FEC source symbol is one whole MMTP packet,
  before its Source FEC Payload ID, framed with its length
  ((#iso-ssbg1-v1))

- **interleaveDepthMs**: When positive, the elapsed source/repair send
  span bound of each actual FEC block, as defined by [@!MOQ-FEC-CORE]
  Sections 10.1 and
  9.3; (#interleaving) defines absent and
  zero values under this profile.  It is independent of
  `groupDurationMs` and does not imply a block count or block boundary
  from MoQ Groups.  When ingesting broadcast content, use the ISO
  protection-window signaling or a known source/repair send-span bound.
  A source-frame count alone does not bound the actual packet send span.

See [@!MOQ-FEC-CATALOG] for the complete catalog field definitions,
[@!MOQ-FEC-CORE] Section 15.2 for the
scheme registry, and [@!MOQ-FEC-BLOCK] for the scheme bounds and the OTI
derivation (its Sections 7 and
6.1).

For FEC block alignment and timing to be deterministic, an mmtp
publisher MUST, in addition to the encoder constraints of
[@!MOQ-FEC-CORE] Section 5.3:

1. Signal the catalog-authored group duration and frame rate in the MoQ
   catalog: publish a positive duration as `groupDurationMs` when its
   integer-millisecond form is exact, or as the exact positive
   `groupDurationTicks`; when both are present, `groupDurationTicks`
   wins and `groupDurationMs` is informational.  Signal the keyframe
   cadence in `keyframeIntervalMs` (or `keyframeIntervalTicks`), and the
   frame rate in the `framerate` field (Sections 4.4.2, 4.4.3 and 13.1).
   The ISO 23008-1 AL-FEC message has no field for either value
   ([@!ISO.23008-1] Table C.3), so an encoder signals neither there, and
   a receiver takes neither from it.

2. If frame rate or GOP size changes mid-session, update the MoQ catalog
   and signal a manifest discontinuity for DASH/HLS.

3. When `interleaveDepthMs` is positive, choose it so that the actual
   elapsed send span from the first source or repair packet of every
   block to its last does not exceed the signaled value.  A zero value
   is usable only with the ISO `protection_window_size` alternative of
   (#interleaving).  The value is not derived from a group count, frame
   count, or per-symbol interval.

{#repair-tracks}
## Repair Tracks

A source track's repair tracks are the track that each of its FEC
instances names in `repairTrack` and the tracks that name it in `source`
([@!MOQ-FEC-CATALOG] Section 3.2; [@!MOQ-FEC-CORE]
Section 10.2);
[@!MOQ-FEC-CATALOG] Section 6 gives their
conventional names.  Subscription to them follows [@!MOQ-FEC-CORE]
Section 7.2, and their priorities its Section
11.

{#al-fec-message}
## FEC Signaling for Multicast Delivery

For SSM and Any-Source Multicast (ASM) delivery there is no
bidirectional signaling channel.  FEC parameters reach multicast
receivers via:

1. **MoQ Catalog Extension** (authoritative for MoQ receivers,
   [@!MOQ-FEC-CORE] Section 10):
   out-of-band delivery in the catalog `fec` field (see the worked
   catalog of [@!MOQ-FEC-CATALOG] Appendix A).

2. **MMTP AL-FEC Signaling (message_id=0x0203)**: in-band delivery
   of the AL-FEC message of [@!ISO.23008-1] Clause C.6, with
   Table C.3 as replaced by [@!ISO.23008-1.AMD1],
   for ISO/IEC 23008-1 receivers that consume the flow without the
   catalog, such as native broadcast (ATSC 3.0, ARIB STD-B60)
   receivers.  A publisher that sends this message MUST carry it in
   an MMTP signaling packet (packet type 0x02) on packet_id 0, the
   MMTP signaling flow, after the signaling message payload header of
   [@!ISO.23008-1] Clause 9.3.4.2 (Section 3.1); on
   multicast delivery it shares the multicast group of the media it
   describes, and on MoQ delivery it MAY be carried as an object of an
   mmtp source track under the rules of Section 8.  No track is
   advertised on packet_id 0
   ([@!MOQ-MULTICAST] Section 4.1),
   and a receiver does not deliver
   these packets to a media or repair decoder (Section 3.1;
   [@!MOQ-MULTICAST] Section 5)

Each FEC source flow has one FEC encoded flow ([@!ISO.23008-1]
Clause C.6.3), so the message describes a source track's flow as one
entry of the message's `fec_flow_descriptor` naming exactly one repair
flow, the track's layer-0 repair track ([@!MOQ-FEC-CORE] Section
7.3).  For a track whose instance's `blockProfile` is
"iso-ssbg1-v1", that entry carries:

- a `number_of_assets` of 1, the one Asset it lists being the source
  track's, the Asset whose packet_id is the track's: an FEC source
  flow of [@!ISO.23008-1] may carry the packets of several Assets
  (its Clause C.1), where an FEC instance of [@!MOQ-FEC-CORE]
  protects one source track (its Section 5.1);
- the coding byte 0x14, that is `fec_coding_structure` 0001
  (one-stage), `ssbg_mode` 01, `ffsrpts_flag` 0 and
  `fec_payload_id_mode` 0 ((#iso-ssbg1-v1));
- as its `fec_code_id_for_repair_flow`, the code point that
  [@!ISO.23008-10] Table 1 assigns to the code that the instance's
  `scheme` names ([@!MOQ-FEC-BLOCK] Section
  3): 3, the "6330 code" (RaptorQ), for
  "raptorq", and 1, the Reed-Solomon code, for "reed-solomon";
- as its `repair_flow_id`, the packet_id of the layer-0 repair
  packets.  [@!ISO.23008-1.AMD1] makes this field 16 bits in the
  one-stage branch, where the 2023 edition of Table C.3 gives it 8
  bits and so cannot name a repair packet_id above 255;
- as its `length_of_repair_symbol`, the instance's `symbolSize` (T), the
  byte length of every repair symbol and, under ssbg_mode1, of every
  source symbol ([@!MOQ-FEC-CORE] Section 10.1;
  (#iso-ssbg1-v1) and (#repair-packet)), and as its
  `num_of_repair_symbol_per_packet` 1, the one repair symbol each repair
  packet carries ((#repair-packet); [@!MOQ-FEC-CORE] Section
  7.5), a field whose semantics
  [@!ISO.23008-1] Clause C.6.3 gives for ssbg_mode2 alone;
- as its `maximum_k_for_repair_flow`, the instance's `sourceSymbols`:
  like that field, it bounds each block's SSB_length and is not the size
  of any particular block ([@!MOQ-FEC-CORE] Section
  5.4); and
- as its `maximum_p_for_repair_flow`, the RSB_length that every
  repair packet of the track's FEC instance carries: the total
  repair count over the published layers, which is the instance's
  `repairSymbols` while layer 0 is the only published layer
  ([@!MOQ-FEC-CORE] Section 7.3.1).  A
  publisher that appends a layer ([@!MOQ-FEC-CORE] Section
  7.3.2) raises that total and sends a new
  version of the message carrying it only after the last repair packet
  generated under the previous total, of whichever block: a block's
  RSB_length is the total in force when its repair symbols were
  generated ([@!MOQ-FEC-CORE] Section 7.5), so
  every repair packet
  sent after the new version carries a value no lower than the
  field it names.  The path keeps no order between the message, on
  `packet_id` 0, and the repair flow (Section 5.2.2), so a receiver
  of both can take a packet generated under the previous total
  after the new version; the blocks generated under the raised
  total follow every block generated under the previous one in the
  serial order of their SS_Start ([@!MOQ-FEC-CORE] Section
  7.6), as its Section
  7.3.2 requires of the publisher, which the
  conversion rule of Section 13.2 relies on instead.

A receiver that holds layer 0 under the AL-FEC message alone, without
the catalog ((#atsc-compatibility)), applies the fail-closed check of
[@!MOQ-FEC-CORE] Section 7.3.2 with
`maximum_p_for_repair_flow` standing for its O_0 + P_0, by that check's
anchored clause alone: layer 0 has no clause of its own track, its O_0
being 0 and its symbols' coordinates depending on no published count, so
a packet of the flow generated under a previous total, which the message
can precede (above), fails it closed on nothing.

Layered repair is an extension of [@!ISO.23008-1] that an ISO AL-FEC
message cannot express: each FEC source flow has one FEC encoded flow,
whose one-stage coding structure carries a single `repair_flow_id`
([@!ISO.23008-1] Clause C.6.3), so only layer 0 maps to an ISO repair
flow.  A repair layer is also unrelated to the layers of ISO layer-aware
FEC (LA-FEC, Clause C.2.3).  A publisher MUST NOT describe a repair
layer above layer 0, or a keyframe overlay, in the message, whether in
that entry or in an entry of its own: the one-stage coding structure
names one repair flow per FEC encoded flow, the overlay protects a RAP
subset that no `packet_id` identifies, and only the catalog declares
either ([@!MOQ-FEC-CORE] Section 7.3;
(#keyframe-overlay) and (#overlay-header-extension)).

{#multicast-integration}
# Multicast Integration

MMT content can be delivered via IP multicast (SSM, AMT) and TreeDN
[@?RFC9706].  Platform-specific delivery paths, the
multicast endpoint catalog extension, and TreeDN/AMT integration are
defined in [@!MOQ-MULTICAST], and the multicast packet format in its
Section 5.

{#atsc-compatibility}
# ATSC 3.0 Compatibility

This specification is designed for interoperability with the
Application-Layer FEC of ATSC A/331 [@?ATSC-A331] MMTP sessions.
[@?ATSC-A331] applies AL-FEC to an MMTP session, when it applies it at
all, through the AL-FEC framework of [@!ISO.23008-1] Annex C and
requires no FEC code of its own (its Section 8.1.2.5): the framework
carries whichever code the AL-FEC message names by its [@!ISO.23008-10]
code point.  The codes are those of [@!MOQ-FEC-BLOCK], which specifies
two, "reed-solomon" (code point 1, mandatory to implement) and "raptorq"
(code point 3, OPTIONAL) (its Sections 3 and
10); Section 8.3 gives the AL-FEC message
a publisher sends for a track of either, and an MMTP session whose
AL-FEC message names any other code is outside this document and its
companions until the "MoQ FEC Schemes" registry of [@!MOQ-FEC-CORE]
Section 15.2 lists that code.  A publisher
that ingests an A/331 MMTP session takes the FEC parameters of its
tracks from that message and the asset locations of the MP table
(Section 13.2), and a receiver that consumes the session without the
catalog takes them from the message alone, holding the one repair flow
as layer 0 under the block total the message bounds, as Section 8.3
specifies.  An MMTP session carries no [@?RFC6330] OTI: the derived OTI
of [@!MOQ-FEC-BLOCK] Section 6.1 fixes N = 1, and
sub-blocks are never used ((#iso-ssbg1-v1)).  ROUTE delivery, whose
repair protocol (Annex A.4 of [@?ATSC-A331]) is RaptorQ-based, is
outside the scope of this document.

{#arib-compatibility}
# ARIB STD-B60 Compatibility

ARIB STD-B60 [@?ARIB-B60] (Japan's MMT-based broadcasting standard)
uses the same ISO 23008-1 foundation as ATSC 3.0.  Publishers SHOULD
preserve the original FEC parameters when ingesting ARIB STD-B60
content.

{#clock-reference}
## Clock Reference

ARIB STD-B60 uses the MMTP Timestamp of Section 3.1: the UTC send
time of the packet in NTP short format.

{#transport-hierarchy}
# Transport Hierarchy

Clients SHOULD attempt transports in the preference order that
[@!MOQ-MULTICAST] Section 3 defines for native and browser clients.
AL-FEC (Section 7) is the loss recovery on SSM/AMT paths, which have
no retransmission.

{#catalog-signaling}
# Catalog Signaling

The MoQ catalog indicates MMT packaging and multicast endpoints.

The catalog of this suite is an MSF catalog: the root object and its
fields (`version`, `generatedAt`, `tracks`, ...), the requirement that
parsers ignore fields they do not understand, and the base per-track
fields are those of [@!I-D.ietf-moq-msf] Section 5.  The catalog is
delivered as a MoQ track whose case-sensitive Track Name is `catalog`
([@!I-D.ietf-moq-msf] Section 5).  The documents of this suite extend
the base in the same manner as [@?I-D.ietf-moq-cmsf] extends it: this
document adds the packaging value `mmtp` and the mmtp track fields
(Section 13.1), [@!MOQ-FEC-CATALOG] adds the per-track `fec` array of
FEC instances and the `fec-repair` and `fec-source` packaging values
(its Sections 3 and
3.3), and [@!MOQ-MULTICAST] adds the root-level
`multicast` member.  Every catalog field this suite uses is defined
either by [@!I-D.ietf-moq-msf] or locally by a document of this suite
(with `cmaf` tracks per [@?I-D.ietf-moq-cmsf]); no field is defined by
any other catalog specification.

{#packaging-value-and-track-fields}
## Packaging Value and Track Fields

This document defines a single packaging value:

~~~
packaging: "mmtp"
~~~

carried in the per-track `packaging` field of the catalog
([@!I-D.ietf-moq-msf] Section 5.2.4).  The value extends the
allowed packaging values of that specification in the same manner
as the `cmaf` value of [@?I-D.ietf-moq-cmsf] Section 3.5.1; see
Section 15 for the registry request.  Object payloads of an
mmtp-packaged track are whole MMTP packets per Section 4.2.

Per-track catalog fields for mmtp packaging:

| Field | Status | Type | Description |
|-------|--------|------|-------------|
| `packaging` | REQUIRED | String | MUST be "mmtp" |
| `mmtpMode` | REQUIRED | String | MUST be "mfu" (Section 5); defined by this document |
| `timescale` | REQUIRED | Number | Media timescale in Hz ([@!I-D.ietf-moq-msf] Section 5.2.21, profiled REQUIRED here; Section 4.4.2) |
| `presentationAnchorTicks` | REQUIRED for synchronized audio/video tracks | Signed integer | Track timestamp corresponding to shared presentation time zero (Section 4.4.1); defined by this document |
| `groupDurationMs` | Conditional | Number | REQUIRED without the tick form; positive integer ms (Section 4.4.2); informational when ticks are present |
| `groupDurationTicks` | OPTIONAL | Number | Positive exact group duration in track ticks; authoritative when present (Section 4.4.2); defined by this document |
| `altGroup` | OPTIONAL | Number | Switching-set membership key ([@!I-D.ietf-moq-msf] Section 5.2.12, profiled in Section 4.4) |
| `keyframeIntervalMs` | OPTIONAL | Number | Keyframe/GOP cadence, integer ms; video only (Section 4.4.3); defined by this document |
| `keyframeIntervalTicks` | OPTIONAL | Number | Integer-tick override for the keyframe interval (Section 4.4.3); defined by this document |
| `initRef` | OPTIONAL | String | `id` of the root `initDataList` entry, of type "inline", that holds the base64 ftyp+moov init segment ([@!I-D.ietf-moq-msf] Sections 5.1.7 and 5.2.13, profiled in Section 4.5) |
| `fec` | OPTIONAL | Array | FEC instances, encoded per [@!MOQ-FEC-CATALOG] Section 3 (Section 8) |

All other base track fields of [@!I-D.ietf-moq-msf] Section 5.2
apply unchanged.  In particular `name` and the rendition
parameters -- `codec` ([@!I-D.ietf-moq-msf] Section 5.2.18; required
for media tracks per that section), `framerate`, `width`, `height`,
`samplerate`, `channelConfig`, `bitrate`, and `lang` -- are flat,
top-level fields of the track object.

`mmtpMode` selects the object layout and MUST be "mfu".  It delivers
one subgroup per FT=0, FT=1, or FT=2 data unit as defined in Sections
4.3 and 5.  A subscriber MUST reject a track whose
`mmtpMode` is absent or has any other value; the object layout cannot
be inferred safely from received objects.

Example, with the `data` value shortened:

~~~ json
{
  "version": "draft-01",
  "tracks": [{
    "name": "video",
    "packaging": "mmtp",
    "isLive": true,
    "mmtpMode": "mfu",
    "timescale": 90000,
    "presentationAnchorTicks": 0,
    "groupDurationMs": 1000,
    "codec": "avc1.640028",
    "width": 1920,
    "height": 1080,
    "framerate": 30,
    "bitrate": 6000000,
    "initRef": "video-init"
  }],
  "initDataList": [{
    "id": "video-init",
    "type": "inline",
    "data": "AAAAIGZ0eXBpc29t..."
  }]
}
~~~

{#mmtp-signaling-to-moq-catalog-conversion}
## MMTP Signaling to MoQ Catalog Conversion

This section is informative: it documents how a converter that
ingests an MMTP broadcast service, an ATSC 3.0 MMTP session
([@?ATSC-A331] Section 8.1.2.1) or an ARIB STD-B60 service, derives a
MoQ catalog from the MMT signaling, and imposes no interoperability
requirements on MoQ publishers or subscribers.  A converter's output
catalog is subject to the normative catalog requirements of
Section 13.1 like any other catalog.  The MP table gives the
location of each Asset ([@!ISO.23008-1] Clause 10.3.9) and the
AL-FEC message the FEC parameters of each protected flow
([@!ISO.23008-1] Annex C.6; Section 8.3 gives the fields a MoQ
publisher sets, which a converter reads back).

The `multicast` field in the output uses the multicast endpoint
format of [@!MOQ-MULTICAST] Section
4.1.  Conversion rules:

- each MMTP session the MP table locates by its source address,
  destination address and destination port -> one
  `multicast.endpoints[]` entry (`sourceAddress`, `groupAddress`,
  `port`), and the Assets it carries -> that endpoint's `tracks[]`
- each Asset -> a track whose `packetId` is the Asset's packet_id,
  unique within the session ([@?ATSC-A331] Section 8.1.2.1.1) and
  carried by every packet of the flow, so a converter cannot renumber
  it.  [@!MOQ-MULTICAST] Section 4.1
  requires each `packetId` value to
  denote one sub-flow across all endpoints of a sending entity and
  reserves 0 for the signaling flow, so a converter publishes
  sessions whose packet_ids collide under different namespaces, and
  never advertises a track on packet_id 0
- the AL-FEC message's entry for a flow -> the track's FEC instance
  (instance 0, encoded as [@!MOQ-FEC-CATALOG] Section
  3.1 specifies): `scheme` from
  `fec_code_id_for_repair_flow`, "reed-solomon" for code point 1 and
  "raptorq" for 3 ([@!MOQ-FEC-BLOCK] Section
  3), `symbolSize` (T) from
  `length_of_repair_symbol`, `sourceSymbols` (K) from
  `maximum_k_for_repair_flow`, `repairSymbols` (P) from
  `maximum_p_for_repair_flow`, and a repair track, named in
  `repairTrack`, whose `packetId` is the packet_id that `repair_flow_id`
  names (Section 8.3).  The converter accepts an
  entry whose `number_of_assets` is 1, whose coding byte is 0x14 and
  whose `fec_code_id_for_repair_flow` is 1 or 3: a source flow of
  several Assets ([@!ISO.23008-1] Clause C.1) is one block sequence
  over the packets of several packet_ids, which no FEC instance of
  [@!MOQ-FEC-CORE] protects (its Section 5.1 protects
  one source track), a flow under any other coding structure,
  `ssbg_mode`, FFSRP_TS or FEC payload ID mode is not one that
  "iso-ssbg1-v1" describes ((#iso-ssbg1-v1)), a session whose message
  names any other code is outside this document and its companions until
  the "MoQ FEC Schemes" registry of [@!MOQ-FEC-CORE] Section
  15.2 lists that code
  ((#atsc-compatibility)), and the conversion of such a flow fails. The
  one
  repair flow the
  one-stage entry names is the track's layer 0, and
  `maximum_p_for_repair_flow` is its P while layer 0 is the only
  published layer, as in a one-stage session of [@!ISO.23008-1],
  whose one repair flow carries the block's whole repair count.
  That field bounds the repair count of a block ([@!ISO.23008-1]
  Clause C.6.3: the maximum allowed number of repair symbols in a
  repair symbol block) where "iso-ssbg1-v1" carries P as the RSB_length
  of every repair packet ((#repair-packet); [@!MOQ-FEC-CORE] Section
  7.5), on
  which every receiver holding the highest layer the converter lists
  (below) fails closed when a packet of that layer, where it is
  above 0, or of a block at or after (in the serial order of
  [@!MOQ-FEC-CORE] Section 7.6) one
  of which it has received a repair
  packet carrying at least the value, carries less than the
  O_i + P_i its catalog derives for that layer, the field itself
  (its Section 7.3.2), so
  the converter, which receives the flow's repair packets before it
  lists the repair track (below), lists it only once it has received
  a repair packet of the flow carrying an RSB_length of at least the
  field of the version it holds, and fails the conversion of a flow
  whose repair packets carry an RSB_length below that field on a
  block at or after, in the serial order of their SS_Start
  ([@!MOQ-FEC-CORE] Section 7.6),
  one of which it has received a repair packet carrying at least the
  field: such a flow is not one
  "iso-ssbg1-v1" describes.  A block before that one whose repair
  packets carry less was generated under the previous total, after
  whose last repair packet a publisher that appends a layer sends
  the raised field (Section 8.3) but which the path, keeping no
  order between the message and the repair flow (Section 5.2.2),
  can deliver after it; and a flow no block of which carries at
  least the field is one the converter never lists.  Such a packet
  of an earlier block, below the `repairSymbols` the catalog gives
  layer 0 (below) where the layers the converter lists above 0 count
  less than the appended one, fails a receiver of the catalog closed
  on nothing: the clause of [@!MOQ-FEC-CORE] Section
  7.3.2 for a packet of a layer's own track
  applies to layers above 0 alone, layer 0's
  coordinates depending on no count, and its anchored clause, which
  anchors a held layer on a block of which the receiver has received
  a repair packet carrying at least that layer's O_i + P_i, for
  layer 0 its `repairSymbols` (the field where the converter lists
  none above 0), treats such a packet as the conforming packet it
  is, every block generated under a total below a layer's O_i + P_i
  preceding, in the serial order of its Section
  7.6, every block generated under
  one at or above it (its Section 7.3.2, which
  has
  a publisher apply a raised total from a block onward in that order
  and lower none), on the repair track the
  converter publishes as on the session's own endpoint, which
  carries the sender's packets and from which the converter
  withholds nothing.
  An RSB_length above the
  field is the append case of the next sentence.  A
  MoQ publisher that appended a layer ([@!MOQ-FEC-CORE] Section
  7.3.2) sends the raised total in that field
  (Section 8.3) while the named flow carries only the P_0 symbols of
  each block ([@!MOQ-FEC-CORE] Section 7.3.1),
  and neither the message nor the MP table describes
  the layers above, so the converter sets `repairSymbols` to
  `maximum_p_for_repair_flow` less the `repairSymbols` of every
  layer above 0 that it lists, and lists a layer it learns from
  provisioning only where provisioning places it, with every other
  layer it lists, above every layer it does not list, the topmost
  layers of the publisher's set: layer 0's `repairSymbols` is then
  the publisher's total below the lowest layer it lists above 0 (the
  whole field where it lists none) and each listed layer's O_i
  ([@!MOQ-FEC-CORE] Section 7.3.1) is the
  publisher's, while listing a
  layer above which lies one the converter does not list would give
  it an O_i that is not the publisher's, which no check detects, and
  an O_i + P_i that its own-track packets generated before the
  append of the layer it does not list fall below (its Section
  7.3.2).  One that lists none publishes the
  whole field, which
  overstates layer 0's count, and the loss tolerance a receiver
  derives from it, by the layers it does not list.  The converter
  keeps the `repairSymbols` it first
  published for a track, and those of every layer it has listed,
  for as long as it publishes the track: a later version of the
  message that raises `maximum_p_for_repair_flow` changes nothing in
  its catalog by itself, since [@!MOQ-FEC-CORE] Section
  7.3.2 forbids
  changing the `repairSymbols` of a published layer while any
  receiver may still be consuming the source track, and says that a
  receiver reading the smaller bound excludes only symbols of layers
  it has not joined.  A layer above 0 that the converter learns from
  provisioning after it published the track, one that provisioning
  places next above the highest layer the converter lists, the
  publisher having appended it after the converter read the field
  with no layer the converter has not learned below it, so that its
  O_i, the total of every layer below it ([@!MOQ-FEC-CORE] Section
  7.3.1), is the total the catalog derives for
  the highest layer
  listed before it, layer 0's `repairSymbols` plus those of every
  layer above 0 listed before it, and the field of the version it
  holds has risen by at least that layer's `repairSymbols`, it
  appends at the next index (its Section
  7.3.2): its symbols' RS_IDs
  run upward from that total, and its O_i + P_i is at most the
  field, which every block generated under the raised total carries.
  The field's rise alone places no layer, a field risen by more than
  a layer's `repairSymbols` counting a layer the converter has not
  learned, which can lie below the learned one.  A layer that
  provisioning does not so place, or whose symbols the field the
  converter first read already counted, it lists only by retiring
  the source encoding and publishing the source track and its repair
  tracks as a separate rendition that lists it, since appending it
  would give it an O_i that is not the publisher's, which no check
  detects, or an O_i + P_i above the wire RSB_length, on which every
  receiver joining it fails closed (that section), while lowering
  layer 0's `repairSymbols` to fit it is the change that section
  forbids.  A
  later version that lowers `maximum_p_for_repair_flow` below the
  total its catalog derives for the highest layer it lists, layer
  0's `repairSymbols` plus those of every layer above 0 it lists, is
  a change that section lets no publisher make, on which a receiver
  holding the highest layer it lists fails closed on the first
  packet of that layer, where it is above 0, or of a block at or
  after, in that serial order, one of which it has received a repair
  packet carrying at least that total, whose RSB_length falls below
  the O_i + P_i its catalog derives for that layer, which is that
  total, and one that no such packet reaches, the check anchored on
  no block it received or, holding that layer alone, reached by no
  repair packet after the change, learns of the change only at the
  next catalog refresh (that section), so the
  converter
  retires the source encoding and
  publishes the source track and its repair tracks as a separate
  rendition carrying the lowered value, as that section has a
  publisher that must retire a layer do; a repair packet whose
  RSB_length falls below that total once the track is published, on
  a block at or after, in that serial order, one of which it has
  received a repair packet carrying at least that total, is the same
  violation and has the converter retire the source encoding in the
  same way, the separate rendition listing the repair track as the
  first listing did, once a repair packet of the flow received after
  that one carries at least the field of the version it then holds,
  as the violating packet, below the field of the version held when
  it arrived, did not.  The
  conversion
  of a flow fails where the FEC instance it would yield fails a rule of
  [@!MOQ-FEC-CORE] Sections 10.1 and
  10.3, or of [@!MOQ-FEC-CATALOG] Section
  5, on which a receiver fails closed: a
  `maximum_p_for_repair_flow` of 0 names no repair flow a catalog can
  publish ([@!MOQ-FEC-CORE] Section 10.1
  requires a `repairSymbols` of at least 1), a
  `maximum_k_for_repair_flow` of 0 names no block (a `sourceSymbols` of
  at least 1), and a `length_of_repair_symbol` below 14 names a symbol
  that protects no MMTP packet under the T - 2 construction of
  (#iso-ssbg1-v1), whose protected packet begins with the 12-octet MMTP
  packet header of Section 3.1 (a `symbolSize` of at least 14 under
  "iso-ssbg1-v1"); an entry that names code point 3 with a
  `length_of_repair_symbol` that is not a multiple of 8 names a T no
  "raptorq" track can carry ([@!MOQ-FEC-BLOCK] Section
  6.1 fixes the Symbol Alignment at 8, which an MMTP
  session, carrying no OTI, does not impose on its symbol length), one
  with `maximum_k_for_repair_flow` above 56403 fails the RaptorQ bound
  of [@!MOQ-FEC-BLOCK] Section 7, and one with
  `maximum_k_for_repair_flow` plus `maximum_p_for_repair_flow` above
  2^24 names an ESI no instance can produce ([@!MOQ-FEC-CORE] Section
  10.3 bounds K + totalP - 1 by 2^24 - 1, a sum the two
  24-bit fields can exceed); and an entry that names code point 1 with
  `maximum_k_for_repair_flow` plus `maximum_p_for_repair_flow` above 255
  names a block no "reed-solomon" instance can hold (the Reed-Solomon
  bound of [@!MOQ-FEC-BLOCK] Section 7, which
  bounds K plus the repair count of every layer).  The
  conversion also fails for a flow whose `repair_flow_id` is 0, the
  signaling flow (Section 3.1), the flow's own packet_id, or the
  packet_id of another track of the session, a value that
  [@!MOQ-MULTICAST] Section 4.1
  requires to denote one sub-flow (a
  repair flow carries a packet_id of its own, [@!ISO.23008-1]
  Clause C.6.3), and for the flows of any two entries that name one
  `repair_flow_id` or list one Asset: two source tracks naming one
  repair track, or two base instances for one track, are shapes no FEC
  instance of [@!MOQ-FEC-CORE] has, a repair packet belonging to the
  instance that the configuration relates to the track it arrived on
  (its Sections 5.1 and
  7.5).  The
  message names the repair flow
  by packet_id without a location, and the MP table does not list it
  ([@!MOQ-MULTICAST] Section 5),
  so the converter lists the repair
  track in the `tracks[]` of each endpoint on whose session it
  receives packets of that packet_id, which is where a receiver
  without the catalog finds them; a repair-only endpoint
  ([@!MOQ-FEC-MULTICAST] Section 4) is one
  the converter learns from provisioning, not from the signaling
- the instance's `interleaveDepthMs`, the ISO protection-window send
  span from
  the first source or repair packet to the last: set only when the
  AL-FEC message's `protection_window_time` or an independently known
  source/repair send schedule supplies that span, as a positive
  integer millisecond upper bound that covers the complete span,
  never rounded down; when the span is unknown, or the message
  signals zero (the size-based case), the converter omits it
- a live service -> `isLive` = true ([@!I-D.ietf-moq-msf]
  Section 5.2.7) on each media track and on its repair track, which
  the converter publishes while it ingests the service
- the source composition/edit-list origin for each synchronized media
  track -> `presentationAnchorTicks`; a converter preserves one
  common presentation origin across audio and video, and does not
  emit zero merely because the source offset was unavailable
- `bitrate` ([@!I-D.ietf-moq-msf] Section 5.2.22) from whatever
  signaling carries it, or from another source, or the conversion of
  that track fails

Flows sharing one (sourceAddress, groupAddress, port) tuple collapse
into a single endpoint whose `tracks[]` array lists them all.  MMT
signaling carries no `networkSource` ([@!MOQ-MULTICAST] Section
4.2).
A converter that adds an AMT network source advertises "driad"
discovery only for a source address whose reverse DNS zone carries an
AMT relay record, and otherwise names a relay service hostname in
`relay` with "dns" discovery ([@!MOQ-MULTICAST] Section
4.2.1).

`timescale`, the group-duration field and `mmtpMode` are required
fields (Section 13.1).  The converter takes `timescale` from
`asset_timescale` in the MP table when `asset_timescale_flag` is 1,
and uses 90 000 Hz when that flag is 0, as specified by
[@!ISO.23008-1] Clause 10.3.9.3.  For each timed
Asset, it obtains the presentation time of each MPU's first AU in
presentation order from the PI document when PI is present;
ISO/IEC 23008-1 Clause 10.5.2.1 says that the MPU timestamp
descriptor is ignored in that case.  Otherwise it decodes each
descriptor's 64-bit NTP `mpu_presentation_time` value
([@!ISO.23008-1] Clause 10.5.2) and does not treat the encoded NTP
integer as a media tick count.  It converts those presentation
instants through the selected asset/media clock, retaining the
authored media timing when NTP fractional quantization does not land
on an integer media tick.  That instant is not `ticks`
(Section 4.4.1) when the MPU has leading pictures: `ticks` is that
instant plus the difference between the authored composition times
(Section 5.1) of the MPU's first AU in decode order and its
earliest-presented AU, converted to the selected timescale as
Section 4.4.1 requires.

The converter derives the group duration from the authored MPU/media
cadence and validates it against those `ticks` values.  It may emit
`groupDurationMs` only when the conversion to the selected timescale
is an exact positive integer tick count; when the cadence is exact
only in ticks it emits `groupDurationTicks`.
The fixed-cadence profile cannot represent a source whose MPU cadence
is not one constant positive duration, so conversion fails rather
than rounding or inventing a cadence.  It sets `mmtpMode` itself.
The AL-FEC message does not name `blockProfile`, which is required on
every FEC instance ([@!MOQ-FEC-CORE] Section
10.1); the converter sets it to "iso-ssbg1-v1",
the profile whose entry carries the coding byte 0x14 that the converter
accepts (Section 8.3; (#iso-ssbg1-v1)).

{#security-considerations}
# Security Considerations

MMT content protection uses Common Encryption (CENC) [@?ISO.23001-7]
which is preserved through MoQ transport.  The MMTP packet and
payload headers are not encrypted by CENC, so receivers, and MMTP
gateways outside MoQ, can inspect packet type, sequence, and
fragmentation metadata without accessing media sample content.  A MoQ
relay treats the object payload, MMTP headers included, as opaque
([@!I-D.ietf-moq-transport] Section 7.8) and never parses MMTP
(Section 6.2).

{#a3sa-signed-region}
## ATSC 3.0 Signed Region (A3SA)

Per [@?ATSC-A360] Section 5.2.2.5, the ATSC 3.0 signing mechanism, whose
certificates the ATSC 3.0 Security Authority (A3SA) administers, covers
signaling messages and MA3 messages (packet type 0x2) but excludes asset
packets (type 0x00 MPU and type 0x03 repair).

Neither [@!ISO.23008-1] nor [@?ATSC-A331] carries the SS_ID inside the
A3SA signed region.  In particular the MMT hint sample does not: neither
its ISO syntax ([@!ISO.23008-1] Clause 8.3.2) nor the ATSC
`MMTHSampleATSC3` syntax ([@?ATSC-A331] Section 7.2.4.2.2.3) has a
Source FEC Payload ID field, and hint samples travel as MPU-mode data
units on the Asset's own packet_id ([@?ATSC-A331] Section 7.2.4.2.3),
that is in asset packets, which A3SA does not sign.  This document
therefore defines no A3SA-authenticated FEC block assignment: block
assignment taken from the trailing Source FEC Payload ID
((#source-fec-payload-id)) of an A3SA verified packet is
unauthenticated.  A receiver that requires authenticated FEC block
assignment MUST obtain it from an integrity mechanism, other than A3SA
signing, whose coverage includes the complete MMTP packet, the trailer
included.  Version 2 of the bc-provenance profile ([@!MOQ-MULTICAST]
Section 7.2) is such a mechanism: its
digest covers the whole UDP payload as transmitted, the Source FEC
Payload ID included.  The same holds for the overlay SS_ID
((#overlay-header-extension)): A3SA signing authenticates neither, and a
receiver that requires authenticated block assignment treats each as
this section requires.

An attacker who can modify the Source FEC Payload ID without detection
could redirect source symbols to incorrect FEC blocks, causing recovery
failures or corrupted output.  On multicast networks without A3SA
verification, receivers SHOULD cross-check the SS_ID against the MMTP
packet_sequence_number to detect obvious tampering (e.g., an SS_ID that
advances further than the packet_sequence_number of the same packet_id,
whereas SS_ID advances by one per FEC source packet, (#iso-ssbg1-v1)).

{#multicast-security}
## Multicast Security

Multicast-specific security considerations (source authentication,
replay protection, AMT relay trust) are defined in
[@!MOQ-MULTICAST] Section 7.

{#iana-considerations}
# IANA Considerations

This document defines the catalog `packaging` value "mmtp"
(Section 13.1), extending the allowed packaging values of the MOQT
Streaming Format [@!I-D.ietf-moq-msf] Section 5.2.4 in the same
manner as [@?I-D.ietf-moq-cmsf].  If a registry of packaging
values is established for that format, this document requests
registration of:

| Value | Description | Reference |
|-------|-------------|-----------|
| "mmtp" | MMTP packets carrying MPU/MFU payloads | This document |

This document requests the registration of the block profile
"iso-ssbg1-v1" ((#iso-ssbg1-v1)) in the "MoQ FEC Block Profiles"
registry that [@!MOQ-FEC-CORE] Section
15.3 creates:

| Block Profile | Admitted Packaging | Reference |
|---------------|--------------------|-----------|
| "iso-ssbg1-v1" | mmtp | This document, (#iso-ssbg1-v1) |

The header extension type 0x8B01 of (#overlay-header-extension) is an
MMTP value, not a MoQ one; [@!ISO.23008-1] Clause 9.2.3 defines no
registry of MMTP header extension types, so its use requires no IANA
action.

This document requests no MoQ message type registrations.  FEC signaling
uses no MoQ control message ([@!MOQ-FEC-CORE] Section
15.1); no document in this suite requests a
control-message codepoint.

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

<reference anchor='ISO.23008-1.AMD1'>
  <front>
    <title>Information technology - High efficiency coding and media delivery in heterogeneous environments - Part 1: MPEG media transport (MMT) - Amendment 1: Signalling of adaptive FEC scheme</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2025' month='May'/>
  </front>
  <seriesInfo name='ISO/IEC' value='23008-1:2023/Amd 1:2025'/>
</reference>

<reference anchor='ISO.23008-10'>
  <front>
    <title>Information technology - High efficiency coding and media delivery in heterogeneous environments - Part 10: MPEG media transport forward error correction (FEC) codes</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2015'/>
  </front>
  <seriesInfo name='ISO/IEC' value='23008-10:2015'/>
</reference>

<reference anchor='ISO.14496-12'>
  <front>
    <title>Information technology - Coding of audio-visual objects - Part 12: ISO base media file format</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2026'/>
  </front>
  <seriesInfo name='ISO/IEC' value='14496-12:2026'/>
</reference>

<reference anchor='ISO.23001-7'>
  <front>
    <title>Information technology - MPEG systems technologies - Part 7: Common encryption in ISO base media file format files</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2023'/>
  </front>
  <seriesInfo name='ISO/IEC' value='23001-7:2023'/>
</reference>

<reference anchor='MOQ-FEC-CORE'>
  <front>
    <title>Forward Error Correction for Media over QUIC: Core Mechanism</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <author initials='M. E.' surname='Fiuczynski' fullname='Marc E. Fiuczynski'>
      <organization>Rutgers University</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-core-00'/>
</reference>

<reference anchor='MOQ-FEC-BLOCK'>
  <front>
    <title>Block FEC Schemes for Media over QUIC: Reed-Solomon and RaptorQ</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-block-codes-00'/>
</reference>

<reference anchor='MOQ-FEC-CATALOG'>
  <front>
    <title>Catalog Binding for Forward Error Correction in Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-catalog-00'/>
</reference>

<reference anchor='MOQ-FEC-MULTICAST'>
  <front>
    <title>Forward Error Correction for Multicast Delivery of Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-multicast-00'/>
</reference>

<reference anchor='MOQ-MULTICAST'>
  <front>
    <title>Multicast Delivery and Endpoint Discovery for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-multicast-02'/>
</reference>

<reference anchor='ATSC-A331' target='https://www.atsc.org/atsc-documents/3312017-signaling-delivery-synchronization-error-protection/'>
  <front>
    <title>Signaling, Delivery, Synchronization, and Error Protection</title>
    <author>
      <organization>ATSC</organization>
    </author>
    <date year='2026' month='February'/>
  </front>
  <seriesInfo name='ATSC' value='A/331:2026-02'/>
</reference>

<reference anchor='ATSC-A360' target='https://www.atsc.org/atsc-documents/3602018-atsc-3-0-security-service-protection/'>
  <front>
    <title>ATSC 3.0 Security and Service Protection</title>
    <author>
      <organization>ATSC</organization>
    </author>
    <date year='2026' month='August'/>
  </front>
  <seriesInfo name='ATSC' value='A/360:2026-08'/>
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

{#change-log}
# Change Log

This appendix is informative.  It is to be removed before
publication as an RFC.

{#changes-since-mmt-01}
## Changes Since draft-ramadan-moq-mmt-01

The FEC draft [@?I-D.ramadan-moq-fec] was split into a core mechanism
[@!MOQ-FEC-CORE] and companion documents [@!MOQ-FEC-BLOCK],
[@!MOQ-FEC-CATALOG] and [@!MOQ-FEC-MULTICAST].  The MMTP block profile
moved into this document, and every citation of the FEC draft was
re-pointed.  The section numbers in the -00 entry below are those of
-01.

- Moved in from draft-ramadan-moq-fec-01: the "iso-ssbg1-v1" block
  profile definition (-01 Sections 5.1, 7.3, 7.4 and 8.3, as the new
  Section 7.1), the Source FEC Payload ID trailer and its relation to
  the FEC Source Info Property (-01 Sections 5.3 and 8.5, as Section
  7.2), the MMTP form of the repair packet (-01 Section 7.1, as Section
  7.3), the keyframe overlay and its 0x8B01 header extension (-01
  Sections 2, 5.1.1, 5.1.2, 6.3.1, 6.3.4 rule 10, 6.4 to 6.4.3, 7.6.6
  and 8.5.1, as Section 7.4), the ISO packet-count meaning of
  `interleaveDepthMs` zero (-01 Sections 2, 5.1, 8.4 and 9, into Section
  7.5, which was Section 7.1), the mmtp encoder constraints (-01 Section
  8.4, into Section 8.1), the ISO single-repair-flow paragraph and the
  catalog-less layer-0 check (-01 Sections 6.3 and 6.3.9, into Section
  8.3), ATSC 3.0 compatibility (-01 Section 12, as the new Section 10),
  the A3SA signed region (-01 Sections 8.5, 8.5.1 and 14.5, as the new
  Section 14.1), the "iso-ssbg1-v1" registration and the 0x8B01 note
  (-01 Sections 15.1 and 15.4, into Section 15), the MMTP capacity
  arithmetic (-01 Appendix B, as Appendix B), the mmtp rendition of CMAF
  content (-01 Section 13, 3893-3900, into Section 1.1; the diagram of
  -01 Section 13 depicts direct protection of a cmaf track under
  "moq-object-v1" and is not carried here) and the FEC terms specific to
  this profile (-01 Section 2, into Section 2).  Section 7.2 OTI
  Signaling of -01 is folded into Section 7.1.

- Section 7.1 states where the profile deviates from [@!MOQ-FEC-CORE]:
  the unit of protection is the MMTP packet, the trailer carries the
  SS_ID and the FEC Source Info Property restates it in the 4-byte form
  naming instance 0 (and a receiver that parses the packet can place a
  symbol by the trailer when the Property is absent, Section 7.2), the
  repair object is an MMTP packet of 12 + 13 + T bytes rather than 13 +
  T, the keyframe overlay is the profile's form of an overlapping
  instance with its overlay SS_ID in the 0x8B01 extension rather than in
  a Property entry, so that overlay membership is read from the
  extension inside the protected packet rather than from the Property
  alone and an overlay recovery counts toward the base instance only
  with an independently determined base SS_ID, `interleaveDepthMs`
  admits zero, and symbol carriage does not apply.

- Duplicates collapsed to one normative copy: the in-band precedence
  rule (Section 8 cites [@!MOQ-FEC-CORE]), the coding-byte paragraph
  (Section 8.3), the prohibition on describing the overlay in the AL-FEC
  message (Section 8.3; Section 7.4.3 keeps the rationale and the
  FFSRP_TS prohibition), and the catalog-less layer-0 anchored check
  (Section 8.3; Sections 10 and 13.2 cite it).  Three further -01
  passages that fall to this document were already stated by
  draft-ramadan-moq-mmt-01 Sections 8 and 8.3 and are collapsed into
  that text rather than moved: the -01 Section 5.2 sentences naming the
  AL-FEC message as the in-band FEC signaling of the mmtp packaging for
  a receiver that consumes the flow without the catalog (Section 8.3;
  Section 8 makes the message optional on a MoQ track), the -01 Section
  8.3 paragraph on the signaling object that carries no source symbol,
  no SS_ID and no ESI and is not counted in K (Section 8), and the -01
  Appendix A.1 sentence that no in-session message is required and that
  a track may carry no AL-FEC signaling object (Section 8). Their
  profile-neutral sentences are kept by [@!MOQ-FEC-CORE] Sections
  5.3 and 10 and
  Appendix E.

- Every citation of the FEC draft is re-pointed: the mechanism to
  [@!MOQ-FEC-CORE], the schemes, their bounds, the OTI derivation and
  the mandatory-to-implement designation to [@!MOQ-FEC-BLOCK], the
  catalog encoding, the worked catalog, the naming convention and the
  unknown-key rules to [@!MOQ-FEC-CATALOG], and the receiver repair
  policy, block classification and repair-only endpoints to
  [@!MOQ-FEC-MULTICAST]; the profile, the trailer, the repair packet and
  the overlay are cited within this document.  Catalog field names
  follow the data model of [@!MOQ-FEC-CORE]: `algorithm` is `scheme`,
  `depends` is `source`, the per-track `fec` field is an array of FEC
  instances, and the "none" scheme is no longer used (a track without
  instances declares no FEC).  [@?RFC6330] is now an informative
  reference, since RaptorQ is specified by [@!MOQ-FEC-BLOCK].
  [@?ATSC-A360] is a new informative reference and [@!MOQ-MULTICAST] is
  cited at its -02 revision.

- Section 1.2 names the document set, Section 2 lists the FEC terms this
  document uses and points at [@!MOQ-FEC-CORE] for the rest, and the
  Abstract and Section 1 say that this document defines the block
  profile, the overlay and the ATSC 3.0 interworking.  Sections 10 to 14
  of -01 are now Sections 11 to 15.

- Sentences that are new rather than moved, listed verbatim with the -01
  text they replace where one exists:

  - This specification defines the mapping of MMT packets to MoQ
    objects, the "iso-ssbg1-v1" block profile under which the Forward
    Error Correction (FEC) mechanism for MoQ protects MMTP packets --
    its source symbols, its Source FEC Payload ID trailer, its repair
    packet and its keyframe overlay -- the derivation of MoQ catalogs
    from MMTP signaling, and compatibility considerations for both ATSC
    3.0 and ARIB STD-B60 systems, including the ATSC 3.0 signed region.

  - FEC: MMT's AL-FEC integrates with MoQ FEC repair tracks per
    [MOQ-FEC-CORE], under the "iso-ssbg1-v1" block profile that this
    document defines (Section 7)

  - Broadcast interworking: ATSC 3.0 A/331 AL-FEC sessions and the ATSC
    3.0 signed region (Sections 10 and 14.1), and ARIB STD-B60 (Section
    11)

  - The last column names the block profile under which the FEC
    mechanism of [MOQ-FEC-CORE] protects tracks of each packaging.

  - "moq-object-v1" is the profile of [MOQ-FEC-CORE] Section
    5.2: each loc or
    cmaf object whose Object Status is Normal occupies whole source
    symbols.

  - "iso-ssbg1-v1" is the profile that Section 7.1 of this document
    defines: each FEC source packet (FEC Type 1) is one source symbol.

  - Both are registered in the "MoQ FEC Block Profiles" registry of
    [MOQ-FEC-CORE] Section 15.3.

  - A publisher that offers CMAF content can also carry it as an mmtp
    track under "iso-ssbg1-v1", where an MPU corresponds to a CMAF
    Fragment (Section 4.2). [reworded from -01 13 3893-3895:
    "Alternatively, the publisher carries the media as an mmtp track
    under iso-ssbg1-v1, where an MPU corresponds to a CMAF Fragment (see
    [MOQ-MMT])"; the alternative it followed, direct protection under
    "moq-object-v1", is [MOQ-FEC-CORE] Section 13.2, and the
    pointer to this document became a pointer to Section 4.2; the two
    sentences that follow are carried verbatim from -01 13 3895-3900
    with the Section 4.1 citation written as a token]

  - Section 1.2, all four sentences: This document is a companion of
    [MOQ-FEC-CORE], which defines the scheme-independent FEC mechanism
    for MoQ and the configuration data model that a catalog carries.
    [MOQ-FEC-BLOCK] specifies the Reed-Solomon and RaptorQ schemes,
    [MOQ-FEC-CATALOG] the catalog encoding of the configuration, and
    [MOQ-FEC-MULTICAST] the delivery of protected tracks over multicast,
    including the receiver repair policy. This document defines the
    "iso-ssbg1-v1" block profile, the part of that set that is specific
    to MMTP packets, and the ATSC 3.0 and ARIB STD-B60 interworking that
    relies on it. [MOQ-MULTICAST] defines multicast endpoint discovery
    and the multicast packet format on which the multicast delivery of
    mmtp tracks rests.

  - The FEC terms of this document -- Source Track, Repair Track, Repair
    Layer, FEC Instance, Source Symbol, Repair Symbol, Source Block,
    SS_ID, SS_Start, SSB_length, RS_ID, RSB_length, Encoding Symbol ID
    (ESI) and Block Profile -- are those of [MOQ-FEC-CORE] Section
    2, and the RS_ID offset O_i and
    per-block repair symbol count P_i of layer i are those of
    [MOQ-FEC-CORE] Section 7.3.1.

  - Under "iso-ssbg1-v1" the following take a form of their own, and the
    remaining terms are specific to this document:

  - Base Instance: Of a source track that a keyframe overlay protects,
    the instance that is not the overlay; of any other source track, its
    only instance. (New definition; -01 used the term without defining
    it. [MOQ-FEC-MULTICAST] Section
    2 carries the same text.)

  - [MOQ-FEC-CORE] Section 5.6 requires
    every source object to carry the FEC Source Info Object Property
    (type 0x11); on an mmtp source object its value is the four-byte
    form of that section, which names instance 0 and carries the
    network-byte-order SS_ID of the base instance, the value of the
    packet's Source FEC Payload ID (Section 7.2); the property is object
    metadata and is not inserted into this payload.

  - A subscriber finds the repair tracks of the rendition it selects
    through the repairTrack of each of that rendition's FEC instances
    and the source fields of its repair tracks ([MOQ-FEC-CATALOG]
    Section 3.2; the data model of [MOQ-FEC-CORE]
    Section 10.2).

  - This section defines that profile, "iso-ssbg1-v1": its source
    symbols, the Source FEC Payload ID trailer, the MMTP form of the
    repair packet, the keyframe overlay and the interleave window.

  - It states where the profile deviates from [MOQ-FEC-CORE], whose
    remaining rules apply unchanged ([MOQ-FEC-CORE] Section
    5.2).

  - The rules of [MOQ-FEC-CORE] apply to a track under this profile with
    the following deviations, which [MOQ-FEC-CORE] Section
    5.2 asks a
    companion profile to state:

  - The unit of protection is the MMTP packet, not the MoQ object: a
    source symbol is formed from one FEC source packet as this section
    specifies, and the Protected Object Unit of [MOQ-FEC-CORE] Section
    5.2 is not used.

  - A source object of an mmtp track carries one source symbol, the FEC
    source packet that is its payload, so SS_IDs advance by one per
    source object.

  - A source packet carries its SS_ID in a 4-byte trailer, the Source
    FEC Payload ID (Section 7.2), which is the canonical carrier.

  - The FEC Source Info Object Property of the object that carries the
    packet restates it in the 4-byte form, which names instance 0
    ([MOQ-FEC-CORE] Section 5.6); the
    Property is object metadata, not part of the protected packet, and
    is not recovered with it.

  - When an object carries a source symbol but no FEC Source Info
    Property, a receiver that parses the packet MAY take the SS_ID from
    the trailer and feed the symbol to the base decoder (Section 7.2),
    a deviation from [MOQ-FEC-CORE] Section
    5.6, under which such an object is
    not a source object; a receiver that does not parse the packet has
    no SS_ID for it and feeds it to no decoder. [new; restates the -01
    5.3 permission (1103-1104) as a deviation in the Section 7.1 list]

  - A repair object is one complete MMTP repair packet of 12 + 13 + T
    bytes (Section 7.3), not the 13 + T byte payload of [MOQ-FEC-CORE]
    Section 7.5.

  - The keyframe overlay (Section 7.4) is this profile's form of an
    overlapping instance ([MOQ-FEC-CORE] Section
    8.4), with two differences from that
    section and from [MOQ-FEC-CORE] Section 5.1: a
    RAP packet's overlay SS_ID travels in an MMTP header extension, not
    in a second entry of the FEC Source Info Property, and the Property
    keeps the 4-byte form, so a receiver learns a packet's overlay
    membership and overlay SS_ID from that extension, which lies inside
    the protected packet (Section 7.4.2), rather than from the Property
    alone; and because a recovered packet carries its overlay SS_ID but
    not its base SS_ID, a base recovery places the packet in the overlay
    instance, whereas an overlay recovery counts toward the base
    instance only where the receiver has determined the packet's base
    SS_ID independently (Section 7.1). [the clauses from "with two
    differences" on are new, restating Sections 7.1, 7.2 and 7.4.2
    against the core's instance-membership rule]

  - interleaveDepthMs admits the value zero, with the ISO packet-count
    meaning of Section 7.5, under the permission of [MOQ-FEC-CORE]
    Section 10.1 for a block profile to give
    zero a meaning of its own.

  - The symbol carriage of [MOQ-FEC-CORE] Section
    6.2, and with it the symbol track and the FEC
    Unit Start Property, does not apply to an mmtp track: its source
    symbols reach a receiver inside the track's own objects or as
    multicast datagrams ([MOQ-MULTICAST] Section
    5), each carrying one whole FEC
    source packet.

  - This profile uses ssbg_mode1, with the one-stage FEC coding
    structure and FEC payload ID mode 0 ([ISO.23008-1] Clause C.1).
    [reworded from -01 7.3: "The iso-ssbg1-v1 block profile (Section
    5.1) uses ssbg_mode1 ..."; the sentence "This subsection specifies
    the source symbols of iso-ssbg1-v1; Section 7.6 specifies those of
    moq-object-v1" is dropped]

  - (Under "raptorq", whose T is a multiple of 8, the least T is
    therefore 16, [MOQ-FEC-BLOCK] Section 6.1.)
    [carried from -01 5.1 688-691, reduced to the iso-ssbg1-v1
    consequence]

  - OTI and sub-blocks: MoQ carries no RaptorQ Object Transmission
    Information (OTI, [RFC6330] Section 3.3) in-session: receivers
    derive it per block from the instance's configuration and the
    block's SSB_length per [MOQ-FEC-BLOCK] Section
    6.1. [-01 mmt 7.2, "from the catalog fec fields"
    reworded]

  - The trailer lies outside the declared MPU payload (Section 5.2) and
    outside the protected packet (Section 7.1).

  - Section 14.1 states why the ATSC 3.0 signing mechanism does not
    authenticate the trailer, and what a receiver that requires
    authenticated block assignment does instead.

  - On an mmtp source object the Property's value is the 4-byte form of
    [MOQ-FEC-CORE] Section 5.6, which
    names instance 0: the sequence number of the source symbol the
    object carries, the same value and the same definition that the
    Source FEC Payload ID trailer of the FEC source packet carries. [-01
    5.3 1034-1039 reworded for the 4-byte form]

  - Both carry the same value and a publisher MUST make them identical,
    on every source object, because the object payload is the whole FEC
    source packet, trailer included. [-01 5.3 1046-1049, two sentences
    merged]

  - No second Property entry conveys the overlay SS_ID: ... [-01 5.3
    1072 "No second Property conveys" reworded for the list form of the
    core]

  - A receiver that parses the packet MAY take the SS_ID from the
    trailer instead, since the packaging delivers it; this is a
    deviation from that section, which has no trailer to fall back on.
    [-01 5.3 1103-1104 plus the deviation clause]

  - The Repair FEC Payload ID carries the fields of the repair object of
    [MOQ-FEC-CORE] Section 7.5 with the
    semantics that section gives them -- SS_Start, RSB_length, RS_ID and
    SSB_length -- and this section defines only the MMTP packet header
    in front of them:

  - A repair object under this profile is therefore 12 + 13 + T bytes
    long, not the 13 + T bytes that [MOQ-FEC-CORE] Section
    7.5 requires of a repair object under
    "moq-object-v1"; a receiver MUST discard a repair object of an mmtp
    track whose payload is not exactly 12 + 13 + T bytes.

  - It reads the Repair FEC Payload ID at byte offset 12, and every
    other rule of that section applies to the fields: a receiver routes
    the packet to the decoder of the instance that the configuration
    relates to the repair track it arrived on, and discards a packet
    whose RS_ID is not less than RSB_length or that fails a bound of the
    instance's scheme ([MOQ-FEC-BLOCK] Section 7).

  - It is this profile's form of an overlapping instance ([MOQ-FEC-CORE]
    Section 8.4).

  - a track under "moq-object-v1" has no overlay, and a catalog that
    declares one for such a track fails the rule of Section 7.4.1. [-01
    7.6.6 2629-2634 condensed]

  - An overlay is a separate FEC instance over the same source track. It
    has its own sourceSymbols (K_overlay) and its own repairSymbols,
    declared on its own instance entry with its own repair track
    ([MOQ-FEC-CATALOG] Section 3.1), and it
    shares the source track's scheme, blockProfile and symbolSize. [-01
    6.4.1: "declared on its own repair track" and "algorithm" renamed]

  - Its priority is independent within 192 to 255 ([MOQ-FEC-CORE]
    Section 10.3, rule 10, and Section
    11), and MAY be numerically lower
    than a base enhancement layer's so that a keyframe repair symbol is
    delivered before an ordinary one. [-01 6.4.1: the range is now the
    core's validation rule 10 and is cited]

  - Overlay ESIs never collide with base ESIs because the two are
    different instances decoded by different decoders; a receiver does
    not feed a repair symbol of one instance to the decoder of the
    other, nor reuse a source symbol's coordinate in one instance as its
    coordinate in the other ([MOQ-FEC-CORE] Section
    5.1). [-01 6.4.1: the two MUST NOTs are the rule
    of [MOQ-FEC-CORE] Section 5.1, now cited rather
    than restated; one normative copy]

  - A source track has at most one overlay, a wire constraint explained
    in Section 7.4.3, and none when its blockProfile is "moq-object-v1";
    the overlay instance's repair track carries no repairLayer. [-01
    6.3.4 rule 10 and 6.4.1 merged]

  - A receiver MUST validate this before starting FEC for an overlay
    instance of the source track, and on any violation MUST fail closed
    as [MOQ-FEC-CORE] Section 10.3 requires for its own
    rules: it reports the offending catalog path, does not start FEC for
    any overlay instance of that source track, and MUST NOT repair the
    catalog by ignoring a track. [-01 6.3.4 preamble 1349-1354 restated
    for rule 10; fail closed is per instance as [MOQ-FEC-CORE] Section
    10.3 scopes it, not per source track as -01 had]

  - An overlay with K_overlay 256 and P_overlay 32 has an RS_ID range of
    0 to 31, an ESI range in a full overlay block of 256 to 287, and
    packets carrying RSB_length 32; it is valid only under "raptorq",
    since 256 + 32 = 288 exceeds 255. [-01 5.1.2 930-938 and 6.4.1
    1813-1815 merged, no longer tied to the -01 worked catalog]

  - It knows that a repair packet belongs to the overlay because it
    arrives on the repair track that the catalog declares for the
    overlay instance of this source track, and that track has its own
    packet_id. [-01 6.4.2: "declares with scope: keyframe" reworded]

  - The instance is therefore fixed by the track the packet arrived on;
    no field of the repair packet distinguishes the two, and a receiver
    does not infer the instance from SS_Start, RSB_length, or
    SSB_length, whose values are only interpretable once the instance is
    known ([MOQ-FEC-CORE] Section 7.5). [-01
    6.4.2: the MUST NOT is the rule of [MOQ-FEC-CORE] Section
    7.5, applied to the MMTP repair packet by
    Section 7.3; now cited rather than restated]

  - The overlay is declared only by the catalog: Section 8.3 forbids
    describing the overlay's repair flow in an AL-FEC message, which
    identifies an FEC source flow by packet_id ([ISO.23008-1] Clause
    C.6.3) and cannot describe the RAP subset that the overlay protects,
    so a receiver that consumes the flow without the catalog uses the
    base instance alone. [-01 8.5.1 3041-3046: the MUST NOT is collapsed
    into the one copy in Section 8.3]

  - The receiver-side half is the repair policy of [MOQ-FEC-MULTICAST]
    Section 6, under which a receiver
    gives a keyframe-bearing base block that in-band decoding leaves
    unrecovered priority unicast repair; its Section
    6.6 states how the two
    combine. [-01 6.4.3: the Section 11.4 and 11.4.6 pointers
    re-pointed]

  - A receiver that does not implement overlays MUST fail closed on a
    catalog that declares one for a track it intends to consume, that is
    on an FEC instance carrying the unknown scope key, and MUST NOT
    ignore the key and consume the source track anyway. [-01 6.4.3: "on
    a fec-repair track carrying" became "on an FEC instance carrying"]

  - scope (string, OPTIONAL): When present, MUST be "keyframe", and
    declares this instance to be the source track's keyframe overlay. It
    is an unknown-key exception (Section 7.4.4). An overlay is defined
    only for a source track under "iso-ssbg1-v1" (Section 7.4). [-01
    5.1.1 816-820: "declares this track" became "declares this
    instance", the member moved from the repair-track entry to the
    overlay's instance object, and "one of the unknown-key exceptions
    below" became an exception this document defines under
    [MOQ-FEC-CATALOG] Section 3.4; the -01 overlay
    sourceSymbols member (821-824) is now the instance's ordinary
    sourceSymbols, Section 7.4.1]

  - The overlay's instance object carries one member that this document
    defines, under the rule of [MOQ-FEC-CATALOG] Section
    3.4 that lets a block profile's document define
    further keys for the tracks it admits, and further exceptions among
    them. [new bridging sentence, Section 7.4.1]

  - This is an unknown-key exception that this document defines (Section
    7.4.1) under [MOQ-FEC-CATALOG] Section 3.4,
    which lets a block profile's document define further exceptions.
    [-01 6.4.3: "one of the unknown-key exceptions of Section 5.1.1"
    re-pointed, since the catalog binding no longer lists scope]

  - [MOQ-FEC-CORE] Section 10.1 admits a
    positive interleaveDepthMs and lets a block profile give the value
    zero a meaning of its own.  Under this profile the field MAY also be
    zero.

  - A publisher uses a zero value only with that ISO
    protection_window_size alternative. [-01 8.4 item 4, 2923-2925
    reworded]

  - An absent field supplies no catalog-signaled span; neither an absent
    nor a zero value supplies an elapsed-time deadline. [-01 5.1 723 and
    mmt-01 7.1 1497-1498 merged]

  - FEC parameters for mmtp-packaged tracks are signaled in the catalog
    fec field, whose encoding [MOQ-FEC-CATALOG] defines (its Section
    3) for the configuration data model of
    [MOQ-FEC-CORE] Section 10, which is
    authoritative for MoQ receivers (that section).

  - the message MUST NOT signal FEC parameters that contradict the
    track's catalog fec instances, and where the two disagree the
    catalog governs, as [MOQ-FEC-CORE] Section
    10 requires of any in-band signaling.

  - When used with MMT packaging, the instance parameters of
    [MOQ-FEC-CORE] Section 10.1, as the catalog
    encodes them ([MOQ-FEC-CATALOG] Section
    3.1), map as follows:

  - scheme: the scheme identifier ([MOQ-FEC-BLOCK] Section
    3) whose [ISO.23008-10] code point the
    MMTP AL-FEC message carries in fec_code_id_for_repair_flow (Section
    8.3)

  - blockProfile: ... REQUIRED on every FEC instance, with no default
    [replaces "REQUIRED when algorithm is not none"]

  - See [MOQ-FEC-CATALOG] for the complete catalog field definitions,
    [MOQ-FEC-CORE] Section 15.2 for the
    scheme registry, and [MOQ-FEC-BLOCK] for the scheme bounds and the
    OTI derivation (its Sections 7 and
    6.1).

  - For FEC block alignment and timing to be deterministic, an mmtp
    publisher MUST, in addition to the encoder constraints of
    [MOQ-FEC-CORE] Section 5.3: [-01 8.4 preamble,
    scoped to mmtp]

  - A zero value is usable only with the ISO protection_window_size
    alternative of Section 7.5. [-01 8.4 item 4]

  - A source track's repair tracks are the track that each of its FEC
    instances names in repairTrack and the tracks that name it in source
    ([MOQ-FEC-CATALOG] Section 3.2; [MOQ-FEC-CORE]
    Section 10.2);
    [MOQ-FEC-CATALOG] Section 6 gives their
    conventional names.

  - A receiver that holds layer 0 under the AL-FEC message alone,
    without the catalog (Section 10), applies the fail-closed check of
    [MOQ-FEC-CORE] Section 7.3.2 with
    maximum_p_for_repair_flow standing for its O_0 + P_0, by that
    check's anchored clause alone: layer 0 has no clause of its own
    track, its O_0 being 0 and its symbols' coordinates depending on no
    published count, so a packet of the flow generated under a previous
    total, which the message can precede (above), fails it closed on
    nothing. [-01 6.3.9 1631-1642 and 1713-1715 and -01 12 3844-3851
    merged into one copy]

  - Layered repair is an extension of [ISO.23008-1] that an ISO AL-FEC
    message cannot express: each FEC source flow has one FEC encoded
    flow, whose one-stage coding structure carries a single
    repair_flow_id ([ISO.23008-1] Clause C.6.3), so only layer 0 maps to
    an ISO repair flow. [-01 6.3 1206-1211, "Under iso-ssbg1-v1" dropped
    as implied]

  - The codes are those of [MOQ-FEC-BLOCK], which specifies two,
    "reed-solomon" (code point 1, mandatory to implement) and "raptorq"
    (code point 3, OPTIONAL) (its Sections 3
    and 10); ... outside this document and
    its companions until the "MoQ FEC Schemes" registry of
    [MOQ-FEC-CORE] Section 15.2 lists that
    code. [-01 12 3836-3843: "this document's to specify" re-pointed to
    the block-codes draft]

  - ... and a receiver that consumes the session without the catalog
    takes them from the message alone, holding the one repair flow as
    layer 0 under the block total the message bounds, as Section 8.3
    specifies. [-01 12 3847-3851: the check itself now lives in Section
    8.3]

  - [MOQ-FEC-CATALOG] adds the per-track fec array of FEC instances and
    the fec-repair and fec-source packaging values (its Sections
    3 and 3.3)

  - fec | OPTIONAL | Array | FEC instances, encoded per
    [MOQ-FEC-CATALOG] Section 3 (Section 8)

  - the AL-FEC message's entry for a flow -> the track's FEC instance
    (instance 0, encoded as [MOQ-FEC-CATALOG] Section
    3.1 specifies): scheme from
    fec_code_id_for_repair_flow, "reed-solomon" for code point 1 and
    "raptorq" for 3 ([MOQ-FEC-BLOCK] Section
    3), ...

  - a session whose message names any other code is outside this
    document and its companions until the "MoQ FEC Schemes" registry of
    [MOQ-FEC-CORE] Section 15.2 lists that
    code (Section 10)

  - The conversion of a flow fails where the FEC instance it would yield
    fails a rule of [MOQ-FEC-CORE] Sections 10.1
    and 10.3, or of [MOQ-FEC-CATALOG] Section
    5, on which a receiver fails closed: ... fails
    the RaptorQ bound of [MOQ-FEC-BLOCK] Section 7
    ... ([MOQ-FEC-CORE] Section 10.3 bounds K + totalP -
    1 by 2^24 - 1 ...) ... (the Reed-Solomon bound of [MOQ-FEC-BLOCK]
    Section 7, which bounds K plus the repair
    count of every layer). [rules 5, 6 and 12 of -01 6.3.4 re-pointed]

  - two source tracks naming one repair track, or two base instances for
    one track, are shapes no FEC instance of [MOQ-FEC-CORE] has, a
    repair packet belonging to the instance that the configuration
    relates to the track it arrived on (its Sections
    5.1 and 7.5).

  - The AL-FEC message does not name blockProfile, which is required on
    every FEC instance ([MOQ-FEC-CORE] Section
    10.1); the converter sets it to
    "iso-ssbg1-v1", the profile whose entry carries the coding byte 0x14
    that the converter accepts (Section 8.3; Section 7.1).

  - The same holds for the overlay SS_ID (Section 7.4.3): A3SA signing
    authenticates neither, and a receiver that requires authenticated
    block assignment treats each as this section requires. [-01 8.5.1
    3055-3057 moved here]

  - An attacker who can modify the Source FEC Payload ID without
    detection could redirect source symbols to incorrect FEC blocks,
    causing recovery failures or corrupted output. [-01 14.5: "it" made
    explicit after the first sentence of 14.5 was merged into the
    paragraph above]

  - This document requests the registration of the block profile
    "iso-ssbg1-v1" (Section 7.1) in the "MoQ FEC Block Profiles"
    registry that [MOQ-FEC-CORE] Section
    15.3 creates:

  - Appendix B, lead sentence, parameter block and the sentence after
    the block: This appendix is informative. It carries the MMTP
    capacity arithmetic of the -01 FEC draft's catalog example, for two
    mmtp tracks with the FEC parameters shown. The block lists each
    track's scheme, K, P, T, groupDurationMs, interleaveDepthMs and
    bitrate in place of the -01 catalog JSON (-01 Appendix B 4415-4497,
    now in [MOQ-FEC-CATALOG]). The video instance is valid only under
    "raptorq", since 625 + 125 = 750 exceeds the "reed-solomon" bound of
    255 ([MOQ-FEC-BLOCK] Section 7); the audio
    instance, with 32 + 8 = 40, is within that bound under either
    scheme.

  - Appendix B, two sentences carried from -01 Appendix B with their
    keyword lowercased because the appendix is informative: "Every
    protected MMTP packet still must fit within `T - 2`
    ((#iso-ssbg1-v1))" (-01: "still MUST fit within `T - 2`"; the rule
    is Section 7.1) and "The publisher must choose the actual
    source-packet count and block boundaries ..." (-01: "The publisher
    MUST choose ...").

  - Appendix B, parameter block: the video and audio lines restate the
    K, P, T, groupDurationMs, interleaveDepthMs and bitrate values of
    the -01 Appendix B catalog, which this document does not carry.

{#changes-since-mmt-00}
## Changes Since draft-ramadan-moq-mmt-00

- Object IDs are numbered per group: 0 for the first object of a group
  and one more for each later object in source order, across subgroups,
  as [@!I-D.ietf-moq-msf] Section 6.2 requires.  In -00 they restarted
  at 0 in each subgroup, so several objects of one group shared an
  Object ID, which [@!I-D.ietf-moq-transport] Section 2.1 does not allow
  (Sections 3.1, 4.1, 4.6, 5, 5.2, and 8). Section 4.6 is retitled
  "Object Identifier Assignment and Reconstruction".
- Section 4.1 states that an mmtp track maps one data unit, not one
  object, to a stream, unlike [@!I-D.ietf-moq-msf] Section 6, and keeps
  the Group and Object numbering of its Sections 6.1 and 6.2.
- The join (Section 6.1, step 3) uses the current-group join of
  [@!I-D.ietf-moq-transport] Section 3.5: SUBSCRIBE with a Next Object
  LOCATION_FILTER and FILL_PARAMETERS with StartGroup = 1. Section 6.2
  is now an informative note.  The relay replay and completeness
  requirements of -00 are removed, because a publisher must not send
  objects outside the requested range ([@!I-D.ietf-moq-transport]
  Section 3.3.1).
- Section 4.4.1: an mmtp publisher, whose Group numbers follow media
  time, does not set the DYNAMIC_GROUPS Track Property to 1, and Section
  6.1 notes that NEW_GROUP_REQUEST cannot shorten a wait for the next
  group.  A publisher that skips Group numbers on a restart signals the
  gap with PRIOR_GROUP_ID_GAP, as [@!I-D.ietf-moq-msf] Section 6.1
  recommends.
- Section 6.1, step 1: the catalog is read through a subscription that
  joins its current group, as [@!I-D.ietf-moq-msf] Section 5 requires,
  and a switching-set disagreement is handled as Section 4.4.2
  specifies.
- Section 4.3: objects of an mmtp track are sent in subgroups, not as
  datagrams.  The permission for a relay to drop a subgroup under
  congestion is removed; [@!I-D.ietf-moq-transport] Section 5.2 governs
  when objects go undelivered.  Section 5.2.1 no longer refers to
  datagram paths: on a lossy path a subsample data unit completes,
  possibly after FEC recovery, or is discarded as incomplete, like any
  other data unit.
- Section 4.4: a repair track carries no `altGroup`, so it is not a
  member of a switching set.  In -00 it carried the `altGroup` of the
  track it protects, although its Groups are FEC blocks, not
  media-time-aligned Groups.
- Catalog initialization data uses the `initDataList` and `initRef`
  fields of [@!I-D.ietf-moq-msf] in place of the per-track `initData`
  field, which the current revisions of [@!I-D.ietf-moq-msf] and
  [@?I-D.ietf-moq-cmsf] do not define.  A receiver may still accept
  `initData` from -00 implementations (Sections 4.5, 6.1, 12, and 12.1).
- Switching sets (Sections 4.4 and 4.4.2): an intra-only mmtp track may
  use a group duration that divides that of the GOP tracks a whole
  number of times.  The exception applies to mmtp tracks only, so cmaf
  members keep the Group number alignment of [@?I-D.ietf-moq-cmsf]
  Section 3.2.  The g * n Group mapping is the alternate mechanism of
  [@!I-D.ietf-moq-msf] Section 4.2, and the 10^-3 tolerance only
  classifies a track as intra-only.
- Section 4.4.2, Table 3: the optional `timescale` field of cmaf tracks
  is attributed to [@!I-D.ietf-moq-msf] Section 5.2.21, not to
  [@?I-D.ietf-moq-cmsf].  A loc switching-set member, like a cmaf one,
  carries a catalog `timescale`, which a TIMESCALE Property on the track
  must equal, so [@!I-D.ietf-moq-loc] is now a normative reference.  A
  track entry without `packaging` is malformed.
- Section 8.3: the AL-FEC message carries in
  `fec_code_id_for_repair_flow` the [@!ISO.23008-10] Table 1 code point
  of the track's algorithm: 3 for "raptorq" and 1 for "reed-solomon".
  Sections 7 and 8.1 follow [@?I-D.ramadan-moq-fec], which now fully
  specifies "reed-solomon" and makes it the mandatory-to-implement
  scheme.  RaptorQ is optional there.  Section 7 states that neither the
  MMT AL-FEC framework nor [@?ATSC-A331], which uses it for MMTP
  sessions, requires a particular code, so the codes are those
  [@?I-D.ramadan-moq-fec] specifies. [@!ISO.23008-10] is now a normative
  reference.  The message's `length_of_repair_symbol` carries the
  track's `symbolSize`, which Section 12.2 reads back, and
  `num_of_repair_symbol_per_packet` is 1; its
  `maximum_p_for_repair_flow` carries the RSB_length of the track's FEC
  instance, the block total, which Section 12.2 reads back as
  `repairSymbols` less the layers above 0 it lists, listing a layer it
  learns from provisioning only where provisioning places it, with every
  other listed layer, above every layer it does not list, keeping the
  value it first published for a track, and those of the layers it has
  listed, across later versions of the message that raise the field,
  retiring the source encoding under one that lowers the field below the
  total its catalog derives for the highest layer it lists
  ([@?I-D.ramadan-moq-fec] Section 6.3.9), appending at the next index a
  layer it learns from provisioning after it published the track only
  where provisioning places it next above the highest layer it lists
  with no unlearned layer below it, the field's rise alone placing none,
  and listing one provisioning does not so place, or whose symbols the
  field it first read already counted, only by retiring the source
  encoding and publishing a separate rendition.  Section 12.2 states
  that the field is a bound in [@!ISO.23008-1] where "iso-ssbg1-v1"
  carries P as every repair packet's RSB_length, lists the repair track
  only once a repair packet of the flow carries at least the field, and
  fails the conversion of a flow whose repair packets carry an
  RSB_length below the field on a block at or after, in the serial order
  of [@?I-D.ramadan-moq-fec] Section 7.5, one received carrying at least
  the field, since a publisher that appends a layer sends the new
  version only after the last repair packet generated under the previous
  total (Section 8.3) while the path keeps no order between the message
  and the repair flow (Section 5.2.2); once the track is published such
  a packet, below the total its catalog derives for the highest layer it
  lists, retires the source encoding, the separate rendition listing the
  repair track again as the first listing did; a previous-total packet
  of an earlier block fails a receiver of the catalog closed on nothing,
  the own-track clause of [@?I-D.ramadan-moq-fec] Section 6.3.9 applying
  to layers above 0 alone.  Section 8.3 sets the entry's
  `number_of_assets` to 1, the one Asset being the source track's.
  Section 12.2 accepts only an entry with a `number_of_assets` of 1, the
  coding byte 0x14 and code point 1 or 3, and fails the conversion of a
  flow whose `fec` object would fail a catalog rule of
  [@?I-D.ramadan-moq-fec] Sections 5.1 and 6.3.4 (a maximum K or maximum
  P of 0, a symbol length below 14, a RaptorQ symbol length that is not
  a multiple of 8, a RaptorQ maximum K above 56403 or maximum K plus
  maximum P above 2^24, a Reed-Solomon maximum K plus maximum P above
  255), of one whose repair flow is packet_id 0, the flow's own
  packet_id or the packet_id of another track of the session, and of the
  flows of two entries that name one repair flow or list one Asset.
- Section 1.1: the CARP row is removed.  CARP (draft-law-moq-carp-00)
  has expired, and its content continues as [@?I-D.ietf-moq-cmsf]. The
  FEC column names the [@?I-D.ramadan-moq-fec] block profile for each
  packaging, including "moq-object-v1" for loc and cmaf tracks.  The
  section names MSF, LOC and CMSF with their references, and the cases
  that suit each packaging are no longer stated with BCP 14 keywords.
- Sections 12.2 and 12.3 and Appendix A of -00 (the S-TSID conversion
  example): the S-TSID conversion of -00 is removed, and this appendix
  of changes is now Appendix A.  This document targets MMTP services and
  not ROUTE, so Section 12.2 now derives the catalog from MMTP
  signaling, the MP table and the AL-FEC message, there is no export to
  broadcast signaling, and the Abstract, Section 1, Section 2 and
  Section 7 no longer name S-TSID.  Section 7.2 no longer cites the
  S-TSID `fecOTI` attribute and says the AL-FEC message carries no OTI,
  and the Section 8.1 `algorithm` rule reads the code point from
  `fec_code_id_for_repair_flow` alone, with no ROUTE-ingest case.
- Sections 4.4.2 and 12.1: the example catalogs carry the fields that
  [@!I-D.ietf-moq-msf] requires.
- Section 13: a MoQ relay treats MMTP headers as opaque object payload.
- Editorial: abbreviations such as ISOBMFF, SSM, ASM, AMT, ABR, GOP and
  OTI are expanded, and Section 2 defines AU.  Section 1 says "FEC"
  instead of "Unified FEC".  Capitalized words that are not BCP 14
  keywords (NOT, LOW, NO) are lowercased.  Section 3.1 cites [@?RFC5905]
  for the NTP short format, Section 9 cites [@?RFC9706] for TreeDN, and
  Section 13 cites [@?ISO.23001-7] for Common Encryption.  Section 14
  uses the name "MOQT Streaming Format".
- [@!ISO.14496-12] (ISOBMFF) is a normative reference, and
  [@!ISO.23008-10] is dated.
- References to the companion drafts point to their -01 revisions.

{#symbol-capacity-example}
# MMTP Symbol Capacity Example

This appendix is informative.  It carries the MMTP capacity arithmetic
of the catalog example of draft-ramadan-moq-fec-01
([@?I-D.ramadan-moq-fec]), Appendix B of that revision, as a
historical example: its parameters are the ones shown
here, and are not those of the worked catalog of [@!MOQ-FEC-CATALOG].

~~~
video: scheme raptorq, K 625, P 125, T 1000,
       groupDurationMs 1000, interleaveDepthMs 1000,
       bitrate 4990000 bit/s
audio: scheme raptorq, K 32, P 8, T 512,
       groupDurationMs 1000, interleaveDepthMs 1000,
       bitrate 128000 bit/s
~~~

The video instance is valid only under "raptorq", since 625 + 125 = 750
exceeds the "reed-solomon" bound of 255 ([@!MOQ-FEC-BLOCK] Section
7); the audio instance, with 32 + 8 = 40, is
within that bound under either scheme.

Parameter consistency: both tracks use one-second MMTP groups (one MPU
per MoQ Group), and each has a 1000 ms source/repair send-span budget.
The group duration does not determine the FEC partition.  A worked
capacity check must include the MMTP and MPU-mode headers, not only the
media bitrate.  With no MMTP header extension, a timed FT=2 packet has
the following media capacity, depending on whether it starts a data unit
(Section 5.2):

~~~
FI=0 or FI=1: T - 2 (length) - 12 (MMTP) - 8 (MPU) - 14 (DU) = T - 36
FI=2 or FI=3: T - 2 (length) - 12 (MMTP) - 8 (MPU)           = T - 22
~~~

The source packet also carries a 4-byte Source FEC Payload ID on the
wire, outside the protected packet and therefore outside these symbol
budgets ((#source-fec-payload-id)).  FT=0/FT=1 metadata consumes
source packets but does not carry sample bytes, and any MMTP extension
consumes additional space.  Every protected MMTP packet still must fit
within `T - 2` ((#iso-ssbg1-v1)).  Using the larger continuation
capacity gives a media ceiling, not a packetization plan:

- Video: 4,990,000 bit/s x 1.0 s / 8 = 623,750 bytes of media per
  one-second group.  `K x (T - 22) = 625 x 978 = 611,250` bytes is an
  upper bound on the media capacity of one full block.  The media
  therefore needs at least `ceil(623,750 / 978) = 638` source packets
  and at least two K=625 blocks; MMTP metadata, fragmentation, and
  authored packet boundaries can require more.  Repair overhead is `P /
  K = 125 / 625 = 20%`.

- Audio: 128,000 bit/s x 1.0 s / 8 = 16,000 bytes of media per group;
  the upper-bound capacity of one full block is `K x (T - 22) = 32 x 490
  = 15,680` bytes.  The media therefore needs at least `ceil(16,000 /
  490) = 33` source packets and at least two K=32 blocks; packetization
  and metadata can require more.  Repair overhead is `P / K = 8 / 32 =
  25%`.

The publisher must choose the actual source-packet count and block
boundaries so that every packet, including FT=0 and FT=1 metadata, fits
the selected symbol size and every block's repair fields describe the
actual `(SS_Start, SSB_length)` partition.  These calculations are
capacity examples, not a rule that one FEC block equals one Group.
