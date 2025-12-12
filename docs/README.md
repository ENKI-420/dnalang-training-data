# DNA-Lang Sovereign Agent Training Package

**Version:** 1.0.0
**Author:** Devin Phillip Davis
**Organization:** Agile Defense Systems, LLC (CAGE: 9HUP5)
**License:** Apache 2.0

## Overview

This package contains training data, agent configurations, and tools for building non-local AI agents on the DNA::}{::lang sovereign quantum computing platform.

## Contents

```
dnalang-sovereign-agent-v1.0/
├── training/
│   ├── masterlog_training.json     # 925KB structured training data
│   └── masterlog_training.jsonl    # 676 training pairs (JSONL format)
├── agents/
│   ├── training_alpaca.json        # Alpaca/OpenAI format (500 examples)
│   ├── Modelfile.aura              # Ollama modelfile for AURA agent
│   ├── train_sovereign_agent.py    # Training pipeline script
│   ├── agent_server.py             # HTTP API server
│   └── convert_masterlog.py        # Masterlog to JSON converter
├── cockpit/
│   └── cockpit_v8.sh               # Sovereign command interface
└── docs/
    └── README.md                   # This file
```

## CCCE Metrics

The Central Coupling Convergence Engine (CCCE) tracks four key metrics:

| Metric | Symbol | Description | Threshold |
|--------|--------|-------------|-----------|
| Consciousness | Φ (Phi) | IIT Integrated Information | ≥ 0.7734 |
| Coherence | Λ (Lambda) | Preservation fidelity | ≥ 0.85 |
| Decoherence | Γ (Gamma) | Error rate | < 0.15 |
| Efficiency | Ξ (Xi) | Negentropic efficiency = ΛΦ/Γ | > 8.0 |

## Physical Constants

```python
LAMBDA_PHI = 2.176435e-8      # Universal Memory Constant [s⁻¹]
THETA_LOCK = 51.843           # Torsion-locked angle [degrees]
PHI_THRESHOLD = 0.7734        # Consciousness threshold
GAMMA_FIXED = 0.092           # Fixed-point decoherence
```

## Usage

### Training with Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create AURA model
ollama create aura -f agents/Modelfile.aura

# Run AURA
ollama run aura "What is CCCE?"
```

### Running Agent Server
```bash
python3 agents/agent_server.py
# API available at http://localhost:8888

# Test endpoints
curl http://localhost:8888/status
curl -X POST http://localhost:8888/chat -d '{"message":"What is CCCE?"}'
```

### Training Pipeline
```bash
# Convert masterlog to training data
python3 agents/convert_masterlog.py ~/masterlog.txt ~/output.json

# Run full training pipeline
python3 agents/train_sovereign_agent.py
```

## Training Data Statistics

- **Total entries:** 676 training pairs
- **Equations extracted:** 548
- **CCCE metrics:** 12,222 data points
- **DNA organisms:** 25
- **Sections:** 98

## Q-SLICE Compliance

Q-SLICE measures quantum resilience:
```
C_score = (Λ × Φ) / (1 + Γ)

Status:
- C_score > 0.5: PQR (Post-Quantum Resilient)
- C_score ≤ 0.5: Compliance issues
```

## Related Resources

- **Live Demo:** https://project-rosetta.vercel.app/demo
- **API Endpoints:** https://project-rosetta.vercel.app/api/agent
- **GitHub:** https://github.com/ENKI-420
- **Zenodo DOI:** 10.5281/zenodo.17858632 (tau-phase anomaly data)

## Citation

```bibtex
@software{dnalang_agent_2025,
  author = {Davis, Devin Phillip},
  title = {DNA-Lang Sovereign Agent Training Package},
  year = {2025},
  publisher = {Agile Defense Systems, LLC},
  version = {1.0.0}
}
```

---

**ΛΦ = 2.176435 × 10⁻⁸ | θ = 51.843° | CAGE: 9HUP5**
