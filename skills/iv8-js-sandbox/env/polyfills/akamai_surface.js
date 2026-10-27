/* Akamai 相关全局位点补丁
 *
 * 只做一件事：让 Akamai 脚本在探测其自有全局命名空间时，
 * 拿到的类型/形状与真实浏览器一致，避免"未定义"直接触发异常分支。
 *
 * 明确不做的事（做了反而更容易被打）：
 *   - 不伪造 _abck / bm_sz 的值。它们是服务端下发并在多次请求间累积的，
 *     在客户端凭空造一个只会让服务端校验失败。
 *   - 不伪造 sensor_data 的时序与轨迹。那部分必须由 Python 侧真实驱动
 *     （见 references/akamai.md）。
 */
(function () {
  var win = window;

  // 部分站的 Akamai 脚本会在 window 上挂自己的命名空间并读写它
  if (typeof win.Akamai === "undefined") {
    win.Akamai = {};
  }

  // bmak 命名空间：脚本可能写入 bmak.sensor_data 等
  if (typeof win.bmak === "undefined") {
    win.bmak = {};
  }

  // 少数版本会探测下面这个函数是否可调用
  if (typeof win.bmak === "object" && typeof win.bmak.ak === "undefined") {
    win.bmak.ak = {};
  }
})();
