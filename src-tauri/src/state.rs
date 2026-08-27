use serde::{Deserialize, Serialize};
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppState {
    pub is_recording: bool,
    pub active_session_id: Option<String>,
    pub stealth_visible: bool,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            is_recording: false,
            active_session_id: None,
            stealth_visible: false,
        }
    }
}

pub struct ManagedState(pub Mutex<AppState>);
