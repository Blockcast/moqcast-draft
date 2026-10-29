%%%
title = "Forward Error Correction for Media over QUIC: Core Mechanism"
abbrev = "MoQ FEC Core"
ipr = "trust200902"
area = "wit"
workgroup = "moq"
submissiontype = "IETF"
date = "2026-10-29T00:00:00Z"
keyword = ["FEC", "MoQ", "erasure code", "unequal error protection"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-moq-fec-core-00"
stream = "IETF"
status = "standard"

[[author]]
initials = "O."
surname = "Ramadan"
fullname = "Omar Ramadan"
organization = "Blockcast"
  [author.address]
  email = "omar@blockcast.net"

[[author]]
initials = "M. E."
surname = "Fiuczynski"
fullname = "Marc E. Fiuczynski"
organization = "Rutgers University"
  [author.address]
  email = "mef@scarletmail.rutgers.edu"
%%%

.# Abstract

This document specifies how Forward Error Correction (FEC) repair data is carried alongside source media in Media over QUIC (MoQ) without naming a particular FEC code. It states the properties that an FEC scheme must have to be used with this mechanism, and defines everything that does not depend on the scheme: how source objects become source symbols, how source symbols are numbered and grouped into blocks, two ways of carrying source symbols (as the source track's own objects, or as a separate symbol track suited to datagram delivery), repair tracks that receivers subscribe to independently and in layers, the repair object format, repair Group IDs that make repair fetchable by block, and equal and unequal protection driven only by metadata that MoQ Transport exposes, so that FEC works when payloads are encrypted end to end. Relays need no FEC knowledge. Specific FEC schemes, catalog bindings, packaging-specific profiles and multicast delivery are left to companion documents.

{mainmatter}

{#introduction}
# Introduction

Media over QUIC (MoQ) [@!I-D.ietf-moq-transport] provides a publish/subscribe transport for real-time media through relays. QUIC recovers lost packets by retransmission, but a retransmission costs at least one round trip and, under loss, often several. Where the playout deadline is shorter than that tail, as in interactive, low-latency live and wireless delivery, retransmission recovers data after it is needed. Objects sent as QUIC datagrams are not retransmitted at all, and a delivery timeout abandons objects sent on streams.

Forward Error Correction (FEC) lets a receiver recover lost data from repair data sent ahead of need, without a round trip. This document defines how repair data is carried in MoQ so that:

1. relays forward and cache repair data as ordinary MoQ objects and need no knowledge of FEC;
2. each receiver chooses for itself whether to take repair data and how much, by subscribing to repair tracks, as it already chooses a rendition;
3. the mechanism does not depend on a particular FEC code: it states what a code must provide (Section 4), and companion documents specify codes;
4. no receiver or relay needs to read a source object's payload, so FEC works when payloads are encrypted by Digital Rights Management (DRM) or by MoQ end-to-end encryption [@?I-D.ietf-moq-secure-objects].

{#design-principles}
## Design Principles

The repair mechanism sits above MoQ Transport and below the streaming format. It treats source objects as opaque byte sequences and decides how redundancy is derived, named, carried, added and fetched. The streaming format, or the application that publishes it, decides which media get how much redundancy, and expresses that decision only through configuration and through per-object metadata defined here (Section 8).

Protection is chosen by the receiver. A publisher can measure its own hop well, but only the receiver knows what loss remains after repair and how close each block is to its playout deadline, which is the signal that decides how much repair it needs. A receiver expresses its choice with SUBSCRIBE and UNSUBSCRIBE, which every relay already implements, so the quality a receiver gets does not depend on which relays its path crosses.

Repair data is additive. A repair symbol is fixed by the block it protects and its index, never by how many repair symbols the publisher generates (Section 4.2), so repair split across several tracks combines in one decode, and a receiver adds or drops repair tracks without the publisher re-encoding anything.

{#relation-to-other-documents}
## Relation to Other Documents

This document is the core of a set of documents. It defines the scheme-independent mechanism and the configuration data model. The companion documents are:

- [@!MOQ-FEC-BLOCK], which specifies FEC schemes that meet Section 4, each with its parameter derivation and test vectors: the systematic Reed-Solomon code over GF(2^8) and RaptorQ, and which designates the mandatory-to-implement scheme (Section 4.4);
- [@!MOQ-FEC-CATALOG], the binding of the configuration data model of Section 10 to the catalog of the MOQT Streaming Format [@?I-D.ietf-moq-msf] and the Common Media Application Format (CMAF) profile of that format [@?I-D.ietf-moq-cmsf];
- [@?MOQ-MMT], which defines the packaging-specific block profile for tracks packaged as MPEG Media Transport Protocol (MMTP) packets, and the broadcast interworking that relies on it;
- [@?MOQ-FEC-MULTICAST], the multicast and hybrid unicast/multicast delivery of protected tracks, independent of how multicast is carried, which [@?MOQ-MULTICAST] specifies.

Appendix A lists the companion documents and what each takes from [@?I-D.ramadan-moq-fec], from which much of this document's text is derived.

{#editor-s-notes removeInRFC="true"}
## Editor's Notes

The name, the author list and the division of material between this document and its companions are open for discussion. Text marked [open] records a question the authors have not settled.

[open] Section 15.1 keeps the pointer of draft-ramadan-moq-fec-01 to Section 8.4 of [@!I-D.ietf-moq-transport] for the "MOQ Properties" registry. In draft-ietf-moq-transport-22, Section 8.4 is the Track and Object Properties text that Section 5.2 of this document cites for relay handling of mutable Properties, and the registry and its registration policies are in Section 16.8. The pointer is to be settled against the current MoQ Transport draft before posting.

{#conventions-and-definitions}
# Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [@!RFC2119] [@!RFC8174] when, and only when, they appear in all capitals, as shown here.

**Source Track**: A MoQ track whose objects carry media, for example video or audio, and which an FEC instance protects.

**Source Object**: An object of a source track, with Object Status Normal ([@!I-D.ietf-moq-transport] Section 11.1.1), that the publisher protects by at least one FEC instance. It carries an FEC Source Info Property (Section 5.6) naming those instances.

**FEC Instance**: One independent FEC encoding over a sequence of source symbols, with its own source symbol bound K, symbol size T, SS_ID space, block partition, repair symbols and repair tracks. A source track has one or more FEC instances (Section 5.1).

**Source Symbol**: A T-byte unit of source data that an FEC instance encodes. Source symbols are formed from source objects by the instance's block profile (Section 5.2).

**Repair Symbol**: A T-byte unit generated by the FEC scheme from the source symbols of one block.

**SS_ID**: The 32-bit sequence number of a source symbol within its FEC instance. It wraps modulo 2^32 (Section 7.6).

**Source Block**: A run of SSB_length consecutive source symbols, 1 <= SSB_length <= K, over which a block FEC scheme encodes. A block is the SS_ID range [SS_Start, SS_Start + SSB_length) and is identified by its SS_Start.

**Encoding Symbol ID (ESI)**: The index of a symbol within its block: a source symbol's serial distance from SS_Start, and SSB_length + RS_ID for a repair symbol.

**RS_ID**: The zero-based index of a repair symbol among the repair symbols of its block.

**RSB_length**: The number of repair symbols generated for a block: the instance's total repair count P when the block's repair symbols are generated, carried in the Repair FEC Payload ID of every repair object of the block (Section 7.5).

**Repair Track**: A MoQ track whose objects each carry one repair symbol of one FEC instance (Section 7).

**Repair Layer**: One of possibly several repair tracks of one FEC instance, each carrying a disjoint range of RS_IDs for every block (Section 7.3). Layer 0 is the base layer.

**Symbol Track**: A MoQ track whose objects each carry exactly one source symbol of one FEC instance, grouped by block (Section 6.2).

**Object Carriage** and **Symbol Carriage**: The two ways in which the source symbols of an FEC instance reach a receiver: inside the source track's own objects, from which the receiver builds the symbols (Section 6.1), or as the objects of a symbol track (Section 6.2).

**Protected Object Unit**: The bytes that one source object contributes to an FEC instance: its Location, its Immutable Properties and its payload, framed as Section 5.2 specifies.

**Protection Class**: A set of source objects of one track that the publisher protects as one FEC instance, distinct from the track's other objects (Section 8).

**Block Profile**: The rules that fix how source symbols are formed from source objects and how blocks are delimited and identified (Section 5.2).

**FEC Scheme**: An FEC code together with the specification of its parameters, its symbol construction and its repair symbols, meeting Section 4.

{#architecture-and-overview}
# Architecture and Overview

{#tracks}
## Tracks

A publisher that protects a source track publishes, alongside it:

- one or more repair tracks per FEC instance, carrying repair symbols (Section 7); and
- optionally, one symbol track per FEC instance, carrying the instance's source symbols (Section 6.2).

All of these are ordinary MoQ tracks in the source track's Track Namespace. Relays forward, cache and serve them as they do any other track. The relationship between the tracks, and the parameters of each FEC instance, are given by configuration that a receiver obtains before it subscribes, normally in the catalog of the streaming format (Section 10). No MoQ control message is defined or changed.

~~~
Publisher        Relay(s)               Receiver
---------        --------               --------
source track   --- objects -----------> plays on arrival
symbol track   --- 1 symbol/object ---> FEC family (datagrams)
repair layer 0 --- 1 repair/object ---> taken when needed
repair layer 1 --- 1 repair/object ---> added on more loss
repair layer n --- ...                  (not subscribed)
~~~

{#protocol-overview}
## Protocol Overview

The protocol operates as follows ((#example-message-flows) shows the exchange):

1. The receiver obtains the configuration of the source track's FEC instances (Section 10).
2. It subscribes to the source track, or to an instance's symbol track, or both (Section 6).
3. When its path conditions call for it, it subscribes to one or more repair layers of an instance, and later adds or drops layers (Section 7.4).
4. The publisher emits source data and, for every block, the block's repair symbols on each layer.
5. The receiver uses source objects and source symbols as they arrive. When some are missing, it decodes each block from the source and repair symbols it holds (Section 9), and it MAY fetch a block's missing repair or source symbols from a relay cache by Group (Section 7.7).

A receiver that implements none of this document, or that chooses not to use FEC, subscribes to the source track only and is unaffected: repair and symbol tracks are optional and a publisher or relay MUST NOT condition delivery of a source track on a subscription to them.

{#when-fec-helps}
## When FEC Helps

The code is systematic (Section 4.2), so a receiver presents source data as it arrives, and FEC adds latency only when a block needs to be decoded.

When source data travels on QUIC streams, QUIC retransmits it, and FEC helps only where the deadline is too short for retransmission or a delivery timeout abandons an object ([@!I-D.ietf-moq-transport] Section 5.2). When source data travels as QUIC datagrams, nothing is retransmitted, and FEC or a FETCH from a relay cache is the only recovery. When a path has no return channel at all, as on multicast, FEC is the only recovery.

The erasure unit is what the network loses. Under object carriage (Section 6.1), the loss of one object erases every source symbol of its Protected Object Unit, so a large object needs as many repair symbols as it spans. Under symbol carriage (Section 6.2), one lost datagram erases one symbol. This is why symbol carriage exists: it makes FEC efficient for the large objects of video, delivered as datagrams.

{#fec-scheme-requirements}
# FEC Scheme Requirements

This document does not specify an FEC code. It specifies the properties that a code must have to be used with it, and the information that a scheme's specification must give. An FEC scheme is identified by a string registered in the "MoQ FEC Schemes" registry (Section 15.2).

{#scheme-classes}
## Scheme Classes

This document defines one class of FEC scheme, block schemes (Section 4.2), and reserves a second, sliding-window schemes (Section 4.3).

A block scheme encodes each source block independently and generates repair symbols over that block only. Every mechanism of Sections 5 to 9 is defined for block schemes.

A sliding-window scheme generates each repair symbol over a window of consecutive source symbols that overlaps the windows of other repair symbols, as the Random Linear Codes of [@?RFC8681] do. Such schemes avoid the latency of waiting for a block to fill, but they do not have blocks, so the Repair FEC Payload ID, repair Group IDs and FETCH rules of Section 7 do not apply to them unchanged.

{#requirements-on-block-schemes}
## Requirements on Block Schemes

A block scheme MUST have the following properties, and its specification MUST establish each of them for the construction it specifies.

1. **Erasure code.** It recovers source symbols that are missing, at known positions, from the symbols that are present. It is not required to correct errors.

2. **Systematic.** The source symbols of a block are among its encoding symbols and are sent unchanged, so a receiver uses each source symbol it receives without decoding.

3. **Fixed symbol size.** Every source and repair symbol of a block is exactly T bytes, where T is the instance's symbol size (Section 10.1). The specification states any constraint on T, for example an alignment.

4. **Index-fixed repair.** The repair symbol with a given RS_ID in a given block is a function of that block's source symbols and of the RS_ID alone. It does not depend on the total number of repair symbols generated for the block, on how they are divided among repair tracks, or on K. This is the property that makes repair layers (Section 7.3) and the short blocks of Section 5.4 possible. For example, a Reed-Solomon code in generator-polynomial form, whose parity depends on the number of parity symbols, lacks it; a systematic code whose generator matrix fixes each repair column by the column's index alone, such as a Vandermonde-derived or Cauchy-derived Reed-Solomon code, or a fountain code with an open Encoding Symbol ID space such as [@?RFC6330], has it.

5. **Parameters from configuration and the wire.** A decoder is fully configured from the instance's configuration (Section 10.1) and the Repair FEC Payload ID of each block (Section 7.5). No other per-session or per-block signaling is defined, and the specification MUST NOT require any, so a receiver that has the configuration needs nothing else, whatever path it receives symbols over.

6. **Stated bounds.** The specification states the largest K, the largest SSB_length + RSB_length, and the largest RS_ID that its construction supports, and a receiver rejects a configuration or a repair object outside them.

7. **Stated recovery condition.** The specification states the condition under which a block is recoverable, as a decoding overhead e: the block recovers whenever the receiver holds at least SSB_length + e distinct encoding symbols of it, with e = 0 for a maximum distance separable (MDS) code, and with the probability of failure at each small overhead for a code that is not MDS.

8. **Deterministic and verifiable.** Encoding is deterministic: two conforming encoders produce identical repair symbols from identical source symbols, so repair from different publishers of the same encoding, or from any relay cache, combines. The specification includes test vectors that distinguish its construction from other constructions of the same family.

A block scheme SHOULD be MDS, or close to it at the block sizes it targets, because the receivers that take the most repair are the ones on the lossiest paths. A scheme specification SHOULD state the encoding and decoding cost per block in terms of K, the number of missing symbols and T, so that a receiver can bound its work (Section 14).

A scheme specification MUST state whether the scheme supports repair layers. A scheme that supports them states how an RS_ID maps to the code's symbol index and bounds K plus the total repair count of an instance by its construction's limit. Every scheme that meets requirement 4 can support them.

{#sliding-window-schemes}
## Sliding-Window Schemes

Editor's Note: this section is a placeholder. The authors expect a companion document to specify sliding-window schemes, and do not yet know whether all of what follows holds [open].

A sliding-window scheme can be used with this mechanism only if its specification defines, at least:

1. a repair payload identifier that replaces the Repair FEC Payload ID of Section 7.5 and carries, with each repair symbol, everything needed to place it: for example the first SS_ID and the length of its coding window, and a key from which the coefficients of the combination are derived;
2. how repair is divided into layers: for random linear combinations over the same window, repair symbols generated from disjoint key ranges on different tracks are linearly independent with high probability and therefore additive, which is the property requirement 4 provides for block schemes;
3. how repair objects are grouped into MoQ Groups so that a receiver can request the repair that covers a given lost source symbol by FETCH, as Section 7.7 does by block;
4. the recovery condition, which for overlapping windows is the rank of the received equations rather than a count of symbols, and how a receiver that fetches repair decides how many symbols to request;
5. how the publisher bounds the window, by count or by time, without feedback from receivers;
6. how the symbols of a symbol track map to Group IDs and Object IDs, what PRIOR_GROUP_ID_GAP on a symbol-track object means, and the checks a receiver applies to symbol-track objects, since Section 6.2 states all of these by block, through SS_Start, ESI and SSB_length.

The source symbol construction, SS_ID assignment, object carriage, the FEC Source Info Property, protection classes and the security considerations of this document apply to such a scheme unchanged; symbol carriage applies with the Location mapping, PRIOR_GROUP_ID_GAP meaning and receiver checks of Section 6.2 replaced by those of item 6.

{#mandatory-to-implement-scheme}
## Mandatory-to-Implement Scheme

The block-codes companion document [@!MOQ-FEC-BLOCK] designates the systematic Reed-Solomon code over GF(2^8) with a Cauchy generator matrix as the mandatory-to-implement scheme (Section 10 of [@!MOQ-FEC-BLOCK]); RaptorQ [@?RFC6330] is optional.

Editor's Note: whether this document should itself require the mandatory-to-implement scheme, so that it is interoperable without its companions, is [open].

{#unimplemented-schemes}
## Unimplemented Schemes

A receiver that does not implement the scheme of an FEC instance forgoes FEC for that instance. It consumes the source track as if the instance did not exist and does not subscribe to the instance's repair or symbol tracks. This is not an error: repair subscription is optional, so an instance under a scheme that a receiver lacks is protected only for the receivers that implement it.

{#fec-instances-and-source-symbols}
# FEC Instances and Source Symbols

{#fec-instances}
## FEC Instances

An FEC instance is one independent FEC encoding. Each instance of a source track has an Instance ID, an integer from 0 to 255 that is unique among the instances of that track, and its own parameters (Section 10.1): its FEC scheme, its block profile, its source symbol bound K, its symbol size T, its repair layers and, optionally, its symbol track. Every per-block quantity of this document (K, T, SS_ID, SS_Start, SSB_length, RS_ID, RSB_length, ESI, the wrap epoch and the repair Group IDs) is defined within one instance. A receiver MUST NOT reuse a symbol's coordinates in one instance as its coordinates in another, and MUST NOT feed a symbol to the decoder of an instance other than the one it was received for, except that a symbol of a Protected Object Unit MAY be placed in another instance to which the unit belongs, at the SS_ID that the unit's FEC Source Info Property gives it there, as Section 8.4 permits for symbols received by symbol carriage and for the symbols of a rebuilt object.

A track protected uniformly has one instance. A track with several protection classes has one instance per class, and an object can belong to more than one instance (Section 8). The instances to which a source object belongs are those its FEC Source Info Property names (Section 5.6), and nothing else: a receiver MUST NOT infer instance membership from an object's Group, Object ID, size, priority, payload or position.

{#block-profile-and-the-protected-object-unit}
## Block Profile and the Protected Object Unit

A block profile fixes how source symbols are formed from source objects, how many source symbols a block holds, and how blocks and source symbols are identified. This document defines one block profile, "moq-object-v1", which applies to every source track whose objects carry their media as whole MoQ objects, whatever their packaging. Other block profiles, for example the one that forms source symbols from MMTP packets ([@?MOQ-MMT] Section 7.1), are defined by companion documents and registered (Section 15.3). A profile's specification MUST fix how source symbols are formed, how many a block holds, how a block and the source symbols in it are identified, and how those identifiers wrap. The rest of this document is written for "moq-object-v1"; a companion profile states which parts apply to it.

Under "moq-object-v1" the unit of protection is a whole MoQ object. The Protected Object Unit of a source object o is:

~~~
Protected Object Unit {
  Group ID (64),
  Object ID (64),
  Immutable Properties Length (16),
  Immutable Properties (..),
  Payload Length (32),
  Payload (..),
}
~~~

All integers are unsigned and in network byte order.

- **Group ID** and **Object ID**: the Location of o ([@!I-D.ietf-moq-transport] Section 8.2).
- **Immutable Properties Length**: the length in bytes of the value of o's Immutable Properties Property ([@!I-D.ietf-moq-transport] Section 10.7), or 0 when o has none. A Property value has at most 2^16 - 1 bytes ([@!I-D.ietf-moq-transport] Section 8.3).
- **Immutable Properties**: that value, exactly as the publisher serialized it. No node may change it ([@!I-D.ietf-moq-transport] Section 10.7). It includes o's FEC Source Info Property (Section 5.6).
- **Payload Length**: the length in bytes of o's Object Payload.
- **Payload**: o's Object Payload, as transmitted. When the payload is encrypted, this is the ciphertext.

The fields are fixed-width because a variable-length integer has several valid encodings, so a variable-length field would make the unit depend on the encoding a session chose. The unit is 22 bytes longer than the Immutable Properties value and the payload together. The mutable Properties, Subgroup ID, Publisher Priority and delivery mode of o are not in the unit, so none of them affects FEC: a relay may add, change or remove mutable Properties as [@!I-D.ietf-moq-transport] Section 8.4 allows, and the publisher chooses the other three, which [@!I-D.ietf-moq-transport] Section 7.8 forbids a relay to modify.

Let len(o) be the length of the unit in bytes and T the instance's symbol size. The unit occupies

~~~
s(o) = ceil(len(o) / T)
~~~

source symbols of the instance: the unit followed by s(o) x T - len(o) zero octets, cut into s(o) consecutive T-byte symbols. Neither the fixed-width fields nor the padding is transmitted under object carriage: the object travels in its usual MoQ form, and the publisher and each receiver build the unit from the object's fields. When o belongs to several instances, the unit is the same bytes in each, and s(o) is computed with each instance's own T.

The construction follows the application data unit framing of [@?RFC6681] Section 5, with fields sized for MoQ objects.

{#ss-id-assignment}
## SS_ID Assignment

Within each instance, the publisher assigns SS_IDs to the source symbols of the objects that belong to the instance, in the order in which it emits those objects. The first SS_ID of the instance is arbitrary. Let SS_ID(o) be the SS_ID of the first source symbol of o in the instance. The unit of o occupies the s(o) SS_IDs from SS_ID(o) on, and the next object o' of the same instance starts where o ends:

~~~
SS_ID(o') = (SS_ID(o) + s(o)) mod 2^32
~~~

SS_ID(o) depends only on the objects of the instance emitted before o, and the FEC Source Info Property has a fixed length for a given set of instances, so the publisher can place the Property inside the unit that it numbers.

An object that belongs to no instance is not a source object: it carries no SS_ID and is not counted in any block. Because SS_IDs are consecutive within an instance, a receiver sees the loss of a source object as missing SS_IDs even before it knows the block partition.

{#blocks-and-short-blocks}
## Blocks and Short Blocks

A block holds whole units: every SS_ID of a source object lies in the block that holds its first SS_ID, so SSB_length is the sum of s(o) over the objects of the block. The blocks of an instance are consecutive: each starts at the SS_ID that follows the last source symbol of its predecessor, so every SS_ID belongs to exactly one block.

A publisher MUST NOT publish a source object whose s(o) exceeds K in any instance it belongs to; it chooses K and T so that the unit of its largest object fits in K x T bytes. A publisher MUST close a block when it has assigned K source symbols to it, and when the open block holds more than K - s(o) source symbols it MUST close the block before it assigns SS_IDs to o, which then starts the next block. It MAY close a block earlier, at any object boundary: for example at a Group boundary, after a frame, or to bound the block's send span (Section 9.3). A block with SSB_length less than K is a short block and differs from a full one only in SSB_length:

1. The publisher encodes it as a block of SSB_length source symbols, at ESIs 0 to SSB_length - 1 in SS_ID order. No padding symbol is transmitted, and none is counted in SSB_length. A scheme that internally extends a block to a size of its own does so inside its encoder and decoder.
2. Its repair ESIs start at SSB_length: ESI = SSB_length + RS_ID.
3. It is complete, and needs no repair, once the receiver holds all its SSB_length source symbols, and recoverable once the receiver holds SSB_length + e distinct encoding symbols of it, where e is the scheme's decoding overhead (Section 4.2).

The publisher MUST carry SSB_length in every repair object of the block, on every repair track of the instance (Section 7.5). Repair objects are the only wire signal of a block's extent, except for the symbol-track signal of Section 6.2. Until a receiver has accepted a repair object of a block, or the signal of Section 6.2, it holds the block's source symbols without placing them. It MUST NOT infer a block boundary or SSB_length from a gap in SS_IDs, from a Group boundary of the source track, from elapsed time or from K.

A receiver MUST fail closed on inconsistent block signaling. It MUST discard a repair object whose SSB_length is 0 or exceeds K, one whose SSB_length differs from the value it has already accepted for the block with the same SS_Start, and one whose range [SS_Start, SS_Start + SSB_length) overlaps a different block it has already accepted, in each case leaving the state of every block unchanged.

{#locating-a-source-symbol}
## Locating a Source Symbol

A source symbol belongs to the block whose (SS_Start, SSB_length) range contains its SS_ID under the serial arithmetic of Section 7.6, and its ESI is its serial distance from SS_Start:

~~~
ESI = (SS_ID - SS_Start) mod 2^32,   0 <= ESI < SSB_length
~~~

An object o whose first SS_ID has ESI ESI(o) occupies ESIs ESI(o) to ESI(o) + s(o) - 1 of its block. No source symbol's block can be computed from its SS_ID alone, because blocks differ in length, and this document defines no block number. A receiver holds a source symbol whose block it has not yet delimited and places it when the block is delimited.

The receiver MUST NOT feed the decoder a source object whose s(o) exceeds K, one whose SS_IDs do not all lie in the block that holds SS_ID(o), or either of two different objects whose SS_ID ranges in the same instance overlap. Each means that the object or the block signaling is not what the publisher sent. The receiver MAY still deliver such an object as media.

Within one instance, a receiver deduplicates source symbols by SS_ID and repair symbols by (SS_Start, RS_ID). Every path that delivers a symbol of an instance, including FETCH and either carriage (Section 6), delivers it at the same coordinates, so a receiver MAY combine symbols received over any of them in one decode.

{#fec-source-info-property}
## FEC Source Info Property

A publisher MUST tag every source object with exactly one FEC Source Info Object Property, whose type is the odd value 0x11 (Section 15.1). The type is odd, so the value is a length-prefixed byte sequence, and a relay or receiver that does not implement this document steps over the Property by its length and forwards and caches it unmodified, as [@!I-D.ietf-moq-transport] requires of any Property it does not support.

0x11 is the value this document requests, and the registration policy for the range it lies in is not reachable by an individual draft (Section 15.1). Until that request is resolved, 0x11 is to be read as provisional. If it is not obtainable, Section 15.1 names an odd value in the range 0x80 to 0x37FF as the fallback. That value can take a 2-byte Delta Type ([@!I-D.ietf-moq-transport] Section 8.3), so adopting it can change the length of an object's Properties on the wire and not only the constant in this paragraph.

The value is either of:

~~~
FEC Source Info (single instance) {
  SS_ID (32),
}

FEC Source Info (instance list) {
  Instance Entry (40) ...,
}

Instance Entry {
  Instance ID (8),
  SS_ID (32),
}
~~~

A value of exactly 4 bytes names instance 0 and carries SS_ID(o) in that instance; it is the form of [@?I-D.ramadan-moq-fec]. A publisher MUST use the list form on a track that declares no instance 0. A publisher MUST use the 4-byte form for an object that belongs to instance 0 and to no other instance, so that a given set of instances has exactly one encoding, the unit of Section 5.2 is the same bytes from every publisher of the same encoding (Section 4.2, requirement 8), and an object of a track with the single instance 0 is tagged exactly as [@?I-D.ramadan-moq-fec] specifies; it uses the list form only for an object that belongs to an instance other than 0. Any other value is a sequence of one or more 5-byte Instance Entries, one for each instance to which the object belongs, in strictly increasing order of Instance ID, each carrying SS_ID(o) in that instance. The two forms cannot be confused, because 4 is not a multiple of 5. A value whose length is neither 4 nor a positive multiple of 5, whose Instance IDs are not strictly increasing, or that is a single Instance Entry naming Instance ID 0, does not match the serialization of this type. When an object it receives carries such a value, a receiver that implements this document MUST close the session with KEY_VALUE_FORMATTING_ERROR, as [@!I-D.ietf-moq-transport] requires for a Property whose type is understood and whose value does not match; such a value in a rebuilt object fails the checks of Section 9.2 and is not a protocol error. An entry naming an Instance ID that the configuration does not declare for the track is ignored for decoding.

SS_ID is a fixed 32-bit field rather than a variable-length integer because [@!I-D.ietf-moq-transport] does not require minimal varint encodings, and because its varint encoding has changed between versions; a fixed width decodes identically on every version and through a relay that re-encodes between versions.

The Property MUST be carried inside the object's Immutable Properties, where no node may change it, where it is part of the Protected Object Unit and so is recovered with the object, and where end-to-end authentication covers it (Section 14). It MUST NOT be carried inside an encrypted container, such as the Encrypted Properties List of [@?I-D.ietf-moq-secure-objects], because a receiver needs it before it decrypts and a relay that serves FETCH may need it without the keys. An object that carries more than one FEC Source Info Property, counting mutable and Immutable Properties together, or one outside its Immutable Properties, is treated as an object that carries none.

An object that carries none is not a source object (Section 5.3). A receiver MUST NOT feed it to any decoder and MAY deliver it as media.

The Property carries no block coordinate and no length. A receiver places the object's symbols by SS_ID (Section 5.5) and learns the block's extent from repair objects or the symbol track (Sections 5.4 and 6.2). The lengths that rebuilding needs are inside the unit and are recovered with it.

Deployed implementations of earlier drafts used the even value 0x10 for this purpose. That value is the TIMESTAMP Property of [@!I-D.ietf-moq-loc] in the same type space, and a receiver that implements TIMESTAMP misparses a 0x10-tagged FEC value as a variable-length integer and can lose its place in the Property sequence. An implementation of this document MUST NOT send 0x10 for this purpose; the defence is necessarily at the publisher, because a receiver cannot tell such an object from a well-formed TIMESTAMP.

{#source-symbol-carriage}
# Source Symbol Carriage

The source symbols of an instance reach a receiver by object carriage, by symbol carriage, or both. The two carry identical symbols at identical SS_IDs.

{#object-carriage}
## Object Carriage

Under object carriage the source track's own objects are the carriage. A receiver that holds a source object builds its Protected Object Unit from the object's fields (Section 5.2) and places the unit's s(o) symbols at the SS_IDs from SS_ID(o) on, in each instance the object belongs to.

The erasure unit is a whole object. An object sent as a datagram is dropped whole when it exceeds the maximum datagram size of a session on its path ([@!I-D.ietf-moq-transport] Section 11.2), and a delivery timeout drops a datagram or resets the stream that carries an object. A lost object erases all s(o) of its source symbols, so a block recovers its lost objects only when the receiver holds at least as many repair symbols as those objects span, plus the decoding overhead. Object carriage therefore suits small objects, such as audio frames, and objects on streams that a delivery timeout abandons. It needs nothing beyond the FEC Source Info Property, and a receiver that does not implement FEC consumes the track unchanged.

{#symbol-carriage}
## Symbol Carriage

Under symbol carriage an instance's source symbols are published as the objects of a symbol track, which the instance's configuration names (Section 10.2). Symbol carriage makes the erasure unit one symbol rather than one object, which is what makes FEC efficient for large objects sent as datagrams.

Each object of a symbol track carries exactly one source symbol:

- its payload is the T bytes of the symbol, padding included, and a receiver MUST discard a symbol-track object whose payload is not exactly T bytes;
- its Group ID is the extended SS_Start of the symbol's block, ext(SS_Start) (Section 7.6), the same Group ID that the block's repair objects use; and
- its Object ID is the symbol's ESI, from 0 to SSB_length - 1.

So the Location of a symbol-track object fixes the symbol's SS_ID as SS_Start + ESI, modulo 2^32, and a symbol track needs no FEC Source Info Property. The symbols of a block form one Group, so a relay cache can serve a block's source symbols by Group and a receiver can request them as it requests repair (Section 7.7). A receiver MUST discard a symbol-track object whose Object ID is not less than the SSB_length it has accepted for the block, and one whose Group ID, taken as an SS_Start, lies inside a different block it has already accepted, in each case leaving the state of every block unchanged. When it accepts a block's SSB_length after holding symbol-track objects of the block, it discards those whose Object ID is not less than that SSB_length. This document does not use End of Group status objects to delimit a block.

A symbol-track object whose symbol is the first symbol of a Protected Object Unit SHOULD carry an FEC Unit Start Object Property (Section 15.1), an even type whose value is the unit's s(o). It lets a receiver that cannot recover a whole block still rebuild every unit whose symbols it holds (Section 9.2). It is not part of any symbol and MAY be carried among the object's mutable or Immutable Properties. A receiver MUST NOT rely on its absence to conclude that a symbol does not start a unit. Editor's Note: this Property costs a codepoint. The alternative is to carry the unit sizes of a block in each of its repair objects, which helps only receivers that take repair [open].

A publisher MAY carry the PRIOR_GROUP_ID_GAP Object Property ([@!I-D.ietf-moq-transport] Section 10.8) on symbol-track objects, set to the SSB_length of the preceding block of the instance minus 1. A receiver that holds a symbol-track object of a block whose Group ID is g and that carries this Property with value v MAY delimit the preceding block as SS_Start = (g - v - 1) mod 2^32 and SSB_length = v + 1, subject to the consistency checks of Section 5.4. This is the one signal other than a repair object from which a receiver may learn a block's extent, and it reaches a receiver that takes no repair. The same Property on repair objects (Section 7.6) has the same meaning. Editor's Note: whether symbol carriage needs PRIOR_GROUP_ID_GAP to be a MUST on symbol-track objects, so that a receiver that takes no repair always learns block extents (Section 5.4), is not settled [open].

The publisher chooses the symbol track's delivery mode. Datagrams are the intended mode: a symbol fits one datagram when T plus the object's framing is within the maximum datagram size of every session on the path. A publisher that sends a symbol track on streams SHOULD put each symbol in its own subgroup, because several symbols on one stream are lost or delayed together and so reintroduce the head-of-line blocking that symbol carriage avoids. The cost of a stream per symbol is per-stream state and stream credit at each end.

A receiver that takes only a symbol track and an instance's repair tracks receives the media of the objects that belong to that instance, and only as rebuilt objects (Section 9.2): Immutable Properties and payload, without mutable Properties. Section 13 states what a packaging must place in Immutable Properties for such a receiver.

{#combining-carriages}
## Combining Carriages

A receiver MAY take an instance's source symbols by both carriages, for example the source track on streams and a FETCH of the symbol track for a block that a delivery timeout left incomplete. It deduplicates by SS_ID (Section 5.5). If a symbol built from a source object and the symbol-track symbol at the same SS_ID differ, at least one of them is not what the publisher encoded: the receiver MUST NOT feed either to the decoder, treats the block as unrecoverable by FEC, and MAY still deliver the source object as media.

{#choosing-a-carriage}
## Choosing a Carriage

This section is informative.

A publisher can offer the same content as two families of tracks, and each subscriber chooses one, as it chooses a rendition:

- a conventional family: the source track on streams, recovered by retransmission, with no repair; and
- an FEC family: an instance's symbol track on datagrams with the instance's repair layers, recovered by repair, with nothing retransmitted.

On a path where loss is rare and the deadline comfortably exceeds the retransmission tail, the conventional family costs nothing extra. On a lossy or variable path with a deadline near the round-trip time, and spare capacity for repair, the FEC family recovers what retransmission cannot reach in time. Keeping the two apart avoids mixing stream source with datagram repair on one connection, where stream data can delay the repair that is meant to beat retransmission. The SS_IDs of the source objects let a receiver that switches families resume at the block that holds the next SS_ID it needs.

The cost is upstream: when the subscribers behind a relay choose differently, the relay pulls both families, and the source crosses the links above it twice. A publisher for which upstream capacity is scarce can instead publish only the symbol track, on streams with one symbol per subgroup, and the repair layers: one copy of the source crosses every link, a subscriber that takes no repair still gets complete delivery by retransmission at a small overhead for symbol framing, and one that takes repair can decode before retransmissions arrive. That alternative spends per-symbol streams instead of upstream bandwidth. Neither choice is right for every deployment, and this document allows both.

{#repair-tracks}
# Repair Tracks

{#track-names}
## Track Names

Repair tracks and symbol tracks MUST be in the Track Namespace of the source track they serve. The configuration names them by Track Name (Section 10.2), and a receiver resolves every relationship between tracks from the configuration alone. A receiver MUST NOT infer that a track is a repair or symbol track, which source or instance it serves, or which layer it is, by parsing a track name, and a publisher MUST NOT rely on a receiver doing so. Names such as "video/repair/1" appear in this document for readability only.

{#subscription-model}
## Subscription Model

Repair is selective and chosen by each receiver. Before it subscribes to a repair track of an instance, a receiver SHOULD subscribe to the source track or to the instance's symbol track. A receiver subscribes to a repair track only when the configuration declares one and the receiver wants the protection, and it MAY start or stop a repair subscription at any time: for example only after it observes loss, or never on a reliable path. Publishers and relays MUST NOT require a subscription to a repair or symbol track, and MUST NOT condition delivery of a source track on one.

Where a receiver adds a repair layer mid-stream, the start location of its subscription decides whether the addition helps. A subscription that starts at the current Group of the repair track also delivers the repair already sent for the block in progress, which may rescue the block whose loss prompted the addition. A start earlier than that replays repair for blocks whose deadlines have passed, sent exactly when the path is struggling. A receiver SHOULD start a new repair subscription no earlier than the Group of the block in progress.

{#repair-layers}
## Repair Layers

An instance MAY have more than one repair track. Each is a repair layer: an independently subscribable set of repair symbols for every block of the instance. All layers of an instance share its block partition and parameters, and differ only in how many repair symbols each carries. Layering separates the two costs of FEC: the number of repair symbols buys tolerance to random loss at a cost in bandwidth, and the block span buys tolerance to burst loss at a cost in recovery latency (Section 9.3). Layers let a receiver on a lossier path add repair without changing the source encoding; a different K, T or block span needs a different instance.

{#repair-symbol-identity}
### Repair Symbol Identity

Let P_i be the number of repair symbols per block that layer i carries, and O_i its RS_ID offset:

~~~
O_0   = 0
O_i   = sum(P_j for j < i)
RS_ID = O_i + j, for the j-th repair symbol of layer i in a block
ESI   = SSB_length + RS_ID
~~~

Layer i carries, for every block, the repair symbols with RS_ID in [O_i, O_i + P_i). The instance's total repair count P is the sum of P_i over its published layers. RSB_length on every repair object of every layer carries P, not the layer's own P_i, so that a receiver holding any subset of layers computes the same coordinates for a symbol as one holding all of them.

By requirement 4 of Section 4.2, the repair symbol at a given RS_ID is the same whichever layer carries it and whatever other layers exist. Symbols received from any subset of layers, which need not be a prefix, over any mix of paths, therefore combine in one decode. A receiver holding a set of layers recovers a block whenever the symbols it lost, source and repair together, number at most C - e, where C is the total P_i of the layers it holds and e the scheme's decoding overhead. This tolerance is derived from the layer counts and the scheme's decoding overhead; it MUST NOT be signaled as a separate configuration parameter.

The encoder generates the instance's repair symbols for each block and assigns the disjoint RS_ID ranges to the layer tracks by O_i. It MUST NOT encode a layer as if it were the block's only repair, for example by generating the first P_i repair symbols of a block and labeling them from O_i: those are not the block's symbols at the RS_IDs they carry, and a receiver holding more than one layer could not combine them.

On layer i, the repair objects of a block form the MoQ Group whose Group ID is the block's ext(SS_Start) (Section 7.6). That Group carries P_i objects, and Object j of it carries the repair symbol with RS_ID O_i + j.

A receiver MUST take layer membership and each P_i from the configuration. RSB_length carries the total and says nothing about which layers a receiver holds.

{#changing-the-layer-set}
### Changing the Layer Set

Because O_i depends on every lower layer's P_i, a change to the layer set can move the coordinates of a layer that a receiver has already joined. Layer sets are therefore append-only. A publisher MAY append a layer at the next index above the highest published one, within the scheme's bounds (Section 4.2, requirement 6). It MUST NOT withdraw a published layer, at any index, for the lifetime of the source encoding, and MUST NOT renumber a published layer or change its P_i while any receiver may still be consuming the source track. A publisher that must retire a layer retires the source encoding and publishes a separate rendition under new Full Track Names (Section 7.6).

An append changes O_i for no published layer. It raises RSB_length, which is benign, because a receiver uses RSB_length only as a bound: a receiver holding configuration from before the append derives a total smaller than the RSB_length on the wire, and the difference covers only symbols of layers it has not joined. A publisher MUST apply a raised total from a block onward in the serial order of Section 7.6, generating the repair symbols of that block and of every block after it under the raised total or one raised later, and those of every block before it under a smaller one, whatever order its encoder generates the repair symbols of blocks in, so that RSB_length is non-decreasing in that order. The repair objects of a block generated under the previous total carry that total, which is O_n for the appended layer n and below O_n + P_n, and a receiver that joins layer n can receive such an object after the configuration that lists the layer, from a relay's cache or by a repair FETCH (Section 7.7).

Append-only makes the following check sound. RSB_length is non-decreasing over the lifetime of a source encoding in the serial order of Section 7.6, and a symbol of a layer above 0 is generated only under a total at or above that layer's O_i + P_i, so a wire RSB_length below a held layer's O_i + P_i on a repair object of that layer's track, the layer being above 0, or on a block at or after one that carried that O_i + P_i, is always a genuine violation: no operation this document defines produces one. A receiver MUST fail closed, and stop FEC for the instance, when, for any layer i it holds, the RSB_length carried on a repair object of that layer's track, i being above 0, or on a repair object of the instance of a block at or after, in the serial order of Section 7.6, one of which it has received a repair object carrying at least O_i + P_i, is less than the O_i + P_i derived from its configuration: its own layer's RS_ID range does not fit under the bound the publisher is advertising, so the two disagree about coordinates the receiver is using. It MUST NOT treat such an object as a symbol to discard under Section 7.5. A block before the anchoring one whose objects carry less was generated before the append and carries no symbol of layer i; its objects are symbols of the layers the receiver holds below i, under unchanged coordinates, and are not subject to the check. An RSB_length larger than the receiver's derived total is not an error in itself: that is the append case above. The check is a backstop and not a substitute for the publisher requirement: an increase to a lower layer's P_i shifts every higher offset while raising the total, and the wire does not reveal it. Nor does it catch a withdrawal of the highest layer for a receiver that holds that layer alone, which no repair object reaches after the withdrawal, or that receives no block generated while the layer was published; such a receiver learns of it only at the next configuration refresh, which this document does not bound.

{#receiver-selection}
## Receiver Selection

On a lossy path a receiver SHOULD subscribe layer 0 first. When a block fails to recover with its current layers and a higher layer exists, it SHOULD add the next layer; it MAY instead fetch only the failed block's repair objects from that layer (Section 7.7) when the block is still within its deadline (Section 9.3). It MAY drop a layer after a number of consecutive blocks, of its choosing, whose loss stayed within the tolerance of its remaining layers. Hysteresis is counted in blocks, the protocol's unit.

A receiver bases these decisions on the residual loss it observes after repair, against its deadline, and SHOULD also check that it has capacity for the repair it adds, because repair added on a path that is losing packets to congestion adds to the congestion. How a receiver estimates that capacity, and how it combines the choice of repair layers with the choice of rendition, is outside the scope of this document.

{#repair-object-format}
## Repair Object Format

Each object of a repair track carries one repair symbol of one block:

~~~
Repair Object {
  Repair FEC Payload ID {
    SS_Start (32),
    RSB_length (24),
    RS_ID (24),
    SSB_length (24),
  },
  Repair Symbol Data (..),
}
~~~

The payload is 13 + T bytes long. A receiver MUST discard a repair object whose payload is not exactly 13 + T bytes. A receiver routes a repair object to the decoder of the instance that the configuration relates to the repair track the object arrived on; no field of the object identifies the instance, and a receiver MUST NOT infer it from the field values.

**SS_Start (32 bits)**: The SS_ID of the first source symbol of the block. Its 62-bit extension is also the repair object's Group ID (Section 7.6).

**RSB_length (24 bits)**: The instance's total repair count P when the block's repair symbols are generated, identical on every repair object of the block. It rises when a layer is appended (Section 7.3.2).

**RS_ID (24 bits)**: The zero-based index of this repair symbol among the block's repair symbols. A receiver MUST discard a repair object whose RS_ID is not less than RSB_length, or that fails a bound of the instance's scheme (Section 4.2, requirement 6), except that a repair object whose RSB_length is less than O_i + P_i for a layer i the receiver holds, of that layer's track where i is above 0 or of a block to which the check of Section 7.3.2 applies, is handled by that check, which fails closed, and not by this rule.

**SSB_length (24 bits)**: The number of source symbols in the block, from 1 to K (Section 5.4). A publisher MUST NOT send 0 or a value above K; a receiver discards a repair object carrying either (Section 5.4).

**Repair Symbol Data**: Exactly one repair symbol, T bytes, generated by the instance's scheme for this block and RS_ID.

Carrying one symbol per object aligns the loss unit with the symbol and needs no symbol count. A repair object fits one datagram when 13 + T plus the object's framing is within the maximum datagram size of every session on the path.

The Repair FEC Payload ID has the field layout of the one-stage Repair FEC Payload ID of [@?ISO.23008-1] Section C.5.3, so a block profile for MMTP packets can carry the same fields in an MMTP repair packet ([@?MOQ-MMT] Section 7.3).

{#ss-id-wrap-and-repair-group-ids}
## SS_ID Wrap and Repair Group IDs

SS_ID and SS_Start are 32-bit values that start from an arbitrary value and wrap to 0 after their maximum. Every comparison, distance and range test on them in this document uses serial number arithmetic [@!RFC1982] with SERIAL_BITS = 32. A block can span the wrap: a block with SS_Start 2^32 - 3 and SSB_length 4 holds the SS_IDs 2^32 - 3, 2^32 - 2, 2^32 - 1 and 0.

The Groups of a track are ordered by Group ID, so the repair objects and symbol-track objects of a block are grouped under its 62-bit extended SS_Start rather than its 32-bit SS_Start, which wraps:

~~~
ext(SS_Start) = (wrap_epoch << 32) | SS_Start
~~~

wrap_epoch, from 0 to 2^30 - 1, is 0 for the first block of the instance's source encoding and increases by one at each block whose SS_Start is numerically below its predecessor's. Equivalently, a block's ext(SS_Start) is its predecessor's plus the predecessor's SSB_length. Repair and symbol-track Group IDs are therefore sparse, one per block at the block's first SS_ID, and strictly increasing. Only [0, 2^62) is used, so that a Group ID is representable in the Group ID encoding of every MoQ Transport version; at one million source symbols per second an instance takes more than 100,000 years to reach the bound.

Sparse Group IDs depart from the recommendation of [@?I-D.ietf-moq-msf] that each subsequent Group ID of a track increase by 1. The departure is deliberate: a Group ID that names its block's first SS_ID is what lets a receiver that has lost source symbols request the block's repair before it knows the block partition (Section 7.7). Within one source encoding the Group IDs still increase. A publisher MAY carry the PRIOR_GROUP_ID_GAP Object Property on the repair objects of a block, set to the preceding block's SSB_length minus 1, so that relays and receivers can tell Group IDs that will never exist from Groups that have not arrived.

A publisher that keeps its FEC state across a restart continues each instance's SS_ID sequence and wrap_epoch. A publisher that starts a new source encoding, including after a restart that loses its FEC state, MUST publish the source track and all of its repair and symbol tracks under Full Track Names that it has not used before, and MUST NOT resume a previously used repair or symbol Track Name with wrap_epoch reset to 0: the new encoding's objects would take Locations already used, and a receiver could feed a cached repair object of the old encoding to a block of the new one.

A repair object carries its block's start twice: in SS_Start and in its Group ID. SS_Start is authoritative. A receiver MUST discard a repair object whose Group ID modulo 2^32 differs from its SS_Start and, once it has established the wrap epoch, one whose Group ID differs from ext(SS_Start) or whose SS_Start it may not extend (below), in each case leaving the state of every block unchanged.

A receiver establishes the wrap epoch of an instance in one of the following ways, and MUST NOT assume one that it has not established:

1. from the Group ID of a repair or symbol-track object of the instance that it received and did not discard; that Group ID is its reference value r;
2. from the Largest Object that a TRACK_STATUS request for a repair or symbol track of the instance reports ([@!I-D.ietf-moq-transport] Section 9.13); the Group of that Location is r, and a reply without it establishes nothing;
3. as epoch 0, when it has observed the instance from its first block; r is then that block's SS_Start.

The epoch is r shifted right by 32 bits. The receiver extends a later 32-bit value x relative to an extended value r it holds to the 62-bit value congruent to x modulo 2^32 that is nearest r in serial order. It MUST NOT extend an x that lies exactly 2^31 from the low 32 bits of r, or one whose extension falls outside [0, 2^62). Serial arithmetic cannot detect an x more than 2^31 SS_IDs from r, so a receiver extends values relative to r only while it can bound that distance below 2^31, and MUST re-establish the epoch after any gap that it cannot so bound, such as a reconnection.

{#fetching-repair-and-source-symbols}
## Fetching Repair and Source Symbols

A receiver that holds a repair or symbol-track object of a block requests more of the block's symbols by a FETCH [@!I-D.ietf-moq-transport] of the one Group ext(SS_Start) on the track it wants them from: a repair layer it has not subscribed, or the instance's symbol track.

A receiver that has lost the source symbol with SS_ID x, and holds no object of the block that contains x, requests by FETCH the absolute, inclusive Group range

~~~
[ max(ext(S_prev) + 1, ext(x) - (K - 1)), ext(x) ]
~~~

where K is the instance's source symbol bound, so the block that contains x starts at most K - 1 SS_IDs before x; S_prev is the SS_Start of the last block the receiver has delimited that ends before x, and when there is none the range is [max(ext(x) - (K - 1), 0), ext(x)]; and ext(x) is x extended relative to ext(S_prev), or otherwise relative to the receiver's reference value r. Group IDs sit at block starts, so the range returns the Group of every block that starts within it, and the last Group it returns is the block that contains x. A receiver that has not established the wrap epoch, or that may not extend x (Section 7.6), has no range to request until it establishes one.

Each such FETCH carries a LOCATION_FILTER parameter ([@!I-D.ietf-moq-transport] Section 9.20.9): for a range [lo, hi], type 0x03 (Absolute Start, Group End) with StartGroup lo, StartObject 0 and EndGroupDelta hi - lo; for some objects of one Group, type 0x04 (Absolute Range) with StartGroup ext(SS_Start), the first and last Object IDs requested, and EndGroupDelta 0. On a repair layer, Object IDs are RS_ID - O_i; on a symbol track they are ESIs, so a receiver can request exactly the source symbols it lacks.

A FETCH costs at least one round trip to the relay that answers it. It suits blocks whose deadlines leave room for that round trip, and losses that are occasional rather than sustained; for sustained loss, adding a layer is cheaper than a FETCH per block (Section 7.4). Section 12 states what this requires of relays.

{#equal-and-unequal-protection}
# Equal and Unequal Protection

Losing some media costs more than losing other media. Losing part of a key frame can make every frame that depends on it undecodable until the next key frame; losing a frame that no other frame references costs that frame alone. Unequal protection gives the media whose loss costs more more repair. This section defines how a publisher expresses equal and unequal protection, using only configuration and the FEC Source Info Property, so that neither relays nor receivers need to read a payload to apply it.

The division of labour is fixed. The publisher decides which objects get how much protection. The mechanism of this document carries out that decision, media-blind. Receivers choose how much of the offered protection to take. Nothing in this section asks a relay or a receiver to classify media.

{#equal-protection}
## Equal Protection

A track protected equally has one instance, instance 0, and every source object of the track belongs to it.

All source objects of an instance share one SS_ID sequence, so an object that a receiver does not receive by design counts as an erasure and consumes repair: for example the subgroups of a temporal layer that a relay drops under congestion, or objects that a receiver chooses not to subscribe to. Media that receivers may skip is better published as a separate track, or as a separate protection class (Section 8.3), so that its absence costs no repair.

{#per-track-protection}
## Per-Track Protection

When the streaming format already places media of different importance on different tracks, as [@!I-D.ietf-moq-loc] does for spatial layers, each track carries its own instances with their own parameters and repair layers, and unequal protection needs nothing further from this document. This is the simplest form of unequal protection and SHOULD be preferred where the format already separates the media.

{#protection-classes}
## Protection Classes

A publisher MAY divide the objects of one track into protection classes, each protected by its own instance. A source object of a class carries an FEC Source Info Property naming that class's instance (Section 5.6), and its symbols are source symbols of each instance it names. Each class therefore has its own K, T, block span, repair layers, priorities and, optionally, symbol track, and a receiver chooses repair for each class separately: for example repair for key frames only.

An object that belongs to no instance is unprotected. A publisher MAY leave objects unprotected that are cheap to lose, such as frames that no other frame references; a receiver that loses one conceals it and continues.

Classes change the shape of blocks. A class that holds only key frames has large objects and few of them, so its blocks are large and span more time; a class of small, frequent objects fills its blocks quickly. The block span of each class is its own recovery latency (Section 9.3), so a publisher sizes each class's K and span against the deadline of the media it holds.

{#overlapping-instances}
## Overlapping Instances

A source object MAY belong to more than one instance. Its FEC Source Info Property then carries one entry per instance, with the object's SS_ID in each, and its Protected Object Unit, which includes that Property, is the same bytes in every instance. A typical use is an instance over every object of a track, with a short block span, together with a second instance over the key frames only, with a longer span: the second instance protects key frames across a window wider than the first instance's latency allows, without lengthening the first.

The instances are decoded independently. Because the unit is the same in each and carries every SS_ID of the object, a receiver that rebuilds an object from one instance learns its SS_ID in each other instance from the rebuilt FEC Source Info Property, and MAY place the object's symbols there as if it had received the object, after the checks of Section 9.2 and, in each other instance, those of Section 5.5. Recovery in either instance therefore reduces the erasures of the other.

When two instances have the same T, the unit is cut into the same symbols in both, so the symbol at offset j of an object's unit is the same bytes at SS_ID(o) + j in either instance. A receiver that holds some symbols of a unit by symbol carriage of one instance, and knows the object's SS_ID in another instance from the FEC Source Info Property in the unit's first symbol, MAY place those symbols in the other instance at the corresponding SS_IDs, after the checks of Section 5.5 there. Without this, a receiver that takes only one instance's symbol track contributes to another instance only the objects it rebuilds whole. A publisher that intends receivers to combine overlapping instances under symbol carriage SHOULD give them the same T and SHOULD keep each object's Immutable Properties within the first symbol of its unit.

A receiver that does not implement overlapping instances, or does not take a given instance, uses the entries for the instances it takes and ignores the rest.

{#classification-without-payload-access}
## Classification Without Payload Access

The entity that assigns protection classes is the one that knows what the media is: normally the encoder or packager. It can classify from the codec's frame types and reference structure, from the Low Overhead Media Container (LOC) Video Frame Marking Property [@!I-D.ietf-moq-loc], from the stream access point types of CMAF [@?I-D.ietf-moq-cmsf], or from an object's position in its group of pictures. This document does not specify a classification. The following is guidance:

- Rank media by what its loss costs, which follows from dependency, not from frame type letters. A predicted frame early in a group of pictures is referenced, directly or indirectly, by every later frame of the group, so its loss costs more than a predicted frame late in the group. Protection can decrease along the group.
- Low-latency encoders often emit no bidirectionally predicted frames, so a useful division may be key frames, early predicted frames, late predicted frames and non-reference frames.
- Unequal protection pays off only when the player exploits it: a player that drops to the next key frame on any unrecovered loss gains nothing from protecting late frames less.

Whatever the classification, its result reaches the rest of the system only as instance membership in the FEC Source Info Property and as configuration. A relay forwards objects without reading either. A receiver decodes each instance from the Property and the configuration alone, and never inspects a payload to decide which instance an object belongs to or how much repair to take. This is what lets unequal protection work when payloads are encrypted.

{#encryption}
## Encryption

FEC is computed over the Protected Object Unit, which holds the payload as transmitted. When payloads are encrypted, whether by DRM sample encryption such as Common Encryption [@?ISO.23001-7] or by MoQ Secure Objects [@?I-D.ietf-moq-secure-objects], source and repair symbols are computed over ciphertext, and recovery yields ciphertext, which the receiver then decrypts as it decrypts a received object. Repair symbols reveal nothing about the plaintext beyond what the ciphertext reveals.

Classification therefore happens before encryption, where the media is known, and FEC encoding after it, over the bytes that are sent. The two need not be done by the same entity, with one constraint: under MoQ Secure Objects, Immutable Properties are authenticated by the entity that protects the object, and no later node may change them, so the FEC Source Info Property, with every instance membership and SS_ID it carries, MUST be set by the entity that applies that protection, or by one before it. Any entity that holds the protected objects and the configuration can then compute the repair symbols, because they depend only on the transmitted bytes.

MoQ Secure Objects authenticates an object's Group ID, Object ID, Publisher Priority, Immutable Properties and payload, and leaves Immutable Properties readable by relays ([@?I-D.ietf-moq-secure-objects] Section 3). The unit carries all of these except the Publisher Priority. A publisher that protects a track this way SHOULD give every object of the track the track's default Publisher Priority ([@!I-D.ietf-moq-transport] Section 10.4), so that a receiver can form the authenticated data of a rebuilt object and verify it. A receiver verifies a rebuilt object as it verifies a received one and discards one that fails.

{#recovery}
# Recovery

{#decoding}
## Decoding

A receiver decodes a block when it holds, in total, at least SSB_length + e distinct encoding symbols of it and lacks some of its source symbols, where e is the scheme's decoding overhead. It configures the decoder from the instance's configuration and the block's Repair FEC Payload ID (Section 4.2, requirement 5). Decoding yields the block's SSB_length source symbols, SSB_length x T bytes in ESI order.

{#rebuilding-objects}
## Rebuilding Objects

The receiver rebuilds the objects it lacks from each run of ESIs that no source object it fed to the decoder covers. Under symbol carriage with no source objects held, the run is the whole block, which begins with a unit at ESI 0 because blocks hold whole units (Section 5.4). It walks each run from its first ESI, one unit at a time:

1. It reads Group ID, Object ID, Immutable Properties Length, Immutable Properties, Payload Length and Payload, in that order. Every byte read MUST lie inside the run.
2. With len the number of bytes read and s = ceil(len / T), every octet from the end of the unit to the end of its s-th symbol MUST be zero.
3. The next unit starts s symbols after the start of this one. The walk MUST end exactly at the end of the run.

If any check fails, the receiver MUST NOT deliver any object from the run. It also MUST NOT deliver a rebuilt object whose Immutable Properties do not parse as a sequence of Key-Value-Pairs, or contain an Immutable Properties Property; whose FEC Source Info Property is absent, has a value that does not match the serialization of Section 5.6, or does not name, for this instance, the SS_ID SS_Start plus the ESI at which the walk found the unit, modulo 2^32; or whose Location is that of an object the receiver already holds. A failed check concerns bytes the receiver computed, not an object it received, so it is not a protocol error of the session.

A receiver need not wait for a block to be delimited or decoded to rebuild a unit whose symbols it holds in full and whose start it knows: ESI 0 of every block is a unit start, and the end of each unit is the start of the next. It MAY rebuild and deliver such a unit at once, applying the checks above with the run being the unit's own symbols, so that symbol carriage adds no latency when nothing is lost.

When a block cannot be decoded, a receiver that takes the symbol track can still rebuild every unit whose symbols it holds in full, if it knows where the unit starts: from an FEC Unit Start Property on the unit's first symbol (Section 6.2), or from the end of the preceding unit, which it can walk to from any unit start it knows. It applies the checks above to each such unit, with the run being the unit's own s(o) symbols.

A rebuilt object that passes these checks is the object at its Location, with the rebuilt Immutable Properties as its only Properties and the rebuilt payload as its payload. The receiver delivers it to its own consumer. Its mutable Properties, Subgroup ID, Publisher Priority and delivery mode are not recovered, and MoQ Transport sends an object according to those fields, so an entity that rebuilds an object MUST NOT forward it as an object of the source track.

A receiver MUST NOT read, copy or allocate beyond the end of the run it walks on the strength of a length field it rebuilt, because a corrupt decode can put any value there. The checks detect many corrupt decodes, but not all (Section 14).

{#deadlines-and-block-span}
## Deadlines and Block Span

An instance's configuration MAY carry a block send span, interleaveDepthMs: the largest elapsed time, in milliseconds, from sending the first source or repair symbol of a block to sending its last. When it is present and positive, the publisher MUST keep every block's actual send span within it; the value 0 has only the meaning that the instance's block profile gives it (Section 10.1) and supplies no elapsed-time deadline. It does not define block membership, imply a number of Groups, or fix K; blocks are delimited only as Section 5.4 states, and a Group may hold several blocks or a block span several Groups.

The figure below is informative. It shows Groups M0 to M2 of a source track holding blocks that do not align with them, the SS_IDs S0 to S7 of their source symbols, and the repair Group ext(SS_Start) of each block (Section 7.6):

~~~
Groups:         M0             M1             M2
                 |              |              |
Blocks:       [Block 0] [Block 1] [Block 2] [Block 3]
SS_ID:           S0  S1  S2  S3  S4  S5  S6  S7  ...
                 |       |       |       |
Repair Groups:  ext(S0) ext(S2) ext(S4) ext(S6)
~~~

A burst loss can therefore erase symbols from several adjacent blocks; each block is recovered with the repair symbols identified by its own SS_Start and SSB_length. With P repair symbols for a block, the recovery condition of the instance's scheme (Section 4.2, requirement 7) applies independently to that block.

A receiver that uses a positive span derives a block deadline from the arrival of the first source or repair symbol of the block that it receives:

~~~
deadline = first_arrival + interleaveDepthMs + reorderToleranceMs
~~~

where reorderToleranceMs, also optional, is the publisher's allowance for jitter, reordering and processing, added once when present. A block whose first symbols the receiver did not receive takes first_arrival from the arrival of the first signal from which it learns of the block: a later source or repair symbol of the block, an object of a successor block, or a FETCH response that covers the block (Section 7.7). A receiver MAY use a deadline of its own instead, for example its playout deadline, and a receiver whose instance carries no positive span has only its own.

When present, reorderToleranceMs MUST be finite and MUST be greater than or equal to zero; fractional values are permitted. An explicit value of zero means that no additional allowance is required. An omitted parameter means that the publisher did not signal an allowance; receivers MUST preserve that distinction from an explicit zero. A receiver that applies an explicit local policy MUST keep that policy separate from the configured value. A receiver whose FEC deadline API requires a signaled allowance MUST reject or disable FEC for an instance that omits reorderToleranceMs.

Spreading a block over time protects against burst loss: a burst then erases a few symbols from each of several blocks instead of many from one. It also delays recovery by up to the span. A publisher chooses the span from the burst durations it expects, the recovery latency the media can tolerate, and the bandwidth available for repair. Shorter blocks lower latency but hold fewer symbols, which weakens burst tolerance and, for codes that are not MDS, coding efficiency. A publisher MAY offer the same media under instances with different spans, for example as separate renditions, and let each receiver choose its trade-off.

Typical values, which are informative, are deployment choices for that send-span budget:

| Application | interleaveDepthMs | Meaning | Recovery Latency |
|-------------|---------------------|---------|------------------|
| Interactive (gaming, WebRTC) | 33-133 | Short source/repair span | 33-133ms |
| Low-latency live | 1000-2000 | One-to-two second span | 1-2s |
| Broadcast | 4000 | Four-second burst-spreading span | 4s |
| ATSC 3.0 default | 8000 | Eight-second burst-spreading span | 8s |

A publisher SHOULD emit a block's source and repair symbols spread across the block's span rather than in a burst at the block's end. On a hop whose MoQ Transport stack does not apply Publisher Priority to datagram-delivered objects, a publisher sends a block's repair objects only after it has sent the block's source objects, within the block's span (Section 11). A burst of repair competes with the next block's source for the same packets, and a burst is what a policer or a shallow queue drops.

The code is systematic, so a receiver presents source data on arrival, and a block's span adds latency only when the block needs decoding.

{#receiver-state}
## Receiver State

A receiver MUST bound the state it holds for open blocks by a local policy, for example a memory cap, a timeout, or a later block that has itself passed its deadline. The bound is needed even when a deadline exists, because a receiver that loses every repair object of a block never learns its SSB_length. For a block that has a deadline, the policy MUST NOT discard the block before that deadline, or while a FETCH for it is outstanding, except under a memory cap; a block so discarded is treated from then on as having reached its deadline unrecovered. The policy is not signaled and does not change any configured value.

One open block holds at most (K + P) x T bytes of symbols, so the configuration bounds the memory a block needs. A receiver MAY decline FEC for an instance whose K x T exceeds its local limits.

{#configuration-data-model}
# Configuration Data Model

This section defines the parameters that describe a track's FEC instances and the tracks that serve them, and the rules a receiver applies to them. It does not define their encoding: a binding defines how a streaming format's catalog carries them. The binding to the catalog of [@?I-D.ietf-moq-msf] and [@?I-D.ietf-moq-cmsf] is [@!MOQ-FEC-CATALOG] (Section 3 of [@!MOQ-FEC-CATALOG]); Section 10.4 shows, informatively, how it looks. The configuration is the receiver's authoritative FEC signaling, and a receiver needs no other (Section 4.2, requirement 5).

A block profile MAY also define in-band FEC signaling carried with the media, which serves a receiver that consumes a flow without the configuration; [@?MOQ-MMT] Section 8.3 defines one for MMTP packets. In-band FEC signaling MUST NOT signal FEC parameters that contradict the track's configuration. Where the two disagree the configuration governs for a MoQ receiver, and a MoQ receiver MUST NOT require in-band signaling in order to configure its decoder.

{#instance-parameters}
## Instance Parameters

For each FEC instance of a source track:

| Parameter | Type | Requirement | Meaning |
|---|---|---|---|
| instanceId | integer 0-255 | default 0 | The Instance ID (Section 5.1), unique within the track. |
| scheme | string | REQUIRED | The FEC scheme (Section 4), a registered identifier (Section 15.2); [@!MOQ-FEC-BLOCK] defines "reed-solomon" and "raptorq" (Section 3 of [@!MOQ-FEC-BLOCK]) and registers them (Section 12 of [@!MOQ-FEC-BLOCK]). |
| blockProfile | string | REQUIRED | The block profile (Section 5.2), a registered identifier (Section 15.3). There is no default, and a receiver MUST NOT infer a profile from the wire, whether from in-band signaling, from the length of the objects it receives, or from any other observation. |
| sourceSymbols | integer >= 1 | REQUIRED | K, the largest SSB_length of a block. An upper bound, not the size of each block. |
| symbolSize | integer >= 1 | REQUIRED | T, the size in bytes of every symbol. |
| repairSymbols | integer >= 1 | REQUIRED | P_0, the repair symbols per block on layer 0. |
| repairTrack | Track Name | REQUIRED | The layer-0 repair track. |
| symbolTrack | Track Name | OPTIONAL | The instance's symbol track (Section 6.2). |
| interleaveDepthMs | integer > 0 | OPTIONAL | The largest send span of a block (Section 9.3). A block profile MAY give the value 0 a meaning of its own (Section 5.2); a receiver under a profile that does not treats 0 as a violation (Section 10.3, rule 11). |
| reorderToleranceMs | finite number >= 0 | OPTIONAL | The allowance added once to a block deadline (Section 9.3). |
| label | string | OPTIONAL | A description for people, for example "key frames". A receiver MUST NOT derive behaviour from it. |

The geometry of an instance is its scheme, blockProfile, sourceSymbols, symbolSize, interleaveDepthMs and reorderToleranceMs. A publisher MUST NOT change an instance's geometry for the lifetime of the source encoding; different geometry is a different instance or a different rendition.

{#repair-and-symbol-track-parameters}
## Repair and Symbol Track Parameters

Each repair track and symbol track describes its own role:

| Parameter | Type | Applies to | Meaning |
|---|---|---|---|
| packaging | "fec-repair" or "fec-source" | both | Marks a repair track or a symbol track. Neither carries directly renderable media. A binding defines how the catalog carries this parameter ([@!MOQ-FEC-CATALOG] Section 3.3) and registers its values ([@!MOQ-FEC-CATALOG] Section 9). |
| source | Track Name | both | The source track served. REQUIRED except on a track that the source's instance parameters name. |
| instanceId | integer 0-255 | both | The instance served. On a track that an instance's parameters name, it defaults to that instance and, if present, MUST equal it; otherwise it defaults to 0. |
| repairLayer | integer >= 0 | repair | The layer index i. REQUIRED on layers above 0. |
| repairSymbols | integer >= 1 | repair | P_i. REQUIRED on layers above 0; on layer 0, if present, equal to the instance's repairSymbols. |
| priority | integer 192-255 (repair), 0-255 (symbol) | both | The Publisher Priority of every object of the track (Section 11). A layer-0 repair track that declares none has 240 (Section 10.3, rule 10). |

A repair or symbol track MUST NOT carry geometry parameters; it takes them from its instance.

{#validation}
## Validation

A receiver MUST validate the following for each instance before starting FEC for it. On any violation it MUST fail closed for that instance: it MUST report the offending parameter and MUST NOT start FEC for the instance, and it MUST NOT repair the configuration by ignoring a track, because each rule separates a layer set that decodes from one that silently mis-maps symbols. A violation in one instance does not stop FEC for another instance or another track.

1. The scheme and the block profile are registered and implemented by the receiver, and the profile admits the source track's packaging (Section 15.3); otherwise FEC for the instance is unavailable (Section 4.5), which is not a validation failure.
2. Every repair and symbol track names, explicitly or by being named, exactly one source track and one instance of it that the configuration declares.
3. The repairLayer values above 0 of an instance are contiguous from 1 to n, without gaps or duplicates. Layer 0 is the instance's repairTrack, and a track that declares repairLayer 0 MUST be that track.
4. Layer 0's repairSymbols, where a repair track restates it, equals the instance's repairSymbols. A receiver MUST NOT resolve a disagreement by preferring either value, because the two readings disagree about every higher layer's offset and about RSB_length.
5. The total repair count P is at most 2^24 - 1, K + P - 1 is at most 2^24 - 1, and K, T, K + P and the largest RS_ID are within the bounds of the instance's scheme (Section 4.2, requirement 6).
6. Repair layers above 0 appear only for a scheme whose specification states that it supports them (Section 4.2).
7. Instance IDs are unique within the source track, and an instance has at most one symbol track.
8. No repair or symbol track carries a geometry parameter.
9. Every track whose packaging is "fec-repair" or "fec-source" is reachable from a source track. A receiver MUST NOT join an unreachable one, and reports it without stopping FEC for any instance. The binding states when this rule binds for a catalog that declares no instance at all ([@!MOQ-FEC-CATALOG] Section 5).
10. The priority of each repair track of an instance, where declared, is in the range 192 to 255 inclusive and is non-decreasing with layer index within that instance; the priorities of different instances are independent. When layer 0 declares none, it is 240, and the publisher MUST give the layer-0 track's objects Publisher Priority 240.
11. The instance meets the range rules of Section 10.1: sourceSymbols is at least 1, repairSymbols is at least 1 and symbolSize is at least 1; and each repair track meets those of Section 10.2: its repairSymbols, where declared, is at least 1. A block of no source or no repair symbols recovers nothing, so a receiver that started FEC on such a configuration would join repair tracks whose symbols recover nothing. interleaveDepthMs, where present, is greater than 0 unless the instance's block profile gives 0 a meaning of its own (Section 5.2).

A binding MUST ensure that a receiver that does not understand a parameter whose meaning changes how symbols are interpreted, rather than one it can safely ignore, fails closed instead of ignoring it.

{#example}
## Example

This section is informative. The encoding below is a sketch of how the binding of [@!MOQ-FEC-CATALOG] carries the data model in the catalog of [@?I-D.ietf-moq-msf], and the scheme name stands for a scheme that a companion document ([@!MOQ-FEC-BLOCK] Section 3) defines and registers in the registry of Section 15.2.

A LOC video track has two instances. Instance 0 covers every reference frame with a 200 ms span, three repair layers and a symbol track for datagram delivery. Instance 1 covers key frames only, with a 1000 ms span. Non-reference frames belong to no instance and are unprotected.

~~~ json
{
  "version": 1,
  "tracks": [
    {
      "name": "video", "packaging": "loc", "isLive": true,
      "codec": "av01.0.08M.08", "width": 1920, "height": 1080,
      "framerate": 30, "bitrate": 4000000,
      "fec": [
        { "instanceId": 0, "scheme": "reed-solomon",
          "blockProfile": "moq-object-v1",
          "sourceSymbols": 200, "symbolSize": 1100,
          "repairSymbols": 8,
          "interleaveDepthMs": 200, "reorderToleranceMs": 40,
          "repairTrack": "video/r0", "symbolTrack": "video/s0",
          "label": "reference frames" },
        { "instanceId": 1, "scheme": "reed-solomon",
          "blockProfile": "moq-object-v1",
          "sourceSymbols": 180, "symbolSize": 1100,
          "repairSymbols": 24,
          "interleaveDepthMs": 1000,
          "repairTrack": "video/kf", "label": "key frames" }
      ]
    },
    { "name": "video/s0", "packaging": "fec-source", "isLive": true,
      "source": "video", "instanceId": 0, "priority": 128 },
    { "name": "video/r0", "packaging": "fec-repair", "isLive": true,
      "source": "video", "instanceId": 0, "repairLayer": 0,
      "repairSymbols": 8, "priority": 240 },
    { "name": "video/r1", "packaging": "fec-repair", "isLive": true,
      "source": "video", "instanceId": 0, "repairLayer": 1,
      "repairSymbols": 16, "priority": 244 },
    { "name": "video/r2", "packaging": "fec-repair", "isLive": true,
      "source": "video", "instanceId": 0, "repairLayer": 2,
      "repairSymbols": 16, "priority": 248 },
    { "name": "video/kf", "packaging": "fec-repair", "isLive": true,
      "source": "video", "instanceId": 1, "priority": 236 }
  ]
}
~~~

From this a receiver derives, for instance 0: O_0 = 0, O_1 = 8, O_2 = 24, total P = 40, so RSB_length is 40 on every repair object of the instance; layer 1 carries RS_IDs 8 to 23 and layer 2 RS_IDs 24 to 39. A full block has K + P = 240 symbols. A receiver holding layers 0 and 2 tolerates the loss of 24 symbols per block, minus the scheme's decoding overhead.

A key frame belongs to both instances, so its FEC Source Info Property carries two entries, for example `00 00 00 1F 40 01 00 00 03 E8`: SS_ID 8000 in instance 0 and SS_ID 1000 in instance 1. A predicted frame belongs to instance 0 only, so it carries the 4-byte form, its SS_ID in instance 0; a non-reference frame carries no FEC Source Info Property.

A receiver on a clean path subscribes to "video" only. One on a lossy path with a tight deadline subscribes to "video/s0" over datagrams and "video/r0", adds "video/r1" when blocks fail, and adds "video/kf" if key frames are still lost. The two instances share T = 1100, so the key-frame symbols it receives on "video/s0" can also count toward instance 1 (Section 8.4). Each relay forwards all of these without knowing what they are.

{#priority-and-congestion}
# Priority and Congestion

Priorities use the MoQ Transport scale [@!I-D.ietf-moq-transport]: an 8-bit value in which a numerically lower value is delivered first. Repair tracks SHOULD have a numerically greater Publisher Priority than the source data they protect, so that repair is shed first under congestion, and the layers of an instance have non-decreasing priority values with layer index (Section 10.3, rule 10), so that the highest layer is shed first and a receiver degrades through its layers in order. The RECOMMENDED assignment places a repair track's priority value at least 64 above its source track's (e.g. repair 240 against a source track at the common default of 128):

| Track | Publisher Priority |
|---|---|
| Catalog and control | 0-63 |
| Source track, symbol track | 64-191, for example 128 |
| Repair layer 0 | 192-255, default 240 (Section 10.3) |
| Repair layer n | 192-255, not below layer n-1 |
| Repair of a more important class | 192-255, independent of other classes |

A repair track's configured priority is the Publisher Priority of all its objects; a publisher conveys it, for example, with the track's DEFAULT_PUBLISHER_PRIORITY ([@!I-D.ietf-moq-transport] Section 10.4). Subscriber priority is applied before publisher priority, so a receiver SHOULD NOT subscribe to a repair track with a numerically lower subscriber priority than its subscription to the data that the repair protects.

MoQ Transport priorities apply to objects whatever their delivery mode, but implementations differ in how they schedule QUIC datagrams against stream data: some send all pending datagrams before any stream data, others send them after. A publisher that sends source data on streams and repair as datagrams on the same connection therefore cannot rely on priority alone to keep repair from delaying source, or source from delaying repair. Keeping the families of Section 6.4 apart avoids the interaction, and spreading each block's emission over its span (Section 9.3) reduces it. A publisher keeps repair from delaying its source on such a hop by sending a block's repair objects only after it has sent the block's source objects.

Repair adds load. On a path whose loss comes from congestion, rather than from the channel, repair that a receiver adds competes for the bottleneck that is dropping its packets. This is why a receiver SHOULD take its capacity into account before adding repair (Section 7.4), and why the layers of an instance are shed in order under congestion.

{#relay-considerations}
# Relay Considerations

Relays need not implement FEC. Repair tracks and symbol tracks are ordinary tracks, and the FEC Source Info and FEC Unit Start Properties are ordinary Properties. The mechanism nevertheless relies on relays doing a few simple things well, and a relay that does not do them prevents FEC, or part of it, for the tracks it serves:

1. **Forward every object of a Group, including Groups delivered as datagrams.** A symbol or repair Group holds many objects. A relay that forwards only one object per datagram Group delivers one symbol per block. A publisher whose receivers sit behind such a relay can send repair objects on streams, which carry every object's Object ID; a symbol track has the same option (Section 6.2).
2. **Do not alter Immutable Properties.** [@!I-D.ietf-moq-transport] forbids it. A relay that alters them changes the Protected Object Unit and silently corrupts recovery of the other objects of the block.
3. **Cache repair and symbol objects and answer FETCH for them, whatever their delivery mode.** Fetching a block's repair or symbols from a nearby cache is the per-block recovery of Section 7.7. A relay that refuses FETCH for objects that arrived as datagrams leaves receivers only the choice of subscribing to more layers.
4. **Do not assume contiguous Group IDs.** Repair and symbol Group IDs are sparse (Section 7.6). Within each such Group, Object IDs start at 0 and are contiguous, so a cache that expects Object 0 in every Group serves these Groups.
5. **Apply MoQ Transport priority to objects sent as datagrams** as to objects sent on streams.
6. **Withdraw an upstream subscription promptly when its last downstream subscriber leaves.** A receiver drops a repair layer to save its own bandwidth, and the saving reaches the links above the relay only when the relay unsubscribes upstream.

A relay MUST NOT forward an object that it rebuilt by FEC as an object of the source track (Section 9.2). An entity that recovers objects and republishes them is a publisher of a new track.

{#packaging-considerations}
# Packaging Considerations

{#loc}
## LOC

A rebuilt object has only its Immutable Properties (Section 9.2), and a receiver that takes a symbol track receives every object as a rebuilt object (Section 6.2). On a LOC track [@!I-D.ietf-moq-loc], whose public metadata travels in Object Properties, a Property is recovered only if it is inside Immutable Properties. A publisher of a LOC track protected under "moq-object-v1" MUST carry inside Immutable Properties every LOC Property that it sets on a source object and that a receiver needs to decode or present the object, including Timestamp and Timescale and, where the track uses them, Video Config, Video Frame Marking and Audio Config. [@!I-D.ietf-moq-loc] already recommends Immutable Properties for these. LOC Private Properties travel in the object payload and are recovered with it.

{#cmaf}
## CMAF

On a CMAF track [@?I-D.ietf-moq-cmsf], each object holds one or more CMAF chunks, and the sample timing that a receiver needs is in each chunk's movie fragment, inside the payload, so a rebuilt object is complete without Properties. The CMAF header that initializes decoding comes from the catalog ([@?I-D.ietf-moq-cmsf] Section 3.1), not from the objects. Each object forms one Protected Object Unit. The publisher chooses K and T so that K x T covers the largest object, which for a chunk that holds a whole key frame can be large; for such objects symbol carriage, or a protection class of its own, avoids one lost object erasing more symbols than the block's repair covers.

A publisher can also close blocks at segment boundaries and choose a segment duration equal to the block span, so that a segment holds whole blocks; an entity serving HTTP Adaptive Streaming clients can then recover segments before it serves them.

{#other-packagings}
## Other Packagings

A packaging whose objects need information outside their Immutable Properties and payload to be decoded cannot be protected under "moq-object-v1" by symbol carriage, and loses that information for objects recovered under object carriage. Such a packaging, or one whose natural unit of protection is not a MoQ object, such as MMTP packets, needs a block profile of its own (Section 15.3), as [@?MOQ-MMT] Section 7.1 defines for MMTP packets.

{#security-considerations}
# Security Considerations

{#confidentiality}
## Confidentiality

FEC provides no confidentiality. Source and repair symbols are computed over the bytes as transmitted, so when payloads are encrypted the symbols are computed over ciphertext and reveal nothing about the plaintext beyond what the ciphertext reveals (Section 8.6). The FEC Source Info Property, which must be readable without keys, reveals which instances an object belongs to; when instances follow frame classes, it reveals which objects are, for example, key frames. Object sizes and positions within Groups usually reveal as much. A deployment for which this matters uses a single instance. The FEC Unit Start Property reveals each object's size rounded up to whole symbols, which object carriage reveals exactly.

{#integrity}
## Integrity

An attacker who can modify or inject symbols can make a receiver rebuild incorrect objects. QUIC protects each hop, so on a MoQ path this requires a compromised relay. The checks of Section 9.2 discard many corrupt rebuilds but not all, and a decoder given a wrong symbol yields wrong source symbols without reporting an error; a receiver that decodes from exactly SSB_length symbols cannot detect it from the code. A receiver that holds more than SSB_length + e symbols of a block can re-encode the recovered block and compare the result with the symbols it did not use. End-to-end authentication of objects, such as MoQ Secure Objects, lets a receiver verify a rebuilt object as it verifies a received one (Section 8.6), which detects a corrupt rebuild.

Block signaling (SS_Start, SSB_length, RSB_length, and the PRIOR_GROUP_ID_GAP Property) is not authenticated end to end by this document. A compromised relay that injects a repair object with a false SSB_length, accepted before the genuine ones, can mis-delimit a block or cause the genuine repair objects to be discarded as inconsistent (Section 5.4). The effect is a block that fails to recover, not wrong media, when objects are authenticated end to end. The FEC Unit Start Property (Section 6.2) is likewise unauthenticated when carried among mutable Properties, which a relay may alter. A false Property starts the walk of Section 9.2 at a symbol that is not a unit start, or gives a unit a wrong s(o); the checks of Section 9.2 then reject the unit, or end-to-end authentication rejects what they pass, so the effect is a unit that fails to rebuild, not wrong media. A stripped Property costs only the partial rebuild, because a receiver does not infer from its absence that a symbol is not a unit start.

{#resource-consumption}
## Resource Consumption

A receiver MUST NOT read, copy or allocate beyond the run it walks on the strength of a rebuilt length (Section 9.2). The configuration bounds the memory of one open block, (K + P) x T bytes, and the receiver bounds the number of open blocks (Section 9.4). A scheme's specification states the cost of decoding a block (Section 4.2), and a receiver MAY decline FEC for an instance whose cost exceeds its limits.

{#amplification}
## Amplification

Repair is additional traffic. Layering changes the amplification exposure, because the lever is which layers a receiver can be made to receive. A receiver receives only the repair tracks it subscribes to, so a relay or publisher MUST NOT deliver a repair or symbol track that a receiver did not subscribe to, and MUST NOT raise the repair count of a track that a receiver already holds as a way of raising its protection. Publishers MUST NOT generate excessive repair symbols that could be used for bandwidth amplification attacks. Publishers SHOULD keep the repair of layer 0 to a modest fraction of the source, for example P_0/K at most 50%. Each layer i adds P_i x T bytes per block, so deployments SHOULD bound the number of repair layers of an instance that any single receiver may hold, and SHOULD apply the same authorization to repair tracks as to the source tracks they protect.

{#iana-considerations}
# IANA Considerations

{#moq-properties}
## MoQ Properties

This document requests two registrations in the "MOQ Properties" registry of [@!I-D.ietf-moq-transport] (Section 8.4 of that document):

| Type | Name | Scope | Specification |
|---|---|---|---|
| 0x11 | FEC_SOURCE_INFO | Object | This document, Section 5.6 |
| TBD1 | FEC_UNIT_START | Object | This document, Section 6.2 |

FEC_SOURCE_INFO is odd-typed because its value is bytes. 0x11, first requested by [@?I-D.ramadan-moq-fec], lies in the range 0x00 to 0x77, for which [@!I-D.ietf-moq-transport] states a registration policy of Standards Action or IESG Approval. That policy is not reachable by an individual draft, so this document asks for 0x11 as a provisional registration in the table [@!I-D.ietf-moq-transport] maintains for other active drafts in the MoQ working group, on the same terms as the existing entries for draft-ietf-moq-loc and draft-ietf-moq-secure-objects, contingent on this document being adopted. If 0x11 is not available on those terms, an odd value in the range 0x80 to 0x37FF, whose policy is Specification Required, is obtainable by this document on its own. It costs at most one additional byte per tagged object, because Property types are delta-coded ([@!I-D.ietf-moq-transport] Section 8.3) and the extra byte appears only when the encoded Delta Type exceeds 127; it changes nothing else in this specification. FEC_UNIT_START is even-typed because its value is an integer. It is requested as TBD1, an even value from the range 0x80 to 0x37FF, whose policy is Specification Required and which this document can reach on its own; it is not requested from the provisional table, so its registration does not depend on adoption, and Section 6.2 refers to it by name until IANA assigns the value. Both Properties have Object scope: each describes the object it tags and carries no track-wide meaning. The even value 0x10 is not requested for FEC_SOURCE_INFO: it is the TIMESTAMP Property of [@!I-D.ietf-moq-loc], at Object scope in the same Property Type space (Section 5.6).

This document requests no MoQ control message type.

{#moq-fec-schemes-registry}
## MoQ FEC Schemes Registry

This document requests a "MoQ FEC Schemes" registry in a new "Media over QUIC (MoQ) Forward Error Correction" registry group. A registration gives an Identifier, a string that no other entry uses and that the scheme parameter of Section 10.1 carries; a Class, "block" or "window"; whether the scheme supports repair layers; and a Reference. New registrations require Specification Required ([@!RFC8126] Section 4.6). The designated expert checks that the specification establishes each requirement of Section 4.2 for a block scheme, or of Section 4.3 and the document that completes it for a window scheme, includes test vectors, and states whether the scheme supports repair layers. This document registers no scheme; the block-codes companion document [@!MOQ-FEC-BLOCK] makes the first registrations, "reed-solomon" and "raptorq" (Section 12 of [@!MOQ-FEC-BLOCK]). The Identifier "none" is reserved and MUST NOT be registered: it names no scheme, and companion documents use it where an encoding has to state that a track has no FEC instance ([@?MOQ-MULTICAST]).

{#moq-fec-block-profiles-registry}
## MoQ FEC Block Profiles Registry

This document requests a "MoQ FEC Block Profiles" registry in the same registry group. A registration gives a Block Profile string that no other entry uses, the source packagings it admits, and a Reference. New registrations require Specification Required. The designated expert checks that the specification fixes what Section 5.2 requires of a block profile. The initial content is:

| Block Profile | Admitted Packaging | Reference |
|---|---|---|
| "moq-object-v1" | any packaging whose objects carry their media as whole MoQ objects, including loc and cmaf | This document, Section 5.2 |

The block profile for MMTP packets, "iso-ssbg1-v1", is registered by [@?MOQ-MMT] (Section 15 of [@?MOQ-MMT]).

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

{#companion-documents}
# Companion Documents

This section is informative. It lists the documents that complete this one, and what each takes from [@?I-D.ramadan-moq-fec]. The section numbers in the last column are those of draft-ramadan-moq-fec-01.

| Document | Content | From draft-ramadan-moq-fec-01 |
|---|---|---|
| This document | The scheme-independent mechanism and the configuration data model. | 1, 3, 4.3 (unimplemented schemes), 5.3 (the generic Property), 6, 6.1, 6.2, 6.3 (generic), 6.3.1, 6.3.2 (formulas), 6.3.3 (the generic index-fixed statement), 6.3.4 (the scheme-neutral rules and rule 3), 6.3.5, 6.3.7, 6.3.8, 6.3.9 (append-only and the fail-closed check in its -01 scope), 7.2 (generic), 7.4, 7.5, 7.6 to 7.6.7 (the worked walk as (#rebuilding-a-block-worked-example)), 8 to 8.4, 9 (span, deadline, diagram and typical values; the conformance cases as (#block-span-conformance-cases)), 10, 13 (direct CMAF protection), 14.1 to 14.3, 14.6, 15.1, 15.2 (registry creation), 15.4 (registry and "moq-object-v1"), Appendix A (message flows, rewritten for "moq-object-v1" and the symbol track, as (#example-message-flows)) |
| [@!MOQ-FEC-BLOCK] | Reed-Solomon over GF(2^8) with a Cauchy generator matrix and RaptorQ [@?RFC6330]: construction, parameter derivation, bounds, decoding overhead, test vectors and support for repair layers. States each requirement of Section 4.2 for both codes, registers both identifiers in the registry of Section 15.2 (Class "block", Layers yes) and designates Reed-Solomon as mandatory to implement (Section 4.4). | 2 (OTI, RaptorQ K' text), 4 preamble, 4.1, 4.2, 4.3 (the mandatory-to-implement designation, why Reed-Solomon and RaptorQ), 4.4, 4.5 (including the discard rule restated against Section 7.3.2 of this document), 6.3.2 (overhead numbers), 6.3.3 (scheme part), 6.3.4 rules 6 and 12 and the scheme parts of 13, 6.3.9 (Reed-Solomon bound), 7.1 and 7.2 (RaptorQ and Reed-Solomon clauses), 7.4 (scheme clauses), 14.7, 15.2 (the "raptorq" and "reed-solomon" registrations and the expert guidance on layers), Appendix C, Appendix A (OTI numbers) |
| [@!MOQ-FEC-CATALOG] | The encoding of Section 10 for the catalog of [@?I-D.ietf-moq-msf] and [@?I-D.ietf-moq-cmsf]: the JSON shape, the "fec-repair" and "fec-source" packaging values and their registration, the rules for unknown keys, a worked catalog and CMSF specifics. Cites [@!MOQ-FEC-BLOCK] for scheme bounds and identifiers. | 5, 5.1 (JSON shape, packaging values, unknown-key rules, the enhancementRepair tombstone), 5.1.1, 5.1.2 (a fresh worked catalog), 5.2 (catalog authority), 6.1 (the "/repair" naming convention, informative), 6.3 (the republish-subset rule), 6.3.4 (the defect table and the rule-9 exception), 13 (CMSF-specific encoding), 15.3, Appendix B |
| [@?MOQ-FEC-MULTICAST] | Hybrid unicast and multicast delivery of protected tracks, independent of how multicast is carried: repair-only multicast endpoints, the receiver repair policy for multicast legs, provisional blocks, and the admitted-packet anchoring of the check of Section 7.3.2. States that multicast endpoints carry MMTP tracks only in this revision and that symbol tracks are not listed on them. | 5.1 (no block classification on multicast), 5.2 (sessionless receivers), 6.3.6, 6.3.9 (admitted-packet anchoring), 7.4 (provisional blocks), 7.5, 8.5 and 9 (bc-provenance clauses), 11, 11.1 to 11.4.6, 14.3 (join authorization), 14.4 |
| [@?MOQ-MMT] | The "iso-ssbg1-v1" block profile: source symbols from MMTP packets, the Source FEC Payload ID trailer, the MMTP form of the repair packet, the keyframe overlay and its header extension, the packet-count meaning of interleaveDepthMs zero, in-band AL-FEC signaling, and ATSC 3.0 and ARIB STD-B60 interworking including the A3SA signed region. Registers "iso-ssbg1-v1" in the registry of Section 15.3. | 2 (keyframe overlay, iso-ssbg1 clauses, interleaveDepthMs zero), 5.1, 5.1.1, 5.1.2, 5.2, 5.3 (MMTP clauses), 6.3, 6.3.1, 6.3.4 rule 10, 6.3.9 (AL-FEC-message clauses), 6.4 to 6.4.3, 7.1 (MMTP form), 7.3, 8.3, 8.4, 8.5, 8.5.1, 12, 13 (the mmtp rendition), 14.5, 15.1 (the 0x8B01 paragraph), 15.4 (the "iso-ssbg1-v1" registration), Appendix A (the AL-FEC sentence), Appendix B (MPU arithmetic) |
| [@?MOQ-MULTICAST] | Multicast delivery and endpoint discovery. Nothing moves in; its citations of draft-ramadan-moq-fec-01 are re-pointed, and its params_hash is defined over the per-instance fields of [@!MOQ-FEC-CATALOG]. | none |
| Not written | Sliding-window schemes (Section 4.3) and content-aware protection (Section 8.5 gives guidance). | none |

Retired, carried by no document: the interworking text for the second ATSC 3.0 transport protocol, since this set covers MMTP only; the closed-list sentence of -01 Section 4.3; -01 Appendix D; the rule that "moq-object-v1" is for MoQ paths only, for which [@?MOQ-FEC-MULTICAST] states the multicast scoping instead; and "none" as a scheme identifier, since a track without instances declares no FEC; the string itself is reserved by Section 15.2 and is only the no-FEC encoding of [@?MOQ-MULTICAST].

LOC needs no document of its own: "moq-object-v1" covers LOC tracks, and Section 13.1 states what LOC publishers must do.

{#changes-from-draft-ramadan-moq-fec-01}
# Changes from draft-ramadan-moq-fec-01

This section is informative.

- The document no longer specifies an FEC code. Section 4 states the properties a scheme must have; Reed-Solomon and RaptorQ move to [@!MOQ-FEC-BLOCK], which designates Reed-Solomon as mandatory to implement and RaptorQ as optional (Section 4.4).
- The "moq-object-v1" construction is kept unchanged and is no longer limited to loc and cmaf.
- Symbol carriage is new (Section 6.2): a symbol track whose objects are single source symbols, grouped by block, with Group ID ext(SS_Start) and Object ID equal to the ESI. It makes one lost datagram erase one symbol, and makes a block's source symbols fetchable by Group.
- FEC instances are generalized (Section 5.1). The FEC Source Info Property can name several instances (Section 5.6), which gives protection classes and overlapping instances (Section 8) without reading payloads. The keyframe overlay, which relied on MMTP fields, becomes a special case of overlapping instances; its MMTP form moves to the MMTP block profile. An object whose only instance is instance 0 carries the 4-byte form, so that a set of instances has one encoding; a single Instance Entry naming instance 0 is malformed. A receiver of draft-ramadan-moq-fec-01 accepts only the 4-byte form and closes the session with KEY_VALUE_FORMATTING_ERROR on the list form; it interoperates only with tracks every tagged object of which belongs to instance 0 alone.
- The FEC Source Info Property is now required to be inside Immutable Properties, where draft-ramadan-moq-fec-01 only recommended it, and must not be carried inside an encrypted container (Section 5.6). A malformed value closes the session only when a received object carries it; in a rebuilt object it fails the checks of Section 9.2 (Section 5.6 and Section 9.2).
- Rebuilt objects can be placed in every instance they belong to (Section 8.4).
- The configuration is defined as a data model (Section 10); its catalog encoding moves to [@!MOQ-FEC-CATALOG]. A track may declare several instances. The "none" algorithm of -01 Section 5.1 is dropped: a track without FEC declares no instance, and the binding states how a catalog expresses an empty instance list. The packaging values "fec-repair" and "fec-source" are registered by the binding, not here (-01 Section 15.3).
- interleaveDepthMs is positive or absent unless a block profile gives zero a meaning of its own (Section 10.1); the ISO packet-count meaning of zero belongs to the MMTP block profile ([@?MOQ-MMT] Section 7.1). Under "moq-object-v1" a zero value is a validation failure (Section 10.3, rule 11), where -01 Sections 5.1, 8.4 and 9 treated it as equivalent to an absent value.
- Relay considerations are new (Section 12). Relays need not implement FEC, but the document does place a few requirements on them (Sections 3.2, 7.2, 12 and 14.4).
- Section 7.2 adds a rule that -01 Section 6.2 did not have: a receiver should start a new repair subscription no earlier than the Group of the block in progress.
- MMTP, ATSC 3.0, ARIB and multicast material moves to companion documents (Appendix A).

The following rules of draft-ramadan-moq-fec-01 were restored or changed by the editorial pass that produced this revision:

- Section 2 defines RSB_length, which -01 Section 2 did not define, by restating the field definition of -01 Section 7.1; Section 1.2 and Section 8.5 expand CMAF and LOC on first use, as the abstract of -01 did.
- Section 4.3 lists, as item 6, what a sliding-window scheme must define for symbol carriage, which Section 6.2 states by block; symbol carriage no longer applies to such a scheme "unchanged".
- Section 5.2: the mutable Properties, Subgroup ID, Publisher Priority and delivery mode are outside the unit, but a relay may change only the mutable Properties; -01 Section 7.6.1 never granted a relay more.
- Section 5.6 reads 0x11 as provisional until the registration request is resolved and names the 0x80 to 0x37FF fallback and its 2-byte Delta Type consequence (-01 Section 5.3).
- Section 6.2 records two open questions as Editor's Notes: whether the FEC Unit Start Property should exist, and whether PRIOR_GROUP_ID_GAP should be required on symbol-track objects.
- Section 7.2 restores the recommendation of -01 Section 6.2 that a receiver subscribe to the source track, or to the instance's symbol track, before a repair track of the instance.
- Section 7.3.1: the loss tolerance is derived and is not signaled as a separate parameter (-01 Section 6.3.2).
- Section 7.3.2 restores the scope of -01 Section 6.3.9: a publisher applies a raised total from a block onward in serial order; the fail-closed check applies to a repair object of a held layer's own track, the layer being above 0, and to any held layer on a block at or after one that carried its O_i + P_i; such an object is not a symbol to discard; a larger RSB_length is not an error; and the backstop does not catch a withdrawal of the highest layer for a receiver that holds it alone. This section is the single normative statement of the check; the companions cite it. Section 7.5 defers to it for the RS_ID discard rule.
- Section 7.5 restores the publisher-side bound on SSB_length of -01 Section 7.1: a publisher must not send 0 or a value above K; the receiver discard of such a repair object is stated in Section 5.4.
- Section 7.7: a receiver that may not extend x has no range to request (-01 Section 7.5).
- Section 9.2 rebuilds from each run of ESIs that no source object fed to the decoder covers, as -01 Section 7.6.4 did, so held-but-unfed objects keep their place in the run.
- Section 9.3 carries the block and repair-Group figure and the typical-values table of -01 Section 9 as informative text; the deadline of a block whose first symbols were lost starts at the first signal from which the receiver learns of it, including an object of a successor block or a FETCH response (-01 Section 9); the reorderToleranceMs clauses of -01 Section 5.1 (finite, explicit zero distinct from absent, local policy kept separate, a deadline API that needs an allowance disables FEC without one) are carried; and Section 11 restores the remedy of -01 Section 10 for a hop whose stack does not apply Publisher Priority to datagram-delivered objects: a publisher sends a block's repair objects only after it has sent the block's source objects; Section 9.3 points at that rule and adds that the order holds within the block's span (new sentence); and, as -01 Section 9 did, Section 9.3 binds the publisher's send span and supplies an elapsed-time deadline only for a positive value, a zero value having only the meaning its block profile gives it (Section 10.1).
- Section 9.4: a receiver must not discard a block before its deadline or while a FETCH for it is outstanding, except under a memory cap, and a block so discarded has reached its deadline unrecovered (-01 Section 9).
- Section 10 keeps the three-sentence precedence rule of -01 Section 5.2: in-band signaling may exist, must not contradict the configuration, and is never required by a MoQ receiver.
- Section 10.1: a receiver does not infer a block profile from the wire, and rule 1 of Section 10.3 requires the profile to admit the source track's packaging (-01 Section 5.1); a block profile may give interleaveDepthMs zero a meaning of its own; reorderToleranceMs is finite.
- Section 10.2 and rule 10 of Section 10.3 restore -01 Section 6.3.4 rule 3: repair priorities are in 192 to 255, non-decreasing with layer index within an instance, and layer 0 defaults to 240; Section 11 points at the rule. Rule 9 points at the binding for the case of a catalog that declares no instance.
- Rule 11 of Section 10.3 restores the scheme-neutral part of -01 Section 6.3.4 rule 13 as a fail-closed validation rule: sourceSymbols, symbolSize, the instance's repairSymbols and a repair track's declared repairSymbols are at least 1; the same rule holds the interleaveDepthMs zero check that Section 10.1 states. The scheme parts of rule 13 are in [@!MOQ-FEC-BLOCK] Section 7.
- Section 11 restores the -01 Section 10 recommendation that a repair track's priority value is at least 64 above its source track's (repair 240 against a source track at 128), which the table alone does not state.
- Section 10.4: a predicted frame carries the 4-byte form.
- Section 12, item 1, restores the publisher remedy of -01 Section 7.5: a publisher whose receivers sit behind a relay that forwards only one object per datagram Group can send repair objects on streams, which carry every object's Object ID; the clause giving a symbol track the same option by way of Section 6.2 is new. The "at the time of writing" account of relay behaviour in -01 Section 7.5 is not carried (no implementations are named).
- Section 14.2 names the FEC Unit Start Property as unauthenticated block signaling and states its effect.
- Section 14.4 restores "publishers must not generate excessive repair symbols" and "deployments should bound the number of layers any single receiver may hold" (-01 Section 14.3).
- Section 15.1 restores the range and policy facts of -01 Section 15.1 for 0x11, the Object-scope statement, and requests FEC_UNIT_START as TBD1 from the Specification Required range 0x80 to 0x37FF.
- Section 15.2 registers no scheme; -01's "raptorq" and "reed-solomon" rows are requested by [@!MOQ-FEC-BLOCK]. The "Catalog Packaging Values" subsection is removed; [@!MOQ-FEC-CATALOG] requests those values.
- Section 1.2, Section 5.2, Section 7.5, Section 10, Section 10.1, Section 10.2, Section 13.3 and Section 15.3 now name the companion documents where they take over.
- Section 13.1 and Section 13.2 carry from -01 Section 7.6.5 that LOC Private Properties travel in the object payload and are recovered with it, and that the CMAF header that initializes decoding comes from the catalog, not from the objects.
- (#block-span-conformance-cases), (#rebuilding-a-block-worked-example) and (#example-message-flows) carry the conformance cases of -01 Section 9, the worked example of -01 Section 7.6.7 and the message flows of -01 Appendix A.1, the last rewritten for "moq-object-v1" and the symbol track; its K and T are those of instance 0 of Section 10.4 (200 and 1100), not -01's 32 and 1312, which were sized for one MMTP packet per symbol and bound a unit to 41,984 bytes (Section 5.4), smaller than the key frame of (#rebuilding-a-block-worked-example). Section 3.2 restores the pointer of -01 Section 3 to the message flows.
- Section 15.2 reserves the Identifier "none", which no scheme may take, so that the no-FEC encoding of [@?MOQ-MULTICAST] stays distinct from every registered scheme.
- Section 5.1 forbids reusing a symbol's coordinates across instances and feeding a symbol to another instance's decoder, except by the cross-instance placement of Section 8.4 at the SS_ID the unit's FEC Source Info Property gives it there.
- Section 1.3 records as open that the MoQ Transport section cited in Section 15.1 for the "MOQ Properties" registry (-01 Section 15.1) is to be settled against the current MoQ Transport draft.

The questions this revision leaves open are marked [open] in the text: the registry pointer of Section 15.1 (Section 1.3); whether Section 4.3 holds for sliding-window schemes (Section 4.3); whether this document should itself require the mandatory-to-implement scheme (Section 4.4); and, in Section 6.2, whether the FEC Unit Start Property is worth its codepoint and whether PRIOR_GROUP_ID_GAP should be required on symbol-track objects.

{#block-span-conformance-cases}
# Block Span Conformance Cases

This appendix is informative. These cases exercise the boundary rules of Sections 5.4 and 9.3 without deriving a block from a Group count. They use "iso-ssbg1-v1" ([@?MOQ-MMT] Section 7.1), under which one source packet is one source symbol; (#rebuilding-a-block-worked-example) works an example under "moq-object-v1".

The first case uses this numeric vector:

~~~ json
{
  "fps": 30,
  "gopFrames": 30,
  "groupDurationMs": 1000,
  "accessUnitsPerBlock": 4,
  "accessUnitStartMs": [0, 33.333, 66.667, 100.0],
  "sourcePacketsPerAccessUnit": [2, 3, 1, 4],
  "K": 16,
  "SSB_length": 10,
  "interleaveDepthMs": 133,
  "firstSourceOrRepairMs": 0,
  "lastSourceOrRepairMs": 133,
  "sourceRepairSpanMs": 133
}
~~~

1. A 30 fps track with a 30-frame (1000 ms) GOP may close a block after four access units (a four-frame access-unit interval). With the send schedule in the vector, interleaveDepthMs = 133. An access unit can produce multiple source packets, so the block is closed after those access units, not after an assumed packet count. For this concrete vector, the four access units begin at 0, 33.333, 66.667, and 100 ms, produce 2, 3, 1, and 4 source packets respectively, and therefore have SSB_length = 10 <= K = 16 as shown above. The publisher sends the last source or repair packet for that block by 133 ms; a later send would require a larger signaled window. The one MoQ Group containing the GOP can therefore contain several such blocks. Each repair packet still carries the actual (SS_Start, SSB_length); the 133 ms value does not mean four MoQ Groups per block and is not a rounded four-frame duration.
2. With K = 4, one Group containing three source packets followed by a Group containing three source packets may be encoded as blocks of lengths 3 and 3, or as a block of length 4 spanning the Group boundary followed by a block of length 2. Both are valid; the repair fields identify which partition was used.

   ~~~ json
   {
     "K": 4,
     "groupPacketCounts": [3, 3],
     "blockPartitions": [[3, 3], [4, 2]],
     "SS_Starts": [[0, 3], [0, 4]]
   }
   ~~~

3. If the stream ends with two source packets in the current block, the publisher sends a short block with SSB_length = 2, which under RaptorQ has the transfer length F = 2 x T ([@!MOQ-FEC-BLOCK] Section 6.1), and no padding or skipped SS_ID. There is no following block.

{#rebuilding-a-block-worked-example}
# Rebuilding a Block: Worked Example

This appendix is informative. It works the rebuild of Section 9.2 under object carriage, with the configuration in the catalog form of Section 10.4.

The configuration below declares a LOC video track under "moq-object-v1". Each one-second Group holds one Group of Pictures (GOP): an Instantaneous Decoder Refresh (IDR) frame as Object 0 and 29 P-frames as Objects 1 to 29 ([@!I-D.ietf-moq-loc] Section 4.2). The publisher sends the parameter sets in the IDR payload ([@!I-D.ietf-moq-loc] Section 2.1.1), so the track needs no Video Config.

~~~ json
{
  "version": 1,
  "tracks": [
    {
      "name": "video", "packaging": "loc", "isLive": true,
      "role": "video", "codec": "avc3.640028",
      "width": 1920, "height": 1080,
      "framerate": 30, "bitrate": 2500000,
      "fec": [
        { "instanceId": 0, "scheme": "raptorq",
          "blockProfile": "moq-object-v1",
          "sourceSymbols": 256, "symbolSize": 1200,
          "repairSymbols": 32,
          "interleaveDepthMs": 1200, "reorderToleranceMs": 40,
          "repairTrack": "video/repair" }
      ]
    },
    { "name": "video/repair", "packaging": "fec-repair",
      "isLive": true, "source": "video", "instanceId": 0,
      "repairSymbols": 32, "priority": 240 }
  ]
}
~~~

Each object carries 15 bytes of Immutable Properties: Timescale in 4 bytes (Delta Type 0x08 and the value 90000 in 3 bytes), Timestamp in 5 bytes (a 4-byte value) and FEC Source Info in 6 bytes, the 4-byte form of Section 5.6. Each unit is therefore 37 bytes longer than its payload. With T = 1200:

- An IDR payload of 60,000 bytes gives len(o) = 60,037 and s(o) = 51. The unit's last symbol ends with 1,163 bytes of padding, which are not sent.
- A P-frame payload of 7,000 bytes gives len(o) = 7,037 and s(o) = 6, with 163 bytes of padding.
- A Group therefore spans 51 + 29 x 6 = 225 source symbols, within K = 256.

Suppose the first source object of the FEC instance, {0, 0}, has SS_ID 0, every Group so far has this shape, and the publisher closes a block at each Group boundary. Group g then starts at SS_ID 225 x g, and its block has SS_Start 225 x g and SSB_length 225. For Group 5:

| Object | len(o) | s(o) | SS_IDs | ESIs |
|---|---|---|---|---|
| {5, 0} (IDR) | 60,037 | 51 | 1125 to 1175 | 0 to 50 |
| {5, 1} | 7,037 | 6 | 1176 to 1181 | 51 to 56 |
| {5, 2} | 7,037 | 6 | 1182 to 1187 | 57 to 62 |
| {5, 3} | 7,037 | 6 | 1188 to 1193 | 63 to 68 |
| {5, 4} | 7,037 | 6 | 1194 to 1199 | 69 to 74 |
| {5, 5} | 7,037 | 6 | 1200 to 1205 | 75 to 80 |
| {5, 29} | 7,037 | 6 | 1344 to 1349 | 219 to 224 |

Objects {5, 6} to {5, 28}, which the table omits, follow the same pattern.

Object {6, 0} starts at SS_ID 1350. The block's repair objects form Group 1125 of "video/repair" (Section 7.6): Objects 0 to 31, with RS_IDs 0 to 31 and ESIs 225 to 256, each 13 + 1200 = 1,213 bytes long. The block's source objects are sent over 967 ms, and its repair objects follow the last of them, so the instance's interleaveDepthMs of 1200 covers the block's send span (Section 9.3).

Suppose a delivery timeout drops {5, 3} and {5, 4}. The receiver holds {5, 2}, which ends at SS_ID 1187, and {5, 5}, which starts at SS_ID 1200, so ESIs 63 to 74 form a run of 12 missing source symbols. With the other 213 source symbols and the 32 repair symbols it holds 245 symbols, 20 more than SSB_length, and decodes. It walks the run from ESI 63. The unit there has Group ID 5, Object ID 3, Immutable Properties Length 15 and Payload Length 7,000, so len = 7,037 and s = 6, and bytes 7,037 to 7,199 from the start of the unit must be zero. The next unit, at ESI 69, is {5, 4} with s = 6, so the walk ends at ESI 75, where {5, 5} starts, as required. The FEC Source Info values in the two units are 1188 and 1194, their first SS_IDs. The receiver delivers both objects with their Timescale, Timestamp and FEC Source Info Properties.

This block recovers the loss of up to five P-frame objects, 30 symbols, with 2 symbols of decoding overhead, the overhead at which RaptorQ's residual failure is about 1e-6 (Section 4.2, requirement 7; [@!MOQ-FEC-BLOCK] Section 8). The IDR object spans 51 symbols, more than the block's 32 repair symbols, so its loss is not recovered in band: the receiver needs a further repair layer or a FETCH of the object, or resumes at the next Group.

This example uses "raptorq". Its configuration is not valid under "reed-solomon", since 256 + 32 exceeds 255 ([@!MOQ-FEC-BLOCK] Section 7).

{#example-message-flows}
# Example Message Flows

This appendix is informative. It shows the exchange of Section 3.2 for a track protected under "moq-object-v1", first under object carriage and then with the instance's symbol track.

{#catalog-driven-fec}
## Catalog-Driven FEC

The subscriber learns the complete FEC configuration from the track's catalog entry before subscribing, in the catalog form of Section 10.4:

~~~ json
"fec": [
  { "instanceId": 0, "scheme": "reed-solomon",
    "blockProfile": "moq-object-v1",
    "sourceSymbols": 200, "symbolSize": 1100,
    "repairSymbols": 8,
    "interleaveDepthMs": 1000, "reorderToleranceMs": 40,
    "repairTrack": "video/repair",
    "symbolTrack": "video/symbols" }
]
~~~

~~~
Publisher                                    Subscriber
    |                                          |
    |  (catalog obtained by SUBSCRIBE with     |
    |   request_id=0; fec field read)          |
    |                                          |
    |  SUBSCRIBE(request_id=2, track=video,    |
    |    LOCATION_FILTER=0x05 (Next Object),   |
    |    FILL_PARAMETERS(LOCATION_FILTER=      |
    |      0x01, StartGroup=1))                |
    |<-----------------------------------------|
    |                                          |
    |  SUBSCRIBE_OK(LARGEST_OBJECT={G, n})     |
    |----------------------------------------->|
    |                                          |
    |  SUBSCRIBE(request_id=4,                 |
    |    track=video/repair,                   |
    |    LOCATION_FILTER=0x05 (Next Object))   |
    |<-----------------------------------------|
    |                                          |
    |  SUBSCRIBE_OK                            |
    |----------------------------------------->|
    |                                          |
    |  [Fill fetch stream: source objects      |
    |   {G, 0} to {G, n}]                      |
    |----------------------------------------->|
    |                                          |
    |  [Source objects from {G, n+1} on]       |
    |----------------------------------------->|
    |                                          |
    |  [Repair objects, group=ext(SS_Start),   |
    |   obj=0..7]                              |
    |----------------------------------------->|
    |                                          |
~~~

Each SUBSCRIBE carries a Request ID ([@!I-D.ietf-moq-transport] Section 6.4.2.1). A client uses even Request IDs, starting at 0 and rising by 2 per request, so the catalog SUBSCRIBE ([@?I-D.ietf-moq-msf] Section 5) takes 0 and the source and repair SUBSCRIBEs take 2 and 4. Each response travels on the bidirectional stream of its request, so SUBSCRIBE_OK carries no Request ID. The source subscription joins at the start of the current Group G ([@!I-D.ietf-moq-transport] Section 3.5). Its Next Object filter starts subscription delivery at {G, n+1}, where {G, n} is the Largest Object that SUBSCRIBE_OK reports, and its fill range, from {G, 0} to that Largest Object, arrives on a fill fetch stream. The repair subscription starts at the Next Object; repair objects published before it can be requested by FETCH (Section 7.7).

In this flow the track is a LOC track with a one-second Group duration. That Group duration describes the MoQ grouping; it does not derive an FEC block. For example, if the first block starts at SS_ID 0 and is full, its repair Group is its extended SS_Start, 0 (Section 7.6), the next block starts at SS_ID 200, and its repair Group is 200. A publisher may choose shorter blocks inside a Group or a block that crosses the Group boundary; each repair object carries the actual SSB_length. The subscriber's decoder configuration is derived from the configuration and each block's SSB_length (Section 4.2, requirement 5); no in-session message is required. The source objects carry the FEC Source Info Property of Section 5.6, and the repair objects are those of Section 7.5.

{#symbol-carriage-flow}
## Symbol Carriage

A receiver that takes the FEC family of Section 6.4 subscribes to the instance's symbol track, "video/symbols", in place of or alongside the source track, with the same Next Object filter; its Request ID is the next even value.

~~~
Publisher                                    Subscriber
    |                                          |
    |  SUBSCRIBE(request_id=6,                 |
    |    track=video/symbols,                  |
    |    LOCATION_FILTER=0x05 (Next Object))   |
    |<-----------------------------------------|
    |                                          |
    |  SUBSCRIBE_OK                            |
    |----------------------------------------->|
    |                                          |
    |  [Symbol objects as datagrams,           |
    |   group=ext(SS_Start),                   |
    |   obj=0..SSB_length-1]                   |
    |----------------------------------------->|
    |                                          |
    |  [Repair objects, group=ext(SS_Start),   |
    |   obj=0..7]                              |
    |----------------------------------------->|
    |                                          |
    |  FETCH(request_id=8, track=video/symbols,|
    |    LOCATION_FILTER=0x04 (Absolute Range),|
    |    StartGroup=ext(SS_Start),             |
    |    the ESIs it lacks)                    |
    |<-----------------------------------------|
    |                                          |
    |  [Fetched symbol objects]                |
    |----------------------------------------->|
    |                                          |
~~~

The symbol track's objects arrive as Groups whose Group ID is ext(SS_Start), the Group ID of the block's repair objects, with Object IDs 0 to SSB_length - 1 (Section 6.2); each datagram carries one symbol, so one lost datagram erases one symbol. A receiver that has lost symbols of a block and holds a repair or symbol-track object of it requests the symbols it lacks by a FETCH of the one Group ext(SS_Start) on the symbol track, or more repair from a layer it has not subscribed (Section 7.7). A receiver that takes only the symbol track and the repair layers receives the media as rebuilt objects (Section 9.2).

{#acknowledgements numbered="false"}
# Acknowledgements

Much of the text of this document is taken from [@?I-D.ramadan-moq-fec], with changes to make it independent of any FEC code and of any packaging.

The authors thank Emmanuel Lochin for discussions of sliding-window codes, the additivity of random-coefficient repair across tracks, and receiver-side control from the decoder's deficit, which shaped Section 4.3. [Editor's note: tentative; to be confirmed with him before submission.]

Editor's Note: further acknowledgements are to be added.

