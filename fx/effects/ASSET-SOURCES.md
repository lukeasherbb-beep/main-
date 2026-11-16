# Bundled sample media and data

Everything in `assets/` is either generated for this library (procedural drawings, or images made from
text prompts with no reference images), or public-domain map data. Nothing is a photograph of a real
person or a third-party logo. The sample images are placeholders: members replace them with their own
(see the image slots in each effect's schema).

| File | Origin |
|---|---|
| assets/country-maps.json | Public-domain map data (Natural Earth, projection of world.geojson) |
| assets/world.geojson | Public-domain map data: Natural Earth 1:50m admin-0 countries |
| assets/crowd.png, eclipse.png, flag-france.png, flag-italy.png, flag-russia.png, flag-uk.png, fuel.png, globe.png, heart.png, money.png, object.png, phases.png, rocket-dark.png, rocket.png, truck.png | Original procedural artwork |
| assets/landscape-1.png, landscape-2.png, landscape-3.png, map-sketch.png, mark.png, person-1.png, person-2.png, paper.png | Original procedural artwork |
| assets/original-coastal-city.png, original-frog-a.png, original-frog-b.png, original-highland.png, original-person-a.png, original-person-b.png | AI-generated from text prompts only (fictional city, fictional people, placeholder frogs; not scientific evidence) |

## Natural Earth attribution

Map geometry: Made with Natural Earth. Free vector and raster map data at https://www.naturalearthdata.com .
Natural Earth data is in the public domain (https://www.naturalearthdata.com/about/terms-of-use/).
Source repository: https://github.com/nvkelso/natural-earth-vector . Boundaries are drawn as Natural Earth
shows them; names and borders are editable demonstration content, not a statement of any position.

## Fonts

Bundled in `fonts/` under the SIL Open Font License 1.1 (licence text beside each font):

- Anton (Anton Project Authors), display headings: https://github.com/googlefonts/AntonFont
- Arimo (Arimo Project Authors), clean sans: https://github.com/googlefonts/arimo
- Gelasio (Gelasio Project Authors), serif: https://github.com/SorkinType/Gelasio

Files were taken from https://github.com/google/fonts (ofl/anton, ofl/arimo, ofl/gelasio). No system fonts are used or shipped.
