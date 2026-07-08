-- ============================================================================
-- 🔍 diagnose_karaoke.lua — Chẩn đoán + GHI RA FILE
-- ============================================================================

local OUTPUT_FILE = "/tmp/ai_karaoke_diagnose.txt"
local lines = {}

local function log(s)
    table.insert(lines, s)
    reaper.ShowConsoleMsg(s .. "\n")
end

local function flush()
    local f = io.open(OUTPUT_FILE, "w")
    if f then f:write(table.concat(lines, "\n")); f:close() end
end

local function find_param(track, fx, name)
    for i = 0, reaper.TrackFX_GetNumParams(track, fx) - 1 do
        local _, p = reaper.TrackFX_GetParamName(track, fx, i)
        if p and p:lower():find(name:lower(), 1, true) then return i, p end
    end
    return -1, ""
end

local function show_p(track, fx, name)
    local i, pname = find_param(track, fx, name)
    if i >= 0 then
        local val = reaper.TrackFX_GetParamNormalized(track, fx, i)
        log(string.format("    [%02d] %-25s = %.4f", i, pname, val))
        return val
    end
    return -1
end

local function find_fx(track, name)
    for i = 0, reaper.TrackFX_GetCount(track) - 1 do
        local _, n = reaper.TrackFX_GetFXName(track, i)
        if n and n:lower():find(name:lower(), 1, true) then return i, n end
    end
    return -1, ""
end

local function find_track(name)
    for i = 0, reaper.CountTracks(0) - 1 do
        local tr = reaper.GetTrack(0, i)
        local _, n = reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "", false)
        local clean_n = n:lower()
        if n == name or (n and n:find(name, 1, true)) or
           (name == "NHAC" and (clean_n:find("nhac", 1, true) or clean_n:find("nhạc", 1, true))) then
            return tr, n
        end
    end
    return nil, ""
end

-- ═══════════════════════════════════════
log("═══ CHẨN ĐOÁN KARAOKE ═══ " .. os.date("%H:%M:%S"))
-- ═══════════════════════════════════════

local bpm = reaper.Master_GetTempo()
local ms = 60000.0 / bpm
log(string.format("\nBPM = %.1f | 1 beat = %.0fms | 1/8 = %.0fms | dotted 1/8 = %.0fms", bpm, ms, ms*0.5, ms*0.75))

-- TRACKS
log(string.format("\nTracks: %d", reaper.CountTracks(0)))
for i = 0, reaper.CountTracks(0) - 1 do
    local tr = reaper.GetTrack(0, i)
    local _, name = reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "", false)
    local vol = reaper.GetMediaTrackInfo_Value(tr, "D_VOL")
    local arm = reaper.GetMediaTrackInfo_Value(tr, "I_RECARM")
    local mon = reaper.GetMediaTrackInfo_Value(tr, "I_RECMON")
    local inp = reaper.GetMediaTrackInfo_Value(tr, "I_RECINPUT")
    local fx_n = reaper.TrackFX_GetCount(tr)
    local peak = reaper.Track_GetPeakInfo(tr, 0)
    local pdb = peak > 0.00001 and (20 * math.log(peak, 10)) or -100
    
    log(string.format("  [%d] %s | vol=%.2f | arm=%s mon=%s | inp=%d | FX=%d | peak=%.1fdB",
        i+1, name or "?", vol, arm==1 and "Y" or "N", mon==1 and "Y" or "N", inp, fx_n, pdb))
    
    for j = 0, fx_n - 1 do
        local _, fn = reaper.TrackFX_GetFXName(tr, j)
        local en = reaper.TrackFX_GetEnabled(tr, j)
        log(string.format("    FX[%d]: %s %s", j, fn or "?", en and "ON" or "OFF"))
    end
end

-- VOCAL DETAIL
local vocal = find_track("VOCAL")
if vocal then
    log("\n═══ VOCAL DETAIL ═══")
    
    local gate = find_fx(vocal, "ReaGate")
    if gate >= 0 then
        log("  ReaGate (Noise Gate):")
        show_p(vocal, gate, "Threshold")
    end

    local eq = find_fx(vocal, "ReaEQ")
    if eq >= 0 then
        log("  ReaEQ:")
        for b = 1, 4 do
            show_p(vocal, eq, "Freq-Band " .. b)
            show_p(vocal, eq, "Gain-Band " .. b)
        end
    end
    
    local comp = find_fx(vocal, "ReaComp")
    if comp >= 0 then
        log("  ReaComp (Vocal Compressor):")
        show_p(vocal, comp, "Thresh")
        show_p(vocal, comp, "Ratio")
    end
end

-- VOCAL AUX / PARALLEL DETAIL
local voc_par = find_track("VOCAL PARALLEL")
if voc_par then
    log("\n═══ VOCAL PARALLEL DETAIL ═══")
    local vpcomp = find_fx(voc_par, "ReaComp")
    if vpcomp >= 0 then
        log("  ReaComp (Parallel Smashed Comp):")
        show_p(voc_par, vpcomp, "Thresh")
        show_p(voc_par, vpcomp, "Ratio")
    end
end

local voc_rev = find_track("VOCAL REVERB")
if voc_rev then
    log("\n═══ VOCAL REVERB DETAIL ═══")
    local verb, vn = find_fx(voc_rev, "ReaVerbate")
    if verb >= 0 then
        log("  ReaVerbate:")
        local room = show_p(voc_rev, verb, "Room Size")
        local wet = show_p(voc_rev, verb, "Wet")
        local dry = show_p(voc_rev, verb, "Dry")
        local damp = show_p(voc_rev, verb, "Dampening")
        show_p(voc_rev, verb, "Stereo")
        show_p(voc_rev, verb, "Width")
        show_p(voc_rev, verb, "Low Cut")
        show_p(voc_rev, verb, "High Cut")
        
        log(string.format("  → Room=%.2f %s", room, room > 0.60 and "⚠️ QUÁ LỚN!" or "✅ OK"))
        log(string.format("  → Wet=%.2f %s", wet, wet > 1.0 and "⚠️ SAI CHẾ ĐỘ WET!" or "✅ OK (100% Wet)"))
        log(string.format("  → Damp=%.2f %s", damp, damp < 0.40 and "⚠️ THẤP! Treble vang lâu" or "✅ OK"))
    end
    local rcomp = find_fx(voc_rev, "ReaComp")
    if rcomp >= 0 then
        log("  ReaComp (Sidechain Ducker):")
        show_p(voc_rev, rcomp, "Thresh")
        show_p(voc_rev, rcomp, "Ratio")
    end
end

local voc_del = find_track("VOCAL DELAY")
if voc_del then
    log("\n═══ VOCAL DELAY DETAIL ═══")
    local del, dn = find_fx(voc_del, "ReaDelay")
    if del >= 0 then
        log("  ReaDelay:")
        local len = show_p(voc_del, del, "Length")
        local fb = show_p(voc_del, del, "Feedback")
        local dvol = show_p(voc_del, del, "Volume")
        show_p(voc_del, del, "Lowpass")
        local est = len * 5000
        log(string.format("  → Delay ~%.0fms (beat=%.0fms) %s", est, ms, est > ms and "⚠️ TRÀN BEAT!" or "✅ OK"))
        log(string.format("  → Feedback=%.3f %s", fb, fb > 0.50 and "⚠️ QUÁ NHIỀU!" or "✅ OK"))
    end
    local dcomp = find_fx(voc_del, "ReaComp")
    if dcomp >= 0 then
        log("  ReaComp (Sidechain Ducker):")
        show_p(voc_del, dcomp, "Thresh")
        show_p(voc_del, dcomp, "Ratio")
    end
end

-- MUSIC DETAIL
local music = find_track("NHAC")
if music then
    log("\n═══ NHẠC NỀN DETAIL ═══")
    local meq = find_fx(music, "ReaEQ")
    if meq >= 0 then
        log("  ReaEQ (Ducking):")
        for b = 1, 4 do
            show_p(music, meq, "Freq-Band " .. b)
            show_p(music, meq, "Gain-Band " .. b)
        end
    end
end

-- MASTER
log("\n═══ MASTER ═══")
local master = reaper.GetMasterTrack(0)
log(string.format("  FX count: %d", reaper.TrackFX_GetCount(master)))
local mp = reaper.Track_GetPeakInfo(master, 0)
log(string.format("  Peak: %.1f dB", mp > 0.00001 and (20*math.log(mp,10)) or -100))

-- FILES
log("\n═══ FILES ═══")
local bf = io.open("/tmp/ai_karaoke_bpm.txt", "r")
if bf then log("  BPM file: " .. bf:read("*all")); bf:close()
else log("  BPM file: ❌ CHƯA CÓ") end

local cf = io.open("/tmp/ai_karaoke_commands.json", "r")
if cf then
    local c = cf:read("*all"); cf:close()
    log("  Command file: ✅ (" .. #c .. " bytes)")
else log("  Command file: ❌ CHƯA CÓ") end

log("\n═══ XONG ═══")
flush()
reaper.ShowConsoleMsg("\n✅ Đã ghi kết quả ra: " .. OUTPUT_FILE .. "\n")
