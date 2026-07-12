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
            if tname then
                local tname_clean = tname:lower()
                local match = false
                if name == "NHẠC" and (tname_clean:find("nhac", 1, true) or tname_clean:find("nhạc", 1, true) or tname_clean:sub(1, 2) == "nh") then
                    match = true
                elseif tname_clean:find(name:lower(), 1, true) then
                    match = true
                end
                if match then
                    t = current_t
                    break
                end
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
    reaper.SetMediaTrackInfo_Value(voc, "D_VOL", 0.80) -- ~-1.9dB (tham chiếu Laiganhonanh: vocal phủ lên trên nhạc, center mạnh)
    reaper.SetMediaTrackInfo_Value(voc, "D_PAN", 0.0)

    local voc_par, is_new_voc_par = get_or_create_track("VOCAL PARALLEL", false)
    set_color(voc_par, 255, 92, 138)
    reaper.SetMediaTrackInfo_Value(voc_par, "D_VOL", 0.22) -- ~-13dB: body ấm nhẹ, hỗ trợ tầng trung-thấp
    reaper.SetMediaTrackInfo_Value(voc_par, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_par, "I_RECINPUT", -1)
 
    local voc_rev, is_new_voc_rev = get_or_create_track("VOCAL REVERB", false)
    set_color(voc_rev, 56, 189, 248)
    reaper.SetMediaTrackInfo_Value(voc_rev, "D_VOL", 0.50) -- ~-6dB: reverb rõ nhưng không dội gần
    reaper.SetMediaTrackInfo_Value(voc_rev, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_rev, "I_RECINPUT", -1)
 
    local voc_del, is_new_voc_del = get_or_create_track("VOCAL DELAY", false)
    set_color(voc_del, 234, 179, 8)
    reaper.SetMediaTrackInfo_Value(voc_del, "D_VOL", 0.40) -- ~-8dB: echo sân khấu tự nhiên
    reaper.SetMediaTrackInfo_Value(voc_del, "D_PAN", 0.0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECARM", 0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECMON", 0)
    reaper.SetMediaTrackInfo_Value(voc_del, "I_RECINPUT", -1)

    local mus, is_new_mus = get_or_create_track("NHẠC", true)
    set_color(mus, 40, 120, 220)
    reaper.SetMediaTrackInfo_Value(mus, "D_VOL", 0.56) -- ~-5.0dB (mức mặc định, AI bridge sẽ đồng bộ với slider UI)
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

    -- FX0: Noise Gate (Tắt mặc định để tránh chặt cụt các đoạn chuyển nốt, luyến láy nhẹ nhàng)
    local vgate = add_fx(voc, "ReaGate")
    if vgate >= 0 then
        reaper.TrackFX_SetEnabled(voc, vgate, false)
    end

    -- FX1: Auto-Tune
    -- FX1: Auto-Tune (Thiết lập cố định dải điểm ngọt để giữ nốt cực kỳ ổn định, không bị cụt nốt)
    local at = add_fx(voc, "MAutoPitch")
    if at >= 0 then
        set_p(voc, at, "Depth", 0.85)       -- 85% Depth (cho phép vibrato nhẹ)
        set_p(voc, at, "Speed", 0.50)       -- ~50ms Speed (mượt mà, không giật)
        set_p(voc, at, "Detune", 0.50)      -- 0 cents
    else
        at = add_fx(voc, "Graillon")
        if at >= 0 then
            -- KARAOKE TUNING: mượt, nịnh giọng, không méo
            set_p(voc, at, "Corr. Amount", 0.60)   -- 60% correction (tự nhiên hơn, cho vibrato 40%)
            set_p(voc, at, "Smooth", 0.25)          -- 25% smooth (chuyển nốt MƯỢT MÀ, không giật)
            set_p(voc, at, "Inertia", 0.35)         -- 35% inertia (giữ nốt ổn định, không chạy)
            set_p(voc, at, "Wet Mix", 0.70)          -- 70% wet (giữ 30% dry để BẢO TỒN TREBLE)
            set_p(voc, at, "Dry Mix", 0.30)          -- 30% dry (treble harmonics gốc)
            set_p(voc, at, "Output Gain", 0.80)      -- -2dB output (bù volume)
        else
            at = add_fx(voc, "Fat1")
            if at >= 0 then
                set_p(voc, at, "Correction", 0.50)
                set_p(voc, at, "Speed", 0.35)
            else
                at = add_fx(voc, "ReaTune")
                if at >= 0 then
                    set_p(voc, at, "Correction rate (ms)", 0.040)
                end
            end
        end
    end

    -- FX2: ReaEQ (Tham chiếu Laiganhonanh.mp3: Bass 21%, Low-Mid 17.5%, Air 9.7%)
    local veq = add_fx(voc, "ReaEQ")
    -- Band 5: High Pass (Hạ xuống 80Hz giữ bass body vocal — tham chiếu Sub 10.8%)
    set_p(voc, veq, "Freq-High Pass 5", 0.07)   -- ~80Hz (hạ từ 120Hz → giữ ấm hơn)
    -- Band 1: Low Shelf (Boost nhẹ +2.0dB để bồi lại LMid/Bass bị thiếu, tạo độ ấm)
    set_p(voc, veq, "Freq-Low Shelf", 0.21)     -- ~200Hz
    set_p(voc, veq, "Gain-Low Shelf", 0.541)    -- +2.0dB (Bồi độ cốt)
    -- Band 2: Bell (Mid Cut 850Hz, nới lỏng về -4.0dB để hát nhẹ nhàng, thoát giọng)
    set_p(voc, veq, "Freq-Band 2", 0.42)        -- ~850Hz
    set_p(voc, veq, "Gain-Band 2", 0.416)       -- -4.0dB (Dễ hát hơn)
    -- Band 3: Bell (BOOST nhẹ dải Presence 3.2kHz → vocal "phủ" lên beat, nghe rõ nét)
    set_p(voc, veq, "Freq-Band 3", 0.62)        -- ~3.2kHz
    set_p(voc, veq, "Gain-Band 3", 0.531)       -- +1.5dB (tôn vinh vocal, nổi trên nhạc)
    -- Band 4: High Shelf (Air mạnh — tham chiếu Air 9.7% rất rõ ràng)
    set_p(voc, veq, "Freq-High Shelf 4", 0.82)  -- ~10.0kHz (hạ freq để phủ rộng hơn)
    set_p(voc, veq, "Gain-High Shelf 4", 0.563) -- +3.0dB Air (tăng gấp đôi từ +1.5dB)
    set_p(voc, veq, "BW-High Shelf 4", 0.25)    -- Rộng hơn cho Air phủ mềm mại

    -- FX3: ReaComp (Vocal Compressor mềm xốp, giảm nén gắt)
    local vcomp = add_fx(voc, "ReaComp")
    set_p(voc, vcomp, "Thresh", 0.030)         -- -24.4dB (norm 0.030)
    set_p(voc, vcomp, "Ratio", 0.025)          -- ~3.5:1 (nén nhẹ nhàng, dẻo dai)
    set_p(voc, vcomp, "Attack", 0.12)          -- 12ms (cho transient đi qua mềm mại, không bị cứng đanh)
    set_p(voc, vcomp, "Release", 0.15)         -- 150ms
    set_p(voc, vcomp, "Knee", 0.50)            -- Soft-knee (đường cong nén cực mịn)
    set_p(voc, vcomp, "Auto make", 1.0)

    -- FX3.5: ReaXcomp (Dynamic EQ Tamer - ĐỘNG LỰC HỌC THÔNG MINH)
    local xcomp = add_fx(voc, "ReaXcomp")
    set_p(voc, xcomp, "1-Band top frequency", 0.26) -- Dưới 250Hz: Bỏ qua không nén
    set_p(voc, xcomp, "2-Band top frequency", 0.65) -- 250Hz - 3kHz: Nén dải Mid/UMid
    set_p(voc, xcomp, "1-Threshold", 1.0) -- Band 1 không nén (Threshold max)
    set_p(voc, xcomp, "2-Threshold", 0.018) -- Band 2 nén tại -27dB (kích hoạt đúng lúc hát to)
    set_p(voc, xcomp, "2-Ratio", 0.38)    -- Ratio 4:1 nén gắt dải chói
    set_p(voc, xcomp, "2-Attack", 0.1)    -- Attack 10ms
    set_p(voc, xcomp, "2-Release", 0.25)  -- Release vừa phải
    set_p(voc, xcomp, "3-Active", 0.0) -- Tắt Band 3
    set_p(voc, xcomp, "4-Active", 0.0) -- Tắt Band 4

    -- FX4: JS Saturation (Hài âm tạo độ ấm xốp như mic tube vintage)
    local vsat = add_fx(voc, "Saturation")
    if vsat >= 0 then
        set_p(voc, vsat, "Amount (%)", 0.20)   -- 20% Saturation: hài âm đầy đặn, giọng xốp như mic ống
    end

    -- FX5: Chorus (Shimmer nhẹ, KHÔNG tạo bản sao giọng)
    local chorus = add_fx(voc, "Chorus")
    if chorus >= 0 then
        set_p(voc, chorus, "Rate", 0.08)        -- Chậm: modulation mượt
        set_p(voc, chorus, "Depth", 0.06)       -- Rất nông: shimmer không doubling
        set_p(voc, chorus, "Mix", 0.06)          -- 6%: chỉ thêm chút ánh sáng
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
    set_p(voc_par, vpeq, "Gain-Band 2", 0.54)            -- +2dB Presence boost (thêm lực cho vocal)
    set_p(voc_par, vpeq, "Freq-Band 3", 0.75)            -- ~10kHz
    set_p(voc_par, vpeq, "Gain-Band 3", 0.52)            -- +1dB Air (sáng lên)

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 3: 🌊 VOCAL REVERB (Aux Reverb)
    -- ══════════════════════════════════════════════════════════════
    -- Filter Abbey Road ấm áp (Hạ HPF 80Hz cho bass reverb ấm, boost 350Hz cho body)
    local vreveq = add_fx(voc_rev, "ReaEQ")
    set_p(voc_rev, vreveq, "Freq-Low Shelf", 0.10)       -- ~80Hz (hạ từ 130Hz: giữ ấm hơn)
    set_p(voc_rev, vreveq, "Gain-Low Shelf", 0.0)        -- -inf dB (cắt trầm)
    set_p(voc_rev, vreveq, "Freq-High Pass 5", 0.10)     -- ~80Hz (HPF)
    
    set_p(voc_rev, vreveq, "Freq-Band 2", 0.30)          -- ~350Hz
    set_p(voc_rev, vreveq, "Gain-Band 2", 0.563)         -- +3dB (độ đầy ấm của reverb, hỗ trợ tầng trung-thấp)
    
    set_p(voc_rev, vreveq, "Freq-Band 3", 0.55)          -- ~2kHz
    set_p(voc_rev, vreveq, "Gain-Band 3", 0.52)          -- +1dB (reverb presence bổ trợ vocal)
    
    -- Air shelf: +3dB (đủ sáng nhưng không chói)
    set_p(voc_rev, vreveq, "Freq-High Shelf 4", 0.85)    -- ~10kHz
    set_p(voc_rev, vreveq, "Gain-High Shelf 4", 0.56)    -- +3dB (bớt chói so với +5dB)

    -- Chorus trên Reverb: tạo độ xốp bao bọc, reverb "phủ" xung quanh vocal
    local rev_chorus = add_fx(voc_rev, "Chorus")
    if rev_chorus >= 0 then
        set_p(voc_rev, rev_chorus, "Rate", 0.10)
        set_p(voc_rev, rev_chorus, "Depth", 0.22)       -- Sâu hơn: reverb 3D bao quanh
        set_p(voc_rev, rev_chorus, "Mix", 0.40)         -- 40%: reverb xốp phủ lên beat
    end

    -- Reverb 100% Wet — Sân khấu PRO: lớn hơn reference vì headphone không có âm phòng tự nhiên
    local vrev = add_fx(voc_rev, "ReaVerbate")
    set_p(voc_rev, vrev, "Wet", 1.0)
    set_p(voc_rev, vrev, "Dry", 0.0)
    set_p(voc_rev, vrev, "Room Size", 0.58)             -- Decay ≈ 1.3s (âm hưởng lưu lại lâu hơn)
    set_p(voc_rev, vrev, "Dampening", 0.28)             -- Treble bớt chói, tầng ấm giữ lâu hơn
    set_p(voc_rev, vrev, "Delay", 0.30)                 -- Pre-delay 30ms (tách rõ "vang" khỏi "giọng gốc")
    set_p(voc_rev, vrev, "Width", 1.0)
    set_p(voc_rev, vrev, "Stereo", 1.0)

    -- Sân khấu PRO: TẮT ducker — reverb HÒA CÙNG vocal, không bị nén cắt
    -- (Sân khấu chuyên nghiệp không dùng ducker trên reverb monitor)
    local vrev_comp = add_fx(voc_rev, "ReaComp")
    reaper.TrackFX_SetEnabled(voc_rev, vrev_comp, false) -- TẮT: reverb luôn chảy tự do

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

    -- Delay (Echo sân khấu: 3-4 echo rõ, giảm dần tự nhiên)
    local vdel = add_fx(voc_del, "ReaDelay")
    set_p(voc_del, vdel, "Dry", 0.0)
    set_p(voc_del, vdel, "1: Volume", 1.0)
    set_p(voc_del, vdel, "1: Feedback", 0.25)            -- 3-4 echo nghe được (sân khấu tự nhiên)
    set_p(voc_del, vdel, "1: Length (time)", 0.0127)     -- Đặt delay = 63ms (0.0127 trên thang 5s, khớp echo interval phân tích)
    set_p(voc_del, vdel, "1: Length (musical)", 0.0)     -- Tắt đồng bộ hóa nốt nhạc của VST để dùng mili-giây từ Python
    set_p(voc_del, vdel, "1: Lowpass", 0.60)             -- Lọc bớt dải cao của delay để tiếng echo ấm hơn

    -- Sân khấu PRO: TẮT ducker delay — echo chảy tự do
    local vdel_comp = add_fx(voc_del, "ReaComp")
    reaper.TrackFX_SetEnabled(voc_del, vdel_comp, false) -- TẮT: echo luôn hòa cùng vocal

    -- ══════════════════════════════════════════════════════════════
    -- CẤU HÌNH VST TRACK 5: 🎵 NHẠC NỀN
    -- ══════════════════════════════════════════════════════════════
    local rpitch = add_fx(mus, "ReaPitch")
    set_p(mus, rpitch, "Shift (semitones)", 0.5)

    local meq = add_fx(mus, "ReaEQ")
    set_p(mus, meq, "Type-Band 1", 3)          -- Chuyển Band 1 thành High Shelf (để dọn sạch dải cao)
    set_p(mus, meq, "Freq-Band 1", 0.85)       -- ~10.0kHz
    set_p(mus, meq, "Gain-Band 1", 0.46)       -- -2.0dB cut (tạo không gian siêu thoáng cho Reverb xốp bay bổng)
    set_p(mus, meq, "Bandwidth-Band 1", 0.5)
    
    set_p(mus, meq, "Freq-Band 2", 0.40)       -- ~2.5kHz (Dải trung dọn chỗ cho giọng hát chính)
    set_p(mus, meq, "Gain-Band 2", 0.39)       -- ★ -5.5dB cut (sâu hơn từ -4.5dB — tham chiếu: vocal 20.1% center)
    set_p(mus, meq, "Bandwidth-Band 2", 0.50)  -- ★ Rộng hơn: dọn pocket rộng hơn cho vocal center
    
    set_p(mus, meq, "Freq-Band 3", 0.52)       -- ~5.0kHz (Dải sáng dọn chỗ cho độ bóng bẩy vocal)
    set_p(mus, meq, "Gain-Band 3", 0.43)       -- -3.5dB cut
    set_p(mus, meq, "Bandwidth-Band 3", 0.4)
    
    set_p(mus, meq, "Freq-Band 4", 0.08)       -- ~120Hz (Low Shelf giữ âm trầm ấm áp cho beat)
    set_p(mus, meq, "Gain-Band 4", 0.56)       -- +3.0dB (Bass warmth)
    set_p(mus, meq, "Bandwidth-Band 4", 0.3)

    local mcomp = add_fx(mus, "ReaComp")
    set_p(mus, mcomp, "Thresh", 0.70)
    set_p(mus, mcomp, "Ratio", 0.08)
    set_p(mus, mcomp, "Attack", 0.25)
    set_p(mus, mcomp, "Release", 0.40)

    -- "Nhạc Tách Mở" (Mid/Side Widening)
    local mwiden = add_fx(mus, "JS: Stereo Enhancer")
    if mwiden >= 0 then
        set_p(mus, mwiden, "Width", 2.0)    -- Kéo dài width (200%) — tham chiếu Low-Mid Side ratio 0.80 (rất rộng)
        set_p(mus, mwiden, "Center", 0.40)  -- ★ GIẢM 50%→40%: Khoét center sâu hơn — vocal phủ lên giữa rõ ràng hơn
    end


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
