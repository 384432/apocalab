// @ts-check
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'astro/config';
import { writeHeaders } from './scripts/gen_headers.mjs';

/**
 * dist/_headers is written here, after the HTML exists, because the noindex
 * decision belongs to the deployment environment, not to the source tree.
 * See scripts/gen_headers.mjs for the branch rule.
 */
const pagesHeaders = {
  name: 'apocalab:pages-headers',
  hooks: {
    'astro:build:done': ({ dir, logger }) => {
      const { mode, reason, siteLive } = writeHeaders(fileURLToPath(dir));
      logger.info(`_headers: ${mode} (${reason}) [SITE_LIVE=${siteLive}]`);
    },
  },
};

// Static output only. No adapters, no SSR, no runtime: the whole site is HTML + one map island later.
export default defineConfig({
  site: 'https://apocalab.com',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [pagesHeaders],
  build: {
    // Keep the HTML readable so the build check can assert on real markup.
    format: 'directory',
    inlineStylesheets: 'auto',
  },
  devToolbar: { enabled: false },
});
