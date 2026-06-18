import { Radio } from 'lucide-react'

import type { SystemEvent } from '../api/types'

interface EventLogProps {
  events: SystemEvent[]
}

export function EventLog({ events }: EventLogProps) {
  return (
    <section className="panel event-panel" aria-label="事件日志">
      <div className="panel-heading">
        <h2>事件</h2>
        <Radio aria-hidden="true" size={20} />
      </div>
      <ol className="event-list">
        {events.slice(0, 8).map((event) => (
          <li key={`${event.event_id}-${event.time}`}>
            <strong>{event.type}</strong>
            <span>{new Date(event.time).toLocaleTimeString()}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
