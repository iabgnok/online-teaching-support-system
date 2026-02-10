import importlib, traceback
try:
    importlib.import_module('models')
    print('models imported ok')
except Exception:
    traceback.print_exc()
