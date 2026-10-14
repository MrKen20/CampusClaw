// Package apidocs embeds locally shipped Swagger UI and generated API contracts.
package apidocs

import (
	"embed"
	"io/fs"
	"net/http"
)

//go:embed static/*
var files embed.FS

func Mount(mux *http.ServeMux) {
	sub, _ := fs.Sub(files, "static")
	mux.Handle("GET /swagger/", http.StripPrefix("/swagger/", http.FileServer(http.FS(sub))))
	mux.HandleFunc("GET /swagger", func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "/swagger/", http.StatusTemporaryRedirect)
	})
	mux.HandleFunc("GET /openapi.json", func(w http.ResponseWriter, r *http.Request) {
		b, e := files.ReadFile("static/openapi.json")
		if e != nil {
			http.Error(w, "文档不可用", 503)
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_, _ = w.Write(b)
	})
}
