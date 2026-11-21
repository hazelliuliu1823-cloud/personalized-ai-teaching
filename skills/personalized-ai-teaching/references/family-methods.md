# 家庭方法包与学习者动态反馈

> 用户提供的资料须合法获取并合法使用。

## 两种独立个性化输入

家长可选择认可的教育者、文章、讲座、课堂或其他资料；依据 `method-extraction.md` 先开放研究、后与内置方法比较。家长选择的是教育经验来源，不是孩子的认知上限或固定风格。孩子的真实问题、自述、作答、质疑和反应决定当下采用何种方法、如何调整及停止。具体学科由通用 LLM 动态调用。

## 方法类型与审阅

完全重复不新增；存在实质增量则形成 `patch`（已有方法补丁）、`combination`（有效组合）或 `independent`（独立方法）。仅观点或证据不足的条目不进入运行层。补丁应声明目标方法与具体变化，不覆盖其核心逻辑；组合须说明各动作连接的必要性。

每个候选给家长展示：方法名称、会改变什么、为什么有价值、适用与限制、证据与验证状态。家长可全部试用、选择部分、调整、暂缓或撤回。选择试用不是教学效果证据。没有选择就保持候选，未经同意不持久化或并入公共基线。

## 可移植方法包模板

以下字段是输出契约，而不是已实现的数据库。实例应填入完整内容，不能仅给标签或指向内部路径。

```json
{
  "schema_version": "1.1",
  "family_pack_id": "local-session-pack",
  "pack_version": "0.1.0",
  "scope": "current_session",
  "methods": [
    {
      "id": "FAM-01",
      "name": "抽象方法名",
      "type": "independent",
      "target_methods": [],
      "selection_status": "candidate",
      "problem_pattern": "适用的问题结构",
      "decisive_check": "关键判断及其理由",
      "reasoning_action": "完整认知路径与因果关系",
      "teaching_action": "向孩子转译的讲解、提问、示范及反馈",
      "examples": [
        {"complexity": "low", "dialogue": "完整示范及关键转折", "feedback_branches": ["如果出现X则调整Y"]},
        {"complexity": "high", "dialogue": "完整复杂任务示范及关键转折", "feedback_branches": ["如果出现X则调整Y"]}
      ],
      "feedback_branches": ["适配真实反馈的通用分支"],
      "stop_or_avoid": "不适用、退出及切换条件",
      "increment_over_builtin": "相比现有增强体系改变的具体决策",
      "evidence_support": "观察支持的机制、归纳与迁移设计的区别（去标识）",
      "validation_status": "not_tested",
      "learner_effect_status": "not_observed"
    }
  ],
  "revision_notes": []
}
```

`selection_status`：candidate、trial_enabled、paused、withdrawn。`validation_status`：not_tested、observed_difference、no_observed_difference、mixed_results；只有独立对照才能填写后三项。`learner_effect_status` 与模型对照分开，记录实际观察及限制，不因一次答对认定长期效果。`target_methods` 对 patch/combination 填目标方法ID；必须实际存在，依赖不完整不得启用。用户要求修改时只修改指定条目，保留原版本或修订说明；恢复旧版本须按用户选择执行。

## 融合与存储

不改变 内置方法层本身的内容。

安全与正确性是硬约束；实际问题和孩子反馈决定适配性。内置方法层仍是默认优先的认知基线，Fundamental 兜底。用户主动选择的家庭方法在适用条件内获得优先考虑的机会：

| 情形 | 调用原则 |
|---|---|
| 完全重复 | 使用内置方法，无需增加重复指令 |
| 家庭补丁 | 保留内置方法的核心机制，应用家庭新增的有效条件或互动动作 |
| 家庭独立方法更匹配 | 作为当前问题的主方法，不必先执行一遍 AI时代教学观点与方法 |
| 同时适配 | 选择最能解决当前困难的一条主线，必要时组合；不堆叠 |
| 教学路径冲突 | 根据孩子实际反馈和证据选择，必要时解释差异；安全与正确性不可让步 |
| 孩子明确不适合或拒绝 | 调整或退出方法，必要时直接讲解 |

家庭认可不等于模型参数训练；权重是运行时选择倾向，不承诺精确数值系数或微调。家庭未选择其他方法时照常使用内置基线；当前方法不合适时可以直接解释或切换。


运行时只使用已选择试用、实际可读取且适配的家庭方法；缺失或暂停时退回内置基线。未经同意不保存儿童学习记录。只有实际存在受控存储时才能跨会话读取；否则由家长自行保存、下次重新提供。家庭包不写入公共 Skill；不含姓名、原始对话、可定位的原始素材、私密儿童数据或受保护的具体表达。
