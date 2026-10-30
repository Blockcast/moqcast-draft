#!/usr/bin/env python3
"""Recompute the Reed-Solomon test vectors of draft-ramadan-moq-fec from scratch.

The code is the Cauchy Reed-Solomon code of the draft's Section 4.4:
GF(2^8) mod 0x11D, A[i][j] = 1 / (alpha^(254 - i) + alpha^j), and
r_j[u] = sum over i of A[i][j] * s_i[u].  No third-party packages.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS_HEADING = "# Reed-Solomon Test Vectors"


def drafts_with_vectors() -> list[Path]:
    """Every draft that publishes the Reed-Solomon vectors: -01 and the block-codes companion of the split."""
    return [p for p in sorted(ROOT.glob("draft-ramadan-moq-*.md")) if VECTORS_HEADING in p.read_text(encoding="utf-8")]


def gmul(a: int, b: int) -> int:
    """Carry-less product of two bytes, reduced modulo x^8 + x^4 + x^3 + x^2 + 1."""
    product = 0
    for bit in range(8):
        if b >> bit & 1:
            product ^= a << bit
    for bit in range(14, 7, -1):
        if product >> bit & 1:
            product ^= 0x11D << (bit - 8)
    return product


def gpow(a: int, n: int) -> int:
    result = 1
    for _ in range(n):
        result = gmul(result, a)
    return result


def ginv(a: int) -> int:
    return gpow(a, 254)  # a^255 = 1 for every nonzero a


def entry(i: int, j: int) -> int:
    return ginv(gpow(2, 254 - i) ^ gpow(2, j))


def combine(pairs) -> bytearray:
    """XOR of coefficient * symbol over (coefficient, symbol) pairs, byte by byte."""
    out = None
    for coefficient, symbol in pairs:
        out = bytearray(len(symbol)) if out is None else out
        for u, byte in enumerate(symbol):
            out[u] ^= gmul(coefficient, byte)
    return out


def encode(source: list[bytes], rs_id: int) -> bytes:
    return bytes(combine((entry(i, rs_id), s) for i, s in enumerate(source)))


def recover(k: int, source: dict[int, bytes], repair: dict[int, bytes]) -> list[bytes]:
    """Solve for the missing rows, in ESI order, from as many held repair symbols."""
    missing = [i for i in range(k) if i not in source]
    columns = sorted(repair)[: len(missing)]
    assert len(columns) == len(missing), "not enough symbols to recover"
    rows = []
    for j in columns:
        rhs = bytearray(repair[j])
        known = combine((entry(i, j), s) for i, s in source.items())
        if known is not None:
            rhs = bytearray(x ^ y for x, y in zip(rhs, known))
        rows.append(([entry(i, j) for i in missing], rhs))
    n = len(rows)
    for c in range(n):  # Gauss-Jordan elimination over GF(2^8)
        p = next(r for r in range(c, n) if rows[r][0][c])
        rows[c], rows[p] = rows[p], rows[c]
        f = ginv(rows[c][0][c])
        rows[c] = ([gmul(f, v) for v in rows[c][0]], bytearray(gmul(f, v) for v in rows[c][1]))
        for r in range(n):
            g = rows[r][0][c]
            if r != c and g:
                rows[r] = (
                    [v ^ gmul(g, w) for v, w in zip(rows[r][0], rows[c][0])],
                    bytearray(v ^ gmul(g, w) for v, w in zip(rows[r][1], rows[c][1])),
                )
    return [bytes(rhs) for _, rhs in rows]


def symbols(hexes: list[str]) -> list[bytes]:
    return [bytes.fromhex(h) for h in hexes]


def appendix_vectors(draft: Path) -> dict[str, dict]:
    text = draft.read_text(encoding="utf-8")
    start = text.index(VECTORS_HEADING)
    appendix = text[start : text.index("\n# ", start + 1)]
    found = {}
    for raw in re.findall(r"^~~~ json\n(.*?)^~~~$", appendix, re.S | re.M):
        vector = json.loads(raw)
        found[vector["vector"]] = vector
    return found


def each_draft(method):
    """Run a vector check against every draft that publishes the vectors."""

    def wrapper(self):
        for name, vectors in self.all_vectors.items():
            with self.subTest(draft=name):
                self.vectors = vectors
                method(self)

    wrapper.__name__ = method.__name__
    wrapper.__doc__ = method.__doc__
    return wrapper


class ReedSolomonVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_vectors = {p.name: appendix_vectors(p) for p in drafts_with_vectors()}
        assert cls.all_vectors, "no draft publishes the Reed-Solomon test vectors"

    @each_draft
    def test_every_vector_is_published(self):
        self.assertEqual(set(self.vectors), {"field", "matrix", "encode", "short-block", "layers"})

    @each_draft
    def test_field(self):
        field = self.vectors["field"]
        self.assertEqual(int(field["polynomial"], 16), 0x11D)
        self.assertEqual(gpow(2, 8), 0x1D)
        for exponent, value in field["alphaPowers"].items():
            self.assertEqual(gpow(2, int(exponent)), int(value, 16), exponent)
        for value, inverse in field["inverses"].items():
            self.assertEqual(gmul(int(value, 16), int(inverse, 16)), 1, value)

    @each_draft
    def test_matrix_entries(self):
        for item in self.vectors["matrix"]["entries"]:
            i, j = item["i"], item["j"]
            self.assertLessEqual(i + j, 253, item)  # inside the K + P <= 255 bound
            self.assertEqual(gpow(2, 254 - i), int(item["x"], 16), item)
            self.assertEqual(gpow(2, j), int(item["y"], 16), item)
            self.assertEqual(entry(i, j), int(item["A"], 16), item)

    @each_draft
    def test_encode(self):
        vector = self.vectors["encode"]
        source = symbols(vector["source"])
        self.assertEqual(len(source), vector["SSB_length"])
        self.assertTrue(all(len(s) == vector["T"] for s in source))
        self.assertEqual([encode(source, j) for j in vector["RS_ID"]], symbols(vector["repair"]))

    @each_draft
    def test_short_block_equals_zero_padded_full_block_and_recovers(self):
        vector = self.vectors["short-block"]
        source = symbols(vector["source"])
        self.assertEqual(len(source), vector["SSB_length"])
        self.assertLess(vector["SSB_length"], vector["K"])
        padded = source + [bytes(vector["T"])] * (vector["K"] - vector["SSB_length"])
        repair = symbols(vector["repair"])
        self.assertEqual([encode(source, j) for j in vector["RS_ID"]], repair)
        self.assertEqual([encode(padded, j) for j in vector["RS_ID"]], repair)
        held = vector["received"]
        got = recover(
            vector["SSB_length"],
            {i: source[i] for i in held["ESI"]},
            {j: repair[vector["RS_ID"].index(j)] for j in held["RS_ID"]},
        )
        self.assertEqual(got, symbols(vector["recovered"]))

    @each_draft
    def test_layers_are_disjoint_columns_and_a_non_prefix_layer_recovers(self):
        vector = self.vectors["layers"]
        source = symbols(vector["source"])
        by_rs_id = {}
        offset = 0
        for layer in vector["layers"]:
            self.assertEqual(layer["RS_ID"], list(range(offset, offset + len(layer["RS_ID"]))))
            offset += len(layer["RS_ID"])
            for j, value in zip(layer["RS_ID"], symbols(layer["repair"])):
                self.assertEqual(encode(source, j), value, j)
                by_rs_id[j] = value
        self.assertEqual(offset, vector["RSB_length"])
        self.assertLessEqual(vector["K"] + vector["RSB_length"], 255)
        # A column does not depend on P: RS_IDs shared with the encode vector match it.
        single = self.vectors["encode"]
        if single["source"] == vector["source"]:
            for j, value in zip(single["RS_ID"], symbols(single["repair"])):
                self.assertEqual(by_rs_id[j], value, j)
        held = vector["received"]
        got = recover(
            vector["SSB_length"],
            {i: source[i] for i in held["ESI"]},
            {j: by_rs_id[j] for j in held["RS_ID"]},
        )
        self.assertEqual(got, symbols(vector["recovered"]))

    def test_reed_solomon_catalog_examples_respect_the_255_bound(self):
        seen = 0
        for path in sorted(ROOT.glob("draft-ramadan-moq-*.md")):
            text = path.read_text(encoding="utf-8")
            for raw in re.findall(r"^~~~ json\n(.*?)^~~~$", text, re.S | re.M):
                try:
                    catalog = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # published member fragments such as "fec": {...}
                if not isinstance(catalog, dict) or not isinstance(catalog.get("tracks"), list):
                    continue
                tracks = catalog["tracks"]
                for track in tracks:
                    name = track.get("name")
                    fec = track.get("fec")
                    if isinstance(fec, dict):  # draft-ramadan-moq-fec-01 shape: one instance, "algorithm", "depends"
                        if fec.get("algorithm") != "reed-solomon":
                            continue
                        seen += 1
                        where = f"{path.name}:{name}"
                        repairs = [t for t in tracks if t.get("depends") == [name]]
                        layers = sum(t["repairSymbols"] for t in repairs if t.get("repairLayer", 0) >= 1)
                        self.assertLessEqual(fec["sourceSymbols"] + fec["repairSymbols"] + layers, 255, where)
                        for overlay in (t for t in repairs if t.get("scope") == "keyframe"):
                            self.assertLessEqual(overlay["sourceSymbols"] + overlay["repairSymbols"], 255, where)
                    elif isinstance(fec, list):  # the split's shape: instances with "scheme", repair tracks by "source" and "instanceId"
                        named = {inst.get("repairTrack"): inst.get("instanceId", 0) for inst in fec if isinstance(inst, dict)}
                        # a keyframe overlay (draft-ramadan-moq-mmt-02 "scope": "keyframe") is an instance of its own
                        # that shares the base instance's scheme, so it is bounded here like every other instance
                        base = next((i for i in fec if isinstance(i, dict) and i.get("instanceId", 0) == 0), {})
                        for inst in fec:
                            if not isinstance(inst, dict):
                                continue
                            scheme = inst.get("scheme", base.get("scheme") if inst.get("scope") == "keyframe" else None)
                            if scheme != "reed-solomon":
                                continue
                            seen += 1
                            iid = inst.get("instanceId", 0)
                            where = f"{path.name}:{name}:instance {iid}"
                            repairs = [
                                t for t in tracks
                                if t.get("packaging") == "fec-repair"
                                and (t.get("source") == name or t.get("name") in named)
                                and named.get(t.get("name"), t.get("instanceId", 0)) == iid
                            ]
                            layers = sum(t["repairSymbols"] for t in repairs if t.get("repairLayer", 0) >= 1)
                            self.assertLessEqual(inst["sourceSymbols"] + inst["repairSymbols"] + layers, 255, where)
        self.assertGreater(seen, 0, "no reed-solomon catalog example found")

if __name__ == "__main__":
    unittest.main()
