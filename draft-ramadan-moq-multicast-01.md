%%%
title = "Multicast Delivery and Endpoint Discovery for Media over QUIC"
abbrev = "MoQ Multicast"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
date = "2026-10-26T00:00:00Z"
keyword = ["multicast", "MoQ", "AMT", "SSM", "TreeDN"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-multicast-01"
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
platforms.  All multicast delivery uses MPEG Media Transport Protocol
(MMTP) packets, the same packet format used on MoQ QUIC streams and
datagrams.  A manifest-based content-authentication profile protects
multicast delivery.

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
2. **Catalog extension**: A multicast endpoint discovery mechanism
   for MoQ catalogs [@!I-D.ietf-moq-msf].  Endpoints carry mmtp tracks
   and their repair tracks, and a loc or cmaf track reaches multicast
   through an mmtp rendition track (Section 4.1).
3. **MMTP wire format**: All multicast delivery uses MMTP packets --
   the same packet format that MoQ objects carry on QUIC streams
   (Section 5).
4. **Multi-path delivery**: Combining MoQ unicast and multicast for
   failover and FEC symbol deduplication

These mechanisms follow TreeDN [@?RFC9706], which gives an
incremental path to native multicast.  A network that supports
multicast delivers the stream to its receivers as native SSM.  A
receiver on a unicast-only network reaches the same stream through an
Automatic Multicast Tunneling (AMT) relay [@!RFC7450] that it finds
in its own network, from a relay service hostname (Section 3.1), or
with DNS Reverse IP AMT Discovery (DRIAD) [@!RFC8777].  Section 4.2.1
describes how a catalog signals both.  Each network can therefore
turn on multicast when it is ready.  Until then, its receivers that
have UDP socket access (Section 3) use AMT, and the others stay on
MoQ unicast.  An AMT relay can replicate packets in router forwarding
hardware or in a kernel data plane, so relay fan-out does not cost a
server per receiver.

## Multicast as Supplement to MoQ Unicast

Multicast delivery as defined in this document is a supplement to
MoQ/QUIC unicast.  Subscribers MUST establish a MoQ session first
to receive the catalog, negotiate parameters, and receive initial
media.  Multicast MAY then be used as an additional delivery path
for ongoing media data.  This ensures that codec configuration is
available before multicast reception begins.

Exception: MMTP-packaged streams [@!MOQ-MMT] delivered via ATSC 3.0
broadcast [@?ATSC-A331] or native SSM MAY operate as unidirectional
data streams without a MoQ session.  MMTP carries per-packet routing
(packet_id), timing (timestamp), sequencing (Packet Sequence Number),
and FEC framing (FEC Type, FEC payload IDs) natively, and its
signaling messages identify the Assets in band: every Asset sent to a
multicast endpoint is named by a PA message on its sending entity's
packet_id 0 signaling sub-flow, whose MP table locates the Asset by
source address, group address, port and packet_id (Section 5).  A
receiver without the catalog
takes the FEC configuration from the AL-FEC message
([@!MOQ-MMT] Section 8.3) when the flow carries one.  A receiver
that holds the catalog takes both from the catalog, which remains
authoritative for media and FEC parameters (Section 4.1;
[@!MOQ-FEC] Section 5.2).  A catalog-provided service name or relay
address is only a discovery input; it is not proof that an upstream
is reachable or healthy.
ATSC 3.0 and ARIB STD-B60 [@?ARIB-B60] receivers consume MMTP over
SSM as their native delivery path.

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

**Service hostname**: A stable DNS name identifying an upstream MoQ
relay or AMT relay service.  It is the receiver's connection identity;
the A and AAAA records returned for it are candidate addresses, not
stable endpoint identities.

**Protocol health**: Successful completion of the protocol-specific
handshake and capability checks required before a receiver selects an
upstream.  A DNS response, a routable address, or a transport handshake
alone is not protocol health.

**MMTP**: MMT Protocol -- the packet layer of MPEG Media Transport
([@!ISO.23008-1] Clause 9; [@!MOQ-MMT] Section 3).

**MMT sending entity**: The entity that packetizes media into MMTP
packets and sends them on one or more multicast endpoints.  It is
the scope over which Section 4.1 assigns each `packetId` value to
exactly one MMTP packet sub-flow, and it serves exactly one MoQ
namespace (Section 4.1).

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
MoQ/WebTransport is the fallback that every client supports and
requires no special platform capabilities.

Broadcast receivers (ATSC 3.0, ARIB STD-B60) consume MMTP streams
natively over RF tuner hardware.  MoQ integration occurs at the
gateway/head-end level via TreeDN [@?RFC9706] and AMT [@!RFC7450] /
DRIAD [@!RFC8777].

Several transports can be available for a given stream.  When more
than one delivery path is available, receivers SHOULD prefer, in
order: tuner-based broadcast reception (where tuner hardware exists),
native SSM, AMT tunneling, and finally MoQ/QUIC unicast.  Local
policy MAY override this order.  Within tuner-based reception,
receivers prefer Single Frequency Network (SFN) diversity reception,
where deployed, over single-transmitter reception.

## Receiver-Owned DNS Candidate Discovery

When a receiver is given a service hostname for a MoQ upstream or an
AMT relay, it MUST perform discovery from that hostname at connection
time.  The resolver's A and AAAA answers form a set of candidate
addresses.  DNS answer order, address reachability, and an address's
geographic or topological appearance do not by themselves establish
health.  Local, anycast, or GeoDNS policy MAY use the resolver to steer
the candidate set toward a nearby upstream, but the receiver MUST
validate the selected candidate at the protocol layer.

For a MoQ/QUIC upstream, a receiver MUST retain the service hostname
for TLS certificate and SNI validation and MUST use a bounded attempt
for each candidate.  A candidate is healthy only after the QUIC
handshake, supported MoQ ALPN negotiation, MoQ session setup, and the
capability or catalog check needed by the requested service have
succeeded.  Receivers MUST bound both the number of concurrent candidate
attempts and the duration of each attempt.  They SHOULD race a bounded
batch of candidates in parallel (or use an equivalent bounded strategy),
select the first healthy candidate, and cancel the losing attempts.  A candidate that
completes QUIC but fails MoQ setup or capability validation MUST NOT
prevent another candidate from being tried.

For an AMT relay, a receiver MUST complete the AMT Discovery,
Advertisement, Request, and Membership Query exchange when those
messages are used, and MUST wait for either the first data packet for
the requested source and group or a configured finite
post-Membership-Query/Update wait to expire.  A receiver MUST NOT wait indefinitely for
data: for a source declared sparse or idle by local policy, expiry of
that wait MAY permit selection after the control-plane exchange, but
the result is control-plane health rather than proof of data-plane
delivery.  A relay that answers DNS or sends an Advertisement but does
not complete the exchange is not healthy.  After selection, the
receiver MUST use bounded liveness and membership-refresh timers and
MUST repeat DNS resolution and the candidate race after tunnel failure
or liveness expiry.

Receivers SHOULD honor DNS TTLs for new connection attempts and SHOULD
apply only bounded negative caching.  An established connection MAY
continue after its DNS answer expires, but a reconnect MUST NOT pin a
previous address indefinitely.  Retries MUST use bounded backoff and
MUST cancel stale attempts before starting another bounded batch; at no
time may candidate attempts accumulate without a bound.  If no candidate
becomes healthy, the receiver uses the next permitted delivery path or
remains in retry state according to local policy; it MUST NOT declare a
path healthy solely because DNS returned an answer.

This procedure applies equally to service hostnames obtained from
configuration, an operator provisioning system, or a multicast catalog.
An operator provisioning system is a control-plane service that publishes
the service hostname, transport metadata, and policy; it is not a
substitute for receiver-side protocol health validation.  A catalog MUST
NOT be interpreted as an authority to bypass that validation.  A literal
IP address is permitted for an explicitly configured static deployment,
but it does not provide DNS locality steering and is not the preferred
form for a service that has multiple upstreams.

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
        "sourceAddress": "192.0.2.1",
        "groupAddress": "232.1.1.1",
        "port": 5004,
        "tracks": [
          { "name": "video",        "packetId": 1 },
          { "name": "video/repair", "packetId": 2 }
        ]
      },
      {
        "sourceAddress": "192.0.2.1",
        "groupAddress": "232.1.1.2",
        "port": 5004,
        "tracks": [
          { "name": "audio", "packetId": 3 }
        ]
      }
    ],
    "networkSource": [{
      "type": "amt",
      "relay": "amt.example.com",
      "discovery": "dns"
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
  for the moq-provenance profile; see Section 7.2.

Endpoint field definitions:

**sourceAddress** (string, OPTIONAL): SSM source IP address per
  [@!RFC4607].  Its presence selects SSM and its absence Any-Source
  Multicast (ASM).

**protocol** (string, OPTIONAL): "ssm" or "asm", restating that
  mode.  An endpoint where it disagrees with `sourceAddress` is
  ignored (see below).

**groupAddress** (string, REQUIRED): Multicast group address.

  - SSM range: 232.0.0.0/8 (IPv4), ff3x::/32 (IPv6)
  - ASM range: 224.0.0.0/4 (IPv4), ff00::/8 outside the SSM range
    ff3x::/32 (IPv6)

**port** (integer, REQUIRED): UDP port number.

**tracks** (array, REQUIRED): Tracks available on this endpoint.
  Each element is an object with the following fields:

  - **name** (string, REQUIRED): Track name corresponding to the
    track identifier used in the MoQ catalog.  The name is resolved
    in the namespace of the catalog track ([@!I-D.ietf-moq-msf]
    Section 5.2.2); an endpoint MUST NOT list a track whose catalog
    entry declares another namespace.  The named track MUST
    be a track whose `packaging` is `mmtp` ([@!MOQ-MMT] Section 12.1)
    or a `fec-repair` track that repairs such a track ([@!MOQ-FEC]
    Section 5.1.1).
  - **packetId** (integer, REQUIRED): MMTP packet_id used for
    packet-level track routing on multicast.  Maps directly to the
    Packet ID field in the MMTP header (Section 3.1 of
    [@!MOQ-MMT]).  The value is an integer in the range 1..65535.
    Each value MUST denote exactly one MMTP packet sub-flow across
    all endpoints of the MMT sending entity (Section 2) for the
    lifetime of the delivery session, not merely within one
    (sourceAddress, groupAddress, port) tuple; two distinct sub-flows
    MUST NOT share a value ([@!ISO.23008-1] Clause 9.2.3).  A sub-flow
    is one sequence of packets with one packet_sequence_number space.
    An endpoint that carries
    another endpoint's sub-flow packet for packet therefore carries it
    under the same value, and every other sub-flow takes a value of
    its own.  The rungs of a ladder never share a value.  A catalog
    track denotes one sub-flow: every endpoint that lists a track
    carries that track's one sub-flow, under one value.  Media that
    the sending entity packetizes separately for several endpoints,
    such as audio packetized once per rung, MUST be published as a
    separate track for each packetization, with its own name, value,
    `fec` object and repair tracks, because the copies differ in the
    bytes that FEC protects ([@!MOQ-FEC] Section 7.3).  packet_id 0 is
    reserved for the sending entity's MMTP signaling sub-flow
    ([@!MOQ-MMT] Section 3.1; Section 5), which arrives on the same
    tuples as the media; a publisher MUST NOT advertise it for a
    track.

**bandwidth** (integer, RECOMMENDED): Aggregate bandwidth of this
  endpoint in bits per second, defined as the sum of the UDP payload
  bitrates of all tracks carried on the endpoint, including repair
  tracks, plus the MMTP signaling sub-flow on packet_id 0
  (Section 5) where the endpoint carries it; IP/UDP header overhead
  is excluded.  Publishers SHOULD
  include bandwidth to enable capacity-aware join decisions.
  Subscribers SHOULD check available network capacity before joining
  high-bandwidth groups.

**networkSource** (array of objects, OPTIONAL): Network delivery
  configuration for this endpoint; see Section 4.2.

Each (sourceAddress, groupAddress, port) multicast tuple MUST be
associated with at most one MoQ namespace.  Publishers requiring
multiple independent streams MUST use distinct multicast groups or
ports.  An MMT sending entity (Section 2) serves exactly one MoQ
namespace, which is one MMT Package (Section 5); a publisher that
serves several namespaces acts as several sending entities, each with
its own endpoints, its own `packetId` assignment and its own
packet_id 0 signaling sub-flow.

Receivers MUST ignore endpoints whose fields are mutually
inconsistent -- for example, a `protocol` of "ssm" with
`sourceAddress` omitted, a `sourceAddress` present with `protocol`
of "asm", or a `groupAddress` outside the multicast address space.
Receivers MUST likewise ignore an endpoint that lists a track
`packetId` outside the range 1..65535, including 0, the MMTP
signaling flow.  They MUST also ignore an endpoint that lists a track
that the `name` field does not permit.

This document defines multicast carriage only for mmtp tracks
(Section 5).  To offer a track packaged as loc [@?I-D.ietf-moq-loc]
or cmaf [@?I-D.ietf-moq-cmsf] on multicast, a publisher also
publishes an mmtp rendition of the same media: a separate track whose
`packaging` is `mmtp`, with its own name, `packetId`, `fec` object
and repair tracks, in the same `altGroup` as the loc or cmaf track
(Section 6.1).  The endpoint lists the mmtp rendition track.  A
receiver that holds the loc or cmaf track over MoQ receives the mmtp
rendition track on multicast in its place.  The two tracks are
separate FEC instances ([@!MOQ-FEC] Section 6.4.1), so symbols of
one never repair the other, and the multi-path combining of
Section 6 applies within the mmtp rendition track only.

Subscribers receiving a catalog with multicast endpoints MAY
auto-connect to the multicast group when multicast APIs are
available and multicast delivery is preferred (UDP socket access,
native or AMT).  Multicast joins create
IGMP/MLD state on intermediate routers; subscribers SHOULD only
join when multicast provides a concrete benefit over unicast.

Joining an SSM endpoint requires source-specific group membership
signaling: receivers MUST use IGMPv3 [@!RFC9776] (IPv4) or MLDv2
[@!RFC9777] (IPv6) to convey (S,G) joins.  Earlier protocol
versions (IGMPv2/MLDv1) cannot express source-specific joins; if
the receiver's network segment operates at an earlier version (for
example, due to an IGMPv2 querier or snooping switch on the
segment), SSM joins fail silently.  Receivers SHOULD detect the
absence of multicast data following a join and fall back to
MoQ/QUIC unicast (Section 6).

During multicast join (which may take 1-3 seconds for IGMP/MLD),
subscribers SHOULD continue receiving via MoQ/QUIC.  Once multicast
data arrives, subscribers switch to the multicast path.  Section 6.3
describes how they then pause or end the unicast subscriptions that
the multicast path replaces.

If multicast reception fails or degrades, subscribers fall back
to MoQ/QUIC unicast per Section 6.

Receivers SHOULD implement hysteresis to prevent flapping between
multicast and unicast paths.  Switch away from multicast after
sustained loss or consecutive FEC block failures; switch back only
after multicast reception is stable for a sufficient period.
Specific thresholds are implementation-defined and configurable.

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
    "relay": "amt.example.com",
    "discovery": "dns"
  }]
}
~~~

**relay** (string, OPTIONAL): AMT relay service name.  With `dns`, it
MUST be a hostname whose A and AAAA answers are candidate addresses.
With `manual`, it MUST be the literal address of the explicitly
configured relay.  It MUST be omitted with `driad`, because DRIAD
supplies the relay candidates.  A literal address does not provide DNS
locality steering.

**port** (integer, OPTIONAL): UDP port on which the relay named by
  the `relay` field accepts requests.  When absent, the AMT port (2268,
  [@!RFC7450] Section 7.2) is used.  A value other than 2268 departs
  from [@!RFC7450] Sections 5.1.1 and 5.1.3 and works only with
  gateways and relays configured for it.  The field never applies to
  a relay found by DRIAD, whose AMTRELAY record carries no port
  ([@!RFC8777] Section 4.2).

**discovery** (string, OPTIONAL): AMT relay discovery method.

  - "dns": Resolve the `relay` service hostname to A and AAAA
    candidates and validate each candidate with the AMT protocol
    (Section 3.1).
    This is the RECOMMENDED method when a relay service hostname is
    available.
  - "driad": DNS Reverse IP AMT Discovery per [@!RFC8777].
    Subscribers query the source IP's reverse DNS for AMT relay
    records; `relay` MUST be omitted.  Each discovered relay is still a
    candidate and MUST be validated with the AMT protocol before
    selection.
  - "manual": Relay address is provided in the `relay` field.
    This is intended for explicitly configured static deployments.

For `dns`, subscribers MUST resolve the hostname at each connection
and reconnect attempt, bound both the number and duration of AMT
validation attempts, and race a bounded batch for the returned A and
AAAA candidates.  The receiver MUST wait for either first `(S,G)` data
or the configured finite post-Membership-Query/Update wait.  It MUST
select only a candidate that completes the AMT control-plane exchange;
for a sparse or idle source, selection after the wait expires records
control-plane health without claiming data-plane proof.  DNS answer
order is not a health signal.

When cancelling a losing AMT attempt that has reached the Query/Update
state, the receiver MUST send a Membership Update carrying the IGMP/MLD
leave (withdrawal) for the requested `(S,G)` [@!RFC7450] Section 5.1.5,
then close that candidate's socket.  An attempt that has not reached
that state is cancelled by closing its socket; a failed cancellation is
bounded and MUST NOT keep the candidate attempt alive.

Subscribers SHOULD look for a relay in this order, which keeps the
preference of [@!RFC8777] Section 3.1.2 for a relay in the
subscriber's own network:

1. Look for a relay in the subscriber's own network, with DNS-based
   Service Discovery (DNS-SD) [@!RFC6763] for `_amt._udp` and then
   through the AMT anycast addresses of [@!RFC7450] Section 7.
2. Use receiver-owned DNS candidate discovery when `discovery` is
   "dns", or when `discovery` is omitted and `relay` is a hostname.
3. Use DRIAD discovery on the SSM source IP when `discovery` is
   "driad", or when both `discovery` and `relay` are omitted and the
   source IP has DRIAD records.
4. Use a literal `relay` directly when `discovery` is "manual", or when
   `discovery` is omitted and `relay` is a literal under an explicitly
   permitted static-deployment policy.
5. Fall back to MoQ/QUIC unicast.

The `discovery` and `relay` fields select at most one of steps 2 to 4
for an endpoint.  A relay named by the `relay` field or found by DRIAD
is one that the sender knows, and is not necessarily near the
subscriber ([@!RFC8777] Section 3.1.1).  A local relay keeps more of
the path on native multicast.  Every relay found in steps 1 to 4 is a
candidate that the subscriber validates with the AMT protocol before
selection (Section 3.1).  DRIAD requires AMTRELAY (TYPE260) reverse
DNS records on the source IP.  Publishers without reverse DNS control
SHOULD provide a stable `relay` service hostname.

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

**plpId** (integer, OPTIONAL): Physical Layer Pipe ID
  ([@!ATSC-A322]).  Defaults to 0.

**serviceId** (integer, OPTIONAL): Service ID within the
  broadcast multiplex ([@!ATSC-A331]).

**slsUri** (string, OPTIONAL): URI for Service Layer Signaling (SLS)
  bootstrap.  Enables receivers joining via IP (not RF) to acquire
  the full ATSC 3.0 SLS including S-TSID with FEC parameters
  ([@!ATSC-A331]).

Receivers with ATSC 3.0 tuner hardware can receive the stream
directly over RF.  MoQ subscribers without tuner hardware ignore
this networkSource type.

### Multiple Network Sources

When a stream is available via multiple delivery technologies, the
`networkSource` array lists one element per technology:

~~~ json
{
  "networkSource": [
    { "type": "amt", "discovery": "driad" },
    { "type": "atsc3", "frequency": 533000, "plpId": 0 }
  ]
}
~~~

Subscribers select the highest-priority available source per the
transport hierarchy defined in Section 3.

# Multicast Packet Format

All multicast delivery uses MMTP packets.  Each UDP datagram carries
one MMTP packet -- the same packet format that MoQ objects carry on
QUIC streams.  MMTP provides track routing (packet_id), send
timestamps, sequencing (packet_sequence_number), FEC framing (FEC
Type and the Source/Repair FEC Payload IDs) and random access
signaling (RAP flag) in its packet header, and fragmentation (FI) in
the MPU-mode payload header ([@!MOQ-MMT] Sections 3.1 and 4.2).
For a MoQ receiver, FEC configuration (the RaptorQ OTI, or the
Reed-Solomon parameters) comes from the catalog ([@!MOQ-FEC]
Sections 4.2, 4.5 and 5.2); a receiver without the catalog relies on
the in-band signaling below.

Frame-sized LOC [@?I-D.ietf-moq-loc] or CMAF [@?I-D.ietf-moq-cmsf]
objects exceed a UDP datagram, while the MMTP MPU-mode payload format
fragments media into MTU-sized packets ([@!ISO.23008-1]
Clause 9.3.2; [@!MOQ-MMT] Section 5.2).  Multicast carriage therefore
uses MMTP: an endpoint lists only mmtp tracks and their repair
tracks, and a loc or cmaf track reaches multicast through an mmtp
rendition track (Section 4.1).

No additional multicast framing, encapsulation, or header format is
needed.  The MMTP packet format is defined in [@!ISO.23008-1]
Clause 9.2, as profiled in [@!MOQ-MMT] Section 3.1.

This design means the same MMTP packet can be delivered via three
transports without modification:

| Transport | Encapsulation |
|-----------|---------------|
| Reliable QUIC stream | MMTP packet as MoQ stream object |
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

A publisher MUST identify in band the Assets of every MMTP packet
flow that it sends to a multicast endpoint, whether a receiver
obtains the flow over native SSM or ASM or through an AMT relay
(Section 4.2.1).  It does so with one MMTP signaling sub-flow per MMT
sending entity (Section 2): a single sequence of packets on
packet_id 0, with one packet_sequence_number space, that every
endpoint listing a track other than a `fec-repair` track carries
packet for packet, as Section 4.1 requires of any sub-flow carried on
several endpoints ([@!ISO.23008-1] Clause 9.2.3).  All endpoints of
the sending entity carry one Package.  The sub-flow carries a PA
message (message_id 0x0000; [@!ISO.23008-1] Clause 10.3.2,
Table 21), in the signaling message mode of [@!MOQ-MMT] Section 3.1,
with the tables that [@!ISO.23008-1] Clause 10.3.1 requires of a PA
message, among them a PA table (Clause 10.3.7, Table 26) and the
complete MP table of the Package (table_id 0x20, Clause 10.3.9,
Table 29), never a subset.  The MP table MUST describe as an Asset
each track, other than a `fec-repair` track ([@!MOQ-FEC]
Section 5.1), that any endpoint of the sending entity lists, and MUST
locate it at each endpoint that carries it, and at no other, by an
MMT_general_location_info of location_type 0x01 (IPv4) or 0x02 (IPv6)
that gives the endpoint's group address and port, the track's
`packetId`, and, as `ipv4_src_addr` or `ipv6_src_addr`, the address
from which the sending entity transmits that endpoint's flow, which is
the source address of its IP packets ([@!ISO.23008-1]
Clause 10.6.1).  On an SSM endpoint that address equals the
endpoint's `sourceAddress` (Section 4.1); an ASM endpoint, whose
catalog entry has no `sourceAddress`, still carries the sending
entity's own address there.  A receiver matches a location by
destination address, destination port, packet_id and source address:
on an SSM endpoint the source address is the endpoint's
`sourceAddress`, and on an ASM endpoint it is the source address of
the received packets, which tells this sending entity's flow apart
from any other sender on the group.  A receiver behind an AMT relay
compares against the encapsulated IP header, which keeps the original
source address ([@!RFC7450] Section 5.1.6).  Because the sending
entity knows its own source address for every endpoint, the PA
message is identical on every endpoint, and its one version sequence
applies everywhere, so a newer version overrides an older one on all
endpoints alike ([@!ISO.23008-1] Clauses 10.2.3 and 10.3.9.3).
Repair flows are not Assets, and the MP table does not list them;
their in-band signaling is the AL-FEC message of [@!MOQ-MMT]
Section 8.3, which travels on the same sub-flow.

The publisher MUST send a PA message on the sub-flow ahead of the MPU
metadata (FT=0) data unit of every MPU of every track that it sends
to an endpoint, later than the FT=0 data unit of the previous MPU of
the same track, and ahead of any other signaling message sent for
that MPU, such as the AL-FEC message, so that a receiver joining any
endpoint at an MPU boundary holds the mapping before that MPU's media
and other signaling; [@!ISO.23008-1] Clause 10.3.2.1 requires a
receiver to process a PA message before any other signaling message.
A receiver joined to several endpoints receives each packet of the
sub-flow once per endpoint, as identical copies with the same
packet_sequence_number; it acts on one copy of each packet, whether a
PA message or an AL-FEC message, and ignores the rest.  An endpoint
that lists only `fec-repair` tracks (a repair-only endpoint,
[@!MOQ-FEC] Section 6.3.6) carries no Asset and need not carry the
sub-flow.  A receiver that holds the catalog routes a repair-only
endpoint's `packetId` values from the catalog ([@!MOQ-FEC]
Section 6.3.6).  A receiver without the catalog cannot discover a
repair-only endpoint, because the MP table locates only Assets and
the AL-FEC message names a repair flow by `packetId` without a
location, so repair carried on a repair-only endpoint reaches only
catalog-holding receivers.

For a receiver that holds the catalog, the endpoint's `packetId`
values remain authoritative: it routes packets by them as above,
needs no PA message, and handles packet_id 0 per [@!MOQ-MMT]
Section 3.1.  A PA message is never carried as a MoQ object
([@!MOQ-MMT] Section 4.2).

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

1. MUST deduplicate symbols within one FEC instance ([@!MOQ-FEC]
   Section 6.4.1) -- a source track's base instance together with all
   of its repair layers, or its keyframe overlay -- using SS_ID as the
   unique key of a source symbol and (SS_Start, RS_ID) as that of a
   repair symbol ([@!MOQ-FEC] Section 8.3)
2. MAY combine source and repair symbols received on different
   paths in either direction: source symbols via multicast with
   repair symbols via MoQ/QUIC, or source symbols via reliable
   MoQ/QUIC with repair symbols via lossy multicast -- skipping
   FEC decoding when all source symbols arrive reliably

Multicast-to-unicast failover: if multicast reception fails, a
subscriber falls back to MoQ/QUIC unicast.  It resumes a unicast
subscription that it paused when it switched to multicast, as
Section 6.3 describes.  Otherwise it subscribes again, with a
SUBSCRIBE whose LOCATION_FILTER parameter ([@!I-D.ietf-moq-transport]
Section 9.20.9) sets where delivery starts, using one of the joins of
[@!I-D.ietf-moq-transport] Section 3.5:

- Next Object (Location Filter Type 0x05) starts at the live edge.
  Delivery can begin in the middle of a group.
- Next Object together with a FILL_PARAMETERS parameter
  ([@!I-D.ietf-moq-transport] Section 9.20.15) whose LOCATION_FILTER
  is Relative Start (0x01) with StartGroup 1 also delivers the
  current group from its start, on a fill fetch stream
  ([@!I-D.ietf-moq-transport] Section 3.4).  This is the join of
  [@!MOQ-MMT] Section 6.1, and the one to use when the receiver
  cannot decode from the middle of a group.
- Relative Start (0x01) with StartGroup 0 starts at the next group.

No coordinate mapping between multicast SS_IDs and MoQ Group IDs is
needed, because the publisher resolves each of these filters against
its Largest Object ([@!I-D.ietf-moq-transport] Section 3.1.4).
Failover replaces the multicast path; it is distinct from per-block
unicast repair (Section 6.2), which leaves the multicast subscription
in place.

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
by a FETCH [@!I-D.ietf-moq-transport] of the block's repair-track
group.  That group's ID is the block's extended SS_Start
([@!MOQ-FEC] Section 7.5): the SS_Start from the Repair FEC Payload
ID of a multicast repair packet of the block, extended with the wrap
epoch to a value in [0, 2^62).  MoQ Transport Group IDs range up to
2^64 - 1 ([@!I-D.ietf-moq-transport] Section 8.1); repair Group IDs
use only [0, 2^62), as [@!MOQ-FEC] Section 7.5 specifies.
A receiver that takes its repair from multicast has usually received
no repair-track Group ID over MoQ.  Before its first FETCH it
therefore establishes the wrap epoch, as [@!MOQ-FEC] Section 7.5
specifies, unless it has received such a Group ID or has observed the
FEC instance from its first block.  To do so, it sends a TRACK_STATUS
request for the repair track ([@!I-D.ietf-moq-transport]
Section 9.13).  The epoch comes from the Group of the Largest Object
([@!I-D.ietf-moq-transport] Section 3.1.4) carried in the
LARGEST_OBJECT parameter ([@!I-D.ietf-moq-transport] Section 9.20.17)
of the REQUEST_OK (TRACK_STATUS_OK) that answers it.  For
lost source packets whose block it has not delimited, because it
holds no repair packet of that block, the receiver instead fetches
the Group range that [@!MOQ-FEC] Section 7.5 derives from a lost
SS_ID.  No other coordinate mapping is needed, and the returned
symbols are deduplicated per item 1 of Section 6.  A receiver without
a MoQ session cannot request unicast repair; it relies on in-band FEC
and, where published, the keyframe overlay ([@!MOQ-FEC] Section 6.4).

A relay that does not hold the requested objects fetches them
upstream ([@!I-D.ietf-moq-transport] Sections 3.2.3 and 7.6).  A
FETCH for a repair-track group that neither the relay nor any
publisher upstream of it still holds fails or returns none of the
group's objects, and the receiver then treats the block as
unrecoverable.  How long relays and the original publisher keep
repair-track groups is their own policy.

## Unicast Subscriptions After a Switch to Multicast

After a receiver switches to multicast (Section 4.1), it still holds
the unicast subscriptions that delivered the same media before the
switch: to the tracks it now receives on multicast or to their loc
or cmaf alternatives (Section 4.1), to the repair tracks of such a
loc or cmaf alternative, and to the repair tracks that its multicast
endpoints now carry.
While these subscriptions forward objects, the receiver gets the
media twice, and the network still carries the unicast copy that the
multicast path replaces.  Once multicast delivery of a track is
verified, for example by the receipt on multicast of a complete group
or a complete FEC block of the track, the receiver SHOULD pause these
subscriptions or end them:

- To pause a subscription, the receiver sends a REQUEST_UPDATE with
  the FORWARD parameter set to 0 ([@!I-D.ietf-moq-transport]
  Sections 3.1.1 and 9.20.18).  The subscription stays Established,
  and the publisher sends no objects on it.  Failback then needs no
  new SUBSCRIBE.
- To end a subscription, the receiver sends STOP_SENDING
  ([@!I-D.ietf-moq-transport] Section 3.1).

The receiver does not pause its other subscriptions, such as those
to the catalog track, any manifest track (Section 7.2.1), and any
repair layer that no endpoint it holds carries and that it combines
with multicast source symbols (Section 6, item 2; [@!MOQ-FEC]
Section 6.3.6).

On failback (Section 6), the receiver resumes a paused subscription
with a REQUEST_UPDATE that sets FORWARD to 1.  FILL_PARAMETERS
carried while a subscription is paused opens no fill fetch stream,
and resuming without re-sending FILL_PARAMETERS opens none either
([@!I-D.ietf-moq-transport] Section 3.4.1).  A receiver that needs
the current group from its start therefore sends FILL_PARAMETERS, as
in the join of Section 6, in a further REQUEST_UPDATE after it
receives the REQUEST_UPDATE_OK for the update that resumed the
subscription.  A receiver that ended its subscriptions subscribes
again as Section 6 describes.

Pausing or ending these subscriptions does not affect per-block
unicast repair (Section 6.2), which uses FETCH.

# Security Considerations

## Multicast Security

SSM inherently limits traffic to authorized sources via (S,G)
filtering.  Receivers MAY detect replayed packets by tracking the
MMTP Packet Sequence Number per packet_id within one (source address,
groupAddress, port) tuple and discarding duplicates and packets
outside a bounded reordering window.  The source address is that of
the received packets, the same address Section 5 matches: it equals
`sourceAddress` on an SSM endpoint and is read from each packet on an
ASM endpoint, so two sending entities that share an ASM group and
each use the same packet_id are tracked separately.  For AMT, trust
is delegated to the relay per [@!RFC7450].

## Content Authentication

Multicast UDP delivery lacks the integrity protection that QUIC
provides on unicast paths.  This section defines "moq-provenance", a
manifest-provenance authentication profile.  The publisher
computes, per MoQ group per protected track, an ordered digest
structure over the group's objects; signs its root with a dedicated
broadcast Ed25519 key [@!RFC8032]; and publishes the signed
manifest on a dedicated MoQ track.  Receivers verify each object --
received or FEC-recovered -- against the group root before admitting
it to reassembly and decode.  Verification cost is one signature
verification per group; all digests use BLAKE3 [@!BLAKE3].
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

A manifest is an ordered sequence of per-object entries, one for
each object of the group that carries a packet of the media track's
own MMTP sub-flow (Section 4.1), each binding:

- **object_id**: the packet_sequence_number of the MMTP packet that
  the object carries ([@!MOQ-MMT] Section 3.1).  It is neither the
  MoQ Object ID nor the SS_ID.  Every delivery path carries it inside
  the authenticated bytes (Section 7.2.4), and FEC decoding restores
  it with the packet, so a receiver reads it from the packet however
  the packet reached it.  `object_id` values are therefore unique
  within the group but need not be contiguous or start at zero.
- **digest**: the object's leaf digest -- a keyed BLAKE3-256 over its
  authenticated bytes (Section 7.2.4), domain-separated with
  `authScope` and computed exactly as in Section 7.2.9.
- **length**: the length of the authenticated bytes in octets.

Entries are in ascending numeric `object_id` order, also in a group
whose packet_sequence_numbers wrap.  An object that carries a
signaling packet on packet_id 0, such as the AL-FEC signaling object
([@!MOQ-MMT] Section 4.6), has no entry.  The entry sequence is
followed by a group-close record binding (group_id, object_count),
and by the signature.  The on-wire encoding
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
track namespace, track name, group_id, object-id range, key
epoch, manifest format version, and the track's catalog-advertised
codec, timing, and FEC-geometry parameters.

Binding the full context prevents a valid (manifest, objects) pair
from being replayed onto another track or broadcast signed by the
same key.

Freshness: receivers MUST reject manifests whose group_id falls
outside the live-edge window unless operating in an
explicitly-configured DVR or replay mode.

### Authenticated Bytes

The authenticated bytes of an object are the bytes of the MMTP
packet that its MoQ object payload carries, excluding the trailing
4-byte Source FEC Payload ID that the payload carries when the
packet's FEC Type is 1 ([@!MOQ-FEC] Section 8.5).  That trailer is
the only range excluded.  It is excluded because it is not part of
the protected packet: it is appended after FEC encoding, so a packet
recovered by FEC decoding carries none ([@!MOQ-FEC] Section 7.3).
The authenticated bytes are therefore identical across MoQ unicast,
multicast UDP, and Real-Time Object Delivery over Unidirectional
Transport (ROUTE) [@?ATSC-A331], and for a packet recovered by FEC
decoding.
This gives cross-path verifiability: the same digest validates a
symbol regardless of which path delivered it, so a symbol received on
any path, or recovered by FEC decoding, verifies against the same
manifest entry.  It also means that a verified digest authenticates
the packet but not its FEC block assignment, which the excluded
trailer carries ([@!MOQ-FEC] Section 8.5).

### Catalog Signaling

The authentication configuration is declared in the catalog as part
of the multicast configuration:

~~~
"auth": {
  "scheme": "moq-provenance",
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
  This document defines only "moq-provenance" with "blake3"
  (BLAKE3-256 [@!BLAKE3]) and "ed25519" ([@!RFC8032]).

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
    `manifestTrack` values MUST NOT collide across entries.  Both
    `mediaTrack` and `manifestTrack` are resolved in the namespace of
    the catalog track, as the endpoint `name` field is (Section 4.1).
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

This section is informative.

Hybrid receivers -- receivers that also hold the MoQ catalog --
verify symbols from any carrier against the same
catalog-advertised manifests; no carrier-specific authentication
is needed.

For broadcast-only receivers, manifest objects are carried in the
ROUTE signaling carousel [@?ATSC-A331], and each source block
additionally carries the signed group digest in the Layered Coding
Transport (LCT) header extension EXT_AUTH (Header Extension Type
(HET) 1, [@?RFC5651] Section 5.2.1) of its Asynchronous Layered
Coding (ALC) packets [@?RFC5775].  The extension identifies this
profile by its ASID field ([@?RFC6584] Section 2), whose value the
session description assigns.  This document does not define the
encoding of the group digest in EXT_AUTH.

### Canonical Encoding

This section specifies the exact octet encoding of the leaf digest,
the tree root, the signed message, and the manifest object, so that
independent implementations produce byte-identical inputs to BLAKE3
and Ed25519.

All multi-octet integers are unsigned and in network byte order
(big-endian).  The notation is:

- `u8`, `u16`, `u32`, `u64`: unsigned integers of that width.
- `lp16(x)`: a `u16` octet count followed by the `x` octets; `lp32(x)`
  is the same with a `u32` count.  A catalog string (`keyId`, `codec`,
  `fecAlgorithm`) is encoded as its UTF-8 octets.
- A digest is 32 octets (BLAKE3-256); the signature is 64 octets
  (Ed25519 [@!RFC8032]).
- `BLAKE3(m)` is BLAKE3 in unkeyed mode; `BLAKE3(k; m)` is BLAKE3
  keyed with the 32-octet key `k` ([@!BLAKE3]).

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
    "MOQPV1-sig"                      # 10-octet ASCII domain tag
 || u8(manifest_format_version)       # = 1
 || u8(compaction)                    # 0 = none, 1 = merkle
 || u8(n)                             # namespace field count
 || lp16(ns_field_1) || ... || lp16(ns_field_n)
 || lp16(track_name)                  # the media track name
 || u64(group_id)
 || u32(object_id_min) || u32(object_id_max)
 || lp16(keyId)
 || params_hash                       # 32 octets (below)
 || lp32(root_or_list)                # root, or flat list (none)
~~~

`n` and `ns_field_1` to `ns_field_n` are the number and the bytes of
the Track Namespace Fields of the media track, in order, and
`track_name` is the bytes of its Track Name, each as MoQ Transport
carries them ([@!I-D.ietf-moq-transport] Sections 2.4.1 and 8.7).  The
value `root_or_list` is the 32-octet root (merkle) or the 32 * m-octet
flat list (none).  `object_id_min` and `object_id_max` are the
smallest and largest `object_id` in the manifest.  `params_hash`
binds the track's codec, timing, and FEC geometry as a hash over a
fixed-order encoding of those catalog fields, so they are bound
without depending on a canonical JSON form:

~~~
params_hash = BLAKE3("MOQPV1-params"
    || lp16(codec) || u32(timescale) || u32(groupDurationTicks)
    || lp16(fecAlgorithm) || u32(sourceSymbols) || u32(repairSymbols)
    || u32(symbolSize) || u32(interleaveDepthMs))
~~~

An absent `interleaveDepthMs` is encoded as u32(0), so it and an
explicit zero yield the same `params_hash`.  The two are equivalent for
this binding: both mean that the catalog signals no elapsed-time FEC
deadline ([@!MOQ-FEC] Section 5.1).

**Manifest object.** The object carried on the manifest track
(Section 7.2.1) is:

~~~
manifest_object =
    u8(manifest_format_version)       # = 1
 || u8(compaction)                    # 0 = none, 1 = merkle
 || u64(group_id)
 || u32(object_count = m)
 || m * ( u32(object_id) || u32(length) || 32-octet digest )
 || 64-octet Ed25519 signature
~~~

The `group_id` and `object_count` fields are the group-close record of
Section 7.2.2, and the entries are in ascending `object_id` order.  A
receiver reconstructs the signed message from these fields plus the
media track's namespace and `track_name`, the `keyId`, and the
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
    <date year='2026' month='October' day='26'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-mmt-01'/>
</reference>

<reference anchor='MOQ-FEC'>
  <front>
    <title>Forward Error Correction for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <author initials='M. E.' surname='Fiuczynski' fullname='Marc E. Fiuczynski'>
      <organization>Rutgers University</organization>
    </author>
    <date year='2026' month='October' day='26'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-fec-01'/>
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

<reference anchor='ATSC-A322' target='https://www.atsc.org/wp-content/uploads/2026/06/A322-2026-06-Physical-Layer-Protocol.pdf'>
  <front>
    <title>Physical Layer Protocol</title>
    <author>
      <organization>ATSC</organization>
    </author>
    <date year='2026' month='June'/>
  </front>
  <seriesInfo name='ATSC' value='A/322:2026-06'/>
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

# Test Vector: moq-provenance (MOQPV1)

This appendix is informative.  It gives a worked `moq-provenance`
example (Section 7.2.9) with `compaction` "merkle".  All values are
hexadecimal; the Ed25519 secret seed is included only so the vector
is reproducible.  The authenticated bytes are placeholders rather
than MMTP packets, so the `object_id` values are not read from them.

Inputs:

~~~
ed25519 secret seed : 000102030405060708090a0b0c0d0e0f
                      101112131415161718191a1b1c1d1e1f
ed25519 publicKey   : 03a107bff3ce10be1d70dd18e74bc099
                      67e4d6309ba50d5f1ddc8664125531b8
authScope           : a0a1a2a3a4a5a6a7a8a9aaabacadaeaf
                      b0b1b2b3b4b5b6b7b8b9babbbcbdbebf
track namespace     : one field, "example.arena"
track_name          : "video/base"
group_id            : 42
keyId               : "v1"
manifest_format_version : 1     compaction : 1 (merkle)

params (for params_hash):
  codec="avc1.640028" timescale=90000 groupDurationTicks=3000
  fecAlgorithm="raptorq" sourceSymbols=32 repairSymbols=16
  symbolSize=1312 interleaveDepthMs=133
params_hash         : 6f0ab95fb0bcbaf034f1d889c251a3b3
                      366ba01152edfcdcd615f2395e72ccb8

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

signed_message (128 octets) and the Ed25519 signature over it:

~~~
signed_message :
  4d4f515056312d736967 0101 01 000d 6578616d706c652e6172656e61
  000a 766964656f2f62617365 000000000000002a 00000000 00000002
  0002 7631
  6f0ab95fb0bcbaf034f1d889c251a3b3366ba01152edfcdcd615f2395e72ccb8
  00000020
  6d32a8a2e87a1a0ea7e7d98f35c7f3e3c8b8bd8226a3cf1baa53ebb115814c34

signature (64 octets) :
  d274092eb1f7de4500e3010732bf1f3dfdadc5a2559020394a02f22de8f99a73
  524d2257bb289382b657d97b19c0fb9c1ff6af2b751f8fdd259d7cc6d9e5460e
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
d274092eb1f7de4500e3010732bf1f3dfdadc5a2559020394a02f22de8f99a73
524d2257bb289382b657d97b19c0fb9c1ff6af2b751f8fdd259d7cc6d9e5460e
~~~

# Changes Since draft-ramadan-moq-multicast-00

This appendix is informative.  It is to be removed before publication
as an RFC.

- Section 1: added a paragraph on TreeDN [@?RFC9706] as an incremental
  path to native multicast, with AMT relays serving unicast-only
  networks; receivers without UDP socket access stay on
  MoQ unicast.  The statement that MoQ relays MAY operate as TreeDN
  nodes is removed, because [@?RFC9706] defines no such role.  The
  catalog extension is no longer called container-agnostic.
- Section 1.1: a catalog-provided service name or relay address is
  a discovery input, not proof that an upstream is reachable or
  healthy.
- Section 2: defines service hostname and protocol health.
- Sections 3 and 4.1: the availability of several transports, the
  preference for SFN diversity reception, and the configurability of
  hysteresis thresholds are no longer stated with BCP 14 keywords.
- New Section 3.1: a receiver given a service hostname for a MoQ
  upstream or an AMT relay resolves it at connection time and treats
  the A and AAAA answers as candidates.  It selects a candidate only
  after protocol health: MoQ session setup and the capability check
  for a MoQ upstream, or the AMT exchange and the first data or a
  bounded wait for an AMT relay.  It races a bounded batch, cancels
  the losers, honors DNS TTLs, and does not pin an address across
  reconnects.
- Section 4.1: an endpoint lists only mmtp tracks and the
  `fec-repair` tracks that repair them, and a receiver ignores an
  endpoint that lists any other track.  A loc or cmaf track reaches
  multicast through an mmtp rendition track in its `altGroup`.
- Section 4.1: an endpoint names tracks in the namespace of the
  catalog track.  The IPv6 ASM range is now ff00::/8 outside the SSM
  range ff3x::/32, which admits transient, unicast-prefix-based and
  embedded-RP groups.  IGMPv3 and MLDv2 are cited to [@!RFC9776] and
  [@!RFC9777], which obsolete RFC 3376 and RFC 3810.
- Section 4.1: points to Section 6.3, under which a receiver SHOULD
  pause or end the unicast subscriptions that the multicast path
  replaces once multicast delivery is verified.
- Section 4.2.1: the new `discovery` value "dns" resolves the
  `relay` service hostname to candidates that the subscriber
  validates (Section 3.1).  It is now the recommended method when a
  relay service hostname is available, in place of "driad".
  `relay` is a hostname with "dns", a literal
  address with "manual", and absent with "driad".  A losing AMT
  candidate sends a Membership Update with the leave before its
  socket closes.  The search starts with a relay in the subscriber's
  own network, found with DNS-SD or the AMT anycast addresses
  ([@!RFC8777] Section 3.1.2).  The claim that DRIAD relay addresses
  are typically anycast is removed.  The examples name a relay
  service hostname.  The `port` field now says that a value other
  than 2268 departs from [@!RFC7450] and never applies to a relay
  found by DRIAD.
- Section 4.2.2: the atsc3 fields cite [@!ATSC-A331] and
  [@!ATSC-A322].
- Section 5: the paragraph on LOC and CMAF objects now refers to the
  mmtp rendition rule of Section 4.1.  It no longer says that
  multicast carriage uses MMTP "regardless of a track's unicast
  packaging".  The catalog-derived FEC configuration now also covers
  the Reed-Solomon parameters ([@!MOQ-FEC] Section 4.5).  The
  transport table drops the QUIC datagram row, because [@!MOQ-MMT]
  Section 4.3 sends the objects of an mmtp track only in subgroups.
- Section 6: failover uses the joins of [@!I-D.ietf-moq-transport]
  Section 3.5 (LOCATION_FILTER Next Object or Relative Start, and
  FILL_PARAMETERS for the current group).  These replace the "Largest
  Object filter" and "Next Group Start filter", which that document no
  longer defines.  A paused unicast subscription is resumed instead
  of subscribing again.
- Section 6.2: "standalone FETCH" is now FETCH, and "Largest Location"
  is now Largest Object, with the LARGEST_OBJECT parameter cited.  The
  text now says that repair Group IDs use only [0, 2^62) of the MoQ
  Transport Group ID range, which goes up to 2^64 - 1.  A relay that
  does not hold a repair-track group fetches it upstream, so a FETCH
  fails only when no publisher upstream still holds the group.
- New Section 6.3: after a switch to multicast, a receiver SHOULD
  pause its unicast subscriptions with REQUEST_UPDATE (FORWARD 0) or
  end them with STOP_SENDING, and resumes paused ones on failback.  It
  keeps any repair layer that no endpoint carries and that it combines
  with multicast source symbols.
- Section 7.2: the profile is renamed from "bc-provenance" to
  "moq-provenance", and its domain tags from "BCPV1-sig" and
  "BCPV1-params" to "MOQPV1-sig" and "MOQPV1-params".  [@!BLAKE3] is
  now a normative reference.
- Section 7.2.2: `object_id` is now the packet_sequence_number of the
  MMTP packet, which every delivery path carries and FEC decoding
  restores.  It is neither the MoQ Object ID nor the SS_ID.  An object
  that carries a signaling packet on packet_id 0 has no entry.
- Section 7.2.5: `mediaTrack` and `manifestTrack` are resolved in the
  namespace of the catalog track, as the endpoint `name` field is.
- Section 7.2.8: the section is now informative.  EXT_AUTH is now
  cited to [@?RFC5651] Section 5.2.1 instead of [@?RFC5775] alone.
  The section now states that the extension identifies this profile
  by its ASID field ([@?RFC6584] Section 2), whose value the session
  description assigns, and that this document does not define the
  encoding of the group digest in EXT_AUTH.
- Section 7.2.9: the signed message binds the media track's Track
  Namespace Fields as a counted list of length-prefixed fields instead
  of a single string, and the Track Name as its bytes.  The test
  vector of Appendix A is regenerated for the new encoding and domain
  tags, and notes that its authenticated bytes are placeholders, not
  MMTP packets.
- Editorial: the Abstract and Sections 1 and 7.2.4 expand MMTP, AMT,
  DRIAD and ROUTE.  Section 1 no longer calls failover seamless,
  Section 1.1 calls multicast an additional delivery path instead of
  an optimized one, and Section 3 calls MoQ/WebTransport the fallback
  that every client supports instead of the universal fallback.  The
  examples of Section 4.1 use a documentation address, and the `auth`
  fragment of Section 7.2.5 is not labeled as JSON.
- References: [@!MOQ-MMT] and [@!MOQ-FEC] now name their -01
  revisions, and [@!MOQ-FEC] lists both of its authors.  ATSC A/331,
  ATSC A/322 and ARIB STD-B60 are now cited.
