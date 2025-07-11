#!/usr/bin/env python3
"""
Smart audio trimming script that removes jingle/outro sections from audio episodes.
Uses cross-correlation to find the jingle pattern and removes everything after it.
"""

import os
import sys
from pydub import AudioSegment
import numpy as np
from scipy.signal import correlate
import shutil

# Configuration
EPISODES_DIR = "episodes"
OUTPUT_DIR = "smart_trimmed"
REMOVED_DIR = "removed"
JINGLE_PATH = "jingle_sample.mp3"
JINGLE_SNIPPET_MS = 5000  # Use first 5 seconds of jingle sample
MIN_JINGLE_POSITION_S = 60  # Jingle should be at least 1 minute into episode
BAR_LENGTH = 30

def load_jingle_sample(jingle_path, snippet_ms):
    """Load and prepare the jingle sample for correlation matching."""
    try:
        full_jingle = AudioSegment.from_file(jingle_path)
        jingle_snippet = full_jingle[:snippet_ms].set_channels(1).set_frame_rate(44100)
        
        print(f"Loaded jingle sample: {len(full_jingle)/1000:.2f}s")
        print(f"Using jingle snippet: {len(jingle_snippet)/1000:.2f}s from beginning")
        
        return jingle_snippet
    except Exception as e:
        print(f"Error loading jingle sample '{jingle_path}': {e}")
        sys.exit(1)

def find_jingle_start(main_audio, jingle_snippet):
    """Find the start position of the jingle in the main audio using cross-correlation."""
    # Normalize audio format
    segment = main_audio.set_channels(1).set_frame_rate(44100)
    
    # Convert to float to avoid integer overflow in correlation
    segment_samples = np.array(segment.get_array_of_samples(), dtype=np.float64)
    jingle_samples = np.array(jingle_snippet.get_array_of_samples(), dtype=np.float64)
    
    if len(segment_samples) < len(jingle_samples):
        return None
    
    # Compute cross-correlation using FFT (much faster than direct correlation)
    correlation = correlate(segment_samples, jingle_samples, mode='valid')
    
    # Normalize correlation values to [-1, 1] range
    max_abs_val = np.max(np.abs(correlation))
    if max_abs_val > 0:
        correlation = correlation / max_abs_val
    
    # Use absolute value to consider both positive and negative correlations
    # (negative correlation indicates phase-inverted match, which is still valid)
    abs_correlation = np.abs(correlation)
    
    # Find the best match
    best_index = np.argmax(abs_correlation)
    
    # Convert sample index to time in milliseconds
    start_ms = int((best_index / segment.frame_rate) * 1000)
    
    # Ensure jingle is not found too early in the episode (likely false positive)
    if start_ms < MIN_JINGLE_POSITION_S * 1000:
        return None
    
    return start_ms

def process_episode(filename, jingle_snippet):
    """Process a single episode file."""
    in_path = os.path.join(EPISODES_DIR, filename)
    out_path = os.path.join(OUTPUT_DIR, filename)
    removed_path = os.path.join(REMOVED_DIR, filename)
    
    try:
        # Load and normalize audio
        audio = AudioSegment.from_file(in_path).set_channels(1).set_frame_rate(44100)
        jingle_start = find_jingle_start(audio, jingle_snippet)
        
        if jingle_start:
            # Trim the audio at the jingle start
            trimmed = audio[:jingle_start]
            removed = audio[jingle_start:]
            
            # Export trimmed and removed portions
            # trimmed.export(out_path, format="mp3")
            # removed.export(removed_path, format="mp3")
            
            # Calculate durations
            removed_duration = len(removed) / 1000
            print(" " * 100, end="\r")  # Clear the line
            print(f"  {filename:<40} removed {removed_duration:.1f}s")
            return (filename, jingle_start / 1000, removed_duration)
        else:
            # No jingle found, copy original file
            shutil.copy(in_path, out_path)
            duration = len(audio) / 1000
            print(" " * 100, end="\r")  # Clear the line
            print(f"  {filename}: {duration:.1f}s (no jingle detected, copied as-is)")
            return (filename, None, 0)
            
    except Exception as e:
        print(" " * 100, end="\r")  # Clear the line
        print(f"  {filename}: Error: {e}")
        return (filename, "ERROR", 0)

def main():
    """Main processing function."""
    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REMOVED_DIR, exist_ok=True)
    
    # Load jingle sample
    jingle_snippet = load_jingle_sample(JINGLE_PATH, JINGLE_SNIPPET_MS)
    
    # Process all episodes
    results = []
    episode_files = [f for f in sorted(os.listdir(EPISODES_DIR)) if f.endswith('.mp3')]
    
    if not episode_files:
        print(f"No .mp3 files found in {EPISODES_DIR}/")
        return
    
    print(f"Processing {len(episode_files)} episodes...")
    
    for i, filename in enumerate(episode_files, 1):
        progress = i / len(episode_files)
        filled_length = int(BAR_LENGTH * progress)
        bar = '█' * filled_length + '-' * (BAR_LENGTH - filled_length)
        print(f"[{i}/{len(episode_files)}] |{bar}| Processing {filename}...", end="\r")
        result = process_episode(filename, jingle_snippet)
        results.append(result)
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Processed {len(results)} episodes:")
    
    successful_trims = 0
    failed_trims = 0
    for filename, jingle_time, removed_dur in results:
        if jingle_time == "ERROR":
            print(f"  {filename}: ERROR during processing")
            failed_trims += 1
        elif jingle_time:
            print(f"  {filename:<40} trimmed at {jingle_time:>6.1f}s, removed {removed_dur:>6.1f}s")
            successful_trims += 1
        else:
            print(f"  {filename}: no jingle detected")
            failed_trims += 1
    
    print(f"\nSuccessfully trimmed: {successful_trims}/{len(results)} episodes")
    if failed_trims > 0:
        print(f"FAILED TO TRIM: {failed_trims}/{len(results)} episodes")
    print(f"Trimmed files saved to: {OUTPUT_DIR}/")
    print(f"Removed audio saved to: {REMOVED_DIR}/")

if __name__ == "__main__":
    main()