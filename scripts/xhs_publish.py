#!/usr/bin/env python3
import asyncio, websockets, json, base64, argparse, subprocess, urllib.request, os
from typing import List, Optional, Dict, Any # Added for type hints
from pathlib import Path # Added for Path

# Added for environment variable loading for cookie
try:
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install python-dotenv requests")
    sys.exit(1)


async def get_all_pages():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    return [x for x in data if x.get('type') == 'page']

async def get_page_id():
    pages = await get_all_pages()
    p = next((x for x in pages), None)
    return (p['id'], p['webSocketDebuggerUrl']) if p else (None, None)

_id = 0
async def send(ws, m, p={}):
    global _id; _id += 1; cid = _id
    await ws.send(json.dumps({'id': cid, 'method': m, 'params': p}))
    async for msg in ws:
        r = json.loads(msg)
        if r.get('id') == cid: return r

async def screenshot(ws, path):
    r = await send(ws, 'Page.captureScreenshot', {'format': 'jpeg', 'quality': 55})
    with open(path, 'wb') as f:
        f.write(base64.b64decode(r['result']['data']))

async def fill_prosemirror(ws, content, x=206, y=249):
    """点击激活 ProseMirror 编辑器，然后注入文本"""
    await send(ws, 'Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    await send(ws, 'Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    await asyncio.sleep(0.5)

    r = await send(ws, 'Runtime.evaluate', {'expression': '''
        var editor = document.querySelector(".tiptap.ProseMirror");
        if (editor) { editor.focus(); document.execCommand("selectAll"); "ok"; }
        else { "editor not found"; }
    '''})
    val = r['result']['result'].get('value', '')
    print('编辑器 focus:', val)
    if val != 'ok':
        print('WARNING: 编辑器未找到，尝试备用方式...')
        await send(ws, 'Input.insertText', {'text': content})
        return

    await send(ws, 'Input.dispatchKeyEvent', {
        'type': 'keyDown', 'key': 'a', 'code': 'KeyA', 'modifiers': 2
    })
    await send(ws, 'Input.dispatchKeyEvent', {
        'type': 'keyUp', 'key': 'a', 'code': 'KeyA', 'modifiers': 2
    })
    await asyncio.sleep(0.3)

    paragraphs = content.split('\n')
    for i, para in enumerate(paragraphs):
        if para:
            await send(ws, 'Input.insertText', {'text': para})
        if i < len(paragraphs) - 1:
            await send(ws, 'Input.dispatchKeyEvent', {
                'type': 'keyDown', 'key': 'Enter', 'code': 'Enter'
            })
            await send(ws, 'Input.dispatchKeyEvent', {
                'type': 'keyUp', 'key': 'Enter', 'code': 'Enter'
            })
        await asyncio.sleep(0.05)

async def add_topics(ws, topics):
    """通用话题添加（图文/长文共用）：点话题按钮 → 搜索 → 点候选"""
    for topic in topics:
        r = await send(ws, 'Runtime.evaluate', {'expression': "(function(){var b=document.querySelector('button.topic-btn');if(b){b.click();return 'clicked';}return 'not found';})()" })
        print(f'话题按钮:', r['result']['result'].get('value'))
        await asyncio.sleep(1)
        await send(ws, 'Input.insertText', {'text': topic})
        await asyncio.sleep(2)
        r = await send(ws, 'Runtime.evaluate', {'expression': f"""
            (function() {{
                var spans = Array.from(document.querySelectorAll('span.name'));
                var t = spans.find(s => s.innerText.trim() === '#{topic}');
                if (!t) t = spans[0];
                if (t) {{ t.click(); return 'clicked: ' + t.innerText.trim(); }}
                return 'not found';
            }})()
        """})
        print(f'话题 {topic}:', r['result']['result'].get('value'))
        await asyncio.sleep(1)
    print('话题添加完毕')


# Cookie Loading and Parsing functions from the other publish_xhs.py
def load_cookie() -> str:
    """从 .env 文件加载 Cookie"""
    env_paths = [
        Path.cwd() / '.env',
        Path(__file__).parent.parent / '.env', # Modified to check parent dirs
        Path(__file__).parent.parent.parent / '.env',
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
    
    cookie = os.getenv('XHS_COOKIE')
    if not cookie:
        print("❌ 错误: 未找到 XHS_COOKIE 环境变量")
        print("请创建 .env 文件，添加以下内容：")
        print("XHS_COOKIE=your_cookie_string_here")
        print("\nCookie 获取方式：")
        print("1. 在浏览器中登录小红书（https://www.xiaohongshu.com）")
        print("2. 打开开发者工具（F12）")
        print("3. 在 Network 标签中查看任意请求的 Cookie 头")
        print("4. 复制完整的 cookie 字符串")
        sys.exit(1)
    
    return cookie

def parse_cookie(cookie_string: str) -> Dict[str, str]:
    """解析 Cookie 字符串为字典"""
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def validate_cookie(cookie_string: str) -> bool:
    """验证 Cookie 是否包含必要的字段"""
    cookies = parse_cookie(cookie_string)
    required_fields = ['a1', 'web_session']
    missing = [f for f in required_fields if f not in cookies]
    if missing:
        print(f"⚠️ Cookie 可能不完整，缺少字段: {', '.join(missing)}")
        print("这可能导致签名失败，请确保 Cookie 包含 a1 和 web_session 字段")
        return False
    return True

def get_api_url() -> str:
    """获取 API 服务地址"""
    return os.getenv('XHS_API_URL', 'http://localhost:5005')

def validate_images(image_paths: List[str]) -> List[str]:
    """验证图片文件是否存在"""
    valid_images = []
    for path in image_paths:
        if os.path.exists(path):
            valid_images.append(os.path.abspath(path))
        else:
            print(f"⚠️ 警告: 图片不存在 - {path}")
    if not valid_images:
        print("❌ 错误: 没有有效的图片文件")
        sys.exit(1)
    return valid_images

class LocalPublisher:
    """本地发布模式：直接使用 xhs 库"""
    
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.client = None
        
    def init_client(self):
        """初始化 xhs 客户端"""
        try:
            from xhs import XhsClient
            from xhs.help import sign as local_sign
        except ImportError:
            print("❌ 错误: 缺少 xhs 库")
            print("请运行: pip install xhs")
            sys.exit(1)
        
        # Simplified sign_func signature and argument passing
        def sign_func(uri, data=None):
            return local_sign(uri, data)
        
        self.client = XhsClient(cookie=self.cookie, sign=sign_func)
        
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取当前登录用户信息"""
        try:
            info = self.client.get_self_info()
            print(f"👤 当前用户: {info.get('nickname', '未知')}")
            return info
        except Exception as e:
            print(f"⚠️ 无法获取用户信息: {e}")
            return None
    
    def publish(self, title: str, desc: str, images: List[str], 
                is_private: bool = True, post_time: str = None, location: str = None) -> Dict[str, Any]: # Added location
        """发布图文笔记"""
        print(f"\n🚀 准备发布笔记（本地模式）...")
        print(f"  📌 标题: {title}")
        print(f"  📝 描述: {desc[:50]}..." if len(desc) > 50 else f"  📝 描述: {desc}")
        print(f"  🖼️ 图片数量: {len(images)}")
        if location:
            print(f"  📍 地点: {location}")
        
        try:
            result = self.client.create_image_note(
                title=title,
                desc=desc,
                files=images,
                is_private=is_private,
                post_time=post_time,
                location=location # Pass location to create_image_note
            )
            
            print("\n✨ 笔记发布成功！")
            if isinstance(result, dict):
                note_id = result.get('note_id') or result.get('id')
                if note_id:
                    print(f"  📎 笔记ID: {note_id}")
                    print(f"  🔗 链接: https://www.xiaohongshu.com/explore/{note_id}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ 发布失败: {error_msg}")
            
            if 'sign' in error_msg.lower() or 'signature' in error_msg.lower():
                print("\n💡 签名错误排查建议：")
                print("1. 确保 Cookie 包含有效的 a1 和 web_session 字段")
                print("2. Cookie 可能已过期，请重新获取")
                print("3. 尝试使用 --api-mode 通过 API 服务发布")
            elif 'cookie' in error_msg.lower():
                print("\n💡 Cookie 错误排查建议：")
                print("1. 确保 Cookie 格式正确")
                print("2. Cookie 可能已过期，请重新获取")
                print("3. 确保 Cookie 来自已登录的小红书网页版")
            
            raise

class ApiPublisher:
    """API 发布模式：通过 xhs-api 服务发布"""
    
    def __init__(self, cookie: str, api_url: str = None):
        self.cookie = cookie
        self.api_url = api_url or get_api_url()
        self.session_id = 'md2redbook_session'
        
    def init_client(self):
        """初始化 API 客户端"""
        print(f"📡 连接 API 服务: {self.api_url}")
        
        try:
            resp = requests.get(f"{self.api_url}/health", timeout=5)
            if resp.status_code != 200:
                raise Exception("API 服务不可用")
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到 API 服务: {e}")
            print(f"\n💡 请确保 xhs-api 服务已启动：")
            print(f"   cd xhs-api && python app_full.py")
            sys.exit(1)
        
        try:
            resp = requests.post(
                f"{self.api_url}/init",
                json={
                    "session_id": self.session_id,
                    "cookie": self.cookie
                },
                timeout=30
            )
            result = resp.json()
            
            if resp.status_code == 200 and result.get('status') == 'success':
                print(f"✅ API 初始化成功")
                user_info = result.get('user_info', {})
                if user_info:
                    print(f"👤 当前用户: {user_info.get('nickname', '未知')}")
            elif result.get('status') == 'warning':
                print(f"⚠️ {result.get('message')}")
            else:
                raise Exception(result.get('error', '初始化失败'))
                
        except Exception as e:
            print(f"❌ API 初始化失败: {e}")
            sys.exit(1)
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取当前登录用户信息"""
        try:
            resp = requests.post(
                f"{self.api_url}/user/info",
                json={"session_id": self.session_id},
                timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get('status') == 'success':
                    info = result.get('user_info', {})
                    print(f"👤 当前用户: {info.get('nickname', '未知')}")
                    return info
            return None
        except Exception as e:
            print(f"⚠️ 无法获取用户信息: {e}")
            return None
    
    def publish(self, title: str, desc: str, images: List[str], 
                is_private: bool = True, post_time: str = None, location: str = None) -> Dict[str, Any]: # Added location
        """发布图文笔记"""
        print(f"\n🚀 准备发布笔记（API 模式）...")
        print(f"  📌 标题: {title}")
        print(f"  📝 描述: {desc[:50]}..." if len(desc) > 50 else f"  📝 描述: {desc}")
        print(f"  🖼️ 图片数量: {len(images)}")
        if location:
            print(f"  📍 地点: {location}")
        
        try:
            payload = {
                "session_id": self.session_id,
                "title": title,
                "desc": desc,
                "files": images,
                "is_private": is_private
            }
            if post_time:
                payload["post_time"] = post_time
            if location: # Add location to payload
                payload["location"] = location
            
            resp = requests.post(
                f"{self.api_url}/publish/image",
                json=payload,
                timeout=120
            )
            result = resp.json()
            
            if resp.status_code == 200 and result.get('status') == 'success':
                print("\n✨ 笔记发布成功！")
                publish_result = result.get('result', {})
                if isinstance(publish_result, dict):
                    note_id = publish_result.get('note_id') or publish_result.get('id')
                    if note_id:
                        print(f"  📎 笔记ID: {note_id}")
                        print(f"  🔗 链接: https://www.xiaohongshu.com/explore/{note_id}")
                return publish_result
            else:
                raise Exception(result.get('error', '发布失败'))
                
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ 发布失败: {error_msg}")
            raise


async def main_image(title, content, images, topics=None, location=None): # Added location
    """图文发布模式"""
    if len(title) > 20:
        print(f'错误：标题{len(title)}字，超过20字限制'); return

    # Modified to directly use LocalPublisher
    cookie = load_cookie()
    validate_cookie(cookie)
    publisher = LocalPublisher(cookie)
    publisher.init_client()
    
    try:
        publisher.publish(title, content, images, is_private=True, location=location) # Pass location
    except Exception as e:
        print(f"❌ 图文发布失败: {e}")
        sys.exit(1)


async def main_article(title, content, topics=None, location=None): # Added location
    if len(title) > 100:
        print(f'WARNING: 标题{len(title)}字，可能超长')
    
    # This part of the code directly interacts with CDP.
    # The LocalPublisher/ApiPublisher classes are not used here directly.
    # The existing CDP logic for adding location needs to be re-evaluated if it's meant to be generic.
    # For now, I'll assume the original CDP logic for location within main_article is sufficient.

    # ... (existing main_article CDP code for location) ...
    
    pid, ws_url = await get_page_id()
    print(f'PAGE_ID: {pid}')
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        await send(ws, 'Page.navigate', {'url': 'https://creator.xiaohongshu.com/publish/publish?source=official'})
        await asyncio.sleep(5)
        await screenshot(ws, '/home/docker/webtop/config/article_step1.jpg')
        print('step1 OK')
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var tabs=Array.from(document.querySelectorAll(".creator-tab"));var t=tabs.find(t=>t.innerText.includes("长文"));t?(t.click(),"ok"):"not found";'})
        print('长文tab:', r['result']['result'].get('value'))
        await asyncio.sleep(4)
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var b=Array.from(document.querySelectorAll("button,div[role=button]"  )).find(b=>b.innerText.includes("新的创作"));b?(b.click(),"ok"):"not found";'})
        print('新的创作:', r['result']['result'].get('value'))
        print('等待编辑器...')
        await asyncio.sleep(8)
        await screenshot(ws, '/home/docker/webtop/config/article_step2.jpg')
        print('step2 OK')
        pages = await get_all_pages()
        art_ws_url = next((pg['webSocketDebuggerUrl'] for pg in pages if pg['id']==pid), ws_url)
    await asyncio.sleep(2)
    pages2 = await get_all_pages()
    fresh = next((pg for pg in pages2 if pg['id']==pid), None)
    if fresh: art_ws_url = fresh['webSocketDebuggerUrl']
    print('ws OK')
    async with websockets.connect(art_ws_url, max_size=50*1024*1024) as ws:
        await asyncio.sleep(3)
        await screenshot(ws, '/home/docker/webtop/config/article_editor.jpg')
        print('编辑器截图OK')
        for _ in range(20):
            chk = await send(ws, 'Runtime.evaluate', {'expression': 'document.querySelector("textarea")?"found":"no"'})
            if chk['result']['result'].get('value')=='found': break
            await asyncio.sleep(0.5)
        print('标题框:', chk['result']['result'].get('value'))
        title_js = json.dumps(title)
        r = await send(ws, 'Runtime.evaluate', {'expression': f'(function(){{var t=document.querySelector("textarea");if(!t)return "nf";t.focus();var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value");s.set.call(t,{title_js});t.dispatchEvent(new Event("input",{{bubbles:true}}));return "set:"+t.value;}})()'  })
        print('标题:', r['result']['result'].get('value'))
        await asyncio.sleep(1)
        print('填写正文...')
        await fill_prosemirror(ws, content, x=206, y=249)
        await asyncio.sleep(2)
        await screenshot(ws, '/home/docker/webtop/config/article_before_publish.jpg')
        print('填写完毕OK')
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var b=Array.from(document.querySelectorAll("button")).find(b=>b.innerText.includes("一键排版"));b?(b.click(),"ok"):"not found";'})
        print('一键排版:', r['result']['result'].get('value'))
        await asyncio.sleep(6)
        await screenshot(ws, '/home/docker/webtop/config/article_format.jpg')
        print('排版弹窗OK')
        for _ in range(20):
            chk2 = await send(ws, 'Runtime.evaluate', {'expression': 'document.querySelector("button.submit") ? "found" : "not found"'})
            if chk2['result']['result'].get('value') == 'found':
                break
            await asyncio.sleep(0.5)
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var b=document.querySelector("button.submit");b?(b.click(),"clicked:"+b.innerText.trim()):"not found";'})
        print('下一步:', r['result']['result'].get('value'))
        await asyncio.sleep(5)
        await screenshot(ws, '/home/docker/webtop/config/article_publish_page.jpg')
        print('发布页OK')
        for _ in range(20):
            chk3 = await send(ws, 'Runtime.evaluate', {'expression': 'Array.from(document.querySelectorAll("button")).some(b=>b.innerText.trim()=== "发布") ? "found" : "not found"'})
            if chk3['result']['result'].get('value') == 'found':
                break
            await asyncio.sleep(0.5)

        # 加话题
        if topics:
            await add_topics(ws, topics)

        # 加地点
        if location:
            r = await send(ws, 'Runtime.evaluate', {'expression': """(function(){
                var el=Array.from(document.querySelectorAll('.d-select-placeholder')).find(e=>e.innerText.trim()==='添加地点');
                if(!el) return 'no btn';
                el.click();
                var wrap=el.closest('.d-select') && el.closest('.d-select').querySelector('.d-select-input-filter');
                if(wrap) wrap.classList.remove('hide');
                return wrap ? 'ok' : 'ok_no_wrap';
            })()""", 'returnByValue': True})
            print('地点按钮:', r['result']['result'].get('value',''))
            await asyncio.sleep(0.5)
            r = await send(ws, 'Runtime.evaluate', {'expression': """(function(loc){
                var inp=document.querySelector('.d-select-input-filter input');
                if(!inp) return 'no input';
                inp.focus();
                var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                s.call(inp,loc);
                inp.dispatchEvent(new Event('input',{bubbles:true}));
                inp.dispatchEvent(new Event('change',{bubbles:true}));
                inp.dispatchEvent(new KeyboardEvent('keyup',{bubbles:true,key:'a'}));
                return 'ok:'+inp.value;
            })("LOCATION_PH")""".replace('LOCATION_PH', location), 'returnByValue': True})
            print('地点input:', r['result']['result'].get('value',''))
            await asyncio.sleep(3)
            r2 = await send(ws, 'Runtime.evaluate', {'expression': """(function(){
                var dds=document.querySelectorAll('.d-dropdown');
                var dd=Array.from(dds).find(el=>el.querySelector('.option-item'));
                if(!dd) return 'no dd with items. total:'+dds.length;
                var item=dd.querySelector('.option-item');
                if(!item) return 'no item';
                item.click();
                var name=item.querySelector('.option-name');
                return 'clicked:'+(name?name.innerText.trim():'?');
            })()""", 'returnByValue': True})
            print('候选:', r2['result']['result'].get('value',''))
            await asyncio.sleep(1)
        print('地点添加完毕')

        print('发布按钮:', chk3['result']['result'].get('value'))
        r = await send(ws, 'Runtime.evaluate', {'expression': '(function(){var b=Array.from(document.querySelectorAll("button")).find(b=>b.innerText.trim()==="发布"&&!b.disabled);if(b){b.click();return "clicked:"+b.innerText.trim();}return "not found. btns:"+Array.from(document.querySelectorAll("button")).map(b=>b.innerText.trim()).filter(t=>t).slice(0,10).join("|");})()'  })
        print('发布:', r['result']['result'].get('value'))
        await asyncio.sleep(5)
        await screenshot(ws, '/home/docker/webtop/config/article_after_publish.jpg')
        print('完成！')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='小红书自动发布')
    parser.add_argument('--type', choices=['image', 'article'], default='image', help='发布类型：image=图文, article=长文')
    parser.add_argument('--title', required=True, help='标题')
    parser.add_argument('--desc', required=True, help='正文内容') # Changed from --content to --desc
    parser.add_argument('--images', nargs='+', help='图片路径（image 模式必填）')
    parser.add_argument('--topics', nargs='+', help='话题列表（不含#号）')
    parser.add_argument('--location', help='地点名称') # Added location argument
    args = parser.parse_args()

    if args.type == 'image':
        if not args.images:
            parser.error('--images 在 image 模式下必填')
        asyncio.run(main_image(args.title, args.desc, args.images, args.topics, args.location)) # Pass location
    elif args.type == 'article':
        asyncio.run(main_article(args.title, args.desc, args.topics, args.location)) # Pass location
