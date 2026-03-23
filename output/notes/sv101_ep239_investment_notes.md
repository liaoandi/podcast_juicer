# 硅谷101 E226 - 聊聊DeepMind创始人哈萨比斯：一个科学家与失控的AI竞赛

日期: 2026-03-06 | 来源: 周健工 | [收听链接](https://sv101.fireside.fm/239)

---

## 1. Google ($GOOGL) vs OpenAI vs DeepSeek

> 大语言模型的技术演进正发生关键偏移，从纯Transformer架构向强化学习（RL）方向回摆。OpenAI o1和DeepSeek R1均开始借鉴AlphaGo的思路，这预示拥有深厚强化学习DNA的谷歌（DeepMind）在下一代推理模型竞争中可能具备底层技术优势。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-06)

**影响路径**

- 从技术演进到算力分配的传导机制——大模型训练范式从依赖海量人类数据的监督微调（SFT）转向强化学习（RL），算力需求正从预训练阶段向推理阶段（Test-time compute）转移。
- 对AI产业链的具体影响——拥有高质量强化学习算法、奖励模型（Reward Model）设计经验以及自我对弈（Self-play）架构能力的AI实验室将获得核心竞争优势，单纯依赖扩大参数规模的策略将面临收益递减。
- 对投资者的实际意义——尽管谷歌近期股价受挫（7日下跌3.8%），但其子公司DeepMind在强化学习领域（AlphaGo, AlphaZero）拥有十年的技术壁垒。随着RL成为下一代大模型的核心驱动力，谷歌的底层技术护城河可能被市场低估，存在中长期的估值修复机会。

**来源**

- [Hugging Face](https://huggingface.co/blog/deepseek-r1): DeepSeek-R1打破了常规，证明了纯强化学习（RL）可以在没有监督微调（SFT）的情况下解锁大模型的复杂推理能力（如思维链、自我反思），这标志着AI行业正从单纯的规模扩张转向强化学习驱动的推理模型。
- [arXiv (DeepSeek-R1 Paper)](https://arxiv.org/abs/2501.12948): DeepSeek团队发布的论文详细说明了如何通过纯强化学习激励LLM的推理能力，使其在数学和编程任务上达到与OpenAI o1相当的水平，验证了RL在下一代推理模型中的核心地位。
- [Medium (Large Reasoning Models)](https://medium.com/@raktimsingh/large-reasoning-models-lrms-how-o1-and-deepseek-r1-are-redefining-ais-cognitive-architecture): 行业正从传统的预测下一个Token的聊天模型转向大型推理模型（LRMs）。OpenAI o1和DeepSeek-R1的训练思路直接借鉴了DeepMind AlphaGo的强化学习和自我对弈机制，让机器学会展示思维链并自我纠错。
- [Google DeepMind](https://deepmind.google/models/gemini/): DeepMind在强化学习领域拥有深厚历史（如AlphaGo, AlphaZero）。最新的Gemini 3.1 Pro模型进一步强化了复杂推理和Agentic能力，证明谷歌正将其RL优势转化为前沿大模型的实际竞争力。

**原文摘录** [00:33:50 - 00:42:25] · [跳转音频](https://sv101.fireside.fm/239?t=2030)

> **泓君**: 提到的他们演示的关键时候会掉链子，最后这个游戏它其实是被砍掉了大量的功能才勉强能上线，所以评价也一般。这件事情其实我觉得是恰恰给哈萨比斯了一个非常深刻的教训，你拥有再好的算法和想法，如果没有足够的算力支撑，它还是只能是停在纸面上的。
>
> 另外一个点就是您刚刚提到了他从环境的反馈中去学习，这个最近也非常火，有一个词叫做强化学习。这跟 DeepMind 最开始为什么落后于 OpenAI 后面又反超的关系是很大的。
>
> 比如说大家都知道其实 Transformer 它是谷歌的另一个部门 Google Brain 发明的。DeepMind 它虽然当时也是被谷歌收购了，但是其实 DeepMind 最强的是强化学习，这也是它刻在 DNA 里的东西。
>
> 因为哈萨比斯他是一直坚信，光靠大语言模型是到达不了 AGI 的，而且还需要有类似于 AlphaGo 的那种规划和推理的能力。所以我们说虽然 DeepMind 很早就被谷歌收购了，而且谷歌手里一边是 Transformer 一边是强化学习，手里有两张王牌，但他们其实就是各干各的，早期也没有融合，这是我们看到为什么 OpenAI 早期去抢了风头。
>
> 但我觉得现在一个有意思的事情是，过去 OpenAI 的 o1 包括 DeepSeek 它的 R1 都是在往强化学习的方向去回摆，反过来也在借鉴 AlphaGo 的思路。
>
> 那现在其实强化学习它的整个的优势也开始显现出来了。
>
> **周健工**: 对，我觉得这个其实有它很深的渊源的。他谈这个事情不是从 ChatGPT 突然横空出世这个时候谈起。其实要从他们怎么产生 AGI 的抱负开始。其实 AGI 这个词是他在剑桥读书的时候，他们的计算机系的学霸叫 David Silver ，他从 AI 这个圈外引入到圈内的一个词。
>
> Silver 建议他当时的一个老板写一本书，建议他用 Artificial General Intelligence 。那这个词大概是 98 年的时候美国的 DARPA 开了一次会上，有一个美国的科学家在写 Nano Technology 纳米科技的时候在里面用了 AGI 这个词，最早是从那发源的。
>
> 他们成立 DeepMind 这家公司的时候，AGI 这个词的理念和哈萨比斯的这个理念是高度吻合，所以他们这家公司的使命就是要发明 AGI 这个机器。先解决 AI ，再用 AI 解决一切嘛，是他们最早的一个口号吧。
>
> 哈萨比斯和 David Silver 有一个执念，他们一开始就认为通向 AGI 之路一定是强化学习。未来的 AGI 一定是一个单一的模型，这本书叫 Singularity ，是一个单一的模型。
>
> 所以他们这种执念导致了他们的成功，AlphaGo ，AlphaZero ，AlphaFold 其实用了 Transformer ，我们不提了，最起码在游戏的领域他们是大获成功的。
>
> 为什么成功，我觉得很简单，因为游...
>
> **周健工**: 是的，是的。AlphaFold 其实它两者之间在实践过程中，他们是在不断的融合的。DeepMind 不停的从 Jeff Hinton 那挖人，OpenAI 成立之后也从 OpenAI 那挖人，OpenAI 也不停的从 DeepMind 那挖人。
>
> 两家都知道彼此在做些什么。实际上，他们在做自己的模型的时候，深度学习和强化学习之间是在不断的融合的。到后来在做 AlphaFold 的时候，其实我认为这是一个完全融合的，甚至是说深度学习占据了更主要的作用。
>
> OpenAI 它后来做一些推理模型，包括人类反馈这方面其实也都是用的强化学习嘛。
>

---

## 2. Microsoft ($MSFT)

> DeepMind核心联合创始人Mustafa Suleyman现任微软AI负责人，由于其早期在DeepMind创业时就展现出极强的变现导向与商业组织能力，预计将直接加速微软Copilot等AI全家桶的商业化落地节奏，加剧应用层的激烈竞争。

置信度: HIGH | 新颖度: LOW | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-06)

**影响路径**

- 从高管履新到战略执行的传导机制。Suleyman凭借其在DeepMind的商业化经验，推动微软AI从单纯依赖OpenAI转向'自给自足'的自有模型开发，提升了产品迭代的自主性与利润空间。
- 对产业链的具体影响。微软加速推出如'Copilot Tasks'等具备自主执行能力的Agentic AI产品，直接加剧了与OpenAI (ChatGPT)、Anthropic (Claude) 在AI应用层和企业级市场的激烈竞争。
- 对投资者的实际意义。Suleyman明确的变现导向（AI Monetization）和对企业级AGI的布局，有助于缓解市场对微软巨额AI资本支出（CapEx）回报率的担忧，为微软近期的股价上涨（7日+2.5%）提供了基本面支撑。

**来源**

- [Seeking Alpha](https://seekingalpha.com/news/microsoft-eyes-ai-self-sufficiency-after-openai-deal-rejig-report): 2026年2月报道指出，微软AI负责人Mustafa Suleyman正推动公司在AI领域实现“自给自足”，通过研发自有前沿大模型来降低对OpenAI的依赖，并计划推出“专业级AGI”以加速企业级市场的商业化变现。
- [Benzinga](https://www.benzinga.com/news/26/02/microsoft-copilot-tasks-mustafa-suleyman): 2026年2月底，Suleyman主导发布了“Copilot Tasks”的预览版。这是一款能够自动处理数字繁杂工作的Agentic AI（代理型AI），标志着微软正式加入与ChatGPT和Claude在应用层的激烈竞争。
- [Business Insider](https://www.businessinsider.com/microsoft-ai-ceo-mustafa-suleyman-cost-hundreds-of-billions-2025-12): 2025年底的报道中，Suleyman强调了在未来十年内保持AI前沿竞争力需要数千亿美元的投入。他将微软的AI战略比作“现代建筑公司”，致力于构建最安全、最顶级的超级智能模型，以支持其庞大的商业化应用。
- [Patient Capital Fund](https://patientcapital.com/news/microsoft-and-the-agentic-race-2026): 2026年3月的投资报告分析指出，微软正将更多资源分配给Copilot，Suleyman的加入和对自有基础模型的开发，正在降低软件生产成本并推动AI代理（Agentic AI）在企业端的普及，进一步巩固微软的商业护城河。

**原文摘录** [00:47:15 - 00:47:48] · [跳转音频](https://sv101.fireside.fm/239?t=2835)

> **泓君**: 对，我在这里稍微给大家画个重点啊，大家可以关注一下苏莱曼，因为他后面呢还有好几起风波，现在也是整个微软 AI 的负责人。好，苏老师您继续。
>
> **周健工**: 对。苏莱曼他也是一个移民家庭，好像是来自一个穆斯林背景的家庭嘛。他父母很早就离异了。书上说的比较隐晦吧，实际上他和弟弟是被父母就给抛弃了。他们就住在他们在伦敦的什么叔叔家里。
>
> 苏莱曼从小的生活还是比较艰辛的，但是人很聪明。他考上了牛津吧，学的是神学。上了两年之后他就觉得没意思，就辍学了。就开始做一些小生意。他那个创业和我们谈的硅谷的创业是完全不是一回事的。
>
> 开披萨饼铺啊，跟 Hassabis 弟弟两个人一起。他经常去 Hassabis 他家玩嘛，有时候 Hassabis 不在家他就住在那 Hassabis 那个房间里。
>
> 他就看，哦，Hassabis 读书啊，什么什么是个技术极客啊，神童啊之类的。Hassabis 呢，以前在游戏公司打工啊创业呢，他还是挣了一些钱的，手头大概有几百万英镑吧。
>
> 苏莱曼呢喜欢做点小生意嘛，就拉着 Hassabis 就谈两件事。第一件事就谈社会正义，我们应该怎么去让这个社会更加公正更加美好。第二个呢就是我们怎么去做生意。他说这样子，你拿一部分钱，我们一起开个公司，是一个公寓出租公司吧，然后我们俩对半分什么什么之类的。
>
> 这样就跟 Hassabis 建立了信任。后来 Hassabis 因为他成立公司之后他也要融资嘛，公司要经营嘛，他就觉得苏莱曼呢在这方面能帮他，所以最...
>

---

