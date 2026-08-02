using Microsoft.Extensions.Logging;
using ModelContextProtocol;
using ModelContextProtocol.Server;
using Siemens.Simatic.Simulation.Runtime;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;

namespace PlcSimMcp
{
    [McpServerToolType]
    public static class McpTools
    {
        public static ILogger? Logger { get; set; }

        // ---------------------------------------------------------------- status / discovery

        [McpServerTool(Name = "GetApiStatus"),
         Description("FIRST call. Read-only. Returns PLCSIM Simulation Runtime API version, whether the runtime manager is installed/available, initialization state, network mode, and the count of registered virtual PLCs. Does not create anything. If IsRuntimeManagerAvailable is false, PLCSIM is not installed/running correctly and no simulation is possible.")]
        public static object GetApiStatus()
        {
            // Each property can throw if the runtime manager process is not up, so guard
            // them individually and report what we could read.
            bool? available = SafeGet(() => (bool?)SimulationRuntimeManager.IsRuntimeManagerAvailable);
            string? version = SafeGet(() =>
            {
                uint ver = SimulationRuntimeManager.Version;
                return $"{(ver >> 24) & 0xFF}.{(ver >> 16) & 0xFF}.{(ver >> 8) & 0xFF}.{ver & 0xFF}";
            });
            int? count = SafeGet(() => (int?)(SimulationRuntimeManager.RegisteredInstanceInfo?.Length ?? 0));

            bool ok = (available == true) || version != null || count != null;
            return new
            {
                RuntimeManagerReachable = ok,
                IsRuntimeManagerAvailable = available,
                ApiVersion = version,
                IsInitialized = SafeGet(() => (bool?)SimulationRuntimeManager.IsInitialized),
                NetworkMode = SafeGet(() => SimulationRuntimeManager.NetworkMode.ToString()),
                Port = SafeGet(() => (int?)SimulationRuntimeManager.Port),
                RegisteredInstanceCount = count,
                DefaultStoragePath = SafeGet(() => SimulationRuntimeManager.DefaultStoragePath),
                Hint = ok ? null : "Runtime manager not reachable. Start PLCSIM (S7PLCSIMV20.exe) or ensure the PLCSIM Advanced runtime service is running, then retry."
            };
        }

        [McpServerTool(Name = "ListInstances"),
         Description("List all registered virtual PLC instances (id + name) currently known to the PLCSIM runtime manager. Requires PLCSIM runtime available. Use before Attach/PowerOn to see what exists.")]
        public static object ListInstances()
        {
            return Sim.Guard(() =>
            {
                var infos = SimulationRuntimeManager.RegisteredInstanceInfo ?? Array.Empty<SInstanceInfo>();
                return (object)new
                {
                    Count = infos.Length,
                    Instances = infos.Select(i => new { i.ID, i.Name }).ToArray()
                };
            }, "ListInstances");
        }

        [McpServerTool(Name = "ListCpuTypes"),
         Description("List the CPU type names accepted by RegisterInstance (S7-1500 / ET200SP family only — the Simulation Runtime API does NOT expose an S7-1200 enum value). For an S7-1200 (e.g. CPU 1211C) use RegisterUnspecifiedInstance and let the TIA download define the CPU, or RegisterCustomInstance with the Vplc1200 dll.")]
        public static object ListCpuTypes()
        {
            var names = Enum.GetNames(typeof(ECPUType)).OrderBy(n => n).ToArray();
            return new { Count = names.Length, CpuTypes = names };
        }

        // ---------------------------------------------------------------- registration / lifecycle

        [McpServerTool(Name = "RegisterInstance"),
         Description("Register (create) a new virtual PLC of a specific CPU type. cpuType must be one of ListCpuTypes (S7-1500/ET200SP family). Returns the new instance id+name. After registering: SetIp (optional) -> PowerOn -> (download from TIA) -> Run. NOTE: for S7-1200 use RegisterUnspecifiedInstance instead.")]
        public static object RegisterInstance(
            [Description("Name for the new virtual PLC, e.g. 'PLC_1'")] string name,
            [Description("CPU type name from ListCpuTypes, e.g. 'CPU1511' or 'CPU1516F'")] string cpuType)
        {
            if (string.IsNullOrWhiteSpace(name))
                throw new McpException("name is required.", McpErrorCode.InvalidParams);
            if (!Enum.TryParse<ECPUType>(cpuType, ignoreCase: true, out var ct))
                throw new McpException($"Unknown cpuType '{cpuType}'. Call ListCpuTypes.", McpErrorCode.InvalidParams);

            return Sim.Guard(() =>
            {
                var inst = SimulationRuntimeManager.RegisterInstance(ct, name);
                Sim.Cache(name, inst);
                return (object)new { inst.ID, inst.Name, CPUType = inst.CPUType.ToString(), Registered = true };
            }, "RegisterInstance");
        }

        [McpServerTool(Name = "RegisterUnspecifiedInstance"),
         Description("Register a new virtual PLC WITHOUT fixing the CPU type — the CPU is determined when you download the hardware config from TIA Portal. This is the recommended path for an S7-1200 (CPU 1211C) or when unsure. Returns id+name. Then: PowerOn -> download from TIA -> Run.")]
        public static object RegisterUnspecifiedInstance(
            [Description("Name for the new virtual PLC, e.g. 'PLC_1'")] string name)
        {
            if (string.IsNullOrWhiteSpace(name))
                throw new McpException("name is required.", McpErrorCode.InvalidParams);
            return Sim.Guard(() =>
            {
                var inst = SimulationRuntimeManager.RegisterInstance(name);
                Sim.Cache(name, inst);
                return (object)new { inst.ID, inst.Name, Registered = true };
            }, "RegisterUnspecifiedInstance");
        }

        [McpServerTool(Name = "RegisterCustomInstance"),
         Description("Advanced/experimental: register a virtual PLC backed by a specific VPLC dll (e.g. the bundled Siemens.Simatic.PlcSim.Vplc1200.dll for S7-1200 simulation). vplcDll may be a bare filename resolved from the PLCSIM bin dir, or an absolute path. Use only if RegisterUnspecifiedInstance does not accept your CPU.")]
        public static object RegisterCustomInstance(
            [Description("Name for the new virtual PLC")] string name,
            [Description("VPLC dll filename or absolute path, e.g. 'Siemens.Simatic.PlcSim.Vplc1200.dll'")] string vplcDll)
        {
            if (string.IsNullOrWhiteSpace(name) || string.IsNullOrWhiteSpace(vplcDll))
                throw new McpException("name and vplcDll are required.", McpErrorCode.InvalidParams);

            var path = System.IO.Path.IsPathRooted(vplcDll)
                ? vplcDll
                : System.IO.Path.Combine(Program.PlcSimBinDir, vplcDll);

            return Sim.Guard(() =>
            {
                var inst = SimulationRuntimeManager.RegisterCustomInstance(path, name);
                Sim.Cache(name, inst);
                return (object)new { inst.ID, inst.Name, VplcDll = path, Registered = true };
            }, "RegisterCustomInstance");
        }

        [McpServerTool(Name = "UnregisterInstance"),
         Description("Unregister (delete) a virtual PLC instance and release its handle. Powers it off first if running. Irreversible for that instance's in-memory state (archive with ArchiveStorage first if you want to keep it).")]
        public static object UnregisterInstance(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.UnregisterInstance(), "UnregisterInstance");
            Sim.Forget(name);
            return new { name, Unregistered = true };
        }

        [McpServerTool(Name = "PowerOn"),
         Description("Power ON a registered virtual PLC (boots the CPU into STOP). Required before downloading a program from TIA Portal or going to RUN. timeoutMs default 60000.")]
        public static object PowerOn(
            [Description("Instance name")] string name,
            [Description("Timeout in ms (default 60000)")] uint timeoutMs = 60000)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() =>
            {
                var code = inst.PowerOn(timeoutMs);
                Sim.Check(code, "PowerOn");
                return (object)new { name, Result = code.ToString(), OperatingState = inst.OperatingState.ToString() };
            }, "PowerOn");
        }

        [McpServerTool(Name = "PowerOff"),
         Description("Power OFF a virtual PLC (shuts the CPU down). timeoutMs default 60000.")]
        public static object PowerOff(
            [Description("Instance name")] string name,
            [Description("Timeout in ms (default 60000)")] uint timeoutMs = 60000)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.PowerOff(timeoutMs), "PowerOff");
            return new { name, PoweredOff = true };
        }

        [McpServerTool(Name = "Run"),
         Description("Set the virtual CPU to RUN (start executing the downloaded program). The CPU must be powered on and have a program downloaded. Equivalent to the RUN switch.")]
        public static object Run(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.Run(), "Run");
            return new { name, OperatingState = inst.OperatingState.ToString() };
        }

        [McpServerTool(Name = "Stop"),
         Description("Set the virtual CPU to STOP (halt program execution, outputs go to safe state). Equivalent to the STOP switch.")]
        public static object Stop(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.Stop(), "Stop");
            return new { name, OperatingState = inst.OperatingState.ToString() };
        }

        [McpServerTool(Name = "MemoryReset"),
         Description("Perform a memory reset (MRES) on the virtual CPU — clears work/load memory and retentive data, like the TIA 'Reset to factory settings' minus IP. CPU must be powered on. Use before re-downloading a clean program.")]
        public static object MemoryReset(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.MemoryReset(), "MemoryReset");
            return new { name, MemoryReset = true, OperatingState = inst.OperatingState.ToString() };
        }

        // ---------------------------------------------------------------- info / state

        [McpServerTool(Name = "GetInstanceInfo"),
         Description("Read full status of one virtual PLC: operating state (Run/Stop/Off/...), operating mode, CPU type, article number, controller name/designation, IP addresses, communication interface, license status, and system time. Read-only.")]
        public static object GetInstanceInfo(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() => (object)new
            {
                inst.ID,
                inst.Name,
                OperatingState = inst.OperatingState.ToString(),
                OperatingMode = inst.OperatingMode.ToString(),
                CPUType = inst.CPUType.ToString(),
                ArticleNumber = SafeGet(() => inst.ArticleNumber),
                ControllerName = SafeGet(() => inst.ControllerName),
                ControllerShortDesignation = SafeGet(() => inst.ControllerShortDesignation),
                IP = SafeGet(() => inst.ControllerIP != null ? string.Join(", ", inst.ControllerIP) : null),
                CommunicationInterface = inst.CommunicationInterface.ToString(),
                LicenseStatus = inst.LicenseStatus.ToString(),
                SystemTime = SafeGet(() => (object)inst.SystemTime)
            }, "GetInstanceInfo");
        }

        [McpServerTool(Name = "GetOperatingState"),
         Description("Quick read of just the RUN/STOP/OFF operating state of a virtual PLC. Read-only.")]
        public static object GetOperatingState(
            [Description("Instance name")] string name)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() => (object)new { name, OperatingState = inst.OperatingState.ToString() }, "GetOperatingState");
        }

        // ---------------------------------------------------------------- tag list

        [McpServerTool(Name = "UpdateTagList"),
         Description("Load/refresh the tag list of a virtual PLC from its downloaded program. Must be called (after a program download) before GetTagList / reading tags by symbolic name. details controls scope: IOMCTDB = everything (I/O, Markers, Counters, Timers, DataBlocks); IO = only inputs/outputs; default IOMCTDB. hmiVisibleOnly=false includes all tags.")]
        public static object UpdateTagList(
            [Description("Instance name")] string name,
            [Description("Scope: None|IO|M|IOM|CT|IOCT|MCT|IOMCT|DB|IODB|MDB|IOMDB|CTDB|IOCTDB|MCTDB|IOMCTDB (default IOMCTDB)")] string details = "IOMCTDB",
            [Description("Only HMI-visible tags (default false = all)")] bool hmiVisibleOnly = false)
        {
            var inst = Sim.Get(name);
            if (!Enum.TryParse<ETagListDetails>(details, ignoreCase: true, out var d))
                throw new McpException($"Invalid details '{details}'.", McpErrorCode.InvalidParams);
            Sim.Guard(() => inst.UpdateTagList(d, hmiVisibleOnly), "UpdateTagList");
            var count = SafeGet(() => inst.TagInfos?.Length ?? 0);
            return new { name, Updated = true, Scope = d.ToString(), TagCount = count };
        }

        [McpServerTool(Name = "GetTagList"),
         Description("List tags known to the virtual PLC after UpdateTagList: name, area (Input/Output/Marker/DataBlock/...), data type, byte offset and bit. Optional nameFilter (case-insensitive substring). Read-only.")]
        public static object GetTagList(
            [Description("Instance name")] string name,
            [Description("Optional case-insensitive substring filter on tag name")] string? nameFilter = null,
            [Description("Max tags to return (default 500)")] int limit = 500)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() =>
            {
                var tags = inst.TagInfos ?? Array.Empty<STagInfo>();
                IEnumerable<STagInfo> q = tags;
                if (!string.IsNullOrWhiteSpace(nameFilter))
                    q = q.Where(t => t.Name != null && t.Name.IndexOf(nameFilter, StringComparison.OrdinalIgnoreCase) >= 0);
                var list = q.Take(Math.Max(1, limit)).Select(t => new
                {
                    t.Name,
                    Area = t.Area.ToString(),
                    DataType = t.PrimitiveDataType.ToString(),
                    t.Offset,
                    t.Bit,
                    t.Size
                }).ToArray();
                return (object)new { name, Returned = list.Length, TotalKnown = tags.Length, Tags = list };
            }, "GetTagList");
        }

        // ---------------------------------------------------------------- read / write by symbolic name

        [McpServerTool(Name = "ReadTag"),
         Description("Read the current value of a tag by symbolic name (e.g. '\"Tag_1\"', 'Start', '\"MyDB\".Speed'). Requires UpdateTagList first. Returns value + detected type. Read-only.")]
        public static object ReadTag(
            [Description("Instance name")] string name,
            [Description("Symbolic tag name as used in TIA (quote DB/tag names as needed)")] string tag)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() =>
            {
                var v = inst.Read(tag);
                return (object)new { name, tag, Type = v.Type.ToString(), Value = Sim.ToClr(v) };
            }, $"ReadTag('{tag}')");
        }

        [McpServerTool(Name = "WriteTag"),
         Description("Write a value to a tag by symbolic name. The tag's type is auto-detected by reading it first, then the value string is coerced to that type ('true'/'1' for bools, decimals for reals, integers otherwise). Requires UpdateTagList first. This changes live simulation values.")]
        public static object WriteTag(
            [Description("Instance name")] string name,
            [Description("Symbolic tag name")] string tag,
            [Description("Value as string, e.g. 'true', '1', '42', '3.14'")] string value)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() =>
            {
                var current = inst.Read(tag);            // learn the type
                var toWrite = Sim.FromString(current.Type, value);
                inst.Write(tag, toWrite);
                var after = inst.Read(tag);
                return (object)new { name, tag, Type = after.Type.ToString(), Written = Sim.ToClr(after) };
            }, $"WriteTag('{tag}')");
        }

        // ---------------------------------------------------------------- read / write by absolute address

        [McpServerTool(Name = "ReadBit"),
         Description("Read a single bit by absolute address from an I/O or Marker area WITHOUT needing the tag list. area = Input|Output|Marker. Example: area=Output, byteOffset=0, bit=7 reads Q0.7. Read-only.")]
        public static object ReadBit(
            [Description("Instance name")] string name,
            [Description("Area: Input | Output | Marker")] string area,
            [Description("Byte offset (the N in Q0.7 -> 0)")] uint byteOffset,
            [Description("Bit number 0-7 (the M in Q0.7 -> 7)")] byte bit)
        {
            var inst = Sim.Get(name);
            var io = ResolveArea(inst, area);
            return Sim.Guard(() => (object)new { name, area, byteOffset, bit, Value = io.ReadBit(byteOffset, bit) },
                $"ReadBit({area} {byteOffset}.{bit})");
        }

        [McpServerTool(Name = "WriteBit"),
         Description("Write a single bit by absolute address to an I/O or Marker area WITHOUT the tag list. area = Input|Output|Marker. Example: area=Input, byteOffset=0, bit=0, value=true sets I0.0 (simulate a pushbutton). Changes live simulation values.")]
        public static object WriteBit(
            [Description("Instance name")] string name,
            [Description("Area: Input | Output | Marker")] string area,
            [Description("Byte offset")] uint byteOffset,
            [Description("Bit number 0-7")] byte bit,
            [Description("Bit value true/false")] bool value)
        {
            var inst = Sim.Get(name);
            var io = ResolveArea(inst, area);
            Sim.Guard(() => io.WriteBit(byteOffset, bit, value), $"WriteBit({area} {byteOffset}.{bit})");
            return new { name, area, byteOffset, bit, Written = value };
        }

        [McpServerTool(Name = "ReadBytes"),
         Description("Read one or more raw bytes by absolute address from an I/O or Marker area. area = Input|Output|Marker. Returns the bytes as an integer array. Read-only.")]
        public static object ReadBytes(
            [Description("Instance name")] string name,
            [Description("Area: Input | Output | Marker")] string area,
            [Description("Starting byte offset")] uint byteOffset,
            [Description("Number of bytes to read")] uint count)
        {
            var inst = Sim.Get(name);
            var io = ResolveArea(inst, area);
            return Sim.Guard(() =>
            {
                var bytes = io.ReadBytes(byteOffset, count);
                return (object)new { name, area, byteOffset, count, Bytes = bytes.Select(b => (int)b).ToArray() };
            }, $"ReadBytes({area} {byteOffset}+{count})");
        }

        [McpServerTool(Name = "WriteBytes"),
         Description("Write one or more raw bytes by absolute address to an I/O or Marker area. area = Input|Output|Marker. bytes is a comma-separated list of 0-255 values, e.g. '255,0,16'. Changes live simulation values.")]
        public static object WriteBytes(
            [Description("Instance name")] string name,
            [Description("Area: Input | Output | Marker")] string area,
            [Description("Starting byte offset")] uint byteOffset,
            [Description("Comma-separated byte values 0-255, e.g. '255,0,16'")] string bytes)
        {
            var inst = Sim.Get(name);
            var io = ResolveArea(inst, area);
            byte[] data;
            try { data = bytes.Split(',').Select(s => byte.Parse(s.Trim())).ToArray(); }
            catch { throw new McpException("bytes must be comma-separated 0-255 values.", McpErrorCode.InvalidParams); }
            return Sim.Guard(() =>
            {
                uint written = io.WriteBytes(byteOffset, data);
                return (object)new { name, area, byteOffset, BytesWritten = written };
            }, $"WriteBytes({area} {byteOffset})");
        }

        // ---------------------------------------------------------------- network / storage / mode

        [McpServerTool(Name = "SetIp"),
         Description("Set the IP suite (address, subnet mask, gateway) of the virtual PLC's interface. interfaceId is usually 0 for the first PROFINET interface. Set the PLC to match the project's configured IP so TIA can download to it. Powered-on CPU recommended.")]
        public static object SetIp(
            [Description("Instance name")] string name,
            [Description("IPv4 address, e.g. '192.168.0.1'")] string ip,
            [Description("Subnet mask, e.g. '255.255.255.0'")] string subnetMask,
            [Description("Default gateway, e.g. '0.0.0.0' for none")] string gateway = "0.0.0.0",
            [Description("Interface id (default 0)")] uint interfaceId = 0,
            [Description("Persist across power cycles (default true)")] bool remanent = true)
        {
            var inst = Sim.Get(name);
            return Sim.Guard(() =>
            {
                var suite = new SIPSuite4
                {
                    IPAddress = new SIP { IPString = ip },
                    SubnetMask = new SIP { IPString = subnetMask },
                    DefaultGateway = new SIP { IPString = gateway }
                };
                inst.SetIPSuite(interfaceId, suite, remanent);
                return (object)new { name, ip, subnetMask, gateway, interfaceId, Set = true };
            }, "SetIp");
        }

        [McpServerTool(Name = "ArchiveStorage"),
         Description("Save the full virtual PLC state (program + retentive memory) to a .zip archive file so it can be restored later with RetrieveStorage. Provide an absolute file path ending in .zip.")]
        public static object ArchiveStorage(
            [Description("Instance name")] string name,
            [Description("Absolute path to write, e.g. 'D:\\\\sim\\\\PLC_1.zip'")] string filePath)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.ArchiveStorage(filePath), "ArchiveStorage");
            return new { name, filePath, Archived = true };
        }

        [McpServerTool(Name = "RetrieveStorage"),
         Description("Restore a virtual PLC's state from a .zip archive previously written by ArchiveStorage. The instance should be powered off. Provide the absolute archive file path.")]
        public static object RetrieveStorage(
            [Description("Instance name")] string name,
            [Description("Absolute path to the .zip archive")] string filePath)
        {
            var inst = Sim.Get(name);
            Sim.Guard(() => inst.RetrieveStorage(filePath), "RetrieveStorage");
            return new { name, filePath, Retrieved = true };
        }

        [McpServerTool(Name = "SetOperatingMode"),
         Description("Set the virtual PLC operating/timing mode. mode = Default (real-time) | SingleStep_C | TimespanSynchronized_C | ... Advanced: use Default unless you need deterministic stepping/scaled time. See EOperatingMode values.")]
        public static object SetOperatingMode(
            [Description("Instance name")] string name,
            [Description("Mode: Default | SingleStep_C | SingleStep_CT | TimespanSynchronized_C | SingleStep_P | TimespanSynchronized_P | SingleStep_CP | SingleStep_CPT | TimespanSynchronized_CP | SingleStep_Bus")] string mode)
        {
            var inst = Sim.Get(name);
            if (!Enum.TryParse<EOperatingMode>(mode, ignoreCase: true, out var m))
                throw new McpException($"Invalid mode '{mode}'.", McpErrorCode.InvalidParams);
            Sim.Guard(() => inst.OperatingMode = m, "SetOperatingMode");
            return new { name, OperatingMode = m.ToString() };
        }

        [McpServerTool(Name = "ShutdownRuntimeManager"),
         Description("Shut down the whole PLCSIM runtime manager and release all instances. Use only when completely done — this affects every virtual PLC, not just one.")]
        public static object ShutdownRuntimeManager()
        {
            Sim.Guard(() => SimulationRuntimeManager.Shutdown(), "ShutdownRuntimeManager");
            return new { ShutDown = true };
        }

        // ---------------------------------------------------------------- helpers

        private static IIOArea ResolveArea(IInstance inst, string area)
        {
            switch ((area ?? "").Trim().ToLowerInvariant())
            {
                case "input": case "i": case "e": return inst.InputArea;
                case "output": case "q": case "a": return inst.OutputArea;
                case "marker": case "m": case "flag": return inst.MarkerArea;
                default:
                    throw new McpException($"Unknown area '{area}'. Use Input, Output, or Marker.", McpErrorCode.InvalidParams);
            }
        }

        private static T? SafeGet<T>(Func<T> getter)
        {
            try { return getter(); }
            catch { return default; }
        }
    }
}
