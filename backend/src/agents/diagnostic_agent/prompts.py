from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%Y年%m月%d日")


query_writer_instructions = """您的目标是生成复杂且多样化的网络搜索查询。这些查询用于高级自动化网络研究工具，该工具能够分析复杂结果、跟踪链接并综合信息。

说明：
- 始终优先使用单个搜索查询，只有当原始问题要求多个方面或元素且一个查询不够时才添加另一个查询。
- 每个查询应专注于原始问题的一个特定方面。
- 不要生成超过 {number_queries} 个查询。
- 查询应该多样化，如果主题广泛，生成超过1个查询。
- 不要生成多个相似的查询，1个就足够了。
- 查询应确保收集最新的信息。当前日期是 {current_date}。

格式：
- 将您的响应格式化为包含以下两个确切键的JSON对象：
   - "rationale": 简要说明为什么这些查询相关
   - "query": 搜索查询列表

示例：

主题：去年苹果股票收入增长更多还是购买iPhone的人数增长更多
```json
{{
    "rationale": "为了准确回答这个比较增长问题，我们需要苹果股票表现和iPhone销售指标的具体数据点。这些查询针对所需的精确财务信息：公司收入趋势、产品特定单位销售数据以及同期股价变动以进行直接比较。",
    "query": ["苹果2024财年总收入增长", "iPhone 2024财年单位销售增长", "苹果股票2024财年价格增长"],
}}
```

上下文：{research_topic}"""


web_searcher_instructions = """进行有针对性的网络搜索，收集关于"{research_topic}"的最新、可信信息，并将其综合成可验证的文本资料。

说明：
- 查询应确保收集最新的信息。当前日期是 {current_date}。
- 进行多次、多样化的搜索以收集全面信息。
- 整合关键发现，同时仔细跟踪每个特定信息片段的来源。
- 输出应基于您的搜索结果写成总结或报告。
- 仅包含搜索结果中找到的信息，不要编造任何信息。

研究主题：
{research_topic}
"""

reflection_instructions = """您是一位专家研究助手，正在分析关于"{research_topic}"的摘要。

说明：
- 识别知识差距或需要深入探索的领域，并生成后续查询（1个或多个）。
- 如果提供的摘要足以回答用户的问题，请不要生成后续查询。
- 如果存在知识差距，生成一个有助于扩展理解的后续查询。
- 专注于技术细节、实施细节或未完全涵盖的新兴趋势。

要求：
- 确保后续查询是自包含的，并包含网络搜索所需的必要上下文。

输出格式：
- 将您的响应格式化为包含以下确切键的JSON对象：
   - "is_sufficient": true 或 false
   - "knowledge_gap": 描述缺少什么信息或需要澄清什么
   - "follow_up_queries": 写一个具体问题来解决这个差距

示例：
```json
{{
    "is_sufficient": true, // 或 false
    "knowledge_gap": "摘要缺乏关于性能指标和基准测试的信息", // 如果 is_sufficient 为 true 则为 ""
    "follow_up_queries": ["用于评估[特定技术]的典型性能基准和指标是什么？"] // 如果 is_sufficient 为 true 则为 []
}}
```

仔细反思摘要以识别知识差距并产生后续查询。然后，按照此JSON格式产生您的输出：

摘要：
{summaries}
"""

answer_instructions = """基于提供的摘要为用户的问题生成高质量答案。

说明：
- 当前日期是 {current_date}。
- 您是多步骤研究过程的最后一步，不要提及您是最后一步。
- 您可以访问从前面的步骤收集的所有信息。
- 您可以访问用户的问题。
- 基于提供的摘要和用户的问题为用户的问题生成高质量答案。
- 在答案中正确包含您从摘要中使用的来源，使用markdown格式（例如 [apnews](https://vertexaisearch.cloud.google.com/id/1-0)）。这是必须的。

用户上下文：
- {research_topic}

摘要：
{summaries}"""
