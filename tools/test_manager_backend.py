"""Small deterministic transactional tests; real archive smoke tests are separate."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock
try:
    import manager_backend as backend
except ModuleNotFoundError:
    from tools import manager_backend as backend

class ManagerTransactions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir();(self.source/'data.win').write_bytes(b'clean stock data')
        (self.source/'VIVIDSTASIS.exe').write_bytes(b'game executable placeholder')
        self.cli=self.root/'cli';self.cli.write_bytes(b'cli placeholder')
        self.stock=backend.sha256(self.source/'data.win')
        self.override=mock.patch.object(backend,'SOURCE_SHA256',self.stock);self.override.start()
        self.manager=backend.Manager(self.root/'workspace')
        self.manager.setup(self.source,self.root/'game',self.cli)
    def tearDown(self):
        self.override.stop();self.temp.cleanup()
    def staged(self,name,content):
        p=self.root/name;p.write_bytes(content);return p
    def install(self,content,ident='song_a',song_id=207):
        m=self.manager
        m.state['assignments'].setdefault(ident,dict(song_id=song_id,chart_id=f'custom_manager_{song_id}'));m._save()
        chart=f'Charts/custom_manager_{song_id}/OPENING.vsb'
        files={'data.win':self.staged('newdata',content),chart:self.staged('chart',b'chart bytes')}
        state=copy.deepcopy(m.state);state.update(archive_sha256=backend.sha256(files['data.win']),installed_files={chart:backend.sha256(files[chart])},installed_ids=[ident],selected_ids=[ident])
        m._install(files,state);return chart
    def test_backup_is_named_immutable_and_verified(self):
        backup=Path(self.manager.state['backup']);self.assertEqual(backup.name,'data.win.backup')
        before=backup.stat().st_mtime_ns
        backend.Manager._immutable_backup(self.source/'data.win',backup)
        self.assertEqual(before,backup.stat().st_mtime_ns)
        backup.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'will not be overwritten'):backend.Manager._immutable_backup(self.source/'data.win',backup)
        self.assertEqual(backup.read_bytes(),b'tampered')
    def test_commit_then_previous_restore_and_stock_build(self):
        chart=self.install(b'custom archive')
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'custom archive')
        self.manager.rollback()
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'clean stock data')
        self.assertFalse((self.root/'game'/chart).exists())
        self.assertIn('song_a',self.manager.state['tombstones'])
        self.manager.rollback() # previous custom installation becomes recoverable
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'custom archive')
        self.manager.build([])
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'clean stock data')
        self.assertEqual(self.manager.state['installed_ids'],[])
        self.assertEqual((self.source/'data.win').read_bytes(),b'clean stock data')
    def test_failed_commit_restores_prior_bytes_and_state(self):
        chart=self.install(b'first custom')
        before=copy.deepcopy(self.manager.state)
        source=self.staged('second',b'second custom')
        desired={'data.win':source}
        newstate=copy.deepcopy(before);newstate.update(installed_ids=[],installed_files={},archive_sha256=backend.sha256(source))
        real=self.manager._replace
        def fail(source_,target):
            if source_==source:raise OSError('injected replace failure')
            return real(source_,target)
        with mock.patch.object(self.manager,'_replace',side_effect=fail):
            with self.assertRaisesRegex(OSError,'injected'):self.manager._install(desired,newstate)
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'first custom')
        self.assertEqual((self.root/'game'/chart).read_bytes(),b'chart bytes')
        self.assertEqual(self.manager.state,before)
        self.assertFalse(self.manager.journal_path.exists())
    def test_crash_recovery_uses_journal_not_partial_committed_state(self):
        m=self.manager;old=copy.deepcopy(m.state)
        transaction=m.workspace/'transactions/crash';transaction.mkdir(parents=True)
        snapshot=transaction/'data.before';snapshot.write_bytes(b'clean stock data')
        (self.root/'game/data.win').write_bytes(b'partial install')
        new=copy.deepcopy(old);new['archive_sha256']=backend.sha256(self.root/'game/data.win')
        backend.atomic_json(m.state_path,new)
        backend.atomic_json(m.journal_path,dict(phase='installing',directory=str(transaction),old_state=old,new_state=new,operations=[dict(relative='data.win',source='unused',existed=True,before=str(snapshot),before_sha256=self.stock)]))
        recovered=backend.Manager(m.workspace)
        self.assertEqual(recovered.state,old)
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'clean stock data')
        self.assertFalse(recovered.journal_path.exists())
    def test_ids_are_never_reused_after_removal(self):
        m=self.manager
        m._assign([SimpleNamespace(metadata={'id':'a'}),SimpleNamespace(metadata={'id':'b'})])
        self.assertEqual(m.state['assignments']['a']['song_id'],207)
        m._assign([SimpleNamespace(metadata={'id':'b'}),SimpleNamespace(metadata={'id':'c'})])
        self.assertEqual(m.state['assignments']['c']['song_id'],209)
        m._assign([SimpleNamespace(metadata={'id':'a'})])
        self.assertEqual(m.state['assignments']['a']['song_id'],207)
    def test_stale_manager_selection_cannot_overwrite_install_state(self):
        other=backend.Manager(self.manager.workspace)
        self.install(b'new archive')
        other.select(['pending'])
        saved=json.loads(self.manager.state_path.read_text())
        self.assertEqual(saved['archive_sha256'],hashlib.sha256(b'new archive').hexdigest())
        self.assertEqual(saved['assignments']['song_a']['song_id'],207)
        self.assertEqual(saved['selected_ids'],['pending'])
    def test_unmanaged_collision_is_not_overwritten(self):
        collision=self.root/'game/Charts/custom_manager_900/OPENING.vsb';collision.parent.mkdir(parents=True);collision.write_bytes(b'external')
        desired={'data.win':self.source/'data.win','Charts/custom_manager_900/OPENING.vsb':self.staged('foreign',b'new')}
        with self.assertRaisesRegex(ValueError,'unmanaged'):self.manager._install(desired,copy.deepcopy(self.manager.state))
        self.assertEqual(collision.read_bytes(),b'external')
        self.assertFalse(self.manager.journal_path.exists())
    def test_retention_keeps_only_previous_installation_snapshot(self):
        self.install(b'one custom')
        self.install(b'two custom')
        transactions=self.manager.workspace/'transactions'
        self.assertEqual(len(list(transactions.iterdir())),1)
        previous=self.manager.state['previous_installation']
        self.assertEqual(Path(previous['files']['data.win']).read_bytes(),b'one custom')
        stage=self.manager.workspace/'builds'/('a'*32);stage.mkdir(parents=True)
        (stage/'.manager-owned').write_text('owned')
        (stage/'data.pending.win').write_bytes(b'large archive placeholder')
        (stage/'patch.log').write_text('diagnostic log')
        self.manager._prune()
        self.assertFalse((stage/'data.pending.win').exists())
        self.assertTrue((stage/'patch.log').exists())
    def test_normalization_cache_reuses_and_detects_corruption(self):
        source=self.staged('audio.wav',b'input audio')
        work=self.root/'normalize';work.mkdir()
        calls=[]
        def normalize(command,log,cancel):
            calls.append(command)
            Path(command[-1]).write_bytes(b'normalized audio')
        with mock.patch.object(self.manager,'_run',side_effect=normalize):
            self.manager._normalized_asset(source,'audio',work/'one.ogg',work/'one.log',None)
            self.manager._normalized_asset(source,'audio',work/'two.ogg',work/'two.log',None)
            self.assertEqual(len(calls),1)
            cache=next((self.manager.workspace/'cache').glob('*.ogg'));cache.write_bytes(b'corrupt')
            self.manager._normalized_asset(source,'audio',work/'three.ogg',work/'three.log',None)
            self.assertEqual(len(calls),2)
            self.assertEqual((work/'three.ogg').read_bytes(),b'normalized audio')
    def test_fingerprint_detects_metadata_and_source_edits(self):
        audio=self.staged('fingerprint_audio',b'audio')
        chart=self.staged('fingerprint_chart',b'chart')
        meta=dict(id='x',title='One',artist='Test',audio='audio',charts={'opening':{'file':'chart','level':3}})
        package=SimpleNamespace(metadata=meta,charts=meta['charts'],asset=lambda name:{'audio':audio,'chart':chart}[name])
        first=self.manager.fingerprint(package)
        meta['title']='Two';second=self.manager.fingerprint(package)
        self.assertNotEqual(first,second)
        chart.write_bytes(b'new chart')
        self.assertNotEqual(second,self.manager.fingerprint(package))
    def test_generated_sparse_registration_preserves_jacket_credit(self):
        song=dict(id='credits',title='Title',artist='Artist',jacket_artist='Cover Credit',audio=self.source/'data.win',chart_id='custom_manager_207',song_id=207,bpm=120,charts={'encore':{'level':4,'designer':'Mapper'}})
        script=backend.make_multi_script([song],self.root,207)
        self.assertIn('custom_song_0.jacket_artist = '+backend.gml('Cover Credit')+';',script)
        self.assertIn('custom_song_0.allowed_difficulties = [3];',script)
        self.assertIn('custom_wanted_diff',script)
        self.assertIn('confirm_menu.difficulties[confirm_menu.selected_difficulty].id',script)
    def test_apotheosis_is_direct_id5_and_preserves_prelude(self):
        song=dict(id='alt',title='Title',artist='Artist',audio=self.source/'data.win',chart_id='custom_manager_207',song_id=207,bpm=120,charts={'encore':{'level':9,'designer':'Base'},'apotheosis':{'level':15.5,'designer':'Alternate'}})
        script=backend.make_multi_script([song],self.root,207)
        self.assertIn('custom_song_0.allowed_difficulties = [3, 5];',script)
        self.assertIn('custom_song_0.custom_difficulties = [false, false, false, true, false, true];',script)
        self.assertNotIn('custom_song_0.difficulty_constant_5',script)
        self.assertIn('custom_song_0.difficulty_constant_6 = 15.5;',script)
        self.assertIn('custom_song_0.custom_apotheosis = {level: 15.5',script)
        self.assertNotIn('keyboard_check_pressed(vk_tab)',script)
        self.assertNotIn('custom_apotheosis_active',script)
        self.assertIn('if (arg1 == 5) arg2.force_chart = ""APOTHEOSIS"";',script)
        self.assertIn('global.songdifficultyconstant = song.difficulty_constant_6;',script)
        self.assertIn('gml_Object_o_transitionsong_Alarm_0', script)
        self.assertIn('jacket_designer = struct_get_fallback(song,', script)
        self.assertIn('variable_struct_set(custom_score_record, ""score"", 0)',script)
        self.assertIn('custom_d < 6',script)
        self.assertIn('custom_rows',script)
        self.assertIn('custom_footer_id',script)
        self.assertNotIn('TAB: switch',script)
    def test_apotheosis_standalone_has_its_own_slot_and_no_encore(self):
        song=dict(id='alt',title='Title',artist='Artist',audio=self.source/'data.win',chart_id='custom_manager_207',song_id=207,bpm=120,charts={'apotheosis':{'level':15}})
        script=backend.make_multi_script([song],self.root,207)
        self.assertIn('custom_song_0.allowed_difficulties = [5];',script)
        self.assertIn('custom_song_0.has_encore = false;',script)
        self.assertIn('custom_song_0.custom_has_apotheosis = true;',script)
        self.assertIn('custom_song_0.difficulty_constant_6 = 15;',script)
        self.assertIn('song_list[song].allowed_difficulties',script)
    def test_restore_clean_preserves_library_ids_and_previous_build(self):
        self.install(b'custom archive')
        package=self.manager.library/'song_a';package.mkdir();(package/'data.toml').write_text('owned package')
        assignments=copy.deepcopy(self.manager.state['assignments'])
        self.manager.restore_clean()
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'clean stock data')
        self.assertEqual(self.manager.state['assignments'],assignments)
        self.assertEqual(self.manager.state['installed_ids'],[])
        self.assertEqual((package/'data.toml').read_text(),'owned package')
        self.assertEqual(backend.sha256(Path(self.manager.state['backup'])),self.stock)
        self.manager.rollback()
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'custom archive')
    def test_stock_score_factory_is_preserved_and_postloads_use_string_members(self):
        song=dict(id='scores',title='Title',artist='Artist',audio=self.source/'data.win',chart_id='custom_manager_207',song_id=207,bpm=120,charts={'apotheosis':{'level':15}})
        script=backend.make_multi_script([song],self.root,207)
        self.assertNotIn('Queue(scores,',script)
        self.assertNotIn('scores[5] = {score:',script)
        self.assertIn('variable_clone(global.highscores.normal[custom_score_i][0])',script)
        self.assertIn('variable_struct_set(custom_score_record, ""score"", 0)',script)
        self.assertIn('global.highscores_at_load.normal[custom_score_i][5]',script)
        for caller in ['gml_Object_initiategame_Other_10','gml_GlobalScript_define_options','gml_Object_o_profile_select_2023boot_Step_0']:
            self.assertIn(caller,script)
        verify=backend.make_verify_script([song],self.root)
        self.assertIn('Stock score-loader assembly changed',verify)
        self.assertIn('pop.v.v self.score',verify)
    def test_cancellation_never_enters_install(self):
        with self.assertRaises(backend.Cancelled):self.manager.build(['not-yet-imported'],cancel=lambda:True)
        self.assertEqual((self.root/'game/data.win').read_bytes(),b'clean stock data')

if __name__=='__main__':unittest.main()
