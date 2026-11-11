import unittest


class NativeSharedTypesTests(unittest.TestCase):
    def test_windows_reexports_shared_identity_and_error(self):
        from geoai.storage.native_io import NativeIdentity, StorageIOError
        from geoai.storage import windows_io
        self.assertIs(windows_io.NativeIdentity, NativeIdentity)
        self.assertIs(windows_io.StorageIOError, StorageIOError)
        self.assertEqual(NativeIdentity('volume', 'file'), NativeIdentity('volume', 'file'))
        self.assertEqual(StorageIOError('reason').code, 'reason')
