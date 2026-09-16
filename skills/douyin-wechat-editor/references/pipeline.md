# 可运行工具与任务清单

所有路径以当前Skill目录为起点，不依赖原作者电脑目录。下例中的SCRIPT_DIR/JOB_ROOT/VIDEO/中文字体路径由实际环境代入，不原样照抄占位值。Python须3.10+和Pillow；preview另需Node/Playwright/Chromium。可设置FFMPEG、FFPROBE、NODE、NODE_PATH、BROWSER_EXE、ARTICLE_FONT；不设置无关全局变量。

## 命令

```sh
python SCRIPT_DIR/source_tools.py doctor
python SCRIPT_DIR/article_pipeline.py init --project-root JOB_ROOT --slug YYYYMMDD-account-topic --account dream
python SCRIPT_DIR/source_tools.py bind JOB_ROOT/YYYYMMDD-account-topic/article-job.json --video source/video.mp4
python SCRIPT_DIR/source_tools.py frame JOB_ROOT/YYYYMMDD-account-topic/article-job.json --at 00:04.6 --output assets/frames/frame-0046.png
python SCRIPT_DIR/build_evidence_collage.py --job JOB_ROOT/YYYYMMDD-account-topic/article-job.json --spec JOB_ROOT/YYYYMMDD-account-topic/analysis/collage-1.json --font FONT_PATH
python SCRIPT_DIR/article_pipeline.py render JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py preview JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py validate JOB_ROOT/YYYYMMDD-account-topic/article-job.json
python SCRIPT_DIR/article_pipeline.py status JOB_ROOT/YYYYMMDD-account-topic/article-job.json
```

init拒绝覆盖旧目录，slug仅字母数字/连字符/下划线。先将已获准使用的视频置入source/，填写source.creator/claim/rights_status，再bind/frame。bind读取真实时长与哈希；换视频必须新任务，不能改哈希沿用旧证据。所有本地资源用任务内相对路径，禁止引用父目录或另一任务。

frame原比例无叠字，生成.frame.json侧车；拼图工具不覆盖旧输出，用版本名。抽帧与拼图是确定性处理，不使用ImageGen改变证据。正式封面必须通过ImageGen另做。

## article-job.json

init生成schema_version=8和空字段，publish_decision默认hold。不要把旧schema7任务直接改版本号当迁移成功。

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
| output/preview/evidence.ledger_output | 本地HTML、375px预览和内部台账路径 |
| build | render/preview写入当前输入指纹及文件哈希，不手写或伪造 |
| qa.review | 真正完成目视、语义和事实检查后填写，见下文 |

正文块type可选lead/paragraph/heading/question/notice/figure，文字仅text，不嵌任意HTML：

```json
{"type":"paragraph","text":"有依据的正文。"}
```

```json
{"type":"figure","visual":"direct-video-frame","src":"assets/frames/frame-0046.png","source_timestamp":"00:04.6","caption":"本帧已核实重点"}
```

```json
{"type":"figure","visual":"video-evidence-collage","src":"assets/collages/chain-1.png","frame_count":4,"collage_manifest":"assets/collages/chain-1.collage.json","caption":"本组不同节点证明的主张"}
```

detail-video-frame/annotated-video-frame另填source_frame、source_timestamp、transform_note；external-evidence填对应sources.id的source_id。两类都须实际制作、目视，不能标注类型却不加来源。

拼图spec含title/claim/output/frames。frames是4至6条 `{ "path":"assets/frames/frame-0046.png", "timestamp":"00:04.6", "label":"本帧重点" }`；每条不同有效节点。输出manifest路径添加到collage_manifests，figure.frame_count与之匹配。

## 标题记录

title_strategy由init列全空字段。每候选包含text/model/score/topic_score/breakdown/evidence_basis/topic_tension_checked/closed_question_rejected。两套最终值必须命中各自候选，至少4不同model。recent_title_overlap_checked、question_pattern_overlap_checked、question_mark_checked、answer_in_lead、flatness_checked、thumbnail_punch_checked、topic_tension_checked、closed_question_rejected只在真实审核后填true；evidence_basis等使用具体依据而非“已检查”。

标题审计中的词库仅启发式，不知道事实真假。出现“少于两种钩子”等提示，需改题或在qa.review.title_audit_notes写实际语义复核；不能为了过词库往标题乱加数字。最终20字符与双问句/评分门槛不会被这段说明放宽。

## QA记录和过期检测

render要求来源及主要编辑门槛满足，生成待QA的本地HTML和内部台账；preview用375px无头浏览器，只加载本地/内嵌资源，检查坏图和横向溢出，不打开用户页面。HTML可用于本地查看/复制，但平台编辑器可能清洗CSS，未实际插入平台时不能保证“零结构提示”。遇提示核对平台当前文档，只用标准text-align和自适应宽度，不声称已通过平台检测。

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

这些true是审核记录而非自动证明，不能预填。preview完成前不能填写mobile_375_checked。改正文/标题/图/封面/台账等后旧指纹作废，重新render会清空review，必须重新预览与审核。源视频变更、图被替换、源帧不匹配、拼图网格或重复图、缺失增量/双封面均不能交付为完成。

最终validate可证明本地结构一致，不能证明来源真实、版权授权、平台通过或推荐效果。未通过保留底稿和错误，不能回报PASS。
