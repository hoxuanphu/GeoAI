#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Deliberately fail closed. No owner lock, process spawn or lifecycle code.
#[tauri::command]
fn bootstrap_session() -> Result<(), String> {
    Err("native_launcher_unavailable".into())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![bootstrap_session])
        .run(tauri::generate_context!())
        .expect("Desktop initialization failed");
}
