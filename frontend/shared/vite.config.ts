/// <reference types="vitest" />

import {defineConfig} from 'vite';

import react from '@vitejs/plugin-react';
import viteTsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
    plugins: [react(), viteTsconfigPaths({parseNative: true, ignoreConfigErrors: false})],
    resolve: {
        dedupe: ['react', 'react-dom'],
    },
    test: {
        environment: 'jsdom',
        setupFiles: ['src/setupTests.ts'],
        globals: true,
        pool: 'typescript',
        /*
         * Below due to random "unhandled error" on GitLab:
         * (Error: [vitest-worker]: Timeout calling "fetch" with "["/@vite/env","web"]")
         * It seems to occur only in that environment. This would be good to investigate.
         * */
        dangerouslyIgnoreUnhandledErrors: false,

        typecheck: {
            enabled: true,
            ignoreSourceErrors: false,
            checker: 'tsc',
        },
    },
});
