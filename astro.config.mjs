import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://reichenberg.ruhr',
  compressHTML: true,
  build: {
    assets: '_assets'
  }
});
