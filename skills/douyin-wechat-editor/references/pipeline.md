# 可运行工具与任务清单

所有路径以当前Skill目录为起点，不依赖原作者电脑目录。下例SCRIPT_DIR为本技能scripts绝对路径，其余路径/字体按实际环境代入。Python须3.10+和Pillow；check-layout另需Node20+/Playwright/Chromium。可设置FFMPEG、FFPROBE、NODE、NODE_PATH、BROWSER_EXE、ARTICLE_FONT；不设置无关全局变量。依赖诊断不证明抖音控制、ImageGen或内容审核通过。

## 命令

```sh
python SCRIPT_DIR/source_tools.py doctor
python SCRIPT_DIR/article_pipeline.py init --project-root JOB_ROOT --slug YYYYMMDD-account-topic --account dream
python SCRIPT_DIR/source_tools.py bind JOB_ROOT/YYYYMMDD-account-topic/article-job.json --video source/video.mp4
python SCRIPT_DIR/source_tools.py frame JOB_ROOT/YYYYMMDD-account-topic/article-job.json --at 00:04.6 --output assets/frames/frame-0046.png
python SCRIPT_DIR/build_evidence_collage.py --job JOB_ROOT/YYYYMMDD-account-topic/article-job.json --spec JOB_ROOT/YYYYMMDD-account-topic/analysis/collage-1.json --font FONT_PATH
python SCRIPT_DIR/article_pipeline.py count JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py render JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py check-layout JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py validate JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py status JOB_ROOT/YYYYMMDD-account-topic/article-job.json
```

init拒绝覆盖旧目录，slug仅字母数字/连字符/下划线。先将已获准使用的视频置入source/，填写source.creator/claim/rights_status，再bind/frame。bind读取真实时长与哈希；换视频必须新任务，不能改哈希沿用旧证据。所有本地资源用任务内相对路径，禁止引用父目录或另一任务。

frame原比例无叠字，生成.frame.json侧车；拼图工具不覆盖旧输出，用版本名。抽帧与拼图是确定性处理，不使用ImageGen改变证据。正式封面必须通过ImageGen另做。

## article-job.json

init生成schema_version=8和空审稿字段，publish_decision默认hold。新版策略由明确policy字段路由，不以schema号迁移旧稿：

```json
{
  "word_count_policy": "wechat-visible-text-400-500-2026-10-13",
  "visual_policy": "two-annotated-collages-2026-10-11",
  "delivery_policy": "article-and-two-covers-2026-10-12",
  "editorial_policy": "substantive-value-and-voice-2026-10-12",
  "preview": null,
  "layout_report": "analysis/mobile-layout-check.json"
}
```

visual_plan.collage_frame_policy为compact-2-4-2026-10-12；qa.require_mobile_preview=false、require_mobile_layout_check=true。新策略的旧preview命令会自动走无截图check-layout，不创建PNG。历史没有新policy仍按原门槛；不批量迁移、删除或覆盖在制任务。

| 字段 | 内容 |
| --- | --- |
| account/slug/identity | 唯一账号、任务名、绑定视频SHA256；identity由bind写入 |
| source | path/sha256/duration_seconds、creator、claim、page_url、published_at、event_date、checked_at、rights_status |
| research | mode=autonomous或supplied；自主模式记录4个不同新tab的id/purpose、mute_checked、≥3候选、freshness_checked_at、selected_reason |
| workflow | 当前stage、next_action、timings；用于续做，不代表发表状态 |
| title/graphic_title/title_strategy | 两条最终疑问标题；候选、评分、证据、判断等按editorial.md |
| originality/digital_decision | 事实、增量、比较、机制、读者决策和账号附加门槛 |
| blocks | 结构化正文和图片，见下例 |
| sources/evidence_items | 外部来源和逐条证据，见research.md |
| cover/imagegen_highlights | 双封面与可选亮点图，见visuals.md |
| visual_plan/collage_manifests | 实际可见单元数、例外理由及任务相对manifest路径列表 |
| output/layout_report/evidence.ledger_output | 本地HTML、无截图375px检查JSON和内部台账路径；preview=null |
| source_dedup/editorial_records | 全历史视频/事件查重及实质价值/语气审稿路径 |
| build | render/check-layout写入当前输入指纹及文件哈希，不手写或伪造 |
| qa.review | 真正完成目视、语义和事实检查后填写，见下文 |

正文块type可选lead/paragraph/heading/question/notice/figure，文字仅text，不嵌任意HTML：

```json
{"type":"paragraph","text":"有依据的正文。"}
```

```json
{"type":"figure","visual":"video-evidence-collage","src":"assets/collages/chain-1.jpg","frame_count":2,"collage_manifest":"assets/collages/chain-1.collage.json","caption":"本组简短说明，也计正文字数"}
```

```json
{"type":"paragraph","text":"两组拼图之间解释相关主张，不能连续贴成长墙。"}
```

然后放第二个不同主张的video-evidence-collage。新策略不使用第三图。旧任务的detail-video-frame/annotated-video-frame保留source_frame/source_timestamp/transform_note，external-evidence保留source_id，不能借改标签逃避新验收。

拼图spec含title/claim/output/frames。frames为2–4条有效、不重复原帧；至少一条有实际public_text，其他可不加说明。label是内部证据标签，不默认公开。示例仅为字段结构，内容必须替换成真实材料：

```json
{
  "title": "本组具体亮点", "claim": "本组证明的独立问题",
  "output": "assets/collages/chain-1.jpg",
  "frames": [
    {"path":"assets/frames/frame-0046.png", "timestamp":"00:04.6", "label":"内部节点",
     "public_text":"短说明指出画面中的实际差别", "basis":"frame", "evidence_ref":"证据台账对应项"},
    {"path":"assets/frames/frame-0062.png", "timestamp":"00:06.2", "label":"另一个有效节点"}
  ]
}
```

可选每帧focus为`{"rect":[10,20,80,100],"shape":"circle","zoom":true}`，坐标按真实原图像素，不照抄示例。circle/box边线不能遮挡关键内容；局部放大不另计帧。生成器记录实际public_annotations与edits；manifest加入collage_manifests，figure数量/引用与实际成品一致。超4096px/3MiB须删冗余或改合理导出，不能把原帧硬缩到不可读。

count无HTML时直接估算job，不要求先生成媒体；有HTML则重计并核对job文本。render写analysis/word-count.json，超字保留草稿/报告并失败。完整正文含图注/来源等400–500，含H1≤500，固定检查不以qa调大绕过；微信计数未实测不得填成已核验。

## 标题记录

title_strategy由init列全空字段。每候选包含text/model/score/topic_score/breakdown/evidence_basis/topic_tension_checked/closed_question_rejected。两套最终值必须命中各自候选，至少4不同model。recent_title_overlap_checked、question_pattern_overlap_checked、question_mark_checked、answer_in_lead、flatness_checked、thumbnail_punch_checked、topic_tension_checked、closed_question_rejected只在真实审核后填true；evidence_basis等使用具体依据而非“已检查”。

标题审计中的词库仅启发式，不知道事实真假。出现“少于两种钩子”等提示，需改题或在qa.review.title_audit_notes写实际语义复核；不能为了过词库往标题乱加数字。最终20字符与双问句/评分门槛不会被这段说明放宽。

## QA记录和过期检测

render要求来源及编辑门槛满足，生成待QA的HTML和台账。预先实际写content-value-review.md、voice-review.md、visual-review.md并记录路径。check-layout只加载本地/内嵌资源，用隔离375px浏览器检查坏图/横向溢出，写当前HTML SHA256/时间/尺寸JSON，不截图、不打开用户页面、不读登录配置。DOM检查不证明文字可读或内容真实；仍实际查看原帧、拼图与双封面。HTML可用于复制，但未实际插入微信时不能保证无结构提示或粘贴成功。

目视后创建analysis/editorial-review.md，写核验了哪些原帧、数字、两标题、中文封面字、中央方裁、375px拼图可读性、去AI腔删改和未决问题；然后填：

```json
{
  "checked_at":"实际检查时间与时区",
  "input_fingerprint":"复制当前build.input_fingerprint",
  "notes_path":"analysis/editorial-review.md",
  "mobile_375_checked":true,
  "cover_text_checked":true,
  "source_subjects_checked":true,
  "human_voice_checked":true,
  "facts_checked":true,
  "title_audit_notes":"若有启发式提示，记录语义复核理由"
}
```

这些true是审核记录而非自动证明，不能预填。mobile_375_checked表示真实按375px尺度看过图片/必要局部视口，不是check-layout自动打勾。改正文/标题/图/封面/审稿底稿后旧指纹作废，render清空review，重新check-layout与实际审稿。源视频变更、图被替换、源帧不匹配、拼图重复、缺增量/双封面均不能交付。validate检查当前HTML及layout哈希，输出deliver/delivery-manifest.json仅列HTML+双封面三项（历史仍四项），不是自动发表。

最终validate可证明本地结构一致，不能证明来源真实、版权授权、平台通过或推荐效果。未通过保留底稿和错误，不能回报PASS。
