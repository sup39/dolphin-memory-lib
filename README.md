# dolphin-memory-lib
A Python library for reading and writing the memory of an emulated game in Dolphin.

## Usage
```python
from dolphin.memorylib import Dolphin
if dolphin.hook() is None:
  print('No game is running')

addr = 0x80000000
dolphin.write_uint32(addr, 39)
result = dolphin.read_uint32(0x80000000)
# assert result == 39
```
