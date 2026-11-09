import { invoke, isTauri } from '@tauri-apps/api/core';
import { validateSession, type SessionDescriptor } from './generated/api';

export async function desktopHandoff(): Promise<SessionDescriptor> {
  if (!isTauri()) throw Error('desktop_handoff_unavailable');
  return validateSession(await invoke<unknown>('bootstrap_session'));
}
