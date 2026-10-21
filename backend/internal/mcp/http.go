package mcp

import (
	"campusclaw/backend/internal/auth"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"strconv"
)

func FromEnv(d *sql.DB) (*Manager, error) {
	urls := os.Getenv("MCP_ALLOWED_BASE_URLS")
	if urls == "" {
		urls = "http://mcp-demo:8090"
	}
	m, e := New(d, os.Getenv("MCP_ENCRYPTION_KEY"), os.Getenv("MCP_AUTH_TOKEN"), urls)
	if e != nil {
		return nil, e
	}
	for _, v := range []struct {
		name string
		dest *int
		max  int
	}{{"MCP_MAX_ROUNDS", &m.MaxRounds, 5}, {"MCP_MAX_CALLS_PER_TURN", &m.MaxPerTurn, 10}, {"MCP_MAX_CALLS_PER_CONVERSATION", &m.MaxPerConversation, 1000}} {
		if s := os.Getenv(v.name); s != "" {
			n, e := strconv.Atoi(s)
			if e != nil || n < 1 || n > v.max {
				return nil, fmt.Errorf("%s须在1到%d之间", v.name, v.max)
			}
			*v.dest = n
		}
	}
	return m, nil
}
func reply(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if status != 204 {
		_ = json.NewEncoder(w).Encode(v)
	}
}
func problem(w http.ResponseWriter, e error) {
	status, msg := 503, "服务暂时不可用"
	if errors.Is(e, sql.ErrNoRows) {
		status, msg = 404, "资源不存在"
	}
	var api *apiError
	if errors.As(e, &api) {
		status, msg = api.Code, api.Message
	}
	reply(w, status, map[string]string{"error": msg})
}
func decode(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 64<<10)
	if json.NewDecoder(r.Body).Decode(v) != nil {
		reply(w, 400, map[string]string{"error": "请求须为合法JSON"})
		return false
	}
	return true
}
func identity(r *http.Request) (int64, int64) {
	u, _ := auth.FromContext(r.Context())
	id, _ := strconv.ParseInt(r.PathValue("id"), 10, 64)
	return u.ClassID, id
}
func (m *Manager) ListServers(w http.ResponseWriter, r *http.Request) {
	class, _ := identity(r)
	v, e := m.List(r.Context(), class)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
func (m *Manager) GetServer(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	v, e := m.Get(r.Context(), class, id)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
func (m *Manager) SaveServer(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	if r.Method == "PUT" {
		if _, e := m.Get(r.Context(), class, id); e != nil {
			problem(w, e)
			return
		}
	}
	var in Input
	if !decode(w, r, &in) {
		return
	}
	v, e := m.Save(r.Context(), class, id, in)
	if e != nil {
		problem(w, e)
		return
	}
	status := 200
	if r.Method == "POST" {
		status = 201
	}
	reply(w, status, v)
}
func (m *Manager) DeleteServer(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	if e := m.Delete(r.Context(), class, id); e != nil {
		problem(w, e)
		return
	}
	reply(w, 204, nil)
}
func (m *Manager) ConnectServer(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	v, e := m.Connect(r.Context(), class, id)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
func (m *Manager) DisconnectServer(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	if e := m.Disconnect(r.Context(), class, id); e != nil {
		problem(w, e)
		return
	}
	v, e := m.Get(r.Context(), class, id)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
func (m *Manager) ListTools(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	v, e := m.Tools(r.Context(), class, id)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
func (m *Manager) ApproveTool(w http.ResponseWriter, r *http.Request) {
	class, id := identity(r)
	var in struct {
		Fingerprint string `json:"fingerprint"`
	}
	if !decode(w, r, &in) {
		return
	}
	if e := m.Approve(r.Context(), class, id, r.PathValue("tool"), in.Fingerprint); e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, map[string]bool{"approved": true})
}

type Call struct {
	ID             int64  `json:"id,omitempty"`
	Ref            string `json:"ref"`
	Status         string `json:"status"`
	Text           string `json:"text"`
	Round          int    `json:"round"`
	ServerName     string `json:"server_name,omitempty"`
	UserID         int64  `json:"user_id,omitempty"`
	Username       string `json:"username,omitempty"`
	ConversationID int64  `json:"conversation_id,omitempty"`
	RequestID      int64  `json:"request_message_id,omitempty"`
	CreatedAt      string `json:"created_at,omitempty"`
}

func (m *Manager) Audit(ctx context.Context, class int64) ([]Call, error) {
	rows, e := m.DB.QueryContext(ctx, `SELECT c.id,c.tool_ref,c.status,c.summary,c.round_number,c.server_name,c.user_id,COALESCE(u.username,''),c.conversation_id,c.request_message_id,c.created_at FROM mcp_tool_calls c LEFT JOIN users u ON u.id=c.user_id WHERE c.class_id=? ORDER BY c.id DESC LIMIT 100`, class)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	out := []Call{}
	for rows.Next() {
		var c Call
		if e = rows.Scan(&c.ID, &c.Ref, &c.Status, &c.Text, &c.Round, &c.ServerName, &c.UserID, &c.Username, &c.ConversationID, &c.RequestID, &c.CreatedAt); e != nil {
			return nil, e
		}
		out = append(out, c)
	}
	return out, rows.Err()
}
func (m *Manager) Calls(w http.ResponseWriter, r *http.Request) {
	class, _ := identity(r)
	v, e := m.Audit(r.Context(), class)
	if e != nil {
		problem(w, e)
		return
	}
	reply(w, 200, v)
}
