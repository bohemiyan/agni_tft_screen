from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/")
async def get_sensors(request: Request):
    # Returns a list of all active sensor identifiers
    worker = request.app.state.worker
    if worker:
        return [{"name": name, "value": name} for name in worker.sensors.keys()]
    return []
