#!/usr/bin/env python3
"""
🎤 AI Real-time Vocal Analyzer for REAPER
==========================================
Captures mic audio via PipeWire (pw-record), analyzes frequency spectrum
with FFT, and writes adjustment commands for a Lua bridge inside REAPER.

Usage: python3 realtime_vocal_ai.py [--device DEVICE_NAME] [--sensitivity low|mid|high]
"""
import subprocess, struct, sys, os, json, time, signal, argparse, threading
import numpy as np
from collections import deque

# ── Config ──
SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_SAMPLES = 2048  # ~42ms window
BYTES_PER_SAMPLE = 2  # 16-bit signed int
CHUNK_BYTES = CHUNK_SAMPLES * CHANNELS * BYTES_PER_SAMPLE
ANALYSIS_INTERVAL = 0.3  # seconds between analysis cycles
CMD_FILE = "/tmp/ai_karaoke_commands.json"
BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
GENRE_FILE = "/tmp/ai_karaoke_genre.json"

# ── Frequency bands for vocal analysis ──
BANDS = [
    ("Sub",      20,    80,  0.10),  # name, low_hz, high_hz, target_energy (normalized)
    ("Bass",     80,   250,  0.20),
    ("Mud",     250,   500,  0.25),
    ("Body",    500,  1000,  0.35),
    ("Presence",1000,  4000, 0.45),  # vocal clarity zone
    ("Bright",  4000,  8000, 0.30),
    ("Air",     8000, 16000, 0.15),
]

# ── EQ band mapping to ReaEQ bands ──
EQ_MAP = {
    "Sub":      {"band": 1, "action": "highpass",  "max_cut": 6},
    "Mud":      {"band": 2, "action": "cut",       "max_cut": 5, "max_boost": 5},
    "Presence": {"band": 3, "action": "boost",     "max_boost": 6},
    "Bright":   {"band": 4, "action": "shelf",     "max_boost": 5},
}

# ── State ──
running = True
history = deque(maxlen=60)  # ~18 seconds of analysis history
pitch_history = deque(maxlen=10) # ~300ms window of pitch tracking
current_adjustments = {}
current_bpm = 120.0
current_genre = {}  # Genre preset from UI
lock = threading.Lock()


def signal_handler(sig, frame):
    global running
    running = False
    print("\n\n🛑 Đang dừng... Đã ghi lệnh reset về REAPER.")
    write_commands({"reset": True})
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def compute_band_energy(fft_magnitudes, freqs):
    """Compute normalized energy for each frequency band."""
    results = {}
    total = np.sum(fft_magnitudes) + 1e-10
    for name, lo, hi, target in BANDS:
        mask = (freqs >= lo) & (freqs < hi)
        energy = np.sum(fft_magnitudes[mask]) / total if np.any(mask) else 0.0
        results[name] = {"energy": float(energy), "target": target}
    return results


def compute_rms_db(samples):
    """Compute RMS level in dB."""
    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
    if rms < 1:
        return -96.0
    return 20.0 * np.log10(rms / 32768.0)


def detect_pitch(fft_magnitudes, freqs):
    """Simple pitch detection via peak frequency in vocal range (80-1000Hz)."""
    mask = (freqs >= 80) & (freqs <= 1000)
    if not np.any(mask):
        return 0.0
    vocal_mags = fft_magnitudes[mask]
    vocal_freqs = freqs[mask]
    peak_idx = np.argmax(vocal_mags)
    return float(vocal_freqs[peak_idx])


def freq_to_note(freq):
    """Convert frequency to musical note name."""
    if freq < 20:
        return "---"
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    midi = 69 + 12 * np.log2(freq / 440.0)
    note_idx = int(round(midi)) % 12
    octave = int(round(midi)) // 12 - 1
    return f"{notes[note_idx]}{octave}"


def read_bpm():
    """Read BPM from REAPER (written by Lua bridge)."""
    try:
        with open(BPM_FILE, "r") as f:
            return float(f.read().strip())
    except Exception:
        return 120.0


def read_genre():
    """Read genre preset from UI control panel."""
    try:
        with open(GENRE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

CALIB_FILE = "/tmp/ai_karaoke_calib.json"

def read_calibration():
    """Đọc dữ liệu phân tích giọng 5s từ auto_calibrate.py"""
    try:
        with open(CALIB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def calc_tempo_sync(bpm, genre=None):
    """
    Tính delay/reverb theo tempo VÀ thể loại nhạc.
    Genre preset ghi đè giá trị mặc định nếu có.
    """
    ms_per_beat = 60000.0 / bpm
    
    # Lấy delay fraction từ genre (mặc định: dotted 1/8 = 0.75)
    fraction = 0.75
    if genre and "delay_fraction" in genre:
        fraction = genre["delay_fraction"]
    
    delay_ms = ms_per_beat * fraction
    if fraction == 0.75: delay_type = "dotted 1/8"
    elif fraction == 0.5: delay_type = "1/8 note"
    elif fraction == 0.25: delay_type = "1/16 note"
    else: delay_type = f"{fraction}"
    
    delay_norm = min(delay_ms / 10000.0, 1.0)
    
    # Lấy reverb từ genre hoặc tính theo tempo
    if genre and "reverb_room" in genre:
        room = genre["reverb_room"]
        wet = genre.get("reverb_wet", 0.38)
    else:
        if bpm > 140: room, wet = 0.30, 0.28
        elif bpm > 100: room, wet = 0.45, 0.35
        else: room, wet = 0.65, 0.45
    
    delay_vol = genre.get("delay_volume", 0.22) if genre else 0.22
    delay_fb = genre.get("delay_feedback", 0.0) if genre else 0.0
    damp = genre.get("reverb_damp", 0.45) if genre else 0.45
    width = genre.get("reverb_width", 0.75) if genre else 0.75
    
    # Áp dụng Reverb Scale tỉ lệ thuận từ thanh kéo (%) chỉ cho Reverb
    reverb_scale = genre.get("reverb_scale", 0.0) if genre else 0.0
    scale_factor = 1.0 + (reverb_scale / 100.0)
    
    scaled_wet = min(max(wet * scale_factor, 0.0), 0.95)
    scaled_delay_vol = min(max(delay_vol, 0.0), 0.95)
    scaled_room = min(max(room * (1.0 + (reverb_scale / 200.0)), 0.2), 0.95)
    scaled_delay_fb = min(max(delay_fb, 0.0), 0.4)
    
    # Pre-delay theo BPM: 1/64 note, clamp 25-40ms (sweet spot thính giác)
    # < 25ms: não nghe thành 1 âm (thickening) → mất vang
    # 25-40ms: não nghe thành "phản xạ/vang" riêng biệt → sân khấu
    # > 40ms: nghe rõ echo riêng → doubling
    predelay_ms = ms_per_beat / 16.0  # 1/64 note (1/16 of beat)
    predelay_ms = max(25.0, min(40.0, predelay_ms))
    predelay_norm = predelay_ms / 100.0  # ReaVerbate Delay param ~= ms/100
    
    return {
        "delay_length": delay_norm,
        "delay_ms": delay_ms,
        "delay_type": delay_type,
        "delay_volume": scaled_delay_vol,
        "delay_feedback": scaled_delay_fb,
        "reverb_room": scaled_room,
        "reverb_wet_tempo": scaled_wet,
        "reverb_damp": damp,
        "reverb_width": width,
        "reverb_predelay": predelay_norm,
        "reverb_predelay_ms": predelay_ms,
    }


def detect_echo_buildup():
    """
    Phát hiện echo/reverb bị tích tụ quá nhiều.
    
    Cách hoạt động:
    - Sau khi giọng hát ngừng, năng lượng phải giảm nhanh
    - Nếu sau 500ms mà năng lượng vẫn cao → echo/reverb tail quá dài
    - Gửi lệnh giảm wet/room
    """
    if len(history) < 15:
        return None
    
    snapshots = list(history)
    
    # Tìm thời điểm người hát ngừng (RMS giảm từ >-30 xuống <-40)
    for i in range(len(snapshots) - 5, 0, -1):
        was_singing = snapshots[i]["rms_db"] > -30
        now_quiet = all(s["rms_db"] < -40 for s in snapshots[i+1:i+4])
        
        if was_singing and now_quiet:
            # Kiểm tra: sau 4-5 frames im lặng, năng lượng còn bao nhiêu?
            if i + 5 < len(snapshots):
                tail_energy = snapshots[i + 5]["rms_db"]
                if tail_energy > -45:
                    # Đuôi reverb/echo vẫn còn khá to → cần giảm
                    return {
                        "echo_detected": True,
                        "tail_db": tail_energy,
                        "action": "reduce"
                    }
            break
    
    return None


def generate_eq_adjustments(band_data, rms_db, sensitivity=1.0):
    """Generate EQ adjustment commands using genre presets."""
    global current_bpm, current_genre
    vocal_adj = {}
    music_adj = {}
    is_singing = bool(rms_db > -50) # Hạ threshold xuống -50 để bắt giọng hát nhẹ nhất

    # ── ĐỌc GENRE PRESET ──
    current_genre = read_genre()
    genre_name = current_genre.get("name", "Default")
    duck_intensity = current_genre.get("duck_intensity", 1.0) * sensitivity

    # ── TEMPO SYNC (với genre override) ──
    current_bpm = read_bpm()
    if "bpm_override" in current_genre:
        vocal_adj["master_bpm"] = current_genre["bpm_override"]
        current_bpm = current_genre["bpm_override"]

    tempo = calc_tempo_sync(current_bpm, current_genre)
    vocal_adj["delay_length"] = tempo["delay_length"]
    vocal_adj["delay_feedback"] = tempo["delay_feedback"]
    
    # ── ACTIVE DELAY DUCKING ──
    # Giữ nguyên Delay volume ổn định 100% để tạo độ kết dính (glue) liên tục
    vocal_adj["delay_volume"] = tempo["delay_volume"]

    vocal_adj["reverb_room"] = tempo["reverb_room"]
    vocal_adj["reverb_wet"] = tempo["reverb_wet_tempo"]
    vocal_adj["reverb_damp"] = tempo["reverb_damp"]
    vocal_adj["reverb_width"] = tempo["reverb_width"]
    vocal_adj["tempo_note"] = f"[{genre_name}] BPM={current_bpm:.0f} Delay={tempo['delay_ms']:.0f}ms ({tempo['delay_type']})"
    
    vocal_adj["autotune_enabled"] = current_genre.get("autotune_enabled", True) if is_singing else False
    vocal_adj["saturation_amount"] = float(current_genre.get("saturation_amount", 0.0)) if is_singing else 0.0

    # ── ADAPTIVE AUTOTUNE (FLEX-TUNE & PENTATONIC) ──
    genre_key = current_genre.get("genre", "nhac_tre")
    scale_type = "Standard"
    autotune_depth = 0.0
    
    if is_singing:
        autotune_depth = 0.5  # default baseline
        # Calculate pitch stability
        with lock:
            active_pitches = [p for p in list(pitch_history) if p > 50]
            
        if len(active_pitches) >= 4:
            # Convert Hz to MIDI notes for standard deviation calculation
            midi_notes = [69 + 12 * np.log2(hz / 440.0) for hz in active_pitches]
            pitch_std = np.std(midi_notes)
            
            # Flex-Tune logic: if pitch standard deviation is high (singer is sliding/vibrato),
            # reduce autotune depth so it doesn't yank the voice.
            if pitch_std > 1.0:     # high fluctuation -> slide / vibrato / transition
                autotune_depth = 0.25  # Giữ lực bám nhẹ để không bị hụt trợ năng
            elif pitch_std < 0.3:   # extremely stable -> holding a note
                autotune_depth = 0.65  # Giữ độ tự nhiên, không bị méo giọng robot
            else:                   # moderate transition
                autotune_depth = 0.45
        else:
            autotune_depth = 0.25  # Giữ lực bám nền nhẹ thay vì tắt ngóm về 0.0 gây hụt hẫng
            
        # Genre-based limits & Scale types
        if genre_key == "dan_ca":
            scale_type = "Pentatonic"
            # Always limit autotune depth for traditional music to keep it natural
            autotune_depth = min(autotune_depth, 0.25)
        elif genre_key == "bolero":
            # Bolero has lots of slides, restrict depth
            autotune_depth = min(autotune_depth, 0.45)
            
    vocal_adj["autotune_depth"] = float(autotune_depth)
    vocal_adj["scale_type"] = scale_type

    # ── GENRE COMP SETTINGS ──
    if "comp_ratio" in current_genre:
        vocal_adj["comp_ratio"] = current_genre["comp_ratio"]
    if "comp_thresh" in current_genre:
        vocal_adj["comp_thresh"] = current_genre["comp_thresh"]

    # ── AUTO-PODCAST / LIVESTREAM LOGIC ──
    is_music_playing = current_genre.get("is_music_playing", True)
    force_podcast = current_genre.get("force_podcast", False)
    
    if force_podcast:
        # Chế độ Podcast/Live thủ công: Khóa cứng giọng nói ấm, tắt autotune & delay & reverb, không dynamic EQ
        vocal_adj["autotune_enabled"] = False
        vocal_adj["autotune_depth"] = 0.0
        vocal_adj["reverb_wet"] = 0.0
        vocal_adj["delay_volume"] = 0.0
        vocal_adj["comp_ratio"] = 0.35   # ~5:1 ratio (normalized)
        vocal_adj["comp_thresh"] = 0.43  # -24dB threshold (normalized)
        vocal_adj["eq_band_1_gain"] = 0.0
        vocal_adj["eq_band_2_gain_db"] = 2.5
        vocal_adj["eq_band_3_gain_db"] = 0.0
        vocal_adj["eq_band_4_gain_db"] = -2.0
        vocal_adj["chorus_mix"] = 0.0
        vocal_adj["reverb_note"] = "Chế độ Podcast cố định (Giọng ấm, Tắt Autotune & Vang)"
        
        music_adj["music_eq_band_1_gain_db"] = 0.0
        music_adj["music_eq_band_2_gain_db"] = 0.0
        music_adj["music_eq_band_3_gain_db"] = 0.0
        return {"vocal": vocal_adj, "music": music_adj, "is_singing": False}
        
    # if not is_music_playing:
    #     # Tự động chuyển chế độ thoại tạm thời khi dừng nhạc
    #     vocal_adj["autotune_enabled"] = False
    #     vocal_adj["reverb_wet"] = 0.0
    #     vocal_adj["delay_volume"] = 0.0
    #     vocal_adj["comp_ratio"] = 0.35   # ~5:1 ratio (normalized)
    #     vocal_adj["comp_thresh"] = 0.43  # -24dB threshold (normalized)
    #     vocal_adj["eq_band_2_gain_db"] = 2.0
    #     vocal_adj["eq_band_4_gain_db"] = -1.5
    #     vocal_adj["reverb_note"] = "Nhạc tắt → Tự động chuyển chế độ Livestream"
    #     
    #     music_adj["music_eq_band_1_gain_db"] = 0.0
    #     music_adj["music_eq_band_2_gain_db"] = -1.5
    #     music_adj["music_eq_band_3_gain_db"] = 0.0
    #     return {"vocal": vocal_adj, "music": music_adj, "is_singing": False}

    # ── GENRE CHORUS ──
    if "chorus_mix" in current_genre:
        vocal_adj["chorus_mix"] = current_genre["chorus_mix"]

    # ── GENRE STEREO WIDENING (Nhạc Tách Mở) ──
    if "music_stereo_width" in current_genre:
        vocal_adj["music_stereo_width"] = current_genre["music_stereo_width"]

    # ── VOCAL TRACK EQ ──
    if is_singing:
        for band_name, info in EQ_MAP.items():
            if band_name not in band_data:
                continue
                
            energy = band_data[band_name]["energy"]
            target = band_data[band_name]["target"]
            diff = energy - target

            if band_name == "Sub" and energy > target * 1.5:
                vocal_adj["eq_band_1_type"] = "highpass"
                vocal_adj["eq_band_1_gain"] = min(diff * 5 * sensitivity, 2.0)
            elif band_name == "Mud":
                if energy > target * 1.5: 
                    vocal_adj["eq_band_2_gain_db"] = -min(diff * 5 * sensitivity, info["max_cut"])
                elif energy < target * 0.7:
                    vocal_adj["eq_band_2_gain_db"] = min((target - energy) * 12 * sensitivity, info["max_boost"])
            elif band_name == "Presence" and energy < target * 0.90:
                vocal_adj["eq_band_3_gain_db"] = min((target - energy) * 6 * sensitivity, info["max_boost"])
            elif band_name == "Bright" and energy < target * 0.90:
                vocal_adj["eq_band_4_gain_db"] = min((target - energy) * 5 * sensitivity, info["max_boost"])

        # CỘNG THÊM OFFSET TỪ BẢN CALIBRATION 5 GIÂY (nếu có)
        calib = read_calibration()
        if "eq_band_2_gain_db" in calib and "eq_band_2_gain_db" in vocal_adj:
            vocal_adj["eq_band_2_gain_db"] += calib["eq_band_2_gain_db"]
        elif "eq_band_2_gain_db" in calib:
            vocal_adj["eq_band_2_gain_db"] = calib["eq_band_2_gain_db"]
            
        if "eq_band_3_gain_db" in calib and "eq_band_3_gain_db" in vocal_adj:
            vocal_adj["eq_band_3_gain_db"] += calib["eq_band_3_gain_db"]
        elif "eq_band_3_gain_db" in calib:
            vocal_adj["eq_band_3_gain_db"] = calib["eq_band_3_gain_db"]
        if "eq_band_4_gain_db" in calib and "eq_band_4_gain_db" in vocal_adj:
            vocal_adj["eq_band_4_gain_db"] += calib["eq_band_4_gain_db"]
        elif "eq_band_4_gain_db" in calib:
            vocal_adj["eq_band_4_gain_db"] = calib["eq_band_4_gain_db"]
    else:
        vocal_adj["eq_band_1_gain"] = 0.0
        vocal_adj["eq_band_2_gain_db"] = 0.0
        vocal_adj["eq_band_3_gain_db"] = 0.0
        vocal_adj["eq_band_4_gain_db"] = 0.0

    # ── MUSIC TRACK SPECTRAL CARVING (Inverse EQ TĨNH) ──
    # User yêu cầu: "Không cần chỉnh trong thời gian thực".
    # Vì vậy, ta KHÓA CHẾT (Lock) một rãnh EQ cố định vào beat nhạc. 
    # Dù bạn có hát hay im lặng, Beat luôn chừa sẵn chỗ trống này, tránh việc nhảy EQ lên xuống (vặn vẹo).
    music_adj["music_eq_band_1_gain_db"] = -2.0  # Gọt dải siêu cao (10.0kHz High Shelf) nhường chỗ cho reverb bông xốp
    music_adj["music_eq_band_2_gain_db"] = -4.5  # Gọt sâu dải trung (2.5kHz) tạo khoảng trống cực rộng cho giọng hát mịn
    music_adj["music_eq_band_3_gain_db"] = -3.5  # Gọt dải sáng (5.0kHz) nhường chỗ cho độ bóng bẩy vocal
    # ── COMPRESSOR & EQ (LOCKED TO OPTIMAL SWEET SPOTS) ──
    # Giữ cố định ở mức ngọt tối ưu để giọng hát có động lực học (dynamics) tự nhiên, hát nhẹ nhàng, không tốn sức
    vocal_adj["comp_ratio"] = 0.025  # ~3.5:1 ratio (nén nhẹ nhàng, mềm mại, dẻo dai)
    vocal_adj["comp_thresh"] = 0.030 # -24.4dB threshold (unity)
    vocal_adj["eq_band_2_gain_db"] = -1.5 # Cắt mud 350Hz -1.5dB (giảm bùn đục)
    vocal_adj["eq_band_3_gain_db"] = 5.0  # BOOST presence 3.2kHz +5dB (bù Graillon resynthesis mất treble)
    vocal_adj["eq_band_4_gain_db"] = 6.0  # BOOST air 12kHz +6dB (bù treble, bay bổng, ninh tai)
    vocal_adj["comp_note"] = "Compressor & EQ khóa cứng ở điểm ngọt mềm xốp tối ưu"

    # ── REVERB: body-based override (Giữ cực kỳ ổn định) ──
    # Khóa cứng reverb_wet theo tempo & preset, không tự động dìm bớt khi giọng dày lên để tránh cảm giác bị hụt vang
    vocal_adj["reverb_wet"] = tempo["reverb_wet_tempo"]
    vocal_adj["reverb_note"] = "Vang giữ ổn định theo thể loại"

    # ── ĐỌC THÔNG SỐ TỰ ĐỘNG CÂN CHỈNH (AUTO-CALIBRATE) ──
    try:
        import os, json
        if os.path.exists("/tmp/ai_karaoke_calib.json"):
            with open("/tmp/ai_karaoke_calib.json", "r") as f:
                calib = json.load(f)
                if time.time() - calib.get("timestamp", 0) < 3600:
                    if "eq_band_2_gain_db" in calib: vocal_adj["eq_band_2_gain_db"] = calib["eq_band_2_gain_db"]
                    if "eq_band_3_gain_db" in calib: vocal_adj["eq_band_3_gain_db"] = calib["eq_band_3_gain_db"]
                    if "eq_band_4_gain_db" in calib: vocal_adj["eq_band_4_gain_db"] = calib["eq_band_4_gain_db"]
    except: pass

    return {"vocal": vocal_adj, "music": music_adj, "is_singing": is_singing}


def write_commands(data):
    """Write adjustment commands to shared JSON file for Lua bridge."""
    data["timestamp"] = time.time()
    try:
        with open(CMD_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def render_bar(value, max_val, width=20, char="█", empty="░"):
    """Render a progress bar."""
    filled = int((value / max(max_val, 0.001)) * width)
    filled = max(0, min(width, filled))
    return char * filled + empty * (width - filled)


def render_display(band_data, rms_db, pitch_hz, adjustments):
    """Render the terminal UI."""
    os.system("clear" if os.name != "nt" else "cls")
    note = freq_to_note(pitch_hz)

    # Level meter color
    if rms_db > -6:
        lvl_color = "\033[91m"  # Red (too hot)
    elif rms_db > -18:
        lvl_color = "\033[92m"  # Green (good)
    else:
        lvl_color = "\033[93m"  # Yellow (quiet)

    print("\033[1m🎤 AI VOCAL ANALYZER — Real-time\033[0m")
    print("━" * 52)
    print(f"  Level: {lvl_color}{render_bar(rms_db + 60, 60)}\033[0m {rms_db:+.1f} dB")
    print(f"  Pitch: \033[96m{note}\033[0m ({pitch_hz:.0f} Hz)")
    print()
    print("\033[1m  Spectrum Analysis:\033[0m")

    for name, lo, hi, target in BANDS:
        if name not in band_data:
            continue
        energy = band_data[name]["energy"]
        ratio = energy / max(target, 0.001)
        bar = render_bar(energy, 0.6, width=25)

        if ratio > 1.4:
            status = "\033[91m⬇ CẮT \033[0m"
            color = "\033[91m"
        elif ratio < 0.6:
            status = "\033[93m⬆ TĂNG\033[0m"
            color = "\033[93m"
        else:
            status = "\033[92m  OK  \033[0m"
            color = "\033[92m"

        label = f"{name:>9s}"
        freq_range = f"({lo}-{hi}Hz)"
        print(f"  {label} {freq_range:>14s}  {color}{bar}\033[0m [{status}]")

    print()
    # Print all adjustments split into vocal and music sections
    if not adjustments or (not adjustments.get("vocal") and not adjustments.get("music")):
        print("\033[1m  🤖 AI:\033[0m \033[90m(Đang lắng nghe...)\033[0m")
    else:
        singing = adjustments.get("is_singing", False)
        status = "\033[92m🎵 ĐANG HÁT\033[0m" if singing else "\033[90m🔇 IM LẶNG\033[0m"
        
        music_play = current_genre.get("is_music_playing", True)
        force_podcast = current_genre.get("force_podcast", False)
        
        music_stat = "\033[92mĐANG PHÁT\033[0m" if music_play else "\033[91mTẮT\033[0m"
        
        if force_podcast:
            verb_stat = "\033[94m🎙️ PODCAST (ÉP BẬT)\033[0m"
        else:
            verb_stat = "\033[92mBẬT\033[0m"
            
        print(f"  Trạng thái: {status}  |  Nhạc: {music_stat}  |  Vang: {verb_stat}")
        print()
        vocal = adjustments.get("vocal", {})
        music = adjustments.get("music", {})
        if vocal:
            print("\033[1m  🎙️ Vocal FX:\033[0m")
            for k, v in vocal.items():
                if k.endswith("_note"): print(f"    💡 {v}")
                elif "gain" in k: print(f"    🎛️  {k}: {v:+.1f} dB")
                elif "reverb" in k: 
                    name = k.replace('reverb_', '').replace('_', ' ').title()
                    print(f"    🎛️  Reverb {name} → {v:.0%}")
        if music:
            print("\033[1m  🎵 Nhạc nền (Spectral Ducking):\033[0m")
            for k, v in music.items():
                if k.endswith("_note"): print(f"    💡 {v}")
                elif "gain" in k: print(f"    🎛️  {k}: {v:+.1f} dB")
                elif "volume" in k: print(f"    🔊 Music vol → {v:.2f}")

    print()
    print("\033[90m  [Ctrl+C để dừng] — Đang ghi lệnh tới REAPER...\033[0m")


def analysis_loop(sensitivity):
    """Main analysis loop running in a thread."""
    global running, current_adjustments
    while running:
        time.sleep(ANALYSIS_INTERVAL)
        with lock:
            if not history:
                continue
            latest = history[-1]

        result = generate_eq_adjustments(
            latest["bands"], latest["rms_db"], sensitivity
        )
        current_adjustments = result

        if result:
            # Flatten vocal + music into one dict (Lua parser chỉ đọc flat JSON)
            flat = {}
            flat.update(result.get("vocal", {}))
            flat.update(result.get("music", {}))
            flat["is_singing"] = result.get("is_singing", False)
            flat["rms_db"] = float(latest["rms_db"])
            
            # Đọc pitch_offset và music_volume từ UI và chuyển qua cho Lua bridge
            current_genre = read_genre()
            flat["pitch_offset"] = current_genre.get("pitch_offset", 0)
            flat["music_volume"] = current_genre.get("music_volume", 0.56)  # 0.56 is default (-5.0dB)
            
            write_commands(flat)


def find_mixpre_port():
    """Tìm port capture của MixPre-6 trên PipeWire."""
    try:
        result = subprocess.run(
            ["pw-link", "-o"], capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if "MixPre" in line and "capture" in line.lower():
                return line.strip()
    except Exception:
        pass
    return None


def find_recorder_port(pid, retries=10):
    """Tìm input port của pw-record process vừa tạo."""
    for _ in range(retries):
        time.sleep(0.3)
        try:
            result = subprocess.run(
                ["pw-link", "-i"], capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if "vocal_ai" in line.lower() or "pw-record" in line.lower() or "pw-cat" in line.lower():
                    return line
        except Exception:
            pass
    return None


def passive_link(source_port, recorder_port):
    """Nối MixPre-6 → pw-record mà KHÔNG đụng kết nối khác."""
    try:
        subprocess.run(
            ["pw-link", source_port, recorder_port],
            capture_output=True, timeout=3
        )
        return True
    except Exception:
        return False


def main():
    global running

    parser = argparse.ArgumentParser(description="AI Real-time Vocal Analyzer")
    parser.add_argument("--target", default="",
        help="PipeWire target (default: auto-detect MixPre-6)")
    parser.add_argument("--sensitivity", choices=["low", "mid", "high"],
        default="mid", help="Mức độ AI can thiệp EQ")
    args = parser.parse_args()

    sens_map = {"low": 0.5, "mid": 1.0, "high": 1.5}
    sensitivity = sens_map[args.sensitivity]

    # ── Tìm MixPre-6 ──
    mic_port = find_mixpre_port()
    if mic_port:
        print(f"🎙️ Tìm thấy MixPre-6: {mic_port}")
    else:
        print("⚠️  Không tìm thấy MixPre-6. Sẽ dùng default input.")

    # ── Khởi động pw-record với --target 0 (KHÔNG tự nối!) ──
    # Đây là bí quyết: target 0 = tạo node nhưng KHÔNG auto-link
    # → Không gây xáo trộn bất kỳ kết nối nào trên qpwgraph
    cmd = [
        "pw-record",
        "-P", "node.name=Vocal_AI node.description=Vocal_AI media.name=Vocal_AI",
        "--rate", str(SAMPLE_RATE),
        "--channels", str(CHANNELS),
        "--format", "s16",
        "--target", "0",   # ★ KHÔNG AUTO-LINK
        "-",               # Output to stdout
    ]

    print(f"🔇 Khởi động pw-record (passive mode — không xáo trộn kết nối)...")
    print(f"   Command: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=dict(os.environ, PIPEWIRE_CLIENT_NAME="Vocal_AI")
        )
    except FileNotFoundError:
        print("❌ Không tìm thấy pw-record!")
        sys.exit(1)

    # ── Tìm recorder port và nối thủ công ──
    if mic_port:
        print("🔍 Đang tìm pw-record node trên PipeWire...")
        rec_port = find_recorder_port(proc.pid)
        if rec_port:
            print(f"🔗 Nối thủ công: {mic_port} → {rec_port}")
            if passive_link(mic_port, rec_port):
                print("✅ Đã nối! Chỉ nghe MixPre-6, KHÔNG đụng kết nối khác.")
            else:
                print("⚠️  Không nối được. Thử chạy lại.")
        else:
            print("⚠️  Không tìm thấy pw-record port. Sẽ thử fallback...")
            # Fallback: kill và chạy lại với auto-link đến MixPre-6
            proc.terminate()
            cmd_fallback = [
                "pw-record",
                "-P", "node.name=Vocal_AI node.description=Vocal_AI media.name=Vocal_AI",
                "--rate", str(SAMPLE_RATE),
                "--channels", str(CHANNELS),
                "--format", "s16",
                "--latency", "2048",
                "--target", "0",
                "-",
            ]
            proc = subprocess.Popen(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        # Không có MixPre-6 → dùng cách cũ với target chỉ định hoặc default
        proc.terminate()
        cmd_fallback = [
            "pw-record",
            "-P", "node.name=Vocal_AI node.description=Vocal_AI media.name=Vocal_AI",
            "--rate", str(SAMPLE_RATE),
            "--channels", str(CHANNELS),
            "--format", "s16",
            "--latency", "2048",
            "--target", "0",
            "-",
        ]
        proc = subprocess.Popen(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    print()

    # Start analysis thread
    analysis_thread = threading.Thread(target=analysis_loop, args=(sensitivity,), daemon=True)
    analysis_thread.start()

    print("✅ Đang lắng nghe mic... Hãy bắt đầu hát!")
    print("   (Kết nối trên qpwgraph KHÔNG bị thay đổi)")
    time.sleep(1)

    last_render = 0
    try:
        while running:
            raw = proc.stdout.read(CHUNK_BYTES)
            if not raw or len(raw) < CHUNK_BYTES:
                break

            samples = np.frombuffer(raw, dtype=np.int16)
            rms_db = compute_rms_db(samples)

            if rms_db < -50:
                now = time.time()
                if now - last_render > 1.0:
                    render_display({}, rms_db, 0, current_adjustments)
                    last_render = now
                continue

            window = np.hanning(len(samples))
            fft_result = np.fft.rfft(samples * window)
            magnitudes = np.abs(fft_result) / len(samples)
            freqs = np.fft.rfftfreq(len(samples), 1.0 / SAMPLE_RATE)

            bands = compute_band_energy(magnitudes, freqs)
            pitch_hz = detect_pitch(magnitudes, freqs)

            snapshot = {"bands": bands, "rms_db": rms_db, "pitch_hz": pitch_hz, "t": time.time()}
            with lock:
                history.append(snapshot)
                if pitch_hz > 50:
                    pitch_history.append(pitch_hz)
                else:
                    pitch_history.append(0)

            now = time.time()
            if now - last_render > 0.2:
                render_display(bands, rms_db, pitch_hz, current_adjustments)
                last_render = now

    except KeyboardInterrupt:
        pass
    finally:
        running = False
        proc.terminate()
        write_commands({"reset": True})
        print("\n🛑 Đã dừng. Kết nối qpwgraph không bị ảnh hưởng.")


if __name__ == "__main__":
    main()
