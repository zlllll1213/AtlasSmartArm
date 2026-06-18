import { useEffect } from 'react'

export function usePolling(load: () => Promise<void>, delayMs: number): void {
  useEffect(() => {
    let active = true
    const run = async () => {
      if (active) {
        await load()
      }
    }
    void run()
    const timer = window.setInterval(() => void run(), delayMs)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [delayMs, load])
}
