import { describe, expect, it } from 'vitest'

import { ApiError, makeApiUrl, unwrapResponse } from './client'

describe('API client helpers', () => {
  it('builds API URLs from the configured base path', () => {
    expect(makeApiUrl('/api/v1/health')).toBe('http://localhost:8080/api/v1/health')
  })

  it('unwraps successful unified API envelopes', () => {
    const data = unwrapResponse({
      request_id: 'req_test',
      success: true,
      data: { status: 'ok' },
      error: null,
    })

    expect(data).toEqual({ status: 'ok' })
  })

  it('throws ApiError for failed unified API envelopes', () => {
    expect(() =>
      unwrapResponse({
        request_id: 'req_test',
        success: false,
        data: null,
        error: {
          code: 'OUT_OF_RANGE',
          message: 'duration_ms must be between 100 and 3000.',
          details: { field: 'duration_ms' },
        },
      }),
    ).toThrow(ApiError)
  })
})
