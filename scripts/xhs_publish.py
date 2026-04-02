#!/usr/bin/env python3
import asyncio
import websockets
import json
import base64
import argparse
import urllib.request
import os
from pathlib import Path
from playwright.async_api import async_playwright


async def get_all_pages():
    data = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read())
    return [x for x in data if x.get('type') == 'page']


async def get_page_id():
    pages = await get_all_pages()
    p = next((x for x in pages if x.get('type') == 'page'), None)
    return (p['id'], p['webSocketDebuggerUrl']) if p else (None, None)


_id = 0
async def send(ws, m, p=None):
    global _id
    _id += 1
    cid = _id
    await ws.send(json.dumps({'id': cid, 'method': m, 'params': p or {}}))
    async for msg in ws:
        r = json.loads(msg)
        if r.get('id') == cid:
            return r


async def screenshot(ws, path):
    r = await send(ws, 'Page.captureScreenshot', {'format': 'jpeg', 'quality': 60})
    with open(path, 'wb') as f:
        f.write(base64.b64decode(r['result']['data']))


async def fill_prosemirror(ws, content, x=206, y=249):
    await send(ws, 'Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    await send(ws, 'Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1
    })
    await asyncio.sleep(0.5)

    r = await send(ws, 'Runtime.evaluate', {'expression': '''
        (function(){
            var editor = document.querySelector('.tiptap.ProseMirror, .ProseMirror, .ql-editor, [contenteditable="true"]');
            if (editor) { editor.focus(); return 'ok'; }
            return 'editor not found';
        })()
    '''})
    val = r['result']['result'].get('value', '')
    print('编辑器 focus:', val)
    if val != 'ok':
        await send(ws, 'Input.insertText', {'text': content})
        return

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
    for topic in topics or []:
        r = await send(ws, 'Runtime.evaluate', {'expression': "(function(){var b=document.querySelector('button.topic-btn');if(b){b.click();return 'clicked';}return 'not found';})()"})
        print('话题按钮:', r['result']['result'].get('value'))
        await asyncio.sleep(1)
        await send(ws, 'Input.insertText', {'text': topic})
        await asyncio.sleep(1)
        # 按 Enter 确认话题关联（type + Enter）
        await send(ws, 'Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter'})
        await send(ws, 'Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter'})
        await asyncio.sleep(1)
        print(f'话题 {topic}: 已按 Enter 确认')
    print('话题添加完毕')


async def add_location(ws, location):
    if not location:
        print('地点添加完毕')
        return
    r = await send(ws, 'Runtime.evaluate', {'expression': '''
        (function(){
            var el = Array.from(document.querySelectorAll('.d-select-placeholder')).find(e => e.innerText && e.innerText.trim() === '添加地点');
            if (!el) return 'no btn';
            el.scrollIntoView({block:'center'});
            el.click();
            return 'clicked';
        })()
    '''})
    print('地点按钮:', r['result']['result'].get('value'))
    await asyncio.sleep(0.8)
    r = await send(ws, 'Runtime.evaluate', {'expression': '''
        (function(){
            var dd = Array.from(document.querySelectorAll('.d-dropdown')).find(el => el.getBoundingClientRect().width > 100);
            if (!dd) return 'no dd';
            var inp = dd.querySelector('input');
            if (!inp) return 'no input';
            inp.focus();
            inp.click();
            return 'ok';
        })()
    '''})
    print('搜索框:', r['result']['result'].get('value'))
    await asyncio.sleep(0.3)
    await send(ws, 'Input.insertText', {'text': location})
    await asyncio.sleep(3)
    r = await send(ws, 'Runtime.evaluate', {'expression': '''
        (function(){
            var dd = Array.from(document.querySelectorAll('.d-dropdown')).find(el => el.getBoundingClientRect().width > 100);
            if (!dd) return 'no dd';
            var item = dd.querySelector('.option-item');
            if (item) {
                var name = item.querySelector('.option-name');
                item.click();
                return 'clicked:' + (name ? name.innerText.trim() : item.innerText.trim());
            }
            return 'no option-item';
        })()
    '''})
    print('地点选择:', r['result']['result'].get('value'))
    await asyncio.sleep(1)
    print('地点添加完毕')


async def playwright_upload_images(images):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9222')
        context = browser.contexts[0]
        page = context.pages[0]
        await page.goto('https://creator.xiaohongshu.com/publish/publish?source=official', wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        await page.get_by_text('上传图文', exact=True).nth(1).click()
        await page.wait_for_timeout(1500)

        upload_btn = page.get_by_role('button', name='上传图片').first
        await upload_btn.click()
        await page.wait_for_timeout(800)

        file_input = page.locator('input[type=file]').first
        await file_input.set_input_files([str(Path(x)) for x in images])
        await page.wait_for_timeout(10000)

        await page.screenshot(path='/home/docker/webtop/config/playwright_after_upload.jpg', quality=60, type='jpeg')

        has_title = await page.locator('input[placeholder*="标题"], textarea[placeholder*="标题"]').count() > 0
        has_editor = await page.locator('[contenteditable="true"], .ql-editor, .ProseMirror, .tiptap.ProseMirror').count() > 0
        print('playwright_has_title:', has_title)
        print('playwright_has_editor:', has_editor)
        await browser.close()
        return has_title or has_editor


async def main_image(title, content, images, topics=None, location=None):
    if len(title) > 20:
        print(f'错误：标题{len(title)}字，超过20字限制')
        return

    ok = await playwright_upload_images(images)
    print('playwright_upload_ready:', ok)

    pid, ws_url = await get_page_id()
    print(f'PAGE_ID: {pid}')
    async with websockets.connect(ws_url, max_size=80 * 1024 * 1024) as ws:
        await asyncio.sleep(2)
        await screenshot(ws, '/home/docker/webtop/config/image_step_after_playwright.jpg')

        r = await send(ws, 'Runtime.evaluate', {'expression': f'''
            (function(){{
                var inputs = Array.from(document.querySelectorAll('input, textarea'));
                var t = inputs.find(el => (el.placeholder||'').includes('标题')) || inputs.find(el => (el.maxLength||0) === 20);
                if (!t) return 'title not found';
                t.focus();
                var proto = t.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                Object.getOwnPropertyDescriptor(proto, 'value').set.call(t, {json.dumps(title)});
                t.dispatchEvent(new Event('input', {{bubbles:true}}));
                t.dispatchEvent(new Event('change', {{bubbles:true}}));
                return 'ok';
            }})()
        '''})
        print('标题:', r['result']['result'].get('value'))
        await asyncio.sleep(0.5)

        r = await send(ws, 'Runtime.evaluate', {'expression': '''
            (function(){
                var ed = Array.from(document.querySelectorAll('[contenteditable="true"], .ql-editor, .ProseMirror, .tiptap.ProseMirror')).find(el => el.offsetParent !== null);
                if (!ed) return 'editor not found';
                ed.focus();
                return 'ok';
            })()
        '''})
        print('正文编辑器:', r['result']['result'].get('value'))
        await asyncio.sleep(0.3)
        await fill_prosemirror(ws, content, x=420, y=420)
        await asyncio.sleep(1)

        await add_topics(ws, topics)
        await add_location(ws, location)

        await screenshot(ws, '/home/docker/webtop/config/image_before_publish.jpg')
        print('发布页OK')

        r = await send(ws, 'Runtime.evaluate', {'expression': '''
            (function(){
                var b = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.trim() === '发布' && !b.disabled)
                     || Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('发布') && !b.disabled);
                return b ? 'found' : 'not found';
            })()
        '''})
        print('发布按钮:', r['result']['result'].get('value'))

        r = await send(ws, 'Runtime.evaluate', {'expression': '''
            (function(){
                var b = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.trim() === '发布' && !b.disabled)
                     || Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('发布') && !b.disabled);
                if (b) { b.click(); return 'clicked:' + b.innerText.trim(); }
                return 'not found';
            })()
        '''})
        print('发布:', r['result']['result'].get('value'))
        await asyncio.sleep(6)
        await screenshot(ws, '/home/docker/webtop/config/image_after_publish.jpg')
        print('完成！')


async def main_article(title, content, topics=None, location=None):
    if len(title) > 100:
        print(f'WARNING: 标题{len(title)}字，可能超长')
    pid, ws_url = await get_page_id()
    print(f'PAGE_ID: {pid}')
    async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
        await send(ws, 'Page.navigate', {'url': 'https://creator.xiaohongshu.com/publish/publish?source=official'})
        await asyncio.sleep(5)
        await screenshot(ws, '/home/docker/webtop/config/article_step1.jpg')
        print('step1 OK')
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var tabs=Array.from(document.querySelectorAll(".creator-tab"));var t=tabs.find(t=>t.innerText.includes("长文"));t?(t.click(),"ok"):"not found";'})
        print('长文tab:', r['result']['result'].get('value'))
        await asyncio.sleep(4)
        r = await send(ws, 'Runtime.evaluate', {'expression': 'var b=Array.from(document.querySelectorAll("button,div[role=button]")).find(b=>b.innerText.includes("新的创作"));b?(b.click(),"ok"):"not found";'})
        print('新的创作:', r['result']['result'].get('value'))
        print('等待编辑器...')
        await asyncio.sleep(8)
        await screenshot(ws, '/home/docker/webtop/config/article_step2.jpg')
        print('step2 OK')
        pages = await get_all_pages()
        art_ws_url = next((pg['webSocketDebuggerUrl'] for pg in pages if pg['id'] == pid), ws_url)
    await asyncio.sleep(2)
    pages2 = await get_all_pages()
    fresh = next((pg for pg in pages2 if pg['id'] == pid), None)
    if fresh:
        art_ws_url = fresh['webSocketDebuggerUrl']
    print('ws OK')
    async with websockets.connect(art_ws_url, max_size=50 * 1024 * 1024) as ws:
        await asyncio.sleep(3)
        await screenshot(ws, '/home/docker/webtop/config/article_editor.jpg')
        print('编辑器截图OK')
        for _ in range(20):
            chk = await send(ws, 'Runtime.evaluate', {'expression': 'document.querySelector("textarea")?"found":"no"'})
            if chk['result']['result'].get('value') == 'found':
                break
            await asyncio.sleep(0.5)
        print('标题框:', chk['result']['result'].get('value'))
        title_js = json.dumps(title)
        r = await send(ws, 'Runtime.evaluate', {'expression': f'(function(){{var t=document.querySelector("textarea");if(!t)return "nf";t.focus();var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value");s.set.call(t,{title_js});t.dispatchEvent(new Event("input",{{bubbles:true}}));return "set:"+t.value;}})()'})
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
        await add_topics(ws, topics)
        await add_location(ws, location)
        r = await send(ws, 'Runtime.evaluate', {'expression': '(function(){var b=Array.from(document.querySelectorAll("button")).find(b=>b.innerText.trim()==="发布"&&!b.disabled);if(b){b.click();return "clicked:"+b.innerText.trim();}return "not found";})()'})
        print('发布:', r['result']['result'].get('value'))
        await asyncio.sleep(5)
        await screenshot(ws, '/home/docker/webtop/config/article_after_publish.jpg')
        print('完成！')


def main():
    parser = argparse.ArgumentParser(description='小红书自动发布（image=Playwright上传, article=CDP）')
    parser.add_argument('--type', choices=['image', 'article'], default='image', help='发布类型：image=图文, article=长文')
    parser.add_argument('--title', required=True, help='标题')
    parser.add_argument('--desc', required=True, help='正文内容')
    parser.add_argument('--images', nargs='+', help='图片路径（image 模式必填）')
    parser.add_argument('--topics', nargs='+', help='话题列表（不含#号）')
    parser.add_argument('--location', help='地点名称')
    args = parser.parse_args()

    if args.type == 'image':
        if not args.images:
            parser.error('--images 在 image 模式下必填')
        asyncio.run(main_image(args.title, args.desc, args.images, args.topics, args.location))
    else:
        asyncio.run(main_article(args.title, args.desc, args.topics, args.location))


if __name__ == '__main__':
    main()
