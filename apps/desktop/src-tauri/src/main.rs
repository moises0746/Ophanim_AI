// Prevents additional console window on Windows in release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    env,
    net::IpAddr,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::Duration,
};

use futures_util::StreamExt;
use reqwest::{Client, Url};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{State, Window};

const EVENT_NAME: &str = "ophanim://assistant-event";
const ERROR_EVENT_NAME: &str = "ophanim://runtime-error";

#[derive(Clone)]
struct RuntimeConfig {
    core_base_url: String,
    workspace_id: String,
    api_token: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PublicRuntimeConfig {
    configured: bool,
    core_base_url: String,
    workspace_id: String,
}

struct RuntimeState {
    config: Result<RuntimeConfig, String>,
    client: Client,
    stream_started: Arc<AtomicBool>,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct ChatRequest {
    messages: Vec<ChatMessage>,
    privacy_mode: String,
    provider: Option<String>,
    model_id: Option<String>,
    max_tokens: Option<u32>,
}

#[derive(Serialize)]
struct CoreChatRequest<'a> {
    workspace_id: &'a str,
    messages: &'a [ChatMessage],
    privacy_mode: &'a str,
    provider: &'a Option<String>,
    model_id: &'a Option<String>,
    max_tokens: Option<u32>,
}

fn is_loopback_url(value: &str) -> bool {
    let Ok(url) = Url::parse(value) else {
        return false;
    };
    if !matches!(url.scheme(), "http" | "https") {
        return false;
    }
    match url.host_str() {
        Some(host) if host.eq_ignore_ascii_case("localhost") => true,
        Some(host) => host
            .trim_matches(&['[', ']'][..])
            .parse::<IpAddr>()
            .map(|address| address.is_loopback())
            .unwrap_or(false),
        None => false,
    }
}

fn load_runtime_config() -> Result<RuntimeConfig, String> {
    let core_base_url =
        env::var("OPHANIM_CORE_BASE_URL").unwrap_or_else(|_| "http://127.0.0.1:8080".into());
    if !is_loopback_url(&core_base_url) {
        return Err("Core base URL must use a loopback host".into());
    }
    let workspace_id = env::var("OPHANIM_RUNTIME_WORKSPACE_ID")
        .map_err(|_| "Runtime workspace is not configured".to_string())?;
    let api_token = env::var("OPHANIM_DESKTOP_API_TOKEN")
        .map_err(|_| "Desktop runtime credential is not configured".to_string())?;
    if workspace_id.trim().is_empty() || api_token.trim().is_empty() {
        return Err("Desktop runtime configuration is incomplete".into());
    }
    Ok(RuntimeConfig {
        core_base_url: core_base_url.trim_end_matches('/').to_string(),
        workspace_id,
        api_token,
    })
}

impl RuntimeState {
    fn configured(&self) -> Result<&RuntimeConfig, String> {
        self.config.as_ref().map_err(Clone::clone)
    }
}

#[tauri::command]
fn runtime_config(state: State<'_, RuntimeState>) -> PublicRuntimeConfig {
    match state.configured() {
        Ok(config) => PublicRuntimeConfig {
            configured: true,
            core_base_url: config.core_base_url.clone(),
            workspace_id: config.workspace_id.clone(),
        },
        Err(_) => PublicRuntimeConfig {
            configured: false,
            core_base_url: String::new(),
            workspace_id: String::new(),
        },
    }
}

async fn checked_json(response: reqwest::Response) -> Result<Value, String> {
    if !response.status().is_success() {
        return Err(format!(
            "Ophanim Core request failed with HTTP {}",
            response.status().as_u16()
        ));
    }
    response
        .json::<Value>()
        .await
        .map_err(|_| "Ophanim Core returned an invalid response".to_string())
}

#[tauri::command]
async fn assistant_models(state: State<'_, RuntimeState>) -> Result<Value, String> {
    let config = state.configured()?.clone();
    let response = state
        .client
        .get(format!(
            "{}/api/v1/assistant/models?workspace_id={}",
            config.core_base_url, config.workspace_id
        ))
        .bearer_auth(&config.api_token)
        .send()
        .await
        .map_err(|_| "Ophanim Core is unavailable".to_string())?;
    checked_json(response).await
}

#[tauri::command]
async fn assistant_chat(
    request: ChatRequest,
    state: State<'_, RuntimeState>,
) -> Result<Value, String> {
    if request.messages.is_empty() || request.messages.len() > 40 {
        return Err("Chat history must contain between 1 and 40 messages".into());
    }
    if request
        .messages
        .iter()
        .any(|message| message.content.trim().is_empty() || message.content.len() > 100_000)
    {
        return Err("Chat message content is invalid".into());
    }
    let config = state.configured()?.clone();
    let body = CoreChatRequest {
        workspace_id: &config.workspace_id,
        messages: &request.messages,
        privacy_mode: &request.privacy_mode,
        provider: &request.provider,
        model_id: &request.model_id,
        max_tokens: request.max_tokens,
    };
    let response = state
        .client
        .post(format!("{}/api/v1/assistant/chat", config.core_base_url))
        .bearer_auth(&config.api_token)
        .json(&body)
        .send()
        .await
        .map_err(|_| "Ophanim Core is unavailable".to_string())?;
    checked_json(response).await
}

#[tauri::command]
async fn start_assistant_events(
    window: Window,
    state: State<'_, RuntimeState>,
) -> Result<(), String> {
    let config = state.configured()?.clone();
    if state.stream_started.swap(true, Ordering::SeqCst) {
        return Ok(());
    }
    let client = state.client.clone();
    let active = state.stream_started.clone();
    tauri::async_runtime::spawn(async move {
        let result: Result<(), String> = async {
            let response = client
                .get(format!(
                    "{}/api/v1/assistant/events/stream?workspace_id={}",
                    config.core_base_url, config.workspace_id
                ))
                .bearer_auth(&config.api_token)
                .header("Accept", "text/event-stream")
                .send()
                .await
                .map_err(|_| "Assistant event stream is unavailable".to_string())?;
            if !response.status().is_success() {
                return Err(format!(
                    "Assistant event stream failed with HTTP {}",
                    response.status().as_u16()
                ));
            }

            let mut stream = response.bytes_stream();
            let mut buffer = Vec::<u8>::new();
            while let Some(chunk) = stream.next().await {
                let chunk = chunk.map_err(|_| "Assistant event stream disconnected".to_string())?;
                buffer.extend_from_slice(&chunk);
                while let Some(index) = buffer.windows(2).position(|window| window == b"\n\n") {
                    let frame = buffer.drain(..index + 2).collect::<Vec<_>>();
                    let frame = String::from_utf8(frame)
                        .map_err(|_| "Assistant event stream returned invalid UTF-8".to_string())?;
                    window
                        .emit(EVENT_NAME, frame)
                        .map_err(|_| "Desktop event delivery failed".to_string())?;
                }
            }
            Err("Assistant event stream disconnected".to_string())
        }
        .await;
        active.store(false, Ordering::SeqCst);
        if let Err(message) = result {
            let _ = window.emit(ERROR_EVENT_NAME, message);
        }
    });
    Ok(())
}

fn main() {
    let client = Client::builder()
        .timeout(Duration::from_secs(45))
        .build()
        .expect("bounded HTTP client configuration must be valid");
    tauri::Builder::default()
        .manage(RuntimeState {
            config: load_runtime_config(),
            client,
            stream_started: Arc::new(AtomicBool::new(false)),
        })
        .invoke_handler(tauri::generate_handler![
            runtime_config,
            assistant_models,
            assistant_chat,
            start_assistant_events
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Ophanim Desktop");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn core_url_is_restricted_to_loopback() {
        assert!(is_loopback_url("http://127.0.0.1:8080"));
        assert!(is_loopback_url("http://localhost:8080"));
        assert!(is_loopback_url("http://[::1]:8080"));
        assert!(!is_loopback_url("https://example.com"));
        assert!(!is_loopback_url("file:///tmp/core"));
    }

    #[test]
    fn public_config_has_no_credential_field() {
        let value = serde_json::to_value(PublicRuntimeConfig {
            configured: true,
            core_base_url: "http://127.0.0.1:8080".into(),
            workspace_id: "00000000-0000-0000-0000-000000000001".into(),
        })
        .expect("serializes");
        assert!(value.get("apiToken").is_none());
        assert!(value.get("token").is_none());
    }
}
