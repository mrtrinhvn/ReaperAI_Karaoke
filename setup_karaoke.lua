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

    -- Hàm hỗ trợ tìm track theo tên
    local function get_or_create_track(name, is_stereo_input)
        for i = 0, reaper.CountTracks(0) - 1 do
            local t = reaper.GetTrack(0, i)
            local _, tname = reaper.GetSetMediaTrackInfo_String(t, "P_NAME", "", false)
            if tname:lower():find(name:lower(), 1, true) then
                return t, false -- false means track existed
            end
        end
        -- Nếu không thấy, tạo mới ở cuối
        reaper.InsertTrackAtIndex(reaper.CountTracks(0), true)
        local t = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
        reaper.GetSetMediaTrackInfo_String(t, "P_NAME", name, true)
        
        -- Cài đặt mặc định khi mới tạo
        reaper.SetMediaTrackInfo_Value(t, "I_RECARM", 1)
        reaper.SetMediaTrackInfo_Value(t, "I_RECMON", 1)
        if is_stereo_input then
            reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", 1024 + 2*32) -- Stereo 3/4
        else
            reaper.SetMediaTrackInfo_Value(t, "I_RECINPUT", 0) -- Input 1 Mono
        end
        return t, true
    end

    -- ══════════════════════════════════════════════════════════════
    -- TRACK 1: 🎙️ VOCAL — Giọng hát chính
    -- ══════════════════════════════════════════════════════════════
    local voc, is_new_voc = get_or_create_track("VOCAL", false)
    set_color(voc, 230, 55, 55)
    reaper.SetMediaTrackInfo_Value(voc, "D_VOL", 1.0)
    reaper.SetMediaTrackInfo_Value(voc, "D_PAN", 0.0)

    -- ── FX1: ReaEQ (Vocal shaping) ──
    local veq = add_fx(voc, "ReaEQ")
    -- Band 1: High-pass 85Hz — cắt rung, tiếng thở, ồn
    set_p(voc, veq, "Type-Band 1", 0.14)     -- HPF
    set_p(voc, veq, "Freq-Band 1", 0.085)    -- ~85Hz
    set_p(voc, veq, "Gain-Band 1", 0.5)
    -- Band 2: Notch cut 300Hz (-3dB) — bớt "ồn ồn" (boxy)
    set_p(voc, veq, "Freq-Band 2", 0.18)     -- ~300Hz
    set_p(voc, veq, "Gain-Band 2", 0.375)    -- -3dB
    set_p(voc, veq, "Bandwidth-Band 2", 0.4)
    -- Band 3: Boost 2.5kHz (+3dB) — giọng rõ lời, cắt xuyên nhạc
    set_p(voc, veq, "Freq-Band 3", 0.40)     -- ~2.5kHz
    set_p(voc, veq, "Gain-Band 3", 0.625)    -- +3dB
    set_p(voc, veq, "Bandwidth-Band 3", 0.35)
    -- Band 4: Air shelf 12kHz (+2.5dB) — sáng, thoáng, "bông xốp"
    set_p(voc, veq, "Type-Band 4", 0.86)     -- High-shelf
    set_p(voc, veq, "Freq-Band 4", 0.80)     -- ~12kHz
    set_p(voc, veq, "Gain-Band 4", 0.60)     -- +2.5dB

    -- ── FX2: ReaComp (Nén giọng ổn định) ──
    local vcomp = add_fx(voc, "ReaComp")
    set_p(voc, vcomp, "Thresh", 0.50)         -- ~-20dB threshold
    set_p(voc, vcomp, "Ratio", 0.27)          -- ~3.5:1
    set_p(voc, vcomp, "Attack", 0.12)         -- ~8ms
    set_p(voc, vcomp, "Release", 0.30)        -- ~80ms
    set_p(voc, vcomp, "Knee", 0.35)           -- Soft knee
    set_p(voc, vcomp, "Auto make", 1.0)       -- Bù gain tự động

    -- ── FX3: ReaDelay (Pure Slapback — CHỈ 1 LẦN NHẠI, không lặp) ──
    -- Mẹo: Feedback = 0 → chỉ nghe 1 tiếng nhại duy nhất, rất sạch.
    -- AI sẽ tự sync Length theo BPM để tiếng nhại rơi đúng nhịp.
    local vdel = add_fx(voc, "ReaDelay")
    set_p(voc, vdel, "Length", 0.0375)         -- ~375ms (120BPM dotted 8th)
    set_p(voc, vdel, "Volume", 0.15)           -- Nhỏ hơn tiếng gốc khá nhiều (-16dB)
    set_p(voc, vdel, "Feedback", 0.0)          -- ★ ZERO FEEDBACK = Chỉ 1 lần nhại
    set_p(voc, vdel, "Lowpass", 0.50)          -- Cắt treble → tiếng nhại ấm, tự nhiên
    set_p(voc, vdel, "Dry", 1.0)               -- Không giảm tiếng gốc

    -- ── FX4: Chorus (JS plugin — tạo hiệu ứng "bông xốp", dày giọng) ──
    local chorus = add_fx(voc, "Chorus")
    if chorus >= 0 then
        set_p(voc, chorus, "Rate", 0.25)       -- Slow modulation
        set_p(voc, chorus, "Depth", 0.30)      -- Subtle
        set_p(voc, chorus, "Mix", 0.15)        -- 15% wet
    end

    -- ── FX5: ReaVerbate (Reverb — linh hồn Karaoke) ──
    -- Room Size nhỏ hơn → decay nhanh hơn → không bị "đuôi" kéo dài
    -- Dampening cao hơn → hấp thụ treble nhanh → ấm, không chói
    -- AI sẽ tự chỉnh Room Size theo tempo (nhanh→phòng nhỏ, chậm→phòng lớn)
    local vverb = add_fx(voc, "ReaVerbate")
    set_p(voc, vverb, "Room Size", 0.45)       -- Phòng vừa (AI sẽ sync tempo)
    set_p(voc, vverb, "Dampening", 0.55)       -- Hấp thụ treble nhiều → ấm, gọn
    set_p(voc, vverb, "Stereo", 0.80)          -- Stereo rộng → bông xốp
    set_p(voc, vverb, "Wet", 0.15)             -- 15% reverb (-16dB)
    set_p(voc, vverb, "Dry", 1.0)              -- Không bao giờ giảm tiếng gốc (0dB)
    set_p(voc, vverb, "Width", 0.75)           -- Stereo width
    set_p(voc, vverb, "Low Cut", 0.18)         -- Cắt bass mạnh hơn (tránh bùng)
    set_p(voc, vverb, "High Cut", 0.60)        -- Cắt treble → reverb ấm

    -- ══════════════════════════════════════════════════════════════
    -- TRACK 2: 🎵 NHẠC NỀN — EQ "khoét lỗ" nhường chỗ giọng hát
    -- ══════════════════════════════════════════════════════════════
    local mus, is_new_mus = get_or_create_track("NHẠC", true)
    set_color(mus, 40, 120, 220)
    reaper.SetMediaTrackInfo_Value(mus, "D_VOL", 0.65)    -- -3.7dB — nhường vocal
    reaper.SetMediaTrackInfo_Value(mus, "D_PAN", 0.0)

    -- ── FX1: ReaEQ (Khoét lỗ phổ tần cho giọng hát) ──
    local meq = add_fx(mus, "ReaEQ")
    -- Band 1: Cut 800Hz (-2dB) — nhường vùng Body giọng hát
    set_p(mus, meq, "Freq-Band 1", 0.30)      -- ~800Hz
    set_p(mus, meq, "Gain-Band 1", 0.42)      -- -2dB
    set_p(mus, meq, "Bandwidth-Band 1", 0.5)
    -- Band 2: Cut 2.5kHz (-4dB) — TRỌNG YẾU: nhường vùng Presence giọng hát
    set_p(mus, meq, "Freq-Band 2", 0.40)      -- ~2.5kHz
    set_p(mus, meq, "Gain-Band 2", 0.33)      -- -4dB (cắt mạnh)
    set_p(mus, meq, "Bandwidth-Band 2", 0.45) -- Dải rộng vừa
    -- Band 3: Cut 5kHz (-2.5dB) — nhường vùng sáng
    set_p(mus, meq, "Freq-Band 3", 0.52)      -- ~5kHz
    set_p(mus, meq, "Gain-Band 3", 0.37)      -- -2.5dB
    set_p(mus, meq, "Bandwidth-Band 3", 0.4)
    -- Band 4: Boost bass nhẹ 80Hz (+1.5dB) — giữ nền nhạc đầy đặn
    set_p(mus, meq, "Freq-Band 4", 0.08)      -- ~80Hz
    set_p(mus, meq, "Gain-Band 4", 0.56)      -- +1.5dB
    set_p(mus, meq, "Bandwidth-Band 4", 0.3)

    -- ── FX2: ReaComp (Nén nhạc nền nhẹ — giữ ổn định) ──
    local mcomp = add_fx(mus, "ReaComp")
    set_p(mus, mcomp, "Thresh", 0.55)
    set_p(mus, mcomp, "Ratio", 0.18)           -- ~2.5:1 (nhẹ)
    set_p(mus, mcomp, "Attack", 0.25)
    set_p(mus, mcomp, "Release", 0.40)

    -- ── FX3: JS Stereo Width (Làm rộng âm trường nhường không gian cho Vocal) ──
    local mwidth = add_fx(mus, "Stereo Width")
    if mwidth < 0 then
        mwidth = add_fx(mus, "utility/stereo_width")
    end
    if mwidth >= 0 then
        set_p(mus, mwidth, "Width", 0.65)      -- Mặc định rộng vừa phải
    end

    -- ══════════════════════════════════════════════════════════════
    -- MASTER BUS: EQ Smile → Multiband Comp → Stereo Width → Limiter
    -- ══════════════════════════════════════════════════════════════
    local master = reaper.GetMasterTrack(0)

    -- ★ XÓA TẤT CẢ FX CŨ TRÊN MASTER (tránh chồng khi chạy setup lại)
    for i = reaper.TrackFX_GetCount(master) - 1, 0, -1 do
        reaper.TrackFX_Delete(master, i)
    end

    -- ── Master FX1: ReaEQ (Smile curve — ấm + sáng) ──
    local meq2 = add_fx(master, "ReaEQ")
    -- Band 1: Low shelf boost 100Hz (+1.5dB) — nền ấm
    set_p(master, meq2, "Type-Band 1", 0.0)    -- Low-shelf
    set_p(master, meq2, "Freq-Band 1", 0.10)   -- ~100Hz
    set_p(master, meq2, "Gain-Band 1", 0.56)   -- +1.5dB
    -- Band 2: Rất nhẹ cut 500Hz (-1dB) — bỏ đục
    set_p(master, meq2, "Freq-Band 2", 0.25)   -- ~500Hz
    set_p(master, meq2, "Gain-Band 2", 0.48)   -- -1dB
    set_p(master, meq2, "Bandwidth-Band 2", 0.5)
    -- Band 3: Gentle boost 3kHz (+1dB) — rõ ràng
    set_p(master, meq2, "Freq-Band 3", 0.45)
    set_p(master, meq2, "Gain-Band 3", 0.54)   -- +1dB
    set_p(master, meq2, "Bandwidth-Band 3", 0.5)
    -- Band 4: High shelf 10kHz (+4dB) — "bông xốp", Air (TĂNG ĐỘ XỐP)
    set_p(master, meq2, "Type-Band 4", 0.86)   -- High-shelf
    set_p(master, meq2, "Freq-Band 4", 0.75)   -- ~10kHz
    set_p(master, meq2, "Gain-Band 4", 0.60)   -- +4.8dB (Xốp lồng lộng)

    -- ── Master FX2: ReaXcomp (Multiband Compressor — keo dính mix) ──
    local mxc = add_fx(master, "ReaXcomp")
    if mxc >= 0 then
        -- Nới lỏng Threshold để không dìm nhạc khi hát to
        set_p(master, mxc, "Thresh", 0.70)      
        set_p(master, mxc, "Ratio", 0.15)       -- Ratio rất nhẹ 1.5:1
        set_p(master, mxc, "Attack", 0.20)
        set_p(master, mxc, "Release", 0.35)
    end

    -- ── Master FX3: JS Stereo Width (Mở rộng âm trường) ──
    local swidth = add_fx(master, "Stereo Width")
    if swidth < 0 then
        swidth = add_fx(master, "utility/stereo_width")
    end
    if swidth >= 0 then
        set_p(master, swidth, "Width", 0.70)    -- Mở rộng vừa phải
    end

    -- ── Master FX4: ReaLimit (Limiter — chống clip, làm to nhạc) ──
    local mlim = add_fx(master, "ReaLimit")
    if mlim >= 0 then
        -- Nâng Threshold lên cao để chỉ hoạt động như màng bảo vệ, KHÔNG bóp nghẹt nhạc
        set_p(master, mlim, "Thresh", 0.85)     
        set_p(master, mlim, "Ceiling", 0.95)    -- -0.3dB ceiling an toàn
    end

    -- ══════════════════════════════════════════════════════════════
    -- PROJECT SETTINGS + GHI BPM CHO PYTHON AI
    -- ══════════════════════════════════════════════════════════════
    reaper.SetCurrentBPM(0, 120, true)
    reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)

    -- Ghi BPM ra file để Python AI đọc và sync delay/reverb
    local bpm_file = io.open("/tmp/ai_karaoke_bpm.txt", "w")
    if bpm_file then
        bpm_file:write(tostring(reaper.Master_GetTempo()))
        bpm_file:close()
    end

    -- Mở Mixer + FX
    reaper.Main_OnCommand(40078, 0)  -- Show Mixer
    reaper.SetTrackSelected(voc, true)
    reaper.Main_OnCommand(40291, 0)  -- Show FX for selected track

    -- ══════════════════════════════════════════════════════════════
    -- DEBUG: In tham số
    -- ══════════════════════════════════════════════════════════════
    reaper.ShowConsoleMsg("\n═══ AI KARAOKE PRO v3 — Parameter Dump ═══\n\n")
    reaper.ShowConsoleMsg("── VOCAL ──\n")
    dump_params(voc, veq)
    dump_params(voc, vcomp)
    dump_params(voc, vdel)
    if chorus >= 0 then dump_params(voc, chorus) end
    dump_params(voc, vverb)
    reaper.ShowConsoleMsg("\n── NHẠC NỀN ──\n")
    dump_params(mus, meq)
    reaper.ShowConsoleMsg("\n── MASTER ──\n")
    dump_params(master, meq2)
    if mxc >= 0 then dump_params(master, mxc) end
    if mlim >= 0 then dump_params(master, mlim) end

    reaper.PreventUIRefresh(-1)
    reaper.UpdateArrange()
    reaper.TrackList_AdjustWindows(false)
    reaper.Undo_EndBlock("AI Karaoke Pro v4", -1)
    reaper.Main_SaveProject(0, false)

    reaper.ShowMessageBox([[🎤 AI KARAOKE PRO v4 — Setup hoàn tất!

═══ DELAY (Sửa tiếng nhại) ═══
  ★ Feedback = 0 → Chỉ 1 lần nhại, KHÔNG lặp
  ★ AI sẽ tự sync delay theo BPM
  ★ Beat nhanh → delay ngắn, beat chậm → delay dài

═══ REVERB (Sync tempo) ═══
  ★ Room Size theo tempo (nhanh→gọn, chậm→rộng)
  ★ Dampening cao → đuôi reverb ấm, không chói
  ★ Vang nhiều mà vẫn quện vào beat!

═══ AI REAL-TIME ═══
  ★ Phát hiện echo buildup tự động
  ★ Điều chỉnh tất cả khi bạn đang hát
  ★ Bạn không cần biết chỉnh gì — AI lo!

Chạy: bash start_karaoke.sh]], "AI Karaoke Pro v4", 0)
end

setup()
