using ModelContextProtocol;
using Siemens.Simatic.Simulation.Runtime;
using System;
using System.Collections.Generic;

namespace PlcSimMcp
{
    /// <summary>
    /// Thin wrapper over the PLCSIM Advanced Simulation Runtime API.
    /// Holds a cache of IInstance handles keyed by name so tool calls across the
    /// session operate on the same virtual PLC.
    /// </summary>
    internal static class Sim
    {
        private static readonly Dictionary<string, IInstance> _cache =
            new Dictionary<string, IInstance>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Get a handle to an already-registered instance (attaches if not cached).</summary>
        public static IInstance Get(string name)
        {
            if (string.IsNullOrWhiteSpace(name))
                throw new McpException("Instance name is required.", McpErrorCode.InvalidParams);

            if (_cache.TryGetValue(name, out var cached))
                return cached;

            try
            {
                var inst = SimulationRuntimeManager.CreateInterface(name);
                _cache[name] = inst;
                return inst;
            }
            catch (Exception ex)
            {
                throw new McpException(
                    $"Instance '{name}' is not registered / cannot be attached: {ex.Message}. " +
                    "Call ListInstances to see registered PLCs, or RegisterInstance to create one.",
                    McpErrorCode.InvalidParams);
            }
        }

        public static void Cache(string name, IInstance inst) => _cache[name] = inst;

        public static void Forget(string name) => _cache.Remove(name);

        /// <summary>Wrap an API call, translating Siemens exceptions into MCP errors.</summary>
        public static T Guard<T>(Func<T> action, string what)
        {
            try { return action(); }
            catch (McpException) { throw; }
            catch (SimulationRuntimeException ex)
            {
                throw new McpException($"{what} failed: {ex.RuntimeErrorCode} — {ex.Message}", McpErrorCode.InternalError);
            }
            catch (Exception ex)
            {
                throw new McpException($"{what} failed: {ex.Message}", McpErrorCode.InternalError);
            }
        }

        public static void Guard(Action action, string what)
        {
            Guard<bool>(() => { action(); return true; }, what);
        }

        /// <summary>Throw if an ERuntimeErrorCode indicates a hard failure (negative code).</summary>
        public static void Check(ERuntimeErrorCode code, string what)
        {
            if ((int)code < 0)
                throw new McpException($"{what} returned error: {code}", McpErrorCode.InternalError);
        }

        /// <summary>Convert an SDataValue into a plain CLR value for JSON output.</summary>
        public static object? ToClr(SDataValue v)
        {
            switch (v.Type)
            {
                case EPrimitiveDataType.Bool: return v.Bool;
                case EPrimitiveDataType.Int8: return v.Int8;
                case EPrimitiveDataType.Int16: return v.Int16;
                case EPrimitiveDataType.Int32: return v.Int32;
                case EPrimitiveDataType.Int64: return v.Int64;
                case EPrimitiveDataType.UInt8: return v.UInt8;
                case EPrimitiveDataType.UInt16: return v.UInt16;
                case EPrimitiveDataType.UInt32: return v.UInt32;
                case EPrimitiveDataType.UInt64: return v.UInt64;
                case EPrimitiveDataType.Float: return v.Float;
                case EPrimitiveDataType.Double: return v.Double;
                case EPrimitiveDataType.Char: return ((char)v.Char).ToString();
                case EPrimitiveDataType.WChar: return v.WChar.ToString();
                default: return null;
            }
        }

        /// <summary>Build an SDataValue of a given primitive type from a string, for typed writes.</summary>
        public static SDataValue FromString(EPrimitiveDataType type, string raw)
        {
            var v = new SDataValue { Type = type };
            try
            {
                switch (type)
                {
                    case EPrimitiveDataType.Bool:
                        v.Bool = raw.Equals("1") || raw.Equals("true", StringComparison.OrdinalIgnoreCase)
                                 || raw.Equals("on", StringComparison.OrdinalIgnoreCase);
                        break;
                    case EPrimitiveDataType.Int8: v.Int8 = sbyte.Parse(raw); break;
                    case EPrimitiveDataType.Int16: v.Int16 = short.Parse(raw); break;
                    case EPrimitiveDataType.Int32: v.Int32 = int.Parse(raw); break;
                    case EPrimitiveDataType.Int64: v.Int64 = long.Parse(raw); break;
                    case EPrimitiveDataType.UInt8: v.UInt8 = byte.Parse(raw); break;
                    case EPrimitiveDataType.UInt16: v.UInt16 = ushort.Parse(raw); break;
                    case EPrimitiveDataType.UInt32: v.UInt32 = uint.Parse(raw); break;
                    case EPrimitiveDataType.UInt64: v.UInt64 = ulong.Parse(raw); break;
                    case EPrimitiveDataType.Float: v.Float = float.Parse(raw); break;
                    case EPrimitiveDataType.Double: v.Double = double.Parse(raw); break;
                    case EPrimitiveDataType.Char: v.Char = (sbyte)(raw.Length > 0 ? raw[0] : 0); break;
                    case EPrimitiveDataType.WChar: v.WChar = raw.Length > 0 ? raw[0] : '\0'; break;
                    default:
                        throw new McpException($"Unsupported primitive type '{type}' for write.", McpErrorCode.InvalidParams);
                }
            }
            catch (FormatException)
            {
                throw new McpException($"Value '{raw}' is not valid for type {type}.", McpErrorCode.InvalidParams);
            }
            return v;
        }
    }
}
