#!/usr/bin/env python3
"""Contracts for the split of draft-ramadan-moq-fec-01 into a core and companion drafts.

Each check runs over the drafts of the split that are present in the repository, so the
checks hold while the drafts land one pull request at a time.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# anchor -> (file, KEY); KEY is the token prefix the drafts were written with
SET = {
    "MOQ-FEC-CORE": ("draft-ramadan-moq-fec-core-00.md", "CORE"),
    "MOQ-FEC-BLOCK": ("draft-ramadan-moq-fec-block-codes-00.md", "BLOCK"),
    "MOQ-FEC-CATALOG": ("draft-ramadan-moq-fec-catalog-00.md", "CATALOG"),
    "MOQ-FEC-MULTICAST": ("draft-ramadan-moq-fec-multicast-00.md", "MCAST"),
    "MOQ-MMT": ("draft-ramadan-moq-mmt-02.md", "MMT"),
    "MOQ-MULTICAST": ("draft-ramadan-moq-multicast-02.md", "MULTICAST"),
}
FRONT = {
    "CORE": ("draft-ramadan-moq-fec-core-00", "Forward Error Correction for Media over QUIC: Core Mechanism", ["Omar Ramadan", "Marc E. Fiuczynski"]),
    "BLOCK": ("draft-ramadan-moq-fec-block-codes-00", "Block FEC Schemes for Media over QUIC: Reed-Solomon and RaptorQ", ["Omar Ramadan"]),
    "CATALOG": ("draft-ramadan-moq-fec-catalog-00", "Catalog Binding for Forward Error Correction in Media over QUIC", ["Omar Ramadan"]),
    "MCAST": ("draft-ramadan-moq-fec-multicast-00", "Forward Error Correction for Multicast Delivery of Media over QUIC", ["Omar Ramadan"]),
    "MMT": ("draft-ramadan-moq-mmt-02", "MPEG Media Transport (MMT) Packaging for Media over QUIC", ["Omar Ramadan"]),
    "MULTICAST": ("draft-ramadan-moq-multicast-02", "Multicast Delivery and Endpoint Discovery for Media over QUIC", ["Omar Ramadan"]),
}
REQUIRED_IDS = {
    "BLOCK": ["scheme-identifiers", "raptorq", "raptorq-oti", "reed-solomon", "rs-code", "rs-parameters", "scheme-bounds", "repair-layers", "repair-symbols", "mandatory-to-implement", "security-considerations", "iana-considerations", "test-vectors"],
    "CATALOG": ["catalog-fields", "instance-fields", "track-fields", "packaging-values", "signaling-model", "validation", "unknown-keys", "naming-convention", "cmsf", "worked-catalog", "iana-considerations"],
    "MCAST": ["repair-only-endpoints", "multicast-delivery", "deployment-applicability", "multicast-quic", "receiver-repair-policy", "block-classification", "unicast-repair-budget", "provisional-symbols", "symbol-tracks-on-multicast", "security-considerations"],
    "MMT": ["iso-ssbg1-v1", "source-fec-payload-id", "repair-packet", "keyframe-overlay", "overlay-header-extension", "interleaving", "al-fec-message", "atsc-compatibility", "a3sa-signed-region", "iana-considerations"],
}
KEYWORDS = re.compile(r"\b(MUST NOT|MUST|REQUIRED|SHALL NOT|SHALL|SHOULD NOT|SHOULD|NOT RECOMMENDED|RECOMMENDED|MAY|OPTIONAL)\b")
IPR = re.compile(r"(?i)\bpatent|\bIPR\b|intellectual property|licen[cs]e|royalt")


def present() -> dict[str, Path]:
    return {key: ROOT / name for name, key in SET.values() if (ROOT / name).exists()}


def body(text: str) -> str:
    """The document after its mmark front matter."""
    first = text.index("%%%")
    second = text.index("%%%", first + 3)
    return text[second + 3:]


def headings(text: str) -> dict[str, tuple[str, str]]:
    """id -> (number, title) for every heading, numbered the way mmark/xml2rfc do (appendices lettered)."""
    counters = [0] * 6
    back = fence = False
    pending = None
    out: dict[str, tuple[str, str]] = {}
    numbers: dict[str, str] = {}
    for line in text.split("\n"):
        if line.startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if line.strip() == "{backmatter}":
            back, counters = True, [0] * 6
            continue
        ial = re.match(r"^\{#([A-Za-z0-9_.-]+)(?:\s+[^}]*)?\}\s*$", line)
        if ial:
            pending = ial.group(1)
            continue
        if line.startswith("{numbered="):
            pending = None
            continue
        m = re.match(r"^(#{1,4}) (.+?)\s*$", line)
        if not m:
            pending = None
            continue
        depth = len(m.group(1))
        counters[depth - 1] += 1
        for k in range(depth, 6):
            counters[k] = 0
        number = chr(ord("A") + counters[0] - 1) if back else str(counters[0])
        if depth > 1:
            number += "." + ".".join(str(c) for c in counters[1:depth])
        numbers[number] = m.group(2)
        if pending:
            out[pending] = (number, m.group(2))
        pending = None
    out["__numbers__"] = numbers  # type: ignore[assignment]
    return out


def sections(text: str):
    """Yield (heading line, section text up to the next heading of any level), fences respected."""
    lines = text.split("\n")
    fence = False
    current, buf = None, []
    for line in lines:
        if line.startswith(("```", "~~~")):
            fence = not fence
        if not fence and re.match(r"^#{1,4} ", line):
            if current is not None:
                yield current, "\n".join(buf)
            current, buf = line, []
            continue
        buf.append(line)
    if current is not None:
        yield current, "\n".join(buf)


class SplitContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafts = present()
        if not cls.drafts:
            raise unittest.SkipTest("no draft of the split is present")
        cls.text = {key: path.read_text(encoding="utf-8") for key, path in cls.drafts.items()}

    def test_front_matter_matches_the_decided_set(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                value, title, authors = FRONT[key]
                front = text[: text.index("%%%", 3)]
                self.assertIn(f'value = "{value}"', front)
                self.assertIn(f'title = "{title}"', front)
                self.assertIn('name = "Internet-Draft"', front)
                self.assertIn('workgroup = "moq"', front)
                self.assertIn('ipr = "trust200902"', front)
                self.assertEqual(re.findall(r'^fullname = "([^"]+)"', front, re.M), authors)

    def test_no_unresolved_cross_document_tokens(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                self.assertEqual(re.findall(r"\{\{[A-Z]+:[A-Za-z0-9_.-]+\}\}", text), [])

    def test_heading_ids_are_unique_and_the_required_ones_exist(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                ids = re.findall(r"^\{#([A-Za-z0-9_.-]+)(?:\s+[^}]*)?\}\s*$", text, re.M)
                self.assertEqual(len(ids), len(set(ids)), "duplicate heading id")
                for required in REQUIRED_IDS.get(key, []):
                    self.assertIn(required, ids, f"{key} lacks the heading id {required}")

    def test_cross_document_section_pointers_resolve(self):
        pattern = re.compile(
            r"(?:(Section|Appendix) ([A-Z]|\d+(?:\.\d+)*) of \[@[!?]([A-Z-]+)\]"
            r"|\[@[!?]([A-Z-]+)\](?:,)? (Section|Appendix) ([A-Z]|\d+(?:\.\d+)*))"
        )
        checked = 0
        for key, text in self.text.items():
            for m in pattern.finditer(text):
                kind, number, anchor = (m.group(1), m.group(2), m.group(3)) if m.group(3) else (m.group(5), m.group(6), m.group(4))
                if anchor not in SET:
                    continue
                target_key = SET[anchor][1]
                if target_key not in self.text:
                    continue  # the target draft is not in the repository yet
                numbers = headings(self.text[target_key])["__numbers__"]
                with self.subTest(draft=key, anchor=anchor, pointer=f"{kind} {number}"):
                    self.assertIn(number, numbers, f"{key} cites {anchor} {kind} {number}, which does not exist")
                    self.assertEqual(kind == "Appendix", number.isalpha())
                    checked += 1
        if len(self.text) > 1:  # the core alone has nothing of the split to point into
            self.assertGreater(checked, 0)

    def test_reference_blocks_match_the_citations(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                cited = {a for a in re.findall(r"\[@[!?]([A-Za-z0-9.-]+)", text) if not a.startswith(("RFC", "I-D."))}
                blocks = {}
                for m in re.finditer(r"<reference anchor='([^']+)'[^>]*>(.*?)</reference>", text, re.S):
                    series = re.search(r"<seriesInfo name='[^']+' value='([^']+)'", m.group(2))
                    blocks[m.group(1)] = series.group(1) if series else None
                self.assertEqual(cited - set(blocks), set(), f"{key} cites anchors without a reference block")
                for anchor, (filename, _) in SET.items():
                    if anchor in blocks:
                        self.assertEqual(blocks[anchor], filename[:-3], f"{key} cites {anchor} at the wrong revision")

    def test_no_bcp14_keyword_in_informative_text(self):
        for key, text in self.text.items():
            for heading, content in sections(body(text)):
                first = content.strip().split("\n\n", 1)[0] if content.strip() else ""
                if not re.search(r"\b(is|are) informative\b", first):
                    continue
                with self.subTest(draft=key, section=heading):
                    self.assertEqual(KEYWORDS.findall(content), [], f"BCP 14 keyword in informative text under {heading!r}")

    def test_no_ipr_or_patent_wording(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                self.assertIsNone(IPR.search(body(text)))

    def test_json_examples_parse(self):
        for key, text in self.text.items():
            for m in re.finditer(r"^~~~ json\n(.*?)^~~~$", text, re.S | re.M):
                source = m.group(1).strip()
                if source.startswith(('"fec":', '"auth":')):
                    continue
                with self.subTest(draft=key, at=text[: m.start()].count("\n") + 1):
                    json.loads(source)

    def test_scheme_bounds_live_in_the_block_codes_draft(self):
        if "BLOCK" in self.text:
            block = self.text["BLOCK"]
            self.assertIn("255", block)
            self.assertIn("56403", block)
            self.assertRegex(block, r"multiple of 8")
            self.assertRegex(block, r'(?s)# IANA Considerations.*"reed-solomon".*"raptorq"')
        if "CORE" in self.text:
            core = self.text["CORE"]
            self.assertNotRegex(core, r'\| *"none" *\|', "the core registers no scheme")
            for constant in ("2^24 - 1", "2^62", "13 + T"):
                self.assertIn(constant, core)
        if "CATALOG" in self.text:
            self.assertIn("[@!MOQ-FEC-BLOCK]", self.text["CATALOG"], "the binding cites the block-codes draft for scheme bounds")
        if "MMT" in self.text:
            self.assertRegex(self.text["MMT"], r"12 \+ 13 \+ T|25 \+ T")

    def test_changes_appendix_records_the_move(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                if key in ("MMT", "MULTICAST"):
                    name = SET["MOQ-MMT" if key == "MMT" else "MOQ-MULTICAST"][0][:-6]
                    self.assertRegex(text, rf"(?m)^## Changes Since {re.escape(name)}-01$")
                else:
                    self.assertIn("# Changes from draft-ramadan-moq-fec-01", text)


if __name__ == "__main__":
    unittest.main()
