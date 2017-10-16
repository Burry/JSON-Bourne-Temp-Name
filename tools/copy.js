// Copies files to the output (build) folder

import path from 'path';
import chokidar from 'chokidar';
import { writeFile, copyFile, makeDir, copyDir, cleanDir } from './lib/fs';
import pkg from '../package.json';
import { format } from './run';

async function copy() {
	await makeDir('build');
	await Promise.all([
		writeFile(
			'build/package.json',
			JSON.stringify(
				{
					private: true,
					engines: pkg.engines,
					dependencies: pkg.dependencies,
					scripts: {
						start: 'node server.js',
					},
				},
				null,
				2
			)
		),
		copyFile('LICENSE.txt', 'build/LICENSE.txt'),
		copyFile('yarn.lock', 'build/yarn.lock'),
		copyDir('src/public', 'build/public'),
		copyDir('src/templates', 'build/templates')
	]);

	if (process.argv.includes('--watch')) {
		const watcher = chokidar.watch(['src/public/**/*', 'src/templates/**/*'], { ignoreInitial: true });

		watcher.on('all', async (event, filePath) => {
			const start = new Date();
			const src = path.relative('./', filePath);
			const dist = path.join(
				'build/',
				src.startsWith('src') ? path.relative('src', src) : src,
			);
			switch (event) {
				case 'add':
				case 'change':
					await makeDir(path.dirname(dist));
					await copyFile(filePath, dist);
					break;
				case 'unlink':
				case 'unlinkDir':
					cleanDir(dist, { nosort: true, dot: true });
					break;
				default:
					return;
			}
			const end = new Date();
			const time = end.getTime() - start.getTime();
			console.info(`[${format(end)}] ${event} '${dist}' after ${time} ms`);
		});
	}
}

export default copy;
