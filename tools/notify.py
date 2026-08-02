"""Play an attention sound — use when Claude needs Min specifically
(not just a routine status update).

Usage: python notify.py [urgent]
"""
import sys
import winsound

if len(sys.argv) > 1 and sys.argv[1] == "urgent":
    for _ in range(3):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        winsound.Beep(1000, 200)
else:
    winsound.MessageBeep(winsound.MB_ICONASTERISK)
