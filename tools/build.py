"""Generate readable documents and the browser dataset from the editorial source."""
import json
from pathlib import Path
from collections import Counter
from validate import validate_data

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/Taku-Ne/HowToLiveBetter-Australia'

def write(path,text):
    dest=ROOT/path; dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(text.rstrip()+'\n',encoding='utf-8')

def paragraph(value):
    return '\n'.join(str(x) for x in value) if isinstance(value,list) else str(value)

def main():
    data=json.loads((ROOT/'sources/guide.json').read_text(encoding='utf-8-sig'))
    baseline=json.loads((ROOT/'sources/upstream.json').read_text(encoding='utf-8-sig'))
    errors=validate_data(data,baseline['items'],expected_chapters=range(1,33))
    if errors: raise SystemExit('\n'.join(errors))
    DATE=max(e['reviewed_on'] for c in data['chapters'] for e in c['entries'])
    sources={s['id']:s for s in data['sources']}
    locations={e['id']:f'book/{c["number"]:02d}.md#{e["id"]}' for c in data['chapters'] for e in c['entries']}
    total=sum(len(c['entries']) for c in data['chapters'])
    unique_sources=len({s['url'] for s in data['sources']})
    for c in data['chapters']:
        lines=['[← 总目录](../README.md) · [检索阅读](https://taku-ne.github.io/HowToLiveBetter-Australia/)',
               f'# {c["number"]:02d} · {c["title"]}',c['summary'],
               '适用范围请逐条阅读。正文核实日期不等于政策生效日期；金额、资格和办事条件以所引机构当前页面为准。']
        for e in c['entries']:
            lines += [f'<a id="{e["id"]}"></a>',f'## {e["title"]}',
                      f'**编号**：{e["id"]} · **地区**：{e["jurisdiction"]} · **核实日期**：{e["reviewed_on"]}',
                      f'**适合谁**：{paragraph(e["applies_to"])}',f'**建议**：{e["action"]}',
                      '**怎么做**：\n\n'+'\n'.join(f'{i}. {step}' for i,step in enumerate(e['steps'],1)),
                      f'**成本**：{e["cost"]}',f'**收益与依据边界**：{e["benefit"]}',
                      f'**限制与例外**：{paragraph(e["caveats"])}',f'**依据类型**：{e["evidence_type"]}',
                      '**来源**：\n\n'+'\n'.join(f'- [{sid} · {sources[sid]["publisher"]} — {sources[sid]["title"]}]({sources[sid]["url"]})'
                      +f'（[核实记录](../sources/README.md#{sid.lower()}))' for sid in e['sources'])]
        write(f'book/{c["number"]:02d}.md','\n\n'.join(lines))
    source_lines=['# 来源与核实记录','[← 总目录](../README.md)',
      '这里记录实际访问的资料、访问方式和支持的具体内容。访问成功、来源权威以及正文表述准确是不同的检查事项；本文不表示主管机构认可本项目，也不表示已完成医疗或法律专业审校。',
      '全文页面、PDF 与摘要分别标记；同一 URL 因支持不同主题可以有多条记录。研究者对每条建议进行了来源阅读，整合阶段另对高风险条目进行抽查和交叉检查。']
    methods={'full_page':'页面正文','abstract':'论文摘要','pdf':'PDF 正文'}
    for s in data['sources']:
        source_lines += [f'<a id="{s["id"].lower()}"></a>',f'## {s["id"]} · {s["title"]}',
         f'- 发布方：{s["publisher"]}\n- 页面：[{s["title"]}]({s["url"]})\n- 访问日期：{s["accessed_on"]}\n- 读取范围：{methods.get(s["verification"],s["verification"])}',
         f'**支持内容（释义）**：{paragraph(s["supports"])}']
    write('sources/README.md','\n\n'.join(source_lines))
    actions=Counter(m['action'] for m in data['mapping'])
    labels={'adapt':'改写','reuse':'沿用原理','merge':'合并','omit':'不适用／不采用'}
    map_lines=['# 原书逐条改编对照','[← 总目录](../README.md)',
      f'基线：[{baseline["repository"]}]({baseline["url"]})，提交 `{baseline["commit"]}`。共 {len(baseline["items"])} 条。',
      '对照表用于追踪主题处理，不表示原书的每个细节、数值或判断都被新版接受。合并后的建议以澳洲版正文及其来源为准；未保留的原文细节不能作为本项目建议。',
      ' · '.join(f'{labels[k]} {actions[k]} 条' for k in labels)]
    originals={(x['chapter'],x['item']):x for x in baseline['items']}
    for chapter in range(1,32):
        rows=sorted((m for m in data['mapping'] if m['original_chapter']==chapter),key=lambda m:m['original_item'])
        table=['| 原条目 | 处理 | 对应新版 | 理由 |','|---|---|---|---|']
        for m in rows:
            original=originals[(chapter,m['original_item'])]
            targets='、'.join(f'[{x}](../{locations[x]})' for x in m['target_ids']) or '—'
            esc=lambda text:str(text).replace('|','／').replace('\n',' ')
            table.append(f'| {chapter}.{m["original_item"]} {esc(original["title"])} | {labels[m["action"]]} | {targets} | {esc(m["reason"])} |')
        map_lines += [f'## 原第 {chapter} 章','\n'.join(table)]
    write('docs/ADAPTATION.md','\n\n'.join(map_lines))
    toc='\n'.join(f'| [{c["number"]:02d} · {c["title"]}](book/{c["number"]:02d}.md) | {len(c["entries"])} | {c["summary"].replace("|","／")} |' for c in data['chapters'])
    readme=f'''# 高性价比悉尼生活指南

给能读中文的澳洲公民和永久居民：把健康、钱、时间和日常权益，落实成在悉尼可以采取的行动。

**{len(data['chapters'])} 章 · {total} 条建议 · {unique_sources} 个来源页面 · {len(baseline['items'])} 条原书对照**

初版资料核实：{DATE}。正文为独立编写的澳洲／NSW 版本；仍需要持续更新。

[打开检索阅读页](https://taku-ne.github.io/HowToLiveBetter-Australia/) · [怎么核实](docs/METHOD.md) · [来源记录](sources/README.md) · [改编对照](docs/ADAPTATION.md) · [交付检查](docs/VERIFICATION.md) · [更新记录](CHANGELOG.md)

## 从哪里开始

- 想先把日常生活安排好：读 [悉尼日常生活](book/32.md)、[租房与买房](book/15.md)、[看病](book/24.md)。
- 正在工作或找工作：读 [在职、离职和工伤](book/19.md)、[没钱时的支持](book/07.md)、[钱与消费](book/05.md)。
- 想改善身体和生活习惯：读 [健康基础](book/02.md)、[精力](book/03.md)、[时间](book/04.md)。
- 想提前准备突发情况：读 [紧急情况](book/13.md)。现实中遇到生命危险先联系当地紧急服务，具体入口见该章来源。

## 怎么读

每条都写：适用人群、地区、建议、具体步骤、成本、收益边界、限制、依据及核实日期。成本和优先级因人而异；不把健康、人身安全、时间和金钱硬算成一个总分。

公民、PR、税务居民、Medicare 资格及各项福利资格分别判断。全国规则不自动覆盖所有 NSW 特例；Greater Sydney 的不同 Council 服务也不相同。第一版不系统覆盖学生签证和其他临时签证，本地读者版本将另行编写。

医疗、法律和财务条目提供一般信息及办事入口；具体诊疗、争议和财务决定应结合个人情况。每条有来源不等于每条都经过独立专业人士审校。我们宁可明确边界，也不虚构精确收益或保证资格。

## 全部章节

| 章节 | 条目数 | 内容 |
|---|---:|---|
{toc}

## 参考与许可

本项目的主题框架参考 [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter)，原项目采用 Unlicense。保留其贡献说明、固定版本与逐条处理记录，见 [ATTRIBUTION](ATTRIBUTION.md)。澳洲正文的事实依据请看各条直接引用的资料。

本项目原创内容和代码使用 [Unlicense](LICENSE)；外链论文、机构文件、商标和第三方材料仍遵循各自权利及许可，不因本仓库许可而变更。

## 更新与贡献

发现错误时，请在 [Issues]({REPO}/issues) 提供条目编号、问题及能够支持修正的来源；不要上传个人医疗、账户或身份资料。编辑及本地构建方式见 [贡献指南](CONTRIBUTING.md)。
'''
    write('README.md',readme)
    public={'reviewed_on':DATE,'repo':REPO,'chapters':data['chapters'],'sources':data['sources'],
            'stats':{'chapters':len(data['chapters']),'entries':total,'sources':unique_sources,
                     'upstream':len(baseline['items'])}}
    write('assets/data.js','window.GUIDE = '+json.dumps(public,ensure_ascii=False,separators=(',',':'))+';')
    print(f'Built {len(data["chapters"])} chapters / {total} entries / {len(data["sources"])} sources.')

if __name__=='__main__': main()
