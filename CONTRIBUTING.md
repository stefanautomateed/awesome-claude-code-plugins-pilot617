# Contributing

Thanks for your interest in contributing to Awesome Claude Code Plugins. This guide covers how to add a new plugin to the marketplace.

## Plugin Structure

Every plugin lives under `plugins/<plugin-name>/` and must include:

```
plugins/your-plugin/
├── .claude-plugin/
│   └── plugin.json        # Plugin manifest (required)
├── skills/
│   └── your-skill/
│       └── SKILL.md       # Skill definition
├── README.md              # Usage documentation (required)
└── ...                    # Any additional files your plugin needs
```

### plugin.json

```json
{
  "name": "your-plugin",
  "description": "One-line description of what it does",
  "version": "1.0.0"
}
```

### README.md

Your plugin README should include:
- What the plugin does and why it's useful
- Installation instructions
- Prerequisites (dependencies, credentials, etc.)
- Usage with real examples
- How it works (brief explanation of the approach)

## Quality Bar

We hold a high bar for plugins in this marketplace. Before submitting, check that your plugin:

- **Solves a real problem** — not a demo or proof of concept
- **Works out of the box** — minimal setup, sensible defaults
- **Handles different inputs gracefully** — doesn't assume a specific project structure or tech stack unless the plugin is explicitly scoped to one
- **Outputs to stdout by default** — only writes files when the user asks
- **Is well-documented** — a developer should be able to use it from the README alone

## Submitting a Plugin

1. Fork this repository
2. Create your plugin under `plugins/<plugin-name>/`
3. Add your plugin entry to `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "your-plugin",
     "source": "./plugins/your-plugin",
     "description": "One-line description",
     "version": "1.0.0",
     "keywords": ["relevant", "keywords"],
     "category": "category"
   }
   ```
4. Test it locally:
   ```shell
   /plugin marketplace add ./path/to/your/fork
   /plugin install your-plugin@awesome-claude-code-plugins
   ```
5. Open a PR with:
   - A clear description of what the plugin does
   - At least one real-world usage example
   - Confirmation that you tested it locally

## Updating an Existing Plugin

- Bump the `version` in both `plugin.json` and `marketplace.json`
- Update the README if behavior changed
- Keep changes backward-compatible when possible

## Code Style

- Keep plugin files minimal and focused
- Use `${CLAUDE_PLUGIN_ROOT}` for internal path references (plugins are copied to a cache on install)
- Don't reference files outside your plugin directory — they won't be available after install
- If your plugin includes scripts, make sure they're self-contained with no external dependencies beyond what's documented in prerequisites
