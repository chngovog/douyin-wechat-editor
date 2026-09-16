"""Synthetic fixtures only: QA booleans here are not real editorial approvals."""
import argparse
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills' / 'douyin-wechat-editor' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from PIL import Image
import article_pipeline as pipeline
from build_evidence_collage import build
from integrity import content_checks, fingerprint, final_checks, inside, read_json, sha256, write_json
import source_tools

FONT = os.environ.get('ARTICLE_FONT')


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wechat-skill-test-')
        self.base = Path(self.temp.name)
        self.root = self.base / 'test-article'
        with contextlib.redirect_stdout(io.StringIO()):
            pipeline.cmd_init(argparse.Namespace(project_root=str(self.base), slug='test-article',
                account='dream', title='', graphic_title=''))
        self.path = self.root / 'article-job.json'
        self.job = read_json(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def fill(self):
        j = self.job
        video = self.root / 'source/video.mp4'
        video.write_bytes(b'SYNTHETIC TEST ONLY, NOT A PLAYABLE SOURCE')
        j['source'].update(path='source/video.mp4', creator='合成测试', claim='仅用于软件测试',
                           duration_seconds=60.0, sha256=sha256(video), rights_status='synthetic test fixture')
        j['identity'] = dict(account='dream', slug='test-article', source_sha256=sha256(video))
        rows = []
        for i in range(6):
            relative = f'assets/frames/frame-{i}.png'; p = self.root / relative
            Image.new('RGB', (200, 120), (i * 30, 40, 90)).save(p)
            write_json(p.with_suffix('.frame.json'), dict(seconds=i, sha256=sha256(p), source_sha256=sha256(video)))
            rows.append(dict(path=relative, timestamp=f'00:0{i}', label=f'合成节点{i}'))
        # Deterministic fixture manifest. A separate test exercises the actual collage builder.
        output = 'assets/collages/test.png'; Image.new('RGB', (200, 800), 'navy').save(self.root / output)
        manifest = dict(kind='video-evidence-collage', layout='single-column-original-ratio', frame_count=4,
                        source_sha256=sha256(video), output=output, output_sha256=sha256(self.root / output),
                        sources=[dict(r, sha256=sha256(self.root / r['path'])) for r in rows[:4]])
        manifest_path = 'assets/collages/test.collage.json'
        write_json(self.root / manifest_path, manifest)
        j['collage_manifests'] = [manifest_path]
        j['blocks'] = [dict(type='lead', text='证据' * 250),
            dict(type='figure', visual='direct-video-frame', src=rows[4]['path'], source_timestamp='00:04'),
            dict(type='figure', visual='video-evidence-collage', src=output, frame_count=4, collage_manifest=manifest_path),
            dict(type='figure', visual='direct-video-frame', src=rows[5]['path'], source_timestamp='00:05')]
        j['visual_plan'].update(planned_visible_units=3, structure_exception_reason='合成夹具仅用于测试一种拼图及两帧的结构')
        j['originality'].update(source_duration_seconds=60.0, publish_decision='publish',
            source_summary='合成摘要', structure_model='合成比较', mechanism_or_impact='合成机制',
            reader_decision='合成判断', recent_similarity_checked=True, distinct_from_recent='合成测试没有历史文章',
            verifiable_facts=[dict(claim=f'合成事实{i}', evidence=f'测试依据{i}', article_use=f'测试用途{i}') for i in range(6)],
            independent_additions=[dict(claim=f'合成增量{i}', type='test', source='test', verification='test', article_use='test', independently_verifiable=True) for i in range(2)],
            comparisons=[dict(subject='甲', baseline='乙', finding='合成差异', evidence='测试')])
        j['evidence_items'] = [dict(claim='合成测试事实', type='test', evidence='fixture', boundary='not editorial approval')]
        j['title'] = '测试队先丢8分又反超，换人赢在哪？'
        j['graphic_title'] = '测试队只剩8秒，还要换人吗？'
        s = j['title_strategy']
        for key, value in list(s.items()):
            if value is False: s[key] = True
            elif value == '': s[key] = f'合成测试{key}'
        s['debate_sides'] = ['合成甲', '合成乙']; s['evidence_basis'] = ['合成证据']
        s['article_question_type'] = 'result'; s['graphic_question_type'] = 'choice'
        for key, selected in [('article_candidates', j['title']), ('graphic_candidates', j['graphic_title'])]:
            s[key] = [dict(text=selected if i == 0 else f'测试队{i}号还要换人吗？', model=f'model{i}',
                           score=10, topic_score=2, evidence_basis=['test'], topic_tension_checked=True,
                           closed_question_rejected=True) for i in range(4)]
        c = j['cover']
        for key, value in list(c.items()):
            if value is False and key != 'evidence_use': c[key] = True
            elif value == '': c[key] = '合成检查'
        c.update(text='丢8分就急着换？', text_method='imagegen-verified',
                 text_candidates=['丢8分就急着换？', '换人就能赢吗？', '还剩8秒不换吗？'],
                 visual_concepts=['合成A', '合成B'], source_frame=rows[0]['path'], source_timestamp='00:00',
                 prompts={'vertical_3_4':'SYNTHETIC TEST', 'horizontal_2_35_1':'SYNTHETIC TEST'})
        for key, size in [('vertical_3_4',(108,144)), ('horizontal_2_35_1',(235,100))]:
            Image.new('RGB', size, 'gray').save(self.root / c['outputs'][key])
        write_json(self.path, j)
        return rows

    def rendered(self):
        self.fill()
        with contextlib.redirect_stdout(io.StringIO()):
            pipeline.cmd_render(argparse.Namespace(job=str(self.path)))
        self.job = read_json(self.path)

    def reviewed_fixture(self):
        j = self.job
        Image.new('RGB', (375, 1000), 'white').save(self.root / j['preview'])
        j['build']['preview_sha256'] = sha256(self.root / j['preview'])
        note = self.root / 'analysis/review.md'
        note.write_text('SYNTHETIC FIXTURE ONLY. This represents a review record for unit testing, not factual or image approval.', encoding='utf-8')
        j['qa']['review'] = dict(checked_at='test time', input_fingerprint=j['build']['input_fingerprint'],
            notes_path='analysis/review.md', mobile_375_checked=True, cover_text_checked=True,
            source_subjects_checked=True, human_voice_checked=True, facts_checked=True, title_audit_notes='synthetic fixture')
        write_json(self.path, j)

    def test_init_hold(self):
        self.assertEqual(self.job['originality']['publish_decision'], 'hold')
        self.assertEqual(self.job['cover']['text_method'], 'pending')

    def test_hold_cannot_render(self):
        self.fill(); self.job['originality']['publish_decision'] = 'hold'; write_json(self.path, self.job)
        with self.assertRaises(pipeline.ArticleError): pipeline.cmd_render(argparse.Namespace(job=str(self.path)))
        self.assertFalse((self.root / self.job['output']).exists())

    def test_path_escape(self):
        for value in ('../escape.html', str(self.base / 'escape.html'), ''):
            with self.assertRaises(ValueError): inside(self.root, value)

    def test_slug_escape(self):
        with self.assertRaises(pipeline.ArticleError):
            pipeline.cmd_init(argparse.Namespace(project_root=str(self.base), slug='../bad', account='dream'))

    def test_identity_and_source_change(self):
        self.fill(); self.job['account'] = 'basketball'
        self.assertTrue(any('identity mismatch' in e for e in content_checks(self.job, self.root)))
        (self.root / self.job['source']['path']).write_bytes(b'changed')
        self.assertTrue(any('hash changed' in e for e in content_checks(self.job, self.root)))

    def test_short_dream_needs_three_additions(self):
        self.fill(); self.job['source']['duration_seconds'] = 45
        self.job['originality']['source_duration_seconds'] = 45
        self.assertTrue(any('3 independent' in e for e in content_checks(self.job, self.root)))

    def test_missing_facts_rejected(self):
        self.fill(); self.job['originality']['verifiable_facts'] = []
        self.assertTrue(any('six complete' in e for e in content_checks(self.job, self.root)))

    def test_digital_gate(self):
        self.fill(); self.job['account'] = self.job['identity']['account'] = 'digital'
        self.assertTrue(any('digital_decision' in e for e in content_checks(self.job, self.root)))

    def test_wrong_frame_source(self):
        self.fill(); sidecar = self.root / 'assets/frames/frame-4.frame.json'
        record = read_json(sidecar); record['source_sha256'] = 'wrong'; write_json(sidecar, record)
        self.assertTrue(any('another source' in e for e in content_checks(self.job, self.root)))

    def test_duplicate_collage_and_grid(self):
        self.fill(); p = self.root / self.job['collage_manifests'][0]; record = read_json(p)
        record['sources'][1] = record['sources'][0]; record['layout'] = 'grid'; write_json(p, record)
        errors = content_checks(self.job, self.root)
        self.assertTrue(any('duplicate' in e for e in errors)); self.assertTrue(any('single-column' in e for e in errors))

    def test_cover_source_lock(self):
        self.fill(); self.job['cover']['added_nontext_visuals'] = ['new dragon']
        self.assertTrue(any('source lock' in e for e in content_checks(self.job, self.root)))

    def test_native_cover_text_required(self):
        self.fill(); self.job['cover']['text_method'] = 'pillow-overlay'
        self.assertTrue(any('native ImageGen' in e for e in content_checks(self.job, self.root)))

    def test_title_limit(self):
        self.fill(); self.job['graphic_title'] = '测' * 21 + '？'; errors = []
        pipeline.validate_titles(self.job, errors)
        self.assertTrue(any('20' in e for e in errors))

    def test_valid_synthetic_full_gate(self):
        self.rendered(); self.reviewed_fixture()
        self.assertEqual(content_checks(self.job, self.root), [])
        self.assertEqual(final_checks(self.job, self.root), [])
        with contextlib.redirect_stdout(io.StringIO()): pipeline.cmd_validate(argparse.Namespace(job=str(self.path)))

    def test_edit_invalidates_render(self):
        self.rendered(); self.reviewed_fixture(); self.job['blocks'][0]['text'] += '变化'
        self.assertTrue(any('inputs changed' in e for e in final_checks(self.job, self.root)))

    def test_asset_change_invalidates_render(self):
        self.rendered(); self.reviewed_fixture()
        Image.new('RGB', (108, 144), 'red').save(self.root / self.job['cover']['outputs']['vertical_3_4'])
        self.assertTrue(any('inputs changed' in e for e in final_checks(self.job, self.root)))

    def test_unreviewed_rejected(self):
        self.rendered()
        self.assertTrue(any('review' in e for e in final_checks(self.job, self.root)))

    def test_html_escaping(self):
        self.assertNotIn('<script>', pipeline.render_block(self.root, dict(type='paragraph', text='<script>bad</script>')))

    @unittest.skipUnless(FONT, 'set ARTICLE_FONT for collage rendering test')
    def test_real_collage_builder(self):
        rows = self.fill()
        spec = dict(title='合成测试的四个节点', claim='软件布局测试，不是真实视频', output='assets/collages/built.png', frames=rows[:4])
        output, manifest = build(self.path, spec, FONT)
        with Image.open(output) as image: self.assertGreater(image.height, image.width)
        self.assertEqual(read_json(manifest)['layout'], 'single-column-original-ratio')
        if os.environ.get('TEST_ARTIFACT_DIR'):
            target = Path(os.environ['TEST_ARTIFACT_DIR']); target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output, target / 'synthetic-collage.png')
        spec['output'] = 'assets/collages/duplicate.png'; spec['frames'][1] = spec['frames'][0]
        with self.assertRaises(ValueError): build(self.path, spec, FONT)

    @unittest.skipUnless(os.environ.get('RUN_BROWSER_TEST') == '1', 'opt-in headless Chromium test')
    def test_headless_mobile_preview(self):
        self.rendered()
        pipeline.cmd_preview(argparse.Namespace(job=str(self.path)))
        j = read_json(self.path)
        with Image.open(self.root / j['preview']) as image: self.assertEqual(image.width, 375)
        artifact_dir = os.environ.get('TEST_ARTIFACT_DIR')
        if artifact_dir:
            target = Path(artifact_dir); target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / j['preview'], target / 'synthetic-mobile-preview.png')

    @unittest.skipUnless(os.environ.get('RUN_FFMPEG_TEST') == '1', 'opt-in real ffmpeg fixture test')
    def test_real_bind_and_extract(self):
        self.job['source'].update(creator='Synthetic test', claim='generated test pattern')
        write_json(self.path, self.job)
        video = self.root / 'source/video.mp4'
        subprocess.run([source_tools.binary('ffmpeg'), '-v', 'error', '-f', 'lavfi', '-i',
            'testsrc=size=320x240:rate=2', '-t', '3', '-pix_fmt', 'yuv420p', '-n', str(video)], check=True)
        source_tools.bind(argparse.Namespace(job=str(self.path), video='source/video.mp4'))
        source_tools.frame(argparse.Namespace(job=str(self.path), at='00:01', output='assets/frames/extracted.png'))
        self.assertTrue((self.root / 'assets/frames/extracted.frame.json').is_file())
        job = read_json(self.path)
        self.assertEqual(job['source']['sha256'], sha256(video))

    def test_wrong_timestamp(self):
        self.fill(); self.job['blocks'][1]['source_timestamp'] = '00:33'
        self.assertTrue(any('timestamp mismatch' in e for e in content_checks(self.job, self.root)))

    def test_autonomous_needs_new_tabs_and_mute(self):
        self.fill(); self.job['research']['mode'] = 'autonomous'
        errors = content_checks(self.job, self.root)
        self.assertTrue(any('four distinct' in e for e in errors))
        self.assertTrue(any('mute not verified' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
