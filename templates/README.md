# Templates

Config presets for different installation profiles.

## Available profiles

- **quickstart**: Minimal prompts, optimized for AI-assisted setup
- **manual**: Full configuration wizard with explanations

## Adding a profile

Create a `.ini` or `.sh` file that exports variables consumed by install.sh:

```bash
# Example: templates/myprofile.sh
MODE="manual"
INSTALL_CONFIG=true
INSTALL_SKILLS=true
INSTALL_MCP=true
INSTALL_COMMANDS=true
INSTALL_LIBS=true
```
