import { describe, expect, it } from 'vitest'

import { canStartProgramAction, isTaskInProgress } from './App'

describe('workbench task control guards', () => {
  it('treats non-terminal task states as active', () => {
    expect(isTaskInProgress({ state: 'moving' })).toBe(true)
    expect(isTaskInProgress({ state: 'detecting' })).toBe(true)
  })

  it('allows new program starts only from program views when idle', () => {
    expect(canStartProgramAction('pick-sort', false, false)).toBe(true)
    expect(canStartProgramAction('stack', false, false)).toBe(true)
    expect(canStartProgramAction('camera', false, false)).toBe(false)
  })

  it('blocks program starts while busy or when a task is active', () => {
    expect(canStartProgramAction('pick-sort', true, false)).toBe(false)
    expect(canStartProgramAction('pick-sort', false, true)).toBe(false)
  })
})
