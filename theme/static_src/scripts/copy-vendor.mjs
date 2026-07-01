// Copies vendor JS from node_modules into theme/static/vendor/, and downloads
// the InterVariable font (which isn't on npm in a stable form) if missing.
//
// Idempotent — safe to run on every build.

import { copyFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const vendorDir = resolve(here, "..", "..", "static", "vendor");
mkdirSync(vendorDir, { recursive: true });

// --- 1. Vendor JS from node_modules ---------------------------------------
const jsFiles = [
  ["alpinejs/dist/cdn.min.js", "alpine.min.js"],
  ["htmx.org/dist/htmx.min.js", "htmx.min.js"],
];

for (const [src, dest] of jsFiles) {
  const srcPath = resolve(here, "..", "node_modules", src);
  const destPath = resolve(vendorDir, dest);
  copyFileSync(srcPath, destPath);
  console.log(`copied ${src} -> static/vendor/${dest}`);
}

// --- 2. Inter variable font (from rsms/inter) -----------------------------
// We pin to a specific tag so first build is reproducible. Update the URL when
// upgrading Inter; delete the existing file to force a re-download.
const FONT_URL =
  "https://github.com/rsms/inter/raw/v4.0/docs/font-files/InterVariable.woff2";
const fontDest = resolve(vendorDir, "InterVariable.woff2");

if (existsSync(fontDest)) {
  console.log("kept   static/vendor/InterVariable.woff2 (already present)");
} else {
  process.stdout.write(`fetch  ${FONT_URL} ... `);
  const res = await fetch(FONT_URL);
  if (!res.ok) {
    console.error(`failed (${res.status} ${res.statusText})`);
    process.exit(1);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  writeFileSync(fontDest, buf);
  console.log(`ok (${buf.length} bytes)`);
}
