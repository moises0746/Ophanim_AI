//! Ophanim Governed Device Node Daemon entrypoint.

use ophanim_node::{
    GovernedExecutor, HubNodeMessage, MetricsCollector, NodeConfig, NodeIdentityStore,
    ProtocolHeader, ProtocolMessageType,
};
use serde_json::json;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting Ophanim Governed Device Node daemon...");
    let config = NodeConfig::default();
    let _store = NodeIdentityStore::new(config.clone());

    println!("Node initialized with device ID: {}", config.device_id);
    println!("Supported tools: {:?}", GovernedExecutor::ALLOWED_TOOLS);

    // Demonstration of heartbeat construction
    let metrics = MetricsCollector::collect();
    let header = ProtocolHeader::new(ProtocolMessageType::Heartbeat, config.device_id.clone(), 1);
    let payload = json!({
        "status": "active",
        "metrics": metrics,
        "available_tools": GovernedExecutor::ALLOWED_TOOLS,
    });
    let heartbeat_msg = HubNodeMessage::new(header, payload);

    let serialized = heartbeat_msg.to_json()?;
    println!("Heartbeat envelope: {}", serialized);

    println!("Device Node daemon running. Press Ctrl+C to terminate.");
    tokio::time::sleep(Duration::from_millis(50)).await;

    Ok(())
}
