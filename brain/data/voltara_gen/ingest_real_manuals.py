#!/usr/bin/env python3
"""Add REAL manuals (PDF / .txt / .md you are licensed to use) to the RAG corpus.

Usage:
  python3 ingest_real_manuals.py --src real_manuals --rag output/rag/rag_chunks.jsonl [--machine-family GP]
Put files in `real_manuals/` (file name = document id). PDFs need `pip install pypdf`.
Chunks follow the same schema as rag_chunks.jsonl (source_type="real_manual").
"""
import argparse, json, os, re, sys

def read(path):
    if path.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            sys.exit("pip install pypdf to read PDFs")
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    return open(path, errors="ignore").read()

def chunks(text, n=350, overlap=50):
    words = text.split()
    i = 0
    while i < len(words):
        yield " ".join(words[i:i + n])
        i += n - overlap

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="real_manuals")
ap.add_argument("--rag", default="output/rag/rag_chunks.jsonl")
ap.add_argument("--machine-family", default=None)
a = ap.parse_args()
start = sum(1 for _ in open(a.rag)) + 1
new = []
for fn in sorted(os.listdir(a.src)):
    doc = os.path.splitext(fn)[0]
    for j, c in enumerate(chunks(re.sub(r"\s+", " ", read(os.path.join(a.src, fn))))):
        new.append(dict(chunk_id=f"c{start + len(new):07d}", source_type="real_manual", source_id=doc, machine_id=None,
                        area=None, title=doc, text=f"[{doc}] {c}", metadata=dict(family=a.machine_family, part=j, file=fn)))
with open(a.rag, "a") as f:
    for r in new:
        f.write(json.dumps(r) + "\n")
print(f"appended {len(new)} chunks")
