use super::NativeError;
use nix::unistd::{access, geteuid, getuid, AccessFlags};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};

pub struct RuntimePaths {
    pub supervisor: PathBuf,
    pub python: PathBuf,
    pub backend: Option<PathBuf>,
}

/// Trusted native build/test configuration, never deserialized from webview input.
pub struct DevRuntimePaths {
    pub supervisor: PathBuf,
    pub python: PathBuf,
    pub backend: PathBuf,
}

impl DevRuntimePaths {
    /// Build-time configuration only. A partial debug configuration fails closed;
    /// release builds do not read or embed the development path inputs here.
    pub fn from_build_environment() -> Result<Option<Self>, NativeError> {
        #[cfg(debug_assertions)]
        {
            match (option_env!("GEOAI_DEV_SUPERVISOR"), option_env!("GEOAI_DEV_PYTHON"), option_env!("GEOAI_DEV_BACKEND")) {
                (None, None, None) => Ok(None),
                (Some(supervisor), Some(python), Some(backend)) => Ok(Some(Self {
                    supervisor: supervisor.into(), python: python.into(), backend: backend.into(),
                })),
                _ => Err(NativeError::LinuxRuntimeUnavailable),
            }
        }
        #[cfg(not(debug_assertions))]
        { Ok(None) }
    }
}

/// Resolve trusted native inputs. This checks current filesystem metadata, not
/// launch-byte identity: consumers must revalidate before launching, and trusted
/// installers must not replace an active runtime. Same-UID compromise is outside
/// this profile. Group/other-writable ancestors (even sticky /tmp) are rejected.
pub fn resolve_runtime(resource_root: &Path, dev: Option<DevRuntimePaths>) -> Result<RuntimePaths, NativeError> {
    if let Some(dev) = dev {
        #[cfg(not(debug_assertions))]
        {
            let _ = dev;
            return Err(NativeError::LinuxRuntimeUnavailable);
        }
        #[cfg(debug_assertions)]
        {
            return Ok(RuntimePaths {
                supervisor: trusted_path(&dev.supervisor, true)?,
                python: trusted_path(&dev.python, true)?,
                backend: Some(trusted_path(&dev.backend, false)?),
            });
        }
    }
    let root = trusted_path(resource_root, false)?;
    let supervisor = trusted_path(&root.join("geoai-runtime/bin/geoai-supervisor"), true)?;
    let python = trusted_path(&root.join("geoai-runtime/python/bin/python3.12"), true)?;
    if !supervisor.starts_with(&root) || !python.starts_with(&root) {
        return Err(NativeError::LinuxRuntimeUnavailable);
    }
    Ok(RuntimePaths { supervisor, python, backend: None })
}

fn trusted_path(path: &Path, executable: bool) -> Result<PathBuf, NativeError> {
    if !path.is_absolute() || geteuid() != getuid() {
        return Err(NativeError::LinuxRuntimeUnavailable);
    }
    // Check both spellings: resolving a link must not hide its writable parent,
    // or an untrusted ancestor of its target outside the original path.
    check_ancestors(path)?;
    let canonical = path.canonicalize().map_err(|_| NativeError::LinuxRuntimeUnavailable)?;
    check_ancestors(&canonical)?;
    let metadata = fs::metadata(&canonical).map_err(|_| NativeError::LinuxRuntimeUnavailable)?;
    if executable {
        if !metadata.is_file() || metadata.mode() & 0o6000 != 0
            || access(canonical.as_path(), AccessFlags::X_OK).is_err()
        {
            return Err(NativeError::LinuxRuntimeUnavailable);
        }
    } else if !metadata.is_dir() {
        return Err(NativeError::LinuxRuntimeUnavailable);
    }
    Ok(canonical)
}

fn check_ancestors(path: &Path) -> Result<(), NativeError> {
    let uid = geteuid().as_raw();
    for ancestor in path.ancestors() {
        let link = fs::symlink_metadata(ancestor).map_err(|_| NativeError::LinuxRuntimeUnavailable)?;
        let metadata = fs::metadata(ancestor).map_err(|_| NativeError::LinuxRuntimeUnavailable)?;
        if !trusted_owner(link.uid(), uid)
            || !trusted_owner(metadata.uid(), uid)
            || metadata.mode() & 0o022 != 0
            || (ancestor != path && !metadata.is_dir())
        {
            return Err(NativeError::LinuxRuntimeUnavailable);
        }
    }
    Ok(())
}

fn trusted_owner(owner_uid: u32, current_uid: u32) -> bool {
    owner_uid == 0 || owner_uid == current_uid
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::os::unix::fs::{DirBuilderExt, PermissionsExt};
    use std::path::{Path, PathBuf};
    use std::sync::atomic::{AtomicUsize, Ordering};

    static NEXT: AtomicUsize = AtomicUsize::new(0);

    struct Fixture(PathBuf);

    impl Fixture {
        fn new() -> Self {
            // Shared /tmp is intentionally outside the accepted trust profile.
            let base = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../work/b01-runtime-fixtures");
            fs::DirBuilder::new().recursive(true).mode(0o700).create(&base).unwrap();
            fs::set_permissions(&base, fs::Permissions::from_mode(0o700)).unwrap();
            let path = base.join(format!("{}-{}", std::process::id(), NEXT.fetch_add(1, Ordering::Relaxed)));
            fs::DirBuilder::new().mode(0o700).create(&path).unwrap();
            Self(path.canonicalize().unwrap())
        }

        fn executable(&self, relative: &str) -> PathBuf {
            let path = self.0.join(relative);
            fs::DirBuilder::new().recursive(true).mode(0o700).create(path.parent().unwrap()).unwrap();
            fs::write(&path, b"fixture, never executed").unwrap();
            fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).unwrap();
            path
        }

        fn packaged(&self) -> (PathBuf, PathBuf) {
            (self.executable("geoai-runtime/bin/geoai-supervisor"), self.executable("geoai-runtime/python/bin/python3.12"))
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) { fs::remove_dir_all(&self.0).unwrap(); }
    }

    #[test]
    fn runtime_resolves_fixed_packaged_layout() {
        let fixture = Fixture::new();
        let (supervisor, python) = fixture.packaged();
        let paths = resolve_runtime(&fixture.0, None).unwrap();
        assert_eq!(paths.supervisor, supervisor);
        assert_eq!(paths.python, python);
        assert!(paths.backend.is_none());
    }

    #[test]
    fn runtime_rejects_path_outside_resource_root() {
        for escaped in ["geoai-runtime/bin/geoai-supervisor", "geoai-runtime/python/bin/python3.12"] {
            let fixture = Fixture::new();
            fixture.packaged();
            // A lexical string prefix is not containment: this sibling shares it.
            let outside = fixture.0.with_extension("outside");
            fs::DirBuilder::new().mode(0o700).create(&outside).unwrap();
            let outside = Fixture(outside);
            let target = outside.executable("executable");
            fs::remove_file(fixture.0.join(escaped)).unwrap();
            std::os::unix::fs::symlink(target, fixture.0.join(escaped)).unwrap();
            assert!(matches!(resolve_runtime(&fixture.0, None), Err(NativeError::LinuxRuntimeUnavailable)));
        }
    }

    #[test]
    fn runtime_rejects_untrusted_write_permissions() {
        for relative in ["", "geoai-runtime", "geoai-runtime/bin", "geoai-runtime/bin/geoai-supervisor", "geoai-runtime/python/bin/python3.12"] {
            for mode in [0o720, 0o702, 0o1777] {
                let fixture = Fixture::new();
                fixture.packaged();
                fs::set_permissions(fixture.0.join(relative), fs::Permissions::from_mode(mode)).unwrap();
                assert!(matches!(resolve_runtime(&fixture.0, None), Err(NativeError::LinuxRuntimeUnavailable)));
            }
        }
    }

    #[test]
    fn runtime_rejects_untrusted_ancestor_of_resource_root() {
        let fixture = Fixture::new();
        fixture.executable("resources/geoai-runtime/bin/geoai-supervisor");
        fixture.executable("resources/geoai-runtime/python/bin/python3.12");
        fs::set_permissions(&fixture.0, fs::Permissions::from_mode(0o1777)).unwrap();
        assert!(resolve_runtime(&fixture.0.join("resources"), None).is_err());
    }

    #[test]
    fn runtime_accepts_only_root_or_current_user_ownership() {
        assert!(trusted_owner(0, 1000));
        assert!(trusted_owner(1000, 1000));
        assert!(!trusted_owner(1001, 1000));
        assert!(!trusted_owner(1000, 0));
    }

    #[test]
    fn runtime_checks_both_symlink_spellings() {
        let fixture = Fixture::new();
        fixture.packaged();
        let alias_parent = Fixture::new();
        let alias = alias_parent.0.join("resources");
        std::os::unix::fs::symlink(&fixture.0, &alias).unwrap();
        let paths = resolve_runtime(&alias, None).unwrap();
        assert_eq!(paths.supervisor, fixture.0.join("geoai-runtime/bin/geoai-supervisor"));
        fs::set_permissions(&alias_parent.0, fs::Permissions::from_mode(0o777)).unwrap();
        assert!(resolve_runtime(&alias, None).is_err());
        fs::set_permissions(&alias_parent.0, fs::Permissions::from_mode(0o700)).unwrap();
        fs::set_permissions(&fixture.0, fs::Permissions::from_mode(0o777)).unwrap();
        assert!(resolve_runtime(&alias, None).is_err());
    }

    #[test]
    fn runtime_errors_expose_only_reason_codes() {
        let fixture = Fixture::new();
        let error = match resolve_runtime(&fixture.0, None) {
            Err(error) => error,
            Ok(_) => panic!("missing runtime unexpectedly resolved"),
        };
        assert_eq!(error.to_string(), "linux_runtime_unavailable");
    }

    #[test]
    fn runtime_rejects_non_executables_and_privilege_bits() {
        for relative in ["geoai-runtime/bin/geoai-supervisor", "geoai-runtime/python/bin/python3.12"] {
            for mode in [0o600, 0o4700, 0o2700] {
                let fixture = Fixture::new();
                fixture.packaged();
                fs::set_permissions(fixture.0.join(relative), fs::Permissions::from_mode(mode)).unwrap();
                assert!(resolve_runtime(&fixture.0, None).is_err());
            }
            let fixture = Fixture::new();
            fixture.packaged();
            fs::remove_file(fixture.0.join(relative)).unwrap();
            fs::DirBuilder::new().mode(0o700).create(fixture.0.join(relative)).unwrap();
            assert!(resolve_runtime(&fixture.0, None).is_err());
        }
    }

    #[test]
    fn runtime_rejects_missing_pack_and_relative_root() {
        let fixture = Fixture::new();
        assert!(resolve_runtime(&fixture.0, None).is_err());
        fixture.packaged();
        let relative = Path::new("../../../work/b01-runtime-fixtures").join(fixture.0.file_name().unwrap());
        assert_eq!(relative.canonicalize().unwrap(), fixture.0);
        assert!(resolve_runtime(&relative, None).is_err());
    }

    #[test]
    fn dev_runtime_is_native_build_configuration_only() {
        const CHILD: &str = "GEOAI_B01_RUNTIME_ENV_TEST_CHILD";
        if std::env::var_os(CHILD).is_some() {
            // Process environment must not override embedded native build inputs.
            let configured = [option_env!("GEOAI_DEV_SUPERVISOR"), option_env!("GEOAI_DEV_PYTHON"), option_env!("GEOAI_DEV_BACKEND")];
            match DevRuntimePaths::from_build_environment() {
                Ok(Some(paths)) => {
                    assert!(cfg!(debug_assertions));
                    assert!(configured.iter().all(Option::is_some));
                    for (path, expected) in [paths.supervisor, paths.python, paths.backend].into_iter().zip(configured) {
                        assert!(path == Path::new(expected.unwrap()));
                    }
                }
                Ok(None) => assert!(!cfg!(debug_assertions) || configured.iter().all(Option::is_none)),
                Err(NativeError::LinuxRuntimeUnavailable) => {
                    assert!(cfg!(debug_assertions));
                    assert!(configured.iter().any(Option::is_some));
                    assert!(configured.iter().any(Option::is_none));
                }
            }
            return;
        }
        let result = std::process::Command::new(std::env::current_exe().unwrap())
            .args(["--exact", "linux_runtime::runtime::tests::dev_runtime_is_native_build_configuration_only"])
            .env(CHILD, "1")
            .env("GEOAI_DEV_SUPERVISOR", "/untrusted-process-environment/supervisor")
            .env("GEOAI_DEV_PYTHON", "/untrusted-process-environment/python")
            .env("GEOAI_DEV_BACKEND", "/untrusted-process-environment/backend")
            .output().unwrap();
        assert!(result.status.success(), "native configuration inherited process overrides");

        let fixture = Fixture::new();
        fixture.packaged();
        let supervisor = fixture.executable("native-dev/supervisor");
        let python = fixture.executable("native-dev/python");
        let backend = fixture.0.join("native-dev");
        let paths = resolve_runtime(&fixture.0, Some(DevRuntimePaths {
            supervisor: supervisor.clone(), python: python.clone(), backend: backend.clone(),
        }));
        if cfg!(debug_assertions) {
            let paths = paths.unwrap();
            assert_eq!(paths.supervisor, supervisor);
            assert_eq!(paths.python, python);
            assert_eq!(paths.backend, Some(backend));
        } else {
            assert!(matches!(paths, Err(NativeError::LinuxRuntimeUnavailable)));
        }
    }

    #[test]
    fn dev_runtime_rejects_untrusted_backend_and_executable() {
        for relative in ["dev", "dev/supervisor", "dev/python"] {
            let fixture = Fixture::new();
            let supervisor = fixture.executable("dev/supervisor");
            let python = fixture.executable("dev/python");
            fs::set_permissions(fixture.0.join(relative), fs::Permissions::from_mode(0o777)).unwrap();
            assert!(resolve_runtime(&fixture.0, Some(DevRuntimePaths {
                supervisor, python, backend: fixture.0.join("dev"),
            })).is_err());
        }
    }
}
