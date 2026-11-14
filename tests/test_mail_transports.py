"""Exercise SMTP compatibility and local mailx delivery without contacting a mail server."""
from contextlib import redirect_stderr
from email import message_from_bytes, policy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from timeshift_btrfs_sync import cli, config as cfg, mail
from test_manual_snapshot_retention import _config

PAYLOAD = {"name": "Daily backup æøå", "command": "sync", "success": True,
           "state": "success", "version": "test", "exit_code": 0}


class MailConfigurationTests(unittest.TestCase):
    """Keep old SMTP validation while allowing recipient-only local utility mode."""

    def load(self, text):
        """Parse a minimal ordinary config without touching backup endpoints."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.toml"
            path.write_text('[source]\nmode="local"\nsnapshot_root="/source"\n[destination]\ntarget_root="/backup"\n[mail]\n'+text)
            return cfg.load_config(path).mail

    def test_old_config_retains_smtp_default(self):
        """Omitted new fields preserve disabled mail and existing SMTP defaults."""
        options = self.load('')
        self.assertFalse(options.use_mailx_util); self.assertEqual(options.to_addr, '')

    def test_mailx_requires_only_enabled_flag_and_recipient(self):
        """Local utility delivery needs no app SMTP host, sender or credentials."""
        options = self.load('enabled=true\nuse_mailx_util=true\nto_addr="admin@example.com"')
        self.assertEqual(options.recipients(), ['admin@example.com'])
        self.assertEqual(options.smtp_host, ''); self.assertEqual(options.from_addr, '')

    def test_single_recipient_overrides_old_list(self):
        """Adding to_addr to a generated template cannot also mail its example recipients."""
        options = self.load('use_mailx_util=true\nto_addr="  root  "\nto_addrs=["old@example.com"]')
        self.assertEqual(options.recipients(), ['root'])

    def test_blank_single_recipient_uses_existing_list(self):
        """Existing multiple-recipient configs keep working with either transport."""
        options = self.load('enabled=true\nuse_mailx_util=true\nto_addr=""\nto_addrs=["root", "admin@example.com"]')
        self.assertEqual(options.recipients(), ['root', 'admin@example.com'])

    def test_smtp_still_requires_host_sender_and_recipient(self):
        """The default backend retains its original mandatory settings."""
        for text, expected in [('enabled=true', 'smtp_host'),
                ('enabled=true\nsmtp_host="smtp"', 'from_addr'),
                ('enabled=true\nsmtp_host="smtp"\nfrom_addr="sender@example.com"', 'to_addrs')]:
            with self.subTest(text=text), self.assertRaisesRegex(cfg.ConfigError, expected): self.load(text)

    def test_smtp_accepts_single_recipient_alias(self):
        """to_addr works consistently when switching back to Python SMTP."""
        options = self.load('enabled=true\nsmtp_host="smtp"\nfrom_addr="sender@example.com"\nto_addr="admin@example.com"')
        self.assertEqual(options.recipients(), ['admin@example.com'])

    def test_ignored_smtp_credentials_and_tls_do_not_block_mailx(self):
        """Old SMTP settings need not be removed or resolved when mailx is selected."""
        options = self.load('enabled=true\nuse_mailx_util=true\nto_addr="root"\npassword="ignored"\npassword_file="/missing/ignored-password"\nsmtp_ssl=true\nstarttls=true')
        self.assertTrue(options.use_mailx_util)

    def test_smtp_still_rejects_password_and_tls_conflicts(self):
        """Backend selection does not weaken existing SMTP configuration checks."""
        for text in ['password="x"\npassword_file="x"', 'smtp_ssl=true\nstarttls=true', 'password_file="/missing/smtp-password"']:
            with self.subTest(text=text), self.assertRaises(cfg.ConfigError): self.load(text)

    def test_new_options_are_strict_types(self):
        """Reject strings pretending to be booleans and non-string single recipients."""
        for text in ['use_mailx_util="true"', 'use_mailx_util=1', 'to_addr=true', 'to_addr=[]']:
            with self.subTest(text=text), self.assertRaises(cfg.ConfigError): self.load(text)

    def test_mailx_rejects_special_destinations_and_option_injection(self):
        """A mailx recipient must never select a pipe command, file or command option."""
        for address in ['|touch /tmp/bad', '/tmp/mail', './mail', '-s', 'a@example.com,b@example.com',
                        'Name <a@example.com>', 'root\nBcc: a@example.com', 'root;bad', 'a!b']:
            with self.subTest(address=address), self.assertRaises(cfg.ConfigError):
                self.load('enabled=true\nuse_mailx_util=true\nto_addr='+json.dumps(address))

    def test_mailx_accepts_plain_remote_and_local_recipients(self):
        """Normal local users and common plus-addressed mailboxes remain usable."""
        for address in ['root', 'backup_user', 'ops+backup@example.org', 'a.b-c@host.example']:
            with self.subTest(address=address):
                self.assertEqual(self.load('enabled=true\nuse_mailx_util=true\nto_addr='+json.dumps(address)).recipients(), [address])

    def test_mailx_validates_optional_sender(self):
        """Reject header/option/file syntax in a supplied local utility sender."""
        with self.assertRaises(cfg.ConfigError):
            self.load('enabled=true\nuse_mailx_util=true\nto_addr="root"\nfrom_addr="-bad"')


class MailTransportTests(unittest.TestCase):
    """Verify formatting, arguments, error reporting and unchanged SMTP behavior."""

    def options(self, **kwargs):
        """Create enabled mailx options without SMTP credentials."""
        return mail.MailConfig(enabled=True, use_mailx_util=True, to_addr='admin@example.com', **kwargs)

    def run_mailx(self, options, *, attachments=None, flavor='GNU Mailutils', result=0):
        """Capture utility argv/stdin while prohibiting SMTP and credential resolution."""
        completed = [subprocess.CompletedProcess([], 0, flavor, ''), subprocess.CompletedProcess([], result, '', 'delivery failed' if result else '')]
        with patch.object(mail.shutil, 'which', return_value='/usr/bin/mailx'), patch.object(mail.subprocess, 'run', side_effect=completed) as run, patch.object(mail.smtplib, 'SMTP') as smtp, patch.object(mail.smtplib, 'SMTP_SSL') as ssl, patch.object(mail.MailConfig, 'resolved_password', side_effect=AssertionError('SMTP password read')):
            mail.send_status(options, PAYLOAD, attachments=attachments)
        smtp.assert_not_called(); ssl.assert_not_called()
        return run

    def test_mailx_sends_plain_body_with_single_recipient_and_no_sender(self):
        """The minimal feature invokes local mailx with shared subject/body via stdin."""
        run = self.run_mailx(self.options())
        args, kwargs = run.call_args
        self.assertEqual(args[0][-1], 'admin@example.com'); self.assertNotIn('-r', args[0])
        self.assertIn('SUCCESS: Daily backup æøå', args[0][2])
        self.assertIn('JSON payload:', kwargs['input']); self.assertEqual(kwargs['timeout'], 10)
        self.assertNotIn('shell', kwargs)

    def test_gnu_attachments_keep_success_body_filtering_and_size_cap(self):
        """Reuse .succes text, de-duplicate files and omit empty/oversized/missing logs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); success=root/'run.succes'; log=root/'run.log'; empty=root/'run.err'; large=root/'big.log'
            success.write_text('Backup result æøå\n'); log.write_text('log'); empty.touch(); large.write_bytes(b'x'*100)
            run = self.run_mailx(self.options(max_attachment_bytes=50), attachments=(p for p in [success, log, log, empty, large, root/'missing']))
            args = run.call_args.args[0]
            self.assertEqual(args.count('--attach'), 2); self.assertNotIn('-a', args)
            self.assertIn(str(success), args); self.assertIn(str(log), args)
            self.assertNotIn(str(large), args); self.assertEqual(run.call_args.kwargs['input'], 'Backup result æøå\n')

    def test_optional_sender_and_recipient_list(self):
        """Pass configured sender while preserving existing recipient-list delivery."""
        options=self.options(from_addr='sender@example.com'); options.to_addr=''; options.to_addrs=['root','ops@example.com']
        args=self.run_mailx(options).call_args.args[0]
        self.assertEqual(args[-2:], ['root','ops@example.com']); self.assertEqual(args[3:5], ['-r','sender@example.com'])

    def test_s_nail_uses_attachment_flag_and_waits_for_mta(self):
        """Avoid GNU -a/header confusion and s-nail asynchronous false successes."""
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'run.log';log.write_text('log')
            args=self.run_mailx(self.options(), attachments=[log], flavor='s-nail v14.9').call_args.args[0]
            self.assertIn('-a',args); self.assertIn('sendwait',args); self.assertNotIn('--',args)

    def test_unknown_mailx_can_send_without_attachments(self):
        """Keep basic POSIX-style utilities usable when no MIME files are selected."""
        self.run_mailx(self.options(attach_logs=False), flavor='BSD mail')

    def test_unknown_attachment_syntax_is_refused_before_submission(self):
        """Never silently lose attachments or reinterpret their names as mail headers."""
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'run.log';log.write_text('log')
            with patch.object(mail.shutil, 'which', return_value='/mailx'), patch.object(mail.subprocess, 'run', return_value=subprocess.CompletedProcess([],1,'','usage')) as run:
                with self.assertRaisesRegex(RuntimeError, 'attach_logs=false'):
                    mail.send_status(self.options(), PAYLOAD, attachments=[log])
                self.assertEqual(run.call_count,1)

    def test_missing_utility_reports_setup_and_never_falls_back_to_smtp(self):
        """A missing installation gives an actionable error without trying a second transport."""
        with patch.object(mail.shutil, 'which', return_value=None), patch.object(mail.smtplib, 'SMTP') as smtp:
            with self.assertRaisesRegex(RuntimeError, 'configured local mail system'): mail.send_status(self.options(),PAYLOAD)
            smtp.assert_not_called()

    def test_mail_command_fallback_when_mailx_name_is_absent(self):
        """A GNU installation exposing only mail is discovered automatically."""
        with patch.object(mail.shutil, 'which', side_effect=[None,'/bin/mail']), patch.object(mail.subprocess, 'run', side_effect=[subprocess.CompletedProcess([],0,'GNU Mailutils',''),subprocess.CompletedProcess([],0,'','')]) as run:
            mail.send_status(self.options(),PAYLOAD)
            self.assertEqual(run.call_args.args[0][0],'/bin/mail')

    def test_disabled_mail_does_not_probe_or_send(self):
        """Turning email off performs neither subprocess nor SMTP I/O."""
        with patch.object(mail.subprocess,'run') as run, patch.object(mail.smtplib,'SMTP') as smtp:
            mail.send_status(mail.MailConfig(),PAYLOAD)
            run.assert_not_called(); smtp.assert_not_called()

    def test_mailx_failure_is_reported_without_retry(self):
        """Nonzero utility status remains a notification error rather than triggering duplicates."""
        with self.assertRaisesRegex(RuntimeError,'mailx exited 75'):
            self.run_mailx(self.options(),result=75)

    def test_mailx_timeout_and_os_error_are_reported(self):
        """Detection/submission failures stay bounded and do not initiate another send."""
        for failure in [subprocess.TimeoutExpired('/mailx',1), FileNotFoundError('gone')]:
            with self.subTest(failure=failure), patch.object(mail.shutil,'which',return_value='/mailx'), patch.object(mail.subprocess,'run',side_effect=failure) as run:
                with self.assertRaises(RuntimeError): mail.send_status(self.options(),PAYLOAD)
                self.assertEqual(run.call_count,1)

    def test_direct_mailx_call_rejects_injected_subject_and_recipient(self):
        """Direct library users receive the same guards as TOML callers."""
        for recipient, name in [('|command','job'), ('root','job\nBcc:bad')]:
            with self.subTest(recipient=recipient), patch.object(mail.subprocess,'run') as run:
                options=self.options();options.to_addr=recipient
                with self.assertRaises(ValueError): mail.send_status(options,{**PAYLOAD,'name':name})
                run.assert_not_called()

    def test_smtp_tls_auth_body_and_mime_attachment_are_preserved(self):
        """Default SMTP still uses the same MIME helpers and password resolver."""
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'run.log'; log.write_bytes(b'log\n')
            options=mail.MailConfig(enabled=True,smtp_host='smtp.example.com',from_addr='sender@example.com',to_addrs=['a@example.com','b@example.com'],username='user',password='secret')
            with patch.object(mail.smtplib,'SMTP') as factory, patch.object(mail.subprocess,'run') as run:
                mail.send_status(options,PAYLOAD,attachments=[log])
                smtp=factory.return_value.__enter__.return_value
                smtp.starttls.assert_called_once(); smtp.login.assert_called_once_with('user','secret')
                message=smtp.send_message.call_args.args[0]
                self.assertEqual(str(message['To']),'a@example.com, b@example.com')
                self.assertEqual(next(message.iter_attachments()).get_payload(decode=True),b'log\n')
                run.assert_not_called()

    def test_smtp_ssl_single_recipient_and_optional_auth(self):
        """The new singular recipient works with SSL without forcing SMTP login."""
        options=mail.MailConfig(enabled=True,smtp_host='smtp',smtp_ssl=True,starttls=False,from_addr='sender@example.com',to_addr='a@example.com')
        with patch.object(mail.smtplib,'SMTP_SSL') as factory:
            mail.send_status(options,PAYLOAD)
            smtp=factory.return_value.__enter__.return_value
            smtp.starttls.assert_not_called(); smtp.login.assert_not_called()
            self.assertEqual(str(smtp.send_message.call_args.args[0]['To']),'a@example.com')

    def test_notification_failure_is_warning_and_existing_filters_still_apply(self):
        """Neither backend can alter backup exit handling or bypass success/failure preferences."""
        config=_config(cleanup_enabled=False);config.mail=self.options();config.mail.notify_on_success=False
        with patch.object(cli,'send_mail_status',side_effect=RuntimeError('failed')) as send, redirect_stderr(io.StringIO()) as err:
            cli._send_notifications(config,'sync',success=True,exit_code=0);send.assert_not_called()
            cli._send_notifications(config,'sync',success=False,exit_code=23)
            self.assertEqual(send.call_args.args[1]['exit_code'],23)
            self.assertIn('WARNING: mail notification failed',err.getvalue())


class InstalledGNUUtilityTests(unittest.TestCase):
    """Exercise real GNU MIME composition using an isolated fake MTA, never Postfix delivery."""

    def test_real_mailx_preserves_unicode_body_and_binary_attachment(self):
        """Run the installed utility but capture its complete message in a temporary local file."""
        command=shutil.which('mailx') or shutil.which('mail')
        if not command: self.skipTest('GNU Mailutils not installed')
        real_run=subprocess.run
        version=real_run([command,'--version'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=5)
        if 'GNU Mailutils' not in version.stdout: self.skipTest('GNU Mailutils not installed')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=root/'message';sink=root/'sink';rc=root/'mailrc';rc.write_text('')
            sink.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\nPath('+repr(str(capture))+').write_bytes(sys.stdin.buffer.read())\n');sink.chmod(0o700)
            success=root/'run.succes';success.write_text('Result æøå\n~!do-not-execute\n')
            log=root/'run.log';data=b'bytes\x00\xff\n';log.write_bytes(data)
            def isolated(args, **kwargs):
                """Force real GNU mail to an isolated capture MTA and empty mail configuration."""
                if args[1:] != ['--version']:
                    args=[args[0],'--no-config','--norc','--mailer=sendmail:'+str(sink),*args[1:]]
                    kwargs['env']={**os.environ,'MAILRC':str(rc)}
                return real_run(args,**kwargs)
            with patch.object(mail.shutil,'which',return_value=command), patch.object(mail.subprocess,'run',side_effect=isolated):
                mail.send_status(mail.MailConfig(enabled=True,use_mailx_util=True,to_addr='admin@example.invalid'),PAYLOAD,attachments=[success,log])
            message=message_from_bytes(capture.read_bytes(),policy=policy.default)
            self.assertIn('Daily backup æøå',str(message['Subject']))
            self.assertEqual(message.get_body(preferencelist=('plain',)).get_content(),success.read_text())
            attachments={part.get_filename():part.get_payload(decode=True) for part in message.iter_attachments()}
            self.assertEqual(attachments[log.name],data)
            self.assertEqual(attachments[success.name],success.read_bytes())
