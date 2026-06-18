export type MaterialCategory =
  | 'electronic_component'
  | 'power_fitting'
  | 'tool'
  | 'consumable'
  | 'unknown'

export type ErrorCode =
  | 'INVALID_ARGUMENT'
  | 'OUT_OF_RANGE'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'ARM_BUSY'
  | 'CALIBRATION_REQUIRED'
  | 'DEVICE_OFFLINE'
  | 'VISION_UNAVAILABLE'
  | 'KINEMATICS_FAILED'
  | 'MODEL_NOT_LOADED'
  | 'TASK_TIMEOUT'
  | 'INTERNAL'

export interface ApiErrorPayload {
  code: ErrorCode
  message: string
  details: Record<string, unknown>
}

export interface ApiResponse<T> {
  request_id: string
  success: boolean
  data: T | null
  error: ApiErrorPayload | null
}

export interface SystemStatus {
  atlas: {
    online: boolean
    host: string
    network: {
      iface: string
      ip_address: string
      netmask: string
      gateway: string | null
      dns: string[]
    }
    os: string
    npu_available: boolean
  }
  camera: {
    online: boolean
    index: number
    width: number
    height: number
  }
  arm: {
    online: boolean
    state: string
    control_lock: string | null
  }
  vision: {
    model_loaded: boolean
    model_name: string
  }
  calibration: {
    ready: boolean
    version: string
  }
}

export interface Detection {
  object_id: string
  label: string
  category: MaterialCategory
  confidence: number
  bbox_norm: { cx: number; cy: number; w: number; h: number }
  pixel_center: { x_px: number; y_px: number }
  arm_position: { x_m: number; y_m: number; z_m: number } | null
}

export interface VisionDetectResult {
  frame_id: string
  image: { width: number; height: number }
  detections: Detection[]
}

export interface TaskCreateResult {
  task_id: string
  type: 'pick_sort' | 'stack'
  state: TaskState
}

export type TaskState =
  | 'queued'
  | 'detecting'
  | 'planning'
  | 'moving'
  | 'verifying'
  | 'succeeded'
  | 'failed'
  | 'cancelled'
  | 'paused'

export interface TaskDetail extends TaskCreateResult {
  progress: number
  current_step: string
  created_at: string
  updated_at: string
  result: Record<string, unknown> | null
}

export interface InventoryLocation {
  area: string
  shelf: string
  slot: string
}

export interface InventoryItem {
  item_id: string
  name: string
  category: MaterialCategory
  label: string
  quantity: number
  location: InventoryLocation
  created_at: string
  updated_at: string
}

export interface InventoryPage {
  items: InventoryItem[]
  page: number
  page_size: number
  total: number
}

export interface SystemEvent {
  event_id: string
  type: string
  time: string
  data: Record<string, unknown>
}

export interface JointAngles {
  joint1_deg: number
  joint2_deg: number
  joint3_deg: number
  joint4_deg: number
  joint5_deg: number
  joint6_deg: number
}
