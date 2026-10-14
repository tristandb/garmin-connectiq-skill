#!/usr/bin/env python3
"""Put a .prg on a Garmin watch that connects over MTP (Forerunner 255/955, fenix 7 and newer on macOS).

  mtp_send.py <file.prg>          # send to GARMIN/Apps on the watch
  mtp_send.py --list              # show folders and storage ids

Needs libmtp (brew install libmtp). The stock mtp-sendfile fails on these watches ("Error sending
file") because they expose several storage ids; this script finds the Apps folder and sends with
its storage id. Do not run OpenMTP or Garmin Express at the same time, they claim the device.
"""
import ctypes
import os
import sys
import time

# libmtp prints "MTP extended association type ... encountered" to stderr once per folder; silence
# it only around libmtp calls so this script's own messages stay visible.
_devnull = os.open(os.devnull, os.O_WRONLY)
_stderr_copy = os.dup(2)


def quiet(on):
    os.dup2(_devnull if on else _stderr_copy, 2)


lib = ctypes.CDLL("/opt/homebrew/lib/libmtp.dylib")


class File(ctypes.Structure):
    _fields_ = [("item_id", ctypes.c_uint32), ("parent_id", ctypes.c_uint32), ("storage_id", ctypes.c_uint32),
                ("filename", ctypes.c_char_p), ("filesize", ctypes.c_uint64), ("modificationdate", ctypes.c_long),
                ("filetype", ctypes.c_int), ("next", ctypes.c_void_p)]


class Folder(ctypes.Structure):
    pass


Folder._fields_ = [("folder_id", ctypes.c_uint32), ("parent_id", ctypes.c_uint32), ("storage_id", ctypes.c_uint32),
                   ("name", ctypes.c_char_p), ("sibling", ctypes.POINTER(Folder)), ("child", ctypes.POINTER(Folder))]

lib.LIBMTP_Get_First_Device.restype = ctypes.c_void_p
lib.LIBMTP_new_file_t.restype = ctypes.POINTER(File)
lib.LIBMTP_Send_File_From_File.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(File), ctypes.c_void_p, ctypes.c_void_p]
lib.LIBMTP_Dump_Errorstack.argtypes = [ctypes.c_void_p]
lib.LIBMTP_Release_Device.argtypes = [ctypes.c_void_p]
lib.LIBMTP_Get_Folder_List.restype = ctypes.POINTER(Folder)
lib.LIBMTP_Get_Folder_List.argtypes = [ctypes.c_void_p]


def walk(node, depth=0):
    while node:
        yield node.contents, depth
        yield from walk(node.contents.child, depth + 1)
        node = node.contents.sibling


if len(sys.argv) < 2:
    sys.exit(__doc__)
local = sys.argv[1]
quiet(True)
lib.LIBMTP_Init()
dev = lib.LIBMTP_Get_First_Device()
folders = list(walk(lib.LIBMTP_Get_Folder_List(dev))) if dev else []
quiet(False)
if not dev:
    sys.exit("No MTP device found. Is the watch connected, and are OpenMTP/Garmin Express closed?")
if "--list" in sys.argv:
    for f, d in folders:
        print(f"{'  ' * d}{f.name.decode()}  id={f.folder_id} storage=0x{f.storage_id:08x}")
    lib.LIBMTP_Release_Device(dev)
    sys.exit(0)
apps = [f for f, d in folders if f.name.lower() == b"apps"]
if not apps:
    sys.exit("Folder GARMIN/Apps not found on the watch")
target = apps[0]
f = lib.LIBMTP_new_file_t()
f.contents.filename = ctypes.c_char_p(os.path.basename(local).encode())
f.contents.filesize = os.path.getsize(local)
f.contents.modificationdate = int(time.time())
f.contents.parent_id = target.folder_id
f.contents.storage_id = target.storage_id
f.contents.filetype = 44  # LIBMTP_FILETYPE_UNKNOWN
quiet(True)
rc = lib.LIBMTP_Send_File_From_File(dev, local.encode(), f, None, None)
quiet(False)
if rc == 0:
    print(f"{os.path.basename(local)} -> GARMIN/Apps ({os.path.getsize(local)} bytes). Disconnect the watch; it installs the app itself.")
else:
    print("Sending failed:")
    lib.LIBMTP_Dump_Errorstack(dev)
lib.LIBMTP_Release_Device(dev)
sys.exit(rc)
