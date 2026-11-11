// @ts-check
import { defineConfig } from 'astro/config';

// Static output only. No adapters, no SSR, no runtime: the whole site is HTML + one map island later.
export default defineConfig({
  site: 'https://apocalab.com',
  output: 'static',
  trailingSlash: 'ignore',
  build: {
    // Keep the HTML readable so the build check can assert on real markup.
    format: 'directory',
    inlineStylesheets: 'auto',
  },
  devToolbar: { enabled: false },
});
