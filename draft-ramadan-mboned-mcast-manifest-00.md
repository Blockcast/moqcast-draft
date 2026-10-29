%%%
title = "Signed Digest Manifests for Multicast Datagram Authentication"
abbrev = "Multicast Manifests"
ipr = "trust200902"
area = "ops"
workgroup = "mboned"
submissiontype = "IETF"
date = "2026-11-01T00:00:00Z"
keyword = ["multicast", "AMBI", "authentication", "manifest", "Ed25519", "SSM"]

[seriesInfo]
name = "Internet-Draft"
value = "draft-ramadan-mboned-mcast-manifest-00"
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

This document defines a format for authenticating UDP datagrams
delivered over IP multicast without changing them.  The sender
computes a digest over every datagram of a flow, places the digests
of up to 37 datagrams in a fixed-layout record, signs the record with
Ed25519 under a prefix that names the flow, and sends it on a second
port of the same source and group immediately before the datagrams it
covers, followed by a byte-identical twin.  A receiver verifies one
signature per record, hashes each datagram once, and delivers a
datagram only after its digest matches an entry of a verified record;
it needs no return channel.  A well-known document supplies a flow's
keys and parameters.  A Media over QUIC profile and a browser profile
use the format.

{mainmatter}

# Introduction

Multicast UDP delivery lacks the integrity protection that QUIC
provides on unicast paths.  A receiver of an IP multicast flow,
whether joined natively, reached through an Automatic Multicast
Tunneling (AMT) relay [@!RFC7450] or running in a browser, has no
per-receiver connection over which the sender could authenticate what
it sends: multicast transports are unidirectional
([@?I-D.ietf-mboned-multicast-security] Section 2.1), and a host that
can inject into the path injects into every receiver at once.  A
format that authenticates each datagram before any use of it, costs
the receiver one hash per datagram and a fraction of one signature
verification, and asks nothing of the receiver but that it receive,
serves every such receiver.

Asymmetric Manifest Based Integrity (AMBI)
[@?I-D.ietf-mboned-ambi] authenticates multicast packets with
manifests of packet digests: a receiver holds packets and digests
until the two meet and consumes a digest on admission (its
Section 3.2).  AMBI requires an authenticating transport for its
manifests (its Section 4.1), and the three it defines (its
Sections 4.2 to 4.4) are unicast; its Section 2.1.1 anticipates
a protocol that signs manifests and carries them over a multicast
transport, leaving that to another specification.  This
document is that specification.  The AMBI manifest of its Section 3.3
carries no signature, and its type-length-value (TLV) space (its
Section 3.3.1.6) is extensible; this document defines a separate
signed record rather than an AMBI TLV, so that the record is a fixed
layout, verified before any parsing and carried on the flow's own
(S, G), and restates the digest pseudoheader of AMBI Section 3.4.2 by
value, since that document has expired.  Discovery Of Restconf
Metadata for Source-specific multicast (DORMS)
[@?I-D.ietf-mboned-dorms] discovers the metadata of an (S, G) through
DNS and RESTCONF and, in its Sections 2.3.5 and 4.5, gates it per web
origin with Cross-Origin Resource Sharing (CORS); the well-known
document of (#the-well-known-document) carries the same grant from
the source address itself, and a DORMS record remains one way to
deliver the same parameters.  The threat model is that
of [@?I-D.ietf-mboned-multicast-security]: its integrity baseline
(Section 2.3), injection rule (Section 2.7.2) and cross-origin
authorization (Section 2.7.3) are met by construction, and what its
Section 2.8.1 asks of a multicast protocol in place of a referrer
check, that a client can unilaterally reject multicast data delivered
for objects referenced by pages the server has not authorized, the
well-known document's grant to a named origin delivers
((#fetching-the-document), (#security-considerations)).

This document defines the digest ((#digest)), the manifest record and
its signature ((#manifest-record)), what a sender emits and when
((#sender-behavior)), what a receiver keeps and checks
((#receiver-behavior)), the parameters a flow's metadata declares and
a well-known document that carries them
((#flow-metadata-and-the-well-known-document)), an optional
per-datagram trailer scheme for low-rate flows
((#the-ed25519-trailer-1-scheme)), and the registry of scheme
identifiers and the registration of the well-known URI
((#iana-considerations)).  It leaves to a profile how a receiver
obtains the metadata (the
well-known document, a DORMS record, an application catalog or
provisioning), how the 32-octet `ctx` field of the record is derived
from the application context, if at all
((#signature-context-binding)), and whether records reach a receiver
by any path other than the flow's manifest port
((#additional-record-paths)).

A receiver that implements this document enforces it: there is no
verify-and-report mode, and no datagram of a protected flow reaches
an application except through (#receiver-behavior).

[@?MOQ-MULTICAST] Section 7.2 profiles this format for Media over QUIC
(MoQ) as "bc-provenance" version 2: it derives `ctx` from the MoQ
catalog, mirrors records on a MoQ track as a second path and carries
flows in broadcasts, and it restates the format by value, so that the
two documents agree on every wire-format fact and every rule of this
document.  A browser profile, proposed for the web platform under the
title "Multicast Receive for Secure Contexts", names the format
`manifest-ed25519-2`, scheme 1 of
(#multicast-datagram-integrity-schemes-registry), fetches the
well-known document on a page's behalf and delivers to the page
nothing that (#receiver-behavior) has not admitted.

# Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
and "OPTIONAL" in this document are to be interpreted as described
in BCP 14 [@!RFC2119] [@!RFC8174] when, and only when, they appear
in all capitals, as shown here.

All multi-octet integers are unsigned and big-endian; `u8`, `u16`,
`u32` and `u64` are unsigned integers of that width; a string is its
UTF-8 octets; `H` is the function selected by the record's
`hash_alg` ((#hash-algorithms)), with a 32-octet output.  Test vectors
are in (#test-vectors).

**SSM**: Source-Specific Multicast [@!RFC4607].

**AMT**: Automatic Multicast Tunneling [@!RFC7450].

**TESLA**: Timed Efficient Stream Loss-Tolerant Authentication
[@?RFC4082] [@?RFC5776].

**ASM**: Any-Source Multicast, the service model of [@!RFC4607]
Section 1 in which any host may send to `G`; the sender of an ASM
flow is the declared `senderAddress` of its metadata
((#flow-parameters)).

**Flow**: every datagram the sender emits to one `(S, G, port)`, `S`
being the source address, `G` the group address and `port` the UDP
destination port, that the flow's metadata declares protected
((#flow-parameters)).  A sender that carries the same content on two
`(S, G, port)` tuples has two flows.

**Manifest port** (`manifestPort`): the UDP destination port, on the
same `(S, G)` as the flow, of the flow's records.

**Record**: one UDP datagram on `manifestPort` that carries the
digests of one window, signed ((#manifest-record)).  "Manifest record"
and "record" are the same thing.

**Window**: a contiguous run of at most 37 datagrams of a flow whose
digests one record carries.

**Twin**: the byte-identical second copy of a record
((#sender-behavior)).

**Path**: a route by which records reach a receiver.  This document
defines one, the flow's `manifestPort`; a profile MAY add others
((#additional-record-paths)).

**Epoch**: a 32-bit counter carried in every record that increments
on sender restart and key change ((#manifest-record)); counters and
replay floors are kept per epoch.

**Generation**: the life of a flow under one `streamId`
((#flow-parameters)); a change of `streamId` resets receiver state
((#generation-change)).

**Key set**: the keys the flow's metadata names for it, each a
`(kid, publicKey, firstEpoch)` triple ((#flow-parameters)).

**Sender**: the entity that emits the flow and signs its records.
"Sending entity" names the same entity wherever this document uses
it.

**Receiver**: an implementation of (#receiver-behavior).  It may act
for an application, for a web page on whose behalf it joins, or for
a decoder it feeds.

**Metadata**: the parameters of (#flow-parameters) that a receiver
holds for a flow, however obtained: from the well-known document, a
DORMS record, an application catalog or out-of-band provisioning.

**Context source**: whatever a profile derives the record's `ctx`
from ((#signature-context-binding)); a receiver "holds the context
source" when it can recompute `ctx`.

**Profile**: a specification that binds this format to an
application by fixing how the metadata is delivered, how `ctx` is
derived and which record paths exist.

# Overview

Data datagrams are untouched: no header, no trailer and no parsing
are added to them.  Their authenticity comes from a separate stream
of signed records on the same `(S, G)` at `manifestPort`.  For each
protected flow the sender computes a digest over every datagram the
flow emits, Forward Error Correction (FEC) repair symbols included
where a flow carries them; collects digests into windows of at most
37 datagrams or `manifestTimerMs`, whichever closes first;
places each window in a fixed-layout manifest record; signs the
record with a dedicated Ed25519 key [@!RFC8032] under a
network-identity prefix; and emits the record on the flow's manifest
port immediately before the datagrams it covers, followed by a second
copy.  Receivers verify one signature per window, hash each datagram
once, and admit a datagram to delivery only after its digest matches
an entry of a verified manifest.

The digest pseudoheader, the hold queue and the consume-on-admission
rule are those of AMBI ([@?I-D.ietf-mboned-ambi] Sections 3.4.2 and
3.2); the signed record carried on the flow's own (S, G) is the
multicast-carried manifest delivery that AMBI Section 2.1.1
anticipates and leaves to another specification.

The digest algorithm is carried in the signed record as a Named
Information Suite ID ((#hash-algorithms)); SHA-256 [@!FIPS180-4] is
mandatory to implement.

A receiver delivers an admitted datagram's payload as received, and
it knows the datagram's `sequence`
((#keys-epochs-and-sequence-numbers)), which it MAY make available
to the application.  It delivers nothing
else of a protected flow.  Every flow parameter that enters the
pseudoheader or the signature prefix is declared in the flow's
metadata; the record carries none of them, and names only the digest
function (`hash_alg`) it uses and the key (`kid`) of the metadata's
key set that verifies it, so a receiver that holds the metadata
needs no other state to start, and nothing read from a datagram but
its length enters the pseudoheader.

This document defines two schemes and registers an identifier for
each ((#multicast-datagram-integrity-schemes-registry)).  Scheme 1,
`manifest-ed25519-2`, is the manifest format of (#digest) through
(#receiver-behavior) and is mandatory to implement.  Scheme 2,
`ed25519-trailer-1` ((#the-ed25519-trailer-1-scheme)), signs each
datagram in a trailer and suits low-rate flows; a receiver MAY
implement it.  A flow's metadata names the scheme the flow uses.

# Digest

Every datagram the sender emits in a protected flow has a digest:

~~~
D = H(pseudoheader || payload)
~~~

`payload` is the entire UDP payload as transmitted, any FEC payload
identifier or trailer the application appends included, so a
verified
digest also authenticates whatever the datagram carries about its
place in a repair block.  This document authenticates received
datagrams: what a receiver reconstructs from admitted datagrams alone
is admitted with them, and what it reconstructs with the help of
anything else is outside this document.

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

It is 20 octets with IPv4 addresses and 44 with IPv6; `streamId`
occupies AMBI's Manifest Stream Identifier field.  Addresses are in
native width, never IPv4-mapped.  `S` is the address from which the
sending entity transmits the flow: the source address of an SSM flow,
and the declared `senderAddress` of an ASM flow ((#flow-parameters)).
`src_port` and `dst_port` are both the flow's `port`: the sender MUST
emit every datagram of the flow from UDP source port `port`.
`streamId` is the flow's `streamId` ((#flow-parameters)).  Every
input is declared in the flow's metadata or provisioned with it
((#receiver-behavior)), so a receiver forms the pseudoheader without
reading anything from the datagram but its length, and one digest
verifies the same bytes whatever carrier delivers the datagram.  A
carrier that re-addresses either flow, or carries the datagrams in
any other form, is not covered: the pseudoheader binds `S`, `G` and
the ports, and a record verifies as it was signed or not at all.

## Hash Algorithms

`hash_alg` is a Suite ID of the IANA Named Information Hash Algorithm
Registry ([@!RFC6920] Section 9.4), a value from 0 to 63; values 64
to 255 are not Suite IDs and MUST NOT be sent.  Only a suite whose
output is 256 bits is usable, since every digest field is 32
octets; the truncated suites MUST NOT be used.  Suite 1, sha-256
[@!FIPS180-4], is mandatory to implement.  A receiver MAY implement
other 256-bit suites; it drops a record whose `hash_alg` it does not
implement ((#receiver-behavior)).  All records of one flow carry the
same `hash_alg` for the life of a flow generation (`streamId`,
(#flow-parameters)); a change of algorithm is a new generation.

# Manifest Record

A manifest record is one UDP datagram on `manifestPort` of the same
`(S, G)` as the protected flow.  Every field except the signature is
at a fixed offset, and the signature is the last 64 octets.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `magic`, the ASCII octets "MHM2" |
| 4 | 4 | `kid`, key identifier ((#flow-parameters)) |
| 8 | 4 | `epoch`, increments on sender restart and key change |
| 12 | 8 | `mseq`, manifest counter, monotonic per `(flow, kid, epoch)` |
| 20 | 8 | `first_seq`, the `sequence` of digest 0 |
| 28 | 2 | `count`, 1 to 37 |
| 30 | 1 | `hash_alg` ((#hash-algorithms)) |
| 31 | 1 | `flags` (below) |
| 32 | 4 | `sent`, emission time in POSIX seconds (below) |
| 36 | 32 | `ctx`, profile context ((#signature-context-binding)) |
| 68 | 32 x count | digests, in emission order |
| 68 + 32 x count | 64 | Ed25519 signature |

Length is `132 + 32 x count` octets, 164 to 1316.  The cap of 37
digests is an MTU choice: a record and every header it acquires on
the way travel as one unfragmented datagram on a 1500-octet path.  At
37 digests the record is 1316 octets: 1344 on the wire with IPv4 and
UDP headers and 1364 with IPv6, and 1394 or 1414 once an AMT relay
[@!RFC7450] adds its own IPv4 or IPv6 header, UDP header and 2-octet
Multicast Data header around the IPv6 datagram.  That leaves 86 to
106 octets for one further tunnel or extension header on the path; an
IPv4 record through an IPv4 relay is 1374 octets, leaving 126.  A
record of 39 digests would still fit a 1500-octet path through AMT;
one of 42 (1476 octets, 1504 under IPv4 and UDP) would not fit even
without it, and neither leaves that room, whatever the address family
of record or relay.  Digest `i` of a record covers
`sequence = first_seq + i`.

`flags`: bit 0, the least significant bit of the octet (mask 0x01),
epoch end ((#receiver-behavior)); bits 1 to 7 reserved, MUST be zero
on send and ignored on receipt.

`sent` is the sender's clock when the record is signed, truncated to
whole seconds since 1970-01-01T00:00:00Z with leap seconds excluded,
from a clock synchronized to UTC within 1 s; the twin of a record
((#sender-behavior)) carries the original's value.  It is a count of
seconds, not the 16.16 NTP short format, so it wraps in 2106 rather
than every 18.2 hours.  A sender whose clock is further off than the
tolerance of (#receiver-behavior) makes its flow unverifiable to
receivers that check freshness.

A record has no other repeat form: its second copy is a
byte-identical twin ((#sender-behavior)).

## Signature Context Binding

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

with `S`, `G`, `streamId` and `manifestPort` as declared for the flow
((#digest), (#flow-parameters)), and the signature is the 64-octet
Ed25519 signature of [@!RFC8032] Section 5.1 (the PureEdDSA variant,
with no prehash and an empty context) under the key that `kid` names.
The prefix binds the flow's network identity; a receiver needs no
state to check it beyond those four values, which it takes from the
flow's metadata or its provisioning ((#receiver-behavior)).

`ctx` is 32 octets that a profile of this format MAY derive from the
application context it binds the flow to, under a label of the
profile's choosing and with the record's `hash_alg`
([@?MOQ-MULTICAST] Section 7.2.4 binds the MoQ catalog this way).  A
flow with no such profile sets `ctx` to 32 zero octets.  A receiver
that holds the context source recomputes `ctx` and MUST reject a
record whose `ctx` differs ((#receiver-behavior)); any other receiver
carries `ctx` blind.  `ctx` is part of the signed message, not an
Ed25519 context string, which the variant above does not carry.

A valid (record, datagrams) pair therefore cannot be replayed onto
another flow, flow generation, key or epoch; `sent` bounds replay
within an epoch to the clock tolerance of (#receiver-behavior).

## Keys, Epochs and Sequence Numbers

`kid` is an unsigned 32-bit integer carried in the clear in every
record and names a key of the flow's key set ((#flow-parameters)),
each key signing the epochs from its `firstEpoch` up to, but not
including, the next larger `firstEpoch` in the set.  `epoch` never
decreases under one `kid`: a sending entity MUST NOT reuse an epoch
under a `kid`, across generations or restarts, and a generation that
would start below the `kid`'s last epoch starts under a new `kid`
((#flow-parameters)).

The protected unit is a flow: every datagram the sender emits to one
flow `(S, G, port)` that its metadata declares protected
((#flow-parameters)).  A flow has one `manifestPort`, which no other
flow of the same `(S, G)` shares ((#flow-parameters)); its `sequence`
counter (below) and its `mseq` counter ((#manifest-record)) are kept
per `(kid, epoch)`.  `mseq` starts at any value and increases by one
for every window the flow closes under one `(kid, epoch)`, in
emission order, which the replay floor of (#receiver-behavior)
(`mseq + 64 <= highest_mseq`) and the twin deadline of
(#sender-behavior) (before the signed record of window `mseq + 64`)
assume.

`sequence` is a 64-bit counter the sender assigns per `(flow, kid,
epoch)`: it starts at any value and increases by one for every
datagram the flow emits, in emission order, repair symbols included.
It is carried only in manifest records, never in data datagrams, and
is unrelated to any sequence number the payload carries.  Digest `i`
of a record covers `sequence = first_seq + i`, so one window is a
contiguous run of the flow.  A datagram the sender emits twice (a
carousel) has two sequences and two digests.  An application MUST NOT
assume that `sequence` continues across an `epoch` change.  Neither
counter wraps within an epoch: a sender ends the epoch (the record
whose `flags` bit 0 is set, (#manifest-record)) before either would
exceed 2^64 - 1, and the comparisons this document states on them,
`mseq + 64 <= highest_mseq` included, are integer comparisons that an
implementation evaluates without unsigned underflow or overflow.

# Sender Behavior

A sender closes a window after 37 datagrams or after `manifestTimerMs`
since the window opened, whichever comes first; the timer governs only
while the flow emits at most 37 datagrams per `manifestTimerMs` (1850
per second at the default, about 21 Mbit/s of 1400-octet datagrams),
and the count cap governs above that.  A sender MUST NOT close
windows on one flow faster than 1000 per second, the rate at which a
receiver's verification budget refills (step 1 of (#processing); its
depth of 64 absorbs jitter), nor close more than `64 + 1000 x t`
windows in any interval of `t` seconds, the envelope of that bucket,
which its bursts share with the network's jitter: at the count cap
that is 37,000 datagrams per second, about 414 Mbit/s of 1400-octet datagrams and
about 59 Mbit/s of 200-octet ones, and a stream above it is carried
as several flows, each with its own `port` and `manifestPort`
((#flow-parameters)), or by another scheme.  A sender above the
ceiling starves its own receivers, whose budgets drop its records and
expire its windows as loss ((#threat-model)).  A sender MAY raise
`manifestTimerMs` to at most `maxAuthDelayMs / 4` on low-rate flows;
`manifestTimerMs` is at least 1 ((#flow-parameters)), so the timer
alone never closes more than 1000 windows per second.

The signed record MUST be transmitted immediately before the first
datagram it covers (only the twin of an earlier window MAY come
between them), so the sender holds at most one window of data: 20 ms
below about 21 Mbit/s, where the timer closes windows at the default,
8.3 ms at 50 Mbit/s and 4.1 ms at 100 Mbit/s with 1400-octet
datagrams.  A twin, a byte-identical copy of the record, MUST be
transmitted after the last datagram the record covers, no later than
`maxAuthDelayMs / 2` after the record and before the signed record of
window `mseq + 64`, so that at most 63 later records precede it and
it arrives above the replay floor of (#receiver-behavior), however
fast the flow closes windows; RECOMMENDED is to transmit it
immediately after the signed record of window `mseq + 2` and before
the first datagram that record covers, or on its own at the
`maxAuthDelayMs / 2` deadline when window `mseq + 2` has not closed by
then.  The two copies then bracket the window's datagrams: a
contiguous loss burst that removes both copies has removed every
datagram between them, and a datagram that survives such a burst has a
usable copy on one side of it, whatever the flow's rate and timer;
only two separate losses can leave an arriving datagram without a
copy, and then at most 37 datagrams expire from the hold queue
((#threat-model)).  Every twin of an epoch MUST be transmitted before
the first record of a later epoch, since a receiver drops the records
of an earlier epoch once its grace period ends ((#receiver-behavior));
every twin of the epoch not yet transmitted when its last datagram has
been sent, the twin of the record whose `flags` bit 0 is set included,
follows that datagram at once.  A receiver handles either copy by
step 1 of (#processing) and drops the second with one lookup
and one hash.

At 37 digests per window, a record and its twin cost about 71 octets
per 1400-octet datagram (5.1%); data datagrams are untouched.  With
the 20 ms timer the two copies cost about 5.6% at 10 Mbit/s, about 9%
at 2.5 Mbit/s and about 23% at 128 kbit/s, where one 1400-octet
datagram is emitted every 87.5 ms and, at the default
`maxAuthDelayMs`, no timer within `maxAuthDelayMs / 4` batches two;
raising `manifestTimerMs` pays only
where several datagrams fit in one timer period, and below that rate
the trailer scheme of (#the-ed25519-trailer-1-scheme) is the cheaper
one.  Manifest records MUST NOT be FEC-protected; the twin is their
loss remedy.

The sender MUST write the current `epoch` to the flow's metadata as
`minEpoch` at every epoch change, sender restart included, so that a
joiner with current metadata cannot be fed an earlier epoch
((#flow-parameters)); what a restart requires of the sender's
`epoch` is in (#sender-responsibilities).

# Receiver Behavior

A receiver that implements this format enforces it: a datagram of a
protected flow is admitted only after its digest matches an entry of a
verified record, and there is no verify-and-report mode.  A receiver
MUST be able to pin "authentication required" for a flow
independently of its metadata.  A receiver that fetches no metadata
MUST be provisioned out of band with the keys, `firstEpoch` included,
and `minEpoch` and, per protected flow, the `streamId`, `S`, `G`,
`port`, `manifestPort` and `maxBitrate` the metadata would declare
((#flow-parameters)), and any non-default `maxAuthDelayMs` and
`manifestTimerMs`: the record carries none of them; keys are never
taken from a carrier's signaling.  A receiver that pins keys takes the
key set, `firstEpoch` included, from the pin rather than from the
metadata, and MUST keep with the pin, across sessions, the highest
`epoch` it has verified under each pinned `kid`; in step 1 below it
drops, at join, a record whose `epoch` is below that value for its
`kid`, so metadata that carries a lower `minEpoch` cannot reopen an
epoch a verified record has closed.  The pin stores no value read
from the metadata: every receiver takes `minEpoch` from the metadata
it fetched, or provisions it with the keys, and it bounds that session
only.  A receiver with no pin is protected at its first join against
an earlier epoch only as far as that metadata is.  A receiver that
implements no algorithm a flow's records carry verifies nothing on
that flow: it admits nothing and treats the flow as one that yields
no data.

Whether a flow is protected is a property of the flow's metadata, not
of any datagram: a receiver that holds metadata declaring a flow
protected delivers nothing from that flow except through this
section.

## Source Check

On an ASM flow a receiver MUST discard, before any parsing or
hashing, a datagram on `port` or `manifestPort` whose IP source
address is not `senderAddress`; behind an AMT relay the address is
that of the encapsulated header of the AMT Multicast Data message
[@!RFC7450].  On an SSM flow reached natively the network enforces
the source and a receiver SHOULD still discard a datagram whose
source address is not `S`; a receiver reached through an AMT gateway
MUST discard it, since nothing upstream of its gateway filters the
encapsulated source address and [@!RFC7450] does not authenticate
Multicast Data messages.  A datagram that passes belongs to the flow
`(S, G, port)` or `(S, G, manifestPort)` with `S` as in (#digest).

## State

State per flow: the current `epoch` with the `kid` that set it; the
grace period that ends `maxAuthDelayMs + 2 x manifestTimerMs` after
the current epoch became current and, until it ends, the previous
`epoch`; the flow's `hash_alg`, fixed by its first verified record;
per `(kid, epoch)` the verified `mseq` values above the replay floor,
each with the `hash_alg` digest of the record's bytes, the
`highest_mseq` that verified records have raised (step 1) and, once a
verified record has `flags` bit 0 set, the `mseq` that closed it; the
verification budget of step 1 with a count of the records it dropped;
a pending table of `(digest, sequence, expiry)` entries; the digests
recorded as admitted, each until the time of recording plus
`maxAuthDelayMs`; and a hold queue of `(digest, datagram, expiry)`
entries in arrival order, `digest` being absent from an entry until
the first record of the flow is verified (step 2).  State per
receiver, shared by its flows: the time of the last metadata re-fetch
that an unknown `kid` triggered ((#key-rotation-and-re-fetch)), and
the per-`kid` epoch floor kept with a key pin.

`maxBitrate`, `maxAuthDelayMs` and `manifestTimerMs` size the hold
queue and the pending table (steps 1 and 2); a receiver bounds both
by local policy.  At the budget of step 1 the pending table holds at
most `37 x (64 + 1000 x (maxAuthDelayMs + 2 x manifestTimerMs) / 1000)`
entries, 11,248 at the defaults, and the hold queue at most
`maxAuthDelayMs x maxBitrate / 8000` octets, 1.25 MB at 50 Mbit/s and
the default `maxAuthDelayMs`.

## Processing

A receiver applies the following, in this order, with no
variable-length interpretation before a cryptographic check:

1.  **Record datagram** (on `manifestPort`, `magic` "MHM2").  Require
   `164 <= len <= 1316` and `(len - 132) mod 32 == 0`.  Read the
   fixed-offset integers `magic`, `kid`, `epoch`, `mseq`, `count`,
   `hash_alg` and `sent` and the 32 octets of `ctx`.  Drop before any
   cryptography if: `magic` differs; `kid` is not in the key set, or
   `epoch` is outside its range ((#flow-parameters));
   `(kid, epoch, mseq)` is already verified (this drops the second
   copy of a record with one lookup and one hash, a copy of the
   previous epoch arriving after its grace period included; a
   dropped copy whose bytes hash, under the flow's `hash_alg`, to
   the digest kept with the verified entry is the record itself, its
   twin or a replay of it, and one whose bytes do not match is not;
   on the single record path of this document neither moves any
   floor or timer, `highest_mseq` having been raised when the entry
   was verified, below, and the distinction serves only a profile
   that adds a path ((#additional-record-paths))); `epoch` is below
   the current epoch and is not
   the previous epoch within its grace period (below), or, when no
   record has yet been verified, is below `minEpoch` or below the
   pinned floor for its `kid`; `mseq + 64 <= highest_mseq(kid, epoch)`
   (replay floor, none before a record of that `(kid, epoch)` has
   raised `highest_mseq`, no upper bound; the sum does not wrap,
   (#keys-epochs-and-sequence-numbers)); `mseq` is above the `mseq`
   that closed the epoch, once a verified record has closed it;
   `sent` is more than `7 s + maxAuthDelayMs` behind, or more than
   6 s ahead of, the receiver's UTC clock (freshness: the sender's
   1 s bound and the receiver's 5 s bound, plus, behind, the
   truncation of `sent` to whole seconds and the delivery of the
   twin); `count != (len - 132) / 32`; `hash_alg` is not in the
   receiver's accepted set, or differs from the flow's `hash_alg` once
   one is fixed; or, on a receiver that holds the context source of
   (#signature-context-binding), `ctx` differs from the value
   recomputed from it (any other receiver carries `ctx` blind).
   Charge the per-flow verification budget, a token bucket of depth
   64 refilled at 1000 tokens per second; drop and count a record
   that finds it empty (nothing before the signature tells a forged
   record from a genuine one, so a forged record spends the same
   token, (#threat-model)).  Verify the Ed25519 signature over
   `signed_message`; drop on failure, and only on success read
   `first_seq`, `flags` and the digests.  If `epoch` is above the
   current epoch, or this is the first verified record, make `epoch`
   current and make the former current epoch the previous epoch,
   with a grace period that ends `maxAuthDelayMs + 2 x manifestTimerMs`
   after now (the sender emitting every twin of it before the new
   epoch's first record, (#sender-behavior)), fix the flow's
   `hash_alg` from this record if none is fixed yet, and hash every
   held datagram that has no digest yet; pending entries and held
   datagrams of the previous epoch are not flushed and live out their
   expiry.  A record of the previous epoch that passes the checks
   above is processed under that epoch's own floor and verified set
   and never changes the current epoch.  Record `(kid, epoch, mseq)`
   as verified, with the `hash_alg` digest of its bytes, and raise
   `highest_mseq`.  For each `(digest, sequence)` of the record, in
   order: if the hold queue holds a datagram with that digest, admit
   the oldest such datagram, remove it from the queue and record its
   digest as admitted until `now + maxAuthDelayMs` (step 2);
   otherwise insert the pair into the pending table with expiry
   `now + maxAuthDelayMs + 2 x manifestTimerMs` (240 ms at the
   defaults).  Once every pair of the record is processed, drop from
   the hold queue each datagram still held whose digest is now
   recorded as admitted: it is a repeated copy of a datagram this
   record admitted, which step 2 would not have held after the
   admission; its drop is not an expiry and counts toward nothing
   ((#threat-model)).  A window's digests are inserted once: a record
   for a window already verified is dropped above, so no entry is
   refreshed or re-inserted.  If `flags` bit 0 is set the epoch is
   closed at this `mseq` ((#manifest-record)): later records with
   this `epoch` and a higher `mseq` are dropped, pending entries live
   out their expiry, and the next epoch is accepted by the rule above.

2.  **Data datagram** (on `port`).  Compute `D` with the flow's
   `hash_alg` (a datagram that arrives before the first record of the
   flow is verified is held without a digest) and look it up in the
   pending table, which maps a digest to an ordered list of sequences
   (carousels repeat byte-identical datagrams).  Hit: remove the
   lowest sequence, admit the datagram and record `D` as admitted
   until `now + maxAuthDelayMs`.  Miss: drop the datagram if `D` is
   so recorded (a copy of an admitted datagram delivered again is
   never held); otherwise append `(D, datagram)` to the hold queue
   with expiry `now + maxAuthDelayMs`, the queue bounded to
   `maxAuthDelayMs x maxBitrate / 8000` octets; drop the newest on
   overflow, since dropping the oldest would let an injector purge
   legitimately held datagrams, and drop at expiry, as
   unauthenticated.  Repair symbols follow the same rule, so an
   injected symbol is dropped before it reaches a decoder.  A
   receiver MUST NOT deliver to an application, or feed to a decoder,
   a datagram of a protected flow that it has not admitted under
   step 1 or 2, on whatever carrier it arrived.

**Replay.** Receivers in an explicitly configured digital video
recorder (DVR) or replay mode MAY relax the epoch, floor and
freshness checks.  A `(digest,
sequence)` entry is consumed when matched, so a replayed datagram
finds no entry unless a legitimate identical copy is still pending,
in which case the replay consumes that copy and the later legitimate
copy is dropped (the application receives the same bytes either way;
this is a denial of service only, bounded by the carousel repeat
count).  Cross-flow replay is excluded by `streamId`, `S` and `G` in
both the digest and the signature, `port` in the digest and
`manifestPort` in the signature.

## Key Rotation and Re-fetch

A key change is an epoch change ((#manifest-record)).  The sender
adds the next `kid` to the metadata with the `firstEpoch` at which it
will sign, at least one metadata lifetime ahead; signs with it from
that epoch; and raises `minEpoch`.  A receiver that holds that
metadata accepts the retired `kid` below the successor's `firstEpoch`
only, so records the retired key signs are admitted until the grace
period for the new epoch ends (step 1 of (#processing)); a receiver
that verifies no record of the new epoch keeps the epoch before it
current, which the retired key still signs, and a receiver whose
metadata or pin predates the rotation is exposed to the retired key
until it re-fetches or is re-provisioned ((#threat-model)).  A record
with an unknown `kid` triggers at most one metadata re-fetch per 30 s
per receiver; until then such records are dropped.  Whenever a
re-fetch or a re-provisioning changes the key set or a `kid`'s range,
the receiver re-applies the range check of (#flow-parameters) to the
`(kid, epoch)` that set each flow's current epoch; where it now
fails, the receiver discards that flow's state as it does on a
`streamId` change ((#generation-change)), the `digest` of every held
datagram included, and returns to the join state of step 1, so a
record a retired key signed before the re-fetch cannot hold the flow
afterwards.  Revocation is key removal, effective within one metadata
lifetime.  The metadata lifetime is the lifetime that
(#fetching-the-document) derives from the response's Cache-Control
for a receiver that uses the well-known document, and whatever bounds
the validity of a DORMS record, a
catalog or a provisioning otherwise.

## Generation Change

The per-flow state of (#state) belongs to the flow generation
((#manifest-record)): when the `streamId` the metadata, or a
receiver's provisioning, declares for the flow changes, the receiver
discards every per-flow item of (#state) but the verification budget
and its count and the hold queue (the current and previous `epoch`,
`hash_alg`, the per-`(kid, epoch)` `mseq` state, the pending table and
the admitted digests), clears the `digest` of every held datagram,
and processes the next record as the first of the flow under the
join-time floors of step 1 of (#processing).

## Additional Record Paths

This document delivers records on `manifestPort` only, so the record
that makes an epoch current is the first record of that epoch the
receiver verifies, the grace period of the previous epoch starts at that
moment, and one replay floor per `(kid, epoch)` suffices.  A profile
that adds a second record path (a unicast mirror of the same record
octets, for instance) MUST specify, per path, the replay floor and
the grace period a record arriving on that path meets, which records
raise or start them, and a deadline after which no record of the
previous epoch is admitted on any path, reckoned from the time the
current epoch became current, since on such a profile a path can see
the new epoch's records late or not at all; it MUST also specify
which verification budget of step 1 a record arriving on each path
charges, with the count of dropped records that goes with it, how a
record verified on one path is treated when its copy arrives on the
other, and by how much the pending-entry expiry and the
admitted-digest retention of step 1 are widened for a record on that
path, so that the lead of one path over the other does not expire an
entry before the datagrams it covers arrive.  [@?MOQ-MULTICAST]
Section 7.2.7 does so for a MoQ manifest track: one budget per path,
each with its count; the previous-epoch deadline at the bound of its
Section 7.2.5 plus `maxAuthDelayMs + 2 x manifestTimerMs` after the
current epoch became current; and the pending expiry and the
admitted-digest retention widened by the mirror's lead, the bound of
that section until one is measured.  A profile that adds no path
applies this document as written.

## Clocks

The freshness check needs a receiver clock synchronized to UTC within
5 s.  A receiver without one MAY skip that check alone; it then
accepts any window of the current epoch at join and has no protection
against replay of the epoch's earlier windows until its first
verified record sets the floor ((#threat-model)).  Every other
timer of this section (`maxAuthDelayMs`, `manifestTimerMs` and the
expiries derived from them) is a local interval and needs no
synchronized clock.

## Cost

A datagram from another source costs one address comparison; one that
spoofs `S` costs one hash, two lookups and, on a miss of both, space
in the hold queue until expiry, so a copy of an admitted datagram
costs one hash and two lookups; an injected record costs at most one
verification inside the budget, a replayed one whose
`(kid, epoch, mseq)` is still verified one lookup and one hash while
its `mseq` is above the replay floor (the already-verified lookup of
step 1 precedes the freshness check), one outside the verified set
and outside the freshness tolerance that lookup alone, a miss, before
the epoch floor, the replay floor or the freshness check drops it,
the second copy of a verified record one lookup and one hash.  With
one verification per 37 datagrams, a Cortex-A53 without SHA2
instructions spends about 0.26 of a core at 100 Mbit/s and, under a
record flood at a budget of 1000/s, about 0.43 of a core on signature
checks, the hashing of the flow's own datagrams continuing beside
them; a core with SHA2 instructions spends a fraction of that.

# Flow Metadata and the Well-Known Document

## Flow Parameters

A receiver needs the following for each protected flow.  They are
delivered by any authenticated means a profile specifies: the
well-known document of (#the-well-known-document), a DORMS record
[@?I-D.ietf-mboned-dorms] or AMBI metadata [@?I-D.ietf-mboned-ambi],
an application catalog ([@?MOQ-MULTICAST] Section 7.2.6), or
out-of-band provisioning ((#receiver-behavior)).  The names below are
those of the well-known document; a profile that carries them under
other names maps them one to one.

- **scheme** (REQUIRED): the name of the scheme the flow uses,
  `manifest-ed25519-2` for this format and `ed25519-trailer-1` for
  (#the-ed25519-trailer-1-scheme), from
  (#multicast-datagram-integrity-schemes-registry).
- **S** (REQUIRED): the address from which the sending entity
  transmits the flow, `S` of (#digest).  On an SSM flow it is the
  SSM source; on an ASM flow it is declared as **senderAddress**,
  which MUST NOT appear on an SSM flow.  Two ASM flows whose
  `senderAddress` differ MAY share `G` and ports; the source check of
  (#receiver-behavior) separates them.
- **G** (REQUIRED): the group address, of the same address family as
  `S`.  Wherever a receiver matches metadata to a flow it compares `S`
  and `G` as IP addresses, never as strings, and an address of one
  family never matches one of the other, an IPv4-mapped IPv6 address
  being of the IPv6 family ((#the-well-known-document)).
- **port** (REQUIRED): the UDP destination port of the data
  datagrams, and the source port from which the sender emits every
  datagram of the flow ((#digest)).
- **manifestPort** (integer, REQUIRED): destination port of the record
  datagrams, twins included, on the flow's `(S, G)`; MUST differ from
  the `port` of every flow of the same `(S, G)` the metadata declares,
  this flow included, and from the `manifestPort` of every other such
  flow, so that no port of an `(S, G)` carries both data and records,
  or the records of two flows.  A receiver MUST NOT join a protected
  flow whose ports violate this.  Metadata MUST declare each
  `(S, G, port)` at most once; a receiver whose metadata declares one
  twice holds no parameters for that flow and does not join it
  ((#the-well-known-document)).
- **streamId** (integer, REQUIRED): 32-bit value chosen per flow
  generation,
  bound into every digest and signature.
- **keys** (array, REQUIRED): one to four `{kid, publicKey, firstEpoch}`
  objects.  `kid` is an unsigned 32-bit integer carried in the clear
  in every record; `publicKey` is the 32-octet Ed25519 public key;
  `firstEpoch` is the first `epoch` the key signs.  A key signs the
  epochs from its `firstEpoch` up to, but not including, the next
  larger `firstEpoch` in the array, and the key with the largest
  `firstEpoch` signs every later epoch.  `kid` values MUST be unique
  within the key set and `firstEpoch` values MUST be distinct within
  the array.  A receiver that takes its keys from metadata whose key
  set repeats a `kid` or a `firstEpoch`, or names a `publicKey` that
  is not 32 octets, holds no key set for the flow or flows that key
  set is attached to (below): it admits nothing
  from them, as it does on a flow whose records carry an algorithm it
  does not implement ((#receiver-behavior)), and the other flows of
  the same metadata, with key sets of their own, are unaffected; a
  receiver that pins keys is unaffected, since its key set comes from
  the pin.  A receiver drops, before
  verification, a record whose `epoch` is outside its `kid`'s range
  ((#receiver-behavior)), so a retired key cannot carry a receiver
  past its successor's `firstEpoch`.
- **minEpoch** (integer, REQUIRED): the lowest `epoch` a receiver
  accepts at
  join (step 1 of (#processing)); after its first verified record the
  current epoch is the floor, with the previous epoch admitted until
  its grace period ends, `maxAuthDelayMs + 2 x manifestTimerMs` after
  the current epoch became current (step 1).  The sender MUST write
  the current `epoch` at every epoch change, sender restart included,
  so a joiner with current metadata cannot be fed an earlier epoch.
- **maxAuthDelayMs** (integer, OPTIONAL, default 200, range 50 to
  1000): how long a receiver holds a datagram whose digest has not
  arrived.
- **manifestTimerMs** (integer, OPTIONAL, default 20, at least 1):
  the window timer of (#sender-behavior).
- **maxBitrate** (integer, REQUIRED): the sender's declared ceiling
  for the
  flow in bit/s, which bounds the receiver's hold queue (step 2 of
  (#processing)).  [@?MOQ-MULTICAST] declares the same value as the
  endpoint's `bandwidth`.

The ranges above are binding.  A receiver that finds `maxAuthDelayMs`
outside 50 to 1000 or `manifestTimerMs` below 1 MUST either clamp it
to the nearest bound or decline the flow, as its profile specifies,
and MUST NOT use the out-of-range value.  The other parameters are
identifiers or sizes, not tunables, and a clamped identifier names a
port, key, generation or epoch the sender never declared: a receiver
that finds a `keys` array of no or more than four entries, a `port`
or `manifestPort` of 0, a `maxBitrate` that is not a positive
integer, or `port`, `manifestPort`, `streamId`, `kid`, `firstEpoch`
or `minEpoch` outside its field width, MUST decline the flow.  The
browser profile clamps `maxAuthDelayMs` (to 50 and 1000).

`maxAuthDelayMs`, `manifestTimerMs` and `maxBitrate` are per flow.
`keys` and `minEpoch` are per key set; the metadata attaches a key
set to one flow (the well-known document carries one per channel,
(#the-well-known-document)) or to several ([@?MOQ-MULTICAST] Section
7.2.6 carries one per broadcast), and every flow it is attached to
uses that key set and that `minEpoch`.  A flow using `ed25519-trailer-1` declares `scheme`, `S`,
`G`, `port`, `keys` and `maxBitrate` only.

## The Well-Known Document

A sender that serves receivers which can fetch over HTTPS publishes
its flows' parameters at

~~~
https://<S>/.well-known/multicast-receive
~~~

where `<S>` is the SSM source address as the IP address literal in
the `host` of an `https` URI ([@!RFC9110] Section 4.3.5), IPv6 in
brackets, never a host name; the well-known URI is registered in
(#well-known-uri-registration).  The document is JSON [@!RFC8259],
served with the media type `application/json`; the well-known URI is
used with the `https` URI scheme only:

~~~ json
{
  "version": 1,
  "channels": [
    {
      "source": "198.51.100.7",
      "group": "232.10.20.30",
      "port": 5004,
      "maxBitrate": 8000000,
      "integrity": {
        "scheme": "manifest-ed25519-2",
        "manifestPort": 5005,
        "streamId": 2864434397,
        "minEpoch": 17,
        "maxAuthDelayMs": 200,
        "manifestTimerMs": 20,
        "keys": [
          {
            "kid": 1,
            "publicKey":
              "A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg",
            "firstEpoch": 1
          }
        ]
      }
    }
  ]
}
~~~

**version** (integer, REQUIRED): the document format; this document
defines 1.  A document whose `version` is not 1 is not used: a
receiver treats it as listing no channel ((#fetching-the-document))
and takes no parameter from it, so no flow is protected on its
account.  A receiver ignores a member it does not recognize at the
document, channel, integrity and key level, so that a later revision of
this document can add members under `version` 1 without disturbing a
receiver that implements this one; `version` changes only when a
receiver that implements this document would otherwise misread the
new format.

**channels** (array, REQUIRED): one object per flow the source
serves to such receivers.  A document that is not a JSON object, or
whose `channels` is not an array, lists no channel.  Each carries
**source** (`S`, an IP literal, equal to the address the document
was fetched from),
**group** (`G`), **port**, **maxBitrate** and an **integrity**
object with **scheme** and, for `manifest-ed25519-2`,
**manifestPort**, **streamId**, **minEpoch**, **maxAuthDelayMs**,
**manifestTimerMs** and **keys**, each as (#flow-parameters)
defines it; `publicKey` is base64url-encoded without padding
([@!RFC4648] Section 5), 43 characters for the 32 octets.  For
`ed25519-trailer-1` the integrity object carries `scheme` and `keys`
only.  A receiver matches a flow by `(S, G, port)` exactly, comparing
`source` and `group` to `S` and `G` as IP addresses after parsing
their textual forms, not as strings, since an IPv6 literal has several
textual forms; `source` and `group` MUST be IP address literals in the
IPv4address or IPv6address form of [@!RFC3986] Section 3.2.2
(dotted-decimal with no leading zeros; IPv6 without brackets or a
zone identifier), never names, of one address family, that of the
address the document was fetched from, and a receiver ignores a channel whose address members
are not; an IPv4-mapped IPv6 literal is of the IPv6 family and does
not match an IPv4 address, the families themselves having to match.
It ignores an element of `channels` that is not a JSON object, a
channel it cannot match, every channel whose `(S, G, port)` another
channel of the same document also declares, one whose ports violate
(#flow-parameters), one that lacks a member this section or
(#flow-parameters) marks REQUIRED for its `scheme`, or carries a
member of this section under a JSON value of a kind other than the
one named here (a number with an integer value for `port`, `kid`,
`firstEpoch` and each member this section or (#flow-parameters)
calls an integer, a string for `source`, `group`, `scheme` and
`publicKey`, an object for `integrity` and for each element of
`keys`, an array for `keys`), a member of the wrong kind being
absent, so that a REQUIRED one leaves the channel ignored and an
OPTIONAL one takes its default, one whose `keys` array yields no key
set (no or more than four entries, a repeated `kid` or `firstEpoch`,
or a `publicKey` that is not 43 base64url characters decoding to 32
octets, (#flow-parameters)), and one whose `scheme` it does not
implement; each of these is ignored alone, and the other channels of
the document are unaffected.  The document describes SSM flows only,
since it is fetched from `S`; an ASM flow's metadata is delivered by
other means.  A receiver bounds the size of the document and the
number of channels by local policy.

## Fetching the Document

A receiver fetches the document with an HTTPS GET addressed to the IP
literal `S`.  The server's certificate MUST contain an iPAddress
subjectAltName ([@!RFC5280] Section 4.2.1.6) carrying `S` in native
width in network byte order, an IP-ID in the terms of [@!RFC9525]
Section 1.5, and the receiver MUST verify the certificate as an https
client does for a host that is an IP literal ([@!RFC9110] Section
4.3.4), with `S` as its IP-ID reference identifier and an
octet-for-octet match of `S` against that entry, no partial match
([@!RFC9525] Sections 6.2 and 6.4); no DNS record is a security boundary of this format, and a
receiver never resolves a name to find the document.  A receiver MUST
NOT follow a redirect, and it sends no credentials.

A receiver that acts on behalf of a web origin sends that origin in
the Origin request header, as the CORS protocol of [@!WHATWG-FETCH]
does, and the response MUST carry an Access-Control-Allow-Origin
header naming that origin; a wildcard is not consent, nor is a
response that carries no Access-Control-Allow-Origin header or one
naming another origin or the string `null`, which names no origin,
and such a receiver MUST treat each of them as
listing no channel for its origin and MUST NOT use it for that
origin.  A receiver acting for an origin that serializes to `null`
sends no Origin header and treats the response as listing no channel
for it, and a sender MUST NOT send
`Access-Control-Allow-Origin: null`.  A sender that publishes for
every origin echoes the request's Origin, a `null` Origin excepted,
which it answers as it answers a request that carries no Origin
header, and sends `Vary: Origin`, as [@!WHATWG-FETCH] asks of any
response whose Access-Control-Allow-Origin is not a single
static value, so that a cache, the receiver's own or one shared on
the path to `S`, does not serve one origin's response, or the
response to a request that carried no Origin header, to another
origin.  This is the per-origin gate that
[@?I-D.ietf-mboned-dorms] Sections 2.3.5 and 4.5 place on DORMS
metadata, carried from a DNS-discovered server to the source address
itself and with the wildcard rejected rather than discouraged; it is
the CORS-like cross-origin authorization that
[@?I-D.ietf-mboned-multicast-security] Section 2.7.3 asks for.  A
receiver that acts for no origin sends no Origin header and ignores
the response header.

A receiver keeps the parameters it took from the document for a
metadata lifetime ((#key-rotation-and-re-fetch)) derived from the
response's Cache-Control and clamped to 60 s at least and 24 h at
most: the value of the max-age directive ([@!RFC9111] Section
5.2.2.1) less the response's current age, reckoned as Section 4.2.3
of that document does from the Age and Date header fields and the
receiver's own request and response times; Expires, s-maxage and
heuristic freshness (its Sections 5.3, 5.2.2.10 and 4.2.2) are not
consulted.  A response with no Cache-Control, with no max-age or a
max-age that is not a non-negative integer, or one that carries
no-store or no-cache (its Sections 5.2.2.5 and 5.2.2.4), gives the
minimum, 60 s.  This lifetime governs the parameters the receiver
holds, not the HTTP response: any HTTP cache the receiver's fetch
passes through follows [@!RFC9111] as usual, so a no-store response
is not stored and a no-cache one is not reused without validation.
The receiver re-fetches the document when that lifetime expires; such a re-fetch
that fails, or returns a response the receiver cannot use (one that
does not verify as this section requires, is not the document of
(#the-well-known-document), carries a `version` the receiver does not
implement, or carries no consent for its origin, as above), is
treated as a document that lists no channel for the flow, since a
receiver that kept the expired document would let an attacker that
can block the fetch keep
a withdrawn grant or a removed key in force past its lifetime; a flow
whose channel,
key set or origin grant the re-fetched document no longer lists is
left (a key set that still names a key but drops the current `kid` is
a key-set change under (#key-rotation-and-re-fetch), not a
withdrawal),
so withdrawal of consent is effective within one metadata lifetime,
and a sender that wants faster withdrawal publishes a short lifetime or
stops signing.  A record with an unknown `kid` triggers at most one
re-fetch per 30 s per receiver ((#key-rotation-and-re-fetch)); a
re-fetch so triggered that fails, or returns a response the receiver
cannot use, leaves the parameters the receiver holds in force until
their lifetime expires, since the records that triggered it are unauthenticated and
are dropped either way, and treating that failure as a withdrawal
would let any host that can inject one such record and keep the
server's answer from the receiver make every receiver that holds the
metadata leave the flow at once.

# The ed25519-trailer-1 Scheme

A receiver MUST implement `manifest-ed25519-2` and MAY implement
`ed25519-trailer-1`, which a flow's metadata selects by its `scheme`
((#flow-parameters)).  The scheme signs each datagram and so costs a
receiver one signature verification per datagram; it suits control
and signaling flows of a few hundred datagrams per second where zero
authentication latency matters more than CPU, and at 128 kbit/s of
1400-octet datagrams its overhead, 5.7%, is below that of the
manifest format ((#sender-behavior)).  A receiver MAY refuse a flow
that declares `ed25519-trailer-1` with `maxBitrate` above 10 Mbit/s,
since every injected datagram costs one full verification
([@?RFC6584] Section 7.1).

Each datagram of the flow ends in an 80-octet fixed-layout trailer:

| Offset from end | Size | Field |
|---|---|---|
| 80 | 4 | `kid`, key identifier ((#flow-parameters)) |
| 76 | 4 | `epoch` |
| 72 | 8 | `seq`, sequence number, per `(flow, kid, epoch)` |
| 64 | 64 | Ed25519 signature |

The signature is the Ed25519 signature of [@!RFC8032] Section 5.1,
under the key that `kid` names, over

~~~
signed_message =
    S                     # 4 or 16 octets
 || G                     # 4 or 16 octets
 || u16(port)
 || u32(epoch)
 || u64(seq)
 || payload               # the datagram without its trailer
~~~

with `S`, `G` and `port` as declared for the flow and addresses in
native width as in (#digest).  `kid`, the key set and the rules for
`epoch` under a `kid` are those of (#keys-epochs-and-sequence-numbers)
and (#flow-parameters); `seq` starts at any value and increases by
one for every datagram the flow emits under the `(kid, epoch)`.

A receiver applies the following, in this order.  Require
`len >= 80`.  Read `kid`, `epoch` and `seq` at their fixed offsets;
drop the datagram if `kid` is not in the key set or `epoch` is
outside its range.  Apply the replay window before any cryptography:
the receiver keeps, per `(flow, epoch)`, a sliding window of 1024
sequence numbers whose right edge is the highest verified `seq`; a
`seq` below the left edge, or already seen inside the window, is
dropped; a `seq` inside the window not yet seen, or above the right
edge, proceeds to verification; on success a `seq` above the right
edge becomes the new right edge, and one inside the window is marked
seen, as in the anti-replay processing of [@?RFC6584] Section 3.3.2.
An `epoch` above the current one, once a datagram of it verifies,
becomes current and resets the window; a datagram of a lower `epoch`
is dropped.  Verify the signature; drop on failure.  Deliver the
payload with the trailer removed, `seq` being the datagram's
`sequence` for the application.  The source check of
(#receiver-behavior) applies to the datagrams of such a flow as to
any other.

Key rotation and revocation are as in (#key-rotation-and-re-fetch),
with no grace period: the key set bounds each `kid` to its epoch
range, and a re-fetch that changes the key set or a `kid`'s range
re-applies the range check to the `(kid, epoch)` that is current and,
where it now fails, discards the flow's window and returns to the
join state.  The scheme carries no emission time and its metadata no
`minEpoch`, so a receiver that joins accepts the first datagram that
verifies under a listed key whatever its `epoch`
((#security-considerations)).

# Security Considerations

## Properties Provided

For a flow using `manifest-ed25519-2`, a receiver that follows
(#receiver-behavior) delivers no datagram that the sender did not
emit on that flow, under that key, in that epoch and flow generation
(integrity and origin authenticity per datagram); admits each
`(digest, sequence)` pair at most once and verifies each record once
(replay, bounded within an epoch by `sent` at join and by the replay
floor after the first verified record); and can detect deletion, loss
and reordering within an epoch of the flow, since digest `i` of a
record covers `sequence = first_seq + i` and the sequences of admitted
datagrams are known.  `sequence` and `mseq` restart at any value at an
epoch change ((#keys-epochs-and-sequence-numbers), (#manifest-record)),
so where an epoch began is not known to a receiver, and where it ended
is known only from a verified record whose `flags` bit 0 is set
((#processing)); a deletion at either boundary is not a gap.  That is
the minimal standard of
[@?I-D.ietf-mboned-multicast-security] Section 2.3, "protection
against replay, injection, and modification and the ability to detect
deletion, loss, or reordering", a deleted datagram being a gap in the
admitted sequences as a lost one is, and no mode of this document delivers an
unauthenticated datagram (Section 2.4.4 of that document).  Because
every datagram, repair symbols included, is admitted by its own
digest before any use, an injected datagram cannot invalidate an
object or a repair block and so force recovery, the amplification
that Section 2.1 of that document describes; because a receiver
delivers nothing it has not admitted, injected or modified traffic
reaches no parser, decoder or renderer behind it, as Section 2.7.2
requires; and because a receiver can reject a flow its metadata does
not authorize for the origin on whose behalf it acts
((#fetching-the-document)), it can unilaterally reject data the
sender has not authorized for that page, the property Section 2.8.1
asks for.  The pseudoheader in every digest and the prefix in every
signature bind the datagrams to the flow and its generation, so an
on-path adversary cannot swap the datagrams of two flows a receiver
trusts, the example Section 2.5 of that document gives of what
unbound delivery permits; that section asks for binding to a
specific client request, and this document binds data to the flow
the receiver chose to join and, where a profile derives `ctx`, to
its application context, which is as far as a format with no return
channel binds it.

The format provides no confidentiality: datagrams, records and keys
are visible to every receiver and to the path, and the digests
reveal whether two datagrams are identical.  It provides no
protection of availability ((#threat-model)).

The format rests on the second-preimage resistance of `H`: an
attacker that can find, for a digest in a verified record, another
`pseudoheader || payload` with that digest has it admitted in place
of the sender's datagram ((#digest)); where the attacker can
influence what the sender transmits it rests on collision resistance
as well, and so does a profile that derives `ctx` with `H`
((#signature-context-binding)).  A datagram whose content an attacker
can predict lets it run that second-preimage search before the sender
transmits the datagram, the offline attack on predictable packets
that [@?I-D.ietf-mboned-ambi] Section 8.1 describes; the pseudoheader
adds nothing unpredictable, so the format relies on the strength of
`H` alone against it rather than on unpredictable content.
Collision difficulty is the digest anchor that Section 2.1 of
[@?I-D.ietf-mboned-ambi] names, and SHA-256 provides both properties
at the full 256-bit output that (#hash-algorithms) requires.  The
Named Information Hash Algorithm Registry carries a Status field
([@!RFC6920] Section 9.4); a suite the registry marks deprecated no
longer offers that assurance, and a sender that moves to another
suite starts a new flow generation ((#hash-algorithms)).  No receiver
holds a secret: the verification keys are public, so a compromised
or malicious receiver can forge nothing that another receiver
admits, the asymmetric authentication of each content unit before
any use that Section 2.4.4 of [@?I-D.ietf-mboned-multicast-security]
asks for; for a receiver that pins keys, the signing key is the
flow's only long-term secret ((#sender-responsibilities)).

## Threat Model

This format protects against off-path and on-segment UDP injection,
against corrupted or attacker-injected repair symbols, and against
replay: a `(record, datagrams)` pair cannot be moved to another
flow, flow generation, key or epoch ((#signature-context-binding));
an earlier epoch is rejected at join by `minEpoch`
((#flow-parameters)) and, on a receiver that pins keys, by the epoch
floor kept with the pin, and after the first verified record by the
current epoch, the previous epoch admitted until its grace period
ends ((#receiver-behavior)); and within an epoch a receiver with a
UTC-synchronized clock admits no window whose record was emitted more
than `7 s + maxAuthDelayMs` before receipt, so the verification
budget cannot be spent with stale genuine records and the replay
floor of (#receiver-behavior) takes over after the first verified
record.  A receiver that skips the freshness check can be fed the
current epoch's earlier windows at join, and an injector that keeps
its budget spent can hold it there.  Clock skew beyond the 1 s and
5 s bounds of (#manifest-record) and (#clocks) costs availability
where it makes the receiver's clock fast or the sender's slow:
genuine records are dropped as stale.  Skew the other way, a
receiver clock slow or a sender clock fast by X in total, widens the
replay window: the receiver admits at join windows older than the
tolerance states by X, within the bounds as beyond them, and once X
passes about 6 s it drops genuine records as future and admits only
what an injector replays from that far back, so a receiver that
cannot keep its clock within its bound does better to skip the
freshness check, as (#clocks) allows, than to check against a clock
it does not trust.  An injector that can only
replay what the multicast path has already delivered meets the
already-verified lookup and the replay floor of step 1.

Metadata rewrite and key substitution are defended only for receivers
that hold an out-of-band key pin.  The digest algorithm is inside the
signed record, so a rewrite can declare the flow unprotected,
substitute keys or lower `minEpoch`; the pin catches the first two
and the per-`kid` epoch floor kept with it ((#receiver-behavior)) the
third, except where a lowered `minEpoch` admits records of an earlier
epoch signed with a still-listed `kid`: every earlier epoch at a
receiver's first join under that `kid`, and at any later join the
highest epoch verified under it, which the floor keeps rather than
drops, so a holder of a still-listed retired key signs fresh records
of that epoch; either is admitted until a record of the current epoch
is verified, and after that as the previous epoch (step 1 of
(#processing)), so rotated-out keys SHOULD be removed promptly.  A
rewrite that raises
`minEpoch` costs a receiver, pinned or not, that session's data and
nothing more, since neither carries a metadata value past the
session ((#receiver-behavior)).  Rewriting any other parameter of the
flow only makes genuine records fail the signature or `ctx` check, or
resizes the hold queue and pending expiry (`maxBitrate`,
`maxAuthDelayMs`, `manifestTimerMs`), which a receiver bounds by local
policy ((#state)).  A rewrite that redirects a receiver to another
`(S, G)` is a join the receiver's metadata source authorized, and
what it then receives verifies under the keys that metadata names or
not at all; bounding the joins a receiver performs on behalf of one
metadata source is a matter for the profile.

This format protects integrity, not availability.  A forged record
passes every check of step 1 of (#processing) up to the signature, so
each one spends a token of the verification budget: an attacker who
sustains more than 1000 records per second on the manifest port
(about 1.3 Mbit/s of 164-octet records) takes a share of the budget
proportional to its rate, and at several times that rate both copies
of a window lose their tokens and the flow yields no data.  The
budget bounds the receiver's CPU; it does not raise the cost of this
attack, and the record flood is not the cheapest availability attack
on every protected flow: a datagram on the data port that matches no
pending entry is held until it expires (step 2 of (#processing)), and
those expiries are loss to the application, so an injector that
sustains, with the same access as the record flood, a given loss
fraction does so for less than the 1000 records per second the record
flood needs wherever that fraction of the flow's packet rate is below
it, as on every audio flow and most low-rate video; only evicting
genuine datagrams, by overflowing the hold queue, needs the flow's
bandwidth.  On an SSM flow reached natively either flood must spoof
`S` or be on path; on an ASM flow any host that can send to the group
suffices, and so it does behind an AMT gateway, where a flood need
only spoof the relay's address toward the gateway
((#receiver-behavior)).  A datagram that expires from the hold queue
is loss to the application; a held copy that step 1 drops because a
record admitted another copy of the same datagram is not.  A receiver
SHOULD report records that the budget dropped for want of a token as
loss as well, so that a sustained record flood is visible to the
application rather than ending in silence.

Joining `(S, G)` delivers to the receiver's host every datagram the
network forwards for `(S, G)`, on every port, before any
verification: multicast routing selects on addresses, not on UDP
ports.  Section 8.2 of
[@?I-D.ietf-mboned-ambi] describes what that does outside the
receiver, a datagram injected into a subscribed group reaching an
unrelated application on the host that listens on the unspecified
address at another port, and recommends that senders list every flow
they send in their metadata and that a firewall block multicast
traffic to the unsecured ports of an `(S, G)` that carries secured
traffic; a receiver that implements this document is not that
application, but it pays for every datagram on `port` and
`manifestPort` as (#cost) states, so an attacker that can inject into
the group spends the receiver's link before any check, and, where it
sends as `S` (or as `senderAddress` on an ASM flow, (#source-check)),
its hashing budget as well; a datagram from any other source costs
the one comparison of (#cost).  This document bounds the price per
datagram and the state: a datagram on `port` that passes the source
check costs one hash and space in the hold queue, which is bounded in
octets, until it expires, when
it is dropped as unauthenticated, loss the application sees (step 2
of (#processing)); one on `manifestPort` costs at most one
verification inside the budget of step 1.  The link capacity the
injected traffic takes and the rate at which the receiver keeps
hashing it are bounded by nothing here: a ceiling on the datagrams a
receiver accepts from a joined group, counted before verification,
and what it does when the ceiling is exceeded, belong to the
profile's ingress ceiling (the browser profile leaves the group).

A receiver that holds the metadata naming the successor key accepts
the retired `kid` only below the successor's `firstEpoch`
((#flow-parameters)), and records of the previous epoch only within
its grace period, so for that receiver a key retired at an epoch
boundary signs records admitted for at most
`maxAuthDelayMs + 2 x manifestTimerMs` after the new epoch's first
record is verified.  An attacker that drops every record of the new
epoch keeps the epoch before the change current at that receiver,
and, holding the retired key, signs records that receiver admits
until a record of the new epoch reaches it, the metadata removes the
retired `kid` or the receiver is re-provisioned, `minEpoch` binding
only a join.  A receiver with older metadata is exposed to the
retired key until it re-fetches, one metadata lifetime plus the 30 s
re-fetch interval of (#key-rotation-and-re-fetch) at most, and a
pinned receiver until it is re-provisioned.

Losing both copies of a window leaves at most 37 datagrams
unauthenticated, which expire from the hold queue.  Latency of
authentication is bounded by `maxAuthDelayMs`.  Digest `i` of a
record covers `sequence = first_seq + i`, so deletion, loss and
reordering within an epoch of a flow are detectable (the "ability to
detect deletion, loss, or reordering" that
[@?I-D.ietf-mboned-multicast-security] Section 2.3 requires), and no
mode of this document delivers an unauthenticated datagram
(Section 2.4.4 of that document).  A lost signed record is covered by its twin, at most
`maxAuthDelayMs / 2` later, so a held datagram waits at most that
plus the burst that removed the record.  The replay floor of 64
records below `highest_mseq` tolerates reordering of records on the
manifest port by up to 63 windows, which is also the bound
(#sender-behavior) places on the twin's lag; a record reordered
further is dropped, and its window is lost unless its other copy
arrived in time.

A receiver that pins keys is exposed to nothing the metadata source
can do beyond that session's data and the state that (#state) bounds
by local policy: a `minEpoch` raise, a `streamId` change or a changed
`port`, `manifestPort` or context source makes genuine records fail,
`maxBitrate`, `maxAuthDelayMs` and `manifestTimerMs` resize its hold
queue and pending table, and a changed `(S, G)` is a join its
metadata source authorized, but none of them lets it admit a datagram
the sender did not emit; a receiver that does not pin is exposed to
the metadata source as to the sender, which is why a profile fixes
how the metadata is authenticated ((#flow-parameters),
(#fetching-the-document)).

The hold queue and its consume-on-admission rule descend from AMBI
([@?I-D.ietf-mboned-ambi] Section 3.2): a `(digest, sequence)` entry
is consumed by one admission, and a copy of an admitted datagram that
arrives while its digest is recorded as admitted, for
`maxAuthDelayMs` after the admission, is dropped rather than held
(steps 1 and 2 of (#processing)).  The hold-down of that section,
which keeps a consumed digest from being re-learned for the same
sequence number from a later manifest, is replaced by the rule that a
window's digests are inserted once, by the first verified copy of the
record that carries them, its twin being dropped as already verified
(step 1).  The hold times are cut from the default hold times its
Section 3.2.1 recommends, 2 s for data packets and 10 s for packet
digests, to `maxAuthDelayMs` for datagrams (200 ms at the default)
and `maxAuthDelayMs + 2 x manifestTimerMs` for digests (240 ms at the
defaults).

## Sender Responsibilities

For a receiver that pins keys, the signing key is the flow's only
long-term secret: a sender that loses it to an attacker has given
that attacker the flow until the key is removed from the metadata and
every receiver has re-fetched or been re-provisioned, so a sender
SHOULD keep a successor key published ahead of need
((#key-rotation-and-re-fetch)) and remove a retired key promptly.
The key that replaces a compromised one MUST carry a `kid` that no
earlier key of the key set has carried: a receiver that pins keys
keeps across sessions the highest `epoch` it has verified under each
pinned `kid` ((#receiver-behavior)), an attacker holding the key can
have raised that floor under the old `kid` past every epoch the
sender will use (the newest key's range has no upper bound,
(#flow-parameters)), and a replacement under the same `kid` would be
dropped at join by every such receiver.
For a receiver that takes its keys from the well-known document there
is a second one, the private key of the TLS certificate for `S`, or
whatever else authenticates the metadata channel a profile uses: its
compromise lets an attacker publish keys of its own to every such
receiver ((#trust-in-the-well-known-document)), so the sender guards
it as it guards the signing key.  A sender MUST NOT reuse an epoch
under a `kid` ((#keys-epochs-and-sequence-numbers)), which requires
it to keep the
last epoch used under each `kid` across restarts, or to start under a
new `kid` after a restart whose state is lost; an epoch reused under a
`kid` reopens the windows of its first use to replay at a receiver
that joins during the reuse: every one of them at a receiver that
skips the freshness check of (#clocks), and those emitted within the
tolerance of step 1 of (#processing) at one that checks it.  A sender
whose clock is off by more than the tolerance of (#receiver-behavior)
makes its flow unverifiable to receivers that check freshness
((#manifest-record)).

## The Trailer Scheme

`ed25519-trailer-1` costs a receiver one signature verification per
datagram, so every injected datagram that passes the replay window
costs a verification: on a flow where any host can send to the group,
or where `S` can be spoofed, the receiver's CPU is the attacker's to
spend, which is why a receiver MAY refuse the scheme above 10 Mbit/s
and why it is not mandatory ((#the-ed25519-trailer-1-scheme)).  A
receiver MAY also bound the verifications it performs per second on
such a flow by local policy, the limit on authentication checks per
time unit that [@?RFC6584] Section 7.1 recommends once the datagrams
failing the check exceed a threshold, dropping genuine datagrams
while the bound binds; the manifest scheme needs no such bound beyond
the budget of step 1 of (#processing), since one verification admits
up to 37 datagrams.  The scheme's signed message binds `S`, `G`,
`port`, `epoch` and `seq` but not `streamId`, and carries no
domain-separation prefix: a datagram cannot be moved to another flow,
epoch or position, and the scheme has no generation in the sense of
(#conventions-and-terminology), since a flow using it declares no
`streamId` ((#flow-parameters)); a sender restart is marked by `epoch`
alone ((#keys-epochs-and-sequence-numbers)).  What keeps a datagram
emitted before a restart out of the flow after it is `epoch` and `seq`
in the signed message: the receiver drops a datagram of an epoch below
the current one and one whose `seq` is below the window or already
seen within it, and (#keys-epochs-and-sequence-numbers) forbids a
sender to reuse an epoch under a `kid` across restarts, so a replayed
datagram of an earlier epoch is admitted only at join, or on the
return to the join state of (#the-ed25519-trailer-1-scheme), before a
datagram of a later epoch has verified (below); a sender that reused
an epoch under a `kid` across restarts would let the earlier datagrams
verify at the positions the window has not yet seen and, with a `seq`
above the right edge, move the window past the genuine datagrams that
follow, which the receiver then drops.  A key used under any other scheme or
protocol is not separated from that use.  That is a known limitation
of the scheme as
(#the-ed25519-trailer-1-scheme) defines it, which the author may
change in a later revision of this document.  The scheme carries no
emission time and its metadata no `minEpoch`, so at join a receiver
is exposed to replay of an earlier epoch under a still-listed key
until it verifies a datagram of a later epoch, and to replay of the
current epoch's earlier datagrams, each verifying as genuine, until a
later datagram of that epoch verifies and moves the window's right
edge past them, after which a replay 1024 or more below that edge,
or already seen inside the window, is dropped
((#the-ed25519-trailer-1-scheme)); removing retired keys promptly
bounds the first exposure to the current key's epochs.

## Trust in the Well-Known Document

The document is authenticated by the TLS certificate of the host at
`S`, and nothing else: a certificate for `S` issued to an attacker,
or a compromise of the host, lets the attacker substitute keys for
every receiver that does not pin them, which (#threat-model) covers.
A receiver that verifies the certificate against the IP literal
presents no server name in the handshake, so a host that serves
several names must present the certificate for `S` to a client that
sends none ([@!RFC9525] Section 7.4).  The per-origin grant restricts
which pages may join a flow, not who may fetch the document, which is
public; a sender that does not want a flow's keys and parameters
public does not publish them there.  The fetch is itself a unicast
connection to `S`, repeated every metadata lifetime, that gives the
operator of `S` the receiver's address, the time of each request and,
from the Origin header, the page the receiver acts for, and lets an
on-path observer infer the subscription from traffic to a known `S`;
this is the disclosure that [@?I-D.ietf-mboned-dorms] Section 5.2
describes for a DORMS fetch, moved from the DORMS server to the
source itself.  A receiver
that must not disclose this is provisioned out of band instead, or
reaches `S` through a proxy that aggregates many receivers and does
not terminate TLS, so that the certificate check against `S` still
holds; this document specifies neither.  The document directs a
receiver to join `(S, G)`; a
receiver that acts for a page bounds the joins it performs for that
page, since a page could otherwise direct it at many groups and
exhaust the network's join state, the attack that
[@?I-D.ietf-mboned-dorms] Section 4.5 describes.

# IANA Considerations

## Well-Known URI Registration

IANA is requested to register the following in the "Well-Known URIs"
registry, following the template of [@!RFC8615] Section 3.1:

- URI suffix: multicast-receive
- Change controller: IETF
- Specification document(s): this document,
  (#the-well-known-document).
- Status: permanent
- Related information: none.

Pending publication, the author will request a provisional
registration of the same URI suffix through the registry's own
procedure ([@!RFC8615] Section 3.1, under the Specification Required
policy of its Section 5.1), with this Internet-Draft as its
specification document and the author as change controller,
"provisional" being the status its Section 3.1 gives a value not
defined by a Standards Track RFC or other open standard; the
permanent entry above replaces that provisional entry on
publication.

## Multicast Datagram Integrity Schemes Registry

IANA is requested to create a "Multicast Datagram Integrity Schemes"
registry.  Entries are assigned under the Specification Required
policy of [@!RFC8126] Section 4.6.  Each entry has a Value (an
integer from 0 to 255), a Name (the string a flow's metadata carries
as `scheme`, (#flow-parameters)), a Reference and a Note.  The
initial contents are:

| Value | Name | Reference | Note |
|---|---|---|---|
| 0 | | this document | reserved |
| 1 | manifest-ed25519-2 | this document | mandatory to implement |
| 2 | ed25519-trailer-1 | this document | optional, low-rate flows |
| 3 | | | unassigned |
| 4 | | this document | reserved for a TESLA profile |
| 5-255 | | | unassigned |

Value 4 is reserved for a TESLA profile ([@?RFC4082], [@?RFC5776]) and
is not to be assigned until such a profile exists
with an implementation on a receive-only receiver and an
authenticated bound on the receiver's clock, which TESLA requires and
this document does not.

A Name is a string of 1 to 64 characters, each a lowercase ASCII
letter, a digit or a hyphen, beginning with a letter; a receiver
compares it to the `scheme` string of a flow's metadata octet for
octet, with no case folding.  A Note is a short description the
registrant supplies, or "reserved" or "unassigned" for an entry that
has no Name.  The designated expert checks that the specification
defines the scheme completely enough for independent interoperable
implementations, namely its wire format, its key, epoch and replay
rules, and which of the parameters of (#flow-parameters) its metadata
carries; that a receiver using the scheme admits no datagram before
authenticating it ((#receiver-behavior)); and that the Name is not
already assigned and is not confusable with an assigned Name.

## Hash Algorithm Identifiers

This document creates no registry of hash algorithms.  `hash_alg`
values are Suite IDs of the Named Information Hash Algorithm Registry
([@!RFC6920] Section 9.4), which this document does not change; a
new 256-bit suite is registered there under that registry's own
policy.

{backmatter}

<reference anchor='MOQ-MULTICAST'>
  <front>
    <title>Multicast Delivery and Endpoint Discovery for Media over QUIC</title>
    <author initials='O.' surname='Ramadan' fullname='Omar Ramadan'>
      <organization>Blockcast</organization>
    </author>
    <date year='2026' month='October' day='26'/>
  </front>
  <seriesInfo name='Internet-Draft' value='draft-ramadan-moq-multicast-01'/>
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

<reference anchor='WHATWG-FETCH' target='https://fetch.spec.whatwg.org/'>
  <front>
    <title>Fetch Living Standard</title>
    <author>
      <organization>WHATWG</organization>
    </author>
    <date/>
  </front>
</reference>

# Test Vectors

This appendix is informative.  It gives one worked example with
`hash_alg` 1 (sha-256, (#hash-algorithms)): one flow, one key, two
datagrams and one signed record with `count` 2; its twin is
byte-identical.  The values are those of [@?MOQ-MULTICAST]
Appendix A, so the two documents verify the same bytes.  `ctx` there
is the value that profile derives from its MoQ catalog for the flow
((#signature-context-binding)); this document treats it as 32 opaque
octets, and a record carrying any other 32 octets in that field, 32
zero octets included, is formed, signed and verified by the same
rules.  Octet strings are hexadecimal, the IPv4 addresses dotted
decimal and other integers decimal unless prefixed 0x; the Ed25519
secret seed is included only so the vectors are reproducible.

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
ctx                 : fe68177dd329ee6fdd668cb43ebdeb6d
                      2e4c2ae351fd25050ab68dd98af19214
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

The public key above, base64url-encoded without padding, is the
`publicKey` of the example in (#the-well-known-document).

# Relationship to AMBI, ALTA, DORMS and MC_INTEGRITY

This appendix is informative.  It places this document beside the
work it descends from, in terms of what each document says; it makes
no claim about what those documents' authors intend.

**AMBI** ([@?I-D.ietf-mboned-ambi]).  The digest of (#digest) is the
AMBI pseudoheader of its Section 3.4.2, with the same field layout,
and the hold queue and consume-on-admission rule of
(#receiver-behavior) are those of its Section 3.2.  Two things
differ.  AMBI's Sections 3.4.2.1, 3.4.2.2, 3.4.2.6 and 3.4.2.7 take
the addresses and ports from the packet on the wire; this document
takes them from the flow's metadata, so that one digest verifies on
whatever carrier delivers the datagram.  AMBI's Section 3.3 manifest
carries a stream identifier, a manifest sequence number, a first
packet sequence number, an extensible TLV space (its Section 3.3.1.6)
and digests, but no signature, and relies on its transport
(Section 4.1: any authenticating transport; Sections 4.2 to 4.4:
HTTPS, TLS and DTLS, all unicast) for authenticity; its Section 2.1.1
admits a protocol that signs manifests and delivers them over a
multicast transport as a manifest delivery to be defined elsewhere,
and this document's record is that delivery, defined as a separate
signed record rather than an AMBI TLV so that it is a fixed layout,
verified before any parsing and carried on the flow's own (S, G).
AMBI's Sections 3.3.1.2
and 4.4 provide loss tolerance by overlapping successive manifests;
this document uses non-overlapping windows and a byte-identical twin
instead, so that a window's digests are inserted once and the replay
floor and consume-once rule interact with nothing.  AMBI names its
hash algorithm in its YANG model; this document carries a Named
Information Suite ID in the signed record.

**ALTA** (Asymmetric Loss-Tolerant Authentication,
[@?I-D.krose-mboned-alta]).  AMBI's Section 4.1 reserves a place for
ALTA, which authenticates a multicast stream with an
acyclic graph of message authentication codes (MACs) and regularly
paced digital signatures.  This document instead signs each window
once and relies on the twin for loss: one signature per 37 datagrams,
no MAC chain and no dependency between windows.

**DORMS** ([@?I-D.ietf-mboned-dorms]).  DORMS discovers a RESTCONF
server for an (S, G) through reverse DNS (its Section 2.2) and serves
YANG-modelled metadata from it, with a per-origin CORS grant that its
Section 2.3.5 recommends and its Section 4.5 relies on against
unauthorized pages.  The well-known document of
(#the-well-known-document) carries the same kind of metadata and the
same grant from the source address itself under a certificate for
that address, with no DNS hop, and treats a wildcard grant as no
grant.  DORMS's Section 2.2 lets a client with another way of finding
a trusted server skip the DNS step, so a DORMS record remains one way
to deliver the parameters of (#flow-parameters).

**MC_INTEGRITY** ([@?I-D.jholland-quic-multicast]).  The multicast
extension for QUIC carries packet hashes in MC_INTEGRITY frames sent
from server to client (its Section 10.5), either on the client's
unicast QUIC connection or on a multicast channel whose packets an
earlier frame verified, a Merkle tree whose root the unicast
connection carries (its Section 4.5), each a hash of the encrypted
channel packet (its Section 7.1), and names its hash algorithm from
the same Named Information Hash Algorithm Registry this document
uses.  A receiver
with no per-receiver QUIC connection, one behind an AMT relay, in a
broadcast or in a browser without one, cannot anchor that tree,
which is the case this document serves; the two carry different
digests over different bytes and cannot share them, so they
complement each other by deployment, not by format.

{numbered="false"}
# Acknowledgments

The digest pseudoheader, the hold queue and the consume-on-admission
rule of this document are those of AMBI, and the per-origin grant of
the well-known document descends from DORMS; the threat model this
document answers is that of the MBONED multicast security draft.  The
author thanks the authors of those documents, Jake Holland, Kyle Rose
and Max Franke, for the work this builds on.  No endorsement of this
document by them is implied.
