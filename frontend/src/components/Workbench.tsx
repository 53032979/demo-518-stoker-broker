export function Workbench() {
  return (
    <section className="workbench">
      <aside className="control-panel">
        <h2>策略配置</h2>
        <label>
          策略模板
          <select>
            <option>动量 Top N</option>
          </select>
        </label>
        <label>
          股票池
          <select>
            <option>沪深300</option>
          </select>
        </label>
        <button type="button">运行回测</button>
      </aside>
      <section className="result-panel">
        <h2>回测结果</h2>
        <div className="metric-grid">
          <div>总收益</div>
          <div>年化收益</div>
          <div>最大回撤</div>
          <div>夏普</div>
          <div>胜率</div>
        </div>
      </section>
    </section>
  );
}
