import { describe, expect, it } from 'vitest'

import { ApiError, api, makeApiUrl, unwrapResponse } from './client'
import type { CameraCapture, TaskDetail } from './types'

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

  it('unwraps board task detail fields used by the demo workbench', () => {
    const task = unwrapResponse<TaskDetail>({
      request_id: 'req_task',
      success: true,
      data: {
        task_id: 'task_000000000001',
        type: 'pick_sort',
        state: 'moving',
        progress: 0.62,
        current_step: 'moving_to_target',
        created_at: '2026-06-25T00:00:00Z',
        updated_at: '2026-06-25T00:00:01Z',
        result: null,
        program: 'pick_sort_default',
        pid: 4242,
        exit_code: null,
        logs: ['default program started'],
        recognition: {
          latest_label: 'Book',
          latest_category: 'recyclable',
          detections: [
            {
              label: 'Book',
              category: 'recyclable',
              x_m: 0.012,
              y_m: 0.321,
              source: 'msg',
            },
          ],
          updated_at: '2026-06-25T00:00:01Z',
        },
        started_at: '2026-06-25T00:00:00Z',
        ended_at: null,
      },
      error: null,
    })

    expect(task.program).toBe('pick_sort_default')
    expect(task.logs).toEqual(['default program started'])
    expect(task.recognition?.latest_label).toBe('Book')
    expect(task.pid).toBe(4242)
  })

  it('builds camera preview and capture image URLs from the API base', () => {
    expect(api.cameraPreviewUrl()).toContain('http://localhost:8080/api/v1/camera/preview.mjpg?t=')
    expect(api.cameraCaptureImageUrl('cap_abc')).toBe(
      'http://localhost:8080/api/v1/camera/captures/cap_abc/image',
    )
  })

  it('unwraps camera capture metadata used by the photo workspace', () => {
    const capture = unwrapResponse<CameraCapture>({
      request_id: 'req_camera',
      success: true,
      data: {
        capture_id: 'cap_001',
        label: 'new_part',
        file_name: 'new_part_cap_001.jpg',
        path: '/tmp/new_part_cap_001.jpg',
        width: 640,
        height: 480,
        captured_at: '2026-06-25T00:00:00Z',
        image_url: '/api/v1/camera/captures/cap_001/image',
      },
      error: null,
    })

    expect(capture.label).toBe('new_part')
    expect(capture.image_url).toBe('/api/v1/camera/captures/cap_001/image')
  })
})
