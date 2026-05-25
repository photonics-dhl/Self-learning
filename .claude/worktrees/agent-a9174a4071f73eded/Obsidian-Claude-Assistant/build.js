const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

// Obsidian vault 插件安装目录
const VAULT_PLUGIN_DIR = path.join(__dirname, '..', 'Obsidian-Vault', '.obsidian', 'plugins', 'Obsidian-Claude-Assistant');

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

	// 自动复制到 Obsidian vault 插件目录
	if (fs.existsSync(VAULT_PLUGIN_DIR)) {
		const filesToCopy = ['main.js', 'main.js.map', 'manifest.json'];
		for (const f of filesToCopy) {
			const src = path.join(__dirname, f);
			if (fs.existsSync(src)) {
				fs.copyFileSync(src, path.join(VAULT_PLUGIN_DIR, f));
				console.log(`Copied ${f} → vault plugin dir`);
			}
		}
	} else {
		console.log(`⚠️  Vault plugin dir not found: ${VAULT_PLUGIN_DIR}`);
	}

	console.log('Build complete!');
}

build().catch(e => { console.error(e); process.exit(1); });
