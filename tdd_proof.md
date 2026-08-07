# TDD Proof — Dynamic Ending Engine

## Step 2: RED Phase Failure Output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/dienk/chronicle_of_the_past
configfile: pyproject.toml
plugins: asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 0 items / 1 error                                                    

==================================== ERRORS ====================================
_____________________ ERROR collecting tests/test_story.py _____________________
ImportError while importing test module '/home/dienk/chronicle_of_the_past/tests/test_story.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_story.py:7: in <module>
    from src.engine.story import calculate_ending
E   ImportError: cannot import name 'calculate_ending' from 'src.engine.story' (/home/dienk/chronicle_of_the_past/src/engine/story.py)
=========================== short test summary info ============================
ERROR tests/test_story.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.10s ===============================
```
