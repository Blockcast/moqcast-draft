# MMT Draft Deployment/Implementation Material (removed from draft-ramadan-moq-mmt-00 for IETF submission)

Verbatim sections removed 2026-06-11. Homes: reference implementations +
test vectors → implementation docs; ARIB 8K/Hybridcast detail →
APPLICATION-2-BROADCAST-BRIDGE + deployment docs; conversion walkthroughs
→ this file (Appendix B in the draft remains the single worked example);
bandwidth comparison → marketing/deployment docs.

---
## From §4.4.2/4.4.3 (Reference Test Vectors / Reference Implementations)

#### 4.4.2. Reference Test Vectors

A normative cross-language test fixture covering boundary, overflow,
and drift cases is published as part of the libmmt reference
implementation at `packages/container/test-vectors/align.json`, and
is loaded unchanged by the Go sender [GroupAligner], the Rust relay
[moqtail-abr], and the TypeScript subscriber libmmt.  Implementers
SHOULD load this fixture in their own test suites to establish
machine-checkable cross-language agreement.

#### 4.4.3. Reference Implementations

- Go (sender): `Blockcast/multicast cmd/caddy/sender/group_align.go`
  at commit `695caa14` (see [GroupAligner]).
- Rust (relay): `moqtail/moqtail apps/relay/src/server/abr.rs` at
  commit `39accbf4` (see [moqtail-abr]).  Currently lives on the
  experimental `server-side-abr` branch; the SHA is the durable
  anchor.
- TypeScript (subscriber): `Blockcast/libmmt
  packages/container/src/align.ts`, exporting `groupIdForTicks` as
  the canonical entry point.

Implementation note: the TypeScript reference also exports a
seconds-form wrapper (`groupIdFor`) for compatibility with existing
consumers.  This is non-normative; new code SHOULD use the integer
entry point.

Reference implementations are pinned by commit SHA in §15 to keep
URLs stable across branch rewrites.  Formula changes are normative:
any update MUST update the test fixture and all reference
implementations in the same release.


---
## From §10.2-10.4 (ARIB 8K / Hybridcast / Typical FEC Parameters)

### 10.2. 8K UHDTV Support

ARIB STD-B60 supports 8K UHDTV (7680x4320) via HEVC Main 10 profile
at Level 6.1 (4:2:0, 10-bit).
For efficient 8K delivery:

1. **Tiled Delivery**: MoQ Group boundaries SHOULD align with HEVC
   CTU rows for spatial random access
2. **Parallel Decoding**: Multiple MoQ tracks MAY carry tile regions
   for parallel decode
3. **Bandwidth**: 8K @ 60fps requires ~80-100 Mbps; FEC adds 25%

Example 8K track structure:
```
namespace: "live/8k"
tracks:
  - video/tile_0_0  (top-left quadrant)
  - video/tile_0_1  (top-right quadrant)
  - video/tile_1_0  (bottom-left quadrant)
  - video/tile_1_1  (bottom-right quadrant)
  - video/repair    (FEC for all tiles)
```

### 10.3. Hybridcast Integration

ARIB defines Hybridcast for companion device synchronization
(second screen experiences).  When bridging Hybridcast services:

1. Include timeline alignment metadata in MoQ catalog
2. Preserve MMT Composition Timeline (CT) information
3. Signal synchronization points via MoQ object timestamps

Catalog extension for Hybridcast:
```json
{
  "hybridcast": {
    "timelineId": "urn:isdb:timeline:ct",
    "ptsOffset": 0,
    "syncToleranceMs": 100
  }
}
```

### 10.4. Typical FEC Parameters

ARIB STD-B60 deployments typically use more conservative FEC
parameters than ATSC 3.0:

| Parameter | ARIB STD-B60 Typical | ATSC 3.0 Typical |
|-----------|-----------------|------------------|
| K (source symbols) | 64 | 32 |
| Interleave depth | 60 frames | 30 frames |
| Symbol size | 1316 bytes | 1312 bytes |
| Overhead | 20-30% | 25% |

Publishers SHOULD preserve original FEC parameters when ingesting
ARIB STD-B60 content.


---
## From §12.2 (inline S-TSID → catalog example)

```
S-TSID Input:
<S-TSID>
  <RS sIpAddr="192.168.1.100" dIpAddr="232.1.1.50" dPort="5000">
    <LS tsi="1" bw="5000000">
      <SrcFlow rt="true">
        <ContentInfo>
          <MediaInfo contentType="video" repId="1080p"/>
        </ContentInfo>
        <Payload codePoint="128" formatId="2"/>
      </SrcFlow>
      <RepairFlow>
        <FECParameters maximumDelay="1000" overhead="25"
                       fecOTI="K=32;T=1312;Z=4">
          <ProtectedObject tsi="1">
            <SourceTOI x="0" y="255"/>
          </ProtectedObject>
        </FECParameters>
      </RepairFlow>
    </LS>
  </RS>
</S-TSID>

MoQ Catalog Output:
{
  "version": 1,
  "namespace": "atsc/service_1",
  "tracks": [{
    "name": "video",
    "packaging": "mmtp",
    "mmtpMode": "mfu",
    "timescale": 90000,
    "groupDurationMs": 1000,
    "selectionParams": {
      "codec": "avc1.64001f",
      "bitrate": 5000000
    },
    "fec": {
      "algorithm": "raptorq",
      "sourceSymbols": 32,
      "repairSymbols": 8,
      "symbolSize": 1312,
      "interleaveDepth": 4,
      "repairTrack": "video/repair"
    }
  }],
  "multicast": {
    "endpoints": [{
      "protocol": "ssm",
      "source": "192.168.1.100",
      "group": "232.1.1.50",
      "port": 5000,
      "tsi": 1,
      "tracks": ["video", "video/repair"]
    }]
  }
}
```

---
## From §12.3 (inline catalog → S-TSID example)

```
MoQ Catalog Input:
{
  "tracks": [{
    "name": "video",
    "packaging": "mmtp",
    "mmtpMode": "mfu",
    "timescale": 90000,
    "groupDurationMs": 1000,
    "selectionParams": {
      "bitrate": 5000000
    },
    "fec": {
      "algorithm": "raptorq",
      "sourceSymbols": 32,
      "repairSymbols": 8,
      "symbolSize": 1312,
      "interleaveDepth": 4,
      "repairTrack": "video/repair"
    }
  }],
  "multicast": {
    "endpoints": [{
      "source": "192.168.1.100",
      "group": "232.1.1.50",
      "port": 5000,
      "tsi": 1
    }]
  }
}

S-TSID Output:
<S-TSID xmlns="tag:atsc.org,2016:XMLSchemas/ATSC3/Delivery/S-TSID/1.0/">
  <RS sIpAddr="192.168.1.100" dIpAddr="232.1.1.50" dPort="5000">
    <LS tsi="1" bw="5000000">
      <SrcFlow rt="true" minBuffSize="5000000">
        <ContentInfo>
          <MediaInfo contentType="video"/>
        </ContentInfo>
        <Payload codePoint="128" formatId="2" srcFecPayloadId="6"/>
      </SrcFlow>
      <RepairFlow>
        <FECParameters maximumDelay="133" overhead="25"
                       fecOTI="F=32;T=1312;Z=4;N=1;Al=8">
        </FECParameters>
      </RepairFlow>
    </LS>
  </RS>
</S-TSID>
```

---
## Appendix A (Bandwidth Comparison)

## Appendix A. Bandwidth Comparison

FEC signaling bandwidth overhead:

### A.1. Per-Session Overhead (One-Time)

| Method | Size | When Sent |
|--------|------|-----------|
| FEC_CONFIG (0x50) | ~30 bytes | After SUBSCRIBE_OK |
| MMTP AL-FEC (0x0203) | ~42 bytes | First signaling packet |
| Catalog JSON FEC | ~100 bytes | Catalog fetch |

### A.2. Per-Object Overhead (Recurring)

| Method | Size | Frequency |
|--------|------|-----------|
| LOC Extension | 8 bytes | Every object |
| MMTP Header | 12 bytes | Every packet |
| FEC_CONFIG | 0 bytes | N/A (one-time) |

### A.3. Total Overhead Analysis

For a 30fps stream with k=32 source symbols per FEC block:

| Method | Overhead/second | Overhead/hour |
|--------|-----------------|---------------|
| FEC_CONFIG | ~0.03 KB | ~0.1 KB |
| LOC Extension | ~0.24 KB | ~0.86 MB |
| MMTP (source only) | ~0.36 KB | ~1.3 MB |
| MMTP + Repair | ~0.50 KB | ~1.8 MB |

FEC_CONFIG has the lowest per-session overhead and zero
per-object overhead, making it ideal for unicast MoQ.

MMTP AL-FEC signaling has higher initial overhead but
works without bidirectional signaling (multicast).

### A.4. Recommendations

| Use Case | Recommended Method |
|----------|-------------------|
| MoQ Unicast | FEC_CONFIG |
| SSM Multicast | MMTP AL-FEC |
| Adaptive FEC | FEC_CONFIG + dynamic updates |
| Hybrid (MoQ + SSM) | Both (MMTP in-band, FEC_CONFIG for unicast) |

