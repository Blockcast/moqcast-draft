# Intrinsic Fragment Coordinate (IFC) — design note

**Status:** design sketch (not a submission draft). Source material for an
extensions-draft section and a patent continuation.
**Renamed** from "Generic Fragment Descriptor" — *GFD* collides with MMT's
**Generic File Delivery** mode (ISO/IEC 23008-1 §9.3.3).

Companions: `draft-ramadan-moq-mmt-00.md` (§"MFU Fragmentation"),
`draft-ramadan-moq-fec-00.md` (`(SBN, ESI)` symbol coords),
`patent/APPLICATION-1-FEC-METHODS.md`, and **ISO/IEC 23008-1:2023** (verified
ground truth — see §2).

## 1. Problem

Reassembly of a *fragmented* application object must survive transport disorder,
loss, FEC recovery, multi-path combining, and relay re-sequencing — without
coupling the reassembly layer to a specific media format. We want one reassembler
that works for MMT timed media, MMT non-timed items, generic files, and future
object types, over a MoQ + multicast + FEC transport.

## 2. ISO/IEC 23008-1 ground truth (verified)

MMT **already** defines intrinsic, content-carried fragment coordinates — three
of them, one per object class. IFC is the *unification* of these; it does not
invent new descriptors.

| MMT object class | Where | Object key | Intrinsic offset/order | Extras |
|---|---|---|---|---|
| **Timed media MFU** | §9.3.2.3, Fig 12 (T=1) | `MPU_sequence_number` + `movie_fragment_sequence_number` + `sample_number` | `offset` (within the referenced sample) | `subsample_priority`, `dependency_counter` |
| **Non-timed media MFU** | §9.3.2.3, Fig 13 (T=0) | `Item_ID` | (item-scoped) | `subsample_priority`, `dependency_counter` |
| **Generic File Delivery** | §9.3.3 / §9.3.3.4 | `packet_id` (Asset) + `TOI` | `start_offset` (48-bit, "location of payload in the object") | `CodePoint` |

Fragmentation framing is also ISO-native: `f_i` (00 complete / 01 first / 10
mid / 11 last), `aggregation_flag`, `fragment_counter` (§9.3.2.3). The MMT draft's
FI=1/2/3 reassembly is a direct restatement of this.

**Consequence for `libmmt` #78:** parsing `movie_fragment_sequence_number` /
`sample_number` / `offset` is *exactly* §9.3.2.3 — **spec-conformant, not novel**.
That's the right outcome for the implementation; it just means the *descriptors*
carry no patent weight (see §9).

## 3. Principle

Order and dedup fragments by **intrinsic** (content-carried) coordinates — never
by **extrinsic** (transport-assigned) delivery order. This mirrors the FEC layer,
which already addresses symbols by `(SBN, ESI)` from `SS_ID`, not by arrival. IFC
applies the same idea at the application-object boundary. Extrinsic ordering (MoQ
Object ID) remains the **mandatory floor** for opaque/unfragmented objects.

## 4. Layer position

```
+---------------------------------------------------------------+
| Container / application parsing                                |
|   MMT MPU/MFU, ISOBMFF, DASH seg, JSON, file                  |
+---------------------------------------------------------------+
| Object reassembly   ◄── consumes the Intrinsic Fragment Coordinate
|   orders, dedups, completes fragmented objects (media-agnostic)|
+---------------------------------------------------------------+
| FEC / recovery      ── intrinsic (SBN, ESI) symbol coordinates |
+---------------------------------------------------------------+
| Transport: MoQ objects / multicast UDP / datagrams            |
|   delivers bytes; assigns EXTRINSIC Object IDs                 |
+---------------------------------------------------------------+
```

IFC sits **above FEC** (reassembles recovered source bytes) and **below container
parsing** (hands up a complete, ordered object). The container layer never sees
loss or ordering.

## 5. The coordinate (abstract; MMT supplies the concrete encodings)

| Field | Meaning | MMT source |
|---|---|---|
| `objectKey` | transport-independent identity of the logical object | timed: `MPU_seq:MFSN:sample` · non-timed: `Item_ID` · file: `packet_id:TOI` |
| `fragmentOffset` | byte offset within the object | timed: DU `offset` · file: `start_offset` |
| completion | `objectTotalLength` or last-fragment (`f_i=11`) | `f_i` / `fragment_counter` |
| `rap` | object is a random-access point (decode-gate) | MPU first AU = SAP (§6.4); RAP packets carry full headers (§9) |
| `priority` | recovery/decode precedence | `subsample_priority`, `priority_id`, `transmission_priority` |
| `dependency` | DUs depending on this one | `dependency_counter` |
| `contentHash` *(opt)* | path-independent dedup/integrity | — (transport overlay) |

**Invariants**
- Order = ascending `fragmentOffset` (ignores arrival order and Object ID).
- Dedup = `(objectKey, fragmentOffset)` (and/or `contentHash`).
- Completion = contiguous `[0, total)` coverage.
- Bounded memory = discard incomplete objects on a derived deadline.

## 6. RAP / I-frame handling (per ISO)

- An MPU begins at a **SAP** (§6.4): the first access unit of an MPU is a
  random-access point. So keyframe boundaries = MPU/Group boundaries.
- RAP is signalled by **full-header packets** (§9): the reassembler's `rap` bit
  derives from this, not from a payload bit alone.
- I-frames are **high `subsample_priority` and dependency roots** (high
  `dependency_counter`). IFC surfaces `rap` + `priority` + `dependency` so the
  receiver can: (a) **gate decode start** on a recovered RAP (patent Emb. 3,
  state 402a "keyframe gate"); (b) **prioritize FEC recovery** of RAP/high-priority
  fragments; (c) drop low-priority dependents first under pressure.

## 7. Precedence model (intrinsic-first, extrinsic-floor)

1. Fragments carry an IFC → reassemble by `fragmentOffset`, dedup by
   `(objectKey, offset)`. Robust on FEC / multi-path / relay.
2. No IFC (opaque payload) → fall back to transport **Object ID** order.
3. Whole/unfragmented object → no reassembly; Object ID for delivery + dedup.

This is the shape already in `libmmt mfu-reassembler.ts` (offset-mode when sample
identity present, else counter), generalized off MMT.

## 8. Draft framing (extensions draft, not lean core)

Section: **"Self-Describing Fragment Reassembly."**
- Normative: a receiver MAY use an MMT-native intrinsic coordinate (timed-MFU
  `offset`, GFD `start_offset`, or `Item_ID`), when present, as the authoritative
  reassembly order, **taking precedence over the MoQ Object ID**; it MUST fall
  back to Object-ID order when absent.
- Cite ISO/IEC 23008-1 §9.3.2.3 (DU headers) and §9.3.3 (GFD `start_offset`) as
  the field source — the draft only specifies the **MoQ mapping + precedence rule**,
  not new fields.
- Updates `draft-ramadan-moq-mmt-00` §"MFU Fragmentation": its "order by Object ID"
  becomes the *floor*, with intrinsic-offset precedence on top. Lands in the
  **extensions** draft per the lean-core/low-exposure sequencing.

## 9. Patent-claim outline (re-scoped above ISO prior art)

ISO already defines the descriptors and offset-reassembly (§2), so claims **must
not** read on "use sample/offset/Item_ID/start_offset to reassemble." The novelty
is the **transport reconciliation on a pub/sub + multicast + FEC path** — the
up-layer companion to `APPLICATION-1`'s `(SBN, ESI)` claims.

- **Independent claim.** A method for reassembling a fragmented application object
  delivered over a publish/subscribe transport that assigns extrinsic per-object
  delivery identifiers (e.g., MoQ Object IDs) and over one or more additional paths
  including multicast with forward error correction, comprising: recovering missing
  fragments via FEC such that recovered fragments lack a transport-assigned delivery
  identifier; ordering and deduplicating fragments — including FEC-recovered and
  multi-path-delivered fragments — by an **intrinsic content-carried coordinate**
  (object identity + byte offset) **in precedence over** the transport-assigned
  delivery identifier; signalling completion by contiguous byte coverage; thereby
  reassembling deterministically irrespective of arrival order, path, or recovery.
- **Dependent claims.**
  - intrinsic coordinate sourced from an MMT timed-MFU DU header (`movie_fragment_sequence_number`/`sample_number`/`offset`);
  - …from an MMT non-timed `Item_ID`;
  - …from an MMT Generic File Delivery `start_offset`/`TOI`;
  - …from a transport object **extension header** for non-MMT payloads (the generalization);
  - dedup of multi-path fragments by content hash;
  - **gating decode start** on a FEC-recovered random-access fragment;
  - **prioritizing FEC recovery** by `subsample_priority`/`dependency_counter`;
  - bounded-memory discard on a derived deadline;
  - composition with `(SBN, ESI)` symbol addressing of `APPLICATION-1`.

Positioning: broader and more standards-essential than MMT-only, because the
claimed step is the *intrinsic-over-extrinsic reconciliation across FEC/multi-path*,
which MMT-over-broadcast never needed (no MoQ Object ID, no unicast/multicast FEC
combining) and which ISO therefore does not anticipate. The nearest in-MoQ
reference, **draft-ietf-moq-loc-03 §4.5**, establishes a timestamp-primary/`ObjectID`-derived-fallback (layer-interleave constants, not byte offsets)
*precedence pattern* but only for whole, in-order, single-path frames (no
fragmentation, FEC, or multi-path); the claims extend that precedence to the
fragmented + FEC-recovered + multi-path regime rather than reading on it (see
§10.1).

## 10. Relationship to existing work

- **Conforms to** ISO/IEC 23008-1 §9.3.2 / §9.3.3 (uses its descriptors verbatim).
- **Extends** `draft-ramadan-moq-mmt-00` §"MFU Fragmentation" (adds intrinsic
  precedence over MoQ Object ID; generalizes off MMT).
- **Aligns with** the FEC layer's `(SBN, ESI)` intrinsic addressing — IFC is the
  same idea one layer up.
- **Distinct from** `APPLICATION-1` claims (FEC-*symbol* dedup); IFC is
  application-*object* reassembly over the FEC/MoQ transport → candidate continuation.

### 10.1 Relationship to existing MoQ drafts (nearest prior art)

The IFC precedence model (§7) is **not without precedent in MoQ** — and saying so
sharpens, not weakens, the positioning. The nearest prior art is
**draft-ietf-moq-loc-03 §4.5**, whose worked example (non-normative, dyadic-framerate layered tracks) orders decode as **timestamp primary**
with **`ObjectID * multiplier + offset`** as the fallback ordering key. That is
the *same precedence shape* as IFC: an intrinsic-ish ordering key the receiver
uses instead of raw arrival order. The distinction is **regime, not shape**:

- **draft-ietf-moq-loc-03 §4.5** — the precedence pattern, but only for **whole
  frames**. LOC objects are never fragmented; there is no FEC recovery, no
  multi-path combining, and no relay re-sequencing in its scope. So LOC
  establishes the timestamp/ObjectID precedence for in-order, single-path,
  whole-frame delivery. **IFC generalizes that precedence to the fragmented +
  FEC-recovered + multi-path regime**: (a) sub-frame MFUs/DUs rather than whole
  frames; (b) FEC-recovered fragments, which carry no transport sequence yet must
  slot into the right intrinsic position; (c) multi-path / relay-re-sequenced
  delivery, where the extrinsic Object ID is unreliable. The intrinsic byte-offset
  (or sample/DU) coordinate is what survives all three — exactly where LOC's
  `ObjectID`-derived fallback cannot reach.
- **draft-ietf-moq-msf §6.1** — *adjacent but not reassembly*. MSF §6.1's Prior Group ID
  Gap Extension marks **intentional numbering discontinuities** (publisher
  restart — nothing was transmitted, so there is nothing to recover); IFC
  addresses **loss-induced** gaps and closes them (FEC + offset reassembly)
  rather than only marking them.
- **MoQ/QUIC FEC** (draft-michel-quic-fec, draft-zheng-quic-fec-extension) and **RFC 6363
  FECFRAME** operate at the **QUIC/symbol layer only**. None define object
  reassembly by an intrinsic content coordinate; IFC sits one layer above them
  (§4), consuming recovered source bytes.

In short: IFC = the LOC §4.5 timestamp/ObjectID precedence pattern **extended** to
fragmented, recovered, and multi-path objects — not a wholly novel idea with no
precedent.
