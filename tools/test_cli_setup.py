import io
import json
import os
from pathlib import Path
import subprocess
import ssl
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import cli_setup
from manager_backend import Cancelled


def archive(system='Linux', extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as output:
        output.writestr('cli/UndertaleModCli.exe' if system=='Windows' else 'cli/UndertaleModCli', b'cli fixture')
        output.writestr('cli/UndertaleModLib.dll', b'dependency')
        for name, value in (extra or {}).items(): output.writestr(name,value)
    return stream.getvalue()


class CliSetup(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.workspace=Path(self.temp.name)

    def install(self, system='Linux', data=None, **kwargs):
        with patch.object(cli_setup.platform,'system',return_value=system), \
             patch.object(cli_setup.urllib.request,'urlopen',return_value=io.BytesIO(data if data is not None else archive(system))) as download, \
             patch.object(cli_setup.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'0.9.2.0+test')) as probe:
            executable=cli_setup.install_cli(self.workspace,**kwargs)
            self.assertEqual(download.call_args.args[0].full_url,cli_setup.ASSETS[system])
            context = download.call_args.kwargs['context']
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertEqual(probe.call_args.args[0][1:], ['--version'])
            return executable

    def test_packaged_roots_work_without_system_certificate_store(self):
        empty = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(empty.cert_store_stats()['x509_ca'], 0)
        with patch.object(cli_setup.ssl, 'create_default_context', return_value=empty):
            context = cli_setup.download_context()
        self.assertGreater(context.cert_store_stats()['x509_ca'], 0)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_platform_download_dependencies_permissions_and_reuse(self):
        for system in ('Linux','Windows'):
            with self.subTest(system=system):
                executable=self.install(system)
                self.assertTrue(executable.is_file())
                self.assertEqual((executable.parent/'UndertaleModLib.dll').read_bytes(),b'dependency')
                self.assertEqual(json.loads((executable.parent/'cli-install.json').read_text())['version'],'0.9.2.0')
                if system=='Linux' and os.name != 'nt': self.assertTrue(executable.stat().st_mode & 0o111)
                with patch.object(cli_setup.platform,'system',return_value=system), patch.object(cli_setup.urllib.request,'urlopen') as download:
                    self.assertEqual(cli_setup.install_cli(self.workspace),executable)
                    download.assert_not_called()

    def test_unsafe_or_invalid_archive_publishes_nothing(self):
        for data in (archive(extra={'../escape':b'bad'}), b'not a zip'):
            with self.subTest(data=data[:10]), self.assertRaises((ValueError,zipfile.BadZipFile)):
                self.install(data=data)
            self.assertEqual(list((self.workspace/'tools').iterdir()),[])
        self.assertFalse((self.workspace/'escape').exists())

    def test_cancel_before_network_and_during_extraction(self):
        with self.assertRaises(Cancelled): self.install(cancel=lambda:True)
        self.assertFalse((self.workspace/'tools').exists())
        with patch.object(cli_setup.platform,'system',return_value='Linux'), patch.object(cli_setup.urllib.request,'urlopen',return_value=io.BytesIO(archive())):
            checks=iter([False,False,False,False,True])
            with self.assertRaises(Cancelled): cli_setup.install_cli(self.workspace,cancel=lambda:next(checks,True))
        self.assertEqual(list((self.workspace/'tools').iterdir()),[])

    def test_version_failure_does_not_publish(self):
        with patch.object(cli_setup.platform,'system',return_value='Linux'), patch.object(cli_setup.urllib.request,'urlopen',return_value=io.BytesIO(archive())), patch.object(cli_setup.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'wrong version')):
            with self.assertRaisesRegex(ValueError,'unexpected version'): cli_setup.install_cli(self.workspace)
        self.assertEqual(list((self.workspace/'tools').iterdir()),[])

    def test_modified_install_is_not_overwritten(self):
        executable=self.install()
        executable.write_bytes(b'changed')
        with patch.object(cli_setup.platform,'system',return_value='Linux'), patch.object(cli_setup.urllib.request,'urlopen') as download:
            with self.assertRaisesRegex(ValueError,'incomplete or modified'): cli_setup.install_cli(self.workspace)
            download.assert_not_called()
        self.assertEqual(executable.read_bytes(),b'changed')
