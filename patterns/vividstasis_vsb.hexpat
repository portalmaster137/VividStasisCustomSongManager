// Vividstasis VSC v1 charts (.vsb). See ../docs/VSB_FORMAT.md.
// Recovered from the shipped V1ChartReader / V1ChartWriter; no game code runs.
#pragma endian little
#pragma pattern_limit 4000000
#pragma array_limit 1000000

import std.mem;
import std.sys;
import type.float16;

enum NoteType : u8 {
    Chip = 0, Bumper = 1, Hold = 2, BPM = 3,
    IgnoredType4 = 4, UnknownType5 = 5,
    ChipMine = 6, BumperMine = 7, TimingBumper = 8
};

enum Ease : u8 {
    Linear = 1, OutElastic = 2, InExpo = 3, OutExpo = 4,
    InOutExpo = 5, InQuad = 6, OutQuad = 7, InOutQuad = 8,
    InCubic = 9, OutCubic = 10, InOutCubic = 11, OutBack = 12,
    InSine = 13, OutSine = 14, InOutSine = 15, OutQuart = 16,
    InOutCirc = 17, InCirc = 18, OutCirc = 19
};

enum ModID : u8 {
    Unknown = 0,
    prx = 1, prxb, prxc, pry, pryb, pryc, prsx, pra, przm, przmb,
    przx, przy, prrx, prry, prrz, prrzb,
    shxs, shxp, shxa, shys, shyp, shya,
    scrollspeed, noterot, velocity, spinradius, spiny, spinx, driven,
    beat, wave, hom, boost_distance, boost_time, yoffset, notealp,
    przmc, prxd, pryd, prct, prcb, prcl, prcr, prvib,
    shct, shft, shcb, shfb, shcl, shfl, shcr, shfr,
    scrollind0, scrollind1, scrollind2, scrollind3, scrollind4, scrollind5, scrollind6,
    drawdist, pburstleft, pburstright, particlexpower, particleypower, uialpha,
    fx_contrast, fx_chroma_distort, fx_film, fx_glow, fx_particleglow,
    pburstspeed, freeze, drawuntil
};

enum ExtraType : u8 {
    U8 = 0xB0, S8 = 0xB1, U32 = 0xB2, S32 = 0xB3,
    F16 = 0xB5, F32 = 0xB6, Boolean = 0xB7, String = 0xB8
};

struct ExtraEntry {
    ExtraType type;
    u8 id; // ID 1 = hold end time (ms), or BPM for a BPM event.
    if (type == ExtraType::U8) u8 value;
    else if (type == ExtraType::S8) s8 value;
    else if (type == ExtraType::U32) u32 value;
    else if (type == ExtraType::S32) s32 value;
    else if (type == ExtraType::F16) type::float16 value;
    else if (type == ExtraType::F32) float value;
    else if (type == ExtraType::Boolean) bool value;
    else if (type == ExtraType::String) char value[];
    else std::assert(false, "Unknown extra type; cannot safely skip its payload");
};

struct Extras {
    ExtraEntry entries[while(std::mem::read_unsigned($, 1) != 0xA7)];
    u8 end_extras;
    std::assert(end_extras == 0xA7, "Expected A7");
};

enum NoteFieldTag : u8 { Type = 0xA2, Lane = 0xA3, Time = 0xA4, Extras = 0xA6 };

struct NoteField {
    NoteFieldTag tag;
    if (tag == NoteFieldTag::Type) NoteType type;
    else if (tag == NoteFieldTag::Lane) u8 lane;
    else if (tag == NoteFieldTag::Time) float time_ms;
    else if (tag == NoteFieldTag::Extras) Extras extra;
    else std::assert(false, "Unknown note field");
};

struct Note {
    u8 begin_note;
    std::assert(begin_note == 0xA0, "Expected A0 note start");
    NoteField fields[while(std::mem::read_unsigned($, 1) != 0xA1)];
    u8 end_note;
    std::assert(end_note == 0xA1, "Expected A1 note end");
};

struct NoteList {
    Note notes[while(std::mem::read_unsigned($, 1) != 0xC1)];
    u8 end_notes;
    std::assert(end_notes == 0xC1, "Expected C1 note-list end");
};

struct Tween {
    float start_beat;
    float duration_beats;
    Ease ease;
    float value_start;
    float value_end;
    ModID mod_id; // Bit 7 set: selected gimmick object's extraMods, not global IDs.
    s8 proxy; // Negative targets controller; nonnegative indexes the proxy array.
};

struct PerFrame {
    float begin_beat;
    float end_beat; // Absolute end beat, not duration.
    char function_name[];
};

enum ModRecordTag : u8 { Tween = 0xE9, PerFrame = 0xEC };
struct ModRecord {
    ModRecordTag tag;
    if (tag == ModRecordTag::Tween) Tween tween;
    else if (tag == ModRecordTag::PerFrame) PerFrame per_frame;
    else std::assert(false, "Unknown modifier record");
};

struct ModList {
    ModRecord records[while(std::mem::read_unsigned($, 1) != 0xE3)];
    u8 end_mod_list;
    std::assert(end_mod_list == 0xE3, "Expected E3");
};

enum ModFieldTag : u8 { List = 0xE2, ProxyCount = 0xE4, ObjectName = 0xE5 };
struct ModField {
    ModFieldTag tag;
    if (tag == ModFieldTag::ProxyCount) u8 proxy_count;
    else if (tag == ModFieldTag::ObjectName) char object_name[];
    else if (tag == ModFieldTag::List) ModList list;
    else std::assert(false, "Unknown modifier field");
};

struct ModSection {
    ModField fields[while(std::mem::read_unsigned($, 1) != 0xE1)];
    u8 end_mod_section;
    std::assert(end_mod_section == 0xE1, "Expected E1");
};

enum SectionTag : u8 { Notes = 0xC0, Modifiers = 0xE0 };
struct Section {
    SectionTag tag;
    if (tag == SectionTag::Notes) NoteList notes;
    else if (tag == SectionTag::Modifiers) ModSection modifiers;
    else std::assert(false, "Unknown top-level section");
};

struct Chart {
    char magic[3];
    u8 version;
    u8 reserved;
    std::assert(magic == "VSC" && version == 1 && reserved == 0, "Expected VSC 01 00 header");
    Section sections[while(std::mem::read_unsigned($, 1) != 0xFF)];
    u8 end_chart;
    std::assert(end_chart == 0xFF, "Expected FF chart end");
    // No padding in the corpus. One shipped chart is unsigned.
    std::assert(std::mem::size() - $ == 0 || std::mem::size() - $ == 384,
                "Unexpected trailer size: expected absent or 384-byte RSA signature");
    if (std::mem::size() - $ == 384) {
        u8 rsa_signature[384]; // Opaque big-endian RSA-3072 signature; not verified here.
    }
};

Chart chart @ 0x00;
