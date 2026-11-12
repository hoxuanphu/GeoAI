#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use geoai_desktop::session::SessionDescriptor;
use std::sync::Mutex;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use url::Url;

#[cfg(windows)]
mod windows_native;


fn trusted_window_url(url: &Url) -> bool {
    let allowed = (url.scheme() == "tauri" && url.host_str() == Some("localhost") && url.port().is_none())
        || (url.scheme() == "http" && url.host_str() == Some("tauri.localhost") && url.port().is_none())
        || (cfg!(debug_assertions) && url.scheme() == "http" && url.host_str() == Some("127.0.0.1") && url.port() == Some(1420));
    allowed && matches!(url.path(), "/" | "/index.html") && url.query().is_none() && url.fragment().is_none()
}

#[cfg(windows)]
type ActiveSession = windows_native::NativeSession;
#[cfg(not(windows))]
struct ActiveSession;

#[derive(Default)]
struct SessionState(Mutex<Option<ActiveSession>>);

#[tauri::command]
fn bootstrap_session(window: tauri::WebviewWindow, state: tauri::State<'_, SessionState>) -> Result<SessionDescriptor, String> {
    if window.label() != "main" || !trusted_window_url(&window.url().map_err(|_| "untrusted_window")?) {
        return Err("untrusted_window".into());
    }
    let mut session = state.0.lock().map_err(|_| "session_state_unavailable")?;
    #[cfg(windows)]
    {
        if let Some(active) = session.as_mut() {
            if active.is_alive()? {
                return Ok(active.descriptor());
            }
            active.stop()?;
            *session = None;
        }
        let active = windows_native::NativeSession::launch(&window.app_handle())?;
        let descriptor = active.descriptor();
        *session = Some(active);
        Ok(descriptor)
    }
    #[cfg(not(windows))]
    {
        drop(session);
        Err("windows_required".into())
    }
}

fn main() {
    tauri::Builder::default()
        .manage(SessionState::default())
        .setup(|app| {
            WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()))
                .title("GeoAI")
                .inner_size(1024.0, 720.0)
                .on_navigation(|url| trusted_window_url(&url))
                .build()?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![bootstrap_session])
        .on_window_event(|window, event| {
            if window.label() == "main" && matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
                let state = window.state::<SessionState>();
                if let Ok(mut guard) = state.0.lock() {
                    if let Some(mut session) = guard.take() {
                        #[cfg(windows)]
                        if session.stop().is_err() {
                            *guard = Some(session);
                        }
                        #[cfg(not(windows))]
                        let _ = session;
                    }
                };
            }
        })
        .run(tauri::generate_context!())
        .expect("Desktop initialization failed");
}
