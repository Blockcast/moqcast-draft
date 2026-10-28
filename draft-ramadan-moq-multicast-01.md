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
broadcast [@!ATSC-A331] or native SSM MAY operate as unidirectional
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
    lifetime of the delivery session, not merely within one `(S, G,
    port)` multicast tuple (below); two distinct sub-flows MUST NOT
    share a value ([@!ISO.23008-1] Clause 9.2.3).  A sub-flow
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

**auth** (object, OPTIONAL when the `multicast` object has no `auth`
  member, REQUIRED otherwise): Content authentication of this
  endpoint's flow; its presence makes the endpoint a protected flow.
  Receivers MUST ignore an endpoint that lacks `auth` when the
  `multicast` object carries `auth`, and an endpoint that carries
  `auth` when the `multicast` object does not (Section 7.2.6).
  See Section 7.2.

**networkSource** (array of objects, OPTIONAL): Network delivery
  configuration for this endpoint; see Section 4.2.

Each `(S, G, port)` multicast tuple, with `S` the endpoint's
`sourceAddress` on an SSM endpoint, its `auth.senderAddress` on a
protected ASM endpoint ((#digest)) and absent on an unprotected ASM
endpoint, MUST be associated with at most one MoQ namespace and at
most one endpoint object, and so MUST a protected endpoint's `(S, G,
manifestPort)` tuple (Section 7.2.6).  Publishers requiring
multiple independent streams MUST use distinct multicast groups or
ports.  An MMT sending entity (Section 2) serves exactly one MoQ
namespace, which is one MMT Package (Section 5); a publisher that
serves several namespaces acts as several sending entities, each with
its own endpoints, its own `packetId` assignment and its own
packet_id 0 signaling sub-flow.  A track listed on an endpoint MUST
NOT declare a `namespace` other than the catalog track's
([@!I-D.ietf-moq-msf] Section 5.2.2); a receiver MUST ignore an
endpoint that lists one.

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
the multicast path replaces.  What a
subscriber receives over MoQ/QUIC for a consumer that has not yet
admitted a datagram of a protected flow is outside the profile of
(#content-authentication): the MoQ session protects it, and the
receiver MAY verify it against the records of a `manifestTrack`
((#emission-and-cadence)); the profile governs a consumer from its
first admitted datagram (step 2 of
(#receiver-enforcement-and-state)), at which the receiver discards
what the consumer still holds of the flow's tracks that it did not
admit.

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
  the full ATSC 3.0 SLS of an MMTP service, its MP table included
  ([@!ATSC-A331] Section 7.2).

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
for a track, for the `(S, G, port)` multicast tuple (Section 4.1) on
which the packet arrived, `S` being the packet's source address as
this section matches it, by an endpoint that the receiver has not
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
are described, informatively, in [@!MOQ-FEC] Section 11.3.

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
  and the publisher sends no objects on it.  Failover then needs no
  new SUBSCRIBE.
- To end a subscription, the receiver sends STOP_SENDING
  ([@!I-D.ietf-moq-transport] Section 3.1).

The receiver does not pause its other subscriptions, such as those
to the catalog track, any manifest track (Section 7.2.5), and any
repair layer that no endpoint it holds carries and that it combines
with multicast source symbols (Section 6, item 2; [@!MOQ-FEC]
Section 6.3.6).

On failover (Section 6), the receiver resumes a paused subscription
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
each use the same packet_id are tracked separately.  For AMT, the
gateway reads the source address from the encapsulated header and
trusts the relay to have joined that source per [@!RFC7450]; the
relay authenticates nothing it forwards, so an AMT receiver of a
protected flow checks the source itself
((#receiver-enforcement-and-state)).

## Content Authentication

Multicast UDP delivery lacks the integrity protection that QUIC
provides on unicast paths.  This section defines "bc-provenance"
version 2, a manifest-provenance authentication profile.  For each
protected flow the publisher computes a digest over every datagram
the flow emits, repair symbols included; collects digests into
windows of at most 37 datagrams or `manifestTimerMs`, whichever
closes first; places each window in a fixed-layout manifest record;
signs the record with a dedicated broadcast Ed25519 key [@!RFC8032]
under a network-identity prefix; and emits the record on the flow's
manifest port immediately before the datagrams it covers, followed
by a second copy.  Receivers verify one signature per window, hash
each datagram once, and admit a datagram to reassembly, FEC decode
or delivery only after its digest matches an entry of a verified
manifest.

The digest pseudoheader, the hold queue and the consume-on-admission
rule are those of AMBI ([@?I-D.ietf-mboned-ambi] Sections 3.4.2 and
3.2); the signed record carried on the flow's own (S, G) is the
multicast-carried manifest delivery that AMBI Section 2.1.1
anticipates and leaves to another specification.

The digest algorithm is carried in the signed record as a Named
Information Suite ID ((#hash-algorithms)); SHA-256 [@!FIPS180-4] is
mandatory to implement.

The record, digest pseudoheader, signature prefix and hash registry
do not depend on MoQ; (#signature-context-binding),
(#catalog-signaling) and (#broadcast-carriage) bind them
to MoQ.

All multi-octet integers are unsigned and big-endian; `u8`, `u16`,
`u32` and `u64` are unsigned integers of that width; `lp16(x)` is a
`u16` octet count followed by the octets of `x`; a string is its
UTF-8 octets; `H` is the function selected by the record's
`hash_alg` ((#hash-algorithms)), with a 32-octet output.  Test vectors
are in (#test-vectors-bc-provenance-version-2).

### Protected Flows and Sequence Numbers

The protected unit is a flow: every datagram the sending entity
emits to one endpoint `(S, G, port)` of (#multicast-endpoint-format)
whose `auth` member is present ((#catalog-signaling)).  That is the
datagrams of every track the endpoint lists, repair tracks included,
and the MMTP signaling sub-flow on packet_id 0
((#multicast-packet-format)) where the endpoint carries it.  A
track carried on several endpoints is in a separate flow on each.
A packet of a listed track that another path delivers to a consumer
protected under the flow, one that has admitted a datagram of it, is
a datagram of the flow as well (step 2 of
(#receiver-enforcement-and-state)).
A flow has one `manifestPort`, which no other flow of the same `(S,
G)` shares ((#catalog-signaling)); its `sequence` counter (below) and
its `mseq` counter ((#manifest-record)) are kept per `(kid, epoch)`.

`sequence` is a 64-bit counter the sender assigns per `(flow, kid,
epoch)`: it starts at any value and increases by one for every
datagram the flow emits, in emission order, repair symbols and
signaling datagrams included.  It is carried only in manifest
records, never in data datagrams, and is unrelated to MoQ
`group_id` and `object_id`.  Digest `i` of a record covers
`sequence = first_seq + i`, so one window is a contiguous run of
the flow.  A window MAY span a MoQ group boundary.  A datagram the
sender emits twice (a carousel) has two sequences and two digests.

### Digest

Every datagram the sender emits in a protected flow has a digest:

~~~
D = H(pseudoheader || payload)
~~~

`payload` is the entire UDP payload as transmitted, including the
trailing Source FEC Payload ID when the packet's FEC Type is 1
([@!MOQ-FEC] Section 8.5), so a verified digest also authenticates
the FEC block assignment of a received packet.  A packet the decoder
recovers carries no Source FEC Payload ID and none is re-appended for
delivery ([@!MOQ-FEC] Section 7.3); when its admission needs a digest,
the receiver appends the base SS_ID its position in the base block
implies, for the hash only ((#receiver-enforcement-and-state)).

`pseudoheader` is the AMBI pseudoheader of [@?I-D.ietf-mboned-ambi]
Section 3.4.2, restated here by value since that draft has expired:

~~~
pseudoheader =
    S                     # 4 octets (IPv4) or 16 octets (IPv6)
 || G                     # 4 or 16 octets, same family as S
 || 0x00                  # zeroes
 || 0x11                  # protocol, UDP
 || u16(payload_length)   # length of payload in octets
 || u16(src_port)
 || u16(dst_port)
 || u32(streamId)
~~~

Addresses are in native width, never IPv4-mapped.  `S` is the
address from which the sending entity transmits the flow
((#multicast-packet-format)): the endpoint's `sourceAddress` on an
SSM endpoint and its `auth.senderAddress` on an ASM endpoint
((#catalog-signaling)).  `src_port` and `dst_port` are both the
endpoint's `port`: the sender MUST emit every datagram of the flow
from UDP source port `port`.  `streamId` is the endpoint's
`auth.streamId`.  Every input is catalog-declared, and a receiver without the catalog
holds the same values from its out-of-band provisioning
((#receiver-enforcement-and-state)), so for a datagram of the flow
delivered over a unicast MoQ path or an MMTP broadcast the receiver
forms the same pseudoheader and one digest verifies the same bytes
on every path ((#broadcast-carriage); step 2 of
(#receiver-enforcement-and-state)).

### Manifest Record

A manifest record is one UDP datagram on `manifestPort` of the same
`(S, G)` as the protected flow.  Every field except the signature is
at a fixed offset, and the signature is the last 64 octets.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `magic`, the ASCII octets "MHM2" |
| 4 | 4 | `kid`, key identifier ((#catalog-signaling)) |
| 8 | 4 | `epoch`, increments on sender restart and key change |
| 12 | 8 | `mseq`, manifest counter, monotonic per `(flow, kid, epoch)` |
| 20 | 8 | `first_seq`, the `sequence` of digest 0 |
| 28 | 2 | `count`, 1 to 37 |
| 30 | 1 | `hash_alg` ((#hash-algorithms)) |
| 31 | 1 | `flags` (below) |
| 32 | 4 | `sent`, emission time in POSIX seconds (below) |
| 36 | 32 | `ctx`, context hash ((#signature-context-binding)) |
| 68 | 32 x count | digests, in emission order |
| 68 + 32 x count | 64 | Ed25519 signature |

Length is `132 + 32 x count` octets.  The cap of 37 digests is an MTU
choice: the 1316-octet maximum is 1344 octets on the wire with IPv4
and UDP headers and 1364 with IPv6, which leaves room for AMT
encapsulation [@!RFC7450] on a 1500-octet path.

`flags`: bit 0, epoch end ((#receiver-enforcement-and-state)); bits
1 to 7 reserved, MUST be zero on send and ignored on receipt.

`sent` is the sender's clock when the record is signed, truncated to
whole seconds since 1970-01-01T00:00:00Z with leap seconds excluded,
from a clock synchronized to UTC within 1 s; the twin of a record
((#emission-and-cadence)) carries the original's value.  It is a count
of seconds, not the 16.16 NTP short format, so it wraps in 2106 rather
than every 18.2 hours.  A sender whose clock is further off than the
tolerance of (#receiver-enforcement-and-state) makes its flow
unverifiable to receivers that check freshness.

All records of one flow carry the same `hash_alg` for the life of a
stream generation (`streamId`, (#catalog-signaling)); a change of
algorithm is a new generation.  `epoch` never decreases under one
`kid`: a sending entity MUST NOT reuse an epoch under a `kid`, across
generations or restarts, and a generation that would start below the
`kid`'s last epoch starts under a new `kid` ((#catalog-signaling)).

### Signature Context Binding

The signature is computed over:

~~~
signed_message =
    "mcast-manifest-v2" || 0x00     # 18-octet prefix
 || u32(streamId)
 || S                               # 4 or 16 octets
 || G                               # 4 or 16 octets
 || u16(manifestPort)
 || record[0 .. len - 64)
~~~

with `S`, `G`, `streamId` and `manifestPort` as declared for the
endpoint ((#digest), (#catalog-signaling)).  The prefix binds the flow's network identity; a receiver needs no
catalog state to check it beyond those four values, which a MoQ
receiver takes from the catalog and a broadcast-only receiver from its
provisioning ((#receiver-enforcement-and-state)).
The MoQ context is bound inside the record by `ctx`:

~~~
ctx = H("BCPV2-ctx"
        || u16(f) || f * lp16(field)        # namespace, in order
        || u16(n) || n * u16(packetId)      # ascending
        || params_hash)

params_hash = H("BCPV2-params"
    || lp16(codec) || u32(timescale) || u32(groupDurationTicks)
    || lp16(fecAlgorithm) || u32(sourceSymbols) || u32(repairSymbols)
    || u32(symbolSize) || u32(interleaveDepthMs))
~~~

both with the record's `hash_alg`.  The `field` values are the `f`
Track Namespace Fields, in order, of the one MoQ namespace the sending
entity serves ((#multicast-endpoint-format)): the Track Namespace of
the catalog track ([@!I-D.ietf-moq-transport]), which every track
listed on an endpoint shares ((#multicast-endpoint-format);
[@!I-D.ietf-moq-msf] Section 5.2.2); each field is the octets MOQT
carries for it.  The `packetId` values are those of the endpoint's
`tracks` ((#multicast-endpoint-format)), `n` of them in ascending
order.  `params_hash` is taken from the catalog
entry of the endpoint's lowest-`packetId` media track or, for an
endpoint that lists only `fec-repair` tracks, from the catalog entry
of the source track that its lowest-`packetId` repair track repairs:
the track its `depends` names or, on layer 0, the track whose
`fec.repairTrack` names it ([@!MOQ-FEC] Section 5.1.1).  `codec` is
that entry's MSF field; `timescale` is its timescale and
`groupDurationTicks` its group duration in `timescale` ticks, both as
[@!MOQ-MMT] Section 4.4.2 resolves them; `fecAlgorithm` is the
`algorithm` member of its `fec` object and the other four are its
same-named members ([@!MOQ-FEC] Section 5.1).  An absent
`interleaveDepthMs` is encoded as `u32(0)`; an entry with no `fec`
object is encoded as `lp16("none")` followed by four `u32(0)`; an
entry for which [@!MOQ-MMT] Section 4.4.2 resolves no `timescale` or
no group duration, as it need not for a track that is not
mmtp-packaged ((#multicast-packet-format)), is encoded as `u32(0)` for
that value.  A flow carried without a MoQ catalog sets `ctx`
to 32 zero octets.  A MoQ receiver recomputes `ctx` from the catalog
and MUST reject a record whose `ctx` differs
((#receiver-enforcement-and-state)); a receiver without the catalog
carries `ctx` blind.  A valid (record, datagrams) pair therefore cannot
be replayed onto another endpoint, stream generation, broadcast, key
or epoch; `sent` ((#manifest-record)) bounds replay within an epoch to
the clock tolerance of (#receiver-enforcement-and-state).

### Emission and Cadence

A sender closes a window after 37 datagrams or after `manifestTimerMs`
since the window opened, whichever comes first; the timer governs only
while the flow emits at most 37 datagrams per `manifestTimerMs` (1850
per second at the default, about 21 Mbit/s of 1400-octet datagrams),
and the count cap governs above that.  A sender MAY raise
`manifestTimerMs` to at most `maxAuthDelayMs / 4` on low-rate flows.

The signed record MUST be transmitted immediately before the first
datagram it covers (only the twin of an earlier window MAY come
between them), so the sender holds at most one window of data.  A twin,
a byte-identical copy of the record, MUST be transmitted after the
last datagram the record covers, no later than `maxAuthDelayMs / 2`
after the record and before the signed record of window `mseq + 64`,
so that at most 63 later records precede it and it arrives above the
replay floor of (#receiver-enforcement-and-state), which only the
records arriving on `manifestPort` raise, however fast the flow
closes windows; RECOMMENDED is to transmit it immediately after
the signed record of window `mseq + 2` and before the first datagram
that record covers, or on its own at the `maxAuthDelayMs / 2`
deadline when window `mseq + 2` has not opened by then.  The two
copies then bracket the window's datagrams: a
contiguous loss burst that removes both copies has removed every
datagram between them, and a datagram that survives such a burst has a
usable copy on one side of it, whatever the flow's rate and timer;
only two separate losses can leave an arriving datagram without a
copy, and then at most 37 datagrams expire from the hold queues
((#threat-model)).  Every twin of an epoch MUST be transmitted before
the first record of a later epoch, since a receiver drops the records
of an earlier epoch once its grace period ends
((#receiver-enforcement-and-state)); every twin of the epoch not yet
transmitted when its last datagram has been sent, the twin of the
record whose `flags` bit 0 is set included, follows that datagram at
once.  A receiver handles either copy by step 1 of
(#receiver-enforcement-and-state) and drops the second with one
lookup and one hash.

At 37 digests per window, a record and its twin cost about 71 octets
per 1400-octet datagram (5.1%); data datagrams are untouched.  Manifest
records MUST NOT be FEC-protected; the twin is their loss remedy.

A publisher MAY mirror the same record octets as objects on a MoQ
manifest track (one record per object; a record goes in
manifest-track group N, N being the Group ID of the latest packet,
emitted at or before the window's first datagram, of the track whose
catalog entry supplies `params_hash` ((#signature-context-binding)),
or of that track's first group of the stream generation where none
precedes) for unicast subscribers.  A packet of a track the endpoint
lists that reaches a consumer protected under the flow is a datagram
of the flow on a MoQ unicast path too (step 2 of
(#receiver-enforcement-and-state)), and the mirror is
its only source of records while the multicast path delivers none,
during the join of (#multicast-endpoint-format) and after the
failover of (#multi-path-delivery).  Without a `manifestTrack` a
track's unicast fallback is a MoQ subscription outside this profile,
protected by the MoQ session alone, so a publisher that wants the
fallback verified against its records MUST name one.  Records read
from the manifest track charge a verification budget of their own,
not the flow's `manifestPort` budget
((#receiver-enforcement-and-state)); a receiver that reads the
manifest track while joined to the multicast path sees each record
first on the shorter path and drops the later copy as already
verified, matching its digests only where it raises the mirror's
lead (step 1 of (#receiver-enforcement-and-state)), so where the
mirror leads `manifestPort` it widens, by the mirror's lead and
under the bound
below, the pending expiry of a mirrored record's entries and the
time for which it keeps a digest it admits recorded as admitted: a
relay copy admitted first would otherwise leave the multicast copy,
arriving up to the lead later, to be held and to expire as loss
(steps 1 and 2 of (#receiver-enforcement-and-state)).  The lead of a
record is unknown when its entries are inserted, so the receiver
keeps the lead as a per-flow value: the largest interval it has
measured in the stream generation from the arrival of a record on
the mirror to the arrival of the first copy on `manifestPort`,
which the lookup drops (a later copy on that path, the twin or one
replayed within the retention, measures nothing; step 1 keeps the
time and path of arrival, and a digest of the record's bytes, with
each verified `(kid, epoch, mseq)` for this), each interval rounded
up to a multiple of `manifestTimerMs` before it is compared with
the lead (so the lead rises at most `5000 / manifestTimerMs` times
in a stream generation, 250 at the default, however a relay paces
the mirror; step 1), and the bound below until it has measured
one; a copy that raises the lead, byte-identical to the
verified record, re-admits or re-inserts, under the raised lead and
ahead of the datagrams they cover, the digests of that record and
of every record verified
on the manifest track within the raised lead before now whose first
copy has not yet arrived, for the pairs that have admitted nothing
and are not pending, widens the pending entries of those records by
the raised lead, and
records again as admitted, under the raised lead, the digests of
the pairs that have, so that a mirror whose lead grows past the one
measured, within the bound below, costs the datagrams of those
records nothing, a late copy of a datagram a pair has admitted is
dropped rather than held, and a copy replayed within the retention
re-admits nothing (step 1).  A
receiver that reads no manifest track applies no
lead, nor does one that will not join the multicast path; one that
may yet join applies the bound until it has measured a lead, since
the multicast copies of the datagrams its relay delivers before the
join arrive after it.  The timers of
(#receiver-enforcement-and-state) are wall-clock bounds; a
relay-buffered QUIC path can deliver records later than
`maxAuthDelayMs`, or the datagrams of a window later than the record
that covers them, the manifest track and the media tracks being
separate streams, and a unicast receiver SHOULD widen its hold, and
the freshness tolerance of step 1 of
(#receiver-enforcement-and-state) for the records it reads from the
manifest track, accordingly, by at most 5 s, the widening W, a
receiver that applies no lead widening the pending expiry of a
mirrored record's entries by W as well (step 1), since no lead
covers the datagrams its relay delivers after the records that
cover them: the widening is also its exposure at join to windows
that old served by its relay ((#threat-model)), a record on
`manifestPort` keeps the unwidened tolerance and pending expiry as
the multicast path's hold queue keeps the unwidened expiry, and a
receiver that needs more is replaying
((#receiver-enforcement-and-state)).  The bound caps the lead as
well: a relay that leads the multicast path by more than the bound
plus `maxAuthDelayMs` outruns the admitted digests the lead widens,
and by more than that plus `2 x manifestTimerMs` the pending
entries as well, and the copy on `manifestPort` of a record it
mirrors that far ahead, which the receiver keeps verified for as
long as the freshness check of step 1 would pass it, or for as long
after that as its `mseq` stays above the manifest track's replay
floor ((#receiver-enforcement-and-state)), is dropped by the lookup
of step 1 while so kept and by that check after, and, the lead
standing at the bound, admits nothing either way, so the multicast
copies of the datagrams of those records are held and expire from
the multicast path's hold queue, loss for the failover
((#threat-model)); the lead being the multicast path's lag behind
the mirror, such a path fails over on its own latency on a receiver
that checks freshness.  One that skips the check (the Clock
paragraph of (#receiver-enforcement-and-state)) keeps the record
verified `7 s + maxAuthDelayMs` after its arrival on the manifest
track, or for as long after that as its `mseq` stays above the
manifest track's replay floor (the state list of that section), so
under a relay leading by more than the longer of the two the copy
on `manifestPort` misses the lookup, meets no freshness check and
is verified anew there, from that path's budget, admitting the
datagrams of its window as any record on `manifestPort` does: such
a receiver fails over on a lead between the bound plus
`maxAuthDelayMs` and that retention and, under a larger one,
verifies every record on both paths instead; on a flow whose 64
windows outlast `7 s + maxAuthDelayMs`, the floor keeps the record
verified until its copy arrives under any lead shorter than 64
windows, the lookup drops the copy, and such a receiver fails over
as one that checks freshness does.

### Catalog Signaling

The `auth` member of the `multicast` object
((#multicast-endpoint-format)) declares the profile and its keys;
the `auth` member of an endpoint object marks that endpoint's flow
as protected and carries the flow's parameters:

~~~ json
{
  "multicast": {
    "auth": {
      "scheme": "bc-provenance",
      "version": 2,
      "sig": "ed25519",
      "keys": [
        { "kid": 1,
          "publicKey": "<32-byte Ed25519 key, base64url unpadded>",
          "firstEpoch": 1 }
      ],
      "minEpoch": 17
    },
    "endpoints": [{
      "sourceAddress": "198.51.100.7",
      "groupAddress": "232.10.20.30",
      "port": 5004,
      "bandwidth": 100000000,
      "tracks": [
        { "name": "video",        "packetId": 1 },
        { "name": "video/repair", "packetId": 2 }
      ],
      "auth": {
        "manifestPort": 5005,
        "streamId": 2864434397,
        "maxAuthDelayMs": 200,
        "manifestTimerMs": 20,
        "manifestTrack": "video/manifest"
      }
    }]
  }
}
~~~

Members of `multicast.auth`:

**scheme**, **version** (REQUIRED): "bc-provenance", 2.

**sig** (string, REQUIRED): "ed25519" [@!RFC8032].

**keys** (array, REQUIRED): one to four `{kid, publicKey,
firstEpoch}` objects.  `kid` is an unsigned 32-bit integer carried in
the clear in every record; `publicKey` is the 32-octet Ed25519 public
key, base64url-encoded without padding; `firstEpoch` is the first
`epoch` the key signs.  A key signs the epochs from its `firstEpoch`
up to, but not including, the next larger `firstEpoch` in the array,
and the key with the largest `firstEpoch` signs every later epoch.
`kid` values MUST be unique within a broadcast and `firstEpoch` values
MUST be distinct within the array.  A receiver that takes its keys
from a catalog whose `keys` repeats a `kid` or a `firstEpoch` holds no
key set for the broadcast: it admits nothing and treats every endpoint
of the `multicast` object as one that yields no data
((#multicast-endpoint-format)), as it does on a flow whose records
carry an algorithm it does not implement
((#receiver-enforcement-and-state)); a receiver that pins keys is
unaffected, since its key set comes from the pin.  A receiver drops, before
verification, a record whose `epoch` is outside its `kid`'s range
((#receiver-enforcement-and-state)), so a retired key cannot carry a
receiver past its successor's `firstEpoch`.

**minEpoch** (integer, REQUIRED): the lowest `epoch` a receiver
accepts at join (step 1 of (#receiver-enforcement-and-state)); after
its first verified record the current epoch is the floor, with the
previous epoch admitted on `manifestPort` until the first record of
the current epoch is verified there or dropped there by the
already-verified lookup of step 1 as its byte-identical copy, and
within its grace period after that, and on the manifest track
within the earlier-started of the
two paths' periods (step 1).  The publisher MUST write the current
`epoch` at every
epoch change, sender restart included, so a joiner with a current
catalog cannot be fed an earlier epoch.

Members of an endpoint's `auth`; a protected endpoint MUST also
declare `bandwidth`, which bounds the receiver's hold queues:

- **manifestPort** (integer, REQUIRED): destination port of the record
  datagrams, twins included, on the endpoint's `(S, G)`; MUST differ
  from the `port` of every endpoint of the same `(S, G)` in the catalog,
  this endpoint included, and from the `manifestPort` of every other
  such endpoint, so that no port of an `(S, G)` carries both data and
  records, or the records of two flows.  `(S, G, manifestPort)` is a
  multicast tuple under the one-namespace rule of
  (#multicast-endpoint-format).  A receiver MUST ignore
  ((#multicast-endpoint-format)) a protected endpoint whose ports
  violate this.  Two ASM endpoints whose `senderAddress` differ MAY share
  `groupAddress` and ports; the source check of
  (#receiver-enforcement-and-state) separates them.
- **streamId** (integer, REQUIRED): 32-bit value chosen per channel
  generation, bound into every digest and signature.
- **senderAddress** (string, REQUIRED on an ASM endpoint, MUST NOT
  appear on an SSM endpoint): the address from which the sending
  entity transmits this endpoint's flow, `S` of (#digest); on an
  SSM endpoint `S` is `sourceAddress`.
- **maxAuthDelayMs** (integer, OPTIONAL, default 200, range 50 to
  1000): how long a receiver holds a datagram whose digest has not
  arrived.
- **manifestTimerMs** (integer, OPTIONAL, default 20, at least 1):
  the window timer of (#emission-and-cadence).
- **manifestTrack** (string, OPTIONAL): the MoQ track mirroring the
  records ((#emission-and-cadence)).

When the `multicast` object carries `auth`, every endpoint of the
`multicast` object MUST carry `auth`; a receiver MUST ignore
((#multicast-endpoint-format)) an endpoint that lacks it, so every
multicast datagram it consumes from the sending entity is in a
protected flow and reaches a decoder only through
(#receiver-enforcement-and-state).  An endpoint that carries `auth`
when the `multicast` object does not is ignored likewise, since it
names no key.

### Receiver Enforcement and State

A receiver that implements this profile enforces it: a datagram of a
protected flow is admitted only after its digest matches an entry of a
verified record, and there is no verify-and-report mode.  A receiver
MUST be able to pin "authentication required" for a broadcast
independently of the catalog.  A receiver without the catalog (a
broadcast-only receiver, or native SSM reception without a MoQ
session) MUST be provisioned out of band with the keys, `firstEpoch` included,
and `minEpoch` and, per protected flow, the `streamId`, `S`, `G`, `port`,
`manifestPort` and `bandwidth` the catalog would declare
((#catalog-signaling)), and any non-default `maxAuthDelayMs` and
`manifestTimerMs`: the record carries none of them, and a broadcast
carries the flow on those addresses and ports or not at all
((#broadcast-carriage)); keys are never taken from a carrier's
signaling.  A
receiver that pins keys takes the key set, `firstEpoch` included, from
the pin rather than from the catalog, and MUST keep with the pin,
across sessions, the highest `epoch` it has verified under each pinned
`kid`; in step 1 below it drops, at join, a record whose `epoch` is
below that value for its `kid`, so a catalog that carries a lower
`minEpoch` cannot reopen an epoch a verified record has closed.  The
pin stores no value read from a catalog: every receiver takes
`minEpoch` from the catalog it fetched, or provisions it with the
keys, and it bounds that session only.  A receiver with no pin is
protected at its first join against an earlier epoch only as far as
that catalog is.  A receiver that implements no
algorithm a flow's records carry verifies nothing on that flow: it
admits nothing and treats the endpoint as one that yields no data
((#multicast-endpoint-format)).

On an ASM endpoint a receiver MUST discard, before any parsing or
hashing, a datagram on `port` or `manifestPort` whose IP source
address is not `senderAddress`; behind an AMT relay the address is
that of the encapsulated header ((#multicast-packet-format)).  On an
SSM endpoint reached natively the network enforces the source and a
receiver SHOULD still discard a datagram whose source address is not
`sourceAddress`; a receiver reached through an AMT gateway MUST
discard it, since nothing upstream of its gateway filters the
encapsulated source address and [@!RFC7450] does not authenticate
Multicast Data messages.
A datagram that passes belongs to the flow `(S, G, port)` or `(S, G,
manifestPort)` with `S` as in (#digest).

State per flow: the current `epoch` with the `kid` that set it, per
path (`manifestPort` and the manifest track) the grace period that
ends
`maxAuthDelayMs + 2 x manifestTimerMs` after the first record of the
current epoch verified on that path or dropped there by the
already-verified lookup of step 1 as its byte-identical copy, and,
until the period on
`manifestPort` ends, the previous `epoch` (step 1; a record on
`manifestPort` meets its own path's period, one read from the
manifest track the earlier-started of the two); the flow's
`hash_alg`, fixed by its first verified
record; per `(kid, epoch)` the verified `mseq` values above the
replay floor of the path they arrived on, and those verified on the
manifest track for as long as the freshness check of step 1 would
pass a copy of them on `manifestPort`, their `sent` within
`7 s + maxAuthDelayMs` behind the receiver's clock, or that long
after their arrival on the manifest track where the receiver skips
that check, whatever the floor (so that the lookup of step 1 still
meets, and measures the lead from, a `manifestPort` copy arriving
after 64 or more further records were verified on the mirror, and
drops as already verified every copy that check would pass: one
arriving more than the bound of (#emission-and-cadence) plus
`maxAuthDelayMs + 2 x manifestTimerMs` after the mirror's copy, the
lead standing at the bound, then admits nothing, and the datagrams
it covers expire, as that section says, rather than being verified
anew on `manifestPort`; where the lead stands below the bound, the
first such copy raises it to the bound and handles the record's
pairs again as step 1 says; a receiver that skips the check
verifies anew a copy arriving after the retention and below the
manifest track's replay floor, dropping by the lookup one that
arrives above the floor, as that section also says), each with the
time and path of its arrival, its `sent`, which that retention
reads, the `hash_alg` digest of the record's bytes,
per pair of the record, whether a datagram has been admitted against
it and, for a record verified on the manifest track whose first copy
on `manifestPort` has not yet arrived, the record's pairs, which a
raise of the lead re-handles (steps 1 and 2), per path the
`highest_mseq` that the records
arriving on it have
raised (step 1) and, once a verified record has `flags` bit 0 set,
the `mseq` that closed it; the verification budgets
of step 1, one for `manifestPort` and one for the manifest track,
each with a count of the records it dropped; the mirror's lead
((#emission-and-cadence)), a multiple of `manifestTimerMs` or the
bound, and whether the stream generation has measured one, the bound of that section applying until it has and
zero on a receiver that reads no manifest track or will not join the
multicast path; a pending table of
`(digest, sequence, expiry)` entries, each naming the record and
the pair that inserted it, an entry whose expiry the mirror's lead
or W widened keeping its insertion time as well (step 1);
the digests recorded as admitted, each until the expiry set when
it was recorded, the time of recording plus `maxAuthDelayMs` plus
the mirror's lead then in force, a copy on `manifestPort` that
raises the lead recording again the digests of the marked pairs
it handles (steps 1 and 2); for each open block of a protected
consumer, the number of decodes, at most two, taken with the help
of symbols of unlisted tracks (step 2) that have left it
unrecovered, block state under the bound of [@!MOQ-FEC] Section 9
released with the block (step 2); on a receiver that can request
unicast repair, for each open block that has an FEC deadline, the
admission time of the first packet, source or repair, admitted into
it, or of the packet that stands for it under step 2 (the source
packet of highest SS_ID admitted at or below its lower bounding
packet, or the packet admitted above it where the instance has
admitted none below), and for each base instance the admission time
of the source packet of highest SS_ID it has admitted in the stream
generation, kept under the serial number arithmetic of [@!MOQ-FEC]
Section 7.5 (step 2); two hold queues of
`(digest, datagram, expiry)` entries in arrival order,
`digest` being absent from an entry until the first record of the
flow is verified (step 2): one for the datagrams a MoQ unicast path
delivers and the packets the base instance recovers with the help of
a symbol that path delivered (step 2), and one for the rest.  State
per receiver, shared by its flows: the time of the last catalog
re-fetch that an unknown `kid` triggered (key rotation, below), and
the per-`kid` epoch floor kept with a key pin.  The per-flow state
belongs to the stream generation ((#manifest-record)): when the
`streamId` the catalog, or a receiver's provisioning, declares for the
endpoint changes, the receiver discards every per-flow item above but
the two verification budgets and their counts and the hold queues
(the current and previous `epoch`, `hash_alg`, the per-`(kid, epoch)`
`mseq` state, the mirror's lead, the pending table with the entries
kept for unicast repair, the admitted digests, the per-block decode
counts and the per-block and per-instance admission times), clears
the `digest` of every held
datagram, and
processes the next record as the first of the flow under the
join-time floors of step 1.

A receiver applies the following, in this order, with no
variable-length interpretation before a cryptographic check:

1.  **Record datagram** (on `manifestPort`, `magic` "MHM2").  Require
   `164 <= len <= 1316` and `(len - 132) mod 32 == 0`.  Read the
   fixed-offset integers `magic`, `kid`, `epoch`, `mseq`, `count`,
   `hash_alg` and `sent` and the 32 octets of `ctx`.  Drop before any
   cryptography if: `magic` differs; `kid` is not in the key set, or
   `epoch` is outside its range ((#catalog-signaling));
   `(kid, epoch, mseq)` is already verified (this drops the second
   copy of a record with one lookup and one hash, a copy of the
   previous epoch arriving after its grace period included; a
   dropped copy whose bytes hash, under the flow's `hash_alg`, to
   the digest kept with the verified entry is the record itself and
   counts as its arrival on this path: it raises the `highest_mseq`
   of the path and starts the path's grace period as a verified
   record would, below, and, where the verified copy arrived on the
   manifest track and this one is the record's first copy on
   `manifestPort` (its pairs, kept until then, are released at this
   arrival; a later copy there, the twin or one an injector replays
   within the retention, counts as a further arrival on the path and
   measures nothing), the interval between the two arrivals, rounded
   up to a multiple of `manifestTimerMs` and capped at the bound of
   (#emission-and-cadence), becomes the mirror's lead if it is the
   first measured in the stream generation and raises it if it
   exceeds it, a copy that raises it also handling this record and
   every record verified on the manifest track within the raised
   lead before now whose first copy on `manifestPort` has not yet
   arrived (the verified entry keeps their pairs for this, this
   record's own bytes carrying its pairs), each pair of
   such a record as below for a record on `manifestPort`, under the
   raised lead: a pair marked as having admitted a datagram has its
   digest recorded as admitted until `now + maxAuthDelayMs` plus
   the raised lead; one whose digest is pending has its entry's
   expiry set to the insertion time plus
   `maxAuthDelayMs + 2 x manifestTimerMs` plus the raised lead; one
   whose digest is neither admitted nor pending admits a held
   datagram or inserts a pending entry with expiry
   `now + maxAuthDelayMs + 2 x manifestTimerMs` plus the raised
   lead, `now` being its insertion time; and, once every such record
   is processed, each datagram held in either hold queue whose
   digest is now recorded as admitted is dropped (step 2), so that
   the datagrams of every record the mirror delivered under a lead
   the receiver had not yet measured, within the bound of
   (#emission-and-cadence), those of the records mirrored while the
   raising copy was in flight included, are still admitted when
   they arrive, a late copy of one a pair has admitted is
   dropped rather than held, and a copy replayed within the
   retention re-admits nothing a pair has admitted
   ((#threat-model)); a dropped
   copy whose bytes do not match counts as nothing); `epoch` is
   below the current epoch and is not the previous epoch within the
   grace period this record meets (below; a path on which no record
   of the current epoch has yet been verified, or dropped by the
   lookup above as its byte-identical copy, has started none and
   drops no record of the previous epoch by it, so the previous
   epoch stays admitted on `manifestPort` until such a record starts
   its grace period, and on the manifest track until the
   earlier-started of the two paths' periods ends), or, when no
   record has yet been
   verified, is below
   `minEpoch` or below the pinned floor for its `kid`; `mseq <=
   highest_mseq(kid, epoch) - 64`, the `highest_mseq` this record
   meets (below; replay floor, none before a record of that
   `(kid, epoch)` has raised a `highest_mseq` this record meets, no
   upper bound);
   `mseq` is above the `mseq` that closed the epoch, once a verified
   record has closed it; `sent` is more than `7 s + maxAuthDelayMs`
   behind, or more than 6 s ahead of, the receiver's UTC clock
   (freshness: the sender's 1 s bound and the receiver's 5 s bound,
   plus, behind, the truncation of `sent` to whole seconds and the
   delivery of the twin; a receiver that widens its hold per
   (#emission-and-cadence) widens the behind tolerance by the same
   amount for a record read from the manifest track, and not for one
   on `manifestPort`); `count != (len - 132) / 32`; `hash_alg` is not in the
   receiver's accepted set, or differs from the flow's `hash_alg` once
   one is fixed; or, on a receiver that holds the catalog, `ctx`
   differs from the value recomputed from it (a receiver without the
   catalog carries `ctx` blind, (#signature-context-binding)).  The
   replay floor and the grace period a record meets are its path's:
   a record on `manifestPort` meets the `highest_mseq` and the grace
   period that the records arriving on `manifestPort`, verified or
   dropped by the lookup above as the record itself, have raised or
   started; a record read from the manifest track meets the higher
   of the two paths' `highest_mseq` values and the earlier-started
   of their grace periods.  The mirror's lead so moves no floor and
   no grace period
   a multicast copy meets: a record a relay withholds from the
   mirror, or one the mirror loses, is tested against the multicast
   path's own cadence however far the mirror leads
   ((#threat-model)), and a mirror that lags the multicast path by
   the floor brings nothing a receiver still holds.  Charge the
   per-flow verification budget, a token
   bucket of depth 64 refilled at 1000 tokens per second (a record
   read from the manifest track of (#emission-and-cadence) charges a
   second bucket of the same shape, so a flood on `manifestPort`
   cannot starve the mirror); drop and
   count a record that finds it empty (nothing before the signature
   tells a forged record from a genuine one, so a forged record spends
   the same token, (#threat-model)).  Verify the Ed25519 signature over
   `signed_message`; drop on failure, and only on success read
   `first_seq`, `flags` and the digests.  If `epoch` is above the
   current epoch, or this is the first verified record, make `epoch`
   current and the former current epoch the previous epoch, with a
   grace period on each path that ends
   `maxAuthDelayMs + 2 x manifestTimerMs` after the first record of
   the new epoch that arrives on it and is verified, or dropped by
   the lookup above as the record itself (this record starts it on
   its own path now; `manifestPort`, while no such record has yet
   arrived there, admits the previous epoch until then, and the
   manifest
   track until the earlier-started of the two periods ends, the
   sender emitting every twin of it before the new epoch's first
   record, (#emission-and-cadence)),
   fix the flow's `hash_alg` from this record if none is fixed yet, and
   hash every held datagram that has no digest yet; pending entries and held datagrams
   of the previous epoch are not flushed and live out their expiry.  A
   record of the previous epoch within the grace period it meets,
   or on `manifestPort` while that path has started none, is
   processed under that epoch's own floor and verified set and never
   changes the current epoch.
   Record `(kid, epoch, mseq)` as verified, with the time and path
   of its arrival, its `sent` and the `hash_alg` digest of its
   bytes, and raise the `highest_mseq` of the path it arrived on.
   For each
   `(digest, sequence)` of the
   record, in order: if a hold queue holds a datagram with that
   digest, admit the oldest such datagram, mark the pair as having
   admitted it, remove it from its queue and record its digest as
   admitted until `now + maxAuthDelayMs` plus the mirror's lead
   (step 2); otherwise insert the pair into the
   pending table with expiry
   `now + maxAuthDelayMs + 2 x manifestTimerMs` (240 ms at the
   defaults), plus the mirror's lead, or W on a receiver that
   applies no lead, for a record read from the manifest track
   ((#emission-and-cadence)), an entry so widened keeping its
   insertion time.  Once every pair of the record is
   processed, drop from both hold queues each datagram still held
   whose digest is now recorded as admitted: it is a copy of a
   datagram this record admitted, delivered on the other path or
   repeated on the same one, which step 2 would not have held after
   the admission; its drop is not an expiry and counts toward nothing
   ((#threat-model)).  If `flags` bit 0 is set the epoch is closed at this
   `mseq` ((#manifest-record)).

2.  **Data datagram** (on `port`).  Compute `D` with the flow's
   `hash_alg` (a datagram that arrives before the first record of the
   flow is verified is held without a digest) and look it up in the
   pending table, which maps a digest to an ordered list of sequences
   (carousels repeat byte-identical datagrams).  Hit: remove the lowest
   sequence, admit the datagram, mark the pair of the record that
   inserted the entry as having admitted it (step 1) and record `D`
   as admitted until `now + maxAuthDelayMs` plus the mirror's lead
   ((#emission-and-cadence)).  Miss: drop the datagram if `D` is so recorded
   (a copy of an admitted datagram delivered again, on any path, is
   never held); otherwise append `(D, datagram)` to the hold queue of
   its path, with expiry `now + maxAuthDelayMs + W`, each queue
   bounded to `(maxAuthDelayMs + W) x bandwidth / 8000` octets, W
   being the widening of (#emission-and-cadence) in milliseconds,
   zero on the multicast path; drop the newest on overflow and drop
   at expiry, so a MoQ unicast path that fills its queue evicts no
   multicast datagram.  Repair symbols follow the same rule,
   so an injected symbol is dropped before FEC decode.  A receiver MUST
   NOT feed a FEC instance, a keyframe overlay or the packet_id 0
   signaling consumer with a datagram of a protected flow that it has
   not admitted under step 1 or 2, on whatever carrier it arrived
   ((#broadcast-carriage)).  A FEC instance, a keyframe
   overlay or the packet_id 0 consumer that has admitted a datagram of
   a protected flow is a protected consumer, protected under each flow
   a datagram of which it has admitted (one that a source endpoint and
   a repair-only endpoint both feed, [@!MOQ-FEC] Section 6.3.6, under
   both), and a symbol admitted under any flow of the multicast object
   is an admitted symbol in every consumer it reaches: a packet of a
   track that the endpoint of a flow the consumer is protected under
   lists, reaching it over any path, a MoQ unicast path included, is a
   datagram of that flow and is admitted by this step ((#digest)).
   A consumer that has admitted none, because the receiver takes the
   track over MoQ unicast alone while its multicast join completes
   ((#multicast-endpoint-format)) or after the failover of
   (#multi-path-delivery), is a MoQ subscriber outside this profile:
   the MoQ session protects its objects, and it MAY verify them
   against the records of a `manifestTrack` ((#emission-and-cadence));
   a consumer protected under one flow of the object is such a
   subscriber for the tracks of a flow it is not yet protected under,
   as one that a repair-only endpoint feeds is for a source track the
   receiver takes over MoQ unicast ([@!MOQ-FEC] Section 6.3.6).
   On failover a receiver that reads no manifest track discards its
   protected consumers and continues as such a subscriber; one that
   does MAY keep them.  A receiver holds an endpoint while it is
   joined to its group, reads its `manifestTrack`
   ((#emission-and-cadence)) or receives the broadcast that carries
   the flow ((#broadcast-carriage)), and a consumer is protected
   under a
   flow only while the receiver holds the flow's endpoint: when the
   receiver ceases to hold one, on the failover above or on dropping
   a repair layer ([@!MOQ-FEC] Section 6.3.6), it discards that
   flow's state as on a `streamId` change (above) and, since no
   further record of the flow will arrive, the flow's hold queues
   with the datagrams they hold, a drop that is no expiry and counts
   toward nothing; the consumer ceases to be protected under the
   flow, the symbols it admitted under it staying admitted, and the
   endpoint's tracks are, for the consumer, unlisted (below) unless
   another flow it is protected under lists them.  At the admission
   that makes a consumer
   protected under a flow, the receiver discards every packet of a
   track that flow's endpoint lists that the consumer still holds and
   that it did not admit under step
   1 or 2, so that none stands, under the deduplication of item 1 of
   (#multi-path-delivery), for the admitted copy of the same symbol;
   within a protected consumer that deduplication keeps an admitted
   symbol over an unadmitted one of the same key.  For a consumer, a
   track that no endpoint of a flow it is protected under lists is
   an unlisted track, one whose symbols reach the consumer only over
   a MoQ unicast path ([@!MOQ-FEC] Section 6.3.6): a track that no
   endpoint the receiver holds lists, or one that an endpoint the
   receiver holds lists while the consumer is not yet protected
   under that endpoint's flow, its join still completing or its
   records unread, the multicast copy of such a packet being a
   datagram of that flow held by this step.  A symbol of an unlisted
   track is not a datagram of any flow the consumer is protected
   under: it MAY enter a FEC instance under that path's own
   integrity protection, which vouches for the relay and not for the
   publisher, neither anchoring nor tripping the fail-closed check of
   [@!MOQ-FEC] Section 6.3.9 (that section), and the admission that
   makes the consumer protected
   under a flow that lists the track ends this for that track, the
   discard above dropping each such symbol the consumer still holds
   and a provisional block those symbols delimited returning its
   source symbols to the undelimited state of [@!MOQ-FEC]
   Section 7.4.  The rules of this step from here to
   its end, for blocks, decodes and recovered packets, govern a FEC
   instance or keyframe overlay only while it is protected under a
   flow whose endpoint lists its source track.  One protected under
   no such flow, as one that a repair-only endpoint feeds while the
   receiver takes the source track over MoQ unicast alone
   ([@!MOQ-FEC] Section 6.3.6), the track unlisted or the join of
   the endpoint that lists it still completing, is a MoQ subscriber
   outside this profile for its blocks: the symbols it admitted
   enter its decodes as admitted symbols, its other packets are what
   the MoQ session delivers, and [@!MOQ-FEC] Sections 7.4, 9 and
   11.4 govern its blocks as those of a consumer outside this
   profile, until the admission that makes it protected under a flow
   whose endpoint lists the track (a record of that flow, from
   `manifestPort` or its `manifestTrack`, admitting a source packet
   under step 1 or this step), at which the discard above applies.
   Within a protected consumer the block
   extent such a symbol signals is provisional: a block that only
   such symbols have delimited yields to an admitted repair packet
   whose (SS_Start, SSB_length) conflicts with it under [@!MOQ-FEC]
   Section 7.4, the receiver discarding the provisional block's repair
   symbols, returning its source symbols to the undelimited state of
   that section and accepting the admitted packet, so that the
   first-accepted rule of that section discards an admitted repair
   packet only for conflict with another admitted one; such a symbol
   that conflicts with a block an admitted repair packet has
   delimited is discarded as that section requires.  Nor is such a
   symbol the later signal of [@!MOQ-FEC] Section 9 or the packet
   whose receipt anchors a block's ts there, whether or not an
   admitted repair packet later delimits the block the symbol
   delimited (that block's ts is the receipt time of the first
   packet of it, in the order received, that this profile admits),
   nor does a
   block only such symbols have delimited take any SS_ID out of a
   run or stand as the S_prev of the Group range of [@!MOQ-FEC]
   Section 7.5: within a protected consumer such a block is held for
   decoding only, has no ts and no FEC deadline, whatever packets
   are admitted into or above its range before or after the symbol,
   and requests no repair, and the SS_IDs in its range that the
   receiver lacks are, for [@!MOQ-FEC] Sections 9 and 11.4, runs
   between the packets the receiver has admitted and the blocks
   admitted packets have delimited, as if the provisional block were
   not delimited, each revealed and given its ts only by a packet
   admitted above it, whether the symbol delimited the block before
   or after that packet, and classified, requested and cancelled as
   those sections specify; what the block decodes before such a
   run's deadline is admitted by its digest, as below, and closes
   the run or part of it.  A relay could otherwise, by one repair
   packet whose SS_Start lies above what the publisher has sent,
   give the SS_IDs below it a deadline they reach unrecovered, by
   one whose range begins at an SS_ID the receiver admitted long
   ago, delimit a block that takes its ts from that old admission
   and is past its deadline on arrival, by one whose `SSB_length`
   reaches past what the publisher is sending, delimit a block that
   reaches a deadline before the rest of its range is sent, and
   force the repair request of [@!MOQ-FEC] Section 11.4.2 any of
   those ways, or, by one whose range covers a run that has a ts,
   take the run's deadline and repair request away, or, by one whose
   range ends just below a lost SS_ID, narrow the run's Group range
   to exclude the block that contains it.  Under the
   open-block bound
   of [@!MOQ-FEC] Section 9 the receiver discards a block that has
   no ts before any block that has a ts, whether or not the track
   derives an FEC deadline, so that the
   blocks such symbols delimit, however many a relay sends, evict
   under a memory cap no block of the multicast path; such a discard
   gives the block no deadline and no class, forces no repair
   request, drops the block's repair symbols and returns its source
   symbols to the undelimited state of [@!MOQ-FEC] Section 7.4.  The
   receiver
   decodes a block from admitted symbols where they suffice and uses
   such symbols only for the shortfall.  A packet the base instance
   recovers with such a symbol's help is admitted by its digest like
   a received datagram, against the pending entries of its window,
   hashed with the base SS_ID its position in the base block implies
   (SS_Start + ESI, [@!MOQ-FEC] Section 8.3) appended for the hash
   only ([@!MOQ-FEC] Sections 7.3 and 8.5), and on a miss is held in
   the MoQ unicast path's hold queue, under that queue's expiry and
   bound, since only such a symbol, which that path alone delivers,
   made the decode possible, so that its octets and its expiry count
   toward nothing of the multicast path.  A recovered packet that
   leaves the queue unadmitted, at expiry or on overflow, is not a
   symbol the receiver holds for [@!MOQ-FEC] Section 11.4: a block
   of which the receiver has not admitted every one of its
   SSB_length source symbols, received or recovered, is unrecovered
   for that section and for the release below, at its FEC deadline
   as at any other time, the receiver keeping the packets it admitted
   (a decode none of whose recovered packets is admitted recovers
   nothing, a corrupt symbol among those decoded from corrupting
   what the decode recovers), and it SHOULD discard the symbols of
   unlisted tracks that fed a decode that left the block unrecovered
   and decode again when the symbols it then holds suffice, at most
   once more per block with such symbols' help: a block that two
   such decodes have left unrecovered takes no further symbol of an
   unlisted track into a decode, since a relay could otherwise drive
   one decode of the block per symbol it sends, while a decode from
   admitted symbols alone, and the admission of a held packet, remain
   open to it; a held
   packet admitted after the deadline recovers the block as a
   received datagram admitted then would, and the receiver SHOULD
   cancel a repair FETCH then outstanding for it, as [@!MOQ-FEC]
   Section 11.4.2 has it for a repair the next RAP makes moot.  A
   packet recovered from admitted symbols
   alone, by the base instance or a keyframe overlay, is admitted with
   them; a packet only the overlay recovers with the help of such a
   symbol has no base SS_ID to hash with ([@!MOQ-FEC] Section 7.3) and
   is not delivered.  A receiver that can request unicast repair
   ((#per-block-unicast-repair)) keeps, instead of letting them
   expire, the pending entries of each open block that has an FEC
   deadline: those pending at the admission of the first packet,
   source or repair, that the receiver admits into the block, and
   those inserted after it (a mirrored record's entries are
   inserted up to the lead before the datagrams they cover arrive
   on the multicast path, and under the bound of
   (#emission-and-cadence) until the stream generation has measured
   a lead, so no span reckoned from the lead in force at the
   admission names them all; the admitted packet is not necessarily
   the packet
   whose receipt set the block's ts in [@!MOQ-FEC] Section 9: a
   datagram held on a miss is admitted, by step 1, after one that a
   verified record admitted on arrival, and a symbol of an unlisted
   track no step admits, nor does one set a ts, so a block only such
   symbols have delimited has no deadline and keeps no entries as a
   block, the lost SS_IDs in its range keeping theirs as the runs
   they are, below), until that
   deadline (the receiver keeps the admission time with the block).
   A
   run of lost SS_IDs that the receiver has not delimited
   ((#per-block-unicast-repair)) is one such block ([@!MOQ-FEC]
   Section 11.4) of which it holds no packet, and the receiver
   learns of the run, and of the block's deadline, only from a packet
   admitted above it ([@!MOQ-FEC] Sections 7.4 and 9; step 2), by
   when the run's entries would have expired; so for each base
   instance it also keeps the entries pending at the admission of
   the source packet of highest SS_ID it has admitted, and those
   inserted after it
   (keeping that admission time with the instance; a symbol of an
   unlisted track, which no step admits, is never
   this anchor however high its SS_ID) until it admits a source
   packet of the instance above that SS_ID; a source packet admitted
   below it moves neither that anchor nor the entries so kept
   (highest, above and below in SS_ID, and the gap below, under the
   serial number arithmetic of [@!MOQ-FEC] Section 7.5, so that the
   anchor follows SS_ID across its wrap to 0).  A gap
   in SS_ID between the two reveals lost SS_IDs, of such a run or of
   a block that a repair packet alone has delimited ([@!MOQ-FEC]
   Section 7.4); each takes the entries so kept as its own from the
   admission of the source packet of highest SS_ID admitted at or
   below its lower bounding packet (lower and upper in SS_ID order,
   [@!MOQ-FEC] Section 11.4.1; a bounding packet can itself be such
   a symbol), or of the packet admitted above it where the instance
   has admitted none below it;
   otherwise the entries whose expiry has passed by the admission of
   the packet above are released.  The blocks that the admitted
   repair packets a run's Group range FETCH returns delimit take
   over the entries so kept; a block that only symbols of an
   unlisted track the response returns have delimited is provisional
   as above and takes none, the run keeping its entries, against
   which the decode of that block admits its recovered packets,
   until the run is recovered or its requested repair, the FETCH on
   each layer it needs ([@!MOQ-FEC] Section 11.4.2), completes
   without recovering it, fails or is cancelled.
   They are block state under the bound of [@!MOQ-FEC] Section 9 and
   are released when the block is recovered, when its deadline passes
   with no repair requested, when a requested repair, the FETCH on
   each layer it needs, completes without recovering the block, fails
   or is cancelled ([@!MOQ-FEC] Section 11.4.2), or when the block is
   discarded under that bound.

**Replay.** Receivers in an explicitly configured DVR or replay mode
MAY relax the epoch, floor and freshness checks.  **Clock.** The
freshness check needs a receiver clock synchronized to UTC within
5 s.  A receiver without one MAY skip that check alone; it
then accepts any window of the current epoch at join and has no
protection against replay of the epoch's earlier windows until its
first verified record sets the floor ((#threat-model)).

**Key rotation.** A key change is an epoch change
((#manifest-record)).  The publisher adds the next `kid` to the
catalog with the `firstEpoch` at which it will sign, at least one
catalog lifetime ahead; signs with it from that epoch; and raises
`minEpoch`.  A receiver that holds that catalog accepts the retired
`kid` below the successor's `firstEpoch` only, so the retired key can
sign for it on `manifestPort` until the first record of the new
epoch is verified there or dropped there by the already-verified
lookup of step 1 as its byte-identical copy, and within the
previous epoch's grace period after that, and on the manifest track
within the earlier-started of
the two paths' periods (step 1 of
(#receiver-enforcement-and-state)); a
receiver whose catalog or pin predates the rotation is exposed to the
retired key until it re-fetches or is re-provisioned
((#threat-model)).  A record with an unknown `kid` triggers at most
one catalog re-fetch per 30 s per receiver; until then such records
are dropped.  Whenever a re-fetch or a re-provisioning changes the key
set or a `kid`'s range, the receiver re-applies the range check of
(#catalog-signaling) to the `(kid, epoch)` that set each flow's
current epoch; where it now fails, the receiver discards that flow's
state as it does on a `streamId` change (above), the `digest` of
every held datagram included, and returns to the join state of step
1, so a record a retired key signed before the re-fetch cannot hold
the flow afterwards.  Revocation is key removal,
effective within one catalog lifetime.

**Cost.** A datagram from another source costs one address comparison;
one that spoofs `S`, or that a relay delivers on a MoQ unicast path,
costs one hash, two lookups and, on a miss of both, space in its
path's hold queue until expiry, so a copy of an admitted datagram costs one hash and two
lookups; an injected record costs at most one
verification inside the budget, a replayed one whose
`(kid, epoch, mseq)` is still verified one lookup and one hash
whatever its age (the already-verified lookup of step 1 precedes the
freshness check), one outside the verified set and outside the
freshness tolerance that lookup alone, a miss, before the epoch
floor, the replay floor or the freshness check drops it, the second
copy of a verified record one lookup and one hash plus, where the
first arrived on the manifest track and this is the first copy on
`manifestPort` and raises the mirror's lead, the re-handling of its
own pairs and of the pairs kept for the records mirrored while it
was in flight, which no later copy of the record repeats and which
the lead's rise by multiples of `manifestTimerMs`
((#emission-and-cadence)) bounds to `5000 / manifestTimerMs` raises
in a stream generation, 250 at the default, each over at most the
records the manifest track's bucket admitted within the raised lead
(step 1),
and a corrupt symbol
of an unlisted track
at most two decodes of its block.  With one verification per 37
datagrams, a Cortex-A53 without
SHA2 instructions spends about 0.26 of a core at 100 Mbit/s and at
most 0.43 of a core under a record flood at a budget of 1000/s, or
0.6 of a core on a receiver that also reads the manifest track, whose
second bucket admits another 1000/s; a core with SHA2 instructions
spends a fraction of that.

### Threat Model

This profile protects against off-path and on-segment UDP injection,
against corrupted or attacker-injected FEC symbols, and against
replay: a `(record, datagrams)` pair cannot be moved to another
endpoint, stream generation, broadcast, key or epoch
((#signature-context-binding)); an earlier epoch is rejected at join
by `minEpoch` ((#catalog-signaling)) and, on a receiver that pins
keys, by the epoch floor kept with the pin, and after the first
verified record by the current epoch, the previous epoch admitted
on `manifestPort` until the first record of the current epoch is
verified there or dropped there by the already-verified lookup of
step 1 as its byte-identical copy, and within its grace period
after that, and on the manifest track within the earlier-started
of the two paths' periods
((#receiver-enforcement-and-state)); and
within an epoch a receiver with a UTC-synchronized clock admits no window whose record was
emitted more than `7 s + maxAuthDelayMs` before receipt, so the verification
budget cannot be spent with stale genuine records and the replay floor
of (#receiver-enforcement-and-state) takes over after the first
verified record.  A receiver that skips the freshness check can be fed
the current epoch's earlier windows at join, and an injector that
keeps its budget spent can hold it there; a unicast receiver that
widens its tolerance by W ((#emission-and-cadence)) can likewise be
started at a window up to W old, 5 s at most, by the relay that
buffers for it.  What a relay delivers to a consumer, of the tracks
a flow's endpoint lists, before the admission that makes the consumer
protected under that flow is discarded at that admission unless
admitted by then ((#receiver-enforcement-and-state)), so a relay
that leads the multicast path during the join cannot leave its own
copy of a symbol in place of the admitted one.  A relay that leads
the multicast path and withholds records from the mirror moves no
replay floor and no grace period the multicast copies of those
records meet, each path keeping its own (step 1 of
(#receiver-enforcement-and-state)), so a healthy multicast path
loses no window to what the mirror omits, absent the injector of the
availability paragraph below, and a relay that lets the
receiver measure a small lead and then leads by more, within the
bound of (#emission-and-cadence), gains nothing either, the copy on
`manifestPort` that raises the lead re-admitting
or re-inserting, under the raised lead, ahead of their datagrams,
the digests of that
record and of the records mirrored while it was in flight, for the
pairs that have admitted nothing and have no pending entry, widening
the pending entries of those records by the raised lead, and
recording again as admitted, under the raised lead, the digests of
the pairs that have, so that a copy an injector replays within the
retention, which measures nothing, re-admits no datagram and a late
multicast copy of a datagram the relay delivered is dropped rather
than held
(step 1 of (#receiver-enforcement-and-state)).  Because every endpoint of a
sending entity that carries `auth` is protected
((#catalog-signaling)), an endpoint without `auth` cannot share a FEC
instance, a keyframe overlay or the signaling sub-flow with a
protected one.

Catalog rewrite and key substitution are defended only for receivers
that hold an out-of-band key pin.  The digest algorithm is inside the
signed record, so a rewrite can remove `auth`, substitute keys or
lower `minEpoch`; the pin catches the first two and the per-`kid` epoch
floor kept with it ((#receiver-enforcement-and-state)) the third,
except at a receiver's first join under a `kid`, where a lowered
`minEpoch` admits records of an earlier epoch signed with a
still-listed `kid` until a record of the current epoch is verified,
so rotated-out keys SHOULD be removed promptly.  A rewrite that
raises `minEpoch` costs a receiver, pinned or not, that session's
data and nothing more, since neither carries a catalog value past the
session ((#receiver-enforcement-and-state)).
Rewriting any other member of the endpoint or its `auth`
only makes genuine records fail the signature or `ctx` check, or
resizes the hold queues and pending expiry (`bandwidth`,
`maxAuthDelayMs`, `manifestTimerMs`), which a receiver bounds by local
policy ((#catalog-as-attack-surface)).

The profile protects integrity, not availability.  A forged record
passes every check of step 1 of (#receiver-enforcement-and-state) up
to the signature, so each one spends a token of the verification
budget: an attacker who sustains more than 1000 records per second on
the manifest port (about 1.3 Mbit/s of 164-octet records) takes a
share of the budget proportional to its rate, and at several times
that rate both copies of a window lose their tokens and the flow
yields no data.  The budget bounds the receiver's CPU, and the
lead's rise by multiples of `manifestTimerMs` bounds the
re-handling a raise costs outside it (Cost,
(#receiver-enforcement-and-state)); it does not
raise the cost of this attack, and the record flood is not the
cheapest availability attack on every protected flow: a datagram on
the data port that matches no pending entry is held on the
multicast path until it expires (step 2 of
(#receiver-enforcement-and-state)), and those expiries are loss for
the failover below, so an injector that sustains, with the same
access as the record flood, the loss fraction at which the receiver
fails over moves it to the unicast fallback for less than the 1000
records per second the record flood needs wherever that fraction of
the flow's packet rate is below it, as on every audio flow and most
low-rate video; only evicting genuine datagrams, by overflowing the
multicast path's hold queue, needs the endpoint's bandwidth (a relay
on a MoQ unicast path can fill only its own path's queue, without
spoofing, and that path's availability is already its to withhold; a
symbol of an unlisted track it delivers gives no block or run a ts or
a deadline, whatever admitted packets lie in its range, takes no
SS_ID out of a run, and delimits a block that is decoded only, never
requested, the SS_IDs it covers that the receiver lacks staying runs
that admitted packets alone reveal, and the
blocks only such symbols delimit are discarded under the open-block
bound of [@!MOQ-FEC] Section 9 before any block that has a ts,
so it forces no repair request, evicts no block of the multicast
path and fails no check of [@!MOQ-FEC] Section 6.3.9 closed, step 2
of (#receiver-enforcement-and-state); a
corrupt symbol of an unlisted track it delivers leaves unrecovered
only a block the admitted symbols could not recover alone, costs at
most two decodes of that block, and what a decode it corrupts
recovers is held on, and expires from, that relay's own queue, step
2 of (#receiver-enforcement-and-state)).
A receiver that reads the manifest track
has a second bucket of the same shape, so its ceiling is 2000
verifications per second, half of them spendable by its relay without
spoofing anything (Cost, (#receiver-enforcement-and-state)).  On an SSM endpoint
reached natively either flood must spoof `S` or be on path; on an ASM
endpoint any host that can send to the group suffices, and so it does
behind an AMT gateway, where a flood need only spoof the relay's
address toward the gateway ((#receiver-enforcement-and-state)).  With
that access an injector forges nothing: a genuine record it reads
from the manifest track, as any subscriber can, and sends on
`manifestPort` more than `maxAuthDelayMs + 2 x manifestTimerMs`
(240 ms at the defaults) before the multicast path delivers the
datagrams it covers is verified there with unwidened pending
entries, which expire before those datagrams arrive, so they are
held, and the sender's own copy, dropped by the already-verified
lookup, admits nothing (step 1 of
(#receiver-enforcement-and-state)); one record per window is then
loss of every window for the failover below, at most 50 a second
at the default `manifestTimerMs` on a flow the timer governs and
one per 37 datagrams on a flow above 1850 datagrams a second
((#emission-and-cadence)), less than the data-port injection above
needs wherever the failover fraction of the flow's packet rate
exceeds that window rate, above 50 a second on the former and above
a thirty-seventh of the packet rate on the latter.  On a receiver
that reads the manifest track the outcome turns on arrival order.
For a record the receiver's mirror delivers before the injector's
copy, that copy, replayed from the mirror ahead of the sender's, is
the record's first copy on `manifestPort` and measures the lead, so
the sender's copy and the twin measure nothing and the re-handling
that a raising copy affords (step 1 of
(#receiver-enforcement-and-state)) is not afforded against it.
Where no larger interval has been measured in the stream generation
this pins the lead at the injector's replay interval, rounded up to
a multiple of `manifestTimerMs` as step 1 rounds it, so the entries
of every later record the mirror delivers are widened by that lead
alone and are short of their datagrams wherever the mirror delivers
the record more than that lead plus
`maxAuthDelayMs + 2 x manifestTimerMs` before the multicast path
delivers the datagrams it covers, which the geometry of the attack
(the injector's copy preceding those datagrams by more than
`maxAuthDelayMs + 2 x manifestTimerMs`) meets up to the rounding,
under `manifestTimerMs`: they are held and expire as a record the
injector's copy brings to `manifestPort` first does below, the
attack succeeding for every such record whose first copy on
`manifestPort` the injector keeps supplying, with no race against
the mirror to win.  It ends at the first such record whose first
copy on `manifestPort` is the sender's (the injector idle, or its
copy lost or arriving after the sender's): that copy measures the
interval from the mirror's delivery to its own arrival, which the
geometry puts above the pinned lead, raises the lead to it (capped
at the bound of (#emission-and-cadence)) and affords the re-handling
of step 1 of (#receiver-enforcement-and-state), so that from then
the next case applies.  A lead the sender's copies measured larger,
before the injector began or at such a record, is never lowered
((#emission-and-cadence)) and keeps widening the entries of mirrored
records, so their datagrams are admitted on arrival and the attack
fails for such a record while the interval from the mirror's
delivery of a record to the multicast path's delivery of the
datagrams it covers stays within that lead plus
`maxAuthDelayMs + 2 x manifestTimerMs`; an interval that later grows
past it is not absorbed, since the sender's copy that would have
raised the lead and afforded that re-handling is dropped by the
lookup and measures nothing, so those datagrams are held and expire
as below.  A record the injector's copy brings to `manifestPort`
before the receiver's mirror delivers it is verified there with
unwidened entries whatever lead the receiver has measured, and the
mirror's later copy, dropped by the already-verified lookup,
measures nothing and widens nothing (step 1), so its datagrams are
held and expire as on a receiver that reads no manifest track; an
injector wins that race on every record where its copy reaches the
receiver sooner than the receiver's mirror does, its read of the
manifest track and its injection path to the receiver counted
together against the mirror's delivery delay.  The
injector's copy also raises the `highest_mseq` of `manifestPort` and
starts its grace period early, which drops a record the mirror lost
or the relay withheld only where the injector's copies lead the
multicast path at the receiver by 64 windows, less the windows by
which the record's twin lags it where the record's own copy was lost
on the multicast path as well (two at the RECOMMENDED placement of
(#emission-and-cadence), up to 63 under its bound, which assumes
that only the sender's records raise the floor of step 1), and a
record of the previous epoch once a grace period so started has
run.  The first needs a mirror that leads the multicast path at the
receiver by that many windows; the second, one that leads it by
more than `maxAuthDelayMs + 2 x manifestTimerMs` (240 ms at the
defaults), a lead within the bound of (#emission-and-cadence) on
any flow: the injector's copy of the new epoch's first record
starts the period that long before the multicast path delivers that
record, which the last twins of the previous epoch immediately
precede ((#emission-and-cadence)), so a record of the previous
epoch, its own copy or its twin, that arrives on `manifestPort`
within the excess of the lead over the period before that record
is dropped, and a window of the previous epoch every copy of whose
record so arrives, the mirror having lost it or the relay withheld
it, expires.  The injector chooses which mirror it reads but makes
no mirror deliver earlier, and the statements of this section about
a relay assume no such sender on the group.  Datagrams
that
expire from the multicast path's hold queue are loss for the failover
of (#multicast-endpoint-format) and (#multi-path-delivery), those
that expire from the unicast path's queue are not, a held copy that
step 1 drops because a record admitted another copy of the same
datagram expires from neither, and, absent such an injector, a relay
that leads the multicast path by no more than the bound of
(#emission-and-cadence) produces none, its admitted digests and
pending entries outliving the lead the receiver applies, which that
bound caps (step 1),
the copy on `manifestPort` that raises that lead, when the relay
leads by more than the receiver has measured, re-admitting or
re-inserting, under the raised lead, before their datagrams arrive,
the digests of that
record and of the records mirrored while it was in flight, for the
pairs that have admitted nothing and have no pending entry, widening
the pending entries of those records by the raised lead, and
recording again as admitted, under the raised lead, the digests of
the pairs that have, so that the late multicast copies of datagrams
the relay delivered are dropped as copies rather than
held, and what the relay delivers or withholds on the mirror
moving no replay floor and no grace period a multicast copy meets
(step 1 of (#receiver-enforcement-and-state)); a receiver
SHOULD also count records that
the `manifestPort` bucket dropped for want of a token toward that
failover, so a sustained record flood ends in the unicast fallback of
(#emission-and-cadence), a MoQ subscription outside this profile
unless the receiver verifies it against the records of a
`manifestTrack` (step 2 of (#receiver-enforcement-and-state)), rather
than in silence.
Records the manifest-track bucket dropped count toward nothing of the
multicast path: a relay that floods the mirror could otherwise move a
receiver with a healthy multicast path onto itself.  A receiver that holds the catalog naming the successor key accepts
the retired `kid` only below the successor's `firstEpoch`
((#catalog-signaling)), and records of the previous epoch on
`manifestPort` until the first record of the new one is verified
there or dropped there by the already-verified lookup of step 1 as
its byte-identical copy, and for
`maxAuthDelayMs + 2 x manifestTimerMs` after that, and on the
manifest track within the earlier-started of the two paths' periods
(step 1), so for that receiver a key retired at an epoch boundary
can sign for that long after the new epoch's first record is
verified on a path, or dropped there as such a copy, at most (an
attacker on the
multicast path can keep the new epoch from reaching it, as it can
drop anything there, and holds the previous epoch open on that path
for as long as it does); a
receiver with an older catalog is exposed to the
retired key until it re-fetches, one catalog lifetime plus the 30 s
re-fetch interval of (#receiver-enforcement-and-state) at most, and a
pinned receiver until it is re-provisioned.

Losing both copies of a window leaves at most 37 datagrams
unauthenticated, which expire from the hold queues.  Latency of
authentication is bounded by `maxAuthDelayMs` on the multicast path
and by `maxAuthDelayMs + W` on a MoQ unicast path, W being the
widening of (#emission-and-cadence).  Digest `i` of a record
covers `sequence = first_seq + i`, so loss and reordering within a
flow are detectable ([@?I-D.ietf-mboned-multicast-security] Section
2.3), and no mode of this profile delivers an unauthenticated datagram
(Section 2.4.4 of that document).

### Broadcast Carriage

Hybrid receivers that also hold the MoQ catalog verify datagrams of
the flow from any path, a MoQ unicast path included, against the same
records ((#digest)); a symbol of an unlisted track, one that no
endpoint of a flow the consumer is protected under lists, is not a
datagram of any such flow, and what it helps the base instance
recover is admitted by digest ((#receiver-enforcement-and-state)).  A
broadcast carries the flow as an MMTP service ([@!ATSC-A331]
Section 8.1.2.1; [@?ARIB-B60]): the flow's datagrams are the MMTP
packets of one MMTP session, carried as the UDP datagrams the sender
emits, each the whole MoQ UDP payload, trailer included, on the
endpoint's `S`, `G` and `port`, and the records are the sender's
record datagrams on `manifestPort` of the same `S` and `G`, both
copies ((#emission-and-cadence)), carried in the same IP multicast
of the broadcast.  A broadcast that re-addresses either flow, or
carries the datagrams in any other form, is not covered: the
pseudoheader binds `S`, `G` and the ports ((#digest)), and a record
verifies as it was signed or not at all.  A broadcast-only receiver
reads both UDP flows of the broadcast, forms the pseudoheader and
`signed_message` from the endpoint's `S`, `G`, `port`, `streamId`
and `manifestPort`, and holds those values and the keys by
provisioning ((#receiver-enforcement-and-state)): the SLS of the
service describes the MMTP session ([@!ATSC-A331] Section 7.2) and
nothing of this profile, so `manifestPort` and the rest come from
provisioning alone, and this document specifies no in-band carriage
of them.  A record so read is a record on `manifestPort` for step 1
of (#receiver-enforcement-and-state), as on any multicast path.

### Hash Algorithms

`hash_alg` is a Suite ID of the IANA Named Information Hash Algorithm
Registry ([@!RFC6920] Section 9.4), a value from 0 to 63; values 64
to 255 are not Suite IDs and MUST NOT be sent.  Only a suite whose
output is 256 bits is usable, since every digest field is 32
octets; the truncated suites MUST NOT be used.  Suite 1, sha-256
[@!FIPS180-4], is mandatory to implement.  A receiver MAY implement
other 256-bit suites; it drops a record whose `hash_alg` it does not
implement ((#receiver-enforcement-and-state)).

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

- **Resource claims**: `bandwidth`, `maxAuthDelayMs` and
  `manifestTimerMs` size the hold queues and pending table of
  (#receiver-enforcement-and-state) and, with the manifest track's
  verification budget, the records verified on that track which a
  receiver retains for as long as the freshness check of step 1
  would pass a copy of them on `manifestPort`, each with the pairs
  kept until its first `manifestPort` copy arrives; the widening W
  of (#emission-and-cadence) enlarges the unicast path's queue and,
  on a receiver that applies no lead, the pending expiry of a
  mirrored record's entries, and the mirror's lead that expiry, the
  admitted-digest set and the entries kept for unicast repair (step
  2, those pending at an admission), both receiver-chosen and capped
  at 5 s.  A
  receiver bounds all of these
  by local policy, and the
  pending entries it keeps for unicast repair by the open-block bound
  of [@!MOQ-FEC] Section 9.

# IANA Considerations

This document has no IANA actions.  `hash_alg` values are Suite IDs
of the Named Information Hash Algorithm Registry ([@!RFC6920]
Section 9.4), which this document does not change, and the multicast
catalog extension (Section 4) requires no registration.

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
    <date year='2026' month='April'/>
  </front>
  <seriesInfo name='ATSC' value='A/331:2026-04'/>
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

<reference anchor='FIPS180-4' target='https://doi.org/10.6028/NIST.FIPS.180-4'>
  <front>
    <title>Secure Hash Standard (SHS)</title>
    <author>
      <organization>National Institute of Standards and Technology</organization>
    </author>
    <date year='2015' month='August'/>
  </front>
  <seriesInfo name='FIPS PUB' value='180-4'/>
</reference>


# Test Vectors: bc-provenance Version 2

This appendix is informative.  It gives one worked `bc-provenance`
version 2 example with `hash_alg` 1 (sha-256, (#hash-algorithms)):
one endpoint, key and two datagrams and one signed record with
`count` 2; its twin is byte-identical.
Octet strings are hexadecimal, the IPv4 addresses dotted decimal and
other integers decimal unless prefixed 0x; the Ed25519 secret seed
is included only so the vectors are reproducible.

Common inputs:

~~~
ed25519 secret seed : 000102030405060708090a0b0c0d0e0f
                      101112131415161718191a1b1c1d1e1f
ed25519 publicKey   : 03a107bff3ce10be1d70dd18e74bc099
                      67e4d6309ba50d5f1ddc8664125531b8
S, G                : 198.51.100.7, 232.10.20.30 (IPv4)
port                : 5004 (src_port = dst_port)
manifestPort        : 5005
streamId            : 2864434397 (0xaabbccdd)
kid, epoch, mseq    : 1, 17, 1
first_seq           : 1000
flags               : 0x00
sent                : 1792972800 (0x6ade9800, 2026-10-26T00:00:00Z)
namespace           : ["example.arena"] (f = 1)
endpoint packetIds  : [1, 2]
params (for params_hash):
  codec="avc1.640028" timescale=90000 groupDurationTicks=3000
  fecAlgorithm="raptorq" sourceSymbols=32 repairSymbols=16
  symbolSize=1312 interleaveDepthMs=133
datagram 0 payload  : 0x11 repeated 1400 times
datagram 1 payload  : 0x22 repeated 1400 times
pseudoheader (20)   : c6336407e80a141e00110578138c138c
                      aabbccdd
signed_message prefix (32 octets, "mcast-manifest-v2" NUL
streamId S G manifestPort):
                      6d636173742d6d616e69666573742d76
                      3200aabbccddc6336407e80a141e138d
~~~

The signed message is the 32-octet prefix followed by the first 132
octets of the record.

~~~
D_0                 : 7ead4d8be7d24e08d7075bbac8fbe777
                      9ab3b8f1c47d3f8be4d2a514f2ec2069
D_1                 : 6f7d9007e81b73c9f54aff8c2f66bd6e
                      8956bfa7e001789b986c328f9ed78751
params_hash         : 1f652ba84e4a44425da55ddffb24c079
                      1a3851a1d1022b4b47b30881146edf7c
ctx                 : fe68177dd329ee6fdd668cb43ebdeb6d
                      2e4c2ae351fd25050ab68dd98af19214
signature           : 9d5154a8e6beb7c472a09fa1e1d3d426
                      b6042519343728835ed5c9416e615aad
                      7ad335c0f0403aa8985e6b6979e5918d
                      3d28e787ca29d55447930777c380d808
~~~

Record (196 octets):

~~~
4d484d32000000010000001100000000
0000000100000000000003e800020100
6ade9800fe68177dd329ee6fdd668cb4
3ebdeb6d2e4c2ae351fd25050ab68dd9
8af192147ead4d8be7d24e08d7075bba
c8fbe7779ab3b8f1c47d3f8be4d2a514
f2ec20696f7d9007e81b73c9f54aff8c
2f66bd6e8956bfa7e001789b986c328f
9ed787519d5154a8e6beb7c472a09fa1
e1d3d426b6042519343728835ed5c941
6e615aad7ad335c0f0403aa8985e6b69
79e5918d3d28e787ca29d55447930777
c380d808
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
  [@!ATSC-A322], and `slsUri` acquires the SLS of an MMTP service,
  its MP table included ([@!ATSC-A331] Section 7.2), in place of
  the S-TSID with FEC parameters of -00.
- Section 5: the paragraph on LOC and CMAF objects now refers to the
  mmtp rendition rule of Section 4.1.  It no longer says that
  multicast carriage uses MMTP "regardless of a track's unicast
  packaging".  The catalog-derived FEC configuration now also covers
  the Reed-Solomon parameters ([@!MOQ-FEC] Section 4.5).  The
  transport table drops the QUIC datagram row, because [@!MOQ-MMT]
  Section 4.3 sends the objects of an mmtp track only in subgroups.
  The mapping of MMTP packets onto Multicast QUIC DATAGRAM frames,
  and the use of [@!MOQ-FEC] on that channel, are now described,
  informatively, in [@!MOQ-FEC] Section 11.3, which that document's
  -01 makes informative, rather than specified there.
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
  end them with STOP_SENDING, and resumes paused ones on failover.  It
  keeps any repair layer that no endpoint carries and that it combines
  with multicast source symbols.
- Editorial: the Abstract and Section 1 expand MMTP, AMT and
  DRIAD.  Section 1 no longer calls failover seamless,
  Section 1.1 calls multicast an additional delivery path instead of
  an optimized one, and Section 3 calls MoQ/WebTransport the fallback
  that every client supports instead of the universal fallback.  The
  examples of Section 4.1 use a documentation address.
- References: [@!MOQ-MMT] and [@!MOQ-FEC] now name their -01
  revisions, and [@!MOQ-FEC] lists both of its authors.  ATSC A/331,
  ATSC A/322, ARIB STD-B60 and FIPS 180-4 are now cited; BLAKE3 is no
  longer cited.
- (#content-authentication) replaces bc-provenance version 1 with
  version 2; the BCPV1 `manifest_object`, its "BCPV1-sig" prefix,
  the `compaction` member, the Merkle Tree Hash and the 198-octet
  test vector are withdrawn.
- The digest is hash-agile: `hash_alg` is a Named Information Suite
  ID ((#hash-algorithms)) and sha-256 is the only mandatory
  algorithm.  The keyed `authScope` is removed (`S`, `G`, the ports
  and `streamId` separate domains).
- Receivers that implement the profile enforce it; the "shadow" and
  "off" modes and the `enforcement` member are removed.
- The catalog `auth` object gains a REQUIRED `version` member, 2
  ((#catalog-signaling)); `keys`, each entry with a `firstEpoch`,
  replaces `publicKey`, `keyId` and `previousKey`; `minEpoch`
  is added; `hash`, `compaction` and the `tracks` array (`mediaTrack`,
  `authScope`, `sourceSymbolFormat`) are removed.  A protected
  endpoint carries an `auth` object of its own: `manifestPort`,
  `streamId`, `senderAddress`, `maxAuthDelayMs`, `manifestTimerMs`,
  and `manifestTrack`, which moves there from the `tracks` entry and
  becomes OPTIONAL.
- A `multicast` object that carries `auth` requires `auth` on every
  endpoint ((#catalog-signaling)).
- A packet of a track the endpoint lists is a datagram of the flow
  on every path that delivers it to a consumer protected under the
  flow, one that has admitted a datagram of it, a MoQ unicast path
  included, and is verified against the same records, a consumer
  that several endpoints feed being protected under each and a
  symbol admitted under any flow of the object being admitted in it,
  a consumer being protected under a flow only while the receiver
  holds its endpoint, joined to its group, reading its
  `manifestTrack` or receiving the broadcast that carries the
  flow, and leaving one discarding that flow's state and
  hold queues, ending the protection under it and keeping what was
  admitted; only a symbol of an unlisted track, one that no endpoint
  of a flow the consumer is protected under lists, a held endpoint's
  track the consumer is not yet protected under included until the
  admission that makes it so, and that a MoQ unicast path alone
  therefore delivers to it, is outside every such flow and MAY enter
  a FEC
  instance under that path's own protection, a block that only such
  symbols have delimited yielding to an admitted repair packet that
  conflicts with it; the block rules of step 2 govern a FEC instance
  or keyframe overlay only while it is protected under a flow whose
  endpoint lists its source track, one protected under no such flow,
  as one a repair-only endpoint feeds while the source track comes
  over MoQ unicast alone, being a MoQ subscriber outside the profile
  for its blocks until a record of a flow that lists the track admits
  a source packet.  A packet recovered from admitted symbols
  alone is
  admitted with them, the receiver decoding from admitted symbols
  where they suffice; a packet the base instance recovers with such a
  symbol's help is admitted by its digest, hashed with the base SS_ID
  its block position implies, a miss held in the MoQ unicast path's
  hold queue, and a block is recovered only once every one of its
  source symbols is admitted, a recovered packet dropped unadmitted
  at expiry or on overflow leaving it unrecovered, the receiver then
  SHOULD discard the unlisted-track symbols that fed the decode and
  decode again when what it holds suffices, at most once more per
  block with such symbols' help, and a held packet admitted after
  the FEC deadline recovers the block, the receiver then SHOULD
  cancel a repair FETCH outstanding for it; a
  packet only the overlay recovers with such help is not delivered,
  and a symbol of an unlisted track gives no block or run its ts or
  FEC deadline and neither anchors nor trips the fail-closed check
  of [@!MOQ-FEC] Section 6.3.9, a block only such symbols delimit
  being decoded
  only, with no ts and no deadline, the lost SS_IDs in its range
  staying runs that a packet admitted above them reveals, and a
  block with no ts being
  discarded under the open-block bound before any block that has a
  ts.
  A copy
  of an admitted datagram delivered again is never held, whether
  step 1 or step 2 admitted it.  At the admission that makes a
  consumer protected under a flow it discards what it holds,
  unadmitted, of the tracks that flow's endpoint lists, and its
  deduplication keeps an admitted symbol over an unadmitted one.  A
  track taken over MoQ unicast
  alone, before the multicast join completes or after failover, is
  a MoQ subscription outside the profile unless the receiver
  verifies it against the records of a `manifestTrack`
  ((#receiver-enforcement-and-state), (#emission-and-cadence)).
- A receiver that can request unicast repair keeps the pending
  entries of an open block with an FEC deadline and, since a run of
  lost SS_IDs is revealed only by a packet admitted above it, those
  pending at the admission of the source packet of highest SS_ID
  each base instance has admitted and those inserted after it,
  as block state under the bound of [@!MOQ-FEC] Section 9; step 1
  drops
  the other held copy of a datagram it admits, which counts toward
  nothing; a record meets a 64-deep replay floor per `(kid, epoch)`,
  and a record of the previous epoch is admitted within a grace
  period of `maxAuthDelayMs + 2 x manifestTimerMs`, in place of the
  `previousKey` overlap of -00, floor and grace period kept per
  arrival path (`manifestPort`, the manifest track), the floor
  raised by the records arriving on the path, verified or dropped as
  the byte-identical copy of a verified one, the period ending that
  long after the first such record of the new epoch on the path, a
  record read from the mirror meeting the higher of the two floors
  and the earlier-started period; the sender transmits each record
  twice, the byte-identical twin after the last datagram the record
  covers, no later than `maxAuthDelayMs / 2` after the record and
  before the signed record of window `mseq + 64`, so that it arrives
  above the floor; a generation reset discards
  every per-flow item but the budgets and the hold queues; the hold
  queues are per path, so a MoQ unicast path that fills its own
  evicts nothing from the multicast path's, and only the multicast
  path's expiries and the `manifestPort` bucket's drops count toward
  failover; a unicast receiver widens its hold, its hold queue with
  it, and the freshness tolerance of the records it reads from the
  manifest track, by at most 5 s, a record on `manifestPort` keeping
  the unwidened tolerance, one that reads the mirror and will not
  join the multicast path widening the pending expiry of a mirrored
  record's entries by the same W, and a receiver reading the mirror
  that has joined or may yet join widens the pending expiry of a
  mirrored record's entries and the life of its admitted digests by
  the mirror's lead, a per-flow value it measures, the bound until
  the generation's first measurement
  ((#receiver-enforcement-and-state), (#emission-and-cadence),
  (#threat-model)).
- A `keys` array that repeats a `kid` or a `firstEpoch` yields no
  key set: the receiver admits nothing from the broadcast
  ((#catalog-signaling)).
- Per-flow receiver state belongs to the stream generation: a change
  of the endpoint's `streamId` discards it, the budgets and the hold
  queues excepted, and the next record is processed as the first of
  the flow; the current epoch is kept with the `kid` that set it,
  and a re-fetch or re-provisioning after which that `(kid, epoch)`
  fails the range check of (#catalog-signaling) resets the flow the
  same way ((#receiver-enforcement-and-state)).
- A broadcast carries the flow as an MMTP service: the flow's
  datagrams as the MMTP packets of one MMTP session, carried as the
  sender's UDP datagrams on `S`, `G` and `port`, and the records as
  the sender's record datagrams on `manifestPort`, a broadcast that
  re-addresses either flow or carries the datagrams in any other
  form being uncovered.  This document no longer covers ROUTE: the
  carriage of -00, the record in the ROUTE signaling carousel and
  the signed group digest in an ALC/LCT EXT_AUTH header, is removed,
  the profile having no inclusion proofs, and so is the
  `sourceSymbolFormat` member of -00, whose only value named the
  authenticated bytes of that revision, trailer excluded
  ((#broadcast-carriage)).
- (#multicast-endpoint-format) defines `S` for the tuple rule
  (`sourceAddress` on an SSM endpoint, `auth.senderAddress` on a
  protected ASM endpoint, absent on an unprotected ASM endpoint),
  binds each `(S, G, port)` tuple to at most one endpoint object as
  well as one namespace, adds the same rule for a protected
  endpoint's `(S, G, manifestPort)` tuple, and requires a track
  listed on an endpoint to carry the catalog track's namespace
  ([@!I-D.ietf-moq-msf] Section 5.2.2); a receiver ignores an
  endpoint that lists another.
- (#multicast-security) no longer delegates source trust to the AMT
  relay: an ASM receiver, and a receiver reached through an AMT
  gateway on SSM, discards a datagram whose IP source address is not
  the endpoint's sender before parsing or hashing it
  ((#receiver-enforcement-and-state)).
