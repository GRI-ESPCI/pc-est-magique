import { nodeResolve } from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import terser from '@rollup/plugin-terser';

export default {
    input: "./app/static/ts/md-editor.ts",
    output: {
        file: "./app/static/dist/md-editor.bundle.js",
        format: "iife"
    },
    plugins: [
        nodeResolve(),
        typescript({
            tsconfig: './tsconfig.json',
        }),
        terser()
    ]
}