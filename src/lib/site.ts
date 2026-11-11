/**
 * The single list of indexable pages.
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
export interface PageDef {
  /** Trailing slash is part of the public URL. */
  path: string;
  priority: string;
  changefreq: 'daily' | 'weekly' | 'monthly' | 'yearly';
}

export const SITE_ORIGIN = 'https://apocalab.com';

export const PAGES: PageDef[] = [
  { path: '/', priority: '1.0', changefreq: 'weekly' },
  { path: '/blast-radius/', priority: '0.9', changefreq: 'monthly' },
  { path: '/nuclear-bomb-map/', priority: '0.8', changefreq: 'monthly' },
  { path: '/methodology/', priority: '0.6', changefreq: 'yearly' },
];

/** Absolute, trailing-slash, query-free. Throws rather than emitting a wrong URL. */
export function pageUrl(path: string): string {
  if (!path.startsWith('/') || !path.endsWith('/')) {
    throw new Error(`pageUrl(): path must start and end with a slash, got ${path}`);
  }
  return new URL(path, SITE_ORIGIN).toString();
}
