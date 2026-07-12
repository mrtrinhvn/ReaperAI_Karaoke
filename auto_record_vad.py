import numpy as np
import subprocess
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tự động thu âm khi có tiếng hát (Voice Activity Detection)")
    parser.add_argument("--threshold", type=float, default=-25.0, help="Ngưỡng âm lượng (dB) để kích hoạt thu âm")
    parser.add_argument("--duration", type=int, default=15, help="Thời gian thu âm (giây)")
    args = parser.parse_args()

    print("⏳ Đang lắng nghe... (Hãy cất giọng, hệ thống sẽ tự động thu âm và phân tích)")

    # Monitor raw mic (MixPre-6)
    cmd_mic = [
        'pw-record', '--target', 'alsa_input.usb-Sound_Devices__LLC_MixPre-6_QC0418025067-00.analog-stereo', 
        '--format', 'f32', '--rate', '48000', '--channels', '1', '-'
    ]
    p = subprocess.Popen(cmd_mic, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        # Chờ tiếng hát
        while True:
            data = p.stdout.read(48000 * 4 // 4) # Đọc 0.25s
            if not data: 
                time.sleep(0.1)
                continue
            s = np.frombuffer(data, np.float32)
            rms = 20 * np.log10(np.sqrt(np.mean(s**2)) + 1e-10)
            
            if rms > args.threshold:
                start_level = rms
                break
    except KeyboardInterrupt:
        print("\nĐã hủy.")
        p.terminate()
        return

    p.terminate()

    # Cố gắng lấy ID động của REAPER (nếu Reaper khởi động lại, ID sẽ thay đổi)
    try:
        reaper_id = subprocess.check_output(
            "pw-dump | jq '.[] | select(.info.props[\"node.name\"] == \"REAPER\") | .id' | head -n 1", 
            shell=True, text=True
        ).strip()
        if reaper_id:
            default_target = reaper_id
            print(f"🔗 Đã tự động kết nối với REAPER (Node ID: {default_target})")
        else:
            default_target = "528967"
    except Exception:
        default_target = "528967"

    target = getattr(args, "target", None)
    if not target:
        target = default_target

    print(f"\n🎙️ BẮT ĐẦU THU (Phát hiện hát: {start_level:.1f}dB) - Hãy hát liên tục {args.duration} giây nhé!")

    # Thu âm thanh Mix đầu ra
    out_file = "/tmp/karaoke_auto_final.wav"
    subprocess.run(f"pw-record --target {target} --format f32 --rate 48000 --channels 2 {out_file} & PID=$!; sleep {args.duration}; kill $PID 2>/dev/null", shell=True)
    print("✅ Đã thu xong! Đang phân tích Spectrum...")

    # Phân tích
    r = subprocess.run(['ffmpeg','-y','-i', out_file, '-f','f32le','-ac','2','-ar','48000','-'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    s = np.frombuffer(r.stdout, np.float32).reshape(-1,2)
    L, R = s[:,0], s[:,1]
    mono = (L + R) / 2
    sr = 48000

    peak_db = 20 * np.log10(np.max(np.abs(mono)) + 1e-10)
    rms_db = 20 * np.log10(np.sqrt(np.mean(mono**2)) + 1e-10)
    clip = np.sum(np.abs(mono) > 0.99)
    print(f"📊 Thu âm {len(mono)/sr:.1f}s | Peak={peak_db:.1f}dB | RMS={rms_db:.1f}dB | Clip={clip} {'⚠️' if clip>0 else '✅'}")

    from numpy.fft import rfft, rfftfreq
    freqs = rfftfreq(len(mono), 1.0/sr)
    fft = np.abs(rfft(mono)) / len(mono)
    bands = [
        ("Sub20-80", 20, 80, 14.2),
        ("Bass80-250", 80, 250, 24.8),
        ("LMid250-500", 250, 500, 36.0),
        ("Mid500-1k", 500, 1000, 18.7),
        ("UMid1-2.5k", 1000, 2500, 4.8),
        ("Pres2.5-5k", 2500, 5000, 0.9),
        ("Bright5-8k", 5000, 8000, 0.2),
        ("Air8-16k", 8000, 16000, 0.3)
    ]
    total = sum(np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) for _,lo,hi,_ in bands)

    print(f"\n📈 SPECTRUM (Hiện tại vs Chuẩn):")
    print(f"  {'Band':<15} {'Thực tế':>8} {'Ref':>6} {'Nhận xét'}")
    for i, (n, lo, hi, ref) in enumerate(bands):
        e = np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) / total * 100
        d = e - ref
        f = "✅ ỔN ĐỊNH" if abs(d) < 4 else ("📈 DƯ" if d > 0 else "📉 THIẾU")
        print(f"  {n:<15} {e:7.1f}% {ref:5.1f}%   {f}")

if __name__ == "__main__":
    main()
