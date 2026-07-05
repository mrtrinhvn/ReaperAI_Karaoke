-- ============================================================================
-- 🧹 fix_master.lua — Dọn FX chồng trên Master + Kiểm tra Input
-- ============================================================================

local function log(s) reaper.ShowConsoleMsg(s .. "\n") end

log("\n🧹 ═══ DỌN DẸP MASTER FX ═══\n")

local master = reaper.GetMasterTrack(0)
local n = reaper.TrackFX_GetCount(master)
log(string.format("  Master hiện có %d FX:", n))

-- Liệt kê tất cả FX hiện có
local fx_list = {}
for i = 0, n - 1 do
    local _, name = reaper.TrackFX_GetFXName(master, i)
    log(string.format("    [%d] %s", i, name or "?"))
    table.insert(fx_list, {idx = i, name = name or "?"})
end

-- Giữ lại: 1 ReaEQ, 1 ReaXcomp, 1 Stereo Width, 1 ReaLimit
-- Xóa tất cả duplicate
local keep = {}  -- {type -> first_index}
local to_remove = {}

for i = #fx_list, 1, -1 do
    local fx = fx_list[i]
    local ftype = "other"
    local n_lower = fx.name:lower()
    if n_lower:find("reaeq") then ftype = "eq"
    elseif n_lower:find("reaxcomp") then ftype = "xcomp"
    elseif n_lower:find("stereo") or n_lower:find("width") then ftype = "width"
    elseif n_lower:find("realimit") then ftype = "limit"
    end
    
    if keep[ftype] then
        -- Đã có loại này rồi → xóa duplicate
        table.insert(to_remove, fx.idx)
    else
        keep[ftype] = fx.idx
    end
end

-- Xóa từ cuối lên (để index không bị shift)
table.sort(to_remove, function(a,b) return a > b end)

if #to_remove > 0 then
    log(string.format("\n  🗑️ Xóa %d FX trùng lặp:", #to_remove))
    reaper.Undo_BeginBlock()
    for _, idx in ipairs(to_remove) do
        local _, name = reaper.TrackFX_GetFXName(master, idx)
        log(string.format("    Xóa [%d] %s", idx, name or "?"))
        reaper.TrackFX_Delete(master, idx)
    end
    reaper.Undo_EndBlock("Fix master FX duplicates", -1)
else
    log("\n  ✅ Không có FX trùng lặp.")
end

-- Kiểm tra lại
local n2 = reaper.TrackFX_GetCount(master)
log(string.format("\n  Master sau khi dọn: %d FX", n2))
for i = 0, n2 - 1 do
    local _, name = reaper.TrackFX_GetFXName(master, i)
    log(string.format("    [%d] %s ✅", i, name or "?"))
end

-- ── Kiểm tra Vocal Input ──
log("\n🎙️ ═══ KIỂM TRA VOCAL INPUT ═══\n")
for i = 0, reaper.CountTracks(0) - 1 do
    local tr = reaper.GetTrack(0, i)
    local _, name = reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "", false)
    if name and name:find("VOCAL") then
        local inp = reaper.GetMediaTrackInfo_Value(tr, "I_RECINPUT")
        local arm = reaper.GetMediaTrackInfo_Value(tr, "I_RECARM")
        local mon = reaper.GetMediaTrackInfo_Value(tr, "I_RECMON")
        log(string.format("  Input channel: %d", inp))
        log(string.format("  RecArm: %s | Monitor: %s", arm==1 and "ON" or "OFF", mon==1 and "ON" or "OFF"))
        
        -- inp=0 là mono ch1, inp=1 là mono ch2, inp=2 là mono ch3
        -- MixPre-6 thường ở ch1 (inp=0) hoặc ch2 (inp=1)
        if inp > 1 then
            log(string.format("  ⚠️ Input = %d (channel %d) — Có thể sai!", inp, inp+1))
            log("  → MixPre-6 thường ở Input 1 (inp=0) hoặc Input 2 (inp=1)")
            log("  → Đặt lại sang Input 1...")
            reaper.SetMediaTrackInfo_Value(tr, "I_RECINPUT", 0)  -- Mono channel 1
            log("  ✅ Đã chuyển về Input 1 Mono")
        else
            log("  ✅ Input OK")
        end
    end
end

-- Ghi file
local f = io.open("/tmp/ai_karaoke_diagnose.txt", "w")
if f then
    f:write("fix_master completed at " .. os.date("%H:%M:%S"))
    f:close()
end

log("\n✅ Dọn dẹp xong!")
log("═══════════════════════════════════════════\n")
