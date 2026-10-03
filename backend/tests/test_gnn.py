import pytest
from app.ml.labels import (
    BOTTLENECK_CLASSES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    CLASS_METADATA,
    SEQ_SCAN_BOTTLENECK,
    NESTED_LOOP_BOTTLENECK,
    EXPENSIVE_SORT,
    GOOD_OR_OPTIMIZED_PLAN,
)
from app.ml.feature_encoder import (
    encode_node_features,
    extract_node_features_from_plan_dict,
    NODE_FEATURE_DIM,
    OPERATOR_VOCAB,
)
from app.ml.graph_builder import build_plan_graph
from app.ml.dataset_generator import PlanDatasetGenerator
from app.ml.model_registry import ModelRegistry
from app.ml.inference import GNNInferenceService


SAMPLE_SANITIZED_PLAN_SEQ_SCAN = {
    "Plan": {
        "Node Type": "Seq Scan",
        "Relation Name": "TBL_REL_A1B2",
        "Total Cost": 45000.0,
        "Startup Cost": 0.0,
        "Plan Rows": 1000000,
        "Plan Width": 32,
        "Filter": "(COL_TX_DATE_9F8E > '2026-01-01')",
        "Plans": [],
    }
}

SAMPLE_SANITIZED_PLAN_NESTED_LOOP = {
    "Plan": {
        "Node Type": "Nested Loop",
        "Total Cost": 85000.0,
        "Startup Cost": 0.0,
        "Plan Rows": 500000,
        "Plan Width": 64,
        "Plans": [
            {
                "Node Type": "Seq Scan",
                "Relation Name": "TBL_OUTER_1122",
                "Total Cost": 2000.0,
                "Startup Cost": 0.0,
                "Plan Rows": 1000,
                "Plan Width": 32,
            },
            {
                "Node Type": "Seq Scan",
                "Relation Name": "TBL_INNER_3344",
                "Total Cost": 80.0,
                "Startup Cost": 0.0,
                "Plan Rows": 500,
                "Plan Width": 32,
            },
        ],
    }
}


def test_canonical_labels():
    """Verify all 7 canonical classes and bidirectional mappings."""
    assert len(BOTTLENECK_CLASSES) == 7
    assert len(CLASS_TO_ID) == 7
    assert len(ID_TO_CLASS) == 7

    for idx, name in enumerate(BOTTLENECK_CLASSES):
        assert CLASS_TO_ID[name] == idx
        assert ID_TO_CLASS[idx] == name
        assert name in CLASS_METADATA
        assert "description" in CLASS_METADATA[name]


def test_feature_encoder_dimensions_and_ranges():
    """Verify node feature vector is exactly 24-dimensional and bounded."""
    node = {
        "Node Type": "Seq Scan",
        "Total Cost": 1500.0,
        "Startup Cost": 0.0,
        "Plan Rows": 50000,
        "Plan Width": 32,
    }
    feats_direct = encode_node_features(
        operator_type="Seq Scan",
        total_cost=1500.0,
        plan_rows=50000.0,
        startup_cost=0.0,
        depth=1,
        child_count=0,
    )
    assert len(feats_direct) == NODE_FEATURE_DIM
    assert len(feats_direct) == 24

    feats_extracted = extract_node_features_from_plan_dict(node, depth=1)
    assert len(feats_extracted) == NODE_FEATURE_DIM
    assert len(feats_extracted) == 24
    feats = feats_direct
    # All features should be numerical and bounded
    for f in feats:
        assert isinstance(f, float)
        assert not (f != f)  # NaN check
        assert f >= 0.0  # normalized features are non-negative


def test_graph_builder_structure():
    """Verify plan tree conversion to graph nodes and bidirectional edges."""
    features, edges, node_ops, summary = build_plan_graph(SAMPLE_SANITIZED_PLAN_NESTED_LOOP)
    
    assert len(features) == 3  # Nested Loop + 2 child Seq Scans
    assert len(features[0]) == NODE_FEATURE_DIM
    assert len(node_ops) == 3
    assert node_ops[0] == "Nested Loop"
    assert node_ops[1] == "Seq Scan"
    assert node_ops[2] == "Seq Scan"
    
    # 2 edges in a tree -> 4 directed edges for bidirectional message passing
    assert len(edges) == 2  # [sources, targets]
    assert len(edges[0]) == 4
    assert len(edges[1]) == 4
    for u in edges[0]:
        assert 0 <= u < 3
    for v in edges[1]:
        assert 0 <= v < 3

    assert summary.plan_depth == 1
    assert summary.nested_loop_count == 1
    assert summary.sequential_scan_count == 2



def test_dataset_generator_privacy_scanner():
    """Verify privacy scanner detects and rejects raw customer strings."""
    generator = PlanDatasetGenerator()

    # Valid sanitized record
    clean_record = {
        "query_fingerprint": "FP_ABCD1234",
        "masked_query": "SELECT COL_A, COL_B FROM TBL_USERS_9999 WHERE COL_ID = :INT",
        "target_relation_token": "TBL_USERS_9999",
        "plan_graph": SAMPLE_SANITIZED_PLAN_SEQ_SCAN,
        "bottleneck_label": SEQ_SCAN_BOTTLENECK,
        "privacy_status": "HMAC_TOKENIZED_VERIFIED",
    }
    assert generator.verify_record_privacy(clean_record) is True

    # Leaked raw table name
    dirty_table_record = {
        "query_fingerprint": "FP_ABCD1234",
        "masked_query": "SELECT COL_A FROM transactions WHERE COL_ID = :INT",
        "target_relation_token": "transactions",
        "plan_graph": SAMPLE_SANITIZED_PLAN_SEQ_SCAN,
        "bottleneck_label": SEQ_SCAN_BOTTLENECK,
    }
    assert generator.verify_record_privacy(dirty_table_record) is False

    # Leaked literal customer name
    dirty_literal_record = {
        "query_fingerprint": "FP_ABCD1234",
        "masked_query": "SELECT * FROM TBL_CUST WHERE name = 'John Doe'",
        "target_relation_token": "TBL_CUST",
        "plan_graph": SAMPLE_SANITIZED_PLAN_SEQ_SCAN,
        "bottleneck_label": SEQ_SCAN_BOTTLENECK,
    }
    assert generator.verify_record_privacy(dirty_literal_record) is False


def test_model_registry_status():
    """Verify ModelRegistry status method exposes expected fields and truthfulness disclaimer."""
    registry = ModelRegistry()
    status = registry.get_status()
    status_dict = status.model_dump()

    assert "model_available" in status_dict
    assert "model_version" in status_dict
    assert status.model_version == "gnn_bottleneck_v1"
    assert "dataset_version" in status_dict
    assert "confidence_threshold" in status_dict
    assert status.confidence_threshold == 0.65
    assert "disclaimer" in status_dict
    assert "experimental" in status.disclaimer.lower()
    assert "synthetic" in status.disclaimer.lower()


def test_gnn_inference_with_model():
    """Verify GNN inference executes safely and produces top-3 predictions."""
    service = GNNInferenceService()
    result = service.predict_plan(
        plan_data=SAMPLE_SANITIZED_PLAN_SEQ_SCAN,
        rule_engine_label="SEQUENTIAL_SCAN_ON_LARGE_TABLE",
    )

    assert result.model_version == "gnn_bottleneck_v1"
    assert len(result.top_3_predictions) <= 3
    assert result.confidence >= 0.0
    assert result.confidence <= 1.0
    assert hasattr(result, "disclaimer")
    assert "experimental" in result.disclaimer.lower()

    if result.model_available:
        assert result.predicted_label is not None
        # Confidence threshold check
        if result.confidence < 0.65:
            assert result.is_low_confidence is True
        else:
            assert result.is_low_confidence is False


def test_rule_disagreement_detection():
    """Verify rule disagreement flag is set when GNN prediction differs from rule engine."""
    service = GNNInferenceService()
    # Pass an obviously different rule engine diagnosis like EXPENSIVE_SORT on a Seq Scan plan
    result = service.predict_plan(
        plan_data=SAMPLE_SANITIZED_PLAN_SEQ_SCAN,
        rule_engine_label="EXPENSIVE_EXTERNAL_SORT",
    )

    if result.model_available and result.predicted_label == SEQ_SCAN_BOTTLENECK:
        assert result.rule_disagreement is True
    assert "authoritative" in result.disclaimer.lower()
