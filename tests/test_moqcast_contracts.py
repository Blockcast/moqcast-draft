#!/usr/bin/env python3
"""Small source-backed checks for the published moqcast examples."""

from __future__ import annotations

import argparse
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
    for i, opener in enumerate(lines):
        if language is None and opener.strip() != "~~~":
            continue
        if language is not None and not re.fullmatch(rf"\s*~~~\s+{language}\s*", opener):
            continue
        end = i + 1
        while end < len(lines) and lines[end].strip() != "~~~":
            end += 1
        if end == len(lines):
            raise AssertionError(f"unterminated fence at line {i + 1}")
        yield i + 1, "\n".join(lines[i + 1 : end])


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
                self.assertEqual(fec["algorithm"], "raptorq", where)
                self.assertTrue(all(isinstance(fec[k], int) and fec[k] >= 1 for k in ("sourceSymbols", "repairSymbols")), where)
                self.assertTrue(isinstance(fec["symbolSize"], int) and fec["symbolSize"] % 8 == 0 and fec["symbolSize"] > 0, where)
                repair = [item for item in tracks if item.get("name") == fec["repairTrack"]]
                self.assertEqual(len(repair), 1, f"missing repair track for {where}")
                self.assertEqual(repair[0].get("packaging"), "fec-repair", where)
                if "depends" in repair[0]:
                    self.assertIn(track.get("name"), repair[0]["depends"], where)
        self.assertGreater(seen, 0)

    def test_mmt_negative_time_rows_compute_admission_and_unique_groups(self):
        text = (ROOT / "draft-ramadan-moq-mmt-00.md").read_text(encoding="utf-8")
        part = self.sec(text, "Negative authored timestamps use", "### Catalog Signaling")
        anchor = int(re.search(r"presentationAnchorTicks:\s*(-?\d+)", part).group(1))
        duration = int(re.search(r"groupDurationTicks:\s*(\d+)", part).group(1))
        row_block = next(raw for _, raw in fences(part) if "first PTS" in raw)
        rows = [tuple(map(int, row)) for row in re.findall(r"first PTS =\s*(-?\d+): relative_ticks =\s*(-?\d+)\s*-> group (-?\d+)", row_block)]
        self.assertEqual((anchor, duration), (-180000, 180000))
        self.assertEqual(rows, [(-90000, 90000, 0), (90000, 270000, 1)])
        for pts, relative, group in rows:
            self.assertEqual((relative, group), (pts - anchor, relative // duration))
        self.assertEqual([row[2] for row in rows], sorted({row[2] for row in rows}))
        normalized = " ".join(part.split())
        self.assertIn("`presentationAnchorTicks: 0` is invalid", part)
        self.assertIn("publisher rejects MPU 0 instead of mapping it to group 0", normalized)
        policy = self.sec(text, "The publisher MUST choose `presentationAnchorTicks`", "Timeline origin:")
        self.assertIn("MUST reject that MPU", policy)
        self.assertIn("MUST NOT clamp", policy)
        self.assertIn("computed Group number MUST be strictly greater than the Group number", " ".join(text.split()))

    def test_packet_budget_arithmetic(self):
        text = (ROOT / "draft-ramadan-moq-fec-00.md").read_text(encoding="utf-8")
        budget = self.sec(text, "Parameter consistency:", "The catalog envelope")
        rows = re.findall(r"ceil\(([\d,]+) / ([\d,]+)\) = ([\d,]+)", budget)
        self.assertEqual(len(rows), 2)
        for media, capacity, packets in rows:
            media, capacity, packets = (int(n.replace(",", "")) for n in (media, capacity, packets))
            self.assertEqual(packets, (media + capacity - 1) // capacity)
        for k, capacity, total in re.findall(r"= (\d+) x (\d+) = ([\d,]+)` bytes", budget):
            self.assertEqual(int(total.replace(",", "")), int(k) * int(capacity))

    def test_mmt_published_bframe_and_tick_only_examples(self):
        text = (ROOT / "draft-ramadan-moq-mmt-00.md").read_text(encoding="utf-8")

        bframe = next(
            (json.loads(raw) for _, raw in fences(text, "json") if '"samplePtsInDecodeOrder"' in raw),
            None,
        )
        self.assertIsNotNone(bframe, "B-frame presentation-order JSON example is missing")
        self.assertEqual(
            (bframe["timescale"], bframe["presentationAnchorTicks"], bframe["groupDurationTicks"]),
            (90000, 0, 180000),
        )
        pts = bframe["samplePtsInDecodeOrder"]
        self.assertEqual(bframe["ticks"], min(pts))
        self.assertEqual(
            bframe["groupNumber"],
            (bframe["ticks"] - bframe["presentationAnchorTicks"]) // bframe["groupDurationTicks"],
        )
        self.assertNotEqual(pts[0], bframe["ticks"])
        self.assertEqual(
            (pts[0] - bframe["presentationAnchorTicks"]) // bframe["groupDurationTicks"],
            bframe["groupNumber"] + 1,
        )

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

    def test_fec_published_json_vectors_compute_blocks_and_short_tail(self):
        text = (ROOT / "draft-ramadan-moq-fec-00.md").read_text(encoding="utf-8")
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
