from itertools import product
from operator import concat
from mutagen.flac import FLAC
from io import BytesIO
import struct


class utils:
    def has_weird_tags(string):
        tags = ["E", "A", "M", "S"]
        combinations_3 = list(product(tags, repeat=3))
        combinations_3 = ["".join(comb) for comb in combinations_3]
        combinations_2 = list(product(tags, repeat=2))
        combinations_2 = ["".join(comb) for comb in combinations_2]
        tags = concat(tags, combinations_3)
        tags = concat(tags, combinations_2)
        tags = [f"[{tag}]" for tag in tags]
        if any(tag in string for tag in tags):
            return True
        return False

    def bytes_to_int(bytes: list) -> int:
        result = 0
        for byte in bytes:
            result = (result << 8) + byte
        return result

    def get_flac_duration(bytesio_obj):
        if bytesio_obj.getvalue().hex().find("664c6143") == -1:
            return "00:00:00"
        length_raw = FLAC(fileobj=BytesIO(bytesio_obj.getvalue())).info.length
        length = int(length_raw)
        return f"{length // 3600:02d}:{length % 3600 // 60:02d}:{length % 60:02d}"
