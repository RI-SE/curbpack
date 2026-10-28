"""make stop ends the process that is listening on the Studio port."""

from __future__ import annotations

import socket
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from scripts.stop_app import pids_from_lsof, pids_from_netstat, pids_from_ss, stop_listener


ROOT = Path(__file__).resolve().parents[1]


class StopAppParseTest(unittest.TestCase):
    def test_lsof_ss_and_netstat_name_the_listener(self):
        self.assertEqual(pids_from_lsof("94281\n"), [94281])
        self.assertEqual(
            pids_from_ss('LISTEN 0 5 127.0.0.1:8770 0.0.0.0:* users:(("Python",pid=94281,fd=6))'),
            [94281],
        )
        netstat = "  TCP    127.0.0.1:8770    0.0.0.0:0    LISTENING    94281\n"
        self.assertEqual(pids_from_netstat(netstat, 8770), [94281])
        self.assertEqual(pids_from_netstat(netstat, 80), [])


class StopAppTest(unittest.TestCase):
    def test_stop_ends_a_listener_and_a_free_port_stays_quiet(self):
        held = socket.socket()
        held.bind(("127.0.0.1", 0))
        port = held.getsockname()[1]
        held.close()
        server = textwrap.dedent(
            f"""
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
            httpd = ThreadingHTTPServer(("127.0.0.1", {port}), BaseHTTPRequestHandler)
            print({port}, flush=True)
            httpd.serve_forever()
            """
        )
        process = subprocess.Popen(
            [sys.executable, "-c", server],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(process.stdout.close)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        line = process.stdout.readline()
        self.assertEqual(line.strip(), str(port))
        stop_listener(port)
        process.wait(timeout=5)
        self.assertIsNotNone(process.poll())
        stop_listener(port)
        self.assertIsNotNone(process.poll())


class MakeStopTest(unittest.TestCase):
    def test_make_stop_exits_when_nothing_is_listening(self):
        held = socket.socket()
        held.bind(("127.0.0.1", 0))
        port = held.getsockname()[1]
        held.close()
        result = subprocess.run(
            ["make", "stop", f"PORT={port}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Nothing is listening on port {port}.", result.stdout)
