import struct
import os
from typing import Generator
import shutil

"""
Format:
| 2 bytes key len | 4 byte value len | key | value |
keys are in utf-8
"""

class KVBinStore:
    """
    A class to handle the reading and writing of key-value pairs in a binary file.
    """

    def __init__(self, filename:str):
        self.filename = filename

    def __getitem__(self,key:str):
        return self.get(key)

    def __setitem__(self, key:str, value:bytes):
        self.set(key, value)

    def get(self, key:str, default=None):
        """
        Retrieves the value associated with the given key from the binary file.
        """
        for k, value in self.iterator(keyscan=True):
            if k == key:
                return value()
         
        return default
    
    def iterator(self, key:bool = False, value:bool = False, keyscan:bool = False):
        """
        Returns an iterator that yields key-value pairs from the binary file.
        """
        if os.path.isfile(self.filename):
            with open(self.filename, 'rb') as f:
                while True:
                    sizes = f.read(6)
                    if not sizes or len(sizes) != 6:
                        break
                    key_len, value_len = struct.unpack('<HL', sizes)
                    read_key = None
                    if key or keyscan:
                        read_key = f.read(key_len).decode('utf-8')
                    else:
                        f.seek(key_len, 1)
                    
                    value_fetched = False
                    
                    def fetch_value(need_fetch:bool = True):
                        nonlocal value_fetched
                        if not value_fetched:
                            v = None
                            if need_fetch:
                                v = f.read(value_len)
                            else:
                                f.seek(value_len, 1)
                            value_fetched = True
                            return v
                            
                    if keyscan:
                        yield read_key, lambda: fetch_value(True)
                        if not value_fetched:
                            fetch_value(False)
                    else:
                        yield read_key, fetch_value(value)
    
    def items(self) -> list[str, bytes]:
        return self.iterator(key=True, value=True)
    
    def keys(self) -> Generator[str, None, None]:
        for k, _ in self.iterator(key=True, value=False):
            yield k
    
    def values(self) -> Generator[bytes, None, None]:
        for _, v in self.iterator(key=False, value=True):
            yield v
    
    def __dict__(self):
        """
        Returns a dictionary representation of the key-value pairs in the binary file.
        """
        return dict(self.items())
    
    def set(self, key:str, value:bytes):
        if not isinstance(value, bytes):
            raise TypeError("Value must be of type bytes")
        swap_path = self.filename+".swap"
        with open(swap_path, "wb") as f:
            f.write(struct.pack('<HL', len(key), len(value)))
            f.write(key.encode('utf-8') + value)
            for k, v in self.items():
                if k != key:
                    f.write(struct.pack('<HL', len(k), len(v)))
                    f.write(k.encode('utf-8') + v)
        shutil.move(swap_path, self.filename)
    
    def delete(self, key:str):
        """
        Deletes the key-value pair associated with the given key from the binary file.
        """
        swap_path = self.filename+".swap"
        with open(swap_path, "wb") as f:
            for k, v in self.items():
                if k != key:
                    f.write(struct.pack('<HL', len(k), len(v)))
                    f.write(k.encode('utf-8') + v)
        shutil.move(swap_path, self.filename)
    
    def __delitem__(self, key:str):
        self.delete(key)
