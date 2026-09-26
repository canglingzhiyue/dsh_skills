# dsh-think-zh —— DSH 插件安装配方

| 项 | 值 |
|---|---|
| 类型 | **DSH 插件**（不是 skill） |
| 优先级 | P2 独立类 |
| 来源 | https://github.com/Len7183/DSH-Think-zh |
| 用途 | 强制模型思考（reasoning）用简体中文，回复跟随提问语言 |
| 本机记录日期 | 2026-09-12 |
| 本机解析到的 commit | `06a27f64218e7c9367d502fe0f7b90cb8e17ed7a` |

---

## 为什么插件要有自己的目录

插件不是"复制到 skill 根"就能用的东西：它要装进 **profile 的依赖**里，并由 profile 的 `bundles` 列表加载，
装完还必须**重启 DSH**。所以插件的"备份"= **安装配方 + profile 配置片段**，而不是文件副本。
本目录只放配方：`node_modules` 里的构建产物可以重装，不入备份。

## 安装

前置：`dsh plugin` 只是 pnpm 的转发器，机器上必须有 pnpm（`pnpm -v` 能跑；没有就 `npm install -g pnpm`）。

```powershell
dsh plugin --profile web add github:Len7183/DSH-Think-zh
```

第一次会失败，报 `ERR_PNPM_GIT_DEP_PREPARE_NOT_ALLOWED`：pnpm 默认拦截 git 依赖的 prepare 脚本，
而这个插件要在 prepare 里跑 `tsc` 构建。把下面这个键加到
`~/.dsh/profiles/web/pnpm-workspace.yaml` 的 `allowBuilds:` 下，再重跑上面的命令：

```yaml
allowBuilds:
  "dsh-think-zh@https://codeload.github.com/Len7183/DSH-Think-zh/tar.gz/06a27f64218e7c9367d502fe0f7b90cb8e17ed7a": true
```

> 键里带 `@` `:` `/`，**必须加引号**；键中的 commit 是 pnpm 解析出的版本。
> 想锁定同一个版本，安装 spec 写成 `github:Len7183/DSH-Think-zh#06a27f64218e7c9367d502fe0f7b90cb8e17ed7a`。

## 装完应该长成什么样

`~/.dsh/profiles/web/package.json`：

```json
{
  "dsh": {
    "profile": {
      "bundles": ["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app", "dsh-think-zh"],
      "patchReload": "live"
    }
  },
  "dependencies": {
    "dsh-think-zh": "github:Len7183/DSH-Think-zh"
  }
}
```

`bundles` 末尾那一条由 dsh 在安装后自动 reconcile，不用手改；但**核对时以它为准** ——
少了它，插件不会加载。

## 验证

```powershell
dsh --profile web --dump-config | Select-String 'dsh-think-zh' -Context 0,4
```

输出末尾应出现 `# == dsh-think-zh` 段落（含 `inject: [systemPrompt]`）。
**必须重启 DSH**（重开 `dsh web`）：bundle 层在 profile 启动时组合，运行中的进程不会热加载这个插件。

## 可调配置

在 `~/.dsh/profiles/web/cordis.patch.yml` 里给对应行加 `config:`：
`injectPrompt: false` 关掉注入，`injectionText: ...` 换成自定义指令文本。

## 卸载

```powershell
dsh plugin --profile web remove dsh-think-zh
```

然后重启 DSH（bundle 列表会自动更新）。

## 小坑

`dsh --dump-config` 会重写 profile 里的 `cordis.yml`；在沙箱里跑会因写 profile 目录被拒，
需要放宽到 danger-full-access 再跑。
