import time
import os
import subprocess

LUA_SCRIPT = """
local function val_to_db(val)
    if val < 0.0000001 then return -150.0 end
    return 20 * math.log(val, 10)
end

local master = reaper.GetMasterTrack(0)
local voc = reaper.GetTrack(0, 0)
local music = reaper.GetTrack(0, 4)

local max_master = 0
local max_voc = 0
local max_music = 0

local start_time = reaper.time_precise()

local function loop()
    local now = reaper.time_precise()
    if now - start_time > 15 then
        local f = io.open("/tmp/peak_log.txt", "w")
        f:write(string.format("Master=%.2f\\n", val_to_db(max_master)))
        f:write(string.format("Vocal=%.2f\\n", val_to_db(max_voc)))
        if music then
            f:write(string.format("Music=%.2f\\n", val_to_db(max_music)))
        end
        f:close()
        return
    end

    local p_master = math.max(reaper.Track_GetPeakInfo(master, 0), reaper.Track_GetPeakInfo(master, 1))
    local p_voc = math.max(reaper.Track_GetPeakInfo(voc, 0), reaper.Track_GetPeakInfo(voc, 1))
    
    if p_master > max_master then max_master = p_master end
    if p_voc > max_voc then max_voc = p_voc end
    
    if music then
        local p_music = math.max(reaper.Track_GetPeakInfo(music, 0), reaper.Track_GetPeakInfo(music, 1))
        if p_music > max_music then max_music = p_music end
    end

    reaper.defer(loop)
end

loop()
"""

def main():
    print("⏳ Đang chuẩn bị giám sát âm thanh (Clipping Monitor)...")
    with open("/tmp/monitor_clip.lua", "w") as f:
        f.write(LUA_SCRIPT)
    
    # Remove old log if exists
    if os.path.exists("/tmp/peak_log.txt"):
        os.remove("/tmp/peak_log.txt")
        
    print("🎙️ BẮT ĐẦU GIÁM SÁT! Hãy hát thật to và bốc trong 15 giây tới để test nhé!")
    subprocess.run(["/opt/REAPER/reaper", "-nonewinst", "/tmp/monitor_clip.lua"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Actively poll for the result file
    for i in range(20):
        print(f"Đang phân tích... ({i}s/15s)", end="\r")
        time.sleep(1)
        if i >= 14 and os.path.exists("/tmp/peak_log.txt"):
            break
            
    print("\n✅ Đã xong! Đang phân tích kết quả...\n")
    
    if not os.path.exists("/tmp/peak_log.txt"):
        print("❌ Lỗi: Không nhận được dữ liệu từ REAPER. Hãy chắc chắn REAPER đang chạy.")
        return
        
    with open("/tmp/peak_log.txt", "r") as f:
        data = f.read()
        
    print("📊 KẾT QUẢ ĐỈNH ÂM LƯỢNG (PEAKS):")
    lines = data.strip().split("\n")
    for line in lines:
        if not line: continue
        name, val_str = line.split("=")
        val = float(val_str)
        
        status = "✅ An toàn"
        if val > 0.0:
            status = "❌ CLIPPING (Vỡ tiếng)"
        elif val > -3.0:
            status = "⚠️ Cảnh báo (Rất gần mức vỡ)"
            
        print(f"  - {name.ljust(10)}: {val:6.2f} dB  |  {status}")
        
    print("\n💡 CHUẨN ĐOÁN:")
    master_val = float([l.split("=")[1] for l in lines if l.startswith("Master")][0])
    voc_val = float([l.split("=")[1] for l in lines if l.startswith("Vocal")][0])
    music_val = float([l.split("=")[1] for l in lines if l.startswith("Music")][0]) if "Music" in data else -100
    
    if master_val > 0:
        if voc_val > 0:
            print("👉 NGUYÊN NHÂN: Track VOCAL của bạn quá to, gây vỡ tiếng trực tiếp từ Vocal kéo theo Master bị vỡ.")
            print("👉 CÁCH FIX: Hát xa mic ra một chút, hoặc vặn núm Gain trên Soundcard nhỏ lại.")
        elif music_val > 0:
            print("👉 NGUYÊN NHÂN: Nhạc (Music) đang quá to gây vỡ tiếng.")
        else:
            print("👉 NGUYÊN NHÂN: Cả Vocal và Nhạc đều không vỡ, nhưng KHI CỘNG LẠI với nhau trên Master thì vượt quá giới hạn (Master Clipping).")
            print("👉 CÁCH FIX: Giảm âm lượng tổng (Master) hoặc giảm nhẹ cả nhạc lẫn mic.")
    else:
        print("👉 KẾT LUẬN: Không có hiện tượng vỡ tiếng ảo (Digital Clipping) trong bản thu này. Nếu bạn vẫn nghe thấy nổ loẹt xoẹt, đó là do Buffer Size của Soundcard/CPU (chứ không phải do âm lượng).")

if __name__ == "__main__":
    main()
