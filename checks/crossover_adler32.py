#!/usr/bin/env python3
"""Linux host check of the patched UWP DSP checksum against Python's zlib.

Run: python checks/crossover_adler32.py /path/to/prepared/windwaker
Requires g++ (or CXX), with no game disc or assets.
"""
import argparse
import ctypes
import os
from pathlib import Path
import random
import subprocess
import tempfile
import zlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('windwaker', type=Path)
    args = parser.parse_args()
    source = (args.windwaker / 'native/dsp_hle/dsp_common_shim.cpp').read_text()
    # Compile the actual function body, without the unrelated Dolphin services.
    body = source[source.index('u32 HashAdler32('):source.index('\nvoid ToLower(')]
    program = ('#include <algorithm>\n#include <cstdint>\n#include <cstddef>\n'
               'using u8=uint8_t; using u32=uint32_t;\n#define COS_UWP 1\n'
               'extern "C" {\n' + body + '\n}\n')
    with tempfile.TemporaryDirectory(prefix='crossover-adler-') as temp:
        library = Path(temp) / 'checksum.so'
        subprocess.run([os.environ.get('CXX', 'g++'), '-O2', '-std=c++20',
                        '-shared', '-fPIC', '-x', 'c++', '-', '-o', str(library)],
                       input=program, text=True, check=True)
        fn = ctypes.CDLL(str(library)).HashAdler32
        fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        fn.restype = ctypes.c_uint32
        rng = random.Random(4107)
        sizes = [0, 1, 2, 255, 256, 5551, 5552, 5553, 65535, 65536, 1048576]
        sizes += [rng.randrange(150000) for _ in range(100)]
        count = 0
        for size in sizes:
            for data in [bytes(size), b'\xff' * size, rng.randbytes(size)]:
                buffer = ctypes.create_string_buffer(data)
                actual, expected = fn(buffer, len(data)), zlib.adler32(data)
                if actual != expected:
                    raise AssertionError(f'{size} bytes: {actual:#x} != {expected:#x}')
                count += 1
        if fn(None, 0) != 1 or fn(None, 50000) != 1:
            raise AssertionError('Null-input semantics differ from zlib')
    print(f'{count} C++ checksum comparisons against zlib passed; null input passed.')


if __name__ == '__main__':
    main()
