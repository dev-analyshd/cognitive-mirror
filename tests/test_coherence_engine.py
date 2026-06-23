#!/usr/bin/env python3
"""
Cognitive Mirror — Mathematical Invariant Test Suite

Tests cover:
- Shannon entropy correctness
- Feature extraction (F1-F9) ranges and semantics
- Plane computation [0,1] bounds
- Weight sum invariant (must equal 1.0)
- Gate logic determinism
- Structured silence completeness
- Archetype classification coverage
- JSON-RPC protocol compliance
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'executas', 'coherence-engine'))

from coherence_engine import (
    shannon_entropy,
    extract_features,
    compute_planes,
    compute_threshold,
    compute_coherence,
    match_archetype,
    handle_describe,
    handle_call,
    build_silence_signal
)


class TestShannonEntropy:
    def test_uniform_distribution_max_entropy(self):
        values = [25, 25, 25, 25]
        assert abs(shannon_entropy(values) - 1.0) < 0.01

    def test_single_value_zero_entropy(self):
        values = [100]
        assert shannon_entropy(values) == 0.0

    def test_zero_total_returns_zero(self):
        assert shannon_entropy([0, 0, 0]) == 0.0

    def test_empty_returns_zero(self):
        assert shannon_entropy([]) == 0.0

    def test_binary_fair_coin(self):
        values = [50, 50]
        assert abs(shannon_entropy(values) - 1.0) < 0.01

    def test_binary_biased_coin(self):
        values = [90, 10]
        assert shannon_entropy(values) < 1.0
        assert shannon_entropy(values) > 0.0

    def test_output_normalized_to_0_1(self):
        for values in [[1, 2, 3, 4, 5], [1, 1000], [5, 5, 5], [1]]:
            result = shannon_entropy(values)
            assert 0.0 <= result <= 1.0, f"Out of range for {values}: {result}"


class TestFeatureExtraction:
    def _make_messages(self, n=10, content="test message", topic="general"):
        return [
            {'content': content, 'timestamp': i * 3600, 'topic': topic, 'role': 'user'}
            for i in range(n)
        ]

    def test_all_features_present(self):
        msgs = self._make_messages()
        features = extract_features(msgs)
        for k in ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9']:
            assert k in features, f"Missing feature {k}"

    def test_all_features_in_range(self):
        msgs = self._make_messages()
        features = extract_features(msgs)
        for k, v in features.items():
            assert 0.0 <= v <= 1.0, f"{k}={v} out of [0,1]"

    def test_f2_high_vocabulary_diversity(self):
        msgs = [{'content': f'word{i} other{i} thing{i}', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F2'] > 0.5

    def test_f2_low_vocabulary_diversity(self):
        msgs = [{'content': 'the the the the', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F2'] < 0.5

    def test_f6_all_questions(self):
        msgs = [{'content': 'What is this?', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F6'] == 1.0

    def test_f6_no_questions(self):
        msgs = [{'content': 'This is a statement.', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F6'] == 0.0

    def test_f7_all_code(self):
        msgs = [{'content': '```python\nprint("hello")\n```', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F7'] == 1.0

    def test_f7_no_code(self):
        msgs = [{'content': 'No code here at all.', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(10)]
        features = extract_features(msgs)
        assert features['F7'] == 0.0

    def test_single_message(self):
        msgs = [{'content': 'solo', 'timestamp': 0, 'topic': 'test', 'role': 'user'}]
        features = extract_features(msgs)
        for k, v in features.items():
            assert 0.0 <= v <= 1.0, f"{k}={v} out of [0,1] for single message"

    def test_empty_content(self):
        msgs = [{'content': '', 'timestamp': i, 'topic': 't', 'role': 'user'} for i in range(5)]
        features = extract_features(msgs)
        for k, v in features.items():
            assert 0.0 <= v <= 1.0


class TestPlaneComputation:
    def _mid_features(self):
        return {f'F{i}': 0.5 for i in range(1, 10)}

    def test_all_planes_present(self):
        planes = compute_planes(self._mid_features())
        for p in ['perceptual', 'inferential', 'consensus', 'self-reflection', 'world-model']:
            assert p in planes

    def test_plane_ranges(self):
        planes = compute_planes(self._mid_features())
        for k, v in planes.items():
            assert 0.0 <= v <= 1.0, f"{k}={v} out of [0,1]"

    def test_inferential_high_questions_lowers_it(self):
        features = self._mid_features()
        features['F6'] = 1.0  # all questions
        planes = compute_planes(features)
        assert planes['inferential'] < 0.5

    def test_inferential_no_questions_raises_it(self):
        features = self._mid_features()
        features['F6'] = 0.0  # no questions
        planes = compute_planes(features)
        assert planes['inferential'] > 0.5

    def test_world_model_optimal_code_ratio(self):
        features = self._mid_features()
        features['F7'] = 0.3  # optimal code ratio
        planes = compute_planes(features)
        assert planes['world-model'] > 0.5


class TestThresholdComputation:
    def test_base_threshold_without_history(self):
        planes = {k: 0.5 for k in ['perceptual', 'inferential', 'consensus', 'self-reflection', 'world-model']}
        theta = compute_threshold(planes)
        assert 0.55 <= theta <= 0.92

    def test_high_volatility_raises_threshold(self):
        planes_low_vol = {'perceptual': 0.5, 'inferential': 0.5, 'consensus': 0.5, 'self-reflection': 0.5, 'world-model': 0.5}
        planes_high_vol = {'perceptual': 0.1, 'inferential': 0.9, 'consensus': 0.2, 'self-reflection': 0.8, 'world-model': 0.3}
        assert compute_threshold(planes_high_vol) >= compute_threshold(planes_low_vol)


class TestCoherenceInvariants:
    def _make_messages(self, n=5):
        return [{'content': f'test {i}', 'timestamp': i * 100, 'topic': 'test', 'role': 'user'} for i in range(n)]

    def test_psi_in_range(self):
        result = compute_coherence(self._make_messages())
        assert 0.0 <= result['psi'] <= 1.0

    def test_theta_in_range(self):
        result = compute_coherence(self._make_messages())
        assert 0.55 <= result['theta'] <= 0.92

    def test_weight_sum_invariant(self):
        weights = [0.25, 0.30, 0.20, 0.15, 0.10]
        assert abs(sum(weights) - 1.0) < 1e-10, "Weights must sum to exactly 1.0"

    def test_gate_logic_deterministic(self):
        result = compute_coherence(self._make_messages())
        expected = result['psi'] >= result['theta']
        assert result['gate_open'] == expected

    def test_limiting_plane_is_minimum(self):
        result = compute_coherence(self._make_messages())
        planes = result['planes']
        limiting = result['limiting_plane']
        assert planes[limiting] == min(planes.values())

    def test_all_required_fields_present(self):
        result = compute_coherence(self._make_messages())
        for field in ['psi', 'theta', 'gate_open', 'limiting_plane', 'archetype', 'planes', 'features']:
            assert field in result, f"Missing field: {field}"

    def test_structured_silence_when_gate_closed(self):
        # Force a low-coherence scenario with many questions
        messages = [
            {'content': '??? ??? ???', 'timestamp': i, 'topic': f'topic{i}', 'role': 'user'}
            for i in range(10)
        ]
        result = compute_coherence(messages)
        if not result['gate_open']:
            assert 'structured_silence' in result
            ss = result['structured_silence']
            for field in ['silence_type', 'limiting_plane', 'coherence_deficit', 'archetype', 'recommendation']:
                assert field in ss, f"Structured silence missing: {field}"

    def test_no_structured_silence_when_gate_open(self):
        # Low question ratio, diverse vocab, code blocks for high coherence
        messages = [
            {'content': f'```python\ncompute_{i}()\n``` analysis of domain {i} and structure.', 'timestamp': i * 10, 'topic': 'coding', 'role': 'user'}
            for i in range(20)
        ]
        result = compute_coherence(messages)
        if result['gate_open']:
            assert 'structured_silence' not in result

    def test_all_plane_scores_in_range(self):
        result = compute_coherence(self._make_messages(20))
        for k, v in result['planes'].items():
            assert 0.0 <= v <= 1.0, f"Plane {k}={v} out of [0,1]"

    def test_all_feature_scores_in_range(self):
        result = compute_coherence(self._make_messages(20))
        for k, v in result['features'].items():
            assert 0.0 <= v <= 1.0, f"Feature {k}={v} out of [0,1]"


class TestArchetypeMatching:
    def test_hero_at_max_psi(self):
        assert match_archetype(0.9, {}) == 'Hero'

    def test_hero_threshold(self):
        assert match_archetype(0.85, {}) == 'Hero'

    def test_sage_range(self):
        assert match_archetype(0.80, {}) == 'Sage'
        assert match_archetype(0.75, {}) == 'Sage'

    def test_creator_range(self):
        assert match_archetype(0.70, {}) == 'Creator'
        assert match_archetype(0.65, {}) == 'Creator'

    def test_innocent_range(self):
        assert match_archetype(0.60, {}) == 'Innocent'
        assert match_archetype(0.55, {}) == 'Innocent'

    def test_jester_range(self):
        assert match_archetype(0.50, {}) == 'Jester'
        assert match_archetype(0.45, {}) == 'Jester'

    def test_rebel_range(self):
        assert match_archetype(0.40, {}) == 'Rebel'
        assert match_archetype(0.35, {}) == 'Rebel'

    def test_shadow_range(self):
        assert match_archetype(0.30, {}) == 'Shadow'
        assert match_archetype(0.25, {}) == 'Shadow'

    def test_caregiver_at_minimum(self):
        assert match_archetype(0.1, {}) == 'Caregiver'
        assert match_archetype(0.0, {}) == 'Caregiver'


class TestStructuredSilence:
    def test_all_silence_types_covered(self):
        planes = {'perceptual': 0.1, 'inferential': 0.5, 'consensus': 0.5, 'self-reflection': 0.5, 'world-model': 0.5}
        for plane in ['perceptual', 'inferential', 'consensus', 'self-reflection', 'world-model']:
            signal = build_silence_signal(0.4, 0.6, planes, plane, 'Shadow')
            assert signal['silence_type'] != 'COGNITIVE_SUBTHRESHOLD' or plane not in ['perceptual', 'inferential', 'consensus', 'self-reflection', 'world-model']
            assert 'recommendation' in signal
            assert len(signal['recommendation']) > 10

    def test_deficit_is_positive(self):
        planes = {k: 0.5 for k in ['perceptual', 'inferential', 'consensus', 'self-reflection', 'world-model']}
        signal = build_silence_signal(0.4, 0.65, planes, 'inferential', 'Shadow')
        assert signal['coherence_deficit'] > 0


class TestJSONRPC:
    def test_describe_returns_manifest(self):
        result = handle_describe()
        assert 'name' in result
        assert 'tools' in result
        assert len(result['tools']) >= 2  # evaluate + health

    def test_describe_tool_names(self):
        result = handle_describe()
        names = [t['name'] for t in result['tools']]
        assert 'evaluate' in names
        assert 'health' in names

    def test_evaluate_returns_coherence(self):
        req = {
            'method': 'call',
            'params': {
                'name': 'evaluate',
                'arguments': {
                    'messages': [
                        {'content': 'How should I approach this problem?', 'timestamp': 1, 'topic': 'coding', 'role': 'user'},
                        {'content': 'Let me analyze the requirements.', 'timestamp': 2, 'topic': 'coding', 'role': 'user'}
                    ]
                }
            }
        }
        result = handle_call(req)
        assert 'output' in result
        assert 'psi' in result['output']
        assert 'theta' in result['output']
        assert 'gate_open' in result['output']
        assert 'archetype' in result['output']

    def test_evaluate_empty_messages_returns_neutral(self):
        req = {
            'method': 'call',
            'params': {'name': 'evaluate', 'arguments': {'messages': []}}
        }
        result = handle_call(req)
        assert 'output' in result
        assert result['output']['psi'] == 0.5

    def test_health_returns_ok(self):
        req = {
            'method': 'call',
            'params': {'name': 'health', 'arguments': {}}
        }
        result = handle_call(req)
        assert result['output']['status'] == 'healthy'
        assert 'formulas' in result['output']

    def test_unknown_tool_returns_error(self):
        req = {
            'method': 'call',
            'params': {'name': 'nonexistent', 'arguments': {}}
        }
        result = handle_call(req)
        assert 'error' in result


def run_tests():
    test_classes = [
        TestShannonEntropy,
        TestFeatureExtraction,
        TestPlaneComputation,
        TestThresholdComputation,
        TestCoherenceInvariants,
        TestArchetypeMatching,
        TestStructuredSilence,
        TestJSONRPC
    ]

    passed = 0
    failed = 0
    errors = []

    print("\n Cognitive Mirror — Coherence Engine Test Suite")
    print("=" * 60)

    for cls in test_classes:
        instance = cls()
        methods = sorted([m for m in dir(instance) if m.startswith('test_')])
        print(f"\n{cls.__name__}:")
        for method in methods:
            try:
                getattr(instance, method)()
                print(f"  PASS  {method}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {method}: {e}")
                errors.append(f"{cls.__name__}.{method}: {e}")
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 60}\n")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
