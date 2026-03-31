# xhs_post.py 使用说明

小红书一键发布脚本，支持 Markdown 渲染 + 浏览器自动发布。

---

## 模式 A：直接发布（手动指定图片）

修改脚本顶部变量：
```python
TITLE   = '标题（≤20字）'
CONTENT = '正文内容'
IMAGES  = ['/path/to/cover.png', '/path/to/card_1.png']
TOPICS  = ['话题1', '话题2']
LOCATION = '武汉'
```
然后运行：
```bash
python3 xhs_post.py
```

---

## 模式 B：Markdown 渲染 + 发布

### v1 引擎（8种主题 + 4种分页模式）
```bash
python3 xhs_post.py --render content.md --theme sketch
python3 xhs_post.py --render content.md --theme botanical --mode auto-split
python3 xhs_post.py --render content.md --theme neo-brutalism --width 1080 --height 1920
```

**可用主题（--theme）：**
| 主题 | 风格 |
|------|------|
| sketch | 手绘素描 |
| default | 紫色渐变 |
| botanical | 植物自然 |
| retro | 复古怀旧 |
| terminal | 命令行风 |
| neo-brutalism | 新粗野主义 |
| playful-geometric | 活泼几何 |
| professional | 商务专业 |

**分页模式（--mode）：**
- `separator`：按 `---` 手动分页（默认）
- `auto-fit`：自动缩放填满固定尺寸
- `auto-split`：内容超高自动切分
- `dynamic`：根据内容动态高度

### v2 引擎（7种渐变风格，自动分页）
```bash
python3 xhs_post.py --render content.md --v2 --style elegant
python3 xhs_post.py --render content.md --v2 --style ocean
```

**可用样式（--style）：**
| 样式 | 风格 |
|------|------|
| purple | 梦幻紫 |
| xiaohongshu | 小红书粉 |
| mint | 薄荷绿 |
| sunset | 暖阳橙 |
| ocean | 深海蓝 |
| elegant | 优雅白 |
| dark | 暗夜黑 |

---

## 全部可选参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `--render <file>` | 指定 Markdown 文件渲染 | 无 |
| `--v2` | 使用 v2 渲染引擎 | 否（默认 v1）|
| `--theme` | v1 主题 | sketch |
| `--mode` | v1 分页模式 | separator |
| `--style` | v2 样式 | purple |
| `--width` | 图片宽度（v1） | 1080 |
| `--height` | 图片高度（v1） | 1440 |
| `--dpr` | 像素密度（v1） | 2 |
| `--post-time` | 定时发布时间 | 立即发布 |
| `--dry-run` | 只验证不发布 | 否 |

---

## 示例

```bash
# 先预览，确认后再发
python3 xhs_post.py --render content.md --v2 --style elegant --dry-run
python3 xhs_post.py --render content.md --v2 --style elegant

# 定时发布
python3 xhs_post.py --render content.md --theme sketch --post-time "2026-04-02 09:00:00"

# 高分辨率竖版
python3 xhs_post.py --render content.md --theme botanical --width 1080 --height 1920 --dpr 3
```

---

## Markdown 文件格式

```markdown
---
emoji: "🔥"
title: "封面大标题（≤15字）"
subtitle: "封面副标题（≤15字）"
---

# 第一张正文卡片内容

正文内容...

---

# 第二张卡片（用 --- 手动分页时）

内容...
```

---

## 注意事项
- 标题最多 20 字，超了发不出去
- 生成图片临时存放在 `/tmp/xhs_render/`，发布后可清理
- 发布依赖 WebTop 容器内 Chrome CDP（localhost:9222）
- 地点功能依赖 `--location` 参数，留空则不加地点
