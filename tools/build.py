"""Generate the Markdown guide and its source/adaptation records."""
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
        lines=['[← 回总目录](../README.md)',
               f'# {c["number"]}. {c["title"]}',c['summary']]
        for number,e in enumerate(c['entries'],1):
            references='；'.join(
                f'{sources[sid]["publisher"]}：[{sources[sid]["title"]}]({sources[sid]["url"]})'
                +(f'，DOI：`{sources[sid]["doi"]}`' if sources[sid].get('doi') else '')
                +f'（[核实记录](../sources/README.md#{sid.lower()})）' for sid in e['sources'])
            steps=' '.join(f'{i}）{step}' for i,step in enumerate(e['steps'],1))
            lines += [f'<a id="{e["id"]}"></a>',f'### {number}. {e["title"]}',
                      '\n'.join([
                          f'- 成本：{e["cost"]}',
                          f'- 说人话：{e["action"]}',
                          f'- 怎么做：{steps}',
                          f'- 收益：{e["benefit"]}',
                          f'- 依据：{e["evidence_type"]}',
                          f'- 来源：{references}',
                          f'- 备注：{paragraph(e["caveats"])}',
                          f'- 适用：{paragraph(e["applies_to"])}；{e["jurisdiction"]}。资料核实：{e["reviewed_on"]}。'
                      ])]
        write(f'book/{c["number"]:02d}.md','\n\n'.join(lines))
    source_lines=['# 来源与核实记录','[← 总目录](../README.md)',
      '想知道一条建议根据什么，先看正文后面的来源；想知道具体核了哪部分，在这里找。每项记录都写明发布方、链接、访问日期、读了什么，以及它能支持什么。',
      '只读到论文摘要的就标摘要。同一个页面可能支持几条不同建议，因此会有重复链接。来源读过、内容写对、结论适合你，是三件不同的事；具体核查过程见[核查记录](../docs/VERIFICATION.md)。']
    methods={'full_page':'页面正文','abstract':'论文摘要','pdf':'PDF 正文'}
    for s in data['sources']:
        source_lines += [f'<a id="{s["id"].lower()}"></a>',f'## {s["id"]} · {s["title"]}',
         f'- 发布方：{s["publisher"]}\n- 页面：[{s["title"]}]({s["url"]})'
         +(f'\n- DOI：`{s["doi"]}`' if s.get('doi') else '')
         +f'\n- 访问日期：{s["accessed_on"]}\n- 读取范围：{methods.get(s["verification"],s["verification"])}',
         f'**支持内容（释义）**：{paragraph(s["supports"])}']
    write('sources/README.md','\n\n'.join(source_lines))
    actions=Counter(m['action'] for m in data['mapping'])
    labels={'adapt':'改写','reuse':'沿用原理','merge':'合并','omit':'不适用／不采用'}
    map_lines=['# 原书逐条改编对照','[← 总目录](../README.md)',
      f'基线：[{baseline["repository"]}]({baseline["url"]})，提交 `{baseline["commit"]}`。共 {len(baseline["items"])} 条。',
      '这张表记录原书每条建议在澳洲版放在哪里。改写、合并、不采用都写明理由。查具体做法时以澳洲版正文和对应来源为准，不能把原书中没有保留的数字或条件补回来。',
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
    toc='\n'.join(f'{c["number"]}. [{c["title"]}](book/{c["number"]:02d}.md)：{c["summary"]}' for c in data['chapters'])
    questions=[
        (1,'哪些小事能少出意外、少得重病？'),
        (2,'烟酒、饮食、运动，先改哪几样？'),
        (3,'每天精力不够用，总被手机和消息打断怎么办？'),
        (4,'忙了一天没干成什么，时间到底花哪了？'),
        (5,'订阅、利息、保险、养老金，哪些钱没必要白花？'),
        (6,'哪些保健品和健康套餐可以不买？'),
        (7,'没工作、没钱、房租交不上，先找谁？'),
        (8,'出车祸、被骗、替人担保，怎么少损失一点？'),
        (9,'哪些看起来不起眼的事会惹上官司？'),
        (10,'同居、结婚、分开，钱和手续怎么算？'),
        (11,'写代码、接外包、测系统，哪些事先要拿到许可？'),
        (12,'开店、注册公司、请人之前，要算哪些账？'),
        (13,'有人倒地、噎住、大出血，先做什么？'),
        (14,'账号被盗、手机丢了、钱转错了，先补哪个漏洞？'),
        (15,'押金交给谁，房东不修东西怎么办，买房能反悔吗？'),
        (16,'得了慢性病，怎么长期管、怎么安排药和复诊？'),
        (17,'老人需要照护，谁能替他决定，钱和文件怎么安排？'),
        (18,'生孩子能领什么，休假和开销怎么算？'),
        (19,'工资少了、被裁了、上班受了伤，去哪处理？'),
        (20,'孩子刚出生，喂养和睡觉最要紧的是什么？'),
        (21,'公民和 PR 出国，护照、签证和保险有什么不同？'),
        (22,'想放松，又不想花太多钱，有哪些办法？'),
        (23,'学什么技能、报什么课，怎么判断值不值？'),
        (24,'看 GP、专科、急诊，分别怎么去、怎么付钱？'),
        (25,'家里人走了，眼前先做什么，遗产以后怎么办？'),
        (26,'自己做网站或平台，收钱和存用户资料要注意什么？'),
        (27,'怀孕、生产、出院，哪些检查和手续别漏？'),
        (28,'想减肥、做医美，怎么少踩坑？'),
        (29,'亲人离世、失业、确诊重病，撑不住时找谁？'),
        (30,'孩子上学以后，哪些健康和情绪问题不能拖？'),
        (31,'成年以后，除了读大学和直接打工，还有哪些路？'),
        (32,'刚到悉尼，政府账户、交通、驾照和水电从哪办？')
    ]
    titles={c['number']:c['title'] for c in data['chapters']}
    question_table='\n'.join(f'| {question} | [{number}. {titles[number]}](book/{number:02d}.md) |' for number,question in questions)
    readme=f'''# 高性价比人生指南（澳洲悉尼版）

在悉尼生活，哪些事值得做，哪些坑可以绕开。

覆盖防病与急救、省钱与理财、失业兜底、租房买房、劳动权益、恋爱婚育、养老、出国和学技能。{len(data['chapters'])} 章、{total} 条建议，每条写清花什么、换什么、怎么做、根据什么。

主要给能读中文的澳洲公民和永久居民看。办事方法以澳洲、NSW 和悉尼为准。资料最近核实于 {DATE}，共引用 {unique_sources} 个来源页面。

[目录](#目录) · [怎么读](#怎么读) · [来源记录](sources/README.md) · [核实方法](docs/METHOD.md) · [原书改编对照](docs/ADAPTATION.md) · [更新记录](CHANGELOG.md)

---

## 这本书想回答的问题

| 问题 | 去哪看 |
|---|---|
{question_table}

## 怎么读

- 只想先知道该干什么：看条目标题和「说人话」。准备照着做时，把「怎么做」「备注」「适用」一起读。
- 想算值不值：看「成本」和「收益」。能省多少钱、能降低多少风险，有可靠数字就写数字，没有就不硬编。
- 想自己核对：点「来源」里的原始论文或官方文件。每个来源另附核实记录，写明看了正文还是摘要。
- 想找一个具体问题：从上面的表或下面的目录进入章节，也可以用 GitHub 仓库搜索。
- 刚到悉尼：先看第 32 章，再看租房、看病和工作。其他章节按自己需要读。

每条采用「成本—说人话—怎么做—收益—依据—来源—备注」的写法。办事资格单独列在末尾，金额如无特别说明均为澳元。

## 哪些地方要看仔细

公民、PR、税务居民、Medicare 和福利资格是几回事。拿到 PR 不代表所有补助马上能领，住在悉尼也不代表能用 City of Sydney 的每一项服务。正文分别标明全国、NSW 和本地条件。

论文结论和办事规则分开看。观察研究发现「有关联」，不能直接说照着做就一定得到同样的好处；政府说某项服务能申请，也不能替你证明自己符合全部条件。条目里的「依据」会说明来源是哪一类。

本书保留原项目关心的健康、时间、精力、金钱和权益。各章把常见、后果重要、能动手做的事放在前面。不同收益不硬换算成一个分数，结婚、生育和家庭选择由读者自己决定。

## 目录

{toc}

## 从哪里改来的

本书参考 [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) 的选题、章节和写法。原书 {len(baseline['items'])} 条建议的处理都记在[改编对照](docs/ADAPTATION.md)里。

适用的科学研究可以引用同一篇原始论文；中国特有的办事方法，换成核实过的澳洲做法。出处直接跟在建议后面，原作者贡献和固定版本见[参考说明](ATTRIBUTION.md)。

## 纠错与更新

发现错漏，可以在 [Issues]({REPO}/issues) 写明章节、条目、哪里有问题，并附上能支持修改的来源。具体怎么修改见[贡献指南](CONTRIBUTING.md)。

本版做过来源核查和交叉检查，记录见[核查记录](docs/VERIFICATION.md)，尚未经过医生、律师或持牌财务专业人士逐条审校。政策、收费和资格会变，办事前再打开对应来源看一次。

本项目原创内容和工具采用 [Unlicense](LICENSE)。外链论文、机构文件和其他第三方材料仍按各自许可使用。
'''
    write('README.md',readme)
    print(f'Built {len(data["chapters"])} chapters / {total} entries / {len(data["sources"])} sources.')

if __name__=='__main__': main()
