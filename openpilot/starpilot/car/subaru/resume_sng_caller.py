"""Bind resume-only stock-ACC stop assistance to Card publications."""

from opendbc.car.structs import car

from openpilot.starpilot.car.subaru.resume_sng import Command, Runtime, Snapshot, eligible, requested


def update(card, cs, now_ns):
  controller = card.CI.CC
  controller.resume_sng_command = 0
  if not eligible(card.CP) or not requested(card.params):
    if hasattr(controller, "resume_sng"):
      controller.resume_sng.reset()
    return

  if not hasattr(controller, "resume_sng"):
    controller.resume_sng = Runtime()

  driver_button = any(button.pressed for button in cs.buttonEvents)
  snapshot = Snapshot(
    cruise_enabled=bool(cs.cruiseState.enabled),
    cruise_available=bool(cs.cruiseState.available),
    standstill=bool(cs.standstill or cs.cruiseState.standstill),
    gear_drive=cs.gearShifter == car.CarState.GearShifter.drive,
    can_valid=bool(cs.canValid),
    can_timeout=bool(cs.canTimeout),
    brake_pressed=bool(cs.brakePressed),
    gas_pressed=bool(cs.gasPressed),
    acc_faulted=bool(cs.accFaulted),
    steer_fault=bool(cs.steerFaultPermanent or cs.steerFaultTemporary),
    stock_aeb=bool(cs.stockAeb),
    lead_present=bool(getattr(cs, "sng_lead_present", False)),
    close_distance=float(getattr(cs, "close_distance", 0.0)),
    driver_button=driver_button,
  )
  command = controller.resume_sng.update(snapshot, now_ns)
  if command == Command.RESUME:
    controller.resume_sng_command = 1
    controller.resume_sng_command_ns = now_ns
