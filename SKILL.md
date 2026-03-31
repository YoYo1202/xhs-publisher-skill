---
name: xhs-publisher
description: 小红书图文笔记一键发布技能。支持从 Markdown 自动渲染图片卡片（15种主题/样式）并通过 CDP 控制浏览器发布到小红书。使用场景：用户要写小红书笔记、生成图片卡片、发布小红书内容时使用。触发词：小红书、发布笔记、生成卡片、xhs。
---

# 小红书一键发布技能

根据用户需求创作内容、渲染图片卡片，预览确认后发布到小红书。

> 完整参数说明见 `references/XHS_POST_README.md`

---

## 环境要求

- WebTop 容器内 Chrome，CDP 端口 9222
- `/home/docker/webtop/config/xhs_publish.py` 存在且可用
- Python 依赖：`playwright`, `markdown`, `PyYAML`
- 渲染脚本：需要先 clone [Auto-Redbook-Skills](https://github.com/comeonzhj/Auto-Redbook-Skills) 到工作目录

---

## 工作流程

### 第一步：撰写笔记内容

根据用户需求创作符合小红书风格的 Markdown 文档：

```markdown
---
emoji: "🔥"
title: "封面大标题（≤15字）"
subtitle: "封面副标题（≤15字）"
---

# 第一张卡片

内容...

---

# 第二张卡片

内容...
```

- 标题 ≤ 20 字
- 段落清晰，点缀少量 Emoji
- 结尾附 5-10 个 SEO 标签
- v1 引擎用 `---` 手动分页；v2 引擎自动分页

### 第二步：渲染图片（发给用户预览）

**先渲染，再发送图片给用户预览，等用户确认后再发布。**

```bash
# v1 引擎（8种主题）
python3 scripts/xhs_post.py --render content.md --theme sketch --dry-run

# v2 引擎（7种渐变风格）
python3 scripts/xhs_post.py --render content.md --v2 --style elegant --dry-run
```

渲染完成后，用 `openclaw message send --media` 把图片发给用户。

### 第三步：用户确认后发布

```bash
# 立即发布
python3 scripts/xhs_post.py --render content.md --v2 --style elegant

# 定时发布
python3 scripts/xhs_post.py --render content.md --theme sketch --post-time "2026-04-02 09:00:00"
```

### 第四步：清理临时文件

```bash
rm -rf /tmp/xhs_render /tmp/xhs_*.png
```

---

## 可用主题

### v1 引擎（--theme）
`sketch` / `default` / `botanical` / `retro` / `terminal` / `neo-brutalism` / `playful-geometric` / `professional`

### v2 引擎（--v2 --style）
`purple` / `xiaohongshu` / `mint` / `sunset` / `ocean` / `elegant` / `dark`

---

## 关键规则

- **必须先预览，用户确认后再发布**
- 标题最多 20 字，超了会断言失败
- 生成图片临时存在 `/tmp/xhs_render/`，发布后清理
- 渲染脚本路径：`/root/.openclaw/workspace/Auto-Redbook-Skills/scripts/`
