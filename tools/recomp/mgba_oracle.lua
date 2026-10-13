-- Independent mGBA replay for the locally hash-gated A9RE Wild Race profile.
-- Run from mGBA 0.10.5's Tools > Scripting window after loading the exact ROM.
-- All captured game memory and screenshots are written under ignored work/.

local output = "E:/Project/Decopm/work/native/mgba-wild-race-A-2141"
local schedule = {
	{900, 0},
	{2, 8},
	{60, 0},
	{2, 1},
	{90, 0},
	{2, 1},
	{90, 0},
	{2, 1},
	{90, 0},
	{2, 1},
	{600, 0},
	{300, 1},
}

assert(emu:getGameCode():match("A9RE$"), "Load the Road Rash Jailbreak USA A9RE ROM")
assert(emu:romSize() == 0x400000, "Unexpected ROM size")
emu:reset()

for _, segment in ipairs(schedule) do
	emu:setKeys(segment[2])
	for _ = 1, segment[1] do
		emu:runFrame()
	end
end

-- mGBA's frame callback and the native debug checkpoint differ by one phase.
local alignment_frames = 1
emu:setKeys(1)
emu:runFrame()
local cpu_frame = emu:currentFrame()
local cpu = {}
for i = 0, 14 do
	cpu["r" .. i] = emu:readRegister("r" .. i)
end
cpu.pc = emu:readRegister("pc")
cpu.cpsr = emu:readRegister("cpsr")

-- The native checkpoint is taken in the visible frame at scanline 183.
-- mGBA's runFrame returns in VBlank, so advance to the same raster point.
local scanline_steps = 0
while emu:read16(0x04000006) ~= 183 do
	emu:step()
	scanline_steps = scanline_steps + 1
	assert(scanline_steps < 100000, "Could not reach native checkpoint scanline")
end

local function writeRange(filename, domain, length)
	local file = assert(io.open(output .. "/" .. filename, "wb"))
	file:write(domain:readRange(0, length))
	file:close()
end

writeRange("iwram.bin", emu.memory.iwram, 0x8000)
writeRange("ewram.bin", emu.memory.wram, 0x40000)
emu:screenshot(output .. "/frame.png")

local state = assert(io.open(output .. "/state.txt", "w"))
state:write("rom_title=" .. emu:getGameTitle() .. "\n")
state:write("rom_code=" .. emu:getGameCode() .. "\n")
state:write("rom_size=" .. emu:romSize() .. "\n")
state:write("frames=" .. emu:currentFrame() .. "\n")
state:write("alignment_frames=" .. alignment_frames .. "\n")
state:write("cpu_frame=" .. cpu_frame .. "\n")
state:write("scanline_steps=" .. scanline_steps .. "\n")
state:write("schedule=")
for i, segment in ipairs(schedule) do
	if i > 1 then
		state:write(",")
	end
	state:write(string.format("%d:0x%03X", segment[1], segment[2]))
end
state:write("\n")

for i = 0, 14 do
	state:write("r" .. i .. "=" .. cpu["r" .. i] .. "\n")
end
state:write("pc=" .. cpu.pc .. "\n")
state:write("cpsr=" .. cpu.cpsr .. "\n")

local io = emu.memory.io
local registers16 = {
	{"dispcnt", 0x000}, {"dispstat", 0x004}, {"vcount", 0x006},
	{"bg0cnt", 0x008}, {"bg0hofs", 0x010}, {"bg0vofs", 0x012},
	{"bg1cnt", 0x00A}, {"bg1hofs", 0x014}, {"bg1vofs", 0x016},
	{"bg2cnt", 0x00C}, {"bg2hofs", 0x018}, {"bg2vofs", 0x01A},
	{"bg3cnt", 0x00E}, {"bg3hofs", 0x01C}, {"bg3vofs", 0x01E},
	{"bg2pa", 0x020}, {"bg2pb", 0x022}, {"bg2pc", 0x024}, {"bg2pd", 0x026},
	{"bg3pa", 0x030}, {"bg3pb", 0x032}, {"bg3pc", 0x034}, {"bg3pd", 0x036},
	{"win0h", 0x040}, {"win1h", 0x042}, {"win0v", 0x044}, {"win1v", 0x046},
	{"winin", 0x048}, {"winout", 0x04A}, {"mosaic", 0x04C},
	{"bldcnt", 0x050}, {"bldalpha", 0x052}, {"bldy", 0x054},
}
for _, register in ipairs(registers16) do
	state:write(register[1] .. "=" .. io:read16(register[2]) .. "\n")
end
state:write("bg2x=" .. io:read32(0x028) .. "\n")
state:write("bg2y=" .. io:read32(0x02C) .. "\n")
state:write("bg3x=" .. io:read32(0x038) .. "\n")
state:write("bg3y=" .. io:read32(0x03C) .. "\n")
state:close()

console:log("mGBA Wild Race oracle captured " .. emu:currentFrame() .. " frames")
