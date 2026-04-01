# 环境配置指南

本技能依赖 **WebTop (Docker)** 运行环境，并需要开启 Chrome 的 **CDP (Chrome DevTools Protocol)** 远程调试端口。

---

## 1. 部署 WebTop 容器

推荐使用 `linuxserver/webtop:ubuntu-xfce` 镜像。部署时必须映射 **9222** 端口：

```bash
docker run -d \
  --name=webtop \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Asia/Shanghai \
  -p 3000:3000 \
  -p 9222:9222 \
  -v /path/to/data:/config \
  --shm-size="1gb" \
  --restart unless-stopped \
  linuxserver/webtop:ubuntu-xfce
```

---

## 2. 配置 Chrome 开启 CDP 端口

在 WebTop 内部，Chrome 必须以 `--remote-debugging-port=9222` 启动：

- **启动参数**: `google-chrome --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0`
- **验证方式**: 在宿主机执行 `curl http://localhost:9222/json`，能返回 JSON 数据即代表连通。

---

## 3. 安装发布脚本依赖

```bash
pip3 install playwright markdown PyYAML python-dotenv requests
playwright install chromium
```

> Auto-Redbook-Skills 已克隆至 `/root/.openclaw/workspace/Auto-Redbook-Skills/`，渲染脚本路径已在技能脚本中写死，无需额外配置。

---

## 4. 发布脚本位置

发布脚本位于技能目录下：`/root/.openclaw/workspace/xhs-publisher-skill/scripts/xhs_publish.py`。

> 注意：`xhs` Python 库已不再使用（2026-04-01 图文模式改用 Playwright 上传）。
