# 证据配图与双封面

## 正文两张说明拼图

新任务恰好2个figure，均为真实原视频节点的单列大图拼图，中间有正文，分别解释不同问题。不额外放第三张直图，完整主体/结果单帧可以是组内主画面。每组2–4个不重复有效节点，通常2–3个；放大同一帧不算新节点，两组不可重复源帧换说明。素材不足补证、换源或hold，不能伪造直图标签绕检查。

每张须有实际入图的材料专属短标题和关键节点短说明，指出“看哪里、差在哪、说明什么”。原字幕、HTML图注和内部label不替代图内解释。至少一个节点有public_text，通常一行、最多两行；画面清楚的其他节点可留空。说明留在画外，不能伪装人物原话或官方UI，不用几百字藏进图片绕字数。

## 单列大图拼接

每帧独占一行、占满内容宽度、保持原比例。默认不公开逐帧编号和精确时间码；时钟/比分原有信息不能擦除。按真实时序或明确标示的前后比较排列，不多列网格、不嫁接反应或编剧情。

使用source_tools.py frame提取绑定视频帧并保留.frame.json；build_evidence_collage.py输出图片和.collage.json，含帧路径/哈希、视频哈希、时间、说明、单列版式和输出哈希。脚本拒绝重复图像，近似画面是否重复表达仍需编辑检查。局部放大记录原帧、裁切区域与说明。

关键位置可少量圈选/框选、箭头或局部放大；源帧保留，衍生图另存，记录区域、文字、时间、操作和哈希，不伪造抽帧sidecar。圈不能盖数字/水印/字幕/反例；放大保持上下文，不补造UI或属性。工具支持focus.rect（原图像素坐标）、shape=circle/box和可选zoom，其他编辑方式也须真实可追溯。

常用宽750–1080px，最长边≤4096px、每图≤3MiB。此为本地防长图预算，不是微信官方限制或可粘贴保证。超限先去冗余画面/留白，再合理压缩，不能缩得375px看不清。新策略生成器输出前检查预算，拒绝输出超限成品。

实际按375px显示尺度逐帧查看字幕、UI、数字、动作、说明与重点；必要时只在内存看局部，不生成整篇手机长图。保存analysis/visual-review.md：两组不同作用、实际入图文字、对应证据、真实尺寸/字节数、圈选放大区域、目视方式/发现/修正。DOM排版检查不等于视觉审稿。两图manifest中的public_annotations记录每条入图文字、source_index（1起）、basis（frame/speaker/editorial/external）、evidence_ref和placement。

## ImageGen双封面

先读imagegen Skill，用内置工具。先目视真实人物关键帧及物件；无合格人物才选产品、球场/游戏对象或真实公开事件，登记例外。先3条短句+2个视觉概念；封面字优先6–14字，疑问/反问以 `？` 结尾，不照抄长题。

正式3:4竖封面+2.35:1横封面两个构图，不能改名同图、拉伸。中文字、字体、排版由ImageGen原生生成，逐字复核；错字继续ImageGen编辑，不用PIL/Canvas/HTML叠字冒充。只允许不加字、不拉伸且保留完整文字/主体的裁切缩放。

文字醒目不等于事实夸大，遮住文字仍要有本篇决定性对象/对比。检查近6张同账号封面，记录实际对象；无历史明确注明。不得把封面放正文伪装证据。

### 梦幻强制素材锁定

仅用已查看的视频人物、角色、装备、召唤兽、道具、战斗或UI。ImageGen仅做文字、版式、比例适配与克制明暗；不加金币、火焰、法阵、怪物、武器、建筑、幻想背景、假UI或战斗。扩展仅延续已有颜色纹理。

每个提示词包含：`Preserve the supplied source frame and its subjects. Add no new person, character, prop, creature, weapon, game object, UI, scene, or decorative narrative element.`

并写 `Text (verbatim): "实际中文短句？"`。

两版分别与原帧并排核对。陌生脸、物件漂移、UI改写、新主体即失败，无合格素材就阻塞，不造“梦幻风”代替。

### 记录

cover记录outputs、每版实际prompts、text、3条text_candidates、2条visual_concepts、source_frame/source_timestamp/source_strategy/subject_method/typography_style、thumbnail_hook_checked/recent_cover_overlap_checked/cover_square_crop_checked、text_method=imagegen-verified、evidence_use=false。梦幻加source_lock=true、added_nontext_visuals=[]、side_by_side_checked=true。实际检查前不得填true。

横版中央1:1裁切仍可辨核心对象；检查两个比例的缩略图和中文字。方裁仅作QA，不增加第三正式封面。

## 兼容和非证据图

新默认两图均须真实素材拼图，不增加生成式亮点图充当第三张或替代证据。只有用户明确另定版式才设计单独策略，不静默关闭校验。没有新版策略的旧任务仍按旧直图/4–6帧拼图/手机预览规则验收，保留历史结果，不只改schema号假装迁移。封面始终是包装，不是事实证据。
