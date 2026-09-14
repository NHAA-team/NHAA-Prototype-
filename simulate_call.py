import asyncio
import websockets
import json
import wave
import sys
import time

async def stream_audio_file(file_path):
    uri = "ws://localhost:8000/ws/triage"
    
    try:
        # Check if file exists and is a valid wav
        with wave.open(file_path, 'rb') as wf:
            framerate = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            
            if framerate != 16000 or channels != 1 or sampwidth != 2:
                print(f"Warning: Audio should ideally be 16kHz, Mono, 16-bit PCM. Found: {framerate}Hz, {channels}ch, {sampwidth}bytes")
            
            async with websockets.connect(uri) as websocket:
                print(f"Connected to backend. Streaming {file_path}...")
                
                # Stream in chunks of 2 seconds (16000 * 2 frames)
                chunk_size = 16000 * 2
                
                while True:
                    data = wf.readframes(chunk_size)
                    if not data:
                        break
                        
                    # Convert to float32 numpy-like array structure (normalized -1 to 1)
                    import numpy as np
                    audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    chunk_msg = {
                        "type": "audio_chunk",
                        "audio": audio_array.tolist(),
                        "dtmf": "" 
                    }
                    
                    # Optionally simulate DTMF duress if you press enter, but we'll keep it simple
                    
                    await websocket.send(json.dumps(chunk_msg))
                    print(f"Sent 2 seconds of audio...")
                    
                    # Wait for 2 seconds to simulate real-time
                    await asyncio.sleep(2.0)
                    
                print("Finished streaming audio file.")
                
    except FileNotFoundError:
        print(f"Error: Could not find audio file at {file_path}")
    except Exception as e:
        print(f"Error streaming audio: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simulate_call.py <path_to_audio.wav>")
        print("Since we don't have an audio file, please provide one!")
        sys.exit(1)
        
    asyncio.run(stream_audio_file(sys.argv[1]))
