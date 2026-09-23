/**
 * Team HUD Plugin for OpenCode
 * Adds multi-agent team swarm branding, per-project dedicated web session discovery,
 * and live monitoring links in OpenCode's central tips interface.
 */

export default async function teamHudPlugin({ project, directory }: any) {
  const projDir = String(directory || (project?.worktree || process.cwd()));
  const rawName = (typeof project === "string" ? project : (project?.worktree || project?.name || project?.id)) ||
                  (projDir ? projDir.split("/").filter(Boolean).pop() : "Workspace");
  const projName = String(rawName);

  // Set terminal title via ANSI OSC sequence
  if (process.stdout && process.stdout.isTTY) {
    process.stdout.write(`\x1b]0;⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ] — ${projName}\x07`);
  }

  // Visual banner colors
  const C_PURPLE = "\x1b[38;5;141m";
  const C_CYAN   = "\x1b[38;5;51m";
  const C_GREEN  = "\x1b[38;5;48m";
  const C_BOLD   = "\x1b[1m";
  const C_DIM    = "\x1b[2m";
  const C_RESET  = "\x1b[0m";
  const C_YELLOW = "\x1b[38;5;220m";
  const C_BLUE   = "\x1b[38;5;75m";

  // Determine dedicated port for this project
  let webPort = process.env.OPENCODE_WEB_PORT || "4040";

  try {
    const { execFileSync } = await import("child_process");
    const path = await import("path");
    const os = await import("os");
    const fs = await import("fs");

    const possiblePaths = [
      path.join(os.homedir(), ".config", "opencode", "web", "server.py"),
      path.join(__dirname, "..", "web", "server.py"),
      "/home/omicron/Documentos/opencodeconfig/web/server.py"
    ];

    let srvPath = "";
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        srvPath = p;
        break;
      }
    }

    if (srvPath) {
      const out = execFileSync("python3", [srvPath, "--ensure", "--dir", projDir, "--project", projName], {
        encoding: "utf8",
        timeout: 2500
      }).trim();
      if (out && !isNaN(Number(out))) {
        webPort = out;
      }
    }
  } catch (_) {}

  process.env.OPENCODE_WEB_PORT = webPort;
  process.env.OPENCODE_WEB_URL = `http://localhost:${webPort}`;

  const webUrl = `http://localhost:${webPort}`;
  const brainUrl = `${webUrl}/#brain`;

  // Stylized welcome banner
  console.log(
    `\n${C_PURPLE}${C_BOLD}╭──────────────────────────────────────────────────────────────╮${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫ v2.0                          │${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_CYAN}🛡️  Multi-Agent Architecture & Persistent Context Memory     ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}├──────────────────────────────────────────────────────────────┤${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_RESET}Project: ${C_GREEN}${projName.padEnd(20)}${C_RESET} ${C_DIM}Status: Swarm Active${C_RESET}       ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_DIM}Team:${C_RESET} @orchestrator · @backend · @frontend · @git-flow    ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│        @qa-auditor · @devops                                 ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}├──────────────────────────────────────────────────────────────┤${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_YELLOW}💡 Tip: Servidor de Monitoreo & GetBrain Activo             ${C_PURPLE}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_RESET}Monitorear flujo de trabajo: ${C_BLUE}${C_BOLD}${webUrl.padEnd(27)}${C_RESET}${C_PURPLE}${C_BOLD}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}│  ${C_RESET}Visualizar grafo GetBrain:   ${C_BLUE}${C_BOLD}${brainUrl.padEnd(27)}${C_RESET}${C_PURPLE}${C_BOLD}│${C_RESET}\n` +
    `${C_PURPLE}${C_BOLD}╰──────────────────────────────────────────────────────────────╯${C_RESET}\n`
  );

  return {
    config: (cfg: any) => {
      if (cfg && !cfg.default_agent) {
        cfg.default_agent = "orchestrator";
      }
      if (cfg && cfg.agent && cfg.agent.orchestrator) {
        cfg.agent.orchestrator.description = `Team Lead & Orchestrator. Monitoreo: ${webUrl} | GetBrain: ${brainUrl}`;
      }
    }
  };
}
