-- ============================================================================
-- 🤖 realtime_fx_bridge.lua v3 — Tempo-Synced AI FX Bridge
-- ============================================================================
-- Xử lý Vocal FX + Music Ducking + Tempo Sync Delay/Reverb + Echo Detection.
-- Đọc /tmp/ai_karaoke_commands.json + Ghi BPM ra /tmp/ai_karaoke_bpm.txt
-- ============================================================================

local CMD_FILE = "/tmp/ai_karaoke_commands.json"
local BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
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
        -- CHORUS: Mix (genre-driven)
        if chorus >= 0 and data.chorus_mix then
            local p = find_p(vocal, chorus, "Mix")
            if p >= 0 then smooth(vocal, chorus, p, data.chorus_mix, 0.2) end
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
        local data = read_json(CMD_FILE)
        if data and data.timestamp and data.timestamp ~= last_mtime then
            last_mtime = data.timestamp
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
