"""Create editable 16:9 treatments from an explicit outline and current canvas assets."""
from __future__ import annotations
from html import escape
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

from _client import SkillError
from _downloads import download_items


def build_treatment(client, session, nodes, args):
    outline = json.loads(Path(args.outline_file).expanduser().read_text(encoding="utf-8-sig"))
    if not isinstance(outline, dict) or not isinstance(outline.get("title"), str) or not outline["title"].strip():
        raise SkillError("Outline requires a title and sections.")
    sections = outline.get("sections")
    if not isinstance(sections, list) or not 1 <= len(sections) <= 30:
        raise SkillError("Outline requires 1..30 sections.")
    by_id = {node["id"]: node for node in nodes}
    selected = []
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get("title"), str) or not isinstance(section.get("body", ""), str):
            raise SkillError("Each section requires a title, plain-text body and node_ids.")
        ids = section.get("node_ids", [])
        if not isinstance(ids, list) or len(ids) > 6 or any(type(value) is not int for value in ids):
            raise SkillError("A section can contain at most six integer node_ids.")
        for node_id in ids:
            if node_id not in by_id:
                raise SkillError("Outline refers to a missing, incomplete or inaccessible node.")
            if node_id not in selected:
                selected.append(node_id)
    directory = Path(args.output_dir).expanduser().resolve()
    if directory.exists() and any(directory.iterdir()):
        raise SkillError("Treatment directory must be new or empty; existing work is never overwritten.")
    directory.mkdir(parents=True, exist_ok=True)
    media = [by_id[node_id] for node_id in selected if by_id[node_id]["node_type"] != "text"]
    events = []
    outcome = download_items(client, media, SimpleNamespace(output_dir=str(directory / "assets"), prefix="", max_mb=args.max_mb, workers=args.workers, session_id=session["sessionId"]), events.append)
    if outcome["failed"]:
        return {**outcome, "message": "Downloaded assets are preserved; the proposal was not presented as complete.", **client.links(session)}
    files = {item["node_id"]: Path(item["path"]).relative_to(directory).as_posix() for item in outcome["downloaded"]}
    pages = []
    for index, section in enumerate(sections, 1):
        blocks = []
        for node_id in section.get("node_ids", []):
            node = by_id[node_id]
            label = escape(str(node.get("label") or ""))
            if node["node_type"] == "text":
                blocks.append(f'<figure class="text-asset"><blockquote>{escape(node.get("body") or "")}</blockquote><figcaption>{label}</figcaption></figure>')
                continue
            src = escape(files[node_id], quote=True)
            if node["node_type"] == "image":
                content = f'<img src="{src}" alt="{label}" loading="lazy">'
            else:
                kind = node["node_type"]
                content = f'<{kind} src="{src}" controls preload="metadata" playsinline></{kind}>'
            blocks.append(f'<figure>{content}<figcaption>{label}</figcaption></figure>')
        cover = " cover" if index == 1 and len(section.get("node_ids", [])) == 1 and by_id[section["node_ids"][0]]["node_type"] == "image" else ""
        pages.append(f'''<section class="slide{cover}" aria-label="{index} {escape(section['title'])}">
          <header><span>{escape(outline['title'])}</span><span>{escape(args.studio or '')}</span></header>
          <h1 data-edit>{escape(section['title'])}</h1><p class="body" data-edit>{escape(section.get('body', ''))}</p>
          <div class="assets count-{len(blocks)}">{''.join(blocks)}</div>
          <footer><span>Director Treatment</span><span>{index:02d} / {len(sections):02d}</span></footer></section>''')
    document = TEMPLATE.replace("{{TITLE}}", escape(outline["title"])).replace("{{PAGES}}", "".join(pages))
    page = directory / "index.html"
    page.write_text(document, encoding="utf-8")
    # No temporary signed media links, credentials or transcripts enter the package.
    manifest = {"title": outline["title"], "session_id": session["sessionId"], "project": session["project"], "sections": sections, "assets": [{"node_id": node_id, "path": path} for node_id, path in files.items()]}
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle = directory / "treatment.zip"
    with zipfile.ZipFile(bundle, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in [page, directory / "manifest.json", *[directory / value for value in files.values()]]:
            archive.write(path, path.relative_to(directory))
    return {"type": "complete", "html": str(page), "zip": str(bundle), "pages": len(pages), "asset_count": len(files), **client.links(session)}


TEMPLATE = '''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{TITLE}}</title>
<style>*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#101010;color:#eee;font-family:system-ui,"PingFang SC",sans-serif}main{display:flex;flex-direction:column;align-items:center;gap:32px;padding:32px 24px 90px}.slide{display:flex;flex-direction:column;width:min(1280px,100%);aspect-ratio:16/9;padding:3% 4%;background:#191919;overflow:auto;scroll-margin-top:24px;border:1px solid #ffffff12;border-radius:12px}header,footer{display:flex;justify-content:space-between;gap:12px;color:#999;font-size:clamp(9px,1vw,13px)}h1{font-size:clamp(22px,3vw,40px);line-height:1.2;font-weight:500;margin:22px 0 12px;text-wrap:balance}.body{margin:0 0 18px;font-size:clamp(12px,1.4vw,18px);line-height:1.65;white-space:pre-wrap}.assets{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;flex:1;min-height:0}.count-1{grid-template-columns:minmax(0,1fr)}.count-3,.count-5,.count-6{grid-template-columns:repeat(3,minmax(0,1fr))}figure{display:flex;flex-direction:column;margin:0;min-height:0;min-width:0}img,video{width:100%;height:100%;min-height:0;object-fit:contain;background:#111;border-radius:6px}audio{width:100%;margin:auto 0}figcaption{font-size:11px;color:#999;margin-top:6px}blockquote{margin:0;overflow:auto;white-space:pre-wrap;font-size:14px;line-height:1.7}footer{margin-top:18px}nav{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);display:flex;gap:8px;padding:8px;border:1px solid #ffffff25;border-radius:14px;background:#222f}button{display:flex;align-items:center;justify-content:center;gap:6px;height:32px;padding:0 10px;border:0;border-radius:7px;background:#ffffff10;color:#fff;font:inherit;font-size:12px;cursor:pointer}button svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.6}button:focus-visible{outline:2px solid white;outline-offset:2px}[contenteditable=true]{outline:1px dashed #aaa;outline-offset:4px}@media(max-width:600px){main{padding:16px 8px 80px;gap:16px}.slide{aspect-ratio:auto;min-height:56.25vw;padding:20px}.assets{grid-template-columns:1fr}img,video{max-height:55vw}h1{margin-top:16px}.body{font-size:13px}}@media print{@page{size:landscape;margin:0}body,main{padding:0;margin:0;background:#191919}.slide{width:100vw;height:100vh;aspect-ratio:16/9;break-after:page;border:0;border-radius:0;overflow:hidden}nav{display:none}}
.cover{position:relative;isolation:isolate}.cover .assets{position:absolute;inset:0;z-index:-2;display:block}.cover figure{height:100%}.cover img{height:100%;object-fit:cover;border-radius:0}.cover figcaption{display:none}.cover::after{content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,#0005,#0002 30%,#0009)}.cover header,.cover footer{color:#ddd}.cover h1{margin:auto 0 20px;font-size:64px;line-height:1.1}.cover .body{max-width:820px;margin-bottom:auto;font-size:22px}.present{overflow:hidden}.present main{width:1280px;height:720px;padding:0;gap:0;transform:scale(var(--presentation-scale,1));transform-origin:top left}.present .slide{display:none;width:1280px;height:720px;flex:none;aspect-ratio:16/9;padding:48px 56px;overflow:hidden;border:0;border-radius:0}.present .slide.is-current{display:flex}.present nav{display:none}.present header,.present footer{font-size:13px}.present h1{font-size:40px}.present .cover h1{font-size:64px}.present .body{font-size:18px}.present .cover .body{font-size:22px}.present .assets{grid-template-columns:repeat(2,minmax(0,1fr))}.present .assets.count-1{grid-template-columns:minmax(0,1fr)}.present img,.present video{max-height:none}.present .cover .assets{display:block}@media print{.present main{transform:none;width:auto;height:auto;display:block}.present .slide{display:flex;width:100vw;height:100vh}}
</style></head><body><main>{{PAGES}}</main><nav aria-label="演示控制"><button id="prev" aria-label="上一页"><svg viewBox="0 0 24 24"><path d="m14 6-6 6 6 6"/></svg></button><button id="next" aria-label="下一页"><svg viewBox="0 0 24 24"><path d="m10 6 6 6-6 6"/></svg></button><button id="edit">编辑文字</button><button id="save">保存页面</button></nav><script>
const pages=[...document.querySelectorAll('.slide')];let current=0;
const presenting=new URLSearchParams(location.search).get('present')==='1';let playing=true;
function show(){pages.forEach((page,index)=>{page.classList.toggle('is-current',index===current);for(const media of page.querySelectorAll('video,audio')){if(presenting&&index===current&&playing&&media.tagName==='VIDEO'&&!matchMedia('(prefers-reduced-motion: reduce)').matches){media.muted=true;media.loop=true;media.play().catch(()=>{})}else media.pause()}})}
const move=n=>{current=Math.max(0,Math.min(pages.length-1,n));if(presenting)show();else pages[current].scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})};
if(presenting){document.querySelectorAll('video,audio').forEach(media=>media.controls=false);document.body.classList.add('present');const resize=()=>document.documentElement.style.setProperty('--presentation-scale',String(innerWidth/1280));resize();addEventListener('resize',resize);show();parent.postMessage({type:'tuoyuan-treatment:ready',pages:pages.length},location.origin);addEventListener('message',e=>{if(e.source!==parent||e.origin!==location.origin||e.data?.type!=='tuoyuan-treatment:show')return;if(Number.isInteger(e.data.index))current=Math.max(0,Math.min(pages.length-1,e.data.index));playing=e.data.playing===true;show()})}
document.querySelector('#prev').onclick=()=>move(current-1);document.querySelector('#next').onclick=()=>move(current+1);
if(!presenting){const observer=new IntersectionObserver(es=>{for(const e of es){if(e.isIntersecting)current=pages.indexOf(e.target);else e.target.querySelectorAll('video,audio').forEach(media=>media.pause())}},{threshold:.6});pages.forEach(p=>observer.observe(p))}
document.addEventListener('keydown',e=>{if(e.target.isContentEditable)return;if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();move(current+1)}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();move(current-1)}});
document.querySelector('#edit').onclick=()=>{const edit=document.querySelector('#edit');const on=edit.textContent==='编辑文字';document.querySelectorAll('[data-edit]').forEach(e=>e.contentEditable=String(on));edit.textContent=on?'完成编辑':'编辑文字'};
document.querySelector('#save').onclick=()=>{const clone=document.documentElement.cloneNode(true);clone.querySelectorAll('[contenteditable]').forEach(e=>e.removeAttribute('contenteditable'));clone.querySelector('#edit').textContent='编辑文字';clone.querySelector('body').classList.remove('present');clone.style.removeProperty('--presentation-scale');const blob=new Blob(['<!doctype html>'+clone.outerHTML],{type:'text/html;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='index.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
</script></body></html>'''
