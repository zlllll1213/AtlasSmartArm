from itertools import count

from src.backend.errors import ApiError
from src.backend.models.schemas import (
    AuditRequest,
    InventoryItemCreate,
    InventoryItemUpdate,
    StockMovementRequest,
)
from src.backend.services.event_bus import EventBus
from src.backend.time_utils import utc_now_iso


class InventoryService:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._counter = count(1)
        self._items: dict[str, dict[str, object]] = {}
        self.create(
            InventoryItemCreate(
                name="绝缘子",
                category="power_fitting",
                label="insulator",
                quantity=12,
                location={"area": "A", "shelf": "A-01", "slot": "A-01-03"},
            )
        )

    def list(self, page: int, page_size: int) -> dict[str, object]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        items = list(self._items.values())
        start = (page - 1) * page_size
        end = start + page_size
        return {"items": items[start:end], "page": page, "page_size": page_size, "total": len(items)}

    def create(self, request: InventoryItemCreate) -> dict[str, object]:
        now = utc_now_iso()
        item_id = f"item_{next(self._counter):06d}"
        item = {
            "item_id": item_id,
            **request.model_dump(mode="json"),
            "created_at": now,
            "updated_at": now,
        }
        self._items[item_id] = item
        self.event_bus.publish("inventory.item.updated", {"item_id": item_id, "action": "created"})
        return item

    def get(self, item_id: str) -> dict[str, object]:
        try:
            return self._items[item_id]
        except KeyError as exc:
            raise ApiError("NOT_FOUND", "Inventory item not found.", 404, {"item_id": item_id}) from exc

    def update(self, item_id: str, request: InventoryItemUpdate) -> dict[str, object]:
        item = self.get(item_id)
        changes = request.model_dump(mode="json", exclude_unset=True)
        item.update(changes)
        item["updated_at"] = utc_now_iso()
        self.event_bus.publish("inventory.item.updated", {"item_id": item_id, "action": "updated"})
        return item

    def inbound(self, request: StockMovementRequest) -> dict[str, object]:
        item = self.get(request.item_id)
        item["quantity"] = int(item["quantity"]) + request.quantity
        item["updated_at"] = utc_now_iso()
        self.event_bus.publish("inventory.item.updated", {"item_id": request.item_id, "action": "inbound"})
        return item

    def outbound(self, request: StockMovementRequest) -> dict[str, object]:
        item = self.get(request.item_id)
        if int(item["quantity"]) < request.quantity:
            raise ApiError(
                "OUT_OF_RANGE",
                "Outbound quantity exceeds stock.",
                400,
                {"item_id": request.item_id, "available": item["quantity"]},
            )
        item["quantity"] = int(item["quantity"]) - request.quantity
        item["updated_at"] = utc_now_iso()
        self.event_bus.publish("inventory.item.updated", {"item_id": request.item_id, "action": "outbound"})
        return item

    def audit(self, request: AuditRequest) -> dict[str, object]:
        item = self.get(request.item_id)
        previous_quantity = item["quantity"]
        item["quantity"] = request.counted_quantity
        item["updated_at"] = utc_now_iso()
        self.event_bus.publish("inventory.item.updated", {"item_id": request.item_id, "action": "audit"})
        return {
            "item": item,
            "previous_quantity": previous_quantity,
            "counted_quantity": request.counted_quantity,
            "operator": request.operator,
            "reason": request.reason,
        }
