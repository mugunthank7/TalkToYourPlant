# Using a real local LLM (for a machine that can run one)

The brain works on any laptop with **no LLM** (`LLM_MODE=off`, the default): a deterministic router builds a structured card from
live tool results. On a stronger machine you can switch on `LLM_MODE=assist`: the same facts are given to a local model with a
strict system prompt, and the model phrases the reply. Every reply passes a grounding guard first; if it fails, the
deterministic answer is shown. So switching models can only make answers more natural, never less grounded.

## Switch it on (Ollama)
```bash
ollama pull qwen2.5:14b-instruct        # good default with 16 GB RAM; llama3.1:8b for 8-10 GB; qwen2.5:32b-instruct for 32 GB+
# brain/.env
LLM_MODE=assist
OLLAMA_MODEL=auto                       # or an exact tag; auto picks the best installed from MODEL_PREFERENCE
OLLAMA_NUM_CTX=8192
LLM_TIMEOUT=60
python3 brain/scripts/llm_check.py --all   # prints reply, guard result and latency for the demo questions
```
Restart the brain (`brain/scripts/stop_all.sh && brain/scripts/start_all.sh`). `GET :8100/health` shows `llm_mode` and the model.

## What the model does and does not do
| Situation | With `assist` |
|---|---|
| A card applies (why red, keep running, who to page, parts, what-if, output) | The model rewrites the card as 2 to 5 spoken sentences. The card is still returned as `report` and as `card` text. |
| Free question that retrieval partly answers | The model answers from the top 4 passages, or says what is missing. |
| Greeting, thanks, glossary, unknown machine, off-topic, purchase request | Deterministic reply, no model call (instant, fixed wording). |
| Station panel "plan" button | Uses the plan prompt (WHAT HAPPENED, DO NOW, WHO TO PAGE). |

## The prompts (`brain/app/prompts.py`)
Built from five blocks: persona (a calm maintenance lead), grounding rules, style rules, a JSON output contract, and a task
with one worked example.
- **Grounding rules:** use only the FACTS block; never invent or change ids, names, numbers, units, extensions or procedures;
  say plainly when the facts do not answer; no safety instructions beyond a cited SOP; cite only ids in ALLOWED_SOURCES; do not
  invent a problem when the machine is running normally.
- **Style rules:** answer or decision in the first sentence; no greeting, no "based on", no apologies; plain words; 2 to 5
  sentences; actions in order, verb first; one useful number; give the reason when advising against something.
- **Output contract:** `{"reply", "sources", "needs_clarification"}` as JSON (Ollama JSON mode).

## The grounding guard (`validate_reply`)
A reply is rejected, and the deterministic answer used, if it: is empty or over 900 characters; contains disclaimer language
("as an AI", "I apologize", "based on the provided context", ...); cites an id that was not retrieved; contains a number of two
or more digits that is not in the facts or the question; or contains markdown headings or code fences. `meta.llm.guard`
records the reason. If the model times out twice in a row the layer pauses for 5 minutes so chat never waits on a dead model.

## Tuning
- Replies too stiff: loosen STYLE in `prompts.py`; keep GROUNDING unchanged.
- Guard rejects numbers the model rounds ("about 150 minutes" for 153): tell it to copy numbers exactly (already in the prompt),
  or use a larger model.
- Add an example: put a second worked example in `NARRATE_SYSTEM` for the question type that reads worst.
- Change the model per machine without code: `OLLAMA_MODEL` in that machine's `brain/.env` (not committed).

## Measured so far
Only the plumbing was exercised here: on an 8 GB laptop the 7B model timed out (60 to 120 s), the guard path fell back to the
deterministic answer correctly, and the unit checks of the guard pass. Reply quality has **not** been measured with a capable
model yet; run `llm_check.py` on the stronger machine and record the acceptance rate in DECISIONS.md.
