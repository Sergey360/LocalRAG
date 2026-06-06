# LocalRAG Walkthrough Poster and Transcript Assets

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Video generation |
| Stage | Dev |
| Issue | #40 - Generate and integrate video assets |
| Date | 2026-06-06 |
| Status | Poster, Russian transcript, and caption source integrated |

## Implemented Assets

| Asset | Repository path |
| --- | --- |
| Poster WebP | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1600x900.webp` |
| Poster PNG fallback | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1600x900.png` |
| Compact poster WebP | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1280x720.webp` |
| Compact poster PNG fallback | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1280x720.png` |
| Russian transcript | `web/static/media/video/localrag-product-walkthrough-v2-75s-transcript.ru.md` |
| Russian captions | `web/static/media/video/localrag-product-walkthrough-v2-75s.ru.vtt` |

## Production Decision

The dev implementation integrates the approved poster, Russian transcript, and
caption source. It intentionally does not commit an MP4/WebM binary yet:

- `docs/solution-design.md` says not to commit large video binaries without an
  approved storage decision.
- The NAS worker currently has no `ffmpeg` or video generation tool available.
- The public page still gets a concrete, browser-rendered walkthrough section
  with poster, caption, transcript link, and localized copy.

When storage and generation tooling are approved, the final clip should use the
same asset names from the design addendum:

- `localrag-product-walkthrough-v2-75s.mp4`
- `localrag-product-walkthrough-v2-75s.webm`
- localized VTT files for EN, NL, ZH, and HE after native QA

## Claim Controls

- The poster does not include generated Russian text; copy is rendered in HTML
  and localization files.
- The transcript keeps the limitation that local files remain local in the
  default scenario, not in every possible deployment.
- Source page/line visibility is described only where metadata is available.
- No fake metrics, customer proof, compliance claims, ratings, or security seals
  were added.
