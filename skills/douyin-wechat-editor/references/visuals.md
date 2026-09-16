# 证据配图与双封面

## 正文约3单元

默认1直图+2组不同主张的4至6帧拼图，两拼图间有正文。无第二证据链时登记visual_plan.structure_exception_reason，采用直图+拼图+标注/局部放大/另一张直图。确有需要可2至4单元，不堆5至8图；一组拼图算1单元。

梦幻/篮球≥1直图+1组4至6有效节点拼图。不足就换素材或hold/merge，不复制凑数。单帧足以证明结论且确无第二有效节点才免拼图：填single_frame_exception，图标single-frame-exception，台账保留理由。

## 单列大图拼接

每帧独占一行、占满内容宽度、保持原比例，顶部简洁主题；编号放独立说明区，下方 `原视频时间点｜本帧重点`，避免覆盖证据。按证据顺序排列，不再多列网格。

使用source_tools.py frame提取绑定视频帧并保留.frame.json；build_evidence_collage.py输出图片和.collage.json，含帧路径/哈希、视频哈希、时间、说明、单列版式和输出哈希。脚本拒绝重复图像，近似画面是否重复表达仍需编辑检查。局部放大记录原帧、裁切区域与说明。

375px预览逐帧检查字幕、UI、属性、动作顺序和原比例。长图分段查看，不只看缩略图。数字小就增加局部放大，不能让ImageGen重绘证据。

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

## 可选视频亮点图

默认不用，有比较解释价值最多1张且计入约3单元，真实证据单元更多。基于已查看参考帧+2至3条核验亮点，不生成/改写数字、台词、UI、参数、关系或结果。标imagegen-highlight-graphic、editorial-highlight、source_references；图注含ImageGen、依据原视频制作、不作为事实证据。填写imagegen_highlights、逐字与主体复核。不能替代梦幻/篮球真实直图+拼图或信息增量。
