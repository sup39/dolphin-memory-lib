# Change Log
## \[v0.1.1] use psutil to find pid of dolphin (2022/06/26)
Use psutil to achieve cross-platform pid finding.
This also fixes the dependency issue on Linux.

## \[v0.1.0] pack into one PyPI package (2022/06/25)
Complete all basic functions, including:
- find dolphin, init shared memory
- read/write raw bytes
- read/write struct
- read/write single value (uint32/16/8, int32/16/8, float)

## Base
This library is based on [Yoshi2's dolphin-memory-lib](https://github.com/RenolY2/dolphin-memory-lib)
```
Copyright (c) 2022 Yoshi2, NerduMiner
```
and [aldelaro5's Dolphin-memory-engine](https://github.com/aldelaro5/Dolphin-memory-engine)
```
Copyright (c) 2017 aldelaro5
```
