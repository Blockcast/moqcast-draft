%%%
title = "Multicast Delivery and Endpoint Discovery for Media over QUIC"
abbrev = "MoQ Multicast"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
keyword = ["multicast", "MoQ", "AMT", "SSM", "TreeDN"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-multicast-00"
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

This document specifies multicast delivery mechanisms and catalog-based
endpoint discovery for Media over QUIC (MoQ).  It defines how MoQ
sessions integrate with IP multicast (SSM, ASM), Automatic Multicast
Tunneling (AMT), and TreeDN for scalable live streaming.  The
specification includes a multicast catalog extension for endpoint
discovery and multi-path delivery across TV, mobile, and browser
platforms.  All multicast delivery uses MMTP packets, the same packet
format used on MoQ QUIC streams and datagrams.  A manifest-based
content-authentication profile protects multicast delivery.

{mainmatter}

# Introduction

Unicast delivery, including Media over QUIC (MoQ)
[@!I-D.ietf-moq-transport], replicates a stream per receiver; IP
multicast replicates it in the network.

This document specifies how MoQ integrates with IP multicast to
combine the scalability of multicast with the reliability and
signaling of QUIC:

1. **Delivery paths**: Platform-specific multicast reception for
   TV, mobile, and browser clients
2. **Catalog extension**: A container-agnostic multicast endpoint
   discovery mechanism for MoQ catalogs [@!I-D.ietf-moq-msf]
3. **MMTP wire format**: All multicast delivery uses MMTP packets --
   the same packet format used on MoQ QUIC streams and datagrams
   (Section 5).
4. **Multi-path delivery**: Combining MoQ unicast and multicast for
   seamless failover and FEC symbol deduplication

MoQ relays MAY operate as TreeDN [@?RFC9706] nodes for hierarchical
distribution.

## Multicast as Supplement to MoQ Unicast

Multicast delivery as defined in this document is a supplement to
MoQ/QUIC unicast.  Subscribers MUST establish a MoQ session first
to receive the catalog, negotiate parameters, and receive initial
media.  Multicast MAY then be used as an optimized delivery path
for ongoing media data.  This ensures that codec configuration is
available before multicast reception begins.

Exception: MMTP-packaged streams [@!MOQ-MMT] delivered
via ATSC 3.0 broadcast or native SSM are self-describing and MAY
operate as unidirectional data streams without a MoQ session.  MMTP
carries per-packet routing (packet_id), timing (timestamp),
sequencing (Packet Sequence Number), FEC framing (FEC Type, FEC
payload IDs), and signaling (PA, MPI messages) natively.  ATSC 3.0 and ARIB
STD-B60 receivers consume MMTP over SSM as their native delivery
path.

# Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
and "OPTIONAL" in this document are to be interpreted as described
in BCP 14 [@!RFC2119] [@!RFC8174] when, and only when, they appear
in all capitals, as shown here.

**SSM**: Source-Specific Multicast [@!RFC4607]

**AMT**: Automatic Multicast Tunneling [@!RFC7450]

**DRIAD**: DNS Reverse IP AMT Discovery [@!RFC8777]

**TreeDN**: Tree-based Content Delivery Network [@?RFC9706]

**MMTP**: MMT Protocol -- the packet layer of MPEG Media Transport
([@!ISO.23008-1] Clause 9; [@!MOQ-MMT] Section 3).

# Delivery Paths

MoQ content can reach receivers via multiple delivery paths depending
on platform capabilities:

| Client Type | Multicast Path |
|-------------|----------------|
| Native (TV, mobile) | SSM direct via OS multicast API |
| Native (no multicast) | AMT tunneling over UDP [@!RFC7450] |
| Browser with UDP socket access (e.g., [@?WICG-DirectSockets]) | SSM/AMT |
| Browser (standard) | MoQ/WebTransport (unicast) |

Both native SSM and AMT tunneling require UDP socket access.
MoQ/WebTransport is the universal fallback and requires no
special platform capabilities.

Broadcast receivers (ATSC 3.0, ARIB STD-B60) consume MMTP streams
natively over RF tuner hardware.  MoQ integration occurs at the
gateway/head-end level via TreeDN [@?RFC9706] and AMT [@!RFC7450] /
DRIAD [@!RFC8777].

Multiple transports MAY be available for a given stream.  When more
than one delivery path is available, receivers SHOULD prefer, in
order: tuner-based broadcast reception (where tuner hardware exists),
native SSM, AMT tunneling, and finally MoQ/QUIC unicast.  Local
policy MAY override this order.  Within tuner-based reception,
receivers SHOULD prefer Single Frequency Network (SFN) diversity
reception, where deployed, over single-transmitter reception.

# Multicast Catalog Extension

For tracks available via multicast, the MoQ catalog includes a
top-level `multicast` field containing an `endpoints` array for
endpoint discovery.

The catalog is the MSF catalog track, named `catalog`
([@!I-D.ietf-moq-msf] Section 5; [@!MOQ-MMT] Section 12).

## Multicast Endpoint Format

The `multicast` field is a root-level extension member of the MSF
catalog; the catalog envelope for this suite is described in
[@!MOQ-MMT] Section 12.  [@!I-D.ietf-moq-msf] Section 5 permits
producers to add fields and requires parsers to ignore fields they
do not understand: parsers that do not support multicast MUST
ignore it.

The `multicast` field contains an `endpoints` array listing one or
more multicast groups.  A single-endpoint deployment uses a
one-element array:

~~~ json
{
  "multicast": {
    "endpoints": [{
      "sourceAddress": "198.51.100.10",
      "groupAddress": "232.0.10.1",
      "port": 8000,
      "tracks": [
        { "name": "video",        "packetId": 1 },
        { "name": "video/repair", "packetId": 2 },
        { "name": "audio",        "packetId": 3 },
        { "name": "audio/repair", "packetId": 4 }
      ],
      "bandwidth": 6500000
    }]
  }
}
~~~

Multi-group deployments (e.g., per-quality ABR tiers or separate
audio/video groups) use multiple elements:

~~~ json
{
  "multicast": {
    "endpoints": [
      {
        "sourceAddress": "10.0.0.1",
        "groupAddress": "232.1.1.1",
        "port": 5004,
        "tracks": [
          { "name": "video",        "packetId": 1 },
          { "name": "video/repair", "packetId": 2 }
        ]
      },
      {
        "sourceAddress": "10.0.0.1",
        "groupAddress": "232.1.1.2",
        "port": 5004,
        "tracks": [
          { "name": "audio", "packetId": 3 }
        ]
      }
    ],
    "networkSource": [{
      "type": "amt",
      "discovery": "driad",
      "relay": "amt.example.com"
    }]
  }
}
~~~

The `multicast` object contains the following members:

**endpoints** (array of objects, REQUIRED): One or more multicast
  endpoint objects as defined below.  The array MUST NOT be empty.

**networkSource** (array of objects, OPTIONAL): Network delivery
  configuration applying to all endpoints; see Section 4.2.

**auth** (object, OPTIONAL): Content authentication configuration
  for the bc-provenance profile; see Section 7.2.

Endpoint field definitions:

**sourceAddress** (string, OPTIONAL): SSM source IP address per
  [@!RFC4607].  Its presence selects SSM and its absence Any-Source
  Multicast (ASM).

**protocol** (string, OPTIONAL): "ssm" or "asm", restating that
  mode.  An endpoint where it disagrees with `sourceAddress` is
  ignored (see below).

**groupAddress** (string, REQUIRED): Multicast group address.

  - SSM range: 232.0.0.0/8 (IPv4), ff3x::/32 (IPv6)
  - ASM range: 224.0.0.0/4 (IPv4), ff0x::/16 (IPv6)

**port** (integer, REQUIRED): UDP port number.

**tracks** (array, REQUIRED): Tracks available on this endpoint.
  Each element is an object with the following fields:

  - **name** (string, REQUIRED): Track name corresponding to the
    track identifier used in the MoQ catalog.
  - **packetId** (integer, REQUIRED): MMTP packet_id used for
    packet-level track routing on multicast.  Maps directly to the
    Packet ID field in the MMTP header (Section 3.1 of
    [@!MOQ-MMT]).  The value is an integer in the range 1..65535.
    Values MUST be unique within an
    (sourceAddress, groupAddress, port) tuple.  packet_id 0 is
    reserved for the MMTP signaling flow ([@!MOQ-MMT] Section 3.1),
    which, when present, arrives on the same tuple as the media; a
    publisher MUST NOT advertise it for a track.

**bandwidth** (integer, RECOMMENDED): Aggregate bandwidth of this
  endpoint in bits per second, defined as the sum of the UDP payload
  bitrates of all tracks carried on the endpoint, including repair
  tracks; IP/UDP header overhead is excluded.  Publishers SHOULD
  include bandwidth to enable capacity-aware join decisions.
  Subscribers SHOULD check available network capacity before joining
  high-bandwidth groups.

**networkSource** (array of objects, OPTIONAL): Network delivery
  configuration for this endpoint; see Section 4.2.

Each (sourceAddress, groupAddress, port) multicast tuple MUST be
associated with at most one MoQ namespace.  Publishers requiring
multiple independent streams MUST use distinct multicast groups or
ports.

Receivers MUST ignore endpoints whose fields are mutually
inconsistent -- for example, a `protocol` of "ssm" with
`sourceAddress` omitted, a `sourceAddress` present with `protocol`
of "asm", or a `groupAddress` outside the multicast address space.
Receivers MUST likewise ignore an endpoint that lists a track
`packetId` outside the range 1..65535, including 0, the MMTP
signaling flow.

Subscribers receiving a catalog with multicast endpoints MAY
auto-connect to the multicast group when multicast APIs are
available and multicast delivery is preferred (UDP socket access,
native or AMT).  Multicast joins create
IGMP/MLD state on intermediate routers; subscribers SHOULD only
join when multicast provides a concrete benefit over unicast.

Joining an SSM endpoint requires source-specific group membership
signaling: receivers MUST use IGMPv3 [@!RFC3376] (IPv4) or MLDv2
[@!RFC3810] (IPv6) to convey (S,G) joins.  Earlier protocol
versions (IGMPv2/MLDv1) cannot express source-specific joins; if
the receiver's network segment operates at an earlier version (for
example, due to an IGMPv2 querier or snooping switch on the
segment), SSM joins fail silently.  Receivers SHOULD detect the
absence of multicast data following a join and fall back to
MoQ/QUIC unicast (Section 6).

During multicast join (which may take 1-3 seconds for IGMP/MLD),
subscribers SHOULD continue receiving via MoQ/QUIC.  Once multicast
data arrives, subscribers switch to the multicast path.

If multicast reception fails or degrades, subscribers fall back
to MoQ/QUIC unicast per Section 6.

Receivers SHOULD implement hysteresis to prevent flapping between
multicast and unicast paths.  Switch away from multicast after
sustained loss or consecutive FEC block failures; switch back only
after multicast reception is stable for a sufficient period.
Specific thresholds are implementation-defined and SHOULD be
tunable.

## Network Source Types

The `networkSource` field is an array of network-source objects
describing how subscribers can reach the multicast stream when
native IP multicast routing is not available.  It MAY appear at the
`multicast` level (applying to all endpoints) or on individual
endpoints; a single source is expressed as a one-element array.

Each network-source object contains:

**type** (string, REQUIRED): Delivery technology identifier.

Defined types:

### AMT (Automatic Multicast Tunneling)

~~~ json
{
  "networkSource": [{
    "type": "amt",
    "relay": "198.51.100.1",
    "discovery": "driad"
  }]
}
~~~

**relay** (string, OPTIONAL): AMT relay address (IP or hostname).

**port** (integer, OPTIONAL): UDP port on which the AMT relay
  accepts requests.  When absent, the IANA-assigned AMT port (2268,
  [@!RFC7450]) is used.

**discovery** (string, OPTIONAL): AMT relay discovery method.

  - "driad": DNS Reverse IP AMT Discovery per [@!RFC8777].
    Subscribers query the source IP's reverse DNS for AMT relay
    records.  This is the RECOMMENDED discovery method.
  - "manual": Relay address is provided in the `relay` field.

Subscribers SHOULD attempt relay discovery in this order:

1. Use `relay` directly if provided
2. Use DRIAD discovery on the SSM source IP if `discovery` is
   "driad" or omitted
3. Fall back to MoQ/QUIC unicast

Note: DRIAD requires TYPE260 reverse DNS records on the source IP.
DRIAD relay addresses are typically anycast -- subscribers connect
to the topologically nearest relay without additional configuration.
Publishers without reverse DNS control SHOULD provide the `relay`
field directly.

### ATSC 3.0 (Broadcast Television)

~~~ json
{
  "networkSource": [{
    "type": "atsc3",
    "frequency": 533000,
    "plpId": 0,
    "serviceId": 1,
    "slsUri": "https://example.com/atsc3/sls/service1.xml"
  }]
}
~~~

**frequency** (integer, REQUIRED): RF center frequency in kHz.

**plpId** (integer, OPTIONAL): Physical Layer Pipe ID.
  Defaults to 0 (base PLP).

**serviceId** (integer, OPTIONAL): Service ID within the
  broadcast multiplex.

**slsUri** (string, OPTIONAL): URI for Service Layer Signaling (SLS)
  bootstrap.  Enables receivers joining via IP (not RF) to acquire
  the full ATSC 3.0 SLS including S-TSID with FEC parameters.

Receivers with ATSC 3.0 tuner hardware can receive the stream
directly over RF.  MoQ subscribers without tuner hardware ignore
this networkSource type.

### Multiple Network Sources

When a stream is available via multiple delivery technologies, the
`networkSource` array lists one element per technology:

~~~ json
{
  "networkSource": [
    { "type": "amt", "relay": "198.51.100.1", "discovery": "driad" },
    { "type": "atsc3", "frequency": 533000, "plpId": 0 }
  ]
}
~~~

Subscribers select the highest-priority available source per the
transport hierarchy defined in Section 3.

# Multicast Packet Format

All multicast delivery uses MMTP packets.  Each UDP datagram carries
one MMTP packet -- the same packet format used on MoQ QUIC streams
and datagrams.  MMTP provides track routing (packet_id), send
timestamps, sequencing (packet_sequence_number), FEC framing (FEC
Type and the Source/Repair FEC Payload IDs) and random access
signaling (RAP flag) in its packet header, and fragmentation (FI) in
the MPU-mode payload header ([@!MOQ-MMT] Sections 3.1 and 4.2); FEC
configuration, including the RaptorQ OTI, comes from the catalog
([@!MOQ-FEC] Section 4.2).

Frame-sized LOC [@?I-D.ietf-moq-loc] or CMAF [@?I-D.ietf-moq-cmsf]
objects exceed a UDP datagram; the MMTP MPU-mode payload format
fragments media into MTU-sized packets ([@!ISO.23008-1]
Clause 9.3.2; [@!MOQ-MMT] Section 5.2), so multicast carriage uses
MMTP regardless of a track's unicast packaging.

No additional multicast framing, encapsulation, or header format is
needed.  The MMTP packet format is defined in [@!ISO.23008-1]
Clause 9.2, as profiled in [@!MOQ-MMT] Section 3.1.

This design means the same MMTP packet can be delivered via four
transports without modification:

| Transport | Encapsulation |
|-----------|---------------|
| Reliable QUIC stream | MMTP packet as MoQ stream object |
| QUIC datagram | MMTP packet as MoQ datagram object |
| Multicast QUIC | MMTP packet as multicast QUIC DATAGRAM object |
| Multicast UDP | MMTP packet as UDP datagram |

Receivers on multicast demultiplex packets using the MMTP packet_id
field, which maps to the `packetId` assigned in the multicast
catalog endpoint (Section 4.1).  A receiver MUST NOT deliver to any
media or repair decoder a packet whose packet_id is not advertised
for a track, for the (sourceAddress, groupAddress, port) tuple on
which the packet arrived, by an endpoint that the receiver has not
ignored under Section 4.1.  Packets of the MMTP signaling flow
(packet_id 0) are handled per [@!MOQ-MMT] Section 3.1.  FEC source
and repair packets are distinguished by the MMTP FEC Type field
([@!MOQ-MMT] Section 3.1).

The Multicast QUIC row corresponds to [@?QUIC-MULTICAST], which adds
QUIC's per-packet AEAD and integrity.  The mapping of MMTP packets
onto its DATAGRAM frames, and the use of [@!MOQ-FEC] on that channel,
are specified in [@!MOQ-FEC] Section 11.3.

# Multi-Path Delivery

The same media content (source and repair) can be transmitted over
both MoQ unicast (QUIC/WebTransport) and multicast (UDP/SSM/AMT)
paths simultaneously.  Because the same MMTP packets are used on all
transports, receivers can combine symbols from any path for FEC
recovery [@!MOQ-FEC].

When symbols arrive from multiple paths simultaneously, receivers:

1. MUST deduplicate symbols using (SBN, ESI) as the unique key
   within one FEC instance ([@!MOQ-FEC] Section 6.4.1): a source
   track's base instance together with all of its repair layers,
   or its keyframe overlay
2. MAY combine source and repair symbols received on different
   paths in either direction: source symbols via multicast with
   repair symbols via MoQ/QUIC, or source symbols via reliable
   MoQ/QUIC with repair symbols via lossy multicast -- skipping
   FEC decoding when all source symbols arrive reliably

Multicast-to-unicast failover: if multicast reception fails,
subscribers fall back to MoQ/QUIC unicast by subscribing with the
Largest Object filter (to resume at the live edge) or the Next Group
Start filter (to resume at the next group boundary) per
[@!I-D.ietf-moq-transport].  No coordinate mapping between multicast SBN and MoQ group_id is
needed -- the relay provides the current position.  Failover replaces
the multicast path; it is distinct from per-block unicast repair
(Section 6.2), which leaves the multicast subscription in place.

## Packaging Negotiation

Packaging is advertised per track in the catalog, and a subscriber
subscribes by name to the tracks whose packaging it supports.  The
`altGroup` catalog field ([@!I-D.ietf-moq-msf] Section 5.2.12,
profiled in [@!MOQ-MMT] Section 4.4) groups alternatives of the same
content in different packaging formats.

## Per-Block Unicast Repair

A multicast or AMT receiver repairs every FEC block in-band from the
repair symbols it receives on its multicast paths.  For a block that
in-band FEC leaves unrecovered at its FEC deadline, a receiver that
holds a MoQ session (Section 1.1) applies the receiver repair policy
of [@!MOQ-FEC] Section 11.4, which repairs a keyframe-bearing block
by a standalone FETCH [@!I-D.ietf-moq-transport] of the repair-track
group numbered with the block's SBN.  The receiver derives the SBN
from the Source FEC Payload IDs of multicast packets, so no
coordinate mapping is needed, and the returned symbols are
deduplicated per item 1 of Section 6.  A receiver without a MoQ
session cannot request unicast repair; it relies on in-band FEC and,
where published, the keyframe overlay ([@!MOQ-FEC] Section 6.4).

A FETCH for a repair-track group that the relay no longer retains
fails or returns none of the group's objects, and the receiver then
treats the block as unrecoverable.  How long a relay retains
repair-track groups is relay policy.

# Security Considerations

## Multicast Security

SSM inherently limits traffic to authorized sources via (S,G)
filtering.  Receivers MAY detect replayed packets by tracking the
MMTP Packet Sequence Number per packet_id and discarding duplicates
and packets outside a bounded reordering window.  For AMT, trust is
delegated to the relay per [@!RFC7450].

## Content Authentication

Multicast UDP delivery lacks the integrity protection that QUIC
provides on unicast paths.  This section defines "bc-provenance", a
manifest-provenance authentication profile.  The publisher
computes, per MoQ group per protected track, an ordered digest
structure over the group's objects; signs its root with a dedicated
broadcast Ed25519 key [@!RFC8032]; and publishes the signed
manifest on a dedicated MoQ track.  Receivers verify each object --
received or FEC-recovered -- against the group root before admitting
it to reassembly and decode.  Verification cost is one signature
verification per group; all digests use BLAKE3 [@?BLAKE3].
Per-packet signatures suit only low-rate signaling flows; media
tracks use this profile.

### Manifest Track

The publisher publishes one manifest object per media group,
group-aligned: the manifest object authenticating group N of the
media track is published in group N of the manifest track.  The
manifest track is a plain sibling track named by the catalog -- it
carries no role suffix and is not part of any switching set.  The
catalog carries the pointer to the manifest track and the profile
parameters (Section 7.2.5); it never carries the digests
themselves.

### Manifest Content

A manifest is an ordered sequence of per-object entries, each
binding:

- **object_id**: the explicit source-symbol identity assigned at
  encode time.  `object_id` values MUST be unique within the
  group but need not be contiguous or start at zero.
- **digest**: the object's leaf digest -- a keyed BLAKE3-256 over its
  authenticated bytes (Section 7.2.4), domain-separated with
  `authScope` and computed exactly as in Section 7.2.9.
- **length**: the length of the authenticated bytes in octets.

The entry sequence is followed by a group-close record binding
(group_id, object_count), and by the signature.  The on-wire encoding
of the manifest object, of the leaf digest, and of the value the
signature covers is specified in Section 7.2.9 (Canonical Encoding).

With `compaction` "merkle", the per-object entries are the leaves
of a binary Merkle tree and the signature covers the tree root; a
receiver verifies an object by hashing its authenticated bytes and
checking an O(log n) inclusion path against the root.  With
`compaction` "none", suitable for small groups, the signature
covers the flat digest list directly.

### Signature Context Binding

The signature MUST NOT cover the bare root.  It covers the signed
message of Section 7.2.9, which binds the root (or, with
`compaction` "none", the flat digest list) to its context: the
broadcast namespace, track name, group_id, object-id range, key
epoch, manifest format version, and the track's catalog-advertised
codec, timing, and FEC-geometry parameters.

Binding the full context prevents a valid (manifest, objects) pair
from being replayed onto another track or broadcast signed by the
same key.

Freshness: receivers MUST reject manifests whose group_id falls
outside the live-edge window unless operating in an
explicitly-configured DVR or replay mode.

### Authenticated Bytes

The authenticated bytes of an object are the MMTP packet bytes as
carried in the MoQ object payload -- identical across MoQ unicast,
multicast UDP, and ROUTE after symbol-level normalization --
excluding any transport-variant trailers.  This gives cross-path
verifiability: the same digest validates a symbol regardless of
which path delivered it, so a symbol received on any path, or
recovered by FEC decoding, verifies against the same manifest
entry.

### Catalog Signaling

The authentication configuration is declared in the catalog as part
of the multicast configuration:

~~~ json
"auth": {
  "scheme": "bc-provenance",
  "hash": "blake3",
  "sig": "ed25519",
  "publicKey": "<32-byte Ed25519 public key, base64url unpadded>",
  "keyId": "v1",
  "previousKey": "<optional, prior public key during rotation>",
  "compaction": "merkle",
  "enforcement": "shadow",
  "tracks": [
    { "mediaTrack": "video/base",
      "manifestTrack": "video/manifest",
      "authScope": "<32-byte value, base64url unpadded>",
      "sourceSymbolFormat": "full-mmtp-packet" }
  ]
}
~~~

**scheme**, **hash**, **sig** (strings, REQUIRED): The
  authentication profile, digest algorithm, and signature algorithm.
  This document defines only "bc-provenance" with "blake3"
  (BLAKE3-256 [@?BLAKE3]) and "ed25519" ([@!RFC8032]).

**publicKey** (string, REQUIRED): The 32-byte Ed25519 broadcast
  public key, base64url-encoded without padding.

**keyId** (string, REQUIRED): Key epoch identifier.  The key epoch
  is part of the signature context binding (Section 7.2.3).

**previousKey** (string, OPTIONAL): The prior epoch's public key,
  retained during rotation.  Together with `keyId` this permits a
  one-epoch overlap: receivers MAY accept manifests signed under
  the prior epoch while the catalog advertises both keys.

**compaction** (string, OPTIONAL, default "merkle"): Digest
  compaction, "merkle" or "none", as defined in Section 7.2.2.

**enforcement** (string, OPTIONAL, default "shadow"): Publisher
  hint.  "shadow" asks receivers to verify and report; "required"
  indicates that receivers SHOULD drop unverified objects.
  Receivers ultimately choose their enforcement mode
  (Section 7.2.6).

**tracks** (array of objects, REQUIRED): One entry per protected
  media track.  The array MUST NOT be empty.

  - **mediaTrack** (string, REQUIRED): Name of the protected media
    track as it appears in the catalog.
  - **manifestTrack** (string, REQUIRED): Name of the manifest
    track carrying the signed manifests for `mediaTrack`.
    `manifestTrack` values MUST NOT collide across entries.
  - **authScope** (string, REQUIRED): A fresh, unpredictable
    32-byte value, base64url-encoded without padding, generated
    per (session, track) and mixed into the digest computation as
    a domain-separation input.  `authScope` values MUST NOT
    collide across entries.
  - **sourceSymbolFormat** (string, REQUIRED): The byte format
    digests are computed over.  Only "full-mmtp-packet" -- the
    authenticated bytes of Section 7.2.4 -- is defined by this
    document.

### Receiver Enforcement

Receivers operate in one of three enforcement modes: "off" (no
verification), "shadow" (verify every object and report failures
without dropping), or "enforce".

In enforce mode a receiver MUST drop objects that fail
verification before admission to reassembly or decode, and MUST
discard FEC-recovered blocks whose recovered objects fail
verification.  Injected or corrupted symbols therefore fail the
digest check and are dropped before they can poison FEC decode.  A
receiver in enforce mode SHOULD apply a hold-down to sources whose
objects repeatedly fail verification.

A receiver MUST be able to pin "authentication required" for a
broadcast independently of the catalog.  Without such a pin, an
attacker able to rewrite the catalog could remove the `auth`
member entirely and downgrade the receiver to unauthenticated
reception.

### Threat Model

This profile protects against off-path and on-segment UDP
injection, and against corrupted or attacker-injected FEC symbols.

It does not protect against a malicious MoQ relay that rewrites
the catalog itself, nor against key substitution at the signaling
layer, until an out-of-band key binding exists.  For
broadcast-only receivers with no return channel, the broadcast
public key (or a certificate chaining to one) MUST be provisioned
or pinned out of band; a key learned solely in-band on a one-way
channel provides no authentication.

### ROUTE and Broadcast Carriage

Hybrid receivers -- receivers that also hold the MoQ catalog --
verify symbols from any carrier against the same
catalog-advertised manifests; no carrier-specific authentication
is needed.

For broadcast-only receivers, manifest objects are carried in the
ROUTE signaling carousel, and each source block additionally
carries the signed group digest in an ALC/LCT EXT_AUTH header
extension per [@?RFC5775].

### Canonical Encoding

This section specifies the exact octet encoding of the leaf digest,
the tree root, the signed message, and the manifest object, so that
independent implementations produce byte-identical inputs to BLAKE3
and Ed25519.

All multi-octet integers are unsigned and in network byte order
(big-endian).  The notation is:

- `u8`, `u16`, `u32`, `u64`: unsigned integers of that width.
- `lp16(x)`: a `u16` octet count followed by the `x` octets; `lp32(x)`
  is the same with a `u32` count.  A string is encoded as its UTF-8
  octets.
- A digest is 32 octets (BLAKE3-256); the signature is 64 octets
  (Ed25519 [@!RFC8032]).
- `BLAKE3(m)` is BLAKE3 in unkeyed mode; `BLAKE3(k; m)` is BLAKE3
  keyed with the 32-octet key `k` ([@?BLAKE3]).

A conforming sender and receiver MUST produce identical octet strings
for the leaf digest, the root, and the signed message.  A receiver
MUST verify the Ed25519 signature over the reconstructed signed
message and MUST reject the manifest on any mismatch.

**Leaf digest.** The digest bound in each manifest entry, and hashed
as a Merkle leaf, is:

~~~
digest_i = BLAKE3(authScope;
                  0x00 || u32(object_id_i) || u32(length_i)
                       || authenticated_bytes_i)
~~~

The 32-octet `authScope` (Section 7.2.5) is the BLAKE3 key, giving
per-(session, track) domain separation.

**Merkle Tree Hash (`compaction` "merkle").** The root is the Merkle
Tree Hash of the leaf digests in ascending `object_id` order, using
the tree structure of [@!RFC9162] Section 2.1 with this profile's
keyed node hash:

~~~
MTH(D):                       # D = leaf digests, ascending object_id
  n = length(D)
  if n == 1: return D[0]
  k = largest power of two strictly less than n
  return BLAKE3(authScope; 0x01 || MTH(D[0:k]) || MTH(D[k:n]))
~~~

An inclusion proof is the list of sibling digests on the path from
a leaf to the root, verified by recomputing the interior-node hashes.

With `compaction` "none" the value used in place of the root is the
flat concatenation `digest_0 || digest_1 || ... || digest_(m-1)` of
the `m` leaf digests in ascending `object_id` order (32 * m octets).

**Signed message.** The signature (Section 7.2.3) is computed over
the following octet string, which the receiver reconstructs from the
manifest object and the catalog:

~~~
signed_message =
    "BCPV1-sig"                       # 9-octet ASCII domain tag
 || u8(manifest_format_version)       # = 1
 || u8(compaction)                    # 0 = none, 1 = merkle
 || lp16(broadcast_namespace)
 || lp16(track_name)                  # the media track name
 || u64(group_id)
 || u32(object_id_min) || u32(object_id_max)
 || lp16(keyId)
 || params_hash                       # 32 octets (below)
 || lp32(root_or_list)                # 32-octet root (merkle), or
                                      #   32*m-octet flat list (none)
~~~

`object_id_min` and `object_id_max` are the smallest and largest
`object_id` in the manifest.  `params_hash` binds the track's codec, timing, and
FEC geometry as a hash over a fixed-order encoding of those catalog
fields, so they are bound without depending on a canonical JSON form:

~~~
params_hash = BLAKE3("BCPV1-params"
    || lp16(codec) || u32(timescale) || u32(groupDurationTicks)
    || lp16(fecAlgorithm) || u32(sourceSymbols) || u32(repairSymbols)
    || u32(symbolSize) || u32(interleaveDepthMs))
~~~

**Manifest object.** The object carried on the manifest track
(Section 7.2.1) is:

~~~
manifest_object =
    u8(manifest_format_version)       # = 1
 || u8(compaction)                    # 0 = none, 1 = merkle
 || u64(group_id)
 || u32(object_count = m)
 || m * ( u32(object_id) || u32(length) || 32-octet digest )
                                      #   in ascending object_id order
 || 64-octet Ed25519 signature
~~~

The `group_id` and `object_count` fields are the group-close record of
Section 7.2.2.  A receiver reconstructs the signed message from these
fields plus the `broadcast_namespace`, `track_name`, `keyId`, and
catalog parameters bound by the profile, recomputes the root (or flat
list) from the entry digests, and verifies the signature against the
`publicKey`.  A worked test vector is in Appendix A.

## Catalog as Attack Surface

The multicast catalog extension directs receivers to join multicast
groups and to dial network sources.  A hostile or compromised
catalog is therefore an attack vector:

- **Join amplification**: Catalog-directed joins create IGMP/MLD
  and multicast routing state on intermediate routers
  (Section 4.1).  A catalog listing many endpoints, or rapidly
  changing endpoints, can exhaust router state or subscribe
  receivers to unwanted high-bandwidth traffic.  Receivers MUST
  validate that each `groupAddress` falls within the multicast
  address ranges given in Section 4.1 before joining, and SHOULD
  bound the number of concurrent joins performed on behalf of a
  single catalog.

- **Attacker-chosen dial-out**: The `relay` field of an AMT network
  source is an address the receiver dials over UDP.  A hostile
  catalog can direct traffic at arbitrary targets (traffic
  reflection) or at internal infrastructure (address-space
  probing).  Receivers and relays MUST treat catalog-supplied
  endpoint and relay addresses as untrusted input and validate them
  against local policy (such as an allowlist of permitted relays or
  networks) before dialing, and SHOULD reject loopback, link-local,
  and otherwise non-routable relay addresses unless explicitly
  configured.

# IANA Considerations

This document has no IANA actions.  The multicast catalog extension
(Section 4) is defined by this document and does not require IANA
registration.

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

<reference anchor='MOQ-MMT'>
  <front>
    <title>MPEG Media Transport (MMT) Packaging for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-mmt-00'/>
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

<reference anchor='QUIC-MULTICAST' target='https://datatracker.ietf.org/doc/draft-jholland-quic-multicast/'>
  <front>
    <title>Multicast Extension for QUIC</title>
    <author initials='J.' surname='Holland' fullname='Jake Holland'>
      <organization>Akamai Technologies, Inc.</organization>
    </author>
    <author initials='L.' surname='Pardue' fullname='Lucas Pardue'/>
    <author initials='M.' surname='Franke' fullname='Max Franke'>
      <organization>TU Berlin</organization>
    </author>
    <author initials='K.' surname='Rose' fullname='Kyle Rose'>
      <organization>Akamai Technologies, Inc.</organization>
    </author>
    <date year='2026' month='July' day='6'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-jholland-quic-multicast-09'/>
</reference>

<reference anchor="BLAKE3" target="https://github.com/BLAKE3-team/BLAKE3-specs/blob/master/blake3.pdf">
  <front>
    <title>BLAKE3: one function, fast everywhere</title>
    <author initials="J." surname="O'Connor" fullname="Jack O'Connor"/>
    <author initials="J-P." surname="Aumasson" fullname="Jean-Philippe Aumasson"/>
    <author initials="S." surname="Neves" fullname="Samuel Neves"/>
    <author initials="Z." surname="Wilcox-O'Hearn" fullname="Zooko Wilcox-O'Hearn"/>
    <date year="2021"/>
  </front>
</reference>

<reference anchor='WICG-DirectSockets' target='https://wicg.github.io/direct-sockets/'>
  <front>
    <title>Direct Sockets API</title>
    <author initials='A.' surname='Rayskiy' fullname='Andrew Rayskiy'>
      <organization>W3C Community Group Draft Report</organization>
    </author>
    <date year='2026'/>
  </front>
</reference>

# Test Vector: bc-provenance (BCPV1)

This appendix is informative.  It gives a worked `bc-provenance`
example (Section 7.2.9) with `compaction` "merkle".  All values are
hexadecimal; the Ed25519 secret seed is included only so the vector
is reproducible.

Inputs:

~~~
ed25519 secret seed : 000102030405060708090a0b0c0d0e0f
                      101112131415161718191a1b1c1d1e1f
ed25519 publicKey   : 03a107bff3ce10be1d70dd18e74bc099
                      67e4d6309ba50d5f1ddc8664125531b8
authScope           : a0a1a2a3a4a5a6a7a8a9aaabacadaeaf
                      b0b1b2b3b4b5b6b7b8b9babbbcbdbebf
broadcast_namespace : "example.arena"
track_name          : "video/base"
group_id            : 42
keyId               : "v1"
manifest_format_version : 1     compaction : 1 (merkle)

params (for params_hash):
  codec="avc1.640028" timescale=90000 groupDurationTicks=3000
  fecAlgorithm="raptorq" sourceSymbols=32 repairSymbols=16
  symbolSize=1312 interleaveDepthMs=133
params_hash         : d04d1a707cebcdc0fad2623afef8ebbd
                      bed0e8b97ffa0eb5f99a7f6a751a01af

objects (object_id, length, authenticated_bytes):
  0, 40, 0x11 repeated 40 times
  1, 40, 0x22 repeated 40 times
  2, 24, 0x33 repeated 24 times
~~~

Leaf digests (Section 7.2.9), keyed BLAKE3 under authScope:

~~~
digest_0 : a640524b7c33e4b32c55d775751aa520
           f5049b3d9a86a1baad086b17abd135c1
digest_1 : 93e1096f01bc083e6a9096f968522b87
           b5404ae171e2753d6771181d9f2ee845
digest_2 : e452c8d0abadb8a9c781c7fc64755552
           550328bab5d69928a4e7be11ef7478d9
~~~

Merkle Tree Hash of (digest_0, digest_1, digest_2): n=3, k=2, so
root = node(node(digest_0, digest_1), digest_2):

~~~
merkle root         : 6d32a8a2e87a1a0ea7e7d98f35c7f3e3
                      c8b8bd8226a3cf1baa53ebb115814c34
~~~

signed_message (126 octets) and the Ed25519 signature over it:

~~~
signed_message :
  42435056312d736967 0101 000d 6578616d706c652e6172656e61
  000a 766964656f2f62617365 000000000000002a 00000000 00000002
  0002 7631
  d04d1a707cebcdc0fad2623afef8ebbdbed0e8b97ffa0eb5f99a7f6a751a01af
  00000020
  6d32a8a2e87a1a0ea7e7d98f35c7f3e3c8b8bd8226a3cf1baa53ebb115814c34

signature (64 octets) :
  179971c4e4e9b04ada879d5a96f4980351e2c6e90a1e29f7c2363d959dd974e2
  75a88b0cef7c66d8c38910499282d1bad710bc1cae4c62043978c11506f26c0e
~~~

The full manifest object (198 octets) carried on the manifest track:

~~~
0101 000000000000002a 00000003
0000000000000028 a640524b7c33e4b32c55d775751aa520
                 f5049b3d9a86a1baad086b17abd135c1
0000000100000028 93e1096f01bc083e6a9096f968522b87
                 b5404ae171e2753d6771181d9f2ee845
0000000200000018 e452c8d0abadb8a9c781c7fc64755552
                 550328bab5d69928a4e7be11ef7478d9
179971c4e4e9b04ada879d5a96f4980351e2c6e90a1e29f7c2363d959dd974e2
75a88b0cef7c66d8c38910499282d1bad710bc1cae4c62043978c11506f26c0e
~~~
