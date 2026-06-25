import {
  Activity,
  Boxes,
  Camera,
  CameraOff,
  ClipboardList,
  Cpu,
  ImageDown,
  Play,
  RefreshCw,
  Router,
  ScanSearch,
  ShieldAlert,
  SquareX,
  Tags,
  Terminal,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from './api/client'
import type {
  CameraCapture,
  RecognitionCategory,
  SystemEvent,
  SystemStatus,
  TaskDetail,
  TaskRecognition,
  TaskState,
} from './api/types'
import { useEventStream } from './hooks/useEventStream'
import { usePolling } from './hooks/usePolling'
import './styles.css'

export type View = 'pick-sort' | 'stack' | 'camera' | 'management' | 'status'

const viewLabels: Record<View, string> = {
  'pick-sort': '分拣',
  stack: '堆叠',
  camera: '相机',
  management: '管理',
  status: '状态',
}

const viewSubtitles: Record<View, string> = {
  'pick-sort': '默认分拣程序',
  stack: '默认堆叠程序',
  camera: '相机预览与样本采集',
  management: '任务记录与事件流',
  status: '开发板与服务状态',
}

const stateLabels: Record<TaskState, string> = {
  queued: '排队',
  detecting: '检测',
  planning: '规划',
  moving: '运行',
  verifying: '确认',
  succeeded: '成功',
  failed: '失败',
  cancelled: '已取消',
  paused: '暂停',
}

const recognitionCategoryLabels: Record<RecognitionCategory, string> = {
  hazardous: '有害垃圾',
  recyclable: '可回收物',
  kitchen: '厨余垃圾',
  other: '其他垃圾',
  unknown: '未知类别',
}

const terminalTaskStates = new Set<TaskState>(['succeeded', 'failed', 'cancelled'])

export function isTaskInProgress(task: Pick<TaskDetail, 'state'> | null | undefined): boolean {
  return task ? !terminalTaskStates.has(task.state) : false
}

export function canStartProgramAction(view: View, activeTask: boolean, busy: boolean): boolean {
  return (view === 'pick-sort' || view === 'stack') && !activeTask && !busy
}

function formatTime(value: string | null | undefined): string {
  if (!value) {
    return '--'
  }
  return new Date(value).toLocaleTimeString('zh-CN', { hour12: false })
}

function formatDateTime(value = new Date()): string {
  return value.toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function stateTone(state: TaskState | undefined): string {
  if (state === 'succeeded') return 'good'
  if (state === 'failed' || state === 'cancelled') return 'bad'
  if (state === 'moving' || state === 'detecting' || state === 'planning') return 'busy'
  return 'idle'
}

export default function App() {
  const [view, setView] = useState<View>('pick-sort')
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [task, setTask] = useState<TaskDetail | null>(null)
  const [history, setHistory] = useState<TaskDetail[]>([])
  const [captures, setCaptures] = useState<CameraCapture[]>([])
  const [captureLabel, setCaptureLabel] = useState('new_object')
  const [events, setEvents] = useState<SystemEvent[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('ready')
  const [statusError, setStatusError] = useState<string | null>(null)

  const rememberTask = useCallback((next: TaskDetail) => {
    setTask(next)
    setHistory((current) => {
      const rest = current.filter((item) => item.task_id !== next.task_id)
      return [next, ...rest].slice(0, 12)
    })
  }, [])

  const rememberEvent = useCallback((event: SystemEvent) => {
    setEvents((current) => {
      const rest = current.filter((item) => item.event_id !== event.event_id)
      return [event, ...rest].slice(0, 40)
    })
  }, [])

  useEventStream(rememberEvent, Boolean(status))

  const refresh = useCallback(async () => {
    try {
      const nextStatus = await api.systemStatus()
      setStatus(nextStatus)
      setStatusError(null)
      const taskId = nextStatus.active_task_id ?? task?.task_id
      if (taskId) {
        rememberTask(await api.taskDetail(taskId))
      }
    } catch (error) {
      void error
      setStatusError('后端未连接')
      setMessage('offline preview')
    }
  }, [rememberTask, task?.task_id])

  usePolling(refresh, 3500)

  const runAction = async (label: string, action: () => Promise<void>) => {
    setBusy(true)
    try {
      await action()
      setMessage(label)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'unknown error')
    } finally {
      setBusy(false)
      await refresh()
    }
  }

  const startPickSort = () =>
    runAction('pick-sort submitted', async () => {
      const created = await api.createPickSortTask(['insulator'], 'power_fitting')
      rememberTask(await api.taskDetail(created.task_id))
    })

  const startStack = () =>
    runAction('stack submitted', async () => {
      const created = await api.createStackTask(['red_block'], 'stack_area_01')
      rememberTask(await api.taskDetail(created.task_id))
    })

  const cancelTask = () =>
    task
      ? runAction('task interrupt requested', async () => {
          rememberTask(await api.cancelTask(task.task_id))
        })
      : undefined

  const capturePhoto = () =>
    runAction('photo captured', async () => {
      const capture = await api.capturePhoto(captureLabel)
      setCaptures((current) => [capture, ...current].slice(0, 12))
    })

  const activeTask = isTaskInProgress(task) || Boolean(status?.active_task_id)
  const canStartFromRibbon = canStartProgramAction(view, activeTask, busy)
  const startSelectedProgram = view === 'stack' ? startStack : startPickSort

  return (
    <main className="app-shell">
      <header className="command-ribbon">
        <div className="brand-mark" aria-label="AtlasSmartArm">
          <Cpu aria-hidden="true" size={26} />
          <div>
            <strong>AtlasSmartArm</strong>
            <span>Board demo workbench</span>
          </div>
        </div>

        <div className="ribbon-actions" aria-label="快速操作">
          <button className="ribbon-command primary" type="button" onClick={startSelectedProgram} disabled={!canStartFromRibbon}>
            <Play aria-hidden="true" size={18} />
            启动程序
          </button>
          <button className="ribbon-command danger" type="button" onClick={cancelTask} disabled={busy || !activeTask}>
            <SquareX aria-hidden="true" size={18} />
            中断任务
          </button>
          <button className="ribbon-command ghost" type="button" onClick={() => void refresh()} disabled={busy}>
            <RefreshCw aria-hidden="true" size={18} className={busy ? 'spin' : undefined} />
            刷新状态
          </button>
          <button className="ribbon-command ghost" type="button" onClick={() => setView('camera')}>
            <Camera aria-hidden="true" size={18} />
            拍照
          </button>
          <button className="ribbon-command ghost" type="button" onClick={() => setView('management')}>
            <ClipboardList aria-hidden="true" size={18} />
            管理
          </button>
        </div>

        <div className="ribbon-status" aria-live="polite">
          <span className={`connection-dot ${statusError ? 'warning' : 'ready'}`} />
          <strong>{statusError ? 'offline preview' : message}</strong>
          <span>{formatDateTime()}</span>
        </div>
      </header>

      <div className="app-frame">
        <aside className="side-rail" aria-label="工作台导航">
          <span className="rail-label">模式</span>
          <nav className="mode-nav">
            <button className={view === 'pick-sort' ? 'active' : ''} type="button" onClick={() => setView('pick-sort')}>
              <Play aria-hidden="true" size={19} />
              <span>分拣</span>
            </button>
            <button className={view === 'stack' ? 'active' : ''} type="button" onClick={() => setView('stack')}>
              <Boxes aria-hidden="true" size={19} />
              <span>堆叠</span>
            </button>
            <button className={view === 'camera' ? 'active' : ''} type="button" onClick={() => setView('camera')}>
              <Camera aria-hidden="true" size={19} />
              <span>相机</span>
            </button>
            <button className={view === 'management' ? 'active' : ''} type="button" onClick={() => setView('management')}>
              <ClipboardList aria-hidden="true" size={19} />
              <span>管理</span>
            </button>
            <button className={view === 'status' ? 'active' : ''} type="button" onClick={() => setView('status')}>
              <Activity aria-hidden="true" size={19} />
              <span>状态</span>
            </button>
          </nav>
        </aside>

        <section className="workbench">
          <header className="workbench-top">
            <div>
              <span className="eyebrow">current workspace</span>
              <h1>{viewLabels[view]}</h1>
              <p>{viewSubtitles[view]}</p>
            </div>
            <div className="topbar-actions">
              <span>{statusError ?? '系统状态已同步'}</span>
              <button className="icon-button" type="button" title="刷新" onClick={() => void refresh()} disabled={busy}>
                <RefreshCw aria-hidden="true" size={18} className={busy ? 'spin' : undefined} />
              </button>
            </div>
          </header>

          {statusError ? (
            <div className="notice-strip" role="status">
              <ShieldAlert aria-hidden="true" size={18} />
              <span>后端未连接，当前为纯前端预览。控制按钮和布局可操作，真实设备状态会在后端可用后同步。</span>
            </div>
          ) : null}

          <section className="signal-strip" aria-label="实时状态">
            <Signal icon={<Router size={18} />} label="Board" value={status?.atlas.host ?? '192.168.137.100'} detail={status?.atlas.online ? '在线' : '等待连接'} tone={status?.atlas.online ? 'good' : 'idle'} />
            <Signal icon={<Activity size={18} />} label="Mode" value={status?.program_mode ?? 'mock'} detail="运行模式" tone="busy" />
            <Signal
              icon={status?.camera.preview_active ? <Camera size={18} /> : <CameraOff size={18} />}
              label="Camera"
              value={status?.camera.preview_active ? 'previewing' : (status?.camera_policy ?? 'unavailable')}
              detail={status?.camera.preview_clients ? `${status.camera.preview_clients} clients` : '相机不可用'}
              tone={status?.camera.preview_active ? 'busy' : 'idle'}
            />
            <Signal icon={<ShieldAlert size={18} />} label="Arm" value={status?.arm.state ?? 'unknown'} detail={status?.arm.control_lock ?? '机械臂状态'} tone={status?.arm.state === 'idle' ? 'good' : 'busy'} />
          </section>

          {view === 'pick-sort' ? (
            <OperationPanel
              title="默认分拣程序"
              program="pick_sort_default"
              task={task}
              busy={busy}
              showRecognition
              onStart={startPickSort}
              onCancel={cancelTask}
            />
          ) : null}
          {view === 'stack' ? (
            <OperationPanel
              title="默认堆叠程序"
              program="stack_default"
              task={task}
              busy={busy}
              onStart={startStack}
              onCancel={cancelTask}
            />
          ) : null}
          {view === 'camera' ? (
            <CapturePanel
              status={status}
              captures={captures}
              label={captureLabel}
              busy={busy}
              onLabelChange={setCaptureLabel}
              onCapture={capturePhoto}
            />
          ) : null}
          {view === 'management' ? <ManagementPanel history={history} events={events} /> : null}
          {view === 'status' ? <StatusPanel status={status} events={events} /> : null}
        </section>
      </div>

      <footer className="system-footer" aria-label="运行环境">
        <span><span className="connection-dot ready" /> ROS2 Humble</span>
        <span>网络 {status?.atlas.network.ip_address ?? '--'}</span>
        <span>模型 {status?.vision.model_name ?? '--'}</span>
        <span>校准 {status?.calibration.ready ? status.calibration.version : '--'}</span>
        <span>电源 {status?.arm.online ? 'ready' : '--'}</span>
      </footer>
    </main>
  )
}

interface SignalProps {
  icon: React.ReactNode
  label: string
  value: string
  detail: string
  tone: 'good' | 'bad' | 'busy' | 'idle'
}

function Signal({ icon, label, value, detail, tone }: SignalProps) {
  return (
    <div className={`signal ${tone}`}>
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
      <em>{detail}</em>
    </div>
  )
}

interface OperationPanelProps {
  title: string
  program: NonNullable<TaskDetail['program']>
  task: TaskDetail | null
  busy: boolean
  showRecognition?: boolean
  onStart: () => void
  onCancel: () => void
}

function OperationPanel({ title, program, task, busy, showRecognition = false, onStart, onCancel }: OperationPanelProps) {
  const isCurrentProgram = task?.program === program || task?.program === null
  const visibleTask = isCurrentProgram ? task : null
  const active = isTaskInProgress(visibleTask)
  const nodeName = program === 'pick_sort_default' ? '/pick_sort_node' : '/stack_node'

  return (
    <section className={`operation-grid ${showRecognition ? 'with-recognition' : ''}`}>
      <div className="command-surface">
        <div className="section-heading">
          <div>
            <span className="eyebrow">ROS2 launch</span>
            <h2>{title}</h2>
          </div>
          <span className={`state-pill ${stateTone(visibleTask?.state)}`}>
            {visibleTask ? stateLabels[visibleTask.state] : '空闲'}
          </span>
        </div>
        <div className="camera-lock">
          <CameraOff aria-hidden="true" size={30} />
          <strong>Camera reserved</strong>
          <span>任务运行时由开发板默认 ROS2 程序独占</span>
        </div>
        <div className="program-fields" aria-label="程序配置">
          <Metric label="程序包" value={program} />
          <Metric label="默认节点" value={nodeName} />
          <Metric label="参数" value="--mode default" />
        </div>
        <div className="button-row">
          <button className="start-command" type="button" onClick={onStart} disabled={busy || active}>
            <Play aria-hidden="true" size={17} />
            启动
          </button>
          <button className="danger" type="button" onClick={onCancel} disabled={busy || !active}>
            <SquareX aria-hidden="true" size={17} />
            中断
          </button>
        </div>
      </div>
      {showRecognition ? <RecognitionPanel recognition={visibleTask?.recognition ?? null} /> : null}
      <TaskInspector task={visibleTask} />
    </section>
  )
}

function RecognitionPanel({ recognition }: { recognition: TaskRecognition | null }) {
  const detections = recognition?.detections ?? []

  return (
    <div className="recognition-panel">
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">Recognition</span>
          <h2>识别结果</h2>
        </div>
        <ScanSearch aria-hidden="true" size={20} />
      </div>
      {recognition ? (
        <div className="recognition-content">
          <div className="recognition-hero">
            <span>最新标签</span>
            <strong>{recognition.latest_label}</strong>
            <em className={`category-chip ${recognition.latest_category}`}>
              {recognitionCategoryLabels[recognition.latest_category]}
            </em>
          </div>
          <div className="recognition-meta">
            <Metric label="更新时间" value={formatTime(recognition.updated_at)} />
            <Metric label="检测数量" value={String(detections.length)} />
          </div>
          <div className="tag-window" aria-label="识别标签列表">
            {detections.map((detection, index) => (
              <div className="detected-tag" key={`${detection.label}-${index}`}>
                <div>
                  <strong>{detection.label}</strong>
                  <span>{recognitionCategoryLabels[detection.category]}</span>
                </div>
                <code>
                  x {detection.x_m.toFixed(3)} · y {detection.y_m.toFixed(3)}
                </code>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="recognition-empty">
          <Tags aria-hidden="true" size={28} />
          <strong>等待识别标签</strong>
          <span>分拣程序输出标签后显示</span>
        </div>
      )}
      <div className="category-legend" aria-label="标签说明">
        {Object.entries(recognitionCategoryLabels).map(([category, label]) => (
          <span className={`category-chip ${category}`} key={category}>
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}

interface CapturePanelProps {
  status: SystemStatus | null
  captures: CameraCapture[]
  label: string
  busy: boolean
  onLabelChange: (value: string) => void
  onCapture: () => void
}

function CapturePanel({ status, captures, label, busy, onLabelChange, onCapture }: CapturePanelProps) {
  const [previewUrl, setPreviewUrl] = useState('')
  const previewImageRef = useRef<HTMLImageElement | null>(null)
  const blockedByTask = Boolean(status?.active_task_id)
  const cameraOnline = Boolean(status?.camera.online)

  useEffect(() => {
    const stopPreview = () => {
      if (previewImageRef.current) {
        previewImageRef.current.src = 'about:blank'
        previewImageRef.current.removeAttribute('src')
      }
      void api.stopCameraPreview().catch(() => undefined)
    }
    if (blockedByTask || !cameraOnline) {
      stopPreview()
      setPreviewUrl('')
      return undefined
    }
    setPreviewUrl(api.cameraPreviewUrl())
    return stopPreview
  }, [blockedByTask, cameraOnline])

  return (
    <section className="capture-grid">
      <div className="capture-surface">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Camera session</span>
            <h2>实时预览</h2>
          </div>
          <span className={`state-pill ${status?.camera.preview_active ? 'busy' : 'idle'}`}>
            {status?.camera.preview_active ? '预览中' : '待连接'}
          </span>
        </div>
        {blockedByTask || !cameraOnline ? (
          <div className="camera-lock live">
            <CameraOff aria-hidden="true" size={30} />
            <strong>{blockedByTask ? 'Camera unavailable' : 'Camera offline'}</strong>
            <span>{blockedByTask ? '真实任务正在运行，默认程序占用摄像头' : '相机服务在线后会显示实时预览'}</span>
          </div>
        ) : (
          <div className="preview-frame">
            {previewUrl ? <img ref={previewImageRef} src={previewUrl} alt="机械臂摄像头实时预览" /> : null}
          </div>
        )}
        <div className="capture-controls">
          <label>
            <span>Label</span>
            <input
              value={label}
              onChange={(event) => onLabelChange(event.target.value)}
              maxLength={80}
              placeholder="new_object"
            />
          </label>
          <button type="button" onClick={onCapture} disabled={busy || blockedByTask}>
            <ImageDown aria-hidden="true" size={17} />
            拍照
          </button>
        </div>
      </div>
      <div className="capture-gallery">
        <div className="section-heading compact">
          <div>
            <span className="eyebrow">Captured samples</span>
            <h2>最近照片</h2>
          </div>
          <Camera aria-hidden="true" size={20} />
        </div>
        <div className="capture-list">
          {captures.map((capture) => (
            <figure key={capture.capture_id} className="capture-item">
              <img src={api.cameraCaptureImageUrl(capture.capture_id)} alt={capture.label} />
              <figcaption>
                <strong>{capture.label}</strong>
                <span>{capture.width}x{capture.height} · {formatTime(capture.captured_at)}</span>
              </figcaption>
            </figure>
          ))}
          {captures.length === 0 ? <div className="empty-line">no captured photos</div> : null}
        </div>
      </div>
    </section>
  )
}

function TaskInspector({ task }: { task: TaskDetail | null }) {
  return (
    <div className="inspector task-detail-panel">
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">Task detail</span>
          <h2>任务详情</h2>
        </div>
        <Terminal aria-hidden="true" size={20} />
      </div>
      <div className="current-task-line">
        <span>当前任务</span>
        <strong>{task?.task_id ?? 'no task'}</strong>
      </div>
      <div className="metric-grid">
        <Metric label="Program" value={task?.program ?? 'none'} />
        <Metric label="PID" value={task?.pid ? String(task.pid) : 'none'} />
        <Metric label="State" value={task ? stateLabels[task.state] : 'pending'} />
        <Metric label="Started" value={formatTime(task?.started_at)} />
        <Metric label="Exit" value={task?.exit_code === null || task?.exit_code === undefined ? 'pending' : String(task.exit_code)} />
        <Metric label="Step" value={task?.current_step ?? '--'} />
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${Math.round((task?.progress ?? 0) * 100)}%` }} />
      </div>
      <TaskStepRail state={task?.state} />
      <LogPanel logs={task?.logs ?? []} />
    </div>
  )
}

function TaskStepRail({ state }: { state: TaskState | undefined }) {
  const steps = [
    { key: 'queued', label: '待启动' },
    { key: 'detecting', label: '识别中' },
    { key: 'planning', label: '规划中' },
    { key: 'moving', label: '执行中' },
    { key: 'succeeded', label: '完成' },
  ] as const
  const activeIndex = state ? Math.max(0, steps.findIndex((step) => step.key === state)) : 0

  return (
    <div className="task-step-rail" aria-label="任务阶段">
      {steps.map((step, index) => (
        <span className={index <= activeIndex ? 'active' : ''} key={step.key}>
          <i />
          {step.label}
        </span>
      ))}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function LogPanel({ logs }: { logs: string[] }) {
  return (
    <div className="log-panel" aria-label="ROS 日志">
      {logs.length === 0 ? <span className="empty-line">waiting for ROS output</span> : null}
      {logs.slice(-18).map((line, index) => (
        <code key={`${line}-${index}`}>{line}</code>
      ))}
    </div>
  )
}

function ManagementPanel({ history, events }: { history: TaskDetail[]; events: SystemEvent[] }) {
  return (
    <section className="management-grid">
      <div className="history-panel">
        <div className="section-heading compact">
          <div>
            <span className="eyebrow">Run ledger</span>
            <h2>任务记录</h2>
          </div>
          <ClipboardList aria-hidden="true" size={20} />
        </div>
        <div className="ledger-table" role="table">
          <div className="ledger-row ledger-head" role="row">
            <span>任务</span>
            <span>程序</span>
            <span>状态</span>
            <span>结束</span>
          </div>
          {history.map((item) => (
            <div className="ledger-row" role="row" key={item.task_id}>
              <span>{item.task_id}</span>
              <span>{item.program ?? item.type}</span>
              <span>{stateLabels[item.state]}</span>
              <span>{formatTime(item.ended_at)}</span>
            </div>
          ))}
          {history.length === 0 ? <div className="empty-line">no task records</div> : null}
        </div>
      </div>
      <EventPanel events={events} />
    </section>
  )
}

function StatusPanel({ status, events }: { status: SystemStatus | null; events: SystemEvent[] }) {
  return (
    <section className="management-grid">
      <div className="history-panel">
        <div className="section-heading compact">
          <div>
            <span className="eyebrow">System</span>
            <h2>开发板状态</h2>
          </div>
          <Activity aria-hidden="true" size={20} />
        </div>
        <div className="status-list">
          <Metric label="Host" value={status?.atlas.host ?? 'unknown'} />
          <Metric label="Camera" value={status?.camera.online ? 'online' : 'offline'} />
          <Metric label="Arm lock" value={status?.arm.control_lock ?? 'none'} />
          <Metric label="Active task" value={status?.active_task_id ?? 'none'} />
          <Metric label="Model" value={status?.vision.model_name ?? 'unknown'} />
          <Metric label="Calibration" value={status?.calibration.ready ? status.calibration.version : 'not ready'} />
        </div>
      </div>
      <EventPanel events={events} />
    </section>
  )
}

function EventPanel({ events }: { events: SystemEvent[] }) {
  return (
    <div className="events-panel">
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">Events</span>
          <h2>事件流</h2>
        </div>
        <Terminal aria-hidden="true" size={20} />
      </div>
      <ul className="event-list">
        {events.slice(0, 18).map((event, index) => (
          <li key={`${event.event_id}-${event.time}-${index}`}>
            <strong>{event.type}</strong>
            <span>{formatTime(event.time)}</span>
          </li>
        ))}
      </ul>
      {events.length === 0 ? <div className="empty-line">no events</div> : null}
    </div>
  )
}
