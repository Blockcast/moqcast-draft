# MoQCAST Internet-Draft submissions

The canonical source branch is `main`. On 14 October 2026, the three individual
`-00` drafts were submitted from commit
[`e21fcd50ede3ac0f08c2e58817ef50373052f02f`](https://github.com/Blockcast/moqcast-draft/tree/e21fcd50ede3ac0f08c2e58817ef50373052f02f).
Only the three standalone XML files were uploaded.

All three passed Datatracker validation and reached `auth` (Awaiting Submitter
Authentication). Datatracker sent confirmation emails to `omar@blockcast.net`.
Publication remains pending until the author follows those links and Datatracker
reports the submissions as posted. This record does not claim RFC publication,
working group adoption, or implementation conformance.

These are correctly submitted as individual Internet-Drafts in the MoQ context.
Each XML has `workgroup=moq`, while the individual `draft-ramadan-moq-*` name
and the Datatracker status “Individual Submission” reflect that the MoQ working
group has not adopted them. MoQ chair approval/adoption is the later step that
would move an adopted document to the `draft-ietf-moq-*` naming convention.

| Draft | Submission receipt | Publication URL (pending) |
| --- | --- | --- |
| `draft-ramadan-moq-mmt-00` | [170369](https://datatracker.ietf.org/submit/status/170369/) | [MMT](https://datatracker.ietf.org/doc/draft-ramadan-moq-mmt/00/) |
| `draft-ramadan-moq-multicast-00` | [170370](https://datatracker.ietf.org/submit/status/170370/) | [Multicast](https://datatracker.ietf.org/doc/draft-ramadan-moq-multicast/00/) |
| `draft-ramadan-moq-fec-00` | [170371](https://datatracker.ietf.org/submit/status/170371/) | [FEC](https://datatracker.ietf.org/doc/draft-ramadan-moq-fec/00/) |

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

After authentication, verify the three document pages and published XML, then
update this record and [the publication issue](https://paperclip.blockcast.net/BLO/issues/BLO-10812).
