import { PackagePlus, Plus } from 'lucide-react'

import type { InventoryItem } from '../api/types'

interface InventoryPanelProps {
  items: InventoryItem[]
  onCreate: () => void
  onInbound: (itemId: string) => void
  busy: boolean
}

export function InventoryPanel({ items, onCreate, onInbound, busy }: InventoryPanelProps) {
  return (
    <section className="panel inventory-panel" aria-label="库存">
      <div className="panel-heading">
        <h2>库存</h2>
        <button className="icon-button" type="button" title="新增物资" onClick={onCreate} disabled={busy}>
          <Plus aria-hidden="true" size={18} />
        </button>
      </div>
      <div className="inventory-table" role="table">
        <div className="table-row table-head" role="row">
          <span role="columnheader">物资</span>
          <span role="columnheader">类别</span>
          <span role="columnheader">数量</span>
          <span role="columnheader">库位</span>
          <span role="columnheader">操作</span>
        </div>
        {items.map((item) => (
          <div className="table-row" role="row" key={item.item_id}>
            <span role="cell">{item.name}</span>
            <span role="cell">{item.category}</span>
            <span role="cell">{item.quantity}</span>
            <span role="cell">{`${item.location.shelf}/${item.location.slot}`}</span>
            <button type="button" title="入库一件" onClick={() => onInbound(item.item_id)} disabled={busy}>
              <PackagePlus aria-hidden="true" size={16} />
              入库
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}
