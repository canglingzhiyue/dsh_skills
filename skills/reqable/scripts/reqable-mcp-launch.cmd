@echo off
rem ---------------------------------------------------------------------------
rem Reqable MCP launcher (used by cordis.patch.yml reverse-mcp-activator).
rem
rem Why this exists: the Reqable MCP server authenticates to the local API with
rem the env var REQABLE_TOKEN. Windows only propagates a NEW user-level variable
rem to processes started afterwards; restarting "dsh web" from a terminal that
rem predates the change keeps the stale environment, so the MCP server would
rem start with no token and every tool call would fail with
rem "Missing or invalid access token."
rem
rem Strategy: use the inherited value when present, otherwise read it from
rem HKCU\Environment at launch time. The token is never written to any file.
rem Usage: reqable-mcp-launch.cmd --scope all
rem ---------------------------------------------------------------------------
setlocal
if not defined REQABLE_TOKEN (
  for /f "usebackq tokens=3" %%A in (`reg query "HKCU\Environment" /v REQABLE_TOKEN 2^>nul ^| findstr /i "REQABLE_TOKEN"`) do set "REQABLE_TOKEN=%%A"
)
if not defined REQABLE_TOKEN (
  1>&2 echo [reqable-mcp-launch] REQABLE_TOKEN not found in process env nor HKCU\Environment
)
"D:\ProgramsDev\reqable\mcp-server.exe" %*