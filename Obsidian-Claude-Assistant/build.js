const esbuild = require('esbuild');

async function build() {
	const entryPoints = [
		['main.ts', 'main.js'],
		['src/ClaudePanel.ts', 'src/ClaudePanel.js'],
		['src/zai-client.ts', 'src/zai-client.js'],
		['src/env-loader.ts', 'src/env-loader.js'],
		['src/types.ts', 'src/types.js'],
		['src/utils.ts', 'src/utils.js']
	];

	for (const [entry, outfile] of entryPoints) {
		await esbuild.build({
			entryPoints: [entry],
			bundle: true,
			platform: 'node',
			target: 'node14',
			outfile,
			format: 'cjs',
			sourcemap: true,
			external: ['obsidian']
		});
		console.log(`Built ${outfile}`);
	}

	console.log('Build complete!');
}

build().catch(e => { console.error(e); process.exit(1); });
