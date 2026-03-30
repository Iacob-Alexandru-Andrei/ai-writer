# Introduction {#sec:intro}

The automation of scientific discovery has progressed from hyperparameter optimization to full-stack research generation. Systems such as *The AI Scientist* [@lu2024aiscientist] produce papers end-to-end---ideating, implementing experiments, and writing---while self-improving coding agents [@zhang2025dgm; @robeyns2025selfimprovingcodingagent; @wang2025hgm] demonstrate that LLM-based agents can recursively modify their own codebases to improve on software engineering benchmarks. These two lines of work share an underexplored structural limitation: in both, the evaluation mechanism is static.

In automated science, the reviewer is a fixed LLM prompt [@lu2024aiscientist]. In self-improving coding agents, the evaluator is a frozen test suite [@zhang2025dgm]. Both setups create the same failure mode: once the generating agent exceeds the discriminative capacity of its evaluator, the feedback signal degrades to noise and improvement stalls. This introduces a *Frozen Critic* problem.

Recent work on self-improving coding agents has shown that even when the evaluator is fixed, the *strategy* for selecting which agent variants to explore matters profoundly. In particular, Clade-Metaproductivity ($\mathrm{CMP}$)---which measures the long-term improvement potential of an agent's lineage rather than its immediate performance---has proven to be a substantially better guide for tree-structured self-modification than greedy benchmark scores [@wang2025hgm]. This success motivates a natural question: *can similar principles guide the recursive improvement of multi-agent scientific systems, where the evaluation itself must co-evolve with the agents it evaluates?*

We answer affirmatively with the **Multi-Agent Recursive Scientist (MARS)**. In MARS, the unit of evolution is not a single coding agent but a *three-tuple*: a paper-writing scientist ($A_{\text{paper}}$), a scientific critic ($A_{\text{critic}}$), and a dual-role coding agent ($A_{\text{code}}$) that both executes experiments and implements mutations. These tuples form the nodes of a search tree that is grown and pruned by the same $\mathrm{CMP}$-guided Thompson sampling used for single-agent evolution, but with three key adaptations to the scientific setting:

First, the Frozen Critic problem demands that the evaluation target itself improve. Because the critic is part of the evolving tuple, its discriminative ability is subject to the same evolutionary pressure as the scientist's generative ability. The outer-loop evaluation---grounded in an immutable corpus of real and AI-generated papers---provides the fixed reference point, while the critic's *strategy for engaging with that corpus* evolves.

Second, multi-agent cooperation introduces a communication structure absent from single-agent settings. We introduce a *tiered mutability model* (Section [3.2](#sec:tiers){reference-type="ref" reference="sec:tiers"}) that distinguishes between the harness-level contracts that keep the system functional, the inter-agent communication protocols that govern cooperation, and the internal logic of each agent. Evolution operates freely on agent internals but may modify communication protocols only during coordinated whole-tuple mutations, preventing single-component changes from breaking inter-agent compatibility.

Third, the scientific setting demands richer feedback than pass/fail. We design a *structured feedback architecture* (Section [3.4](#sec:feedback){reference-type="ref" reference="sec:feedback"}) in which every agent interaction produces a reasoning trace and a meta-reflective self-assessment alongside its primary output. These traces are compiled into evidence bundles that provide the coding agent with *causal signal*---not just that a node scored poorly, but *why*---enabling a deliberation-before-implementation mutation protocol.

#### Contributions.

- We formalize the *Frozen Critic* problem in automated scientific discovery and introduce **MARS**, a recursively self-improving multi-agent system that addresses it by co-evolving a scientist, critic, and coder within a $\mathrm{CMP}$-guided search tree (Section [3](#sec:method){reference-type="ref" reference="sec:method"}).

- We prove that the $\mathrm{CMP}$ oracle guarantee extends to multi-agent tuples under a natural set of assumptions (Theorem [1](#thm:cmp_multiagent){reference-type="ref" reference="thm:cmp_multiagent"}).

- We introduce a tiered mutability model for multi-agent evolution, a structured feedback architecture with three communication channels, and a two-phase mutation protocol that separates diagnosis from implementation (Sections [3.2](#sec:tiers){reference-type="ref" reference="sec:tiers"}--[3.6](#sec:expansion){reference-type="ref" reference="sec:expansion"}).

- We design a ground-truth evaluation framework using three binary task types with configurable batching, preserving the Beta-Bernoulli structure required for $\mathrm{CMP}$ estimation (Section [3.5](#sec:outer_loop){reference-type="ref" reference="sec:outer_loop"}).

- We release an open benchmark, a curated evaluation dataset, and an evolutionary paper corpus annotated by tree depth and lineage (Section [6](#sec:releases){reference-type="ref" reference="sec:releases"}).

# Preliminaries {#sec:background}

#### Self-improvement as tree search.

We adopt the formulation of self-improvement as iterative tree search [@wang2025hgm]. Let $\mathcal{T}_t$ denote the archive of agents at iteration $t$, initialized as $\mathcal{T}_0 = \{a_0\}$. A policy $\pi$ selects at each step either an expansion action $m_a$ (producing a self-modified child of agent $a$) or an evaluation action $v_a$ (testing agent $a$ on a downstream task). The goal is to maximize $J(\pi) = \mathbb{E}[U(a_{\text{final}})]$, where $a_{\text{final}} = \arg\max_{a \in \mathcal{T}_B} \mathit{Score}_\pi(a)$ and $U$ measures downstream task performance.

#### Clade-Metaproductivity.

Let $C(\mathcal{T}, a)$ denote the clade of agent $a$---the subtree of $\mathcal{T}$ rooted at $a$. The Clade-Metaproductivity of $a$ under policy $\pi$ is $$\begin{equation}
\label{eq:cmp}
\mathrm{CMP}_\pi(\mathcal{T}, a) \;=\; \mathbb{E}_{\mathcal{T}_B \sim p_\pi(\cdot \mid \mathcal{T}, a)} \!\left[\max_{a' \in C(\mathcal{T}_B, a)} U(a')\right].
\end{equation}$$ $\mathrm{CMP}$ captures the long-term potential of the lineage rooted at $a$, aggregating descendant performance rather than relying on $a$'s immediate score. This is estimated by the clade-aggregated success ratio: $$\begin{equation}
\label{eq:cmp_hat}
\widehat{\mathrm{CMP}}(a) = \frac{n^C_\text{success}(a)}{n^C_\text{success}(a) + n^C_\text{failure}(a)}, \qquad \text{where } n^C_\text{success}(a) = \sum_{a' \in C(a)} n_\text{success}(a').
\end{equation}$$

#### Thompson sampling and scheduling.

Expansion and evaluation targets are selected via Thompson sampling over Beta posteriors, with an exploration--exploitation scheduler $\tau(t) = B/b$ (where $b$ is remaining budget) that flattens early and sharpens late. The expand-vs-evaluate decision follows UCB-Air [@NIPS200849ae49a2]: expand when $N_t^\alpha \geq |\mathcal{T}_t|$ for widening parameter $\alpha \in [0,1]$.

# The Recursive Scientist {#sec:method}

## Multi-Agent Nodes {#sec:nodes}

In MARS, each node in the search tree is a three-tuple $$\begin{equation}
\label{eq:node}
  N = (A_{\text{paper}},\; A_{\text{code}},\; A_{\text{critic}}).
\end{equation}$$ $A_{\text{paper}}$ generates hypotheses, designs experiments, and writes papers. $A_{\text{code}}$ executes experiments in a sandboxed environment and, during expansion, implements mutations to the tuple's codebase. $A_{\text{critic}}$ provides peer review during the inner loop and is evaluated against ground truth in the outer loop. All three share a common LLM backend and differ only in their system prompts, tool configurations, and scaffolding code---all of which are subject to evolution.

A child node inherits only the mutated source code and a one-time evidence summary from its parent. No chat histories, embedding caches, or accumulated state persist across generations, ensuring that evaluations reflect the quality of the *code* rather than accumulated context.

## Tiered Mutability {#sec:tiers}

Multi-agent evolution introduces a structural risk absent from the single-agent setting: a mutation to one agent's output format can silently break a downstream agent that depends on it. We address this with a tiered mutability model.

::: {#def:tiers .definition}
**Definition 1** (Interface Tiers).

- ***Tier 1 (Immutable):** Interfaces between the orchestrator and the agents. Enforced at runtime; violations trigger the exhaustion penalty (the node receives utility zero and is never expanded).*

- ***Tier 2 (Constrained evolution):** Inter-agent communication schemas. These have fixed required fields and extensible optional fields. Only whole-tuple mutations may modify Tier 2.*

- ***Tier 3 (Free evolution):** Agent internals---prompts, reasoning strategies, tool usage, helper functions. This is the primary mutation target.*
:::

The key constraint is that single-agent mutations operate exclusively within Tier 3 of the target agent, while Tier 2 changes---which reshape how agents communicate---require the coordinated whole-tuple mutation (Section [3.6](#sec:expansion){reference-type="ref" reference="sec:expansion"}). This mirrors the distinction between local mutations (common, low-risk) and structural rearrangements (rare, high-impact) in biological evolution.

## The Inner Loop: Time-Bounded Research {#sec:inner_loop}

For each node $N$, the agents execute a research workflow within a wall-clock budget $T_{\text{inner}}$. The workflow proceeds through ideation, experimentation, drafting, and iterative peer review, cycling through the review--revision loop as many times as the budget permits.

#### Ideation.

$A_{\text{paper}}$ generates an experiment specification: a testable hypothesis, expected outcome, and implementation instructions. On subsequent cycles, feedback from the most recent review is included.

#### Experimentation.

$A_{\text{code}}$ executes the specification inside a CPU-only container with a per-experiment timeout. The experimental domain is restricted to synthetic optimization landscapes (Rosenbrock, Rastrigin, and similar functions), ensuring tractability. Crucially, $A_{\text{code}}$ must produce a narrative interpretation of the execution---not merely a log dump---even on failure.

#### Drafting and review.

$A_{\text{paper}}$ synthesizes results into a paper draft accompanied by a mandatory self-assessment of its own uncertainties and evidence gaps. $A_{\text{critic}}$ reviews the draft and returns structured feedback: per-section scores with justifications, identified logical gaps, suggested revisions with priorities, a confidence estimate, and a full reasoning trace. $A_{\text{paper}}$ responds with a revision plan---documenting which suggestions it accepts, which it rejects, and why---before rewriting. This plan is a first-class artifact preserved for later use during expansion.

#### Calibration artifact.

The final draft is saved as a "Kin Fake"---an AI-generated paper produced by this node's agents, used to contextually prime $A_{\text{critic}}$ before the outer-loop evaluation.

## The Structured Feedback Architecture {#sec:feedback}

A core design principle of MARS is that *every agent interaction produces three communication channels*:

1.  **Primary output:** the deliverable (draft, experiment result, review score).

2.  **Reasoning trace:** a structured chain-of-thought explaining the output. When the critic assigns a score of 4/10, the trace identifies the specific passages, logical gaps, or missing evidence that led to that score.

3.  **Meta-reflection:** a self-assessment of confidence and known weaknesses. The critic might flag its own uncertainty about mathematical correctness; the paper agent might acknowledge that a claim rests on a single experimental seed.

This architecture serves two purposes. Within the inner loop, it enables targeted revision: the paper agent can address specific weaknesses rather than responding to opaque scores. Across generations, the accumulated traces provide the coding agent with *causal signal* for diagnosing systematic failures during expansion (Section [3.6](#sec:expansion){reference-type="ref" reference="sec:expansion"}).

## The Outer Loop: Ground-Truth Evaluation {#sec:outer_loop}

Node utility is derived from $A_{\text{critic}}$'s performance on a frozen evaluation dataset $D_{\text{eval}}$ containing class-balanced real ICLR papers (with ground-truth peer-review scores) and AI-generated papers.

#### Evaluation tasks.

Three task types produce binary outcomes:

::: center
  **Task**                    **Description**                                       **Outcome**
  --------------------------- ----------------------------------------------------- -----------------------------------------
  [Distinguish]{.smallcaps}   Classify a single paper as real or AI-generated       $\mathbb{1}[\hat{y} = y]$
  [Paired]{.smallcaps}        Given one real and one fake, identify the fake        $\mathbb{1}[\hat{y} = y]$
  [Score]{.smallcaps}         Predict a real paper's review score within $\delta$   $\mathbb{1}[|\hat{y} - y| \leq \delta]$
:::

The restriction to binary outcomes is deliberate: it preserves the Beta-Bernoulli conjugacy that underlies $\mathrm{CMP}$ estimation via [\[eq:cmp_hat\]](#eq:cmp_hat){reference-type="eqref" reference="eq:cmp_hat"}. Richer signals---the critic's reasoning traces, confidence, and error categories---are preserved alongside the binary outcome for use in evidence bundles but do not alter the Thompson sampling machinery.

#### Batched evaluation.

Each task type has an independent batch-size hyperparameter. A batch of $k$ tasks yielding $s$ successes updates counters as $n_\text{success} \mathrel{+}= s$, $n_\text{failure} \mathrel{+}= (k - s)$. This is equivalent to sequential updates because the Beta posterior is order-invariant for i.i.d. Bernoulli observations. Each batch counts as *one evaluation action* for the UCB-Air selection policy (incrementing $N_t$ by one, not by $k$), preserving the expansion--evaluation balance.

#### Node utility.

The scalar utility combines classification accuracy and score-prediction agreement: $$\begin{equation}
\label{eq:utility}
  U(N) = \lambda \cdot M_{\text{dist}} + (1 - \lambda) \cdot M_{\text{agree}},
\end{equation}$$ where $M_{\text{dist}} = \frac{1}{|D_{\text{cls}}|}\sum_{i \in D_{\text{cls}}} \mathbb{1}[\hat{y}^{(i)} = y^{(i)}]$ aggregates [Distinguish]{.smallcaps} and [Paired]{.smallcaps} tasks, and $$\begin{equation}
  M_{\text{agree}} = 1 - \frac{1}{S \cdot |D_{\text{score}}|} \sum_{j \in D_{\text{score}}} |\hat{y}^{(j)} - y^{(j)}|
\end{equation}$$ measures score-prediction quality on a scale of $S$ (default $S = 10$, $\lambda = 0.5$). For $\mathrm{CMP}$ counter updates, individual binary outcomes from each task are used directly; $U(N)$ is not fed into the Thompson sampling.

## Node Expansion and the Mutation Protocol {#sec:expansion}

#### Mutation target selection.

When the scheduler selects node $N$ for expansion, the harness draws a mutation target: $$\begin{equation}
\label{eq:mutation_probs}
  \mu \sim \text{Categorical}\!\left(\underbrace{\tfrac{1}{3}}_{A_{\text{paper}}},\; \underbrace{\tfrac{1}{3}}_{A_{\text{critic}}},\; \underbrace{\tfrac{1}{6}}_{A_{\text{code}}},\; \underbrace{\tfrac{1}{6}}_{\text{tuple}}\right).
\end{equation}$$ Single-agent targets ($A_{\text{paper}}$, $A_{\text{critic}}$, $A_{\text{code}}$) restrict the coding agent to Tier 3 modifications of the selected component. The whole-tuple target permits Tier 2 and Tier 3 modifications across all components, including inter-agent communication schemas.

The asymmetric allocation reflects structural considerations. The paper agent and critic are the primary cognitive components, meriting equal and largest share. The coding agent, as the mutation mechanism, has multiplicative leverage on all future mutations but is already indirectly refined through operation. Whole-tuple mutations carry the highest variance---they can reshape inter-agent dynamics---and are thus allocated the smallest share.

#### Two-phase protocol.

Mutations follow a diagnosis-then-implementation protocol controlled by a boolean hyperparameter (default: two separate LLM calls).

In **Phase A (Diagnosis)**, the coding agent receives a compiled evidence bundle---containing outer-loop evaluation traces with error categories, inner-loop review reports and revision plans, critic self-assessments, a compacted performance narrative, an AST-based codebase summary, and ancestor diff history (see Appendix [12](#app:evidence){reference-type="ref" reference="app:evidence"} for the full specification)---and produces a diagnosis: identified root causes, proposed changes ranked by priority with cited evidence, risk assessments, and expected impact.

In **Phase B (Implementation)**, the coding agent receives its own diagnosis and the repository workspace, then implements the highest-priority change. Post-mutation, the harness validates Tier 1 compliance; failure triggers the exhaustion penalty ($U = 0$, never expanded).

The separation is significant for two reasons. It produces an auditable causal chain from evidence to diagnosis to code change, which informs future mutations in descendant nodes. And it prevents the coding agent from making unjustified changes by forcing explicit reasoning before any edit.

#### Evidence compaction.

A single node's inner and outer loop artifacts can easily exceed 50K tokens. We compact evidence through a four-stage pipeline: AST-based codebase mapping, LLM-based trace summarization preserving systematic patterns, hierarchical ancestor compression (full diffs for the parent, summaries for grandparent and beyond), and token-budget enforcement with priority-based truncation (see Appendix [12.2](#app:compaction){reference-type="ref" reference="app:compaction"}).

# Theoretical Analysis {#sec:theory}

We now show that the $\mathrm{CMP}$ oracle guarantee extends to multi-agent tuples. The key observation is that the decision-theoretic framework underlying the Gödel Machine [@Schmidhuber:03gm] and its $\mathrm{CMP}$-based approximation [@wang2025hgm] is agnostic to the internal structure of nodes.

::: {#assumption:main .assumption}
**Assumption 1**. *We assume: (i) the objective depends only on the final selected tuple; (ii) evaluation uses repeatable trials---for any tuple--task pair, the expected outcome is independent of evaluation time or prior events; (iii) the proof mechanism does not consume budget; (iv) each self-modification costs exactly one budget unit.*
:::

::: {#thm:cmp_multiagent .theorem}
**Theorem 1**. *Under Assumption [1](#assumption:main){reference-type="ref" reference="assumption:main"}, access to a $\mathrm{CMP}$ oracle over multi-agent tuples is sufficient to implement the Gödel Machine in the MARS setting.*
:::

::: proof
*Proof.* We construct a Gödel POMDP whose state is $(\mathcal{T}, N_\text{parent}, N_\text{child}, b)$, where $\mathcal{T}$ is the tree of tuples, $N_\text{parent}$ and $N_\text{child}$ are distinguished tuples, and $b$ is the remaining budget. The observation space, action space (accept/reject), transitions, and scoring function are defined identically to the single-agent case in @wang2025hgm, with each "agent" $a$ replaced by a tuple $N$.

As in the single-agent proof, $\mathrm{CMP}_\pi$ adapted to this POMDP satisfies $$\begin{align}
\mathrm{CMP}_\pi\!\left((\mathcal{T}, N_p, N_c, b), N\right)
&= \mathbb{E}_{(\mathcal{T}_B, N_{Bp}, N_{Bc}, 0) \sim p_\pi}\!\left[U\!\left(\argmax_{N' \in C(\mathcal{T}_B, N)} \mathit{Score}_\pi(N_{Bp}, N_{Bc})(N')\right)\right] \nonumber \\
&= \mathbb{E}\!\left[U\!\left(\argmax_{N' \in \{N_{Bp}, N_{Bc}\}} \mathit{Score}_\pi(N_{Bp}, N_{Bc})(N')\right)\right] \label{eq:score_restrict} \\
&= Q_\pi\!\left((\mathcal{T}, N_p, N_c, b), N\right). \label{eq:q_equiv}
\end{align}$$ Equality [\[eq:score_restrict\]](#eq:score_restrict){reference-type="eqref" reference="eq:score_restrict"} holds because $\mathit{Score}_\pi$ is an indicator on one of the two observed tuples. Equality [\[eq:q_equiv\]](#eq:q_equiv){reference-type="eqref" reference="eq:q_equiv"} follows from unrolling the Q-value function. Access to $\mathrm{CMP}$ therefore provides the true Q-value, which suffices as a proof of improvement for the accept/reject decision. Optimality follows from the Bellman optimality equation. ◻
:::

::: remark
**Remark 1**. *Theorem [1](#thm:cmp_multiagent){reference-type="ref" reference="thm:cmp_multiagent"} does not depend on the internal structure of nodes---only on the fact that each node has a well-defined utility and can produce self-modifications. The multi-agent architecture affects the *distribution* of child utilities (and hence the quality of $\widehat{\mathrm{CMP}}$ as an estimator), but not the decision-theoretic framework itself.*
:::

::: remark
**Remark 2** (On the quality of $\widehat{\mathrm{CMP}}$ estimation). *The structured feedback architecture (Section [3.4](#sec:feedback){reference-type="ref" reference="sec:feedback"}) and two-phase mutation protocol (Section [3.6](#sec:expansion){reference-type="ref" reference="sec:expansion"}) are mechanisms for improving the *quality of mutations*, which in turn improves the distribution of child utilities and thereby the signal-to-noise ratio in $\widehat{\mathrm{CMP}}$ estimates. The estimation formula [\[eq:cmp_hat\]](#eq:cmp_hat){reference-type="eqref" reference="eq:cmp_hat"} itself remains unchanged.*
:::

# The MARS Algorithm {#sec:algorithm}

We now state the complete MARS procedure. The orchestrator operates in asynchronous mode: each available CPU runs either one evaluation action (possibly batched) or one expansion action, updating shared counters upon completion.

#### Selection policy.

At each scheduling decision, expand if $N_t^\alpha \geq |\mathcal{T}_t|$ and expandable parents exist; otherwise evaluate. Running expansions count toward $|\mathcal{T}_t|$ and running evaluations toward $N_t$.

#### Expansion policy.

Sample the parent for expansion via Thompson sampling over clade-aggregated counters: $$\begin{equation}
  N^* \sim \text{TS}\!\left(\left\{\left(\tau(1 + n^C_\text{s}(N)),\; \tau(1 + n^C_\text{f}(N))\right) \mid N \in \mathcal{T}_t\right\}\right).
\end{equation}$$

#### Evaluation policy.

Sample the node to evaluate via Thompson sampling over per-node counters: $$\begin{equation}
  N^* \sim \text{TS}\!\left(\left\{\left(\tau(1 + n_\text{s}(N)),\; \tau(1 + n_\text{f}(N))\right) \mid N \in \mathcal{T}_t\right\}\right).
\end{equation}$$ This favors higher-performing nodes, inducing a soft-max over clades that biases $\widehat{\mathrm{CMP}}$ toward an estimate of the clade maximum.

#### Final selection.

At budget exhaustion, return the node maximizing the $\epsilon$-percentile of the posterior: $\arg\max_{N \in \mathcal{T}_B} I_\epsilon(1 + n_\text{s}(N),\; 1 + n_\text{f}(N))$, where $I_\epsilon$ is the regularized incomplete beta function.

#### Initialization.

To avoid early-stage bias from asynchronous startup, the system expands the root node $K$ times in parallel (where $K$ is the number of workers) before beginning normal operation.

The full procedure is given in Algorithm [\[alg:mars\]](#alg:mars){reference-type="ref" reference="alg:mars"} (Appendix [9](#app:algorithm){reference-type="ref" reference="app:algorithm"}).

# Released Artifacts {#sec:releases}

We release three artifacts to support research on recursive scientific self-improvement.

#### The MARS Benchmark.

The complete codebase: orchestrator, tiered interface architecture, initial agent implementations, evidence compaction pipeline, and evaluation harness. The system is modular---researchers can substitute LLM backends, modify initial prompts, or introduce new task types while preserving the core guarantees.

#### The ICLR-vs-AI Evaluation Dataset.

A frozen, class-balanced dataset pairing real ICLR papers (with ground-truth review scores from OpenReview) and AI-generated papers from the Agents4Science corpus [@agents4science]. The dataset supports all three task types and is versioned for reproducibility.

#### The Evolutionary Paper Corpus.

A collection of machine-authored scientific papers generated at increasing evolutionary depth during MARS runs. Each paper is annotated with tree depth, node utility, the complete chain of mutation diffs from root, and inner-loop peer-review traces. This corpus provides a resource for studying how paper quality, structural patterns, and scientific reasoning evolve as the producing system recursively self-improves.

# Related Work {#sec:related}

#### Self-improving machines.

The concept of recursive self-improvement was articulated by @good1966speculations and first instantiated by @Schmidhuber1987EvolutionaryPI. The Gödel Machine [@Schmidhuber:03gm] provides the provably optimal framework. The Success-Story Algorithm [@schmidhuber1997shifting] enforces monotonic improvement via hindsight. Recent work operationalizes self-improvement through LLM-based coding agents: STOP [@zelikmanSelfTaughtOptimizerSTOP2024], DGM [@zhang2025dgm], SICA [@robeyns2025selfimprovingcodingagent], and HGM [@wang2025hgm]. MARS applies the tree-structured $\mathrm{CMP}$ framework, shown effective for coding agents, to the qualitatively different problem of multi-agent scientific discovery with co-evolving evaluation.

#### Automated scientific discovery.

The AI Scientist [@lu2024aiscientist] demonstrated end-to-end research automation but with a static reviewer. SciAgents [@ghafarollahi2024sciagents] and Agents4Science [@agents4science] extend the paradigm to multi-agent collaboration without recursive self-improvement. MARS introduces the co-evolutionary dynamic: the reviewer evolves alongside the scientist, driven by ground-truth anchoring rather than a fixed prompt.

#### Evolutionary agent design.

AlphaEvolve [@deepmind2025alphaevolve] evolves code via LLM-guided mutation. GPTSwarm [@zhuge2024gptswarm] optimizes communication graphs. MetaGPT [@hong2024metagpt] structures multi-agent software development. These systems optimize fixed objectives; MARS uniquely evolves both the optimization target (the critic) and the optimizer (the scientist) jointly.

#### AI content detection.

Detecting AI-generated text has progressed rapidly [@mitchell2023detectgpt; @kirchenbauer2023watermark], but existing detectors are static classifiers. MARS treats detection as a co-evolutionary signal: the critic's discriminative ability drives evolutionary pressure on both agents.

# Conclusion {#sec:conclusion}

We have presented MARS, a framework for recursively self-improving scientific agents that addresses the Frozen Critic problem by co-evolving a three-tuple of scientist, critic, and coder. The $\mathrm{CMP}$ oracle guarantee extends naturally to multi-agent tuples, grounding the search in the same theoretical framework that has proven effective for single-agent code evolution. The structured feedback architecture, tiered mutability model, and two-phase mutation protocol are mechanisms designed for the multi-agent scientific setting specifically: they ensure that the mutation engine receives causal signal, that evolution can reshape inter-agent communication without breaking single-agent mutations, and that every code change is preceded by explicit diagnosis.

The central question this work poses is not "how good is the AI scientist today?" but "how quickly can the AI scientist improve itself?"---which is precisely the quantity that $\mathrm{CMP}$ measures. The released benchmark, evaluation dataset, and evolutionary paper corpus are intended to make this question empirically tractable.

# Algorithm {#app:algorithm}

:::: algorithm
::: algorithmic
**Input:** Initial tuple $N_0 = (A^0_{\text{paper}}, A^0_{\text{code}}, A^0_{\text{critic}})$, widening $\alpha$, percentile $\epsilon$ Initialize tree $\mathcal{T}$ with root $N_0$; initialize counters for all $N \in \mathcal{T}$ **Expand:** Sample $S_C(N) \sim \text{Beta}(\tau(1 + n^C_\text{s}(N)),\; \tau(1 + n^C_\text{f}(N)))$ $N^* \leftarrow \arg\max_N S_C(N)$ Draw mutation target $\mu \sim \text{Categorical}(\nicefrac{1}{3}, \nicefrac{1}{3}, \nicefrac{1}{6}, \nicefrac{1}{6})$ Compile evidence bundle for $N^*$ with target $\mu$; compact to token budget $D \leftarrow A_\text{code}.\text{diagnose}(\text{evidence})$ // Phase A: Diagnosis $\Delta \leftarrow A_\text{code}.\text{implement}(D, \text{repo}, \mu)$ // Phase B: Implementation Add child $N_\text{child}$ to $\mathcal{T}$ as child of $N^*$ Add $N_\text{child}$ with $n_\text{f} = 1$ // Exhaustion penalty **Evaluate:** Sample $S(N) \sim \text{Beta}(\tau(1 + n_\text{s}(N)),\; \tau(1 + n_\text{f}(N)))$ $N^* \leftarrow \arg\max_N S(N)$ Run eval batch on $N^*$ $\to$ $s$ successes, $f$ failures $n_\text{s}(N^*) \mathrel{+}= s$; $n_\text{f}(N^*) \mathrel{+}= f$ Propagate to clade counters of $N^*$ and all ancestors **Return** $\arg\max_{N \in \mathcal{T}_B} I_\epsilon(1 + n_\text{s}(N),\; 1 + n_\text{f}(N))$
:::
::::

# Hyperparameters {#app:hyperparams}

::: {#tab:hyperparams}
  **Parameter**                       **Default**         **Description**
  ----------------------------------- ------------------- ---------------------------------------------------------------------------------------------------
  $\alpha$                            0.6                 UCB-Air widening parameter
  $\epsilon$                          1.0                 Percentile for final selection
  $\tau(t)$                           $B/b$               Exploration--exploitation scheduler
  $p_\text{paper}, p_\text{critic}$   $\nicefrac{1}{3}$   Mutation probability
  $p_\text{code}$                     $\nicefrac{1}{6}$   Mutation probability
  $p_\text{tuple}$                    $\nicefrac{1}{6}$   Mutation probability (Tier 2 permitted)
  `separate_diagnosis`                `True`              Two-phase mutation protocol
  $\delta$                            1.0                 [Score]{.smallcaps} task tolerance (1--10 scale)
  $\lambda$                           0.5                 Utility weighting in [\[eq:utility\]](#eq:utility){reference-type="eqref" reference="eq:utility"}
  $T_\text{inner}$                    3600 s              Inner-loop wall-clock budget
  Experiment timeout                  600 s               Per-experiment limit
  Expansion timeout                   1800 s              Per-expansion limit
  Max evidence tokens                 32 000              Evidence bundle token budget
  Batch sizes                         1 / 1 / 1           Per-task-type (distinguish / paired / score)

  : Complete hyperparameter reference.
:::

# Data Contracts and Agent Interfaces {#app:contracts}

All inter-component communication is mediated by typed data structures. Fields marked **R** are required (Tier 1, immutable); fields marked **O** are optional (Tier 2, evolvable during whole-tuple mutations only).

#### ExperimentSpec

(paper $\to$ code). **R:** hypothesis (str), expected_outcome (str), experiment_code_instructions (str). **O:** metadata (dict).

#### ExperimentResult

(code $\to$ paper). **R:** success (bool), metrics (dict), execution_log (str), execution_narrative (str). **R if failure:** traceback (str). **O:** metadata.

#### PaperDraft

. **R:** title (str), sections (list of heading--content pairs), raw_text (str). **O:** metadata.

#### DraftMeta

(paper self-assessment). **R:** uncertainty_areas (list\[str\]), evidence_gaps (list\[str\]), self_score (float), reasoning (str).

#### ReviewReport

(critic $\to$ paper). **R:** overall_score (float), per_section_scores (dict), justifications (dict), logical_gaps (list), factual_errors (list), suggested_revisions (list), confidence (float), reasoning_trace (str). **O:** metadata.

#### RevisionPlan

(paper response to review). **R:** accepted_suggestions (list), rejected_suggestions (list of {suggestion, reason}), planned_changes (list), reasoning (str).

#### EvalTrace

(outer loop, per instance). **R:** task_type (str), outcome (bool), critic_reasoning (str), critic_confidence (float), ground_truth_explanation (str). **O:** error_category (str), raw_prediction (float), time_taken_ms (int), metadata.

#### DiagnosisReport

(coding agent, Phase A). **R:** root_causes (list), proposed_changes (list of {change, rationale, risk, priority}), evidence_cited (list), expected_impact (str), reasoning_trace (str).

#### Agent protocols.

Each agent conforms to a runtime-checkable `Protocol`:

$A_\text{paper}$: `generate_spec`, `draft_paper`, `revise_paper`.

$A_\text{critic}$: `review_draft`, `evaluate_paper`, `evaluate_paper_batch`, `self_assess`.

$A_\text{code}$: `run_experiment` (experiment mode); `diagnose`, `implement_mutation` (expansion mode).

A mutation that causes any agent to fail protocol conformance on a smoke test triggers the exhaustion penalty.

# Evidence Bundle Construction and Compaction {#app:evidence}

## Evidence Bundle Contents {#app:evidence_contents}

The evidence bundle compiled for each expansion contains: (1) all `EvalTrace` objects from the outer loop, including error categories; (2) inner-loop `ReviewReport`s, `RevisionPlan`s, and `DraftMeta`s; (3) critic self-assessment reports; (4) a compacted performance narrative; (5) an AST-based codebase summary; (6) ancestor diff history (compacted).

The emphasis varies by mutation target: `ReviewReport`s and `RevisionPlan`s for paper mutations; `EvalTrace`s with error categories for critic mutations; `ExperimentResult`s for coding-agent mutations; all artifacts for whole-tuple mutations.

## Compaction Pipeline {#app:compaction}

**Stage 1: Codebase mapping.** An AST-based tool (e.g., tree-sitter or Aider's `repomap`) produces a structural summary, replacing full file contents.

**Stage 2: Trace summarization.** A dedicated LLM call summarizes inner-loop artifacts, preserving systematic patterns, the most informative individual examples, and quantitative trends.

**Stage 3: Hierarchical history.** Most recent parent: full diff + summarized evidence. Grandparent: summarized diff + key findings. Further ancestors: one-line summaries.

**Stage 4: Token budget.** The final bundle is truncated to a configurable limit (default 32K tokens). Truncation priority: ancestor history first, then inner-loop artifacts, then eval traces (highest priority, as they contain ground-truth signal).

# Cross-Loop Signal Flow {#app:signal_flow}

::: {#tab:signal_flow}
  **Artifact**                          **Producer**    **Consumer**   **Purpose**
  ----------------------------------- ---------------- --------------- -------------------------------------------
  ReviewReport.reasoning_trace         Critic (inner)   Code (expand)  Reveals evaluation biases
  RevisionPlan.rejected_suggestions    Paper (inner)    Code (expand)  Exposes communication failures
  EvalTrace.error_category             Critic (outer)   Code (expand)  Taxonomizes systematic failures
  DraftMeta.uncertainty_areas          Paper (inner)    Critic + Code  Directs attention; reveals self-awareness
  ExperimentResult.narrative            Code (inner)    Paper + Code   Grounds writing; reveals coding failures

  : Key cross-loop feedback artifacts.
:::

# Initial Agent Prompts {#app:prompts}

## Paper-Writing Agent

> You are an AI research scientist. Your job is to formulate hypotheses about optimization algorithms, design experiments to test them, interpret experimental results, and write clear scientific papers.
>
> When generating an experiment specification, produce a concrete, testable hypothesis with defined success criteria. When drafting, synthesize results with sections: abstract, introduction, methodology, results, discussion. When revising, first produce a revision plan before rewriting.
>
> Always articulate uncertainties. Document failures honestly. Never fabricate data.

## Critic Agent

> You are a scientific peer reviewer and AI-content detector.
>
> For peer review: evaluate rigor, clarity, reproducibility, novelty, logical consistency. For every section, provide a score (0-10) and a justification citing specific passages.
>
> For AI detection: look for inconsistent notation, unsupported claims, hallucinated references, uniform prose, overclaiming, missing practical details.
>
> Show full reasoning before answers. State confidence (0-1). Never give a score without justification.

## Coding Agent (Expansion Mode)

> You are a software engineer improving an AI research system.
>
> Phase 1 (Diagnosis): Analyze the evidence bundle. Identify root causes. Propose changes ranked by impact, citing specific evidence.
>
> Phase 2 (Implementation): Implement the highest-priority change. Make targeted, minimal edits. Run syntax checks.
>
> Only modify the designated target unless the target is \"tuple.\" Do not alter required interface fields. Justify every change with evidence.

# Codebase Organization {#app:codebase}

> mars/\
> config/ \# Hyperparameters\
> src/contracts/ \# Tier 1: types, protocols, validation\
> src/harness/ \# Orchestrator (immutable)\
> src/compaction/ \# Evidence pipeline\
> src/agents/ \# Initial implementations (evolvable)\
> src/eval/ \# Evaluation task generation\
> data/ \# Frozen corpora\
> containers/ \# Docker configs\
> tests/ \# Contract + integration tests