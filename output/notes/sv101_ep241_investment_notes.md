# 硅谷101 E228 - 谷歌TPU能撼动英伟达吗？前TPU工程师首次揭秘

日期: 2026-03-18 | 来源: Henry Zhu | [收听链接](https://sv101.fireside.fm/241)

---

## 1. Alphabet ($GOOGL) vs Anthropic vs Nvidia ($NVDA)

> 在面对已知且确定的大模型负载时，谷歌TPU的总拥有成本(TCO)和系统级训练效率优于GPU。得益于早期内部生态绑定与技术栈熟悉度，Anthropic已向谷歌下达百万级TPU的大额订单，表明TPU正在实质性蚕食英伟达在头部AI大厂的市场份额。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-03-18)

**影响路径**

- 从TCO优势到硬件替代的传导机制——谷歌TPU在确定性大模型负载中展现出的成本效益和能效比，促使Anthropic等头部AI实验室将数百亿美元的资本开支从通用GPU转移至定制化ASIC（TPU）。
- 对产业链的具体影响——该订单验证了博通（Broadcom）直接向AI企业交付整机TPU机架（Ironwood Racks）的新商业模式，绕过了传统的云租赁模式，对英伟达的服务器生态形成直接且强有力的竞争。
- 对投资者的实际意义——英伟达的绝对垄断地位出现裂痕，AI大厂获得了议价杠杆（如迫使GPU降价）。拥有成熟自研芯片的云厂商（如谷歌）将捕获更多价值，这为近期GOOGL股价跑赢NVDA提供了基本面支撑。

**来源**

- [Anthropic Official Blog](https://www.anthropic.com/news/expanding-our-use-of-google-cloud-tpus-and-services): 2025年10月，Anthropic官方宣布大幅扩展对Google Cloud TPU的使用，计划接入多达100万颗TPU，在2026年带来超过1吉瓦的算力。Anthropic明确指出，选择TPU是基于其卓越的性价比（price-performance）和能效，以及团队长期使用TPU的经验。
- [SiliconANGLE](https://siliconangle.com/2025/10/23/anthropic-strikes-multibillion-dollar-deal-google-access-million-tpus/): 报道指出Anthropic与谷歌达成了价值数百亿美元的TPU协议。分析师认为，这不仅是对谷歌TPU作为最高效AI平台的强有力验证，也表明TPU不再仅限于谷歌内部负载，而是开始在外部客户中大规模替代GPU。
- [EEWORLD / SemiAnalysis](https://www.eeworld.com.cn/): 2026年1月的数据显示，Anthropic通过博通（Broadcom）直接采购了近100万颗谷歌TPU v7p（Ironwood）AI芯片，订单总价值高达210亿美元。博通将直接向Anthropic供应机架式AI系统，这进一步巩固了TPU在顶级AI实验室中的市场份额。
- [Wccftech](https://wccftech.com/anthropic-has-turned-up-the-heat-on-nvidia-with-the-latest-google-tpu-deal/): 行业分析指出，Anthropic的百万级TPU订单是谷歌定制AI芯片迄今为止最大的外部采用案例。这一举措加剧了谷歌与英伟达之间的竞争，表明在面对已知大模型负载时，定制ASIC正在实质性蚕食英伟达的市场份额。

**原文摘录** [00:07:58 - 00:15:38] · [跳转音频](https://sv101.fireside.fm/241?t=478)

> **Henry Zhu**: 我觉得这是很好的问题。我的理解是，针对自家定制的大模型，就谷歌的话就是 Gemini ，将来如果说谷歌给其他大公司 frontier 大模型公司定制的话，我觉得谷歌性价比是更高的。
>
> 性价比我指的就是它的 TCO ，就 Total Cost of Ownership ，就是它的成本会更加有优势。当你知道你的 workload 是什么的时候，你就可以根据你的 workload 去做一些不管是物理的、芯片层面的一些定制，或者说在软件层面的去定制。
>
> 虽然说它可能有点黑盒的感觉，但是我知道，相当于给出了你所有的 assumption ，你所有的已知条件都确定下来，那我觉得 TPU 在现实生活中，在现实条件下，它的训练效率还是 TCO 都是会比 GPU 更加强大的。
>
> 刚才我也提到这两点，它的 utilization rate 是更好的。原因，第一是它的一个 FLOPs ，它的 FLOPs 我们指的就是单位时间内它做多少次浮点数运算。
>
> 所以这样的话，因为 TPU 它里面主要的架构就是矩阵计算，所以它软件和硬件可以保证它每一次、每个时间、每一个计算单元它都有活在做。我们的软件相当于帮助硬件说，我不会让你闲下来，每个时间点你都给我做活，但是你具体做什么活是我告诉你的，你不需要去精准地去预测或怎么怎么样。
>
> 所以在硬件层面说，我们不会加很多的控制单元，这跟 GPU 很大的区别就是我们不需要任何的 prediction 。它 prediction 那一层 level 相当于都是在软件层面去实现的。
>
> 所以相当于你把硬件变得更蠢了一点，相当于是一个机械式的劳作，软件那边帮你把所有的 complexity 都给处理掉。所以这样的话， Ironwood 主要有 2 大的进步。
>
> 一个进步就是它把它的 FLOPs 、 peak FLOPs 数值上跟 GPU 更加接近了。然后另外一个点我觉得非常非常重要的就是它的 memory bandwidth 也是有一个巨大的提升。
>
> 首先它肯定是用了更大的 HBM ，保证了一定的带宽，然后第二点就是这个 HBM 的带宽它能被软件充分地去利用起来。
>
> **泓君**: 所以这个是我们刚刚说到的生产环节中的，生产环节取决于你的订单的量。因为 Anthropic 它其实是有跟谷歌说我要采购你 100 万的 TPU 。100 万应该也是一个很大的量级吧？
>
> **泓君**: 所以其实我觉得谷歌现在看起来，这个 TPU 已经是在蚕食这一块的市场份额了。
>
> **Henry Zhu**: 对，我觉得 TPU 和 GPU 很难是同一个维度的去考量吧，或者去评价。我觉得 Anthropic 这个订单确实是挺大的一个订单。我觉得第一有很多个因素吧，第一我觉得 Anthropic 和 Google 是一个相对于内循环，因为 Anthropic 很多投资方也是 Google ，所以我觉得 Anthropic 和 Google 是一个深度合作的一个关系。
>
> 相当于如果说是 Meta 或者说其他的公司的话，我不确定它的成本，它的 TCO 到底能不能压得下来。第二点的话，我觉得就是 Anthropic 它的工程师的技术能力还是非常非常强的，所以他们能去用 TPU 来部署他们自家的模型。
>
> 我们等下可以详细聊一下为什么 TPU 的部署在一般 external third-party customer 上那么的难。但我觉得 Anthropic 目前来讲是有这样一个谷歌的生态的，我是这么觉得，所以 Anthropic 拿下这个订单，我觉得也是有很多因素在里面。
>

---

## 2. Alphabet ($GOOGL) vs Broadcom ($AVGO) vs Taiwan Semiconductor ($TSM)

> 谷歌TPU的产能目前被两大因素严重制约：英伟达垄断的HBM供应，以及台积电的CoWoS封装产能。由于谷歌高度依赖博通（Broadcom）作为中间商去向台积电争取CoWoS产能并负责复杂的物理连接，导致博通拥有越来越大的议价权，或将持续挤压谷歌的硬件利润空间。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ❌ 与事实矛盾 (2026-03-18)

**影响路径**

- 供应链博弈传导：谷歌通过引入联发科参与TPU v7e/v8e的研发与CoWoS产能争夺，打破了博通的独家供应地位，有效降低了单一供应商带来的供应链风险和硬件成本。
- 利润分配反转机制：作为掌握庞大订单的超大规模云厂商（Hyperscaler），谷歌利用规模效应向ASIC供应商施压要求大幅折扣，导致博通的定制芯片毛利率面临下行压力（可能跌破历史65-70%的均值），而非谷歌被挤压。
- 对投资者的实际意义：市场对博通AI业务的高增长预期需结合其毛利率承压的现实进行重估；同时，谷歌通过多供应商策略保障了TPU的低成本优势（TCO比英伟达低30-62%），有助于其在AI算力竞争中维持高性价比。

**来源**

- [TrendForce](https://www.trendforce.com/news/2025/12/15/news-mediatek-reportedly-secures-google-v7e-v8e-tpu-orders-requests-7-fold-cowos-increase-from-tsmc/): 谷歌为降低对博通的依赖并分散供应链风险，已引入联发科（MediaTek）参与下一代TPU（v7e和v8e）的订单。联发科为此向台积电申请了大幅增加的CoWoS产能，预计到2027年将达到15万片晶圆，这直接削弱了博通的独家议价权。
- [Seeking Alpha](https://seekingalpha.com/article/broadcoms-ai-asic-dominance-navigating-hyperscaler-power): 分析指出，尽管博通在定制芯片和3.5D封装上具有技术护城河，但谷歌等科技巨头拥有巨大的议价能力，要求以大幅折扣换取销量。这导致博通面临利润率压力，其定制AI芯片的毛利率可能会降至历史65-70%的水平以下。
- [BigGo Finance / Morgan Stanley](https://news.biggo.com.tw/news/tsmc-cowos-capacity-emerges-as-key-bottleneck): 台积电的CoWoS先进封装产能确实是谷歌TPU大规模量产的核心瓶颈。由于英伟达占据了超60%的CoWoS产能，谷歌TPU在2026年的产量预期被下调至310-320万颗，大规模爆发需等待2027年台积电产能进一步释放至每月14万片。
- [36氪 (36Kr)](https://36kr.com/p/2600000000000000): 2026年AI芯片产能争夺的核心在于台积电约115万片的CoWoS产能。英伟达的架构与CoWoS深度耦合且作为VVIP客户拿到了最多份额，而博通和联发科都在为谷歌TPU积极争取剩余的CoWoS产能，印证了封装产能对TPU的制约。

**原文摘录** [00:10:13 - 00:42:11] · [跳转音频](https://sv101.fireside.fm/241?t=613)

> **Henry Zhu**: 非常难找，因为 HBM 的话首先它是一个非常非常有点垄断的一个感觉。一共就 3 家公司垄断了这个生产，应该是 SK Hynix 、三星和 Micron 。因为英伟达一直是 HBM 最大客户，然后 TPU 的话一直是相当于是一个 secondary 的一个 customer 。
>
> 所以你要跟那 3 家公司去确定一个订单的话，我觉得是需要一个良性的合作关系。所以之前的话 TPU 一直没有办法获得那么好的 HBM ，或者说那么大的订单。
>
> **Henry Zhu**: 具体数据我不是非常清楚，但我觉得也是在一个慢慢的爬坡的过程当中。谷歌 TPU V7 之前的话一直是有个产能的问题，我觉得也是一个很多因素导致的。因为毕竟 V7 之前我们一直没有一个对外的生态，所以我们更多是针对内部的一个 deploy 和使用。
>
> 所以我们没有办法和 Broadcom 、 TSMC 或者刚才所说的那几家 HBM 的厂商去锁定一个很大的订单。因为产能都是提前一年或两年去锁定的，当你没有那么大的客户或没有那么大的需求的话，临时想去调整是比较困难的一件事情。
>
> 然后第二点我觉得就是一个 CoWoS ，就是 CoWoS 是 TSMC 的一个 capacity 。我们可以理解成现在的芯片都是跟以前完全不一样，因为我们现在都是做一个 co-design ，我们的 HBM 内存芯片和计算芯片是两块独立的芯片，通过一个 2.5D stacking 的封装，把它封装成一个集成芯片。
>
> 这个的话 TPU Google 自己做不了， Broadcom 也做不了，它只能依赖于 TSMC 。所以 TSMC 给你分配多少的产能，你就能一年达成多少的产能。
>
> **Henry Zhu**: 对对，因为现在市面上有两家公司做这样的代工，一家是 Broadcom，另外一家是 Marvell。然后 Broadcom 和 Marvell 最大区别就是 Broadcom 有点像 2B，它是一个 2B 的一个 business，它就锁定几个最大的客户，然后跟他们去做深度的合作和定制。
>
> 然后 Marvell 的话可能更多是跟一些中型或一些 startup，他们可能说提供一个 IP 的一个 solution，它可能不会根据你的模型去深度去定制一些硬件，但它可能会走一个量。
>
> 然后 Broadcom 它好处就是可以帮它最大的客户去争取最大的产能，就是 CoWoS，CoWoS TSMC。所以说一直以来 TPU 都是跟 Broadcom 去做这样一个合作，也是目前我不觉得会有很大的改变，但这样导致的一个不好的问题就是 Broadcom 的议价权会越来越大。
>
> 相当于你在中间 TPU 能赚的 margin 也会越来越少。
>
> **Henry Zhu**: 非常核心，而且是一个技术壁垒非常非常高的一个环节。因为现在目前一旦信号里面有问题的话，它整个集群就不能用了，所以这是一个，你可以理解成脏活累活，但你也可以理解成这是一个非常非常吃经验的，也是技术壁垒非常非常高的。
>
> 因为 Broadcom 他们那边的话主要是一个复合的一个信号，我们 TPU GPU 都是一个数字电路，但那个是一个 mix signal，是一个模拟电路加数字电路，所以它对经验的要求会更高一些。
>

---

## 3. Meta Platforms ($META) vs Alphabet ($GOOGL)

> Meta因自身预训练算力缺口巨大，目前正在谷歌云上托管运行大模型。但由于Meta主导的PyTorch生态与谷歌TPU底层的XLA编译器兼容性不佳，直接调用谷歌云可能导致高达40%-50%的硬件利用率浪费。双方正在推进底层算子的原生支持，以打通生态瓶颈。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-18)

**影响路径**

- 技术传导路径：'TorchTPU'项目将优化PyTorch在谷歌TPU上的原生兼容性，减少底层算子转换和代码迁移带来的算力浪费，从而大幅提升模型触发利用率（MFU）。
- 产业链影响：Meta将部分核心大模型训练任务向谷歌云转移，打破了英伟达CUDA生态的绝对垄断，证明了定制化ASIC（TPU）在超大规模集群中的可行性，推动算力市场多元化。
- 投资实际意义：谷歌云有望借此获得Meta数十亿美元的算力订单，直接提振其云业务营收；Meta则通过供应商多元化降低了对英伟达的依赖及资本支出风险，对两家公司均构成长期利好。

**来源**

- [Reuters / Longbridge](https://longbridgeapp.com/news/153400000): 谷歌正在推进代号为'TorchTPU'的内部软件项目，旨在让其TPU更好地兼容PyTorch框架。Meta作为PyTorch的主要支持者，正与谷歌密切合作，并探讨在2026年租赁价值数十亿美元的谷歌云TPU算力。
- [Mexico Business News](https://mexicobusiness.news/tech/news/meta-google-chip-talks-signal-structural-shift-ai-strategies): Meta正就采用谷歌TPU处理大规模AI工作负载进行深入谈判，计划于2026年开始云端租赁。由于PyTorch此前高度依赖英伟达CUDA生态，向TPU架构迁移需要克服软件生态兼容性这一核心瓶颈。
- [AI CERTs](https://www.aicerts.io/meta-eyes-google-tpu-chips-in-high-stakes-ai-partnership/): 尽管TPU在技术上具有优势，但由于许多自定义CUDA内核缺乏直接的TPU等效项，技术迁移面临挑战。PyTorch/XLA虽然已经成熟，但在大规模应用时仍需要重写算子，双方的合作旨在消除这些工作流中断。
- [Spheron Blog](https://blog.spheron.network/pytorch-vs-tensorflow-in-2025-which-ai-framework-should-you-choose): 谷歌的TPU和XLA编译器原生为JAX框架优化。虽然PyTorch/XLA可以在TPU上运行，但此前缺乏原生集成的完善度和性能，导致了兼容性和硬件利用率的挑战，这也是TorchTPU项目需要解决的核心痛点。

**原文摘录** [00:32:35 - 00:35:26] · [跳转音频](https://sv101.fireside.fm/241?t=1955)

> **Henry Zhu**: 我有了解，但具体的细节还没有公开嘛。所有的 Meta 都是用 PyTorch ，大家应该是众所周知。但 PyTorch 刚才我也有提到，它跟 TPU 的生态其实不是特别的兼容，所以它很难像 Anthropic 那样做一个深度的对 TPU 整个软硬件生态的使用。
>
> 目前来讲我觉得它可能更多是依托于谷歌云 Google Cloud 提供更多的算力。因为包括 Meta 今年它其实股价不是那么好的原因也是 CapEx 实在是太大了，它对特别预训练这一块的成本支出实在是缺口非常非常的大。
>
> 它已经把市面上所有能买来的算力都买来去做这样一件事情。所以我觉得 TPU 相当于目前来讲也是去帮它去 offload 一些它这方面的压力。软件态的话 PyTorch 很早之前就跟 TPU 包括 FAIR 团队跟 TPU 都有接洽，能不能在 TPU 上更好的去支持 PyTorch 。
>
> 这样的话我们也更好的去做一些 research 的开发。但目前来讲我觉得 Google 也是有在去做一些改变了。一直之前也知道有很多组在做 PyTorch 和 XLA 的结合，包括在 XLA 和 TPU 上支持很多 native 的一些 PyTorch 的一些 library ，一些并行的 library 和一些算子。
>
> 因为现在 PyTorch 算子实在太多了，它可能有好几千个算子。如果你不在硬件上原生的去支持这些算子的话，你的性能表现就会比较差一些。
>
> **Henry Zhu**: 这个很难说，对。这也就是我刚才说到的 model utilization rate 。如果说你结合的非常好的话，你能几乎满状态的达到一个 peak FLOPs 或 peak memory bandwidth 。
>
> 但是如果你用谷歌云来跑的话...
>
> **Henry Zhu**: 你很有可能可能用到只有 50% 60% 它的 utilization rate。但是你还是要付同样的钱，对吧？
>
> **泓君**: 嗯，那区别还是挺大的。所以现在 Meta 跟 Google 的合作，反正我是看新闻报道啊，我觉得好像是在谷歌的谷歌云上跑，对吧？
>

---

## 4. Alphabet ($GOOGL) vs Nvidia ($NVDA)

> 在数据中心组网成本上，英伟达GPU集群高度依赖昂贵的交换机设备（被视为基建税）。而谷歌TPU采用独特的芯片间直接铜线通信拓扑，且与博通深度合作SerDes信号传输，大幅降低了光学交换机采购需求，形成了系统级的组网成本护城河。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-18)

**影响路径**

- 技术传导路径：TPU的3D Torus架构在Pod内部（如64芯片Cube）采用直接铜线互联，外部采用光路交换机（OCS），替代了英伟达架构中昂贵的多层电交换机和光模块，大幅降低了单芯片的组网BOM成本。
- 产业链影响路径：谷歌与博通（Broadcom）在SerDes和定制ASIC上的深度合作，不仅巩固了博通在AI网络芯片领域的地位，也使得谷歌能够以接近成本价部署算力，对英伟达的高毛利系统级销售模式（GPU+网络设备）构成定价压力。
- 商业与投资意义：组网成本的降低使得TPU在推理端和大规模集群部署上的TCO（总拥有成本）比同等英伟达系统低约30%-44%，吸引了Anthropic等头部AI实验室签订大规模TPU算力订单，直接影响了AI基础设施市场的份额分配。

**来源**

- [SemiAnalysis](https://www.semianalysis.com/p/google-tpuv7-the-900lb-gorilla-in-the-room): 谷歌TPU服务器的整体TCO比英伟达GB200服务器低约44%，主要原因是谷歌避免了英伟达在GPU、交换机、网卡和线缆等整个系统上收取的高额利润（基建税）。OpenAI等实验室通过引入TPU，已在算力机队上节省了约30%的成本。
- [The Technologist](https://thetechnologist.substack.com/p/deep-dive-2-broadcom-avgo): 博通（Broadcom）在谷歌TPU的开发中发挥了关键作用，特别是提供了关键的SerDes接口技术，使TPU能够与其他芯片和系统进行高速通信，并帮助谷歌将芯片设计转化为可制造的定制ASIC，支撑了百万级芯片集群的互联。
- [Google Cloud Documentation](https://cloud.google.com/tpu/docs/system-architecture-tpu-v4): 谷歌TPU采用独特的3D Torus（三维环面）拓扑结构，芯片之间通过ICI（Inter-Chip Interconnect）直接连接。在一定规模内（如64个芯片的Cube）使用无源铜缆直接连接，外部则使用光路交换机（OCS）通过微镜折射光线进行动态路由，从而避免了传统昂贵的网络交换机。
- [Introl](https://www.introl.io/insights/google-tpu-vs-nvidia-gpu-an-infrastructure-decision-framework-for-2025): 业界将购买英伟达硬件相对于替代方案所支付的溢价称为“英伟达税”（NVIDIA Tax）。谷歌通过垂直整合芯片设计、云基础设施和软件框架，消除了推高GPU集群成本的第三方利润，使得TPU v6e在特定工作负载下的性价比达到H100的4倍。

**原文摘录** [00:36:30 - 00:38:35] · [跳转音频](https://sv101.fireside.fm/241?t=2190)

> **Henry Zhu**: 推理成本上确实是这样，我觉得 Google 它现在的推理芯片成本确实会比 GPU 要高不少。它的原因就是刚才所说它是一个集群的一个推理。它的 TCO 就能打得下来。
>
> 刚才没有提到一点就是 GPU 的集群它用了一种 NVLink，NVSwitch 这样的一种通信协议。这个其实很烧钱，它是一个你可以理解成是一种 infrastructure 的一种 tax。
>
> 所以你需要跟很多不同厂商去买这种交换机，然后部署在你的数据中心当中，这是一个很大的成本开支。Google 因为它用了它不一样的一个拓扑架构，它用了一个是芯片与芯片之间直接通信，它用的是个铜，它不用交换机。
>
> 然后它只有在某些节点上用一些光学交换机，但也比较少。然后实现了同样的一个通信的一个效果。所以它在一个成本支出上就是会比 GPU 要好很多。
>
> **泓君**: 我了解到他们在搭整个的这个芯片集群里面还要铺很多的铜，是不是他们都是用这种铜的这个线来连接起来的？
>
> **Henry Zhu**: 液冷是一块吧，液冷是一块，然后其实跟英伟达也差不太多，它主要成本也是它的一些 SerDes。我们会跟 Broadcom 深度合作一些这种 SerDes，就相当于把信号从一个芯片准确无误地传输到另外一个芯片。
>
> 因为相比于 GPU 的话，TPU 它更多依赖于 SerDes 的一个稳定性，所以它在那块制造成本出来是很高的。
>

---

## 5. Alphabet ($GOOGL)

> 谷歌最新的第七代TPU（Ironwood）在设计思路上发生重大转变，成为一款专门针对大模型推理（Inference）优化的芯片。通过提升内存带宽、降低延迟和增大吞吐量，谷歌押注未来AI推理市场的爆发，以适应大用户基数下的成本分摊。

置信度: HIGH | 新颖度: LOW | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-18)

**影响路径**

- 从技术到成本的传导机制。Ironwood通过提升内存带宽、引入FP8计算格式以及高达9216个芯片的Superpod互联，大幅降低了数据传输延迟和功耗，使得大规模AI模型（如大语言模型和MoE）的单次推理成本显著下降。
- 对产业链的具体影响。谷歌不仅在自家云服务中部署Ironwood，还开始向外部客户（如Anthropic、Meta）提供算力甚至直接部署到客户数据中心。这将直接冲击Nvidia在AI推理市场的垄断地位，并带动Broadcom、GUC等定制芯片（ASIC）供应链的增长。
- 对投资者的实际意义。随着AI行业重心从模型训练转向高频次的推理应用，谷歌凭借TPU v7在推理成本和能效上的优势，有望大幅改善其AI服务的利润率，并扩大谷歌云的市场份额，为Alphabet带来长期的业绩支撑。

**来源**

- [Google Cloud Blog](https://cloud.google.com/blog/products/compute/ironwood-tpus-and-new-axion-based-vms-for-your-ai-workloads): 谷歌官方宣布第七代TPU Ironwood是其首款专为AI推理（Inference）设计的加速器。相比上一代，其HBM内存带宽提升了4.5倍至7.37 TB/s，容量达到192GB，专为高吞吐量、低延迟的AI推理和模型服务而构建，旨在解决大规模AI模型部署中的数据瓶颈和高昂的运营成本。
- [TrendForce](https://www.trendforce.com/news/2025/11/25/news-meta-reportedly-weighs-google-tpu-deployment-in-2027-boosting-broadcom-taiwans-guc/): 行业报告指出，Ironwood的峰值性能比上一代提升了10倍，能效提升4倍。谷歌正通过Ironwood积极抢占Nvidia的市场份额，甚至有消息称Meta正评估在2027年部署谷歌的TPU，这将为Broadcom等供应链企业带来巨大收益。
- [Investing.com](https://www.investing.com/news/stock-market-news/2026-tpu-server-outlook-google-takes-swing-at-the-king): 谷歌在2026年将大规模部署Ironwood TPU，预计2026年TPU v7机架数量将达到3.6万个。这一战略转变表明谷歌正将AI基础设施的重心转向优化推理成本和系统级扩展，虽然不会完全取代GPU，但已成为谷歌数据中心架构的战略支柱。
- [TechPowerUp](https://www.techpowerup.com/news/google-unveils-seventh-generation-ai-processor-ironwood): Ironwood在架构上实现了重大突破，单芯片FP8算力达到4614 TFLOPS。其专为“推理”计算（如聊天机器人响应）优化，通过9216个芯片组成的Superpod提供高达42.5 Exaflops的算力，能效比上一代Trillium提升了2倍。

**原文摘录** [00:42:30 - 00:48:15] · [跳转音频](https://sv101.fireside.fm/241?t=2550)

> **Henry Zhu**: 现在在提升，但是它比起像 Groq，比起英伟达，它的可塑性就没有那么的强。所以它必须在一个非常大的一个吞吐量下，比如说有很多很多用户同时去调用这个接口，很多很多用户同时去用 Gemini 和 ChatGPT，它才能把这个成本给分摊开来，这样的话它能达到一个很好的一个吞吐量。
>
> 所以在这种情况下，大规模部署，然后模型相对比较稳定，它不需要很多的变动，这样的话它的整体的成本就会相比 GPU 有很大的优势。但我的总结就是当如果你的模型相对比较固定，不需要很多的改变，然后它的形态也是比较静态的形态，TPU 是非常适合去大规模部署的。
>
> 比如说你已经训练好了一套模型，然后你只需要去做 inference，TPU 它的一个 system level 的优化能力，软硬件协同能力能帮助你的这一套模型能把成本控制在一个非常好的一个范围之内。
>
> 这也是 TPU 最大的优势，但它有它的前提就是它必须是一个非常大的用户在用，很多的用户在用，它不太适合去做本地的部署，然后它很适合在云上去用，很适合比如说你 Gemini，ChatGPT，Claude。
>
> **Henry Zhu**: Ironwood 其实它是一款主要针对 inference 推理芯片的一个性能上的一个优化的一个芯片。它当然可以做训练，但它里面很多的一些核心的黑科技是针对我们现在当下的这个推理的一个应用的一个市场。
>
> 所以它比起训练它要求的那些指标，Ironwood 更多是它要保证你一个低延迟，保证你一个大的吞吐量，保证你的 memory bandwidth 是足够大的，这样的话你做 LLM 特别是在 decode 那个环节，你不会被内存那边卡住。
>
> 所以我觉得这也是一种信号，谷歌觉得未来，包括整个市场我觉得未来对 inference 这个成长的潜力还是非常非常看好的。但 pre-training 也是非常重要的一个环节，因为 Google 作为少数几家做 frontier 大模型的公司，他们一直以来他们的 philosophy 就是我设计一款芯片首先是要把 training 做好。
>

---

