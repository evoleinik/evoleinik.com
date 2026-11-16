---
title: {{ .Title }}
date: {{ .Date.Format "2006-01-02" }}
url: {{ .Permalink }}
---

{{ .RawContent }}
{{- if eq .Section "posts" }}

---

{{ partial "author_line_text.html" . }}
{{- end }}
