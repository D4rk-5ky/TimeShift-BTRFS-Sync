"""Regressions for dynamic snapshot totals and independent MQTT monitoring."""
from __future__ import annotations
import contextlib, io, json, shlex, tempfile, threading, time, types, unittest, uuid
from pathlib import Path
from unittest.mock import Mock, patch
from timeshift_btrfs_sync import cli, config as cfg, inventory, monitor, mqtt, sync
from timeshift_btrfs_sync.commands import PipelineResult
from timeshift_btrfs_sync.config import load_config, ConfigError
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.source import SourceRunner
from timeshift_btrfs_sync.state import empty_state

TEMPLATE=Path(__file__).parents[1]/'timeshift_btrfs_sync/data/example-config-local-backup.toml'

class ProgressTests(unittest.TestCase):
    def test_unknown_total_until_inventory_ready(self):
        p=monitor.SnapshotProgress();self.assertIsNone(p.view()['total_snapshots']);self.assertEqual(p.view()['progress'],'planning')
    def test_two_payloads_count_only_one_complete_date(self):
        p=monitor.SnapshotProgress();p.replan(['a','b']);p.payload_done('a','@',10)
        self.assertEqual(p.view()['progress'],'0 / 2')
        p.payload_done('a','@home',20);p.complete('a')
        self.assertEqual(p.view()['progress'],'1 / 2');self.assertEqual(p.view()['data_transferred_bytes'],30)
    def test_shrinking_plan_finishes_22_of_22(self):
        p=monitor.SnapshotProgress();p.replan(range(23))
        for n in range(5):p.complete(n)
        p.replan(range(5,22));self.assertEqual(p.view()['progress'],'5 / 22')
        for n in range(5,22):p.complete(n)
        self.assertEqual(p.view()['progress'],'22 / 22')
    def test_growing_plan_keeps_completed_history(self):
        p=monitor.SnapshotProgress();p.replan(range(22))
        for n in range(5):p.complete(n)
        p.replan(range(5,23));self.assertEqual(p.view()['progress'],'5 / 23')
        for n in range(5,23):p.complete(n)
        self.assertEqual(p.view()['progress'],'23 / 23')
    def test_changed_completed_tags_and_duplicate_plans_do_not_reset_or_double_count(self):
        p=monitor.SnapshotProgress();p.replan(['a','b']);p.complete('a');p.complete('a');p.replan(['b','b'])
        self.assertEqual(p.view()['progress'],'1 / 2');p.complete('b');p.replan([]);self.assertEqual(p.view()['progress'],'2 / 2')
    def test_recovery_invalidates_only_failed_version_bytes(self):
        p=monitor.SnapshotProgress();p.replan(['a','b']);p.payload_done('a','@',5);p.complete('a');p.payload_done('b','@',7);p.invalidate('b')
        self.assertEqual(p.view()['progress'],'1 / 2');self.assertEqual(p.view()['data_transferred_bytes'],5)
    def test_unknown_byte_measurements_stay_labeled(self):
        p=monitor.SnapshotProgress();p.payload_done('a','@',None);self.assertFalse(p.view()['bytes_complete'])
    def test_source_unavailable_is_skipped_not_transferred(self):
        p=monitor.SnapshotProgress();p.replan(['a','b']);p.complete('a');p.drop('b')
        self.assertEqual(p.view()['progress'],'1 / 1');self.assertEqual(p.view()['skipped_snapshots'],1)
    def test_observer_failure_does_not_fail_backup(self):
        p=monitor.SnapshotProgress(observer=Mock(side_effect=RuntimeError('broker down')));p.replan(['a']);p.complete('a');self.assertEqual(p.view()['progress'],'1 / 1')

class MonitorConfigTests(unittest.TestCase):
    def load_extra(self,text):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'backup.toml';p.write_text('[source]\nmode="local"\nsnapshot_root="/source"\n[destination]\ntarget_root="/target"\n'+text);return load_config(p)
    def test_old_config_opts_out_and_filename_is_name_fallback(self):
        c=self.load_extra('');self.assertFalse(c.mqtt_monitor.enabled);self.assertEqual(c.name,'backup')
    def test_live_monitor_is_independent_of_completion_enablement(self):
        c=self.load_extra('[mqtt]\nhost="broker"\nenabled=false\n[mqtt_monitor]\nenabled=true\n');self.assertTrue(c.mqtt_monitor.enabled);self.assertFalse(c.mqtt.enabled)
    def test_enabled_requires_broker(self):
        with self.assertRaisesRegex(ConfigError,'mqtt.host'):self.load_extra('[mqtt_monitor]\nenabled=true\n')
    def test_strict_schema_types_expiry_and_topic_prefixes(self):
        for text in ('enabled="true"','heartbeat_interval=true','heartbeat_interval=0','expire_after=60','topic_prefix="foo/#"','discovery_prefix=""','unknown=true'):
            with self.subTest(text=text),self.assertRaises(ConfigError):self.load_extra('[mqtt_monitor]\n'+text+'\n')
    def test_identity_is_canonical_path_and_hostname_not_filename_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a/backup.toml';p.parent.mkdir();p.write_text('');link=Path(tmp)/'alias.toml';link.symlink_to(p)
            one=monitor.backup_identity(p,'host');self.assertEqual(one,monitor.backup_identity(link,'host'))
            self.assertNotEqual(one,monitor.backup_identity(Path(tmp)/'b/backup.toml','host'));self.assertNotEqual(one,monitor.backup_identity(p,'other'))
    def test_every_profile_contains_exact_monitor_options(self):
        import tomllib
        for p in TEMPLATE.parent.glob('*.toml'):
            self.assertEqual(set(tomllib.loads(p.read_text())['mqtt_monitor']),cfg.MONITOR_KEYS);self.assertFalse(load_config(p).mqtt_monitor.enabled)

class MonitorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.config=load_config(TEMPLATE);self.config.mqtt_monitor.enabled=True;self.config.mqtt_monitor.discovery=False;self.messages=[]
    def publish(self,_broker,messages,**kwargs):
        self.messages.extend((topic,json.loads(json.dumps(body)),retain) for topic,body,retain in messages)
    def last(self):
        return [body for topic,body,_ in self.messages if topic.endswith('/last_result')][-1]
    def test_discovery_groups_live_expiring_and_durable_result_sensors(self):
        messages=monitor.discovery_messages(monitor.MonitorConfig(),'id','Backup','x/status','x/last_result');self.assertEqual(len(messages),12)
        for topic,body,retain in messages:
            self.assertTrue(retain);self.assertEqual(body['device']['identifiers'],['id'])
            if topic.endswith('/last_result/config'):self.assertNotIn('expire_after',body)
            else:self.assertEqual(body['expire_after'],180)
    def test_live_and_events_nonretained_last_result_retained(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):
                p=monitor.SnapshotProgress();p.replan(['a','b']);p.complete('a');p.replan(['b']);p.complete('b');monitor.report_phase('cleanup')
        self.assertEqual(self.last()['progress'],'2 / 2');self.assertEqual(self.last()['status'],'success')
        self.assertTrue(all(not retain for topic,_,retain in self.messages if topic.endswith(('/status','/events'))))
        self.assertTrue(any(t.endswith('/last_result') and r for t,_,r in self.messages));self.assertIsNone(monitor._ACTIVE.get())
        self.assertTrue(any(b.get('event')=='started' for _,b,_ in self.messages));self.assertTrue(any(b.get('event')=='completed' for _,b,_ in self.messages))
    def test_failure_preserves_truthful_21_of_22(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish),self.assertRaisesRegex(RuntimeError,'transfer failed'):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):
                p=monitor.SnapshotProgress();p.replan(range(22))
                for n in range(21):p.complete(n)
                p.current(21,'@home');raise RuntimeError('transfer failed')
        self.assertEqual(self.last()['progress'],'21 / 22');self.assertEqual(self.last()['status'],'failed');self.assertEqual(self.last()['failed_snapshots'],1)
    def test_unfinished_work_is_never_labeled_success(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):monitor.report_progress({'remaining_snapshots':1})
        self.assertEqual(self.last()['status'],'incomplete')
    def test_cleanup_failure_preserves_completed_transfers(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish),self.assertRaises(RuntimeError):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):
                p=monitor.SnapshotProgress();p.replan(['a']);p.complete('a');monitor.report_phase('cleanup');raise RuntimeError('cleanup failed')
        self.assertEqual(self.last()['progress'],'1 / 1');self.assertEqual(self.last()['failed_snapshots'],0);self.assertEqual(self.last()['status'],'failed')
    def test_keyboard_interrupt_is_130(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish),self.assertRaises(KeyboardInterrupt):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):raise KeyboardInterrupt
        self.assertEqual(self.last()['exit_code'],130);self.assertEqual(self.last()['status'],'interrupted')
    def test_duplicate_event_never_replaces_live_or_last_result(self):
        with patch.object(monitor,'publish_messages',side_effect=self.publish) as publisher:monitor.duplicate_event(self.config,'/jobs/a.toml')
        self.assertTrue(self.messages);self.assertTrue(all(t.endswith('/events') and not r for t,_,r in self.messages));self.assertEqual(self.messages[0][1]['event'],'duplicate_run')
        self.assertIn('-live-',publisher.call_args.kwargs['client_suffix'])
    def test_missing_paho_or_broker_does_not_escape(self):
        with patch.object(monitor,'publish_messages',side_effect=ImportError('no paho')),contextlib.redirect_stderr(io.StringIO()) as err:
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):monitor.report_progress({'remaining_snapshots':0})
        self.assertIn('monitoring unavailable',err.getvalue())
    def test_heartbeat_without_transfer_callbacks(self):
        self.config.mqtt_monitor.heartbeat_interval=.03;arrived=threading.Event()
        def record(*args,**kwargs):
            self.publish(*args,**kwargs)
            if sum(t.endswith('/status') for t,_,_ in self.messages)>=2:arrived.set()
        with patch.object(monitor,'publish_messages',side_effect=record):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):self.assertTrue(arrived.wait(1))
    def test_network_worker_final_drain_is_bounded(self):
        entered=threading.Event();release=threading.Event()
        def block(*args,**kwargs):entered.set();release.wait(3)
        with patch.object(monitor,'publish_messages',side_effect=block):
            run=monitor.LiveMonitor(self.config,'/jobs/a.toml');run.__enter__();self.assertTrue(entered.wait(1));started=time.monotonic();run.__exit__(None,None,None)
            self.assertLess(time.monotonic()-started,1.4);self.assertTrue(run._cancelled.is_set());release.set();run._thread.join(1)
    def test_worker_start_failure_does_not_fail_finalization(self):
        with patch.object(monitor.Thread,'start',side_effect=RuntimeError('threads exhausted')),contextlib.redirect_stderr(io.StringIO()):
            with monitor.LiveMonitor(self.config,'/jobs/a.toml'):pass
        self.assertIsNone(monitor._ACTIVE.get())
    def test_payload_excludes_credentials_and_config_path(self):
        self.config.mqtt.password='secret-password';text=json.dumps(monitor.LiveMonitor(self.config,'/sensitive/config.toml').payload())
        self.assertNotIn('secret-password',text);self.assertNotIn('/sensitive/config.toml',text)

def fake_paho(client, modern=True):
    """Provide one isolated Paho module tree for both supported callback APIs."""
    fake=types.ModuleType('paho.mqtt.client');fake.Client=Mock(return_value=client)
    if modern:fake.CallbackAPIVersion=types.SimpleNamespace(VERSION2=2)
    parent=types.ModuleType('paho');sub=types.ModuleType('paho.mqtt');parent.mqtt=sub;sub.client=fake
    return {'paho':parent,'paho.mqtt':sub,'paho.mqtt.client':fake}

class PublisherTests(unittest.TestCase):
    def test_shared_publisher_has_network_loop_qos_credentials_and_retention(self):
        fake=types.ModuleType('paho.mqtt.client');client=Mock();client.publish.return_value.is_published.return_value=True
        fake.Client=Mock(return_value=client);fake.CallbackAPIVersion=types.SimpleNamespace(VERSION2=2)
        parent=types.ModuleType('paho');sub=types.ModuleType('paho.mqtt');parent.mqtt=sub;sub.client=fake
        with patch.dict('sys.modules',{'paho':parent,'paho.mqtt':sub,'paho.mqtt.client':fake}):
            mqtt.publish_messages(mqtt.MQTTConfig(host='broker',username='user',password='pw',qos=1),[('status',{'status':'running'},False),('result',{'status':'success'},True)],client_suffix='-unique')
        client.loop_start.assert_called_once();client.loop_stop.assert_called_once();client.disconnect.assert_called_once();client.username_pw_set.assert_called_once_with('user','pw')
        self.assertEqual([c.kwargs['retain'] for c in client.publish.call_args_list],[False,True]);self.assertTrue(all(c.kwargs['qos']==1 for c in client.publish.call_args_list));self.assertTrue(fake.Client.call_args.kwargs['client_id'].endswith('-unique'))
    def test_disabled_legacy_notifications_do_not_connect(self):
        with patch.object(mqtt,'publish_messages') as publisher:mqtt.publish_status(mqtt.MQTTConfig(enabled=False),{})
        publisher.assert_not_called()

    def test_connect_failure_disconnects_without_starting_network_thread(self):
        client=Mock();client.connect.side_effect=OSError('broker down')
        with patch.dict('sys.modules',fake_paho(client)),self.assertRaisesRegex(OSError,'broker down'):
            mqtt.publish_messages(mqtt.MQTTConfig(host='broker'),[])
        client.disconnect.assert_called_once();client.loop_start.assert_not_called();client.loop_stop.assert_not_called()
    def test_publish_ack_timeout_stops_network_loop(self):
        client=Mock();client.publish.return_value.is_published.return_value=False
        with patch.dict('sys.modules',fake_paho(client)),self.assertRaisesRegex(RuntimeError,'timeout'):
            mqtt.publish_messages(mqtt.MQTTConfig(host='broker'),[('status',{},False)])
        client.disconnect.assert_called_once();client.loop_stop.assert_called_once()
    def test_cancelled_slow_connection_cannot_publish_after_drain_deadline(self):
        client=Mock();cancelled=threading.Event();client.connect.side_effect=lambda *_args,**_kwargs:cancelled.set()
        with patch.dict('sys.modules',fake_paho(client)):
            mqtt.publish_messages(mqtt.MQTTConfig(host='broker'),[('status',{'status':'running'},False)],cancelled=cancelled.is_set)
        client.publish.assert_not_called();client.disconnect.assert_called_once();client.loop_stop.assert_called_once()
    def test_legacy_callback_api_still_uses_unique_live_client_suffix(self):
        client=Mock();client.publish.return_value.is_published.return_value=True;modules=fake_paho(client,modern=False)
        with patch.dict('sys.modules',modules):mqtt.publish_messages(mqtt.MQTTConfig(host='broker',client_id='configured'),[('status',{},False)],client_suffix='-live-unique')
        modules['paho.mqtt.client'].Client.assert_called_once_with(client_id='configured-live-unique')

class SyncReplanTests(unittest.TestCase):
    def ident(self,date,subvol,suffix=''):
        return str(uuid.uuid5(uuid.NAMESPACE_URL,date+subvol+suffix))
    def exercise(self,generations,*,subvolumes=('@',),limit=None,fail_payload=None,fail_info=False):
        """Exercise actual sync, state and refreshed queues with isolated stream readers."""
        with tempfile.TemporaryDirectory() as tmp:
            c=load_config(TEMPLATE);c.source.snapshot_root='/snapshots';c.source.cache_root='/cache';c.source.subvolumes=list(subvolumes);c.source.verify_subvolumes_at_discovery=True
            c.manual_snapshot.enabled=False;c.retention.hourly=1;c.retention.daily=1;c.retention.weekly=0;c.retention.monthly=0;c.retention.boot=0;c.destination.target_root=Path(tmp)/'target';c.state_file=Path(tmp)/'state.json'
            views=[];scans=[];calls=[];copied=[]
            def scan(*args,**kwargs):
                """Return the next fresh flags/JSON/native generation at a real boundary."""
                rows=generations[min(len(scans),len(generations)-1)];scans.append(rows);idx=inventory.BtrfsIndex('/snapshots','local');infos={}
                for name,tags in rows:
                    infos[name]=json.dumps({'type':'btrfs','tags':tags,'comments':'fixture'})
                    for sv in subvolumes:idx.add(SubvolumeMeta(sv,f'/snapshots/{name}/{sv}',uuid=self.ident(name,sv),readonly=True))
                return inventory.SourceInventory('\n'.join(f'{n} {t}' for n,t in rows),idx,inventory.BtrfsIndex('/cache','local'),infos)
            def meta(_self,path,*,name=None,required=True):
                """Provide immutable sender/receiver identities for existing validation."""
                p=Path(path);date=p.parent.name;received=str(path).startswith(tmp)
                return SubvolumeMeta(name or p.name,str(path),uuid=self.ident(date,p.name,'received' if received else ''),received_uuid=self.ident(date,p.name) if received else None,readonly=True)
            def receive(send,receive,**kwargs):
                """Model namespace appearance after a confirmed stream or raise its failure."""
                calls.append((send,receive))
                if fail_payload and len(calls)==fail_payload:raise RuntimeError('payload failed')
                source=shlex.split(send[-1])[-1] if send[0]=='sh' else send[-1]
                dest=shlex.split(receive[-1])[-1] if receive[0]=='sh' else receive[-1]
                (Path(dest)/Path(source).name).mkdir(parents=True,exist_ok=True);return PipelineResult(transferred_bytes=10)
            def ensure(_config,name,*_indexes):
                """Create an ordinary date container, never a native Btrfs subvolume."""
                p=c.destination.target_root/'snapshots'/name;p.mkdir(parents=True,exist_ok=True);return p
            def info(_c,_inv,name,*,dry_run):
                """Copy fixture control metadata before the date completion callback."""
                copied.append(name)
                if fail_info:raise RuntimeError('metadata failed')
                (c.destination.target_root/'snapshots'/name/'info.json').write_text('{}')
            with patch.object(sync.SourceRunner,'from_config',return_value=SourceRunner.from_mode('local',None)),patch.object(sync.preflight,'check_required_sync_paths'),patch.object(sync,'prepare_destination'),patch.object(sync.inventory,'build_source_inventory',side_effect=scan),patch.object(sync.inventory,'build_local_btrfs_index',return_value=inventory.BtrfsIndex(str(c.destination.target_root/'snapshots'),'local')),patch.object(sync,'_recover_stale_state_snapshots_missing_from_source',return_value=0),patch.object(sync,'_verify_sync_viability_before_manual_snapshot'),patch.object(sync,'_maybe_create_manual_snapshot',return_value=False),patch.object(sync,'refresh_state_metadata_and_report',return_value=0),patch.object(sync,'_select_parent',return_value=(None,None)),patch.object(sync,'_ensure_source_send_path',side_effect=lambda _c,_s,_n,sv,*_:sv.path),patch.object(sync,'_ensure_destination_snapshot_subvolume',side_effect=ensure),patch.object(sync.BtrfsOps,'meta',meta),patch.object(sync,'_sync_snapshot_info_json',side_effect=info),patch.object(sync,'stream_pipeline',side_effect=receive),patch.object(monitor,'report_progress',side_effect=lambda value:views.append(value.copy())),contextlib.redirect_stdout(io.StringIO()):
                if fail_payload or fail_info:
                    with self.assertRaisesRegex(RuntimeError,'metadata failed' if fail_info else 'payload failed'):sync.sync_once(c,empty_state(),dry_run=False,limit=limit)
                    result=None
                else:result=sync.sync_once(c,empty_state(),dry_run=False,limit=limit)
            return result,views,calls,copied,scans
    def test_new_date_grows_total_without_losing_changed_completed_date(self):
        a='2026-10-19_10-00-00';b='2026-10-19_11-00-00';c='2026-10-19_12-00-00'
        result,views,calls,copied,scans=self.exercise([[(a,'D'),(b,'H')],[(a,'H'),(b,'H'),(c,'D')]])
        self.assertEqual(result.snapshot_progress['progress'],'3 / 3');self.assertEqual([e['snapshot'] for e in result.events],[a,b,c]);self.assertIn('1 / 3',[v['progress'] for v in views if 'progress' in v]);self.assertEqual(copied,[a,b,c])
    def test_expired_pending_date_shrinks_total_and_keeps_completed(self):
        a='2026-10-19_10-00-00';b='2026-10-19_11-00-00'
        result,_,calls,_,_=self.exercise([[(a,'D'),(b,'H')],[(a,'H')]])
        self.assertEqual(result.snapshot_progress['progress'],'1 / 1');self.assertEqual(len(calls),1)
    def test_two_payloads_count_once_and_soft_limit_keeps_whole_date(self):
        a='2026-10-19_10-00-00';b='2026-10-19_11-00-00'
        result,views,calls,copied,scans=self.exercise([[(a,'D'),(b,'H')]],subvolumes=('@','@home'),limit=1)
        self.assertEqual(result.transferred,2);self.assertEqual(result.snapshot_progress['progress'],'1 / 1');self.assertEqual(copied,[a]);self.assertEqual(len(scans),1)
        self.assertTrue(any(v.get('data_transferred_bytes')==10 and v.get('completed_snapshots')==0 for v in views))
    def test_second_payload_failure_keeps_unfinished_snapshot_visible(self):
        a='2026-10-19_10-00-00';b='2026-10-19_11-00-00'
        _,views,calls,copied,_=self.exercise([[(a,'D'),(b,'H')]],subvolumes=('@','@home'),fail_payload=2)
        self.assertEqual(views[-1]['progress'],'0 / 2');self.assertEqual(copied,[]);self.assertEqual(len(calls),2)

    def test_metadata_failure_does_not_count_a_received_date_complete(self):
        a='2026-10-19_10-00-00';b='2026-10-19_11-00-00'
        _,views,calls,copied,_=self.exercise([[(a,'D'),(b,'H')]],fail_info=True)
        self.assertEqual(views[-1]['progress'],'0 / 2');self.assertEqual(len(calls),1)
    def test_actual_22_date_workflow_keeps_completed_date_after_source_expiry(self):
        dates=[f'2026-10-19_{n:02d}-00-00' for n in range(22)]
        result,_,calls,copied,scans=self.exercise([[(n,'O') for n in dates],[(n,'O') for n in dates[1:]]])
        self.assertEqual(result.snapshot_progress['progress'],'22 / 22');self.assertEqual(copied,dates);self.assertEqual(len(calls),22)
    def test_noop_is_zero_of_zero(self):
        result,_,calls,_,_=self.exercise([[]]);self.assertEqual(result.snapshot_progress['progress'],'0 / 0');self.assertEqual(calls,[])


class LockedCLITests(unittest.TestCase):
    setUp = MonitorLifecycleTests.setUp
    publish = MonitorLifecycleTests.publish
    last = MonitorLifecycleTests.last
    def run_cli(self,command='--run',error=None,owner=False):
        """Run actual CLI logging/lock/monitor lifetimes with a simulated sync body."""
        from timeshift_btrfs_sync.lock import FileLock
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            c=self.config;c.log_dir=None;c.lock_file=Path(tmp)/'lock';c.state_file=Path(tmp)/'state.json';c.destination.target_root=Path(tmp)/'target'
            held=[]
            def publish(broker,messages,**kwargs):
                with c.lock_file.open('a') as f:
                    try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError:held.append(True)
                    else:held.append(False);fcntl.flock(f,fcntl.LOCK_UN)
                self.publish(broker,messages,**kwargs)
            def work(*args,**kwargs):
                monitor.report_progress({'total_snapshots':0,'remaining_snapshots':0,'completed_snapshots':0,'progress':'0 / 0'})
                if error:raise error
                return sync.SyncRunSummary(0,[],command=='--dry-run',0,0)
            args=['sync','--config',str(Path(tmp)/'config.toml'),command]
            with patch.object(cli,'load_config',return_value=c),patch.object(cli,'prepare_lock_path'),patch.object(cli,'sync_once',side_effect=work),patch.object(monitor,'publish_messages',side_effect=publish),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                if owner:
                    with FileLock(c.lock_file):result=cli.main(args)
                else:result=cli.main(args)
            return result,held
    def test_live_status_is_published_only_while_actual_lock_is_owned(self):
        result,held=self.run_cli();self.assertEqual(result,0);self.assertTrue(held);self.assertTrue(all(held));self.assertEqual(self.last()['status'],'success')
    def test_duplicate_launch_never_replaces_original_status_or_result(self):
        result,_=self.run_cli(owner=True);self.assertEqual(result,3);self.assertTrue(self.messages);self.assertTrue(all(t.endswith('/events') for t,_,_ in self.messages))
    def test_dry_run_never_publishes_live_status(self):
        result,_=self.run_cli(command='--dry-run');self.assertEqual(result,0);self.assertEqual(self.messages,[])
    def test_work_io_error_is_failed_backup_not_duplicate_launch(self):
        result,_=self.run_cli(error=BlockingIOError('storage busy'));self.assertEqual(result,3);self.assertEqual(self.last()['status'],'failed');self.assertFalse(any(b.get('event')=='duplicate_run' for _,b,_ in self.messages))

if __name__=='__main__':unittest.main()
