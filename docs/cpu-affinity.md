# Side note: running the game on chosen CPU cores

You can start the layer on a subset of your processors with Windows' own `start /affinity`, for example to keep
it off one core, or off the efficiency cores:

```bat
rem Every logical processor except 8 and 9 (hex mask, bit n = logical processor n):
start "" /b /wait /affinity FFFFFCFF target\release\victory.exe run "D:\MyDump\game_scarlett_master.exe" --execute --console series-s
```

**Without a patch the mask does not hold.** The title places its own threads with `SetThreadGroupAffinity`, using
the console's processor numbers. On Windows 11 a thread may be given processors outside its process's mask, and
then the process's mask widens to all of them: a minute into a run, the game was on every processor again (seen
with `(Get-Process victory).ProcessorAffinity`).

The two patches in `patches/` fix that in the layer's kernel module: a title request is narrowed to the mask the
layer was started with (all of the mask if the two do not meet), an empty request passes as Windows defines it,
and a start without a mask changes nothing. They apply to fxceless/victory-fork `f299fba`:

```bat
git apply <kit>\patches\0001-hle-thread-affinity-stays-within-the-launch-mask.patch
git apply <kit>\patches\0002-hle-empty-thread-affinity-mask-passed-on.patch
```

Check it in the first minute of a run (it must print your mask):

```powershell
'{0:X}' -f [int64](Get-Process victory).ProcessorAffinity
```

## Why this kit has it: the test laptop's CPU

The laptop the numbers in [results.md](results.md) come from has one P-core (logical processors 8 and 9) that logs
corrected hardware errors (Event Viewer > Windows Logs > System, source WHEA-Logger, event 19, "internal parity
error"), and that crashed programs and the system while it was in use. Every build, shader warm-up and game run
here was started with the mask above, and this patch is what made that mask hold for the game. With it, no error
came from the runs.

If your CPU logs WHEA-Logger event 19 too, the event's details name a "Processor APIC ID". On this CPU
(i9-14900HX) P-core logical processor *n* has APIC ID (*n* / 2) × 8 + *n* mod 2 (8 and 9 are APIC 32 and 33);
read the mapping on yours before choosing a mask (CPUID leaf 0xB on each processor). Intel's microcode updates for
13th/14th-generation processors and your laptop maker's BIOS updates are worth checking as well.

Builds are long CPU jobs too: run `cargo` under the same mask (`start "" /b /wait /affinity FFFFFCFF cargo build
--release --locked -p victory`), and mind git hooks that run cargo, which start from your shell and not from the
mask.
