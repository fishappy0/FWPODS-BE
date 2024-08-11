from itertools import product
from operator import concat
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

    def get_flac_duration(file_obj):
        if file_obj.read(4) != b"fLaC":
            return "00:00:00"
        header = file_obj.read(4)
        while len(header):
            meta = struct.unpack("4B", header)
            block_type = meta[0] & 0x7F
            size = utils.bytes_to_int(header[1:4])

            if block_type == 0:
                streaminfo_header = file_obj.read(size)
                unpacked = struct.unpack("2H3p3p8B16p", streaminfo_header)
                """
                https://xiph.org/flac/format.html#metadata_block_streaminfo
                16 (unsigned short)  | The minimum block size (in samples)
                                       used in the stream.
                16 (unsigned short)  | The maximum block size (in samples)
                                       used in the stream. (Minimum blocksize
                                       == maximum blocksize) implies a
                                       fixed-blocksize stream.
                24 (3 char[])        | The minimum frame size (in bytes) used
                                       in the stream. May be 0 to imply the
                                       value is not known.
                24 (3 char[])        | The maximum frame size (in bytes) used
                                       in the stream. May be 0 to imply the
                                       value is not known.
                20 (8 unsigned char) | Sample rate in Hz. Though 20 bits are
                                       available, the maximum sample rate is
                                       limited by the structure of frame
                                       headers to 655350Hz. Also, a value of 0
                                       is invalid.
                3  (^)               | (number of channels)-1. FLAC supports
                                       from 1 to 8 channels
                5  (^)               | (bits per sample)-1. FLAC supports from
                                       4 to 32 bits per sample. Currently the
                                       reference encoder and decoders only
                                       support up to 24 bits per sample.
                36 (^)               | Total samples in stream. 'Samples'
                                       means inter-channel sample, i.e. one
                                       second of 44.1Khz audio will have 44100
                                       samples regardless of the number of
                                       channels. A value of zero here means
                                       the number of total samples is unknown.
                128 (16 char[])      | MD5 signature of the unencoded audio
                                       data. This allows the decoder to
                                       determine if an error exists in the
                                       audio data even when the error does not
                                       result in an invalid bitstream.
                """

                samplerate = utils.bytes_to_int(unpacked[4:7]) >> 4
                sample_bytes = [(unpacked[7] & 0x0F)] + list(unpacked[8:12])
                total_samples = utils.bytes_to_int(sample_bytes)
                duration = float(total_samples) / samplerate
                return duration
            header = file_obj.read(4)
