"""Recompute the RaptorQ test vectors of the block-codes draft with an RFC 6330 implementation.

Optional: skipped when the `raptorq` package (the Python binding of the cberner RaptorQ
implementation, `pip install raptorq`) is not installed.  Every draft whose appendix is
headed "RaptorQ Test Vectors" is checked; each vector is encoded from its source symbols
and the repair symbols at RS_ID 0.. are compared at ESI = SSB_length + RS_ID, and a vector
with a `received` set is decoded from exactly that set.
"""
import json
import re
import unittest
from pathlib import Path

try:
    import raptorq
except ImportError:  # pragma: no cover - the package is optional
    raptorq = None

ROOT = Path(__file__).resolve().parent.parent
HEADING = "# RaptorQ Test Vectors"


def vectors():
    found = []
    for path in sorted(ROOT.glob("draft-ramadan-moq-*.md")):
        text = path.read_text(encoding="utf-8")
        if HEADING not in text:
            continue
        appendix = text.split(HEADING, 1)[1]
        for raw in re.findall(r"^~~~ json\n(.*?)^~~~$", appendix, re.S | re.M):
            vector = json.loads(raw)
            if str(vector.get("vector", "")).startswith("raptorq"):
                found.append((path.name, vector))
    return found


def packets_by_esi(packets):
    """cberner serializes a packet as a 4-byte Payload ID (SBN, 24-bit ESI) then the symbol."""
    out = {}
    for packet in packets:
        out[int.from_bytes(packet[1:4], "big")] = bytes(packet[4:])
    return out


@unittest.skipIf(raptorq is None, "the raptorq package is not installed")
class RaptorQVectors(unittest.TestCase):
    def test_vectors_are_present(self):
        self.assertTrue(vectors(), "no draft carries a RaptorQ Test Vectors appendix")

    def test_repair_symbols_match_rfc6330(self):
        for name, v in vectors():
            with self.subTest(draft=name, vector=v["vector"]):
                T, K = v["T"], v["SSB_length"]
                source = bytes.fromhex("".join(v["source"]))
                self.assertEqual(len(source), K * T)
                self.assertEqual(v["OTI"], {"F": K * T, "T": T, "Z": 1, "N": 1, "Al": 8})
                self.assertEqual(v["ESI"], [K + j for j in v["RS_ID"]])
                self.assertEqual(v["ISI"], [e + v["Kprime"] - K for e in v["ESI"]])
                encoded = packets_by_esi(raptorq.Encoder.with_defaults(source, T).get_encoded_packets(len(v["RS_ID"])))
                for i in range(K):
                    self.assertEqual(encoded[i], source[i * T:(i + 1) * T])
                for esi, repair in zip(v["ESI"], v["repair"]):
                    self.assertEqual(encoded[esi].hex(), repair, f"ESI {esi}")

    def test_received_set_recovers_the_lost_symbols(self):
        for name, v in vectors():
            if "received" not in v:
                continue
            with self.subTest(draft=name, vector=v["vector"]):
                T, K = v["T"], v["SSB_length"]
                source = bytes.fromhex("".join(v["source"]))
                encoded = packets_by_esi(raptorq.Encoder.with_defaults(source, T).get_encoded_packets(len(v["RS_ID"])))
                decoder = raptorq.Decoder.with_defaults(len(source), T)
                decoded = None
                for esi in list(v["received"]["ESI"]) + [K + j for j in v["received"]["RS_ID"]]:
                    decoded = decoder.decode(bytes([0]) + esi.to_bytes(3, "big") + encoded[esi])
                self.assertEqual(decoded, source)
                lost = sorted(set(range(K)) - set(v["received"]["ESI"]))
                self.assertEqual([decoded[i * T:(i + 1) * T].hex() for i in lost], v["recovered"])


if __name__ == "__main__":
    unittest.main()
