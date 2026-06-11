# Test Fixtures

Place test assets here. Do NOT commit large video files or real SOP documents
(large binaries are gitignored — `tests/fixtures/*.pdf` and `*.mp4`).

## What belongs here

| File | Purpose |
|---|---|
| `prusa_mk3s_plus_assembly.pdf` | Official Prusa MK3S+ kit assembly manual (28.9 MB, gitignored — download locally, see below) |
| `sample_sop_short.pdf` | A 2–3 page synthetic SOP for unit testing the extractor |
| `sample_observations.json` | A small hand-crafted Observations JSON for testing the reasoning engine |
| `sample_checklist.json` | A small hand-crafted checklist for testing Agent 2 and timing engine |

## Getting the Prusa SOP manual

The SOP smoke test uses the official manual (same procedure the OpenMarcie
Scenario B participants follow). It is gitignored — download it once:

```powershell
curl.exe -L -o tests/fixtures/prusa_mk3s_plus_assembly.pdf "https://help.prusa3d.com/wp-content/uploads/generated/original-prusa-i3-mk3s-kit-assembly_1128_en_2025-04-18.pdf"
```

Then run the smoke test with a page range (the manual is 200+ pages):

```powershell
python scripts/test_sop_pipeline.py --pages 1-30 --granularity section
```

## What does NOT belong here

- Real IndustReal `.mp4` files — too large, use Blob Storage
- Real SOP PDFs from clients — confidential
- Any file over 1 MB

## Getting test clips

For smoke testing `video_analyzer.py` against a real Content Understanding call,
download a short IndustReal clip separately and pass it via the test script:

```bash
python scripts/test_video_pipeline.py --clip /path/to/short_clip.mp4
```

IndustReal dataset: https://data.4tu.nl/datasets/b008dd74-020d-4ea4-a8ba-7bb60769d224
