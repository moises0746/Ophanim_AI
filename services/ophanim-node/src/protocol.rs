//! Hub-Node versioned protocol schemas and serialization contracts (v1.0.0).

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub const PROTOCOL_VERSION: &str = "1.0.0";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProtocolMessageType {
    #[serde(rename = "node.enrollment.request")]
    EnrollmentRequest,
    #[serde(rename = "node.enrollment.response")]
    EnrollmentResponse,
    #[serde(rename = "node.heartbeat")]
    Heartbeat,
    #[serde(rename = "node.heartbeat.ack")]
    HeartbeatAck,
    #[serde(rename = "hub.lease.offer")]
    LeaseOffer,
    #[serde(rename = "node.lease.accept")]
    LeaseAccept,
    #[serde(rename = "node.lease.reject")]
    LeaseReject,
    #[serde(rename = "node.execution.report")]
    ExecutionReport,
    #[serde(rename = "hub.task.cancel")]
    CancellationNotice,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub cpu_percent: f64,
    pub memory_used_mb: f64,
    pub memory_total_mb: f64,
    pub disk_available_gb: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProtocolHeader {
    pub protocol_version: String,
    pub message_id: String,
    pub message_type: ProtocolMessageType,
    pub timestamp_utc: DateTime<Utc>,
    pub device_id: String,
    pub sequence: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub correlation_id: Option<String>,
}

impl ProtocolHeader {
    pub fn new(message_type: ProtocolMessageType, device_id: String, sequence: u64) -> Self {
        Self {
            protocol_version: PROTOCOL_VERSION.to_string(),
            message_id: Uuid::new_v4().to_string(),
            message_type,
            timestamp_utc: Utc::now(),
            device_id,
            sequence,
            correlation_id: None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HubNodeMessage {
    pub header: ProtocolHeader,
    pub payload: serde_json::Value,
}

impl HubNodeMessage {
    pub fn new(header: ProtocolHeader, payload: serde_json::Value) -> Self {
        Self { header, payload }
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    pub fn from_json(raw: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(raw)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EnrollmentRequestPayload {
    pub device_name: String,
    pub device_type: String,
    pub public_key_fingerprint: String,
    pub supported_tools: Vec<String>,
    pub os_info: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HeartbeatPayload {
    pub status: String,
    pub metrics: SystemMetrics,
    pub available_tools: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HeartbeatAckPayload {
    pub acknowledged: bool,
    pub server_timestamp_utc: DateTime<Utc>,
    pub pending_leases: u32,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LeaseOfferPayload {
    pub lease_id: String,
    pub task_id: String,
    pub task_step_id: String,
    pub tool_name: String,
    pub parameters: serde_json::Value,
    pub timeout_seconds: u32,
    pub risk_level: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LeaseAcceptPayload {
    pub lease_id: String,
    pub task_id: String,
    pub accepted: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LeaseRejectPayload {
    pub lease_id: String,
    pub task_id: String,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionReportPayload {
    pub lease_id: String,
    pub task_id: String,
    pub status: String,
    pub output_payload: serde_json::Value,
    pub evidence_hashes: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    pub execution_duration_ms: f64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CancellationNoticePayload {
    pub lease_id: String,
    pub task_id: String,
    pub reason: String,
}
