import { AlertTriangle, Bot, Route } from 'lucide-react'

import type { SystemStatus } from '../api/types'

interface ArmPanelProps {
  status: SystemStatus | null
  onDryRun: () => void
  onEmergencyStop: () => void
  busy: boolean
}

export function ArmPanel({ status, onDryRun, onEmergencyStop, busy }: ArmPanelProps) {
  return (
    <section className="panel arm-panel" aria-label="机械臂">
      <div className="panel-heading">
        <h2>机械臂</h2>
        <Bot aria-hidden="true" size={20} />
      </div>
      <dl className="detail-list">
        <div>
          <dt>State</dt>
          <dd>{status?.arm.state ?? 'unknown'}</dd>
        </div>
        <div>
          <dt>Lock</dt>
          <dd>{status?.arm.control_lock ?? 'free'}</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{status?.vision.model_name ?? 'not loaded'}</dd>
        </div>
      </dl>
      <div className="button-row">
        <button type="button" title="dry-run 校验" onClick={onDryRun} disabled={busy}>
          <Route aria-hidden="true" size={17} />
          Dry-run
        </button>
        <button className="danger" type="button" title="急停" onClick={onEmergencyStop} disabled={busy}>
          <AlertTriangle aria-hidden="true" size={17} />
          急停
        </button>
      </div>
    </section>
  )
}
