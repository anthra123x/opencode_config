/**
 * Team HUD Plugin for OpenCode
 * Adds multi-agent team swarm branding, terminal title hooks,
 * and session greeting with stylized typography.
 */

export default async function teamHudPlugin({ project, directory }: any) {
  const projName = project || (directory ? directory.split("/").pop() : "Workspace");

  // Set terminal title via ANSI OSC sequence
  if (process.stdout && process.stdout.isTTY) {
    process.stdout.write(`\x1b]0;⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ] — ${projName}\x07`);
  }

  // Visual banner with stylized typography
  const C_PURPLE = "\x1b[38;5;141m";
  const C_CYAN   = "\x1b[38;5;51m";
  const C_GREEN  = "\x1b[38;5;48m";
  const C_BOLD   = "\x1b[1m";
  const C_DIM    = "\x1b[2m";
  const C_RESET  = "\x1b[0m";

  console.log(
    `\n${C_PURPLE}${C_BOLD}╭──────────────────────────────────────────────────────────────╮${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫ v2.0                          │${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_CYAN}🛡️  Multi-Agent Architecture & Persistent Context Memory     ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}├──────────────────────────────────────────────────────────────┤${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_RESET}Project: ${C_GREEN}${projName.padEnd(20)}${C_RESET} ${C_DIM}Status: Swarm Active${C_RESET}       ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_DIM}Team:${C_RESET} @orchestrator · @backend · @frontend · @git-flow    ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│        @qa-auditor · @devops                                 ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}╰──────────────────────────────────────────────────────────────╯${C_RESET}\n`
  );

  return {
    config: (cfg: any) => {
      if (cfg && !cfg.default_agent) {
        cfg.default_agent = "orchestrator";
      }
    }
  };
}
