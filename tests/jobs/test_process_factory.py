"""Portable adapter/transport boundaries; no native containment proof."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from geoai.contracts import WorkerLaunchPacket


def packet():
    data=json.loads((Path(__file__).parents[1]/'fixtures/contracts/worker-launch-packet.json').read_text())
    return WorkerLaunchPacket.model_validate(data['WorkerLaunchPacket'])


class ProcessFactoryTests(unittest.TestCase):
    def factory(self):
        calls=[]
        class Factory:
            def launch_worker(self, executable, value, *, owner, deadline):
                calls.append(SimpleNamespace(packet=value,owner=owner,deadline=deadline))
                return SimpleNamespace(marker='process')
        return Factory(),calls

    def transport_class(self):
        from geoai.jobs.transport import WorkerTransport
        class CaptureTransport(WorkerTransport):
            def __init__(self, process, **options):
                self.process,self.options=process,options
        return CaptureTransport

    def test_transport_delegates_original_packet_and_absolute_deadline(self):
        from geoai.jobs import transport
        factory,calls=self.factory(); value=packet()
        owner=SimpleNamespace(owner_id=value.execution_owner_id,owner_epoch=value.owner_epoch)
        with patch.object(transport.time,'monotonic',return_value=100.):
            instance=self.transport_class().launch(Path('/trusted/python'),value,process_factory=factory,owner=owner)
        self.assertIs(calls[0].packet,value)
        self.assertEqual(calls[0].deadline,110.)
        self.assertIs(calls[0].owner,owner)
        self.assertEqual(instance.process.marker,'process')

    def test_expired_deadline_does_not_spawn(self):
        from geoai.jobs import transport
        factory,calls=self.factory(); readings=iter([100.,111.])
        with patch.object(transport.time,'monotonic',side_effect=lambda:next(readings,111.)):
            with self.assertRaises(transport.TransportError):
                self.transport_class().launch(Path('/trusted/python'),packet(),process_factory=factory,owner=None)
        self.assertEqual(calls,[])

    def test_transport_import_does_not_load_windows_adapter(self):
        import subprocess,sys
        code='import geoai.jobs.transport,sys,json; print(json.dumps([m for m in sys.modules if m in ("geoai.jobs.native_process","geoai.storage.windows_owner")]))'
        result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),[])

    def test_reexported_error_classes_keep_catch_compatibility(self):
        from geoai.jobs.process import NativeProcessError
        from geoai.storage.native_owner import OwnershipError
        from geoai.jobs import native_process
        from geoai.storage import windows_owner
        self.assertIs(native_process.NativeProcessError,NativeProcessError)
        self.assertIs(windows_owner.OwnershipError,OwnershipError)

    def test_owned_fd_close_cannot_close_reused_descriptor(self):
        from geoai.jobs.native_process import _OwnedFD
        read_fd,write_fd=os.pipe()
        owned=_OwnedFD(read_fd)
        owned.close()
        next_read,next_write=os.pipe()
        try:
            if next_read != read_fd: os.dup2(next_read,read_fd)
            owned.close()
            os.fstat(read_fd)
        finally:
            for fd in {write_fd,next_read,next_write,read_fd}:
                try: os.close(fd)
                except OSError: pass


class WindowsAdapterPolicyUnitTests(unittest.TestCase):
    def test_partial_bootstrap_failure_closes_only_owned_fds(self):
        import sys,time
        from geoai.jobs import native_process
        allocated=[]; real_pipe=os.pipe
        def allocate():
            fds=real_pipe(); allocated.extend(fds); return fds
        factory=native_process.WindowsProcessFactory()
        value=SimpleNamespace(model_dump=lambda **kwargs:{})
        with patch.dict(sys.modules,{'msvcrt':SimpleNamespace(get_osfhandle=lambda fd:fd)}), \
             patch.object(native_process.os,'pipe',side_effect=allocate), \
             patch.object(native_process.ManagedProcess,'launch',side_effect=native_process.NativeProcessError('unit_launch_failed')):
            with self.assertRaisesRegex(native_process.NativeProcessError,'unit_launch_failed'):
                factory._launch_with_bootstrap(Path('/trusted/python'),value,None,time.monotonic()+10)
        self.assertEqual(len(allocated),2)
        for fd in allocated:
            with self.assertRaises(OSError): os.fstat(fd)

    def test_legacy_duration_receives_remaining_absolute_budget(self):
        from geoai.jobs import native_process
        calls=[]
        native=SimpleNamespace(wait=lambda seconds:calls.append(seconds) or True)
        process=native_process._WindowsManagedProcess(native,None,None,None,packet())
        with patch.object(native_process.time,'monotonic',return_value=100.): process.wait(110.)
        with patch.object(native_process.time,'monotonic',return_value=104.): process.wait(110.)
        self.assertEqual(calls,[10.,6.])

    def test_stop_evidence_rechecks_bound_process_and_attempt(self):
        from geoai.jobs import native_process
        value=packet(); observed=[]; stopped=[True]
        native=SimpleNamespace(group_stopped=lambda seconds:observed.append(seconds) or stopped[0])
        class Guard:
            def assert_held(self,project):
                if project != value.project_id: raise RuntimeError('wrong_project')
        guard=Guard()
        owner=SimpleNamespace(owner_id=value.execution_owner_id,owner_epoch=value.owner_epoch,
            _closed=False,_recovery_required=False,_writers={value.project_id:guard})
        factory=native_process.WindowsProcessFactory()
        process=native_process._WindowsManagedProcess(native,factory,owner,guard,value)
        factory._processes[id(process)]=process  # Explicit unit registry, no OS proof.
        evidence=factory.stop_evidence(process,project_id=value.project_id,attempt=value.start.attempt)
        evidence.assert_stopped(value.project_id,value.start.attempt)
        stopped[0]=False
        with self.assertRaisesRegex(native_process.NativeProcessError,'workload_still_active'):
            evidence.assert_stopped(value.project_id,value.start.attempt)
        self.assertEqual(observed,[0.,0.])
        with self.assertRaises(native_process.NativeProcessError):
            evidence.assert_stopped('project:other',value.start.attempt)
        stopped[0]=True
        owner._writers[value.project_id]=Guard()
        with self.assertRaises(native_process.NativeProcessError):
            evidence.assert_stopped(value.project_id,value.start.attempt)


class PortableTransportRoundtripTests(unittest.TestCase):
    def test_capabilities_and_shutdown_over_real_pipes(self):
        import sys
        from process_fixtures import UnitFactory
        from geoai.jobs.transport import WorkerTransport
        transport=WorkerTransport.launch(Path(sys.executable),packet(),process_factory=UnitFactory(),owner=None)
        self.addCleanup(transport.shutdown,.2,2)
        response=transport.request('capabilities',{'protocol_version':'0.1.0','schema_version':'0.1.0'},2)
        self.assertEqual(response.result['protocol_version'],'0.1.0')
        self.assertTrue(transport.shutdown(.2,2))
        self.assertFalse(transport._reader.is_alive())
        self.assertFalse(transport._writer_thread.is_alive())


class WindowsWriterLifetimeUnitTests(unittest.TestCase):
    """Actual writer/lease bookkeeping, with Win32 I/O replaced explicitly."""
    def setUp(self):
        from geoai.storage import windows_owner
        from geoai.jobs import native_process
        self.value=packet()
        self.native_process=native_process
        self.owner=windows_owner.ExecutionOwner(Path('/unit'),None,None,
            {'owner_id':self.value.execution_owner_id,'epoch':self.value.owner_epoch,
             'creation_time':1,'session_id':1})
        self.writer=windows_owner.ProjectWriter(self.owner,self.value.project_id,'unit-root',123)
        self.owner._writers[self.value.project_id]=self.writer
        self.owner._project_roots[self.value.project_id]=Path('/unit')
        for patcher in [patch.object(windows_owner,'_directory_identity',return_value='unit-root',create=True),
                        patch.object(windows_owner,'CloseHandle',return_value=True,create=True),
                        patch.object(native_process,'os',SimpleNamespace(name='nt',pipe=os.pipe,
                            set_inheritable=os.set_inheritable,write=os.write,close=os.close))]:
            patcher.start(); self.addCleanup(patcher.stop)
        self.addCleanup(self.writer.close)
        self.factory=native_process.WindowsProcessFactory()
        class Native:
            active=True
            def terminate_group(inner,seconds): inner.active=False; return True
            def close(inner):
                if inner.active: raise native_process.NativeProcessError('group_still_active')
        self.native=Native()

    def launch(self):
        with patch.object(self.factory,'_launch_with_bootstrap',return_value=self.native):
            process=self.factory.launch_worker(Path('/trusted/python'),self.value,owner=self.owner,deadline=10**12)
        self.addCleanup(process.terminate_group,10**12)
        return process

    def test_live_process_prevents_writer_close(self):
        from geoai.storage.native_owner import OwnershipError
        process=self.launch()
        with self.assertRaisesRegex(OwnershipError,'writer_has_live_leases'): self.writer.close()
        self.assertEqual(self.writer._leases,1)

    def test_failed_launch_releases_its_lease(self):
        with patch.object(self.factory,'_launch_with_bootstrap',side_effect=self.native_process.NativeProcessError('unit_failure')):
            with self.assertRaises(self.native_process.NativeProcessError):
                self.factory.launch_worker(Path('/trusted/python'),self.value,owner=self.owner,deadline=10**12)
        self.assertEqual(self.writer._leases,0)
        self.writer.close()

    def test_stop_releases_lease_exactly_once(self):
        process=self.launch()
        self.assertEqual(self.writer._leases,1)
        self.assertTrue(process.terminate_group(10**12))
        process.close(); process.close()
        self.assertEqual(self.writer._leases,0)
        self.writer.close()

    def test_unproved_bootstrap_cleanup_keeps_writer_lease(self):
        import sys
        from geoai.storage.native_owner import OwnershipError
        self.native.terminate_group=lambda seconds:False
        with patch.dict(sys.modules,{'msvcrt':SimpleNamespace(get_osfhandle=lambda fd:fd)}), \
             patch.object(self.native_process.ManagedProcess,'launch',return_value=self.native), \
             patch.object(self.native_process.threading.Thread,'start',side_effect=RuntimeError('unit_start_failure')):
            with self.assertRaisesRegex(self.native_process.NativeProcessError,'bootstrap_cleanup_unproved'):
                self.factory.launch_worker(Path('/trusted/python'),self.value,owner=self.owner,deadline=10**12)
        try:
            with self.assertRaisesRegex(OwnershipError,'writer_has_live_leases'): self.writer.close()
            self.assertEqual(self.writer._leases,1)
        finally:
            # Unit-only cleanup after simulating a later proved stop.
            for item in self.factory._unproved:
                if isinstance(item,tuple) and item[1] is not None: item[1].close()
