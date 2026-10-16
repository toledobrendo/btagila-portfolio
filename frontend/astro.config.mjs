// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
	// Pure static output: no adapter, no runtime server. Pages are rendered at build
	// time and served as plain files (see ../ARCHITECTURE.md §1). Gallery content is
	// fetched from the backend API during the build, which is why a published change
	// requires a rebuild (../ARCHITECTURE.md §7).
	output: 'static',

	// TODO(Phase 7): set the real public URL — used for canonical links and the sitemap.
	// site: 'https://portfolio.example.com',

	vite: {
		plugins: [tailwindcss()]
	}
});
