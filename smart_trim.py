# Re-run the trimming detection script now that we have the jingle sample
import os
from pydub import AudioSegment
from pydub.utils import make_chunks
import numpy as np
from scipy.signal import correlate
import shutil

# Setup paths
episodes_dir = "episodes"
output_dir = "smart_trimmed"
removed_dir = "removed"
jingle_path = "jingle_sample.mp3"
threshold = 0.7  # Lowered threshold slightly

os.makedirs(output_dir, exist_ok=True)
os.makedirs(removed_dir, exist_ok=True)

# Load the jingle sample - use the BEGINNING of the sample (first 5 seconds)
full_jingle = AudioSegment.from_file(jingle_path).set_channels(1).set_frame_rate(44100)
jingle = full_jingle[:5000]  # Use first 5 seconds instead of 2 seconds
jingle_array = np.array(jingle.get_array_of_samples())
jingle_length_ms = len(jingle)

print(f"Full jingle sample: {len(full_jingle)/1000:.2f}s")
print(f"Using jingle snippet: {len(jingle)/1000:.2f}s from the beginning")

def find_jingle_start(main_audio):
    # Normalize formats
    segment = main_audio.set_channels(1).set_frame_rate(44100)
    jingle_snippet = jingle.set_channels(1).set_frame_rate(44100)

    segment_samples = np.array(segment.get_array_of_samples())
    jingle_samples = np.array(jingle_snippet.get_array_of_samples())

    if len(segment_samples) < len(jingle_samples):
        return None

    correlation = correlate(segment_samples, jingle_samples, mode='valid')
    correlation = correlation / np.max(np.abs(correlation))  # normalize

    # Use absolute value to consider both positive and negative correlations
    abs_correlation = np.abs(correlation)

    # Focus on matches in the last 100 seconds of the episode
    expected_start_time = len(segment) - 100000  # 100 seconds from end in ms
    expected_start_samples = int((expected_start_time / 1000) * segment.frame_rate)
    search_end_samples = len(segment_samples) - len(jingle_samples)  # Don't go past the end
    
    # Find all matches above threshold in the target region (using absolute correlation)
    if expected_start_samples < len(abs_correlation):
        target_correlation = abs_correlation[expected_start_samples:]
        high_matches = np.where(target_correlation >= threshold)[0] + expected_start_samples
    else:
        high_matches = np.where(abs_correlation >= threshold)[0]
    
    # Find the best match in the target region (using absolute correlation)
    if len(high_matches) > 0:
        best_index = high_matches[np.argmax(abs_correlation[high_matches])]
        best_value = abs_correlation[best_index]
        original_value = correlation[best_index]
    else:
        # Fall back to global best match
        best_index = np.argmax(abs_correlation)
        best_value = abs_correlation[best_index]
        original_value = correlation[best_index]

    if best_value >= threshold:
        start_ms = int((best_index / segment.frame_rate) * 1000)
        return start_ms
    return None

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
            trimmed.export(out_path, format="mp3")
            removed.export(removed_path, format="mp3")
            
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