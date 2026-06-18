import { Bot, Camera, Cpu, Radar, ShieldCheck } from 'lucide-react'

import type { SystemStatus } from '../api/types'

interface StatusGridProps {
  status: SystemStatus | null
}

const statusItems = [
  { key: 'atlas', label: 'Atlas', icon: Cpu },
  { key: 'camera', label: 'Camera', icon: Camera },
  { key: 'arm', label: 'Arm', icon: Bot },
  { key: 'vision', label: 'Vision', icon: Radar },
  { key: 'calibration', label: 'Calibration', icon: ShieldCheck },
] as const

export function StatusGrid({ status }: StatusGridProps) {
  return (
    <section className="panel status-panel" aria-label="系统状态">
      <div className="panel-heading">
        <h2>系统状态</h2>
        <span>{status?.atlas.host ?? 'localhost'}</span>
      </div>
      <div className="status-grid">
        {statusItems.map((item) => {
          const Icon = item.icon
          const online =
            item.key === 'calibration'
              ? status?.calibration.ready
              : item.key === 'vision'
                ? status?.vision.model_loaded
                : status?.[item.key].online
          return (
            <div className="status-cell" key={item.key}>
              <Icon aria-hidden="true" size={22} />
              <div>
                <strong>{item.label}</strong>
                <span className={online ? 'state-ok' : 'state-bad'}>{online ? 'online' : 'offline'}</span>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
