import { defineConfig } from 'astro/config';
import { viteStaticCopy } from 'vite-plugin-static-copy';

// https://astro.build/config
export default defineConfig({
  vite: {
    plugins: [
      viteStaticCopy({
        targets: [
          {
            src: 'node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js',
            dest: './'
          },
          {
            src: 'node_modules/@ricky0123/vad-web/dist/silero_vad.onnx',
            dest: './'
          },
          {
            src: 'node_modules/onnxruntime-web/dist/*.wasm',
            dest: './_astro/'
          }, {
            src: 'node_modules/onnxruntime-web/dist/ort-wasm*.mjs',
            dest: './_astro/'
          }
        ]
      })
    ],
    optimizeDeps: {
      exclude: ["onnxruntime-web"]
    }
  }
});
