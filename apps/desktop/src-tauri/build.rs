fn main() {
    for input in ["GEOAI_DEV_SUPERVISOR", "GEOAI_DEV_PYTHON", "GEOAI_DEV_BACKEND"] {
        println!("cargo:rerun-if-env-changed={input}");
    }
    tauri_build::build()
}
