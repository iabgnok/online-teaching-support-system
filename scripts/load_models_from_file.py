import importlib.util, traceback
try:
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    models_path = os.path.join(project_root, 'models.py')
    spec = importlib.util.spec_from_file_location('models_local', models_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print('Loaded models_local, has RaiseHandRecord =', hasattr(m, 'RaiseHandRecord'))
except Exception:
    traceback.print_exc()
