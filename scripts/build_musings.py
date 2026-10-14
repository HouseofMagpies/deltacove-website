#!/usr/bin/env python3
"""Build static Musings pages from posts/*.md. Python standard library only."""
from pathlib import Path
from datetime import date
import html, re, shutil
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parents[1]

def metadata(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('Article must begin with front matter between --- lines')
    try: end = lines.index('---', 1)
    except ValueError: raise ValueError('Front matter has no closing ---')
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'): continue
        key, sep, value = line.partition(':')
        if not sep: raise ValueError('Front matter fields must use key: value')
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '\"\'': value = value[1:-1]
        fields[key.strip()] = value
    for key in ('title','date','summary'):
        if not fields.get(key): raise ValueError('Missing '+key)
    fields['date'] = date.fromisoformat(fields['date'])
    if fields.get('draft','false').lower() not in ('true','false'): raise ValueError('draft must be true or false')
    return fields, '\n'.join(lines[end+1:])

def safe_url(value):
    scheme=urlsplit(value).scheme.lower()
    return value if scheme in ('','https','http','mailto') and not value.startswith('//') else '#'

def inline(text):
    tokens=[]
    def token(value):
        tokens.append(value); return '\x00'+str(len(tokens)-1)+'\x00'
    # Escape HTML; only generated markup is allowed.
    text=html.escape(text,quote=False)
    text=re.sub(r'`([^`]+)`',lambda m:token('<code>'+m[1]+'</code>'),text)
    def link(m):
        label,url=m.groups();url=html.unescape(url)
        return token('<a href="'+html.escape(safe_url(url),quote=True)+'">'+label+'</a>')
    text=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<em>\1</em>',text)
    text=re.sub(r'\x00(\d+)\x00',lambda m:tokens[int(m[1])],text)
    return text

def markdown(body):
    """Supported Markdown: paragraphs, headings, emphasis, links, lists, quotes, fenced code."""
    output=[];paragraph=[];items=[];list_type=None;code=None
    def flush():
        nonlocal list_type
        if paragraph: output.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
        if items:
            output.append('<'+list_type+'>'+''.join('<li>'+inline(x)+'</li>' for x in items)+'</'+list_type+'>');items.clear();list_type=None
    for line in body.splitlines():
        if line.startswith('```'):
            if code is None:flush();code=[]
            else:output.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');code=None
            continue
        if code is not None:code.append(line);continue
        if not line.strip():flush();continue
        heading=re.match(r'^(#{1,6})\s+(.+)$',line)
        if heading:flush();level=len(heading[1]);output.append(f'<h{level}>'+inline(heading[2])+f'</h{level}>');continue
        item=re.match(r'^\s*(?:([-*])|\d+\.)\s+(.+)$',line)
        if item:
            typ='ul' if item[1] else 'ol'
            if paragraph or (list_type and list_type!=typ):flush()
            list_type=typ;items.append(item[2]);continue
        if line.startswith('> '):flush();output.append('<blockquote><p>'+inline(line[2:])+'</p></blockquote>');continue
        if line.strip() in ('---','***'):flush();output.append('<hr>');continue
        if items:flush()
        paragraph.append(line.strip())
    if code is not None:raise ValueError('Unclosed fenced code block')
    flush();return '\n'.join(output)

def shell(title,description,main,depth):
    base='../'*depth
    esc=html.escape
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} — DeltaCove</title><meta name="description" content="{esc(description,quote=True)}"><meta name="theme-color" content="#051e35"><link rel="stylesheet" href="{base}styles.css"><link rel="icon" href="{base}assets/favicon.svg"></head><body><a class="skip" href="#main">Skip to content</a><header class="header"><div class="wrap navigation"><a href="{base}index.html" aria-label="DeltaCove home"><img class="logo" src="{base}assets/deltacove-logo.png" alt="DeltaCove.ai" width="1222" height="352"></a><nav aria-label="Main navigation"><a href="{base}index.html#approach">Home</a><a href="{base}what-we-do.html">What we do</a><a href="{base}musings/index.html">Musings &amp; Views</a><a class="nav-contact" href="{base}index.html#contact">Let’s talk <span aria-hidden="true">↗</span></a></nav></div></header><main id="main">{main}</main><footer class="footer"><div class="wrap footer-inner"><a href="{base}index.html"><img src="{base}assets/deltacove-logo.png" alt="DeltaCove.ai" width="1222" height="352"></a><span>© 2026 DeltaCove Ltd</span><span>A safe place for change.</span></div></footer></body></html>'''

def build():
    posts=[]
    for path in sorted((ROOT/'posts').glob('*.md')):
        try:
            meta,body=metadata(path.read_text(encoding='utf-8'))
            if meta.get('draft','false').lower()=='true':continue
            if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',path.stem):raise ValueError('Use a lowercase filename with words separated by hyphens')
            posts.append((meta,path.stem,markdown(body)))
        except ValueError as e:raise ValueError(f'{path.name}: {e}') from e
    posts.sort(key=lambda p:(p[0]['date'],p[1]),reverse=True)
    out=ROOT/'musings'
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    cards=[]
    for meta,slug,content in posts:
        esc=html.escape;display=meta['date'].strftime('%d %B %Y');iso=meta['date'].isoformat()
        folder=out/slug;folder.mkdir()
        main=f'<section class="musings-header"><div class="wrap"><div class="eyebrow">Musings &amp; Views</div><h1>{esc(meta["title"])}</h1><p>{esc(meta["summary"])}</p></div></section><section class="section wrap"><article class="article-content"><a class="back-link" href="../index.html">← All Musings &amp; Views</a><div class="article-meta"><time datetime="{iso}">{display}</time> · {esc(meta.get("author","DeltaCove"))}</div>{content}<p><a href="mailto:info@deltacove.ai">Want to discuss this? Request a chat.</a></p></article></section>'
        (folder/'index.html').write_text(shell(meta['title'],meta['summary'],main,2),encoding='utf-8')
        cards.append(f'<article class="post-card"><time datetime="{iso}">{display}</time><h2><a href="{slug}/index.html">{esc(meta["title"])}</a></h2><p>{esc(meta["summary"])}</p><a class="text-link dark-link" href="{slug}/index.html">Read the view ↗</a></article>')
    main='<section class="musings-header"><div class="wrap"><div class="eyebrow">Questions. Challenges. Developing perspectives.</div><h1>Musings &amp; Views</h1><p>Thoughts on data, AI and how organisations put intelligence to work.</p></div></section><section class="section wrap"><div class="article-list">'+(''.join(cards) or '<p>New perspectives coming soon.</p>')+'</div></section>'
    (out/'index.html').write_text(shell('Musings & Views','Thoughts on data, AI and how organisations put intelligence to work.',main,1),encoding='utf-8')
    print(f'Built Musings & Views: {len(posts)} published article(s), newest first.')
if __name__=='__main__':build()
