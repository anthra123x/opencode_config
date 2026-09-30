/**
 * Swarm Live Tester Plugin for OpenCode (V2)
 * Connects real-time testing, Sentinel certification, and agent metadata.
 */

export default {
  id: "opencode-live-tester",
  async setup(ctx: any) {
    const webPort = process.env.OPENCODE_WEB_PORT || "4040"
    const testerUrl = `http://127.0.0.1:${webPort}/#tester`

    if (ctx?.agent?.transform) {
      await ctx.agent.transform((editor: any) => {
        const qa = editor.get("qa-auditor")
        if (qa) {
          editor.update("qa-auditor", (agent: any) => {
            agent.description = `Specialized QA & Test Auditor. Real-time verification with swarm-tester. Live: ${testerUrl}`
          })
        }
      })
    }
  },
}
