import unittest

from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, DBC, SubaruSafetyFlags
from opendbc.safety.tests.libsafety import libsafety_py


class TestSubaruStockAccResume(unittest.TestCase):
  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.cp = CarInterface.get_params(CAR.SUBARU_IMPREZA_2025, {0: {}, 1: {}, 2: {}}, [], False, False, False)
    cfg = self.cp.safetyConfigs[0]
    self.assertTrue(cfg.safetyParam & SubaruSafetyFlags.STOCK_ACC_BUTTONS)
    self.assertEqual(self.safety.set_safety_hooks(cfg.safetyModel.raw, cfg.safetyParam), 0)
    self.safety.init_tests()
    self.packer = CANPacker(DBC[CAR.SUBARU_IMPREZA_2025][Bus.pt])

  def packet(self, **values):
    addr, dat, bus = self.packer.make_can_msg('ES_Distance', 1, values)
    return libsafety_py.make_CANPacket(addr, bus, dat)

  def test_resume_is_allowed_with_inactive_throttle(self):
    self.assertTrue(self.safety.safety_tx_hook(self.packet(COUNTER=1, Cruise_Throttle=1818, Cruise_Resume=1)))
    self.assertFalse(self.safety.safety_tx_hook(self.packet(COUNTER=2, Cruise_Throttle=808, Cruise_Resume=1)))
    self.assertFalse(self.safety.safety_tx_hook(self.packet(COUNTER=3, Cruise_Throttle=1818, Cruise_Set=1)))
    self.assertFalse(self.safety.safety_tx_hook(self.packet(COUNTER=4, Cruise_Throttle=1818, Cruise_Resume=1, Cruise_Set=1)))
    self.assertFalse(self.safety.safety_tx_hook(self.packet(COUNTER=5, Cruise_Throttle=1818)))
