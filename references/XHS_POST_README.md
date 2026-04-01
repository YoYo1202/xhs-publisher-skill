# 小红书发布脚本说明

本目录包含两个独立脚本：

- **`xhs_post.py`** — 渲染脚本：将 Markdown 渲染成小红书卡片图片
- **`xhs_publish.py`** — 发布脚本：通过 Playwright/CDP 浏览器自动化发布内容

---

## 一、渲染脚本：xhs_post.py

将 Markdown 内容渲染成小红书卡片图片，输出到 `/tmp/xhs_render/`。

### v1 引擎（8种主题）
```bash
python3 xhs_post.py --render content.md --theme sketch --dry-run
python3 xhs_post.py --render content.md --theme botanical
```

### v2 引擎（7种渐变风格）
```bash
python3 xhs_post.py --render content.md --v2 --style elegant --dry-run
python3 xhs_post.py --render content.md --v2 --style ocean
```

| 主题（v1） | 风格 |
|------------|------|
| sketch | 手绘素描 |
| default | 紫色渐变 |
| botanical | 植物自然 |
| retro | 复古怀旧 |
| terminal | 命令行风 |
| neo-brutalism | 新粗野主义 |
| playful-geometric | 活泼几何 |
| professional | 商务专业 |

| 样式（v2） | 风格 |
|------------|------|
| purple | 梦幻紫 |
| xiaohongshu | 小红书粉 |
| mint | 薄荷绿 |
| sunset | 暖阳橙 |
| ocean | 深海蓝 |
| elegant | 优雅白 |
| dark | 暗夜黑 |

---

## 二、发布脚本：xhs_publish.py

通过 Playwright 浏览器自动化发布图文或长文到小红书。

> 2026-04-01 更新：图文模式改用 Playwright 上传（小红书页面变更后 CDP setFileInputFiles 失效）。话题添加统一用 type + Enter 确认关联，图文物和长文模式一致。

### 基本用法

```bash
# 图文模式（推荐）：Playwright 全流程
python3 xhs_publish.py \
  --type image \
  --title '标题（≤20字）' \
  --desc '正文内容，含话题标签' \
  --images /tmp/xhs_render/cover.png /tmp/xhs_render/card_1.png /tmp/xhs_render/card_2.png ...

# 长文模式
python3 xhs_publish.py \
  --type article \
  --title '标题（≤100字）' \
  --desc '正文内容' \
  --topics 销冠 销售干货 \
  --location 武汉
```

### 全部参数

| 参数 | 说明 | 适用模式 |
|------|------|----------|
| `--type image` | 图文模式，Playwright 全流程（上传+填标题正文+话题+地点+发布） | 必填 |
| `--type article` | 长文模式，CDP 填内容 + Playwright 处理话题地点 | 必填 |
| `--title` | 标题 | 必填 |
| `--desc` | 正文内容（支持换行） | 必填 |
| `--images` | 图片路径列表（image 模式必填，7张卡片的路径） | image |
| `--topics` | 话题列表（不含#号），每个话题输入后按 Enter 确认关联 | 两者 |
| `--location` | 地点名称 | 两者 |

---

## 三、完整工作流

### 第一步：渲染图片
```bash
python3 /root/.openclaw/workspace/xhs-publisher-skill/scripts/xhs_post.py \
  --render content.md --v2 --style elegant --dry-run
```

### 第二步：发图给用户预览
用 `openclaw message send --media` 把 `/tmp/xhs_render/` 里的图片发给用户，等用户确认。

### 第三步：用户确认后发布
```bash
python3 /root/.openclaw/workspace/xhs-publisher-skill/scripts/xhs_publish.py \
  --type image \
  --title '报价后怎么舒服逼单？' \
  --desc '做销售，就怕报价后空气安静三秒…客户一句"我再考虑考虑"，你就只能干等？...' \
  --images /tmp/xhs_render/cover.png \
           /tmp/xhs_render/card_1.png \
           /tmp/xhs_render/card_2.png \
           /tmp/xhs_render/card_3.png \
           /tmp/xhs_render/card_4.png \
           /tmp/xhs_render/card_5.png \
           /tmp/xhs_render/card_6.png \
  --topics 大客户销售 销冠 销售干货 与客户沟通 销售就是玩转情商 销售秘诀 销售的本质
```

### 第四步：清理
```bash
rm -rf /tmp/xhs_render
```

---

## 注意事项

- 图文模式标题最多 20 字，超了会断言失败
- 长文模式标题上限 100 字
- 生成图片临时存在 `/tmp/xhs_render/`，发布后清理
- 话题添加：输入话题文字 → 等待下拉候选出现 → 按 Enter 确认关联（变绿/变蓝表示生效）
- 发布依赖 WebTop 容器内 Chrome CDP（`localhost:9222`）
- 脚本路径：`/root/.openclaw/workspace/xhs-publisher-skill/scripts/`
