"""A controlled single RPC child for portable transport tests, not native proof."""
import subprocess
import sys
import threading
import time


WORKER = '''
import json,sys
for line in sys.stdin:
    value=json.loads(line)
    result={'protocol_version':'0.1.0','schema_version':'0.1.0'} if value['method']=='capabilities' else {'accepted':True}
    print(json.dumps({'jsonrpc':'2.0','id':value['id'],'result':result}),flush=True)
    if value['method']=='shutdown': break
'''


class UnitChild:
    def __init__(self):
        self.child=subprocess.Popen([sys.executable,'-u','-c',WORKER],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        self.stdin,self.stdout,self.stderr=self.child.stdin,self.child.stdout,self.child.stderr
        self.pid=self.child.pid; self.stderr_bytes_seen=0; self._drain=None

    def start_stderr_drain(self,max_count=65536):
        def drain():
            for block in iter(lambda:self.stderr.read(4096),b''):
                self.stderr_bytes_seen=min(max_count,self.stderr_bytes_seen+len(block))
        self._drain=threading.Thread(target=drain,daemon=True); self._drain.start()

    def wait(self,deadline):
        try: self.child.wait(timeout=max(0,deadline-time.monotonic())); return True
        except subprocess.TimeoutExpired: return False

    def group_stopped(self,deadline):
        # Fixture creates no descendants. This is not a Linux cgroup observer.
        return self.wait(deadline)

    def terminate_group(self,deadline):
        if self.child.poll() is None: self.child.kill()
        if not self.wait(deadline): return False
        self.close(); return True

    def close(self):
        if self.child.poll() is None: raise RuntimeError('unit child still alive')
        if self._drain: self._drain.join(1)
        for stream in (self.stdin,self.stdout,self.stderr): stream.close()


class UnitFactory:
    def launch_worker(self,executable,packet,*,owner,deadline):
        return UnitChild()
