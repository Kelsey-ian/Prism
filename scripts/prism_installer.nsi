; ================================================================
;  Prism (棱镜) NSIS Installer Script
;  Usage: makensis prism_installer.nsi
;  Output: dist\Prism_Setup_x64.exe
; ================================================================

!define APP_NAME "Prism"
!define APP_DISPLAY "棱镜 Prism"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Kelsey-ian"
!define APP_URL "https://github.com/Kelsey-ian/Prism"
!define APP_EXE "Prism.exe"
!define APP_REGKEY "Software\Kelsey-ian\Prism"

!ifndef ARCH
  !define ARCH "x64"
!endif

Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "${APP_DISPLAY}"
OutFile "..\dist\Prism_Setup_${ARCH}.exe"
InstallDir "$PROGRAMFILES64\Prism"
InstallDirRegKey HKLM "${APP_REGKEY}" "InstallDir"
ShowInstDetails show

VIAddVersionKey "ProductName" "Prism"
VIAddVersionKey "FileDescription" "Prism - Media Format Converter"
VIAddVersionKey "CompanyName" "Kelsey-ian"
VIAddVersionKey "LegalCopyright" "Copyright (C) Kelsey-ian 2025-2026"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIProductVersion "1.0.0.0"

!define MUI_ICON "..\Logo\Prism.ico"
!define MUI_UNICON "..\Logo\Prism.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_LINK "GitHub"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ================================================================
Section "MainSection" SecMain
  SetShellVarContext all
  SetOutPath "$INSTDIR"

  File /nonfatal /r "..\dist\Prism\*.*"

  WriteRegStr HKLM "${APP_REGKEY}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "${APP_REGKEY}" "Version" "${APP_VERSION}"
  WriteUninstaller "$INSTDIR\uninstall.exe"

  CreateDirectory "$SMPROGRAMS\棱镜 Prism"
  CreateShortcut "$SMPROGRAMS\棱镜 Prism\棱镜 Prism.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateShortcut "$SMPROGRAMS\棱镜 Prism\卸载.lnk" "$INSTDIR\uninstall.exe" "" "" 0

  CreateShortcut "$DESKTOP\棱镜 Prism.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${APP_REGKEY}" "InstallSize" "$0"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "DisplayName" "棱镜 Prism"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "Publisher" "Kelsey-ian"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "URLInfoAbout" "${APP_URL}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism" "NoRepair" 1
SectionEnd

; ================================================================
Section "Uninstall"
  SetShellVarContext all

  RMDir /r "$INSTDIR"

  RMDir /r "$SMPROGRAMS\棱镜 Prism"
  Delete "$DESKTOP\棱镜 Prism.lnk"

  DeleteRegKey HKLM "${APP_REGKEY}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Prism"
SectionEnd