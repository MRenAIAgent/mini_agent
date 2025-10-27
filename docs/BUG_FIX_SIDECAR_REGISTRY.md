# Bug Fix: SidecarRegistry Boolean Evaluation

## Issue

The persistent agent tests were failing with:
```
RuntimeError: Sidecars not enabled. Set enable_sidecars=True when creating agent.
```

Even though sidecars were enabled and the registry was created.

## Root Cause

The `SidecarRegistry` class implements a `__len__` method:

```python
# sidecars/base.py:222-223
def __len__(self) -> int:
    return len(self._sidecars)
```

In Python, when an object has a `__len__` method, `bool(obj)` returns:
- `True` if `len(obj) > 0`
- `False` if `len(obj) == 0`

When a `SidecarRegistry` is first created, `self._sidecars` is an empty dict `{}`, so:
- `len(registry)` = 0
- `bool(registry)` = False
- `if not registry:` = **True** (even though the object exists!)

## The Bug

Several methods in `agent.py` checked for sidecar availability using:

```python
if not self.sidecar_registry:  # ❌ WRONG - checks if empty!
    raise RuntimeError("Sidecars not enabled...")
```

This was checking if the registry was **empty**, not if it was **None**.

Since the registry is created with no sidecars registered yet, `bool(registry)` evaluated to `False`, causing the error.

## The Fix

Changed all boolean checks to explicit `is None` checks:

**Before:**
```python
if not self.sidecar_registry:
    raise RuntimeError("Sidecars not enabled...")
```

**After:**
```python
if self.sidecar_registry is None:
    raise RuntimeError("Sidecars not enabled...")
```

## Files Changed

### agent.py

Fixed 7 occurrences:

1. **Line 250**: `_register_default_sidecars()`
   - Changed: `if not self.sidecar_registry:` → `if self.sidecar_registry is None:`

2. **Line 279**: `register_sidecar()`
   - Changed: `if not self.sidecar_registry:` → `if self.sidecar_registry is None:`

3. **Line 291**: `unregister_sidecar()`
   - Changed: `if self.sidecar_registry:` → `if self.sidecar_registry is not None:`

4. **Line 296**: `get_sidecars()`
   - Changed: `if self.sidecar_registry:` → `if self.sidecar_registry is not None:`

5. **Line 302**: `get_sidecar_stats()`
   - Changed: `if self.sidecar_executor:` → `if self.sidecar_executor is not None:`

6. **Line 325**: `_trigger_sidecars()`
   - Changed: `if not self.sidecar_executor:` → `if self.sidecar_executor is None:`

7. **Line 329**: `_trigger_sidecars()`
   - Changed: `if self.sidecar_registry else` → `if self.sidecar_registry is not None else`

Also fixed in `stop()` method:
- Line 235: `if self.sidecar_executor:` → `if self.sidecar_executor is not None:`
- Line 238: `if self.memory_manager:` → `if self.memory_manager is not None:`

## Test Results

### Before Fix
```
FAILED tests/test_persistent_agent.py::test_concurrent_sessions_no_race_condition
RuntimeError: Sidecars not enabled. Set enable_sidecars=True when creating agent.
```

### After Fix
```
============================== 6 passed in 0.56s ===============================
```

All tests now pass:
- ✅ `test_concurrent_sessions_no_race_condition` - Thread-safety verified
- ✅ `test_session_parameter_overrides_instance_session` - Session override works
- ✅ `test_fallback_to_instance_session` - Fallback works
- ✅ `test_persistent_sidecar_executor` - Executor persists across requests
- ✅ `test_run_without_session_parameter_still_works` - Backward compatible
- ✅ `test_setting_instance_session_still_works` - Backward compatible

All 19 sidecar tests also still pass.

## Lesson Learned

**Always use explicit `is None` checks for optional objects, not boolean evaluation.**

Boolean evaluation can be affected by:
- `__len__()` returning 0 (containers)
- `__bool__()` returning False (custom classes)
- Numeric values being 0
- Empty strings

Explicit `is None` checks are:
- ✅ Clear and unambiguous
- ✅ Not affected by object state
- ✅ More Pythonic for "does this object exist?" checks

## Related Python Gotcha

This is a common Python gotcha with objects that implement container protocols:

```python
>>> registry = SidecarRegistry()
>>> len(registry)
0
>>> bool(registry)
False  # ❌ Unexpected!
>>> registry is None
False  # ✅ Correct check
```

For existence checks, always prefer:
```python
if obj is None:        # Check if object doesn't exist
if obj is not None:    # Check if object exists
```

Over:
```python
if not obj:   # ❌ Checks truthiness, not existence
if obj:       # ❌ Checks truthiness, not existence
```
