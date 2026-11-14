"""Render the shipped card against isolated Home Assistant-style states."""
from datetime import datetime, timezone
import json
from pathlib import Path
import textwrap
from types import SimpleNamespace
import unittest

try:
    from jinja2 import Environment
except ImportError:
    Environment = None

CARD = Path(__file__).resolve().parents[1] / 'home-assistant/manufacturer-monitor.yaml'


def datetime_value(value, default=None):
    """Model HA datetime conversion without an installed HA server."""
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return default


def timestamp(value, default=None):
    """Convert valid timestamps while retaining unknown input as unknown."""
    parsed = datetime_value(value)
    return parsed.timestamp() if parsed else default


@unittest.skipIf(Environment is None, 'Optional jinja2 is required for dashboard rendering')
class ManufacturerDashboardTests(unittest.TestCase):
    """Verify actual template counters, metrics and live/retained run selection."""

    def setUp(self):
        """Create isolated registries and load the actual packaged template."""
        self.devices = {}
        self.entities = {}
        self.template = textwrap.dedent(CARD.read_text().split('content: |\n', 1)[1])

    def job(self, key, live='running', last='unknown', *, manufacturer='TimeShift-BTRFS-Sync',
            live_attrs=None, last_attrs=None, renamed=False, result=True):
        """Add one discovered job and its status/result/metric fixture entities."""
        self.devices[key] = {'manufacturer': manufacturer, 'name': key, 'name_by_user': None}
        shared = {'backup_name': key, 'run_id': key + '-new', 'started_at': '2026-11-13T10:00:00Z',
                  'total_snapshots': 4, 'completed_snapshots': 1, 'failed_snapshots': 0,
                  'skipped_snapshots': 0, 'data_transferred_bytes': 1073741824,
                  'runtime_seconds': 60, 'bytes_complete': True, 'current_snapshot': '2026-11-13_10-00-00',
                  'current_subvolume': '@home', 'phase': 'transfer', 'status': live,
                  'last_heartbeat': '2026-11-13T10:01:00Z'}
        self.entities[f'sensor.{key}_' + ('renamed_live' if renamed else 'status')] = {
            'device': key, 'state': live,
            'attributes': {**shared, 'friendly_name': key + ' Live status', **(live_attrs or {})}}
        if result:
            self.entities[f'sensor.{key}_' + ('renamed_result' if renamed else 'last_result')] = {
                'device': key, 'state': last,
                'attributes': {**shared, 'run_id': key + '-old', 'status': last,
                               'started_at': '2026-11-12T10:00:00Z', 'ended_at': '2026-11-12T10:01:00Z',
                               'exit_code': 0, 'friendly_name': key + ' Last result', **(last_attrs or {})}}
        self.entities[f'sensor.{key}_runtime_seconds'] = {'device': key, 'state': '60', 'attributes': {}}

    def render(self):
        """Execute the actual Jinja card through the HA APIs it references."""
        entities = self.entities
        class States:
            """Provide both states.sensor iteration and callable state lookup."""
            sensor = [SimpleNamespace(entity_id=eid) for eid in entities]
            def __call__(self, eid):
                """Return unknown for absent entities, matching HA state lookup."""
                return entities.get(eid, {}).get('state', 'unknown')
        def device_id(eid):
            """Resolve the registered device independently of the entity name."""
            return entities.get(eid, {}).get('device')
        def device_attr(identifier, attr):
            """Read device metadata for either a device ID or entity ID."""
            dev = identifier if identifier in self.devices else device_id(identifier)
            return self.devices.get(dev, {}).get(attr)
        def device_entities(dev):
            """Return every fixture entity associated with a discovered job."""
            return [eid for eid, value in entities.items() if value['device'] == dev]
        def state_attr(eid, attr):
            """Read real fixture attributes without inventing zero metrics."""
            return entities.get(eid, {}).get('attributes', {}).get(attr)
        environment = Environment()
        environment.globals.update(states=States(), device_id=device_id, device_attr=device_attr,
            device_entities=device_entities, state_attr=state_attr, as_timestamp=timestamp,
            as_datetime=datetime_value, as_local=lambda value: value.astimezone(timezone.utc))
        return environment.from_string(self.template).render()

    def test_manufacturer_filter_and_device_deduplication(self):
        """Include each Timeshift config once and exclude unrelated manufacturers."""
        self.job('timeshift'); self.job('other', manufacturer='Syncerate')
        result = self.render()
        self.assertIn('**1 backup job(s) discovered**', result)
        self.assertEqual(result.count('### 🟢 timeshift'), 1)
        self.assertNotIn('### 🟢 other', result)

    def test_summary_counts(self):
        """Count active, retained success/failure and unknown jobs separately."""
        self.job('running'); self.job('finished', live='unavailable', last='success')
        self.job('failed', live='unavailable', last='failure'); self.job('unknown', live='unknown')
        self.assertIn('| **1** | **1** | **1** | **1** |', self.render())

    def test_first_run_without_retained_entity(self):
        """Show a first live run before its result entity is present."""
        self.job('first', result=False)
        self.assertIn('### 🟢 first — RUNNING', self.render())

    def test_renamed_entity_ids(self):
        """Find renamed entities through their default friendly labels."""
        self.job('renamed', renamed=True)
        self.assertIn('### 🟢 renamed — RUNNING', self.render())

    def test_current_run_beats_prior_success(self):
        """Do not show an older completed result as the active run's outcome."""
        self.job('new', last='success')
        self.assertIn('### 🟢 new — RUNNING', self.render())

    def test_matching_result_beats_stale_running(self):
        """Handle a completion received before its live terminal update."""
        self.job('matching', last='success', last_attrs={'run_id': 'matching-new'})
        self.assertIn('### ✅ matching — SUCCESS', self.render())

    def test_newer_result_beats_older_live_run(self):
        """Use the later retained run instead of a delayed older live packet."""
        self.job('newer', last='success', last_attrs={'started_at': '2026-11-14T10:00:00Z'})
        self.assertIn('### ✅ newer — SUCCESS', self.render())

    def test_expired_unfinished_run_remains_unknown(self):
        """A lost newer heartbeat cannot inherit the old run's success."""
        self.job('lost', live='unavailable', last='success', live_attrs={'status': 'running'})
        result = self.render()
        self.assertIn('### 🟠 lost — HEARTBEAT LOST', result)
        self.assertIn('Its outcome is unknown', result)
        self.assertIn('It belongs to another run', result)

    def test_normal_idle_expiry_uses_matching_result(self):
        """Preserve a matching completed result through normal live expiry."""
        self.job('idle', live='unavailable', last='success', live_attrs={'status': 'running'},
                 last_attrs={'run_id': 'idle-new'})
        result = self.render()
        self.assertIn('### ✅ idle — SUCCESS', result)
        self.assertIn('Retained result from the last completed run', result)

    def test_unfinished_statuses_remain_distinct(self):
        """Keep incomplete/interrupted outcomes distinct from successful completion."""
        self.job('incomplete', live='incomplete'); self.job('interrupted', live='interrupted')
        result = self.render()
        self.assertIn('— INCOMPLETE', result); self.assertIn('— INTERRUPTED', result)
        self.assertIn('| **0** | **0** | **0** | **2** |', result)

    def test_unknown_metrics(self):
        """Display missing progress, byte and time measurements as unknown."""
        self.job('planning', live_attrs={key: None for key in ['total_snapshots', 'completed_snapshots',
            'failed_snapshots', 'skipped_snapshots', 'data_transferred_bytes', 'runtime_seconds']})
        result = self.render()
        for expected in ['**Progress:** Unknown', '**Items:** ? / ? completed · ? failed · ? skipped',
                         '**Confirmed transferred:** Unknown', '**Confirmed-byte average:** Unknown', '**Runtime:** Unknown']:
            self.assertIn(expected, result)

    def test_zero_total_has_no_invented_percentage(self):
        """Represent a no-op as zero selected transfers instead of fake 100 percent."""
        self.job('noop', live='success', live_attrs={'total_snapshots': 0, 'completed_snapshots': 0})
        result = self.render()
        self.assertIn('No transfers selected (0 / 0)', result)
        self.assertNotIn('**100%**', result)

    def test_snapshot_payload_and_partial_byte_metrics(self):
        """Read native Timeshift fields and explicitly label partial confirmed bytes."""
        self.job('partial', live_attrs={'bytes_complete': False})
        result = self.render()
        for expected in ['**Current snapshot:** 2026-11-13_10-00-00', '**Current payload:** @home', '**25%**',
                         '1.00 GiB (partial; some payload sizes unknown)', '**Confirmed-byte average:** 17.07 MiB/s',
                         '**Runtime:** 00:01:00']:
            self.assertIn(expected, result)

    def test_zero_runtime_average_is_unknown(self):
        """Avoid dividing by zero at the start of a run."""
        self.job('start', live_attrs={'runtime_seconds': 0})
        self.assertIn('**Confirmed-byte average:** Unknown', self.render())

    def test_actual_error_and_finish_fields(self):
        """Format ended_at and exit code while escaping HTML in error text."""
        self.job('error', live='failed', live_attrs={'error': '<bad>\nreceive failed', 'exit_code': 1,
            'ended_at': '2026-11-13T10:01:00Z'})
        result = self.render()
        for expected in ['**Last error:** &lt;bad&gt; receive failed', '**Exit code:** 1',
                         '**Finished:** 2026-11-13 10:01']:
            self.assertIn(expected, result)

    def test_user_device_name(self):
        """Respect the user's HA device name while grouping by manufacturer."""
        self.job('renamed'); self.devices['renamed']['name_by_user'] = 'My desktop'
        self.assertIn('### 🟢 My desktop — RUNNING', self.render())

    def test_empty_dashboard_setup_hint(self):
        """Explain the monitoring/discovery requirements when no jobs are present."""
        result = self.render()
        self.assertIn('**0 backup job(s) discovered**', result)
        self.assertIn('**No matching backup devices detected for TimeShift-BTRFS-Sync.**', result)
        self.assertIn('discovery = true', result)

    def test_last_success_remains_visible_during_later_failure(self):
        """Use the independent retained success sensor after a newer run fails."""
        self.job('history', live='failed', last='failed')
        self.entities['sensor.history_last_success'] = {'device': 'history',
            'state': '2026-11-10T10:01:00Z', 'attributes': {
                'friendly_name': 'Last successful run', 'ended_at': '2026-11-10T10:01:00Z'}}
        result = self.render()
        self.assertIn('### 🔴 history — FAILED', result)
        self.assertIn('**Last successful run:** 2026-11-10 10:01', result)

    def test_actual_stream_measurement_labels(self):
        """Distinguish active cumulative byte measurement from legacy confirmed totals."""
        self.job('measured', live_attrs={'byte_measurement': 'actual send stream'})
        result = self.render()
        self.assertIn('**Transferred so far:** 1.00 GiB', result)
        self.assertIn('**Run average speed:** 17.07 MiB/s', result)

    def test_last_success_fallback_to_existing_successful_result(self):
        """Show an existing retained success before the new success entity has data."""
        self.job('upgrade', live='unavailable', last='success')
        self.assertIn('**Last successful run:** 2026-11-12 10:01', self.render())

    def test_only_manufacturer_variable_selects_multiple_jobs(self):
        """One card value selects all jobs in a custom group without leaking other groups."""
        self.job('desktop', manufacturer='My backups', live_attrs={'runtime_seconds': 10})
        self.job('server', manufacturer='My backups', live='unavailable', last='success',
                 last_attrs={'runtime_seconds': 1800})
        self.job('excluded', manufacturer='Other backups')
        self.template = self.template.replace("set manufacturer = 'TimeShift-BTRFS-Sync'", "set manufacturer = 'My backups'", 1)
        result = self.render()
        self.assertIn('## My backups — Backup Monitor', result)
        self.assertIn('**2 backup job(s) discovered**', result)
        self.assertIn('### 🟢 desktop', result)
        self.assertIn('### ✅ server', result)
        self.assertNotIn('### 🟢 excluded', result)
        self.assertIn('| **1** | **1** | **0** | **0** |', result)
        self.assertIn('**Runtime:** 00:00:10', result)
        self.assertIn('**Runtime:** 00:30:00', result)

    def test_explicit_roles_survive_fully_renamed_entities(self):
        """Find roles even after both entity IDs and friendly names are user-renamed."""
        self.job('renamed', last='success')
        for old, new, role in [('sensor.renamed_status', 'sensor.anything_a', 'status'),
                               ('sensor.renamed_last_result', 'sensor.anything_b', 'last_result')]:
            entity = self.entities.pop(old)
            entity['attributes'].update(friendly_name='Unrelated label', live_preview_role=role)
            self.entities[new] = entity
        self.assertIn('### 🟢 renamed — RUNNING', self.render())

    def test_role_metadata_takes_priority_over_suffix_lookalike(self):
        """Do not let a similarly named unrelated metric replace explicit status data."""
        self.job('real')
        self.entities['sensor.real_status']['attributes']['live_preview_role'] = 'status'
        self.entities['sensor.decoy_status'] = {'device': 'real', 'state': 'failed',
            'attributes': {'friendly_name': 'Decoy status'}}
        self.assertIn('### 🟢 real — RUNNING', self.render())

    def test_manufacturer_match_is_exact_and_uses_device_registry(self):
        """A payload claiming another manufacturer cannot cross the registry filter."""
        self.job('wrongcase', manufacturer='timeshift-btrfs-sync')
        self.job('spoofed', manufacturer='Other', live_attrs={'manufacturer': 'TimeShift-BTRFS-Sync'})
        self.assertIn('**0 backup job(s) discovered**', self.render())

    def test_compatible_dataset_script_uses_its_own_metrics(self):
        """Read a grouped dataset-style job without editing fields in the card."""
        self.job('dataset')
        attrs = self.entities['sensor.dataset_status']['attributes']
        for key in ['total_snapshots', 'completed_snapshots', 'failed_snapshots', 'skipped_snapshots', 'current_snapshot', 'current_subvolume']:
            attrs.pop(key)
        attrs.update(total_datasets=8, completed_datasets=2, failed_datasets=1,
                     skipped_datasets=0, current_dataset='tank/data')
        result = self.render()
        self.assertIn('**Current dataset:** tank/data', result)
        self.assertIn('**Datasets:** 2 / 8 completed · 1 failed · 0 skipped', result)
        self.assertIn('**25%**', result)

    def test_compatible_generic_job_uses_its_own_units_and_time(self):
        """Render generic task metrics and finished_at from compatible external scripts."""
        self.job('generic', live='success')
        attrs = self.entities['sensor.generic_status']['attributes']
        for key in ['total_snapshots', 'completed_snapshots', 'failed_snapshots', 'skipped_snapshots', 'current_snapshot', 'current_subvolume', 'data_transferred_bytes']:
            attrs.pop(key)
        attrs.update(total=5, completed=5, failed=0, skipped=0, item_unit='tasks',
                     transferred_bytes=1048576, finished_at='2026-11-13T10:01:00Z')
        result = self.render()
        self.assertIn('**Tasks:** 5 / 5 completed · 0 failed · 0 skipped', result)
        self.assertIn('**Finished:** 2026-11-13 10:01', result)

    def test_discovery_role_templates_preserve_metric_attributes(self):
        """Inject stable HA roles while retaining every incoming measurement field."""
        from timeshift_btrfs_sync.monitor import MonitorConfig, discovery_messages
        messages = discovery_messages(MonitorConfig(manufacturer='Shared backups'), 'job', 'Backup', 'x/status', 'x/last_result')
        source = {'status': 'success', 'run_id': 'run-1', 'total_snapshots': 4,
                  'runtime_seconds': 60, 'ended_at': '2026-11-13T10:01:00Z'}
        found = set()
        for topic, body, retained in messages:
            if 'json_attributes_template' in body:
                role = topic.split('/')[-2]
                rendered = Environment().from_string(body['json_attributes_template']).render(value_json=source)
                attributes = json.loads(rendered)
                self.assertEqual(attributes, {**source, 'live_preview_role': role})
                found.add(role)
        self.assertEqual(found, {'status', 'last_result', 'last_success'})


    def test_cleanup_and_overall_bars_read_native_counters(self):
        """Display the actual cleanup date, ordinal, confirmed counts and combined steps."""
        self.job('cleanup', live_attrs={'cleanup_enabled': True, 'cleanup_status': 'running',
            'cleanup_total': 4, 'cleanup_completed': 2, 'cleanup_processed': 3, 'cleanup_blocked': 1,
            'cleanup_current_snapshot': 'old-date', 'cleanup_current_group': 'paired', 'cleanup_current_number': 4,
            'overall_total_steps': 8, 'overall_completed_steps': 3})
        result = self.render()
        for expected in ['**Overall steps:** 3 / 8 completed', '**37%**', '**50%**',
                         '**Snapshot cleanup jobs:** 2 / 4 confirmed · 3 evaluated · 1 blocked / unconfirmed',
                         '**Current cleanup:** paired — old-date (item 4 / 4)']:
            self.assertIn(expected, result)

    def test_cleanup_estimate_and_changed_total_are_explicit(self):
        """Keep the first estimate visible beside a changed current expectation."""
        self.job('forecast', live_attrs={'cleanup_enabled': True, 'cleanup_status': 'estimated',
            'cleanup_total': 3, 'cleanup_completed': 0, 'cleanup_initial_total': 5,
            'cleanup_initial_plan_estimated': True, 'cleanup_plan_estimated': True,
            'overall_plan_estimated': True, 'overall_total_steps': 7, 'overall_completed_steps': 1})
        result = self.render()
        self.assertIn('**Cleanup progress** (estimate): estimated', result)
        self.assertIn('**Initial estimate:** 5 cleanup jobs · **Current expected:** 3', result)
        self.assertIn('**Overall progress** (estimate):', result)

    def test_cleanup_unknown_and_noop_have_no_invented_completion(self):
        """Unknown plans and known empty plans have separate truthful representations."""
        self.job('unknown-cleanup', live_attrs={'cleanup_enabled': True, 'cleanup_total': None,
            'cleanup_completed': 0, 'overall_total_steps': None, 'overall_completed_steps': 1})
        self.job('empty-cleanup', live_attrs={'cleanup_enabled': True, 'cleanup_total': 0,
            'cleanup_completed': 0, 'total_snapshots': 0, 'completed_snapshots': 0,
            'overall_total_steps': 0, 'overall_completed_steps': 0})
        result = self.render()
        self.assertIn('**Snapshot cleanup jobs:** 0 / ? confirmed', result)
        self.assertIn('No cleanup jobs selected (0 / 0)', result)
        self.assertIn('No work selected (0 / 0)', result)
        self.assertNotIn('**100%**', result)

    def test_disabled_cleanup_and_older_scripts_are_supported(self):
        """The same manufacturer card remains usable when cleanup metrics are absent."""
        self.job('disabled', live_attrs={'cleanup_enabled': False})
        self.job('legacy')
        result = self.render()
        self.assertEqual(result.count('**Cleanup:** Not requested.'), 1)
        self.assertNotIn('**Snapshot cleanup jobs:**', result)

    def test_fractional_progress_never_rounds_incomplete_work_to_100(self):
        """Large queues cannot show full bars while their last item is still pending."""
        self.job('large', live_attrs={'cleanup_enabled': True, 'cleanup_total': 1000,
            'cleanup_completed': 999, 'overall_total_steps': 1000, 'overall_completed_steps': 999,
            'total_snapshots': 1000, 'completed_snapshots': 999})
        result = self.render()
        self.assertEqual(result.count('**99%**'), 3)
        self.assertNotIn('**100%**', result)

    def test_retained_cleanup_result_displays_after_live_expiry(self):
        """Finished cleanup and overall counters are read from the durable run result."""
        self.job('finished', live='unavailable', last='success', last_attrs={'cleanup_enabled': True,
            'cleanup_status': 'complete', 'cleanup_total': 2, 'cleanup_completed': 2,
            'overall_total_steps': 6, 'overall_completed_steps': 6})
        result = self.render()
        self.assertIn('**Overall steps:** 6 / 6 completed', result)
        self.assertIn('**Snapshot cleanup jobs:** 2 / 2 confirmed', result)


if __name__ == '__main__':
    unittest.main()
