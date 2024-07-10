Set objShell = CreateObject("WScript.Shell")

scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
exeDir = scriptDir & "\bat_exe\bat_exe.exe"

Set objLink = objShell.CreateShortcut(scriptDir & "\Agrobit_BAT.lnk")

objLink.TargetPath = exeDir
objLink.WorkingDirectory = scriptDir & "\bat_exe"
objLink.IconLocation = scriptDir & "\bat_exe\Agrobit_logo.ico" 

objLink.Save

Dim fso, f
Set fso = CreateObject("Scripting.FileSystemObject")
datapath = scriptDir & "\bat_exe\DataFiles"
if not fso.FolderExists(datapath) then
	Set f = fso.CreateFolder(datapath)
end if

if not fso.FolderExists(datapath + "\BAT") then
	Set f = fso.CreateFolder(datapath + "\BAT")
end if

if not fso.FolderExists(datapath + "\csv") then
	Set f = fso.CreateFolder(datapath + "\csv")
end if

Dim FileName, UploadStac
UploadStac ="Stac Upload"
FileName = "Agrobit Data"
	Set shortcut = CreateObject("WScript.Shell").CreateShortcut(scriptDir + "\" + FileName + ".lnk")
	shortcut.Description = "Agrobit Data"
	shortcut.TargetPath = datapath
	shortcut.Arguments = "/Arguments:Shortcut"
	shortcut.Save