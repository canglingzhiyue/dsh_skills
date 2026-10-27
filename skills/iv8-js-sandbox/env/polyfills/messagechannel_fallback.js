/* MessageChannel 兜底实现（legacy）
 *
 * 适用：iv8 版本过老、MessageChannel 未内置，而目标 JS 依赖它做异步调度。
 *
 * 警告：先用 `probe_env.py` 确认 `typeof MessageChannel === "undefined"` 再加载。
 *       iv8 0.1.4 起已内置正确的 MessageChannel，本补丁会覆盖内置实现 ——
 *       在没有缺失的情况下加载，等于把正确实现换成近似实现，是净损失。
 */
(function () {
  if (typeof window.MessageChannel !== "undefined") {
    return; // 已内置，什么都不做
  }

  var wrap = window.__iv8__ && window.__iv8__.wrapNative;

  function MessageChannel() {
    var port1 = { onmessage: null };
    var port2 = { onmessage: null };

    function make(port, peer) {
      port.postMessage = function (data) {
        // 用宏任务投递，对齐规范里"异步、不递归"的语义
        setTimeout(function () {
          if (typeof peer.onmessage === "function") {
            peer.onmessage({ data: data });
          }
        }, 0);
      };
      port.start = function () {};
      port.close = function () {};
      return port;
    }

    make(port1, port2);
    make(port2, port1);

    return { port1: port1, port2: port2 };
  }

  if (wrap) {
    MessageChannel = wrap(MessageChannel, "MessageChannel");
  }
  window.MessageChannel = MessageChannel;
})();
