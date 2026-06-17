<!--
Draft section prose for review — "Self-Describing Fragment Reassembly".
Intended to slot into the extensions draft (or draft-ramadan-moq-mmt) after
the "MFU Fragmentation (Raw Passthrough)" section. RFC 2119 keywords. Cross
references shown as {{...}} are to be wired to the host draft's sections.
Not yet integrated into a submission draft.
-->

# Self-Describing Fragment Reassembly

## Motivation

{{mfu-fragmentation}} reassembles the fragments of a Media Fragment Unit (MFU)
in reconstructed Object ID order ({{object-identifier-reconstruction}}). The
Object ID is assigned by the transport. It is authoritative on a reliable,
in-order delivery path, but it is not authoritative on the paths this mapping
exists to serve:

- A fragment recovered by FEC ({{fec-integration}}) is reconstructed below the
  MoQ object layer and carries no transport-assigned Object ID; its position in
  the object must be re-derived.
- When the same content is combined from more than one path — for example a
  reliable unicast subscription and a multicast group — Object IDs are
  path-relative and cannot serve as a common ordering or de-duplication key.
- A publisher MAY emit a constant zero Object ID delta and rely on a relay to
  re-sequence on egress ({{object-identifier-reconstruction}}); end to end the
  Object ID is then not a stable content identifier.

MMT data units already carry an intrinsic, content-derived coordinate that is
invariant to all of the above. A receiver that treats that coordinate as the
reassembly authority — falling back to Object ID order only when it is absent —
reassembles deterministically irrespective of arrival order, delivery path, or
FEC recovery.

## Intrinsic Fragment Coordinate

For each class of MMT object, ISO/IEC 23008-1:2023 defines an intrinsic
coordinate comprising a transport-independent object identity and a byte
offset. No addition to the MoQ object encoding is required; the fields are
already present in the data unit (DU) header or the payload header.

| Object class            | Object identity                                                       | Byte offset    | Reference            |
|-------------------------|-----------------------------------------------------------------------|----------------|----------------------|
| Timed-media MFU         | MPU_sequence_number + movie_fragment_sequence_number + sample_number  | offset (in the referenced sample) | 23008-1 9.3.2.3 |
| Non-timed media MFU     | Item_ID                                                               | item-scoped    | 23008-1 9.3.2.3      |
| Generic File Delivery   | packet_id + Transport Object Identifier (TOI)                         | start_offset   | 23008-1 9.3.3        |

An object whose fragments carry such a coordinate is said to be
**self-describing**.

## Receiver Behaviour

A receiver reassembling a fragmented object:

1. If every fragment of the object carries an intrinsic byte offset, the
   receiver SHOULD order the fragments by ascending byte offset, and MUST treat
   that order as authoritative in precedence over reconstructed Object ID order.
2. If the intrinsic coordinate is absent, the receiver MUST fall back to
   reconstructed Object ID order ({{object-identifier-reconstruction}}).
3. The receiver MUST de-duplicate fragments by the pair (object identity, byte
   offset). A fragment whose coordinate has already been incorporated MUST be
   discarded, including a duplicate that arrives on a different path or that is
   produced by FEC recovery.
4. The receiver MUST determine completion by contiguous byte coverage of the
   object and MUST NOT emit a partially-covered object to the container or
   application parser.
5. The receiver MUST bound the memory used for in-flight reassembly and MUST
   discard an object whose coverage does not complete within a deadline derived
   from the FEC interleave depth or the frame duration, rather than buffer
   without limit (consistent with {{mfu-fragmentation}}).

## Random Access and Priority

An MPU begins at a Stream Access Point: the first access unit of an MPU is a
random access point (RAP) (ISO/IEC 23008-1:2023, 6.4). Accordingly a receiver:

- SHOULD gate the start of media decoding on the availability of a complete RAP
  object, including a RAP object completed by FEC recovery; and
- SHOULD prioritise FEC recovery and retention of fragments that carry a higher
  subsample_priority or a higher dependency_counter (ISO/IEC 23008-1:2023,
  9.3.2.3), since these are decode-order roots upon which other access units
  depend.

## Relationship to Object Identifier Reassembly

This section refines {{mfu-fragmentation}}. Reconstructed Object ID order
remains the mandatory reassembly order for objects that have no intrinsic
coordinate — for example opaque or unfragmented objects — and is the universal
fallback. Where an intrinsic coordinate is present it takes precedence, because
it is invariant to the transport conditions (loss, multi-path combining, FEC
recovery, and relay re-sequencing) under which Object ID order is not reliable.

The mechanism is not specific to MMT: the same receiver procedure applies to any
fragmented application object whose fragments carry an object identity and a byte
offset, whether sourced from an MMT DU header, an MMT Generic File Delivery
payload header, or a transport object extension header defined for a non-MMT
payload.
