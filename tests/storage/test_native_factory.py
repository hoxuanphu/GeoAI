import unittest


class NativeSharedTypesTests(unittest.TestCase):
    def test_windows_reexports_shared_identity_and_error(self):
        from geoai.storage.native_io import NativeIdentity, StorageIOError
        from geoai.storage import windows_io
        self.assertIs(windows_io.NativeIdentity, NativeIdentity)
        self.assertIs(windows_io.StorageIOError, StorageIOError)
        self.assertEqual(NativeIdentity('volume', 'file'), NativeIdentity('volume', 'file'))
        self.assertEqual(StorageIOError('reason').code, 'reason')


class NativeInterfaceTests(unittest.TestCase):
    def test_external_registration_keeps_identity_and_is_immutable(self):
        from dataclasses import FrozenInstanceError
        from pathlib import Path
        from geoai.storage.native_io import ExternalRegistration, NativeIdentity
        registration = ExternalRegistration(Path('/trusted/input.tif'), NativeIdentity('v', 'f'))
        self.assertEqual(registration.identity.file_id, 'f')
        with self.assertRaises(FrozenInstanceError):
            registration.path = Path('/other')

    def test_protocols_do_not_grant_runtime_authorization(self):
        from geoai.storage.native_io import NativeIOFactory, NativeRoot
        # A protocol describes a shape; it is not an authorization check.
        with self.assertRaises(TypeError):
            isinstance(object(), NativeRoot)
        with self.assertRaises(TypeError):
            isinstance(object(), NativeIOFactory)


class _UnitLegacyReader:
    """Unit-only I/O double; never native filesystem evidence."""
    def __init__(self, root):
        from geoai.storage.native_io import NativeIdentity
        self.root, self.closed = root, False
        self.identity, self.size_bytes = NativeIdentity('v', 'f'), 1
        root.readers += 1

    def read(self, size=-1):
        return b'x'

    def seek(self, offset):
        pass

    def close(self):
        if not self.closed:
            self.root.readers -= 1
            self.closed = True


class _UnitLegacyRoot:
    """Only replaces Win32 syscalls for exercising production factory policy."""
    def __init__(self, path):
        self.path, self.closed, self.readers = path, False, 0
        self.calls = []

    def open_read(self, path, **options):
        self.calls.append(('read', options))
        return _UnitLegacyReader(self)

    def create_file(self, path, chunks, **options):
        self.calls.append(('create', options))
        return 1, '0' * 64

    def ensure_directory(self, path):
        self.calls.append(('directory', path))

    def move_verified(self, path, destination, target, **options):
        self.calls.append(('move', options))

    def delete_verified(self, path, **options):
        self.calls.append(('delete', options))

    def close(self):
        from geoai.storage.native_io import StorageIOError
        if self.readers:
            raise StorageIOError('root_has_live_readers')
        self.closed = True


class _FactoryUnitFixture:
    def setUp(self):
        from pathlib import Path
        from unittest.mock import patch
        from geoai.storage import windows_io
        self.legacy_patch = patch.object(windows_io, 'NativeRoot', _UnitLegacyRoot)
        self.legacy_patch.start()
        self.addCleanup(self.legacy_patch.stop)
        self.now = 100.0
        self.clock_patch = patch.object(windows_io.time, 'monotonic', lambda: self.now)
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.factory = windows_io.WindowsIOFactory()
        self.directory = Path.cwd()
        self.options = dict(sha256='0' * 64, size_bytes=1,
                            cancelled=lambda: False, deadline=110.0)

    def root(self, purpose='staging', name='root:one'):
        return self.factory.open_registered_root(name, self.directory, purpose=purpose)


class NativeFactoryPolicyUnitTests(_FactoryUnitFixture, unittest.TestCase):
    def test_none_is_an_unregistered_root(self):
        from geoai.storage.native_io import StorageIOError
        with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
            self.factory.require_root(None, purpose='read')

    def test_protocol_shape_does_not_register_a_root(self):
        from geoai.storage.native_io import StorageIOError
        with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
            self.factory.require_root(_UnitLegacyRoot(self.directory), purpose='publication')

    def test_read_root_refuses_mutations_even_without_require_root(self):
        from geoai.storage.native_io import StorageIOError
        root = self.root('read')
        with self.assertRaisesRegex(StorageIOError, 'root_purpose_mismatch'):
            self.factory.require_root(root, purpose='publication')
        for operation in [lambda: root.create_file('x', [b'x'], max_bytes=1, cancelled=lambda: False, deadline=110),
                          lambda: root.ensure_directory('x'),
                          lambda: root.delete_verified('x', **self.options),
                          lambda: root.move_verified('x', self.root('publication', 'output'), 'y', **self.options)]:
            with self.assertRaisesRegex(StorageIOError, 'root_purpose_mismatch'):
                operation()
        root.close()

    def test_remaining_budget_is_not_reset_between_calls(self):
        root = self.root()
        with root.open_read('x', **self.options): pass
        self.now = 104.0
        with root.open_read('x', **self.options): pass
        self.assertEqual([call[1]['deadline_seconds'] for call in root._legacy.calls], [10.0, 6.0])
        root.close()

    def test_expired_or_cancelled_operation_never_reaches_legacy_io(self):
        from geoai.storage.native_io import StorageIOError
        root = self.root()
        for value in [100.0, float('nan'), float('inf'), True]:
            with self.subTest(deadline=value), self.assertRaises(StorageIOError):
                root.open_read('x', **{**self.options, 'deadline': value})
        with self.assertRaises(StorageIOError):
            root.open_read('x', **{**self.options, 'cancelled': lambda: True})
        self.assertEqual(root._legacy.calls, [])
        root.close()

    def test_registry_retains_root_and_rejects_closed_or_foreign_objects(self):
        import weakref, gc
        from geoai.storage import windows_io
        from geoai.storage.native_io import StorageIOError
        root = self.root()
        ref = weakref.ref(root)
        del root
        gc.collect()
        self.assertIsNotNone(ref())
        with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
            windows_io.WindowsIOFactory().require_root(ref(), purpose='staging')
        root = ref()
        root.close()
        with self.assertRaises(StorageIOError):
            self.factory.require_root(root, purpose='staging')
        root.close()

    def test_duplicate_root_id_cannot_change_purpose(self):
        from geoai.storage.native_io import StorageIOError
        root = self.root('read')
        with self.assertRaises(StorageIOError):
            self.root('publication')
        self.factory.require_root(root, purpose='read')
        root.close()

    def test_reader_keeps_root_open_and_seek_returns_position(self):
        from geoai.storage.native_io import StorageIOError
        root = self.root('read')
        reader = root.open_read('x', **self.options)
        self.assertEqual(reader.seek(0), 0)
        with self.assertRaisesRegex(StorageIOError, 'root_has_live_readers'):
            root.close()
        self.factory.require_root(root, purpose='read')
        reader.close(); reader.close(); root.close()

    def test_external_reader_owns_root_and_failed_open_cleans_up(self):
        from pathlib import Path
        from geoai.storage.native_io import ExternalRegistration, NativeIdentity, StorageIOError
        registration = ExternalRegistration(self.directory / 'x', NativeIdentity('v', 'f'))
        reader = self.factory.open_external(registration, **self.options)
        legacy = reader._reader.root
        self.assertEqual(legacy.calls[0][1]['expected_identity'], ('v', 'f'))
        self.assertEqual(reader.read(), b'x')
        reader.close(); reader.close()
        self.assertTrue(legacy.closed)
        self.assertEqual(legacy.readers, 0)

    def test_move_requires_same_factory_and_publication_destination(self):
        from geoai.storage import windows_io
        from geoai.storage.native_io import StorageIOError
        source = self.root()
        destination = self.root('publication', 'output')
        source.move_verified('x', destination, 'x', **self.options)
        self.assertEqual(source._legacy.calls[0][0], 'move')
        wrong = self.root('read', 'wrong')
        with self.assertRaisesRegex(StorageIOError, 'root_purpose_mismatch'):
            source.move_verified('x', wrong, 'x', **self.options)
        foreign = windows_io.WindowsIOFactory().open_registered_root('foreign', self.directory, purpose='publication')
        with self.assertRaisesRegex(StorageIOError, 'unregistered_root'):
            source.move_verified('x', foreign, 'x', **self.options)
        for root in (source, destination, wrong, foreign): root.close()


class NativeFactoryFailureUnitTests(_FactoryUnitFixture, unittest.TestCase):
    # New failure-path cases share the same explicit unit-only legacy adapter.
    def test_deadline_bounds_wait_for_busy_root(self):
        import threading, time
        from unittest.mock import patch
        from geoai.storage.native_io import StorageIOError
        self.clock_patch.stop()  # This test observes real timed lock acquisition.
        root = self.root()
        started, release = threading.Event(), threading.Event()
        original = root._legacy.open_read
        failures = []
        def delayed(path, **options):
            if path == 'slow':
                started.set()
                if not release.wait(2): raise RuntimeError('unit fixture stalled')
            return original(path, **options)
        def slow():
            try:
                with root.open_read('slow', **{**self.options,'deadline':time.monotonic()+5}): pass
            except BaseException as error: failures.append(error)
        with patch.object(root._legacy,'open_read',side_effect=delayed):
            worker=threading.Thread(target=slow)
            worker.start()
            self.assertTrue(started.wait(1))
            timer=threading.Timer(.4,release.set); timer.start()
            began=time.monotonic()
            try:
                with self.assertRaisesRegex(StorageIOError,'cancelled_or_deadline'):
                    root.open_read('fast', **{**self.options,'deadline':began+.02})
                elapsed=time.monotonic()-began
            finally:
                release.set(); timer.cancel(); worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertFalse(failures)
        self.assertLess(elapsed,.25)
        self.assertEqual(len(root._legacy.calls),1)
        root.close()

    def test_external_failed_open_releases_registered_root(self):
        from unittest.mock import patch
        from geoai.storage.native_io import ExternalRegistration, NativeIdentity, StorageIOError
        instances = []
        original = _UnitLegacyRoot.__init__
        def capture(root, path):
            original(root, path)
            instances.append(root)
        with patch.object(_UnitLegacyRoot, '__init__', capture), patch.object(
                _UnitLegacyRoot, 'open_read', side_effect=StorageIOError('content_mismatch')):
            with self.assertRaisesRegex(StorageIOError, 'content_mismatch'):
                self.factory.open_external(ExternalRegistration(self.directory/'x', NativeIdentity('v','f')), **self.options)
        self.assertTrue(instances[0].closed)
        self.assertFalse(self.factory._roots)

    def test_os_error_does_not_expose_native_path(self):
        from unittest.mock import patch
        from geoai.storage.native_io import StorageIOError
        root = self.root()
        with patch.object(root._legacy, 'ensure_directory', side_effect=PermissionError('/private/sentinel')):
            with self.assertRaises(StorageIOError) as raised:
                root.ensure_directory('x')
        self.assertEqual(str(raised.exception), 'native_io_failed')
        root.close()


import os


@unittest.skipUnless(os.name == 'nt', 'Windows registered factory native handles required')
class WindowsRegisteredFactoryNativeTests(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        import tempfile
        from geoai.storage.windows_io import WindowsIOFactory
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.factory = WindowsIOFactory()
        self.source = self.factory.open_registered_root('staging', self.path, purpose='staging')

    def tearDown(self):
        self.source.close()
        self.temp.cleanup()

    def options(self):
        import hashlib, time
        return dict(sha256=hashlib.sha256(b'payload').hexdigest(), size_bytes=7,
                    cancelled=lambda: False, deadline=time.monotonic()+10)

    def test_reader_denies_writes_and_root_release_until_closed(self):
        import time
        from geoai.storage.native_io import StorageIOError
        self.source.create_file('x', [b'payload'], max_bytes=7,
                                cancelled=lambda: False, deadline=time.monotonic()+10)
        with self.source.open_read('x', **self.options()) as reader:
            self.assertEqual(reader.read(), b'payload')
            self.assertEqual(reader.seek(0), 0)
            with self.assertRaises(OSError): (self.path/'x').write_bytes(b'changed')
            with self.assertRaisesRegex(StorageIOError, 'root_has_live_readers'): self.source.close()
        self.factory.require_root(self.source, purpose='staging')

    def test_external_registration_checks_expected_bytes_and_identity(self):
        import time
        from geoai.storage.native_io import ExternalRegistration, StorageIOError
        self.source.create_file('x', [b'payload'], max_bytes=7,
                                cancelled=lambda: False, deadline=time.monotonic()+10)
        with self.source.open_read('x', **self.options()) as reader: identity=reader.identity
        registration = ExternalRegistration(self.path/'x', identity)
        with self.factory.open_external(registration, **self.options()) as reader:
            self.assertEqual(reader.read(), b'payload')
        (self.path/'x').write_bytes(b'changed')
        with self.assertRaises(StorageIOError): self.factory.open_external(registration, **self.options())

    def test_expired_creation_never_writes_file(self):
        import time
        from geoai.storage.native_io import StorageIOError
        with self.assertRaises(StorageIOError):
            self.source.create_file('expired', [b'x'], max_bytes=1,
                                    cancelled=lambda: False, deadline=time.monotonic()-1)
        self.assertFalse((self.path/'expired').exists())
