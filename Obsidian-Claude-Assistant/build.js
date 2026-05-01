const esbuild = require('esbuild');
const fs = require('fs');

async function build() {
  // Build main.ts with obsidian as external
  await esbuild.build({
    entryPoints: ['main.ts'],
    bundle: true,
    platform: 'node',
    target: 'node14',
    outfile: 'main.js',
    format: 'cjs',
    sourcemap: true,
    external: ['obsidian']
  });
  console.log('Built main.js');

  // Build src files
  await esbuild.build({
    entryPoints: ['src/ClaudePanel.ts'],
    bundle: true,
    platform: 'node',
    target: 'node14',
    outfile: 'src/ClaudePanel.js',
    format: 'cjs',
    sourcemap: true,
    external: ['obsidian']
  });
  console.log('Built src/ClaudePanel.js');

  await esbuild.build({
    entryPoints: ['src/cli.ts'],
    bundle: true,
    platform: 'node',
    target: 'node14',
    outfile: 'src/cli.js',
    format: 'cjs',
    sourcemap: true,
    external: ['obsidian']
  });
  console.log('Built src/cli.js');

  // Build types.ts and utils.ts separately
  await esbuild.build({
    entryPoints: ['src/types.ts'],
    bundle: true,
    platform: 'node',
    target: 'node14',
    outfile: 'src/types.js',
    format: 'cjs',
    sourcemap: true,
    external: ['obsidian']
  });
  console.log('Built src/types.js');

  await esbuild.build({
    entryPoints: ['src/utils.ts'],
    bundle: true,
    platform: 'node',
    target: 'node14',
    outfile: 'src/utils.js',
    format: 'cjs',
    sourcemap: true,
    external: ['obsidian']
  });
  console.log('Built src/utils.js');

  console.log('Build complete!');
}

build().catch(e => { console.error(e); process.exit(1); });