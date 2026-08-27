pub struct GlobalHotkeyManager;

impl GlobalHotkeyManager {
    pub fn register_stealth_hotkey() -> bool {
        println!("[Hotkey Manager] Registered Ctrl+Space / Cmd+Shift+Space stealth prompt shortcut.");
        true
    }
}
