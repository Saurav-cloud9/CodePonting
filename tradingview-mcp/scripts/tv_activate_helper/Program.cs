using System;
using System.Runtime.InteropServices;

[ComImport, Guid("2e941141-7f97-4756-ba1d-9decde894a3d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IApplicationActivationManager
{
    [PreserveSig]
    int ActivateApplication(
        [In, MarshalAs(UnmanagedType.LPWStr)] string appUserModelId,
        [In, MarshalAs(UnmanagedType.LPWStr)] string arguments,
        [In] int options,
        [Out] out uint processId);
}

[ComImport, Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")]
class ApplicationActivationManagerClass
{
}

class Program
{
    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("Usage: tv_activate_helper.exe <AUMID> [arguments]");
            return 1;
        }

        string aumid = args[0];
        string arguments = args.Length > 1 ? args[1] : "";

        var mgr = (IApplicationActivationManager)new ApplicationActivationManagerClass();
        uint pid;
        int hr = mgr.ActivateApplication(aumid, arguments, 0, out pid);

        Console.WriteLine("HRESULT: 0x" + hr.ToString("X8"));
        Console.WriteLine("PID: " + pid);
        return hr;
    }
}
