# Huxley-Gödel Machine: Human-Level Coding Agent Development by an Approximation of the Optimal Self-Improving Machine

Wenyi Wang, Piotr Piękos, Li Nanbo, Firas Laakom, Yimeng Chen, Mateusz Ostaszewski, Mingchen Zhuge, Jürgen Schmidhuber

King Abdullah University of Science and Technology (KAUST)

## Abstract

Recent work operationalizes self-improvement through coding agents that modify their own codebases. These systems grow trees of self-modifications guided by software engineering benchmark performance, assuming higher scores predict better future iterations. However, we identify a critical gap: an agent's immediate performance doesn't reliably indicate its capacity for productive self-improvement, which we term the "Metaproductivity-Performance Mismatch."

We introduce Clade-Metaproductivity (CMP), a metric aggregating descendant performance rather than evaluating individual agents. This concept, inspired by evolutionary biology's notion of clades as ancestral lineages, measures an agent's self-improvement potential. We prove that access to true CMP suffices to simulate Gödel Machines under specific assumptions about our problem setting.

We propose the Huxley-Gödel Machine (HGM), which estimates CMP and uses Thompson sampling to guide tree search. Experiments on SWE-bench Verified and Polyglot show HGM outperforms prior methods (DGM and SICA) while using substantially fewer CPU hours. Remarkably, an agent optimized on SWE-bench Verified with GPT-5-mini achieves human-level performance matching top human-engineered solutions when evaluated on SWE-bench Lite with GPT-5.

## Introduction

The automation of software engineering has progressed from simple auto-completion to sophisticated coding agents capable of solving complex real-world tasks. A particularly exciting frontier is self-improving coding agents---systems that modify their own codebases to enhance their capabilities. These systems grow search trees of self-modifications, where each node represents an agent variant and edges represent mutation operations.

The prevailing approach evaluates agent variants using benchmark scores and selects the best performers for further modification. This greedy strategy assumes that higher immediate performance predicts greater capacity for productive self-improvement. We challenge this assumption with a key observation: benchmark scores alone do not reliably indicate an agent's long-term potential for self-improvement.

We formalize this as the Metaproductivity-Performance Mismatch: a high-scoring agent may produce unproductive descendants, while a lower-scoring one seeds lineages that achieve greater long-term gains. This mismatch arises because immediate benchmark performance captures task-solving ability but not the agent's capacity to generate productive mutations.

To address this, we introduce Clade-Metaproductivity (CMP), inspired by evolutionary biology's clade concept. CMP measures the expected maximum utility achievable within an agent's entire descendant lineage, capturing the long-term improvement potential of an evolutionary branch rather than a single individual. We prove that access to true CMP values is sufficient to implement the accept/reject decisions of a Gödel Machine---the provably optimal self-improving system---within our problem setting.

## Self-Improvement as Tree-Search

We formalize self-improving agent development as an iterative tree search problem. Let $\mathcal{T}_t$ denote the tree (archive) of agents at iteration $t$, initialized as $\mathcal{T}_0 = \{a_0\}$ where $a_0$ is the initial agent. At each step, a policy $\pi$ selects either:

- An expansion action $m_a$: produce a self-modified child of agent $a$
- An evaluation action $v_a$: test agent $a$ on a downstream task

The objective is to maximize $J(\pi) = \mathbb{E}[U(a_{\text{final}})]$, where $a_{\text{final}} = \arg\max_{a \in \mathcal{T}_B} \mathit{Score}_\pi(a)$ at budget exhaustion $B$, and $U$ measures downstream task performance.

### Clade-Metaproductivity

Let $C(\mathcal{T}, a)$ denote the clade of agent $a$---the subtree of $\mathcal{T}$ rooted at $a$. The Clade-Metaproductivity of $a$ under policy $\pi$ is:

$$\mathrm{CMP}_\pi(\mathcal{T}, a) = \mathbb{E}_{\mathcal{T}_B \sim p_\pi(\cdot \mid \mathcal{T}, a)}\left[\max_{a' \in C(\mathcal{T}_B, a)} U(a')\right]$$

CMP captures the long-term potential of the lineage rooted at $a$, aggregating descendant performance rather than relying on $a$'s immediate score. This is estimated by the clade-aggregated success ratio:

$$\widehat{\mathrm{CMP}}(a) = \frac{n^C_\text{success}(a)}{n^C_\text{success}(a) + n^C_\text{failure}(a)}$$

where $n^C_\text{success}(a) = \sum_{a' \in C(a)} n_\text{success}(a')$.

### Thompson Sampling and Scheduling

Expansion and evaluation targets are selected via Thompson sampling over Beta posteriors. The exploration-exploitation scheduler $\tau(t) = B/b$ (where $b$ is remaining budget) flattens the posterior early in the run (encouraging exploration) and sharpens it late (encouraging exploitation of the best-performing lineages).

The expand-vs-evaluate decision follows UCB-Air: expand when $N_t^\alpha \geq |\mathcal{T}_t|$ for widening parameter $\alpha \in [0,1]$.

## Huxley-Gödel Machine

The HGM instantiates the CMP-guided tree search framework. It separates the expansion policy (which parent to mutate) from the evaluation policy (which agent to test), using Thompson sampling over clade-aggregated counters for expansion and per-node counters for evaluation.

### Expansion Policy

For expansion, sample the parent via Thompson sampling:
$$a^* \sim \text{TS}\left(\left\{\left(\tau(1 + n^C_s(a)), \tau(1 + n^C_f(a))\right) \mid a \in \mathcal{T}_t\right\}\right)$$

### Evaluation Policy

For evaluation, sample the node to test:
$$a^* \sim \text{TS}\left(\left\{\left(\tau(1 + n_s(a)), \tau(1 + n_f(a))\right) \mid a \in \mathcal{T}_t\right\}\right)$$

### Final Selection

At budget exhaustion, return the agent maximizing the $\epsilon$-percentile of the posterior:
$$\arg\max_{a \in \mathcal{T}_B} I_\epsilon(1 + n_s(a), 1 + n_f(a))$$

### Asynchronous Implementation

HGM operates asynchronously: multiple CPU workers run expansion and evaluation tasks in parallel. Running expansions count toward $|\mathcal{T}_t|$ and running evaluations toward $N_t$, ensuring the UCB-Air condition accounts for in-progress work.

## Theoretical Analysis

We prove that access to a CMP oracle is sufficient to implement the Gödel Machine's accept/reject decisions.

**Theorem (CMP Oracle Guarantee).** Under assumptions of (i) objective depending only on the final selected agent, (ii) repeatable evaluation trials, (iii) proof mechanism not consuming budget, and (iv) each self-modification costing exactly one budget unit: access to a CMP oracle is sufficient to implement the Gödel Machine.

The proof constructs a Gödel POMDP whose state is $(\mathcal{T}, a_p, a_c, b)$ and shows that CMP equals the Q-value function, providing the true action-value needed for optimal accept/reject decisions.

## Experimental Results

### CMP Correlation Analysis

We empirically validate that CMP correlates more strongly with long-term improvement potential than immediate benchmark performance. Across multiple experimental runs, agents selected by CMP produce lineages with higher maximum utility than agents selected by immediate performance.

### Self-Improvement Effectiveness

On SWE-bench Verified, HGM agents improve from baseline performance to human-level, matching established baselines like Agentless, Moatless, and SWE-agent while using substantially fewer computational resources. On Polyglot, HGM demonstrates consistent improvement across iterations.

### Generalization

HGM-discovered agents transfer across:
- LLM scales (GPT-5-mini to GPT-5)
- Benchmarks (SWE-bench to Polyglot and vice versa)
- Programming languages (Python-trained agents improve on non-Python tasks)

## Conclusion

We have identified the Metaproductivity-Performance Mismatch in self-improving coding agents and proposed Clade-Metaproductivity as a theoretically grounded metric for guiding tree-structured self-modification. The Huxley-Gödel Machine, which estimates CMP via Thompson sampling, achieves human-level performance on SWE-bench while using fewer resources than prior methods. The theoretical connection to Gödel Machines provides a principled foundation for self-improving systems.
