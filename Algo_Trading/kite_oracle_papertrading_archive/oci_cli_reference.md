# OCI CLI Reference

- **Tenancy OCID**: `ocid1.tenancy.oc1..aaaaaaaamjyo6wy75wcw6lv7sxifjr2i4faeuu2hlkprkroty7ld32e4x4ma`
- **Region**: `ap-mumbai-1`

---

**Authenticate (Windows, session token expires ~1hr - re-run when needed):**
>```powershell
>oci session authenticate
>```

**VM (Ubuntu) uses API-key auth - never expires, no re-auth needed.**

---

**Raw JSON cost details (Windows):**
>```powershell
>oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaamjyo6wy75wcw6lv7sxifjr2i4faeuu2hlkprkroty7ld32e4x4ma --time-usage-started 2026-07-01T00:00:00Z --time-usage-ended 2026-08-03T00:00:00Z --granularity MONTHLY --config-file C:\Users\Saurav\.oci\config --profile DEFAULT --auth security_token
>```

**Raw JSON cost details (VM):**
>```bash
>oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaamjyo6wy75wcw6lv7sxifjr2i4faeuu2hlkprkroty7ld32e4x4ma --time-usage-started 2026-07-01T00:00:00Z --time-usage-ended 2026-08-03T00:00:00Z --granularity MONTHLY
>```

---

**One-time setup - create the group-by file (needed for the tabular commands below):**
>```powershell
>'["service"]' | Set-Content -Path group_by.json -NoNewline
>```

**Tabular cost details, grouped by service (Windows):**
>```powershell
>oci usage-api usage-summary request-summarized-usages `
>  --tenant-id ocid1.tenancy.oc1..aaaaaaaamjyo6wy75wcw6lv7sxifjr2i4faeuu2hlkprkroty7ld32e4x4ma `
>  --time-usage-started 2026-07-01T00:00:00Z `
>  --time-usage-ended 2026-08-03T00:00:00Z `
>  --granularity MONTHLY `
>  --group-by file://group_by.json `
>  --config-file C:\Users\Saurav\.oci\config --profile DEFAULT --auth security_token |
>  ConvertFrom-Json |
>  Select-Object -ExpandProperty data |
>  Select-Object -ExpandProperty items |
>  Select-Object service, @{N='Amount';E={$_.'computed-amount'}}, @{N='Quantity';E={$_.'computed-quantity'}}, currency, @{N='PeriodStart';E={$_.'time-usage-started'}}, @{N='PeriodEnd';E={$_.'time-usage-ended'}} |
>  Format-Table -AutoSize
>```

**Tabular cost details, grouped by service (VM - needs `jq`):**
>```bash
>oci usage-api usage-summary request-summarized-usages \
>  --tenant-id ocid1.tenancy.oc1..aaaaaaaamjyo6wy75wcw6lv7sxifjr2i4faeuu2hlkprkroty7ld32e4x4ma \
>  --time-usage-started 2026-07-01T00:00:00Z \
>  --time-usage-ended 2026-08-03T00:00:00Z \
>  --granularity MONTHLY \
>  --group-by '["service"]' \
>  | jq -r '.data.items[] | [.service, .["computed-amount"], .["computed-quantity"], .currency, .["time-usage-started"], .["time-usage-ended"]] | @tsv' \
>  | column -t -s $'\t'
>```

---

**What to look for:** `computed-amount` = actual charge. `0.0` across every service = no charges (Always Free tier). Verified 2026-08-03 across console UI, VM CLI, and Windows CLI.
