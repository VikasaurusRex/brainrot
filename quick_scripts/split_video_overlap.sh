#!/bin/bash

# Script to split a video into overlapping clips using ffmpeg

# --- Configuration ---
INPUT_VIDEO="assets/background_videos/parkour.mp4"
# Define an output directory relative to the script or workspace root
OUTPUT_DIR="output/parkour_clips_$(date +%Y%m%d_%H%M%S)"
CLIP_DURATION=200 # Desired duration of each clip in seconds
OVERLAP_DURATION=100 # Desired overlap between clips in seconds
# --- End Configuration ---

# Ensure ffmpeg and ffprobe are installed
if ! command -v ffmpeg &> /dev/null || ! command -v ffprobe &> /dev/null; then
    echo "Error: ffmpeg and/or ffprobe could not be found. Please install them."
    exit 1
fi

# Absolute path to the input video, assuming the script is run from workspace root
# If script is in quick_scripts/, adjust path or use absolute paths
# For simplicity, this script assumes INPUT_VIDEO is accessible from where it's run.
# If workspace root is /Users/vh/Desktop/Implementation/brainrot, then the path is correct.

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"
if [ ! -d "${OUTPUT_DIR}" ]; then
    echo "Error: Could not create output directory ${OUTPUT_DIR}"
    exit 1
fi

echo "Processing video: ${INPUT_VIDEO}"
echo "Output directory: ${OUTPUT_DIR}"

# Get video duration in seconds
VIDEO_DURATION_FLOAT=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${INPUT_VIDEO}")
if [ -z "${VIDEO_DURATION_FLOAT}" ]; then
  echo "Error: Could not get video duration for ${INPUT_VIDEO}."
  exit 1
fi
# Convert duration to integer (floor)
VIDEO_DURATION_INT=$(printf "%.0f" "${VIDEO_DURATION_FLOAT}")

echo "Total video duration: ${VIDEO_DURATION_INT} seconds."

current_start_time=0
clip_index=0
# Calculate the amount to advance the start time for each new clip
step_duration=$((CLIP_DURATION - OVERLAP_DURATION))

if [ "${step_duration}" -le 0 ]; then
    echo "Error: OVERLAP_DURATION must be less than CLIP_DURATION."
    exit 1
fi

while (( $(echo "${current_start_time} < ${VIDEO_DURATION_INT}" | bc -l) )); do
  # Ensure that we don't try to make a clip if the remaining part is smaller than a minimal meaningful portion,
  # e.g., if current_start_time is already past the point where a new clip makes sense.
  # This check prevents creating zero-length or tiny clips if the video ends abruptly after an overlap.
  if (( $(echo "${current_start_time} >= ${VIDEO_DURATION_INT} - 1" | bc -l) )) && (( ${clip_index} > 0 )); then # Avoid tiny last segment if already started. -1 to allow for very short final segments if desired.
      echo "Remaining video too short for another meaningful overlapping clip. Stopping."
      break
  fi

  output_filename="clip_${clip_index}.mp4"
  output_filepath="${OUTPUT_DIR}/${output_filename}"
  
  echo "Creating ${output_filename}: Start Time: ${current_start_time}s, Max Duration: ${CLIP_DURATION}s"
  
  # -ss before -i for fast seeking
  # -t specifies the duration of the clip
  # -c copy to avoid re-encoding (fast, but cuts might not be frame-accurate if not on keyframes)
  # -avoid_negative_ts make_zero helps prevent issues with timestamps, e.g. black frames at start
  # -y overwrites output files without asking
  ffmpeg -ss "${current_start_time}" -i "${INPUT_VIDEO}" -t "${CLIP_DURATION}" -c copy -avoid_negative_ts make_zero -y "${output_filepath}"
  
  if [ $? -ne 0 ]; then
    echo "Error during ffmpeg command for ${output_filename}. Check ffmpeg output."
    # Decide if you want to stop or continue
    # exit 1 
  else
    echo "Successfully created ${output_filepath}"
  fi
  
  current_start_time=$((current_start_time + step_duration))
  clip_index=$((clip_index + 1))

  # If the next start time is beyond the video duration, no need to continue
  if (( $(echo "${current_start_time} >= ${VIDEO_DURATION_INT}" | bc -l) )); then
      break
  fi
done

echo "-----------------------------------------------------"
echo "Video splitting process completed."
echo "Clips are saved in: ${OUTPUT_DIR}"
echo "-----------------------------------------------------"

