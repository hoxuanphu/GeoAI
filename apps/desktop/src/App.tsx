import { useEffect, useState } from 'react';
import { desktopHandoff } from './handoff';
import { getCapabilities, getHealth, validateSession, type CapabilitiesResponse, type HealthResponse, type SessionDescriptor } from './generated/api';

type Handoff = () => Promise<SessionDescriptor>;
type Connection = { kind: 'loading' } | { kind: 'error'; message: string } | { kind: 'ready'; health: HealthResponse; capabilities: CapabilitiesResponse };

export function App({ handoff = desktopHandoff }: { handoff?: Handoff }) {
  const [connection, setConnection] = useState<Connection>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [panel, setPanel] = useState<'data' | 'status'>('data');
  const [projectName, setProjectName] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    // Technical UI deadline only; this is not a business/G0 performance SLO.
    const deadline = window.setTimeout(() => {
      if (!active) return;
      active = false;
      controller.abort();
      setConnection({ kind: 'error', message: 'Kết nối quá thời gian chờ.' });
    }, 10_000);
    async function connect() {
      setConnection({ kind: 'loading' });
      let session: SessionDescriptor;
      try { session = validateSession(await handoff()); }
      catch { if (active) setConnection({ kind: 'error', message: 'Chưa kết nối được ứng dụng desktop.' }); return; }
      if (!active) return;
      try {
        const [health, capabilities] = await Promise.all([getHealth(session, controller.signal), getCapabilities(session, controller.signal)]);
        if (health.status !== 'ok' || health.schema_version !== '0.1.0' || capabilities.runtime !== 'python-local-metadata' || capabilities.technical_ready !== true) throw Error('Unsupported API');
        if (active) setConnection({ kind: 'ready', health, capabilities });
      } catch { if (active) setConnection({ kind: 'error', message: 'Chưa kết nối được dịch vụ cục bộ.' }); }
    }
    void connect().finally(() => window.clearTimeout(deadline));
    return () => { active = false; window.clearTimeout(deadline); controller.abort(); };
  }, [handoff, attempt]);

  return <main>
    <header><span className="brand">GeoAI</span><span>Nền tảng desktop · bản kỹ thuật</span></header>
    <section className="connection" aria-live="polite">
      <h1>Không gian làm việc</h1>
      {connection.kind === 'loading' && <p>Đang kết nối phiên desktop…</p>}
      {connection.kind === 'error' && <><p role="alert">{connection.message}</p><p>Mở ứng dụng desktop để kết nối dịch vụ cục bộ.</p><button onClick={() => setAttempt(v => v + 1)}>Thử lại</button></>}
      {connection.kind === 'ready' && <><p role="status">Kết nối kỹ thuật sẵn sàng</p><p>API {connection.health.app_version} · schema {connection.health.schema_version}</p><p>Chưa hỗ trợ phân tích hoặc lưu dự án.</p></>}
    </section>
    <nav aria-label="Bảng làm việc"><button aria-pressed={panel === 'data'} onClick={() => setPanel('data')}>Dữ liệu</button><button aria-pressed={panel === 'status'} onClick={() => setPanel('status')}>Trạng thái</button></nav>
    <section className="panel">
      {panel === 'data' ? <><h2>Dữ liệu dự án</h2><label htmlFor="project-name">Tên dự án ghi chú</label><input id="project-name" value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="Ghi chú trong phiên làm việc" /><p>Ghi chú giữ khi đổi bảng. Thêm dữ liệu và lưu dự án sẽ được bổ sung sau.</p></> : <><h2>Phạm vi hiện tại</h2><p>Bạn có thể kiểm tra kết nối. Chức năng dữ liệu và phân tích sẽ được bổ sung sau.</p></>}
    </section>
  </main>;
}
