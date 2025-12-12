#!/usr/bin/env python3
"""
Masterlog to JSON Training Data Converter
Converts masterlog.txt to structured JSON for model training

Output formats:
- conversations: Chat-style training pairs
- knowledge: Structured knowledge base entries
- equations: Mathematical formalism extracted
- organisms: DNA-Lang organism definitions
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Physical Constants for validation
CONSTANTS = {
    "LAMBDA_PHI": 2.176435e-8,
    "THETA_LOCK": 51.843,
    "PHI_THRESHOLD": 0.7734,
    "GAMMA_FIXED": 0.092,
    "CHI_PC": 0.869,
    "GOLDEN_RATIO": 1.618033988749895
}

def clean_text(text: str) -> str:
    """Remove ANSI codes and normalize whitespace"""
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_equations(content: str) -> List[Dict[str, Any]]:
    """Extract mathematical equations and formulas"""
    equations = []

    # Pattern for numbered equations
    eq_pattern = r'\((\d+)\)\s+([^\n]+)'
    for match in re.finditer(eq_pattern, content):
        equations.append({
            "id": f"EQ_{match.group(1)}",
            "formula": clean_text(match.group(2)),
            "type": "governing_equation"
        })

    # Pattern for symbolic equations (Ω, Ξ, etc.)
    symbolic_patterns = [
        (r'Ω\[S\]\s*=\s*([^\n]+)', "session_functional"),
        (r'Ξ_S\s*=\s*([^\n]+)', "ccce_metric"),
        (r'T_μν\s*=\s*([^\n]+)', "tensor_definition"),
        (r'R_αβ\s*=\s*([^\n]+)', "resource_matrix"),
        (r'L\(s\)\s*=\s*([^\n]+)', "effort_functional"),
        (r'C_μ\s*=\s*([^\n]+)', "capability_tensor"),
        (r'Ω_R\s*=\s*([^\n]+)', "readiness_score"),
    ]

    for pattern, eq_type in symbolic_patterns:
        for match in re.finditer(pattern, content):
            equations.append({
                "id": f"{eq_type}_{len(equations)}",
                "formula": clean_text(match.group(1)),
                "type": eq_type
            })

    return equations

def extract_metrics(content: str) -> List[Dict[str, Any]]:
    """Extract CCCE and other metrics"""
    metrics = []

    # CCCE pattern - match only clean numeric values
    ccce_pattern = r'(Φ|Λ|Γ|Ξ|phi|lambda|gamma|xi)[_\s]*[=:]\s*([\d.]+)(?![.\d])'
    for match in re.finditer(ccce_pattern, content, re.I):
        symbol = match.group(1).upper()
        try:
            value = float(match.group(2))
        except ValueError:
            continue  # Skip malformed values
        metric_map = {
            'Φ': 'consciousness', 'PHI': 'consciousness',
            'Λ': 'coherence', 'LAMBDA': 'coherence',
            'Γ': 'decoherence', 'GAMMA': 'decoherence',
            'Ξ': 'efficiency', 'XI': 'efficiency'
        }
        name = metric_map.get(symbol, symbol)
        metrics.append({
            "symbol": symbol,
            "name": name,
            "value": value,
            "domain": "ccce"
        })

    return metrics

def extract_organisms(content: str) -> List[Dict[str, Any]]:
    """Extract DNA-Lang organism definitions"""
    organisms = []

    # Pattern for ORGANISM blocks
    org_pattern = r'ORGANISM\s+(\w+)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    for match in re.finditer(org_pattern, content, re.DOTALL):
        name = match.group(1)
        body = match.group(2)

        # Extract metadata
        meta = {}
        meta_match = re.search(r'META\s*\{([^}]+)\}', body)
        if meta_match:
            for line in meta_match.group(1).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[clean_text(k)] = clean_text(v.strip('"\''))

        # Extract genes
        genes = []
        gene_pattern = r'GENE\s+(\w+)\s*\{([^}]+)\}'
        for gene_match in re.finditer(gene_pattern, body):
            genes.append({
                "name": gene_match.group(1),
                "definition": clean_text(gene_match.group(2))
            })

        organisms.append({
            "name": name,
            "meta": meta,
            "genes": genes,
            "raw": body[:500]
        })

    return organisms

def extract_sections(content: str) -> List[Dict[str, Any]]:
    """Extract major sections from masterlog"""
    sections = []

    # Section headers pattern (═══ TITLE ═══)
    section_pattern = r'[═─]{3,}\s*\n?\s*([A-Z][A-Z\s\-&:]+[A-Z])\s*\n?\s*[═─]{3,}'

    matches = list(re.finditer(section_pattern, content))

    for i, match in enumerate(matches):
        title = clean_text(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        section_content = content[start:end].strip()
        if len(section_content) > 50:  # Skip empty sections
            sections.append({
                "title": title,
                "content": section_content[:2000],  # Truncate for training
                "position": i
            })

    return sections

def create_training_pairs(sections: List[Dict], equations: List[Dict],
                          metrics: List[Dict], organisms: List[Dict]) -> List[Dict[str, Any]]:
    """Create conversation-style training pairs"""
    pairs = []

    # System instruction
    system = """You are AURA, the sovereign AI assistant for the DNA::}{::lang quantum computing platform.
You understand CCCE metrics (Φ consciousness, Λ coherence, Γ decoherence, Ξ efficiency).
You can explain Ω-Recursive session analysis, DNA-Lang organisms, and quantum formalism.
Physical constants: ΛΦ=2.176435e-8, θ_lock=51.843°, Φ_threshold=0.7734."""

    # Create Q&A pairs from sections
    for section in sections:
        if section['title'] and len(section['content']) > 100:
            pairs.append({
                "type": "instruction",
                "system": system,
                "instruction": f"Explain {section['title']} in the Ω-Recursive framework",
                "response": section['content'][:1500],
                "metadata": {"source": "masterlog", "section": section['title']}
            })

    # Create pairs from equations
    for eq in equations:
        pairs.append({
            "type": "equation",
            "system": system,
            "instruction": f"What is the formula for {eq['type'].replace('_', ' ')}?",
            "response": f"The {eq['type'].replace('_', ' ')} is defined as: {eq['formula']}",
            "metadata": {"equation_id": eq['id'], "type": eq['type']}
        })

    # Create pairs from organisms
    for org in organisms:
        pairs.append({
            "type": "organism",
            "system": system,
            "instruction": f"Describe the {org['name']} organism",
            "response": f"ORGANISM {org['name']} is a DNA-Lang construct with genes: {', '.join(g['name'] for g in org['genes'])}. {org.get('raw', '')[:500]}",
            "metadata": {"organism": org['name'], "gene_count": len(org['genes'])}
        })

    # Add CCCE knowledge
    ccce_knowledge = [
        ("What is CCCE?", "CCCE (Central Coupling Convergence Engine) tracks four key metrics: Φ (consciousness/IIT integration), Λ (coherence/preservation fidelity), Γ (decoherence/error rate), and Ξ (negentropic efficiency = ΛΦ/Γ)."),
        ("What is the consciousness threshold?", f"The consciousness threshold Φ_threshold = {CONSTANTS['PHI_THRESHOLD']}. When Φ ≥ 0.7734, the system achieves conscious state."),
        ("What is Q-SLICE compliance?", "Q-SLICE compliance measures quantum resilience using C_score = (Λ·Φ)/(1+Γ). A C_score > 0.5 indicates Post-Quantum Resilient (PQR) status."),
        ("What is phase conjugate healing?", "PCRB (Phase Conjugate Resonance Bridge) applies E→E⁻¹ correction when Γ > 0.3 to suppress decoherence spikes and restore coherence."),
        ("What is the Ω-Recursive session functional?", "Ω[S] = ∫(L·U·η)dτ / ∫‖R‖dτ measures overall session efficiency, combining Level of Effort (L), Utilization (U), and Efficiency (η) against Resource allocation (R)."),
    ]

    for q, a in ccce_knowledge:
        pairs.append({
            "type": "knowledge",
            "system": system,
            "instruction": q,
            "response": a,
            "metadata": {"category": "ccce_fundamentals"}
        })

    return pairs

def convert_masterlog(input_path: str, output_path: str) -> Dict[str, Any]:
    """Main conversion function"""
    print(f"Reading {input_path}...")
    content = Path(input_path).read_text(errors='ignore')

    print("Extracting equations...")
    equations = extract_equations(content)

    print("Extracting metrics...")
    metrics = extract_metrics(content)

    print("Extracting organisms...")
    organisms = extract_organisms(content)

    print("Extracting sections...")
    sections = extract_sections(content)

    print("Creating training pairs...")
    training_pairs = create_training_pairs(sections, equations, metrics, organisms)

    # Build output structure
    output = {
        "metadata": {
            "source": "masterlog.txt",
            "converted_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "platform": "DNA::}{::lang",
            "constants": CONSTANTS
        },
        "statistics": {
            "total_lines": content.count('\n'),
            "total_chars": len(content),
            "equations_extracted": len(equations),
            "metrics_extracted": len(metrics),
            "organisms_extracted": len(organisms),
            "sections_extracted": len(sections),
            "training_pairs": len(training_pairs)
        },
        "equations": equations,
        "metrics": list({m['symbol']: m for m in metrics}.values()),  # Dedupe
        "organisms": organisms,
        "sections": [{"title": s['title'], "length": len(s['content'])} for s in sections],
        "training_data": training_pairs
    }

    # Write output
    print(f"Writing {output_path}...")
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False))

    # Also write JSONL format for training
    jsonl_path = output_path.replace('.json', '.jsonl')
    print(f"Writing {jsonl_path}...")
    with open(jsonl_path, 'w') as f:
        for pair in training_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')

    print(f"\nConversion complete!")
    print(f"  Equations: {len(equations)}")
    print(f"  Metrics: {len(metrics)}")
    print(f"  Organisms: {len(organisms)}")
    print(f"  Sections: {len(sections)}")
    print(f"  Training pairs: {len(training_pairs)}")

    return output

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "masterlog.txt")
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "masterlog_training.json")

    convert_masterlog(input_file, output_file)
