pub mod runtime;

/// Filtered internal failure codes. Never attach paths or secret-bearing data.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NativeError {
    LinuxRuntimeUnavailable,
}

impl std::fmt::Display for NativeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(match self {
            Self::LinuxRuntimeUnavailable => "linux_runtime_unavailable",
        })
    }
}

impl std::error::Error for NativeError {}
