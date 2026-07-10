# Intrinsic Fragment Coordinate reassembly — draft claims (for review)

**Status:** draft claim language for review — *not* a filed application. Companion
/ continuation to `patent/APPLICATION-1-FEC-METHODS.md`.

**Novelty scoping (read first).** ISO/IEC 23008-1:2023 already defines the
*descriptors* — the timed-MFU DU header (§9.3.2.3: `movie_fragment_sequence_number`,
`sample_number`, `offset`), the non-timed `Item_ID`, and the Generic File Delivery
`start_offset` (§9.3.3) — and offset-based reassembly within each. These are prior
art and the claims below do **not** read on them in isolation. The claimed advance
is the **reconciliation**: using an intrinsic, content-carried coordinate, *in
precedence over a transport-assigned object identifier*, to order and de-duplicate
fragments **including FEC-recovered and multi-path-combined fragments**, over a
publish/subscribe plus multicast transport. Broadcast MMT has no MoQ Object IDs and
no unicast/multicast FEC combining, so ISO does not anticipate this step. The claim
set is the application-object-layer companion to APPLICATION-1's FEC-symbol-layer
`(SBN, ESI)` claims.

**Distinction over the nearest MoQ prior art (draft-ietf-moq-loc-03 §4.5).** The
closest reference within MoQ is draft-ietf-moq-loc-03 §4.5, whose worked example (non-normative, dyadic-framerate layered tracks) orders decode
as timestamp-primary with `ObjectID * multiplier + offset` as the fallback ordering
key — i.e., the same *precedence shape* the claims rely on (an intrinsic-ish
ordering key used in place of raw arrival order). The claims are framed as
**extending**, not contradicting, that pattern. LOC §4.5 applies only to **whole,
in-order, single-path frames**: LOC objects are never fragmented, and LOC defines
no FEC recovery, no multi-path combining, and no relay re-sequencing. The claimed
method operates precisely in the regime LOC does not reach — **fragmented**
(sub-frame) objects, **FEC-recovered** fragments that carry no transport-assigned
identifier (step (b)/(c)), and **multi-path-combined** fragments where the
`ObjectID`-derived key is path-relative and unreliable (Claim 6). In all three the
intrinsic byte offset is the only key that survives, so LOC's whole-frame
`ObjectID`-offset fallback does not anticipate step (c). draft-ietf-moq-msf §6.1 is
adjacent only — it marks intentional publisher-restart numbering discontinuities (loss-independent, nothing to recover) but performs no
reassembly. None of draft-michel-quic-fec, draft-zheng-quic-fec-extension, or RFC 6363
FECFRAME define object reassembly by an intrinsic content coordinate; they protect
the QUIC/symbol layer beneath this method.

---

## Independent Claim 1 (method)

A method for reassembling a fragmented application object delivered to a receiver
over (i) a publish/subscribe transport that assigns to delivered objects an
extrinsic, transport-assigned delivery identifier, and (ii) at least one further
delivery path comprising multicast delivery protected by forward error correction
(FEC), the method comprising:

(a) receiving a plurality of fragments of the application object, each fragment
    carrying an intrinsic descriptor comprising an object identity and a byte
    offset of the fragment within the application object, the intrinsic descriptor
    being independent of the transport-assigned delivery identifier;

(b) recovering at least one missing fragment of the application object by FEC
    decoding, the recovered fragment lacking a transport-assigned delivery
    identifier;

(c) ordering the fragments, including the FEC-recovered fragment, by the byte
    offset of the intrinsic descriptor, in precedence over the transport-assigned
    delivery identifier;

(d) de-duplicating the fragments by the intrinsic descriptor, such that a fragment
    whose object identity and byte offset have already been incorporated is
    discarded irrespective of the delivery path on which it arrived;

(e) determining completion of the application object by contiguous byte coverage;
    and

(f) outputting the reassembled application object to a container or application
    parser;

whereby the application object is reassembled deterministically irrespective of
fragment arrival order, delivery path, or FEC recovery.

## Dependent Claim 2

The method of Claim 1, wherein the intrinsic descriptor is carried in a media data
unit header of an MPEG Media Transport (MMT) timed-media media fragment unit and
comprises a movie fragment sequence number, a sample number, and an offset within
the referenced sample.

## Dependent Claim 3

The method of Claim 1, wherein the intrinsic descriptor is carried in a media data
unit header of an MMT non-timed media fragment unit and comprises an item
identifier.

## Dependent Claim 4

The method of Claim 1, wherein the intrinsic descriptor is carried in a generic
file delivery payload header and comprises a transport object identifier and a
start offset.

## Dependent Claim 5

The method of Claim 1, wherein the application object is not an MMT object and the
intrinsic descriptor is carried in an extension header of a transport object of the
publish/subscribe transport.

## Dependent Claim 6

The method of Claim 1, wherein the further delivery path and the publish/subscribe
transport deliver the same application object, and de-duplicating in step (d)
comprises discarding a fragment combined from a second delivery path whose intrinsic
descriptor matches that of a fragment already incorporated from a first delivery
path.

## Dependent Claim 7

The method of Claim 6, wherein de-duplicating further comprises comparing a content
hash carried with, or computed over, each fragment.

## Dependent Claim 8

The method of Claim 1, further comprising gating a start of media decoding on the
completion — including completion by FEC recovery — of an application object that
is a random access point.

## Dependent Claim 9

The method of Claim 1, further comprising prioritising FEC recovery or buffer
retention of fragments according to a priority value or a dependency count carried
in, or associated with, the intrinsic descriptor.

## Dependent Claim 10

The method of Claim 1, further comprising discarding an incompletely-covered
application object upon expiry of a deadline derived from a FEC interleave depth or
a frame duration, thereby bounding reassembly memory.

## Dependent Claim 11

The method of Claim 1, wherein the FEC decoding of step (b) operates on source
symbols addressed by intrinsic FEC coordinates derived as in the method of
APPLICATION-1 Claim 1, such that both the FEC symbol layer and the
application-object reassembly layer order and de-duplicate by intrinsic,
transport-independent coordinates.

## Independent Claim 12 (apparatus)

A receiver comprising one or more processors and a memory storing instructions
that, when executed by the one or more processors, cause the receiver to perform
the method of any of Claims 1 to 11.

## Independent Claim 13 (medium)

A non-transitory computer-readable medium storing instructions that, when executed
by one or more processors, cause the one or more processors to perform the method
of any of Claims 1 to 11.

---

## Notes for the drafter

- Claim 1 step (c) "in precedence over the transport-assigned delivery identifier"
  is the crux distinguishing over ISO/IEC 23008-1 (which has no competing transport
  identifier) and over plain MoQ (which orders by Object ID). Step (c) alone does not distinguish over the nearest
  MoQ reference, **draft-ietf-moq-loc-03 §4.5**:
  LOC §4.5 already pairs a primary ordering key with an `ObjectID`-derived fallback,
  but only for whole, in-order, single-path frames. The distinguishing limitations
  are therefore the *fragmented + FEC-recovered + multi-path* context — step (b)
  (recovered fragment lacking a delivery identifier) and Claim 6 (multi-path
  combining) — which place the method outside LOC's regime. Keep step (c) in the
  independent claim and lean on (b)/Claim 6 when arguing non-anticipation over LOC.
  The prose "Distinction over the nearest MoQ prior art" block above is intended to
  carry this argument without rewording the claim limitations.
- Claims 2–5 enumerate the descriptor encodings (MMT timed / non-timed / GFD /
  generic extension header). 2–4 are ISO-sourced encodings; 5 is the generalization
  that extends reach to JSON/file/arbitrary objects — likely the most commercially
  important dependent claim.
- Claim 11 is the explicit tie to APPLICATION-1; consider whether to file as a
  continuation-in-part of APPLICATION-1 or a standalone application that references
  it.
- Consider a method claim variant where step (b) is omitted (no FEC) but multi-path
  combining remains, to cover the unicast-multicast dedup case without FEC.
