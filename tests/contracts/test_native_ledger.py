"""Private ledger shape/codec checks; metadata does not establish OS authority."""
from copy import deepcopy
import json
from pathlib import Path
import unittest


class NativeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads((Path(__file__).parents[1]/'fixtures/contracts/native-ledger.json').read_text())['LinuxOwnerLedger']

    def decode(self,value):
        from geoai.contracts.native import decode_ledger
        return decode_ledger(json.dumps(value,separators=(',',':')).encode()+b'\n')

    def test_roundtrip_and_private_registry_only(self):
        from geoai import contracts
        from geoai.contracts.native import LinuxOwnerLedger,encode_ledger,decode_ledger
        value=self.decode(self.fixture)
        self.assertEqual(decode_ledger(encode_ledger(value)),value)
        self.assertTrue(encode_ledger(value).endswith(b'\n'))
        self.assertIn('LinuxOwnerLedger',contracts.PRIVATE_NATIVE_MODELS)
        self.assertIn('LinuxOwnerGeneration',contracts.PRIVATE_NATIVE_MODELS)
        self.assertNotIn('LinuxOwnerLedger',contracts.CONTRACT_MODELS)
        self.assertNotIn('LinuxOwnerLedger',contracts.WIRE_MODELS)
        self.assertNotIn('LinuxOwnerLedger',contracts.PRIVATE_CONTEXT_MODELS)

    def test_invalid_versions_fields_and_naive_time(self):
        for changes in [{'schema_version':'1.0.0'},{'unknown':True},{'created_at':'2026-11-11T00:00:00'}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError): self.decode({**self.fixture,**changes})

    def test_epochs_are_positive_strict_and_watermark_covers_history(self):
        for epoch in [0,True,'7']:
            value=deepcopy(self.fixture);value['generations'][0]['owner_epoch']=epoch
            with self.subTest(epoch=epoch),self.assertRaises(ValueError):self.decode(value)
        for high in [0,True,6]:
            with self.subTest(high=high),self.assertRaises(ValueError):self.decode({**self.fixture,'epoch_high_watermark':high})

    def test_duplicate_owner_or_epoch_rejected(self):
        for changes in [{'owner_epoch':6},{'owner_id':'owner:other'}]:
            value=deepcopy(self.fixture);value['generations'].append({**value['generations'][0],**changes})
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.decode(value)

    def test_record_budget_is_separate_from_encoded_byte_budget(self):
        value=deepcopy(self.fixture);first=value['generations'][0]
        value['generations']=[{**first,'owner_id':f'owner:{i}','owner_epoch':i} for i in range(1,1025)]
        value['epoch_high_watermark']=1024
        from geoai.contracts.native import encode_ledger
        self.assertLess(len(encode_ledger(self.decode(value))),1048576)
        value['generations'].append({**first,'owner_id':'owner:1025','owner_epoch':1025})
        value['epoch_high_watermark']=1025
        with self.assertRaises(ValueError):self.decode(value)
        with self.assertRaises(ValueError):self.decode({**self.fixture,'generations':[]})

    def test_inclusive_byte_limit_and_lf(self):
        from geoai.contracts.native import decode_ledger,encode_ledger,LinuxOwnerLedger
        raw=json.dumps(self.fixture,separators=(',',':')).encode()+b'\n'
        exact=b'{'+b' '*(1048576-len(raw))+raw[1:]
        self.assertEqual(len(exact),1048576)
        self.assertEqual(decode_ledger(exact),self.decode(self.fixture))
        with self.assertRaises(ValueError):decode_ledger(b'{ '+exact[1:])
        for invalid in [raw[:-1],raw+b'\n',raw[:-1]+b'\r\n',raw[:-1]+b'{}\n']:
            with self.subTest(length=len(invalid)),self.assertRaises(ValueError):decode_ledger(invalid)
        huge=deepcopy(self.fixture);huge['generations'][0]['project_root_identity']['file_id']='x'*1048576
        with self.assertRaises(ValueError):encode_ledger(LinuxOwnerLedger.model_validate(huge))

    def test_strict_json_duplicate_keys_nan_and_invalid_utf8(self):
        from geoai.contracts.native import decode_ledger
        raw=json.dumps(self.fixture,separators=(',',':')).encode()+b'\n'
        for invalid in [raw.replace(b'"epoch_high_watermark":7',b'"epoch_high_watermark":NaN'),
                        raw.replace(b'"epoch_high_watermark":7',b'"epoch_high_watermark":7,"epoch_high_watermark":7'),
                        b'\xff\n',raw.replace(b'linux-dev:1',b'\\ud800')]:
            with self.assertRaises(ValueError):decode_ledger(invalid)

    def test_generation_paths_and_identities_are_metadata_only(self):
        for path in ['relative','/a/../geoai-execution.service','//user/geoai-execution.service','/a//geoai-execution.service','/a/geoai-execution.service/','/a/\x00/geoai-execution.service']:
            value=deepcopy(self.fixture);value['generations'][0]['cgroup_path']=path
            with self.subTest(path=path),self.assertRaises(ValueError):self.decode(value)
