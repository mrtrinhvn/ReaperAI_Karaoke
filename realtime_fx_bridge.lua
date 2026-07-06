-- ============================================================================
-- 🤖 realtime_fx_bridge.lua v3 — Tempo-Synced AI FX Bridge
-- ============================================================================
-- Xử lý Vocal FX + Music Ducking + Tempo Sync Delay/Reverb + Echo Detection.
-- Đọc /tmp/ai_karaoke_commands.json + Ghi BPM ra /tmp/ai_karaoke_bpm.txt
-- ============================================================================

local CMD_FILE = "/tmp/ai_karaoke_commands.json"
local BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
local KEY_FILE = "/tmp/ai_karaoke_key.json"
local POLL_INTERVAL = 0.2
local last_mtime = 0
local bpm_tick = 0

-- ── Helpers ──

function find_track(name)
    for i = 0, reaper.CountTracks(0) - 1 do
        local tr = reaper.GetTrack(0, i)
        local _, n = reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "", false)
        if n and n:find(name) then return tr end
    end
    return nil
end

function find_fx(track, name)
    for i = 0, reaper.TrackFX_GetCount(track) - 1 do
        local _, n = reaper.TrackFX_GetFXName(track, i)
        if n and n:lower():find(name:lower(), 1, true) then return i end
    end
    return -1
end

function find_p(track, fx, name)
    if fx < 0 then return -1 end
    for i = 0, reaper.TrackFX_GetNumParams(track, fx) - 1 do
        local _, n = reaper.TrackFX_GetParamName(track, fx, i)
        if n and n:lower():find(name:lower(), 1, true) then return i end
    end
    return -1
end

-- Smooth transition (lerp) để tránh tiếng click khi chỉnh nhanh
function smooth(track, fx, pidx, target, speed)
    if pidx < 0 then return end
    speed = speed or 0.25
    local cur = reaper.TrackFX_GetParamNormalized(track, fx, pidx)
    reaper.TrackFX_SetParamNormalized(track, fx, pidx, cur + (target - cur) * speed)
end

-- Bật/tắt các nốt nhạc cụ thể cho thang âm ngũ cung (Vietnamese Pentatonic Scale)
function set_vst_notes(track, fx_idx, root_note, scale_type, detected_scale)
    local intervals = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11} -- mặc định mở hết
    if scale_type == "Pentatonic" then
        if detected_scale == "Minor" then
            intervals = {0, 3, 5, 7, 10} -- Ngũ cung Thứ (Nam / Oán - Vọng cổ)
        else
            intervals = {0, 2, 4, 7, 9} -- Ngũ cung Trưởng (Dân ca Bắc Bộ / Lý cây bông)
        end
    end

    local is_active = {}
    for i = 0, 11 do is_active[i] = false end
    for _, val in ipairs(intervals) do
        local note = (root_note + val) % 12
        is_active[note] = true
    end

    local note_names = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}
    local num_params = reaper.TrackFX_GetNumParams(track, fx_idx)
    for p = 0, num_params - 1 do
        local retval, buf = reaper.TrackFX_GetParamName(track, fx_idx, p)
        if retval then
            local param_name = buf:match("^%s*(.-)%s*$")
            for note_idx, name in ipairs(note_names) do
                if param_name == name or param_name == "Snap " .. name or param_name == "Note " .. name then
                    local state = is_active[note_idx - 1] and 1.0 or 0.0
                    reaper.TrackFX_SetParamNormalized(track, fx_idx, p, state)
                end
            end
        end
    end
end

-- Điều chỉnh động học Auto-Tune (Flex-Tune / Humanize tự thiết kế)
function adjust_autotune_dynamics(track, fx_idx, depth)
    local num_params = reaper.TrackFX_GetNumParams(track, fx_idx)
    for p = 0, num_params - 1 do
        local retval, buf = reaper.TrackFX_GetParamName(track, fx_idx, p)
        if retval then
            local name = buf:lower()
            -- Nhận diện các núm vặn mức độ can thiệp (Depth / Correction / Amount)
            if name:find("correction") or name:find("depth") or name:find("amount") then
                smooth(track, fx_idx, p, depth, 0.25)
            -- Nhận diện các núm độ trễ / quán tính / độ mượt (Smooth / Inertia)
            elseif name:find("smooth") or name:find("inertia") then
                local smooth_val = 1.0 - depth
                smooth(track, fx_idx, p, smooth_val, 0.25)
            -- Nhận diện núm tốc độ chỉnh nốt (Speed / Pull)
            elseif name:find("speed") or name:find("pull") then
                smooth(track, fx_idx, p, depth, 0.25)
            end
        end
    end
end

-- ── JSON reader (simple flat key-value, handles nested "vocal"/"music" keys) ──
function read_json(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local content = f:read("*all")
    f:close()
    if not content or #content < 2 then return nil end
    local data = {}
    for key, val in content:gmatch('"([^"]+)":%s*([^,}]+)') do
        val = val:match("^%s*(.-)%s*$")
        if val == "true" then data[key] = true
        elseif val == "false" then data[key] = false
        elseif val:match('^"') then data[key] = val:match('^"(.-)"$')
        else data[key] = tonumber(val)
        end
    end
    return data
end

-- Convert dB to normalized EQ gain (0.5 = 0dB, range ~ -24 to +24)
function db_to_norm(db)
    return 0.5 + (db / 48.0)
end

-- ── Apply adjustments ──
function apply(data)
    if not data then return end
    if data.reset then return end

    local vocal = find_track("VOCAL")
    local music = find_track("NHẠC")

    -- ═══ VOCAL TRACK ═══
    if vocal then
        local eq = find_fx(vocal, "ReaEQ")
        local comp = find_fx(vocal, "ReaComp")
        local verb = find_fx(vocal, "ReaVerbate")
        local del = find_fx(vocal, "ReaDelay")
        local chorus = find_fx(vocal, "Chorus")

        -- Vocal EQ Band 2 (Mud)
        if eq >= 0 and data.eq_band_2_gain_db then
            local p = find_p(vocal, eq, "Gain-Band 2")
            if p >= 0 then smooth(vocal, eq, p, db_to_norm(data.eq_band_2_gain_db), 0.2) end
        end
        -- Vocal EQ Band 3 (Presence)
        if eq >= 0 and data.eq_band_3_gain_db then
            local p = find_p(vocal, eq, "Gain-Band 3")
            if p >= 0 then smooth(vocal, eq, p, db_to_norm(data.eq_band_3_gain_db), 0.2) end
        end
        -- Vocal EQ Band 4 (Air)
        if eq >= 0 and data.eq_band_4_gain_db then
            local p = find_p(vocal, eq, "Gain-Band 4")
            if p >= 0 then smooth(vocal, eq, p, db_to_norm(data.eq_band_4_gain_db), 0.2) end
        end
        -- Compressor ratio
        if comp >= 0 and data.comp_ratio then
            local p = find_p(vocal, comp, "Ratio")
            if p >= 0 then smooth(vocal, comp, p, data.comp_ratio, 0.15) end
        end
        -- Compressor threshold (genre-driven)
        if comp >= 0 and data.comp_thresh then
            local p = find_p(vocal, comp, "Thresh")
            if p >= 0 then smooth(vocal, comp, p, data.comp_thresh, 0.15) end
        end
        -- ★ DELAY: Tempo-synced length
        if del >= 0 and data.delay_length then
            local p = find_p(vocal, del, "Length")
            if p >= 0 then smooth(vocal, del, p, data.delay_length, 0.3) end
        end
        -- ★ DELAY: Volume
        if del >= 0 and data.delay_volume then
            local p = find_p(vocal, del, "Volume")
            if p >= 0 then smooth(vocal, del, p, data.delay_volume, 0.2) end
        end
        -- ★ DELAY: Feedback (genre-driven)
        if del >= 0 and data.delay_feedback then
            local p = find_p(vocal, del, "Feedback")
            if p >= 0 then smooth(vocal, del, p, data.delay_feedback, 0.2) end
        end
        -- ★ REVERB: Room Size
        if verb >= 0 and data.reverb_room then
            local p = find_p(vocal, verb, "Room Size")
            if p >= 0 then smooth(vocal, verb, p, data.reverb_room, 0.15) end
        end
        -- REVERB: Wet
        if verb >= 0 and data.reverb_wet then
            local p = find_p(vocal, verb, "Wet")
            if p >= 0 then smooth(vocal, verb, p, data.reverb_wet, 0.15) end
        end
        -- REVERB: Dampening (genre-driven)
        if verb >= 0 and data.reverb_damp then
            local p = find_p(vocal, verb, "Dampening")
            if p >= 0 then smooth(vocal, verb, p, data.reverb_damp, 0.15) end
        end
        -- REVERB: Width (genre-driven)
        if verb >= 0 and data.reverb_width then
            local p = find_p(vocal, verb, "Width")
            if p >= 0 then smooth(vocal, verb, p, data.reverb_width, 0.15) end
        end
        -- REVERB: Pre-Delay (Delay parameter in ReaVerbate / Pre-delay in other VSTs)
        if verb >= 0 then
            local p = find_p(vocal, verb, "Delay")
            if p < 0 then p = find_p(vocal, verb, "Pre-delay") end
            if p < 0 then p = find_p(vocal, verb, "Predelay") end
            if p >= 0 then smooth(vocal, verb, p, 0.25, 0.15) end
        end
        -- CHORUS: Mix (genre-driven)
        if chorus >= 0 and data.chorus_mix then
            local p = find_p(vocal, chorus, "Mix")
            if p >= 0 then smooth(vocal, chorus, p, data.chorus_mix, 0.2) end
        end
        -- SATURATION: Warmth & Excitation (genre-driven)
        local sat = find_fx(vocal, "Saturation")
        if sat < 0 then sat = find_fx(vocal, "Exciter") end
        if sat >= 0 and data.saturation_amount then
            smooth(vocal, sat, 0, data.saturation_amount, 0.2)
        end
        
        -- ★ AUTO-TUNE (Graillon, MAutoPitch, Fat1)
        if data.root_note and data.scale then
            -- MAutoPitch or similar VSTs that use "Root" and "Scale"
            local at = find_fx(vocal, "MAutoPitch")
            if at < 0 then at = find_fx(vocal, "Graillon") end
            if at < 0 then at = find_fx(vocal, "Fat1") end
            if at < 0 then at = find_fx(vocal, "AutoTune") end
            
            if at >= 0 then
                -- Bật / Tắt bypass
                if data.autotune_enabled ~= nil then
                    reaper.TrackFX_SetEnabled(vocal, at, data.autotune_enabled)
                end
                
                if data.autotune_enabled ~= false then
                    -- 1. Áp dụng dynamic depth (Flex-Tune)
                    if data.autotune_depth then
                        adjust_autotune_dynamics(vocal, at, data.autotune_depth)
                    end
                    
                    -- 2. Áp dụng scale âm giai (Pentatonic hoặc Standard)
                    if data.scale_type == "Pentatonic" then
                        -- Thử set note rời (cho Graillon 2)
                        set_vst_notes(vocal, at, data.root_note, data.scale_type, data.scale)
                        
                        -- Set Root & Scale thông qua các núm vặn chính (cho MAutoPitch / các plugin khác)
                        local root_p = find_p(vocal, at, "Root")
                        if root_p < 0 then root_p = find_p(vocal, at, "Key") end
                        local scale_p = find_p(vocal, at, "Scale")
                        if scale_p < 0 then scale_p = find_p(vocal, at, "Mode") end
                        
                        if root_p >= 0 then
                            local root_norm = data.root_note / 11.0
                            reaper.TrackFX_SetParamNormalized(vocal, at, root_p, root_norm)
                        end
                        if scale_p >= 0 then
                            -- MAutoPitch có Pentatonic Major/Minor ở vị trí index ~3,4. 
                            -- Ta thử set giá trị tầm trung (ví dụ 0.28 cho Pentatonic Major, 0.36 cho Pentatonic Minor)
                            local scale_norm = (data.scale == "Major") and 0.28 or 0.36
                            reaper.TrackFX_SetParamNormalized(vocal, at, scale_p, scale_norm)
                        end
                    else
                        -- Reset về thang âm chuẩn
                        set_vst_notes(vocal, at, data.root_note, "Standard", data.scale)
                        
                        local root_p = find_p(vocal, at, "Root")
                        if root_p < 0 then root_p = find_p(vocal, at, "Key") end
                        local scale_p = find_p(vocal, at, "Scale")
                        if scale_p < 0 then scale_p = find_p(vocal, at, "Mode") end
                        
                        if root_p >= 0 then
                            local root_norm = data.root_note / 11.0
                            reaper.TrackFX_SetParamNormalized(vocal, at, root_p, root_norm)
                        end
                        if scale_p >= 0 then
                            local scale_norm = (data.scale == "Major") and 0.0 or 0.1 
                            reaper.TrackFX_SetParamNormalized(vocal, at, scale_p, scale_norm)
                        end
                    end
                end
            end
        end
    end

    -- ═══ REAPER TEMPO SYNC ═══
    if data.master_bpm then
        local current_bpm = reaper.Master_GetTempo()
        if math.abs(current_bpm - data.master_bpm) > 0.5 then
            reaper.SetCurrentBPM(0, data.master_bpm, true)
        end
    end

    -- ═══ MUSIC TRACK (Spectral Ducking) ═══
    if music then
        local meq = find_fx(music, "ReaEQ")

        -- Music EQ Band 1 (~800Hz)
        if meq >= 0 and data.music_eq_band_1_gain_db then
            local p = find_p(music, meq, "Gain-Band 1")
            if p >= 0 then smooth(music, meq, p, db_to_norm(data.music_eq_band_1_gain_db), 0.2) end
        end
        -- Music EQ Band 2 (~2.5kHz) — DẢI QUAN TRỌNG NHẤT
        if meq >= 0 and data.music_eq_band_2_gain_db then
            local p = find_p(music, meq, "Gain-Band 2")
            if p >= 0 then smooth(music, meq, p, db_to_norm(data.music_eq_band_2_gain_db), 0.25) end
        end
        -- Music EQ Band 3 (~5kHz)
        if meq >= 0 and data.music_eq_band_3_gain_db then
            local p = find_p(music, meq, "Gain-Band 3")
            if p >= 0 then smooth(music, meq, p, db_to_norm(data.music_eq_band_3_gain_db), 0.2) end
        end
    end
end

-- ── Main Loop ──
local tick = 0
function loop()
    tick = tick + 1
    
    -- Đọc và áp dụng AI commands
    if tick % math.floor(POLL_INTERVAL * 30) == 0 then
        local data = read_json(CMD_FILE) or {}
        local key_data = read_json(KEY_FILE)
        
        if key_data and key_data.timestamp then
            data.root_note = key_data.root_note
            data.scale = key_data.scale
        end
        
        if data and (data.timestamp ~= last_mtime or key_data) then
            if data.timestamp then last_mtime = data.timestamp end
            apply(data)
        end
    end
    
    -- Cập nhật BPM cho Python (mỗi 2 giây)
    bpm_tick = bpm_tick + 1
    if bpm_tick % 60 == 0 then  -- ~2 giây
        local bpm = reaper.Master_GetTempo()
        local f = io.open(BPM_FILE, "w")
        if f then
            f:write(string.format("%.1f", bpm))
            f:close()
        end
    end
    
    reaper.defer(loop)
end

reaper.ShowConsoleMsg("\n🤖 AI FX Bridge v3 — Tempo-Synced + Echo Detection\n")
reaper.ShowConsoleMsg("   Đang lắng nghe lệnh từ Python AI...\n")
reaper.ShowConsoleMsg("   BPM hiện tại: " .. string.format("%.0f", reaper.Master_GetTempo()) .. "\n\n")
loop()
