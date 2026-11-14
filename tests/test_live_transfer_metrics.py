"""Real subprocess byte-stream checks and isolated whole-run monitor accounting."""
import contextlib
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import cli, commands, monitor, sync
from timeshift_btrfs_sync.config import ConfigError, load_config
from timeshift_btrfs_sync.sync import _terminal_destination_receive_failure_reason

TEMPLATE = Path(__file__).parents[1] / 'timeshift_btrfs_sync/data/example-config-local-backup.toml'
DATA = bytes(range(256)) * 4096


class StreamMeasurementTests(unittest.TestCase):
    """Check binary preservation, live updates, failure and cancellation with real pipes."""
    def producer(self, slow=False):
        """Emit a known binary Btrfs-stream stand-in, optionally in delayed blocks."""
        text = "import sys,time; block=bytes(range(256))*256; "
        text += "[(sys.stdout.buffer.write(block),sys.stdout.buffer.flush(),time.sleep(.02)) for _ in range(16)]" if slow else "sys.stdout.buffer.write(block*16)"
        return [sys.executable, '-c', text]

    def receiver(self):
        """Verify every received byte through a SHA-256 assertion in the child."""
        return [sys.executable, '-c', "import sys,hashlib; data=sys.stdin.buffer.read(); assert hashlib.sha256(data).hexdigest()==" + repr(hashlib.sha256(DATA).hexdigest())]

    def test_direct_send_reports_active_exact_bytes(self):
        """Measure an active Btrfs-send-style stdout stream before its producer exits."""
        progress = []
        result = commands.stream_pipeline(self.producer(True), self.receiver(), verbose=False,
                                         progress_callback=progress.append, progress_interval=.01)
        self.assertEqual(result.transferred_bytes, len(DATA))
        self.assertEqual(result.transferred_bytes_source, 'btrfs-send-stream')
        self.assertTrue(any(0 < value < len(DATA) for value in progress))
        self.assertEqual(progress, sorted(progress)); self.assertEqual(progress[-1], len(DATA))

    def test_mbuffer_output_counts_stream_not_rounded_diagnostics(self):
        """Count actual buffer output even when stderr totals are rounded or absent."""
        middle = [sys.executable, '-c', "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()); print('summary: 2 MiByte in 1 sec',file=sys.stderr)"]
        result = commands.stream_pipeline(self.producer(), self.receiver(), middle_cmd=middle,
                                         verbose=False, progress_callback=lambda value: None)
        self.assertEqual(result.transferred_bytes, len(DATA))
        self.assertEqual(result.transferred_bytes_source, 'mbuffer-output')

    @unittest.skipUnless(shutil.which('mbuffer'), 'mbuffer is not installed')
    def test_installed_mbuffer_binary_stream(self):
        """Exercise the installed optional buffer with a real binary producer/consumer."""
        result = commands.stream_pipeline(self.producer(), self.receiver(), middle_cmd=['mbuffer', '-q', '-m', '1M'],
                                         verbose=False, progress_callback=lambda value: None)
        self.assertEqual(result.transferred_bytes, len(DATA))

    def test_copy_fallback_preserves_binary_stream(self):
        """Retain exact bytes where kernel splice is unavailable."""
        with patch.object(commands.os, 'splice', None):
            result = commands.stream_pipeline(self.producer(), self.receiver(), verbose=False,
                                             progress_callback=lambda value: None)
        self.assertEqual(result.transferred_bytes, len(DATA))

    def test_observer_failure_cannot_break_transfer(self):
        """Monitoring callbacks remain non-authoritative for successful storage I/O."""
        def broken(value):
            """Model an unavailable observer while leaving the actual stream intact."""
            raise RuntimeError('observer unavailable')
        result = commands.stream_pipeline(self.producer(), self.receiver(), verbose=False, progress_callback=broken)
        self.assertEqual(result.transferred_bytes, len(DATA))

    def test_zero_byte_stream(self):
        """Distinguish a measured empty stream from missing measurement."""
        result = commands.stream_pipeline([sys.executable, '-c', 'pass'],
            [sys.executable, '-c', 'import sys; assert not sys.stdin.buffer.read()'],
            verbose=False, progress_callback=lambda value: None)
        self.assertEqual(result.transferred_bytes, 0)

    def test_receive_failure_keeps_storage_diagnostic(self):
        """Keep existing ENOSPC refusal/recovery semantics while metering a stream."""
        receiver = [sys.executable, '-c', "import sys; sys.stdin.buffer.read(); print('No space left on device',file=sys.stderr); sys.exit(1)"]
        with self.assertRaises(commands.CommandError) as caught:
            commands.stream_pipeline(self.producer(), receiver, verbose=False, progress_callback=lambda value: None)
        self.assertEqual(caught.exception.stage_returncodes['receive'], 1)
        self.assertEqual(_terminal_destination_receive_failure_reason(caught.exception), 'destination reported no allocatable space (ENOSPC)')

    def test_early_receiver_exit_cannot_be_successful_truncation(self):
        """Fail if a consumer closes its pipe before the measured stream is relayed."""
        with self.assertRaises(commands.CommandError):
            commands.stream_pipeline(self.producer(), [sys.executable, '-c', 'pass'],
                                     verbose=False, progress_callback=lambda value: None)

    def test_interrupt_reaps_all_pipeline_processes(self):
        """Cancellation closes the relay and reaps producer, buffer and receiver."""
        processes = []; factory = subprocess.Popen
        def record(*args, **kwargs):
            """Track actual process objects for post-interruption cleanup assertions."""
            process = factory(*args, **kwargs); processes.append(process); return process
        with patch.object(commands.subprocess, 'Popen', side_effect=record), patch.object(commands.os, 'splice', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                commands.stream_pipeline(self.producer(True), self.receiver(),
                    middle_cmd=[sys.executable, '-c', 'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                    verbose=False, progress_callback=lambda value: None)
        self.assertEqual(len(processes), 3)
        self.assertTrue(all(process.poll() is not None for process in processes))


class WholeRunMeasurementTests(unittest.TestCase):
    """Check cumulative physical traffic, wall runtime and durable last-success results."""
    def setUp(self):
        """Use the real validated profile without connecting to any external service."""
        self.config = load_config(TEMPLATE)
        self.config.mqtt_monitor.enabled = True
        self.config.mqtt_monitor.discovery = False

    def test_retries_accumulate_and_snapshot_updates_do_not_reset_bytes(self):
        """Count attempted bytes once even when a snapshot retry invalidates completion."""
        run = monitor.LiveMonitor(self.config, '/jobs/test.toml', started_monotonic=10)
        with patch.object(monitor.time, 'monotonic', return_value=20):
            first = run.begin_transfer(); first(100); first(100); first(150)
            second = run.begin_transfer(); second(50); first(999)
            run.update({'data_transferred_bytes': 0, 'bytes_complete': False})
            payload = run.payload()
        self.assertEqual(payload['data_transferred_bytes'], 200)
        self.assertEqual(payload['average_speed_bytes_per_second'], 20)
        self.assertEqual(payload['runtime_seconds'], 10)
        self.assertTrue(payload['bytes_complete'])

    def test_average_uses_whole_cli_elapsed_and_updates_each_heartbeat(self):
        """Divide total stream bytes by elapsed startup/inventory/transfer/cleanup time."""
        run = monitor.LiveMonitor(self.config, '/jobs/test.toml', started_monotonic=5)
        run.begin_transfer()(1000)
        with patch.object(monitor.time, 'monotonic', return_value=15):
            self.assertEqual(run.payload()['average_speed_bytes_per_second'], 100)
        with patch.object(monitor.time, 'monotonic', return_value=25):
            self.assertEqual(run.payload()['average_speed_bytes_per_second'], 50)
        run.ended_monotonic = 30
        with patch.object(monitor.time, 'monotonic', return_value=100):
            self.assertEqual(run.payload()['runtime_seconds'], 25)

    def test_last_success_survives_a_later_failure(self):
        """Only successful final runs replace the retained success topic."""
        retained = {}
        def publish(broker, messages, **kwargs):
            """Model retained broker storage without any socket connection."""
            for topic, payload, retain in messages:
                if retain:
                    retained[topic] = dict(payload)
        with patch.object(monitor, 'publish_messages', side_effect=publish):
            with monitor.LiveMonitor(self.config, '/jobs/test.toml') as success:
                success.begin_transfer()(100)
            success_topic = success.base + '/last_success'
            self.assertEqual(retained[success_topic]['status'], 'success')
            first = retained[success_topic]
            with self.assertRaisesRegex(RuntimeError, 'receive failed'):
                with monitor.LiveMonitor(self.config, '/jobs/test.toml') as failure:
                    failure.begin_transfer()(20)
                    raise RuntimeError('receive failed')
        self.assertEqual(retained[success_topic], first)
        self.assertEqual(retained[failure.base + '/last_result']['status'], 'failed')

    def test_last_success_sensor_is_retained_and_does_not_expire(self):
        """Expose a stable timestamp/attributes sensor for every discovered backup job."""
        messages = monitor.discovery_messages(self.config.mqtt_monitor, 'job', 'Backup', 'base/status', 'base/last_result')
        last_success = next(body for topic, body, retain in messages if topic.endswith('/last_success/config'))
        self.assertEqual(last_success['state_topic'], 'base/last_success')
        self.assertEqual(last_success['device_class'], 'timestamp')
        self.assertNotIn('expire_after', last_success)

    def test_disabled_byte_measurement_preserves_legacy_totals(self):
        """Allow monitoring without inserting a stream meter into the pipeline."""
        self.config.mqtt_monitor.measure_transfers = False
        run = monitor.LiveMonitor(self.config, '/jobs/test.toml')
        run.update({'data_transferred_bytes': 123, 'bytes_complete': False})
        self.assertEqual(run.payload()['data_transferred_bytes'], 123)
        token = monitor._ACTIVE.set(run)
        try:
            self.assertIsNone(monitor.transfer_reporter())
        finally:
            monitor._ACTIVE.reset(token)

    def test_new_measurement_options_are_strict(self):
        """Reject mistyped enablement and nonpositive/noninteger callback intervals."""
        for setting in ['measure_transfers="true"', 'progress_interval=true',
                        'progress_interval=0', 'progress_interval=1.5']:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'invalid.toml'
                path.write_text('[source]\nmode="local"\nsnapshot_root="/source"\n'
                    '[destination]\ntarget_root="/target"\n[mqtt_monitor]\n' + setting)
                with self.subTest(setting=setting), self.assertRaises(ConfigError):
                    load_config(path)

    def test_cli_runtime_includes_config_and_final_notifications(self):
        """Measure from CLI entry, not just monitor creation or snapshot sends."""
        messages = []
        with tempfile.TemporaryDirectory() as tmp:
            self.config.lock_file = Path(tmp) / 'job.lock'
            self.config.log_dir = None
            def load(path):
                """Model setup work that occurs before lock and monitor acquisition."""
                time.sleep(.04)
                return self.config
            def work(*args, **kwargs):
                """Model backup work under the actual local lock."""
                time.sleep(.02)
                return sync.SyncRunSummary(0, [], False, 0, 0)
            def notify(*args, **kwargs):
                """Model completion-notification time after backup work returns."""
                time.sleep(.03)
            def publish(broker, batch, **kwargs):
                """Capture actual monitor payloads without connecting to a broker."""
                messages.extend(batch)
            with patch.object(cli, 'load_config', side_effect=load), patch.object(cli, 'prepare_lock_path'), \
                    patch.object(cli, 'sync_once', side_effect=work), patch.object(cli, '_send_notifications', side_effect=notify), \
                    patch.object(monitor, 'publish_messages', side_effect=publish), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(['sync', '--config', str(Path(tmp) / 'config.toml'), '--run']), 0)
        final = next(payload for topic, payload, retain in messages if topic.endswith('/last_result'))
        self.assertGreaterEqual(final['runtime_seconds'], .08)


if __name__ == '__main__':
    unittest.main()
