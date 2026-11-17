from dataclasses import replace

from openpilot.starpilot.car.subaru.resume_sng import Command, Runtime, Snapshot

BASE = dict(cruise_enabled=True, cruise_available=True, standstill=True, gear_drive=True,
            can_valid=True, can_timeout=False, brake_pressed=False, gas_pressed=False,
            acc_faulted=False, steer_fault=False, stock_aeb=False, lead_present=True,
            close_distance=4.0, driver_button=False)


def test_resume_after_stopped_lead_departs():
  runtime = Runtime()
  snapshot = Snapshot(**BASE)
  assert runtime.update(snapshot, 1_000_000_000) == Command.NONE
  assert runtime.update(snapshot, 1_600_000_000) == Command.NONE
  assert runtime.update(replace(snapshot, lead_present=False), 1_700_000_000) == Command.NONE
  assert runtime.update(replace(snapshot, lead_present=False), 2_100_000_000) == Command.RESUME
  assert runtime.update(replace(snapshot, lead_present=False), 2_200_000_000) == Command.NONE


def test_resume_requires_a_lead_to_have_been_seen():
  runtime = Runtime()
  snapshot = Snapshot(**{**BASE, "lead_present": False})
  assert runtime.update(snapshot, 1_000_000_000) == Command.NONE
  assert runtime.update(snapshot, 2_000_000_000) == Command.NONE


def test_moving_or_driver_button_cancels_pending_resume():
  runtime = Runtime()
  snapshot = Snapshot(**BASE)
  assert runtime.update(snapshot, 1_000_000_000) == Command.NONE
  assert runtime.update(replace(snapshot, standstill=False), 1_700_000_000) == Command.NONE
  assert runtime.update(replace(snapshot, driver_button=True), 2_000_000_000) == Command.NONE
