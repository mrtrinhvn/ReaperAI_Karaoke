-- ============================================================================
-- 🎤 AI KARAOKE PRO v4 — Tempo-Synced Delay & Echo Control
-- ============================================================================
-- v4 cải tiến:
--   • Delay: Pure slapback (không nhại nhiều lần), sync tempo
--   • Reverb: Decay phù hợp tempo, Pre-delay sync nhịp
--   • AI tự phát hiện echo buildup & điều chỉnh real-time
--   • Ghi BPM ra file cho Python AI đọc
-- ============================================================================

-- ═══════ HELPERS ═══════

function find_param(track, fx, name)
    local n = reaper.TrackFX_GetNumParams(track, fx)
    -- 1. Exact match first (tránh trường hợp "Hold" khớp nhầm vào "Threshold")
    for i = 0, n - 1 do
        local _, p = reaper.TrackFX_GetParamName(track, fx, i)
        if p and p:lower() == name:lower() then return i end
    end
    -- 2. Substring match fallback
    for i = 0, n - 1 do
        local _, p = reaper.TrackFX_GetParamName(track, fx, i)
        if p and p:lower():find(name:lower(), 1, true) then return i end
    end
    return -1
end

function set_p(track, fx, name, val)
    if fx < 0 then return end
    local i = find_param(track, fx, name)
    if i >= 0 then reaper.TrackFX_SetParamNormalized(track, fx, i, val) end
end

function add_fx(track, name)
    local idx = reaper.TrackFX_GetByName(track, name, false)
    if idx < 0 then
        -- Add at end if it doesn't exist
        idx = reaper.TrackFX_AddByName(track, name, false, 1)
    end
    if idx >= 0 then reaper.TrackFX_SetEnabled(track, idx, true) end
    return idx
end

function set_color(track, r, g, b)
    reaper.SetMediaTrackInfo_Value(track, "I_CUSTOMCOLOR",
        reaper.ColorToNative(r, g, b) | 0x1000000)
end

function dump_params(track, fx)
    if fx < 0 then return end
    local _, name = reaper.TrackFX_GetFXName(track, fx)
    reaper.ShowConsoleMsg("▸ " .. (name or "?") .. "\n")
    for i = 0, reaper.TrackFX_GetNumParams(track, fx) - 1 do
        local _, p = reaper.TrackFX_GetParamName(track, fx, i)
        local v = reaper.TrackFX_GetParamNormalized(track, fx, i)
        reaper.ShowConsoleMsg(string.format("    [%02d] %-25s = %.3f\n", i, p or "?", v))
    end
end

-- ═══════ MAIN ═══════

function setup()
    reaper.Undo_BeginBlock()
    reaper.PreventUIRefresh(1)

    -- Mặc định: Vocal dùng Input 3 (Mono = 2), Nhạc dùng Input 1/2 (Stereo = 1024)
    local vocal_input_val = 2
    local music_input_val = 1024

    -- Tìm đường dẫn .env để đọc cấu hình cổng đầu vào
    local info = debug.getinfo(1, 'S')
    local script_path = info.source:sub(2)
    local project_dir = script_path:match("(.*[/\\])")
    if project_dir then
        local env_file = io.open(project_dir .. ".env", "r")
        if env_file then
            local music_in_l, vocal_in_l
            for line in env_file:lines() do
                if not line:match("^#") and line:match("=") then
                    local key, val = line:match("^([^=]+)=(.*)$")
                    if key and val then
                        key = key:gsub("%s+", "")
                        val = val:gsub("%s+", ""):gsub('"', ''):gsub("'", "")
                        if key == "REAPER_MUSIC_IN_L" then
                            music_in_l = val
                        elseif key == "REAPER_VOCAL_IN_L" then
                            vocal_in_l = val
                        end
                    end
                end
            end
            env_file:close()

            if music_in_l then
                local num = music_in_l:match("in(%d+)")
                if num then
                    local idx = tonumber(num) - 1
                    if idx >= 0 then music_input_val = 1024 + idx * 32 end
                end
            end

            if vocal_in_l then
                local num = vocal_in_l:match("in(%d+)")
                if num then
                    local idx = tonumber(num) - 1
                    if idx >= 0 then vocal_input_val = idx end
                end
            end
        end
    end

    -- Hàm hỗ trợ tìm track theo tên
    local function get_or_create_track(name, is_stereo_input)
        local t
        local is_new = false
        for i = 0, reaper.CountTracks(0) - 1 do
            local current_t = reaper.GetTrack(0, i)
            local _, tname = reaper.GetSetMediaTrackInfo_String(current_t, "P_NAME", "", false)
            if tname:lower():find(name:lower(), 1, true) then
                t = current_t
                break
            end
        end

        if not t then
            reaper.InsertTrackAtIndex(reaper.CountTracks(0), true)
            t = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
            reaper.GetSetMediaTrackInfo_String(t, "P_NAME", name, true)
            is_new = true
        end
        
        reaper.SetMediaTrackInfo_Value(t, "I_RECARM", 1)
        reaper.SetMediaTrackInfo_Value(t, "I_RECMON", 1)
        if is_stereo_input then
            reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", music_input_val)
        else
            reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", vocal_input_val)
        end
        return t, is_new
    end

    -- ══════════════════════════════════════════════════════════════
    -- KHỞI TẠO 5 TRACK CHUYÊN NGHIỆP (OPTION C - HYBRID MASTERPIECE)
    -- ══════════════════════════════════════════════════════════════
    local voc, is_new_voc = get_or_create_track("VOCAL", false)
    set_color(voc, 230, 55, 55)
    reaper.SetMediaTrackInfo_Value(voc, "D_VOL", 1.0)
    reaper.SetMediaTrackInfo_Value(voc, "D_PAN", 0.0)

    local voc_par, is_new_voc_par = get_or_create_track("VOCAL PARALLEL", false)
    set_color(voc_par, 255, 92, 138)
    reaper.SetMediaTrackInfo_Value(voc_par, "D_VOL", 0.22) -- Trộn song song dày dặn hơn (-13.1dB)
    reaper.SetMediaTrackInfo_Value(voc_par, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECINPUT", -1)
 
    local voc_rev, is_new_voc_rev = get_or_create_track("VOCAL REVERB", false)
    set_color(voc_rev, 56, 189, 248)
    reaper.SetMediaTrackInfo_Value(voc_rev, "D_VOL", 0.63) -- Reverb level (-4dB, tăng thêm 11dB để vang dạt dào nịnh giọng)
    reaper.SetMediaTrackInfo_Value(voc_rev, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECINPUT", -1)
 
    local voc_del, is_new_voc_del = get_or_create_track("VOCAL DELAY", false)
    set_color(voc_del, 234, 179, 8)
    reaper.SetMediaTrackInfo_Value(voc_del, "D_VOL", 0.63) -- Delay level (-4dB, tăng thêm 3dB để echo nổi bật)
    reaper.SetMediaTrackInfo_Value(voc_del, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECINPUT", -1)

    local mus, is_new_mus = get_or_create_track("NHẠC", true)
    set_color(mus, 40, 120, 220)
    reaper.SetMediaTrackInfo_Value(mus, "D_VOL", 0.56) -- -5.0dB (tối ưu theo phản hồi người dùng)
    reaper.SetMediaTrackInfo_Value(mus, "D_PAN", 0.0)
    
    -- Dọn dẹp Stereo Width cũ trên track NHẠC
    for i = reaper.TrackFX_GetCount(mus) - 1, 0, -1 do
        local _, fx_name = reaper.TrackFX_GetFXName(mus, i)
        if fx_name and (fx_name:lower():find("stereo width") or fx_name:lower():find("stereo_width")) then
            reaper.TrackFX_Delete(mus, i)
        end
    end

    -- XÓA TẤT CẢ CÁC SEND CŨ TRÊN TRACK VOCAL (tránh trùng lặp)
    local num_sends = reaper.GetTrackNumSends(voc, 0)
    for i = num_sends - 1, 0, -1 do
        reaper.RemoveTrackSend(voc, 0, i)
    end

    -- ĐỊNH TUYẾN SEND MỚI CHO BÀN MIX SONG SONG
    -- 1. Send VOCAL sang Parallel Vocal
    local send_par = reaper.CreateTrackSend(voc, voc_par)
    reaper.SetTrackSendInfo_Value(voc, 0, send_par, "D_VOL", 1.0)
    reaper.SetTrackSendInfo_Value(voc, 0, send_par, "I_SENDMODE", 0) -- Post-Fader

    -- 2. Send VOCAL sang Vocal Reverb
    local send_rev = reaper.CreateTrackSend(voc, voc_rev)
    reaper.SetTrackSendInfo_Value(voc, 0, send_rev, "D_VOL", 1.0)
    reaper.SetTrackSendInfo_Value(voc, 0, send_rev, "I_SENDMODE", 0)

    -- 3. Send VOCAL sang Vocal Delay
    local send_del = reaper.CreateTrackSend(voc, voc_del)
    reaper.SetTrackSendInfo_Value(voc, 0, send_del, "D_VOL", 1.0)
    reaper.SetTrackSendInfo_Value(voc, 0, send_del, "I_SENDMODE", 0)

    -- 4. Send Sidechain từ VOCAL sang VOCAL REVERB (chạy vào cổng 3/4 của Compressor)
    local sc_rev = reaper.CreateTrackSend(voc, voc_rev)
    reaper.SetTrackSendInfo_Value(voc, 0, sc_rev, "D_VOL", 1.0)
    reaper.SetTrackSendInfo_Value(voc, 0, sc_rev, "I_SENDMODE", 1) -- Pre-Fader / Post-FX
    reaper.SetTrackSendInfo_Value(voc, 0, sc_rev, "I_DSTCHAN", 2)  -- Aux Input 3/4

    -- 5. Send Sidechain từ VOCAL sang VOCAL DELAY (chạy vào cổng 3/4 của Compressor)
    local sc_del = reaper.CreateTrackSend(voc, voc_del)
    reaper.SetTrackSendInfo_Value(voc, 0, sc_del, "D_VOL", 1.0)
    reaper.SetTrackSendInfo_Value(voc, 0, sc_del, "I_SENDMODE", 1) -- Pre-Fader / Post-FX
    reaper.SetTrackSendInfo_Value(voc, 0, sc_del, "I_DSTCHAN", 2)  -- Aux Input 3/4

    -- XÓA TẤT CẢ CÁC SEND CŨ TRÊN TRACK VOCAL DELAY (tránh trùng lặp)
    local num_del_sends = reaper.GetTrackNumSends(voc_del, 0)
    for i = num_del_sends - 1, 0, -1 do
        reaper.RemoveTrackSend(voc_del, 0, i)
    end

    -- 6. Send từ VOCAL DELAY sang VOCAL REVERB (đưa Echo vào không gian Reverb để âm hòa quyện)
    local send_del_to_rev = reaper.CreateTrackSend(voc_del, voc_rev)
    reaper.SetTrackSendInfo_Value(voc_del, 0, send_del_to_rev, "D_VOL", 0.25) -- -12dB send level
    reaper.SetTrackSendInfo_Value(voc_del, 0, send_del_to_rev, "I_SENDMODE", 0) -- Post-Fader

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 1: 🎙️ VOCAL (Core processing)
    -- ══════════════════════════════════════════════════════════════
    -- Dọn dẹp ReaDelay và ReaVerbate cũ trên track VOCAL để chuyển hẳn sang Aux bus
    for i = reaper.TrackFX_GetCount(voc) - 1, 0, -1 do
        local _, fx_name = reaper.TrackFX_GetFXName(voc, i)
        if fx_name and (fx_name:lower():find("readelay") or fx_name:lower():find("reaverbate")) then
            reaper.TrackFX_Delete(voc, i)
        end
    end

    -- FX0: Noise Gate lọc ồn phòng sạch sẽ
    local vgate = add_fx(voc, "ReaGate")
    set_p(voc, vgate, "Threshold", 0.0010)       -- -54.0dB (nhạy, cực kỳ dễ bắt mic)
    set_p(voc, vgate, "Attack", 0.002)         -- 2ms
    set_p(voc, vgate, "Release", 0.15)         -- 150ms
    set_p(voc, vgate, "Hold", 0.05)            -- 50ms

    -- FX1: Auto-Tune
    local at = add_fx(voc, "MAutoPitch")
    if at < 0 then at = add_fx(voc, "Graillon") end
    if at < 0 then at = add_fx(voc, "Fat1") end
    if at < 0 then at = add_fx(voc, "ReaTune") end

    -- FX2: ReaEQ (Vocal shaping - Khớp trung âm ấm áp của khonggianhatok.wav)
    local veq = add_fx(voc, "ReaEQ")
    -- Band 5: High Pass (Low Cut ở 120Hz)
    set_p(voc, veq, "Freq-High Pass 5", 0.16)   -- ~120Hz
    -- Band 1: Low Shelf (giữ phẳng ở 0dB)
    set_p(voc, veq, "Freq-Low Shelf", 0.085)
    set_p(voc, veq, "Gain-Low Shelf", 0.5)      -- 0dB
    -- Band 2: Bell (Mud Cut ở 250Hz, giảm nhẹ -1.5dB để giữ độ đầy đặn cho giọng)
    set_p(voc, veq, "Freq-Band 2", 0.26)        -- ~250Hz
    set_p(voc, veq, "Gain-Band 2", 0.47)        -- -1.5dB
    -- Band 3: Bell (Clarity Boost ở 3.2kHz, giảm nhẹ về +1.0dB để bớt ròn thân, nghe êm tai và đỡ mệt)
    set_p(voc, veq, "Freq-Band 3", 0.62)        -- ~3.2kHz
    set_p(voc, veq, "Gain-Band 3", 0.521)       -- +1.0dB
    -- Band 4: High Shelf (Air & Brilliance hạ về 7kHz, tăng +4.5dB để ròn phần cao, tạo chi tiết sạch, bay đẹp)
    set_p(voc, veq, "Freq-High Shelf 4", 0.80)  -- ~7.0kHz
    set_p(voc, veq, "Gain-High Shelf 4", 0.594) -- +4.5dB
    set_p(voc, veq, "BW-High Shelf 4", 0.20)

    -- FX3: ReaComp (Vocal Compressor mượt mà)
    local vcomp = add_fx(voc, "ReaComp")
    set_p(voc, vcomp, "Thresh", 0.030)         -- -24.4dB (norm 0.030 khớp giọng nói/hát)
    set_p(voc, vcomp, "Ratio", 0.025)          -- ~3.5:1 (norm 0.025 tránh bị nén quá chặt)
    set_p(voc, vcomp, "Attack", 0.05)          -- 5ms (bắt mic nhanh hơn)
    set_p(voc, vcomp, "Release", 0.15)         -- 150ms
    set_p(voc, vcomp, "Knee", 0.35)
    set_p(voc, vcomp, "Auto make", 1.0)

    -- FX4: JS Saturation (Hài âm tạo độ ấm đắt tiền)
    local vsat = add_fx(voc, "Saturation")
    if vsat >= 0 then
        set_p(voc, vsat, "Amount (%)", 0.08)   -- 8% ấm analog
    end

    -- FX5: Chorus (Tắt bỏ trên track Vocal mộc để giữ giọng ca sắc nét ở trung tâm, tránh tiếng bị lảo đảo rẻ tiền)
    local chorus = add_fx(voc, "Chorus")
    if chorus >= 0 then
        set_p(voc, chorus, "Rate", 0.25)
        set_p(voc, chorus, "Depth", 0.30)
        set_p(voc, chorus, "Mix", 0.0)          -- Set về 0% Mix
    end

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 2: 🔊 VOCAL PARALLEL (Nén song song)
    -- ══════════════════════════════════════════════════════════════
    -- Smashed Compressor
    local vpcomp = add_fx(voc_par, "ReaComp")
    set_p(voc_par, vpcomp, "Thresh", 0.20)     -- -35dB nén sập sàn
    set_p(voc_par, vpcomp, "Ratio", 0.70)      -- 10:1 ratio cực lớn
    set_p(voc_par, vpcomp, "Attack", 0.08)     -- 5ms
    set_p(voc_par, vpcomp, "Release", 0.40)    -- 150ms
    set_p(voc_par, vpcomp, "Auto make", 1.0)

    -- EQ nắn tiếng (Cắt trầm dưới 200Hz, làm sáng)
    local vpeq = add_fx(voc_par, "ReaEQ")
    set_p(voc_par, vpeq, "Freq-Low Shelf", 0.23)         -- ~200Hz
    set_p(voc_par, vpeq, "Gain-Low Shelf", 0.0)          -- -inf dB (cắt trầm sạch sẽ)
    set_p(voc_par, vpeq, "Freq-Band 2", 0.45)            -- ~3kHz
    set_p(voc_par, vpeq, "Gain-Band 2", 0.58)            -- ~+2.3dB boost
    set_p(voc_par, vpeq, "Freq-Band 3", 0.75)            -- ~10kHz
    set_p(voc_par, vpeq, "Gain-Band 3", 0.56)            -- ~+1.5dB boost

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 3: 🌊 VOCAL REVERB (Aux Reverb)
    -- ══════════════════════════════════════════════════════════════
    -- Filter Abbey Road ấm áp (Cắt trầm hợp lý dưới 130Hz, giữ phẳng 350Hz để lấp đầy không gian đầy đặn)
    local vreveq = add_fx(voc_rev, "ReaEQ")
    set_p(voc_rev, vreveq, "Freq-Low Shelf", 0.18)       -- ~130Hz
    set_p(voc_rev, vreveq, "Gain-Low Shelf", 0.0)        -- -inf dB (cắt trầm)
    set_p(voc_rev, vreveq, "Freq-High Pass 5", 0.18)     -- ~130Hz (HPF)
    
    set_p(voc_rev, vreveq, "Freq-Band 2", 0.30)          -- ~350Hz
    set_p(voc_rev, vreveq, "Gain-Band 2", 0.50)          -- 0dB (giữ phẳng để Reverb ấm dày, lấp đầy khoảng trống)
    
    set_p(voc_rev, vreveq, "Gain-Band 3", 0.50)          -- 0dB (flat)
    
    -- Mở rộng dải cao (Vang cao) để tiếng xì vang lấp lánh, bay bổng
    set_p(voc_rev, vreveq, "Freq-High Shelf 4", 0.78)    -- ~6.5kHz
    set_p(voc_rev, vreveq, "Gain-High Shelf 4", 0.54)    -- +2.0dB

    -- Chorus làm rộng và tạo độ bóng (modulate) cho đuôi Reverb
    local rev_chorus = add_fx(voc_rev, "Chorus")
    if rev_chorus >= 0 then
        set_p(voc_rev, rev_chorus, "Rate", 0.15)
        set_p(voc_rev, rev_chorus, "Depth", 0.20)
        set_p(voc_rev, rev_chorus, "Mix", 0.35)        -- 35% Chorus để tạo đuôi reverb long lanh, bóng bẩy trên stream
    end

    -- Reverb 100% Wet (Phòng rộng rãi, mịn màng và vang xa bay bổng)
    local vrev = add_fx(voc_rev, "ReaVerbate")
    set_p(voc_rev, vrev, "Wet", 1.0)
    set_p(voc_rev, vrev, "Dry", 0.0)
    set_p(voc_rev, vrev, "Room Size", 0.22)             -- Tăng lên 22% để phòng rộng mở hơn, vang bay xa hơn
    set_p(voc_rev, vrev, "Dampening", 0.30)             -- Giảm về 30% Dampening để giữ lại các đuôi vang cao sáng, mịn
    set_p(voc_rev, vrev, "Delay", 0.071)                -- Pre-delay = 7.1ms (khớp first reflection từ autocorrelation)
    set_p(voc_rev, vrev, "Width", 1.0)
    set_p(voc_rev, vrev, "Stereo", 0.90)

    -- Sidechain Ducker (Reverb né giọng thật)
    local vrev_comp = add_fx(voc_rev, "ReaComp")
    reaper.TrackFX_SetParam(voc_rev, vrev_comp, 8, 1.0) -- Auxiliary Input L+R
    set_p(voc_rev, vrev_comp, "Thresh", 0.06)   -- ~-18.8dB (ngưỡng nhạy bén để dìm vang khi đang hát)
    set_p(voc_rev, vrev_comp, "Ratio", 0.015)   -- ~2.5:1 ratio (né nhẹ nhàng tự nhiên)
    set_p(voc_rev, vrev_comp, "Attack", 0.20)   -- 15ms
    set_p(voc_rev, vrev_comp, "Release", 0.55)  -- 300ms
    reaper.TrackFX_SetEnabled(voc_rev, vrev_comp, false) -- Tắt Ducker để vang quyện liên tục ảo diệu dạt dào khi hát live

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 4: ✨ VOCAL DELAY (Aux Delay)
    -- ══════════════════════════════════════════════════════════════
    -- Filter HPF/LPF (Cắt trầm 180Hz, Cắt cao sâu ở 3.5kHz để tiếng nhại ấm rực rỡ dải Mid)
    local vdeleq = add_fx(voc_del, "ReaEQ")
    set_p(voc_del, vdeleq, "Freq-Low Shelf", 0.22)       -- ~180Hz
    set_p(voc_del, vdeleq, "Gain-Low Shelf", 0.0)        -- -inf dB (cắt hoàn toàn dải trầm)
    set_p(voc_del, vdeleq, "Freq-High Pass 5", 0.22)     -- ~180Hz (kết hợp tạo độ dốc cắt cực mạnh)
    set_p(voc_del, vdeleq, "Gain-Band 2", 0.50)          -- 0dB (flat)
    set_p(voc_del, vdeleq, "Gain-Band 3", 0.50)          -- 0dB (flat)
    set_p(voc_del, vdeleq, "Freq-High Shelf 4", 0.70)    -- Hạ tần số cắt cao về ~3.5kHz phù hợp trung âm ấm của WAV mẫu
    set_p(voc_del, vdeleq, "Gain-High Shelf 4", 0.0)     -- -inf dB (cắt hoàn toàn dải cao)

    -- Delay 100% Wet (Khớp khonggianhatok.wav: Echo chính ~63ms, feedback 60%, Semi-Rhythmic)
    local vdel = add_fx(voc_del, "ReaDelay")
    set_p(voc_del, vdel, "Dry", 0.0)
    set_p(voc_del, vdel, "1: Volume", 1.0)
    set_p(voc_del, vdel, "1: Feedback", 0.60)            -- Feedback 60% tạo chuỗi 6 echo tự nhiên (khớp WAV: 75% raw, cap 60% an toàn)
    set_p(voc_del, vdel, "1: Length (time)", 0.0127)     -- Đặt delay = 63ms (0.0127 trên thang 5s, khớp echo interval phân tích)
    set_p(voc_del, vdel, "1: Length (musical)", 0.0)     -- Tắt đồng bộ hóa nốt nhạc của VST để dùng mili-giây từ Python
    set_p(voc_del, vdel, "1: Lowpass", 0.60)             -- Lọc bớt dải cao của delay để tiếng echo ấm hơn

    -- Sidechain Ducker (Delay né giọng thật)
    local vdel_comp = add_fx(voc_del, "ReaComp")
    reaper.TrackFX_SetParam(voc_del, vdel_comp, 8, 1.0) -- Auxiliary Input L+R
    set_p(voc_del, vdel_comp, "Thresh", 0.06)   -- ~-18.8dB (dìm mạnh delay khi đang hát)
    set_p(voc_del, vdel_comp, "Ratio", 0.02)    -- ~3:1 ratio
    set_p(voc_del, vdel_comp, "Attack", 0.10)   -- 5ms (phản hồi cực nhanh để nén ngay)
    set_p(voc_del, vdel_comp, "Release", 0.45)  -- 150ms (nhả nhanh để vang lên khi nghỉ lấy hơi)
    reaper.TrackFX_SetEnabled(voc_del, vdel_comp, false) -- Tắt Ducker để echo bay bổng ảo diệu dạt dào khi hát live

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 5: 🎵 NHẠC NỀN
    -- ══════════════════════════════════════════════════════════════
    local rpitch = add_fx(mus, "ReaPitch")
    set_p(mus, rpitch, "Shift (semitones)", 0.5)

    local meq = add_fx(mus, "ReaEQ")
    set_p(mus, meq, "Freq-Band 1", 0.30)
    set_p(mus, meq, "Gain-Band 1", 0.47)
    set_p(mus, meq, "Bandwidth-Band 1", 0.5)
    set_p(mus, meq, "Freq-Band 2", 0.40)
    set_p(mus, meq, "Gain-Band 2", 0.43)
    set_p(mus, meq, "Bandwidth-Band 2", 0.45)
    set_p(mus, meq, "Freq-Band 3", 0.52)
    set_p(mus, meq, "Gain-Band 3", 0.47)
    set_p(mus, meq, "Bandwidth-Band 3", 0.4)
    set_p(mus, meq, "Freq-Band 4", 0.08)
    set_p(mus, meq, "Gain-Band 4", 0.56)
    set_p(mus, meq, "Bandwidth-Band 4", 0.3)

    local mcomp = add_fx(mus, "ReaComp")
    set_p(mus, mcomp, "Thresh", 0.70)
    set_p(mus, mcomp, "Ratio", 0.08)
    set_p(mus, mcomp, "Attack", 0.25)
    set_p(mus, mcomp, "Release", 0.40)


    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST MASTER BUS (Sân khấu mastering)
    -- ══════════════════════════════════════════════════════════════
    local master = reaper.GetMasterTrack(0)
    for i = reaper.TrackFX_GetCount(master) - 1, 0, -1 do
        reaper.TrackFX_Delete(master, i)
    end

    -- 1. Master EQ (Smile curve & IEM Bass Leakage Compensation)
    local meq2 = add_fx(master, "ReaEQ")
    -- Band 1: Low Shelf ở 80Hz, tăng +3.8dB để bù đắp rò rỉ bass của tai nghe IEM khi đeo lỏng, nghe sát thì bass cực sâu ấm
    set_p(master, meq2, "Freq-Low Shelf", 0.07)       -- ~80Hz
    set_p(master, meq2, "Gain-Low Shelf", 0.58)       -- +3.8dB
    
    set_p(master, meq2, "Freq-Band 2", 0.25)          -- Cắt đục 500Hz
    set_p(master, meq2, "Gain-Band 2", 0.47)          -- -1.5dB (bản gốc là 0.48)
    set_p(master, meq2, "Bandwidth-Band 2", 0.5)
    
    set_p(master, meq2, "Freq-Band 3", 0.45)          -- Sáng nhẹ 3kHz
    set_p(master, meq2, "Gain-Band 3", 0.54)          -- +2.0dB
    set_p(master, meq2, "Bandwidth-Band 3", 0.5)
    
    set_p(master, meq2, "Freq-High Shelf 4", 0.75)    -- ~10kHz dải Air
    set_p(master, meq2, "Gain-High Shelf 4", 0.60)    -- +4.8dB Air

    -- 2. Master Multiband Compressor (Keo dán mix)
    local mxc = add_fx(master, "ReaXcomp")
    if mxc >= 0 then
        set_p(master, mxc, "Thresh", 0.70)
        set_p(master, mxc, "Ratio", 0.15)
        set_p(master, mxc, "Attack", 0.20)
        set_p(master, mxc, "Release", 0.35)
    end


    -- 4. Master Limiter (Làm to nhạc cực đại, chống bể tiếng)
    local mlim = add_fx(master, "ReaLimit")
    if mlim >= 0 then
        set_p(master, mlim, "Threshold", 0.7708)  -- -4.5dB threshold
        set_p(master, mlim, "Ceiling", 0.9792)    -- -0.5dB ceiling
    end

    -- ══════════════════════════════════════════════════════════════
    -- PROJECT SETTINGS + SYNC
    -- ══════════════════════════════════════════════════════════════
    reaper.SetCurrentBPM(0, 87, true)  -- 87 BPM khớp phân tích file khonggianhatok.wav (beat regularity 98.8%)
    reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)

    local bpm_file = io.open("/tmp/ai_karaoke_bpm.txt", "w")
    if bpm_file then
        bpm_file:write(tostring(reaper.Master_GetTempo()))
        bpm_file:close()
    end

    reaper.Main_OnCommand(40078, 0) -- Show Mixer
    reaper.SetTrackSelected(voc, true)
    reaper.Main_OnCommand(40291, 0) -- Show FX for selected track

    -- ══════════════════════════════════════════════════════════════
    -- DEBUG: In tham số
    -- ══════════════════════════════════════════════════════════════
    reaper.ShowConsoleMsg("\n═══ AI KARAOKE MASTERPIECE v6 — Parameter Dump ═══\n\n")
    reaper.ShowConsoleMsg("── VOCAL DRY ──\n")
    dump_params(voc, vgate)
    dump_params(voc, veq)
    dump_params(voc, vcomp)
    if chorus >= 0 then dump_params(voc, chorus) end

    reaper.ShowConsoleMsg("── VOCAL PARALLEL ──\n")
    dump_params(voc_par, vpcomp)
    dump_params(voc_par, vpeq)

    reaper.ShowConsoleMsg("── VOCAL REVERB ──\n")
    dump_params(voc_rev, vreveq)
    dump_params(voc_rev, vrev)
    dump_params(voc_rev, vrev_comp)

    reaper.ShowConsoleMsg("── VOCAL DELAY ──\n")
    dump_params(voc_del, vdeleq)
    dump_params(voc_del, vdel)
    dump_params(voc_del, vdel_comp)

    reaper.ShowConsoleMsg("\n── NHẠC NỀN ──\n")
    dump_params(mus, rpitch)
    dump_params(mus, meq)
    dump_params(mus, mcomp)

    reaper.ShowConsoleMsg("\n── MASTER ──\n")
    dump_params(master, meq2)
    if mxc >= 0 then dump_params(master, mxc) end
    if mlim >= 0 then dump_params(master, mlim) end

    reaper.PreventUIRefresh(-1)
    reaper.UpdateArrange()
    reaper.TrackList_AdjustWindows(false)
    reaper.Undo_EndBlock("AI Karaoke Masterpiece v6", -1)
    reaper.Main_SaveProject(0, false)

    reaper.ShowConsoleMsg("\n🎤 AI KARAOKE MASTERPIECE v6 — Configured according to khonggianhatok.wav!\n")
end

setup()
