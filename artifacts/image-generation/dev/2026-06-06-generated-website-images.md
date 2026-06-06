# LocalRAG Generated Website Images

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Image generation |
| Stage | Dev |
| Issue | #37 - Generate and integrate image assets |
| Date | 2026-06-06 |
| Status | Integrated into `dev` branch candidate |

## Selected Assets

| Asset | Repository path | Purpose | Notes |
| --- | --- | --- | --- |
| IMG-01 hero | `web/static/media/image/localrag-hero-product-2026-06-06-1600x900.webp` | First viewport product proof visual | WebP primary, PNG fallback. Generated without embedded text so Russian and localized copy stays in HTML. |
| IMG-01 hero mobile/fallback | `web/static/media/image/localrag-hero-product-2026-06-06-1200x675.webp` | Smaller responsive source for future use | Kept for responsive optimization follow-up. |
| IMG-08 poster | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1600x900.webp` | Poster for walkthrough section and future video | WebP primary, PNG fallback. |
| IMG-08 poster compact | `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1280x720.webp` | Smaller poster source for future use | Kept for responsive optimization follow-up. |

PNG fallbacks are committed next to WebP assets because older browsers and
debugging tools may not display WebP. The application template currently uses
the 1600px WebP with PNG fallback.

## Generation Prompts

### Hero

Create a polished product-faithful hero illustration for a local-first document
question answering app named LocalRAG. Composition: a clean desktop app
interface beside a local folder of neutral sample documents, visible document
fragments flowing into a subtle retrieval graph, and a source-context card
connected back to an answer panel. Premium technical SaaS aesthetic, light
interface, precise panels, restrained depth, subtle 3D nodes and thin connector
lines, no people, no cloud symbols, no shield or lock badges, no fake ratings,
no generic AI glow. Do not include readable text, letters, logos, customer
names, file names, watermarks, or UI copy; leave labels as neutral interface
blocks because localized HTML will overlay real Russian copy. Wide 16:9
composition, readable at desktop and mobile crop, enough clear space on the left
for headline overlay, crisp high-resolution web hero asset.

### Video Poster

Create a cinematic 16:9 product poster illustration for a LocalRAG walkthrough
video. Show a local document folder, a clean desktop app UI, a restrained 3D
retrieval graph flattening into a source proof card, and a clear answer/source
relationship. Premium technical product style, light UI, crisp panels, calm
professional color accents, useful explanatory depth rather than decoration. No
people, no cloud upload symbols, no shields, no locks, no fake testimonials, no
ratings, no generic AI brain, no glowing abstract background. Do not include
readable text, letters, captions, logos, customer names, or watermarks; all copy
will be rendered as localized HTML overlay. Leave negative space in the
upper-left and lower-right for overlay title and CTA. High-resolution web
poster, 16:9.

## Approval Notes

- The selected images avoid embedded text to prevent unreadable generated
  Cyrillic and to keep EN/RU/NL/ZH/HE localization in maintainable HTML.
- The visuals do not claim certified privacy, compliance, enterprise readiness,
  ratings, testimonials, or cloud isolation.
- The hero asset supports the current first viewport with local folder,
  retrieval graph, product UI, answer panel, and source card.
- The poster supports the Russian-first walkthrough direction without committing
  a large video binary before a storage policy is approved.

## Integration

- `web/templates/main_content.html` now renders the hero image with
  `<picture>` and localized `alt` text.
- The walkthrough poster is rendered in the new `#walkthrough` section.
- `web/static/style.css` defines stable aspect ratios and mobile layout rules.
- Locale keys were added for all active UI languages.
