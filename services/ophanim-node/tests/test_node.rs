use ophanim_node::protocol::{LeaseOfferPayload, PROTOCOL_VERSION};
use ophanim_node::{
    ExecutionError, GovernedExecutor, HubNodeMessage, MetricsCollector, NodeConfig,
    NodeIdentityStore, ProtocolHeader, ProtocolMessageType,
};
use serde_json::json;

#[tokio::test]
async fn test_protocol_message_serialization() {
    let header = ProtocolHeader::new(
        ProtocolMessageType::Heartbeat,
        "test-device-uuid".to_string(),
        42,
    );
    let payload = json!({
        "status": "active",
        "tools": ["diagnostics.ping"]
    });
    let msg = HubNodeMessage::new(header, payload);

    let json_str = msg.to_json().expect("failed to serialize");
    assert!(json_str.contains(PROTOCOL_VERSION));
    assert!(json_str.contains("node.heartbeat"));
    assert!(json_str.contains("test-device-uuid"));

    let decoded = HubNodeMessage::from_json(&json_str).expect("failed to deserialize");
    assert_eq!(decoded.header.device_id, "test-device-uuid");
    assert_eq!(decoded.header.sequence, 42);
}

#[tokio::test]
async fn test_governed_executor_allowed_tools() {
    let offer = LeaseOfferPayload {
        lease_id: "lease-01".to_string(),
        task_id: "task-01".to_string(),
        task_step_id: "step-01".to_string(),
        tool_name: "diagnostics.ping".to_string(),
        parameters: json!({"echo": "hello-ophanim"}),
        timeout_seconds: 10,
        risk_level: "low".to_string(),
    };

    let report = GovernedExecutor::execute(&offer)
        .await
        .expect("execution failed");
    assert_eq!(report.status, "completed");
    assert_eq!(report.output_payload["response"], "hello-ophanim");
    assert_eq!(report.evidence_hashes.len(), 1);
    assert_eq!(report.evidence_hashes[0].len(), 64); // SHA-256 hex length
}

#[tokio::test]
async fn test_governed_executor_denies_unauthorized_tools() {
    let malicious_offer = LeaseOfferPayload {
        lease_id: "lease-bad".to_string(),
        task_id: "task-bad".to_string(),
        task_step_id: "step-bad".to_string(),
        tool_name: "shell.exec".to_string(),
        parameters: json!({"cmd": "whoami"}),
        timeout_seconds: 5,
        risk_level: "critical".to_string(),
    };

    let err = GovernedExecutor::execute(&malicious_offer)
        .await
        .expect_err("should have rejected unauthorized tool");

    match err {
        ExecutionError::UnauthorizedTool(tool) => assert_eq!(tool, "shell.exec"),
        _ => panic!("unexpected error variant: {:?}", err),
    }
}

#[tokio::test]
async fn test_metrics_and_identity_store() {
    let metrics = MetricsCollector::collect();
    assert!(metrics.cpu_percent >= 0.0 && metrics.cpu_percent <= 100.0);
    assert!(metrics.memory_total_mb > 0.0);

    let config = NodeConfig::default();
    let store = NodeIdentityStore::new(config.clone());

    let initial = store.get_config().await;
    assert_eq!(initial.device_id, config.device_id);
    assert!(initial.token.is_none());

    store.set_token("oph_live_secret_token_123".to_string()).await;
    let updated = store.get_config().await;
    assert_eq!(
        updated.token.as_deref(),
        Some("oph_live_secret_token_123")
    );
}
