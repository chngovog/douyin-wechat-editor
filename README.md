# Douyin WeChat Editor

把抖音素材整理成有证据、有编辑增量的公众号短文，本地交付完整文章包。

支持手机数码、篮球、梦幻西游、娱乐四个独立账号。包含一个可独立安装的 Codex Skill：选题、视频解读、实质价值审稿、自然语气改稿、说明拼图、双封面及本地验收。不依赖原作者的私人项目或另一份未分享技能，不会自动上传文章或打开成品页面。

## 2026-10-12 同步内容

- 完整正文400–500个可见字符，通常420–450；标点、数字、英文、图注、署名和来源都计入，含页内标题也不超过500。是本地保守估算，不冒充微信后台实测。
- 正文恰好两张单列说明拼图，各2–4个有效原视频节点，优先2–3个；支持短说明、圈选/框选及局部放大。最长边4096px、3MiB为本地预算，不是平台官方限额。
- 只交付HTML、3:4竖封面、2.35:1横封面。不生成手机预览长图，但仍做375px无截图排版检查、真实图片与内容目视。
- 全历史视频/事件查重、核心外部信息增量、标题前提核验，以及最近5篇首尾比较与一次总编改稿。
- 当日优先，无合格素材主动扩展近3/7/30天和仍有价值的旧素材；如实标日期，不用旧累计互动冒充当日热度。

这是作者当前编辑默认，不是微信官方规则。旧任务按已有策略兼容，不批量迁移历史文章。模型、定时任务、账号凭据和运行历史不在分享包内。

## 安装与使用

将 `skills/douyin-wechat-editor` 整个文件夹放入自己的Codex技能目录（通常为用户目录下 `.codex/skills`），或让Codex从此仓库安装该路径，保留目录结构。

本仓库为私有：朋友需要先被仓库所有者添加为协作者并接受邀请，再用自己的 GitHub 账号登录。不要分享所有者令牌或浏览器登录态。安装入口：[SKILL.md](skills/douyin-wechat-editor/SKILL.md)。

```text
使用 $douyin-wechat-editor，为篮球公众号找今天适合的抖音视频，完成一篇本地文章包。
```

也可指定梦幻、数码、娱乐账号，提供视频链接/本地文件，或指向已有 `article-job.json` 续做。

## 依赖

- 支持登录态网页操作的浏览器工具，登录与验证码由用户完成。
- 可用的内置ImageGen和imagegen Skill。缺少时不能用脚本叠字冒充正式封面。
- Python 3.10+；`pip install -r requirements.txt`；ffmpeg/ffprobe。
- Node.js 20+；仓库内执行 `npm ci`；Playwright Chromium可用，或设置 `BROWSER_EXE` 指向Chrome/Edge。需要安装浏览器时自行运行 `npx playwright install chromium`。
- 中文字体，通过拼图 `--font` 指定；不包含商业字体、图片或视频。
- 已配置的转写工具/模型，缺失时不偷偷切换云服务上传音频。

Skill单独安装后，可在其scripts目录安装playwright，或设置 `NODE_PATH` 指向已有node_modules。代码不写死本机用户名、盘符或依赖目录。

## 工作流

4个新研究标签并静音 → 查重/候选比较与必要扩窗 → 来源绑定/转写/抽帧 → 核心事实与外部增量实审 → 两套疑问标题与短文 → 一次总编改稿 → 两张说明拼图与ImageGen双封面 → render → check-layout → 图片/内容目视 → validate → 三项链接集中交付。

图文标题≤20字符，两标题用不同问句骨架。梦幻封面只用视频人物/物件/界面加文字。具体门槛见 [Skill](skills/douyin-wechat-editor/SKILL.md)。

## 本地检查

```sh
python skills/douyin-wechat-editor/scripts/source_tools.py doctor
python -m unittest discover -s tests -v
```

命令与字段说明见 [pipeline.md](skills/douyin-wechat-editor/references/pipeline.md)。测试使用临时合成图片和数据，不包含真实账号内容；测试通过不代表实测了所有平台环节。

## 隐私与授权

只保存流程、代码和测试。账号数据、Cookie、登录态、AppSecret、签名媒体链接、原视频、文章产物和字体不上传。新文章输出请放仓库之外；.gitignore不替代提交前检查。

这是个人工作流，不是微信/抖音官方规则或流量保证。素材能播放不等于授权转载，本地校验不等于平台审核通过。publish字段仅代表编辑判断可独立成文，不执行外部发表。
