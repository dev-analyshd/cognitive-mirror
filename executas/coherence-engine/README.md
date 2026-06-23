# Coherence Engine

**Anna Executa Tool** — 5-plane cognitive coherence engine for the Cognitive Mirror app.

## What It Does

Computes a real-time cognitive coherence score `Ψ(t)` from conversation message streams using mathematically-rigorous behavioral oracle mathematics derived from TRION Protocol and SOVEREIGN-Ω research.

## Mathematics

### 5-Plane Coherence

```
Ψ(t) = 0.25·P(t) + 0.30·I(t) + 0.20·C(t) + 0.15·S(t) + 0.10·W(t)
```

| Plane | Weight | Description |
|-------|--------|-------------|
| P — Perceptual | 0.25 | Entropy of message length, temporal spacing, punctuation |
| I — Inferential | 0.30 | Reasoning chain consistency (questions = uncertainty) |
| C — Consensus | 0.20 | Agreement with your historical patterns |
| S — Self-Reflection | 0.15 | Meta-cognitive marker density |
| W — World Model | 0.10 | Environmental anomaly (code ratio proxy) |

### Dynamic Threshold

```
Θ(t) = 0.55 + 0.37 × V(t)
```

Where `V(t)` is the volatility (standard deviation) of plane scores.

### Gate Logic

- `Ψ ≥ Θ` → **ACT** — Cognitive state supports deep work
- `Ψ < Θ` → **SILENCE** — Sub-threshold; rest recommended

### 9 Shannon Entropy Features (F1–F9)

| Feature | Description |
|---------|-------------|
| F1 | Message length distribution entropy |
| F2 | Vocabulary diversity (unique/total words) |
| F3 | Temporal spacing entropy |
| F4 | Topic concentration entropy |
| F5 | Punctuation entropy (emotional proxy) |
| F6 | Question ratio (curiosity vs assertion) |
| F7 | Code block frequency (technical depth) |
| F8 | Length consistency (perfectionism proxy) |
| F9 | Topic transition entropy (cross-conversation drift) |

## JSON-RPC Protocol

### Describe

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"describe"}' | python coherence_engine.py
```

### Evaluate

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"call","params":{"name":"evaluate","arguments":{"messages":[{"content":"How do I approach this? Let me think through the steps.","timestamp":1748965722,"topic":"coding","role":"user"}]}}}' | python coherence_engine.py
```

### Health Check

```bash
echo '{"jsonrpc":"2.0","id":3,"method":"call","params":{"name":"health","arguments":{}}}' | python coherence_engine.py
```

## Installation

```bash
cd executas/coherence-engine
uv tool install . --reinstall
```

Or run directly:

```bash
python coherence_engine.py
```

## Testing

```bash
cd tests
python test_coherence_engine.py
```

Expected output: 20+ tests covering Shannon entropy correctness, plane score ranges, weight sum invariant, gate logic determinism, structured silence completeness, archetype classification, and JSON-RPC protocol compliance.
