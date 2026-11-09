import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { App } from './App';

afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

const descriptor = { base_url: 'http://127.0.0.1:49231', token: 'synthetic-secret-in-memory' };
const health = { status: 'ok', app_version: '0.1.0', schema_version: '0.1.0' };
const capabilities = { schema_version: '0.1.0', runtime: 'python-local-metadata', features: ['health', 'capabilities'], technical_ready: true, inference_ready: false, execution_owner_ready: false, native_launcher_ready: false, project_writer_ready: false };

function network() {
  vi.stubGlobal('fetch', vi.fn(async (url: string, options: RequestInit) => {
    if (options.headers && new Headers(options.headers).get('Authorization') !== 'Bearer ' + descriptor.token) return new Response('', { status: 401 });
    if (url.includes('?') || !url.startsWith(descriptor.base_url)) return new Response('', { status: 403 });
    return new Response(JSON.stringify(url.endsWith('/health') ? health : capabilities), { status: 200 });
  }));
}

test('desktop handoff uses authenticated API and panel changes retain project state', async () => {
  network();
  render(<App handoff={async () => descriptor} />);
  await screen.findByText('Kết nối kỹ thuật sẵn sàng');
  expect(screen.getByText('Chưa hỗ trợ phân tích hoặc lưu dự án.')).toBeTruthy();
  fireEvent.change(screen.getByLabelText('Tên dự án ghi chú'), { target: { value: 'Dự án thử nghiệm' } });
  fireEvent.click(screen.getByRole('button', { name: 'Trạng thái' }));
  fireEvent.click(screen.getByRole('button', { name: 'Dữ liệu' }));
  expect((screen.getByLabelText('Tên dự án ghi chú') as HTMLInputElement).value).toBe('Dự án thử nghiệm');
  expect(document.body.textContent).not.toContain(descriptor.token);
  expect(localStorage.length).toBe(0);
});

test('handoff failure has sanitized error and retry can reconnect', async () => {
  network(); let attempts = 0;
  render(<App handoff={async () => { if (++attempts === 1) throw Error(descriptor.token); return descriptor; }} />);
  await screen.findByText('Chưa kết nối được ứng dụng desktop.');
  expect(document.body.textContent).not.toContain(descriptor.token);
  fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
  await screen.findByText('Kết nối kỹ thuật sẵn sàng');
});

test('API failure requires retry and never displays untrusted response', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(descriptor.token, { status: 401 })));
  render(<App handoff={async () => descriptor} />);
  await screen.findByText('Chưa kết nối được dịch vụ cục bộ.');
  expect(document.body.textContent).not.toContain(descriptor.token);
  network(); fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
  await screen.findByText('Kết nối kỹ thuật sẵn sàng');
});

test('browser mode reports absent desktop handoff without manufacturing a session', async () => {
  render(<App />);
  await screen.findByText('Chưa kết nối được ứng dụng desktop.');
});

test('untrusted handoff URL is rejected before credentials can be sent', async () => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  render(<App handoff={async () => ({ ...descriptor, base_url: 'https://attacker.invalid' })} />);
  await screen.findByText('Chưa kết nối được ứng dụng desktop.');
  expect(fetcher).not.toHaveBeenCalled();
});

test('hung handoff times out, retry connects and a late old handoff cannot replace the new session', async () => {
  vi.useFakeTimers(); network();
  let finishOld!: (value: typeof descriptor) => void;
  const pending = new Promise<typeof descriptor>(resolve => { finishOld = resolve; });
  let attempts = 0;
  render(<App handoff={() => ++attempts === 1 ? pending : Promise.resolve(descriptor)} />);
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(screen.getByText('Kết nối quá thời gian chờ.')).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Thử lại' })); });
  expect(screen.getByText('Kết nối kỹ thuật sẵn sàng')).toBeTruthy();
  expect(fetch).toHaveBeenCalledTimes(2);
  await act(async () => { finishOld({ base_url: 'http://127.0.0.1:49232', token: 'late-old-private-token' }); });
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByText('Kết nối kỹ thuật sẵn sàng')).toBeTruthy();
});

test('hung network is aborted on deadline and retry can connect', async () => {
  vi.useFakeTimers(); let signal: AbortSignal | undefined;
  vi.stubGlobal('fetch', vi.fn((_url: string, options: RequestInit) => { signal = options.signal as AbortSignal; return new Promise<Response>(() => {}); }));
  render(<App handoff={async () => descriptor} />);
  await act(async () => { await vi.advanceTimersByTimeAsync(10_000); });
  expect(signal?.aborted).toBe(true);
  expect(screen.getByText('Kết nối quá thời gian chờ.')).toBeTruthy();
  network();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Thử lại' })); });
  expect(screen.getByText('Kết nối kỹ thuật sẵn sàng')).toBeTruthy();
});
