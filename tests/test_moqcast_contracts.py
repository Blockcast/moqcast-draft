#!/usr/bin/env python3
"""Small source-backed checks for the published moqcast examples."""

from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import re
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
        markdown = (ROOT / "draft-ramadan-moq-multicast-01.md").read_text(encoding="utf-8")
        xml = (ROOT / "draft-ramadan-moq-multicast-01.xml").read_text(encoding="utf-8")
        self.assertIn('value = "draft-ramadan-moq-multicast-01"', markdown)
        self.assertIn('docName="draft-ramadan-moq-multicast-01"', xml)
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

    def test_mboned_manifest_draft_md_and_xml_agree_on_docname(self):
        stem = "draft-ramadan-mboned-mcast-manifest-00"
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
        # firstEpoch, publicKey 43 unpadded base64url characters for 32 octets, manifestPort != port.
        markdown = (ROOT / "draft-ramadan-mboned-mcast-manifest-00.md").read_text(encoding="utf-8")
        channels = 0
        for line, raw in fences(markdown, "json"):
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
                if integrity["scheme"] == "manifest-ed25519-2":
                    self.assertNotEqual(integrity["manifestPort"], channel["port"], where)
                channels += 1
        self.assertGreater(channels, 0)

    def test_mboned_appendix_a_vectors_equal_moq_multicast_appendix_a(self):
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

        def record(text: str) -> str:
            return next(block for _, block in fences(text[text.index("Record (196 octets):") :]))

        ours = appendix("draft-ramadan-mboned-mcast-manifest-00.md", "# Test Vectors\n")
        theirs = appendix("draft-ramadan-moq-multicast-01.md", "# Test Vectors: bc-provenance Version 2\n")
        mine, moq = table(ours), table(theirs)
        self.assertGreaterEqual(len(mine), 10)
        for label, value in mine.items():
            self.assertEqual(value, moq.get(label), f"Appendix A value {label!r} differs from draft-ramadan-moq-multicast-01")
        self.assertEqual(record(ours), record(theirs))

    def test_mboned_rate_arithmetic_is_consistent(self):
        text = " ".join((ROOT / "draft-ramadan-mboned-mcast-manifest-00.md").read_text(encoding="utf-8").split())

        def numbers(pattern: str):
            match = re.search(pattern, text)
            self.assertIsNotNone(match, pattern)
            return [int(v.replace(",", "")) if v.replace(",", "").isdigit() else float(v) for v in match.groups()]

        auth_delay, _low, _high = numbers(r"\*\*maxAuthDelayMs\*\* \(integer, OPTIONAL, default (\d+), range (\d+) to (\d+)\)")
        timer, timer_min = numbers(r"\*\*manifestTimerMs\*\* \(integer, OPTIONAL, default (\d+), at least (\d+)\)")
        count_rate, mbit, octets = numbers(r"at most 37 datagrams per `manifestTimerMs` \((\d+) per second at the default, about (\d+) Mbit/s of (\d+)-octet datagrams\)")
        self.assertEqual(count_rate, 37 * 1000 // timer)
        self.assertEqual(mbit, round(count_rate * octets * 8 / 1e6))
        (ceiling,) = numbers(r"MUST NOT close windows on one flow faster than (\d+) per second")
        depth, refill = numbers(r"a token bucket of depth (\d+) refilled at (\d+) tokens per second")
        self.assertEqual(ceiling, refill)
        self.assertEqual(1000 // timer_min, ceiling)  # the timer alone never closes more windows than the ceiling
        pps, big_mbit, big, small_mbit, small = numbers(r"at the count cap that is ([\d,]+) datagrams per second, about (\d+) Mbit/s of (\d+)-octet datagrams and about (\d+) Mbit/s of (\d+)-octet ones")
        self.assertEqual(pps, 37 * ceiling)
        self.assertEqual((big_mbit, small_mbit), (round(pps * big * 8 / 1e6), round(pps * small * 8 / 1e6)))
        (entries,) = numbers(r"holds at most `37 x \(64 \+ 1000 x \(maxAuthDelayMs \+ 2 x manifestTimerMs\) / 1000\)` entries, ([\d,]+) at the defaults")
        self.assertEqual(entries, 37 * (depth + refill * (auth_delay + 2 * timer) // 1000))
        megabytes, rate = numbers(r"`maxAuthDelayMs x maxBitrate / 8000` octets, ([\d.]+) MB at (\d+) Mbit/s")
        self.assertEqual(megabytes, auth_delay * rate / 8000)
        (floor,) = numbers(r"`mseq \+ (\d+) <= highest_mseq\(kid, epoch\)`")
        self.assertIn(f"before the signed record of window `mseq + {floor}`, so that at most {floor - 1} later records precede it", text)
        self.assertIn(f"nor close more than `{depth} + {refill} x t` windows in any interval of `t` seconds", text)

    def test_mboned_replay_floor_is_written_without_unsigned_underflow(self):
        stem = "draft-ramadan-mboned-mcast-manifest-00"
        markdown = (ROOT / f"{stem}.md").read_text(encoding="utf-8")
        xml = (ROOT / f"{stem}.xml").read_text(encoding="utf-8")
        self.assertIn("`mseq + 64 <= highest_mseq(kid, epoch)`", markdown)
        self.assertIn("mseq + 64 &lt;= highest_mseq(kid, epoch)", xml)
        for text in (markdown, xml):
            self.assertNotIn("highest_mseq(kid, epoch) - 64", text)
            self.assertNotIn("highest_mseq - 64", text)
            self.assertIn("Neither counter wraps within an epoch", " ".join(text.split()))  # hard-wrapped source

    def test_amt_discovery_combinations_are_unambiguous(self):
        for name in ("draft-ramadan-moq-multicast-01.md", "draft-ramadan-moq-multicast-01.xml"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('"relay": "amt.example.com"', text)
            self.assertIn('"discovery": "dns"', text)
            self.assertIn('"discovery": "driad"', text)
            self.assertNotIn('"discovery": "driad",\n      "relay":', text)
            if name.endswith(".md"):
                self.assertIn("**relay** (string, OPTIONAL)", text)
        markdown = (ROOT / "draft-ramadan-moq-multicast-01.md").read_text(encoding="utf-8")
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
        text = (ROOT / "draft-ramadan-moq-mmt-01.md").read_text(encoding="utf-8")
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
        text = (ROOT / "draft-ramadan-moq-mmt-01.md").read_text(encoding="utf-8")
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
        text = (ROOT / "draft-ramadan-moq-mmt-01.md").read_text(encoding="utf-8")
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
