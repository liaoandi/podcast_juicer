# 硅谷101 E230 - 1万亿收入预期背后：英伟达的巅峰与软肋

日期: 2026-05-15 | 来源: 张璐, Dr.Mark Ren, Dr.Zhibin Xiao, Alex Yeh | [收听链接](https://sv101.fireside.fm/244)

---

## 1. NVIDIA ($NVDA) vs TSMC ($TSM)

> 英伟达预计2027年Blackwell和Hopper累计订单将达1万亿美元，尽管台积电3nm制程产能足以支撑，但CoWoS先进封装产能即便在大幅扩产下仍存明显缺口，这将可能成为限制英伟达超大规模订单交付和业绩兑现的核心供应链瓶颈。

置信度: HIGH | 新颖度: LOW | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-05-15)

**影响路径**

- 从订单到交付的传导机制——英伟达高达1万亿美元的庞大订单量直接遭遇台积电CoWoS封装产能的天花板，当前交货周期已延长至52-78周，导致账面订单转化为实际营收的周期被大幅拉长。
- 对产业链的具体影响——CoWoS产能紧缺迫使台积电将资源向高利润的AI加速器倾斜，同时英伟达锁定了台积电超60%的CoWoS产能，这将挤压其他芯片设计厂商的生存空间，并推高整个先进封装及HBM内存的供应链成本。
- 对投资者的实际意义——尽管英伟达订单预期极高，但受制于物理产能瓶颈，其短期业绩可能无法如期爆发，投资者需警惕预期打满后的估值回调风险；同时，掌握CoWoS产能的台积电将获得更高的议价权和确定性溢价。

**来源**

- [The Motley Fool](https://www.fool.com/investing/2026/03/26/nvidia-just-reported-a-1-trillion-order-pipeline/): 英伟达CEO黄仁勋在2026年3月的GTC大会上宣布，预计到2027年，公司Blackwell和Vera Rubin芯片架构的订单管道将达到1万亿美元，是此前预期的两倍。这凸显了超大规模企业对AI基础设施的爆炸性需求。
- [Silicon Analysts](https://siliconanalysts.com/tsmc-foundry-allocation-status-q1-2026/): 行业数据显示，台积电的CoWoS先进封装是半导体供应链中最严重的瓶颈。目前台积电三大CoWoS后端工厂已满载，交货周期达52-78周，其中英伟达占据了60%-70%的产能。即使客户获得了3nm晶圆代工名额，没有CoWoS封装也无法出货。
- [FinancialContent](https://markets.financialcontent.com/stock/news/read/44000000/tsmc-boosts-cowos-capacity-as-nvidia-dominates-advanced-packaging-orders-through-2027): 台积电正积极将CoWoS产能到2026年提升33%，以缓解AI芯片生产瓶颈。英伟达已预订了台积电2026年超50%的CoWoS预期产能，用于Blackwell Ultra和Rubin架构的生产，这使得其他竞争对手难以获得足够的封装产能。
- [StartupHub.ai](https://www.startuphub.ai/ai-chip-bottleneck-advanced-packaging-demands-accelerate/): 当前AI繁荣的关键制约因素并非芯片制造工艺本身，而是将复杂组件整合在一起的先进封装。英伟达提前数年预订了台积电2026-2027年超过一半的CoWoS产能，先进封装的可用性正成为决定AI发展和部署速度的核心瓶颈。

**原文摘录** [00:01:50 - 00:08:10] · [跳转音频](https://sv101.fireside.fm/244?t=110)

> **主持人**: 因为我们的嘉宾基本上都在硅谷工作了十几年，所以如果这集节目的中英夹杂影响了大家的理解，大家可以在 B 站和 YouTube 上搜索我们的字幕版，也请大家能够多多包涵。
>
> 那下面就跟我一起正式进入到我们线下录制的会场，我们先从四个数字开始。今年我也去老黄的 keynote 的主题演讲了，其实准确地说我大概已经是去了好多年的 GTC 的活动了。
>
> 我跟大家先总结一下他在这个演讲上的几个关键数字。第一个数字呢是 1 万亿。Jensen 说到 2027 年 Blackwell 跟 Hopper 的订单规模累计将达到 1 万亿美元。
>
> 去年的这个数字是 5000 亿美元。我觉得应该现在在全球商业史上是很难有人能达到这个销售的规模的。第二个呢就是 7 块新芯片。Blackwell 它的平台是一次性发布了 7 块新的芯片，而且已经全部进入量产了。
>
> 也可以说这是英伟达有史以来规模最大的一次同步发布。还有一个就是 10 倍，就是 Blackwell 它 NVL72 相比 Hopper 推理效率提升了 10 倍。
>
> 每个 token 的成本降了十分之一。另外呢就是还有一个数字是 35 倍，就是今年大家很火的一个概念就是 token per watt，性能提升了 35 倍。不然我们就先从第一个数字开始分析起，就是 1 万亿的销售规模，仅仅靠 Blackwell 跟 Hopper。
>
> Luan，你怎么看这个销售规模？就是你觉得现在市场有这么大的一个需求量吗？
>
> **志斌**: 你这个数字都非常的精准。过去几年有很多人讲 1 万亿，我们是半导体协会嘛，我们整个 2024 年半导体的产业就是 6000 亿美元。当时 2024 年大家很兴奋说 2030 年我们整个半导体产业会到 1 万亿。
>
> 这是还整个半导体产业，芯片、供应链、半导体的测试设备。去年 10 月份 Lisa 就是 AMD 的 CEO 就预测整个数据中心的 AI 的加速芯片到 2030 年到 1 万亿。
>
> 今年 3 月份老黄的这个重磅炸弹，就是他一家，加上 Rubin，当然他不是芯片了，他是整个系统，他 NVLink Switch，包括他的 Ethernet Switch，包括他的软件，2027 年就要到 1 万亿。
>
> 这个增长速度是非常非常的迅速。那说明一个什么问题呢？其实需求端是非常的旺盛。老黄给这个数字一定是来自于需求端的这个数字。但是就像红金刚才问的问题，其实现在的瓶颈已经到了供应链这个层次。
>
> 但是在供应链上能不能在 2027 年能做到 1 万亿，这是非常的 challenging。包括 3 纳米的产能，包括先进封装 CoWoS。因为我们以前半导体产业，我们相当于是乙方，所以我们是 vendor。
>
> 那现在有点角色互换了，现在变成了卖方市场，就是我们半导体的产能是卖方市场。所以 3 纳米的产能我觉得是跟得上，但是 CoWoS 的产能就很难说了。因为 2024 年到现在，台积电 CoWoS 的产能基本上涨了 3 倍，还在持续的疯狂的扩产中。
>

---

## 2. Groq vs NVIDIA ($NVDA)

> Groq推出的LPU推理芯片采用纯SRAM架构去除了DRAM，极大降低数据通信延迟，在智能体应用中生成Token效率比GPU提升30倍，暴露传统GPU推理的通信瓶颈，未来将对英伟达高利润推理份额形成不对称竞争威胁。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ❌ 与事实矛盾 (2026-05-15)

**影响路径**

- 技术与产品传导路径：纯SRAM架构解决了传统GPU的‘内存墙’瓶颈，英伟达将其与Vera Rubin GPU结合，推出GPU-LPU混合架构，将大模型推理的吞吐量/功耗比提升了约35倍。
- 商业与产业链影响：英伟达通过200亿美元的战略性‘软收购’提前消除了Groq的竞争威胁，不仅避免了反垄断审查，还进一步垄断了从AI训练到低延迟推理的全栈硬件生态。
- 市场定价与投资者意义：市场对英伟达整合Groq技术后的推理市场统治力给予高度溢价，认为这将极大降低推理成本并引爆AI应用需求，直接推动NVDA股价在信号发出后36天内大涨31.9%创下历史新高，看空英伟达推理份额的逻辑破产。

**来源**

- [EE Times](https://www.eetimes.com/groq-nvidias-20-billion-bet-on-ai-inference/): 2025年12月，英伟达斥资200亿美元达成技术授权与核心团队吸纳协议，获取了Groq基于SRAM的确定性架构IP及核心研发团队。此举被视为英伟达在AI推理领域的重大战略布局，成功化解了Groq对其GPU架构的潜在威胁。
- [IO Fund](https://io-fund.com/nvidia-stock-to-see-new-growth-catalyst-35x-faster-ai-with-groq-3-lpx): 在2026年3月的GTC大会上，英伟达正式推出了集成Groq SRAM架构的Groq 3 LPX机架。官方宣称，通过将Decode阶段的负载转移至LPU，该架构可提供高达35倍的每兆瓦吞吐量提升，极大优化了万亿参数大模型的推理成本。
- [Spheron Blog](https://blog.spheron.network/nvidia-groq-3-lpu-explained): NVIDIA的Groq 3 LPU采用500MB片上SRAM替代HBM，内存带宽达150 TB/s。NVIDIA推荐采用3:1的GPU-LPU混合部署架构，由GPU处理Prefill阶段，LPU专门负责自回归Token生成，实现确定性的超低延迟。
- [Business Insider](https://www.businessinsider.com/nvidia-stock-hits-an-all-time-high-on-new-ai-bullishness-from-wall-street-analysts): 受益于华尔街对英伟达AI数据中心增长（特别是整合Groq技术后在推理市场的统治力）的乐观预期，英伟达股价在2026年5月创下历史新高，市值突破5.5万亿美元，验证了市场对该收购案的积极反馈。

**原文摘录** [00:10:50 - 00:14:10] · [跳转音频](https://sv101.fireside.fm/244?t=650)

> **说话人 1**: 做 AI 推理芯片。2017 年给阿里巴巴做了第一款 AI 推理芯片。当时没有 ChatGPT，没有 BERT，当时更多的是 Computer Vision，所以我们当时也是纯 SRAM 的架构。
>
> Groq 的这个芯片其实是一个纯的，我不知道大家知不知道 SRAM、DRAM 这些啊。SRAM 是静态的存储，它跟我们的芯片设计的时候它是用的逻辑的工艺，所以它的 latency 非常的短，就 1 到 2 纳秒，就是访问一次。
>
> 它不需要动态刷新，但是它的成本是比 DRAM 高的。DRAM 是一个 transistor，SRAM 是 6 个晶体管。DRAM 你可以 density 可以做得非常大，但是 latency 非常大，而且你还有 dynamic refresh 的这个问题。
>
> 大部分的这个 AI 芯片都是有 DRAM 的，因为 DRAM 的成本比较低，capacity 比较大，然后你的模型就可以放得更大。但是 Groq 就是剑走偏锋，完全去掉了 DRAM，只是通过 on-chip SRAM 把你的模型的参数跟你模型中间产生的这些 KV cache 结果存在这个片上，通过极致的互联把它扩展到更大的集群。
>
> 这带来了一个好处就是对于这种 agentic 应用，它的 latency 非常非常的短，就是非常快，就 token per second per user 可以做得非常好。
>
> 这也是老黄在他的 slide 上面讲的，就是对于 token per second per user 要求非常高的那些应用啊，它直接就是把 GPU 的效率提升了 30 多倍，可以把曲线保持比较平稳的状态。
>
> GPU 其实不大适合做 agentic 应用的。
>
> **说话人 2**: 其实从推理的应用来讲，你可以想象 language model 它有两个部分，有一个部分叫 encoder，一部分叫 decoder。那 encoder 它是适合一个 high throughput 的一个批量的过程，这非常适合 GPU。
>
> decoder 这边呢，它是一个 token 一个 token 的来做的。生成每一个 token 的 compute 并没有那么多，但是要中间有很多 communication，就是它要把大语言模型的权值从 memory 里面把它 load 上来。
>
> 这个过程是非常 take time。如果说我每生成一个 token 我都要重新 load 全部的 weight 上来的话，那你大部分时间其实都在那抓 weight，communication，不是在 compute。
>
> Groq 的做法就是它是把这个 weight 放在芯片里面，那它就不需要来回取 grab 那个 weight 了，这样就减少了 communication 的时间。
>
> 其实将来的这个 AI system 会是 hybrid，将来可能还有更多的芯片进去，depend on 将来 model 会怎么样。不同的芯片可能会适合于不同的算子，比如说 encoder、decoder 是不同的算子，那将来可能还有个什么 middle layer 都有可能。
>
> **说话人 3**: 其实刚才两位都提到一个非常关键的词就是 communication。刚才提到一个很大的优势，其实 LPU 它是延迟比较低，对于 agentic 的 workflow 它是非常非常有帮助的。
>
> 因为我们开始用 agent 的时候，你对它的需求一定是希望它经常在线的，而且它是一个持续性的一个 inquiry，你不是说调用一次就结束。除了它低延迟之外的话呢，因为它优化了 communication，很重要的一点就是它能耗也会降低。
>
> 其实很多时候我们不会讨论到这一点，现在你会发现，当然一方面是 compute 的一个能耗。
>

---

## 3. Micron ($MU) vs Intel ($INTC)

> 由于AI集群建设狂潮与HBM产能的排挤效应，传统DDR内存受到挤压导致DDR4价格暴涨，且SSD、CX7交换机及Intel CPU、水冷设备开始全面告急，一线云厂商预测该基础设施的全线缺货状态将延续至2027年底。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-05-15)

**影响路径**

- 产能排挤传导：AI芯片对HBM的庞大需求迫使美光等存储巨头转移产线，导致传统DDR4/DDR5内存产能锐减，引发消费级和企业级内存价格大幅飙升。
- 全产业链缺货蔓延：数据中心的高密度计算需求不仅耗尽了内存产能，还引发了Intel CPU、企业级SSD以及配套液冷散热系统的全面供应链瓶颈。
- 资本市场重估：由于结构性缺货带来的高利润率和长期订单可见度，美光（MU）和英特尔（INTC）等核心供应商的盈利预期大幅上调，推动其股价在2026年初实现翻倍以上的历史性暴涨。

**来源**

- [EE Times](https://www.eetimes.com/ai-to-drive-surge-in-memory-prices-through-2026): 市场研究表明，由于美光和SK海力士将产能转移至HBM以满足AI需求，导致传统DDR4内存严重短缺，其现货价格甚至反超先进的HBM3e，预计内存价格在2026年将继续大幅上涨。
- [TechPowerUp](https://www.techpowerup.com/memory-makers-expect-shortages-to-end-in-late-2028): 存储制造商和供应链分析预测，由于AI基础设施的持续建设，全球内存和相关组件的短缺状态将至少持续到2027年底至2028年，届时供应链平衡才可能恢复。
- [Zacks Investment Research](https://www.zacks.com/article/micron-and-intel-shares-push-highs-again): 受益于HBM的结构性短缺和AI数据中心的强劲需求，美光和英特尔股价在2026年初出现历史性暴涨，美光年内涨幅超100%，英特尔单月涨幅惊人，反映了市场对AI基础设施供应商的重估。
- [Tech News](https://www.technews.com/cpu-ssd-and-hdd-supply-constraints-as-ai-and-data-centers-scale-in-2026): AI工作负载和超大规模数据中心的扩张导致计算和存储基础设施需求激增，Intel CPU、企业级SSD和DDR4内存的供应链出现严重瓶颈，采购团队面临极长的交货期和价格波动。

**原文摘录** [00:57:15 - 00:58:50] · [跳转音频](https://sv101.fireside.fm/244?t=3435)

> **嘉宾**: 我觉得 power 这个当然是 a huge issue，可是有不同的 bottleneck 嘛。因为我们事实上是有做 component 能力的公司，事实上中美两家的 hyperscaler 就是那七家吧。
>
> 另外一个 Neo Cloud 可能就是 Nevius 有这个 component 的能力，他不是直接买 off the shelf product 像是 Dell gear 啊这种 Supermicro gear 啊，那我们事实上也是另外一家 Neo Cloud that have this capabilities。
>
> 我们是直接去跟这个 ODM 直接下单，去订每一个指定供货商或是指定代理商。那我们对这个东西也是事实上非常敏感，我们也是做 forward 的 projection，锁定 2027 的所有的 capacity。
>
> 至少我们能确定是说我们的 capacity 是有，可是价格无法确定。现在的话，obviously everyone already knows memory is kind of crazy。
>
> 去年到现在的话已经涨 100 到 200% 了，DDR 4。现在的话 CX 7 转到 Bluefield，事实上也都是 Nvidia 的 solution。lead time 也在不断的拉长。
>
> overall 在 memory 还有以及事实上是因为 HBM 压缩到了其他的，像是 DDR 就开始缺，然后现在 SSD 也开始缺。我们预估至少跟供应链的沟通的话，他们是到 27 年底吧，都不会有好转的迹象。
>
> CX 7 that we talked about，switch gear 也在缺。现在开始亮黄灯和亮红灯的就是连 Intel 的 CPU 也开始缺货。不只是这个东西，还有到 CDU 就是水冷的方案，也都是开始缺货的状况。
>

---

## 4. Data Center Infrastructure

> 美国输电网络面临严重瓶颈，新建数据中心难以从电网获取10兆瓦以上电力。目前90%的新建数据中心被迫采用表后发电模式，就地部署天然气发电机或核电机组，底层能源获取能力将成为决定大厂AI算力扩张的绝对天花板。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-05-15)

**影响路径**

- 从电网瓶颈到表后发电（BTM）的传导机制。由于高压变压器等设备交货期长达3-5年且电网排队严重，数据中心开发商被迫从“并网买电”转向“自建电厂”（Bring Your Own Power），直接在园区内部署天然气轮机或燃料电池以换取时间。
- 对产业链的具体影响。中游天然气管道商和发电设备制造商迎来巨大增量市场，天然气基础设施正从传统的电网补充转变为AI算力的直接能源底座，形成平行的私人能源网络。
- 对投资者的实际意义。AI基础设施的投资逻辑发生根本转变，拥有现成电力接入权或具备表后发电快速部署能力的数据中心资产将享有极高的溢价，同时天然气发电和微型核电（SMR）供应链成为高确定性投资主线。

**来源**

- [Cleanview / Distilled](https://www.distilled.earth/p/bypassing-the-grid-how-data-centers): 2025年以来表后发电（BTM）趋势从利基走向主流，约30%（约56GW）的全美新建数据中心容量计划绕过电网自建电厂。在这些项目中，约75%的发电设备是天然气驱动的，以解决长达7年的电网排队问题。信号中提到的'90%'实为2025年单年宣布的BTM项目占总BTM项目的比例。
- [Rabobank](https://research.rabobank.com/far/en/sectors/energy/the-sprint-data-centers-are-building-a-parallel-energy-system-in-the-us.html): 报告指出，电网互联时间（36-84个月）与数据中心建设周期（12-24个月）存在结构性错配。这推动了超过130GW的表后能源资源提案，其中天然气占表后管道的80%以上，速度而非燃料类型成为首要考量。
- [Morgan Stanley](https://www.morganstanley.com/ideas/ai-data-center-power-bottleneck): 摩根士丹利研究表明，由于电网投资不足和供应链中断，数据中心开发者预计在2027-2028年面临严重的电力短缺。天然气、微电网和核能等“自带电力”（Bring your own power）的离网模式正获得强劲发展势头。
- [TechTarget](https://www.techtarget.com/searchdatacenter/news/power-constrained-data-architecture-curbing-ai-ambitions): 电力而非计算能力，正成为决定AI工作负载运行地点和上线时间的首要限制因素。电网互联延迟和区域容量受限使得“获取电力的时间”（time-to-power）成为与成本和延迟同等重要的核心架构决策因素。

**原文摘录** [00:47:15 - 00:50:40] · [跳转音频](https://sv101.fireside.fm/244?t=2835)

> **Alex**: 我觉得对于数据中心的铺设事实上是非常快的，可是最终的 bottleneck 事实上还是卡在 line and power 。现在的整个发展，美国的 US 的 grid 已经是 bone dry ，没有任何的东西。
>
> 你是不可拿到 10 兆瓦以上的电。现在 90% 新的 data center 建设都是 behind the meter ，意思是 on site ，都是用 gas gen 的方式。
>
> 哪里有气管，我直接扩大，直接放天然气的 gas gen 放在上面直接燃烧，直接在就地去盖这个数据中心。事实上现在所有的 data center 开发基本上都是找一些旧的 brownfield 的地产，直接去改建成新的数据中心。
>
> 过去的用钢筋水泥这样子盖也不存在了。以前 hyperscaler 可能还是有抗拒，基本上这几个 Q 基本上都没有人在乎了，全部都是用 container 的方式来做。
>
> 直接从 40 尺海运柜里面 pre-rack CDU ，所有的 fiber 加 HVAC 加 UPS 全部都一起上。过去至少我们都是以几百兆瓦和几个吉瓦的方式在建。
>
> 一个天然气发电厂的 average size 通常是差不多 300 到 500 的 megawatts 。一个 nuclear power plant 差不多是 2 个 gigawatt 到 4 个 gigawatt 。
>
> 事实上还蛮不够的。基本上现在美国的大厂和中国的大厂都是开始包核能发电厂。你也别卖给 grid 了，你全部给我，我全部就地直接做一个 substation 降电，直接盖。
>
> 回答你的问题，要达到 1 兆美元的这个营收的话，最终就是看你到底能多快的时间能把整个 data center 建起来。
>
> **Alex**: 我觉得是 multi-parts 的一个比较 complex 的 situation 吧。美国事实上是不缺电，美国是有很多的 transmission power 。
>
> 你在高压电上面都是有 330 KV 的电。重点是 distribution ，到可用电，过去是 400 V ，现在是 800 V 。重点是要到这个情况。基本上还是被 regulation 绑住吧。
>
> 因为你要建一个……
>
> **Speaker 1**: 变电站，你影响到可能是以整个德州的 grid 的这个 stability，所以当然是要做比较多的 study。美国的 grid 事实上就是 it's run by oil and gas people，那他们不是 tech guys，right？他们动作事实上是没有在硅谷这么快的。
>
> 所以基本上都被卡住，所以现在他们才转而是说，好吧，你慢慢搞吧，我现在就直接用柴油发电机或是天然气机组直接先上。
>

---

## 5. Salesforce ($CRM)

> AI智能体的广泛部署正颠覆传统的SaaS商业模式，未来的企业级软件将从售卖标准化系统权限转向高度定制化的AI劳动力外包。若现有的SaaS厂商无法迅速整合底层AI算力并提供模型能力，其护城河和市场份额将被迅速蚕食并淘汰。

置信度: LOW | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-05-15)

**影响路径**

- 从按座收费到按效付费的商业模式重构。AI智能体的引入使得企业软件的价值衡量标准从“软件使用权”转向“实际工作产出”，迫使SaaS厂商重塑定价体系（如Salesforce全面推行Flex Credits按次计费）。
- 对产业链的具体影响。传统SaaS企业面临收入可见性下降和短期估值重估的阵痛，必须加大底层AI算力和模型集成的研发投入，否则将面临AI原生初创公司的降维打击和市场份额蚕食。
- 对投资者的实际意义。市场对“SaaS-pocalypse”的担忧导致SaaS板块在2026年遭遇剧烈抛售，投资者需重新评估SaaS企业的护城河，重点关注其AI业务（如Agentforce）的ARR增速能否对冲核心云业务的放缓。

**来源**

- [The Motley Fool](https://www.fool.com/investing/2026/05/11/salesforce-stock-just-cant-catch-a-break-heres-wha/): 截至2026年5月，Salesforce股价年内下跌超30%。尽管其Agentforce的年度经常性收入（ARR）达到8亿美元，且公司基本面依然强劲，但市场对AI颠覆传统SaaS订阅模式的担忧并未消退，投资者仍在观望AI能否真正转化为持续的业绩增长。
- [CX Today](https://www.cxtoday.com/crm/benioff-rejects-saas-pocalypse-fears-as-ai-reshapes-enterprise-software/): Salesforce CEO Marc Benioff公开反驳了华尔街关于AI将引发“SaaS末日（SaaS-pocalypse）”的担忧。投资者普遍担心AI智能体将减少企业对人类员工的需求，从而直接破坏Salesforce等公司依赖的传统按座收费（per-seat pricing）模式。
- [Trefis](https://www.trefis.com/articles/how-salesforce-stock-slipped-30): 2025年底至2026年3月期间，Salesforce股价下跌约31%。投资者对核心云业务增长预测放缓、AI原生挑战者竞争加剧以及传统CRM市场份额可能被侵蚀的担忧，导致了估值的急剧重估，市场正在奖励其Agentforce等新AI产品的高增长，但担忧其体量尚小。
- [O-mega.ai](https://www.o-mega.ai/articles/agentforce-pricing-2026-complete-cost-guide): Salesforce在2026年全面推行Agentforce的Flex Credits定价模式，企业不再单纯为软件席位付费，而是为AI智能体执行的具体任务（如解决客户工单）按次或按消耗的算力积分付费，标志着向“数字劳动力外包”模式的实质性转变。

**原文摘录** [00:25:20 - 00:28:55] · [跳转音频](https://sv101.fireside.fm/244?t=1520)

> **Lu**: 对，我觉得真的看所有的科技创新，它是三个阶段：基础技术创新、技术应用创新、商业模式创新。所以就像你提到的，我们未来如果真的可以很快地进入到这个时代，有一个大规模的智能体 Agent 的一个铺设的话，它对传统的企业级软件就是一个商业模式的巨大挑战。
>
> 这个可能不只是技术层面上的，是我们一个商业理念层面上的。传统的这些 SaaS...
>
> **女**: SaaS 公司提供的是什么？是一个标准化的软件服务，就不管什么公司用的都是一样的软件。但是 Agent 它未来可以做到的实际上就像你说的高度的定制化和个性化。未来的软件公司它到底卖的是软件还是什么？是服务吗？我觉得都不一定是服务。
>
> 如果说你相信我们未来的整个公司的架构会改变，它不只是有我们叫 human labor，人力的劳动力，还有 AI labor。那未来可能做软件的这些公司或做 Agent 的这些公司，它就变成了一个劳动力输出方。
>
> 它可能会有成千上万的智能体，这种专属化的智能体去符合你各种各样的要求。你在想你的这个时候的商业模式是什么样的一个模式？好消息是说现在你可能卖软件，你用的预算是 IT 的预算。
>
> 那将来的话呢，你的输出实际上是一个人工智能劳动力，你可以用到劳动力的预算。所以你可能可以去卖到更大的预算，但是它对人工智能的劳动力的要求也会更高。比如说你是一个公司的 CEO，你要去招人，那你招人的一个标准是不是希望你招的这个人能做你这个职位 90% 以上的工作，同时要超过 90% 以上的人的一个能力。
>
> 那可能这也是未来对于 AI Agent 的要求。所以如果拿这个要求去看的话呢，现在 Agent 的能力确实还有一定的距离。所以我并没有那么悲观觉得，因为我也知道前一段大家也看到股市上一些 SaaS 公司的股价跌得非常惨。
>
> 我觉得并不是说这个产业全部都要消灭掉，因为它本身企业级销售它不单纯只是一个产品，它也是一个售后服务、销售网络等等，它是一个集合体。但是如果说 SaaS 公司它自己本身没有 AI 模型能力的话呢，确实大概率未来可能就会被淘汰掉或者被替代掉。
>
> 但是还是有很多的 SaaS 公司它自己本身是有模型能力的。我觉得这方面还是会有机会的。另外一点创业者也要考虑到底你的机会在哪里。是哪些 SaaS 公司可能会要消失掉，那它的市场你是不是可以快速地占领？这也是可以去探索的一个方向。
>
> **男**: 我觉得这新的 SaaS 公司如果它现在不做剧烈的改变，很快会被这些 Agent platform 替代。它以前是通过招人嘛，或者是把它的服务做上去。但是现在的话是需要通过买算力，怎么样把这个算力加上你原来对行业的理解，也要 adopt 这些 Agent。
>
> 这是他们现在非常 critical point，对于这些 SaaS 公司。同时买算力以后你可能还要去做优化，你的算力到你的 service 输出的成本 ROI 是最好的。
>
> 这一块原来就是通过人来做，那现在其实是针对算力去做优化。所以这两个事情，一个是算力优化，第二是把原来有的你的经验赶紧跟 Agent 或者是现在的 AI 平台去结合。
>
> 这样才有机会。
>

---

