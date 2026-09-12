"""Bounded exact-byte cache for observation-independent covariance moments."""
from collections import OrderedDict
import copy
import hashlib
import os
import numpy as np


def array_digest(array):
    a=np.asarray(array)
    if a.dtype.hasobject:raise ValueError('Numeric arrays required')
    h=hashlib.sha256();h.update(a.dtype.str.encode());h.update(str(a.shape).encode());h.update(a.tobytes(order='C'))
    return h.digest()


class MomentCache:
    """Hash values, not object IDs or rounded coordinates; cache no densities."""
    def __init__(self,*,maximum_bytes=128*1024**2,maximum_entries=4096):
        if type(maximum_bytes)is not int or maximum_bytes<1 or type(maximum_entries)is not int or maximum_entries<1:
            raise ValueError('Explicit positive cache limits required')
        self.maximum_bytes=maximum_bytes;self.maximum_entries=maximum_entries;self.entries=OrderedDict();self.bytes=0
        self.hits=0;self.misses=0;self.pid=os.getpid()

    def get(self,geometry_key,C0,C1,compute):
        if os.getpid()!=self.pid:raise RuntimeError('Moment cache is single-process')
        key=(geometry_key,array_digest(C0),array_digest(C1))
        if key in self.entries:
            self.hits+=1;self.entries.move_to_end(key);values,checks,size=self.entries[key]
            return values[0],values[1],values[2],copy.deepcopy(checks)
        self.misses+=1;c0,c1,basis,checks=compute()
        arrays=[np.array(a,copy=True) for a in (c0,c1,*basis)]
        for a in arrays:a.setflags(write=False)
        size=sum(a.nbytes for a in arrays)
        if size>self.maximum_bytes:raise MemoryError('One moment entry exceeds the declared cache budget')
        while self.entries and (self.bytes+size>self.maximum_bytes or len(self.entries)>=self.maximum_entries):
            _,(_,_,old_size)=self.entries.popitem(last=False);self.bytes-=old_size
        values=(arrays[0],arrays[1],tuple(arrays[2:]));self.entries[key]=(values,copy.deepcopy(checks),size);self.bytes+=size
        return values[0],values[1],values[2],copy.deepcopy(checks)

    def statistics(self):
        return dict(hits=self.hits,misses=self.misses,entries=len(self.entries),numeric_bytes=self.bytes,
                    maximum_numeric_bytes=self.maximum_bytes,maximum_entries=self.maximum_entries,
                    key_and_metadata_overhead_not_in_numeric_bytes=True,new_density_values=0)
