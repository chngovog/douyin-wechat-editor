# Douyin WeChat Editor

把抖音素材整理成有证据、有编辑增量的公众号短文，本地交付完整文章包。

支持手机数码、篮球、梦幻西游、娱乐四个独立账号。包含Codex Skill、任务清单、截图与单列长拼图工具、HTML/移动端预览及校验脚本。不会自动上传文章或打开成品页面。

## 安装与使用

将 `skills/douyin-wechat-editor` 整个文件夹放入自己的Codex技能目录（通常为用户目录下 `.codex/skills`），或让Codex从此仓库安装该路径，保留目录结构。

```text
使用 $douyin-wechat-editor，为篮球公众号找今天适合的抖音视频，完成一篇本地文章包。
```

也可指定梦幻、数码、娱乐账号，提供视频链接/本地文件，或指向已有 `article-job.json` 续做。

## 依赖

- 支持登录态网页操作的浏览器工具，登录与验证码由用户完成。
- 可用的内置ImageGen和imagegen Skill。缺少时不能用脚本叠字冒充正式封面。
- Python 3.10+；`pip install -r requirements.txt`；ffmpeg/ffprobe。
- Node.js；仓库内执行 `npm ci`；Playwright Chromium可用，或设置 `BROWSER_EXE` 指向Chrome/Edge。
- 中文字体，通过拼图 `--font` 指定；不包含商业字体、图片或视频。
- 已配置的转写工具/模型，缺失时不偷偷切换云服务上传音频。

Skill单独安装后，可在其scripts目录安装playwright，或设置 `NODE_PATH` 指向已有node_modules。代码不写死本机用户名、盘符或依赖目录。

## 工作流

4个新研究标签并静音 → 筛选当日视频 → 来源绑定/转写/抽帧 → 一手核验与信息增量 → 两套疑问标题 → 约500字正文 → 约3个配图单元 → ImageGen双封面 → 无头预览/质检 → 4项链接集中交付。

图文标题≤20字符，正文通常450–550中文字符。拼图单列大图纵向排列。梦幻封面只用视频人物/物件/界面加文字。具体门槛和例外见 [Skill](skills/douyin-wechat-editor/SKILL.md)。

## 本地检查

```sh
python skills/douyin-wechat-editor/scripts/source_tools.py doctor
python -m unittest discover -s tests -v
```

命令与字段说明见 [pipeline.md](skills/douyin-wechat-editor/references/pipeline.md)。测试使用临时合成图片和数据，不包含真实账号内容；测试通过不代表实测了所有平台环节。

## 隐私与授权

只保存流程、代码和测试。账号数据、Cookie、登录态、AppSecret、签名媒体链接、原视频、文章产物和字体不上传。新文章输出请放仓库之外；.gitignore不替代提交前检查。

这是个人工作流，不是微信/抖音官方规则或流量保证。素材能播放不等于授权转载，本地校验不等于平台审核通过。publish字段仅代表编辑判断可独立成文，不执行外部发表。
