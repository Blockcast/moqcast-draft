#!/usr/bin/env python3
"""Small source-backed checks for the published moqcast examples."""

from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
import math
import re
import struct
import sys
import unittest
from fractions import Fraction
from pathlib import Path


def draft_root() -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--draft-root", type=Path)
    args, rest = parser.parse_known_args()
    sys.argv[1:] = rest
    return args.draft_root or Path(__file__).resolve().parents[1]


ROOT = draft_root()


def fences(text: str, language: str | None = None):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opener = lines[i]
        if language is None and not re.fullmatch(r"\s*~~~(\s+\w+)?\s*", opener):
            i += 1
            continue
        if language is not None and not re.fullmatch(rf"\s*~~~\s+{language}\s*", opener):
            i += 1
            continue
        end = i + 1
        while end < len(lines) and lines[end].strip() != "~~~":
            end += 1
        if end == len(lines):
            raise AssertionError(f"unterminated fence at line {i + 1}")
        yield i + 1, "\n".join(lines[i + 1 : end])
        i = end + 1  # resume after the closer, which is not an opener


def catalogs():
    """Yield catalogs; skip only the explicitly published member fragments."""

    for path in sorted(ROOT.glob("draft-ramadan-moq-*.md")):
        for line, raw in fences(path.read_text(encoding="utf-8"), "json"):
            source = raw.strip()
            try:
                value = json.loads(source)
            except json.JSONDecodeError as error:
                if source.startswith(('"fec":', '"auth":')):
                    continue
                raise AssertionError(f"malformed complete JSON example {path}:{line}") from error
            if isinstance(value, dict) and isinstance(value.get("tracks"), list):
                yield path, line, value


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


class PublishedExamples(unittest.TestCase):
    def sec(self, text: str, start: str, end: str) -> str:
        try:
            return section(text, start, end)
        except ValueError:
            self.fail(f"published example section is missing: {start!r}")

    def test_multicast_revision_specifies_receiver_owned_dns_health(self):
        markdown = (ROOT / "draft-ramadan-moq-multicast-02.md").read_text(encoding="utf-8")
        xml = (ROOT / "draft-ramadan-moq-multicast-02.xml").read_text(encoding="utf-8")
        self.assertIn('value = "draft-ramadan-moq-multicast-02"', markdown)
        self.assertIn('docName="draft-ramadan-moq-multicast-02"', xml)
        self.assertIn('anchor="receiver-owned-dns-candidate-discovery"', xml)
        for text in (markdown, xml):
            self.assertIn("DNS answer order", text)
            self.assertIn("MUST NOT", text)
            self.assertIn("cancel", text)
            self.assertIn("bounded batch", text)
            self.assertIn("Discovery", text)
            self.assertIn("Advertisement", text)
            self.assertIn("Request", text)
            self.assertIn("Membership Query", text)
            self.assertIn("post-Membership", text)
            self.assertIn("Membership Update", text)
            self.assertIn("leave", text)
            self.assertIn("operator provisioning system", text)

    def test_multicast_receivers_react_to_ce_marks(self):
        # Section 5.1 (CEO D18 A, 2026-11-01): a flow sent ECN-capable needs a congestion
        # reaction to CE (RFC 3168 s5); in multicast that reaction is the receiver's (RFC 8085 s4.1),
        # departing from the sender feedback of RFC 8085 s3.1.7.
        markdown = (ROOT / "draft-ramadan-moq-multicast-02.md").read_text(encoding="utf-8")
        xml = (ROOT / "draft-ramadan-moq-multicast-02.xml").read_text(encoding="utf-8")
        texts = (
            section(markdown, "## Explicit Congestion Notification", "{#multi-path-delivery}"),
            re.sub(r"<[^>]+>", "", section(xml, 'anchor="explicit-congestion-notification"', "</section>")),
        )
        for text in texts:
            text = " ".join(text.split())
            self.assertIn("SHOULD set ECT(0)", text)
            self.assertIn("MUST treat a datagram that arrives marked CE as it treats a lost one", text)
            self.assertIn("MUST NOT wait for the sender to lower its rate in response to the marks", text)
            self.assertIn("E flag", text)
            self.assertNotIn("MAY use the fraction", text)

    def test_fec_multicast_overlay_repair_track_follows_the_layer_rules(self):
        # Section 4, -01 (author ruling 2026-11-04): the rules for adding and dropping a repair
        # layer also govern a keyframe overlay's repair track, read on the overlay instance's own
        # blocks and fields; the track stays outside the base instance's layer chain.
        stem = "draft-ramadan-moq-fec-multicast-01"
        markdown = (ROOT / f"{stem}.md").read_text(encoding="utf-8")
        xml = (ROOT / f"{stem}.xml").read_text(encoding="utf-8")
        self.assertIn(f'value = "{stem}"', markdown)
        self.assertIn(f'docName="{stem}"', xml)
        self.assertIn('anchor="changes-since-draft-ramadan-moq-fec-multicast-00"', xml)
        texts = (
            section(markdown, "# Repair-Only Multicast Endpoints\n", "{#provisional-symbols}"),
            re.sub(r"<[^>]+>", "", section(xml, 'anchor="repair-only-endpoints"', 'anchor="provisional-symbols"')),
        )
        for text in texts:
            text = " ".join(text.replace("`", "").split())
            for rule in (
                "The repair track of a keyframe overlay",
                "is not a layer of the base instance: it carries no repairLayer",
                "The rules of this section for adding and dropping a repair layer apply to adding and "
                "dropping the overlay's repair track",
                "For the overlay's repair track they read the overlay instance's blocks, interleaveDepthMs "
                "and reorderToleranceMs, and for a repair layer the base instance's.",
                "it means the base instance's value, which governs none of these rules for the overlay",
                "The loss it measures for the overlay is then the RAP packets that it lacks and that base "
                "decoding has not recovered",
                "a receiver of an overlay whose instance omits interleaveDepthMs or sets it to zero keeps "
                "fixed whether it holds the overlay's repair track",
                "joining or leaving it changes both, and a receiver does so only when the rules for each allow it",
                "Every rule of the paragraph on amplification above applies to it as to a repair layer, and "
                "the bound on the layers a receiver may hold counts it",
            ):
                self.assertIn(rule, text)
            self.assertNotIn("whatever the base instance carries", text)

    def test_mboned_manifest_draft_md_and_xml_agree_on_docname(self):
        stem = "draft-ramadan-mboned-mcast-manifest-01"
        markdown = (ROOT / f"{stem}.md").read_text(encoding="utf-8")
        xml = (ROOT / f"{stem}.xml").read_text(encoding="utf-8")
        self.assertIn(f'value = "{stem}"', markdown)
        self.assertIn(f'docName="{stem}"', xml)
        self.assertIn('anchor="hash-algorithms"', xml)
        self.assertIn('anchor="signature-context-binding"', xml)
        for text in (markdown, xml):
            self.assertIn("manifest-ed25519-2", text)
            self.assertIn("ed25519-trailer-1", text)
            self.assertIn("mcast-manifest-v2", text)
            self.assertIn("132 + 32 x count", text)
            self.assertIn("multicast-receive", text)
        for line, raw in fences(markdown, "json"):
            document = json.loads(raw)
            self.assertEqual(document["version"], 1, f"well-known example at line {line}")
            self.assertTrue(document["channels"], f"well-known example at line {line}")

    def test_mboned_well_known_example_obeys_its_own_rules(self):
        # Sections 8.1/8.2: address literals of one family, 1..4 keys with distinct kid and
        # firstEpoch, publicKey 43 unpadded base64url characters for 32 octets, no manifestPort
        # (records travel in band on `port`) and no `port` shared by two channels of one (S, G).
        markdown = (ROOT / "draft-ramadan-mboned-mcast-manifest-01.md").read_text(encoding="utf-8")
        channels = 0
        for line, raw in fences(markdown, "json"):
            flows = set()
            for channel in json.loads(raw)["channels"]:
                where = f"well-known example at line {line}"
                source, group = (ipaddress.ip_address(channel[k]) for k in ("source", "group"))
                self.assertEqual(source.version, group.version, where)
                integrity = channel["integrity"]
                keys = integrity["keys"]
                self.assertTrue(1 <= len(keys) <= 4, where)
                for member in ("kid", "firstEpoch"):
                    self.assertEqual(len({key[member] for key in keys}), len(keys), where)
                for key in keys:
                    self.assertRegex(key["publicKey"], r"^[A-Za-z0-9_-]{43}$", where)
                    self.assertEqual(len(base64.urlsafe_b64decode(key["publicKey"] + "=")), 32, where)
                for obj in (channel, integrity):
                    self.assertNotIn("manifestPort", obj, where)
                flow = (source, group, channel["port"])
                self.assertNotIn(flow, flows, where)
                flows.add(flow)
                channels += 1
        self.assertGreater(channels, 0)

    def test_appendix_a_vectors_recompute_from_their_inputs(self):
        # Every value each appendix prints is recomputed from its printed inputs (seed, S, G, port, streamId and
        # the record fields; ctx from the MoQ catalog inputs where the appendix derives it), and the two
        # recomputed records are equal, so the two documents verify the same bytes.
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        except ImportError:
            self.skipTest("the cryptography package is not installed (Ed25519)")

        def appendix(name: str, heading: str) -> str:
            text = (ROOT / name).read_text(encoding="utf-8")
            start = text.index(heading)
            end = text.find("\n# ", start + 1)
            return text[start : len(text) if end < 0 else end]

        def table(text: str) -> dict:
            values, label = {}, None
            for _, block in fences(text):
                for raw in block.splitlines():
                    head, sep, tail = raw.partition(":")
                    if sep and not raw.startswith(" "):
                        label, values[label] = head.strip(), [tail.strip()]
                    elif label is not None and raw.startswith(" "):
                        values[label].append(raw.strip())
            return {key: " ".join(filter(None, value)) for key, value in values.items()}

        def octets(value: str) -> bytes:
            return bytes.fromhex(value.replace(" ", ""))

        def u16(n: int) -> bytes:
            return struct.pack(">H", n)

        def u32(n: int) -> bytes:
            return struct.pack(">I", n)

        def lp16(value: bytes) -> bytes:
            return u16(len(value)) + value

        records = []
        for name, heading in (
            ("draft-ramadan-mboned-mcast-manifest-01.md", "# Test Vectors\n"),
            ("draft-ramadan-moq-multicast-02.md", "# Test Vectors: bc-provenance Version 2\n"),
        ):
            text = appendix(name, heading)
            flat, printed = " ".join(text.split()), table(text)
            key = Ed25519PrivateKey.from_private_bytes(octets(printed["ed25519 secret seed"]))
            self.assertEqual(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw), octets(printed["ed25519 publicKey"]), name)
            source, group = (ipaddress.ip_address(a.strip()).packed for a in printed["S, G"].split("(")[0].split(","))
            port, stream_id, first_seq, sent = (int(printed[k].split()[0]) for k in ("port", "streamId", "first_seq", "sent"))
            kid, epoch, mseq = (int(n) for n in printed["kid, epoch, mseq"].split(","))
            flags = int(printed["flags"], 16)
            self.assertEqual(int(re.search(r"`hash_alg` (\d+) \(sha-256", flat).group(1)), 1, name)  # H is SHA-256
            payloads = []
            for i in range(2):
                fill, length = re.fullmatch(r"0x([0-9a-f]{2}) repeated (\d+) times", printed[f"datagram {i} payload"]).groups()
                payloads.append(bytes.fromhex(fill) * int(length))
            # Digest: pseudoheader S || G || 0x00 || 0x11 || u16(len) || u16(port) || u16(port) || u32(streamId).
            pseudo = [source + group + b"\x00\x11" + u16(len(p)) + u16(port) + u16(port) + u32(stream_id) for p in payloads]
            self.assertEqual(pseudo[0], octets(printed["pseudoheader (20)"]), name)
            digests = [hashlib.sha256(h + p).digest() for h, p in zip(pseudo, payloads)]
            self.assertEqual(digests, [octets(printed[f"D_{i}"]) for i in range(2)], name)
            if "params (for params_hash)" in printed:  # the MoQ profile derives ctx from its catalog
                params = dict(re.findall(r'(\w+)="?([^"\s]+)"?', printed["params (for params_hash)"]))
                params_hash = hashlib.sha256(
                    b"BCPV2-params" + lp16(params["codec"].encode()) + u32(int(params["timescale"]))
                    + u32(int(params["groupDurationTicks"])) + lp16(params["scheme"].encode())
                    + b"".join(u32(int(params[k])) for k in ("sourceSymbols", "repairSymbols", "symbolSize", "interleaveDepthMs"))
                ).digest()
                self.assertEqual(params_hash, octets(printed["params_hash"]), name)
                fields = json.loads(printed["namespace"].split("(")[0])
                packet_ids = sorted(json.loads(printed["endpoint packetIds"]))
                ctx = hashlib.sha256(
                    b"BCPV2-ctx" + u16(len(fields)) + b"".join(lp16(f.encode()) for f in fields)
                    + u16(len(packet_ids)) + b"".join(u16(p) for p in packet_ids) + params_hash
                ).digest()
                self.assertEqual(ctx, octets(printed["ctx"]), name)
            else:
                ctx = octets(printed["ctx"])
            # Section 5.1: the signed_message prefix is 32 octets and ends in u16(port) of the inputs.
            prefix = b"mcast-manifest-v2\x00" + u32(stream_id) + source + group + u16(port)
            shown = re.search(r"signed_message prefix \([^)]*\):\n((?:[ \t]+[0-9a-f]+\n)+)", text)
            self.assertIsNotNone(shown, f"signed_message prefix is missing from {name}")
            self.assertEqual(bytes.fromhex(shown.group(1)), prefix, name)
            self.assertEqual((len(prefix), prefix[-2:]), (32, u16(port)), name)
            body = b"MHM2" + u32(kid) + u32(epoch) + struct.pack(">QQHBBI", mseq, first_seq, len(digests), 1, flags, sent) + ctx + b"".join(digests)
            self.assertIn(f"followed by the first {len(body)} octets of the record", flat, name)
            signature = key.sign(prefix + body)
            self.assertEqual(signature, octets(printed["signature"]), name)
            shown = re.search(rf"Record \({len(body) + len(signature)} octets\):", text)
            self.assertIsNotNone(shown, f"record length is not {len(body) + len(signature)} in {name}")
            self.assertEqual(bytes.fromhex(next(block for _, block in fences(text[shown.end() :]))), body + signature, name)
            records.append(body + signature)
        self.assertEqual(records[0], records[1])

    @unittest.skip("the libmmt in-band JSON is not published yet: BLO-49771 (libmmt re-cut), blocked on BLO-50124")
    def test_appendix_a_record_equals_published_libmmt_json(self):
        """Compare the recomputed Appendix A record with the matching case of the published libmmt JSON, pinned by its SHA-256."""

    def test_mboned_rate_arithmetic_is_consistent(self):
        text = " ".join((ROOT / "draft-ramadan-mboned-mcast-manifest-01.md").read_text(encoding="utf-8").split())
        moq = " ".join((ROOT / "draft-ramadan-moq-multicast-02.md").read_text(encoding="utf-8").split())

        def numbers(pattern: str, source: str = text):
            match = re.search(pattern, source)
            self.assertIsNotNone(match, pattern)
            return [int(v.replace(",", "")) if v.replace(",", "").isdigit() else float(v) for v in match.groups()]

        auth_delay, _low, _high = numbers(r"\*\*maxAuthDelayMs\*\* \(integer, OPTIONAL, default (\d+), range (\d+) to (\d+)\)")
        timer, timer_min = numbers(r"\*\*manifestTimerMs\*\* \(integer, OPTIONAL, default (\d+), at least (\d+)\)")
        count_rate, mbit, octets = numbers(r"at most 37 datagrams per `manifestTimerMs` \((\d+) per second at the default, about (\d+) Mbit/s of (\d+)-octet datagrams\)")
        self.assertEqual(count_rate, 37 * 1000 // timer)
        self.assertEqual(mbit, round(count_rate * octets * 8 / 1e6))
        # The verification budget V scales with the declared maxBitrate; the sender rule and step 1 state one formula.
        formula = r"`V = max\((\d+), ([\d.]+) x maxBitrate / \(8 x (\d+) x (\d+)\)\)`"
        envelope = r"MUST NOT close more than `(\d+) \+ V x t` windows on one flow in any interval of `t` seconds, a long-run rate of at most V per second"
        depth_rule, *v_rule = numbers(envelope + r", where " + formula)
        depth, *v_step1 = numbers(r"a token bucket of depth (\d+) refilled at V tokens per second, " + formula)
        self.assertEqual(v_step1, v_rule)
        self.assertEqual(depth_rule, depth)  # the sender's envelope is the receiver's bucket
        v_floor, headroom, size, cap = v_rule
        self.assertEqual(cap, 37)  # one window carries at most 37 datagrams
        self.assertEqual(1000 // timer_min, v_floor)  # the timer alone never closes more windows than V's floor
        self.assertIn(f"so the timer alone never closes more than {v_floor} windows per second", text)
        self.assertIn(f"`{depth} + V x t` is the envelope of that bucket, whose depth of {depth}", text)
        crossover, headroom2, size2, average, v_gig, gig = numbers(
            r"At the count cap that is 37 x V datagrams per second, which above V's floor \(a `maxBitrate` above about (\d+) Mbit/s\) "
            r"is ([\d.]+) x `maxBitrate` of (\d+)-octet datagrams: a flow at its declared rate stays under V while its datagrams "
            r"average at least about (\d+) octets \(V is ([\d,]+) at (\d+) Gbit/s\)"
        )
        self.assertEqual((headroom2, size2), (headroom, size))
        self.assertEqual(crossover, round(v_floor * 8 * size * cap / headroom / 1e6))  # where V leaves its floor
        self.assertEqual(average, round(size / headroom))
        self.assertEqual(v_gig, math.ceil(headroom * gig * 1e9 / (8 * size * cap)))
        self.assertEqual(numbers(r"declared `maxBitrate` \(\(#flow-parameters\)\): (\d+) up to about (\d+) Mbit/s, ([\d,]+) at (\d+) Gbit/s"), [v_floor, crossover, v_gig, gig])
        depth2, entries, crossover2, entries_gig, gig2 = numbers(
            r"holds at most `37 x \((\d+) \+ V/1000 x \(maxAuthDelayMs \+ 2 x manifestTimerMs\)\)` entries, ([\d,]+) at the defaults "
            r"up to a `maxBitrate` of about (\d+) Mbit/s and ([\d,]+) at (\d+) Gbit/s"
        )
        self.assertEqual((depth2, crossover2, gig2), (depth, crossover, gig))
        window = auth_delay + 2 * timer
        self.assertEqual((entries, entries_gig), (int(cap * (depth + v_floor * window / 1000)), int(cap * (depth + v_gig * window / 1000))))
        megabytes, rate = numbers(r"`maxAuthDelayMs x maxBitrate / 8000` octets, ([\d.]+) MB at (\d+) Mbit/s")
        self.assertEqual(megabytes, auth_delay * rate / 8000)
        (floor,) = numbers(r"`mseq \+ (\d+) <= highest_mseq\(kid, epoch\)`")
        self.assertIn(f"before the signed record of window `mseq + {floor}`, so that at most {floor - 1} later records precede it", text)
        # Section 7.2.7 of draft-ramadan-moq-multicast-02 refills both of its buckets at the same V, from `bandwidth`.
        enforcement = self.sec(moq, "### Receiver Enforcement and State", "### Threat Model")
        moq_depth, *v_moq = numbers(
            r"a token bucket of depth (\d+) refilled at V tokens per second, " + formula
            + r" computed from the flow's declared `maxBitrate` \(\[@\?MCAST-MANIFEST\]\), which this profile declares as the endpoint's `bandwidth`",
            enforcement,
        )
        self.assertEqual([moq_depth, *v_moq], [depth, *v_rule])
        # Its senders keep to the same envelope (Emission and Cadence), as the MBONED sender rule does.
        (moq_envelope,) = numbers(envelope, self.sec(moq, "### Emission and Cadence", "### Catalog Signaling"))
        self.assertEqual(moq_envelope, depth)
        self.assertIn("charges a second bucket of the same depth and refill", enforcement)
        self.assertIn("so its ceiling is 2V verifications per second", moq)
        # The record-flood figures are re-derived from V in both drafts; nothing still assumes a fixed budget.
        single, double = numbers(r"at most ([\d.]+) of a core on signature checks, or twice that, about ([\d.]+),", enforcement)
        self.assertEqual(double, round(2 * single, 2))
        self.assertEqual(numbers(r"so these figures rise with V: ([\d,]+) per second, V at (\d+) Gbit/s", enforcement), [v_gig, gig])
        self.assertEqual(numbers(r"so the flood figure rises with V: ([\d,]+) per second, V at (\d+) Gbit/s"), [v_gig, gig])
        for name, source in (("draft-ramadan-mboned-mcast-manifest-01", text), ("draft-ramadan-moq-multicast-02", moq)):
            mbit_floor, record, mbit_v, v_stated = numbers(
                r"more than V records per second on (?:the flow's )?`port` \(about ([\d.]+) Mbit/s of (\d+)-octet records "
                r"at V's floor, ([\d.]+) Mbit/s at ([\d,]+)\)",
                source,
            )
            self.assertEqual((record, v_stated), (132 + 32, v_gig), name)  # the shortest record, count 1
            self.assertEqual((mbit_floor, mbit_v), (round(record * 8 * v_floor / 1e6, 1), round(record * 8 * v_gig / 1e6, 1)), name)
            for stale in ("faster than 1000 per second", "37,000 datagrams", "414 Mbit/s", "several flows"):
                self.assertNotIn(stale, source, name)

    def test_mboned_record_cap_arithmetic(self):
        stem = "draft-ramadan-mboned-mcast-manifest-01"
        texts = {suffix: " ".join((ROOT / f"{stem}.{suffix}").read_text(encoding="utf-8").split()) for suffix in ("md", "xml")}
        pattern = (
            r"one unfragmented datagram on a (\d+)-octet path\. At (\d+) digests the record is (\d+) octets: "
            r"(\d+) on the wire with IPv4 and UDP headers and (\d+) with IPv6, and (\d+) or (\d+) once an AMT relay "
            r".{0,40}? adds its own IPv4 or IPv6 header, UDP header and (\d+)-octet Multicast Data header around the IPv6 datagram\. "
            r"That leaves (\d+) to (\d+) octets .*?; an IPv4 record through an IPv4 relay is (\d+) octets, leaving (\d+)\. "
            r"A record of (\d+) digests would still fit a (\d+)-octet path through AMT; one of (\d+) \((\d+) octets, (\d+) under IPv4 and UDP\) would not fit"
        )
        groups = {}
        for suffix, text in texts.items():
            match = re.search(pattern, text)
            self.assertIsNotNone(match, f"cap paragraph not found in the {suffix}")
            groups[suffix] = tuple(map(int, match.groups()))
        self.assertEqual(groups["md"], groups["xml"])
        mtu, cap, record, v4, v6, amt4, amt6, amt_hdr, room_lo, room_hi, v4_in_v4, room_v4, fits, mtu2, over, over_record, over_v4 = groups["md"]
        ipv4, ipv6, udp = 20, 40, 8
        self.assertEqual((mtu, mtu2, amt_hdr), (1500, 1500, 2))  # RFC 7450 Figure 16: 2-octet Multicast Data header over UDP
        amt = amt_hdr + udp
        self.assertEqual(record, 132 + 32 * cap)
        self.assertEqual((v4, v6), (record + ipv4 + udp, record + ipv6 + udp))
        self.assertEqual((amt4, amt6), (v6 + amt + ipv4, v6 + amt + ipv6))
        self.assertEqual((room_lo, room_hi), (mtu - amt6, mtu - amt4))
        self.assertEqual((v4_in_v4, room_v4), (v4 + amt + ipv4, mtu - (v4 + amt + ipv4)))
        self.assertLessEqual(132 + 32 * fits + ipv6 + udp + amt + ipv6, mtu)  # worst case: IPv6 record through an IPv6 relay
        self.assertGreater(132 + 32 * (fits + 1) + ipv6 + udp + amt + ipv6, mtu)
        self.assertEqual((over_record, over_v4), (132 + 32 * over, 132 + 32 * over + ipv4 + udp))
        self.assertGreater(over_v4, mtu)
        self.assertIn(f"`164 <= len <= {record}`", texts["md"])  # step 1 bounds the record by the same size

    def test_replay_floor_is_written_without_unsigned_underflow(self):
        # Both drafts state the floor as a sum, `mseq + 64 <= highest_mseq`, and say neither counter wraps.
        for stem in ("draft-ramadan-mboned-mcast-manifest-01", "draft-ramadan-moq-multicast-02"):
            markdown = (ROOT / f"{stem}.md").read_text(encoding="utf-8")
            xml = (ROOT / f"{stem}.xml").read_text(encoding="utf-8")
            self.assertIn("`mseq + 64 <= highest_mseq(kid, epoch)`", markdown, stem)
            self.assertIn("mseq + 64 &lt;= highest_mseq(kid, epoch)", xml, stem)
            for text in (markdown, xml):
                self.assertNotIn("highest_mseq(kid, epoch) - 64", text, stem)
                self.assertNotIn("highest_mseq - 64", text, stem)
                self.assertIn("Neither counter wraps within an epoch", " ".join(text.split()), stem)  # hard-wrapped source

    def test_amt_discovery_combinations_are_unambiguous(self):
        for name in ("draft-ramadan-moq-multicast-02.md", "draft-ramadan-moq-multicast-02.xml"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('"relay": "amt.example.com"', text)
            self.assertIn('"discovery": "dns"', text)
            self.assertIn('"discovery": "driad"', text)
            self.assertNotIn('"discovery": "driad",\n      "relay":', text)
            if name.endswith(".md"):
                self.assertIn("**relay** (string, OPTIONAL)", text)
        markdown = (ROOT / "draft-ramadan-moq-multicast-02.md").read_text(encoding="utf-8")
        self.assertIn("discovery` is omitted and `relay` is a hostname", markdown)
        self.assertIn("discovery` is omitted and `relay` is a literal", markdown)

    def test_iso_catalogs_have_required_fields_and_repair_references(self):
        required = {"algorithm", "blockProfile", "sourceSymbols", "repairSymbols", "symbolSize", "repairTrack"}
        seen = 0
        for path, line, catalog in catalogs():
            tracks = catalog["tracks"]
            names = [track.get("name") for track in tracks]
            self.assertEqual(len(names), len(set(names)), f"duplicate track at {path}:{line}")
            media = {
                track.get("name", "").split("/", 1)[0]: track
                for track in tracks if track.get("packaging") == "mmtp"
            }
            for track in tracks:
                if track.get("packaging") != "mmtp":
                    continue
                where = f"{path.name}:{line}:{track.get('name', '<unnamed>')}"
                self.assertEqual(track.get("mmtpMode"), "mfu", where)
                self.assertIsInstance(track.get("timescale"), int, where)
                self.assertGreater(track["timescale"], 0, where)
                ticks = track.get("groupDurationTicks")
                if ticks is not None:
                    self.assertIsInstance(ticks, int, where)
                    self.assertGreater(ticks, 0, where)
                else:
                    milliseconds = track.get("groupDurationMs")
                    self.assertIsInstance(milliseconds, int, where)
                    self.assertGreater(milliseconds, 0, where)
                    self.assertEqual((milliseconds * track["timescale"]) % 1000, 0, where)
            if {"audio", "video"} <= media.keys():
                for kind in ("audio", "video"):
                    if media[kind].get("packaging") == "mmtp":
                        self.assertIsInstance(media[kind].get("presentationAnchorTicks"), int)
            for track in tracks:
                fec = track.get("fec")
                if not isinstance(fec, dict) or fec.get("blockProfile") != "iso-ssbg1-v1":
                    continue
                seen += 1
                where = f"{path.name}:{line}:{track.get('name', '<unnamed>')}"
                self.assertEqual(track.get("packaging"), "mmtp", where)  # rejects cmaf
                self.assertEqual(track.get("mmtpMode"), "mfu", where)
                self.assertIsInstance(track.get("timescale"), int, where)
                self.assertTrue(required <= fec.keys(), where)
                self.assertIn(fec["algorithm"], ("raptorq", "reed-solomon"), where)
                self.assertTrue(all(isinstance(fec[k], int) and fec[k] >= 1 for k in ("sourceSymbols", "repairSymbols")), where)
                self.assertTrue(isinstance(fec["symbolSize"], int) and fec["symbolSize"] > 0, where)
                if fec["algorithm"] == "raptorq":
                    self.assertEqual(fec["symbolSize"] % 8, 0, where)  # RFC 6330 Al = 8
                else:
                    # GF(2^8) Cauchy code: K + P <= 255 per FEC instance (fec Section 4.4)
                    self.assertLessEqual(fec["sourceSymbols"] + fec["repairSymbols"], 255, where)
                repair = [item for item in tracks if item.get("name") == fec["repairTrack"]]
                self.assertEqual(len(repair), 1, f"missing repair track for {where}")
                self.assertEqual(repair[0].get("packaging"), "fec-repair", where)
                if "depends" in repair[0]:
                    self.assertIn(track.get("name"), repair[0]["depends"], where)
        self.assertGreater(seen, 0)

    def test_mmt_negative_time_rows_compute_admission_and_unique_groups(self):
        text = (ROOT / "draft-ramadan-moq-mmt-02.md").read_text(encoding="utf-8")
        part = self.sec(text, "Negative authored timestamps use", "### Catalog Signaling")
        anchor = int(re.search(r"presentationAnchorTicks:\s*(-?\d+)", part).group(1))
        duration = int(re.search(r"groupDurationTicks:\s*(\d+)", part).group(1))
        row_block = next(raw for _, raw in fences(part) if "relative_ticks" in raw)
        rows = [tuple(map(int, row)) for row in re.findall(r"MPU \d+ ticks =\s*(-?\d+): relative_ticks =\s*(-?\d+)\s*-> group (-?\d+)", row_block)]
        self.assertEqual((anchor, duration), (-180000, 180000))
        self.assertEqual(rows, [(-90000, 90000, 0), (90000, 270000, 1)])
        for pts, relative, group in rows:
            self.assertEqual((relative, group), (pts - anchor, relative // duration))
        self.assertEqual([row[2] for row in rows], sorted({row[2] for row in rows}))
        normalized = " ".join(part.split())
        self.assertIn("`presentationAnchorTicks: 0` is invalid", part)
        self.assertIn("publisher rejects MPU 0 instead of mapping it to group 0", normalized)
        policy = " ".join(self.sec(text, "The publisher MUST choose `presentationAnchorTicks`", "Timeline origin:").split())
        self.assertIn("MUST reject that MPU", policy)
        self.assertIn("MUST NOT clamp", policy)
        self.assertIn("computed Group number MUST be strictly greater than the Group number", " ".join(text.split()))

    def test_packet_budget_arithmetic(self):
        text = (ROOT / "draft-ramadan-moq-fec-01.md").read_text(encoding="utf-8")
        budget = self.sec(text, "Parameter consistency:", "The catalog envelope")
        rows = re.findall(r"ceil\(([\d,]+) / ([\d,]+)\) = ([\d,]+)", budget)
        self.assertEqual(len(rows), 2)
        for media, capacity, packets in rows:
            media, capacity, packets = (int(n.replace(",", "")) for n in (media, capacity, packets))
            self.assertEqual(packets, (media + capacity - 1) // capacity)
        for k, capacity, total in re.findall(r"= (\d+) x (\d+) = ([\d,]+)` bytes", budget):
            self.assertEqual(int(total.replace(",", "")), int(k) * int(capacity))

    def decode_order_vector(self, text: str):
        vector = next(
            (json.loads(raw) for _, raw in fences(text, "json") if '"mpuSamplePtsInDecodeOrder"' in raw),
            None,
        )
        self.assertIsNotNone(vector, "open-GOP decode-order JSON example is missing")
        anchor, duration = vector["presentationAnchorTicks"], vector["groupDurationTicks"]
        self.assertEqual((vector["timescale"], anchor, duration), (90000, 0, 180000))
        return vector, (lambda ticks: (ticks - anchor) // duration)

    def test_mmt_published_bframe_and_tick_only_examples(self):
        text = (ROOT / "draft-ramadan-moq-mmt-02.md").read_text(encoding="utf-8")
        definition = " ".join(self.sec(text, "- `ticks` is", "- `groupDurationTicks`").split())
        self.assertIn("first AU in decode order", definition)
        self.assertNotIn("presentation order", definition)

        # Mutation control: `ticks` is the first decoded AU (the RAP), not the minimum presented PTS.
        vector, group = self.decode_order_vector(text)
        mpus = vector["mpuSamplePtsInDecodeOrder"]
        self.assertEqual(vector["ticks"], [pts[0] for pts in mpus])
        self.assertEqual(vector["groupNumbers"], [group(ticks) for ticks in vector["ticks"]])
        reordered = mpus[1]
        self.assertNotEqual(min(reordered), reordered[0])
        self.assertEqual(group(min(reordered)), group(reordered[0]) - 1)

        tick_catalog = next(
            (json.loads(raw) for _, raw in fences(text, "json") if '"video-30fps"' in raw),
            None,
        )
        self.assertIsNotNone(tick_catalog, "30 fps tick-only catalog example is missing")
        tracks = tick_catalog["tracks"]
        self.assertEqual(len(tracks), 1)
        track = tracks[0]
        self.assertEqual(track["packaging"], "mmtp")
        self.assertEqual(track["mmtpMode"], "mfu")
        self.assertNotIn("groupDurationMs", track)
        self.assertEqual(track["groupDurationTicks"], track["timescale"] // track["framerate"])
        self.assertEqual((track["timescale"], track["groupDurationTicks"]), (44100, 1470))

    def test_mmt_open_gop_leading_pictures_yield_increasing_groups(self):
        text = (ROOT / "draft-ramadan-moq-mmt-02.md").read_text(encoding="utf-8")
        vector, group = self.decode_order_vector(text)
        closed, open_gop = vector["mpuSamplePtsInDecodeOrder"]
        self.assertEqual(closed[0], min(closed))  # closed GOP: both selections agree
        self.assertTrue(any(pts < open_gop[0] for pts in open_gop[1:]))  # leading pictures before the RAP
        decode_first = [group(closed[0]), group(open_gop[0])]
        presentation_min = [group(min(closed)), group(min(open_gop))]
        self.assertEqual(decode_first, [0, 1])
        self.assertEqual(vector["groupNumbers"], decode_first)
        self.assertLess(decode_first[0], decode_first[1])
        self.assertEqual(presentation_min, [0, 0])  # violates the strictly-greater rule

    def test_fec_published_json_vectors_compute_blocks_and_short_tail(self):
        text = (ROOT / "draft-ramadan-moq-fec-01.md").read_text(encoding="utf-8")
        cases = self.sec(text, "**Conformance cases.**", "# Priority")
        vector = next(json.loads(raw) for _, raw in fences(cases, "json") if '"sourcePacketsPerAccessUnit"' in raw)
        self.assertEqual((vector["fps"], vector["gopFrames"], vector["groupDurationMs"], vector["interleaveDepthMs"]), (30, 30, 1000, 133))
        self.assertEqual(Fraction(vector["gopFrames"] * 1000, vector["fps"]), vector["groupDurationMs"])
        self.assertEqual(sum(vector["sourcePacketsPerAccessUnit"]), vector["SSB_length"])
        self.assertLessEqual(vector["SSB_length"], vector["K"])
        self.assertEqual(vector["accessUnitsPerBlock"], len(vector["sourcePacketsPerAccessUnit"]))
        self.assertEqual(vector["firstSourceOrRepairMs"] + vector["sourceRepairSpanMs"], vector["lastSourceOrRepairMs"])
        self.assertEqual(vector["sourceRepairSpanMs"], vector["interleaveDepthMs"])
        partition = next((json.loads(raw) for _, raw in fences(cases, "json") if '"groupPacketCounts"' in raw), None)
        self.assertIsNotNone(partition, "K=4 partition example must be a JSON vector")
        self.assertEqual(partition["groupPacketCounts"], [3, 3])
        self.assertEqual(partition["K"], 4)
        self.assertEqual(partition["blockPartitions"], [[3, 3], [4, 2]])
        self.assertEqual(partition["SS_Starts"], [[0, 3], [0, 4]])
        k = partition["K"]
        for lengths, starts in zip(partition["blockPartitions"], partition["SS_Starts"]):
            self.assertEqual(sum(lengths), sum(partition["groupPacketCounts"]))
            self.assertTrue(all(1 <= length <= k for length in lengths))
            ids = []
            start = 0
            computed_starts = []
            for length in lengths:
                computed_starts.append(start)
                ids.extend(range(start, start + length))
                start += length
            self.assertEqual(starts, computed_starts)
            self.assertEqual(ids, list(range(6)))
        short = re.search(r"short block with `SSB_length = (?P<length>\d+)`, `F = (?P<factor>\d+) x T`,\s+and no padding or skipped `SS_ID`", cases, re.S)
        self.assertIsNotNone(short)
        self.assertEqual({key: int(value) for key, value in short.groupdict().items()}, {"length": 2, "factor": 2})
        self.assertIn("There is no following block.", cases)


if __name__ == "__main__":
    unittest.main()
