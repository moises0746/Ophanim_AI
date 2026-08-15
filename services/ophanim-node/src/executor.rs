//! Governed local capability executor with strict allowlist and cryptographic receipts.

use hex;
use serde_json::json;
use sha2::{Digest, Sha256};
use std::time::Instant;
use thiserror::Error;

use crate::protocol::{ExecutionReportPayload, LeaseOfferPayload};

#[derive(Debug, Error)]
pub enum ExecutionError {
    #[error("Tool '{0}' is not in the approved endpoint allowlist (fail-closed)")]
    UnauthorizedTool(String),
    #[error("Execution timed out or cancelled")]
    Cancelled,
    #[error("Invalid parameters: {0}")]
    InvalidParameters(String),
}

pub struct GovernedExecutor;

impl GovernedExecutor {
    pub const ALLOWED_TOOLS: &'static [&'static str] = &[
        "diagnostics.ping",
        "diagnostics.os_info",
        "diagnostics.health_check",
    ];

    pub async fn execute(offer: &LeaseOfferPayload) -> Result<ExecutionReportPayload, ExecutionError> {
        let start = Instant::now();

        // 1. Strict allowlist verification
        if !Self::ALLOWED_TOOLS.contains(&offer.tool_name.as_str()) {
            return Err(ExecutionError::UnauthorizedTool(offer.tool_name.clone()));
        }

        // 2. Execute bounded diagnostic slice
        let output = match offer.tool_name.as_str() {
            "diagnostics.ping" => {
                let echo = offer.parameters.get("echo").and_then(|v| v.as_str()).unwrap_or("pong");
                json!({
                    "response": echo,
                    "status": "healthy",
                    "timestamp": chrono::Utc::now().to_rfc3339()
                })
            }
            "diagnostics.os_info" => {
                json!({
                    "os": std::env::consts::OS,
                    "arch": std::env::consts::ARCH,
                    "family": std::env::consts::FAMILY,
                })
            }
            "diagnostics.health_check" => {
                json!({
                    "node_status": "operational",
                    "governance_engine": "active",
                    "fail_closed_mode": true,
                })
            }
            _ => return Err(ExecutionError::UnauthorizedTool(offer.tool_name.clone())),
        };

        // 3. Compute cryptographic evidence receipt
        let serialized_output = serde_json::to_string(&output).unwrap_or_default();
        let mut hasher = Sha256::new();
        hasher.update(serialized_output.as_bytes());
        let evidence_hash = hex::encode(hasher.finalize());

        let duration_ms = start.elapsed().as_secs_f64() * 1000.0;

        Ok(ExecutionReportPayload {
            lease_id: offer.lease_id.clone(),
            task_id: offer.task_id.clone(),
            status: "completed".to_string(),
            output_payload: output,
            evidence_hashes: vec![evidence_hash],
            error: None,
            execution_duration_ms: duration_ms,
        })
    }
}
