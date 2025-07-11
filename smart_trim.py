import os
from pydub import AudioSegment
import numpy as np
from scipy.signal import correlate
import shutil

# Setup paths
episodes_dir = "test_episodes"
output_dir = "smart_trimmed"
removed_dir = "removed"
jingle_path = "jingle_sample.mp3"
threshold = 0.99 # for logging

os.makedirs(output_dir, exist_ok=True)
os.makedirs(removed_dir, exist_ok=True)

# Load the jingle sample - use the first 5 seconds)
full_jingle = AudioSegment.from_file(jingle_path)
jingle_snippet = full_jingle[:5000].set_channels(1).set_frame_rate(44100)  # Use first 5 seconds

print(f"Full jingle sample: {len(full_jingle)/1000:.2f}s")
print(f"Using jingle snippet: {len(jingle_snippet)/1000:.2f}s starting from the beginning")

def find_jingle_start(main_audio):
    # Normalize formats
    segment = main_audio.set_channels(1).set_frame_rate(44100)

    segment_samples = np.array(segment.get_array_of_samples())
    jingle_samples = np.array(jingle_snippet.get_array_of_samples())

    if len(segment_samples) < len(jingle_samples):
        return None

    correlation = correlate(segment_samples, jingle_samples, mode='valid')

    # Use absolute value to consider both positive and negative correlations
    abs_correlation = np.abs(correlation)

    normalized_correlation = correlation / np.max(abs_correlation)

    
    #just for debugging
    high_matches = np.where(normalized_correlation >= threshold)[0]
    match_times_sec = (high_matches / segment.frame_rate).round(2)
    match_times_str = ", ".join([
        f"{mt:.2f}s (corr={normalized_correlation[idx]:.2f})"
        for mt, idx in zip(match_times_sec, high_matches)
    ])
    print(f"Top matches: [{match_times_str}]")
    print(f"Top matches: {len(high_matches)}")
    
    best_index = np.argmax(normalized_correlation)

    start_ms = int((best_index / segment.frame_rate) * 1000)
    return start_ms

# Process all episodes
results = []
for filename in sorted(os.listdir(episodes_dir)):
    if filename.endswith('.mp3'):
        in_path = os.path.join(episodes_dir, filename)
        out_path = os.path.join(output_dir, filename)
        removed_path = os.path.join(removed_dir, filename)

        audio = AudioSegment.from_file(in_path).set_channels(1).set_frame_rate(44100)
        jingle_start = find_jingle_start(audio)

        if jingle_start:
            trimmed = audio[:jingle_start]
            removed = audio[jingle_start:]
            # trimmed.export(out_path, format="mp3")
            # removed.export(removed_path, format="mp3")
            
            original_duration = len(audio) / 1000
            trimmed_duration = len(trimmed) / 1000
            removed_duration = len(removed) / 1000
            
            print(f"{filename}: {original_duration:.1f}s -> {trimmed_duration:.1f}s (removed {removed_duration:.1f}s from {jingle_start/1000:.1f}s)")
            results.append((filename, jingle_start / 1000, trimmed_duration, removed_duration))
        else:
            # No jingle found, copy original
            shutil.copy(in_path, out_path)
            duration = len(audio) / 1000
            print(f"{filename}: {duration:.1f}s (no jingle found, copied as-is)")
            results.append((filename, None, duration, 0))

print(f"\nProcessed {len(results)} episodes:")
for filename, jingle_time, trimmed_dur, removed_dur in results:
    if jingle_time:
        print(f"  {filename}: trimmed at {jingle_time:.1f}s, removed {removed_dur:.1f}s")
    else:
        print(f"  {filename}: no jingle detected")

print(f"\nTrimmed files saved to: {output_dir}/")
print(f"Removed audio saved to: {removed_dir}/")