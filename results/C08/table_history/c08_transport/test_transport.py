import hashlib,json,tempfile,unittest
from pathlib import Path
import compactar_arquivo as c

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.data=b''.join(hashlib.sha256(str(i).encode()).digest() for i in range(10000))+bytes(10000)
        self.source=self.root/'source.npz';self.source.write_bytes(self.data)
    def pack(self,name='parts'):
        return c.pack(self.source,self.root/name,expected_sha256=c.digest(self.source),maximum_part_bytes=8192)
    def test_deterministic_bounded_exact_roundtrip(self):
        a=self.pack();b=self.pack('again');self.assertEqual(a,b)
        self.assertGreater(len(a['parts']),1);self.assertTrue(all(p['bytes']<=8192 for p in a['parts']))
        c.unpack(self.root/'parts',self.root/'restored.npz');self.assertEqual((self.root/'restored.npz').read_bytes(),self.data)
        self.assertEqual(self.source.read_bytes(),self.data)
        with self.assertRaises(ValueError):c.unpack(self.root/'parts',self.root/'restored.npz')
    def test_wrong_expected_source_and_corrupted_part(self):
        with self.assertRaisesRegex(ValueError,'approved SHA256'):c.pack(self.source,self.root/'wrong',expected_sha256='0'*64)
        self.assertFalse((self.root/'wrong').exists());m=self.pack()
        p=self.root/'parts'/m['parts'][0]['file'];v=bytearray(p.read_bytes());v[100]^=1;p.write_bytes(v)
        with self.assertRaisesRegex(ValueError,'Part SHA256'):c.unpack(self.root/'parts',self.root/'bad.npz')
        self.assertFalse((self.root/'bad.npz').exists())
    def test_path_and_decompression_size_guards(self):
        m=self.pack();manifest=self.root/'parts/manifest.json'
        with self.assertRaisesRegex(ValueError,'original length'):c.unpack(self.root/'parts',self.root/'small',maximum_output_bytes=1024)
        m['parts'][0]['file']='../outside';manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'sequence/path'):c.unpack(self.root/'parts',self.root/'bad')
        m['parts'][0]['file']='payload.gz.part0000';m['original_bytes']=1000;manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'exceeds declared'):c.unpack(self.root/'parts',self.root/'bad')
        self.assertFalse((self.root/'bad').exists())

if __name__=='__main__':unittest.main(verbosity=2)
