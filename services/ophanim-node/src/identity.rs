//! Device Node identity and configuration management.

use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct NodeConfig {
    pub device_id: String,
    pub device_name: String,
    pub workspace_id: String,
    pub hub_url: String,
    pub token: Option<String>,
    pub public_key_fingerprint: String,
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            device_id: Uuid::new_v4().to_string(),
            device_name: "Ophanim Device Node".to_string(),
            workspace_id: "default-workspace".to_string(),
            hub_url: "ws://localhost:8000/api/v1/node/stream".to_string(),
            token: None,
            public_key_fingerprint: "sha256:ophanim-node-default-fp".to_string(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct NodeIdentityStore {
    config: Arc<RwLock<NodeConfig>>,
}

impl NodeIdentityStore {
    pub fn new(config: NodeConfig) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
        }
    }

    pub async fn get_config(&self) -> NodeConfig {
        self.config.read().await.clone()
    }

    pub async fn set_token(&self, token: String) {
        let mut w = self.config.write().await;
        w.token = Some(token);
    }
}
