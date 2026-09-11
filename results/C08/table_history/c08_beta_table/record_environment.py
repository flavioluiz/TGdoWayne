import platform,sys,datetime,os
import numpy,scipy
from beta_builder import HERE,write_json,sha_file
report=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,executable=sys.executable,platform=platform.platform(),machine=platform.machine(),numpy=numpy.__version__,scipy=scipy.__version__,numpy_build=numpy.show_config(mode='dicts'),VECLIB_MAXIMUM_THREADS=os.environ.get('VECLIB_MAXIMUM_THREADS'),workers=1,Darwin_ru_maxrss_units='bytes, process historical resident high-water mark; not a memory-enforcement mechanism',RSS_ceiling_bytes=1610612736,estimated_numeric_ceiling_bytes=1073741824,source_sha256=sha_file(__file__),no_scientific_computation=True)
write_json(HERE/'environment.json',report)
