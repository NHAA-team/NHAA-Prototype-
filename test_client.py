import asyncio
import websockets
import json

async def test_merge():
    uri = "ws://localhost:8000/ws/triage"
    async with websockets.connect(uri) as websocket:
        print("Connected to merged pipeline server.")
        
        # Send an audio chunk (mocked)
        chunk = {
            "type": "audio_chunk",
            "audio": [0.0] * 32000, # 2 seconds of silence
            "dtmf": "9631" # Simulate duress code
        }
        await websocket.send(json.dumps(chunk))
        
        # We expect a transcript_update and potentially action_updates
        for _ in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"Received {data.get('type')}:")
                print(json.dumps(data, indent=2))
                
                if data.get("type") == "transcript_update":
                    assert "svi" in data
                    assert "bucket" in data["svi"]
                    # Due to dtmf='9631', it should be 'critical'
                    if data.get("silent_sos_alert"):
                        assert data["svi"]["bucket"] == "critical"
                        
            except asyncio.TimeoutError:
                break
                
        print("Test complete.")

if __name__ == "__main__":
    asyncio.run(test_merge())
