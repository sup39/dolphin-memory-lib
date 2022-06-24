import unittest
from dolphin.memorylib import Dolphin

class TestMemorylib(unittest.TestCase):
  def test_rw_uint32(self):
    dolphin = Dolphin()
    import multiprocessing
    self.assertIsNotNone(dolphin.hook(), msg='No game is running')

    from random import randint
    from timeit import default_timer
    start = default_timer()

    print("Testing Shared Memory Method")
    start = default_timer()
    count = 500000
    for i in range(count):
      value = randint(0, 2**32-1)
      dolphin.write_uint32(0x80000000, value)
      result = dolphin.read_uint32(0x80000000)
      self.assertEqual(result, value)
    diff = default_timer()-start
    print(count/diff, "per sec")
    print("time: ", diff)

if __name__ == '__main__':
  unittest.main()
