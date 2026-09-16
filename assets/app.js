/* No trackers, external dependencies or storage. User text is always rendered as text. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const data=window.GUIDE;
  if(!data){$('result-count').textContent='内容未能加载，请刷新或从 GitHub 阅读。';return;}
  $('review-date').dateTime=data.reviewed_on;
  $('review-date').textContent=data.reviewed_on;
  const sources=new Map(data.sources.map(s=>[s.id,s]));
  const all=data.chapters.flatMap(c=>c.entries.map(e=>({...e,chapter:c.number,chapterTitle:c.title})));
  const entries=new Map(all.map(e=>[e.id,e]));
  const searchText=new Map(all.map(e=>[e.id,[e.id,...e.sources,e.title,e.action,e.applies_to,...e.steps,e.caveats,e.cost,e.benefit,e.jurisdiction,e.chapterTitle,
    ...e.sources.map(id=>sources.get(id).title)].join(' ').toLocaleLowerCase()]));
  let limit=20,priorFocus=null,openedFromCard=false;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const link=(text,url)=>{const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
  for(const [number,label] of [[data.stats.chapters,'个生活主题'],[data.stats.entries,'条具体建议'],[data.stats.sources,'个来源页面']]){
    const n=el('div',undefined,'stat');n.append(el('strong',String(number)),el('span',label));$('stats').append(n);
  }
  for(const c of data.chapters){const o=el('option',`${String(c.number).padStart(2,'0')} · ${c.title}`);o.value=String(c.number);$('chapter').append(o);}
  function matchRegion(e,region){
    const scope=e.jurisdiction.toLowerCase();
    if(!region)return true;
    if(region==='NSW')return /nsw|新南威尔士/.test(scope);
    if(region==='Sydney')return /sydney|悉尼|council|本地/.test(scope);
    return /\bau\b|australia|澳洲|澳大利亚|全国|通用/.test(scope);
  }
  function render(){
    const terms=$('query').value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const chapter=$('chapter').value,region=$('region').value;
    const found=all.filter(e=>(!chapter||e.chapter===Number(chapter))&&matchRegion(e,region)&&terms.every(t=>searchText.get(e.id).includes(t)));
    const selected=data.chapters.find(c=>String(c.number)===chapter);
    $('result-heading').textContent=selected?selected.title:'生活里的每一步';
    $('chapter-summary').textContent=selected?selected.summary:'';
    $('result-count').textContent=`找到 ${found.length} 条 · 共 ${all.length} 条`;
    $('entries').replaceChildren();
    for(const e of found.slice(0,limit)){
      const card=el('article',undefined,'entry');
      const meta=el('div',undefined,'entry-meta');meta.append(el('span',`${String(e.chapter).padStart(2,'0')} / ${e.chapterTitle}`),el('span','· '+e.jurisdiction));
      const bottom=el('div',undefined,'entry-bottom'),button=el('button','阅读建议与来源 ↗','read-entry');button.type='button';button.setAttribute('aria-label','阅读：'+e.title);
      button.addEventListener('click',()=>{priorFocus=button;openedFromCard=true;location.hash=e.id;});
      bottom.append(el('span',`${e.sources.length} 条引用 · ${e.reviewed_on}`),button);
      card.append(meta,el('h3',e.title),el('p',e.action),bottom);$('entries').append(card);
    }
    if(!found.length)$('entries').append(el('p','没有匹配的建议。试试更短的关键词，或清除筛选。','empty'));
    $('more').hidden=found.length<=limit;
    $('more').textContent=`再看 ${Math.min(20,found.length-limit)} 条`;
    for(const b of document.querySelectorAll('[data-chapter]'))b.setAttribute('aria-pressed',String(b.dataset.chapter===chapter));
  }
  function section(article,title,text){article.append(el('h3',title),el('p',text));}
  function openFromHash(){
    let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{id='';}
    const e=entries.get(id);
    if(!e){if($('detail').open)$('detail').close();return;}
    const article=$('detail-content');article.replaceChildren();
    const title=el('h2',e.title);title.id='detail-title';
    article.append(title,el('p',`${e.id} · ${e.jurisdiction} · 核实于 ${e.reviewed_on}`,'byline'));
    $('detail-chapter').textContent=`${String(e.chapter).padStart(2,'0')} / ${e.chapterTitle}`;
    section(article,'适合谁',e.applies_to);section(article,'建议',e.action);
    article.append(el('h3','怎么做'));const steps=el('ol');for(const step of e.steps)steps.append(el('li',step));article.append(steps);
    section(article,'成本',e.cost);section(article,'收益与依据边界',e.benefit);section(article,'限制与例外',e.caveats);section(article,'依据类型',e.evidence_type);
    article.append(el('h3','具体来源'));const list=el('ol',undefined,'source-list');
    for(const id of e.sources){const s=sources.get(id),li=el('li');li.append(link(`${id} · ${s.publisher} — ${s.title}`,s.url),el('p',s.supports,'source-support'),el('p',`访问：${s.accessed_on} · ${s.verification==='abstract'?'论文摘要':s.verification==='pdf'?'PDF 正文':'页面正文'}`,'source-support'));list.append(li);}article.append(list);
    const actions=el('div',undefined,'detail-actions');actions.append(link('在 GitHub 阅读本章',`${data.repo}/blob/main/book/${String(e.chapter).padStart(2,'0')}.md#${e.id}`),link('报告这条建议的问题',`${data.repo}/issues/new?title=${encodeURIComponent('条目 '+e.id+'：')}`));article.append(actions);
    if(!$('detail').open)$('detail').showModal();$('detail').scrollTop=0;$('close').focus();
  }
  function closeDetail(){
    if(openedFromCard){openedFromCard=false;history.back();}
    else{history.replaceState(null,'',location.pathname+location.search);$('detail').close();}
  }
  $('filters').addEventListener('submit',e=>e.preventDefault());
  $('query').addEventListener('input',()=>{limit=20;render();});
  for(const name of ['chapter','region'])$(name).addEventListener('change',()=>{limit=20;render();});
  $('reset').addEventListener('click',()=>{$('filters').reset();limit=20;render();$('query').focus();});
  for(const b of document.querySelectorAll('[data-chapter]'))b.addEventListener('click',()=>{$('query').value='';$('region').value='';$('chapter').value=b.dataset.chapter;limit=20;render();$('results').scrollIntoView({block:'start'});});
  $('more').addEventListener('click',()=>{
    const previous=$('entries').children.length;limit+=20;render();
    const firstNew=$('entries').children[previous];
    if(firstNew)firstNew.querySelector('button').focus();
  });
  $('close').addEventListener('click',closeDetail);
  $('detail').addEventListener('cancel',e=>{e.preventDefault();closeDetail();});
  $('detail').addEventListener('close',()=>{if(priorFocus&&priorFocus.isConnected)priorFocus.focus();});
  window.addEventListener('hashchange',openFromHash);
  render();openFromHash();
})();
