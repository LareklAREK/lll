#!/usr/bin/env python3
"""ЛР4, вариант 12: подсчёт нулей в R0 и R1 (результат в RQ) для кросс-системы GR1804.

Микропрограмма записана так же, как её набирают в GR1804 командой W:
адрес и поля M1..M15 в восьмеричной системе. Скрипт упаковывает её в файл
задачи LAB4.PZU, который кросс-система читает при старте («Считать файл задачи Y»).

Формат .PZU (GR1804 v1.0, 1993): каждая ячейка ПЗУ занимает 10 байт,
это 5 слов little-endian:
    addr, M1,
    w1 = M2 | M3<<2 | M5<<6 | M6<<11,
    w2 = M4 | M7<<4 | M8<<6 | M9<<8 | M10<<11 | M13<<14,
    w3 = M11 | M12<<3 | M14<<6 | M15<<8.

Использование:
    python3 make_lab4_pzu.py             записать LAB4.PZU и напечатать листинг
    python3 make_lab4_pzu.py --list F    напечатать листинг любого .PZU
    python3 make_lab4_pzu.py --selftest  сверить декодер с протоколами GR1804
"""
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "LAB4.PZU")

# Разрядность полей M1..M15
WIDTH = (16, 2, 4, 4, 5, 5, 2, 2, 3, 3, 3, 3, 2, 2, 8)

# Адр  M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15   (всё восьмеричное)
PROGRAM = [
    ("00", " 5  0  0 16  0  0  0  0  7  0  3  2  0  0  0", "R0 <- 000005 (M1->D, D+0 -> R0)"),
    ("01", " 1  0  0 16  0  1  0  0  7  0  3  2  0  0  0", "R1 <- 000001"),
    ("02", " 1  0  0 16  0  2  0  0  7  0  3  2  0  0  0", "R2 <- 000001 (маска)"),
    ("03", " 0  0  0 16  0  0  0  0  7  0  0  2  0  0  0", "RQ <- 0"),
    ("04", " 0  0  0 16  0  2  0  0  1  4  1  0  1  0  0", "R0 & R2 -> PSW (Z=1: разряд R0 = 0)"),
    ("05", "14  0  2  1  0  0  0  0  0  0  1  0  0  0  0", "CJS 14, если Z=1"),
    ("06", " 0  0  0 16  1  2  0  0  1  5  1  0  1  0  0", "not R1 & R2 -> PSW (Z=0: разряд R1 = 0)"),
    ("07", "14  1  2  1  0  0  0  0  0  0  1  0  0  0  0", "CJS 14, если Z=0 (инверсия условия)"),
    ("10", " 0  0  0 16  0  2  0  0  3  3  7  0  0  0  0", "R2 <- 2*R2, в младший разряд '0'"),
    ("11", " 0  0  0 16  0  2  0  0  3  3  1  0  1  0  0", "R2 -> PSW (проверка маски на 0)"),
    ("12", " 4  1  2  3  0  0  0  0  0  0  1  0  0  0  0", "CJP 04, если R2 != 0"),
    ("13", "13  0  0 17  0  0  0  0  0  0  1  0  0  0  0", "JP 13 - конец"),
    ("14", " 0  1  7 12  0  0  0  1  2  0  0  0  0  0  0", "ПП: RQ <- RQ+1; CRTN"),
]


def pack(f):
    for i, (v, w) in enumerate(zip(f, WIDTH)):
        if not 0 <= v < (1 << w):
            raise ValueError("M%d = %o вне диапазона" % (i + 1, v))
    m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15 = f
    w1 = m2 | m3 << 2 | m5 << 6 | m6 << 11
    w2 = m4 | m7 << 4 | m8 << 6 | m9 << 8 | m10 << 11 | m13 << 14
    w3 = m11 | m12 << 3 | m14 << 6 | m15 << 8
    return m1, w1, w2, w3


def unpack(m1, w1, w2, w3):
    return (m1, w1 & 3, w1 >> 2 & 15, w2 & 15, w1 >> 6 & 31, w1 >> 11 & 31,
            w2 >> 4 & 3, w2 >> 6 & 3, w2 >> 8 & 7, w2 >> 11 & 7,
            w3 & 7, w3 >> 3 & 7, w2 >> 14 & 3, w3 >> 6 & 3, w3 >> 8 & 255)


def encode(cells):
    """cells: {адрес: (M1..M15)} -> байты .PZU (ячейки 0..max подряд)."""
    out = bytearray()
    for addr in range(max(cells) + 1):
        f = cells.get(addr, (0,) * 15)
        out += struct.pack("<5H", addr, *pack(f))
    return bytes(out)


def decode(data):
    cells = {}
    for i in range(0, len(data) - 9, 10):
        addr, m1, w1, w2, w3 = struct.unpack_from("<5H", data, i)
        cells[addr] = unpack(m1, w1, w2, w3)
    return cells


HEADER = "Addr     M1  M2  M3  M4  M5  M6  M7  M8  M9 M10 M11 M12 M13 M14 M15"


def row(addr, f):
    return "%4o%7o" % (addr, f[0]) + "".join("%4o" % v for v in f[1:])


def listing(cells, notes=None):
    lines = [HEADER]
    for addr in sorted(cells):
        if any(cells[addr]):
            line = row(addr, cells[addr])
            if notes and addr in notes:
                line += "   ; " + notes[addr]
            lines.append(line)
    return "\n".join(lines)


def build():
    cells, notes = {}, {}
    for addr, fields, note in PROGRAM:
        a = int(addr, 8)
        cells[a] = tuple(int(x, 8) for x in fields.split())
        assert len(cells[a]) == 15, addr
        notes[a] = note
    return cells, notes


def selftest():
    """Сверка с файлами задач и протоколами, которые записала сама GR1804."""
    ref_dir = os.path.join(HERE, "..", "..", "2025-26", "Часть 2", "dosbox", "files", "K1804")
    pairs = [("PROBA1.DOC", "proba1.pzu"), ("PROBA2.DOC", "PROBA2.PZU"), ("PROBA6.DOC", "proba6.pzu")]
    checked = 0
    for doc, pzu in pairs:
        data = open(os.path.join(ref_dir, pzu), "rb").read()
        assert encode(decode(data)) == data, pzu + ": round-trip не совпал"
        cells = decode(data)
        text = open(os.path.join(ref_dir, doc), "rb").read().decode("cp866")
        lines = text.splitlines()
        for i, line in enumerate(lines[:-1]):
            if line.startswith("Addr"):
                ref = lines[i + 1].rstrip()
                addr = int(ref.split()[0], 8)
                got = row(addr, cells.get(addr, (0,) * 15))
                assert got == ref, "%s: %r != %r" % (pzu, got, ref)
                checked += 1
    cells, _ = build()
    assert decode(encode(cells)) == {a: cells.get(a, (0,) * 15) for a in range(max(cells) + 1)}
    print("selftest OK: %d строк протоколов GR1804 совпали, round-trip побайтовый" % checked)


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    if "--list" in sys.argv:
        path = sys.argv[sys.argv.index("--list") + 1]
        print(listing(decode(open(path, "rb").read())))
        return
    cells, notes = build()
    data = encode(cells)
    with open(OUT, "wb") as fh:
        fh.write(data)
    print(listing(cells, notes))
    print("\nЗаписан %s: %d ячеек, %d байт" % (OUT, len(data) // 10, len(data)))


if __name__ == "__main__":
    main()
