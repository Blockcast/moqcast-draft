# MoQCAST Internet-Draft submissions

The canonical source branch is `main`. On 14 October 2026, the three individual
`-00` drafts were submitted from commit
[`e21fcd50ede3ac0f08c2e58817ef50373052f02f`](https://github.com/Blockcast/moqcast-draft/tree/e21fcd50ede3ac0f08c2e58817ef50373052f02f).
Only the three standalone XML files were uploaded.

All three passed Datatracker validation, were authenticated by the author, and are
now posted as revision `-00`. This record does not claim RFC publication, working
group adoption, or implementation conformance.

These are correctly submitted as individual Internet-Drafts in the MoQ context.
Each XML has `workgroup=moq`, while the individual `draft-ramadan-moq-*` name
and the Datatracker status “Individual Submission” reflect that the MoQ working
group has not adopted them. MoQ chair approval/adoption is the later step that
would move an adopted document to the `draft-ietf-moq-*` naming convention.

| Draft | Submission receipt | Published document |
| --- | --- | --- |
| `draft-ramadan-moq-mmt-00` | [170369](https://datatracker.ietf.org/submit/status/170369/) | [MMT document](https://datatracker.ietf.org/doc/draft-ramadan-moq-mmt/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-mmt-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-mmt-00.txt) |
| `draft-ramadan-moq-multicast-00` | [170370](https://datatracker.ietf.org/submit/status/170370/) | [Multicast document](https://datatracker.ietf.org/doc/draft-ramadan-moq-multicast/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-multicast-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-multicast-00.txt) |
| `draft-ramadan-moq-fec-00` | [170371](https://datatracker.ietf.org/submit/status/170371/) | [FEC document](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-00.txt) |

## Uploaded XML checksums

The staged copies at `https://www.ietf.org/staging/<filename>` were independently
retrieved and compared byte for byte with the submitted commit. All three match.

```text
d423dd8271375bcb7981f2b6958e0c8938c7ed92bc8b58ac2fc5787a2271af08  draft-ramadan-moq-mmt-00.xml
7591c130ec8cfb519a496859a300ec4cb5f2b9b443177398b0373c1d768032dc  draft-ramadan-moq-multicast-00.xml
7c374dec94f1092db7f091d5b4298fdd9ee413f6a8336bf3132a3ef00c485961  draft-ramadan-moq-fec-00.xml
```

## Validation and submission procedure

The submitted XML was generated with mmark 2.2.48. XML parsing, xml2rfc rendering
and preparation, and all six repository contracts passed. idnits 3.1.0 reported
zero nits for all three XML files in submission mode. Datatracker also passed all
three drafts; its older idnits 2.17.1 reported one non-ASCII warning for MMT,
with zero errors or flaws.

To regenerate and validate a future revision, update the source document name
and explicit date, then run from the repository root with mmark, xml2rfc,
xmllint, idnits, and pytest installed:

```sh
set -eu
for stem in draft-ramadan-moq-mmt-00 draft-ramadan-moq-multicast-00 draft-ramadan-moq-fec-00; do
  mmark "$stem.md" > "$stem.xml"
  xmllint --noout --nonet "$stem.xml"
  xml2rfc --v3 --text --no-dtd "$stem.xml"
  idnits -m submission --no-progress --no-color -o simple "$stem.xml"
done
python3 -m pytest -q tests/test_moqcast_contracts.py
```

Inspect the idnits output as well as its exit status. Upload the XML through
[Datatracker's submission form](https://datatracker.ietf.org/submit/), wait for
validation, verify the metadata, and select **Post submission**. Use the author
email and add `repo https://github.com/Blockcast/moqcast-draft` as a resource.
Complete the email authentication. Do not re-upload these pending `-00` drafts;
use their existing submission records.

The public JSON state endpoints allow confirmation without creating another
submission:

- <https://datatracker.ietf.org/api/submission/170369/status>
- <https://datatracker.ietf.org/api/submission/170370/status>
- <https://datatracker.ietf.org/api/submission/170371/status>

The three document pages and archive XML were verified after authentication; the
archive XML is byte-identical to the submitted source hashes above. Track future
revisions through the same Datatracker process and update [the publication issue](https://paperclip.blockcast.net/BLO/issues/BLO-10812).

## draft-ramadan-mboned-mcast-manifest-00 (29 October 2026)

The MBONED individual draft was submitted on 29 October 2026 from the XML of
commit [`62b907ddd73754793041c49ef9ae01d49e1e1486`](https://github.com/Blockcast/moqcast-draft/tree/62b907ddd73754793041c49ef9ae01d49e1e1486)
on `main` (the content of `af8c814` with the explicit date set to the upload
day). Only the XML was uploaded, through the submission API
(`POST https://datatracker.ietf.org/api/submission`, which takes the same
email authentication round-trip as the form); the author completed the
authentication and the draft is posted as revision `-00`. It names
`workgroup=mboned` and is an individual submission, not an MBONED adoption.

| Draft | Submission receipt | Published document |
| --- | --- | --- |
| `draft-ramadan-mboned-mcast-manifest-00` | [171216](https://datatracker.ietf.org/submit/status/171216/) | [Manifest document](https://datatracker.ietf.org/doc/draft-ramadan-mboned-mcast-manifest/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-mboned-mcast-manifest-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-mboned-mcast-manifest-00.txt) |

The uploaded XML checksum, matched byte for byte against the archive copy after
posting:

```text
00f5fd777e39d1fdc84a35c5c2fd9949d44f6795db4e735a2f1d598668e89559  draft-ramadan-mboned-mcast-manifest-00.xml
```

Validation before upload: mmark 2.2.48, `xmllint --noout --nonet`, xml2rfc 3.34.0
with no unresolved anchors in the rendered text, idnits 3.1.0 with zero nits in
submission mode, and the 21 tests under `tests/` (`python3 -m pytest -q
tests`: 14 draft contracts in `tests/test_moqcast_contracts.py` and 7
Reed-Solomon vector checks in `tests/test_rs_vectors.py`). State endpoint:
<https://datatracker.ietf.org/api/submission/171216/status>.

## The 2 November 2026 batch

Seven drafts were submitted on 2 November 2026 from the XML of commit
[`5f4917291e2f0e58bdee9e4a813ff248537695e2`](https://github.com/Blockcast/moqcast-draft/tree/5f4917291e2f0e58bdee9e4a813ff248537695e2)
on `drafts/manifest-records-in-band` (#19): the four documents of the FEC split
of `draft-ramadan-moq-fec-01`, the `-02` revisions of the MMT and multicast
drafts, and the manifest draft's `-01`. Only the XML was uploaded, through the
submission API; the author completed each email authentication, and all seven
were posted between 18:22 and 18:23 UTC. Each is an individual submission:
the manifest draft names `workgroup=mboned`, the other six `workgroup=moq`.

| Draft | Submission receipt | Published document |
| --- | --- | --- |
| `draft-ramadan-moq-fec-core-00` | [172046](https://datatracker.ietf.org/submit/status/172046/) | [FEC core document](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec-core/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-core-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-core-00.txt) |
| `draft-ramadan-moq-fec-block-codes-00` | [172047](https://datatracker.ietf.org/submit/status/172047/) | [Block codes document](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec-block-codes/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-block-codes-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-block-codes-00.txt) |
| `draft-ramadan-moq-fec-catalog-00` | [172048](https://datatracker.ietf.org/submit/status/172048/) | [Catalog document](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec-catalog/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-catalog-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-catalog-00.txt) |
| `draft-ramadan-moq-fec-multicast-00` | [172049](https://datatracker.ietf.org/submit/status/172049/) | [FEC multicast document](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec-multicast/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-multicast-00.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-fec-multicast-00.txt) |
| `draft-ramadan-moq-mmt-02` | [172050](https://datatracker.ietf.org/submit/status/172050/) | [MMT document](https://datatracker.ietf.org/doc/draft-ramadan-moq-mmt/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-mmt-02.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-mmt-02.txt) |
| `draft-ramadan-moq-multicast-02` | [172051](https://datatracker.ietf.org/submit/status/172051/) | [Multicast document](https://datatracker.ietf.org/doc/draft-ramadan-moq-multicast/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-moq-multicast-02.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-moq-multicast-02.txt) |
| `draft-ramadan-mboned-mcast-manifest-01` | [172052](https://datatracker.ietf.org/submit/status/172052/) | [Manifest document](https://datatracker.ietf.org/doc/draft-ramadan-mboned-mcast-manifest/) · [XML](https://www.ietf.org/archive/id/draft-ramadan-mboned-mcast-manifest-01.xml) · [TXT](https://www.ietf.org/archive/id/draft-ramadan-mboned-mcast-manifest-01.txt) |

The uploaded XML checksums, matched byte for byte against the archive copies
after posting:

```text
2d66c2b2414a4ae8ad52bdaffde2e8fa6114d8eb98eea4c96ee75ff056feb8bb  draft-ramadan-moq-fec-core-00.xml
3644fe0a32fa55db866a757af513657600bc181e203b79ed45a6333fd43101bd  draft-ramadan-moq-fec-block-codes-00.xml
86952dc5ade97c0beeb75b62729e580bfa8735d0e8638d9fec444479acd25b37  draft-ramadan-moq-fec-catalog-00.xml
2dd8046146d240c26875db70cdcbf7f493d76a210fd4ac7026940d8cfb9495ff  draft-ramadan-moq-fec-multicast-00.xml
cf3c7f0b0558516d891b45b3630b065e6b50eb877cdba5bfdd649a1f2cbf62b9  draft-ramadan-moq-mmt-02.xml
74315f7566349d203aed03723582c63a5152ca038116b53fca2a35c1f0f64200  draft-ramadan-moq-multicast-02.xml
461aed019786a1ebc4ee36e77b7c8156b12a5b7f7fd206611bf40c61a284001b  draft-ramadan-mboned-mcast-manifest-01.xml
```

The repository's `draft-ramadan-moq-mmt-02.md` and `.xml` have since taken one
erratum (#25: an `iso-ssbg1-v1` AL-FEC entry carries neither
`num_of_repair_symbol_per_packet` nor `num_of_symbol_element_per_source_symbol`,
per ISO/IEC 23008-1 Table C.3) and one change (#27: the keyframe overlay's
members include the FT=0 and FT=1 data units that govern each Random Access
Point it covers, Section 7.4.2), and they cite
`draft-ramadan-moq-fec-multicast-01`, the unposted revision of #24, #29 and #30,
so the two are posted together. The `-02` checksum above is the posted copy's;
the repository's `-02` XML no longer matches it. The files keep the `-02` name
as the working copy until the next posting, which the Datatracker takes only as
`-03`.

Validation of the uploaded XML: each file is the output of mmark 2.2.48 for its
markdown; `xmllint --noout --nonet` passes; idnits 3.1.0 in submission mode
with `--offline` reports no nits for any of the seven. Run online after posting,
idnits adds only the two checks against the posted version itself (the version
exists, and it has no stream on the Datatracker). `python3 -m pytest -q tests`
gives 32 passed and 4 skipped (the libmmt in-band JSON is not published yet;
the raptorq package is not installed). The Datatracker's own validation passed
for all seven.

State endpoints: <https://datatracker.ietf.org/api/submission/172046/status> to
<https://datatracker.ietf.org/api/submission/172052/status>.
