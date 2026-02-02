# {{ .Site.Title }}

{{ .Site.Params.description }}

## Posts

{{ range .Site.RegularPages }}
- [{{ .Title }}]({{ .Permalink }}) - {{ .Date.Format "2006-01-02" }}
{{ end }}
