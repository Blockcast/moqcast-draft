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
    "MOQ-FEC-CORE": ("draft-ramadan-moq-fec-core-01.md", "CORE"),
    "MOQ-FEC-BLOCK": ("draft-ramadan-moq-fec-block-codes-01.md", "BLOCK"),
    "MOQ-FEC-CATALOG": ("draft-ramadan-moq-fec-catalog-01.md", "CATALOG"),
    "MOQ-FEC-MULTICAST": ("draft-ramadan-moq-fec-multicast-01.md", "MCAST"),
    "MOQ-MMT": ("draft-ramadan-moq-mmt-03.md", "MMT"),
    "MOQ-MULTICAST": ("draft-ramadan-moq-multicast-03.md", "MULTICAST"),
}
# drafts revised since the batch posted on 2026-11-02; a draft that is still as posted cites their previous revision
REVISED = {"MOQ-FEC-CORE", "MOQ-FEC-BLOCK", "MOQ-FEC-CATALOG", "MOQ-FEC-MULTICAST", "MOQ-MMT", "MOQ-MULTICAST"}
AS_POSTED: set[str] = set()


def previous(name: str) -> str:
    stem, rev = name.rsplit("-", 1)
    return f"{stem}-{int(rev) - 1:02d}"
FRONT = {
    "CORE": ("draft-ramadan-moq-fec-core-01", "Forward Error Correction for Media over QUIC: Core Mechanism", ["Omar Ramadan", "Marc E. Fiuczynski"]),
    "BLOCK": ("draft-ramadan-moq-fec-block-codes-01", "Block FEC Schemes for Media over QUIC: Reed-Solomon and RaptorQ", ["Omar Ramadan"]),
    "CATALOG": ("draft-ramadan-moq-fec-catalog-01", "Catalog Binding for Forward Error Correction in Media over QUIC", ["Omar Ramadan"]),
    "MCAST": ("draft-ramadan-moq-fec-multicast-01", "Forward Error Correction for Multicast Delivery of Media over QUIC", ["Omar Ramadan"]),
    "MMT": ("draft-ramadan-moq-mmt-03", "MPEG Media Transport (MMT) Packaging for Media over QUIC", ["Omar Ramadan"]),
    "MULTICAST": ("draft-ramadan-moq-multicast-03", "Multicast Delivery and Endpoint Discovery for Media over QUIC", ["Omar Ramadan"]),
}
REQUIRED_IDS = {
    "BLOCK": ["scheme-identifiers", "raptorq", "raptorq-oti", "reed-solomon", "rs-code", "rs-parameters", "scheme-bounds", "repair-layers", "repair-symbols", "mandatory-to-implement", "security-considerations", "iana-considerations", "test-vectors"],
    "CATALOG": ["catalog-fields", "instance-fields", "track-fields", "packaging-values", "signaling-model", "validation", "unknown-keys", "naming-convention", "cmsf", "worked-catalog", "iana-considerations"],
    "MCAST": ["repair-only-endpoints", "multicast-delivery", "deployment-applicability", "multicast-quic", "receiver-repair-policy", "block-classification", "unicast-repair-budget", "provisional-symbols", "symbol-tracks-on-multicast", "security-considerations"],
    "MMT": ["iso-ssbg1-v1", "source-fec-payload-id", "repair-packet", "keyframe-overlay", "overlay-header-extension", "interleaving", "al-fec-message", "atsc-compatibility", "a3sa-signed-region", "iana-considerations"],
}
# The drafts cite other Internet-Drafts through unversioned references, so a built document names
# the latest posted revision of each. These are the sections the drafts cite, with their titles in
# draft-ietf-moq-transport-23 and draft-ietf-moq-msf-02. A number that is not listed here fails:
# check it against the latest posted text and add it with its title.
TRANSPORT_23 = {
    "2.1": "Objects", "2.1.1": "Object Fields", "2.2": "Subgroups", "2.4.1": "Track Naming",
    "3.1": "Subscriptions", "3.1.1": "Pausing Subscriptions", "3.1.4": "Largest Object",
    "3.2.1": "Fetch Object Delivery", "3.2.3": "Relay Fetch Handling", "3.2.4": "Fetch State Management",
    "3.3.1": "Location Filters", "3.3.2": "Range Filters", "3.4": "Fill Semantics",
    "3.4.1": "Opening and Closing Fill Fetch Streams", "3.5": "Joining an Ongoing Track",
    "5.1.1": "Definitions", "5.1.2": "Scheduling Algorithm", "5.2": "Delivery Timeouts and Data Reliability",
    "6.2": "Session establishment", "6.4.2.1": "Request ID", "7.1": "Caching Relays", "7.7": "Publisher Interactions",
    "7.9": "Relay Object Handling", "8.1": "Variable-Length Integers", "8.2": "Location Structure",
    "8.3": "Key-Value-Pair Structure", "8.4": "Track and Object Properties", "9.1.6": "MAX FILTER RANGES", "9.9": "PUBLISH_DONE",
    "9.12": "TRACK_STATUS", "9.19.4": "OBJECT_DELIVERY_TIMEOUT Parameter",
    "9.19.7": "SUBSCRIBER PRIORITY Parameter", "9.19.9": "LOCATION FILTER Parameter",
    "9.19.11": "OBJECTID FILTER Parameter", "9.19.15": "FILL PARAMETERS Parameter",
    "9.19.17": "LARGEST OBJECT Parameter", "9.19.18": "PAUSED Parameter",
    "9.19.19": "NEW GROUP REQUEST Parameter", "10.4": "DEFAULT PUBLISHER PRIORITY", "10.6": "DYNAMIC GROUPS",
    "10.7": "Immutable Properties", "10.8": "Prior Group ID Gap", "11.1.1": "Object Status",
    "11.2": "Datagrams", "11.2.1": "Object Datagram", "11.3.1": "Subgroup Header",
    "11.3.2": "Closing Subgroup Streams", "11.4.1.1": "Flags", "12.4": "Publish Done Codes",
}
MSF_02 = {
    "4.1": "LOC packaging", "4.1.1": "LOC to MOQT Stream mapping", "4.2": "Time-alignment", "4.3": "Packaging for multi-variant track switching",
    "5": "Catalog", "5.1": "Root Catalog Fields", "5.1.1": "MSF version", "5.1.7": "Initialization Data List", "5.2": "Track Object Fields",
    "5.2.2": "Track namespace", "5.2.4": "Packaging", "5.2.8": "Is Live", "5.2.13": "Alternate group",
    "5.2.14": "Initialization reference", "5.2.15": "Dependencies", "5.2.19": "Codec", "5.2.22": "Timescale",
    "5.2.23": "Maximum Bitrate", "5.2.46": "Keyframe spacing", "6": "Media transmission",
    "6.1": "Group numbering", "6.2": "Object Numbering", "6.3": "Multi-Variant Fast Track Switching", "6.3.2": "Calculating Valid Switch Points",
}
# the parameter, message or field that a section defines; the drafts name it just before they cite the section
NAMED_BEFORE = {
    "transport": {"9.12": "TRACK_STATUS", "9.19.4": "OBJECT_DELIVERY_TIMEOUT", "9.19.7": "SUBSCRIBER_PRIORITY",
                  "9.19.9": "LOCATION_FILTER", "9.19.11": "OBJECTID_FILTER", "9.19.15": "FILL_PARAMETERS",
                  "9.19.17": "LARGEST_OBJECT", "9.19.18": "PAUSED", "9.19.19": "NEW_GROUP_REQUEST"},
    "msf": {"4.1.1": "stream mapping", "5.1.1": "version", "5.2.2": "namespace", "5.2.4": "packaging", "5.2.8": "isLive", "5.2.13": "altGroup", "5.2.14": "initRef",
            "5.2.15": "depends", "5.2.19": "codec", "5.2.22": "timescale", "5.2.23": "bitrate",
            "5.2.46": "keyframeSpacing"},
}
CITED = re.compile(r"\[@[!?]I-D\.ietf-moq-(transport|msf)\],? Sections? (\d+(?:\.\d+)*(?:(?:, (?:and )?| and )\d+(?:\.\d+)*)*)")
# names that draft-ietf-moq-transport-23 does not have: it renamed the first, replaced the second by PAUSED
# with the opposite values, and has no message of the third name
GONE_FROM_TRANSPORT = re.compile(r"\b(KEY_VALUE_FORMATTING_ERROR|FORWARD|UNSUBSCRIBE)\b")
KEYWORDS = re.compile(r"\b(MUST NOT|MUST|REQUIRED|SHALL NOT|SHALL|SHOULD NOT|SHOULD|NOT RECOMMENDED|RECOMMENDED|MAY|OPTIONAL)\b")
IPR = re.compile(r"(?i)\bpatent|\bIPR\b|intellectual property|licen[cs]e|royalt")


def present() -> dict[str, Path]:
    return {key: ROOT / name for name, key in SET.values() if (ROOT / name).exists()}


def body(text: str) -> str:
    """The document after its mmark front matter."""
    first = text.index("%%%")
    second = text.index("%%%", first + 3)
    return text[second + 3:]


def flat(text: str) -> str:
    """The text with every run of white space as one space, so a phrase matches across line breaks."""
    return " ".join(text.split())


def without_change_log(text: str) -> str:
    """The document without its change log, which may name what an earlier revision said."""
    return re.sub(r"(?ms)^# (?:Change Log|Changes from )[^\n]*\n.*?(?=^# |\Z)", "", text)


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
                        self.assertIn(blocks[anchor], {filename[:-3]} | ({previous(filename[:-3])} if anchor in REVISED and key in AS_POSTED else set()), f"{key} cites {anchor} at the wrong revision")

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

    def test_cited_sections_are_those_of_the_latest_posted_revisions(self):
        tables = {"transport": TRANSPORT_23, "msf": MSF_02}
        checked = 0
        for key, text in self.text.items():
            text = flat(text)
            for m in CITED.finditer(text):
                draft = m.group(1)
                for number in re.findall(r"\d+(?:\.\d+)*", m.group(2)):
                    with self.subTest(draft=key, cites=draft, section=number):
                        self.assertIn(number, tables[draft], f"{key} cites {draft} Section {number}, which is not in the table of its latest revision")
                        name = NAMED_BEFORE[draft].get(number)
                        if name:
                            before = text[max(0, m.start() - 200) : m.start()].lower()
                            self.assertIn(name.lower(), before, f"{key} cites {draft} Section {number} ({tables[draft][number]}) without naming {name}")
                        checked += 1
        if "MMT" in self.text and "MULTICAST" in self.text:
            self.assertGreater(checked, 100)

    def test_names_and_rules_are_those_of_the_latest_posted_revisions(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                self.assertEqual(GONE_FROM_TRANSPORT.findall(without_change_log(text)), [])
        if "CORE" in self.text:
            core = flat(self.text["CORE"])
            self.assertIn("MUST close the session with MALFORMED_KEY_VALUE", core)
            # transport-23 Section 8.4: more instances of a supported Property than allowed make the track malformed
            self.assertIn("carries more than one, a receiver that implements this document MUST also treat the track as malformed", core)
            self.assertIn("The count is over both lists because [@!I-D.ietf-moq-transport] Section 10.7", core)
            self.assertIn('"MOQ Properties" registry of [@!I-D.ietf-moq-transport] (Section 16.8 of that document)', core)
            # the same transport-23 Section 8.4 rule for FEC Delivery Info (Section 5.7)
            self.assertIn("When an object it receives carries more than one, a receiver that implements this Property MUST also treat the track as malformed", core)
            # Section 14.4: SUBSCRIBE_TRACKS is a request for every repair track under its prefix
            self.assertIn("a repair or symbol track that a receiver did not request, by a SUBSCRIBE or FETCH for that track or a SUBSCRIBE_TRACKS whose namespace prefix covers it", core)
        if "CATALOG" in self.text:
            # enhancementRepair is not defined, and the receiver fails closed under rule 4 rather than rejecting the catalog
            self.assertIn("a catalog that carries it violates rule 4 of (#validation), for which the receiver fails closed", flat(self.text["CATALOG"]))
        if "MULTICAST" in self.text:
            multicast = flat(self.text["MULTICAST"])
            # transport-23 Section 3.1.1: PAUSED set to 1 pauses, PAUSED set to 0 resumes
            self.assertIn("To pause a subscription, the receiver sends a REQUEST_UPDATE with the PAUSED parameter set to 1", multicast)
            self.assertIn("resumes a paused subscription with a REQUEST_UPDATE that sets PAUSED to 0", multicast)
            # a replacement key never reuses a kid, so a pinned epoch floor cannot block it
            self.assertIn("The key that replaces a compromised one MUST carry a `kid` that no earlier key of the catalog has carried", multicast)
            self.assertIn("This document defines no authorization of receivers on the multicast path.", multicast)
        if "MMT" in self.text:
            mmt = flat(self.text["MMT"])
            # msf-02 Section 6 leaves the stream mapping to the packaging; msf-01 put each object on a new stream
            self.assertNotIn("maps each object to a new stream", mmt)
            self.assertIn("Section 6 leaves the mapping of objects to streams to the packaging of each track", mmt)
            # msf-02 Sections 4.3, 5.2.46 and 6.3 are new; a switching set with an intra-only track follows them
            self.assertNotIn("does not carry the `keyframeSpacing` field", mmt)
            self.assertIn("its publisher MUST follow [@!I-D.ietf-moq-msf] Section 4.3", mmt)
            self.assertIn("Every track MUST carry `keyframeSpacing`", mmt)
            self.assertIn("so that the first Group of every track is Group 0", mmt)
            self.assertIn("A publisher MUST NOT leave a numeric gap, whether after a restart", mmt)
            self.assertIn("is called a mixed-interval switching set in this document", mmt)
            self.assertIn("An mmtp track that is not in a mixed-interval switching set MUST NOT carry `keyframeSpacing`", mmt)
            self.assertIn("is valid when `(g * S + N) / T` is an integer", mmt)
        if "CATALOG" in self.text:
            catalog = flat(self.text["CATALOG"])
            # msf-02 Section 5.2.15 no longer says in which namespace a dependency is resolved
            self.assertNotIn("does for `depends`", catalog)
            self.assertIn("as a string entry of `depends` does ([@!I-D.ietf-moq-msf] Section 5.2.15), and a receiver resolves each in the source track's Track Namespace", catalog)
        if "CORE" in self.text:
            # msf-02 Section 4.1.1: by default the objects of a Group share one Subgroup, so an example that loses
            # two objects of a Group to a delivery timeout and receives the rest declares the "object" mapping
            self.assertIn('"packagingMetadata": "streamMapping=object"', self.text["CORE"])
            self.assertIn('The track declares the "object" stream mapping ([@?I-D.ietf-moq-msf] Section 4.1.1)', self.text["CORE"])
        # msf-02 Section 5.1.1: the root `version` is a String, and "draft-02" names that revision
        for key, text in self.text.items():
            if key in AS_POSTED:
                continue
            for m in re.finditer(r"^~~~ json\n(\{.*?)^~~~$", text, re.S | re.M):
                document = json.loads(m.group(1))
                if "tracks" in document:
                    with self.subTest(draft=key, at=text[: m.start()].count("\n") + 1):
                        self.assertEqual(document.get("version"), "draft-02")

    def test_fec_source_info_is_requested_as_0x85_and_0x11_is_retired(self):
        if "CORE" not in self.text:
            self.skipTest("the core draft is not present")
        core = self.text["CORE"]
        rows = re.findall(r"^\| (\S+) \| (FEC_[A-Z_]+) \| Object \|", core, re.M)
        self.assertEqual(rows, [("0x85", "FEC_SOURCE_INFO"), ("TBD1", "FEC_UNIT_START"), ("TBD2", "FEC_DELIVERY_INFO")])
        value = int(rows[0][0], 16)
        self.assertEqual(value % 2, 1, "a value of bytes needs an odd type")
        self.assertTrue(0x80 <= value <= 0x37FF, "the Specification Required range of draft-ietf-moq-transport-23 Section 16.8")
        self.assertNotEqual((value - 0x9D) % 0x7F, 0, "a grease value")
        self.assertIn("whose type is the odd value 0x85 (Section 15.1)", core)
        self.assertIn("0x85 is the value this document requests", core)
        self.assertIn("It is requested as 0x85, an odd value from the range 0x80 to 0x37FF", core)
        # draft-ietf-moq-loc-05 assigns 0x11 to its Codec String Property
        self.assertIn("MUST NOT send 0x11 for this purpose and MUST NOT read a Property of type 0x11 as FEC Source Info", core)
        for stale in ("whose type is the odd value 0x11", "0x11 is the value this document requests", "asks for 0x11", "| 0x11 |"):
            self.assertFalse(stale in core, f"the core draft still says {stale!r}")
        for key, text in self.text.items():
            if key != "CORE":
                with self.subTest(draft=key):
                    self.assertNotRegex(flat(text), r"FEC Source Info Object Property \(type", "the type is stated in the core draft only")

    def test_changes_appendix_records_the_move(self):
        for key, text in self.text.items():
            with self.subTest(draft=key):
                if key in ("MMT", "MULTICAST"):
                    name = SET["MOQ-MMT" if key == "MMT" else "MOQ-MULTICAST"][0][:-6]
                    self.assertRegex(text, rf"(?m)^## Changes Since {re.escape(name)}-01$")
                else:
                    self.assertIn("# Changes from draft-ramadan-moq-fec-01", text)

    def test_moot_keyframe_repair_is_admission_and_deadline_scoped(self):
        text = self.text["MCAST"]
        start = text.index("{#moot-keyframe-repair}")
        end = text.index("{#other-video-blocks}", start)
        section = text[start:end]

        self.assertRegex(
            section,
            r"(?s)1\.\s+The receiver holds a RAP the receiver has already admitted complete",
        )
        self.assertRegex(
            section,
            r"(?s)2\.\s+The repair cannot arrive.*?current time is not earlier than it",
        )
        self.assertIn("while its playout deadline has not passed, the media it recovers", section)
        self.assertNotIn("cancelling it stalls nothing", section)

        changes = text[text.index("# Changes from draft-ramadan-moq-fec-multicast-00") :]
        self.assertIn("once a newer RAP had been admitted complete", changes)


if __name__ == "__main__":
    unittest.main()
