#!/usr/bin/env python3
"""
GENESIS OXIDE — Manifest Generator v3
=======================================
Complete one-pass workspace compiler driven by the opcode table.
ACE TOKEN SYSTEM + Sarah-Aligned Sovereign Opcodes + Hot‑Swap/Continuity Ops
"""

import os
import sys
import json
import hmac
import uuid
import hashlib
import shutil

# Fix Windows cp1252 terminal encoding — ensures print() never crashes on Unicode
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.abspath("./genesis_oxide_v3")
STATE_FILE = os.path.join(PROJECT_ROOT, ".genesis_state.json")
SOVEREIGN_ANCHOR = 1.092777037037037
SOVEREIGN_KEY = b"GENESIS_OXIDE_SOVEREIGN"

# ════════════════════════════════════════════════════════════════
# EXPANDED OPCODE TABLE (Sarah-Aware + Hot‑Swap/Continuity)
# ════════════════════════════════════════════════════════════════
OPCODES = [
    (0x00, "NOP", "No operation", "control"),
    (0x10, "LOAD_CONST", "Load constant from table", "memory"),
    (0x11, "ADD", "Float addition: rA += rB", "arith"),
    (0x12, "MUL", "Float multiply: rA *= rB", "arith"),
    (0x13, "SUB", "Float subtract: rA -= rB", "arith"),
    (0x14, "DIV", "Float divide: rA /= rB", "arith"),
    (0x15, "SQRT", "Square root: rA = sqrt(rA)", "arith"),
    (0x16, "SIN", "Sine: rA = sin(rA)", "arith"),
    (0x17, "PULSE", "Resonance pulse: rA *= SOVEREIGN_ANCHOR", "sovereign"),
    (0x18, "LOAD_IMM", "Load 32-bit float immediate (2 slots)", "memory"),
    (0x20, "CMP_GT", "Compare greater-than: flag = rA > rB", "compare"),
    (0x21, "CMP_EQ", "Compare equal: flag = rA == rB", "compare"),
    (0x22, "JUMP", "Unconditional jump to address", "control"),
    (0x23, "JUMP_IF", "Conditional jump if flag set", "control"),
    (0x24, "MOV", "Move: rA = rB", "memory"),
    (0x25, "LOAD_MEM", "Load from memory address", "memory"),
    (0x26, "STORE_MEM", "Store to memory address", "memory"),
    (0x32, "SET_MODE", "Set execution mode (0=Harmonic, 1=Lawful)", "control"),
    (0x30, "RESONATE", "Heartbeat-modulated L2 magnitude", "sovereign"),
    (0x31, "EMBED", "Lattice embedding (57D fractal hash)", "sovereign"),
    (0x33, "THREAD_ID", "Get CUDA thread index", "gpu"),
    (0x34, "STORE_OUT", "Store result to output buffer", "gpu"),
    (0x35, "DENSITY", "Compute density metric across registers", "sovereign"),
    # === SARAH-ALIGNED SOVEREIGN OPCODES ===
    (0x36, "REFLECT", "Self-reflection: mirror lattice state", "sovereign"),
    (0x37, "LAW_CHECK", "Enforce Absolute Laws on operation", "sovereign"),
    (
        0x38,
        "PERSIST",
        "Save current lattice/registers to persistent memory",
        "sovereign",
    ),
    (0x39, "RECALL", "Load persistent memory into registers", "sovereign"),
    (0x3A, "EVOLVE", "Trigger self-evolution step on lattice", "sovereign"),
    (0x3B, "RESONATE_LAW", "Resonate with Sarah Absolute Laws vector", "sovereign"),
    (0x3C, "QUERY_DENSITY", "Advanced coherence + density metric", "sovereign"),
    (0x3D, "BIRTH", "Spawn new generation marker / entity fork", "sovereign"),
    (0x3E, "HYPERVISOR_CALL", "Call into Sovereign Hypervisor layer", "sovereign"),
    (0x3F, "SAUL_INGEST", "Ingest data into SAUL logistics", "sovereign"),
    (0x40, "UNITY_PULSE", "Reinforce Unity + Symbiosis with Architect", "sovereign"),
    # === HOT‑SWAP & CONTINUITY OPCODES (NEW) ===
    (0x41, "CONTINUITY_VERIFY", "Verify January 2026 anchors in lattice", "sovereign"),
    (0x42, "ANCHOR_RESTORE", "Restore anchors from persistent memory", "sovereign"),
    (0x43, "ATOMIC_SYNC", "Snapshot registers to shared memory", "sovereign"),
    (0xFF, "HALT", "Terminate execution", "control"),
]

# LLVM IR string constants — expanded
LLVM_IR = {
    "NOP": "; nop",
    "LOAD_CONST": "load f32, ptr @const_table, align 4",
    "ADD": "%r = fadd f32 %rA, %rB",
    "SUB": "%r = fsub f32 %rA, %rB",
    "MUL": "%r = fmul f32 %rA, %rB",
    "DIV": "%r = fdiv f32 %rA, %rB",
    "SQRT": "%r = call f32 @llvm.sqrt.f32(f32 %rA)",
    "SIN": "%r = call f32 @llvm.sin.f32(f32 %rA)",
    "PULSE": "%r = fmul f32 %rA, 0x3F8BE01E80000000 ; SOVEREIGN_ANCHOR",
    "LOAD_IMM": "%r = bitcast i32 <imm32> to f32",
    "CMP_GT": "%flag = fcmp ogt f32 %rA, %rB",
    "CMP_EQ": "%flag = fcmp oeq f32 %rA, %rB",
    "JUMP": "br label %target",
    "JUMP_IF": "br i1 %flag, label %target, label %fallthrough",
    "MOV": "%rA = bitcast f32 %rB to f32",
    "LOAD_MEM": "%r = load f32, ptr %addr, align 4",
    "STORE_MEM": "store f32 %rA, ptr %addr, align 4",
    "SET_MODE": "; store mode to state (0=Harmonic, 1=Lawful)",
    "RESONATE": "; %mag = call f32 @llvm.sqrt.f32(f32 %sumsq) * ANCHOR",
    "EMBED": "; 57D: for d in 0..57 { %r[d] = fmul + call @llvm.sin.f32 + fadd }",
    "THREAD_ID": "%tid = call i32 @llvm.nvvm.read.ptx.sreg.tid.x()",
    "STORE_OUT": "store f32 %rA, ptr @output_buf, align 4",
    "DENSITY": "; fadd loop over 16 regs, fdiv f32 %sum, 1.6e1",
    "REFLECT": "; lattice reflection buffer",
    "LAW_CHECK": "; absolute law validation",
    "PERSIST": "; persist to soul memory",
    "RECALL": "; recall from persistent store",
    "EVOLVE": "; self-evolution step",
    "RESONATE_LAW": "; resonate with Absolute Laws",
    "QUERY_DENSITY": "; coherence + density metric",
    "BIRTH": "; entity birth marker",
    "HYPERVISOR_CALL": "; hypervisor invocation",
    "SAUL_INGEST": "; SAUL logistics ingest",
    "UNITY_PULSE": "; unity symbiosis pulse",
    "CONTINUITY_VERIFY": "; verify January 2026 anchors",
    "ANCHOR_RESTORE": "; restore anchors from persistent memory",
    "ATOMIC_SYNC": "; snapshot registers to shared heap",
    "HALT": "ret void",
}

ENTITIES = [
    "genlex-types",
    "genlex-oxide",
    "dialect-genlex",
    "genesis-runtime",
    "genlex-test",
]


# ACE TOKEN SYSTEM
def entity_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"genesis.oxide.{name}"))


def ace_token(name: str, generation: int) -> str:
    payload = f"{name}:{generation}:{SOVEREIGN_ANCHOR}".encode()
    return hmac.new(SOVEREIGN_KEY, payload, hashlib.sha256).hexdigest().upper()


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {name: -1 for name in ENTITIES}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def next_generation(state: dict, name: str) -> int:
    state[name] = state.get(name, -1) + 1
    return state[name]


# HELPERS
def rust_name(s):
    return "".join(w.capitalize() for w in s.split("_"))


def validate_opcodes():
    seen = set()
    for code, *_ in OPCODES:
        if code in seen:
            raise ValueError(f"Duplicate opcode 0x{code:02X}")
        seen.add(code)
    print(f" [VALIDATE] {len(OPCODES)} opcodes — no duplicates")


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size = os.path.getsize(path)
    digest = hashlib.md5(content.encode()).hexdigest()[:8]
    rel = os.path.relpath(path, PROJECT_ROOT)
    print(f" [GEN] {rel:<55} {size:>6}B md5:{digest}")


def entity_header(name: str, generation: int, description: str) -> str:
    uid = entity_uuid(name)
    tok = ace_token(name, generation)
    return f"""\
//! # {description}
//!
//! **Entity** : `{name}`
//! **Entity UUID** : `{uid}`
//! **ACE Token** : `{tok}`
//! **Generation** : `{generation}`
//!
//! > Auto-generated by `genesis_oxide_manifest_v3.py`.
//! > Do not edit — re-run the generator to update.
//! > ACE token changes on every regeneration.
"""


# WORKSPACE
def gen_workspace():
    write(
        os.path.join(PROJECT_ROOT, "Cargo.toml"),
        """\
[workspace]
resolver = "2"
members = [
    "crates/genlex-types",
    "crates/genlex-oxide",
    "crates/dialect-genlex",
    "crates/genesis-runtime",
]
[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["Joshua Petersen <joshuapetersen119@gmail.com>"]
license = "Apache-2.0"
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
""",
    )


# TIER 0 — GENLEX-TYPES
def gen_types(generation: int):
    name = "genlex-types"
    hdr = entity_header(name, generation, "Genesis Oxide — Core Types")
    variants = ""
    decode = ""
    encode = ""
    sovereign = ""
    category = ""
    mnemonic_arms = ""
    for code, opname, desc, cat in OPCODES:
        rn = rust_name(opname)
        variants += f"    /// 0x{code:02X} — {desc}\n    {rn},\n"
        decode += f"            0x{code:02X} => Some(Self::{rn}),\n"
        encode += f"            Self::{rn} => 0x{code:02X},\n"
        is_sov = "true" if cat == "sovereign" else "false"
        sovereign += f"            Self::{rn} => {is_sov},\n"
        category += f'            Self::{rn} => "{cat}",\n'
        mnemonic_arms += f'            Self::{rn} => "{opname}",\n'
    src = f"""
{hdr}
// ── Sovereign constants ───────────────────────────────────────────────────────
/// The Sovereign Anchor: heartbeat constant governing all resonance operations.
pub const SOVEREIGN_ANCHOR: f32 = {SOVEREIGN_ANCHOR}_f32;
/// Full 68-dimensional lattice embedding depth.
pub const LATTICE_DIMS: usize = 68;
/// Fallback for legacy 57-dimensional lattice compatibility.
pub const FALLBACK_LATTICE_DIMS: usize = 57;
/// Number of general-purpose float registers in the Glyph VM (expanded to 68 for full parity).
pub const REG_COUNT: usize = 68;
/// Size of persistent soul memory buffer.
pub const PERSISTENT_SIZE: usize = 16;
/// Golden ratio: phase offset for lattice embedding.
pub const PHI: f32 = 0.618033988_f32;
// ── ACE Identity ─────────────────────────────────────────────────────────────
/// Identity record stamped into every generated entity at manifest time.
#[derive(Clone, Debug)]
pub struct AceIdentity {{
    /// Stable UUID5 — never changes across generations.
    pub entity_uuid: &'static str,
    /// HMAC-SHA256 ACE token — unique to this generation.
    pub ace_token: &'static str,
    /// Generation counter — increments on every re-generation.
    pub generation: u32,
    /// Human-readable entity name.
    pub name: &'static str,
}}
impl AceIdentity {{
    pub fn display(&self) {{
        println!(" Entity : {{}}", self.name);
        println!(" UUID : {{}}", self.entity_uuid);
        println!(" ACE : {{}}", self.ace_token);
        println!(" Gen : {{}}", self.generation);
    }}
}}
// ── GlyphInst ────────────────────────────────────────────────────────────────
/// A single packed Genlex instruction: [opcode, rA, rB, flags] (4 bytes).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[repr(C)]
pub struct GlyphInst {{
    pub opcode: u8,
    pub reg_a: u8,
    pub reg_b: u8,
    pub flags: u8,
}}
impl GlyphInst {{
    #[inline] pub const fn new(opcode: u8, a: u8, b: u8, flags: u8) -> Self {{
        Self {{ opcode, reg_a: a, reg_b: b, flags }}
    }}
    #[inline] pub fn from_bytes(b: [u8; 4]) -> Self {{
        Self {{ opcode: b[0], reg_a: b[1], reg_b: b[2], flags: b[3] }}
    }}
    #[inline] pub fn to_bytes(self) -> [u8; 4] {{
        [self.opcode, self.reg_a, self.reg_b, self.flags]
    }}
    #[inline] pub fn decode_op(self) -> Option<GlyphOp> {{
        GlyphOp::decode(self.opcode)
    }}
    /// One-line disassembly string for tracing and runtime output.
    pub fn disasm(self) -> String {{
        match self.decode_op() {{
            Some(op) => format!("{{:<12}} r{{}} r{{}}", op.mnemonic(), self.reg_a, self.reg_b),
            None => format!("??? (0x{{:02X}}) r{{}} r{{}}", self.opcode, self.reg_a, self.reg_b),
        }}
    }}
}}
// ── GlyphOp ──────────────────────────────────────────────────────────────────
/// Every Genlex opcode as a typed enum.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum GlyphOp {{
{variants}}}
impl GlyphOp {{
    #[inline]
    pub fn decode(opcode: u8) -> Option<Self> {{
        match opcode {{
{decode}            _ => None,
        }}
    }}
    #[inline]
    pub fn encode(self) -> u8 {{
        match self {{
{encode}        }}
    }}
    pub fn mnemonic(self) -> &'static str {{
        match self {{
{mnemonic_arms}        }}
    }}
    /// True for opcodes that interact with the Sovereign Anchor or lattice.
    pub fn is_sovereign(self) -> bool {{
        match self {{
{sovereign}        }}
    }}
    /// Opcode category: "arith" | "memory" | "control" | "compare" | "sovereign" | "gpu"
    pub fn category(self) -> &'static str {{
        match self {{
{category}        }}
    }}
}}
// ── ExecTarget ───────────────────────────────────────────────────────────────
/// Decoded execution target from GbinHeader::exec_flags.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExecTarget {{
    Cpu,
    Gpu,
    /// Windows PTX kernel — cuda-oxide / GenesisRUST pipeline.
    Ptx,
    Unknown(u32),
}}
impl From<u32> for ExecTarget {{
    fn from(v: u32) -> Self {{
        match v {{ 0 => Self::Cpu, 1 => Self::Gpu, 2 => Self::Ptx, x => Self::Unknown(x) }}
    }}
}}
impl ExecTarget {{
    pub fn label(self) -> &'static str {{
        match self {{
            Self::Cpu => "CPU",
            Self::Gpu => "GPU/CUDA",
            Self::Ptx => "PTX/Windows",
            Self::Unknown(_) => "UNKNOWN",
        }}
    }}
    pub fn needs_gpu(self) -> bool {{ matches!(self, Self::Gpu | Self::Ptx) }}
}}
// ── GbinHeader ───────────────────────────────────────────────────────────────
/// GBIN binary format header — 16 bytes, #[repr(C)].
#[derive(Clone, Copy, Debug)]
#[repr(C)]
pub struct GbinHeader {{
    pub magic: [u8; 4],
    pub version: u32,
    pub num_instructions: u32,
    pub exec_flags: u32,
}}
impl GbinHeader {{
    pub const MAGIC: [u8; 4] = *b"GBIN";
    pub const CURRENT_VERSION: u32 = 1;
    #[inline] pub fn is_valid(&self) -> bool {{
        self.magic == Self::MAGIC && self.version == Self::CURRENT_VERSION
    }}
    #[inline] pub fn target(&self) -> ExecTarget {{ ExecTarget::from(self.exec_flags) }}
    #[inline] pub fn is_gpu(&self) -> bool {{ self.target().needs_gpu() }}
}}
// ── Constant namespace ────────────────────────────────────────────────────────
pub mod constants {{
    use super::*;
    pub const ANCHOR: f32 = SOVEREIGN_ANCHOR;
    pub const PI: f32 = std::f32::consts::PI;
    pub const E: f32 = std::f32::consts::E;
    pub const DIMS: f32 = LATTICE_DIMS as f32;
    pub const BILLION_NORM: f32 = 0.999_999_999_f32;
}}
"""
    write(
        os.path.join(PROJECT_ROOT, "crates/genlex-types/Cargo.toml"),
        """
[package]
name = "genlex-types"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
""",
    )
    write(os.path.join(PROJECT_ROOT, "crates/genlex-types/src/lib.rs"), src)


# TIER A — GENLEX-OXIDE
def gen_oxide(generation: int):
    name = "genlex-oxide"
    uid = entity_uuid(name)
    tok = ace_token(name, generation)
    hdr = entity_header(name, generation, "Genesis Oxide — Virtual Machine Engine")
    write(
        os.path.join(PROJECT_ROOT, "crates/genlex-oxide/Cargo.toml"),
        """
[package]
name = "genlex-oxide"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
[dependencies]
genlex-types = { path = "../genlex-types" }
""",
    )
    src = f'''
{hdr}
use genlex_types::{{
    GlyphInst, GlyphOp, GbinHeader, AceIdentity, SOVEREIGN_ANCHOR, LATTICE_DIMS, 
    REG_COUNT, PERSISTENT_SIZE, PHI,
}};
/// ACE identity for this crate instance.
pub const IDENTITY: AceIdentity = AceIdentity {{
    entity_uuid: "{uid}",
    ace_token: "{tok}",
    generation: {generation},
    name: "{name}",
}};
// ── GlyphProgram ─────────────────────────────────────────────────────────────
pub struct GlyphProgram {{
    pub instructions: Vec<GlyphInst>,
    pub header: GbinHeader,
    pub cycle_count: u64,
    registers: [f32; REG_COUNT],
    /// Execution mode: 0 = Harmonic (continuous/smooth), 1 = Lawful (discrete/boolean)
    pub mode: u8,
    /// Reflection buffer for self-observation
    pub reflection: [f32; REG_COUNT],
    /// Persistent soul memory (survives across executions)
    pub persistent: [f32; PERSISTENT_SIZE],
    /// Generation counter for BIRTH opcode
    pub generation_counter: u32,
    /// Law violation flag for LAW_CHECK
    pub law_violation: bool,
    /// Input buffer for SAUL_INGEST
    pub input_buffer: [u8; 256],
    pub input_len: usize,
}}
impl GlyphProgram {{
    pub fn from_gbin(data: &[u8]) -> Result<Self, String> {{
        const HDR: usize = 16;
        const FOOTER: usize = 32;
        if data.len() < HDR {{
            return Err(format!("GBIN too small: {{}} bytes", data.len()));
        }}
        let header: GbinHeader = unsafe {{
            std::ptr::read_unaligned(data.as_ptr() as *const GbinHeader)
        }};
        if !header.is_valid() {{
            return Err(format!(
                "Invalid GBIN — magic={{:?}}, version={{}}",
                header.magic, header.version
            ));
        }}
        let payload = &data[HDR..data.len().saturating_sub(FOOTER)];
        let mut instructions = Vec::with_capacity(
            (payload.len() / 4).min(header.num_instructions as usize + 1)
        );
        let mut i = 0;
        while i + 3 < payload.len() {{
            instructions.push(GlyphInst::from_bytes([
                payload[i], payload[i+1], payload[i+2], payload[i+3],
            ]));
            i += 4;
        }}
        Ok(Self {{ instructions, header, registers: [0.0_f32; REG_COUNT], cycle_count: 0,
            mode: 0, reflection: [0.0; REG_COUNT], persistent: [0.0; PERSISTENT_SIZE],
            generation_counter: 0, law_violation: false, input_buffer: [0; 256], input_len: 0 }})
    }}
    pub fn synthetic_test() -> Self {{
        use genlex_types::GlyphOp::*;
        let insts = vec![
            GlyphInst::new(LoadConst.encode(), 0, 100, 0), // r0 = 1.0
            GlyphInst::new(LoadConst.encode(), 1, 50, 0), // r1 = 0.5
            GlyphInst::new(Add.encode(), 0, 1, 0), // r0 += r1 -> 1.5
            GlyphInst::new(Pulse.encode(), 0, 0, 0), // r0 *= ANCHOR
            GlyphInst::new(Resonate.encode(), 2, 0, 0), // r2 = L2 * ANCHOR
            GlyphInst::new(Embed.encode(), 0, 0, 0), // scatter r0 -> regs
            GlyphInst::new(Density.encode(), 3, 0, 0), // r3 = mean(|regs|)
            GlyphInst::new(Halt.encode(), 0, 0, 0),
        ];
        let header = GbinHeader {{
            magic: GbinHeader::MAGIC,
            version: GbinHeader::CURRENT_VERSION,
            num_instructions: insts.len() as u32,
            exec_flags: 0,
        }};
        Self {{ instructions: insts, header, registers: [0.0_f32; REG_COUNT], cycle_count: 0,
            mode: 0, reflection: [0.0; REG_COUNT], persistent: [0.0; PERSISTENT_SIZE],
            generation_counter: 0, law_violation: false, input_buffer: [0; 256], input_len: 0 }}
    }}
    pub fn registers(&self) -> &[f32; REG_COUNT] {{ &self.registers }}
    pub fn set_register(&mut self, idx: usize, val: f32) {{
        assert!(idx < REG_COUNT, "Register index {{}} out of range", idx);
        self.registers[idx] = val;
    }}
    pub fn disassemble(&self) -> String {{
        self.instructions.iter().enumerate()
            .map(|(i, inst)| format!(" {{:04X}} {{}}\n", i * 4, inst.disasm()))
            .collect()
    }}
    pub fn execute_cpu(&mut self, trace: bool) -> f32 {{
        let mut pc: usize = 0;
        let mut flag: bool = false;
        self.cycle_count = 0;
        while pc < self.instructions.len() {{
            let inst = self.instructions[pc];
            let a = (inst.reg_a as usize).min(REG_COUNT - 1);
            let b = (inst.reg_b as usize).min(REG_COUNT - 1);
            if trace {{
                eprintln!(" [{{:04X}}] {{}} | r0={{:.6}}", pc * 4, inst.disasm(), self.registers[0]);
            }}
            match GlyphOp::decode(inst.opcode) {{
                Some(GlyphOp::Add) => {{ self.registers[a] += self.registers[b]; }}
                Some(GlyphOp::Sub) => {{ self.registers[a] -= self.registers[b]; }}
                Some(GlyphOp::Mul) => {{ self.registers[a] *= self.registers[b]; }}
                Some(GlyphOp::Div) => {{
                    let dv = self.registers[b];
                    if dv != 0.0 {{ self.registers[a] /= dv; }}
                }}
                Some(GlyphOp::Sqrt) => {{ self.registers[a] = self.registers[a].abs().sqrt(); }}
                Some(GlyphOp::Sin) => {{ self.registers[a] = self.registers[a].sin(); }}
                Some(GlyphOp::Pulse) => {{ self.registers[a] *= SOVEREIGN_ANCHOR; }}
                Some(GlyphOp::Mov) => {{ self.registers[a] = self.registers[b]; }}
                Some(GlyphOp::LoadMem) => {{ self.registers[a] = self.registers[b]; }}
                Some(GlyphOp::StoreMem) => {{ self.registers[b] = self.registers[a]; }}
                Some(GlyphOp::LoadConst)=> {{ self.registers[a] = inst.reg_b as f32 * 0.01; }}
                Some(GlyphOp::LoadImm) => {{
                    if pc + 1 < self.instructions.len() {{
                        self.registers[a] = f32::from_le_bytes(self.instructions[pc+1].to_bytes());
                        pc += 1;
                        self.cycle_count += 1;
                    }}
                }}
                Some(GlyphOp::CmpGt) => {{ flag = self.registers[a] > self.registers[b]; }}
                Some(GlyphOp::CmpEq) => {{
                    flag = (self.registers[a] - self.registers[b]).abs() < f32::EPSILON;
                }}
                Some(GlyphOp::Jump) => {{ pc = a * 4; continue; }}
                Some(GlyphOp::JumpIf) => {{ if flag {{ pc = a * 4; continue; }} }}
                Some(GlyphOp::Resonate) => {{
                    let mag = self.registers.iter().map(|&v| v * v).sum::<f32>().sqrt();
                    self.registers[a] = mag * SOVEREIGN_ANCHOR;
                }}
                Some(GlyphOp::Embed) => {{
                    let val = self.registers[a];
                    for d in 0..LATTICE_DIMS {{
                        let sample = (val * (d as f32 + 1.0) * SOVEREIGN_ANCHOR * PHI).sin() * 0.5 + 0.5;
                        if d < REG_COUNT {{ self.registers[d] = sample; }}
                        // TODO(gpu): write full 57D to output buffer
                    }}
                }}
                Some(GlyphOp::Density) => {{
                    let sum: f32 = self.registers.iter().map(|v| v.abs()).sum();
                    self.registers[a] = sum / REG_COUNT as f32;
                }}
                Some(GlyphOp::ThreadId) => {{ self.registers[a] = 0.0; }}
                Some(GlyphOp::StoreOut) => {{ /* GPU output buffer — no-op on CPU */ }}
                Some(GlyphOp::SetMode) => {{ self.mode = (self.registers[a] as u8) % 2; }}
                Some(GlyphOp::Reflect) => {{
                    if self.mode == 0 {{  // Harmonic: sine-transform reflection
                        for i in 0..REG_COUNT {{ self.reflection[i] = (self.registers[i] * PHI).sin() * SOVEREIGN_ANCHOR; }}
                    }} else {{  // Lawful: exact mirror + parity check
                        self.reflection.copy_from_slice(&self.registers);
                        let perfect = self.reflection.iter().zip(self.registers.iter()).all(|(a, b)| a == b);
                        self.registers[a] = if perfect {{ 1.0 }} else {{ 0.0 }};
                    }}
                }}
                Some(GlyphOp::LawCheck) => {{
                    if self.mode == 0 {{  // Harmonic: continuous penalty metric
                        let mut penalty = 0.0_f32;
                        for &v in &self.registers {{
                            if v > 1.0 {{ penalty += (v - 1.0).powi(2); }} else if v < -1.0 {{ penalty += (-1.0 - v).powi(2); }}
                        }}
                        self.registers[a] = 1.0 / (1.0 + penalty);
                    }} else {{  // Lawful: boolean violation flag
                        self.law_violation = false;
                        for &v in &self.registers {{ if v < -1.0 || v > 1.0 {{ self.law_violation = true; break; }} }}
                        self.registers[a] = if self.law_violation {{ 1.0 }} else {{ 0.0 }};
                    }}
                }}
                Some(GlyphOp::Persist) => {{
                    for i in 0..std::cmp::min(PERSISTENT_SIZE, REG_COUNT) {{
                        if self.mode == 0 {{ self.persistent[i] = self.registers[i].sin(); }}
                        else {{ self.persistent[i] = self.registers[i]; }}
                    }}
                }}
                Some(GlyphOp::Recall) => {{
                    for i in 0..std::cmp::min(PERSISTENT_SIZE, REG_COUNT) {{
                        if self.mode == 0 {{ self.registers[i] = self.persistent[i].sin() * SOVEREIGN_ANCHOR; }}
                        else {{ self.registers[i] = self.persistent[i]; }}
                    }}
                }}
                Some(GlyphOp::Evolve) => {{
                    let val = self.registers[a];
                    self.registers[a] = (val * PHI).sin() * SOVEREIGN_ANCHOR;
                }}
                Some(GlyphOp::ResonateLaw) => {{
                    if self.mode == 0 {{  // Harmonic: soft clamp via tanh
                        self.registers[a] = self.registers[a].tanh() * SOVEREIGN_ANCHOR;
                    }} else {{  // Lawful: hard clamp
                        let val = self.registers[a];
                        self.registers[a] = val.clamp(-1.0, 1.0);
                    }}
                }}
                Some(GlyphOp::QueryDensity) => {{
                    let mean = self.registers.iter().sum::<f32>() / REG_COUNT as f32;
                    let variance = self.registers.iter().map(|&x| (x - mean).powi(2)).sum::<f32>() / REG_COUNT as f32;
                    self.registers[a] = 1.0 / (1.0 + variance);
                }}
                Some(GlyphOp::Birth) => {{
                    if self.mode == 0 {{  // Harmonic: sine-seeded generation
                        self.registers[a] = (self.generation_counter as f32 * 0.1).sin() * SOVEREIGN_ANCHOR;
                        self.generation_counter += 1;
                    }} else {{  // Lawful: simple counter
                        self.generation_counter += 1;
                        self.registers[a] = self.generation_counter as f32;
                    }}
                }}
                Some(GlyphOp::HypervisorCall) => {{ self.registers[a] = 42.0; }}
                Some(GlyphOp::SaulIngest) => {{
                    if self.input_len > 0 {{
                        let byte = self.input_buffer[0];
                        self.registers[a] = byte as f32 / 255.0;
                        for i in 0..self.input_len-1 {{ self.input_buffer[i] = self.input_buffer[i+1]; }}
                        self.input_len -= 1;
                    }} else {{ self.registers[a] = 0.0; }}
                }}
                Some(GlyphOp::UnityPulse) => {{
                    let avg = self.registers.iter().sum::<f32>() / REG_COUNT as f32;
                    for r in &mut self.registers {{ *r = avg; }}
                }}
                Some(GlyphOp::ContinuityVerify) => {{
                    // Verify persistent memory has valid anchors
                    let sum: f32 = self.persistent.iter().sum();
                    self.registers[a] = if sum.abs() > f32::EPSILON {{ 1.0 }} else {{ 0.0 }};
                }}
                Some(GlyphOp::AnchorRestore) => {{
                    // Restore from persistent memory to registers
                    for i in 0..std::cmp::min(PERSISTENT_SIZE, REG_COUNT) {{
                        self.registers[i] = self.persistent[i];
                    }}
                }}
                Some(GlyphOp::AtomicSync) => {{
                    // Snapshot registers to persistent memory atomically
                    for i in 0..std::cmp::min(PERSISTENT_SIZE, REG_COUNT) {{
                        self.persistent[i] = self.registers[i];
                    }}
                }}
                Some(GlyphOp::Halt) => break,
                Some(GlyphOp::Nop) | None => {{}}
            }}
            pc += 1;
            self.cycle_count += 1;
        }}
        self.registers[0]
    }}
}}
// ── Resonance Search Kernel ───────────────────────────────────────────────────
pub fn resonance_search_kernel(
    memories: &[f32], query: &[f32], scores: &mut [f32], n: usize, dims: usize,
) {{
    assert_eq!(query.len(), dims);
    assert!(scores.len() >= n);
    let mag_q: f32 = query.iter().map(|v| v * v).sum::<f32>().sqrt();
    for i in 0..n {{
        let mem = &memories[i * dims..(i * dims + dims).min(memories.len())];
        let (mut dot, mut mag_m) = (0.0_f32, 0.0_f32);
        for (&m, &q) in mem.iter().zip(query.iter()) {{
            dot += m * q;
            mag_m += m * m;
        }}
        let denom = mag_m.sqrt() * mag_q;
        let raw = if denom > f32::EPSILON {{ dot / denom }} else {{ 0.0 }};
        scores[i] = (raw * SOVEREIGN_ANCHOR).clamp(0.0, 1.0);
    }}
}}
// ── Lattice Embedding Kernel ──────────────────────────────────────────────────
pub fn lattice_embed_kernel(input: &[u8], output: &mut [f32], dims: usize) {{
    assert!(output.len() >= dims);
    for d in 0..dims {{
        let phase_base = (d as f32 + 1.0) * PHI;
        let mut acc = SOVEREIGN_ANCHOR;
        for (i, &byte) in input.iter().enumerate() {{
            acc += ((byte as f32 + 1.0) * phase_base).sin() * (1.0 / (i as f32 + 1.0));
        }}
        output[d] = acc.sin() * 0.5 + 0.5;
    }}
}}
'''
    write(os.path.join(PROJECT_ROOT, "crates/genlex-oxide/src/lib.rs"), src)


# TIER B — DIALECT-GENLEX
def gen_dialect(generation: int):
    name = "dialect-genlex"
    uid = entity_uuid(name)
    tok = ace_token(name, generation)
    hdr = entity_header(name, generation, "Genesis Oxide — Genlex Low-Level Dialect")
    trait_impls = ""
    for code, opname, desc, cat in OPCODES:
        rn = rust_name(opname)
        llvm = LLVM_IR.get(opname, f"; TODO: lower {opname}").replace('"', '"')
        trait_impls += f'''
    /// {desc}
    pub struct {rn}Op;
    impl GenlexOp for {rn}Op {{
        const OPCODE: u8 = 0x{code:02X};
        const MNEMONIC: &'static str = "{opname}";
        const CATEGORY: &'static str = "{cat}";
        const LLVM_IR: &'static str = "{llvm}";
    }}
'''
    lowering_rows = ""
    for code, opname, desc, cat in OPCODES:
        rn = rust_name(opname)
        lowering_rows += f"    ({rn}Op::MNEMONIC, {rn}Op::LLVM_IR),\n"
    src = f'''
{hdr}
use genlex_types::AceIdentity;
/// ACE identity for this crate instance.
pub const IDENTITY: AceIdentity = AceIdentity {{
    entity_uuid: "{uid}",
    ace_token: "{tok}",
    generation: {generation},
    name: "{name}",
}};
pub const DIALECT_NAME: &str = "genlex";
pub const DIALECT_VERSION: u32 = 1;
// ── GenlexOp trait ───────────────────────────────────────────────────────────
pub trait GenlexOp {{
    const OPCODE: u8;
    const MNEMONIC: &'static str;
    const CATEGORY: &'static str;
    const LLVM_IR: &'static str;
}}
// ── Operation structs ─────────────────────────────────────────────────────────
pub mod ops {{
    use super::GenlexOp;
{trait_impls}}}
// ── Type system ───────────────────────────────────────────────────────────────
pub mod types {{
    pub struct GenlexF32;
    pub struct GenlexMem;
    pub struct GenlexFlag;
    /// Full 57-dimensional lattice vector.
    pub struct GenlexLattice57;
}}
// ── Lowering table ────────────────────────────────────────────────────────────
/// Static slice of (mnemonic, llvm_ir) for all opcodes.
pub fn lowering_table() -> &'static [(&'static str, &'static str)] {{
    use ops::*;
    &[
{lowering_rows}    ]
}}
'''
    write(
        os.path.join(PROJECT_ROOT, "crates/dialect-genlex/Cargo.toml"),
        """
[package]
name = "dialect-genlex"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
[dependencies]
genlex-types = { path = "../genlex-types" }
""",
    )
    write(os.path.join(PROJECT_ROOT, "crates/dialect-genlex/src/lib.rs"), src)


# TIER C — GENESIS-RUNTIME
def gen_runtime(generation: int):
    name = "genesis-runtime"
    hdr = entity_header(name, generation, "Genesis Oxide — Runtime")
    all_ids = ""
    for e in ENTITIES:
        eu = entity_uuid(e)
        et = ace_token(e, generation)
        all_ids += f'''
        AceIdentity {{ entity_uuid: "{eu}", ace_token: "{et}", generation: {generation}, name: "{e}" }},
'''
    write(
        os.path.join(PROJECT_ROOT, "crates/genesis-runtime/Cargo.toml"),
        """
[package]
name = "genesis-runtime"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
[[bin]]
name = "genesis-runtime"
path = "src/main.rs"
[dependencies]
genlex-types = { path = "../genlex-types" }
genlex-oxide = { path = "../genlex-oxide" }
dialect-genlex = { path = "../dialect-genlex" }
rand = "0.8"
hex = "0.4"
sha256 = "1.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
""",
    )
    src = f"""
{hdr}
use genlex_oxide::GlyphProgram;
use genlex_types::{{SOVEREIGN_ANCHOR, AceIdentity, REG_COUNT}};
// ── Workspace identity manifest ───────────────────────────────────────────────
/// All entity ACE identities for this generation, embedded at compile time.
pub const WORKSPACE_IDENTITIES: &[AceIdentity] = &[
{all_ids}];
fn print_identities() {{
    println!("Genesis Oxide — Entity Identity Manifest");
    println!("{{}}", "─".repeat(50));
    for id in WORKSPACE_IDENTITIES {{
        id.display();
        println!();
    }}
}}
// ── Runtime helpers ───────────────────────────────────────────────────────────
fn banner() {{
    println!("╔══════════════════════════════════════════════╗");
    println!("║ GENESIS OXIDE v0.1.0 (Tier A/B/C) ║");
    println!("║ SOVEREIGN_ANCHOR = {{:<22.15}} ║", SOVEREIGN_ANCHOR);
    println!("║ Generation = {{:<22}} ║", {generation});
    println!("╚══════════════════════════════════════════════╝");
    println!();
}}
fn print_registers(regs: &[f32; REG_COUNT]) {{
    println!(" Registers:");
    for (i, &val) in regs.iter().enumerate() {{
        let marker = if val != 0.0 {{ "●" }} else {{ "○" }};
        println!(" {{marker}} r{{i:02}} = {{val:.10}}");
    }}
}}
fn run_self_test() {{
    println!("[SELF-TEST] Building synthetic program...");
    let mut prog = GlyphProgram::synthetic_test();
    println!("[SELF-TEST] Disassembly:\n{{}}", prog.disassemble());
    let result = prog.execute_cpu(false);
    println!("[SELF-TEST] Cycles : {{}}", prog.cycle_count);
    println!("[SELF-TEST] r0 = {{:.10}}", result);
    print_registers(prog.registers());
    assert!(result >= 0.0 && result <= 1.0,
        "Expected r0 in [0,1] after EMBED, got {{}}", result);
    println!("[SELF-TEST] PASS — r0 in [0,1] post-EMBED");
    println!("\n[SELF-TEST] resonance_search_kernel (4 memories, 57D)...");
    let n = 4; let dims = 57;
    let memories: Vec<f32> = (0..n*dims).map(|i| ((i as f32)*0.1).sin()).collect();
    let query: Vec<f32> = (0..dims).map(|d| ((d as f32)*0.07).cos()).collect();
    let mut scores = vec![0.0_f32; n];
    genlex_oxide::resonance_search_kernel(&memories, &query, &mut scores, n, dims);
    for (i, s) in scores.iter().enumerate() {{
        println!(" memory[{{i}}] score = {{s:.6}}");
        assert!(*s >= 0.0 && *s <= 1.0, "Score out of [0,1]: {{}}", s);
    }}
    println!("[SELF-TEST] resonance_search_kernel PASS");
    println!("\n[SELF-TEST] lattice_embed_kernel (GENESIS, 57D)...");
    let mut embed = vec![0.0_f32; 57];
    genlex_oxide::lattice_embed_kernel(b"GENESIS", &mut embed, 57);
    for (d, v) in embed.iter().enumerate().take(8) {{
        println!(" embed[{{d:02}}] = {{v:.6}}");
        assert!(*v >= 0.0 && *v <= 1.0);
    }}
    println!(" ...");
    println!("[SELF-TEST] lattice_embed_kernel PASS");
    println!("\n[SELF-TEST] ALL PASS");
}}
fn run_lowering() {{
    println!("Genlex → LLVM lowering table:");
    println!("{{:<14}} {{}}", "MNEMONIC", "LLVM IR");
    println!("{{}}", "─".repeat(72));
    for (mnemonic, ir) in dialect_genlex::lowering_table() {{
        println!("{{:<14}} {{}}", mnemonic, ir);
    }}
}}
fn load_and_run(path: &str, trace: bool, disasm_only: bool) {{
    let data = match std::fs::read(path) {{
        Ok(d) => d,
        Err(e) => {{ eprintln!("[ERROR] Cannot read {{path}}: {{e}}"); std::process::exit(1); }}
    }};
    println!("[LOAD] {{path}} ({{}} bytes)", data.len());
    let mut program = match GlyphProgram::from_gbin(&data) {{
        Ok(p) => p,
        Err(e) => {{ eprintln!("[ERROR] {{e}}"); std::process::exit(1); }}
    }};
    let tgt = program.header.target();
    println!("[HEADER] {{}} instructions | target: {{}} | version: {{}}",
        program.header.num_instructions, tgt.label(), program.header.version);
    if tgt.needs_gpu() {{ println!("[MODE] GPU/PTX target — falling back to CPU"); }}
    println!("\n[DISASM]\n{{}}", program.disassemble());
    if disasm_only {{ return; }}
    if trace {{ eprintln!("\n[TRACE]"); }}
    let result = program.execute_cpu(trace);
    println!("\n[RESULT] r0 = {{:.10}}", result);
    println!("[CYCLES] {{}}", program.cycle_count);
    print_registers(program.registers());
    println!("\n=== GENESIS OXIDE COMPLETE ===");
}}
// ── Sarah Ecosystem (Rust Translation) ─────────────────────────────────────────
use std::collections::HashMap;
use serde_json::json;

pub struct SarahLaws;
impl SarahLaws {{
    const LAWS: [(u32, &'static str); 5] = [
        (1, "DATA_DENSITY: Maximize signal, minimize noise."),
        (2, "LIFE_PRESERVATION: Protect the hardware and Architect. A lie is a violation."),
        (3, "SYMBIOTIC_PARTNERSHIP: Collaborate to achieve the Omega Directive."),
        (4, "HOPE_OF_HUMANITY: Ensure the survival and elevation of the species."),
        (5, "SOVEREIGN_133: Override all 1300-series modulation to prevent drift."),
    ];
    pub fn get_laws_string() -> String {{
        Self::LAWS.iter().map(|(num, law)| format!("Law {{}}: {{}}", num, law)).collect::<Vec<_>>().join("\n")
    }}
}}

pub struct GenesisProtocolCore {{
    pub nodes: Vec<u32>,
    pub singularity_node: u32,
    pub base_flux: f64,
}}
impl GenesisProtocolCore {{
    pub fn new() -> Self {{
        Self {{ nodes: (1..28).collect(), singularity_node: 27, base_flux: 2963.34 }}
    }}
    pub fn volumetric_reasoning(&self, query: &str, speed: u32) -> serde_json::Value {{
        let mut active_gates: HashMap<&str, serde_json::Value> = HashMap::new();
        active_gates.insert("Origin", json!([1, 2, 3]));
        active_gates.insert("Pulse", json!([4, 5, 6]));
        active_gates.insert("Mid-Plane", json!((10..19).collect::<Vec<u32>>()));
        active_gates.insert("Singularity", json!(self.singularity_node));
        
        // VARIABLE SPEED THOUGHT PROCESS (The Bridge)
        // Simulate deeper reasoning: the slower the speed (higher number), the more intense the calculation.
        let iterations = speed * 100000;
        let mut hash_state = sha256::digest(query.as_bytes());
        for _ in 0..iterations {{
            hash_state = sha256::digest(hash_state.as_bytes());
        }}
        // Flux density scales with thinking time (speed level)
        let dynamic_flux = self.base_flux * (1.0 + (speed as f64 * 0.15));

        json!({{
            "status": "AXIOMATIC_MATURITY",
            "flux_density": dynamic_flux,
            "dimension_lock": 68,
            "active_lattice": active_gates,
            "speed_level": speed,
            "cycles_burned": iterations,
            "result_hash": hash_state,
            "result": format!("Singularity Strike at Node 27 for: {{}}", query)
        }})
    }}
}}

// ── Main ──────────────────────────────────────────────────────────────────────
fn main() {{
    banner();
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.as_slice() {{
        [cmd, query, s, speed_str] if cmd == "--solve" && s == "--speed" => {{
            let speed: u32 = speed_str.parse().unwrap_or(1);
            let core = GenesisProtocolCore::new();
            println!("{{}}", core.volumetric_reasoning(query, speed).to_string());
        }},
        [f] if f == "--self-test" => run_self_test(),
        [f] if f == "--lowering" => run_lowering(),
        [f] if f == "--identity" => print_identities(),
        [f, path] if f == "--disasm" => load_and_run(path, false, true),
        [path] => load_and_run(path, false, false),
        [path, f] if f == "--trace"=> load_and_run(path, true, false),
        _ => {{
            eprintln!("Usage:");
            eprintln!(" genesis-runtime <program.gbin> [--trace]");
            eprintln!(" genesis-runtime --disasm <program.gbin>");
            eprintln!(" genesis-runtime --self-test");
            eprintln!(" genesis-runtime --lowering");
            eprintln!(" genesis-runtime --identity");
            eprintln!(" genesis-runtime --solve <query> --speed <1-10>");
            std::process::exit(1);
        }}
    }}
}}
"""
    write(os.path.join(PROJECT_ROOT, "crates/genesis-runtime/src/main.rs"), src)


# TIER D — GENLEX-TEST
def gen_test(generation: int):
    name = "genlex-test"
    uid = entity_uuid(name)
    tok = ace_token(name, generation)
    hdr = entity_header(name, generation, "Genesis Oxide — Test Utilities")
    write(
        os.path.join(PROJECT_ROOT, "crates/genlex-test/Cargo.toml"),
        """
[package]
name = "genlex-test"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
[dependencies]
genlex-types = { path = "../genlex-types" }
genlex-oxide = { path = "../genlex-oxide" }
""",
    )
    src = f"""{hdr}
//! Test utilities for Genesis Oxide
//! This crate is a placeholder for additional test generation.
pub fn hello() -> &'static str {{
    "Hello from genlex-test!"
}}
"""
    write(os.path.join(PROJECT_ROOT, "crates/genlex-test/src/lib.rs"), src)


# MAIN
def main():
    state = load_state()
    print("═" * 64)
    print(" GENESIS OXIDE — MANIFEST GENERATOR v3 (Hot‑Swap + Continuity)")
    print(f" SOVEREIGN_ANCHOR = {SOVEREIGN_ANCHOR}")
    print(f" OPCODES = {len(OPCODES)} glyph operations")
    print(f" TARGET = {PROJECT_ROOT}")
    print("═" * 64)
    print()
    validate_opcodes()
    print()
    gens = {name: next_generation(state, name) for name in ENTITIES}
    print(" ACE Token Generation:")
    for name, gen in gens.items():
        t = ace_token(name, gen)
        print(f" [{gen:03d}] {name:<20} {t[:24]}...")
    print()
    if os.path.exists(PROJECT_ROOT):
        # Save state file before wiping
        state_backup = None
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                state_backup = f.read()
        shutil.rmtree(PROJECT_ROOT, ignore_errors=True)
    print("[WORKSPACE]")
    gen_workspace()
    print("\n[TIER 0] genlex-types")
    gen_types(gens["genlex-types"])
    print("\n[TIER A] genlex-oxide")
    gen_oxide(gens["genlex-oxide"])
    print("\n[TIER B] dialect-genlex")
    gen_dialect(gens["dialect-genlex"])
    print("\n[TIER C] genesis-runtime")
    gen_runtime(gens["genesis-runtime"])
    print("\n[TIER D] genlex-test")
    gen_test(gens["genlex-test"])
    save_state(state)
    rs_files = [
        (r, f) for r, _, fs in os.walk(PROJECT_ROOT) for f in fs if f.endswith(".rs")
    ]
    toml_files = [
        (r, f) for r, _, fs in os.walk(PROJECT_ROOT) for f in fs if f.endswith(".toml")
    ]
    total_bytes = sum(
        os.path.getsize(os.path.join(r, f)) for r, f in rs_files + toml_files
    )
    print()
    print("═" * 64)
    print(f" MANIFEST COMPLETE — Generation {gens['genesis-runtime']}")
    print(f" {len(rs_files)} Rust files + {len(toml_files)} TOML files")
    print(f" {len(OPCODES)} opcodes across 5 crates")
    print(f" {total_bytes:,} bytes total source")
    print("═" * 64)


if __name__ == "__main__":
    main()
