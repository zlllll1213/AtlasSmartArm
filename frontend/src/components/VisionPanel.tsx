import { Camera, RefreshCw } from 'lucide-react'

import type { VisionDetectResult } from '../api/types'

interface VisionPanelProps {
  result: VisionDetectResult | null
  onDetect: () => void
  busy: boolean
}

export function VisionPanel({ result, onDetect, busy }: VisionPanelProps) {
  const detection = result?.detections[0]
  return (
    <section className="panel vision-panel" aria-label="视觉识别">
      <div className="panel-heading">
        <h2>视觉识别</h2>
        <button className="icon-button" type="button" title="触发识别" onClick={onDetect} disabled={busy}>
          {busy ? <RefreshCw aria-hidden="true" size={18} className="spin" /> : <Camera aria-hidden="true" size={18} />}
        </button>
      </div>
      <div className="camera-frame">
        {detection ? (
          <div
            className="bbox"
            style={{
              left: `${(detection.bbox_norm.cx - detection.bbox_norm.w / 2) * 100}%`,
              top: `${(detection.bbox_norm.cy - detection.bbox_norm.h / 2) * 100}%`,
              width: `${detection.bbox_norm.w * 100}%`,
              height: `${detection.bbox_norm.h * 100}%`,
            }}
          >
            <span>{detection.label}</span>
          </div>
        ) : null}
      </div>
      <dl className="detail-list">
        <div>
          <dt>Frame</dt>
          <dd>{result?.frame_id ?? 'pending'}</dd>
        </div>
        <div>
          <dt>Object</dt>
          <dd>{detection ? `${detection.label} ${(detection.confidence * 100).toFixed(0)}%` : 'none'}</dd>
        </div>
        <div>
          <dt>Arm XYZ</dt>
          <dd>
            {detection?.arm_position
              ? `${detection.arm_position.x_m.toFixed(4)} / ${detection.arm_position.y_m.toFixed(4)} / ${detection.arm_position.z_m.toFixed(4)} m`
              : 'not mapped'}
          </dd>
        </div>
      </dl>
    </section>
  )
}
