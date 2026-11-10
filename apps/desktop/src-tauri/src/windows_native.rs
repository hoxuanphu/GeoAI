//! Contained Windows sidecar. The Job Object root handle belongs only to this shell.

use super::SessionDescriptor;
use std::ffi::{c_void, OsStr};
use std::fs::File;
use std::io::{Read, Write};
use std::os::windows::ffi::OsStrExt;
use std::os::windows::io::FromRawHandle;
use std::path::{Path, PathBuf};
use std::ptr::{null, null_mut};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};
use tauri::Manager;

type Handle = isize;
const INVALID_HANDLE: Handle = -1;
const JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: u32 = 0x2000;
const JOB_OBJECT_EXTENDED_LIMIT_INFORMATION: u32 = 9;
const JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION: u32 = 1;
const PROC_THREAD_ATTRIBUTE_HANDLE_LIST: usize = 0x0002_0002;
const PROC_THREAD_ATTRIBUTE_JOB_LIST: usize = 0x0002_000D;
const EXTENDED_STARTUPINFO_PRESENT: u32 = 0x0008_0000;
const CREATE_UNICODE_ENVIRONMENT: u32 = 0x400;
const CREATE_NO_WINDOW: u32 = 0x0800_0000;
const STARTF_USESTDHANDLES: u32 = 0x100;
const HANDLE_FLAG_INHERIT: u32 = 1;
const WAIT_OBJECT_0: u32 = 0;
const WAIT_TIMEOUT: u32 = 258;
const ERROR_INSUFFICIENT_BUFFER: u32 = 122;

#[repr(C)]
struct SecurityAttributes { length: u32, descriptor: *mut c_void, inherit: i32 }
impl Default for SecurityAttributes {
    fn default() -> Self { Self { length: 0, descriptor: null_mut(), inherit: 0 } }
}

#[repr(C)]
#[derive(Default)]
struct BasicLimit {
    process_time: i64, job_time: i64, flags: u32, min_working_set: usize,
    max_working_set: usize, active_limit: u32, affinity: usize,
    priority: u32, scheduling: u32,
}

#[repr(C)]
#[derive(Default)]
struct IoCounters { reads: u64, writes: u64, other: u64, read_bytes: u64, write_bytes: u64, other_bytes: u64 }

#[repr(C)]
#[derive(Default)]
struct ExtendedLimit { basic: BasicLimit, io: IoCounters, process_memory: usize, job_memory: usize, peak_process_memory: usize, peak_job_memory: usize }

#[repr(C)]
#[derive(Default)]
struct BasicAccounting { user_time: i64, kernel_time: i64, period_user: i64, period_kernel: i64, page_faults: u32, total: u32, active: u32, terminated: u32 }

#[repr(C)]
struct StartupInfo {
    cb: u32, reserved: *mut u16, desktop: *mut u16, title: *mut u16,
    x: u32, y: u32, width: u32, height: u32, chars_x: u32, chars_y: u32,
    fill: u32, flags: u32, show: u16, reserved_size: u16, reserved2: *mut u8,
    stdin: Handle, stdout: Handle, stderr: Handle,
}
impl Default for StartupInfo {
    fn default() -> Self {
        // All-zero is a valid initial state for this Win32 C record.
        unsafe { std::mem::zeroed() }
    }
}

#[repr(C)]
struct StartupInfoEx { startup: StartupInfo, attributes: *mut c_void }
impl Default for StartupInfoEx {
    fn default() -> Self { Self { startup: StartupInfo::default(), attributes: null_mut() } }
}

#[repr(C)]
#[derive(Default)]
struct ProcessInfo { process: Handle, thread: Handle, pid: u32, tid: u32 }

#[link(name = "kernel32")]
extern "system" {
    fn CreateJobObjectW(attrs: *const SecurityAttributes, name: *const u16) -> Handle;
    fn SetInformationJobObject(job: Handle, class: u32, info: *const c_void, size: u32) -> i32;
    fn QueryInformationJobObject(job: Handle, class: u32, info: *mut c_void, size: u32, returned: *mut u32) -> i32;
    fn TerminateJobObject(job: Handle, exit_code: u32) -> i32;
    fn CloseHandle(handle: Handle) -> i32;
    fn CreatePipe(read: *mut Handle, write: *mut Handle, attrs: *const SecurityAttributes, size: u32) -> i32;
    fn SetHandleInformation(handle: Handle, mask: u32, flags: u32) -> i32;
    fn InitializeProcThreadAttributeList(list: *mut c_void, count: u32, flags: u32, size: *mut usize) -> i32;
    fn UpdateProcThreadAttribute(list: *mut c_void, flags: u32, attribute: usize, value: *mut c_void, size: usize, previous: *mut c_void, returned: *mut usize) -> i32;
    fn DeleteProcThreadAttributeList(list: *mut c_void);
    fn CreateProcessW(application: *const u16, command: *mut u16, process_attrs: *const c_void, thread_attrs: *const c_void, inherit: i32, flags: u32, env: *const c_void, cwd: *const u16, startup: *const StartupInfoEx, info: *mut ProcessInfo) -> i32;
    fn WaitForSingleObject(handle: Handle, timeout: u32) -> u32;
    fn GetLastError() -> u32;
}

struct OwnedHandle(Handle);
impl OwnedHandle {
    fn new(raw: Handle) -> Result<Self, String> {
        if raw == 0 || raw == INVALID_HANDLE { Err("native_handle_unavailable".into()) } else { Ok(Self(raw)) }
    }
    fn into_file(mut self) -> File {
        let raw = self.0;
        self.0 = 0;
        unsafe { File::from_raw_handle(raw as *mut c_void) }
    }
}
impl Drop for OwnedHandle {
    fn drop(&mut self) { if self.0 != 0 && self.0 != INVALID_HANDLE { unsafe { CloseHandle(self.0); } } }
}

struct AttributeList { words: Vec<usize>, initialized: bool }
impl AttributeList {
    fn new() -> Result<Self, String> {
        let mut size = 0usize;
        unsafe { InitializeProcThreadAttributeList(null_mut(), 2, 0, &mut size); }
        if unsafe { GetLastError() } != ERROR_INSUFFICIENT_BUFFER || size == 0 || size > 65536 {
            return Err("process_attributes_unavailable".into());
        }
        let mut list = Self { words: vec![0; size.div_ceil(std::mem::size_of::<usize>())], initialized: false };
        if unsafe { InitializeProcThreadAttributeList(list.ptr(), 2, 0, &mut size) } == 0 {
            return Err("process_attributes_unavailable".into());
        }
        list.initialized = true;
        Ok(list)
    }
    fn ptr(&mut self) -> *mut c_void { self.words.as_mut_ptr().cast() }
    fn set(&mut self, attribute: usize, handles: &mut [Handle]) -> Result<(), String> {
        if unsafe { UpdateProcThreadAttribute(self.ptr(), 0, attribute, handles.as_mut_ptr().cast(), std::mem::size_of_val(handles), null_mut(), null_mut()) } == 0 {
            return Err("atomic_process_attributes_unavailable".into());
        }
        Ok(())
    }
}
impl Drop for AttributeList {
    fn drop(&mut self) { if self.initialized { unsafe { DeleteProcThreadAttributeList(self.ptr()); } } }
}

fn wide(s: &OsStr) -> Vec<u16> { s.encode_wide().chain(std::iter::once(0)).collect() }

fn quote(arg: &str) -> String {
    if !arg.is_empty() && !arg.chars().any(|ch| matches!(ch, ' ' | '\t' | '"')) { return arg.to_owned(); }
    let mut out = String::from("\"");
    let mut backslashes = 0;
    for ch in arg.chars() {
        match ch {
            '\\' => backslashes += 1,
            '"' => { out.push_str(&"\\".repeat(backslashes * 2 + 1)); out.push('"'); backslashes = 0; }
            _ => { out.push_str(&"\\".repeat(backslashes)); backslashes = 0; out.push(ch); }
        }
    }
    out.push_str(&"\\".repeat(backslashes * 2));
    out.push('"');
    out
}

fn create_pipe() -> Result<(OwnedHandle, OwnedHandle), String> {
    let mut read = 0;
    let mut write = 0;
    let attrs = SecurityAttributes { length: std::mem::size_of::<SecurityAttributes>() as u32, inherit: 1, ..Default::default() };
    if unsafe { CreatePipe(&mut read, &mut write, &attrs, 0) } == 0 { return Err("private_pipe_unavailable".into()); }
    Ok((OwnedHandle::new(read)?, OwnedHandle::new(write)?))
}

fn environment(dev_backend: Option<&Path>) -> Result<Vec<u16>, String> {
    let mut vars = Vec::new();
    for key in ["SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA"] {
        if let Some(value) = std::env::var_os(key) {
            let value = value.to_string_lossy();
            if value.contains('\0') { return Err("invalid_runtime_environment".into()); }
            vars.push((key.to_owned(), value.into_owned()));
        }
    }
    if !vars.iter().any(|(key, _)| key == "SystemRoot") { return Err("windows_environment_unavailable".into()); }
    if let Some(path) = dev_backend { vars.push(("PYTHONPATH".into(), path.to_string_lossy().into_owned())); }
    vars.sort_by_key(|(key, _)| key.to_ascii_uppercase());
    let mut block: Vec<u16> = vars.into_iter().flat_map(|(key, value)| format!("{key}={value}\0").encode_utf16().collect::<Vec<_>>()).collect();
    block.push(0);
    Ok(block)
}

fn runtime(app: &tauri::AppHandle) -> Result<(PathBuf, Vec<String>, Option<PathBuf>), String> {
    if cfg!(debug_assertions) {
        let python = option_env!("GEOAI_DEV_PYTHON").ok_or("trusted_dev_runtime_unconfigured")?;
        let backend = option_env!("GEOAI_DEV_BACKEND").ok_or("trusted_dev_runtime_unconfigured")?;
        let executable = PathBuf::from(python).canonicalize().map_err(|_| "trusted_dev_runtime_unavailable")?;
        let root = PathBuf::from(backend).canonicalize().map_err(|_| "trusted_dev_runtime_unavailable")?;
        if !executable.is_absolute() || !executable.is_file() || !root.is_dir() { return Err("trusted_dev_runtime_unavailable".into()); }
        Ok((executable, vec!["-m".into(), "geoai.bootstrap".into(), "--native-stdio-handoff".into(), "--no-console".into()], Some(root)))
    } else {
        let resource = app.path().resource_dir().map_err(|_| "bundled_runtime_unavailable")?;
        let executable = resource.join("geoai-sidecar.exe").canonicalize().map_err(|_| "bundled_runtime_unavailable")?;
        if !executable.starts_with(&resource) || !executable.is_file() { return Err("bundled_runtime_unavailable".into()); }
        Ok((executable, vec!["--native-stdio-handoff".into(), "--no-console".into()], None))
    }
}

fn read_descriptor(file: &mut File) -> Result<SessionDescriptor, String> {
    let mut line = Vec::with_capacity(256);
    let mut byte = [0u8; 1];
    loop {
        if line.len() >= 2048 { return Err("session_descriptor_too_large".into()); }
        if file.read(&mut byte).map_err(|_| "session_descriptor_unavailable")? == 0 { return Err("session_descriptor_unavailable".into()); }
        if byte[0] == b'\n' { break; }
        line.push(byte[0]);
    }
    let descriptor: SessionDescriptor = serde_json::from_slice(&line).map_err(|_| "invalid_session_descriptor")?;
    descriptor.validate().map_err(str::to_owned)?;
    Ok(descriptor)
}

pub struct NativeSession {
    job: OwnedHandle,
    process: OwnedHandle,
    stdin: Option<File>,
    descriptor: SessionDescriptor,
    stderr_drain: Option<thread::JoinHandle<()>>,
    stdout_drain: Option<thread::JoinHandle<()>>,
}

impl NativeSession {
    pub fn launch(app: &tauri::AppHandle) -> Result<Self, String> {
        let (executable, args, dev_backend) = runtime(app)?;
        let env = environment(dev_backend.as_deref())?;
        let job = OwnedHandle::new(unsafe { CreateJobObjectW(null(), null()) })?;
        let mut limit = ExtendedLimit::default();
        limit.basic.flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if unsafe { SetInformationJobObject(job.0, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, (&limit as *const ExtendedLimit).cast(), std::mem::size_of::<ExtendedLimit>() as u32) } == 0 {
            return Err("job_configuration_failed".into());
        }
        let (child_stdin, parent_stdin) = create_pipe()?;
        let (parent_stdout, child_stdout) = create_pipe()?;
        let (parent_stderr, child_stderr) = create_pipe()?;
        for handle in [parent_stdin.0, parent_stdout.0, parent_stderr.0] {
            if unsafe { SetHandleInformation(handle, HANDLE_FLAG_INHERIT, 0) } == 0 { return Err("pipe_inheritance_failed".into()); }
        }
        let mut attrs = AttributeList::new()?;
        let mut inherited_handles = [child_stdin.0, child_stdout.0, child_stderr.0];
        let mut job_handles = [job.0];
        attrs.set(PROC_THREAD_ATTRIBUTE_HANDLE_LIST, &mut inherited_handles)?;
        attrs.set(PROC_THREAD_ATTRIBUTE_JOB_LIST, &mut job_handles)?;
        let mut startup = StartupInfoEx::default();
        startup.startup.cb = std::mem::size_of::<StartupInfoEx>() as u32;
        startup.startup.flags = STARTF_USESTDHANDLES;
        startup.startup.stdin = child_stdin.0;
        startup.startup.stdout = child_stdout.0;
        startup.startup.stderr = child_stderr.0;
        startup.attributes = attrs.ptr();
        let mut command = wide(OsStr::new(&std::iter::once(quote(&executable.to_string_lossy())).chain(args.iter().map(|arg| quote(arg))).collect::<Vec<_>>().join(" ")));
        let app_name = wide(executable.as_os_str());
        let cwd = wide(executable.parent().ok_or("trusted_runtime_unavailable")?.as_os_str());
        let mut info = ProcessInfo::default();
        if unsafe { CreateProcessW(app_name.as_ptr(), command.as_mut_ptr(), null(), null(), 1,
            EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW,
            env.as_ptr().cast(), cwd.as_ptr(), &startup, &mut info) } == 0 {
            return Err("contained_sidecar_creation_failed".into());
        }
        let process = OwnedHandle::new(info.process)?;
        let _thread = OwnedHandle::new(info.thread)?;
        drop(child_stdin);
        drop(child_stdout);
        drop(child_stderr);
        let stderr_file = parent_stderr.into_file();
        let stderr_drain = thread::spawn(move || {
            let mut stream = stderr_file;
            let mut chunk = [0u8; 4096];
            while let Ok(count) = stream.read(&mut chunk) { if count == 0 { break; } }
        });
        let (sender, receiver) = mpsc::sync_channel(1);
        let stdout_drain = thread::spawn(move || {
            let mut stream = parent_stdout.into_file();
            let result = read_descriptor(&mut stream);
            let _ = sender.send(result);
            let mut chunk = [0u8; 4096];
            while let Ok(count) = stream.read(&mut chunk) { if count == 0 { break; } }
        });
        let mut active = Self { job, process, stdin: Some(parent_stdin.into_file()),
            descriptor: SessionDescriptor { base_url: String::new(), token: String::new() },
            stderr_drain: Some(stderr_drain), stdout_drain: Some(stdout_drain) };
        match receiver.recv_timeout(Duration::from_secs(10)) {
            Ok(Ok(descriptor)) if active.is_alive()? => { active.descriptor = descriptor; Ok(active) }
            _ => { active.stop()?; Err("sidecar_startup_failed".into()) }
        }
    }

    pub fn descriptor(&self) -> SessionDescriptor { self.descriptor.clone() }

    pub fn is_alive(&self) -> Result<bool, String> {
        let wait = unsafe { WaitForSingleObject(self.process.0, 0) };
        match wait {
            WAIT_OBJECT_0 => Ok(false),
            WAIT_TIMEOUT => Ok(!self.group_stopped()?),
            _ => Err("sidecar_state_unknown".into()),
        }
    }

    fn group_stopped(&self) -> Result<bool, String> {
        let mut accounting = BasicAccounting::default();
        let ok = unsafe { QueryInformationJobObject(self.job.0, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            (&mut accounting as *mut BasicAccounting).cast(), std::mem::size_of::<BasicAccounting>() as u32, null_mut()) };
        if ok == 0 { return Err("sidecar_group_state_unknown".into()); }
        Ok(accounting.active == 0)
    }

    fn wait_group(&self, duration: Duration) -> Result<bool, String> {
        let deadline = Instant::now() + duration;
        loop {
            if self.group_stopped()? { return Ok(true); }
            if Instant::now() >= deadline { return Ok(false); }
            thread::sleep(Duration::from_millis(25));
        }
    }

    pub fn stop(&mut self) -> Result<(), String> {
        if let Some(mut stdin) = self.stdin.take() { let _ = stdin.write_all(b"shutdown\n"); }
        if !self.wait_group(Duration::from_secs(3))? {
            if unsafe { TerminateJobObject(self.job.0, 1) } == 0 { return Err("sidecar_termination_failed".into()); }
            if !self.wait_group(Duration::from_secs(5))? { return Err("sidecar_stop_unconfirmed".into()); }
        }
        if let Some(join) = self.stderr_drain.take() { let _ = join.join(); }
        if let Some(join) = self.stdout_drain.take() { let _ = join.join(); }
        Ok(())
    }
}

impl Drop for NativeSession {
    fn drop(&mut self) {
        if self.group_stopped().unwrap_or(false) { return; }
        unsafe { TerminateJobObject(self.job.0, 1); }
        let _ = self.wait_group(Duration::from_secs(5));
    }
}
