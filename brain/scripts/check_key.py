#!/usr/bin/env python3
"""Verify GEMINI_API_KEY, list usable models, and make one tiny call per role."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, ratelimit  # noqa: E402


def main():
    if not config.API_KEY:
        print("GEMINI_API_KEY not set. Put it in brain/.env (see .env.example).")
        sys.exit(1)
    from google import genai
    client = genai.Client(api_key=config.API_KEY)
    gen, emb = [], []
    for m in ratelimit.call_with_retry("lite", lambda: list(client.models.list())):
        acts = getattr(m, "supported_actions", None) or []
        name = m.name.replace("models/", "")
        if "generateContent" in acts:
            gen.append(name)
        if "embedContent" in acts:
            emb.append(name)
    print("generate models:", ", ".join(sorted(gen)[:25]))
    print("embed models   :", ", ".join(sorted(emb)))
    for role in ("agent", "lite"):
        name = config.MODELS[role]
        if name not in gen:
            print(f"WARN {role}: {name} not available to this key; pick one from the list above")
            continue
        r = ratelimit.call_with_retry(role, lambda: client.models.generate_content(
            model=name, contents="Reply with the single word: ok"))
        print(f"OK {role}: {name} -> {r.text.strip()[:20]!r}")
    en = config.MODELS["embed"]
    if en in emb:
        r = ratelimit.call_with_retry("embed", lambda: client.models.embed_content(
            model=en, contents="hello plant"))
        print(f"OK embed: {en} dim={len(r.embeddings[0].values)}")
    else:
        print(f"WARN embed: {en} not available; pick one from the list above")
    for role in ("agent", "lite", "embed"):
        l = ratelimit.limiter(role)
        print(f"usage today {role}: {l.used_today()}/{l.rpd} (client RPM cap {l.rpm})")


if __name__ == "__main__":
    main()
