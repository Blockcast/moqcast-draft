%%%
title = "Forward Error Correction for Multicast Delivery of Media over QUIC"
abbrev = "MoQ FEC Multicast"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
date = "2026-10-29T00:00:00Z"
keyword = ["FEC", "MoQ", "multicast", "AMT", "repair policy"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-fec-multicast-00"
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

This document specifies how the Forward Error Correction (FEC)
mechanism for Media over QUIC (MoQ) is used when protected tracks are
delivered over multicast.  It defines repair-only multicast endpoints
and how a receiver adds and drops the repair layers they carry, states
which tracks a multicast endpoint carries in this revision, specifies
how a receiver treats blocks and symbols that a multicast
content-authentication profile has not admitted, and specifies the
receiver repair policy of a multicast or AMT leg: in-band FEC first,
then per-block unicast repair for the blocks that FEC did not recover,
with a budget and priorities derived from the catalog.  It is
independent of how multicast is carried, whether by Source-Specific
Multicast and Automatic Multicast Tunneling or by a multicast QUIC
channel.

{mainmatter}

{#introduction}
# Introduction

The FEC mechanism of [@!MOQ-FEC-CORE] lets a receiver recover lost
source symbols from repair symbols that the publisher sends ahead of
need, and lets each receiver choose how much repair it takes by
subscribing to repair tracks.  On a MoQ unicast path a receiver can
also fall back on QUIC retransmission.  On a multicast path it cannot:
IP multicast and Automatic Multicast Tunneling (AMT) deliver the same
packets to every receiver, no receiver can ask the network for a
retransmission, and a receiver without a return path cannot ask
anyone.  FEC is therefore the primary recovery mechanism on a
multicast leg, and this document specifies what is particular to it.

On a multicast endpoint the receiver does not choose tracks; the
operator of the endpoint does.  This document defines how the repair
layers of an FEC instance are placed on endpoints, including endpoints
that carry only repair, and how a receiver that measures loss moves
between them (#repair-only-endpoints).  It states which tracks a
multicast endpoint carries in this revision
(#symbol-tracks-on-multicast), and how the mechanism relates to the
repair that a multicast QUIC channel may provide below it
(#multicast-quic).  Where a multicast content-authentication profile
decides which packets a receiver may trust, it specifies how blocks
delimited by packets that the profile has not admitted are held
(#provisional-symbols).  Finally it specifies the receiver repair
policy of a multicast or AMT leg (#receiver-repair-policy): every
block gets in-band FEC first, and a receiver that holds a MoQ session
requests unicast repair, by the per-block FETCH of [@!MOQ-FEC-CORE],
only for blocks that FEC did not recover, in an order and within a
budget that the catalog fixes.

{#relation-to-other-documents}
## Relation to Other Documents

This document is a companion to [@!MOQ-FEC-CORE], which defines the
scheme-independent mechanism: source symbols and blocks, symbol and
repair tracks, repair layers, repair Group IDs, fetching by block,
deadlines and the configuration data model.  Everything this document
does not define it takes from there.  The set of documents is
completed by [@!MOQ-FEC-BLOCK], which specifies the Reed-Solomon and
RaptorQ schemes, [@!MOQ-FEC-CATALOG], which binds the configuration
data model to the catalog, and [@!MOQ-MMT], which defines the MMTP
block profile `iso-ssbg1-v1` and the keyframe overlay.  Multicast
carriage itself, endpoint discovery, the multicast packet format and
the bc-provenance content-authentication profile are defined in
[@!MOQ-MULTICAST]; this document adds the FEC-specific behavior on
top of them and does not depend on which carriage delivers the
multicast packets.  Most of the text of this document is taken from
[@?I-D.ramadan-moq-fec]; (#changes-from-draft-ramadan-moq-fec-01)
lists what moved here and what changed.

{#conventions-and-definitions}
# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [@!RFC2119] [@!RFC8174] when, and only when, they appear in all
capitals, as shown here.

The terms below are used in this document with the meaning that
[@!MOQ-FEC-CORE] gives them; every other term of that document, and
of [@!MOQ-MULTICAST], keeps its meaning there.

**Source Track**: A MoQ track whose objects carry media, for example
video or audio, and which an FEC instance protects.

**FEC Instance**: One independent FEC encoding over a sequence of
source symbols, with its own source symbol bound K, symbol size T,
SS_ID space, block partition, repair symbols and repair tracks.  A
source track has one or more FEC instances (Section
5.1 of [@!MOQ-FEC-CORE]).

**Base Instance**: Of a source track that a keyframe overlay protects,
the instance that is not the overlay; of any other source track, its
only instance.

**Source Symbol**: A T-byte unit of source data that an FEC instance
encodes.  Under `iso-ssbg1-v1` a source symbol is one FEC source
packet, an MMTP packet framed as Section 7.1 of
[@!MOQ-MMT] specifies.

**Repair Symbol**: A T-byte unit generated by the FEC scheme from the
source symbols of one block.

**SS_ID**: The 32-bit sequence number of a source symbol within its
FEC instance.  It wraps modulo 2^32 (Section
7.6 of [@!MOQ-FEC-CORE]).

**Source Block**: A run of SSB_length consecutive source symbols,
1 <= SSB_length <= K, over which a block FEC scheme encodes.  A block
is the SS_ID range [SS_Start, SS_Start + SSB_length) and is identified
by its SS_Start.

**SS_Start and SSB_length**: The first SS_ID of a source block and the
block's source symbol count, carried in the Repair FEC Payload ID of
every repair packet of the block (Section 7.5
of [@!MOQ-FEC-CORE]).

**RS_ID**: The zero-based index of a repair symbol among the repair
symbols of its block.

**Repair Track**: A MoQ track whose objects each carry one repair
symbol of one FEC instance.  Under `iso-ssbg1-v1` its objects are MMTP
FEC repair packets ([@!ISO.23008-1] Section C.4.3), the layer-0 repair
track carries the FEC repair flow that an ISO AL-FEC message names for
the source track's FEC encoded flow (Section 8.3
of [@!MOQ-MMT]), and further repair layers and a keyframe overlay are
repair tracks that only the catalog declares.

**Repair Layer**: One of possibly several repair tracks of one FEC
instance, each carrying a disjoint range of RS_IDs for every block
(Section 7.3 of [@!MOQ-FEC-CORE]).  Layer 0 is the
base layer.  Layer i may use RS_IDs from its RS_ID offset O_i, and
carries P_i repair symbols per block.

**Symbol Track**: A MoQ track whose objects each carry exactly one
source symbol of one FEC instance, grouped by block (Section
6.2 of [@!MOQ-FEC-CORE]).

**Keyframe Overlay**: A second, independent FEC instance over an
MMTP-packaged source track whose source symbols are only the fragments
of Random Access Points, defined in Section 7.4
of [@!MOQ-MMT].  An overlay is not a repair layer and carries no layer
index.

**Interleave Depth**: When positive, the complete time span, in
milliseconds, of one FEC source/repair packet block, signaled as
`interleaveDepthMs` (Section 9.3 of
[@!MOQ-FEC-CORE]).  Zero is not a millisecond span: under
`iso-ssbg1-v1` it selects the ISO packet-count alternative (Section
7.5 of [@!MOQ-MMT]).

**FEC Deadline**: The elapsed-time deadline that a receiver derives
for a block from a positive `interleaveDepthMs` together with
`reorderToleranceMs` (Section 9.3 of
[@!MOQ-FEC-CORE]).  A block has an FEC deadline only when its
instance carries a positive `interleaveDepthMs`.

**Multicast Endpoint**: One multicast group of a catalog's `multicast`
extension, with the list of tracks it carries (Section
4.1 of [@!MOQ-MULTICAST]).

**Unlisted Track** and **Admitted Packet**: Within a consumer that the
bc-provenance profile of [@!MOQ-MULTICAST] protects, an unlisted
track is one that no endpoint of a flow the consumer is protected
under lists, and an admitted packet is one that step 2 of the
receiver procedure of that profile (Section
7.2.7 of [@!MOQ-MULTICAST])
has admitted.

{#multicast-delivery}
# Hybrid Unicast and Multicast Delivery

The FEC mechanism of [@!MOQ-FEC-CORE] is designed to support hybrid
delivery architectures where the same media stream is delivered via
multiple transport paths simultaneously.  Multicast delivery paths,
TreeDN integration, and the transport hierarchy are defined in
[@!MOQ-MULTICAST] (its Sections 1 and
3); this section covers FEC-specific
considerations for hybrid delivery.

The catalog's authority over FEC configuration (Section
10 of [@!MOQ-FEC-CORE]) holds uniformly
across a MoQ receiver's delivery paths, its multicast and AMT legs
included.  MoQ control messages cannot reach multicast or sessionless
receivers at all, so no control-message mechanism could serve as the
common signaling path; the catalog can, because it is delivered as
track data or out of band.

{#multicast-and-amt-delivery}
## Multicast and AMT Delivery

IP multicast (including Source-Specific Multicast per [@?RFC4607]) and
Automatic Multicast Tunneling (AMT per [@?RFC7450]) provide efficient
one-to-many delivery but are inherently unreliable.  FEC enables receivers
to recover from packet loss without retransmission:

- **Native SSM**: Receivers join multicast group directly
- **AMT Tunneling**: Receivers without native multicast connect via AMT
  relays discovered through DRIAD ([@?RFC8777])
- **TreeDN** ([@?RFC9706]): native SSM where a network supports
  multicast, and AMT relays, found through DRIAD, for receivers on
  unicast-only networks.  The publisher generates FEC repair end to
  end, and the repair is the same on every leg.

For an mmtp track, the same MoQ objects (source and repair) can be
transmitted over both
unicast (QUIC/WebTransport) and multicast (UDP/SSM/AMT) paths.  Receivers
on reliable unicast paths can skip FEC decoding (Section
3.3 of [@!MOQ-FEC-CORE]), while
receivers on lossy multicast paths use FEC for recovery and apply the
receiver repair policy of (#receiver-repair-policy) to any block that
FEC does not recover.  A multicast endpoint carries only mmtp tracks,
so a loc or cmaf track reaches multicast through an mmtp rendition
track, which is a separate FEC instance ([@!MOQ-MULTICAST] Section
4.1; see
(#symbol-tracks-on-multicast)).

~~~
Publisher
    |
    v
+----------------+
|   MoQ Relay    |
| (Origin/Root)  |
+-------+--------+
        |
   +----+----+--------------------+
   |         |                    |
   v         v                    v
Unicast   SSM Multicast      AMT Tunnel
(QUIC)    (Native)           (Encapsulated)
   |         |                    |
   v         v                    v
[Web     [Native SSM         [Mobile/
Client]   Clients]            Remote]

FEC:      FEC:                FEC:
Optional  Expected            Expected
~~~

{#deployment-applicability}
## Deployment Applicability

The repair overhead this mechanism adds is justified only where the
delivery path actually loses packets, and multicast loss characteristics
differ by orders of magnitude across access technologies.  FEC strength
(P and Interleave Depth) is a per-path deployment choice, expressed by
which tracks each endpoint carries, not a protocol constant.

- **Engineered low-loss segments.**  On managed PON or DOCSIS delivered
  over a provisioned VLAN, steady-state loss is typically far below
  10^-6.  Disabling FEC for such a path is signaled by omitting the
  repair track from the tracks that path's endpoints carry.  Adding
  repair symbols
  on such a path spends bandwidth to recover losses that do not occur.

- **FEC-capable broadcast PHYs.**  ATSC 3.0, DVB-S2/S2X, and 5G broadcast
  already apply bit-error correction on their own radio link (e.g.,
  LDPC/BCH in ATSC 3.0 and DVB-S2/S2X).
  Application-layer FEC is NOT a duplicate of that correction: it recovers
  *packet erasures* the PHY cannot address -- bursts when reception falls
  below the PHY threshold (rain fade, mobility, indoor reception), and
  losses on upstream aggregation or backbone hops that the last-hop PHY
  never sees.  Its value on these paths comes primarily from Interleave
  Depth spreading a burst across the time domain, not from the code rate.
  On a one-way broadcast downlink with no return path, application-layer
  FEC is the only available erasure-recovery mechanism -- which is why
  ATSC 3.0 (see Section 10 of [@!MOQ-MMT])
  specifies it above the PHY.

- **Public Internet and AMT tunnels.**  Loss is real and bursty; a
  non-trivial repair count with interleaving is RECOMMENDED.

Which tracks a multicast endpoint carries in this revision, and so
which of the core's carriages reach a multicast leg, is stated in
(#symbol-tracks-on-multicast).

{#symbol-tracks-on-multicast}
## Symbol Tracks on Multicast Endpoints

In this revision a multicast endpoint of [@!MOQ-MULTICAST] carries
mmtp tracks and their repair tracks only ([@!MOQ-MULTICAST] Section
4.1), so every track that a
multicast leg carries is protected under the `iso-ssbg1-v1` block
profile of [@!MOQ-MMT], where one MMTP packet is one source symbol.  A
loc or cmaf track reaches a multicast endpoint only through an mmtp
rendition track, which is a separate FEC instance.  A symbol track of
the symbol carriage of [@!MOQ-FEC-CORE] (its Section
6.2) has the packaging value `fec-source`
([@!MOQ-FEC-CATALOG] Section 3.3), which the
`name` rule of [@!MOQ-MULTICAST] Section
4.1 does not permit, so a symbol
track is not listed on a multicast endpoint, and a receiver ignores an
endpoint that lists one under the rule of that section; this document
adds no receiver rule of its own.

Editor's Note: Symbol carriage makes one lost datagram erase one
symbol, which is what multicast needs, and nothing in the core ties a
symbol track to a MoQ path.  Carrying symbol tracks and their repair
layers on multicast endpoints, with a packet format for them, is
future work for this document and [@!MOQ-MULTICAST].

{#multicast-quic}
## Interaction with Multicast QUIC

This section is informative.

[@?QUIC-MULTICAST] lets a server send QUIC packets on one-way multicast
channels.  A channel is an alternate path of the unicast QUIC
connections whose clients have joined it, and its packets can carry
STREAM and DATAGRAM frames.  Clients acknowledge channel packets with
MC_ACK frames on their unicast connections ([@?QUIC-MULTICAST]
Section 4.4).  The server of each connection remains responsible for
any necessary frame data that a channel loses, and Section 8 of
[@?QUIC-MULTICAST] recommends that it send FEC repair packets on the
channel instead of retransmitting the lost frames.  That repair is a
transport mechanism below this mechanism, and this document does not
depend on it.  This mechanism can serve as the application-layer FEC on
such a channel, and suits broadcast-scale audiences better than
unicast repair, because per-receiver retransmission does not scale.

When this mechanism is carried over a multicast QUIC channel:

1. **Symbol-to-datagram mapping.**  Each source or repair symbol (one MMTP
   packet, per [@!MOQ-MMT]) is best carried in exactly one QUIC DATAGRAM
   frame.  This aligns the erasure unit (a lost QUIC packet) with the FEC
   symbol, so one lost packet erases exactly one source symbol.  STREAM
   framing defeats symbol-aligned recovery of FEC-protected media on a
   multicast channel: a lost packet then spans a byte range crossing
   symbol boundaries.

2. **Crypto boundary.**  FEC encoding operates on application-layer
   objects, ABOVE the QUIC packet protection of [@?QUIC-MULTICAST].
   Unlike bare multicast UDP -- which lacks QUIC's integrity guarantees
   (see (#security-considerations)) -- the multicast QUIC binding
   applies a shared-key
   AEAD per packet.  A sender computes source and repair symbols over the
   unencrypted objects; the channel then applies its AEAD; a receiver
   decrypts each surviving packet and recovers erased objects from the
   decrypted source and repair symbols.  A lost packet cannot be
   decrypted, but its object is reconstructed from other verified symbols,
   so recovery does not depend on possessing it.

3. **Integrity of recovered objects.**  The MC_INTEGRITY frames of
   [@?QUIC-MULTICAST] carry hashes of channel packets, and a client
   decodes a channel packet only after a matching hash has arrived
   over another integrity-protected path ([@?QUIC-MULTICAST]
   Section 4.5).  A
   FEC-reconstructed object was never carried in a single packet and is
   therefore not individually covered by a packet hash; it inherits trust
   transitively from the verified surviving symbols used to reconstruct
   it.  Deployments requiring per-object authentication of recovered data
   can additionally apply a scheme that authenticates every multicast
   symbol before it enters the decoder, repair symbols included, and,
   whenever a symbol of its decode was not so authenticated, checks a
   recovered packet against its own digest or, where it can derive no
   coordinate to hash with, withholds it (for example version 2 of
   the manifest-based bc-provenance profile of [@!MOQ-MULTICAST]
   Section 7.2, whose receiver
   procedure is its Section
   7.2.7).

4. **Repair channel versus unicast repair.**  A publisher using this
   mechanism broadcasts repair symbols on the multicast channel (the
   repair track) rather than relying on unicast retransmission.
   Receivers covered by the repair flow have no need to drive unicast
   repair for losses the FEC recovers, which preserves the O(1) sender
   cost that motivates broadcast FEC.  Unicast repair remains a last
   resort for losses exceeding the repair budget, and
   (#receiver-repair-policy) specifies it.

Item 1 assumes `iso-ssbg1-v1`, under which one MMTP packet is one
source symbol; (#symbol-tracks-on-multicast) states that this is the
only block profile a multicast endpoint carries in this revision.

A receiver deduplicates the symbols it receives on a multicast QUIC
channel as on any other path, within one FEC instance: source symbols
by SS_ID and repair symbols by (SS_Start, RS_ID).  Section
5.5 of [@!MOQ-FEC-CORE] states
that requirement; [@?QUIC-MULTICAST] states none for application
symbols.  That section also permits combining them with
symbols received from other paths.

{#repair-only-endpoints}
# Repair-Only Multicast Endpoints

Multicast endpoints carry only mmtp tracks and their repair tracks
((#symbol-tracks-on-multicast)), so this section concerns tracks
under `iso-ssbg1-v1`.

On a multicast endpoint the receiver cannot choose tracks; the
operator of the endpoint chooses which tracks that path carries.  Each
repair layer carried on an endpoint is listed with its own `packetId`
([@!MOQ-MULTICAST] Section 4.1),
exactly as a source track is, and a
receiver MUST route every such `packetId` to the decoder of the FEC
instance that layer serves, the one its `source` and `instanceId`
name (Section 10.2 of
[@!MOQ-FEC-CORE]).  Because every endpoint carries the same
source packets under the same block partition (Section
7.3 of [@!MOQ-FEC-CORE]), a
receiver that moves between endpoints, or that is side-fed over MoQ
unicast, mixes symbols from all of them in one decode.  Layers not
carried on any endpoint the receiver holds remain reachable over MoQ
unicast (Section 7.2 of [@!MOQ-FEC-CORE]) for
receivers that have a return path.

An operator MAY carry the source track and its layers together on one
endpoint, or MAY place layers on endpoints of their own.  An endpoint
whose track list contains only `fec-repair` tracks (the packaging
value of Section 3.3 of [@!MOQ-FEC-CATALOG])
is a repair-only endpoint:

~~~ json
{
  "multicast": {
    "endpoints": [
      {
        "sourceAddress": "198.51.100.100",
        "groupAddress": "232.1.1.50",
        "port": 5000,
        "tracks": [
          { "name": "video",          "packetId": 1 },
          { "name": "video/repair",   "packetId": 2 }
        ]
      },
      {
        "sourceAddress": "198.51.100.100",
        "groupAddress": "232.1.1.51",
        "port": 5000,
        "tracks": [
          { "name": "video/repair/1", "packetId": 3 },
          { "name": "video/repair/2", "packetId": 4 }
        ]
      }
    ]
  }
}
~~~

The first endpoint suits a regional path with low random loss.  The
second is repair-only: a receiver on a lossy path holds both, and
receives source packets once while adding layers 1 and 2 to the same
decode.

A repair-only endpoint is never a media tier.  A receiver MUST NOT
treat one as a rendition or quality choice, and endpoint or ladder
selection MUST exclude it on every path by which a receiver picks
what to render.  A repair-only endpoint's `bandwidth`
([@!MOQ-MULTICAST] Section 4.1) is
the cost of adding repair to a
stream the receiver has already selected, not the cost of an
alternative rendition, and MUST NOT be compared against a media
endpoint's `bandwidth` when choosing one.

A receiver joins a repair-only endpoint on measured loss: the rate at
which its FEC blocks fail to recover, and the margin by which
recovering blocks consume the repair symbols available to it.  A
receiver MUST NOT use goodput, throughput, or estimated available
bandwidth to decide whether to add or drop a repair layer.  The
capacity check that Section 7.4 of
[@!MOQ-FEC-CORE] recommends before a layer is added is the one
exception: it can withhold an add that measured loss calls for, but
it is neither a trigger for adding a layer nor a reason to drop one.

Layer changes are make-before-break.  A receiver MUST join the
additional layer's endpoint and begin receiving from it before
leaving any endpoint it currently holds, so that no source block is
left with less coverage than the receiver already had.  A layer
whose endpoint the receiver has left is carried on no endpoint it
holds, reachable over MoQ unicast as above; under the bc-provenance
profile of [@!MOQ-MULTICAST] Section
7.2 a receiver holds an
endpoint while joined to its group, reading its manifest track or
receiving the broadcast that carries the flow (its
Section 7.2.9), and a consumer is protected
under that endpoint's
flow only while the receiver holds it (step 2 of [@!MOQ-MULTICAST]
Section 7.2.7).

Hysteresis MUST derive from the FEC block span, that is from
`interleaveDepthMs` together with `reorderToleranceMs`, and MUST NOT
come from a fixed timer or a fixed symbol count.  A receiver MUST
observe at least one full block span at the new layer set before
making a further layer change.

That loss measure and this hysteresis both need a block deadline,
which exists only for a positive `interleaveDepthMs` (Section
9.3 of [@!MOQ-FEC-CORE]).  On a
multicast or AMT leg, a receiver of a track whose catalog omits that
field or sets it to zero MUST NOT add or drop a repair layer of the
track on block-recovery evidence, and keeps its repair-layer selection
for the track fixed.  This is an exception to the layer addition that
Section 7.4 of [@!MOQ-FEC-CORE] recommends
when a block fails to recover: without a signaled span a receiver has
only a deadline of its own (its Section
9.3), and on a multicast or AMT leg this
document does not let it change layers on that basis.

Layering changes the shape of the amplification exposure, because the
attacker's lever is now which layers a victim can be made to receive
rather than only whether it receives repair at all.  Each layer i adds
P_i x T bytes per source block, so a receiver induced to hold more
layers receives proportionally more repair traffic.  Deployments
SHOULD bound the number of layers any single receiver may hold, and
SHOULD apply the same join authorization to repair-layer endpoints as
to media endpoints; a repair-only endpoint is not
less sensitive than a media one merely because it carries no media.
A receiver MUST NOT be made to receive a repair layer it did not
join.  A publisher or relay MUST NOT push a repair-layer endpoint to
a receiver that has not joined it, and MUST NOT add a layer to an
endpoint a receiver has already joined as a way of raising that
receiver's protection (Section 14.4 of
[@!MOQ-FEC-CORE]).

{#provisional-symbols}
# Provisional Blocks and Admitted Packets

The bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2 decides, in step 2 of its
receiver procedure (its Section
7.2.7), which packets of a
protected flow a consumer admits.  This section specifies what a
receiver does with the blocks and symbols that the profile has not
admitted; it adds no admission rule of its own.  The block and
short-block rules that it qualifies are those of Section
5.4 of [@!MOQ-FEC-CORE], the fail-closed
layer check is that of Section 7.3.2, the
Group-range FETCH is that of Section
7.7, and the block deadline
and receiver-state policy are those of Sections
9.3 and 9.4.

{#provisional-blocks}
## Provisional Blocks

A consumer that the bc-provenance profile of [@!MOQ-MULTICAST]
Section 7.2 governs for its blocks is
one protected under a flow whose endpoint lists its source track (step
2 of its Section 7.2.7).  A
consumer protected under no such flow, as one that a repair-only
endpoint feeds while the receiver takes the source track over MoQ
unicast alone, is, for this section,
(#deadline-anchoring-and-discard) and (#receiver-repair-policy), a
consumer outside the profile.  The scoping of the check of (#anchoring-the-layer-check) to
admitted packets is wider: it reaches a consumer wherever it is
protected under any flow of the profile, as it reaches every consumer
so protected.

An unlisted track is one that no endpoint of a flow the consumer is
protected under lists, as that step defines it: a track that no
multicast endpoint the receiver holds lists, where holding an endpoint
is being joined to its group, reading its manifest track or receiving
the broadcast that carries the flow; or a track that a held endpoint
lists while the consumer is not yet protected under its flow
((#repair-only-endpoints)).

Within a consumer the profile governs for its blocks, a block that
only symbols of an unlisted track have delimited is provisional: it yields to a repair
packet the profile has admitted whose (SS_Start, SSB_length) conflicts
with it, as that step specifies, and the fail-closed consistency rules of Section
5.4 of [@!MOQ-FEC-CORE] then apply among
admitted packets.  A provisional block is held for decoding only:
it has no ts and no FEC deadline (Section
9.3 of [@!MOQ-FEC-CORE]), and the
SS_IDs in its
range that the receiver lacks belong, for (#receiver-repair-policy),
to blocks
the receiver holds no repair packet of, as if the block were not
delimited; such a symbol reveals no run of lost SS_IDs, which a
packet the profile admits above them alone reveals.

{#anchoring-the-layer-check}
## Anchoring the Fail-Closed Layer Check

Section 7.3.2 of [@!MOQ-FEC-CORE] requires
a receiver to fail closed, and stop FEC for the instance, when, for a
layer i that it holds, a repair object of that layer's track, i being
above 0, or a repair object of the instance of a block at or after,
in the serial order of Section
7.6 of [@!MOQ-FEC-CORE], one of
which it has received a repair object carrying at least O_i + P_i,
carries an RSB_length below the O_i + P_i derived from its
configuration; a block before the anchoring one whose objects carry
less is not subject to the check.
Within a consumer protected under a flow of the
bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2, whether or
not that profile governs it for its blocks ((#provisional-blocks)),
the packet
that anchors the check and the packet it tests are both repair
packets that profile has admitted (step 2 of its Section
7.2.7): a
symbol of an unlisted track reaches the consumer under the
integrity protection of a MoQ unicast path, which vouches for the
relay and not for the publisher, so the total it carries attests to
no coordinate the publisher is using; it anchors nothing, and one
whose RSB_length is below the O_i + P_i of a layer the receiver
holds is discarded, leaving the state of every block unchanged, so
that a relay on that path cannot stop FEC for the instance with one
packet.

{#admitted-blocks-in-the-fetch-range}
## Admitted Blocks in the Group-Range FETCH

Section 7.7 of
[@!MOQ-FEC-CORE] derives, for a lost SS_ID x, the Group range
[ max(ext(S_prev) + 1, ext(x) - (K - 1)), ext(x) ], where S_prev is
the SS_Start of the last block that the receiver has delimited that
ends before x.
Within a consumer that the
bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2 governs for
its blocks ((#provisional-blocks)), only a block that a repair packet
the
profile has admitted delimits counts here: a provisional block,
one that only symbols of an unlisted track ((#provisional-blocks))
have
delimited, is no such block, as its (SS_Start, SSB_length) is
unverified and the block that contains x may start within its
range.  When the receiver has delimited no such block, the first
term is absent and the range is
[ max(ext(x) - (K - 1), 0), ext(x) ].

{#deadline-anchoring-and-discard}
## Deadline Anchoring and Discard

The block deadline of Section 9.3 of
[@!MOQ-FEC-CORE] is anchored at first_arrival, written `ts` in this
document: the timestamp of the first source or repair packet of the
block when the receiver received that packet, not at block creation
or the first repair receipt.  A
block whose first packet the receiver did not receive is one that it
first learns of from a later signal -- a later source or repair
packet of the block, a packet of a successor block, or a FETCH
response that covers the block (Section
7.7 of [@!MOQ-FEC-CORE]) --
and its `ts` is the
arrival time of that signal.  Within a consumer that the
bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2 governs for
its blocks ((#provisional-blocks)), the packet whose receipt anchors
`ts` is
the first packet of the block, in the order received, that the
profile admits, whenever it admits it (a datagram held on a miss
and admitted later keeps its receipt time), and a symbol of an
unlisted track ((#provisional-blocks)) is neither that packet nor such
a
signal, whether or not a repair packet the profile admits later
delimits the same block; a block that only such symbols have
delimited is held for decoding only: it has no `ts` and no FEC
deadline,
whatever packets the profile admits into or above its range, and the
SS_IDs in its range that the receiver lacks are runs of
(#receiver-repair-policy), each with the `ts` the packet admitted
above it gives, as step
2 of [@!MOQ-MULTICAST] Section
7.2.7 specifies.

A receiver bounds the state it holds for open blocks by the
receiver-local policy of Section 9.4 of
[@!MOQ-FEC-CORE], which forbids discarding a block that has an FEC
deadline before that deadline, or while a FETCH for it is outstanding,
the unicast repair FETCH of (#keyframe-bearing-blocks) included,
except under a memory cap.  A block so discarded is, under that
section, treated from then on as having reached its FEC deadline
unrecovered and, on a track whose blocks (#block-classification)
classifies, of unknown class.  Within a consumer that the
bc-provenance profile governs for its blocks ((#provisional-blocks)),
the
policy discards a block that has no `ts`, one that only symbols of
an unlisted track have delimited, before any block that has a `ts`,
on a track that derives no FEC deadline as on one that does, and
such a discard is neither a reached deadline nor a
signal: it gives the block no deadline and no class, drops its repair
symbols and returns its source symbols to the undelimited state of
Section 5.4 of [@!MOQ-FEC-CORE] (step 2
of [@!MOQ-MULTICAST] Section
7.2.7).  The policy is not
signaled and is kept separate from the configured values (Section
9.4 and Section 9.3
of [@!MOQ-FEC-CORE]): it changes neither `interleaveDepthMs` nor
`reorderToleranceMs` nor a deadline derived from them, and discarding
a block under it does not create an FEC deadline
((#receiver-repair-policy)).

{#receiver-repair-policy}
# Receiver Repair Policy

This section specifies what a receiver of a multicast or AMT leg does
with a base-instance block of a source track that in-band FEC has not
recovered by the block's FEC deadline (Section
9.3 of [@!MOQ-FEC-CORE]).  A receiver on
a reliable MoQ/QUIC leg relies on transport retransmission (Section
3.3 of [@!MOQ-FEC-CORE])
and does not need it, and nothing in this section adds a deadline or
a timer to such a leg.  Multicast and AMT legs carry only mmtp tracks
([@!MOQ-MULTICAST] Section 5;
(#symbol-tracks-on-multicast)), so this section, which classifies
blocks from MMTP fields, concerns tracks under `iso-ssbg1-v1`.

Every step of this section is keyed on a block's FEC deadline, which
exists only when the track's catalog carries a positive
`interleaveDepthMs` (Section 9.3 of
[@!MOQ-FEC-CORE]).  On a multicast or AMT leg, this
section therefore requires a positive `interleaveDepthMs`: a receiver
of a track whose catalog omits it or sets it to zero MUST disable the
block classification and unicast repair of this section for that
track.  The receiver still decodes in-band FEC from the symbols that
arrive (Section 5.5 of
[@!MOQ-FEC-CORE]), with open-block state bounded by the local
policy of Section 9.4 of [@!MOQ-FEC-CORE] and
(#deadline-anchoring-and-discard).
Media still missing at its presentation time is
lost: the loss of a RAP, or of a data unit that governs one, is
handled as for an unrecoverable keyframe-bearing block
((#keyframe-bearing-blocks)), and other loss is concealed as in
(#other-video-blocks) and (#audio-blocks).

Every block receives in-band FEC processing.  A receiver MUST attempt
to recover every block, whatever its class, from the source and repair
symbols received on its multicast and AMT paths, together with any it
receives on other paths (Section 5.5 of
[@!MOQ-FEC-CORE]), up to the block's FEC deadline.
Within a consumer that the bc-provenance profile of [@!MOQ-MULTICAST]
Section 7.2 governs for its blocks
((#provisional-blocks)), a symbol of an
unlisted track ((#provisional-blocks)) enters a decode only as step 2
of [@!MOQ-MULTICAST] Section
7.2.7 allows, which takes none
into a
decode of a block that two decodes with such symbols' help have left
unrecovered; the attempt continues from the symbols the profile
admits.  The rest of this section governs only a block that is still
unrecovered at that deadline: the receiver does not hold all of its
SSB_length source symbols (Section 5.4 of
[@!MOQ-FEC-CORE]), and decoding from the
symbols it holds has not recovered them.  Within such a consumer, a
source symbol the profile has not admitted, received or recovered, is
not held for this purpose (step 2 of [@!MOQ-MULTICAST]
Section 7.2.7).

A run of SS_IDs that the receiver lacks and that lies in no block it
has delimited belongs to one or more blocks of which it holds no
repair packet (Section 5.4 of
[@!MOQ-FEC-CORE]).  For this section the receiver treats
such a run as one block of the instance (within a consumer that the
bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2 governs for
its blocks, (#provisional-blocks), a block only symbols of an unlisted
track
have delimited being no block the receiver has delimited, and the
run one only once a packet the profile has admitted lies above it,
step 2 of [@!MOQ-MULTICAST] Section
7.2.7):
(#block-classification)
classifies it from the source packets the receiver holds on either
side of it, and its repair is requested by the Group range of
Section 7.7 of
[@!MOQ-FEC-CORE], whose response also delimits the blocks it covers.

The policy distinguishes keyframe-bearing blocks, whose loss can stop
video decoding until the next Random Access Point (RAP), from other
blocks, whose loss damages only frames up to the next RAP.
Keyframe-bearing blocks are protected by priority unicast repair and
are the only blocks whose loss may stall video.  Other blocks are
repaired on a best-effort basis and, when repair fails, concealed.
Every frame and audio sample a receiver presents MUST be presented at
its authored time on the presentation clock shared by its tracks, and
a receiver MUST NOT stall video or pause that clock except for a
keyframe-bearing block ((#keyframe-bearing-blocks)).

{#block-classification}
## Block Classification

This section applies to tracks protected under the `iso-ssbg1-v1`
block profile of [@!MOQ-MMT], and the fields it reads are those of
the MMTP packet header and of the keyframe overlay header extension,
as Sections 7.1 and 7.4 of
[@!MOQ-MMT] define them.  The classification is a receiver-side
repair-ordering policy computed from MMTP packet headers that the
receiver already holds: it decides which unrecovered blocks are
requested first and which may stall video.  It is not instance
membership.  A receiver never uses it to decide which FEC instance a
packet belongs to, which repair layers to hold, or whether to feed a
symbol to a decoder: instance membership and the symbols a decoder
takes follow from the configuration and the Source FEC Payload ID
alone, and the layers a receiver holds are chosen as Section
7.4 of [@!MOQ-FEC-CORE] describes, from the
loss it observes and its capacity, never from a payload, as Section
8.5 of [@!MOQ-FEC-CORE]
requires.  What this section decides from the headers is only the
order and budget of the per-block unicast repair of
(#keyframe-bearing-blocks) and (#unicast-repair-budget), a choice
that Sections 7.4 and
7.7 of [@!MOQ-FEC-CORE] leave
to the receiver.

A base block of a video source track is keyframe-bearing if it
carries, or may carry, any part of a RAP: a fragment of a RAP MFU, or
of the FT=0 or FT=1 data unit that governs it ([@!MOQ-MMT]
Sections 4.3 and
5.1).  The receiver classifies
each block when the
block reaches its FEC deadline, from two inputs and only from them:
in-band evidence in the source packets it holds, and the
catalog-authored timing of the track, that is its group structure,
one MPU per group of the catalog group duration ([@!MOQ-MMT]
Sections 4.3 and
4.4.2), and its keyframe
interval ([@!MOQ-MMT]
Section 4.4.3).  The block's
SS_Start and SSB_length, once known
(Section 5.4 of [@!MOQ-FEC-CORE]), fix
which SS_IDs belong to the block, and a positive
`interleaveDepthMs` with `reorderToleranceMs` fixes the elapsed-time
deadline at which the class is taken (Section
9.3 of [@!MOQ-FEC-CORE]).

The receiver first bounds what the block's missing source symbols can
carry.  The lower bounding packet is the last source packet it holds,
in SS_ID order, before the block's first missing source symbol; the
upper bounding packet is the first source packet it holds after the
block's last missing source symbol.  Either may lie in an adjacent
block.  Only FEC source symbols count: the AL-FEC signaling object of
[@!MOQ-MMT] Section 8.3 carries no SS_ID and is
never a bounding
packet.  A publisher MUST assign the base SS_IDs of a track's source
packets in increasing order along the authored order of [@!MOQ-MMT]
Section 4.3, so every data unit the missing
symbols can carry lies
between the data units of the two bounding packets, those two
included.

The block is keyframe-bearing if any of the following holds:

1. A source packet the receiver holds from the block sets `RAP_flag`,
   carries the 0x8B01 overlay header extension (Section
   7.4.3 of [@!MOQ-MMT]), or is
   an FT=0 packet, or two source packets it holds from the block carry
   different MPU sequence numbers.

2. The two bounding packets carry different MPU sequence numbers, or
   the lower bounding packet is the FT=0 packet or the first FT=1
   packet of its MPU, or belongs to the first FT=2 sample of its MPU.
   The missing symbols can then carry part of a group-start RAP, or of
   the metadata that governs it ([@!MOQ-MMT] Section
   4.3).

3. The catalog carries a usable keyframe interval, and the closed
   interval between the authored decode times ([@!MOQ-MMT]
   Section 5.1) of the samples of
   the two bounding packets contains an
   instant a positive whole number of keyframe intervals after the
   decode time of the first sample of their MPU.  Where a bounding
   packet is an FT=1 packet, its time is the decode time of the first
   sample it describes.  The interval is `keyframeIntervalTicks`, or
   `keyframeIntervalMs` converted to the track timescale where that
   conversion is exact; an inexact `keyframeIntervalMs` gives no usable
   interval.

The block is non-keyframe-bearing only when none of these holds, the
catalog carries a usable keyframe interval, the receiver holds both
bounding packets, and it can determine every value item 3 needs.
Every other block is of unknown class, and a receiver MUST treat a
block of unknown class as keyframe-bearing.  In particular:

- A block for which the receiver holds no lower or no upper bounding
  packet at its FEC deadline is of unknown class, as is one for which
  it cannot determine a decode time that item 3 needs.  So is a block
  discarded before its FEC deadline under a memory cap
  ((#deadline-anchoring-and-discard)).

- On a video track whose catalog entry carries no usable keyframe
  interval, the receiver cannot exclude a keyframe after the group
  start from any span, so every block of the track is keyframe-bearing
  or of unknown class.

- A block's keyframe classification uses its actual source-packet
  range.  A block MAY contain a complete Group, span a Group boundary,
  or close inside a Group; none of those shapes is inferred from
  `interleaveDepthMs` or from the catalog's group duration.

A receiver MUST NOT classify a block from any input other than those
this section names; in particular, the absence of `RAP_flag` on the
packets it holds says nothing about a packet that was lost.  A
publisher that wants receivers to be able to
apply the non-keyframe treatment of (#other-video-blocks) publishes
an exact
keyframe interval, which then binds every keyframe of the track
([@!MOQ-MMT] Section 4.4.3).

The blocks of a track that the catalog identifies as audio are
treated by (#audio-blocks), not classified by this section.  A track
that the receiver cannot identify from its catalog entry is treated as
video.

{#keyframe-bearing-blocks}
## Keyframe-Bearing Blocks

When a keyframe-bearing block is still unrecovered at its FEC
deadline, a receiver that holds a MoQ session with a relay serving the
block's repair track MUST request on-demand unicast repair for it,
with the priority of (#unicast-repair-budget), unless the block lies
below a
RAP the receiver has already admitted complete (the repair would be
moot on completion, below); within a consumer that the
bc-provenance profile of [@!MOQ-MULTICAST] Section
7.2 governs for
its blocks ((#provisional-blocks)), a block only symbols of an
unlisted track
((#provisional-blocks)) have delimited reaches no deadline and is
never
requested, the SS_IDs it covers that the receiver lacks being runs
of this section (step 2 of [@!MOQ-MULTICAST] Section
7.2.7).  The
request is a FETCH
[@!I-D.ietf-moq-transport], over QUIC, of the block's
repair-track group, whose Group ID is the block's extended SS_Start,
or, for a run that the receiver has not delimited, of the Group range
that Section 7.7 of
[@!MOQ-FEC-CORE] derives from a lost SS_ID x of the run.  The receiver
sends it on layer 0, and on further layers in layer order where it
needs more symbols than layer 0 carries (Sections
7.3.1 and 7.4 of
[@!MOQ-FEC-CORE]).
Section 7.7 of
[@!MOQ-FEC-CORE] gives the LOCATION_FILTER of either form, and the
receiver
establishes the wrap epoch as Section
7.6 of [@!MOQ-FEC-CORE]
specifies, for instance by a
TRACK_STATUS request when it has received no repair-track Group ID
over MoQ.  The FETCH of a
single group MAY be limited to the object range that covers the
block's shortfall.  The repair symbols it returns are deduplicated
against the symbols already held by (SS_Start, RS_ID) (Section
5.5 of [@!MOQ-FEC-CORE])
and fed to the same decoder; their SS_Start and SSB_length also
delimit a block the receiver had not delimited (Section
5.4 of [@!MOQ-FEC-CORE]).  The
receiver MUST NOT delay this request behind any non-keyframe or audio
repair; (#relationship-to-the-keyframe-overlay) covers its interplay
with a keyframe overlay.
A FETCH completes or fails by MoQ Transport events, its last object
or an error; a receiver MUST NOT declare it failed on a locally chosen
timeout.  A relay answers it only where it caches the repair track's
objects, datagram-delivered ones included (Section
12 of [@!MOQ-FEC-CORE]); where it
does not, the FETCH fails by those events.

Only a keyframe-bearing block may stall video.  While its unicast
repair is outstanding, the receiver MAY hold video presentation for
it.  The block is unrecoverable when its unicast repair fails or
completes without recovering it, or when the receiver holds no MoQ
session through which to request it (for example a receiver that
consumes an MMTP stream without a MoQ session, [@!MOQ-MULTICAST]
Section 1.1).
If the data of an unrecoverable block that the receiver could not
recover includes, or may include, any part of a RAP
((#block-classification)),
the receiver treats the track as discontinuous, MAY stall video, and
does not resume video before the next RAP ([@!MOQ-MMT] Section
6.1,
step 6).  Otherwise, as when it holds or has recovered every part of
the block's RAPs (including through a keyframe overlay,
(#relationship-to-the-keyframe-overlay)), it conceals the block's
remaining loss as for a
non-keyframe block ((#other-video-blocks)).

If the next RAP arrives complete before a keyframe repair completes,
the repair is moot: the receiver resumes from that RAP and SHOULD
cancel the FETCH; a block that reaches its deadline already below
such a RAP is not requested at all.

{#other-video-blocks}
## Other Video Blocks

For a non-keyframe-bearing block of a video track, in-band FEC remains
the primary repair.  A receiver MAY also request unicast repair for
it, in the form of (#keyframe-bearing-blocks), but only on the terms
of
(#unicast-repair-budget): never ahead of or concurrently with keyframe
repair,
and only within the budget that keyframe repair leaves unspent.

When such a block is unrecovered -- at its FEC deadline without
unicast repair, or when its unicast repair has not completed by the
presentation time of the first media it would repair -- the receiver
MUST NOT stall.  It conceals the affected frames, and every frame that
depends on them, until the next RAP, and keeps presentation and
audio/video synchronization running:

- Concealment fills the presentation interval of the frames it
  replaces and ends at the authored presentation time of the next
  frame the receiver presents.  The receiver MUST NOT drop later
  frames to absorb the loss.  It derives no
  timing for the frames it replaces ([@!MOQ-MMT] Section
  5.1).

- The concealment method is an implementation choice: for example
  holding or replaying the last presented frame, or presenting decoder
  output in which missing reference data is filled (commonly visible
  as a solid or green fill).  The receiver MUST NOT submit to the
  decoder a sample that the packaging's reassembly rules have
  invalidated ([@!MOQ-MMT] Section
  5.2).

- The next RAP ends concealment, and the receiver resumes normal
  decoding from it.

{#audio-blocks}
## Audio Blocks

In-band FEC applies to the blocks of an audio track as to every block,
and a receiver MAY
request unicast repair for an audio block on the same best-effort
terms as for a non-keyframe video block ((#unicast-repair-budget)).
`RAP_flag`
on an audio packet does not make its block keyframe-bearing; that
class applies to video tracks only.

When an audio block is unrecovered, the receiver MUST conceal the lost
audio, for example with silence or packet-loss concealment, from the
end of the last audio it presented to the authored presentation time
of the next audio it presents, and MUST keep the audio clock advancing
through the loss.  It MUST NOT stall audio presentation waiting for a
repair that has not completed by the presentation time of the lost
audio.

{#unicast-repair-budget}
## Unicast Repair Budget and Priority

A receiver's unicast repair budget is derived from the catalog, not
from a receiver-local rate or byte constant.  It is kept per MoQ
session and counted in bytes of repair symbol data, a repair symbol of
a track counting as that track's `symbolSize` T (Section
10.1 of [@!MOQ-FEC-CORE]).

- Each block that (#block-classification) treats as keyframe-bearing,
  including
  a block of unknown class, credits the budget with P_t x T bytes when
  it reaches its FEC deadline, where P_t is the total repair count of
  its base instance, the sum of P_i over its published layers (Section
  7.3.1 of [@!MOQ-FEC-CORE]), and T is its
  track's `symbolSize`.

- A credit expires when the next keyframe-bearing block of the same
  source track reaches its FEC deadline, so unspent budget never
  accumulates beyond one block's credit per source track.

- Every unicast repair FETCH debits the budget with the repair symbol
  bytes it requests.  A FETCH of a Group range (Section
  7.7 of [@!MOQ-FEC-CORE])
  requests
  every Group that starts in the range, a number the receiver learns
  only from the response, and is debited with the repair symbol bytes
  of every Group it returns.

1. A receiver does not withhold a keyframe-bearing block's repair for
   lack of credit.  For a block that it has delimited, it requests at
   most one repair-track Group per base repair layer, that is at most
   the P_t x T bytes that the block itself credits.  For a run of
   blocks that it has not delimited, it issues the one Group range
   FETCH of Section 7.7 of
   [@!MOQ-FEC-CORE] per base repair layer.  Each Group that FETCH
   returns is the repair of one block of the run, and every block
   holds at least one SS_ID of a range that spans at most K SS_IDs
   (that section), so these FETCHes cost at most K x P_t x T bytes in
   all, which can exceed the credit.  A debit that exceeds the remaining credit exhausts it:
   the budget never falls below zero, and no deficit carries over to a
   later credit.  A receiver MUST NOT have more than one repair FETCH
   outstanding for the same block and repair layer.

2. Non-keyframe and audio repair MAY spend only unexpired credit that
   keyframe-bearing blocks left unspent, and a receiver MUST NOT issue
   a non-keyframe or audio repair FETCH that the remaining credit does
   not cover.  Because the cost of a Group range FETCH is not known
   before it is issued, a receiver MUST NOT request non-keyframe or
   audio repair by a Group range.

3. A receiver MUST NOT issue a non-keyframe or audio repair FETCH
   while a keyframe repair FETCH is outstanding on the same session,
   and SHOULD cancel its outstanding non-keyframe and audio repair
   FETCHes when it requests the repair of a keyframe-bearing block
   that reaches its FEC deadline unrecovered; a block whose repair
   (#keyframe-bearing-blocks) does not request cancels nothing.

Priorities follow the ranges of Section
11 of [@!MOQ-FEC-CORE].  A keyframe
repair FETCH
MUST carry a SUBSCRIBER_PRIORITY ([@!I-D.ietf-moq-transport]
Section 9.20.7) in the source track range, numerically at most 191.
It MUST also be numerically no greater than the SUBSCRIBER_PRIORITY of
the receiver's subscription to the source track, where the receiver
holds one on the session, and numerically lower than the
SUBSCRIBER_PRIORITY of every repair-track subscription that the
receiver holds on the session.  Subscriber priority is compared first
([@!I-D.ietf-moq-transport] Section 5.1.2), so the FETCH is then
delivered ahead of the receiver's repair tracks and is not shed with
repair data under congestion.  A
non-keyframe or audio repair FETCH MUST carry a SUBSCRIBER_PRIORITY
numerically no lower than the Publisher Priority of the repair track
it fetches ([@!MOQ-FEC-CORE] Section 11),
and so at least 192, so that it is shed first.

{#relationship-to-the-keyframe-overlay}
## Relationship to the Keyframe Overlay

The keyframe overlay of Section 7.4 of
[@!MOQ-MMT], an overlapping instance in the sense of Section
8.4 of [@!MOQ-FEC-CORE], and this policy
are
complementary.  The overlay is publisher-side and proactive: it
protects RAP fragments across a block of its own, needs no return
path, and so also serves sessionless receivers.  This policy is
receiver-side and reactive: it spends unicast repair only on
keyframe-bearing blocks that in-band FEC actually failed to recover,
and it needs a MoQ session.  A receiver that holds both:

- classifies blocks by (#block-classification) whether or not it holds
  the
  overlay;

- MUST NOT defer the unicast repair of a keyframe-bearing block to
  wait for overlay recovery, whose latency is the overlay's own block
  span (Section 7.4 of [@!MOQ-MMT]), not the base
  deadline;

- ends its wait for a RAP with whichever of base decoding, overlay
  decoding, or unicast repair supplies the RAP's fragments first; and

- having recovered a block's RAP MFU fragments through the overlay,
  and holding the FT=0 and FT=1 data units that govern them, conceals
  the rest of that block's loss as for a non-keyframe block
  ((#other-video-blocks)) and SHOULD cancel any outstanding keyframe
  repair
  FETCH for it.  The overlay covers only packets that set `RAP_flag`
  (Section 7.4 of [@!MOQ-MMT]), so it does not by
  itself recover a lost FT=0 or
  FT=1 data unit.

{#security-considerations}
# Security Considerations

The security considerations of [@!MOQ-FEC-CORE] and of
[@!MOQ-MULTICAST] apply.  Join authorization for repair-layer
endpoints and the amplification exposure of layers are covered in
(#repair-only-endpoints).

When FEC is used over multicast (SSM/AMT), which carries only mmtp
tracks under `iso-ssbg1-v1` ([@!MOQ-MULTICAST] Section
4.1; (#symbol-tracks-on-multicast)),
additional considerations
apply:

1. **No QUIC Protection**: Multicast UDP has neither the
   confidentiality nor the integrity of QUIC.  A publisher that needs
   confidentiality SHOULD encrypt the media samples, for example with
   Common Encryption [@?ISO.23001-7] and its 'cbcs' scheme, as
   [@!MOQ-MMT] Section 14 describes for
   mmtp tracks.  All receivers of
   the flow share the content keys, which reach each receiver over its
   unicast MoQ session or from a Digital Rights Management (DRM)
   system.  Sample encryption leaves
   the MMTP headers and the Source FEC Payload ID in the clear and
   leaves every packet identical across paths, so FEC encodes the
   ciphertext (Section 14.1 of [@!MOQ-FEC-CORE])
   and symbols still combine across paths
   (Section 5.5 of [@!MOQ-FEC-CORE]).
   Encrypting each MoQ object payload instead, as MoQ
   Secure Objects [@?I-D.ietf-moq-secure-objects] does, would make the
   MoQ copy of a packet differ from its multicast copy.  A keying
   handshake per receiver, such as DTLS-SRTP, needs a return path and
   cannot key a one-to-many flow.  A key that every receiver holds does
   not authenticate the publisher; item 3 covers authentication.

2. **Repair Injection**: Attackers could inject malicious repair
   symbols on multicast networks.  The bc-provenance profile of items
   3 and 5 is the mitigation: a receiver that enforces it admits a
   symbol only when its digest is in a verified manifest, so an
   injected symbol never enters a decode; a receiver that does not
   enforce it has, beyond the container parsing of its media pipeline,
   only the block-level checksum of item 4 where it implements one.

3. **Source Authentication**: SSM limits which sources reach a
   receiver ([@!MOQ-MULTICAST] Section
   7.1), and version 2 of the
   bc-provenance profile ([@!MOQ-MULTICAST] Section
   7.2) authenticates
   the datagrams themselves, repair symbols included, with a digest
   that covers the whole UDP payload, the Source FEC Payload ID
   included (Section 7.2 of [@!MOQ-MMT]).

4. **Block Integrity**: Receivers MAY implement block-level checksums
   to detect corrupted recovery.  A block whose decoded source data
   fails such a check, or, within a consumer that the bc-provenance
   profile of [@!MOQ-MULTICAST] Section
   7.2 governs for its blocks
   ((#provisional-blocks)), whose recovered packets step 2 of its
   Section 7.2.7
   does not admit, is unrecovered: (#receiver-repair-policy) governs
   it from its
   FEC deadline, and the receiver requests unicast repair for it only
   as that section directs, never by the multicast-to-unicast
   failover of [@!MOQ-MULTICAST], which replaces the multicast path.

5. **Repair Policy Inputs**: The in-band evidence that
   (#block-classification)
   classifies blocks from, and the SSB_length by which Section
   5.4 of [@!MOQ-FEC-CORE]
   completes a short block, are unauthenticated on bare multicast.
   An injected packet that marks a block keyframe-bearing costs at
   most the unicast repair that block's own credit covers
   ((#unicast-repair-budget)).  An injected source packet inside a
   block's gap
   can instead narrow the bounds of (#block-classification) until a
   keyframe-bearing block is classified otherwise, and an injected
   repair packet carrying a false SS_Start or SSB_length, accepted
   before the genuine ones, can mis-delimit a block, mark it complete
   early, or cause its genuine repair packets to be discarded as
   inconsistent (Section 5.4 of
   [@!MOQ-FEC-CORE]).  Deployments
   exposed to injection SHOULD authenticate source and repair packets
   with an integrity mechanism whose coverage includes the complete
   packet, the Source FEC Payload ID and the Repair FEC Payload ID
   included (Section 7.2 of [@!MOQ-MMT]).
   Version 2 of the bc-provenance profile
   ([@!MOQ-MULTICAST] Section 7.2) is
   such a mechanism: its digest
   covers the whole UDP payload of source and repair packets, both
   Payload IDs included.

{#iana-considerations}
# IANA Considerations

This document has no IANA actions.

{backmatter}

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

<reference anchor='MOQ-MMT'>
  <front>
    <title>MPEG Media Transport (MMT) Packaging for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='29'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-mmt-02'/>
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

<reference anchor='ISO.23001-7'>
  <front>
    <title>Information technology - MPEG systems technologies - Part 7: Common encryption in ISO base media file format files</title>
    <author>
      <organization>ISO/IEC</organization>
    </author>
    <date year='2023' month='August'/>
  </front>
  <seriesInfo name='ISO/IEC' value='23001-7:2023'/>
</reference>

{#changes-from-draft-ramadan-moq-fec-01}
# Changes from draft-ramadan-moq-fec-01

This appendix is informative.  It lists what this document takes from
[@?I-D.ramadan-moq-fec] and every sentence that is new or changed
rather than carried.

Moved here, by section of this document:

- (#multicast-delivery): -01 Section 11 and, as its second paragraph,
  the last paragraph of -01 Section 5.2 (control messages cannot
  reach multicast or sessionless receivers).
- (#multicast-and-amt-delivery): -01 Section 11.1.
- (#deployment-applicability): -01 Section 11.2, without its last
  paragraph (the moq-object-v1 scoping that the core supersedes),
  which (#symbol-tracks-on-multicast) replaces.
- (#symbol-tracks-on-multicast): new.
- (#multicast-quic): -01 Section 11.3.
- (#repair-only-endpoints): -01 Section 6.3.6 and the second and
  third paragraphs of -01 Section 14.3 (join authorization for
  repair-layer endpoints).  The multicast rule of -01 Section 5.1
  (no block classification, no unicast repair and a fixed layer
  selection without a positive interleaveDepthMs) is restated by this
  section's last paragraph and by (#receiver-repair-policy).
- (#provisional-symbols): the bc-provenance clauses of -01 Sections
  7.4 (provisional blocks), 6.3.9 (anchoring of the fail-closed layer
  check), 7.5 (S_prev) and 9 (ts anchoring, discard policy).
- (#receiver-repair-policy) and its subsections: -01 Sections 11.4
  to 11.4.6.
- (#security-considerations): -01 Section 14.4.
- (#acknowledgements): -01 Appendix E.

Changed sentences:

- In (#multicast-and-amt-delivery), "A multicast endpoint carries only
  mmtp tracks, so a loc or cmaf track under moq-object-v1 reaches
  multicast through an mmtp rendition track" now reads "A multicast
  endpoint carries only mmtp tracks, so a loc or cmaf track reaches
  multicast through an mmtp rendition track" and points at
  (#symbol-tracks-on-multicast).
- In (#multicast-quic), "Item 1 assumes iso-ssbg1-v1, under which one
  MMTP packet is one source symbol.  This document defines no
  multicast carriage for moq-object-v1 (Section 7.6.6)." now reads
  "Item 1 assumes iso-ssbg1-v1, under which one MMTP packet is one
  source symbol; (#symbol-tracks-on-multicast) states that this is the
  only block profile a multicast endpoint carries in this revision."
- In (#multicast-quic), the four occurrences of "this scheme" in the
  -01 Section 11.3 text ("below this scheme", "This scheme can serve",
  "When this scheme is carried", "A publisher using this scheme") now
  read "this mechanism", because "scheme" is the core's term for the
  FEC code (Section 2 and Section
  10.1 of [MOQ-FEC-CORE]).
- In (#repair-only-endpoints), "Multicast endpoints carry only mmtp
  tracks and their repair tracks ([MOQ-MULTICAST] Section 4.1), so
  this subsection concerns tracks under iso-ssbg1-v1" now cites
  (#symbol-tracks-on-multicast), and "the decoder of the source track
  that layer depends on" now reads "the decoder of the FEC instance
  that layer serves, the one its source and instanceId name", per the
  core's data model.
- In (#repair-only-endpoints), "An endpoint whose track list contains
  only fec-repair tracks is a repair-only endpoint" gains the
  parenthesis "(the packaging value of [MOQ-FEC-CATALOG])".
- In (#repair-only-endpoints), the two sentences of -01 Section 14.3
  on receivers not being made to receive a layer they did not join
  now end with a citation of the core's amplification section.
- In (#provisional-blocks), the -01 sentence that defined the
  governed consumer, the unlisted track and the provisional block is
  now three paragraphs: the first defines the consumer the profile
  governs for its blocks, and "is for this paragraph, Section 9 and
  Section 11.4 a consumer outside that profile" now reads "is, for
  this section, (#deadline-anchoring-and-discard) and
  (#receiver-repair-policy), a consumer outside the profile"; the second defines the unlisted track; the third
  states the provisional block.  "the rules of the previous paragraph
  then apply among admitted packets" now reads "the fail-closed
  consistency rules of [MOQ-FEC-CORE] then apply among admitted
  packets".
- In (#unicast-repair-budget), the non-keyframe FETCH rule names the
  priorities it compares: the FETCH's SUBSCRIBER_PRIORITY against the
  Publisher Priority of the repair track it fetches, citing the core.
- In (#security-considerations), item 2 names the bc-provenance
  profile of items 3 and 5 as the mitigation for repair injection, in
  place of "checking that decoded data matches expected patterns".
- In (#anchoring-the-layer-check), "whether or not that profile
  governs it for its blocks (Section 7.4)" now cites
  (#provisional-blocks).
- In (#anchoring-the-layer-check), "so that a relay on that path
  cannot stop FEC for the source track with one packet" now reads "so
  that a relay on that path cannot stop FEC for the instance with one
  packet", per the core's data model.
- In (#deadline-anchoring-and-discard), the -01 Section 9 sentences
  that require a receiver to bound the state it holds for open
  blocks by a receiver-local policy (a memory cap, a local timeout,
  or a later block past its own deadline), forbid the policy to
  discard a block before its FEC deadline or while a unicast repair
  FETCH for it is outstanding except under a memory cap, and require
  the receiver to keep the policy separate from the catalog values
  are replaced by "A receiver bounds the state it holds for open
  blocks by the receiver-local policy of Section
  9.4 of [MOQ-FEC-CORE], which forbids discarding
  a block that has an FEC deadline before that deadline, or while a
  FETCH for it is outstanding, the unicast repair FETCH of
  (#keyframe-bearing-blocks) included, except under a memory cap.  A
  block so discarded is, under that section, treated from then on as
  having reached its FEC deadline unrecovered and, on a track whose
  blocks (#block-classification) classifies, of unknown class." and
  "The policy is not signaled and is kept separate from the
  configured values (Section 9.4 and Section
  9.3 of [MOQ-FEC-CORE]): it changes
  neither `interleaveDepthMs` nor `reorderToleranceMs` nor a deadline
  derived from them, and discarding a block under it does not create
  an FEC deadline ((#receiver-repair-policy)).", because the
  requirements themselves are the core's; this document keeps only
  their consequences on a multicast or AMT leg.
- In (#unicast-repair-budget), "where P_t is the total repair count
  of its base instance (Section 6.4.1)" now reads "where P_t is the
  total repair count of its base instance, the sum of P_i over its
  published layers ([MOQ-FEC-CORE])", and "in the Source Media range"
  now reads "in the source track range", the core's name for the
  64-191 range.
- In (#relationship-to-the-keyframe-overlay), "The keyframe overlay
  of Section 6.4 and this policy are complementary" now reads "The
  keyframe overlay of [MOQ-MMT], an overlapping instance in the sense
  of [MOQ-FEC-CORE], and this policy are complementary".
- In (#security-considerations), the preamble "When FEC is used over
  multicast (SSM/AMT), which carries only mmtp tracks under
  iso-ssbg1-v1 ([MOQ-MULTICAST] Section 4.1), additional
  considerations apply" is preceded by two new sentences (below).
- In (#acknowledgements), "Marc E. Fiuczynski reviewed this revision
  and reported how relays and MoQ Transport stacks of the time handle
  datagram-delivered repair objects (Sections 7.5, 10 and 11.4.2)."
  now reads "Marc E. Fiuczynski reviewed draft-ramadan-moq-fec-01 and
  reported how relays and MoQ Transport stacks of the time handle
  datagram-delivered repair objects, which shaped the FETCH behavior
  of (#keyframe-bearing-blocks) and the priority rules of
  (#unicast-repair-budget)".  -01 Sections 7.5 and 10 are now
  sections of [MOQ-FEC-CORE].
- Every citation of a section of draft-ramadan-moq-fec-01 is
  re-pointed at the section of [MOQ-FEC-CORE], [MOQ-FEC-CATALOG] or
  [MOQ-MMT] that now holds it, and every intra-document reference at
  the section of this document.

New sentences:

- The Abstract, (#introduction) and (#relation-to-other-documents)
  are new.
- In (#conventions-and-definitions): the paragraph "The terms below
  are used in this document with the meaning that [MOQ-FEC-CORE]
  gives them; every other term of that document, and of
  [MOQ-MULTICAST], keeps its meaning there."; the definitions of
  Base Instance, FEC Deadline, Multicast Endpoint, and Unlisted Track
  and Admitted Packet; the sentence "Layer i may use RS_IDs from its
  RS_ID offset O_i, and carries P_i repair symbols per block." in the
  definition of Repair Layer; and the sentence "Under iso-ssbg1-v1 a
  source symbol is one FEC source packet, an MMTP packet framed as
  [MOQ-MMT] specifies." in the definition of Source Symbol.  Five
  definitions are not copied whole: Repair Track joins the core's
  definition to the iso-ssbg1-v1 clauses of -01 Section 2, without
  the moq-object-v1 clause, the ISO 3.1.7 and 3.1.9 term citations
  and the -01 Section 6.3 and 6.4 pointers, and cites [MOQ-MMT] at
  the AL-FEC message, where -01 cited it after "only the catalog
  declares"; Keyframe Overlay reads "over an MMTP-packaged source
  track", drops "with its own source symbol count, its own repair
  symbols, and its own repair track" and the scope keyframe
  declaration, drops the sentence "It is defined only under
  iso-ssbg1-v1.", and cites [MOQ-MMT] in place of -01 Section 6.4;
  Interleave Depth drops "the catalog form of protection_window_time
  in [ISO.23008-1] Sections 11.2 and C.6.3" and the moq-object-v1
  clause; Source Symbol carries only the first sentence of the core's
  definition; and SS_Start and SSB_length carries only the first
  sentence of -01's.  The other definitions are copied from Section 2
  of [MOQ-FEC-CORE] or of draft-ramadan-moq-fec-01.
- In (#multicast-delivery): "The catalog's authority over FEC
  configuration ([MOQ-FEC-CORE]) holds uniformly across a MoQ
  receiver's delivery paths, its multicast and AMT legs included."
  (reworded from -01 Section 5.2, which named the catalog fec
  object).
- In (#deployment-applicability): "Which tracks a multicast endpoint
  carries in this revision, and so which of the core's carriages
  reach a multicast leg, is stated in (#symbol-tracks-on-multicast)."
- (#symbol-tracks-on-multicast) is new in its entirety, including its
  Editor's Note.
- In (#repair-only-endpoints), after the sentence that forbids a
  receiver to use goodput, throughput, or estimated available
  bandwidth to decide whether to add or drop a repair layer: "The
  capacity check that
  [MOQ-FEC-CORE] recommends before a layer is added is the one
  exception: it can withhold an add that measured loss calls for, but
  it is neither a trigger for adding a layer nor a reason to drop
  one."  The core's receiver selection adds that check, which -01
  Section 6.3.5 did not have, and this sentence reconciles the -01
  Section 6.3.6 rule with it.
- In (#repair-only-endpoints), after "keeps its repair-layer
  selection for the track fixed": "This is an exception to the layer
  addition that [MOQ-FEC-CORE] recommends when a block fails to
  recover: without a signaled span a receiver has only a deadline of
  its own, and on a multicast or AMT leg this document does not let it
  change layers on that basis."
- In (#provisional-symbols): the preamble paragraph, and the first
  sentence of each of (#anchoring-the-layer-check),
  (#admitted-blocks-in-the-fetch-range) and
  (#deadline-anchoring-and-discard), which name the core rule that
  the carried clause qualifies.
- In (#receiver-repair-policy): the citation "([MOQ-MULTICAST];
  (#symbol-tracks-on-multicast))" added to "Multicast and AMT legs
  carry only mmtp tracks", and "and
  (#deadline-anchoring-and-discard)" added to the local-policy
  citation.
- In (#block-classification): the first paragraph, which scopes the
  section to tracks under iso-ssbg1-v1, names [MOQ-MMT] for the
  fields, and states that the classification is a receiver-side
  repair-ordering policy on MMTP packet headers and not instance
  membership, so that it does not conflict with the core's rule that
  receivers never classify media for FEC membership or for the repair
  they take, and that what it decides is only the order and budget of
  per-block unicast repair, which the core leaves to the receiver.
- In (#security-considerations): "The security considerations of
  [MOQ-FEC-CORE] and of [MOQ-MULTICAST] apply." and "Join
  authorization for repair-layer endpoints and the amplification
  exposure of layers are covered in (#repair-only-endpoints)."
- (#iana-considerations): "This document has no IANA actions."
- In (#acknowledgements): "He proposed the division of
  draft-ramadan-moq-fec-01 into the core document and its companions,
  of which this document is one."

{#acknowledgements numbered="false"}
# Acknowledgements

Marc E. Fiuczynski reviewed draft-ramadan-moq-fec-01 and reported how
relays and MoQ Transport stacks of the time handle datagram-delivered
repair objects, which shaped the FETCH behavior of
(#keyframe-bearing-blocks) and the priority rules of
(#unicast-repair-budget).  He proposed the division of
draft-ramadan-moq-fec-01 into the core document and its companions,
of which this document is one.
