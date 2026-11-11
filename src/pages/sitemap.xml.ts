import type { APIRoute } from 'astro';
import { PAGES, pageUrl } from '../lib/site';

/**
 * Generated from src/lib/site.ts at build time, so the sitemap and the pages
 * cannot drift apart. check_site.py asserts that every <loc> resolves to a real
 * built file, and that no built page is missing from this list.
 */
export const GET: APIRoute = () => {
  const urls = PAGES.map(
    (p) =>
      [
        '  <url>',
        `    <loc>${pageUrl(p.path)}</loc>`,
        `    <changefreq>${p.changefreq}</changefreq>`,
        `    <priority>${p.priority}</priority>`,
        '  </url>',
      ].join('\n'),
  ).join('\n');

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    urls,
    '</urlset>',
    '',
  ].join('\n');

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
