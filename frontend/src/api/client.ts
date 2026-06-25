import type {
  ApiErrorPayload,
  ApiResponse,
  CameraCapture,
  CameraStatus,
  InventoryItem,
  InventoryPage,
  JointAngles,
  MaterialCategory,
  SystemEvent,
  SystemStatus,
  TaskCreateResult,
  TaskDetail,
  VisionDetectResult,
} from './types'

const DEFAULT_API_BASE = 'http://localhost:8080'

export class ApiError extends Error {
  readonly payload: ApiErrorPayload

  constructor(payload: ApiErrorPayload) {
    super(payload.message)
    this.name = 'ApiError'
    this.payload = payload
  }
}

export function makeApiUrl(path: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

export function makeWsUrl(path: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE
  const wsBase = base.replace(/^http/, 'ws')
  return `${wsBase}${path.startsWith('/') ? path : `/${path}`}`
}

export function unwrapResponse<T>(payload: ApiResponse<T>): T {
  if (!payload.success || payload.error) {
    throw new ApiError(
      payload.error ?? {
        code: 'INTERNAL',
        message: 'Unknown API error.',
        details: {},
      },
    )
  }
  if (payload.data === null) {
    throw new ApiError({
      code: 'INTERNAL',
      message: 'Successful response did not include data.',
      details: {},
    })
  }
  return payload.data
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(makeApiUrl(path), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  const payload = (await response.json()) as ApiResponse<T>
  return unwrapResponse(payload)
}

export const api = {
  health: () =>
    requestJson<{ service: string; status: string; version: string; time: string }>('/api/v1/health'),
  systemStatus: () => requestJson<SystemStatus>('/api/v1/system/status'),
  detect: () =>
    requestJson<VisionDetectResult>('/api/v1/vision/detect', {
      method: 'POST',
      body: JSON.stringify({ source: 'camera', camera_index: 0, save_frame: false }),
    }),
  cameraStatus: () => requestJson<CameraStatus>('/api/v1/camera/status'),
  cameraPreviewUrl: () => makeApiUrl(`/api/v1/camera/preview.mjpg?t=${Date.now()}`),
  cameraCaptureImageUrl: (captureId: string) =>
    makeApiUrl(`/api/v1/camera/captures/${captureId}/image`),
  capturePhoto: (label: string) =>
    requestJson<CameraCapture>('/api/v1/camera/captures', {
      method: 'POST',
      body: JSON.stringify({ label: label.trim() || undefined }),
    }),
  createPickSortTask: (labels: string[], category: MaterialCategory) =>
    requestJson<TaskCreateResult>('/api/v1/tasks/pick-sort', {
      method: 'POST',
      body: JSON.stringify({
        target: { mode: 'auto_detect', labels },
        destination: { type: 'category_bin', category },
        options: { dry_run: false, max_retry: 1 },
      }),
    }),
  createStackTask: (labels: string[], slotId: string) =>
    requestJson<TaskCreateResult>('/api/v1/tasks/stack', {
      method: 'POST',
      body: JSON.stringify({
        target: { mode: 'auto_detect', labels },
        stack: { slot_id: slotId, max_layers: 3 },
        options: { dry_run: false, max_retry: 1 },
      }),
    }),
  taskDetail: (taskId: string) => requestJson<TaskDetail>(`/api/v1/tasks/${taskId}`),
  cancelTask: (taskId: string) =>
    requestJson<TaskDetail>(`/api/v1/tasks/${taskId}/cancel`, { method: 'POST' }),
  inventoryItems: () => requestJson<InventoryPage>('/api/v1/inventory/items'),
  createInventoryItem: () =>
    requestJson<InventoryItem>('/api/v1/inventory/items', {
      method: 'POST',
      body: JSON.stringify({
        name: '螺丝刀',
        category: 'tool',
        label: 'screwdriver',
        quantity: 1,
        location: { area: 'B', shelf: 'B-02', slot: 'B-02-01' },
      }),
    }),
  inbound: (itemId: string, quantity: number) =>
    requestJson<InventoryItem>('/api/v1/inventory/inbound', {
      method: 'POST',
      body: JSON.stringify({
        item_id: itemId,
        quantity,
        operator: 'frontend-demo',
        reason: 'Manual stock adjustment from dashboard.',
      }),
    }),
  dryRunMove: (joints: JointAngles) =>
    requestJson<{ accepted: boolean; dry_run: boolean; validated: boolean; duration_ms: number }>(
      '/api/v1/arm/move',
      {
        method: 'POST',
        body: JSON.stringify({
          target: { type: 'joints', joints },
          duration_ms: 1000,
          dry_run: true,
        }),
      },
    ),
  emergencyStop: () =>
    requestJson<{ state: string; message: string }>('/api/v1/arm/emergency-stop', { method: 'POST' }),
}

export function connectEventStream(onEvent: (event: SystemEvent) => void): () => void {
  const socket = new WebSocket(makeWsUrl('/ws/v1/events'))
  socket.onmessage = (message) => {
    onEvent(JSON.parse(message.data) as SystemEvent)
  }
  return () => socket.close()
}
