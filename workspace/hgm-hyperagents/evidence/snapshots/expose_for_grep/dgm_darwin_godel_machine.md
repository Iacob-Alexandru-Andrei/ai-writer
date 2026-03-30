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
