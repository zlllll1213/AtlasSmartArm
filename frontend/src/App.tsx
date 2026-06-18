import { RefreshCw } from 'lucide-react'
import { useCallback, useState } from 'react'

import { api } from './api/client'
import type { InventoryItem, SystemEvent, SystemStatus, TaskDetail, VisionDetectResult } from './api/types'
import { ArmPanel } from './components/ArmPanel'
import { EventLog } from './components/EventLog'
import { InventoryPanel } from './components/InventoryPanel'
import { StatusGrid } from './components/StatusGrid'
import { TaskPanel } from './components/TaskPanel'
import { VisionPanel } from './components/VisionPanel'
import { useEventStream } from './hooks/useEventStream'
import { usePolling } from './hooks/usePolling'
import './styles.css'

const demoJoints = {
  joint1_deg: 90,
  joint2_deg: 80,
  joint3_deg: 50,
  joint4_deg: 50,
  joint5_deg: 265,
  joint6_deg: 30,
}

export default function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [vision, setVision] = useState<VisionDetectResult | null>(null)
  const [task, setTask] = useState<TaskDetail | null>(null)
  const [items, setItems] = useState<InventoryItem[]>([])
  const [events, setEvents] = useState<SystemEvent[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('mock mode ready')

  const rememberEvent = useCallback((event: SystemEvent) => {
    setEvents((current) => [event, ...current].slice(0, 24))
  }, [])

  useEventStream(rememberEvent)

  const refresh = useCallback(async () => {
    const [nextStatus, inventory] = await Promise.all([api.systemStatus(), api.inventoryItems()])
    setStatus(nextStatus)
    setItems(inventory.items)
    if (task) {
      setTask(await api.taskDetail(task.task_id))
    }
  }, [task])

  usePolling(refresh, 5000)

  const runAction = async (label: string, action: () => Promise<void>) => {
    setBusy(true)
    try {
      await action()
      setMessage(label)
    } catch (error) {
      const text = error instanceof Error ? error.message : 'unknown error'
      setMessage(text)
    } finally {
      setBusy(false)
      await refresh()
    }
  }

  const detect = () =>
    runAction('detection updated', async () => {
      const result = await api.detect()
      setVision(result)
    })

  const createPickSort = () =>
    runAction('pick-sort task queued', async () => {
      const created = await api.createPickSortTask(['insulator'], 'power_fitting')
      setTask(await api.taskDetail(created.task_id))
    })

  const createStack = () =>
    runAction('stack task queued', async () => {
      const created = await api.createStackTask(['component_box'], 'stack_area_01')
      setTask(await api.taskDetail(created.task_id))
    })

  const cancelTask = () =>
    task
      ? runAction('task cancelled', async () => {
          setTask(await api.cancelTask(task.task_id))
        })
      : undefined

  const createItem = () =>
    runAction('inventory item created', async () => {
      await api.createInventoryItem()
    })

  const inbound = (itemId: string) =>
    runAction('inventory updated', async () => {
      await api.inbound(itemId, 1)
    })

  const dryRun = () =>
    runAction('dry-run validated', async () => {
      await api.dryRunMove(demoJoints)
    })

  const emergencyStop = () =>
    runAction('emergency stop accepted', async () => {
      await api.emergencyStop()
    })

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>AtlasSmartArm</h1>
          <p>电力智能运维 / 库房管理</p>
        </div>
        <div className="topbar-actions">
          <span>{message}</span>
          <button className="icon-button" type="button" title="刷新" onClick={() => void refresh()} disabled={busy}>
            <RefreshCw aria-hidden="true" size={18} className={busy ? 'spin' : undefined} />
          </button>
        </div>
      </header>
      <section className="dashboard-grid" aria-label="系统总览">
        <StatusGrid status={status} />
        <ArmPanel status={status} onDryRun={dryRun} onEmergencyStop={emergencyStop} busy={busy} />
        <VisionPanel result={vision} onDetect={detect} busy={busy} />
        <TaskPanel task={task} onPickSort={createPickSort} onStack={createStack} onCancel={cancelTask} busy={busy} />
        <InventoryPanel items={items} onCreate={createItem} onInbound={inbound} busy={busy} />
        <EventLog events={events} />
      </section>
    </main>
  )
}
