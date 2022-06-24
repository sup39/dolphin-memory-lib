# SPDX-License-Identifier: MIT
'''
  Copyright (c) 2022 sup39

This file is based on Yoshi2's dolphin-memory-lib
https://github.com/RenolY2/dolphin-memory-lib
  Copyright (c) 2022 Yoshi2, NerduMiner

The find_dolphin function is based on WindowsDolphinProcess::findPID() from
aldelaro5's Dolphin memory engine
https://github.com/aldelaro5/Dolphin-memory-engine
  Copyright (c) 2017 aldelaro5
'''

import os
from struct import pack, unpack, calcsize
from multiprocessing.shared_memory import SharedMemory

if os.name == 'nt':
  # windows
  from ctypes import Structure, POINTER, sizeof, byref, windll
  from ctypes.wintypes import DWORD, ULONG, LONG, CHAR, MAX_PATH
  kernel32 = windll.kernel32
  NULL = 0
  ## https://docs.microsoft.com/ja-jp/windows/win32/api/tlhelp32/ns-tlhelp32-processentry32
  class PROCESSENTRY32(Structure):
    _fields_ = [
      ('dwSize', DWORD),
      ('cntUsage', DWORD),
      ('th32ProcessID', DWORD),
      ('th32DefaultHeapID', POINTER(ULONG)),
      ('th32ModuleID', DWORD),
      ('cntThreads', DWORD),
      ('th32ParentProcessID', DWORD),
      ('pcPriClassBase', LONG),
      ('dwFlags', DWORD),
      ('szExeFile', CHAR*MAX_PATH),
    ]
  ## https://docs.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot
  TH32CS_SNAPPROCESS = 2
  ## find pids of dolphin
  def find_dolphin():
    # prepare entry struct
    entry = PROCESSENTRY32()
    entry.dwSize = sizeof(PROCESSENTRY32)
    # prepare snapshot
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, NULL)
    # find pids
    pids = []
    if kernel32.Process32First(snapshot, byref(entry)):
      while True:
        if entry.szExeFile in (b'Dolphin.exe', b'DolphinQt2.exe', b'DolphinWx.exe'):
          pids.append(entry.th32ProcessID)
        if not kernel32.Process32Next(snapshot, byref(entry)): break
    kernel32.CloseHandle(snapshot);
    # done
    return pids
else:
  # UNIX
  import psutil
  def find_dolphin():
    return [
      proc.pid
      for proc in psutil.process_iter()
      if proc.name() in ('dolphin-emu', 'dolphin-emu-qt2', 'dolphin-emu-wx')
    ]

'''
@typedef {(int|str) | [(int|str), ...int[]]} Addr
  -- address or symbol name with arbitrary offsets
  -- e.g. 0x8040A378, 'gpMarioOriginal',
  --      (0x8040A2A8, 0x54), ('gpMap', 0x10, 0x04)
'''

class Dolphin():
  def __init__(self):
    self.pid = None
    self.memory = None
  def reset(self):
    self.pid = None
    self.memory = None
  def hook(self, pids=None):
    '''
      @params pids {None|int|Iterable<int>}
        -- pid or pid array of dolphin
      @returns {int|None}
        -- pid of hooked dolphin
    '''
    self.memory = None
    # init pids
    if pids is None: # auto-detect
      pids = Dolphin.find_dolphin()
    elif type(pids) is int: # pid -> [pid]
      pids = [pids]
    ## no process found
    if len(pids) == 0: return None
    # init memory
    for pid in pids:
      memory = Dolphin.init_shared_memory(pid)
      if memory is not None:
        self.pid = pid
        self.memory = memory
        return pid
    ## no memory found
    return None

  # virtual methods
  def get_symb_addr(self, name):
    '''
      @params {str} name
        -- name of the symbol
      @returns {int|never}
        -- addr of the symbol
    '''
    raise NotImplemented

  # private methods
  def _get_slice(self, addr, size):
    '''
      @params {int} addr
        -- memory address
      @params {int} size
        -- size of memory slice
      @returns {slice|never}
        -- slice object for self.memory at the address
    '''
    idx = addr - 0x8000_0000
    assert 0 <= idx < 0x0180_0000
    return slice(idx, idx+size)
  def _read_bytes(self, addr, size):
    '''
      @params {int} addr
        -- memory address
      @params {int} size
        -- size to read
      @returns {bytes|never}
        -- bytes at the address
    '''
    return self.memory.buf[self._get_slice(addr, size)].tobytes()
  def _write_bytes(self, addr, data):
    '''
      @params {int} addr
        -- memory address
      @params {bytes} data
        -- bytes to write
    '''
    self.memory.buf[self._get_slice(addr, len(data))] = data

  # public methods
  def try_resolve_addr(self, addr):
    '''
      @params {Addr} addr
        -- address or symbol name with arbitrary offsets
      @returns {int|None}
        -- (resolved address) or (None if NullPointerException occurred)
    '''
    try: addr, *offsets = addr
    except TypeError: offsets = []
    # resolve base
    if type(addr) == str:
      addr = self.get_symb_addr(addr)
    # offset
    for off in offsets:
      # dereference
      addr = unpack('>I', self._read_bytes(addr, 4))[0]
      # check nullptr
      if addr == 0: return None
      # add offset
      addr += off
    return addr
  def read_bytes(self, addr, size):
    '''
      @params {Addr} addr
        ## See `addr` of `try_resolve_addr()`
      @params {int} size
        -- size to read
      @returns {bytes|None}
        -- (bytes at addr) or (None if NullPointerException occurred)
    '''
    addr = self.try_resolve_addr(addr)
    if addr is None: return None
    return self._read_bytes(addr, size)
  def write_bytes(self, addr, data):
    '''
      @params {Addr} addr
        ## See `addr` of `try_resolve_addr()`
      @params {bytes} data
        -- bytes to write
      @returns {int|None}
        -- (written address) or (None if NullPointerException occurred)
    '''
    addr = self.try_resolve_addr(addr)
    if addr is None: return None
    self._write_bytes(addr, data)
    return addr
  def read_struct(self, addr, fmt):
    '''
      @params {Addr} addr
        ## See `addr` of `try_resolve_addr()`
      @params {int} size
        -- size to read
      @returns {bytes|None}
        ## See `addr` of `read_bytes()`
    '''
    data = self.read_bytes(addr, calcsize(fmt))
    return None if data is None else unpack(fmt, data)
  def write_struct(self, addr, fmt, *args):
    '''
      @params {Addr} addr
        ## See `addr` of `try_resolve_addr()`
      @params {str} fmt
        -- format string for struct.pack
      @params {...} *args
        -- args for struct.pack(fmt, *args)
      @returns {int|None}
        ## See `addr` of `write_bytes()`
    '''
    return self.write_bytes(addr, pack(fmt, *args))

  ## read single value from memory
  '''
    @params {Addr} addr
      ## See `addr` of `try_resolve_addr()`
    @returns {bytes|None}
      ## See `addr` of `read_bytes()`
  '''
  def read_uint32(self, addr): return self.read_struct(addr, '>I')[0]
  def read_uint16(self, addr): return self.read_struct(addr, '>H')[0]
  def read_uint8(self, addr): return self.read_struct(addr, '>B')[0]
  def read_int32(self, addr): return self.read_struct(addr, '>i')[0]
  def read_int16(self, addr): return self.read_struct(addr, '>h')[0]
  def read_int8(self, addr): return self.read_struct(addr, '>b')[0]
  def read_float(self, addr): return self.read_struct(addr, '>f')[0]
  ## write single value to memory
  '''
    @params {Addr} addr
      ## See `addr` of `try_resolve_addr()`
    @params {...} val
      -- value to write
    @returns {int|None}
      ## See `addr` of `write_bytes()`
  '''
  def write_uint32(self, addr, val): return self.write_struct(addr, '>I', val)
  def write_uint16(self, addr, val): return self.write_struct(addr, '>H', val)
  def write_uint8(self, addr, val): return self.write_struct(addr, '>B', val)
  def write_int32(self, addr, val): return self.write_struct(addr, '>i', val)
  def write_int16(self, addr, val): return self.write_struct(addr, '>h', val)
  def write_int8(self, addr, val): return self.write_struct(addr, '>b', val)
  def write_float(self, addr, val): return self.write_struct(addr, '>f', val)

  # static methods
  def init_shared_memory(pid):
    try: return SharedMemory('dolphin-emu.'+str(pid))
    except FileNotFoundError: return None
  find_dolphin = find_dolphin