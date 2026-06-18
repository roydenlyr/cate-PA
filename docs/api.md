# PA Audio System — API Reference

Base URL: `http://<station-ip>:5000`

---

## GET /status

Check if a station is currently playing audio.

**Request**

```
GET /status
```

**Response**

```json
{
    "station": "FS1",
    "playing": false
}
```

| Field     | Type    | Description                                      |
|-----------|---------|--------------------------------------------------|
| station   | string  | Station ID of this Pi (derived from hostname)    |
| playing   | boolean | `true` if audio is currently playing             |

---

## GET /stations

List all known stations and identify which one you're talking to.

**Request**

```
GET /stations
```

**Response**

```json
{
    "stations": ["FS1", "FS2", "FS3", "WS"],
    "self": "FS1"
}
```

| Field    | Type     | Description                                  |
|----------|----------|----------------------------------------------|
| stations | string[] | All station IDs from `stations.json`         |
| self     | string   | Station ID of this Pi                        |

---

## POST /send

Send a WAV file to one or more stations for playback.

**Request**

```
POST /send
Content-Type: multipart/form-data
```

| Form Field | Type   | Required | Description                                                        |
|------------|--------|----------|--------------------------------------------------------------------|
| target     | string | Yes      | Where to send: a station ID (e.g. `FS2`, `WS`) or `BROADCAST`     |
| audio      | file   | Yes      | A valid WAV file                                                   |

**Example — single station**

```bash
curl -X POST \
  -F "target=FS2" \
  -F "audio=@announcement.wav" \
  http://128.127.1.50:5000/send
```

**Example — broadcast to all stations**

```bash
curl -X POST \
  -F "target=BROADCAST" \
  -F "audio=@announcement.wav" \
  http://128.127.1.50:5000/send
```

### Response — Single Target

Returns after playback/send completes.

**Success (sent to remote station)**

```json
{
    "status": "ok",
    "message": "Sent to ('128.127.2.50', 8080)"
}
```

**Success (played locally)**

```json
{
    "status": "ok",
    "message": "Local playback complete"
}
```

**Station busy**

```json
{
    "status": "busy",
    "message": "FS1 is currently playing"
}
```

**Error**

```json
{
    "status": "error",
    "message": "Failed to send to ('128.127.3.50', 8080): [Errno 113] No route to host"
}
```

### Response — Broadcast

Returns immediately with the accept/busy status of each station. Audio streams in the background.

```json
{
    "status": "ok",
    "message": "Broadcast complete",
    "details": {
        "local": {
            "status": "ok",
            "message": "FS1 accepted"
        },
        "FS2": {
            "status": "ok",
            "message": "Sent to ('128.127.2.50', 8080)"
        },
        "FS3": {
            "status": "error",
            "message": "Failed to send to ('128.127.3.50', 8080): [Errno 113] No route to host"
        },
        "WS": {
            "status": "busy",
            "message": "Target ('128.127.4.50', 8080) is busy"
        }
    }
}
```

| Detail Status | Meaning                                          |
|---------------|--------------------------------------------------|
| ok            | Station accepted the audio; playback/streaming has started in the background |
| busy          | Station is already playing audio; request rejected |
| error         | Could not reach the station                       |

### Error Responses

| HTTP Code | Condition          | Body                                                        |
|-----------|--------------------|-------------------------------------------------------------|
| 400       | Missing target     | `{"status": "error", "message": "Missing target"}`         |
| 400       | Missing audio file | `{"status": "error", "message": "Missing audio file"}`     |
| 400       | Invalid WAV        | `{"status": "error", "message": "Invalid WAV file"}`       |

---

## TCP Protocol (Port 8080)

Used internally between stations for audio streaming. Not intended for direct use — the HTTP API triggers this automatically.

### Connection Flow

```
Sender                          Receiver
  |                                |
  |  ---- TCP connect ---------->  |
  |                                |  Check playback state
  |  <--- 0x00 (OK) -------------  |  (or 0x01 if busy)
  |                                |
  |  ---- WAV header (44 B) ---->  |  Parse sample rate, channels, bit depth
  |  ---- audio chunks --------->  |  Pipe to aplay
  |  ---- audio chunks --------->  |
  |  ...                           |
  |  ---- close connection ----->  |  Playback ends
```

| Byte     | Meaning                           |
|----------|-----------------------------------|
| `0x00`   | OK — station is free, send audio  |
| `0x01`   | BUSY — station is playing, abort  |

---

## Station Configuration

Stations are defined in `stations.json`:

```json
{
    "FS1": "128.127.1.50",
    "FS2": "128.127.2.50",
    "FS3": "128.127.3.50",
    "WS":  "128.127.4.50"
}
```

Each station's ID is auto-detected from its hostname (e.g. hostname `cate-PA-FS1` → station ID `FS1`). The HTTP server runs on port **5000** and the TCP audio server on port **8080** on every station.