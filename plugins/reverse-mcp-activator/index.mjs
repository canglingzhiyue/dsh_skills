/**
 * reverse-mcp-activator —— 让逆向模式的 MCP 服务器"随会话按需启动"。
 *
 * ## 为什么需要它
 *
 * DSH 0.2.0 起，agent preset registry 在**启动期就急切挂载**所有已声明 preset
 * （`AgentPresetRegistry.activate()` → `mountPreset()`），所以写在 preset 里的
 * `dsh-mcp-client` 行会随 `dsh web` 一起把服务器全部拉起 —— rc.6 时代
 * "读文件不挂载、新会话选中才 compose"的惰性语义已经不存在了。
 *
 * 后果：启动被拖慢（IDA 的 uvx 在无代理时反复重试 PyPI，实测 6×~17s），
 * 且 5 个服务器常驻（9~13 个进程、约 300 MB）—— 正是 2026-10-02 那次迁移要避免的。
 *
 * ## 它怎么工作
 *
 * 不在 composition 里声明 MCP 行（那样必然被急切挂载），改为在本插件里按需挂载：
 *
 *   1. 插件挂在 **host 层**（profile patch 的一行），启动时只加载自身，不碰任何 MCP；
 *   2. 监听 `agent/created` —— 该事件是 serial 且被 await（AgentLoop 会 hold 住排队输入
 *      直到所有监听器结束），所以逆向会话的第一条消息就能看到工具；
 *   3. 用 registry 的 `composedPreset(agent.ctx)` 判断这个会话是不是目标 preset；
 *   4. 是 → 对 `agent.ctx` 调 `ctx.plugin(McpClient, server)`，把 MCP 客户端挂到
 *      **该会话自己的作用域**上。`ToolRuntime.register()` 依据调用方 ctx 的 scope 落层，
 *      所以工具只进这个会话的 scope 层：普通会话看不到 `mcp__*`；会话销毁时作用域随之
 *      下沉，MCP 进程一起退出（不再跨会话常驻）。
 *
 * ## 超时与降级
 *
 * 慢的服务器（camoufox 冷启动、IDA 的 uvx 解析）不阻塞会话创建：挂载并发进行，
 * `startupTimeoutMs` 之后监听器放行，未就绪的留在后台继续；每个服务器配置都用
 * `failOnStartupError: false`，连不上只是静默少工具。想完全等齐就把超时调大。
 *
 * ## 插件形式（踩过的坑）
 *
 * - **函数式插件**而不是类：DSH 内置类插件走 `[Service.init]` 生成器（见
 *   `@deepseek-ai/dsh-agent-preset`），而本文件在 `$DSH_HOME\plugins\` 下解析不到
 *   `@deepseek-ai/cordis`，拿不到那个 symbol。实测：类的 `apply()` **不会被调用**。
 * - **用 `ctx.inject()` 而不是模块级 `export const inject`**：后者在本 loader 下不生效，
 *   `ctx.tools` 属性访问会抛 "cannot get property tools without inject"
 *   （`ctx.get()` 因为绕过 inject 检查而"看起来能用"，容易误判）。
 *
 * ## 解析
 *
 * 插件自身位置解析不到 `@deepseek-ai/*`（那些包在 DSH 安装目录里），所以借 profile
 * 目录做 `createRequire` 解析根，再按绝对 URL 动态 import —— 见 `loadClient()`。
 */

import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import { join } from 'node:path'
import { homedir } from 'node:os'

const DEFAULT_TIMEOUT_MS = 15000

export const name = 'reverse-mcp-activator'

export default function reverseMcpActivator(ctx, config) {
  const settings = config ?? {}
  const targetPreset = String(settings.presetId ?? 'reverse')
  const servers = Array.isArray(settings.servers) ? settings.servers : []
  const timeoutMs = Number(settings.startupTimeoutMs ?? DEFAULT_TIMEOUT_MS)
  if (servers.length === 0) {
    ctx.logger.warn('reverse-mcp-activator: config.servers 为空，不做任何事')
    return
  }

  /** 已处理过的 agent（WeakSet 不阻止回收），避免重复挂载。 */
  const bound = new WeakSet()
  let clientPromise

  /**
   * 解析并载入 `@deepseek-ai/dsh-mcp-client`。
   *
   * 以 profile 目录为解析根（`createRequire`），因为 DSH 的包不在本插件目录的
   * 解析路径上。profile 名可用 `config.profileName` 覆盖，默认 `web`。
   */
  const loadClient = () => {
    clientPromise ??= (async () => {
      const home = process.env.DSH_HOME || join(homedir(), '.dsh')
      const profileDir = join(home, 'profiles', String(settings.profileName ?? 'web'))
      const require = createRequire(join(profileDir, 'package.json'))
      const entry = require.resolve('@deepseek-ai/dsh-mcp-client')
      const mod = await import(pathToFileURL(entry).href)
      return mod.default ?? mod
    })()
    return clientPromise
  }

  ctx.inject(['agentPresets'], (scoped) => {
    scoped.on('agent/created', async ({ agent }) => {
      let current
      try {
        current = scoped.agentPresets?.composedPreset?.(agent.ctx)
      } catch {
        return
      }
      if (current !== targetPreset) return
      if (bound.has(agent)) return
      bound.add(agent)

      let McpClient
      try {
        McpClient = await loadClient()
      } catch (error) {
        scoped.logger.warn(`reverse-mcp-activator: 无法载入 @deepseek-ai/dsh-mcp-client：${error?.message ?? error}`)
        return
      }

      const fibers = []
      for (const server of servers) {
        try {
          fibers.push(agent.ctx.plugin(McpClient, server))
        } catch (error) {
          scoped.logger.warn(`reverse-mcp-activator: 挂载 ${server?.serverName ?? '?'} 失败：${error?.message ?? error}`)
        }
      }
      if (fibers.length === 0) return

      scoped.logger.info(`reverse-mcp-activator: preset「${targetPreset}」会话，按需挂载 ${fibers.length} 个 MCP 服务器`)
      const settled = Promise.allSettled(fibers.map((fiber) => fiber.await()))
      const timer = new Promise((resolve) => {
        const handle = setTimeout(resolve, timeoutMs)
        handle.unref?.()
      })
      await Promise.race([settled, timer])
      scoped.logger.info('reverse-mcp-activator: MCP 挂载结束（未就绪的留在后台继续）')
    })
  })
}
