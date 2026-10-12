"""Synthetic fixtures only; records are not real editorial approvals."""
import argparse
import contextlib
import copy
import io
import os
from pathlib import Path
import subprocess
import unittest

import test_pipeline as legacy
from policies import (WORD_POLICY, VISUAL_POLICY, FRAME_POLICY, DELIVERY_POLICY,
                      EDITORIAL_POLICY, count_report, count_errors)

pipeline = legacy.pipeline
read_json, write_json, sha256 = legacy.read_json, legacy.write_json, legacy.sha256


class CurrentPolicyTests(unittest.TestCase):
    setUp = legacy.PipelineTests.setUp
    tearDown = legacy.PipelineTests.tearDown
    rendered = legacy.PipelineTests.rendered

    def fill(self):
        rows = legacy.PipelineTests.fill(self)
        j = self.job
        j.update(word_count_policy=WORD_POLICY, visual_policy=VISUAL_POLICY,
                 delivery_policy=DELIVERY_POLICY, editorial_policy=EDITORIAL_POLICY,
                 preview=None, layout_report='analysis/mobile-layout-check.json')
        j['qa'].update(require_mobile_preview=False, require_mobile_layout_check=True,
                       recommended_minimum_visible_units=2, recommended_maximum_visible_units=2)
        j['source_dedup'].update(checked_at='synthetic', scope='temporary test fixture only',
            event_summary='synthetic event', decision='unused', reason='synthetic fixture, no production sources')
        j['visual_plan'].update(planned_visible_units=2, collage_frame_policy=FRAME_POLICY)
        for name in ('content-value-review.md', 'voice-review.md', 'visual-review.md'):
            (self.root / 'analysis' / name).write_text(
                'SYNTHETIC UNIT TEST RECORD ONLY. No factual verification, image review or platform checks occurred.', encoding='utf-8')
        j['blocks'] = [dict(type='lead', text='证据' * 195)]
        j['collage_manifests'] = []
        for i in range(2):
            output = f'assets/collages/new-{i}.png'
            legacy.Image.new('RGB', (300, 400), ('navy', 'green')[i]).save(self.root / output)
            manifest_path = f'assets/collages/new-{i}.collage.json'
            sources = [dict(r, sha256=sha256(self.root / r['path'])) for r in rows[i*2:i*2+2]]
            write_json(self.root / manifest_path, dict(kind='video-evidence-collage',
                layout='single-column-original-ratio', frame_count=2, claim=f'synthetic claim {i}',
                source_sha256=j['source']['sha256'], sources=sources, output=output,
                output_sha256=sha256(self.root / output), public_annotations={
                    'title': '测试', 'items': [dict(source_index=1, text='合成说明',
                        basis='frame', evidence_ref='synthetic fixture', placement='caption band')]}))
            j['blocks'].append(dict(type='figure', visual='video-evidence-collage', src=output,
                frame_count=2, collage_manifest=manifest_path, caption='合成测试说明'))
            if i == 0:
                j['blocks'].append(dict(type='paragraph', text='这是另一条合成证据。'))
            j['collage_manifests'].append(manifest_path)
        write_json(self.path, j)
        return rows

    def reviewed_fixture(self):
        j = self.job
        report = dict(html_sha256=sha256(self.root / j['output']), checked_at='SYNTHETIC',
            viewport_width=375, broken_images=0, horizontal_overflow=False, passed=True,
            scope='Synthetic unit test report, not a browser observation')
        write_json(self.root / j['layout_report'], report)
        j['build']['layout_sha256'] = sha256(self.root / j['layout_report'])
        j['qa']['review'] = dict(checked_at='SYNTHETIC', input_fingerprint=j['build']['input_fingerprint'],
            notes_path='analysis/visual-review.md', mobile_375_checked=True, cover_text_checked=True,
            source_subjects_checked=True, human_voice_checked=True, facts_checked=True, title_audit_notes='synthetic fixture')
        write_json(self.path, j)

    def test_init_current_defaults(self):
        self.assertEqual(self.job['delivery_policy'], DELIVERY_POLICY)
        self.assertIsNone(self.job['preview'])
        self.assertFalse(self.job['qa']['require_mobile_preview'])
        self.assertTrue(self.job['qa']['require_mobile_layout_check'])
        self.assertEqual(self.job['visual_plan']['planned_visible_units'], 2)
        self.assertEqual(self.job['visual_plan']['collage_frame_policy'], FRAME_POLICY)

    def test_count_all_visible_text(self):
        html = '<main><h1>标题？</h1><div class="byline">来源甲</div><p>中A1，&amp; \n</p><figure><img alt="不计"><figcaption>图注。</figcaption></figure><section class="sources"><a href="https://example.invalid">官方</a></section><script>不计</script></main>'
        r = count_report(html, html)
        self.assertEqual(r['body_visible_chars'], 3+5+3+2)
        self.assertEqual(r['copy_all_visible_chars'], r['body_visible_chars']+3)
        self.assertIsNone(r['wechat_editor_count'])

    def test_count_boundaries_and_h1(self):
        for length, expected in [(399, False), (400, True), (500, True), (501, False)]:
            html = f'<main><p>{"文" * length}</p></main>'
            self.assertEqual(not count_errors(count_report(html, html)), expected)
        html = f'<main><h1>标题</h1><p>{"文" * 500}</p></main>'
        self.assertTrue(count_errors(count_report(html, html)))

    def test_count_before_media_creation(self):
        self.job['blocks'] = [dict(type='paragraph', text='文' * 410),
            dict(type='figure', src='assets/missing.png', caption='说明')]
        r = pipeline.word_report(self.job, self.root)
        self.assertIsNone(r['html_sha256'])
        self.assertEqual(count_errors(r), [])

    def test_current_full_validation_three_files(self):
        self.rendered(); self.reviewed_fixture()
        self.assertEqual(legacy.content_checks(self.job, self.root), [])
        self.assertEqual(legacy.final_checks(self.job, self.root), [])
        with contextlib.redirect_stdout(io.StringIO()):
            pipeline.cmd_validate(argparse.Namespace(job=str(self.path)))
        manifest = read_json(self.root / 'deliver/delivery-manifest.json')
        self.assertEqual(manifest['files_required'], 3)
        self.assertEqual(set(manifest['files']), {'article', 'vertical_3_4', 'horizontal_2_35_1'})
        self.assertFalse((self.root / 'deliver/mobile_preview.png').exists())

    def test_render_saves_overlimit_report_and_fails(self):
        self.fill(); self.job['blocks'][0]['text'] = '文' * 501; write_json(self.path, self.job)
        with self.assertRaises(pipeline.ArticleError):
            pipeline.cmd_render(argparse.Namespace(job=str(self.path)))
        self.assertTrue((self.root / 'analysis/word-count.json').is_file())

    def test_missing_dedup_and_reviews_rejected(self):
        self.fill(); self.job['source_dedup']['decision'] = 'pending'
        self.job['editorial_records']['voice'] = 'analysis/missing.md'
        errors = legacy.content_checks(self.job, self.root)
        self.assertTrue(any('dedup' in e for e in errors))
        self.assertTrue(any('voice review missing' in e for e in errors))

    def test_missing_annotation_rejected(self):
        self.fill(); p = self.root / self.job['collage_manifests'][0]
        record = read_json(p); record.pop('public_annotations'); write_json(p, record)
        self.assertTrue(any('in-image' in e for e in legacy.content_checks(self.job, self.root)))

    def test_cross_collage_duplicates_rejected(self):
        self.fill(); p = self.root / self.job['collage_manifests'][1]
        record = read_json(p); record['sources'] = read_json(self.root / self.job['collage_manifests'][0])['sources']
        write_json(p, record)
        self.assertTrue(any('duplicate source frames across' in e for e in legacy.content_checks(self.job, self.root)))

    def test_third_figure_rejected(self):
        self.fill(); self.job['blocks'].append(copy.deepcopy(self.job['blocks'][1]))
        self.assertTrue(any('exactly two' in e for e in legacy.content_checks(self.job, self.root)))

    def test_export_dimension_budget(self):
        self.fill(); p = self.root / self.job['collage_manifests'][0]; m = read_json(p)
        legacy.Image.new('RGB', (100, 4097), 'navy').save(self.root / m['output'])
        m['output_sha256'] = sha256(self.root / m['output']); write_json(p, m)
        self.assertTrue(any('4096px' in e for e in legacy.content_checks(self.job, self.root)))

    def test_stale_html_and_layout_rejected(self):
        self.rendered(); self.reviewed_fixture()
        output = self.root / self.job['output']
        output.write_text(output.read_text(encoding='utf-8-sig').replace('这是另一条合成证据。', '改变正文'), encoding='utf-8')
        self.assertFalse(pipeline.word_report(self.job, self.root)['text_matches_job'])
        self.assertTrue(any('stale' in e for e in legacy.final_checks(self.job, self.root)))

    def test_layout_cannot_be_disabled_by_qa_flag(self):
        self.rendered(); self.job['qa']['require_mobile_layout_check'] = False
        self.assertTrue(legacy.final_checks(self.job, self.root))

    @unittest.skipUnless(legacy.FONT, 'set ARTICLE_FONT for Chinese collage test')
    def test_real_compact_collages_two_three_four_and_focus(self):
        rows = self.fill()
        rows[0].update(public_text='合成区域说明', basis='frame', evidence_ref='synthetic test',
                       focus={'rect':[20,20,100,80], 'shape':'circle', 'zoom':True})
        for count in (2, 3, 4):
            spec = dict(title='合成图像布局测试', claim='not real evidence',
                output=f'assets/collages/built-{count}.jpg', frames=rows[:count])
            output, manifest = legacy.build(self.path, spec, legacy.FONT)
            data = read_json(manifest)
            self.assertEqual(data['frame_count'], count)
            self.assertEqual(data['public_annotations']['items'][0]['text'], '合成区域说明')
            self.assertEqual(len(data['edits']), 1)
            self.assertGreater(data['edits'][0]['zoom_output_px'][0], 80)
            self.assertLessEqual(output.stat().st_size, 3*1024*1024)
            self.assertLessEqual(max(data['export']['width'], data['export']['height']), 4096)
            if os.environ.get('TEST_ARTIFACT_DIR') and count == 2:
                target = Path(os.environ['TEST_ARTIFACT_DIR']); target.mkdir(parents=True, exist_ok=True)
                legacy.shutil.copy2(output, target / 'synthetic-compact-collage.jpg')
        with self.assertRaises(ValueError):
            legacy.build(self.path, dict(spec, output='assets/collages/too-many.jpg', frames=rows[:5]), legacy.FONT)

    @unittest.skipUnless(os.environ.get('RUN_BROWSER_TEST') == '1', 'opt-in browser test')
    def test_real_check_layout_and_preview_alias_no_png(self):
        self.rendered()
        pipeline.cmd_preview(argparse.Namespace(job=str(self.path)))
        j = read_json(self.path); report = read_json(self.root / j['layout_report'])
        self.assertTrue(report['passed'])
        self.assertEqual(report['html_sha256'], sha256(self.root / j['output']))
        self.assertEqual(report['viewport_width'], 375)
        self.assertFalse((self.root / 'deliver/mobile_preview.png').exists())
        self.assertEqual(list((self.root / 'deliver').glob('*.png')), [])

    @unittest.skipUnless(os.environ.get('RUN_BROWSER_TEST') == '1', 'opt-in browser test')
    def test_real_layout_failure_reports(self):
        renderer = Path(pipeline.__file__).with_name('render_local_html_mobile.js')
        for i, content in enumerate(('<img src="missing.png">', '<div style="width:2000px">overflow</div>')):
            html = self.root / f'bad-{i}.html'; report = self.root / f'bad-{i}.json'
            html.write_text(f'<html><body>{content}</body></html>', encoding='utf-8')
            result = subprocess.run([os.environ.get('NODE','node'), str(renderer), '--layout-check', str(html), str(report)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(read_json(report)['passed'])


if __name__ == '__main__':
    unittest.main()
