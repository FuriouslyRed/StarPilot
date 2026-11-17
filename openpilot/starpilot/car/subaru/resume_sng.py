"""Resume-only stock-ACC stop assistance.

The factory ACC remains the longitudinal owner. This controller never sends
throttle or brake; it only asks the factory ACC to resume after a stopped lead
has departed.
"""

from dataclasses import dataclass
from enum import IntEnum

from opendbc.car.subaru.sng import resume_eligible

KEY = "SubaruSNG"


class Command(IntEnum):
  NONE = 0
  RESUME = 1


@dataclass(frozen=True)
class Snapshot:
  cruise_enabled: bool
  cruise_available: bool
  standstill: bool
  gear_drive: bool
  can_valid: bool
  can_timeout: bool
  brake_pressed: bool
  gas_pressed: bool
  acc_faulted: bool
  steer_fault: bool
  stock_aeb: bool
  lead_present: bool
  close_distance: float
  driver_button: bool


def eligible(cp) -> bool:
  return resume_eligible(cp)


def requested(params) -> bool:
  try:
    return params.get(KEY) in (b"1", "1", True)
  except (AttributeError, TypeError, ValueError):
    return False


class Runtime:
  """One RESUME pulse after a stopped lead departs."""

  def __init__(self, *, min_stop_ns: int = 500_000_000, departure_ns: int = 300_000_000,
               distance_delta: float = 1.0):
    self.min_stop_ns = int(min_stop_ns)
    self.departure_ns = int(departure_ns)
    self.distance_delta = float(distance_delta)
    self.reset()

  def reset(self) -> None:
    self.stop_since_ns = 0
    self.lead_seen = False
    self.lead_gone_since_ns = 0
    self.last_distance = None
    self.sent = False

  def update(self, snapshot: Snapshot, now_ns: int) -> Command:
    if (not snapshot.cruise_enabled or not snapshot.cruise_available or
        not snapshot.can_valid or snapshot.can_timeout or not snapshot.gear_drive or
        snapshot.brake_pressed or snapshot.gas_pressed or snapshot.acc_faulted or
        snapshot.steer_fault or snapshot.stock_aeb or snapshot.driver_button):
      self.reset()
      return Command.NONE

    if not snapshot.standstill:
      self.reset()
      return Command.NONE

    if not self.stop_since_ns:
      self.stop_since_ns = int(now_ns)
      self.last_distance = None

    if snapshot.lead_present:
      self.lead_seen = True
      self.lead_gone_since_ns = 0
      if (self.last_distance is not None and
          snapshot.close_distance >= self.last_distance + self.distance_delta):
        self.lead_gone_since_ns = self.lead_gone_since_ns or int(now_ns)
      self.last_distance = float(snapshot.close_distance)
    elif self.lead_seen:
      if not self.lead_gone_since_ns:
        self.lead_gone_since_ns = int(now_ns)
    else:
      self.lead_gone_since_ns = 0

    stopped_long_enough = now_ns - self.stop_since_ns >= self.min_stop_ns
    departed = bool(self.lead_seen and self.lead_gone_since_ns and
                    now_ns - self.lead_gone_since_ns >= self.departure_ns)
    if not self.sent and stopped_long_enough and departed:
      self.sent = True
      return Command.RESUME
    return Command.NONE
