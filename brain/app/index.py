"""Hybrid retrieval over rag/rag_chunks.jsonl: dense (exact numpy inner product) + BM25, fused with RRF.

Exact flat search over ~11k normalised vectors is a single matmul (sub-millisecond), so FAISS
is not needed; importing faiss together with torch also segfaulted on this macOS setup.

- Embeddings: local sentence-transformers by default (no quota); Gemini optional via
  EMBED_BACKEND=gemini (rate limited, batched). Cached on disk by chunk-text hash, so
  reruns never re-embed.
- Metadata filters: machine_id (twin or voltara id, plus that machine's family manuals),
  doc_type (source_type), family, area, fault_code, shift.
"""
import hashlib
import json
import os
import re

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
from functools import lru_cache

import numpy as np

from . import config, ratelimit
from .graph import get_graph

CHUNKS = config.BRAIN_DIR / "data" / "out" / "rag" / "rag_chunks.jsonl"
_TOK = re.compile(r"[a-z0-9][a-z0-9_.\-]*")


def tokenize(text):
    toks = _TOK.findall(text.lower())
    out = []
    for t in toks:
        out.append(t)
        if "-" in t or "_" in t:           # also index the parts of fault codes / ids
            out.extend(p for p in re.split(r"[-_]", t) if len(p) > 1)
    return out


# Deterministic intent expansion: maps natural phrasing onto the vocabulary of our SOP titles.
_EXPAND = [
    (re.compile(r"keep (it )?running|run (it )?(on|longer)|more hours?|extend(ed)? run|continue running|run to failure", re.I),
     "run-extension run-to-failure risk decision SOP-OPS-02"),
    (re.compile(r"who (do i|should i|to) (page|call|contact)|\bpage\b|escalat", re.I),
     "who to page escalation chain L1 primary technician L2 backup L3 supervisor"),
    (re.compile(r"lock ?out|tag ?out|loto|isolat", re.I), "lockout tagout SOP-SAF-01"),
    (re.compile(r"spare|in stock|part number|on hand", re.I), "spare part stock on hand lead time"),
    (re.compile(r"why is .{0,30}(red|alarm|alert|down|stopped)|what('s| is) wrong|what should we do", re.I),
     "symptom cause diagnosis fault mode repair procedure SOP"),
]
_MEANING = re.compile(r"what does .{0,40}(mean|stand for)|meaning of|what is (the )?(fault|alarm|error) code|explain .{0,20}(code|alarm)", re.I)
_PREFER_BONUS = 0.03
_SHIFT = re.compile(r"\bshift\s+([abc])\b", re.I)


def expand_query(q):
    extra = [e for rx, e in _EXPAND if rx.search(q)]
    return q + (" " + " ".join(extra) if extra else "")


def _h(text):
    return hashlib.sha1(text.encode()).hexdigest()


class Embedder:
    def __init__(self):
        self.backend = config.EMBED_BACKEND
        self._model = None
        self._client = None
        self.name = config.LOCAL_EMBED_MODEL if self.backend == "local" else config.MODELS["embed"]

    def _local(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.name, device="cpu")
        return self._model

    def embed(self, texts, batch=64):
        if self.backend == "local":
            v = self._local().encode(texts, batch_size=batch, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(v, dtype="float32")
        from google import genai
        self._client = self._client or genai.Client(api_key=config.API_KEY)
        out = []
        for i in range(0, len(texts), 50):
            part = texts[i:i + 50]
            est = sum(len(t) for t in part) // 3
            r = ratelimit.call_with_retry(
                "embed", lambda: self._client.models.embed_content(model=self.name, contents=part), est_tokens=est)
            out.extend(e.values for e in r.embeddings)
        v = np.asarray(out, dtype="float32")
        v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
        return v


class DocIndex:
    def __init__(self, chunks_path=CHUNKS, build=True):
        self.chunks = [json.loads(l) for l in open(chunks_path) if l.strip()]
        self.emb = Embedder()
        self.ids = {c["chunk_id"]: i for i, c in enumerate(self.chunks)}
        self._fam_by_machine = {}
        self.vecs = None
        self.bm25 = None
        if build:
            self.build()

    # ---------------------------------------------------------------- build
    def _cache_path(self):
        key = _h(self.emb.backend + self.emb.name)[:10]
        return config.CACHE_DIR / f"emb_{key}.npz"

    def build(self):
        from rank_bm25 import BM25Okapi
        texts = [c["text"] for c in self.chunks]
        hashes = [_h(t) for t in texts]
        cache = {}
        p = self._cache_path()
        if p.exists():
            z = np.load(p, allow_pickle=False)
            cache = dict(zip(z["hashes"].tolist(), z["vecs"]))
        missing = [i for i, h in enumerate(hashes) if h not in cache]
        if missing:
            v = self.emb.embed([texts[i] for i in missing])
            for i, row in zip(missing, v):
                cache[hashes[i]] = row
            p.parent.mkdir(parents=True, exist_ok=True)
            hs = list(cache.keys())
            np.savez(p, hashes=np.array(hs), vecs=np.stack([cache[h] for h in hs]))
        self.vecs = np.stack([cache[h] for h in hashes]).astype("float32")
        # title tokens counted twice so SOP/manual titles weigh more than body text
        self.bm25 = BM25Okapi([tokenize(c["title"] + " " + c["title"] + " " + c["text"]) for c in self.chunks])
        self.n_embedded_now = len(missing)

    # ---------------------------------------------------------------- filters
    def _family(self, machine_id):
        if machine_id not in self._fam_by_machine:
            m = get_graph().get_machine(machine_id)
            self._fam_by_machine[machine_id] = m["family"] if m else None
        return self._fam_by_machine[machine_id]

    def _mask(self, machine_id, doc_type, family, area, fault_code, shift, include_family_docs):
        n = len(self.chunks)
        mask = np.ones(n, dtype=bool)
        mid = None
        if machine_id:
            mid = get_graph().machine_id(machine_id) or machine_id
            fam = self._family(mid)
        for i, c in enumerate(self.chunks):
            if not mask[i]:
                continue
            md = c.get("metadata") or {}
            if machine_id:
                same = c["machine_id"] == mid
                famdoc = include_family_docs and fam and md.get("family") == fam and c["source_type"] == "manual"
                glob = include_family_docs and c["source_type"] == "sop"   # plant/area SOPs apply to every machine
                if not (same or famdoc or glob):
                    mask[i] = False
                    continue
            if doc_type and c["source_type"] not in ([doc_type] if isinstance(doc_type, str) else doc_type):
                mask[i] = False
            elif family and md.get("family") != family:
                mask[i] = False
            elif area and c.get("area") != area:
                mask[i] = False
            elif shift and md.get("shift") not in (None, shift):
                mask[i] = False
            elif fault_code and not (md.get("fault_code") == fault_code or fault_code.lower() in c["text"].lower()):
                mask[i] = False
        return mask

    # ---------------------------------------------------------------- search
    def search(self, query, k=6, machine_id=None, doc_type=None, family=None, area=None,
               fault_code=None, shift=None, include_family_docs=True, pool=60, rrf_k=60):
        if shift is None:
            m = _SHIFT.search(query)
            shift = m.group(1).upper() if m else None
        prefer = ("manual", "sop") if _MEANING.search(query) else ()
        query = expand_query(query)
        mask = None
        if any([machine_id, doc_type, family, area, fault_code, shift]):
            mask = self._mask(machine_id, doc_type, family, area, fault_code, shift, include_family_docs)
            if not mask.any():
                return []
        qv = self.emb.embed([query])
        scores = (self.vecs @ qv[0])
        bm = np.asarray(self.bm25.get_scores(tokenize(query)))
        if mask is not None:
            scores = np.where(mask, scores, -1e9)
            bm = np.where(mask, bm, -1e9)
        dense_top = np.argsort(-scores)[:pool]
        bm_top = np.argsort(-bm)[:pool]
        fused = {}
        for rank, i in enumerate(dense_top):
            if scores[i] > -1e8:
                fused[i] = fused.get(i, 0) + 1.0 / (rrf_k + rank + 1)
        for rank, i in enumerate(bm_top):
            if bm[i] > 0 and (mask is None or mask[i]):
                fused[i] = fused.get(i, 0) + 1.0 / (rrf_k + rank + 1)
        if prefer:
            for i in list(fused):
                if self.chunks[i]["source_type"] in prefer:
                    fused[i] += _PREFER_BONUS
        top = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
        out = []
        for i, s in top:
            c = self.chunks[i]
            out.append({"chunk_id": c["chunk_id"], "source_type": c["source_type"], "source_id": c["source_id"],
                        "machine_id": c["machine_id"], "area": c["area"], "title": c["title"], "text": c["text"],
                        "metadata": c.get("metadata"), "score": round(float(s), 5),
                        "dense": round(float(scores[i]), 3), "bm25": round(float(bm[i]), 2)})
        return out


@lru_cache(maxsize=1)
def get_index():
    return DocIndex()


def search_docs(query, machine_id=None, doc_type=None, k=6, **kw):
    return get_index().search(query, k=k, machine_id=machine_id, doc_type=doc_type, **kw)
