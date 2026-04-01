# 小红书发布技能

小红书图文/长文自动发布工具，支持从 Markdown 内容自动渲染卡片图片并通过浏览器自动化发布。

> 使用场景：运营小红书账号时，快速生成多张风格统一的卡片图并一键发布。

---

## 功能特性

- **Markdown → 图片卡片**：支持 15 种主题/v2 样式，自动分页渲染
- **图文发布**：Playwright 自动化，上传图片 → 填标题正文 → 话题关联 → 地点 → 发布
- **长文发布**：CDP 填内容 + Playwright 处理话题地点
- **话题关联**：输入话题后按 Enter 确认，真正变成可点击话题标签（非纯文本）
- **浏览器即点即用**：依赖 WebTop Docker 容器内的 Chrome CDP，无需额外配置登录态

---

## 快速开始

### 环境要求

- WebTop 容器（Chrome 开启 CDP 9222 端口）
- Python 3.10+，依赖：`playwright` / `markdown` / `PyYAML` / `python-dotenv` / `requests`
- 小红书账号已在浏览器中登录

### 渲染图片

```bash
# v2 引擎（7种渐变风格）
python3 scripts/xhs_post.py --render content.md --v2 --style elegant --dry-run
```

### 发布图文

```bash
python3 scripts/xhs_publish.py \
  --type image \
  --title '标题（≤20字）' \
  --desc '正文内容，含话题标签' \
  --images /tmp/xhs_render/cover.png /tmp/xhs_render/card_1.png ... \
  --topics 大客户销售 销冠 销售干货
```

### 发布长文

```bash
python3 scripts/xhs_publish.py \
  --type article \
  --title '文章标题' \
  --desc '正文内容' \
  --topics 销冠 销售干货 \
  --location 武汉
```

完整参数说明见 [references/XHS_POST_README.md](references/XHS_POST_README.md)。

---

## 目录结构

```
.
├── SKILL.md                         # 技能入口说明
├── README.md                         # 本文件
├── references/
│   ├── XHS_POST_README.md           # 发布脚本详细说明
│   └── SETUP.md                     # 环境配置指南
└── scripts/
    ├── xhs_post.py                  # 渲染脚本
    ├── xhs_publish.py               # 发布脚本
    ├── render_xhs.py / _v2.py       # 渲染引擎
    └── render_xhs.js / _v2.js       # 渲染引擎（Node）
```

---

## 可用主题

| v1 引擎 | v2 引擎 |
|---------|---------|
| sketch / default / botanical / retro / terminal / neo-brutalism / playful-geometric / professional | purple / xiaohongshu / mint / sunset / ocean / elegant / dark |

---

## 更新日志

### v2（2026-04-01）
- 图文模式改用 Playwright 上传（小红书页面变更后 CDP setFileInputFiles 失效）
- 话题添加统一改为 `type + Enter` 确认，真正关联话题标签
- 长文模式话题添加同步更新为 Playwright 方式
- 文档整理，移除冗余文件

---

## 免责声明

本工具仅供个人学习、研究和正当运营使用。请遵守小红书平台服务条款，合理合规使用。
