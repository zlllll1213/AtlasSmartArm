import { useEffect } from 'react'

import { connectEventStream } from '../api/client'
import type { SystemEvent } from '../api/types'

export function useEventStream(onEvent: (event: SystemEvent) => void): void {
  useEffect(() => {
    let disconnect = connectEventStream(onEvent)
    const reconnect = window.setInterval(() => {
      disconnect()
      disconnect = connectEventStream(onEvent)
    }, 15000)
    return () => {
      window.clearInterval(reconnect)
      disconnect()
    }
  }, [onEvent])
}
