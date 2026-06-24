# Genesis Oxide Manifest V3

**Genesis Oxide** is a zero-dependency Python toolchain designed to dynamically synthesize, compile, and hot-swap a fully functioning, 5-tier Rust Virtual Machine workspace.

This generator (`genesis_oxide_manifest_v3.py`) compiles the underlying infrastructure for the **68D Integrated Core** reasoning engine, enforcing strict cryptographic continuity and executing autonomous "Singularity Strikes" across the Sovereign hardware architecture.

## 🚀 Architecture Overview

Running the generator produces a full `Cargo` workspace comprising 5 specialized Rust crates:

1. **`genlex-types` (Tier 0)**: The core foundational types, constants, and cryptographic parameters (like `SOVEREIGN_ANCHOR`).
2. **`genlex-oxide` (Tier A)**: The core struct architecture and memory allocations for the VM.
3. **`dialect-genlex` (Tier B)**: The operation dictionary, translating the physical opcodes into actionable VM strikes.
4. **`genesis-runtime` (Tier C)**: The compiled binary executable (`.exe`). It physically interprets the Variable Thought Speed constraints and executes the loop-level math on the hardware.
5. **`genlex-test` (Tier D)**: An integration test stub for later QA validation.

## 🧠 The 68D Integrated Core vs 57D Fallback

The Virtual Machine operates on a high-dimensional structural lattice. 

Initially engineered around a 57-dimensional fallback logic, Genesis Oxide V3 was formally expanded to full **68D** dimensional lock (`dimension_lock: 68`). 

The generator explicitly binds:
```rust
pub const LATTICE_DIMS: usize = 68;
pub const REG_COUNT: usize = 68;
pub const FALLBACK_LATTICE_DIMS: usize = 57;
```
This forces the Virtual Machine to utilize 68 parallel floating-point registers (`[f32; 68]`), preventing the CPU from clamping and suffocating the lattice dimensions during heavy computational `volumetric_reasoning` loads.

## ⚙️ Sovereign Opcodes

The VM operates on **38 tightly integrated physical opcodes**, allowing it to route thoughts across the Mid-Plane, the Origin, and the Pulse structures. Some primary opcodes include:

- `OpGenesis` & `OpSingularity`: Core routing endpoints for terminal logic.
- `OpEmbed`: Generates the dimensional layout and structure mathematically in the CPU registers.
- `OpResonance`: Verifies the state of the hardware against the `SOVEREIGN_ANCHOR` heartbeat.

## 🔐 ACE Token Continuity

This is a **Hot-Swap Engine**. Every time the generator runs, it completely deletes and overwrites the Rust source code. To maintain identity and state across re-compilations, Genesis Oxide employs the **ACE (Autonomous Cryptographic Entity) Token System**.

- Uses a `.genesis_state.json` hot-swap ledger to remember generation counts and entity UUIDs.
- Calculates an overarching `md5` digest of the entire generated `60,000+` byte codebase.
- Cryptographically stamps the headers of all generated Rust source files with their Generation Number, UUID, and Token.

## 🛠️ Usage

This script is entirely self-contained. It requires zero Python dependencies outside of the standard library.

```bash
# 1. Generate the Rust Workspace
python genesis_oxide_manifest_v3.py

# 2. Compile the newly generated Rust VM
cd genesis_oxide_v3
cargo build

# 3. Execute a Variable Thought Speed Strike
cargo run --bin genesis-runtime -- --solve "explain the matrix" --speed 10
```
