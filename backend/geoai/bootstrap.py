"""Development-only anonymous stdio pipe handoff; no native owner or writer."""
import argparse
import asyncio
import logging
import os
import socket
import stat
import sys
import threading

import uvicorn

from geoai.api.app import create_app
from geoai.api.session import DEVELOPMENT_ORIGINS, PRODUCTION_ORIGINS, SanitizedLogFilter, SessionPolicy
from geoai.contracts import SessionDescriptor


async def serve(sock, policy):
    config = uvicorn.Config(create_app(policy), access_log=False, log_config=None, lifespan="off", timeout_graceful_shutdown=3)
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started and not task.done():
            await asyncio.sleep(0.01)
        if not server.started:
            await task
            raise RuntimeError("Local service unavailable")
        # The only secret-bearing output, permitted only to a trusted private pipe.
        descriptor = SessionDescriptor(base_url=f"http://127.0.0.1:{policy.port}", token=policy.token)
        sys.stdout.write(descriptor.model_dump_json() + "\n")
        sys.stdout.flush()

        def control_reader():
            # Parent owns this anonymous input pipe. EOF also requests clean stop.
            sys.stdin.buffer.readline(64)
            server.should_exit = True

        threading.Thread(target=control_reader, daemon=True).start()
        await task
    finally:
        server.should_exit = True
        if not task.done():
            await task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev-stdio-handoff", action="store_true")
    parser.add_argument("--no-console", action="store_true")
    args = parser.parse_args()
    if not (args.dev_stdio_handoff and args.no_console):
        parser.error("Native launcher unavailable; development requires both explicit flags")
    if any(stream.isatty() or not stat.S_ISFIFO(os.fstat(stream.fileno()).st_mode) for stream in (sys.stdin, sys.stdout)):
        parser.error("Private anonymous input/output pipes required; console/file handoff forbidden")
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(SanitizedLogFilter())
    logging.basicConfig(handlers=[handler], level=logging.WARNING, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        # Socket remains owned; Uvicorn receives it directly, without probe/rebind.
        sock.setblocking(False)
        policy = SessionPolicy(port=sock.getsockname()[1], allowed_origins=PRODUCTION_ORIGINS + DEVELOPMENT_ORIGINS, allow_missing_origin=True)
        asyncio.run(serve(sock, policy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
