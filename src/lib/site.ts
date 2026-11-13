/**
 * The single list of indexable pages, and the one switch that decides whether
 * this build may be indexed at all.
 *
 * sitemap.xml is generated from this array, and check_site.py asserts that it
 * matches exactly the set of pages that actually got built — so a page cannot
 * ship without appearing in the sitemap, and the sitemap cannot list a URL that
 * does not resolve.
 *
 * priority/changefreq are hints only; Google ignores them, Bing sometimes reads
 * them. Keep lastmod out on purpose: it would be a build timestamp, which
 * teaches crawlers that this file changes when nothing changed.
 */
import { cities, PUBLISHED_CITY_SLUGS } from './cities';

export interface PageDef {
  /** Trailing slash is part of the public URL. */
  path: string;
  priority: string;
  changefreq: 'daily' | 'weekly' | 'monthly' | 'yearly';
}

export const SITE_ORIGIN = 'https://apocalab.com';

/**
 * When this site's content was first published, as a date — not a year.
 *
 * Every page carried the manual's 1977 as its `datePublished`, which is a
 * different claim entirely: 1977 is when the source was printed, not when this
 * page appeared. Structured data now takes its page date from here, and 1977
 * stays where it belongs, on the Book node under `isBasedOn`.
 *
 * 2026-11-13 is the first production deployment that served this content
 * publicly. It is one constant because the alternative — a date per page,
 * copied by hand — drifts the moment a page is rebuilt.
 */
export const SITE_PUBLISHED = '2026-11-13';

/**
 * Is apocalab.com serving this build?
 *
 * false — the domain is not pointed at Cloudflare Pages yet. Every deployment,
 *   production on `main` included, is served with `X-Robots-Tag: noindex`.
 *   Reason: every page carries `rel=canonical` pointing at apocalab.com, and
 *   Google cannot fetch that target. Left indexable, it would index the
 *   *.pages.dev addresses instead, and the day the domain goes live the same
 *   content would exist at two hostnames.
 * true  — the domain serves this build. Production is indexable; preview
 *   branches stay noindexed, because a preview is a build in progress.
 *
 * Flipping this one boolean is the entire go-live step. scripts/gen_headers.mjs
 * reads it out of this file at build time and check_site.py reads it out of this
 * file when it decides what to expect, so the artifact and the gate cannot
 * disagree — and there is no second place to edit and forget.
 */
export const SITE_LIVE = false;

export const PAGES: PageDef[] = [
  { path: '/', priority: '1.0', changefreq: 'weekly' },
  { path: '/blast-radius/', priority: '0.9', changefreq: 'monthly' },
  { path: '/nuclear-bomb-map/', priority: '0.8', changefreq: 'monthly' },
  { path: '/methodology/', priority: '0.6', changefreq: 'yearly' },
  { path: '/nuclear-winter/', priority: '0.7', changefreq: 'yearly' },
  // City pages live under the map they are a reading of: /nuclear-bomb-map/new-york/.
  // Only the slugs in PUBLISHED_CITY_SLUGS are listed — a city page that has not
  // been built yet must not appear here, or the sitemap would promise a 404.
  ...cities
    .filter((c) => PUBLISHED_CITY_SLUGS.includes(c.slug))
    .map((c) => ({
      path: `/nuclear-bomb-map/${c.slug}/`,
      priority: '0.7',
      changefreq: 'yearly' as const,
    })),
];

/** Absolute, trailing-slash, query-free. Throws rather than emitting a wrong URL. */
export function pageUrl(path: string): string {
  if (!path.startsWith('/') || !path.endsWith('/')) {
    throw new Error(`pageUrl(): path must start and end with a slash, got ${path}`);
  }
  return new URL(path, SITE_ORIGIN).toString();
}
