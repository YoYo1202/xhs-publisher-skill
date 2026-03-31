# 环境配置指南 (SETUP.md)

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

在 WebTop 内部，Chrome 必须以 `--remote-debugging-port=9222` 启动。通常修改启动快捷方式或环境变量：

- **启动参数**: `google-chrome --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0`
- **验证方式**: 
  在宿主机执行 `curl http://localhost:9222/json`，能返回 JSON 数据即代表连通。

---

## 3. 安装发布脚本依赖

进入容器或在宿主机（如果网络通畅）安装 Python 依赖：

```bash
pip3 install playwright markdown PyYAML xhs python-dotenv requests
playwright install chromium
```

---

## 4. 获取发布脚本

确保主发布脚本 `xhs_publish.py` 放在容器挂载目录（如 `/home/docker/webtop/config/`）。

> 本技能 `xhs_post.py` 是对此脚本的二次封装，用于实现渲染+发布全流程。

---

## 5. 常见问题 (FAQ)

### Q: 发布时提示「无登录信息」？
- **A**: 确保 WebTop 里的 Chrome 已经手动登录了小红书（creator.xiaohongshu.com）。CDP 方式是直接控制浏览器现有 Session，无需手动填 Cookie。

### Q: 地点功能失效？
- **A**: `xhs_publish.py` 内部使用 JS 模拟点击和输入。如果页面结构变化，需更新脚本内的 `CSS Selector`。当前脚本支持武汉等城市关键词搜索和匹配。

### Q: 无法渲染图片？
- **A**: 确保已克隆 [Auto-Redbook-Skills](https://github.com/comeonzhj/Auto-Redbook-Skills) 仓库，并将其路径填入 `xhs_post.py` 的 `RENDER_SCRIPT_V1/V2` 变量中。
