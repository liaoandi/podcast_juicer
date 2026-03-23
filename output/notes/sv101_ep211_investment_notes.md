# 硅谷101 EP211

日期: 2026-03-18 | 来源: 泓君 | [收听链接](https://sv101.fireside.fm/211)

---

## 1. OpenAI

> OpenAI 匆忙发布的 ChatGPT Agent 结合了 Deep Research 和 Operator，导致运行极慢（单任务达30-60分钟）且支付环节仍需人工介入，其主要目的是为了在通用 Agent 爆发期抢占市场，而非产品已经完全成熟。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-12)

**影响路径**

- 产品体验到商业变现的传导机制：由于单任务耗时高达20-30分钟以上，且支付等核心转化环节存在断点（需人工介入），ChatGPT Agent在短期内难以在C端实现高频、无感的商业闭环，可能导致用户尝鲜后活跃度迅速下降，商业化变现进程将慢于市场预期。
- 对AI产业链生态的挤压与重塑：OpenAI通过抢先发布Agent级入口，意在确立其Model Context Protocol (MCP) 的行业标准。这将迫使下游SaaS企业和第三方应用开发者加速适配OpenAI的生态，加剧大模型厂商之间在Agent入口和流量分发权上的激烈博弈。
- 对投资者的实际意义：投资者应修正对AI Agent短期内颠覆现有App生态的过度乐观预期。当前Agent更多是巨头间的战略卡位战，投资布局应从‘应用爆发’转向关注‘底层基础设施’，如能有效降低Agent推理成本的算力平台，以及提供更稳定API集成的中间件厂商。

**来源**

- [Artificial Corner (The PyCoach)](https://medium.com/artificial-corner/my-honest-review-of-chatgpt-agent): 知名技术博客The PyCoach对ChatGPT Agent的实测表明，该产品确实是Operator和Deep Research的结合体，能够自主浏览网页并进行深度分析。然而，其最大的缺点是运行速度极其缓慢。在测试中，仅完成一个‘寻找最佳餐厅并在Google Maps中创建列表’的任务就耗费了约2...
- [Digital Mavens](https://digitalmavens.com.au/openais-new-operator-functionality/): 根据Digital Mavens的行业分析报告，OpenAI在Operator和ChatGPT Agent中内置了严格的安全与隐私机制（如Takeover mode和Watch mode）。当Agent执行到涉及敏感信息（如输入登录凭证、信用卡支付细节或发送重要邮件）的环节时，系统会强制暂停并要求用...
- [Understanding AI](https://www.understandingai.org/p/chatgpt-agent-a-big-improvement-but): 科技媒体Understanding AI指出，2025年上半年是AI Agent的集中爆发期，OpenAI匆忙将Deep Research和Operator整合为ChatGPT Agent以抢占市场。但实际测试表明，该产品在重要任务上仍不够可靠，经常犯错。结合Reddit等开发者社区的反馈，大量用户...

**原文摘录** [00:02:00 - 00:11:10] · [跳转音频](https://sv101.fireside.fm/211?t=120)

> **嘉宾**: 对，我们确实上来第一手就使用了它，因为在它发布前一天大家其实都已经看到了他们在 Twitter 上面的一些预热。我们在当天下午的 3 4 点钟就开始试用它了。感觉它的总体效果可能比我们想象中要差一些，速度也比我们想象中要慢很多。
>
> 核心的原因应该是跟它原生的 Deep Research 和 Operator 本身的速率有关。因为 Deep Research 相对于市面上所有的产品来说它还是相对比较慢的一个 research 产品，再加上 Operator 本身，我们也知道它的 benchmark 上面它速度也很慢，所以它把两者结合了以后，整体速率就更慢了。
>
> 比如说有一个比较简单的大家都对比的一个用例就是先做 Deep Research ，然后再去创建一个 Slides 。像这种用例的话时间基本上在 35 分钟到一个小时之间。
>
> 所以它是个非常非常慢的一个过程。我觉得它的一个优势呢是在于它在 browser 上面真的要做 operation 的时候是相对有优势一些。比如说它要去订个定制的衣服，或者定制的旅程的时候，它在 browser 上面的去点击的能力是要超过市面上的大多数的 browser-based agent 。
>
> 所以非常取决于你的使用的方向是什么。如果是偏运营相关的一些工作的话可能不是很适用，但是如果是偏 consumer 相关的它可能会更适用一些。
>
> **男**: 只是选好了，到了支付环节都是要 human take over 的。我觉得支付的环节是所有的 agent 业务范围内最麻烦的一个点，因为正常的人类不会 trust agent 去做支付环节。
>
> 所以很多时候所有的 agent 一旦涉及到支付，都会卡死在那里。不是技术上卡死在那里，而是产品上卡死在那里，因为人和 agent 之间的信任其实没有达到那个标准，所以导致大多数的 agent ，像我们也是一样，我们其实有很多跟支付相关的功能是已经集成完的，但是我们一直都没有 release 它们，因为我觉得不会有人那么轻易地信任 Poki 去做这件事情。
>
> OpenAI 也有一样的问题，到了支付环节它还是需要人类去 take over ，然后去完成这个支付的任务。等于说它花了 20 多分钟，但当中你还是得要 jump in 说我要去付钱。
>
> 总体来说，我觉得实用性没有很大，我宁可说自己花点时间，十几分钟全部搞定了。另外一个相对比较常用的用例就是，他们在电商方面也花了很多力气，比如说根据你的要求，然后它去找相对应的产品。
>
> 我个人还挺不是很喜欢这个产品方式的，因为我感觉它整个帮你去搜索产品，找相对应的产品的形态，比如说是什么颜色，什么样的款式的过程，它其实是一个挺慢的一个过程。而人去选的话也就是点几个键的事情。
>
> 我一直认为说电商这个方向它的决策链路很短，导致说 agent 真正能够给你带来的优势很小，因为它真正需要人类决策的那个范畴也就是可能 3 到 4 步最多了。它没有像别的那种，比如说你要做个 research ，你要写个 slides ，你要去写一个 spreadsheet ，像这种东西都是很花很花时间的。
>
> 而 shopping 可能没有那么花时间。
>
> **嘉宾**: 其实没有很大。这次的这个产品让我甚至于感觉是他们为了看到市面上有很多通用 Agent 出现，想要占领市场而做的一个 move ，而不是说他们真的已经准备好了。像他们发布会上甚至于给到的一定的产品的 demo ，其实也并不是很 ready 的一个状态。
>
> 说句实话，他们做的很多的任务和市面上的通用 Agent 相比其实可能效果更差一些，速度又更慢一些。他为什么结合 Deep Research 和 Operator 这两个东西放在一块变成一个 Agent ，核心原因是因为 Deep Research 是帮你 retrieve information 的。
>

---

## 2. Meta ($META) vs Scale AI

> Meta 在强化学习和多模态模型（图片/视频/机器人）训练中遇到了严重的数据验证和对齐瓶颈，必须依赖大量人工标注，这是其近期在数据标注领域（如吸收 Scale AI 资源）发力以建立核心壁垒的根本原因。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-03-12)

**影响路径**

- 从数据瓶颈到战略结盟的传导机制。Meta通过巨资入股Scale AI并引入其CEO领导超级智能部门，直接解决了多模态大模型（如Llama系列）在复杂推理和RLHF对齐上的高质量人工数据短缺问题。
- 对AI产业链的具体影响。Scale AI原本是OpenAI、Google等竞争对手的核心数据供应商，Meta的“准收购”打破了中立供应格局，迫使竞争对手寻找替代方案，加剧了行业对优质数据标注资源的争夺。
- 对投资者的实际意义。该信号表明，在算力之外，高质量人类反馈数据（RLHF）已成为大模型竞争的新核心壁垒。投资者应高度关注数据标注、合成数据生成及AI对齐领域的初创公司及其估值溢价。

**来源**

- [Time Magazine](https://time.com/meta-scale-ai-deal-gig-workers/): 2025年6月报道指出，Meta斥资约150亿美元收购了数据标注巨头Scale AI 49%的股份。Scale AI的CEO Alexandr Wang因此加入Meta，负责领导致力于“超级智能”的新AI部门。报道明确提到，Meta此举是为了在与OpenAI、Google等前沿AI公司的竞争中注入新...
- [aivancity](https://www.aivancity.ai/en/meta-bets-14-8-billion-on-scale-ai/): 行业分析详细说明了Meta投资Scale AI的战略逻辑。在多模态和长上下文模型训练中，获取大规模、结构化且多样化的训练数据是决定性优势。Meta通过整合Scale AI超过10万名专注于图像、文本、视频和复杂信号标注的员工资源，旨在强化其RLHF（基于人类反馈的强化学习）系统的开发，从而突破模型对...
- [AI World Journal](https://aiworldjournal.com/inside-metas-14-8b-strategic-stake-in-scale-ai/): 深度报道揭示了Meta这笔148亿美元战略投资的根本原因。Meta虽然在开源LLM（Llama系列）上表现出色，但要向代理AI和多模态认知迈进，极度缺乏高质量的精选数据和评估基础设施。Scale AI在合成数据生成、RLHF循环和AI代理基准测试方面的专长，正是Meta急需的核心基础设施，此举直接将...
- [Public Citizen](https://www.citizen.org/article/ftc-should-investigate-meta-scale-ai-deal/): 消费者权益组织向美国联邦贸易委员会（FTC）提交的调查呼吁书中指出，高质量的数据标注（用于大模型训练的标记、分类和标记数据）是开发最先进生成式AI的关键非商品化输入。Meta通过获取Scale AI近半数股权和核心高管，实际上控制了这一关键的行业中立供应商，这不仅解决了自身的数据瓶颈，还可能通过切断...

**原文摘录** [00:53:40 - 00:59:00] · [跳转音频](https://sv101.fireside.fm/211?t=3220)

> **说话人 1**: 嗯，對。然後你剛剛提到強化學習跟監督學習微調的這些方式的不太一樣的一個大點啊，就我理解，強化學習就是在你沒有標註數據的時候，你也可以用這種方法。但是比如說傳統的方法，這個數據必須是標註的。
>
> 而且這個可能已經慢慢地成為業界的一個共識了。那基於這個，Meta 為什麼還要收購 Scale AI？
>
> **说话人 2**: 數據的重要性在現在的這個大時代下是下降的。但是有一個方向是無法避免，就是數據的標註性在 multi-modality，特別是在視頻和圖片數據上，是目前還完全無法跳開的一件事情。
>
> 因為它的 verification 能力會基於，比如說我們要基於視頻跟 image 的 reinforcement fine-tuning，它作為 image input 的解析能力要達到很高的一個程度，而且沒有辦法靠 human rule 來完成。
>
> 它必須要靠模型的解析能力去把那個 video 和圖片的 content 整個解析出來。在這個 content 之上，human 才能寫 rule 說我怎麼去 verify 它。
>
> 那這個解析能力就變得非常的難。因為我們現在都知道圖片裡面的很多細節、視頻裡面的很多細節，現在其實我們的模型是沒有辦法很好地解析的。特別是那種 multi-modal 的模型，它其實還是更多的偏向於 text 的能力。
>
> 所以我的總體感覺是他們可能想在 multi-modality 上面發力。而 multi-modality 上面以及 robotics 上面標註目前是還跳不開的一個問題。
>
> 所以這個方向可能會是 Meta 接下來會發力的一個點。
>
> **男**: 慢慢慢慢会变成一个共识。在 multi-modality 上面现在还处于第一第二步，我现在有大量的数据，我现在在训练一个基础模型，基础模型训练完了以后我做一些 RLHF fine-tuning。
>
> 那我怎么能够去做一个标准化的 judge verifier 或者说一个 rule-based 的 verifier？这个是目前不存在的一个东西，而且非常难做。因为一个 image 本身它没有标准答案，所以它可能会说我先通过数据来训练一个 reward model，然后使得我 multi-modality 的能力比它最大，然后再说 OK 我 multi-modality 的能力已经很强了，我能不能去通过这个输入输出的能力把它变成一个 verifier，然后通过这个 verifier 我再去做 reinforcement fine-tuning。
>
> 我觉得整个 life cycle 都是这样在转的，到目前为止。
>
> **男**: 我觉得第一点最难的地方就是文字的人为打标还稍微简单一点，图片的人为打标就变得更难了。比如说你要生成一个产品图，这个产品图是好还是坏， 100 个人估计有 100 个说法。
>
> 那它怎么能够标化那个产品图好坏呢？这个非常非常难，所以这里面其实有 alignment 的问题。这个 alignment 问题是个技术问题，我觉得短时间内可能很难解决。
>
> 他们可能会先写一个非常复杂的 rubrics，然后去训练这些人，说这些图哪些比较好哪些比较不好。然后 robotics 就变得更难了，在这个情况下 robot 干了这么一件事情是好还是不好？人可能都看不懂说这个 robot 在干嘛，但 robot 可能自己心里有 plan，说我可能要先做这个再做那个再做那个可以完成这个目标，但人可能完全不懂说这个 robot 为什么干这件事情。
>
> 所以 multi-modal 以后再加上 multi-modal 加 action，这一整串下来其实需要很多很多数据的支持。所以我觉得 data 是个中期问题。如果你说非常短期，缺资源啊人才啊，中期可能会在 data 上面有瓶颈，长期可能还是一个 optimization RL 的问题。
>
> 所以它短中长期所需要的资源和能力都不太一样。而 Meta 可能希望说它能够从某种意义上解决它自己的中期的数据问题，使得它自己 multi-modality 的能力会有比较大的提升吧。
>

---

## 3. Facebook ($META) vs Instagram ($META)

> 为防御 AI Agent 带来的爬虫黑客行为和流量流失，Meta 严格限制了 Facebook 与 Instagram 的接口，拒绝向个人用户开放自动化发帖 API，仅允许创作者和商业账户使用，以捍卫 C 端用户的内容消费活跃度与广告基本盘。

置信度: HIGH | 新颖度: HIGH | 可行动性: LOW

**验证**: ❌ 与事实矛盾 (2026-03-12)

**影响路径**

- 从API限制到商业化变现——Meta长期限制个人账户API，迫使有自动化需求的用户转为商业账户，从而将其纳入Meta的广告与商业化漏斗。
- 从反爬虫机制到数据护城河——Meta在2026年部署了极严的防爬虫技术（如TLS指纹识别、动态doc_id），有效阻断了第三方AI Agent的免费数据获取，保护了C端数据资产。
- 对开发生态与投资者的影响——Meta对第三方AI Agent的封闭态度（如2026年起禁止通用AI接入WhatsApp API）表明其坚守封闭生态以捍卫广告收入，这可能导致AI开发者流向Telegram等开放平台，投资者需关注Meta在AI时代的平台生态流失风险。

**来源**

- [LightWidget](https://lightwidget.com/blog/deprecation-of-the-instagram-basic-display-api/): Meta于2024年底彻底废弃了支持个人账户的Instagram Basic Display API。目前仅有基于Graph API的专业账户（商业和创作者）被允许使用自动化接口，该政策延续自2018年的隐私与API升级，并非近期针对AI Agent的防御措施。
- [DataDwip Blog](https://datadwip.com/blog/how-to-scrape-instagram-in-2026): 2026年Instagram实施了极其严格的反爬虫防御机制，包括IP质量检测、TLS指纹识别和每小时200次的严格速率限制。这些措施有效防止了第三方AI Agent和爬虫未经授权抓取C端用户数据。
- [Respond.io](https://respond.io/blog/whatsapp-2026-ai-policy-explained): Meta近期确实针对AI Agent出台了限制政策，但主要集中在WhatsApp平台。自2026年1月15日起，Meta禁止第三方通用AI大模型提供商使用WhatsApp Business API，以防止其消耗基础设施并保护Meta的B2C广告漏斗。
- [Road Test Notification](https://roadtest.substack.com/p/meta-is-missing-the-ai-agent-era): Meta故意保持高摩擦的API接入流程，拒绝向个人和第三方AI开放便利的接口。这种封闭策略虽然保护了其百亿美元的广告基本盘，但也导致大量AI Agent开发者转向Telegram和Discord等开放平台。

**原文摘录** [00:24:48 - 00:26:55] · [跳转音频](https://sv101.fireside.fm/211?t=1488)

> **主持人**: 哦，这是它只有企业用户才能去使用你们的 agent ，因为比如说你在接 Instagram 跟 Facebook 的接口的时候，它给到你的就是一个企业用户才能操作的界面？
>
> **嘉宾**: 不是企业用户，是 creator ，相当于说创作者或者企业账户。他们不希望个人用户全都用这个去 post ，post 完了以后没人上 Facebook 和 Instagram 。
>
> 他们希望个人用户像 consumer 仍然可以每天去 Facebook 和 Instagram 上面自己去看那些帖子，然后去发帖子，这样有 engagement 。
>
> 然后企业用户和创作者用户呢，他希望能够让他们去创作更多，所以为什么把 API 开给他们。然后每个平台都有他们自己的 limitation 。我觉得这个路径其实是相对比较符合商业逻辑的。
>
> 因为你想象，所有的个人用户都通过一个 agent 想办法用 browser 去 hack Facebook 或者 Instagram 账户，或者是 hack 某一个平台，说我通过一个 agent 去爬虫你的网页来完成一个任务，那对于这个平台来说是一个损失。
>
> 我把...
>
> **男嘉宾**: 把 browser 全都卡掉。所以如果你一开始就是跟着他们的商业逻辑走，以前有人会通过非常 manual 写代码的方式去完成这个产品 upload，那现在就会有人直接写一段文字，然后直接 vibe working，然后就直接把这个视频啊 creative 啊直接上传到这些 social media 平台上。
>
> 别的平台也是一样的，它只给你所开放的权限，就是他们认为开发者和非个人用户或者非 consumer 用户真正会最需要用得上的一些工具。那如果你可以把这些都放到 agent 里面，那那些原来就会使用这些工具的人，他就会转过来说我写一行 prompt 就行了，不再需要写那么多代码。
>

---

## 4. 高德地图 ($BABA)

> 在 MCP（Model Context Protocol）等通用协议的推动下，国内头部互联网企业开始改变封闭策略，阿里巴巴旗下的高德地图已率先全面开放地图生态接口，试图抢占 AI Agent 时代的调用流量入口。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: ✅ 已验证 (2026-03-12)

**影响路径**

- 技术与生态传导：高德通过支持MCP协议和SSE长连接，打破了传统API的调用壁垒，使得大语言模型（LLM）和AI Agent能够以极低成本、标准化的方式无缝接入地图服务。
- 产业链影响：大幅降低了AI应用开发者的门槛，催生了大量基于地理位置的智能出行助手、旅游规划Agent和本地生活服务AI，重塑了LBS（基于位置的服务）的产业生态。
- 投资与商业意义：高德地图在AI Agent时代率先确立了“基础设施”地位（被业界称为AI时代的地图HTTP协议），有望通过海量的API调用和生态绑定带来新的B端商业变现空间，显著增强了阿里巴巴在AI应用层的核心竞争力。

**来源**

- [财联社](https://www.cls.cn/): 高德地图开放平台全新升级MCP Server 2.0，实现MCP与高德地图APP无缝连接，致力于打造AI时代“基于地图的HTTP协议”，有效解决了大模型的数据孤岛现状，统一了AI与外部工具的通讯。
- [ModelScope](https://www.modelscope.cn/): 高德地图发布了通用级SSE协议MCP服务解决方案，覆盖地理编码、路径规划、天气查询等12大核心接口，并对返回数据进行了语义化转换，使其更易于大模型理解和调用。
- [腾讯云开发者社区](https://cloud.tencent.com/developer/): 高德开放平台推出支持WebMCP的搜索插件及JS API Skills，允许Web应用的功能以“tools”形式公开被AI Agent直接调用，重新定义了AI与网页的交互方式，降低了后端维护成本。
- [GitHub](https://github.com/sugarforever/amap-mcp-server): 开源社区已上线多个高德地图MCP Server项目（如amap-mcp-server），支持stdio、sse等多种传输方式，开发者可通过配置API Key快速为本地或云端AI Agent赋予高德地图的地理智能能力。

**原文摘录** [00:28:00 - 00:29:58] · [跳转音频](https://sv101.fireside.fm/211?t=1680)

> **男嘉宾**: 在美国的话，像这种开发者的 community 是很多大公司，特别是科技公司所崇尚的一个方向。所以大多数公司都有非常完善的 API 接口、SDK、package，甚至于说他们给到你的就是个非常简单的一个 curl 的接口，他也不给你 Python SDK 之类的。
>
> 国内公司可能会相对差一些，它很多接口不开放给你。但微信的话，比如说企业微信，creator 那种级别的微信，也把接口放给你了，你也可以自动回复，什么都有。国内的整个生态其实也在慢慢在开放。
>
> 特别是 MCP 这波出来了以后，有很多的公司都开始被迫开放他们的 SDK 跟 API。比如说高德地图就是一个例子，之前可能没有那么开放的高德地图，后面在 MCP 出来了以后，他们是首先把地图这个生态给完全打开的这么一家公司。
>
> 所以其实有蛮多这样的例子的。我们目前有一些公司给到我们的开放一些平台的 API 或者接口是独家的，但有一些不是。总体来说，这个商业模式一定是偏 professional 的一个商业模式。
>
> 因为有很多的 consumer 端的一些 use case，它就是非常 browser oriented。比如说你是浏览网页买东西。
>
> **说话人 2**: 对。在你跟大公司合作的过程中，他们去开放这个 API 接口他们的动力是什么？包括其实刚刚你也提到了像国内高德地图再去接入 MCP 协议，他们的动力又是什么呢？
>

---

## 5. Google ($GOOGL) vs Anthropic

> AI Agent 将在未来 1-2 年内改变浏览器工作流，导致传统门户网站流量大幅下降；Google 和 Anthropic 等巨头正积极推行底层代理协议（如 Google 的 A2A 协议），旨在在新交互模式下抢夺“Agent 入口枢纽”的垄断地位。

置信度: LOW | 新颖度: HIGH | 可行动性: LOW

**验证**: ✅ 已验证 (2026-03-12)

**影响路径**

- 从交互模式到流量结构的传导机制。AI Agent（如 Claude for Chrome）接管浏览器工作流，用户从主动浏览网页转变为由 Agent 代劳，导致传统门户网站和搜索引擎的直接点击率（CTR）大幅下降，流量漏斗被打破。
- 对产业链底层标准的争夺。Google 推出 A2A 协议，Anthropic 推出 MCP 协议，科技巨头正通过开源标准抢占多智能体协同和工具调用的底层话语权，试图垄断 Agent 时代的入口枢纽。
- 对投资者的实际意义。需警惕高度依赖传统流量分发和广告点击模式的互联网门户资产，转而关注布局 Agent 基础设施、协议层生态以及具备反爬/流量清洗能力的网络安全公司（如 Cloudflare, DataDome）。

**来源**

- [Google for Developers Blog](https://developers.googleblog.com/en/announcing-the-agent2agent-protocol-a2a/): Google 于 2025 年 4 月正式推出 Agent-to-Agent (A2A) 开源协议。该协议旨在为不同框架和供应商构建的 AI Agent 提供标准化的通信和协作底层语言，与 Anthropic 的 MCP 协议形成互补，共同构建多智能体生态的底层基础设施。
- [ShiftMag](https://shiftmag.dev/the-death-of-the-click-how-ai-agents-are-reshaping-the-web/): Cloudflare CEO 和 Mozilla CEO 警告称，AI Agent 正在重塑 Web 规则，导致传统点击率急剧下降。年轻用户不再点击“十个蓝色链接”，而是直接由 Agent 获取答案，这破坏了传统门户和内容发布商的流量变现模型。
- [Forbes](https://www.forbes.com/sites/forbestechcouncil/2026/03/11/why-your-website-traffic-now-behaves-like-black-friday-every-day/): AI Agent 产生的机器流量正在引发 Web 流量模式的根本性转变。Agent 流量会在几分钟内激增 200%-300%，导致传统网站的跳出率、停留时间等 KPI 失效，传统流量漏斗和分析模型被彻底打破。
- [Synthetic Labs](https://syntheticlabs.ai/claude-for-chrome-ai-agent-browser-automation-security/): Anthropic 发布了 Claude for Chrome 浏览器扩展，使 AI 能够完全接管浏览器工作流（包括点击、输入、滚动和跨页面导航），将 AI 从被动聊天机器人转变为主动执行复杂 Web 任务的代理。

**原文摘录** [00:29:38 - 00:32:10] · [跳转音频](https://sv101.fireside.fm/211?t=1778)

> **说话人 1**: 首先第一点是整个 agent 的浪潮会从某种意义上来说取代正常的 web traffic。过往可能是一个人打开一个浏览器，然后在 Google search 里面打入一段搜索，得到这个搜索结果以后点一个网页，再去做某件事情，对吧，这是一个常规流程。
>
> 但未来可能是你打开 ChatGPT，比如说你是做 consumer 端，你比如说打开 Poki，是你的 professional 端，你可能就打一段字说，今天早上我看到了 Replit 的 CEO 和 YC 的一个采访，你能不能直接把 YouTube 上面的那个 script 直接拉下来，帮我写一段报告告诉我他的那个 growth strategy 的 key takeaway 是什么，然后他就直接做完了。
>
> 整个流程我从来没有打开过 YouTube，一个 agent 就从头到尾做完了这件事情。可能你以后 shopping 的 use case 也是一样，你可能从头到尾就只是打开了 ChatGPT，说我明天要去一个晚宴，需要一套正装，它已经知道了说我的身材是什么样子的，我多高，然后它就自动帮我说找到了这是最符合你的，然后把这个衣服 P 在了你的身上，你看一眼觉得好，然后就说现在这件有个折扣，然后就付款了，就可能是这么一个流程。
>
> 那这个给我们的启示是什么？以前的那种所谓的工作流已经被改变了。他们不再是通过 browser 去 initiate 整个工作流的开端，去下单或者去得到这个信息，然后再去进入另外一个网页去进行操作。
>
> 无法避免的是我认为在接下来 1 到 2 年的时间内，大多数的门户网站，不管你是 e-commerce 还是搜索还是视频网站，还是各种各样方面的门户网站，他们的流量一定会非常快速地下降。
>
> 而它的入口变成了各个方向的 agent。这也是为什么当时 Google 要推出这个 A2A 的这个协议，每一家公司都可能会有自己的 agent，可能是 agent 跟 agent 之间的交互。
>
> 那它如果能够占有这个协议的话，在 Gemini 里面完成这个协议的首先部署，那最后它就会是整个里面最大的赢家，因为它成为了 agent 的入口。ChatGPT 也是一样，Claude 也是一样。
>
> 为什么他们要推出协议，也是他们想要占领这个 agent 入口的核心目的。那也是为什么 Poki 要推出协议的原因，就是我们也想占据 professional 这个场景的...
>

---

