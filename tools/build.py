"""Render the original 31-chapter structure as readable GitHub Markdown."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from validate import validate_data, chapter_path

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/Taku-Ne/HowToLiveBetter-Australia'
METHODS={'full_page':'相关页面正文','abstract':'论文摘要','pdf':'PDF 相关正文','upstream_citation':'原书转引；未据此声称独立阅读全文'}

def write(path,text):
    dest=ROOT/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(text.rstrip()+'\n',encoding='utf-8')

def esc(text): return str(text).replace('|','／').replace('\n',' ')

def references(e,sources):
    parts=[]
    if e['references'].strip(): parts.append('原书转引文献：'+e['references'].strip())
    for sid in e['sources']:
        s=sources[sid]
        if s['verification']=='upstream_citation':
            parts.append(f'[{s["title"]}]({s["url"]})（原题与转引出处）')
        else:
            parts.append(f'{s["publisher"]}：[{s["title"]}]({s["url"]})')
    records='、'.join(f'[{sid}](../sources/README.md#{sid.lower()})' for sid in e['sources'])
    return '；'.join(parts)+f'。读取范围：{records}。'

def render_chapter(c,sources,is_appendix=False):
    title=c['title'] if is_appendix else f'{c["number"]}. {c["title"]}'
    lines=['[← 回总目录](../README.md)',f'# {title}',c['summary']]
    for number,e in enumerate(c['entries'],1):
        action=e['action']
        if e['steps']:
            action+=' '+ ' '.join(f'{i}. {step}' for i,step in enumerate(e['steps'],1))
        lines += [f'<a id="{e["id"]}"></a>',f'### {number}. {e["title"]}', '\n'.join([
            f'- 成本：{e["cost"]}',f'- 说人话：{action}',f'- 收益：{e["benefit"]}',
            f'- 证据等级：{e["evidence_grade"]}。{e["evidence_type"]}',
            f'- 来源：{references(e,sources)}',
            f'- 备注：{e["caveats"]} 适用：{e["applies_to"]}；{e["jurisdiction"]}。资料整理：{e["reviewed_on"]}。'])]
    return '\n\n'.join(lines)

def main():
    data=json.loads((ROOT/'sources/guide.json').read_text(encoding='utf-8-sig'))
    baseline=json.loads((ROOT/'sources/upstream.json').read_text(encoding='utf-8-sig'))
    errors=validate_data(data,baseline['items'],range(1,32))
    if errors: raise SystemExit('\n'.join(errors))
    sources={s['id']:s for s in data['sources']}
    paths={c['number']:chapter_path(c,baseline['items']) for c in data['chapters']}
    locations={e['id']:f'{paths[c["number"]]}#{e["id"]}' for c in data['chapters'] for e in c['entries']}
    for c in data['chapters']: write(paths[c['number']],render_chapter(c,sources))
    for c in data.get('appendices',[]): write(c['path'],render_chapter(c,sources,True))
    # Split detailed records to remain comfortably below GitHub's Markdown size limit.
    groups=defaultdict(list)
    for s in data['sources']:
        if s['id'].startswith('O') and s['id'][1:].isdigit():
            group=Path(paths[int(s['id'][1:3])]).name
        elif s['id'].startswith(('H','RH')): group='健康与急救.md'
        elif s['id'].startswith(('W','RW')): group='工作法律与金钱.md'
        elif s['id'].startswith(('L','RL')): group='生活与家庭.md'
        else: group='其他研究与澳洲资料.md'
        groups[group].append(s)
    index=['# 来源与读取范围','[← 总目录](../README.md)',
      '正文的原始文献书目与澳洲办事来源都可直接点击。这里进一步说明读到了什么：正文、摘要、PDF，还是原书转引。原书转引不等于已独立核实原论文；同一页面有时支持多条建议，记录数不是独立研究数量。',
      'O 开头的 498 项记录对应原书 498 个条目，固定到同一提交。它们证明选题和转引关系，不单独证明澳洲规则。其余编号的日期和读取范围见具体记录。',
      '| 编号 | 来源 | 读取范围 |','|---|---|---|']
    record_directory=['# 核实记录','[← 总目录](../../README.md) · [来源编号索引](../../sources/README.md)',
      '原书逐条引用和澳洲资料分开记录。标注「原书转引」的论文没有在本次修订中全部独立通读；无法核实或不适用的推论不能因此变成澳洲事实。']
    for group,items in sorted(groups.items()):
        file='docs/核实记录/'+group
        record_directory.append(f'- [{group[:-3]}]({group})：{len(items)} 项记录。')
        lines=[f'# {group[:-3]}：来源记录','[← 来源索引](../../sources/README.md) · [← 总目录](../../README.md)']
        for s in items:
            index.append(f'| <a id="{s["id"].lower()}"></a>[{s["id"]}](../{file}#{s["id"].lower()}) | {esc(s["title"])} | {METHODS[s["verification"]]} |')
            lines += [f'<a id="{s["id"].lower()}"></a>', f'## {s["id"]} · {s["title"]}',
                f'- 发布方：{s["publisher"]}\n- 页面：[{s["title"]}]({s["url"]})\n- 访问日期：{s["accessed_on"]}\n- 读取范围：{METHODS[s["verification"]]}',
                f'**支持内容与限制**：{s["supports"]}']
        write(file,'\n\n'.join(lines))
    write('sources/README.md','\n'.join(index))
    write('docs/核实记录/README.md','\n\n'.join(record_directory))
    actions=Counter(m['action'] for m in data['mapping'])
    map_lines=['# 原书逐条改编对照','[← 总目录](../README.md)',
      f'固定基线：[{baseline["repository"]}]({baseline["url"]})，提交 `{baseline["commit"]}`。原书 31 章、498 条，在本版保留相同章节、顺序和条目位置。',
      f'沿用研究与原理 {actions["reuse"]} 条；替换澳洲做法 {actions["adapt"]} 条。没有合并、跳过或挪到其他章节。沿用不表示逐字照抄，也不表示原书的全部推论都成立；修正和限制写在正文。']
    originals={(x['chapter'],x['item']):x for x in baseline['items']}
    for chapter in range(1,32):
        table=['| 原条目 | 处理 | 澳洲版 | 理由 |','|---|---|---|---|']
        for m in (m for m in data['mapping'] if m['original_chapter']==chapter):
            original=originals[(chapter,m['original_item'])]; target=m['target_ids'][0]
            label='沿用研究／原理' if m['action']=='reuse' else '澳洲改写'
            table.append(f'| {chapter}.{m["original_item"]} {esc(original["title"])} | {label} | [{target}](../{locations[target]}) | {esc(m["reason"])} |')
        map_lines += [f'## 第 {chapter} 章','\n'.join(table)]
    write('docs/ADAPTATION.md','\n\n'.join(map_lines))
    questions=[
      (1,'几乎不花钱，就能明显降低早死风险的事有哪些？'),(2,'抽烟、喝酒、久坐、熬夜到底有什么代价？'),
      (3,'每天精力不够用、总被打断，怎么改？'),(4,'时间都花哪去了，怎么少做无收益的事？'),
      (5,'攒下的钱该怎么放，才不被利息、费率和骗局吃掉？'),(6,'哪些保健品、体检套餐可以直接不买？'),
      (7,'失业了、被欠薪了、身上没钱了，能领什么、去哪求助？'),
      (8,'婚前房产、恋爱期间的大额转账，分开以后怎么算？'),(8,'被人报案指控、被捏造事实举报，第一步做什么，事后能追究和赔偿吗？'),
      (9,'哪些「兼职」和顺手的小事会让普通人变成刑事被告？'),(10,'追人该广撒网还是死磕一个，异地恋能不能成，结婚要办什么？'),
      (11,'写哪些代码、接哪些单会惹上刑事和民事责任？'),(12,'借钱开店、开公司之前最该先想清楚什么？'),
      (13,'有人倒地、呼吸不正常、大出血、火灾、迷路，先做什么？'),(14,'账号被盗、手机丢了，第一步做什么？'),
      (15,'押金被扣、房东赶人、中介收了钱不交怎么办？'),(16,'确诊慢性病之后，长期该怎么管、怎么少花钱？'),
      (17,'老人的监护、遗嘱和钱该怎么提前安排？'),(18,'生孩子能领什么、要占掉多少时间和钱？'),
      (19,'加班费、年休假该怎么算，被裁该拿多少，上班受了伤去哪申请？'),(20,'孩子刚出生，最要紧的几件事是什么？'),
      (21,'哪些国家现在别去，出事了使领馆管到哪一步？'),(22,'去 KTV、酒吧、密室怎么不踩坑，压力大时做什么？'),
      (23,'读书、学技能、考证，哪些真的回本？'),(24,'GP、公立专科、私立专科，去哪看、自己付多少？'),
      (24,'伤得很重该怎么进急诊，治完之后伤残评估和残疾支持怎么办？'),(25,'家里人走了，先做什么、哪些钱能取回来、哪些费用先别交？'),
      (26,'做个网站或平台收钱，要办哪些证、服务器放哪？'),(27,'怀孕了、要生了，什么时候做什么，出院前后要办什么？'),
      (28,'想减肥、想变好看，哪些做法会把身体搞坏？'),(29,'亲人走了、被裁了、拿到重病诊断，头几个月最要紧的是什么？'),
      (30,'孩子上学以后，哪些身体和心理的事不能等到考完再说？'),(31,'十八岁之后除了读书和打工还有哪几条路，各自门槛是什么？')]
    titles={c['number']:c['title'] for c in data['chapters']}
    question_table='\n'.join(f'| {q} | [{n}. {titles[n]}]({paths[n]}) |' for n,q in questions)
    toc='\n'.join(f'{c["number"]}. [{c["title"]}]({paths[c["number"]]})：{c["summary"]}' for c in data['chapters'])
    grades=Counter(e['evidence_grade'] for c in data['chapters'] for e in c['entries'])
    grade_counts='、'.join(f'{g} {grades[g]} 条' for g in ('A','B','C','规则'))
    readme=f'''# 高性价比人生指南（澳洲悉尼版）

用尽量少的钱、时间和精力，避开能避开的病、损失和麻烦。

给能读中文、在澳洲生活的公民和永久居民看，办事以 NSW 和悉尼为主。按[原版](https://github.com/eternity4719/HowToLiveBetter)的 **31 章、498 条**逐条改写：通用研究留下，中国的办理方法换成澳洲的；没有等同制度的，就把区别说清楚。

[目录](#目录) · [怎么读](#怎么读) · [来源记录](sources/README.md) · [逐条改编对照](docs/ADAPTATION.md) · [更新记录](CHANGELOG.md)

## 这本书想回答的问题

| 问题 | 去哪看 |
|---|---|
{question_table}

## 怎么读

- **想按顺序读**：从目录打开章节。章节和条目顺序与原书相同，每个原题在澳洲版都有同一位置。
- **只想先看怎么办**：读标题和「说人话」。要动手办事，再看「备注」里的资格、例外和期限。
- **想知道值不值**：看「成本」和「收益」。钱、时间、精力和长期坚持的负担都算成本。
- **想自己核数字**：读「收益」，点「来源」。研究人群、年代、置信区间和争议尽量保留，观察到的关联不写成个人收益保证。
- **想找出处**：论文直接链接 DOI 或原文；原书转引会明确标出来。澳洲规则附主管机构页面，读取范围另有记录。
- **刚到悉尼**：可先看[悉尼生活入门](docs/悉尼生活入门.md)，再按需要读租房、工作和看病。

每条建议长这样；下面是第 2 章第 5 条的缩略示例，完整人群、比较和限制见[正文](book/02-不要慢慢死.md#au-02-05)：

```markdown
### 5. 低钠盐有用，但先确认自己能不能用
- 成本：买盐的价差；有肾病或相关用药的人，先问医生或药师。
- 说人话：中国农村高危人群的随机试验里，换成低钠盐后，卒中发生率相对低约 14%，全因死亡发生率相对低约 12%。
- 收益：保留原研究效应量、随访时间和适用人群；不当作每个人都能得到的绝对收益。
- 证据等级：A。随机对照试验；不是人人适用。
- 来源：Neal B, et al. (2021). NEJM. https://doi.org/10.1056/NEJMoa2105675
- 备注：涉及肾功能、血钾和药物相互作用，先核对个人情况。
```

金额如无特别说明为澳元。公民、PR、税务居民、Medicare 资格和福利资格分别判断；拿了 PR 不代表所有补助马上能领。资料整理日期为 2026-09-16，各来源实际读取日期见记录。

## 四种资源

这本书考虑四种东西：**寿命、时间与精力、金钱、人身自由**。每条都问同样两件事：付出什么，换回什么。

不同口径分开算。某研究死亡风险低 12%、每月少交一笔订阅费、避免错过申诉期限，不在同一把尺子上。帮自己、帮家人、帮陌生人也可能付出不同成本；本书把后果和条件写出来，不把互惠概率或个人价值选择伪装成研究结论。

急救先保证现场安全。做得到的帮助包括打 000、取 AED、按接线员指示行动；施救者不应再变成第二个伤者。具体做法见第 13 章。

## 证据分级

沿用原书 A／B／C 的阅读标记，另把办事制度写成「规则」，避免把法规当医学试验：

| 等级 | 含义 |
|---|---|
| A | 有可量化研究结果，例如荟萃分析、大型队列或随机试验；研究设计和限制仍要看正文 |
| B | 有研究或专业资料支持，但证据有限、样本较小，或不能给出稳定的个人收益 |
| C | 编辑建议、成本核算或经验性做法；没有直接证明其效果的研究 |
| 规则 | 法律、服务资格、申请方法或官方办理指引；准确性取决于地区、日期和个人条件 |

目前 {grade_counts}。这不是 GRADE 评级，也不是「A 就一定正确」。原书转引与独立核实是另一维度，不能由等级推断已经通读全部原论文。详见[核实方法](docs/METHOD.md)。

## 性价比档

沿用原书「花掉什么、换回什么」的看法，但不把人民币金额、国外相对风险和悉尼个人情况直接折成一个分数。

| 维度 | 怎么看 |
|---|---|
| 口径 | 换寿命、钱、时间精力，还是保住权利与人身自由；不同口径分别比较 |
| 收益量级 | 有绝对金额或绝对风险就列出来；只有相对风险，要一起看基线风险、人群和时间 |
| 成本 | 钱、机会成本、时间、长期坚持和可能的副作用都算；补贴减成本，贷款只是推迟付款 |
| 优先顺序 | 先做适合自己、成本低、收益可信的事；紧急情况和法定期限优先 |

原版顺序保留用于对照，不等于这些条目在澳洲也有完全相同的性价比排名。疫苗是否免费、能不能报销、能否得到补助，都会改变个人的账。

## 读懂数字（术语表）

<details>
<summary>展开术语表</summary>

| 术语 | 意思 |
|---|---|
| 全因死亡 | 不分死因的死亡；发生率、风险及随访时间要看原研究，不能统称某人的寿命增加 |
| HR | 危险比，比较随访期间事件发生的瞬时速率；0.8 不是「每个人死亡概率少 20 个百分点」 |
| RR | 风险比，两组在相应时间内事件概率之比；0.8 表示相对低 20%，绝对差取决于基线风险 |
| OR | 比值比。概率为 p 时 odds 是 p/(1-p)；OR 不能直接当概率倍数，事件很少时才可能接近 RR |
| IRR、RaR | 发生率或次数率之比；要保留随访时间、事件定义和分母 |
| SMR | 标准化死亡比：观察死亡数与按参照人群计算的预期死亡数之比 |
| 风险差 | 两组概率相减。例如从 10% 到 8%，绝对少 2 个百分点，相对少 20% |
| 95% CI | 置信区间，表示估计的不确定性。不能解释成此区间有 95% 概率包含固定真值；区间跨 1 或 0 也不等于证明没效果 |
| RCT | 随机对照试验，随机分组有助于比较因果效果；仍要看偏倚、失访、样本和适用人群 |
| 荟萃分析 | 合并多项研究的统计结果；质量仍受原研究和合并方法限制 |
| 队列、观察研究 | 跟踪或观察不同人群；混杂和反向因果可能影响结果 |
| 混杂、反向因果 | 例如健康状况同时影响运动和死亡，或者疾病使人睡得更多，未必是睡得多造成疾病 |
| d、g、r | 标准化均值差或相关系数；不是百分比，惯用的大中小界限不是通用临床阈值 |
| MET、MET·h | 运动强度、强度乘时间的量；研究用法和个人强度会有差异 |
| 意向筛查分析 | 按最初分配的筛查组比较，不因是否真参加而改组；不等同实际参加者的效果 |
| 包年 | 每天吸烟包数乘年数；筛查还会看年龄、戒烟时间等条件 |
| BMI、LDL、HbA1c | 体重指数、低密度脂蛋白胆固醇、糖化血红蛋白；需结合临床情况解释 |
| HPV、HBsAg、LDCT | 人乳头瘤病毒、乙肝表面抗原、低剂量 CT；检测或筛查的用途与适用人群不同 |
| GRADE | 对证据确定性作系统评价的方法，与本书简化的 A／B／C 标记不同 |
| CPR、AED | 心肺复苏、自动体外除颤器；按澳洲急救指南及 000 接线员指导行动 |
| Medicare、PBS、Safety Net | 医疗补贴、药品补贴及符合条件支出达到门槛后的安排；不是所有费用都全额支付 |
| super、CSP、HELP | 退休储蓄、政府补贴学位、学生贷款；补贴与贷款不同，公民与 PR 条件也不同 |
| award、ABN、GST | 行业最低雇佣条件、商业号码、商品服务税；拿 ABN 不会自动把雇员变承包人 |
| CTP、bond、RCM | 强制第三者人身伤害车险、租赁押金、适用产品的澳洲合规标志；不能互相替代其他保障 |

</details>

## 目录

{toc}

与原书同名的长文：[家庭应急装备清单](docs/家庭应急装备清单.md)、[做平台要办哪些证](docs/做平台要办哪些证.md)、[结婚划不划算](docs/结婚划不划算.md)、[遇到陌生人出事该不该停](docs/遇到陌生人出事该不该停.md)。澳洲额外内容放在[悉尼生活入门](docs/悉尼生活入门.md)。来源读取过程见[核实记录](docs/核实记录/README.md)。

## 正文

正文分成 31 个 Markdown 文件放在 [book/](book/)，点目录就能读。章节文件名与原书一致，条目固定为成本、说人话、收益、证据等级、来源、备注六项。

原作者贡献、许可和固定版本见[参考说明](ATTRIBUTION.md)。本次改编保留原书允许使用的内容和出处，外链论文与机构资料仍按各自许可使用。

发现错误可在 [Issues]({REPO}/issues) 写明章节、条目和支持修改的来源；维护方法见[贡献指南](CONTRIBUTING.md)。自动检查验证条目完整、引用关系和链接，内容核查的实际范围见[核查记录](docs/VERIFICATION.md)。
'''
    write('README.md',readme)
    print(f'Built 31 chapters / 498 entries / {len(data["sources"])} source records; {len(data.get("appendices",[]))} local appendix.')

if __name__=='__main__': main()
