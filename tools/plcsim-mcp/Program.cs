using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

namespace PlcSimMcp
{
    public class Program
    {
        // Directory holding the bundled Simulation Runtime API + its native/managed deps.
        // Overridable with the PLCSIM_BIN environment variable in case the install moves.
        internal static readonly string PlcSimBinDir =
            Environment.GetEnvironmentVariable("PLCSIM_BIN")
            ?? @"D:\sieman_plc\PLCSIM_V20\resources\bin";

        internal static readonly string PlcSimRuntimeDir =
            Path.Combine(PlcSimBinDir, "wwwroot", "assets", "lib", "runtime");

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool SetDllDirectory(string? lpPathName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern int AddDllDirectory(string newDirectory);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetDefaultDllDirectories(uint directoryFlags);

        private const uint LOAD_LIBRARY_SEARCH_DEFAULT_DIRS = 0x00001000;

        public static async Task Main(string[] args)
        {
            // Resolve the Siemens/Grpc/Google managed assemblies from the PLCSIM install,
            // and point native DLL loading (plcsimscputil64.dll, Vplc*.dll ...) there too.
            AppDomain.CurrentDomain.AssemblyResolve += ResolveManaged;
            try
            {
                SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
                AddDllDirectory(PlcSimBinDir);
            }
            catch { /* pre-Win8 fallback below */ }
            SetDllDirectory(PlcSimBinDir);

            // Prepend to PATH so any transitive native dependency also resolves.
            Environment.SetEnvironmentVariable(
                "PATH", PlcSimBinDir + Path.PathSeparator + Environment.GetEnvironmentVariable("PATH"));

            // Diagnostic mode: exercise the API without the MCP transport.
            if (Array.IndexOf(args, "--selftest") >= 0)
            {
                SelfTest();
                return;
            }

            await RunStdioHost();
        }

        private static void SelfTest()
        {
            try
            {
                var status = McpTools.GetApiStatus();
                Console.WriteLine("SELFTEST OK:");
                Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(
                    status, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                try
                {
                    var list = McpTools.ListInstances();
                    Console.WriteLine("INSTANCES:");
                    Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(
                        list, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                }
                catch (Exception ex) { Console.WriteLine("ListInstances error: " + ex.Message); }
            }
            catch (Exception ex)
            {
                Console.WriteLine("SELFTEST FAILED: " + ex);
            }
        }

        private static Assembly? ResolveManaged(object? sender, ResolveEventArgs eArgs)
        {
            var shortName = new AssemblyName(eArgs.Name).Name;
            if (string.IsNullOrEmpty(shortName)) return null;

            foreach (var dir in new[] { PlcSimRuntimeDir, PlcSimBinDir })
            {
                var candidate = Path.Combine(dir, shortName + ".dll");
                if (File.Exists(candidate))
                {
                    try { return Assembly.LoadFrom(candidate); }
                    catch { /* keep probing */ }
                }
            }
            return null;
        }

        public static async Task RunStdioHost()
        {
            var builder = Host.CreateEmptyApplicationBuilder(settings: null);

            // For STDIO transport, any logging MUST go to stderr (stdout carries JSON-RPC).
            builder.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);
            builder.Logging.SetMinimumLevel(LogLevel.Warning);

            builder.Services
                .AddMcpServer()
                .WithStdioServerTransport()
                .WithToolsFromAssembly();

            var host = builder.Build();
            McpTools.Logger = host.Services.GetRequiredService<ILoggerFactory>().CreateLogger("PlcSimMcp");

            await host.RunAsync();
        }
    }
}
