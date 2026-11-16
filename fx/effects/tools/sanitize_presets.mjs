// One-off: replace real-world names/news in sample text with fictional copy (applied to presets/*.json).
import fs from 'node:fs';
const R = {
  'regional-profile': { labels: ['SAMPLE LEADER'] },
  'territory-date': { title: '12 June 1900', subtitle: 'Where it happened' },
  'regional-share': { subtitle: 'SAMPLE PARTY' },
  'country-trace': { title: 'COUNTRY NAME' },
  'clock-badge': { subtitle: 'JUNE 5, 1980' },
  'date-center': { subtitle: '1980' },
  'date-slide': { subtitle: '1975' },
  'feature-card': { title: 'Product Name' },
  'money-counter': { subtitle: 'PER DAY ON AVERAGE' },
  'headline-build': { title: 'Sample Co. Reports|$2.5 Million In|New Sales' },
  'paragraph-marker': { body: 'A spokesperson says the team has found and logged a collection of 14,000 sample items worth close to $2.5 million at current rates.', highlight: 'A spokesperson says' },
  'article-zoom': { body: 'A SPOKESPERSON SAYS THE TEAM HAS FOUND AND LOGGED A COLLECTION OF 14,000 SAMPLE ITEMS WORTH CLOSE TO $2.5 MILLION AT CURRENT RATES.', highlight: 'A SPOKESPERSON' },
  'flight-route': { pointLabels: ['City A', ''] },
  'news-column': { title: 'RESIDENTS ARE ANGRY AT THE PLAN,|BUT FORGIVING OF THE MAYOR', body: 'A generation ago, local fury over the old stadium deal often blurred into distrust of the council. Now, some residents seem ready to separate the plan from the people.' },
  'news-image': { title: 'LOCAL BAKERY OPENS THIRD SHOP AS LINES GROW', subtitle: 'JUNE 16, 2030' },
  'chapter-number': { subtitle: 'The first chapter of the story.' },
  'spoken-phrases': { labels: ['HELLO, I AM A SAMPLE.', 'I AM STILL LEARNING.'] },
  'falling-subjects': { title: 'SUBJECTS' },
  'subject-pointer': { subtitle: 'JOB TITLE HERE' },
  'torn-profile': { title: 'SAMPLE NAME' },
  'percentage-ring': { subtitle: 'OF SAMPLE ITEMS' },
  'territory-symbols': { subtitle: 'Sample region, 1900' },
  'brand-stat': { suffix: ' MILLION IN SALES' },
  'place-and-image': { title: 'Sample Place' },
  'image-to-crowd': { title: 'SAMPLE MARKET, SAMPLE CITY' },
  'picture-area-chart': { title: 'Big increase in sample prices' },
  'press-stack': { label: 'NEWS WIRE', labels: ['NEWS WIRE', 'The Daily Sample', 'NEWS', 'NEWS WIRE'], title: 'WHY FEARS OF A SAMPLE MARKET BUBBLE ARE GROWING', body: 'Observers are looking closely at the rapid growth of a made-up industry. Fresh products have attracted large sums, and some experts worry about what comes next.' },
  'ranked-bars': { title: 'Top Countries by Sample Score' },
  'news-lower-third': { title: 'MIND OVER MUSCLE' },
  'two-bars': { title: 'School funding comparison' },
  'text-magnifier': { title: 'WELCOME TO OUR STORY' },
  'life-dates': { title: 'SAMPLE NAME', subtitle: '1900–1980' },
  'subject-headline': { title: 'FIRST FIRES' },
};
for (const [id, patch] of Object.entries(R)) {
  const f = new URL(`../presets/${id}.json`, import.meta.url);
  const q = JSON.parse(fs.readFileSync(f, 'utf8'));
  for (const [k, v] of Object.entries(patch)) { if (!(k in q)) console.log('missing key', id, k); q[k] = v; }
  fs.writeFileSync(f, JSON.stringify(q, null, 1));
}
