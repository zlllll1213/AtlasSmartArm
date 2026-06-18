import { Boxes, ClipboardList, Play, SquareX } from 'lucide-react'

import type { TaskDetail } from '../api/types'

interface TaskPanelProps {
  task: TaskDetail | null
  onPickSort: () => void
  onStack: () => void
  onCancel: () => void
  busy: boolean
}

export function TaskPanel({ task, onPickSort, onStack, onCancel, busy }: TaskPanelProps) {
  return (
    <section className="panel task-panel" aria-label="任务状态">
      <div className="panel-heading">
        <h2>任务</h2>
        <ClipboardList aria-hidden="true" size={20} />
      </div>
      <div className="task-current">
        <strong>{task?.task_id ?? 'no active task'}</strong>
        <span>{task?.current_step ?? 'idle'}</span>
        <div className="progress-track">
          <div className="progress-bar" style={{ width: `${Math.round((task?.progress ?? 0) * 100)}%` }} />
        </div>
      </div>
      <div className="button-row">
        <button type="button" title="创建分拣任务" onClick={onPickSort} disabled={busy}>
          <Play aria-hidden="true" size={17} />
          分拣
        </button>
        <button type="button" title="创建堆叠任务" onClick={onStack} disabled={busy}>
          <Boxes aria-hidden="true" size={17} />
          堆叠
        </button>
        <button type="button" title="取消当前任务" onClick={onCancel} disabled={busy || !task}>
          <SquareX aria-hidden="true" size={17} />
          取消
        </button>
      </div>
    </section>
  )
}
