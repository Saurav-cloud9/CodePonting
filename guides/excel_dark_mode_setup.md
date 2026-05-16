# Excel Dark Mode Setup Guide

## Colors Used

| Element | Color |
|---|---|
| Background | `#1E1E1E` |
| Font (data rows) | `#D0CECE` |
| Font (header row 1) | `#C65911` (orange) |
| Gridlines | `#3A3A3A` |

---

## 1. Applying Dark Mode to Existing Files (Macro via Ctrl+Shift+D)

*First-time setup only.*

### Step 1 — Create PERSONAL.XLSB

- Excel → View → Macros → Record Macro
- Set "Store macro in" → **Personal Macro Workbook**
- Click OK → immediately View → Macros → Stop Recording

### Step 2 — Paste the macro

- `Alt+F11` to open VBA editor
- Expand **PERSONAL.XLSB** → Modules → Module1
- Paste this **below** the existing `Sub Macro1()...End Sub`:

```vba
Sub ApplyDarkMode()
    Dim ws As Worksheet
    Dim lastCol As Long
    Dim headerRange As Range

    For Each ws In ActiveWorkbook.Worksheets
        With ws.Cells
            .Interior.Color = RGB(30, 30, 30)
            .Font.Color = RGB(208, 206, 206)
            .Borders.LineStyle = xlContinuous
            .Borders.Weight = xlThin
            .Borders.Color = RGB(58, 58, 58)
        End With

        lastCol = ws.UsedRange.Columns(ws.UsedRange.Columns.Count).Column
        Set headerRange = ws.Range(ws.Cells(1, 1), ws.Cells(1, lastCol))
        With headerRange.Font
            .Color = RGB(198, 89, 17)
            .Bold = False
            .Size = 11
        End With
    Next ws

    MsgBox "Dark mode applied!", vbInformation
End Sub
```

### Step 3 — Save

- `Ctrl+S` in VBA editor
- Close Excel → click Save when prompted for PERSONAL.XLSB

### Step 4 — Assign keyboard shortcut

- Excel → View → Macros → View Macros
- Select **PERSONAL.XLSB!ApplyDarkMode** → click Options
- Set shortcut: `Ctrl+Shift+D` → OK

### Step 5 — Delete the dummy Macro1

- Excel → View → Unhide → select PERSONAL.XLSB → OK
- View → Macros → View Macros → select Macro1 → Delete
- View → Hide to re-hide PERSONAL.XLSB
- Close Excel → Save PERSONAL.XLSB when prompted

**Usage:** Open any existing file → press `Ctrl+Shift+D` → dark mode applied instantly.

---

## 2. Dark Mode for New Files (Ctrl+N)

*First-time setup only.*

### Step 1 — Apply dark theme to a blank sheet

- Open a blank workbook
- Run the ApplyDarkMode macro (or ask Claude to apply the dark theme)

### Step 2 — Save as default template

- File → Save As → Browse
- Set **Save as type** → `Excel Template (*.xltx)`
- Name it exactly: `Book`
- Paste this in the address bar and hit Enter:
  ```
  C:\Users\[YourName]\AppData\Roaming\Microsoft\Excel\XLSTART
  ```
- Click Save → overwrite if prompted
- Close and reopen Excel

**Usage:** Press `Ctrl+N` → new workbook opens dark automatically.

---

## Notes

| Scenario | Mechanism |
|---|---|
| `Ctrl+N` new file | `Book.xltx` in XLSTART |
| Existing file | `Ctrl+Shift+D` macro in PERSONAL.XLSB |
| Right-click → New on desktop | Does **not** use either (Windows shell template — unreliable to configure) |

Both files live in:
```
C:\Users\[YourName]\AppData\Roaming\Microsoft\Excel\XLSTART
```
