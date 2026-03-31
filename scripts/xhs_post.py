#!/usr/bin/env python3
"""
小红书发布辅助脚本

两种使用模式：

模式 A：直接发布（手动指定图片）
  修改下方变量后运行: python3 xhs_post.py

模式 B：从 Markdown 渲染图片再发布
  # v1 渲染引擎（8种主题 + 4种分页）
  python3 xhs_post.py --render content.md --theme sketch
  python3 xhs_post.py --render content.md --theme botanical --mode auto-split

  # v2 渲染引擎（7种渐变风格，自动分页）
  python3 xhs_post.py --render content.md --v2 --style purple
  python3 xhs_post.py --render content.md --v2 --style ocean

可选参数:
  --dry-run        只验证不发布
  --render <file>  指定 markdown 文件，自动渲染图片

  v1 引擎参数（默认）:
  --theme     主题: default / playful-geometric / neo-brutalism / botanical /
                    professional / retro / terminal / sketch（默认 sketch）
  --mode      分页: separator / auto-fit / auto-split / dynamic（默认 separator）
  --width     图片宽度（默认 1080）
  --height    图片高度（默认 1440）
  --dpr       像素密度（默认 2）

  v2 引擎参数:
  --v2        使用 v2 渲染引擎
  --style     样式: purple / xiaohongshu / mint / sunset / ocean / elegant / dark（默认 purple）
"""
import sys
import os
import argparse
import subprocess
import glob

sys.path.insert(0, '/home/docker/webtop/config')

RENDER_SCRIPT_V1 = '/root/.openclaw/workspace/Auto-Redbook-Skills/scripts/render_xhs.py'
RENDER_SCRIPT_V2 = '/root/.openclaw/workspace/Auto-Redbook-Skills/scripts/render_xhs_v2.py'
RENDER_OUTPUT_DIR = '/tmp/xhs_render'

THEMES_V1 = ['default', 'playful-geometric', 'neo-brutalism', 'botanical',
              'professional', 'retro', 'terminal', 'sketch']
MODES_V1  = ['separator', 'auto-fit', 'auto-split', 'dynamic']
STYLES_V2 = ['purple', 'xiaohongshu', 'mint', 'sunset', 'ocean', 'elegant', 'dark']

# ===== 模式 A：直接填变量发布 =====
POST_TYPE = 'image'   # 'image' 图文 | 'article' 长文
TITLE = '标题（20字以内）'
CONTENT = (
    '正文第一段'
    '\n\n正文第二段'
    '\n\n#话题1 #话题2 #话题3'
)
IMAGES = [   # 图文模式填图片路径，长文模式留空 []
    # '/path/to/img1.jpg',
]
TOPICS = ['话题1', '话题2']   # 不含#号
LOCATION = '武汉'   # 留空字符串则不加地点
# ===== END =====


VALID_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


def validate(title, content, images, post_type):
    errors = []
    if len(title) > 20:
        errors.append(f'❌ 标题超长：{len(title)}字，最多20字')
    if not title.strip():
        errors.append('❌ 标题不能为空')
    if not content.strip():
        errors.append('❌ 正文不能为空')
    if post_type == 'image':
        if not images:
            errors.append('❌ 图文模式至少需要一张图片')
        else:
            for img in images:
                if not os.path.exists(img):
                    errors.append(f'❌ 图片不存在: {img}')
                elif os.path.splitext(img)[1].lower() not in VALID_EXTS:
                    errors.append(f'❌ 不支持的图片格式: {img}（支持 jpg/png/webp）')
    return errors


def render_images_v1(md_file, theme='sketch', mode='separator', width=1080, height=1440, dpr=2):
    """v1 引擎：8种主题 + 4种分页模式"""
    os.makedirs(RENDER_OUTPUT_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(RENDER_OUTPUT_DIR, '*.png')):
        os.remove(f)
    cmd = [
        'python3', RENDER_SCRIPT_V1, md_file,
        '-t', theme, '-m', mode,
        '-o', RENDER_OUTPUT_DIR,
        '-w', str(width), '--height', str(height), '--dpr', str(dpr)
    ]
    print(f'🎨 渲染图片中（v1 / 主题: {theme} / 分页: {mode}）...')
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print('❌ 渲染失败')
        sys.exit(1)
    images = sorted(glob.glob(os.path.join(RENDER_OUTPUT_DIR, '*.png')))
    print(f'✅ 生成 {len(images)} 张图片')
    return images


def render_images_v2(md_file, style='purple'):
    """v2 引擎：7种渐变风格，自动分页"""
    os.makedirs(RENDER_OUTPUT_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(RENDER_OUTPUT_DIR, '*.png')):
        os.remove(f)
    cmd = [
        'python3', RENDER_SCRIPT_V2, md_file,
        '-s', style,
        '-o', RENDER_OUTPUT_DIR
    ]
    print(f'🎨 渲染图片中（v2 / 样式: {style}）...')
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print('❌ 渲染失败')
        sys.exit(1)
    images = sorted(glob.glob(os.path.join(RENDER_OUTPUT_DIR, '*.png')))
    print(f'✅ 生成 {len(images)} 张图片')
    return images


def publish(title, content, images, topics, location, post_type, post_time=None):
    import xhs_publish
    sys.argv = ['xhs_publish.py', '--type', post_type, '--title', title, '--content', content]
    if images:
        sys.argv += ['--images'] + images
    if topics:
        sys.argv += ['--topics'] + topics
    if location:
        sys.argv += ['--location', location]
    if post_time:
        sys.argv += ['--post_time', post_time]
    exec(open('/home/docker/webtop/config/xhs_publish.py').read(), {'__name__': '__main__'})


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--render', default=None, metavar='MD_FILE')
    # v1 参数
    parser.add_argument('--v2', action='store_true')
    parser.add_argument('--theme', default='sketch', choices=THEMES_V1)
    parser.add_argument('--mode', default='separator', choices=MODES_V1)
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=1440)
    parser.add_argument('--dpr', type=int, default=2)
    # v2 参数
    parser.add_argument('--style', default='purple', choices=STYLES_V2)
    parser.add_argument('--post-time', default=None, metavar='YYYY-MM-DD HH:MM:SS', help='定时发布时间')
    parser.add_argument('-h', '--help', action='store_true')
    args, _ = parser.parse_known_args()

    if args.help:
        print(__doc__)
        print('v1 主题:', ', '.join(THEMES_V1))
        print('v1 分页:', ', '.join(MODES_V1))
        print('v2 样式:', ', '.join(STYLES_V2))
        return

    title    = TITLE
    content  = CONTENT
    images   = list(IMAGES)
    topics   = list(TOPICS)
    location = LOCATION

    if args.render:
        md_file = os.path.abspath(args.render)
        if not os.path.exists(md_file):
            print(f'❌ Markdown 文件不存在: {md_file}')
            sys.exit(1)
        if args.v2:
            images = render_images_v2(md_file, style=args.style)
        else:
            images = render_images_v1(md_file, theme=args.theme, mode=args.mode,
                                      width=args.width, height=args.height, dpr=args.dpr)

    errors = validate(title, content, images, POST_TYPE)
    if errors:
        print('\n'.join(errors))
        sys.exit(1)

    if args.dry_run:
        engine = f'v2 / {args.style}' if args.v2 else f'v1 / {args.theme} / {args.mode}'
        print('✅ 验证通过（dry-run，不实际发布）')
        print(f'  📌 标题: {title} ({len(title)}字)')
        print(f'  📝 正文: {content[:60]}...' if len(content) > 60 else f'  📝 正文: {content}')
        if args.render:
            print(f'  🎨 引擎: {engine}')
        print(f'  🖼️ 图片: {images}')
        print(f'  🏷️ 话题: {topics}')
        print(f'  📍 地点: {location or "无"}')
        if args.post_time:
            print(f'  ⏰ 定时: {args.post_time}')
        return

    publish(title, content, images, topics, location, POST_TYPE, post_time=args.post_time)


if __name__ == '__main__':
    main()
