import asyncio
from typing import Annotated

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect

from src.backend.models.schemas import (
    AuditRequest,
    CalibrationOffsetRequest,
    FKRequest,
    IKRequest,
    InventoryItemCreate,
    InventoryItemUpdate,
    MoveRequest,
    PickSortRequest,
    StackRequest,
    StockMovementRequest,
    VisionDetectRequest,
)
from src.backend.response import ok
from src.backend.services.container import Services
from src.backend.time_utils import utc_now_iso

api_router = APIRouter(prefix="/api/v1")
ws_router = APIRouter(prefix="/ws/v1")


def services_from(request: Request) -> Services:
    return request.app.state.services


@api_router.get("/health")
def health(request: Request):
    services = services_from(request)
    return ok(
        request,
        {
            "service": "atlas-smart-arm-backend",
            "status": "ok",
            "version": services.settings.app_version,
            "time": utc_now_iso(),
        },
    )


@api_router.get("/system/status")
def system_status(request: Request):
    return ok(request, services_from(request).system.status())


@api_router.post("/vision/detect")
def vision_detect(request: Request, payload: VisionDetectRequest):
    data = services_from(request).vision.detect(payload)
    services_from(request).event_bus.publish("vision.detection.created", data)
    return ok(request, data)


@api_router.get("/calibration/status")
def calibration_status(request: Request):
    return ok(request, services_from(request).calibration.status())


@api_router.put("/calibration/offset")
def calibration_offset(request: Request, payload: CalibrationOffsetRequest):
    return ok(request, services_from(request).calibration.update_offset(payload))


@api_router.post("/arm/kinematics/fk")
def arm_fk(request: Request, payload: FKRequest):
    return ok(request, services_from(request).arm.fk(payload.joints))


@api_router.post("/arm/kinematics/ik")
def arm_ik(request: Request, payload: IKRequest):
    return ok(request, services_from(request).arm.ik(payload.pose))


@api_router.post("/arm/move")
def arm_move(request: Request, payload: MoveRequest):
    return ok(request, services_from(request).arm.move(payload))


@api_router.post("/arm/emergency-stop")
def arm_emergency_stop(request: Request):
    return ok(request, services_from(request).arm.emergency_stop())


@api_router.post("/tasks/pick-sort")
def create_pick_sort_task(request: Request, payload: PickSortRequest):
    return ok(request, services_from(request).tasks.create_pick_sort(payload))


@api_router.post("/tasks/stack")
def create_stack_task(request: Request, payload: StackRequest):
    return ok(request, services_from(request).tasks.create_stack(payload))


@api_router.get("/tasks/{task_id}")
def get_task(request: Request, task_id: str):
    return ok(request, services_from(request).tasks.get(task_id))


@api_router.post("/tasks/{task_id}/cancel")
def cancel_task(request: Request, task_id: str):
    return ok(request, services_from(request).tasks.cancel(task_id))


@api_router.get("/inventory/items")
def list_inventory_items(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return ok(request, services_from(request).inventory.list(page, page_size))


@api_router.post("/inventory/items")
def create_inventory_item(request: Request, payload: InventoryItemCreate):
    return ok(request, services_from(request).inventory.create(payload))


@api_router.get("/inventory/items/{item_id}")
def get_inventory_item(request: Request, item_id: str):
    return ok(request, services_from(request).inventory.get(item_id))


@api_router.put("/inventory/items/{item_id}")
def update_inventory_item(request: Request, item_id: str, payload: InventoryItemUpdate):
    return ok(request, services_from(request).inventory.update(item_id, payload))


@api_router.post("/inventory/inbound")
def inventory_inbound(request: Request, payload: StockMovementRequest):
    return ok(request, services_from(request).inventory.inbound(payload))


@api_router.post("/inventory/outbound")
def inventory_outbound(request: Request, payload: StockMovementRequest):
    return ok(request, services_from(request).inventory.outbound(payload))


@api_router.post("/inventory/audit")
def inventory_audit(request: Request, payload: AuditRequest):
    return ok(request, services_from(request).inventory.audit(payload))


@ws_router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    await websocket.accept()
    services: Services = websocket.app.state.services
    await websocket.send_json(
        {
            "event_id": "evt_connection_opened",
            "type": "system.status.changed",
            "time": utc_now_iso(),
            "data": services.system.status(),
        }
    )
    try:
        while True:
            # WebSocket is a live refresh channel; REST remains the source of truth.
            await asyncio.sleep(2)
            for event in services.event_bus.latest(limit=5):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return
