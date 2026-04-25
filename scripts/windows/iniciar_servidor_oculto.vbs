Set WShell = CreateObject("WScript.Shell")
scriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
batPath = scriptPath & "\iniciar_servidor_oculto.bat"
WShell.Run Chr(34) & batPath & Chr(34), 0, False
