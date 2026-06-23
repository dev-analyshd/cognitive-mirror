#!/usr/bin/env python3
"""
Cognitive Mirror — 5-Plane Cognitive Coherence Engine
Anna Executa Tool (stdio JSON-RPC)

Computes Psi(t) = 0.25*P + 0.30*I + 0.20*C + 0.15*S + 0.10*W
from conversation message streams using Shannon entropy features.

Derived from TRION Protocol behavioral oracle mathematics.
"""
import json
import sys
import math
import statistics
from collections import Counter
from typing import List, Dict, Any


def shannon_entropy(values: List[float]) -> float:
    """Normalized Shannon entropy H = -sum(p * log2(p)), normalized to [0,1]."""
    total = sum(values)
    if total == 0:
        return 0.0
    probs = [v / total for v in values if v > 0]
    if not probs:
        return 0.0
    raw_entropy = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(len(probs)) if len(probs) > 1 else 1.0
    return raw_entropy / max_entropy if max_entropy > 0 else 0.0


def extract_features(messages: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extract 9 Shannon entropy features from message stream.

    F1: Message length distribution entropy
    F2: Vocabulary diversity (unique / total words)
    F3: Temporal spacing entropy
    F4: Topic concentration entropy
    F5: Punctuation entropy (emotional state proxy)
    F6: Question ratio (curiosity vs assertion)
    F7: Code-block frequency (technical depth)
    F8: Length consistency (perfectionism proxy)
    F9: Topic transition entropy (cross-conversation drift)
    """
    n = max(len(messages), 1)

    # F1: Length distribution entropy
    lengths = [len(m.get('content', '')) for m in messages]
    length_counts = Counter(lengths)
    F1 = shannon_entropy(list(length_counts.values()))

    # F2: Vocabulary diversity
    all_text = ' '.join(m.get('content', '') for m in messages)
    words = all_text.split()
    F2 = len(set(w.lower() for w in words)) / max(len(words), 1)

    # F3: Temporal spacing entropy
    timestamps = sorted([m.get('timestamp', 0) for m in messages])
    if len(timestamps) > 1:
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        interval_counts = Counter(intervals)
        F3 = shannon_entropy(list(interval_counts.values()))
    else:
        F3 = 0.5

    # F4: Topic concentration entropy
    topics = [m.get('topic', 'general') for m in messages]
    topic_counts = Counter(topics)
    F4 = shannon_entropy(list(topic_counts.values()))

    # F5: Punctuation entropy (emotional state proxy)
    punct_counts = [sum(1 for c in m.get('content', '') if c in '?!.,;:-\u2014') for m in messages]
    punct_dist = Counter(punct_counts)
    F5 = shannon_entropy(list(punct_dist.values()))

    # F6: Question ratio (curiosity vs assertion)
    questions = sum(1 for m in messages if '?' in m.get('content', ''))
    F6 = questions / n

    # F7: Code-block frequency (technical depth)
    code_blocks = sum(1 for m in messages if '```' in m.get('content', ''))
    F7 = code_blocks / n

    # F8: Length consistency (low variance = high consistency = perfectionism/focus)
    if len(lengths) > 1:
        F8 = 1.0 - min(1.0, statistics.stdev(lengths) / (statistics.mean(lengths) + 1))
    else:
        F8 = 0.5

    # F9: Topic transition entropy (cross-conversation drift)
    if len(topics) > 1:
        transitions = [(topics[i], topics[i+1]) for i in range(len(topics)-1)]
        transition_counts = Counter(transitions)
        F9 = shannon_entropy(list(transition_counts.values()))
    else:
        F9 = 0.5

    return {
        'F1': round(F1, 4), 'F2': round(F2, 4), 'F3': round(F3, 4),
        'F4': round(F4, 4), 'F5': round(F5, 4), 'F6': round(F6, 4),
        'F7': round(F7, 4), 'F8': round(F8, 4), 'F9': round(F9, 4)
    }


def compute_planes(features: Dict[str, float]) -> Dict[str, float]:
    """
    Map 9 entropy features to 5 cognitive planes.

    P (Perceptual)     = mean(F1, F3, F5) — sensory/environmental entropy
    I (Inferential)    = 1 - (F6 * 0.8)  — reasoning consistency (questions = uncertainty)
    C (Consensus)      = mean(F4, F2)     — agreement with own historical patterns
    S (Self-Reflection)= bounded distance from optimal question ratio (0.25)
    W (World-Model)    = bounded distance from optimal code ratio (0.30)
    """
    P = (features['F1'] + features['F3'] + features['F5']) / 3
    I = max(0.0, 1.0 - (features['F6'] * 0.8))
    C = (features['F4'] + features['F2']) / 2

    optimal_question_ratio = 0.25
    S = 1.0 - abs(features['F6'] - optimal_question_ratio) * 2
    S = max(0.0, min(1.0, S))

    optimal_code_ratio = 0.3
    W = 1.0 - abs(features['F7'] - optimal_code_ratio) * 2
    W = max(0.0, min(1.0, W))

    return {
        'perceptual': round(P, 4),
        'inferential': round(I, 4),
        'consensus': round(C, 4),
        'self-reflection': round(S, 4),
        'world-model': round(W, 4)
    }


def compute_threshold(planes: Dict[str, float], history: List[float] = None) -> float:
    """
    Dynamic threshold: Theta(t) = 0.55 + 0.37 * V(t)
    where V(t) is volatility (stdev) of current plane scores,
    blended with 7-day historical volatility if available.
    """
    base = 0.55
    plane_values = list(planes.values())
    if len(plane_values) > 1:
        volatility = statistics.stdev(plane_values)
    else:
        volatility = 0.1

    volatility = min(1.0, max(0.0, volatility))

    if history and len(history) > 2:
        hist_vol = statistics.stdev(history[-7:]) if len(history) >= 7 else statistics.stdev(history)
        volatility = (volatility + hist_vol) / 2

    theta = base + 0.37 * volatility
    return round(min(1.0, theta), 4)


def match_archetype(psi: float, planes: Dict[str, float]) -> str:
    """Map Psi score to one of 8 cognitive archetypes."""
    if psi >= 0.85:
        return 'Hero'
    elif psi >= 0.75:
        return 'Sage'
    elif psi >= 0.65:
        return 'Creator'
    elif psi >= 0.55:
        return 'Innocent'
    elif psi >= 0.45:
        return 'Jester'
    elif psi >= 0.35:
        return 'Rebel'
    elif psi >= 0.25:
        return 'Shadow'
    else:
        return 'Caregiver'


def build_silence_signal(psi: float, theta: float, planes: Dict[str, float],
                         limiting_plane: str, archetype: str) -> Dict[str, Any]:
    """
    Build a typed, information-rich Structured Silence signal.
    Silence is not empty — it is a typed anomaly with actionable recommendations.
    """
    deficit = theta - psi

    silence_types = {
        'perceptual': 'COGNITIVE_OVERLOAD',
        'inferential': 'REASONING_COLLAPSE',
        'consensus': 'IDENTITY_DRIFT',
        'self-reflection': 'META_COGNITIVE_FATIGUE',
        'world-model': 'ENVIRONMENTAL_MISMATCH'
    }

    recommendations = {
        'perceptual': 'Your perceptual entropy is too high. You are scattered. Take a 15-minute break. Return to one task.',
        'inferential': 'Your reasoning chains are contradicting. Stop arguing with yourself. Take 20 minutes. Revisit your last coherent thought.',
        'consensus': 'You are drifting from your usual patterns. This is disorientation, not growth. Do something familiar.',
        'self-reflection': 'You are either over-thinking or not reflecting enough. Set a 10-minute timer. Write one clear sentence about what you want.',
        'world-model': 'Your environment does not match your mental model. Step back. Verify assumptions before proceeding.'
    }

    return {
        'silence_type': silence_types.get(limiting_plane, 'COGNITIVE_SUBTHRESHOLD'),
        'limiting_plane': limiting_plane,
        'coherence_deficit': round(deficit, 4),
        'archetype': archetype,
        'recommendation': recommendations.get(limiting_plane, 'Rest. The silence is information.'),
        'plane_scores': planes,
        'timestamp': None
    }


def compute_coherence(messages: List[Dict[str, Any]],
                      history: List[float] = None) -> Dict[str, Any]:
    """
    Main coherence computation entry point.

    Returns:
        psi: float          Coherence score [0,1]
        theta: float        Dynamic threshold [0.55, 0.92]
        gate_open: bool     Psi >= Theta
        limiting_plane: str Lowest-scoring plane
        archetype: str      Cognitive archetype label
        planes: dict        5-plane scores
        features: dict      9 entropy features
        structured_silence: dict (only when gate is closed)
    """
    features = extract_features(messages)
    planes = compute_planes(features)

    # Weighted coherence: Psi(t) = 0.25*P + 0.30*I + 0.20*C + 0.15*S + 0.10*W
    psi = (
        0.25 * planes['perceptual'] +
        0.30 * planes['inferential'] +
        0.20 * planes['consensus'] +
        0.15 * planes['self-reflection'] +
        0.10 * planes['world-model']
    )
    psi = round(max(0.0, min(1.0, psi)), 4)

    theta = compute_threshold(planes, history)
    limiting_plane = min(planes, key=planes.get)
    archetype = match_archetype(psi, planes)
    gate_open = psi >= theta

    result = {
        'psi': psi,
        'theta': theta,
        'gate_open': gate_open,
        'limiting_plane': limiting_plane,
        'archetype': archetype,
        'planes': planes,
        'features': features
    }

    if not gate_open:
        result['structured_silence'] = build_silence_signal(
            psi, theta, planes, limiting_plane, archetype
        )
        result['structured_silence']['timestamp'] = None

    return result


def handle_describe() -> Dict[str, Any]:
    return {
        'name': 'coherence-engine',
        'version': '1.0.0',
        'description': '5-plane cognitive coherence engine using Shannon entropy and behavioral oracle mathematics',
        'tools': [
            {
                'name': 'evaluate',
                'description': 'Compute 5-plane cognitive coherence from conversation messages',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'messages': {
                            'type': 'array',
                            'description': 'Array of message objects with content, timestamp, topic, role',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'content': {'type': 'string'},
                                    'timestamp': {'type': 'number'},
                                    'topic': {'type': 'string'},
                                    'role': {'type': 'string'}
                                }
                            }
                        }
                    },
                    'required': ['messages']
                }
            },
            {
                'name': 'health',
                'description': 'Health check for the coherence engine',
                'parameters': {'type': 'object', 'properties': {}}
            }
        ]
    }


def handle_call(req: Dict[str, Any]) -> Dict[str, Any]:
    params = req.get('params', {})
    tool_name = params.get('name', '')
    args = params.get('arguments', {})

    if tool_name == 'evaluate':
        messages = args.get('messages', [])
        if not messages:
            return {
                'output': {
                    'psi': 0.5,
                    'theta': 0.55,
                    'gate_open': False,
                    'limiting_plane': 'perceptual',
                    'archetype': 'Innocent',
                    'planes': {
                        'perceptual': 0.5, 'inferential': 0.5,
                        'consensus': 0.5, 'self-reflection': 0.5, 'world-model': 0.5
                    },
                    'features': {f'F{i}': 0.5 for i in range(1, 10)},
                    'note': 'No messages provided — returning neutral state'
                }
            }

        result = compute_coherence(messages)
        return {'output': result}

    elif tool_name == 'health':
        return {
            'output': {
                'status': 'healthy',
                'version': '1.0.0',
                'formulas': {
                    'shannon_entropy': 'H = -sum(p * log2(p)) / log2(n)',
                    'coherence': 'Psi = 0.25*P + 0.30*I + 0.20*C + 0.15*S + 0.10*W',
                    'threshold': 'Theta = 0.55 + 0.37*V(t)',
                    'gate': 'OPEN if Psi >= Theta, SILENCE if Psi < Theta'
                }
            }
        }

    else:
        return {
            'error': {
                'code': 'unknown_tool',
                'message': f'Unknown tool: {tool_name}. Available: evaluate, health'
            }
        }


def handle(req: Dict[str, Any]) -> Dict[str, Any]:
    method = req.get('method', '')

    if method == 'describe':
        return handle_describe()
    elif method == 'call':
        return handle_call(req)
    else:
        return {
            'error': {
                'code': 'unknown_method',
                'message': f'Unknown method: {method}. Available: describe, call'
            }
        }


def main():
    """stdio JSON-RPC loop — reads one JSON object per line, writes one response per line."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
            result = handle(req)

            response = {
                'jsonrpc': '2.0',
                'id': req.get('id'),
                'result': result
            }

            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            sys.stdout.write(json.dumps({
                'jsonrpc': '2.0',
                'id': None,
                'error': {'code': 'parse_error', 'message': str(e)}
            }) + '\n')
            sys.stdout.flush()
        except Exception as e:
            req_id = req.get('id') if 'req' in dir() else None
            sys.stdout.write(json.dumps({
                'jsonrpc': '2.0',
                'id': req_id,
                'error': {'code': 'internal_error', 'message': str(e)}
            }) + '\n')
            sys.stdout.flush()


if __name__ == '__main__':
    main()
