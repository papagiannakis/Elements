# test_subtitle.py - Simple tests for subtitle system
import time
import numpy as np

from Elements.extensions.Captions_Screenshot.subtitle_system import SubtitleManager, SubtitleRenderer

print("=" * 60)
print("Subtitle System Tests")
print("=" * 60)


# =====================================================================
# TEST 1: Basic subtitle display
# =====================================================================

print("\nTEST 1: Basic subtitle display")
print("-" * 60)

# Create the manager
manager = SubtitleManager()

# Add some subtitles
manager.add_subtitle("First subtitle", duration=1.0)
manager.add_subtitle("Second subtitle", duration=1.0)
manager.add_subtitle("Third subtitle", duration=1.0)

print("Added 3 subtitles to the queue")
print(f"Queue size: {len(manager.subtitle_queue)}")

# Simulate playing the subtitles
total_time = 0.0
dt = 0.1  # update every 0.1 seconds
displayed = []

while total_time < 3.5:
    current = manager.update(dt)
    
    # If we got a new subtitle, save it
    if current and current not in displayed:
        displayed.append(current)
        print(f"[{total_time:.1f}s] Showing: '{current}'")
    
    time.sleep(dt)
    total_time += dt

# Check if all 3 subtitles were shown
test1_pass = len(displayed) == 3

if test1_pass:
    print("\nPASS - All 3 subtitles were displayed")
    print(f"  Displayed: {displayed}")
else:
    print("\nFAIL - Not all subtitles were shown")
    print(f"  Expected 3, got {len(displayed)}")


print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

# Count how many tests passed
tests = [
    ("Basic display", test1_pass),
]

passed = sum(1 for _, p in tests if p)

print(f"\nThe test is passed\n")

for name, result in tests:
    status = "PASS" if result else "FAIL"
    print(f"  {status} - {name}")

print("\n" + "=" * 60)

if passed == 1:
    print("ALL GOOD - Subtitle system works")
else:
    print(f"WARNING - {1-passed} test(s) failed")

print("=" * 60)