# FEC Extensions Material (removed from draft-ramadan-moq-fec-00 for IETF submission)

Verbatim sections removed 2026-06-11 to keep the IETF -00 to the
interop-essential core. This material is claim-bearing (patent
APPLICATION-1-FEC-METHODS) and/or optimization guidance; it returns
post-filing as draft-ramadan-moq-fec-extensions. Section numbers are
as of commit prior to removal.

---

### 8.5. Clock-Synchronized Block Identifiers

When multiple encoders share an FEC block namespace (hot standby
failover, simulcast bitrate tiers, or auxiliary streams), the Source
Block Number (SBN) MUST be derived from a shared wall-clock reference
rather than an encoder-local sequential counter.  This ensures that
any encoder producing source symbols for the same content generates
identical block boundaries without direct inter-encoder signaling.

The SBN is derived from UTC wall-clock time as follows:

```
block_duration_ms = K * GOP_duration_ms * D
SBN = floor((ntp_time_ms - epoch_ms) / block_duration_ms)
```

Where:

- **ntp_time_ms**: Current UTC time in milliseconds (NTP epoch)
- **epoch_ms**: Shared session epoch, signaled in the MoQ catalog
  or ISO 23008-1 AL-FEC signaling message
- **block_duration_ms**: Wall-clock span of one FEC source block
- **K**, **D**, **GOP_duration_ms**: As defined in Section 8.3

The corresponding Source FEC Payload ID (SS_ID per ISO 23008-1
Section C.5.2) is:

```
SS_ID = SBN * K + ESI
```

This remains decoupled from the MMTP packet_sequence_number (PSN),
which may restart on encoder failover.  The 4-byte Source FEC Payload
ID appended to each MMTP source packet carries the SS_ID, enabling
receivers to correctly route symbols to FEC blocks regardless of
which encoder produced them.

The epoch MUST be identical across all encoders sharing the namespace.
It MAY be derived from the MoQ catalog session start time or signaled
explicitly via a new `fecEpoch` field in the catalog FEC configuration:

```json
{
  "fec": {
    "sourceSymbols": 32,
    "repairSymbols": 8,
    "interleaveDepth": 4000,
    "fecEpoch": 1713052800000
  }
}
```

Receivers MUST NOT assume that SS_ID values are contiguous across
encoder transitions.  A hot standby encoder joining at time T produces
SBN = floor((T - epoch) / block_duration_ms), which may skip block
numbers if the standby was offline.  Receivers SHOULD treat each
(SBN, ESI) independently and not require sequential SBN progression.


---

### 8.7. Unequal Error Protection for Keyframes

Keyframes (Random Access Points) are disproportionately important:
losing a single keyframe fragment renders all dependent P-frames
undecodable.  When keyframes span multiple FEC blocks (e.g.,
16 fragments across 8 blocks with K=4), any single block failure
prevents keyframe assembly.

Encoders MAY provide Unequal Error Protection (UEP) per RFC 6363
Section 6 using one of these strategies:

1. **Large-K blocks** (RECOMMENDED): Use K >= 32 so that keyframe
   fragments fit within 1-2 FEC blocks.  With P/K >= 25%, a single
   block can tolerate burst loss of up to P symbols.  This is the
   simplest approach and requires no receiver-side changes.

2. **Keyframe FEC overlay**: A SECOND FEC encoder covers only
   keyframe fragments with higher redundancy.  Repair symbols are
   published on a separate MoQ track (e.g., `video/keyframe-repair`).
   The catalog signals the overlay via a second `fec` entry:

   ```json
   {
     "fec": {
       "sourceSymbols": 4,
       "repairSymbols": 2,
       "repairTrack": "video/repair"
     },
     "fecOverlay": {
       "sourceSymbols": 16,
       "repairSymbols": 8,
       "repairTrack": "video/keyframe-repair",
       "scope": "keyframe"
     }
   }
   ```

   Receivers subscribe to both repair tracks.  The base FEC recovers
   P-frame losses with low overhead.  The overlay FEC provides 50%
   redundancy for keyframe fragments across a wider block.

3. **Per-block adaptive P**: The encoder adjusts P per block based
   on the block's content.  Blocks containing keyframe fragments
   (identified by rapFlag) receive more repair symbols than blocks
   containing only P-frames.  SSB_length in the repair header
   (Section 7.1) signals the per-block K; the receiver uses it to
   determine the expected repair count.

Strategy 1 is sufficient for most deployments.  Strategy 2 enables
low-latency P-frame delivery (small K) with high-reliability
keyframe recovery (large K overlay).  Strategy 3 requires encoder
awareness of frame types during FEC block formation.

### 8.8. Keyframe Fragment Alignment with FEC Blocks

Keyframes (IDR/IRAP) produce N MFU fragments where N varies per
scene (typically 8-30 for HD, 30-100 for 4K).  With interleave
depth D, consecutive MMTP packets interleave across D blocks:

```
Keyframe fragments: KF0 KF1 KF2 KF3 KF4 KF5 KF6 KF7 ...
With D=2:           B0  B1  B0  B1  B0  B1  B0  B1
```

Each block receives N/D keyframe fragments.  The keyframe's MFU
cannot be reassembled until ALL D blocks containing its fragments
are recovered.  This creates a reliability dependency:

```
P(keyframe recovered) = P(block recovered) ^ D
```

With 99% per-block recovery and D=4: P(keyframe) = 0.99^4 = 96%.
With D=1 (no interleaving): P(keyframe) = 99%.

**Interleaving tradeoff for keyframes:**

| Depth D | Burst protection | Keyframe reliability (99% block) |
|---------|------------------|----------------------------------|
| D=1     | None             | 99% (1 block)                    |
| D=2     | 2-packet burst   | 98% (2 blocks)                   |
| D=4     | 4-packet burst   | 96% (4 blocks)                   |
| D=8     | 8-packet burst   | 92% (8 blocks)                   |

**CMAF segment alignment**: With 1 FEC block = 1 CMAF segment,
the keyframe spans D segments.  MSE SourceBuffer receives fragments
across multiple `appendBuffer()` calls.  The MFU reassembler
(ISO 23008-1 §8.3.2) must collect all D blocks' fragments before
emitting the keyframe AU to the CMAF assembler.

Encoders SHOULD choose K and D such that:

1. `K >= N_max / D` where N_max is the maximum keyframe fragments
   expected for the configured resolution and codec.
2. The combined constraint `K * D * frameDuration_ms` (block span)
   does not exceed the target latency budget.
3. For CMAF compatibility: `interleaveDepth_ms` equals the target
   CMAF segment duration so each segment is FEC-coherent.

When `D=1` and `K >= N_max`: all keyframe fragments are in a single
FEC block and a single CMAF segment.  This is the most reliable
configuration for keyframe delivery but provides no burst loss
interleaving.  Use the keyframe FEC overlay (Section 8.7 Strategy 2)
to combine burst protection (small K, large D for P-frames) with
keyframe reliability (large K, D=1 overlay for keyframes).


---

### 9.1. Object-Level FEC for High-Resolution Content

Per-packet FEC (ssbg_mode0) ties the FEC block size K to network
latency: K source symbols must be accumulated before recovery can
begin.  For high-resolution codecs (4K AV1, 8K HEVC) where a single
keyframe may produce 100-600 MFU fragments, per-packet FEC requires
impractically large K values (K >= 100) with multi-second block spans.

**Object-level FEC** eliminates this limitation by treating each
semantic media object (keyframe, CMAF segment, GOP) as a single
FEC source block:

```
Per-packet FEC (ssbg_mode0):
  1 MMTP packet = 1 FEC symbol
  K = number of packets per block
  Keyframe (200KB) = 150 symbols → K=150, block span = 20s ❌

Object-level FEC:
  1 MoQ Group = 1 FEC source block
  Source objects = encoding symbols OF the group payload
  Keyframe (200KB) → K=10 symbols of 20KB each → block span = 0 ❌ 
  (symbols sent concurrently, not sequentially)
```

In object-level FEC, the encoder:

1. Collects the complete keyframe (or CMAF segment) payload
2. Applies RaptorQ to the payload as a single transfer object
   (transfer_length = keyframe size, T = payload / K)
3. Publishes K source objects and P repair objects to the MoQ track
4. Each MoQ object within the Group carries one encoding symbol

The receiver:

1. Collects MoQ objects as they arrive (source + repair)
2. When >= K objects received for a Group: decode the full payload
3. Emit the recovered keyframe to the CMAF assembler

This maps directly to MoQ's (Group, Object) model:

```json
{
  "fec": {
    "mode": "object",
    "sourceSymbols": 10,
    "repairSymbols": 5,
    "repairTrack": "video/repair"
  }
}
```

With `mode: "object"`: the Group payload is the FEC transfer object.
Source symbols are the first K objects in the Group.  Repair symbols
are published on the repair track with the same Group ID.  The
receiver needs any K objects out of (K + P) to recover the Group.

**Comparison:**

| Property | Per-packet (ssbg_mode0) | Object-level |
|----------|------------------------|--------------|
| FEC unit | MMTP packet (T bytes) | MoQ Group (variable) |
| Block span | K × D × frameDuration | 0 (concurrent) |
| Keyframe reliability | P(block)^D | P(block)^1 |
| Interleaving | Packet-level (depth D) | Group-level (natural) |
| CMAF alignment | 1 block = 1 segment | 1 group = 1 segment |
| Latency | K-dependent | Object delivery time |
| Best for | Low-latency HD | High-res 4K/8K |

Publishers MAY use per-packet FEC for P-frames (low latency) and
object-level FEC for keyframes (high reliability).  This is a
specialization of the keyframe FEC overlay (Section 8.7 Strategy 2)
where the overlay uses object-level FEC instead of per-packet FEC
with large K.


---

### 11.2. Relay-Generated Repair

Relays MAY generate additional repair symbols for local network conditions.
This is enabled by the fountain code property of RaptorQ, which allows
generation of arbitrary repair symbols from decoded source data.

Use cases for relay-generated repair include:

- Edge relays serving lossy last-mile networks (WiFi, cellular) can increase
  repair overhead beyond what the publisher provides
- Regional relays can adapt FEC parameters to local loss patterns
- Relays can regenerate repair if upstream repair symbols were lost
- IWA home gateways receiving multicast over wired Ethernet can apply
  local FEC repair before redistributing via WebTransport to wireless
  clients, reducing retransmission round trips to the origin

When a relay generates its own repair symbols:

1. The relay MUST successfully decode the source block first
2. Generated repair symbols SHOULD use ESIs that do not conflict with
   publisher-generated repair (e.g., ESI >= K + P_publisher)
3. The relay MAY advertise relay-specific repair via a separate track
   namespace or track path suffix

Security considerations for relay-generated repair:

A compromised relay could inject malicious repair symbols that cause
receivers to reconstruct corrupted source data.  This risk is
elevated on multicast paths where QUIC's integrity guarantees are
absent.  To mitigate:

1. **Block-level integrity**: Publishers SHOULD include a
   per-block HMAC or content hash in the repair object header
   (as an optional trailing field) so receivers can verify that
   decoded source data matches the publisher's original.
2. **Trust model**: Receivers MUST distinguish between
   publisher-generated repair (trusted, from the origin) and
   relay-generated repair (semi-trusted).  If decoded data fails
   integrity verification using relay-generated repair, receivers
   SHOULD discard it and request retransmission via unicast.
3. **Separate tracks**: Relay-generated repair SHOULD be published
   on a distinct track (e.g., "video/repair/relay") so receivers
   can apply different trust policies.

```
Publisher (K=32, P=8, 25% overhead)
    |
    | Source ESI: 0-31, Repair ESI: 32-39
    v
+------------------+
| Backbone Relay   |  (passes through, low loss)
+--------+---------+
         |
    +----+----+
    |         |
    v         v
+--------+ +--------+
| Edge A | | Edge B |
| P=16   | | P=4    |
| (50%)  | | (12%)  |
+--------+ +--------+
    |         |
    v         v
[Lossy    [Clean
 WiFi]     Fiber]
```

### 11.3. Relay FEC Recovery

Relays that subscribe to both source and repair tracks can perform FEC
recovery before forwarding to downstream subscribers.  This is distinct
from relay-generated repair (Section 11.2): recovery uses the
publisher's repair symbols to reconstruct missing source objects,
while relay-generated repair creates new repair symbols.

A relay performing FEC recovery:

1. Subscribes to both source and repair tracks from the upstream
   publisher
2. If any source objects are missing (e.g., due to datagram loss or
   multicast packet loss on the relay's ingress), uses received repair
   symbols to recover the missing source objects via FEC decoding
3. Forwards the complete set of source objects as reliable QUIC stream
   objects to downstream subscribers (stripping FEC overhead)
4. Or packages recovered source data as CMAF segments for HLS/DASH
   clients that do not understand FEC

Downstream subscribers on reliable QUIC streams receive a complete,
ordered source track with no FEC overhead.  This enables CDN-side
repair: edge relays absorb multicast/datagram loss and present a
clean stream to end users.


---

### 12.2. S-TSID to FEC_CONFIG Conversion

When converting ATSC S-TSID FEC parameters to MoQ FEC_CONFIG:

```
S-TSID (per ATSC A/331):
<FECParameters maximumDelay="1000" overhead="25"
               fecOTI="F=32;T=1312;Z=4;N=1;Al=8">
  <ProtectedObject tsi="1">
    <SourceTOI x="0" y="255"/>
  </ProtectedObject>
</FECParameters>

Note: The fecOTI attribute uses ATSC A/331 field names, which
differ from RFC 6330 terminology.  F denotes the number of source
symbols per block (equivalent to K in this document), T is symbol
size, Z is the number of source blocks, N is sub-blocks, and Al
is symbol alignment.  RFC 6330 uses F for Transfer Length (40 bits),
which is a different concept; implementors should use the A/331
schema as the reference for S-TSID parsing.

Converts to FEC_CONFIG:
  FEC Algorithm: 0x01 (RaptorQ)
  Source Symbols Per Block: 32  (from F parameter)
  Repair Symbols Per Block: 8  (25% of 32, from overhead)
  Symbol Size: 1312  (from T parameter)
  Interleave Depth: 1000  (from maximumDelay attribute, in ms)
  OTI: [12-byte concatenation of Common FEC OTI + Scheme-Specific
        FEC OTI per RFC 6330]
```
