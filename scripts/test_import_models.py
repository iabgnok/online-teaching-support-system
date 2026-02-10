import traceback
try:
    import models
    print('Imported models, has RaiseHandRecord =', hasattr(models, 'RaiseHandRecord'))
except Exception as e:
    print('Import failed:')
    traceback.print_exc()
