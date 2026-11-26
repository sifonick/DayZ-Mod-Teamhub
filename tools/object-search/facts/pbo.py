"""Minimal reader for Bohemia PBO archives (read-only)."""
import struct

CPRS = 0x43707273  # 'Cprs' : LZSS compressed entry
VERS = 0x56657273  # 'Vers' : header/properties entry


def _cstr(buf, pos):
    end = buf.index(b"\0", pos)
    return buf[pos:end].decode("latin-1"), end + 1


def lzss_decompress(data, out_len):
    out = bytearray()
    i = 0
    while len(out) < out_len and i < len(data):
        flags = data[i]; i += 1
        for bit in range(8):
            if len(out) >= out_len or i >= len(data):
                break
            if flags & (1 << bit):
                out.append(data[i]); i += 1
            else:
                if i + 1 >= len(data):
                    break
                b1, b2 = data[i], data[i + 1]; i += 2
                rpos = len(out) - ((b1 | ((b2 & 0xF0) << 4)))
                rlen = (b2 & 0x0F) + 3
                for k in range(rlen):
                    p = rpos + k
                    out.append(out[p] if 0 <= p < len(out) else 0x20)
    return bytes(out[:out_len])


def read_pbo(path):
    """Yield (name, bytes) for each file in the PBO, and return the prefix via .prefix."""
    with open(path, "rb") as fh:
        buf = fh.read()
    pos, entries, props = 0, [], {}
    first = True
    while True:
        name, pos = _cstr(buf, pos)
        method, orig, _res, _ts, size = struct.unpack_from("<5I", buf, pos); pos += 20
        if first and name == "" and method == VERS:
            while True:
                k, pos = _cstr(buf, pos)
                if not k:
                    break
                v, pos = _cstr(buf, pos)
                props[k] = v
            first = False
            continue
        first = False
        if name == "":
            break
        entries.append((name, method, orig, size))
    data_pos = pos
    files = []
    for name, method, orig, size in entries:
        raw = buf[data_pos:data_pos + size]
        data_pos += size
        if method == CPRS and orig and orig != size:
            raw = lzss_decompress(raw, orig)
        files.append((name.replace("\\", "/"), raw))
    return props.get("prefix", "").replace("\\", "/").strip("/"), files
