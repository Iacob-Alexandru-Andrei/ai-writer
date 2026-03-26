# ai-writer

A writing system that leverages Claude Code and Codex for structured document generation, research synthesis, and iterative refinement.

## Features

- **Structured Workflows**: Define multi-stage writing pipelines via YAML configs
- **Claude Code Integration**: Slash commands for drafting, reviewing, and refining documents
- **Research Support**: BibTeX parsing and citation management
- **Extensible**: Plugin-based integrations for additional NLP tools and knowledge sources

## Installation

### Basic install

```bash
cd ai-writer
pip install -e .
```

### With all optional dependencies

```bash
pip install -e ".[all]"
```

### With NLP tools (spaCy)

```bash
pip install -e ".[nlp]"
```

### Install Claude Code slash commands

After installing the package, run the command installer to register slash commands:

```bash
python scripts/install_claude_commands.py
```

This symlinks all `.md` files from `commands/` into `~/.claude/commands/`, making them available as slash commands in any Claude Code session.

To remove the installed commands:

```bash
python scripts/install_claude_commands.py --uninstall
```

## Project Structure

```
ai-writer/
├── lib/writing/            # Main package
│   ├── integrations/       # External service integrations
│   └── workflows/          # Writing pipeline definitions
├── config/                 # YAML configuration files
├── templates/              # Prompt templates
├── commands/               # Claude Code slash command definitions (.md)
├── scripts/                # Utility scripts
└── tests/                  # Test suite
    ├── integration/        # Integration tests
    └── fixtures/           # Test data and fixtures
```

## Usage

Slash commands (installed via `scripts/install_claude_commands.py`) provide the primary interface. Once installed, use them inside any Claude Code session:

- Commands are defined as `.md` files in the `commands/` directory
- Each command specifies a structured workflow for a particular writing task
- Workflows can chain multiple stages: research, outline, draft, review, revise

## Configuration

Place YAML config files in `config/` to customize:

- Model parameters and provider settings
- Output formatting preferences
- Citation style defaults
- Workflow stage definitions

## License

MIT License. See [LICENSE](LICENSE) for details.
