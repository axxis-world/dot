import fs from 'fs';
import path from 'path';
import os from 'os';

const CACHE_DIR = path.join(os.homedir(), '.axxis');
const CACHE_PATH = path.join(CACHE_DIR, 'embed-cache.json');

// Swap this one line when upgrading to Gemini or another model
const MODEL = 'Xenova/all-MiniLM-L6-v2';   // 384-dim, 25MB, Apache 2.0

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _pipeline: any = null;

export async function embed(text: string): Promise<number[]> {
  if (!_pipeline) {
    const { pipeline } = await import('@huggingface/transformers');
    _pipeline = await pipeline('feature-extraction', MODEL, { dtype: 'fp32' });
  }
  const out = await _pipeline(text, { pooling: 'mean', normalize: true });
  return Array.from(out.data as Float32Array);
}

export function loadCache(): Record<string, number[]> {
  try {
    if (fs.existsSync(CACHE_PATH)) return JSON.parse(fs.readFileSync(CACHE_PATH, 'utf8'));
  } catch { /* empty cache */ }
  return {};
}

export function saveCache(cache: Record<string, number[]>): void {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  fs.writeFileSync(CACHE_PATH, JSON.stringify(cache));
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}
