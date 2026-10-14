Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd.exe /c cd /d """ & ScriptDir & """ && python desktop_toggler.py", 0, False