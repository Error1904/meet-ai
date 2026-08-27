// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod audio;
mod hotkey;
mod state;

use state::{AppState, ManagedState};
use std::sync::Mutex;
use tauri::Manager;

#[tauri::command]
fn get_audio_devices() -> Vec<String> {
    audio::AudioEngine::list_host_devices()
}

#[tauri::command]
fn toggle_stealth_bar(app_handle: tauri::AppHandle) -> bool {
    if let Some(window) = app_handle.get_webview_window("stealth") {
        if window.is_visible().unwrap_or(false) {
            let _ = window.hide();
            false
        } else {
            let _ = window.show();
            let _ = window.set_focus();
            true
        }
    } else {
        false
    }
}

fn main() {
    hotkey::GlobalHotkeyManager::register_stealth_hotkey();

    tauri::Builder::default()
        .manage(ManagedState(Mutex::new(AppState::default())))
        .invoke_handler(tauri::generate_handler![
            get_audio_devices,
            toggle_stealth_bar
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
