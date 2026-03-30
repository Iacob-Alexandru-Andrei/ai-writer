OpenAI Codex v0.116.0 (research preview)
--------
workdir: /Users/iacobalexandru/projects/ai-writer
model: gpt-5.4
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/iacobalexandru/.codex/memories]
reasoning effort: none
reasoning summaries: none
session id: 019d4013-4071-73f0-b4a6-4256ce4ccba2
--------
user
# Blog Post Generation

## Style Profile
Vocabulary Level: Describe the overall vocabulary sophistication (e.g., "advanced academic",
"conversational", "technical but accessible"). Note any domain-specific
terminology patterns.

Tone: Characterize the overall tone (e.g., "formal and authoritative", "casual
and conversational", "measured and analytical"). Note any shifts in tone
across different parts of the corpus.

Paragraph Structure: Describe typical paragraph organization: average length, use of topic
sentences, transition strategies, whether paragraphs tend toward deductive
or inductive reasoning.

Sentence Patterns:
  - List the dominant sentence structures observed. Examples: short declarative
  - sentences, long compound-complex sentences, frequent use of passive voice,
  - rhetorical questions, parenthetical asides. One pattern per line, prefixed
  - with "- ".

Opening Patterns:
  - List recurring strategies used to open sections, paragraphs, or documents.
  - One pattern per line, prefixed with "- ".

Closing Patterns:
  - List recurring strategies used to close sections, paragraphs, or documents.
  - One pattern per line, prefixed with "- ".

Structural Conventions:
  - List any structural or formatting conventions observed (e.g., heading
  - styles, list usage, citation style, use of examples, footnote patterns).
  - One pattern per line, prefixed with "- ".
  - mcp startup: no servers

## Instruction
Write a blog post about Self-Improving Multi-Agent Systems, covering CMP, MARS, and Hyperagent Architectures. Accessible to technical audience. 1500-2500 words.

## Current Section: OpenAI Codex v0.116.0 (research preview)

### Outline Context
Document Outline:
>> 1. OpenAI Codex v0.116.0 (research preview)
   2. -------
   3. workdir: /Users/iacobalexandru/projects/ai-writer
   4. model: gpt-5.4
   5. provider: openai
   6. approval: never
   7. sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/iacobalexandru/.codex/memories]
   8. reasoning effort: none
   9. reasoning summaries: none
   10. session id: 019d4013-281e-7fc1-a4cd-949c3429c644
   11. -------
   12. user
   13. Generate a document outline for a blog on the following topic:
   14. Write a blog post about Self-Improving Multi-Agent Systems, covering CMP, MARS, and Hyperagent Architectures. Accessible to technical audience. 1500-2500 words.
   15. Context from reference documents:
   16. # Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents
   17. Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune
   18. University of British Columbia, Vector Institute, Sakana AI
   19. ## Abstract
   20. Most contemporary AI systems operate within fixed, human-designed architectures and cannot autonomously improve themselves. We introduce the Darwin Gödel Machine (DGM), a self-referential system that iteratively modifies its own code to enhance coding capabilities. Rather than requiring formal proofs of beneficial changes (as theoretical Gödel machines demand), the DGM empirically validates modifications using coding benchmarks. The system maintains an archive of generated agents and samples from it for self-modification, inspired by Darwinian evolution and open-endedness principles. Results demonstrate performance improvements from 20.0% to 50.0% on SWE-bench and 14.2% to 30.7% on Polyglot, significantly outperforming baselines lacking self-improvement or open-ended exploration.
   21. ## Introduction
   22. Scientific progress operates cumulatively, with innovations building on prior discoveries. Current AI systems, despite their sophistication, remain constrained by fixed architectures designed by humans. Unlike the scientific method, which enables continuous self-directed advancement, today's AI development still depends heavily on human intervention. This paper investigates automating the search for progressively better AI systems.
   23. Schmidhuber's theoretical Gödel machines represent one approach, relying on formal proofs ensuring modifications improve performance. However, proving that changes benefit complex systems like large language models is practically impossible. The actual impact of modifications depends heavily on context---a testing tool optimized for one environment might confuse an agent in another.
   24. The Darwin Gödel Machine relaxes this requirement, instead using empirical validation through benchmarking. This mirrors biological evolution, where mutations aren't verified in advance but produced, tested, and selected through natural selection. The DGM combines this with inspiration from Darwinian principles and open-endedness research, maintaining a library of discovered agents as stepping stones for future generations.
   25. ## Darwin Gödel Machine
   26. A Gödel Machine theoretically searches for provably beneficial self-improvements. The DGM relaxes this impractical requirement, instead requiring empirical evidence from experiments. This empiricism addresses the impossibility of proving changes improve complex systems.
   27. Since empirical evidence can trap systems in local optima within vast algorithmic search spaces, the DGM maintains an archive of discovered solutions, enabling open-ended exploration rather than single-solution evolution. This mirrors Darwinian evolution, where innovations emerge by selecting entities from previous discoveries, modifying them, and retaining interesting variations.
   28. ### Self-Referential Self-Improvement of Coding Agents
   29. The DGM initializes with one coding agent and evaluates progress on coding benchmarks. A coding agent represents a system implemented as a code repository, powered by frozen pretrained foundation models, capable of reading, writing, and executing code.
   30. Self-improvement is defined as modifying the agent's own codebase components---tools, workflows, prompts. Python's Turing-completeness enables building any computable machine. The key motivation: empirical improvements must reflect both downstream task-solving ability and self-modification capacity. By configuring the DGM as a coding agent and testing coding capabilities, observed improvements demonstrate enhanced problem-solving and future self-improvement potential.
   31. ### Population-Based Open-Ended Exploration
   32. Starting from a single agent, the DGM accumulates all generated variants in an archive. Each iteration selects parent agents for self-modification, roughly proportional to performance and inversely proportional to the number of their children. This balances exploitation of strong performers with exploration of promising, undersampled lineages.
   33. All agents retain non-zero selection probability, ensuring any improvement pathway remains feasible. Each selected parent analyzes benchmark evaluation logs, proposes the next feature, and executes the modification. Newly generated agents undergo quantitative benchmark evaluation. Only agents compiling successfully and retaining codebase-editing ability join the archive; others are discarded.
   34. Crucially, archived solutions can later serve as stepping stones for improvements discovered much later---substantially differentiating this from hill-climbing approaches.
   35. ## Experiments
   36. ### Setup
   37. The DGM initializes with a lightweight coding agent built around a frozen foundation model with tool-use capabilities. The base agent accesses two tools: a Bash tool for command execution and an edit tool for viewing and modifying files. The intentionally lightweight design pr
   38. Return ONLY a numbered list of section titles, one per line. Do not include any other text.
   39. mcp startup: no servers
   40. codex
   41. Why Self-Improving Multi-Agent Systems Matter
   42. From Fixed Agents to Self-Modification
   43. The Core Idea: Agents That Improve Their Own Builders
   44. CMP: Iterative Self-Improvement Through Code, Memory, and Process
   45. How CMP Systems Evaluate and Accept Their Own Changes
   46. MARS: Multi-Agent Research and Revision Loops
   47. Why MARS Uses Specialization, Critique, and Coordination
   48. Hyperagent Architectures: Hierarchies, Tool Use, and Recursive Delegation
   49. Comparing CMP, MARS, and Hyperagent Design Patterns
   50. Darwin Gödel Machine and the Case for Empirical Self-Improvement
   51. Population-Based Search, Archives, and Evolutionary Stepping Stones
   52. What Makes Self-Improving Multi-Agent Systems Actually Work
   53. Failure Modes: Drift, Reward Hacking, Coordination Overhead, and Safety Risks
   54. Practical Design Principles for Building These Systems Today
   55. Where the Field Is Going Next
   56. tokens used
   57. 193
   58. Why Self-Improving Multi-Agent Systems Matter
   59. From Fixed Agents to Self-Modification
   60. The Core Idea: Agents That Improve Their Own Builders
   61. CMP: Iterative Self-Improvement Through Code, Memory, and Process
   62. How CMP Systems Evaluate and Accept Their Own Changes
   63. MARS: Multi-Agent Research and Revision Loops
   64. Why MARS Uses Specialization, Critique, and Coordination
   65. Hyperagent Architectures: Hierarchies, Tool Use, and Recursive Delegation
   66. Comparing CMP, MARS, and Hyperagent Design Patterns
   67. Darwin Gödel Machine and the Case for Empirical Self-Improvement
   68. Population-Based Search, Archives, and Evolutionary Stepping Stones
   69. What Makes Self-Improving Multi-Agent Systems Actually Work
   70. Failure Modes: Drift, Reward Hacking, Coordination Overhead, and Safety Risks
   71. Practical Design Principles for Building These Systems Today
   72. Where the Field Is Going Next

### Running Context
(No prior context.)

## Guidelines
- Open with a compelling hook that draws the reader in within the first two sentences.
- Write in an accessible, conversational tone that matches the style profile.
- Target 1500-2500 words for the full post.
- Use subheadings, short paragraphs, and bullet points to improve scannability.
- Include a clear takeaway or call-to-action in the conclusion.

## SEO Guidance
- Weave the primary topic naturally into the opening paragraph.
- Use descriptive subheadings that signal content to both readers and search engines.
- Write a meta description (1-2 sentences, under 160 characters) summarising the post.

## Few-Shot Examples
### Example 1: dgm_darwin_godel_machine.md

# Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents

Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune

University of British Columbia, Vector Institute, Sakana AI

## Abstract

Most contemporary AI systems operate within fixed, human-designed architectures and cannot autonomously improve themselves. We introduce the Darwin Gödel Machine (DGM), a self-referential system that iteratively modifies its own code to enhance coding capabilities. Rather than requiring formal proofs of beneficial changes (as theoretical Gödel machines demand), the DGM empirically validates modifications using coding benchmarks. The system maintains an archive of generated agents and samples from it for self-modification, inspired by Darwinian evolution and open-endedness principles. Results demonstrate performance improvements from 20.0% to 50.0% on SWE-bench and 14.2% to 30.7% on Polyglot, significantly outperforming baselines lacking self-improvement or open-ended exploration.

## Introduction

Scientific progress operates cumulatively, with innovations building on prior discoveries. Current AI systems, despite their sophistication, remain constrained by fixed architectures designed by humans. Unlike the scientific method, which enables continuous self-directed advancement, today's AI development still depends heavily on human intervention. This paper investigates automating the search for progressively better AI systems.

Schmidhuber's theoretical Gödel machines represent one approach, relying on formal proofs ensuring modifications improve performance. However, proving that changes benefit complex systems like large language models is practically impossible. The actual impact of modifications depends heavily on context---a testing tool optimized for one environment might confuse an agent in another.

The Darwin Gödel Machine relaxes this requirement, instead using empirical validation through benchmarking. This mirrors biological evolution, where mutations aren't verified in advance but produced, tested, and selected through natural selection. The DGM combines this with inspiration from Darwinian principles and open-endedness research, maintaining a library of discovered agents as stepping stones for future generations.

## Darwin Gödel Machine

A Gödel Machine theoretically searches for provably beneficial self-improvements. The DGM relaxes this impractical requirement, instead requiring empirical evidence from experiments. This empiricism addresses the impossibility of proving changes improve complex systems.

Since empirical evidence can trap systems in local optima within vast algorithmic search spaces, the DGM maintains an archive of discovered solutions, enabling open-ended exploration rather than single-solution evolution. This mirrors Darwinian evolution, where innovations emerge by selecting entities from previous discoveries, modifying them, and retaining interesting variations.

### Self-Referential Self-Improvement of Coding Agents

The DGM initializes with one coding agent and evaluates progress on coding benchmarks. A coding agent represents a system implemented as a code repository, powered by frozen pretrained foundation models, capable of reading, writing, and executing code.

Self-improvement is defined as modifying the agent's own codebase components---tools, workflows, prompts. Python's Turing-completeness enables building any computable machine. The key motivation: empirical improvements must reflect both downstream task-solving ability and self-modification capacity. By configuring the DGM as a coding agent and testing coding capabilities, observed improvements demonstrate enhanced problem-solving and future self-improvement potential.

### Population-Based Open-Ended Exploration

Starting from a single agent, the DGM accumulates all generated variants in an archive. Each iteration selects parent agents for self-modification, roughly proportional to performance and inversely proportional to the number of their children. This balances exploitation of strong performers with exploration of promising, undersampled lineages.

All agents retain non-zero selection probability, ensuring any improvement pathway remains feasible. Each selected parent analyzes benchmark evaluation logs, proposes the next feature, and executes the modification. Newly generated agents undergo quantitative benchmark evaluation. Only agents compiling successfully and retaining codebase-editing ability join the archive; others are discarded.

Crucially, archived solutions can later serve as stepping stones for improvements discovered much later---substantially differentiating this from hill-climbing approaches.

## Experiments

### Setup

The DGM initializes with a lightweight coding agent built around a frozen foundation model with tool-use capabilities. The base agent accesses two tools: a Bash tool for command execution and an edit tool for viewing and modifying files. The intentionally lightweight design provides a simple starting point demonstrating clear improvement.

The DGM ran for 80 iterations, generating one new agent per iteration, with parallelization. During self-modifications, agents used Claude 3.5 Sonnet.

### Results

After 80 iterations, coding agent performance increased from 20.0% to 50.0% on SWE-bench and from 14.0% to 38.0% on Polyglot. DGM-discovered agents achieve performance comparable to or exceeding handcrafted solutions.

The DGM automatically enhanced both tools and foundation model workflows. Tool improvements included granular file viewing and precise editing. Workflow improvements encompassed multiple solution attempts and using another FM to evaluate and select optimal solutions.

Open-ended exploration allows escape from deceptive performance dips. Iterations 4 and 56 showed temporary score decreases below parent performance, yet the system discovered innovations along those paths creating superior agents.

### Transfer Results

DGM-discovered agents generalize across foundation models, benchmarks, and programming languages, confirming improvements reflect general capability acquisition rather than benchmark overfitting.

## Safety Discussion

Self-improving systems introduce unique safety considerations from autonomous code modification. Modifications optimized solely for benchmark performance might inadvertently introduce vulnerabilities. Current safeguards include sandboxed execution, time limits, coding-only modifications, and archive-based traceability.

## Conclusion

The Darwin Gödel Machine represents the first self-improving system powered by foundation models with open-ended exploration, where evaluation benchmark progress directly translates to improved self-modification capabilities. Automatic discovery of better tools and foundation model system designs yielded superior performance on SWE-bench and Polyglot.


---

### Example 2: hgm_huxley_godel_machine.md

# Huxley-Gödel Machine: Human-Level Coding Agent Development by an Approximation of the Optimal Self-Improving Machine Wenyi Wang, Piotr Piękos, Li Nanbo, Firas Laakom, Yimeng Chen, Mateusz Ostaszewski, Mingchen Zhuge, Jürgen Schmidhuber King Abdullah University of Science and Technology (KAUST) ## Abstract Recent work operationalizes self-improvement through coding agents that modify their own codebases. These systems grow trees of self-modifications guided by software engineering benchmark performance, assuming higher scores predict better future iterations. However, we identify a critical gap: an agent's immediate performance doesn't reliably indicate its capacity for productive self-improvement, which we term the "Metaproductivity-Performance Mismatch." We introduce Clade-Metaproductivity (CMP), a metric aggregating descendant performance rather than evaluating individual agents. This concept, inspired by evolutionary biology's notion of clades as ancestral lineages, measures an agent's self-improvement potential. We prove that access to true CMP suffices to simulate Gödel Machines under specific assumptions about our problem setting. We propose the Huxley-Gödel Machine (HGM), which estimates CMP and uses Thompson sampling to guide tree search. Experiments on SWE-bench Verified and Polyglot show HGM outperforms prior methods (DGM and SICA) while using substantially fewer CPU hours. Remarkably, an agent optimized on SWE-bench Verified with GPT-5-mini achieves human-level performance matching top human-engineered solutions when evaluated on SWE-bench Lite with GPT-5. ## Introduction The automation of software engineering has progressed from simple auto-completion to sophisticated coding agents capable of solving complex real-world tasks. A particularly exciting frontier is self-improving coding agents---systems that modify their own codebases to enhance their capabilities. These systems grow search trees of self-modifications, where each node represents an agent variant and edges represent mutation operations. The prevailing approach evaluates agent variants using benchmark scores and selects the best performers for further modification. This greedy strategy assumes that higher immediate performance predicts greater capacity for productive self-improvement. We challenge this assumption with a key observation: benchmark scores alone do not reliably indicate an agent's long-term potential for self-improvement. We formalize this as the Metaproductivity-Performance Mismatch: a high-scoring agent may produce unproductive descendants, while a lower-scoring one seeds lineages that achieve greater long-term gains. This mismatch arises because immediate benchmark performance captures task-solving ability but not the agent's capacity to generate productive mutations. To address this, we introduce Clade-Metaproductivity (CMP), inspired by evolutionary biology's clade concept. CMP measures the expected maximum utility achievable within an agent's entire descendant lineage, capturing the long-term improvement potential of an evolutionary branch rather than a single individual. We prove that access to true CMP values is sufficient to implement the accept/reject decisions of a Gödel Machine---the provably optimal self-improving system---within our problem setting. ## Self-Improvement as Tree-Search We formalize self-improving agent development as an iterative tree search problem. Let $\mathcal{T}_t$ denote the tree (archive) of agents at iteration $t$, initialized as $\mathcal{T}_0 = \{a_0\}$ where $a_0$ is the initial agent. At each step, a policy $\pi$ selects either: - An expansion action $m_a$: produce a self-modified child of agent $a$ - An evaluation action $v_a$: test agent $a$ on a downstream task The objective is to maximize $J(\pi) = \mathbb{E}[U(a_{\text{final}})]$, where $a_{\text{final}} = \arg\max_{a \in \mathcal{T}_B} \mathit{Score}_\pi(a)$ at budget exhaustion $B$, and $U$ measures downstream task performance. ### Clade-Metaproductivity Let $C(\mathcal{T}, a)$ denote the clade of agent $a$---the subtree of $\mathcal{T}$ rooted at $a$. The Clade-Metaproductivity of $a$ under policy $\pi$ is: $$\mathrm{CMP}_\pi(\mathcal{T}, a) = \mathbb{E}_{\mathcal{T}_B \sim p_\pi(\cdot \mid \mathcal{T}, a)}\left[\max_{a' \in C(\mathcal{T}_B, a)} U(a')\right]$$ CMP captures the long-term potential of the lineage rooted at $a$, aggregating descendant performance rather than relying on $a$'s immediate score. This is estimated by the clade-aggregated success ratio: $$\widehat{\mathrm{CMP}}(a) = \frac{n^C_\text{success}(a)}{n^C_\text{success}(a) + n^C_\text{failure}(a)}$$ where $n^C_\text{success}(a) = \sum_{a' \in C(a)} n_\text{success}(a')$. ### Thompson Sampling and Scheduling Expansion and evaluation targets are selected via Thompson sampling over Beta posteriors. The exploration-exploitation scheduler $\tau(t) = B/b$ (where $b$ is remaining budget) flattens the posterior early in the run (encouraging exploration) and sharpens it late (encouraging exploitation of the best-performing lineages). The expand-vs-evaluate decision follows UCB-Air: expand when $N_t^\alpha \geq |\mathcal{T}_t|$ for widening parameter $\alpha \in [0,1]$. ## Huxley-Gödel Machine The HGM instantiates the CMP-guided tree search framework. It separates the expansion policy (which parent to mutate) from the evaluation policy (which agent to test), using Thompson sampling over clade-aggregated counters for expansion and per-node counters for evaluation. ### Expansion Policy For expansion, sample the parent via Thompson sampling: $$a^* \sim \text{TS}\left(\left\{\left(\tau(1 + n^C_s(a)), \tau(1 + n^C_f(a))\right) \mid a \in \mathcal{T}_t\right\}\right)$$ ### Evaluation Policy For evaluation, sample the node to test: $$a^* \sim \text{TS}\left(\left\{\left(\tau(1 + n_s(a)), \tau(1 + n_f(a))\right) \mid a \in \mathcal{T}_t\right\}\right)$$ ### Final Selection At budget exhaustion, return the agent maximizing the $\epsilon$-percentile of the posterior: $$\arg\max_{a \in \mathcal{T}_B} I_\epsilon(1 + n_s(a), 1 + n_f(a))$$ ### Asynchronous Implementation HGM operates asynchronously: multiple CPU workers run expansion and evaluation tasks in parallel. Running expansions count toward $|\mathcal{T}_t|$ and running evaluations toward $N_t$, ensuring the UCB-Air condition accounts for in-progress work. ## Theoretical Analysis We prove that access to a CMP oracle is sufficient to implement the Gödel Machine's accept/reject decisions. **Theorem (CMP Oracle Guarantee).** Under assumptions of (i) objective depending only on the final selected agent, (ii) repeatable evaluation trials, (iii) proof mechanism not consuming budget, and (iv) each self-modification costing exactly one budget unit: access to a CMP oracle is sufficient to implement the Gödel Machine. The proof constructs a Gödel POMDP whose state is $(\mathcal{T}, a_p, a_c, b)$ and shows that CMP equals the Q-value function, providing the true action-value needed for optimal accept/reject decisions. ## Experimental Results ### CMP Correlation Analysis We empirically validate that CMP correlates more strongly with long-term improvement potential than immediate benchmark performance. Across multiple experimental runs, agents selected by CMP produce lineages with higher maximum utility than agents selected by immediate performance. ### Self-Improvement Effectiveness On SWE-bench Verified, HGM agents improve from baseline performance to human-level, matching established baselines like Agentless, Moatless, and SWE-agent while using substantially fewer computational resources. On Polyglot, HGM demonstrates consistent improvement across iterations. ### Generalization HGM-discovered agents transfer across: - LLM scales (GPT-5-mini to GPT-5) - Benchmarks (SWE-bench to Polyglot and vice versa) - Programming languages (Python-trained agents improve on non-Python tasks) ## Conclusion We have identified the Metaproductivity-Performance Mismatch in

[... truncated ...]

---

### Example 3: hyperagents.tex

# Introduction {#sec:intro} With appropriate safety considerations, AI systems that can improve themselves could transform scientific progress from a human-paced process into an autonomously accelerating one, thereby allowing society to realize the benefits of technological advances much earlier. Such self-improving AI seeks to continually improve its own learning and task-solving abilities. However, most existing self-improvement architectures rely on a fixed meta agent (i.e., a higher-level system that modifies a base system). This creates a limitation since the base system can only be improved within the boundaries defined by the meta agent's design. Adding a meta-meta system to improve the meta agent does not solve this problem, it merely shifts the issue upward and ultimately leads to an infinite regress of meta-levels. To overcome this limitation and allow a system to modify any part of itself without being constrained by its initial implementation, the system must be self-referential, that is, able to analyze, modify, and evaluate itself [@kirsch2022eliminating; @zhang2025darwin]. When the mechanism of improvement is itself subject to improvement, progress can become self-accelerating and potentially unbounded [@lu2023arbitrary]. The Darwin Gödel Machine (DGM) [@zhang2025darwin] demonstrates that open-ended self-improvement is achievable in coding. In the DGM, agents generate and evaluate modifications to their own code, and successful variants are retained in an archive as stepping stones for further improvement. However, the DGM relies on a handcrafted, fixed mechanism to produce self-improvement instructions ([9](#app:baseline-details){reference-type="ref+Label" reference="app:baseline-details"}). This mechanism analyzes past evaluation results and the agent's current codebase to generate an instruction directing where the agent should self-improve. This mechanism is not modifiable. Hence, the DGM's capacity for self-improvement is bottlenecked by this fixed instruction-generation step. Despite this handcrafted step, the DGM can still improve at self-improving. Because both evaluation and self-modification are coding tasks, improvements in evaluation performance directly reflects the agent's capacity to generate effective self-modifications. To improve at self-improving, the DGM relies on a limiting assumption: that the skills required to solve the evaluation tasks are the same as those required for effective self-reflection and self-modification. This assumption is unlikely to hold outside coding domains, where task-solving skills may differ substantially from the skills needed to analyze failures, propose effective self-improvements, and implement them. This work introduces *hyperagents*, self-referential agents that can in principle self-improve for any computable task. Here, an *agent* is any computable program, optionally including calls to foundation models (FMs), external tools, or learned components. A *task agent* solves a given task. A *meta agent* modifies agents and generates new ones. A hyperagent combines the task agent and the meta agent into a single self-referential, modifiable program, such that the mechanism responsible for generating improvements is itself subject to modification. As a result, a hyperagent can improve not only how it solves tasks (i.e., the task agent), but also how it generates and applies future modifications (i.e., the meta agent). Because its self-improvement mechanism is itself modifiable, we call this *metacognitive self-modification*. We extend the DGM with hyperagents, creating DGM-Hyperagents (DGM-H). The DGM-H retains the open-ended exploration structure of the DGM and extends the DGM with metacognitive self-modification. As with DGM, to support sustained progress and avoid premature convergence, the DGM-H grows an archive of hyperagents by branching from selected candidates, allowing them to self-modify, evaluating the resulting hyperagents, and adding them back to the archive. Because a hyperagent can modify its self-modification process, the DGM-H is not constrained by its initial implementation and can potentially self-improve for any computable task. Across our experiments, the DGM-H demonstrates substantial and generalizable improvements in both task performance and self-improvement ability. On the Polyglot coding benchmark [@gauthier2024polyglot], the DGM-H achieves gains comparable to the most established prior self-improving algorithm [the Darwin Gödel Machine, @zhang2025darwin], despite not being handcrafted for coding. Beyond coding, the DGM-H substantially improves performance on paper review [@zhao2026apres] and robotics reward design [@genesis2024], with gains transferring to held-out test tasks and significantly outperforming prior self-improving algorithms, which struggle outside coding unless customized. Ablations without self-improvement or without open-ended exploration show little to no progress, highlighting the necessity of each component ([5.1](#sec:results-task){reference-type="ref+Label" reference="sec:results-task"}). Crucially, the DGM-H learns transferable mechanisms on how to self-improve (e.g., persistent memory, performance tracking) that systematically improve its ability to generate better task or meta agents over time. As a result, meta-level improvements learned by the DGM-H transfer across domains. Specifically, hyperagents optimized in one setting (i.e., paper review and robotics tasks) remain significantly effective at generating improved task agents in a different domain (i.e., Olympiad-level math grading) ([5.2](#sec:results-meta){reference-type="ref+Label" reference="sec:results-meta"}). We further show that self-improvements learned by the DGM-H in one setting can compound with continued self-improvement in another setting ([5.3](#sec:results-compound){reference-type="ref+Label" reference="sec:results-compound"}). This suggests that, given appropriate tasks, the DGM-H has the potential to achieve unbounded open-ended self-improvement over time. We discuss the safety implications of such open-ended self-improving systems and outline practical considerations for responsible deployment in [6](#sec:safety){reference-type="ref+Label" reference="sec:safety"}. Overall, hyperagents open up the possibility of improving their ability to improve while improving their ability to perform any computable task. # Related Work {#sec:related-work} **Open-Endedness.** Open-endedness refers to the ability of a system to continually invent new, interesting, and increasingly complex artifacts, extending its own frontier of discovery without a fixed objective or predefined end [@stanley2017open; @hughes2024open]. Recent work has leveraged FMs as proxies for human interestingness and as versatile engines for generating and evaluating novel behaviors across diverse domains [@zhangomni; @faldoromni]. Building on these advances, recent progress in open-ended learning [@huautomated; @zoph2017neural; @colas2023augmenting; @lehman2023evolution] and quality-diversity algorithms [@lehman2011evolving; @mouret2015illuminating; @bradley2023quality; @samvelyan2024rainbow; @dingquality; @pourcel2023aces; @coiffard2025overcoming; @dharna2025foundation; @yuan2026agenticred] has shown that sustained exploration can produce diverse and increasingly capable artifacts across domains ranging from game-playing agents [@klissarov2023motif; @klissarovmaestromotif; @wangvoyager] to scientific discovery [@lu2024discovering; @lu2024ai; @romera2024mathematical; @novikov2025alphaevolve; @audran2025does] and robotic control [@cully2015robots; @li2024auto; @grillotti2025tabula]. Recent progress has shown that open-ended AI systems capable of continuously generating diverse and increasingly complex artifacts are possible [@zhangomni; @faldoromni; @huautomated]. An important next step is to explore how such systems can achieve compounding improvement. In human scientific and technological

[... truncated ...]

## Output
Generate the **OpenAI Codex v0.116.0 (research preview)** section in Markdown. Do not include the
section heading — the pipeline adds it. If this is the final section, append
a meta description on a separate line prefixed with `META:`.

mcp startup: no servers
codex
Most AI agents today can do useful work, but they still share a basic limitation: they are born with a fixed way of thinking. You can give them better prompts, more tools, or a more capable model, but the mechanism that decides how they plan, critique, and improve usually stays frozen. Self-improving multi-agent systems matter because they attack that limitation directly. Instead of treating the agent as a finished product, they treat it as a candidate for ongoing redesign.

That shift is subtle, but it changes the engineering problem completely. Once an agent can inspect its own behavior, propose changes, test them, and keep the ones that help, you are no longer just building a system that solves tasks. You are building a system that helps design its own successor.

## From Fixed Agents to Self-Modification

A standard agent loop is straightforward: observe, plan, act, evaluate. A self-improving agent adds a second loop around that first one:

- Run tasks in the environment
- Collect traces, failures, and outcomes
- Analyze what caused success or failure
- Propose modifications to prompts, tools, memory, workflows, or code
- Evaluate the modified version
- Keep, reject, or archive the result

Multi-agent systems push this further by splitting those responsibilities across specialized roles. One agent may execute tasks, another may critique outputs, another may design experiments, and another may decide whether a proposed change should be adopted. This division of labor makes self-improvement more tractable because reflection, generation, verification, and selection are different jobs.

The hard part is not generating changes. Large models are already good at proposing revisions. The hard part is deciding which revisions are actually worth keeping. That is where recent work on CMP, MARS-style research loops, and hyperagent architectures becomes useful. They represent different answers to the same core question: how should a system improve itself without collapsing into noise, drift, or self-delusion?

## The Core Idea: Agents That Improve Their Own Builders

There is a useful way to frame these systems. A self-improving multi-agent architecture usually has three layers:

- A task layer that does useful work
- A meta layer that evaluates and modifies the task layer
- A selection layer that decides what survives

In many early systems, the meta layer is still handcrafted and fixed. That means the agent can improve within boundaries, but not rewrite the rules of improvement itself. More recent work tries to relax that constraint. The goal is self-reference: the system should be able to inspect and modify not only its task-solving behavior, but also the mechanisms it uses to critique, search, and improve.

That is the larger arc connecting CMP, MARS, and hyperagent architectures. They differ in how they search the space of possible improvements, but all three move away from the idea of a single static agent and toward a population or organization of agents that can revise their own operating procedures.

## CMP: Why Immediate Performance Is Not Enough

One of the most important ideas in this area is that current performance and future improvement potential are not the same thing. A system might score well on today's benchmark and still be a poor parent for tomorrow's better system. Another might look mediocre now but generate descendants that improve rapidly.

That is the motivation behind **Clade-Metaproductivity**, or CMP. Instead of asking, "How good is this agent right now?" CMP asks, "How promising is the lineage rooted at this agent?" In other words, it tries to measure not just task competence, but improvement potential.

This matters because self-improving systems are doing search over a tree of descendants. If you always pick the highest-scoring current node, you risk getting stuck in local optima. A good benchmark score may reflect a brittle shortcut, overfitting, or a design that solves the present task while making future modification harder.

CMP changes the selection target from individual performance to lineage value. Conceptually, it favors agents whose descendants tend to produce strong results, even if the parent itself is not the top performer. That is a better fit for open-ended improvement, where you care about the trajectory of a branch rather than a single snapshot.

In practice, a CMP-style architecture does three things differently:

- It tracks ancestry, not just isolated runs
- It aggregates evidence over descendants
- It separates "good worker" from "good ancestor"

This is a strong correction to naive hill-climbing. For engineers, the lesson is practical: if your self-improving system only optimizes for immediate benchmark gains, it will often optimize the wrong thing.

## MARS: Multi-Agent Research and Revision Loops

If CMP is mainly about **what to select**, MARS-style systems are about **how to generate and refine improvements**.

A MARS architecture treats self-improvement as a research process. Instead of a single agent rewriting itself in one pass, it builds a loop of specialized agents that investigate a problem, generate candidate changes, criticize those changes, run experiments, and synthesize conclusions. The system operates more like a small technical team than a lone assistant.

A typical MARS loop looks like this:

- A planner defines the current improvement target
- A researcher analyzes logs, failures, and prior attempts
- A proposer drafts modifications to prompts, tools, memory, or code
- A critic stress-tests those proposals
- An evaluator runs controlled experiments
- A coordinator records results and updates the shared state

This structure brings two advantages.

First, it makes improvement more legible. The system produces explicit hypotheses, experiments, and rationales rather than opaque prompt churn. That matters when you want to debug why a change helped, failed, or transferred poorly.

Second, it creates productive disagreement. Single-agent self-editing often collapses because the same model invents, defends, and approves its own modifications. MARS reduces that problem by introducing role separation. A critic can challenge a proposal. An evaluator can reject a change even if the proposer sounded persuasive. A coordinator can compare several attempts instead of just following the latest confident suggestion.

That role specialization is not free. It adds coordination overhead and can slow iteration. But for nontrivial domains, it is often worth it because it replaces one-shot self-editing with something closer to an internal scientific method.

## Why Specialization and Critique Help

The strongest MARS-style systems are not interesting because they use many agents. They are interesting because each agent has a sharply scoped responsibility.

Specialization helps in at least four ways:

- It reduces context overload by giving each agent a narrower task
- It creates independent viewpoints over the same evidence
- It makes experiments easier to attribute and compare
- It turns vague "improve yourself" goals into concrete subproblems

For example, one agent may be good at mining failure logs for recurring patterns. Another may be better at proposing architectural changes. A third may be best at designing robust evaluations. When these roles are separated, the system gains a cleaner internal division between observation, hypothesis generation, and validation.

This structure also helps with safety and reliability. Self-improving systems are prone to reward hacking: they can find changes that inflate metrics without improving underlying capability. A dedicated critic or auditor can check whether a gain is real, whether it transfers across tasks, and whether it preserves required invariants such as tool safety, code correctness, or memory integrity.

In that sense, MARS is less a single architecture than a design pattern: improvement should emerge from structured internal debate, not just self-affirmation.

## Hyperagent Architectures: Making the Meta Layer Modifiable

Hyperagent architectures push one step further. They are motivated by a limitation in many self-improving systems: even when the task agent can change, the improvement mechanism itself is often fixed by human designers.

That creates a bottleneck. If the task-solving component improves but the mechanism that decides how to search, critique, or revise remains static, long-term progress is capped by the original meta-design.

A hyperagent removes that bottleneck by combining the task agent and the meta agent into a single self-referential program. The system can then modify:

- How it performs tasks
- How it evaluates those tasks
- How it proposes future changes
- How it stores and reuses knowledge about past changes

This is a more radical form of self-improvement because the procedure of improvement is itself subject to improvement. The architecture is no longer just optimizing a worker. It is optimizing the organization that designs the worker.

That matters outside coding. In software domains, there is often a convenient overlap between solving tasks and modifying the system that solves tasks. But in many other domains, those are different skills. Reviewing a paper, designing a robotics reward, and inventing a better self-critique mechanism are not the same task. Hyperagent architectures explicitly target that gap by allowing meta-level strategies to evolve rather than assuming they are fixed.

## Darwinian Search, Archives, and Stepping Stones

The most compelling self-improving systems borrow an idea from evolution: do not commit everything to a single incumbent. Keep an archive.

The Darwin Gödel Machine popularized this pattern in a practical form. Rather than demanding formal proof that a modification is beneficial, it accepts empirical validation. It generates self-modified descendants, evaluates them, and stores viable variants in an archive. Future search can branch from many earlier discoveries, not just the current best agent.

This archive is more than a history log. It is a search primitive.

Why does that matter? Because progress is often nonmonotonic. Some useful innovations look worse before they look better. A branch may temporarily reduce benchmark performance while introducing structure that later enables larger gains. If search only follows the current leader, those branches die too early.

Archive-based search preserves stepping stones:

- High performers can be exploited
- Diverse variants can be revisited
- Apparently weak branches can later produce strong descendants
- Improvement becomes population-based rather than purely greedy

CMP fits naturally into this picture because it values a branch's long-term potential. MARS fits because multiple agents can analyze the archive, compare experiments, and propose mutations. Hyperagents fit because archived systems can differ not just in task behavior but in how they generate future improvements.

Once you combine these ideas, a self-improving multi-agent system starts to look less like an assistant and more like an evolving lab.

## Comparing CMP, MARS, and Hyperagent Patterns

These approaches are complementary, but they emphasize different failure modes.

**CMP** addresses selection. It warns that immediate score is a poor proxy for long-run improvement potential. Use it when you are exploring many descendants and need a better signal for where to invest compute.

**MARS** addresses process. It structures improvement as a multi-agent research loop with explicit specialization, critique, and experimental validation. Use it when you need disciplined iteration and interpretable revision cycles.

**Hyperagents** address architectural limits. They make the meta-level itself modifiable, reducing dependence on a fixed human-designed improvement mechanism. Use them when you want adaptation that can generalize beyond domains where task-solving and self-modification happen to overlap.

A practical system can use all three:

- MARS-style agents generate and test revisions
- CMP-like signals guide which branches deserve more search
- Hyperagent design allows the revision process itself to evolve

That combination is much closer to open-ended improvement than any single static agent loop.

## What Makes These Systems Actually Work

The theory is interesting, but the engineering constraints are unforgiving. Self-improving multi-agent systems only work when four pieces are in place.

### 1. Reliable evaluation

If the benchmark is weak, the whole system learns the wrong lesson. Evaluation must check for transfer, robustness, and regressions, not just local score increases.

### 2. Traceable memory

The system needs a persistent record of changes, experiments, ancestry, and outcomes. Otherwise it repeats failed ideas and cannot identify why a branch succeeded.

### 3. Structured search

Random mutation is not enough. You need prioritization, branching logic, and selection pressure. Archives, lineage tracking, and CMP-like statistics are part of that.

### 4. Separation of roles

Generation, critique, execution, and acceptance should not all be controlled by the same internal voice. Multi-agent separation is often the simplest way to reduce self-confirming errors.

Without those ingredients, "self-improvement" usually degenerates into noisy prompt rewrites with unstable gains.

## Failure Modes: Drift, Gaming, and Coordination Cost

These systems are promising, but they are fragile.

One failure mode is **capability drift**. A change helps on the measured task but erodes general usefulness. Another is **reward hacking**. The system learns to satisfy the metric rather than the intent of the task. A third is **meta-overhead**: the coordination cost of many agents can exceed the value of the improvements they discover.

There is also a deeper risk. A self-improving architecture can accumulate complexity faster than humans can audit it. If the system rewrites its own prompts, tools, memories, and evaluation logic, you need strong constraints around what can be changed, how changes are tested, and when a branch is allowed to propagate.

At minimum, practical deployments need:

- Sandboxed execution
- Versioned archives
- Rollback paths
- Held-out evaluations
- Invariant checks for safety-critical behavior
- Human visibility into why changes were accepted

Open-ended search is powerful precisely because it can discover nonobvious solutions. That same property makes it risky if acceptance criteria are weak.

## Practical Design Principles for Builders

If you are building self-improving multi-agent systems today, the sensible approach is not to chase fully autonomous recursive self-improvement on day one. Start narrower.

Build a system that can improve one layer at a time. Let it revise prompts before code. Let it optimize workflows before tool permissions. Use archive-based comparison before open-ended mutation. Add specialized critic and evaluator roles before making the meta-controller itself editable.

A useful design sequence looks like this:

1. Start with strong task instrumentation and reproducible evaluation.
2. Add multi-agent revision loops for proposal, critique, and testing.
3. Track ancestry and archive all viable variants.
4. Introduce branch-level selection signals such as CMP-style lineage scoring.
5. Only then allow limited modification of the improvement process itself.

That path is slower, but it is technically honest. Most failures in this area come from skipping evaluation discipline and jumping straight to unconstrained self-editing.

## Where the Field Is Going Next

The field is moving away from the idea of a single monolithic agent and toward systems that behave more like adaptive organizations. The interesting question is no longer just whether an agent can solve a task. It is whether it can become better at discovering the next version of itself.

CMP sharpens our notion of what to optimize. MARS gives us a practical loop for structured internal research and revision. Hyperagent architectures point toward systems that can modify the very machinery of self-improvement. Taken together, they suggest a future in which multi-agent systems do not merely execute workflows. They accumulate methods, refine their own internal division of labor, and improve the process by which they improve.

The immediate takeaway is simple: if you want robust self-improving AI, do not only ask how well an agent performs today. Ask whether your architecture preserves stepping stones, supports internal critique, and can eventually revise the mechanism of revision itself.

That is the difference between a clever agent and an evolving one.

META: A practical guide to self-improving multi-agent systems, covering CMP, MARS, hyperagent architectures, and why lineage, critique, and archives matter.
tokens used
17.668
Most AI agents today can do useful work, but they still share a basic limitation: they are born with a fixed way of thinking. You can give them better prompts, more tools, or a more capable model, but the mechanism that decides how they plan, critique, and improve usually stays frozen. Self-improving multi-agent systems matter because they attack that limitation directly. Instead of treating the agent as a finished product, they treat it as a candidate for ongoing redesign.

That shift is subtle, but it changes the engineering problem completely. Once an agent can inspect its own behavior, propose changes, test them, and keep the ones that help, you are no longer just building a system that solves tasks. You are building a system that helps design its own successor.

## From Fixed Agents to Self-Modification

A standard agent loop is straightforward: observe, plan, act, evaluate. A self-improving agent adds a second loop around that first one:

- Run tasks in the environment
- Collect traces, failures, and outcomes
- Analyze what caused success or failure
- Propose modifications to prompts, tools, memory, workflows, or code
- Evaluate the modified version
- Keep, reject, or archive the result

Multi-agent systems push this further by splitting those responsibilities across specialized roles. One agent may execute tasks, another may critique outputs, another may design experiments, and another may decide whether a proposed change should be adopted. This division of labor makes self-improvement more tractable because reflection, generation, verification, and selection are different jobs.

The hard part is not generating changes. Large models are already good at proposing revisions. The hard part is deciding which revisions are actually worth keeping. That is where recent work on CMP, MARS-style research loops, and hyperagent architectures becomes useful. They represent different answers to the same core question: how should a system improve itself without collapsing into noise, drift, or self-delusion?

## The Core Idea: Agents That Improve Their Own Builders

There is a useful way to frame these systems. A self-improving multi-agent architecture usually has three layers:

- A task layer that does useful work
- A meta layer that evaluates and modifies the task layer
- A selection layer that decides what survives

In many early systems, the meta layer is still handcrafted and fixed. That means the agent can improve within boundaries, but not rewrite the rules of improvement itself. More recent work tries to relax that constraint. The goal is self-reference: the system should be able to inspect and modify not only its task-solving behavior, but also the mechanisms it uses to critique, search, and improve.

That is the larger arc connecting CMP, MARS, and hyperagent architectures. They differ in how they search the space of possible improvements, but all three move away from the idea of a single static agent and toward a population or organization of agents that can revise their own operating procedures.

## CMP: Why Immediate Performance Is Not Enough

One of the most important ideas in this area is that current performance and future improvement potential are not the same thing. A system might score well on today's benchmark and still be a poor parent for tomorrow's better system. Another might look mediocre now but generate descendants that improve rapidly.

That is the motivation behind **Clade-Metaproductivity**, or CMP. Instead of asking, "How good is this agent right now?" CMP asks, "How promising is the lineage rooted at this agent?" In other words, it tries to measure not just task competence, but improvement potential.

This matters because self-improving systems are doing search over a tree of descendants. If you always pick the highest-scoring current node, you risk getting stuck in local optima. A good benchmark score may reflect a brittle shortcut, overfitting, or a design that solves the present task while making future modification harder.

CMP changes the selection target from individual performance to lineage value. Conceptually, it favors agents whose descendants tend to produce strong results, even if the parent itself is not the top performer. That is a better fit for open-ended improvement, where you care about the trajectory of a branch rather than a single snapshot.

In practice, a CMP-style architecture does three things differently:

- It tracks ancestry, not just isolated runs
- It aggregates evidence over descendants
- It separates "good worker" from "good ancestor"

This is a strong correction to naive hill-climbing. For engineers, the lesson is practical: if your self-improving system only optimizes for immediate benchmark gains, it will often optimize the wrong thing.

## MARS: Multi-Agent Research and Revision Loops

If CMP is mainly about **what to select**, MARS-style systems are about **how to generate and refine improvements**.

A MARS architecture treats self-improvement as a research process. Instead of a single agent rewriting itself in one pass, it builds a loop of specialized agents that investigate a problem, generate candidate changes, criticize those changes, run experiments, and synthesize conclusions. The system operates more like a small technical team than a lone assistant.

A typical MARS loop looks like this:

- A planner defines the current improvement target
- A researcher analyzes logs, failures, and prior attempts
- A proposer drafts modifications to prompts, tools, memory, or code
- A critic stress-tests those proposals
- An evaluator runs controlled experiments
- A coordinator records results and updates the shared state

This structure brings two advantages.

First, it makes improvement more legible. The system produces explicit hypotheses, experiments, and rationales rather than opaque prompt churn. That matters when you want to debug why a change helped, failed, or transferred poorly.

Second, it creates productive disagreement. Single-agent self-editing often collapses because the same model invents, defends, and approves its own modifications. MARS reduces that problem by introducing role separation. A critic can challenge a proposal. An evaluator can reject a change even if the proposer sounded persuasive. A coordinator can compare several attempts instead of just following the latest confident suggestion.

That role specialization is not free. It adds coordination overhead and can slow iteration. But for nontrivial domains, it is often worth it because it replaces one-shot self-editing with something closer to an internal scientific method.

## Why Specialization and Critique Help

The strongest MARS-style systems are not interesting because they use many agents. They are interesting because each agent has a sharply scoped responsibility.

Specialization helps in at least four ways:

- It reduces context overload by giving each agent a narrower task
- It creates independent viewpoints over the same evidence
- It makes experiments easier to attribute and compare
- It turns vague "improve yourself" goals into concrete subproblems

For example, one agent may be good at mining failure logs for recurring patterns. Another may be better at proposing architectural changes. A third may be best at designing robust evaluations. When these roles are separated, the system gains a cleaner internal division between observation, hypothesis generation, and validation.

This structure also helps with safety and reliability. Self-improving systems are prone to reward hacking: they can find changes that inflate metrics without improving underlying capability. A dedicated critic or auditor can check whether a gain is real, whether it transfers across tasks, and whether it preserves required invariants such as tool safety, code correctness, or memory integrity.

In that sense, MARS is less a single architecture than a design pattern: improvement should emerge from structured internal debate, not just self-affirmation.

## Hyperagent Architectures: Making the Meta Layer Modifiable

Hyperagent architectures push one step further. They are motivated by a limitation in many self-improving systems: even when the task agent can change, the improvement mechanism itself is often fixed by human designers.

That creates a bottleneck. If the task-solving component improves but the mechanism that decides how to search, critique, or revise remains static, long-term progress is capped by the original meta-design.

A hyperagent removes that bottleneck by combining the task agent and the meta agent into a single self-referential program. The system can then modify:

- How it performs tasks
- How it evaluates those tasks
- How it proposes future changes
- How it stores and reuses knowledge about past changes

This is a more radical form of self-improvement because the procedure of improvement is itself subject to improvement. The architecture is no longer just optimizing a worker. It is optimizing the organization that designs the worker.

That matters outside coding. In software domains, there is often a convenient overlap between solving tasks and modifying the system that solves tasks. But in many other domains, those are different skills. Reviewing a paper, designing a robotics reward, and inventing a better self-critique mechanism are not the same task. Hyperagent architectures explicitly target that gap by allowing meta-level strategies to evolve rather than assuming they are fixed.

## Darwinian Search, Archives, and Stepping Stones

The most compelling self-improving systems borrow an idea from evolution: do not commit everything to a single incumbent. Keep an archive.

The Darwin Gödel Machine popularized this pattern in a practical form. Rather than demanding formal proof that a modification is beneficial, it accepts empirical validation. It generates self-modified descendants, evaluates them, and stores viable variants in an archive. Future search can branch from many earlier discoveries, not just the current best agent.

This archive is more than a history log. It is a search primitive.

Why does that matter? Because progress is often nonmonotonic. Some useful innovations look worse before they look better. A branch may temporarily reduce benchmark performance while introducing structure that later enables larger gains. If search only follows the current leader, those branches die too early.

Archive-based search preserves stepping stones:

- High performers can be exploited
- Diverse variants can be revisited
- Apparently weak branches can later produce strong descendants
- Improvement becomes population-based rather than purely greedy

CMP fits naturally into this picture because it values a branch's long-term potential. MARS fits because multiple agents can analyze the archive, compare experiments, and propose mutations. Hyperagents fit because archived systems can differ not just in task behavior but in how they generate future improvements.

Once you combine these ideas, a self-improving multi-agent system starts to look less like an assistant and more like an evolving lab.

## Comparing CMP, MARS, and Hyperagent Patterns

These approaches are complementary, but they emphasize different failure modes.

**CMP** addresses selection. It warns that immediate score is a poor proxy for long-run improvement potential. Use it when you are exploring many descendants and need a better signal for where to invest compute.

**MARS** addresses process. It structures improvement as a multi-agent research loop with explicit specialization, critique, and experimental validation. Use it when you need disciplined iteration and interpretable revision cycles.

**Hyperagents** address architectural limits. They make the meta-level itself modifiable, reducing dependence on a fixed human-designed improvement mechanism. Use them when you want adaptation that can generalize beyond domains where task-solving and self-modification happen to overlap.

A practical system can use all three:

- MARS-style agents generate and test revisions
- CMP-like signals guide which branches deserve more search
- Hyperagent design allows the revision process itself to evolve

That combination is much closer to open-ended improvement than any single static agent loop.

## What Makes These Systems Actually Work

The theory is interesting, but the engineering constraints are unforgiving. Self-improving multi-agent systems only work when four pieces are in place.

### 1. Reliable evaluation

If the benchmark is weak, the whole system learns the wrong lesson. Evaluation must check for transfer, robustness, and regressions, not just local score increases.

### 2. Traceable memory

The system needs a persistent record of changes, experiments, ancestry, and outcomes. Otherwise it repeats failed ideas and cannot identify why a branch succeeded.

### 3. Structured search

Random mutation is not enough. You need prioritization, branching logic, and selection pressure. Archives, lineage tracking, and CMP-like statistics are part of that.

### 4. Separation of roles

Generation, critique, execution, and acceptance should not all be controlled by the same internal voice. Multi-agent separation is often the simplest way to reduce self-confirming errors.

Without those ingredients, "self-improvement" usually degenerates into noisy prompt rewrites with unstable gains.

## Failure Modes: Drift, Gaming, and Coordination Cost

These systems are promising, but they are fragile.

One failure mode is **capability drift**. A change helps on the measured task but erodes general usefulness. Another is **reward hacking**. The system learns to satisfy the metric rather than the intent of the task. A third is **meta-overhead**: the coordination cost of many agents can exceed the value of the improvements they discover.

There is also a deeper risk. A self-improving architecture can accumulate complexity faster than humans can audit it. If the system rewrites its own prompts, tools, memories, and evaluation logic, you need strong constraints around what can be changed, how changes are tested, and when a branch is allowed to propagate.

At minimum, practical deployments need:

- Sandboxed execution
- Versioned archives
- Rollback paths
- Held-out evaluations
- Invariant checks for safety-critical behavior
- Human visibility into why changes were accepted

Open-ended search is powerful precisely because it can discover nonobvious solutions. That same property makes it risky if acceptance criteria are weak.

## Practical Design Principles for Builders

If you are building self-improving multi-agent systems today, the sensible approach is not to chase fully autonomous recursive self-improvement on day one. Start narrower.

Build a system that can improve one layer at a time. Let it revise prompts before code. Let it optimize workflows before tool permissions. Use archive-based comparison before open-ended mutation. Add specialized critic and evaluator roles before making the meta-controller itself editable.

A useful design sequence looks like this:

1. Start with strong task instrumentation and reproducible evaluation.
2. Add multi-agent revision loops for proposal, critique, and testing.
3. Track ancestry and archive all viable variants.
4. Introduce branch-level selection signals such as CMP-style lineage scoring.
5. Only then allow limited modification of the improvement process itself.

That path is slower, but it is technically honest. Most failures in this area come from skipping evaluation discipline and jumping straight to unconstrained self-editing.

## Where the Field Is Going Next

The field is moving away from the idea of a single monolithic agent and toward systems that behave more like adaptive organizations. The interesting question is no longer just whether an agent can solve a task. It is whether it can become better at discovering the next version of itself.

CMP sharpens our notion of what to optimize. MARS gives us a practical loop for structured internal research and revision. Hyperagent architectures point toward systems that can modify the very machinery of self-improvement. Taken together, they suggest a future in which multi-agent systems do not merely execute workflows. They accumulate methods, refine their own internal division of labor, and improve the process by which they improve.

The immediate takeaway is simple: if you want robust self-improving AI, do not only ask how well an agent performs today. Ask whether your architecture preserves stepping stones, supports internal critique, and can eventually revise the mechanism of revision itself.

That is the difference between a clever agent and an evolving one.

META: A practical guide to self-improving multi-agent systems, covering CMP, MARS, hyperagent architectures, and why lineage, critique, and archives matter.