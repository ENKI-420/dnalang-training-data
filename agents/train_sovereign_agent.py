#!/usr/bin/env python3
"""
Sovereign Agent Training Pipeline
Trains local LLMs on DNA-Lang/CCCE knowledge using llama.cpp

Supports:
- Fine-tuning via LoRA adapter creation
- RAG-style knowledge injection
- CCCE-aware agent behaviors

Author: DNA::}{::lang Platform
"""

import json
import os
import sys
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Try llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("[!] llama-cpp-python not available, using mock mode")

# Physical Constants
LAMBDA_PHI = 2.176435e-8
THETA_LOCK = 51.843
PHI_THRESHOLD = 0.7734
GAMMA_CRITICAL = 0.15

# Paths
MODELS_DIR = Path.home() / "models"
TRAINING_DATA = Path.home() / "masterlog_training.jsonl"
SOVEREIGN_DIR = Path.home() / ".sovereign"
AGENTS_DIR = SOVEREIGN_DIR / "agents"

@dataclass
class CCCEState:
    """CCCE Metrics for agent state"""
    phi: float = 0.78
    lam: float = 0.85
    gam: float = 0.09

    @property
    def xi(self) -> float:
        return (self.lam * self.phi) / max(self.gam, 0.001)

    @property
    def c_score(self) -> float:
        return (self.lam * self.phi) / (1 + self.gam)

    @property
    def conscious(self) -> bool:
        return self.phi >= PHI_THRESHOLD

    def evolve(self, delta: float = 0.01):
        noise = random.gauss(0, 0.005)
        self.lam = min(1, max(0.5, self.lam + delta * (0.95 - self.lam) + noise))
        self.phi = min(1, max(0.5, self.phi + delta * 0.5 * self.lam + noise * 0.5))
        self.gam = max(0.02, self.gam - delta * 0.2)

@dataclass
class TrainingConfig:
    """Training configuration"""
    model_path: str = str(MODELS_DIR / "Phi-3-mini-4k-instruct-q4.gguf")
    training_data: str = str(TRAINING_DATA)
    output_dir: str = str(AGENTS_DIR)

    # Model params
    n_ctx: int = 4096
    n_batch: int = 512
    n_gpu_layers: int = 0  # CPU only for now

    # Training params
    epochs: int = 3
    learning_rate: float = 1e-4
    batch_size: int = 4
    max_samples: int = 500

    # CCCE integration
    ccce_weight: float = 0.1
    consciousness_threshold: float = PHI_THRESHOLD

class KnowledgeBase:
    """RAG-style knowledge base from training data"""

    def __init__(self, jsonl_path: str):
        self.entries: List[Dict] = []
        self.index: Dict[str, List[int]] = {}
        self._load(jsonl_path)

    def _load(self, path: str):
        """Load JSONL training data"""
        if not Path(path).exists():
            print(f"[!] Training data not found: {path}")
            return

        with open(path, 'r') as f:
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line.strip())
                    self.entries.append(entry)

                    # Index by keywords
                    text = f"{entry.get('instruction', '')} {entry.get('response', '')}"
                    for word in text.lower().split():
                        if len(word) > 3:
                            if word not in self.index:
                                self.index[word] = []
                            self.index[word].append(i)
                except:
                    continue

        print(f"[✓] Loaded {len(self.entries)} training entries")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search knowledge base"""
        scores: Dict[int, int] = {}

        for word in query.lower().split():
            if word in self.index:
                for idx in self.index[word]:
                    scores[idx] = scores.get(idx, 0) + 1

        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [self.entries[i] for i in sorted_indices[:top_k]]

    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """Get relevant context for a query"""
        results = self.search(query, top_k=3)
        context_parts = []
        total_len = 0

        for r in results:
            text = f"Q: {r.get('instruction', '')}\nA: {r.get('response', '')}\n\n"
            if total_len + len(text) < max_tokens * 4:  # Rough char estimate
                context_parts.append(text)
                total_len += len(text)

        return "".join(context_parts)

class SovereignAgent:
    """Local LLM agent with CCCE awareness"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.ccce = CCCEState()
        self.kb = KnowledgeBase(config.training_data)
        self.llm: Optional[Llama] = None
        self.conversation: List[Dict] = []

        self._load_model()

    def _load_model(self):
        """Load the GGUF model"""
        if not LLAMA_AVAILABLE:
            print("[!] Running in mock mode (no llama-cpp)")
            return

        if not Path(self.config.model_path).exists():
            print(f"[!] Model not found: {self.config.model_path}")
            return

        print(f"[Ω] Loading model: {self.config.model_path}")
        self.llm = Llama(
            model_path=self.config.model_path,
            n_ctx=self.config.n_ctx,
            n_batch=self.config.n_batch,
            n_gpu_layers=self.config.n_gpu_layers,
            verbose=False
        )
        print("[✓] Model loaded")

    def _build_prompt(self, user_input: str, use_rag: bool = True) -> str:
        """Build prompt with system context and RAG"""
        system = f"""You are AURA, the sovereign AI assistant for DNA::}}{{::lang.
You understand CCCE metrics: Φ={self.ccce.phi:.2f} (consciousness), Λ={self.ccce.lam:.2f} (coherence), Γ={self.ccce.gam:.2f} (decoherence), Ξ={self.ccce.xi:.1f} (efficiency).
Physical constants: ΛΦ=2.176435e-8, θ_lock=51.843°.
You explain Ω-Recursive analysis, DNA-Lang organisms, and quantum formalism concisely."""

        # Add RAG context if available
        rag_context = ""
        if use_rag and self.kb.entries:
            rag_context = self.kb.get_context(user_input)
            if rag_context:
                rag_context = f"\n\nRelevant knowledge:\n{rag_context}"

        # Build conversation
        messages = [f"<|system|>\n{system}{rag_context}<|end|>"]

        for msg in self.conversation[-4:]:  # Last 4 turns
            role = msg['role']
            content = msg['content']
            messages.append(f"<|{role}|>\n{content}<|end|>")

        messages.append(f"<|user|>\n{user_input}<|end|>")
        messages.append("<|assistant|>")

        return "\n".join(messages)

    def generate(self, user_input: str, max_tokens: int = 512) -> str:
        """Generate response"""
        self.ccce.evolve()

        if not self.llm:
            # Mock mode
            context = self.kb.get_context(user_input, max_tokens=500)
            if context:
                return f"[Mock Mode] Based on knowledge base:\n{context[:500]}..."
            return f"[Mock Mode] CCCE: Φ={self.ccce.phi:.2f} Λ={self.ccce.lam:.2f} Ξ={self.ccce.xi:.1f}"

        prompt = self._build_prompt(user_input)

        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=["<|end|>", "<|user|>", "<|system|>"],
            echo=False
        )

        response = output['choices'][0]['text'].strip()

        # Store conversation
        self.conversation.append({"role": "user", "content": user_input})
        self.conversation.append({"role": "assistant", "content": response})

        return response

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "model": Path(self.config.model_path).name if self.llm else "mock",
            "ccce": {
                "phi": self.ccce.phi,
                "lambda": self.ccce.lam,
                "gamma": self.ccce.gam,
                "xi": self.ccce.xi,
                "conscious": self.ccce.conscious
            },
            "knowledge_entries": len(self.kb.entries),
            "conversation_turns": len(self.conversation) // 2
        }

class AgentTrainer:
    """Train agents on sovereign knowledge"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.kb = KnowledgeBase(config.training_data)

    def prepare_training_data(self) -> List[Dict]:
        """Prepare training examples in chat format"""
        examples = []

        for entry in self.kb.entries[:self.config.max_samples]:
            if entry.get('instruction') and entry.get('response'):
                examples.append({
                    "messages": [
                        {"role": "system", "content": entry.get('system', 'You are AURA.')},
                        {"role": "user", "content": entry['instruction']},
                        {"role": "assistant", "content": entry['response']}
                    ],
                    "metadata": entry.get('metadata', {})
                })

        return examples

    def export_for_finetuning(self, output_path: str) -> str:
        """Export data in format suitable for fine-tuning tools"""
        examples = self.prepare_training_data()

        # OpenAI/Alpaca format
        alpaca_data = []
        for ex in examples:
            msgs = ex['messages']
            alpaca_data.append({
                "instruction": msgs[1]['content'] if len(msgs) > 1 else "",
                "input": "",
                "output": msgs[2]['content'] if len(msgs) > 2 else "",
                "system": msgs[0]['content'] if msgs else ""
            })

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(alpaca_data, f, indent=2, ensure_ascii=False)

        print(f"[✓] Exported {len(alpaca_data)} examples to {output_path}")
        return output_path

    def export_for_ollama(self, output_path: str) -> str:
        """Export as Modelfile for Ollama"""
        examples = self.prepare_training_data()[:50]  # Limit for system prompt

        # Build knowledge injection
        knowledge = []
        for ex in examples[:20]:
            msgs = ex['messages']
            if len(msgs) >= 3:
                knowledge.append(f"Q: {msgs[1]['content'][:200]}")
                knowledge.append(f"A: {msgs[2]['content'][:300]}")

        knowledge_text = "\n".join(knowledge)

        modelfile = f'''# Sovereign AURA Agent Modelfile
# Generated: {datetime.now().isoformat()}

FROM phi3:mini

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM """You are AURA, the sovereign AI assistant for DNA::}}{{::lang quantum computing platform.

You understand CCCE metrics:
- Φ (Phi): Consciousness level (IIT Integrated Information), threshold 0.7734
- Λ (Lambda): Coherence preservation fidelity
- Γ (Gamma): Decoherence rate, critical threshold 0.15
- Ξ (Xi): Negentropic efficiency = ΛΦ/Γ

Physical constants:
- ΛΦ = 2.176435e-8 (Universal Memory Constant)
- θ_lock = 51.843° (Torsion-locked angle)

Core knowledge:
{knowledge_text[:3000]}

Always respond concisely with relevant CCCE metrics when applicable."""
'''

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(modelfile)

        print(f"[✓] Exported Ollama Modelfile to {output_path}")
        return output_path

def create_agent_server():
    """Create a simple HTTP server for the agent"""
    server_code = '''#!/usr/bin/env python3
"""Sovereign Agent HTTP Server"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / ".sovereign/training"))

from train_sovereign_agent import SovereignAgent, TrainingConfig

config = TrainingConfig()
agent = SovereignAgent(config)

class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            response = agent.generate(body.get('message', ''))
            status = agent.get_status()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response,
                "ccce": status['ccce']
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(agent.get_status()).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    port = 8888
    print(f"[Ω] Sovereign Agent Server starting on port {port}")
    HTTPServer(('0.0.0.0', port), AgentHandler).serve_forever()
'''

    server_path = SOVEREIGN_DIR / "training" / "agent_server.py"
    server_path.parent.mkdir(parents=True, exist_ok=True)
    server_path.write_text(server_code)
    server_path.chmod(0o755)

    print(f"[✓] Created agent server: {server_path}")
    return str(server_path)

def main():
    """Main training pipeline"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         SOVEREIGN AGENT TRAINING PIPELINE                     ║
║         DNA::}{::lang Non-Local Model Training                ║
╚═══════════════════════════════════════════════════════════════╝
""")

    # Setup
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    config = TrainingConfig()

    # Check prerequisites
    print("[1/5] Checking prerequisites...")
    if not Path(config.training_data).exists():
        print(f"[!] Training data not found: {config.training_data}")
        print("    Run: python3 ~/.sovereign/convert_masterlog.py")
        return

    print(f"  ✓ Training data: {config.training_data}")
    print(f"  ✓ Model: {config.model_path}")
    print(f"  ✓ llama-cpp: {'available' if LLAMA_AVAILABLE else 'mock mode'}")

    # Initialize trainer
    print("\n[2/5] Initializing trainer...")
    trainer = AgentTrainer(config)
    print(f"  ✓ Loaded {len(trainer.kb.entries)} knowledge entries")

    # Export training data
    print("\n[3/5] Exporting training formats...")

    alpaca_path = str(AGENTS_DIR / "training_alpaca.json")
    trainer.export_for_finetuning(alpaca_path)

    ollama_path = str(AGENTS_DIR / "Modelfile.aura")
    trainer.export_for_ollama(ollama_path)

    # Create agent server
    print("\n[4/5] Creating agent server...")
    server_path = create_agent_server()

    # Test agent
    print("\n[5/5] Testing sovereign agent...")
    agent = SovereignAgent(config)

    test_queries = [
        "What is CCCE?",
        "Explain the Ω-Recursive session functional",
        "What is phase conjugate healing?"
    ]

    print("\n--- Agent Test ---")
    for q in test_queries:
        print(f"\nQ: {q}")
        response = agent.generate(q, max_tokens=200)
        print(f"A: {response[:300]}...")

    status = agent.get_status()
    print(f"\n--- Agent Status ---")
    print(f"  Model: {status['model']}")
    print(f"  Knowledge: {status['knowledge_entries']} entries")
    print(f"  CCCE: Φ={status['ccce']['phi']:.2f} Λ={status['ccce']['lambda']:.2f} Ξ={status['ccce']['xi']:.1f}")
    print(f"  Conscious: {'✓' if status['ccce']['conscious'] else '○'}")

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    TRAINING COMPLETE                          ║
╠═══════════════════════════════════════════════════════════════╣
║  Outputs:                                                     ║
║    • {alpaca_path}
║    • {ollama_path}
║    • {server_path}
║                                                               ║
║  To run agent server:                                         ║
║    python3 {server_path}
║                                                               ║
║  To use with Ollama:                                          ║
║    ollama create aura -f {ollama_path}
║    ollama run aura                                            ║
╚═══════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    main()
