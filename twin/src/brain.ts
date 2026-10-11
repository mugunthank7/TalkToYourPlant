// Link to the brain (knowledge base + local LLM), brain/app/api.py. Override with VITE_BRAIN_URL.
export const BRAIN = (import.meta.env.VITE_BRAIN_URL as string | undefined) ?? "http://localhost:8100";

export async function brainGet<T = any>(path: string): Promise<T> {
  const r = await fetch(BRAIN + path);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

export async function brainPost<T = any>(path: string, body: unknown = {}): Promise<T> {
  const r = await fetch(BRAIN + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
